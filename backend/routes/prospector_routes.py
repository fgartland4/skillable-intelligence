"""Prospector blueprint — batch company scoring and results."""

import csv
import io
import threading
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, Response, stream_with_context, jsonify

from core import _push, _sse_stream, _attach_scores, _compute_composite, _fmt_ondemand, _fmt_cert, _cancelled_jobs
from researcher import discover_products
from scorer import discover_products_with_claude, score_selected_products
from storage import (
    save_analysis, load_analysis,
    find_analysis_by_company_name,
    save_prospector_run, load_prospector_run,
    append_poor_fit_feedback, load_poor_fit_companies,
    load_discovery,
)

import logging
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prospector Blueprint
# ---------------------------------------------------------------------------

prospector = Blueprint("prospector", __name__, url_prefix="/prospector")


def _derive_skillable_path(lab_score: int) -> str:
    """Map a lab score to the three Prospector path labels (software companies)."""
    if lab_score >= 50:
        return "Labable"
    if lab_score >= 20:
        return "Simulations"
    return "Do Not Pursue"


def _derive_academic_path(lab_score: int, school_name: str | None, has_tech_programs: bool) -> str:
    """Map academic institution signals to a Skillable path label.

    - No tech programs at all → "Not a Fit"
    - Has tech programs: use engineering/tech school name if known, else tier label
    """
    if not has_tech_programs:
        return "Not a Fit"
    if school_name:
        return school_name  # e.g. "Tandy School of Computer Science"
    if lab_score >= 40:
        return "Academic — High Potential"
    return "Academic — Emerging"


@prospector.route("/")
@prospector.route("")
def prospector_home():
    poor_fit = load_poor_fit_companies()
    return render_template("prospector.html", poor_fit_count=len(poor_fit))


@prospector.route("/run", methods=["POST"])
def prospector_run():
    company_names = []

    # Mode 1: CSV file upload — read first column
    uploaded = request.files.get("csv_file")
    if uploaded and uploaded.filename:
        stream = io.StringIO(uploaded.stream.read().decode("utf-8-sig"))
        reader = csv.reader(stream)
        for row in reader:
            if row and row[0].strip() and row[0].strip().lower() != "company":
                company_names.append(row[0].strip())

    # Mode 2: pasted text (fallback)
    if not company_names:
        raw = request.form.get("companies", "")
        company_names = [n.strip() for n in raw.replace(",", "\n").splitlines() if n.strip()]

    if not company_names:
        return redirect(url_for("prospector.prospector_home"))

    # Filter out previously flagged poor fits
    poor_fit = load_poor_fit_companies()
    filtered = [n for n in company_names if n.lower() not in poor_fit]
    skipped = len(company_names) - len(filtered)
    company_names = filtered

    if not company_names:
        return redirect(url_for("prospector.prospector_home"))

    force_refresh = request.form.get("force_refresh") == "1"

    COMPANY_TIMEOUT_SECS = 180  # 3 minutes — slow orgs are skipped, not waited on

    job_id = str(uuid.uuid4())[:8]
    results = {}
    semaphore = threading.Semaphore(3)

    def run_batch():
        def analyze_one(name):
            if job_id in _cancelled_jobs:
                return
            with semaphore:
                if job_id in _cancelled_jobs:
                    return
                _push(job_id, f"status:Analyzing {name}...")

                result_holder = [None]
                def _run():
                    result_holder[0] = _quick_analyze_company(name, force_refresh=force_refresh)

                worker = threading.Thread(target=_run, daemon=True)
                worker.start()
                worker.join(timeout=COMPANY_TIMEOUT_SECS)

                if worker.is_alive():
                    # Timed out — release the slot and move on
                    results[name] = {"company_name": name, "timed_out": True}
                    _push(job_id, f"timeout:{name}")
                else:
                    row = result_holder[0]
                    if row:
                        # Academic path labels are set inside _quick_analyze_company — don't override
                        if not row.get("skillable_path"):
                            row["skillable_path"] = _derive_skillable_path(row.get("lab_score", 0))
                        row["flagged_poor_fit"] = False
                    results[name] = row or {"company_name": name, "error": "Analysis failed"}
                    _push(job_id, f"progress:{name}")

        threads = [threading.Thread(target=analyze_one, args=(n,), daemon=True) for n in company_names]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        cancelled = job_id in _cancelled_jobs
        _cancelled_jobs.discard(job_id)
        save_prospector_run(job_id, {
            "job_id": job_id,
            "companies": company_names,
            "skipped_poor_fit": skipped,
            "results": results,
            "status": "cancelled" if cancelled else "done",
        })
        _push(job_id, f"done:{job_id}")

    threading.Thread(target=run_batch, daemon=True).start()
    return render_template("prospector_running.html", job_id=job_id,
                           company_names=company_names,
                           company_count=len(company_names))


@prospector.route("/cancel/<job_id>", methods=["POST"])
def prospector_cancel(job_id: str):
    _cancelled_jobs.add(job_id)
    _push(job_id, f"done:{job_id}")
    return jsonify({"cancelled": True})


@prospector.route("/status/<job_id>")
def prospector_status(job_id: str):
    return Response(stream_with_context(_sse_stream(job_id, poll_interval=0.5)),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@prospector.route("/results/<job_id>")
def prospector_results(job_id: str):
    job = load_prospector_run(job_id)
    if not job:
        return redirect(url_for("prospector.prospector_home"))
    results = job.get("results", {})
    rows = [r for r in results.values() if r and "error" not in r and not r.get("timed_out")]
    rows.sort(key=lambda r: r.get("composite_score", 0), reverse=True)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    errors = [r for r in results.values() if r and "error" in r]
    timed_out = [r for r in results.values() if r and r.get("timed_out")]
    return render_template("prospector_results.html", rows=rows, errors=errors,
                           timed_out=timed_out,
                           job_id=job_id,
                           company_count=len(job.get("companies", [])),
                           skipped_poor_fit=job.get("skipped_poor_fit", 0))


@prospector.route("/flag", methods=["POST"])
def prospector_flag():
    data = request.get_json() or {}
    company_name = data.get("company_name", "").strip()
    job_id = data.get("job_id", "").strip()
    reason = data.get("reason", "").strip()
    if not company_name:
        return jsonify({"error": "company_name required"}), 400

    from datetime import datetime, timezone
    append_poor_fit_feedback({
        "company_name": company_name,
        "job_id": job_id,
        "reason": reason,
        "flagged_at": datetime.now(timezone.utc).isoformat(),
    })

    # Mark row as flagged in the stored job
    job = load_prospector_run(job_id)
    if job and company_name in job.get("results", {}):
        job["results"][company_name]["flagged_poor_fit"] = True
        save_prospector_run(job_id, job)

    return jsonify({"success": True})


@prospector.route("/export-csv/<job_id>")
def prospector_export_csv(job_id: str):
    job = load_prospector_run(job_id)
    if not job:
        return "Job not found", 404

    results = job.get("results", {})
    rows = sorted([r for r in results.values() if r and "error" not in r],
                  key=lambda r: r.get("composite_score", 0), reverse=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "#", "Company", "Website", "Top Product", "Skillable Path",
        "Lab Score", "Partnership Score", "Composite Score",
        "Highly Labable", "Likely Labable", "Not Labable",
        "ATP Program", "Channel Program", "On-Demand Library", "Cert Program", "Existing Lab Partner",
        "Top Contact", "Title", "LinkedIn",
        "2nd Contact", "2nd Title", "2nd LinkedIn",
        "Full Analysis URL", "Notes",
    ])
    for i, row in enumerate(rows, 1):
        aid = row.get("analysis_id", "")
        writer.writerow([
            i,
            row.get("company_name", ""),
            row.get("company_url", ""),
            row.get("top_product", ""),
            row.get("skillable_path", ""),
            row.get("lab_score", ""),
            row.get("partnership_score", ""),
            row.get("composite_score", ""),
            row.get("total_highly_labable", ""),
            row.get("total_likely_labable", ""),
            row.get("total_not_labable", ""),
            row.get("atp_program", ""),
            row.get("channel_program", ""),
            row.get("ondemand_library", ""),
            row.get("cert_program", ""),
            row.get("existing_lab_partner", ""),
            row.get("top_contact_name", ""),
            row.get("top_contact_title", ""),
            row.get("top_contact_linkedin", ""),
            row.get("second_contact_name", ""),
            row.get("second_contact_title", ""),
            row.get("second_contact_linkedin", ""),
            f"/inspector/results/{aid}" if aid else "",
            "",  # Notes — blank for user
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=prospector-{job_id}.csv"},
    )


@prospector.route("/export/<job_id>")
def prospector_export(job_id: str):
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    job = load_prospector_run(job_id)
    if not job:
        return "Job not found", 404

    results = job.get("results", {})
    rows = sorted([r for r in results.values() if r and "error" not in r],
                  key=lambda r: r.get("composite_score", 0), reverse=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prospector Results"

    # Color palette
    green_dark  = "FF0D1A14"
    green_hi    = "FF24ED9B"
    green_mid   = "FF6b9e88"
    amber       = "FFF59E0B"
    red_soft    = "FFF87171"
    white       = "FFE8F5F0"
    muted       = "FF3d6655"
    bg_header   = "FF06100C"

    header_font  = Font(bold=True, color=green_hi, size=9)
    default_font = Font(color=white, size=9)
    muted_font   = Font(color=muted, size=8)
    thin_side    = Side(style="thin", color="1E3329")
    thin_border  = Border(bottom=thin_side)

    headers = ["#", "Company", "Top Product", "Skillable Path",
               "Lab Score", "Partnership", "Composite",
               "Highly Labable Products", "Likely Labable Products", "Not Labable Products",
               "ATP Program", "Channel Program", "On-Demand Library", "Cert Program",
               "Existing Lab Partner",
               "Top Contact", "Title", "LinkedIn",
               "2nd Contact", "2nd Title", "2nd LinkedIn",
               "Full Analysis", "Notes"]
    col_widths = [4, 26, 28, 16, 11, 11, 11, 10, 10, 10, 26, 26, 14, 12, 18, 22, 24, 12, 20, 22, 12, 14, 30]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = PatternFill("solid", fgColor=bg_header)
        cell.alignment = Alignment(horizontal="center" if col in (1,5,6,7,10,11) else "left",
                                   vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.row_dimensions[1].height = 18
    ws.freeze_panes = "A2"

    path_colors = {"Labable": green_hi, "Simulations": amber, "Do Not Pursue": red_soft}

    for i, row in enumerate(rows, 2):
        lab   = row.get("lab_score", 0)
        prtn  = row.get("partnership_score", 0)
        comp  = row.get("composite_score", 0)
        path  = row.get("skillable_path", "")
        aid   = row.get("analysis_id", "")

        def score_color(s):
            return green_hi if s >= 70 else (amber if s >= 40 else red_soft)

        values = [
            row.get("rank", i - 1),
            row.get("company_name", ""),
            row.get("top_product", ""),
            path,
            lab, prtn, comp,
            row.get("total_highly_labable", ""),
            row.get("total_likely_labable", ""),
            row.get("total_not_labable", ""),
            row.get("atp_program", ""),
            row.get("channel_program", ""),
            row.get("ondemand_library", ""),
            row.get("cert_program", ""),
            row.get("existing_lab_partner", ""),
            row.get("top_contact_name", ""),
            row.get("top_contact_title", ""),
            row.get("top_contact_linkedin", ""),
            row.get("second_contact_name", ""),
            row.get("second_contact_title", ""),
            row.get("second_contact_linkedin", ""),
            f"/inspector/results/{aid}" if aid else "",
            "",  # Notes — blank for user to fill
        ]
        # Center columns: #(1), scores(5,6,7), product counts(8,9,10), ondemand(13), cert(14)
        center_cols = {1, 5, 6, 7, 8, 9, 10, 13, 14}
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=i, column=col, value=val)
            cell.fill = PatternFill("solid", fgColor="FF0D1A14")
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center",
                                       horizontal="center" if col in center_cols else "left")
            if col in (5, 6, 7):
                cell.font = Font(bold=True, color=score_color(val if isinstance(val, int) else 0), size=9)
            elif col == 4:
                cell.font = Font(bold=True, color=path_colors.get(path, white), size=9)
            elif col == 1:
                cell.font = Font(color=muted, size=9, bold=True)
            elif col in (8, 9, 10):
                cell.font = Font(color=green_mid, size=9)
            else:
                cell.font = default_font
        ws.row_dimensions[i].height = 16

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return Response(
        out.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=prospector-{job_id}.xlsx"},
    )


# ---------------------------------------------------------------------------
# Core analysis engine — shared by all Prospector run paths
# ---------------------------------------------------------------------------

_LABABLE_ORDER = {"highly_likely": 0, "likely": 1, "less_likely": 2, "not_likely": 3}

# Tech-related categories that indicate an academic institution has qualifying programs
_ACADEMIC_TECH_CATEGORIES = {
    "Computer Science", "Cybersecurity", "Cloud Computing", "Information Technology",
    "Engineering", "Data Science", "Software Engineering", "Network Engineering",
    "Academic Program", "Technology Platform",
}

# Contacts relevant for academic outreach (checked against title keywords)
_ACADEMIC_CONTACT_KEYWORDS = ("faculty", "curriculum", "dean", "professor", "chair",
                               "director", "ed tech", "edtech", "learning technology")


def _has_academic_tech_programs(discovery: dict) -> bool:
    """Return True if discovery shows CS/engineering/IT/cybersecurity programs."""
    academic_sigs = discovery.get("academic_signals") or {}
    tech_programs = academic_sigs.get("tech_program_areas") or []
    if tech_programs:
        return True
    # Fall back to checking product categories
    products = discovery.get("products") or []
    return any(p.get("category", "") in _ACADEMIC_TECH_CATEGORIES for p in products)


def _pick_academic_contact(contacts: list) -> dict | None:
    """Prefer Faculty / CDD / Dean contacts over generic decision_maker."""
    for kw in _ACADEMIC_CONTACT_KEYWORDS:
        match = next(
            (c for c in contacts if kw in (c.get("title") or "").lower()),
            None,
        )
        if match:
            return match
    return contacts[0] if contacts else None


def _quick_analyze_company(company_name: str, force_refresh: bool = False) -> dict | None:
    """Discovery + score for a single company (top 1 product) — Prospector mode.

    Skips research_products() entirely. Scoring runs from discovery context only,
    which eliminates ~9 Serper searches and ~3 page fetches per company.

    If a prior analysis exists and force_refresh is False, returns cached result
    without any web or Claude calls.

    Academic institutions receive different path labels, a pre-filter (liberal arts
    with no tech school = Not a Fit), and academic-appropriate contact selection.
    """
    # ── Cache lookup ────────────────────────────────────────────────────────
    if not force_refresh:
        cached = find_analysis_by_company_name(company_name)
        if cached:
            _attach_scores(cached)
            products = cached.get("products") or []
            top_product = products[0] if products else {}
            lab_score = top_product.get("_total_score", 0)
            pr_total = cached["_pr_total"]
            composite = cached["_composite_score"]

            org_type = cached.get("organization_type", "software_company")
            contacts = top_product.get("contacts") or []
            if org_type == "academic_institution":
                dm = _pick_academic_contact(contacts)
                dm2 = next((c for c in contacts if c != dm), None)
            else:
                dm = next((c for c in contacts if c.get("role_type") == "decision_maker"), None) or (contacts[0] if contacts else None)
                dm2 = next((c for c in contacts if c != dm and c.get("role_type") in ("influencer", "champion")), None) or next((c for c in contacts if c != dm), None)

            total_highly = sum(1 for p in products if p.get("_total_score", 0) >= 50)
            total_likely = sum(1 for p in products if 20 <= p.get("_total_score", 0) < 50)
            total_not = sum(1 for p in products if p.get("_total_score", 0) < 20)

            # Partnership signals — load from associated discovery if available
            ps = {}
            discovery_id = cached.get("discovery_id")
            if discovery_id:
                disc = load_discovery(discovery_id)
                if disc:
                    ps = disc.get("partnership_signals") or {}

            skillable_path = ""
            if org_type == "academic_institution":
                has_tech = bool(products)  # if we have stored products, assume tech programs present
                skillable_path = _derive_academic_path(lab_score, None, has_tech)

            return {
                "company_name": cached.get("company_name", company_name),
                "company_url": cached.get("company_url", ""),
                "top_product": top_product.get("name", ""),
                "lab_score": lab_score,
                "partnership_score": pr_total,
                "composite_score": composite,
                "skillable_path": skillable_path,
                "top_contact_name": dm.get("name", "") if dm else "",
                "top_contact_title": dm.get("title", "") if dm else "",
                "top_contact_linkedin": dm.get("linkedin_url", "") if dm else "",
                "second_contact_name": dm2.get("name", "") if dm2 else "",
                "second_contact_title": dm2.get("title", "") if dm2 else "",
                "second_contact_linkedin": dm2.get("linkedin_url", "") if dm2 else "",
                "analysis_id": cached.get("analysis_id", ""),
                "total_highly_labable": total_highly,
                "total_likely_labable": total_likely,
                "total_not_labable": total_not,
                "atp_program": ps.get("atp_program") or "",
                "channel_program": ps.get("channel_program") or "",
                "ondemand_library": _fmt_ondemand(ps.get("ondemand_library")),
                "cert_program": _fmt_cert(ps.get("cert_program")),
                "existing_lab_partner": ps.get("existing_lab_partner") or "",
                "_from_cache": True,
            }

    # ── Full research path ───────────────────────────────────────────────────
    try:
        findings = discover_products(company_name)
        discovery = discover_products_with_claude(findings)
        for key in ("training_programs", "atp_signals", "training_catalog",
                    "partner_ecosystem", "partner_portal", "cs_signals",
                    "lms_signals", "org_contacts", "page_contents"):
            discovery[key] = findings.get(key, [])

        org_type = discovery.get("organization_type", "software_company")

        # ── Academic pre-filter ──────────────────────────────────────────────
        if org_type == "academic_institution":
            has_tech = _has_academic_tech_programs(discovery)
            if not has_tech:
                # Liberal arts / no tech school — skip deep scoring
                return {
                    "company_name": discovery.get("company_name", company_name),
                    "company_url": discovery.get("company_url", ""),
                    "top_product": "",
                    "lab_score": 0,
                    "partnership_score": 0,
                    "composite_score": 0,
                    "skillable_path": "Not a Fit",
                    "top_contact_name": "",
                    "top_contact_title": "",
                    "top_contact_linkedin": "",
                    "analysis_id": "",
                    "total_highly_labable": 0,
                    "total_likely_labable": 0,
                    "total_not_labable": 0,
                    "atp_program": "",
                    "channel_program": "",
                    "ondemand_library": "",
                    "cert_program": "",
                    "existing_lab_partner": "",
                    "_academic_prefilter": True,
                }

        all_products = discovery.get("products", [])
        labable = [p for p in all_products if p.get("likely_labable") != "not_likely"]
        if not labable:
            labable = all_products
        labable.sort(key=lambda p: _LABABLE_ORDER.get(p.get("likely_labable", "not_likely"), 4))
        selected = labable[:1]
        if not selected:
            return None

        # Prospector mode: skip deep product research — score from discovery context only.
        # Eliminates ~9 Serper searches + 3 page fetches per company.
        research = {
            "company_name": company_name,
            "selected_products": selected,
            "search_results": {},
            "page_contents": {},
            "discovery_data": discovery,
        }
        analysis = score_selected_products(research)
        analysis_id = save_analysis(analysis)

        data = load_analysis(analysis_id)
        _attach_scores(data)
        products = data.get("products") or []
        top_product = products[0] if products else {}
        lab_score = top_product.get("_total_score", 0)
        pr_total = data["_pr_total"]
        composite = data["_composite_score"]

        contacts = top_product.get("contacts") or []
        if org_type == "academic_institution":
            dm = _pick_academic_contact(contacts)
            dm2 = next((c for c in contacts if c != dm), None)
        else:
            dm = next((c for c in contacts if c.get("role_type") == "decision_maker"), None) or (contacts[0] if contacts else None)
            dm2 = next((c for c in contacts if c != dm and c.get("role_type") in ("influencer", "champion")), None) or next((c for c in contacts if c != dm), None)

        # Product labability counts from discovery phase
        all_disc = discovery.get("products", [])
        total_highly  = sum(1 for p in all_disc if p.get("likely_labable") == "highly_likely")
        total_likely  = sum(1 for p in all_disc if p.get("likely_labable") == "likely")
        total_not     = sum(1 for p in all_disc if p.get("likely_labable") in ("less_likely", "not_likely"))

        # Partnership signals from discovery Claude output
        ps = discovery.get("partnership_signals") or {}

        # Academic path label — use school name from discovery if available
        skillable_path = ""
        if org_type == "academic_institution":
            academic_sigs = discovery.get("academic_signals") or {}
            school_name = academic_sigs.get("engineering_school_name")
            has_tech = _has_academic_tech_programs(discovery)
            skillable_path = _derive_academic_path(lab_score, school_name, has_tech)

        return {
            "company_name": data.get("company_name", company_name),
            "company_url": data.get("company_url", ""),
            "top_product": top_product.get("name", ""),
            "lab_score": lab_score,
            "partnership_score": pr_total,
            "composite_score": composite,
            "skillable_path": skillable_path,
            "top_contact_name": dm.get("name", "") if dm else "",
            "top_contact_title": dm.get("title", "") if dm else "",
            "top_contact_linkedin": dm.get("linkedin_url", "") if dm else "",
            "second_contact_name": dm2.get("name", "") if dm2 else "",
            "second_contact_title": dm2.get("title", "") if dm2 else "",
            "second_contact_linkedin": dm2.get("linkedin_url", "") if dm2 else "",
            "analysis_id": analysis_id,
            "total_highly_labable": total_highly,
            "total_likely_labable": total_likely,
            "total_not_labable": total_not,
            "atp_program": ps.get("atp_program") or "",
            "channel_program": ps.get("channel_program") or "",
            "ondemand_library": _fmt_ondemand(ps.get("ondemand_library")),
            "cert_program": _fmt_cert(ps.get("cert_program")),
            "existing_lab_partner": ps.get("existing_lab_partner") or "",
        }
    except Exception:
        log.exception("Quick analyze failed for %s", company_name)
        return None
