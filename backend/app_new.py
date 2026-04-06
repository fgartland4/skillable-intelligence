"""Flask application for the Skillable Intelligence Platform.

Routes for Inspector, Prospector, and Designer.
All routes use the new three-pillar data model and scoring framework.
Template filters use locked vocabulary (GP4).
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from pathlib import Path

import jinja2
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, stream_with_context

from config_new import ANTHROPIC_API_KEY, validate_startup
from core_new import (
    assign_verdict, company_classification_label, discovery_tier,
    DISCOVERY_TIER_LABELS, error_response, org_badge_color_group,
    score_products_and_sort, push, sse_stream, poll_job,
)
from intelligence_new import discover, score, qualify, lookup, cache_is_fresh
from models_new import CompanyAnalysis, Product
from storage import (
    load_analysis, load_discovery,
    find_discovery_by_company_name, find_analysis_by_discovery_id,
    list_analyses,
)

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# App initialization
# ═══════════════════════════════════════════════════════════════════════════════

_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = Flask(
    __name__,
    static_folder=str(_STATIC_DIR),
    static_url_path="/static",
    template_folder=str(_TOOLS_DIR / "inspector" / "templates"),
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-in-production")

# Search all tool template directories — includes work across tools
app.jinja_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "shared" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "inspector" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "designer" / "templates")),
    jinja2.FileSystemLoader(str(_TOOLS_DIR / "prospector" / "templates")),
])

# Validate config, scoring_config, and prompt generation on startup
validate_startup()


# ═══════════════════════════════════════════════════════════════════════════════
# Template Filters — locked vocabulary, GP4
# ═══════════════════════════════════════════════════════════════════════════════

@app.template_filter("score_color")
def score_color_filter(score: int) -> str:
    if score >= 80: return "score-dark-green"
    elif score >= 65: return "score-green"
    elif score >= 45: return "score-light-amber"
    elif score >= 25: return "score-amber"
    return "score-red"


@app.template_filter("tier_label")
def tier_label_filter(tier_key: str) -> str:
    return DISCOVERY_TIER_LABELS.get(tier_key, tier_key)


@app.template_filter("tier_class")
def tier_class_filter(tier_key: str) -> str:
    return {"seems_promising": "t-sp", "likely": "t-l", "uncertain": "t-u", "unlikely": "t-ul"}.get(tier_key, "")


@app.template_filter("badge_color_class")
def badge_color_class_filter(color: str) -> str:
    return {"green": "badge-green", "gray": "badge-gray", "amber": "badge-amber", "red": "badge-red"}.get(color, "badge-gray")


@app.template_filter("deployment_display")
def deployment_display_filter(model: str) -> str:
    return {"installable": "Installable", "hybrid": "Hybrid", "cloud": "Cloud-Native", "saas-only": "SaaS-Only"}.get(model, model)


@app.template_filter("deployment_color")
def deployment_color_filter(model: str) -> str:
    return {"installable": "badge-deploy-green", "hybrid": "badge-deploy-gray", "cloud": "badge-deploy-green", "saas-only": "badge-deploy-amber"}.get(model, "")


@app.template_filter("org_color")
def org_color_filter(org_type: str) -> str:
    group = org_badge_color_group(org_type)
    return {"purple": "org-purple", "teal": "org-teal", "warm_blue": "org-blue"}.get(group, "org-purple")


@app.template_filter("format_acv")
def format_acv_filter(value) -> str:
    value = float(value or 0)
    if value >= 1_000_000: return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000: return f"${value / 1_000:.0f}k"
    return f"${value:.0f}"


@app.template_filter("dim_caps")
def dim_caps_filter(name: str) -> str:
    return name.upper()


# ═══════════════════════════════════════════════════════════════════════════════
# Inspector Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
@app.route("/inspector")
def inspector_home():
    """Inspector home — search for a company."""
    return render_template("home_new.html")


@app.route("/inspector/discover", methods=["POST"])
def inspector_discover():
    """Start discovery research for a company."""
    company_name = request.form.get("company_name", "").strip()
    product_name = request.form.get("product_name", "").strip()
    force_refresh = request.form.get("force_refresh") == "1"

    if not company_name and not product_name:
        return error_response("Please enter a company or product name.", 400)

    known_products = [product_name] if product_name else None

    # Check cache first
    if not force_refresh:
        cached = find_discovery_by_company_name(company_name)
        if cached and cache_is_fresh(cached.get("created_at", "")):
            disc_id = cached.get("discovery_id", "")
            if disc_id:
                return redirect(url_for("inspector_product_selection", discovery_id=disc_id))

    # Start discovery in background thread, stream progress via SSE
    job_id = str(uuid.uuid4())[:8]

    def run_discovery():
        try:
            push(job_id, "status:Searching for products...")
            result = discover(company_name, known_products=known_products, force_refresh=force_refresh)
            push(job_id, "status:Analyzing product portfolio...")
            push(job_id, f"done:{result['discovery_id']}")
        except Exception as e:
            log.exception("Discovery failed for %s", company_name)
            push(job_id, f"error:{e}")

    threading.Thread(target=run_discovery, daemon=True).start()

    return render_template("discovering.html",
                          discovery_id=job_id,
                          search_label=company_name)


@app.route("/inspector/discover/progress/<job_id>")
def discover_progress(job_id: str):
    """SSE stream for discovery progress."""
    return Response(stream_with_context(sse_stream(job_id)),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/inspector/product-selection/<discovery_id>")
def inspector_product_selection(discovery_id: str):
    """Product Selection page — choose products for Deep Dive."""
    disc = load_discovery(discovery_id)
    if not disc:
        return error_response("Discovery not found.", 404)

    # Assign discovery tiers
    for p in disc.get("products", []):
        score_val = p.get("_discovery_score", 0)
        p["_tier"] = discovery_tier(score_val)
        p["_tier_label"] = DISCOVERY_TIER_LABELS.get(p["_tier"], p["_tier"])

    # Company classification
    disc["_company_badge"] = company_classification_label(
        disc.get("organization_type", "software_company"), []
    )
    disc["_org_color"] = org_badge_color_group(
        disc.get("organization_type", "software_company")
    )

    # Check for existing analysis
    existing = find_analysis_by_discovery_id(discovery_id)

    return render_template("product_selection.html",
                          discovery=disc, existing_analysis=existing)


@app.route("/inspector/score", methods=["POST"])
def inspector_score():
    """Start Deep Dive scoring for selected products."""
    discovery_id = request.form.get("discovery_id", "")
    selected_names = request.form.getlist("products")

    if not selected_names:
        return error_response("No products selected.", 400)

    disc = load_discovery(discovery_id)
    if not disc:
        return error_response("Discovery not found.", 404)

    # Build selected product list from discovery data
    all_products = disc.get("products", [])
    selected = [p for p in all_products if p.get("name") in selected_names]

    job_id = str(uuid.uuid4())[:8]

    def run_scoring():
        try:
            push(job_id, f"status:Scoring {len(selected)} products...")
            for i, p in enumerate(selected):
                push(job_id, f"status:Researching {p.get('name', '')} ({i+1}/{len(selected)})...")
            analysis_id, analysis = score(
                disc.get("company_name", ""),
                selected, discovery_id,
                discovery_data=disc,
            )
            push(job_id, f"done:{analysis_id}")
        except Exception as e:
            log.exception("Scoring failed")
            push(job_id, f"error:{e}")

    threading.Thread(target=run_scoring, daemon=True).start()

    return render_template("scoring.html",
                          job_id=job_id,
                          company_name=disc.get("company_name", ""),
                          product_count=len(selected))


@app.route("/inspector/score/progress/<job_id>")
def score_progress(job_id: str):
    """SSE stream for scoring progress."""
    return Response(stream_with_context(sse_stream(job_id)),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/inspector/score/status/<job_id>")
def score_status(job_id: str):
    """Polling fallback for SSE."""
    return jsonify(poll_job(job_id))


@app.route("/inspector/analysis/<analysis_id>")
def inspector_full_analysis(analysis_id: str):
    """Full Analysis page — deep research results."""
    analysis = load_analysis(analysis_id)
    if not analysis:
        return error_response("Analysis not found.", 404)

    return render_template("full_analysis.html",
                          analysis=analysis)


# ═══════════════════════════════════════════════════════════════════════════════
# Prospector Routes (placeholder — redesign pending)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/prospector")
def prospector_home():
    return render_template("prospector.html")


# ═══════════════════════════════════════════════════════════════════════════════
# Designer Routes (placeholder — Foundation Session pending)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/designer")
def designer_home():
    return render_template("designer_home.html")


# ═══════════════════════════════════════════════════════════════════════════════
# API Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "api_key_configured": bool(ANTHROPIC_API_KEY)})


# ═══════════════════════════════════════════════════════════════════════════════
# Startup
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5000)
