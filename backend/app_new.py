"""Flask application for the Skillable Intelligence Platform.

Routes for Inspector, Prospector, and Designer.
All routes use the new three-pillar data model and scoring framework.
Template filters use locked vocabulary (GP4).
"""

from __future__ import annotations

import logging
import os

from flask import Flask, render_template, request, redirect, url_for, jsonify

from config import ANTHROPIC_API_KEY
from core_new import (
    assign_verdict, company_classification_label, discovery_tier,
    DISCOVERY_TIER_LABELS, error_response, org_badge_color_group,
    score_products_and_sort,
)
from models_new import CompanyAnalysis, Product
from storage import Storage

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# App initialization
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "tools"),
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-in-production")

storage = Storage()


# ═══════════════════════════════════════════════════════════════════════════════
# Template Filters — locked vocabulary, GP4
# ═══════════════════════════════════════════════════════════════════════════════

@app.template_filter("score_color")
def score_color_filter(score: int) -> str:
    """Return CSS color class for a score value."""
    if score >= 80:
        return "dark-green"
    elif score >= 65:
        return "green"
    elif score >= 45:
        return "light-amber"
    elif score >= 25:
        return "amber"
    return "red"


@app.template_filter("tier_label")
def tier_label_filter(tier_key: str) -> str:
    """Convert discovery tier key to display label."""
    return DISCOVERY_TIER_LABELS.get(tier_key, tier_key)


@app.template_filter("tier_class")
def tier_class_filter(tier_key: str) -> str:
    """CSS class for discovery tier."""
    return {
        "seems_promising": "t-sp",
        "likely": "t-l",
        "uncertain": "t-u",
        "unlikely": "t-ul",
    }.get(tier_key, "")


@app.template_filter("badge_color_class")
def badge_color_class_filter(color: str) -> str:
    """Convert badge color to CSS class."""
    return {
        "green": "badge-green",
        "gray": "badge-gray",
        "amber": "badge-amber",
        "red": "badge-red",
    }.get(color, "badge-gray")


@app.template_filter("deployment_display")
def deployment_display_filter(model: str) -> str:
    """Convert deployment model data value to display label."""
    return {
        "installable": "Installable",
        "hybrid": "Hybrid",
        "cloud": "Cloud-Native",
        "saas-only": "SaaS-Only",
    }.get(model, model)


@app.template_filter("deployment_color")
def deployment_color_filter(model: str) -> str:
    """CSS class for deployment model badge."""
    return {
        "installable": "badge-deploy-green",
        "hybrid": "badge-deploy-gray",
        "cloud": "badge-deploy-green",
        "saas-only": "badge-deploy-amber",
    }.get(model, "")


@app.template_filter("org_color")
def org_color_filter(org_type: str) -> str:
    """CSS class for organization type badge."""
    group = org_badge_color_group(org_type)
    return {
        "purple": "org-purple",
        "teal": "org-teal",
        "warm_blue": "org-blue",
    }.get(group, "org-purple")


@app.template_filter("format_acv")
def format_acv_filter(value: float) -> str:
    """Format ACV value with lowercase k / uppercase M."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.0f}k"
    return f"${value:.0f}"


@app.template_filter("dim_caps")
def dim_caps_filter(name: str) -> str:
    """Convert dimension name to ALL CAPS for UX display."""
    return name.upper()


# ═══════════════════════════════════════════════════════════════════════════════
# Inspector Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
@app.route("/inspector")
def inspector_home():
    """Inspector home — search for a company."""
    return render_template("inspector/templates/home.html")


@app.route("/inspector/discover", methods=["POST"])
def inspector_discover():
    """Start discovery research for a company."""
    company_name = request.form.get("company_name", "").strip()
    product_name = request.form.get("product_name", "").strip()
    force_refresh = request.form.get("force_refresh") == "1"

    if not company_name and not product_name:
        return error_response("Please enter a company or product name.", 400)

    # TODO: Wire to intelligence.discover() when rebuilt
    # For now, redirect to discovering page with SSE
    return redirect(url_for("inspector_discovering",
                           company=company_name,
                           product=product_name,
                           refresh="1" if force_refresh else "0"))


@app.route("/inspector/discovering")
def inspector_discovering():
    """Discovery in progress — shows SSE progress."""
    company = request.args.get("company", "")
    return render_template("inspector/templates/discovering.html",
                          company_name=company)


@app.route("/inspector/product-selection/<discovery_id>")
def inspector_product_selection(discovery_id: str):
    """Product Selection page (was Caseboard) — choose products for Deep Dive."""
    discovery = storage.load_discovery(discovery_id)
    if not discovery:
        return error_response("Discovery not found.", 404)

    # Assign discovery tiers to products
    for p in discovery.get("products", []):
        p["_tier"] = discovery_tier(p.get("_discovery_score", 0))
        p["_tier_label"] = DISCOVERY_TIER_LABELS.get(p["_tier"], p["_tier"])

    # Company classification
    discovery["_company_badge"] = company_classification_label(
        discovery.get("organization_type", "software_company"),
        []  # Products not yet scored — use org type only
    )
    discovery["_org_color"] = org_badge_color_group(
        discovery.get("organization_type", "software_company")
    )

    return render_template("inspector/templates/product_selection.html",
                          discovery=discovery)


@app.route("/inspector/score", methods=["POST"])
def inspector_score():
    """Start Deep Dive scoring for selected products."""
    discovery_id = request.form.get("discovery_id", "")
    selected = request.form.getlist("products")

    if not selected:
        return error_response("No products selected.", 400)

    # TODO: Wire to intelligence.score() when rebuilt
    return redirect(url_for("inspector_scoring",
                           discovery_id=discovery_id,
                           products=",".join(selected)))


@app.route("/inspector/scoring")
def inspector_scoring():
    """Scoring in progress — shows SSE progress."""
    discovery_id = request.args.get("discovery_id", "")
    return render_template("inspector/templates/scoring.html",
                          discovery_id=discovery_id)


@app.route("/inspector/analysis/<analysis_id>")
def inspector_full_analysis(analysis_id: str):
    """Full Analysis page (was Dossier) — deep research results."""
    analysis = storage.load_analysis(analysis_id)
    if not analysis:
        return error_response("Analysis not found.", 404)

    # Sort products by Fit Score
    if isinstance(analysis, dict):
        # TODO: Convert dict to CompanyAnalysis when storage is rebuilt
        pass

    return render_template("inspector/templates/full_analysis.html",
                          analysis=analysis)


# ═══════════════════════════════════════════════════════════════════════════════
# Prospector Routes (placeholder — redesign pending)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/prospector")
def prospector_home():
    """Prospector home — upload CSV, paste list, or find lookalikes."""
    # TODO: Redesign from scratch per decision log
    return render_template("prospector/templates/prospector.html")


# ═══════════════════════════════════════════════════════════════════════════════
# Designer Routes (placeholder — Foundation Session pending)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/designer")
def designer_home():
    """Designer home — program list."""
    # TODO: Redesign after Designer Foundation Session
    return render_template("designer/templates/designer_home.html")


# ═══════════════════════════════════════════════════════════════════════════════
# API Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/health")
def api_health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "api_key_configured": bool(ANTHROPIC_API_KEY),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Startup
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5000)
