"""Inspector blueprint — product discovery, scoring, and results.

Routes are thin surfaces: parse input → call Intelligence → render template.
All research, scoring, caching, and discrepancy logic lives in intelligence.py.
"""

import csv
import io
import threading
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, Response, stream_with_context, jsonify

from core import _push, _sse_stream, _poll_job, _attach_scores, _labable_tier
from researcher import resolve_company_from_product
from intelligence import (
    discover as intel_discover,
    score as intel_score,
    CACHE_TTL_DAYS,
    cache_is_fresh as _cache_is_fresh,
)
from datetime import datetime, timezone

from storage import (
    save_analysis, save_analysis_dict, load_analysis, list_analyses,
    save_discovery, load_discovery,
    find_analysis_by_discovery_id,
    find_analysis_by_company_name,
    find_discovery_by_company_name,
    load_all_discoveries,
    load_competitor_candidates,
)

import logging
log = logging.getLogger(__name__)

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
    force_refresh = request.form.get("force_refresh") == "1"

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

    if not force_refresh:
        # Discovery cache → always land on Caseboard, never skip directly to Dossier.
        # The existing analysis (if any) surfaces via the "View Previous →" button on
        # the Caseboard, letting the user decide whether to re-run or review the old one.
        cached_disc = find_discovery_by_company_name(company_name)
        if cached_disc and _cache_is_fresh(cached_disc.get("created_at", "")):
            disc_id = cached_disc.get("discovery_id", "")
            if disc_id:
                log.info("Inspector cache hit (discovery) for %s → %s", company_name, disc_id)
                return redirect(url_for("inspector.caseboard", discovery_id=disc_id))

    discovery_id = str(uuid.uuid4())[:8]

    def run_discovery():
        try:
            _push(discovery_id, "status:Searching for products...")
            # Intelligence handles research, Claude call, and storage
            discovery = intel_discover(company_name, known_products=known_products,
                                       force_refresh=force_refresh)
            # Restamp the ID we allocated so the SSE completion message matches
            # the discovery_id the progress page is polling on.
            # (intel_discover may have returned a cached record with a different ID —
            #  in that case the cached path above already redirected; we only reach
            #  here when a fresh discovery ran, so its ID matches what we allocated.)
            _push(discovery_id, "status:Analyzing product portfolio...")
            _push(discovery_id, f"done:{discovery['discovery_id']}")
        except Exception as e:
            log.exception("Discovery failed for %s", company_name)
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
    """Legacy redirect — /select was replaced by /caseboard."""
    return redirect(url_for("inspector.caseboard", discovery_id=discovery_id), 301)


@inspector.route("/caseboard/<discovery_id>")
def caseboard(discovery_id: str):
    """Caseboard — Seller Action Plan (Company Report).

    Shows the company's product portfolio in scored tiers. The seller or SE
    selects up to 3 products to carry forward into Dossier deep-dive scoring.
    UI label is "Seller Action Plan."
    """
    discovery = load_discovery(discovery_id)
    if not discovery:
        # Caller may have passed an analysis_id — look up the discovery_id from it
        analysis = load_analysis(discovery_id)
        if analysis and analysis.get("discovery_id"):
            return redirect(url_for("inspector.caseboard", discovery_id=analysis["discovery_id"]))
        return redirect(url_for("inspector.home"))

    # Tag each product with its per-product score cache status so the Caseboard
    # can compute Est. Research Time client-side without an extra server call.
    product_score_cache = discovery.get("_product_scores", {})
    for i, p in enumerate(discovery.get("products", []), start=1):
        if not p.get("priority"):
            p["priority"] = i
        cached_score = product_score_cache.get(p.get("name", ""))
        p["cached"] = bool(cached_score and _cache_is_fresh(cached_score.get("scored_at", "")))

    # Extract competitive_landscape from discovery for the right panel.
    # Source: partnership_signals.existing_lab_partner from Claude discovery response.
    partnership = discovery.get("partnership_signals") or {}
    existing_partner = partnership.get("existing_lab_partner")
    if isinstance(existing_partner, list):
        competitive_landscape = [{"name": c} for c in existing_partner if c]
    elif isinstance(existing_partner, str) and existing_partner.strip():
        competitive_landscape = [{"name": existing_partner.strip()}]
    else:
        competitive_landscape = []
    discovery["competitive_landscape"] = competitive_landscape

    existing_analysis = find_analysis_by_discovery_id(discovery_id)
    return render_template("caseboard.html", discovery=discovery, existing_analysis=existing_analysis)


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
    # Read form flags before the thread starts — request context is not thread-safe.
    force_refresh = request.form.get("force_refresh") == "1"

    def run_scoring():
        try:
            from researcher import research_products

            # ── Per-product score cache split ──────────────────────────────────
            # Products with a fresh cached score are served from cache; only
            # uncached products go through research + Claude scoring.
            product_score_cache = discovery.get("_product_scores", {})
            fresh_cached_products = []   # full scored product dicts, ready to use
            needs_scoring = []           # original discovery product dicts

            for p in selected_products:
                name = p.get("name", "")
                cached = product_score_cache.get(name)
                if not force_refresh and cached and _cache_is_fresh(cached.get("scored_at", "")):
                    fresh_cached_products.append(cached["product_data"])
                else:
                    needs_scoring.append(p)

            # ── Case A: all products are fresh from cache ──────────────────────
            if not needs_scoring:
                _push(job_id, "status:Loading cached scores")
                new_aid = str(uuid.uuid4())[:8]
                assembled = {
                    "analysis_id": new_aid,
                    "company_name": company_name,
                    "company_description": discovery.get("company_description", ""),
                    "organization_type": discovery.get("organization_type", "software_company"),
                    "company_url": discovery.get("company_url", ""),
                    "discovery_id": discovery_id,
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                    "total_products_discovered": len(discovery.get("products", [])),
                    "products": fresh_cached_products,
                }
                _attach_scores(assembled)
                save_analysis_dict(new_aid, assembled)
                _push(job_id, f"done:{new_aid}")
                return

            # ── Case B: some products need scoring ────────────────────────────
            # Research phase — only for products that need scoring.
            cache = discovery.get("_research_cache", {})
            cached_research_names = set(cache.get("researched_products", []))
            scoring_name_set = {p["name"] for p in needs_scoring}

            if scoring_name_set <= cached_research_names:
                _push(job_id, "status:Loading cached research data")
                research_cache = cache
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
                raw_research = research_products(company_name, needs_scoring)
                msg_thread.join()

                merged_search = {**cache.get("search_results", {}), **raw_research["search_results"]}
                merged_pages  = {**cache.get("page_contents", {}),  **raw_research["page_contents"]}
                research_cache = {
                    "researched_products": list(cached_research_names | scoring_name_set),
                    "search_results": merged_search,
                    "page_contents":  merged_pages,
                }
                updated_discovery = {**discovery, "_research_cache": research_cache}
                save_discovery(discovery_id, updated_discovery)

            _push(job_id, "status:Scoring with Claude AI")
            analysis_id, _ = intel_score(
                company_name, needs_scoring, discovery_id,
                discovery_data=discovery,
                research_cache=research_cache,
            )

            # If any products came from cache, inject them into the new analysis
            # and recompute the composite score across the full set.
            if fresh_cached_products:
                data = load_analysis(analysis_id)
                if data:
                    data["products"] = fresh_cached_products + (data.get("products") or [])
                    _attach_scores(data)
                    save_analysis_dict(analysis_id, data)

            # Persist newly scored products to the per-product score cache on the
            # discovery record so future Caseboard visits reflect the new cache state.
            _persist_product_scores(discovery_id, discovery, analysis_id)

            _push(job_id, "status:Generating report")
            _push(job_id, f"done:{analysis_id}")
        except Exception as e:
            log.exception("Scoring failed for %s", company_name)
            _push(job_id, f"error:{e}")

    threading.Thread(target=run_scoring, daemon=True).start()
    return render_template("scoring.html", job_id=job_id, company_name=company_name,
                           product_count=len(selected_products))


@inspector.route("/score/progress/<job_id>")
def score_progress(job_id: str):
    return Response(stream_with_context(_sse_stream(job_id)),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@inspector.route("/score/poll/<job_id>")
def score_poll(job_id: str):
    """Polling fallback for SSE — returns job status as JSON.
    Used by the scoring page when the SSE connection drops."""
    return jsonify(_poll_job(job_id))


# Results

@inspector.route("/results/<analysis_id>")
def results(analysis_id: str):
    """Legacy redirect — /results was replaced by /dossier."""
    return redirect(url_for("inspector.dossier", analysis_id=analysis_id), 301)


@inspector.route("/dossier/<analysis_id>")
def dossier(analysis_id: str):
    """Dossier — Seller & SE Action Plan (Solution Recommendations).

    Full per-product scoring breakdown for the SE, plus an at-a-glance Zone 1
    seller summary with verdict, ACV estimate, and data-driven next steps.
    Sellers and SEs use this output; program owners open Designer separately.
    UI label is "Seller & SE Action Plan."
    """
    data = load_analysis(analysis_id)
    if not data:
        return "Analysis not found", 404

    _attach_scores(data)
    from_cache = request.args.get("cached") == "1"

    # Load competitor candidates discovered while scoring this company
    company_name = data.get("company_name", "")
    all_candidates = load_competitor_candidates()
    competitor_list = [
        c for c in all_candidates
        if c.get("discovered_from_company", "").lower() == company_name.lower()
    ]
    competitors_logged = len(competitor_list)

    return render_template("dossier.html", data=data, from_cache=from_cache,
                           competitors_logged=competitors_logged,
                           competitor_list=competitor_list)


# Product detail page

@inspector.route("/results/<analysis_id>/product/<int:product_idx>")
def product_detail(analysis_id: str, product_idx: int):
    data = load_analysis(analysis_id)
    if not data:
        return "Analysis not found", 404

    _attach_scores(data)
    products = data.get("products") or []
    if product_idx < 0 or product_idx >= len(products):
        return "Product not found", 404

    product = products[product_idx]
    return render_template("product_detail.html", data=data, product=product, product_idx=product_idx, analysis_id=analysis_id)


# CSV export

@inspector.route("/export/<analysis_id>")
def export(analysis_id: str):
    data = load_analysis(analysis_id)
    if not data:
        return "Analysis not found", 404

    _attach_scores(data)
    products = data.get("products") or []

    output = io.StringIO()
    fieldnames = ["company_name", "product_name", "composite_score", "orchestration_method", "org_type"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    _csv_defaults = {f: "" for f in fieldnames}
    writer.writeheader()
    org_type = data.get("organization_type", "software_company")
    for p in products:
        writer.writerow({**_csv_defaults,
                         "company_name": data.get("company_name", ""),
                         "product_name": p.get("name", ""),
                         "composite_score": p.get("_total_score", 0),
                         "orchestration_method": p.get("orchestration_method") or p.get("skillable_path", ""),
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
        from researcher import research_products

        discovery = intel_discover(company_name, known_products=known_products, force_refresh=True)

        if selected_product_names:
            selected = [p for p in discovery["products"] if p["name"] in selected_product_names]
        else:
            selected = discovery["products"]

        raw_research = research_products(company_name, selected)
        research_cache = {
            "search_results": raw_research.get("search_results", {}),
            "page_contents":  raw_research.get("page_contents", {}),
        }
        analysis_id, data = intel_score(
            company_name, selected, discovery["discovery_id"],
            discovery_data=discovery, research_cache=research_cache,
        )
        return jsonify(load_analysis(analysis_id))
    except Exception as exc:
        log.exception("API analyze failed for %s", company_name)
        return jsonify({"error": str(exc)}), 500


# Top Blockers

@inspector.route("/blockers")
def blockers():
    """Scan all stored Inspector data and surface products that can't be labified, grouped by reason."""
    from collections import defaultdict
    from models import compute_product_score

    blocker_rows: list[dict] = []
    seen_keys: set[str] = set()  # deduplicate by (source_id, product_name)

    # --- Pass 1: scan discoveries ---
    all_discoveries = load_all_discoveries()
    for disc in all_discoveries:
        company_name = disc.get("company_name", "")
        source_id = disc.get("discovery_id", "")
        analyzed_at = disc.get("created_at", "")
        products = disc.get("products") or []

        for product in products:
            p_name = product.get("name", "")
            labable = product.get("likely_labable", "")
            flags = product.get("poor_match_flags") or []
            dedup_key = f"disc:{source_id}:{p_name}"

            if flags:
                for flag in flags:
                    if flag:
                        seen_keys.add(dedup_key)
                        blocker_rows.append({
                            "company_name": company_name,
                            "product_name": p_name,
                            "blocker_type": flag,
                            "likely_labable": labable,
                            "tech_score": None,
                            "source_id": source_id,
                            "source_type": "discovery",
                            "analyzed_at": analyzed_at,
                        })
            elif labable in ("not_likely", "less_likely"):
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    blocker_rows.append({
                        "company_name": company_name,
                        "product_name": p_name,
                        "blocker_type": "Unclassified low fit",
                        "likely_labable": labable,
                        "tech_score": None,
                        "source_id": source_id,
                        "source_type": "discovery",
                        "analyzed_at": analyzed_at,
                    })

    # --- Pass 2: scan analyses for low tech_orchestrability ---
    analyses = list_analyses()
    for summary in analyses:
        aid = summary.get("analysis_id", "")
        data = load_analysis(aid)
        if not data:
            continue
        company_name = data.get("company_name", "")
        analyzed_at = data.get("analyzed_at", "")
        products = data.get("products") or []

        for product in products:
            p_name = product.get("name", "")
            flags = product.get("poor_match_flags") or []
            tech_score = None

            # Extract product_labability score from dimension scores
            dims = product.get("dimension_scores") or {}
            if isinstance(dims, dict):
                tech_score = dims.get("product_labability")
            if tech_score is None:
                # Fallback: check labability_score nested structure (primary storage location)
                labability = product.get("labability_score") or {}
                pl = labability.get("product_labability") or {}
                if isinstance(pl, dict):
                    tech_score = pl.get("score")

            dedup_key = f"analysis:{aid}:{p_name}"
            disc_dedup_key = f"disc:{data.get('discovery_id', '')}:{p_name}"

            if flags:
                for flag in flags:
                    if flag and dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        blocker_rows.append({
                            "company_name": company_name,
                            "product_name": p_name,
                            "blocker_type": flag,
                            "likely_labable": _labable_tier(product),
                            "tech_score": tech_score,
                            "source_id": aid,
                            "source_type": "analysis",
                            "analyzed_at": analyzed_at,
                        })
            elif tech_score is not None and tech_score < 20:
                if dedup_key not in seen_keys and disc_dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    blocker_rows.append({
                        "company_name": company_name,
                        "product_name": p_name,
                        "blocker_type": "Low Product Labability score",
                        "likely_labable": _labable_tier(product),
                        "tech_score": tech_score,
                        "source_id": aid,
                        "source_type": "analysis",
                        "analyzed_at": analyzed_at,
                    })

    # --- Group by blocker_type, sorted by frequency ---
    frequency: dict[str, int] = defaultdict(int)
    for row in blocker_rows:
        frequency[row["blocker_type"]] += 1

    # Sort: "Unclassified low fit" always last; others by frequency desc
    def sort_key(bt):
        if bt == "Unclassified low fit":
            return (1, 0)
        return (0, -frequency[bt])

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in blocker_rows:
        grouped[row["blocker_type"]].append(row)

    ordered_types = sorted(grouped.keys(), key=sort_key)
    blocker_groups = [
        {
            "blocker_type": bt,
            "count": len(grouped[bt]),
            "rows": grouped[bt],
        }
        for bt in ordered_types
    ]

    total_companies = len({r["company_name"] for r in blocker_rows})
    total_products = len(blocker_rows)
    distinct_types = len([bt for bt in ordered_types if bt != "Unclassified low fit"])

    return render_template(
        "blockers.html",
        blocker_groups=blocker_groups,
        total_companies=total_companies,
        total_products=total_products,
        distinct_types=distinct_types,
    )


def _persist_product_scores(discovery_id: str, discovery: dict, analysis_id: str) -> None:
    """Write newly scored product data back to the per-product score cache on the
    discovery record so subsequent Caseboard renders can tag products as cached."""
    data = load_analysis(analysis_id)
    if not data:
        return
    # Reload from storage to preserve _research_cache written during the score run.
    # Using the in-memory `discovery` snapshot would overwrite any saves that happened
    # during scoring (e.g. the _research_cache update on line 256).
    current = load_discovery(discovery_id) or discovery
    now = datetime.now(timezone.utc).isoformat()
    product_scores = dict(current.get("_product_scores", {}))
    for p in data.get("products", []):
        name = p.get("name", "")
        if name:
            product_scores[name] = {"scored_at": now, "product_data": p}
    updated = {**current, "_product_scores": product_scores}
    save_discovery(discovery_id, updated)



