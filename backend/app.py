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
import json
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


@app.template_filter("format_count")
def format_count_filter(value) -> str:
    """Format an integer count with k / M abbreviations (no dollar sign).

    Used by the ACV by Use Case table for audience / hours / annual
    hours columns. "15,000" → "15k", "400,000" → "400k", "1,200,000"
    → "1.2M". Sub-1000 values render as-is. Keeps the table compact
    so columns don't overflow and get truncated.
    """
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        return "0"
    if value >= 1_000_000: return f"{value / 1_000_000:.1f}M"  # magic-allowed: standard count formatting (millions)
    elif value >= 10_000: return f"{value / 1_000:.0f}k"  # magic-allowed: 10k+ rounds to whole-k
    elif value >= 1_000: return f"{value / 1_000:.1f}k"  # magic-allowed: 1k-10k shows one decimal so 1.2k distinguishable from 1.5k
    return f"{int(value)}"


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

    Frank 2026-04-08: the AI also wraps the label in Markdown-style `**...**`.
    Since the filter is already doing the bolding via `<strong>`, the literal
    asterisks are noise — strip them up front so the bolded label renders
    clean instead of showing `**Label**` with escaped asterisks.
    """
    from markupsafe import Markup, escape
    if not value:
        return Markup("")
    # Strip Markdown bold markers — the filter handles bolding itself
    value = value.replace("**", "")
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
    """Inspector home — unified search for a company or product."""
    return render_template("home.html")


@app.route("/api/cached-companies")
def api_cached_companies():
    """Return cached company names for typeahead suggestions.

    Searches saved discoveries for company names matching the query.
    Returns a lightweight list — name, badge, domain, discovery_id.
    The cache grows organically as companies are researched.
    """
    q = (request.args.get("q") or "").strip().lower()
    if len(q) < 2:  # magic-allowed: minimum query length for typeahead
        return jsonify([])

    from storage import list_discoveries
    results = []
    seen_names: set[str] = set()
    for disc in list_discoveries():
        name = disc.get("company_name", "")
        name_key = name.lower().strip()
        if q in name_key and name_key not in seen_names:
            seen_names.add(name_key)
            results.append({
                "name": name,
                "badge": disc.get("_company_badge", ""),
                "url": disc.get("company_url", ""),
                "discovery_id": disc.get("discovery_id", ""),
            })
        if len(results) >= 10:  # magic-allowed: typeahead result limit
            break
    return jsonify(results)


# ═══════════════════════════════════════════════════════════════════════════
# INSPECTOR SEARCH + PROGRESS ROUTES — ALL FLOWS USE THE SHARED SEARCH MODAL
# ═══════════════════════════════════════════════════════════════════════════
#
# THE RULE (platform-wide, Inspector + Prospector + Designer): every long-
# running operation renders its progress through the SHARED search modal
# defined in `tools/inspector/templates/_search_modal.html`.  There is ONE
# progress UI in the platform — no per-flow custom pages, no per-tool
# bespoke overlays.
#
# Every route below follows the same three-step pattern:
#
#   1. Kick off the long-running work on a background thread.
#   2. Publish progress via `push(job_id, "status:...")` / "done:..." /
#      "error:..." — the exact SSE contract the shared modal consumes.
#   3. Return JSON `{ok: True, job_id: ..., ...}` so the caller can open
#      the shared modal via `openSearchModal({sseUrl: '/.../progress/' +
#      job_id, onComplete: ...})`.
#
# The ONLY exception is `inspector_discover` which renders `discovering.html`
# (a 75-line shell that itself opens the shared modal on load) — the form
# POST from `home.html` is traditional because there's no JS on home.html
# that could fetch() and intercept.  `discovering.html` is NOT a custom
# progress page; it's a thin wrapper around the shared modal.
#
# If you are adding a new long-running flow and are tempted to build a new
# progress page / loading spinner / overlay / decision prompt:  STOP.  The
# answer is always the shared modal.  See `docs/Platform-Foundation.md` →
# "The Standard Search Modal" and `CLAUDE.md` → "The Standard Search Modal"
# for the full rule.
# ═══════════════════════════════════════════════════════════════════════════

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

    # discovering.html is a thin shell that opens the SHARED search modal
    # (see `_search_modal.html`) subscribed to the discovery progress SSE
    # stream.  We pass the job_id; the modal's onComplete reads the real
    # discovery_id out of the 'done:<discovery_id>' SSE payload and
    # redirects to /inspector/product-selection/<discovery_id>.
    return render_template("discovering.html",
                          job_id=job_id,
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

    # Families are AI-assigned product categories (see the picker builder
    # below for why). Matching a product to a family is a simple
    # case-insensitive equality check on the category field — no token
    # machinery needed. Training & Certification products always come
    # along regardless of which family the user picked.
    if selected_families:
        _selected_lower = {f.strip().lower() for f in selected_families}
        disc["products"] = [
            p for p in disc.get("products", [])
            if p.get("category") == "Training & Certification"
            or (p.get("category") or "").strip().lower() in _selected_lower
        ]
        disc["_selected_families"] = selected_families
    elif len(non_tc) >= cfg.PRODUCT_FAMILY_PICKER_THRESHOLD:
        # Build the family picker — PRIMARY strategy is grouping by the
        # AI-assigned product CATEGORY. Every discovered product has a
        # category (Endpoint Protection, Threat Intelligence, Data
        # Protection, etc.), so grouping by category gives 100% coverage
        # of the product list. The user can see every product through
        # some family, no stranded products.
        #
        # Frank 2026-04-08 Trellix: earlier attempts used the scraped
        # website-nav families as the primary source with various
        # token-overlap heuristics to match them to products. The nav
        # families (Data Security, AI and Security Operations, etc.) use
        # a different vocabulary than the AI's own category assignments,
        # so the matchers either over-matched (generic security tokens)
        # or under-matched (40 products -> 3 families covering 10 of
        # them, stranding 30). Categories sidestep the vocabulary
        # mismatch entirely because they're the labels the AI literally
        # put on each product.
        family_counts: dict[str, int] = {}
        for p in non_tc:
            cat = (p.get("category") or "Other").strip() or "Other"
            family_counts[cat] = family_counts.get(cat, 0) + 1

        # Noise filter: drop categories below PRODUCT_FAMILY_MIN_PRODUCTS
        # (single-product categories are not meaningful picker choices).
        # No MAX ratio cap needed — categories are inherently clean.
        families = sorted(
            [
                {"name": c, "product_count": n}
                for c, n in family_counts.items()
                if n >= cfg.PRODUCT_FAMILY_MIN_PRODUCTS
            ],
            key=lambda f: f["product_count"], reverse=True
        )

        # Only show the picker when there are multiple families to
        # choose from — one family is no choice at all. The threshold
        # check above (len(non_tc) >= PRODUCT_FAMILY_PICKER_THRESHOLD)
        # already guarantees we're dealing with enough products to make
        # narrowing worthwhile; this guard just avoids showing a picker
        # with a single option.
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

    # Stale-cache decision: if there's an existing analysis AND it was scored
    # with an older logic version, surface a confirmation modal when the user
    # clicks Deep Dive instead of silently re-using the cached scores. Frank
    # 2026-04-07: "it would be nice maybe to have that modal saying, hey,
    # there's newer stuff. Do you wanna just go, or do you want the newer stuff?"
    cached_is_stale = bool(existing) and not cfg.is_cached_logic_current(existing)

    return render_template("product_selection.html",
                          discovery=disc,
                          existing_analysis=existing,
                          cached_product_names=cached_product_names,
                          cached_is_stale=cached_is_stale,
                          deep_dive_max_new=cfg.DEEP_DIVE_MAX_NEW_PRODUCTS,
                          show_family_picker=show_family_picker,
                          modal_content_json=json.dumps(cfg.MODAL_CONTENT))


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
            total = len(selected)
            push(job_id, f"status:Preparing scoring context for {total} products...")
            # Transition banner for the shared search modal's status line.
            # The modal just renders whatever status text the backend pushes;
            # no phase-machine state is required on the client anymore.
            push(job_id, "status:Scoring with Claude...")

            # Honest per-completion progress callback.  The Intelligence
            # layer calls this as each product ACTUALLY FINISHES scoring
            # (not upfront at dispatch time, which was the old behavior
            # and produced a dishonest progress bar that zipped through
            # the first N-2 products in a second and then sat silent on
            # the last few for minutes).  GP1 "right way" + GP3 honest
            # progress — the bar traces back to completed work.
            def _progress(product_name: str, completed: int, total_count: int) -> None:
                push(
                    job_id,
                    f"status:Scored {product_name} ({completed}/{total_count})",
                )

            analysis_id, new_product_names = score(
                disc.get("company_name", ""),
                selected, discovery_id,
                discovery_data=disc,
                progress_cb=_progress,
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

    # Return JSON — the caller (product_selection.html) opens the SHARED
    # search modal in progress mode and subscribes to
    # /inspector/score/progress/<job_id>.  There is ONE shared progress
    # modal in the platform (see `_search_modal.html`); no route should
    # render its own full-page progress view.
    return jsonify({
        "ok": True,
        "job_id": job_id,
        "discovery_id": discovery_id,
        "company_name": disc.get("company_name", ""),
        "product_count": len(selected),
    })


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
            total = len(selected)
            push(job_id, f"status:Refreshing {total} products...")
            # Transition banner for the shared search modal's status line.
            push(job_id, "status:Scoring with Claude...")

            # Honest per-completion progress callback — mirrors the
            # run_scoring path so the refresh experience shows real
            # per-product progress instead of a silent wall.
            def _progress(product_name: str, completed: int, total_count: int) -> None:
                push(
                    job_id,
                    f"status:Scored {product_name} ({completed}/{total_count})",
                )

            new_analysis_id, new_product_names = score(
                disc.get("company_name", ""),
                selected, discovery_id,
                discovery_data=disc,
                force_refresh=True,
                progress_cb=_progress,
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
        "acv_html": render_template("_acv_widget.html",
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
# Prospector Routes — ICP Validation & Prioritization
#
# Prospector takes a list of company names, runs discovery on each, and
# returns them ranked by ACV potential. Same discovery data as Inspector —
# every company Prospector researches is cached and immediately available
# for Deep Dives in Inspector. Intelligence compounds (GP5).
#
# Design completed 2026-04-12. See Platform-Foundation.md → Prospector UX.
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/prospector")
def prospector_home():
    """Prospector landing — input form + results if a batch was just run."""
    batch_id = request.args.get("batch")
    results = None
    if batch_id:
        results = _load_prospector_batch(batch_id)
    return render_template("prospector.html", results=results, batch_id=batch_id)


@app.route("/prospector/run", methods=["POST"])
def prospector_run():
    """Start batch discovery — returns a progress page with SSE modal.

    Accepts a textarea of company names (one per line). Kicks off a
    background thread that runs discovery on each company sequentially,
    emitting SSE progress per company via the standard search modal.
    """
    # Accept company names from textarea OR CSV upload
    raw = request.form.get("companies", "")
    company_names = []
    for line in raw.strip().split("\n"):
        for name in line.split(","):
            name = name.strip()
            if name:
                company_names.append(name)

    # CSV upload — extract company names from the first column
    csv_file = request.files.get("csv_file")
    if csv_file and csv_file.filename:
        import csv
        import io
        content = csv_file.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            if row and row[0].strip():
                name = row[0].strip()
                if name.lower() not in ("company", "company name", "name", "organization"):
                    company_names.append(name)

    if not company_names:
        return redirect(url_for("prospector_home"))

    deep_dive = request.form.get("deep_dive") == "on"

    job_id = str(uuid.uuid4())[:8]
    batch_id = str(uuid.uuid4())[:8]
    total = len(company_names)

    # Per-company timeouts — Frank 2026-04-13
    DISCOVERY_TIMEOUT = 180   # magic-allowed: three-minute-per-company discovery timeout
    DEEP_DIVE_TIMEOUT = 300   # magic-allowed: five-minute-per-company deep-dive timeout

    def _run_one_company(name: str, index: int) -> dict:
        """Run discovery (+ optional Deep Dive) for one company with timeout."""
        import signal as _signal
        import functools

        push(job_id, f"status:Researching {name}… {index} of {total}")
        try:
            disc = discover(name)
        except Exception as e:
            log.warning("Prospector: discovery failed for %s: %s", name, e)
            return {"company_name": name, "error": str(e)}

        row = _build_prospector_row(disc)

        if deep_dive and not row.get("error"):
            try:
                push(job_id, f"status:Deep Dive on {name}… {index} of {total}")
                disc_id = disc.get("discovery_id", "")
                products = disc.get("products", [])
                if products and disc_id:
                    # Pick the top product (first by popularity — same sort as product chooser)
                    top_product = products[0]
                    top_name = top_product.get("name", "")
                    if top_name:
                        from intelligence import score
                        analysis = score([top_product], disc_id, discovery_data=disc)
                        # Rebuild the row with sharpened Deep Dive data
                        if analysis:
                            row = _build_prospector_row_from_analysis(disc, analysis, row)
            except Exception as e:
                log.warning("Prospector: Deep Dive failed for %s: %s", name, e)
                row["deep_dive_error"] = str(e)

        return row

    def run_batch():
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        # Run companies in parallel — Frank 2026-04-13
        max_workers = min(len(company_names), 3)  # magic-allowed: parallel-cap-avoids-rate-limits
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {}
            for i, name in enumerate(company_names, 1):
                f = ex.submit(_run_one_company, name, i)
                futures[f] = name

            for future in as_completed(futures, timeout=total * DISCOVERY_TIMEOUT):
                try:
                    row = future.result(timeout=DISCOVERY_TIMEOUT)
                    results.append(row)
                except Exception as e:
                    name = futures[future]
                    log.warning("Prospector: timed out for %s: %s", name, e)
                    results.append({"company_name": name, "error": f"Timed out: {e}"})

        # Sort by estimated ACV (descending)
        results.sort(key=lambda r: r.get("_sort_acv", 0), reverse=True)
        for i, r in enumerate(results, 1):
            r["rank"] = i

        _save_prospector_batch(batch_id, results)
        push(job_id, f"done:{batch_id}")

    threading.Thread(target=run_batch, daemon=True).start()

    return render_template("prospector_running.html",
                          job_id=job_id,
                          company_count=total,
                          deep_dive=deep_dive)


@app.route("/prospector/progress/<job_id>")
def prospector_progress(job_id: str):
    """SSE stream for Prospector batch progress."""
    return Response(stream_with_context(sse_stream(job_id)),
                    content_type="text/event-stream")


@app.route("/prospector/export/<batch_id>")
def prospector_export(batch_id):
    """Export a Prospector batch as CSV."""
    import csv
    import io

    results = _load_prospector_batch(batch_id)
    if not results:
        return "Batch not found", 404  # magic-allowed: HTTP status

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Company", "Badge", "Estimated ACV",
        "Top Product", "Subcategory", "Why",
        "Promising Products", "Potential Products",
        "Uncertain Products", "Unlikely Products",
        "Lab Platform", "Key Signal", "Discovery ID",
    ])
    for r in results:
        writer.writerow([
            r.get("rank", ""),
            r.get("company_name", ""),
            r.get("company_badge", ""),
            r.get("estimated_acv", ""),
            r.get("top_product_name", ""),
            r.get("top_product_subcategory", ""),
            r.get("top_product_why", ""),
            r.get("promising_count", 0),
            r.get("potential_count", 0),
            r.get("uncertain_count", 0),
            r.get("unlikely_count", 0),
            r.get("lab_platform", ""),
            r.get("key_signal", ""),
            r.get("discovery_id", ""),
        ])

    csv_content = output.getvalue()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=prospector-{batch_id}.csv"},
    )


@app.route("/prospector/field-mapper")
def prospector_field_mapper():
    """Display all intelligence fields available for HubSpot mapping.

    Hierarchical, collapsible view that mirrors the scoring framework:
    ACV Potential → Fit Score (Pillars → Dimensions) → Seller Briefcase →
    Company Signals → Product Identity.

    Treats RevOps as first-class citizens — same care in UX design as
    sellers, CSMs, and SEs get. GP1: right information, right context,
    right way — for the RevOps persona.

    Field hierarchy is built directly in the template because the
    structure IS the framework (GP4). No flat field lists needed.
    """
    # Hierarchical view is built directly in the template — the hierarchy
    # IS the template structure (GP4 — self-evident at the UX layer).
    # No flat field lists needed from the route.
    return render_template("prospector_field_mapper.html")




def _build_prospector_row(disc: dict) -> dict:
    """Build a single Prospector results row from a discovery dict.

    Extracts the fields the results table needs. Handles both v1 (old)
    and v2 (new) discovery formats gracefully — missing fields default
    to empty/zero rather than erroring.
    """
    from intelligence import enrich_discovery
    enrich_discovery(disc)

    products = [p for p in disc.get("products", [])
                if p.get("category") != "Training & Certification"]

    # Tier counts
    tier_counts = {"promising": 0, "potential": 0, "uncertain": 0, "unlikely": 0}
    for p in products:
        tier = p.get("_tier", "uncertain")
        if tier in tier_counts:
            tier_counts[tier] += 1

    # Top product — highest rough_labability_score / discovery_score
    top = None
    if products:
        top = max(products, key=lambda p: p.get("rough_labability_score",
                                                 p.get("discovery_score", 0)))

    # Company signals (v2 discoveries have these in company_signals)
    signals = disc.get("company_signals", {})
    lab_platform = signals.get("lab_platform", "") if signals else ""
    # Fallback for v1 discoveries that have lab_platform_detections
    if not lab_platform:
        detections = disc.get("_lab_platform_detections", [])
        if detections:
            lab_platform = detections[0].get("platform", "")

    # Key signal — pick the strongest company-level signal
    key_signal = ""
    if signals:
        # Priority order for key signal selection
        if signals.get("atp_program") and "no" not in signals["atp_program"].lower():
            key_signal = signals["atp_program"]
        elif signals.get("events") and "no" not in signals["events"].lower():
            key_signal = signals["events"]
        elif signals.get("training_programs"):
            key_signal = signals["training_programs"][:80]  # magic-allowed: truncation for display
        elif signals.get("delivery_partners"):
            key_signal = signals["delivery_partners"][:80]  # magic-allowed: truncation for display

    # Estimated ACV — rough estimate from user base + product count
    # For now, use the top product's user base as the ACV proxy
    # Full ACV calculation happens during Deep Dive
    estimated_acv = ""
    sort_acv = 0
    if top and top.get("estimated_user_base"):
        estimated_acv = f"~{top['estimated_user_base']} users"
        # Parse rough numeric for sorting
        sort_acv = _parse_user_base_for_sort(top.get("estimated_user_base", ""))

    # Build why string for top product
    top_why = ""
    if top:
        parts = []
        if top.get("estimated_user_base"):
            parts.append(top["estimated_user_base"] + " users")
        if top.get("deployment_model"):
            parts.append(top["deployment_model"])
        if top.get("api_surface") and top["api_surface"] != "none":
            api_short = top["api_surface"].split("—")[0].strip() if "—" in top.get("api_surface", "") else top.get("api_surface", "")
            parts.append(api_short + " API")
        top_why = ", ".join(parts)

    return {
        "company_name": disc.get("company_name", ""),
        "company_badge": disc.get("_company_badge", ""),
        "badge_color": disc.get("_org_color", "purple"),
        "discovery_id": disc.get("discovery_id", ""),
        "estimated_acv": estimated_acv,
        "_sort_acv": sort_acv,
        "top_product_name": top.get("name", "") if top else "",
        "top_product_subcategory": top.get("subcategory", "") if top else "",
        "top_product_why": top_why,
        "promising_count": tier_counts["promising"],
        "potential_count": tier_counts["potential"],
        "uncertain_count": tier_counts["uncertain"],
        "unlikely_count": tier_counts["unlikely"],
        "lab_platform": lab_platform,
        "key_signal": key_signal,
    }


def _build_prospector_row_from_analysis(
    disc: dict, analysis: dict, base_row: dict,
) -> dict:
    """Sharpen a Prospector row with Deep Dive data.

    When a Deep Dive completes, replaces the rough discovery-level
    estimates with the actual scored data. GP5: intelligence compounds.
    """
    row = dict(base_row)  # shallow copy
    products = analysis.get("products") or analysis.get("top_products") or []
    if products:
        top = products[0]
        fit_score = (top.get("fit_score") or {})
        fs_total = fit_score.get("total") or fit_score.get("_total") or 0
        row["fit_score"] = fs_total
        row["verdict"] = (top.get("verdict") or {}).get("label", "")

        acv = analysis.get("_company_acv") or {}
        if acv.get("scored_low"):
            from app import _format_acv_value
            row["estimated_acv"] = f"~{_format_acv_value(acv['scored_low'])}"
            row["_sort_acv"] = acv["scored_low"]
        row["deep_dive_complete"] = True
    return row


def _format_acv_value(value: int) -> str:
    """Format a dollar value for display: $1.2M, $450k, etc."""
    if value >= 1_000_000:  # magic-allowed: display formatting threshold
        return f"${value / 1_000_000:.1f}M"  # magic-allowed: display formatting divisor
    if value >= 1_000:  # magic-allowed: display formatting threshold
        return f"${value // 1_000}k"  # magic-allowed: display formatting divisor
    return f"${value}"


def _parse_user_base_for_sort(value: str) -> int:
    """Parse estimated_user_base string to an integer for sorting.

    Handles formats like "~14M", "~50K", "~2000", "14000000".
    Returns 0 on parse failure — safe fallback for sorting.
    """
    if not value:
        return 0
    # Strip tilde and whitespace
    s = value.replace("~", "").replace(",", "").strip().upper()
    try:
        if s.endswith("M"):
            return int(float(s[:-1]) * 1_000_000)  # magic-allowed: million multiplier
        elif s.endswith("K"):
            return int(float(s[:-1]) * 1_000)  # magic-allowed: thousand multiplier
        elif s.endswith("B"):
            return int(float(s[:-1]) * 1_000_000_000)  # magic-allowed: billion multiplier
        else:
            return int(float(s))
    except (ValueError, IndexError):
        return 0


def _save_prospector_batch(batch_id: str, results: list[dict]) -> None:
    """Save a Prospector batch to the data directory."""
    import json
    batch_dir = Path("data/prospector_batches")
    batch_dir.mkdir(parents=True, exist_ok=True)
    with open(batch_dir / f"{batch_id}.json", "w") as f:
        json.dump(results, f, indent=2)  # magic-allowed: JSON formatting indent


def _load_prospector_batch(batch_id: str) -> list[dict] | None:
    """Load a saved Prospector batch."""
    import json
    batch_path = Path("data/prospector_batches") / f"{batch_id}.json"
    if not batch_path.exists():
        return None
    with open(batch_path) as f:
        return json.load(f)


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
