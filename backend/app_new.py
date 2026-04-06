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

from config_new import ANTHROPIC_API_KEY, validate_startup
from core_new import (
    assign_verdict, company_classification_label, discovery_tier,
    DISCOVERY_TIER_LABELS, error_response, org_badge_color_group,
    score_products_and_sort, push, sse_stream, poll_job,
)
from intelligence_new import discover, score, qualify, lookup, cache_is_fresh, generate_briefcase_for_analysis
from models_new import CompanyAnalysis, Product
from storage_new import (
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
    return {"seems_promising": "t-sp", "likely": "t-l", "uncertain": "t-u", "unlikely": "t-ul"}.get(tier_key, "")


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

    return render_template("discovering_new.html",
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

    # Assign discovery tiers
    for p in disc.get("products", []):
        score_val = p.get("discovery_score", 0)
        p["_tier"] = discovery_tier(score_val)
        p["_tier_label"] = DISCOVERY_TIER_LABELS.get(p["_tier"], p["_tier"])

    # Company classification — pass products so category can be derived
    from models_new import Product
    product_objs = [Product(name=p.get("name", ""), category=p.get("category", ""))
                    for p in disc.get("products", [])]
    disc["_company_badge"] = company_classification_label(
        disc.get("organization_type", "software_company"), product_objs
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

    return render_template("scoring_new.html",
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


_EVIDENCE_LABEL_RE = re.compile(r'^\*\*([^*|]+?)\s*\|\s*([^*]+?):\*\*\s*')


def _normalize_badges_for_scoring(p: dict) -> None:
    """Phase 1 of badge normalization — runs BEFORE the scoring math.

    Decision-log principle (2026-04-06): visual changes must NEVER affect
    scoring. This function does ONLY the transforms that legitimately
    change what the math sees:

    Bug 1 — The AI groups multiple distinct signals under one umbrella badge.
    Each evidence item starts with its own `**Label | Qualifier:**` prefix
    that names the actual signal. Fix: when a badge's evidence items each
    carry an embedded label, split into N badges — one per evidence —
    using the embedded label as the new badge name and the embedded
    qualifier as the new badge qualifier. The prefix is stripped from the
    claim text since the badge name now carries it.

    Bug 2 — The "No Learner Isolation" badge is sometimes missing on
    products where it should always appear (multi_tenant_only or saas_only
    ceiling flags set). Fix: ensure the badge exists in the Lab Access
    dimension when the relevant ceiling flag is present. This is a
    deterministic injection from the deployment model.

    Mutates the product dict in place. Display-only transforms (merging
    same-named badges, color promotion) live in
    _normalize_badges_for_display() and run AFTER the math.
    """
    import scoring_config as cfg

    fs = p.get("fit_score")
    if not isinstance(fs, dict):
        return

    flags = set(p.get("poor_match_flags") or [])
    needs_isolation_badge = bool(cfg.ISOLATION_BLOCKING_CEILING_FLAGS & flags)

    for pillar_key, pillar_dict in fs.items():
        if not isinstance(pillar_dict, dict):
            continue
        for dim_dict in pillar_dict.get("dimensions", []) or []:
            if not isinstance(dim_dict, dict):
                continue
            old_badges = dim_dict.get("badges", []) or []
            new_badges = []
            for b in old_badges:
                if not isinstance(b, dict):
                    new_badges.append(b)
                    continue
                ev_list = b.get("evidence", []) or []
                if not ev_list:
                    new_badges.append(b)
                    continue

                # Inspect each evidence claim for an embedded label prefix
                parsed = []
                for ev in ev_list:
                    if not isinstance(ev, dict):
                        continue
                    claim = ev.get("claim", "") or ""
                    m = _EVIDENCE_LABEL_RE.match(claim)
                    if m:
                        label = m.group(1).strip()
                        qualifier = m.group(2).strip()
                        new_ev = dict(ev)
                        new_ev["claim"] = claim[m.end():]
                        parsed.append((label, qualifier, new_ev))
                    else:
                        parsed.append((None, None, ev))

                # If every evidence carries an embedded label, split into N badges
                if parsed and all(label is not None for label, _, _ in parsed):
                    for label, qualifier, ev in parsed:
                        new_badges.append({
                            "name": label,
                            "color": b.get("color", ""),
                            "qualifier": qualifier or b.get("qualifier", ""),
                            "evidence": [ev],
                        })
                else:
                    # Mixed or no labels — leave the badge alone
                    new_badges.append(b)

            dim_dict["badges"] = new_badges

            # Bug 2 enforcement: ensure the synthetic No Learner Isolation
            # badge exists in the Lab Access dimension when the deployment
            # model demands it. This is a real signal the math should see,
            # not a display tweak. All metadata reads from cfg.SYNTHETIC_BADGES
            # — Define-Once for the badge name, color, qualifier, and claim.
            if needs_isolation_badge and dim_dict.get("name") == cfg.LAB_ACCESS_DIMENSION_NAME:
                synth = cfg.SYNTHETIC_BADGES["no_learner_isolation"]
                synth_name_lower = synth["name"].lower()
                already_present = any(
                    (b.get("name", "") or "").strip().lower() == synth_name_lower
                    for b in dim_dict["badges"] if isinstance(b, dict)
                )
                if not already_present:
                    # Pick the friendly flag label. Priority order is the
                    # insertion order of synth["flag_labels"] in scoring_config
                    # (dicts preserve order in Python 3.7+) — the first entry
                    # listed there is the most specific case and wins when
                    # multiple flags are set on the same product.
                    flag_labels = synth["flag_labels"]
                    chosen_flag = next(
                        (f for f in flag_labels.keys() if f in flags),
                        "",
                    )
                    flag_label_text = flag_labels.get(chosen_flag, "")
                    dim_dict["badges"].append({
                        "name": synth["name"],
                        "color": synth["color"],
                        "qualifier": synth["qualifier"],
                        "evidence": [{
                            "claim": synth["claim_template"].format(flag_label=flag_label_text),
                            "confidence_level": synth["confidence_level"],
                            "source_url": "",
                            "source_title": synth["source_title"],
                        }],
                    })


def _normalize_badges_for_display(p: dict) -> None:
    """Phase 2 of badge normalization — runs AFTER the scoring math.

    Decision-log principle (2026-04-06): visual changes must NEVER affect
    scoring. This function only does transforms that affect what the user
    sees, not what the math saw. By the time it runs, scores are already
    written into the product dict — these mutations cannot retroactively
    change them.

    **Defensive safety net for the universal variable-badge rule.**

    The scoring prompt now tells the AI to disambiguate same-name badges
    at the source — first occurrence keeps the canonical name, subsequent
    occurrences are renamed to a scoring signal name (preferred) or a
    qualifier-derived label (fallback). When the AI complies, this
    function has nothing to do because every badge in a dimension is
    already uniquely named.

    But two cases still produce duplicates:
      1. **Legacy cached analyses** scored before the prompt change.
         These still have raw duplicate-name badges from the old AI
         output. The merger collapses them so old pages render cleanly.
      2. **AI non-compliance** — the AI occasionally still emits
         duplicates despite the prompt instruction. The merger is the
         backstop.

    Merge behavior: combine all evidence items into one badge and promote
    the color to the worst of the group (red > amber > green > gray) so
    risks aren't hidden by an adjacent positive signal. The hover modal
    still shows every evidence item, so no information is lost.

    The math layer in Phase 1 has already been called against the
    pre-merge badge list, so dropping the count or changing colors here
    has zero effect on scores.
    """
    import scoring_config as cfg

    fs = p.get("fit_score")
    if not isinstance(fs, dict):
        return

    # Read display severity ranking from config (Define-Once). Separate from
    # BADGE_COLOR_POINTS which is the scoring concept — these two dicts are
    # deliberately distinct per the 2026-04-06 decision-log principle that
    # visual changes must never affect scoring.
    color_priority = cfg.BADGE_COLOR_DISPLAY_PRIORITY

    for pillar_key, pillar_dict in fs.items():
        if not isinstance(pillar_dict, dict):
            continue
        for dim_dict in pillar_dict.get("dimensions", []) or []:
            if not isinstance(dim_dict, dict):
                continue
            badges = dim_dict.get("badges", []) or []
            merged_by_name: dict[str, dict] = {}
            ordered_names: list[str] = []
            for b in badges:
                if not isinstance(b, dict):
                    continue
                name = (b.get("name") or "").strip()
                if not name:
                    continue
                if name not in merged_by_name:
                    merged_by_name[name] = {
                        "name": name,
                        "color": b.get("color", ""),
                        "qualifier": b.get("qualifier", ""),
                        "evidence": list(b.get("evidence") or []),
                    }
                    ordered_names.append(name)
                else:
                    existing = merged_by_name[name]
                    # Promote color to the worst (highest-priority) of the two
                    if color_priority.get(b.get("color", ""), 0) > color_priority.get(existing["color"], 0):
                        existing["color"] = b.get("color", "")
                        existing["qualifier"] = b.get("qualifier", "")
                    existing["evidence"].extend(b.get("evidence") or [])
            dim_dict["badges"] = [merged_by_name[n] for n in ordered_names]


def _prepare_analysis_for_render(analysis: dict) -> None:
    """Mutates analysis dict in place: re-runs the deterministic scoring math
    on every product, then sorts by Fit Score descending.

    The math is the source of truth — it reads the badges the AI emitted from
    the saved evidence, looks up signal points and penalty deductions in
    `scoring_config.py`, applies ceiling flags and the Technical Fit Multiplier,
    and rewrites every score in place. Old saved analyses immediately reflect
    the latest config the moment the page is rendered. Define-Once at runtime.

    Zero hardcoded values — pillar keys, dimension keys, and weights all come
    from `scoring_config.py`.
    """
    import scoring_math
    import scoring_config as cfg
    from core_new import assign_verdict

    # Map each pillar's dict-key to its Pillar object — once, not per product
    pillar_key_to_obj: dict[str, cfg.Pillar] = {}
    dim_key_to_pillar_key: dict[str, str] = {}
    for pillar in cfg.PILLARS:
        pkey = pillar.name.lower().replace(" ", "_")
        pillar_key_to_obj[pkey] = pillar
        for dim in pillar.dimensions:
            dkey = dim.name.lower().replace(" ", "_")
            dim_key_to_pillar_key[dkey] = pkey

    products = analysis.get("products", [])
    for p in products:
        fs = p.get("fit_score")
        if not isinstance(fs, dict):
            p["fit_score"] = {"total": 0, "_total": 0}
            continue

        # ── Phase 1: Normalize badges for SCORING (changes math inputs) ──
        # Splits multi-signal umbrella badges into one-badge-per-signal so
        # evidence is always shown under the correct badge name. Also injects
        # the No Learner Isolation badge when ceiling flags require it.
        # Display-only transforms (merging same-named badges, color promotion)
        # run AFTER the math in Phase 2 below.
        _normalize_badges_for_scoring(p)

        # ── Collect badges per dimension from the saved evidence ──
        # Pass dicts with name + color so the math layer can apply
        # color-based fallback scoring for badge-presence dimensions.
        badges_by_dim: dict[str, list] = {}
        for pillar_key, pillar_obj in pillar_key_to_obj.items():
            pillar_dict = fs.get(pillar_key, {})
            if not isinstance(pillar_dict, dict):
                continue
            for dim_dict in pillar_dict.get("dimensions", []) or []:
                if not isinstance(dim_dict, dict):
                    continue
                dim_name = dim_dict.get("name", "")
                dim_key = dim_name.lower().replace(" ", "_")
                badge_objs: list[dict] = []
                for b in dim_dict.get("badges", []) or []:
                    if isinstance(b, dict) and b.get("name"):
                        badge_objs.append({
                            "name": b["name"],
                            "color": b.get("color", ""),
                        })
                badges_by_dim[dim_key] = badge_objs

        # ── Run the math — single source of truth ──
        result = scoring_math.compute_all(
            badges_by_dimension=badges_by_dim,
            ceiling_flags=p.get("poor_match_flags") or [],
            orchestration_method=p.get("orchestration_method") or "",
        )

        # ── Write computed scores back into the saved dict in place ──
        # Dimension scores remain authentic (the badges that matched).
        # Pillar scores reflect post-ceiling values for Product Labability.
        for pillar_key, pillar_obj in pillar_key_to_obj.items():
            pillar_dict = fs.get(pillar_key, {})
            if not isinstance(pillar_dict, dict):
                continue
            pillar_dict["weight"] = pillar_obj.weight
            for dim_dict in pillar_dict.get("dimensions", []) or []:
                if not isinstance(dim_dict, dict):
                    continue
                dim_key = dim_dict.get("name", "").lower().replace(" ", "_")
                dim_result = result["dimensions"].get(dim_key)
                if dim_result is not None:
                    dim_dict["score"] = dim_result["score"]
            pillar_dict["score"] = result["pillars"].get(pillar_key, 0)

        # Top-level fit_score audit fields
        fs["total"] = result["fit_score"]
        fs["_total"] = result["fit_score"]
        fs["pl_score_pre_ceiling"] = result["pillar_labability_pre_ceiling"]
        fs["ceilings_applied"] = result["ceilings_applied"]
        fs["technical_fit_multiplier"] = result["technical_fit_multiplier"]

        # ── Recompute ACV from motions × deterministic rate ──
        # The AI's job is to estimate per-motion population, adoption %,
        # and hours per learner. Python's job is everything else: per-motion
        # hours, total hours, rate lookup by orchestration method, dollar
        # conversion, and tier assignment from dollar thresholds.
        # Mutates p["acv_potential"] in place; the verdict and the widget
        # both read from the new values immediately.
        scoring_math.compute_acv_potential(p)

        # Recompute the verdict from the new Fit Score and ACV tier — the
        # AI's cached verdict is stale once the math layer rewrites the score.
        acv_tier = (p.get("acv_potential") or {}).get("acv_tier") or "low"
        new_verdict = assign_verdict(result["fit_score"], acv_tier)
        p["verdict"] = {
            "label": new_verdict.label,
            "color": new_verdict.color,
            "fit_label": new_verdict.fit_label,
            "acv_label": new_verdict.acv_label,
        }

        # ── Phase 2: Normalize badges for DISPLAY (does NOT affect math) ──
        # Merges same-named badges within each dimension and promotes color
        # to the worst of the group so risks are visible. Runs strictly
        # AFTER the math + score writeback so it can never silently distort
        # scores. Decision-log principle (2026-04-06): visual changes must
        # never affect scoring.
        _normalize_badges_for_display(p)

    # Sort by computed Fit Score, descending
    products.sort(key=lambda p: (p.get("fit_score") or {}).get("_total", 0), reverse=True)
    analysis["top_products"] = products
    analysis["products"] = products


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

    # Wipe the current analysis's products so they re-score fresh (force_refresh)
    analysis["products"] = []
    from storage_new import save_analysis as _save
    _save(analysis)

    job_id = str(uuid.uuid4())[:8]

    def run_refresh():
        try:
            push(job_id, f"status:Refreshing {len(selected)} products...")
            new_analysis_id, new_product_names = score(
                disc.get("company_name", ""),
                selected, discovery_id,
                discovery_data=disc,
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

    # Backfill company_description and competitive_products from discovery
    # (analyses don't store these directly — they live on the discovery)
    if analysis.get("discovery_id"):
        disc = load_discovery(analysis["discovery_id"])
        if disc:
            if not analysis.get("company_description"):
                analysis["company_description"] = disc.get("company_description", "")
            if not analysis.get("competitive_products"):
                analysis["competitive_products"] = disc.get("competitive_products", [])

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

    return render_template("full_analysis.html",
                          analysis=analysis,
                          selected_product=selected_product,
                          default_index=default_idx)


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
