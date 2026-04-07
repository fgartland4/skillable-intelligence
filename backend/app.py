"""Flask application for the Skillable Intelligence Platform.

Routes for Inspector, Prospector, and Designer.
All routes use the new three-pillar data model and scoring framework.
Template filters use locked vocabulary (GP4).
"""

from __future__ import annotations

import logging
import os
import re
import threading
import uuid
from pathlib import Path

import jinja2
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, stream_with_context

from config import ANTHROPIC_API_KEY, validate_startup
from core import (
    assign_verdict, company_classification_label, discovery_tier,
    DISCOVERY_TIER_LABELS, error_response, org_badge_color_group,
    score_products_and_sort, push, sse_stream, poll_job,
)
from intelligence import discover, score, qualify, lookup, cache_is_fresh, generate_briefcase_for_analysis
from models import CompanyAnalysis, Product
from storage import (
    load_analysis, load_discovery,
    find_discovery_by_company_name, find_analysis_by_discovery_id,
    list_analyses,
)

import sys
# Configure logging for ALL processes (parent + reloader child)
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logging.getLogger("werkzeug").setLevel(logging.INFO)

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
    """Score color CSS class — reads thresholds from config (Define-Once)."""
    from backend import scoring_config as cfg
    for color, threshold in sorted(cfg.SCORE_THRESHOLDS.items(),
                                    key=lambda x: x[1], reverse=True):
        if score >= threshold:
            return f"score-{color.replace('_', '-')}"
    return "score-red"


@app.template_filter("tier_label")
def tier_label_filter(tier_key: str) -> str:
    return DISCOVERY_TIER_LABELS.get(tier_key, tier_key)


@app.template_filter("tier_class")
def tier_class_filter(tier_key: str) -> str:
    import scoring_config as cfg
    return cfg.TIER_CSS_CLASSES.get(tier_key, "")


@app.template_filter("badge_color_class")
def badge_color_class_filter(color: str) -> str:
    """Map a badge color to its CSS class.

    The CSS class name is derived from the color name itself
    (`badge-{color}`). Validity is checked against the canonical
    color list in `cfg.BADGE_COLOR_POINTS` so the function works
    automatically if a new color is ever added to the config.
    """
    import scoring_config as cfg
    if color in cfg.BADGE_COLOR_POINTS:
        return f"badge-{color}"
    return "badge-gray"


@app.template_filter("deployment_display")
def deployment_display_filter(model: str) -> str:
    """Return the display label for a deployment model key.

    Reads from `cfg.DEPLOYMENT_MODELS` (Define-Once). Falls back to
    the raw model key if the value is unknown.
    """
    import scoring_config as cfg
    entry = cfg.DEPLOYMENT_MODELS.get(model)
    if isinstance(entry, dict):
        return entry.get("display", model)
    return model


@app.template_filter("deployment_color")
def deployment_color_filter(model: str) -> str:
    import scoring_config as cfg
    return cfg.DEPLOYMENT_MODEL_BADGE_CLASSES.get(model, "")


@app.template_filter("org_color")
def org_color_filter(org_type: str) -> str:
    group = org_badge_color_group(org_type)
    return {"purple": "org-purple", "teal": "org-teal", "warm_blue": "org-blue"}.get(group, "org-purple")


@app.template_filter("format_acv")
def format_acv_filter(value) -> str:
    """Format a dollar value with $1k / $1M abbreviations."""
    value = float(value or 0)
    if value >= 1_000_000: return f"${value / 1_000_000:.1f}M"  # magic-allowed: standard money formatting (millions)
    elif value >= 1_000: return f"${value / 1_000:.0f}k"  # magic-allowed: standard money formatting (thousands)
    return f"${value:.0f}"


@app.template_filter("dim_caps")
def dim_caps_filter(name: str) -> str:
    """Uppercase a dimension name and put each word on its own line.

    Two-word names ("Lab Access", "Product Complexity") render as two lines
    so the dim-name column stays narrow and bars align across all dimensions.
    Returns a Markup-safe string with <br> tags between words.
    """
    from markupsafe import Markup
    if not name:
        return Markup("")
    parts = name.upper().split()
    return Markup("<br>".join(parts))


@app.template_filter("clean_subcategory")
def clean_subcategory_filter(value: str) -> str:
    """Strip AI-generated subcategory concatenation down to one clean label.

    The AI sometimes returns subcategories like "Endpoint, Network, Data &
    Email Security / XDR Platform". We want a single clean subcategory like
    "XDR Platform" or "Endpoint Protection". Take the part after the last
    "/" if present, otherwise the part before the first ",".
    """
    if not value:
        return ""
    # Prefer the last segment after "/" — usually the more specific label
    if "/" in value:
        value = value.rsplit("/", 1)[-1]
    # Drop everything after the first comma (it's the AI listing siblings)
    if "," in value:
        value = value.split(",", 1)[0]
    return value.strip()


@app.template_filter("inline_md")
def inline_md_filter(value: str):
    """Render the inline markdown subset (bold, italic) to HTML.

    Used for evidence bullets where the AI emits `**Label | Strength:**`
    style markup that should render as bold green text per the wireframe
    pattern. The full markdown library is overkill — we only need bold
    and italic, and we want safe HTML escaping for everything else.
    """
    import re
    from markupsafe import Markup, escape
    if not value:
        return Markup("")
    # First escape any pre-existing HTML so it can't break out
    safe = str(escape(value))
    # Bold: **text** → <strong>text</strong>
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    # Italic: *text* or _text_ → <em>text</em>
    # (but only when not adjacent to other asterisks/underscores to avoid
    # eating bold markers we already converted)
    safe = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", safe)
    safe = re.sub(r"(?<!_)_([^_\n]+?)_(?!_)", r"<em>\1</em>", safe)
    return Markup(safe)


@app.template_filter("bold_label")
def bold_label_filter(value: str):
    """Wrap the part before the first em-dash in <strong> tags.

    Briefcase bullets come from the AI as 'Label — Description'. The wireframe
    bolds the label (in the green strong color from CSS). This filter splits on
    the first em-dash (or " - " hyphen) and bolds the leading label.
    """
    from markupsafe import Markup, escape
    if not value:
        return Markup("")
    # Try em-dash first, then hyphen with spaces, then colon
    for sep in ["\u2014", " - ", ":"]:
        if sep in value:
            label, rest = value.split(sep, 1)
            return Markup(f"<strong>{escape(label.strip())}</strong>{sep}{escape(rest)}")
    return escape(value)


@app.template_filter("format_analyzed_date")
def format_analyzed_date_filter(value) -> str:
    """Format an ISO timestamp like '2026-04-05T22:46:00' as 'April 5, 2026'."""
    if not value:
        return ""
    try:
        from datetime import datetime
        if isinstance(value, str):
            # Strip timezone if present
            v = value.replace("Z", "")
            dt = datetime.fromisoformat(v.split("+")[0])
        else:
            dt = value
        return dt.strftime("%B %-d, %Y") if hasattr(dt, "strftime") else str(value)
    except Exception:
        try:
            # Windows doesn't support %-d, fall back to %#d
            return dt.strftime("%B %#d, %Y")
        except Exception:
            return str(value)


# ═══════════════════════════════════════════════════════════════════════════════
# Inspector Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
@app.route("/inspector")
def inspector_home():
    """Inspector home — search for a company."""
    return render_template("home.html")


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
                          company_name=company_name)


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

    # Enrich the discovery with tier / badge / color fields. Idempotent —
    # only sets fields that aren't already there. discover() also calls this
    # at creation, so cached discoveries already have the fields. This call
    # exists to backfill any older cached discovery that pre-dates the
    # shared enrichment helper. See HIGH-1 in code-review-2026-04-07.md.
    from intelligence import enrich_discovery
    enrich_discovery(disc)

    import scoring_config as cfg

    # ── Product Family Picker ────────────────────────────────────────────────
    # When a discovery returns 20+ non-TC products AND the website nav scrape
    # produced multiple families, surface a family picker so the user can
    # narrow the scope before selecting products for Deep Dive. The modal
    # markup already lives in the template — this just builds the data and
    # the show_family_picker flag, plus filters when the user has chosen.
    show_family_picker = False
    non_tc = [p for p in disc.get("products", [])
              if p.get("category") != "Training & Certification"]
    selected_families = request.args.getlist("family")

    if selected_families:
        # User picked one or more families — filter products to matches.
        # Training & Certification products always come along regardless.
        families_lower = {f.lower() for f in selected_families}
        disc["products"] = [
            p for p in disc.get("products", [])
            if p.get("category", "").lower() in families_lower
            or any(fl in p.get("name", "").lower() for fl in families_lower)
            or any(fl in p.get("subcategory", "").lower() for fl in families_lower)
            or p.get("category") == "Training & Certification"
        ]
        disc["_selected_families"] = selected_families
    elif len(non_tc) >= cfg.PRODUCT_FAMILY_PICKER_THRESHOLD:
        # Show the family picker — prefer scraped families from website nav
        # (vendor's own organization), fall back to category-based grouping.
        scraped = disc.get("_scraped_families") or []
        families = []
        if scraped:
            for fam in scraped:
                fam_lower = fam["name"].lower()
                fam["product_count"] = sum(
                    1 for p in non_tc
                    if fam_lower in p.get("name", "").lower()
                    or fam_lower in p.get("category", "").lower()
                    or fam_lower in p.get("subcategory", "").lower()
                )
            families = sorted(scraped,
                              key=lambda f: f.get("product_count", 0),
                              reverse=True)
        else:
            # Fallback: group by category
            family_counts: dict[str, int] = {}
            for p in non_tc:
                cat = p.get("category", "Other")
                family_counts[cat] = family_counts.get(cat, 0) + 1
            families = sorted(
                [{"name": c, "product_count": n} for c, n in family_counts.items()],
                key=lambda f: f["product_count"], reverse=True
            )

        # Only show the picker when there are multiple families to choose
        # from — one family is no choice at all.
        if len(families) > 1:
            disc["product_families"] = families
            show_family_picker = True

    # Check for existing analysis
    existing = find_analysis_by_discovery_id(discovery_id)

    # Build the set of cached product names so the Product Selection page can
    # pre-select them with a visual chip indicator. The user can deselect or
    # add more products before clicking Deep Dive — the score() path is
    # cache-and-append, so cached products are re-used and only NEW selections
    # actually trigger fresh scoring.
    cached_product_names: set[str] = set()
    if existing:
        for p in existing.get("products", []) or []:
            n = (p.get("name") or "").strip()
            if n:
                cached_product_names.add(n)

    return render_template("product_selection.html",
                          discovery=disc,
                          existing_analysis=existing,
                          cached_product_names=cached_product_names,
                          deep_dive_max_new=cfg.DEEP_DIVE_MAX_NEW_PRODUCTS,
                          show_family_picker=show_family_picker)


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

    # Capture which products the user selected — used for "default product to display"
    selected_set = set(selected_names)

    def run_scoring():
        try:
            push(job_id, f"status:Scoring {len(selected)} products...")
            for i, p in enumerate(selected):
                push(job_id, f"status:Researching {p.get('name', '')} ({i+1}/{len(selected)})...")
            analysis_id, new_product_names = score(
                disc.get("company_name", ""),
                selected, discovery_id,
                discovery_data=disc,
            )
            # Signal "done" immediately — stable URL (existing analysis_id if cache hit)
            # Pass selected products as URL-encoded query so the page can default to
            # the highest-scoring product of THIS selection
            from urllib.parse import quote
            done_url = analysis_id
            if selected_set:
                encoded = ",".join(quote(n, safe="") for n in sorted(selected_set))
                done_url = analysis_id + "?selected=" + encoded
            push(job_id, f"done:{done_url}")

            # Phase B: Generate briefcase in the background — ONLY for newly scored products
            if new_product_names:
                def run_briefcase():
                    try:
                        log.info("Background briefcase generation starting for analysis %s (%d new products)",
                                 analysis_id, len(new_product_names))
                        generate_briefcase_for_analysis(analysis_id, only_for_products=new_product_names)
                    except Exception as e:
                        log.exception("Background briefcase generation failed for %s", analysis_id)
                threading.Thread(target=run_briefcase, daemon=True).start()
            else:
                log.info("Skipping briefcase generation — all selected products were cached")
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


def _prepare_analysis_for_render(analysis: dict) -> None:
    """Thin wrapper that delegates the actual cache-revalidation to the
    Intelligence layer — Inspector route handlers should not own scoring
    math, badge normalization, or recompute logic.

    See intelligence.recompute_analysis() for the implementation.
    Per the Layer Discipline principle (CLAUDE.md) and CRIT-2 in
    code-review-2026-04-07.md, this function moved out of Inspector
    in Phase C of the deep-review fix sequence. Prospector and Designer
    will eventually call intelligence.recompute_analysis() directly.
    """
    from intelligence import recompute_analysis
    recompute_analysis(analysis)


def _select_default_product_index(analysis: dict, selected_csv: str | None) -> int:
    """Pick the default product to display.

    If `selected_csv` is provided (from ?selected=foo,bar query), choose the
    highest-scoring product from THAT subset. Otherwise the top product overall.
    """
    products = analysis.get("products", [])
    if not products:
        return 0
    if not selected_csv:
        return 0
    selected_set = {n.strip() for n in selected_csv.split(",") if n.strip()}
    best_idx = 0
    best_score = -1
    for i, p in enumerate(products):
        if p.get("name") not in selected_set:
            continue
        total = (p.get("fit_score") or {}).get("total", 0) if isinstance(p.get("fit_score"), dict) else 0
        if total > best_score:
            best_score = total
            best_idx = i
    return best_idx


@app.route("/inspector/analysis/<analysis_id>/refresh", methods=["POST"])
def inspector_refresh_cache(analysis_id: str):
    """Refresh an existing analysis: re-run scoring for all its current products.

    Triggered by clicking the cache date link in the header. Re-uses the same
    discovery and the same analysis_id (stable URL).
    """
    analysis = load_analysis(analysis_id)
    if not analysis:
        return jsonify({"ok": False, "error": "not_found"}), 404
    discovery_id = analysis.get("discovery_id")
    if not discovery_id:
        return jsonify({"ok": False, "error": "no_discovery"}), 400
    disc = load_discovery(discovery_id)
    if not disc:
        return jsonify({"ok": False, "error": "discovery_missing"}), 404

    # Build the list of products to re-score from the existing analysis
    product_names = {p.get("name") for p in analysis.get("products", []) if p.get("name")}
    selected = [p for p in disc.get("products", []) if p.get("name") in product_names]
    if not selected:
        return jsonify({"ok": False, "error": "no_products_to_refresh"}), 400

    # CRIT-7 in code-review-2026-04-07.md: do NOT pre-save a wiped state
    # with the old analyzed_at stamp. Instead, pass force_refresh=True to
    # intelligence.score(), which now atomically wipes the existing
    # products and re-scores them within the same save boundary. The user
    # sees the previous analysis until the new score completes, which is
    # honest — no glitchy "0 products with old date" intermediate state.

    job_id = str(uuid.uuid4())[:8]

    def run_refresh():
        try:
            push(job_id, f"status:Refreshing {len(selected)} products...")
            new_analysis_id, new_product_names = score(
                disc.get("company_name", ""),
                selected, discovery_id,
                discovery_data=disc,
                force_refresh=True,
            )
            push(job_id, f"done:{new_analysis_id}")
            if new_product_names:
                def run_briefcase():
                    try:
                        log.info("Refresh: background briefcase generation for %s", new_analysis_id)
                        generate_briefcase_for_analysis(
                            new_analysis_id, only_for_products=new_product_names)
                    except Exception:
                        log.exception("Refresh briefcase generation failed")
                threading.Thread(target=run_briefcase, daemon=True).start()
        except Exception as e:
            log.exception("Refresh scoring failed")
            push(job_id, f"error:{e}")

    threading.Thread(target=run_refresh, daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id})


@app.route("/inspector/analysis/<analysis_id>/briefcase-status")
def inspector_briefcase_status(analysis_id: str):
    """Returns whether the Seller Briefcase has been generated for a specific product.

    Query: ?product_index=N (default 0). Returns the rendered HTML fragment when ready
    so the page can swap it in place without a full reload.
    """
    analysis = load_analysis(analysis_id)
    if not analysis:
        return jsonify({"ready": False, "error": "not_found"}), 404
    products = analysis.get("products", [])
    if not products:
        return jsonify({"ready": False, "error": "no_products"}), 404
    try:
        product_index = int(request.args.get("product_index", 0))
    except (ValueError, TypeError):
        product_index = 0
    if product_index < 0 or product_index >= len(products):
        return jsonify({"ready": False, "error": "bad_index"}), 400
    product = products[product_index]
    # Per-product briefcase OR legacy analysis-level briefcase as fallback
    briefcase = product.get("briefcase") or analysis.get("briefcase")
    if briefcase is None:
        return jsonify({"ready": False})
    # Render fragment in the same shape the page uses (analysis + selected_product)
    _prepare_analysis_for_render(analysis)
    html = render_template("_briefcase_section.html",
                           analysis=analysis,
                           selected_product=product)
    return jsonify({"ready": True, "html": html})


@app.route("/inspector/analysis/<analysis_id>/product/<int:product_index>")
def inspector_product_fragment(analysis_id: str, product_index: int):
    """Returns rendered HTML fragments for switching products in the dropdown.

    Used by the in-place swap JS — no page reload, no URL change.
    Returns: { hero_html, pillars_html, briefcase_html }
    """
    analysis = load_analysis(analysis_id)
    if not analysis:
        return jsonify({"error": "not_found"}), 404
    _prepare_analysis_for_render(analysis)
    products = analysis.get("products", [])
    if product_index < 0 or product_index >= len(products):
        return jsonify({"error": "bad_index"}), 400
    selected_product = products[product_index]
    return jsonify({
        "hero_html": render_template("_hero_section.html",
                                     analysis=analysis,
                                     selected_product=selected_product),
        "pillars_html": render_template("_pillars_section.html",
                                        analysis=analysis,
                                        selected_product=selected_product),
        "briefcase_html": render_template("_briefcase_section.html",
                                          analysis=analysis,
                                          selected_product=selected_product),
    })


@app.route("/inspector/analysis/<analysis_id>")
def inspector_full_analysis(analysis_id: str):
    """Full Analysis page — deep research results."""
    analysis = load_analysis(analysis_id)
    if not analysis:
        return error_response("Analysis not found.", 404)

    # Hydrate the analysis with company-context fields from its parent
    # discovery (company_description, competitive_products, _company_badge,
    # _org_color). Idempotent — only sets missing fields. Lives in the
    # intelligence layer so Prospector and Designer can hydrate the same way.
    # See HIGH-2 in code-review-2026-04-07.md.
    from intelligence import hydrate_analysis
    hydrate_analysis(analysis)

    # Cache version check — if the cached analysis was scored with an older
    # SCORING_LOGIC_VERSION than the current one, the page should prompt the
    # user to refresh (decision modal opens on page load). The user can choose
    # Refresh (kicks off scoring with progress modal) or Ignore for now
    # (renders the cached page as-is). Closes the gap that allowed Workday
    # cached scores to render with degraded math after the Pillar 1/2/3 refactor.
    import scoring_config as cfg
    is_cache_stale = not cfg.is_cached_logic_current(analysis)
    if is_cache_stale:
        log.info(
            "inspector_full_analysis: analysis %s is stale (cached version %r vs current %r) — "
            "page will prompt user to refresh",
            analysis_id,
            analysis.get("_scoring_logic_version", "<missing>"),
            cfg.SCORING_LOGIC_VERSION,
        )

    _prepare_analysis_for_render(analysis)

    # If no product has a briefcase yet (and there's no legacy analysis-level
    # briefcase either), kick off background briefcase generation so the page's
    # polling JS will resolve. This handles cache-hit cases where briefcase
    # generation never ran.
    products = analysis.get("products", [])
    needs_briefcase = (
        products
        and not analysis.get("briefcase")
        and all(p.get("briefcase") is None for p in products)
    )
    if needs_briefcase:
        product_names = [p.get("name") for p in products if p.get("name")]
        log.info("Briefcase needed for analysis %s — kicking off background generation",
                 analysis_id)
        threading.Thread(
            target=lambda: generate_briefcase_for_analysis(
                analysis_id, only_for_products=product_names),
            daemon=True,
        ).start()

    # Default product = highest of THIS run's selection (if provided), else top overall
    default_idx = _select_default_product_index(analysis, request.args.get("selected"))
    selected_product = products[default_idx] if products else None

    import json
    import scoring_config as cfg
    return render_template("full_analysis.html",
                          analysis=analysis,
                          selected_product=selected_product,
                          default_index=default_idx,
                          is_cache_stale=is_cache_stale,
                          # Modal content lives in scoring_config so the
                          # pillar weights inside the eyebrows can never
                          # drift from the actual config. HIGH-4 in
                          # code-review-2026-04-07.md.
                          modal_content_json=json.dumps(cfg.MODAL_CONTENT))


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
    app.run(debug=True, port=5000)  # magic-allowed: Flask dev server port
