"""Skillable Intelligence — unified Flask backend for Inspector, Designer, Prospector."""

import csv
import io
import os
import re as _re
import time
import traceback
import uuid
import threading
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

import jinja2
from flask import Flask, Blueprint, render_template, request, jsonify, redirect, url_for, Response, stream_with_context
from markupsafe import Markup, escape as _escape
from researcher import discover_products, research_products, resolve_company_from_product
from scorer import discover_products_with_claude, score_selected_products
from storage import (
    save_analysis, load_analysis, list_analyses,
    save_discovery, load_discovery,
    save_batch_job, load_batch_job,
    find_analysis_by_discovery_id,
)
from models import compute_labability_total

# ---------------------------------------------------------------------------
# App setup — multi-tool template loader
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).parent
_TOOLS_DIR = _BACKEND_DIR.parent / "tools"
_STATIC_DIR = _BACKEND_DIR.parent / "static"

app = Flask(
    __name__,
    static_folder=str(_STATIC_DIR),
    static_url_path="/static",
    template_folder=str(_TOOLS_DIR / "inspector" / "templates"),  # default fallback
)

# Allow templates to be found across all three tool directories
app.jinja_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "inspector" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "designer" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "prospector" / "templates")),
])

# Custom Jinja2 tests not available in this version
app.jinja_env.tests['match'] = lambda value, pattern: bool(_re.match(pattern, str(value or '')))

# SSE stream timeout — abandon after this many seconds with no terminal message
_SSE_TIMEOUT = 600  # 10 minutes


# ---------------------------------------------------------------------------
# Template filters (registered on app, available in all blueprints)
# ---------------------------------------------------------------------------

@app.template_filter('bold_labels')
def bold_labels(text):
    """Convert **text** markdown to <strong>text</strong> HTML.
    Labels matching warning patterns render in red."""
    _WARNING_LABELS = {'Blockers', 'Blocker', 'Note', 'Warning', 'Risk', 'Limitation'}
    def _replace(m):
        label = m.group(1)
        # Check if the bold text starts with a known warning label (before the colon)
        colon_pos = label.find(':')
        first_word = (label[:colon_pos] if colon_pos != -1 else label).strip()
        if first_word in _WARNING_LABELS:
            if colon_pos != -1:
                # Only color the label word; leave the rest of the bold text normal
                return f'<strong><span style="color:#e05252;">{label[:colon_pos]}</span>{label[colon_pos:]}</strong>'
            return f'<strong style="color:#e05252;">{label}</strong>'
        return f'<strong>{label}</strong>'
    result = _re.sub(r'\*\*(.+?)\*\*', _replace, str(text))
    return Markup(result)


@app.template_filter('linkify')
def linkify(text):
    """Convert [label](url) markdown links to <a> HTML, then apply bold_labels."""
    result = str(text)
    result = _re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" class="rec-link">\1</a>',
        result,
    )
    result = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', result)
    return Markup(result)


@app.template_filter('link_product_name')
def link_product_name(text, name, url):
    """Wrap the first occurrence of the product name in a description with a link."""
    if not url or not name:
        return Markup(str(text))
    safe_text = str(_escape(text))
    safe_url = str(_escape(url))
    safe_name = str(_escape(name))
    linked = safe_text.replace(safe_name, f'<a href="{safe_url}" target="_blank" class="product-name-link">{safe_name}</a>', 1)
    return Markup(linked)


# ---------------------------------------------------------------------------
# In-memory progress store for SSE streaming
# ---------------------------------------------------------------------------

_progress: dict[str, list[str]] = {}
_progress_lock = threading.Lock()
_PROGRESS_MAX_JOBS = 50
_PROGRESS_EVICT_COUNT = 10


def _push(job_id: str, msg: str):
    with _progress_lock:
        if job_id not in _progress:
            if len(_progress) >= _PROGRESS_MAX_JOBS:
                for old_key in list(_progress.keys())[:_PROGRESS_EVICT_COUNT]:
                    del _progress[old_key]
            _progress[job_id] = []
        _progress[job_id].append(msg)


def _sse_stream(job_id: str, poll_interval: float = 0.3):
    """Generic SSE generator: yields messages for job_id until done/error or timeout."""
    last = 0
    deadline = time.time() + _SSE_TIMEOUT
    while time.time() < deadline:
        with _progress_lock:
            msgs = _progress.get(job_id, [])
        for msg in msgs[last:]:
            last += 1
            yield f"data: {msg}\n\n"
            if msg.startswith("done:") or msg.startswith("error:"):
                return
        time.sleep(poll_interval)
    yield "data: error:Timed out — the operation took too long. Please try again.\n\n"


# ---------------------------------------------------------------------------
# Composite score helper (single source of truth)
# ---------------------------------------------------------------------------

_CHANNEL_ORGS = {"training_organization", "systems_integrator", "technology_distributor", "professional_services"}


def _compute_composite(top_lab: int, pr_score: int, org_type: str) -> tuple[int, bool, str]:
    """Return (composite_score, is_gated, weights_label)."""
    if org_type in _CHANNEL_ORGS:
        raw = round(top_lab * 0.35 + pr_score * 0.65)
        gate_threshold, gate_cap = 20, 30
        weights = "35% Product / 65% Partnership"
    else:
        raw = round(top_lab * 0.65 + pr_score * 0.35)
        gate_threshold, gate_cap = 30, 25
        weights = "65% Product / 35% Partnership"

    if top_lab < gate_threshold:
        return min(raw, gate_cap), True, weights
    return min(100, raw), False, weights


# ---------------------------------------------------------------------------
# Platform landing page
# ---------------------------------------------------------------------------

@app.route("/")
def platform_home():
    recent = list_analyses()
    return render_template("home.html", recent=recent, platform_mode=True)


# ---------------------------------------------------------------------------
# Inspector Blueprint
# ---------------------------------------------------------------------------

inspector = Blueprint("inspector", __name__, url_prefix="/inspector")


@inspector.route("/")
@inspector.route("")
def home():
    recent = list_analyses()
    return render_template("home.html", recent=recent)


# Phase 1: Discovery

@inspector.route("/discover", methods=["POST"])
def discover():
    company_name = request.form.get("company_name", "").strip()
    product_name = request.form.get("product_name", "").strip()

    if not company_name and not product_name:
        return redirect(url_for("inspector.home"))

    if company_name and product_name:
        known_products = [product_name]
        search_label = f"{company_name} {product_name}"
    elif product_name and not company_name:
        company_name, known_products = resolve_company_from_product(product_name)
        search_label = product_name
    else:
        known_products = None
        search_label = company_name

    discovery_id = str(uuid.uuid4())[:8]

    def run_discovery():
        try:
            _push(discovery_id, "status:Searching for products...")
            findings = discover_products(company_name, known_products)
            _push(discovery_id, "status:Analyzing product portfolio...")
            discovery = discover_products_with_claude(findings)
            discovery["discovery_id"] = discovery_id
            discovery["known_products"] = known_products or []
            for key in ("training_programs", "atp_signals", "training_catalog",
                        "partner_ecosystem", "partner_portal", "cs_signals",
                        "lms_signals", "org_contacts", "page_contents"):
                discovery[key] = findings.get(key, [])
            save_discovery(discovery_id, discovery)
            _push(discovery_id, f"done:{discovery_id}")
        except Exception as e:
            traceback.print_exc()
            _push(discovery_id, f"error:{e}")

    threading.Thread(target=run_discovery, daemon=True).start()
    return render_template("discovering.html", discovery_id=discovery_id, search_label=search_label)


@inspector.route("/discover/progress/<discovery_id>")
def discover_progress(discovery_id: str):
    return Response(stream_with_context(_sse_stream(discovery_id)),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@inspector.route("/select/<discovery_id>")
def select_products(discovery_id: str):
    discovery = load_discovery(discovery_id)
    if not discovery:
        return redirect(url_for("inspector.home"))
    for i, p in enumerate(discovery.get("products", []), start=1):
        if not p.get("priority"):
            p["priority"] = i
    existing_analysis = find_analysis_by_discovery_id(discovery_id)
    return render_template("select.html", discovery=discovery, existing_analysis=existing_analysis)


# Phase 2: Scoring

@inspector.route("/score", methods=["POST"])
def score():
    discovery_id = request.form.get("discovery_id", "")
    discovery = load_discovery(discovery_id)
    if not discovery:
        return redirect(url_for("inspector.home"))

    selected_names = request.form.getlist("products")
    all_products = discovery.get("products", [])
    selected_products = [p for p in all_products if p["name"] in selected_names]

    if not selected_products:
        return redirect(url_for("inspector.select_products", discovery_id=discovery_id))

    job_id = str(uuid.uuid4())[:8]
    company_name = discovery.get("company_name", "")

    def run_scoring():
        try:
            # Check if research is fully cached for all selected products
            cache = discovery.get("_research_cache", {})
            cached_names = set(cache.get("researched_products", []))
            selected_names = {p["name"] for p in selected_products}

            if selected_names <= cached_names:
                # All selected products already researched — skip web searches
                _push(job_id, "status:Loading cached research data")
                research = {
                    "company_name": company_name,
                    "selected_products": selected_products,
                    "search_results": cache.get("search_results", {}),
                    "page_contents": cache.get("page_contents", {}),
                }
            else:
                research_messages = [
                    "status:Scouring technical docs, APIs & deployment guides",
                    "status:Finding training (ATP and gray) & certification programs",
                    "status:Researching product focus areas, AI features & target personas",
                    "status:Analyzing channel partners, enablement resources, roadshows & hands-on events",
                    "status:Identifying training and enablement organizational structures & contacts",
                ]
                def push_research_messages():
                    for i, msg in enumerate(research_messages):
                        _push(job_id, msg)
                        if i < len(research_messages) - 1:
                            threading.Event().wait(5)

                msg_thread = threading.Thread(target=push_research_messages, daemon=True)
                msg_thread.start()

                research = research_products(company_name, selected_products)
                msg_thread.join()

                # Save research to discovery cache for future re-runs
                merged_search = {**cache.get("search_results", {}), **research["search_results"]}
                merged_pages = {**cache.get("page_contents", {}), **research["page_contents"]}
                updated_discovery = {**discovery, "_research_cache": {
                    "researched_products": list(cached_names | selected_names),
                    "search_results": merged_search,
                    "page_contents": merged_pages,
                }}
                save_discovery(discovery_id, updated_discovery)

            research["discovery_data"] = discovery

            _push(job_id, "status:Scoring with Claude AI")
            analysis = score_selected_products(research)
            analysis.discovery_id = discovery_id
            analysis.total_products_discovered = len(discovery.get("products", []))
            analysis_id = save_analysis(analysis)
            _push(job_id, "status:Generating report")
            _push(job_id, f"done:{analysis_id}")
        except Exception as e:
            traceback.print_exc()
            _push(job_id, f"error:{e}")

    threading.Thread(target=run_scoring, daemon=True).start()
    return render_template("scoring.html", job_id=job_id, company_name=company_name,
                           product_count=len(selected_products))


@inspector.route("/score/progress/<job_id>")
def score_progress(job_id: str):
    return Response(stream_with_context(_sse_stream(job_id)),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# Results

@inspector.route("/results/<analysis_id>")
def results(analysis_id: str):
    data = load_analysis(analysis_id)
    if not data:
        return "Analysis not found", 404

    products = data.get("products") or []
    for p in products:
        scores = p.get("labability_score") or {}
        tech = scores.get("technical_orchestrability", {}).get("score", 0) if scores else 0
        other = sum(
            s.get("score", 0)
            for k, s in scores.items()
            if k != "technical_orchestrability" and isinstance(s, dict)
        ) if scores else 0
        p["_total_score"] = compute_labability_total(tech, other, p.get("skillable_path", ""))
    products.sort(key=lambda p: p.get("_total_score", 0), reverse=True)
    data["products"] = products

    pr = data.get("partnership_readiness") or {}
    pr_raw = sum(s.get("score", 0) for s in pr.values() if isinstance(s, dict))
    data["_pr_total"] = min(100, round(pr_raw / 1.17))

    org_type = data.get("organization_type", "software_company")
    top_lab = products[0].get("_total_score", 0) if products else 0
    composite, gated, weights = _compute_composite(top_lab, data["_pr_total"], org_type)
    data["_composite_score"] = composite
    data["_composite_gated"] = gated
    data["_composite_weights"] = weights or "65% Product / 35% Partnership"

    return render_template("results.html", data=data)


# CSV export

@inspector.route("/export/<analysis_id>")
def export(analysis_id: str):
    data = load_analysis(analysis_id)
    if not data:
        return "Analysis not found", 404

    products = data.get("products") or []
    for p in products:
        scores = p.get("labability_score") or {}
        tech = scores.get("technical_orchestrability", {}).get("score", 0) if scores else 0
        other = sum(s.get("score", 0) for k, s in scores.items()
                    if k != "technical_orchestrability" and isinstance(s, dict))
        p["_total_score"] = compute_labability_total(tech, other, p.get("skillable_path", ""))

    pr = data.get("partnership_readiness") or {}
    pr_raw = sum(s.get("score", 0) for s in pr.values() if isinstance(s, dict))
    pr_total = min(100, round(pr_raw / 1.17))

    output = io.StringIO()
    fieldnames = ["company_name", "product_name", "labability_score", "partnership_score",
                  "composite_score", "skillable_path", "org_type"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    _csv_defaults = {f: "" for f in fieldnames}
    writer.writeheader()
    org_type = data.get("organization_type", "software_company")
    for p in products:
        lab = p.get("_total_score", 0)
        composite, _, _ = _compute_composite(lab, pr_total, org_type)
        writer.writerow({**_csv_defaults,
                         "company_name": data.get("company_name", ""),
                         "product_name": p.get("name", ""),
                         "labability_score": lab,
                         "partnership_score": pr_total,
                         "composite_score": composite,
                         "skillable_path": p.get("skillable_path", ""),
                         "org_type": org_type})

    output.seek(0)
    safe_name = data.get("company_name", "analysis").replace(" ", "-").lower()
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inspector-{safe_name}-{analysis_id}.csv"},
    )


# API (batch mode)

@inspector.route("/api/analyze", methods=["POST"])
def api_analyze():
    body = request.get_json()
    company_name = body.get("company_name", "").strip()
    known_products = body.get("known_products")
    selected_product_names = body.get("products")

    if not company_name:
        return jsonify({"error": "company_name is required"}), 400

    try:
        findings = discover_products(company_name, known_products)
        discovery = discover_products_with_claude(findings)
        for key in ("training_programs", "atp_signals", "training_catalog",
                    "partner_ecosystem", "partner_portal", "cs_signals",
                    "lms_signals", "org_contacts", "page_contents"):
            discovery[key] = findings.get(key, [])

        if selected_product_names:
            selected = [p for p in discovery["products"] if p["name"] in selected_product_names]
        else:
            selected = discovery["products"]

        research = research_products(company_name, selected)
        research["discovery_data"] = discovery
        analysis = score_selected_products(research)
        analysis_id = save_analysis(analysis)
        return jsonify(load_analysis(analysis_id))
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Prospector Blueprint (stub — Phase 4)
# ---------------------------------------------------------------------------

prospector = Blueprint("prospector", __name__, url_prefix="/prospector")


@prospector.route("/")
@prospector.route("")
def prospector_home():
    return render_template("prospector.html")


# ---------------------------------------------------------------------------
# Designer Blueprint (stub — Phase 3)
# ---------------------------------------------------------------------------

designer = Blueprint("designer", __name__, url_prefix="/designer")


@designer.route("/")
@designer.route("")
def designer_home():
    return render_template("designer.html")


# ---------------------------------------------------------------------------
# Prospector batch (currently served under /inspector/marketing — kept for compat)
# Will move fully to /prospector in Phase 4
# ---------------------------------------------------------------------------

_LABABLE_ORDER = {"highly_likely": 0, "likely": 1, "less_likely": 2, "not_likely": 3}


def _quick_analyze_company(company_name: str) -> dict | None:
    """Run full discovery + score for a single company (top 1 product)."""
    try:
        findings = discover_products(company_name)
        discovery = discover_products_with_claude(findings)
        for key in ("training_programs", "atp_signals", "training_catalog",
                    "partner_ecosystem", "partner_portal", "cs_signals",
                    "lms_signals", "org_contacts", "page_contents"):
            discovery[key] = findings.get(key, [])

        all_products = discovery.get("products", [])
        labable = [p for p in all_products if p.get("likely_labable") != "not_likely"]
        if not labable:
            labable = all_products
        labable.sort(key=lambda p: _LABABLE_ORDER.get(p.get("likely_labable", "not_likely"), 4))
        selected = labable[:1]
        if not selected:
            return None

        research = research_products(company_name, selected)
        research["discovery_data"] = discovery
        analysis = score_selected_products(research)
        analysis_id = save_analysis(analysis)

        data = load_analysis(analysis_id)
        products = data.get("products") or []
        for p in products:
            scores = p.get("labability_score") or {}
            tech = scores.get("technical_orchestrability", {}).get("score", 0)
            other = sum(s.get("score", 0) for k, s in scores.items()
                        if k != "technical_orchestrability" and isinstance(s, dict))
            p["_total_score"] = compute_labability_total(tech, other, p.get("skillable_path", ""))
        products.sort(key=lambda p: p.get("_total_score", 0), reverse=True)

        pr = data.get("partnership_readiness") or {}
        pr_raw = sum(s.get("score", 0) for s in pr.values() if isinstance(s, dict))
        pr_total = min(100, round(pr_raw / 1.17))

        top_product = products[0] if products else {}
        lab_score = top_product.get("_total_score", 0)
        org_type = data.get("organization_type", "software_company")
        composite, _, _ = _compute_composite(lab_score, pr_total, org_type)

        contacts = top_product.get("contacts") or []
        dm = next((c for c in contacts if c.get("role_type") == "decision_maker"), None) or (contacts[0] if contacts else None)

        return {
            "company_name": data.get("company_name", company_name),
            "company_url": data.get("company_url", ""),
            "top_product": top_product.get("name", ""),
            "lab_score": lab_score,
            "partnership_score": pr_total,
            "composite_score": composite,
            "top_contact_name": dm.get("name", "") if dm else "",
            "top_contact_title": dm.get("title", "") if dm else "",
            "top_contact_linkedin": dm.get("linkedin_url", "") if dm else "",
            "analysis_id": analysis_id,
        }
    except Exception:
        traceback.print_exc()
        return None


@inspector.route("/marketing")
def marketing():
    return render_template("marketing.html")


@inspector.route("/marketing/run", methods=["POST"])
def marketing_run():
    raw = request.form.get("companies", "")
    company_names = [n.strip() for n in raw.replace(",", "\n").splitlines() if n.strip()]
    if not company_names:
        return redirect(url_for("inspector.marketing"))

    job_id = str(uuid.uuid4())[:8]
    save_batch_job(job_id, {"job_id": job_id, "companies": company_names, "results": {}, "status": "running"})

    def run_batch():
        results = {}
        semaphore = threading.Semaphore(3)

        def analyze_one(name):
            with semaphore:
                _push(job_id, f"status:Analyzing {name}...")
                row = _quick_analyze_company(name)
                results[name] = row or {"company_name": name, "error": "Analysis failed"}
                _push(job_id, f"progress:{name}")

        threads = [threading.Thread(target=analyze_one, args=(n,), daemon=True) for n in company_names]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        save_batch_job(job_id, {"job_id": job_id, "companies": company_names, "results": results, "status": "done"})
        _push(job_id, f"done:{job_id}")

    threading.Thread(target=run_batch, daemon=True).start()
    return render_template("marketing_running.html", job_id=job_id,
                           company_count=len(company_names))


@inspector.route("/marketing/status/<job_id>")
def marketing_status(job_id: str):
    return Response(stream_with_context(_sse_stream(job_id, poll_interval=0.5)),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@inspector.route("/marketing/results/<job_id>")
def marketing_results(job_id: str):
    job = load_batch_job(job_id)
    if not job:
        return redirect(url_for("inspector.marketing"))
    results = job.get("results", {})
    rows = [r for r in results.values() if r and "error" not in r]
    rows.sort(key=lambda r: r.get("composite_score", 0), reverse=True)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    errors = [r for r in results.values() if r and "error" in r]
    return render_template("marketing_results.html", rows=rows, errors=errors,
                           job_id=job_id, company_count=len(job.get("companies", [])))


@inspector.route("/marketing/export/<job_id>")
def marketing_export(job_id: str):
    job = load_batch_job(job_id)
    if not job:
        return "Job not found", 404
    results = job.get("results", {})
    rows = sorted([r for r in results.values() if r and "error" not in r],
                  key=lambda r: r.get("composite_score", 0), reverse=True)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "rank", "company_name", "company_url", "top_product",
        "lab_score", "partnership_score", "composite_score",
        "top_contact_name", "top_contact_title", "top_contact_linkedin", "analysis_id",
    ])
    _csv_defaults = {f: "" for f in writer.fieldnames}
    writer.writeheader()
    for i, r in enumerate(rows):
        writer.writerow({**_csv_defaults, **r, "rank": i + 1})

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=labability-batch-{job_id}.csv"},
    )


# Register all blueprints after all routes are defined
app.register_blueprint(inspector)
app.register_blueprint(prospector)
app.register_blueprint(designer)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n*** WARNING: ANTHROPIC_API_KEY not set. Set it in .env or environment. ***\n")
    app.run(debug=True, port=5000)
