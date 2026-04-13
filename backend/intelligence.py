"""
Intelligence — the shared platform layer for Skillable Intelligence.

All product research, scoring, and Skillable-specific knowledge flows through
this module. Inspector, Prospector, and Designer call these six operations.
Researcher and scorer are implementation details — callers never import them.

Six named operations
--------------------
    discover(company_name, force_refresh=False)
        Web research + Claude product identification. Returns discovery dict.
        Cached for CACHE_TTL_DAYS; force_refresh bypasses the cache.

    score(company_name, products, discovery_id, force_refresh=False)
        Deep per-product scoring via Prompt Generation System.
        Returns (analysis_id, CompanyAnalysis).
        Runs discrepancy detection after scoring.

    refresh(target_id, scope="all")
        Rerun a specific phase on an existing record.
        Returns updated data dict.

    expand(company_name, additional_products, analysis_id)
        Add products to an existing analysis without re-scoring what's already there.
        Returns (analysis_id, updated CompanyAnalysis).

    qualify(company_name, force_refresh=False)
        Prospector-mode: discovery + scoring at caseboard depth.
        Returns a Prospector-compatible row dict.

    lookup(company_name)
        Pure cache read — no research, no Claude calls.
        Returns {"analysis": dict|None, "discovery": dict|None, "found": bool}.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta

log = logging.getLogger(__name__)

from researcher import discover_products, research_products, research_company_fit, scrape_product_families
from scorer import discover_products_with_claude, score_selected_products, generate_briefcase, _call_claude
from storage import (
    save_analysis, load_analysis,
    save_discovery, load_discovery,
    find_analysis_by_company_name, find_discovery_by_company_name,
    find_analysis_by_discovery_id,
    save_competitor_candidates,
)
from core import (
    assign_verdict, discovery_tier, DISCOVERY_TIER_LABELS,
    company_classification_label, org_badge_color_group,
    score_products_and_sort,
)
from models import CompanyAnalysis, Product
from config import ANTHROPIC_MODEL

# ═══════════════════════════════════════════════════════════════════════════════
# Cache TTL — single definition for the whole platform
# ═══════════════════════════════════════════════════════════════════════════════

from config import CACHE_TTL_DAYS


def cache_is_fresh(timestamp_str: str) -> bool:
    """Return True if an ISO timestamp is within CACHE_TTL_DAYS of now."""
    if not timestamp_str:
        return False
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days < CACHE_TTL_DAYS
    except Exception:
        return False


def _new_id() -> str:
    return str(uuid.uuid4())[:8]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _badge_is_stronger(new_badge: dict, existing: dict) -> bool:
    """Decide whether `new_badge` should replace `existing` in the unified
    Customer Fit merge across products of the same company.

    Rule (Frank's "best showing wins" preference, 2026-04-07):
      1. Strongest strength tier wins (strong > moderate > weak).
      2. Within the same strength tier, prefer the most-positive color
         (green > gray > amber > red), sourced from the canonical color
         scoring values in scoring_config.BADGE_COLOR_POINTS — higher
         numeric value means more positive.
      3. Tiebreak by evidence length (more text = more grounding).

    Rationale: Customer Fit is the company-level "best evidence we have"
    reading. If one product's research found a strong-tier badge for a
    signal_category and another product's research surfaced a weaker
    or more-negative reading, the deeper/stronger research wins. Per
    Frank: "apply the best of the best and make the best showing for
    customer fit possible."

    Returns True if new_badge replaces existing.
    """
    import scoring_config as cfg

    strength_order = {"strong": 3, "moderate": 2, "weak": 1, "": 0}
    new_strength = strength_order.get((new_badge.get("strength") or "").lower(), 0)
    old_strength = strength_order.get((existing.get("strength") or "").lower(), 0)
    if new_strength != old_strength:
        return new_strength > old_strength

    # Same strength tier — prefer the most-positive color, using the
    # canonical points table (higher score = more positive = "best showing")
    fallback = cfg.BADGE_UNKNOWN_COLOR_SCORE_FALLBACK
    new_color_score = cfg.BADGE_COLOR_POINTS.get(
        (new_badge.get("color") or "").lower(), fallback
    )
    old_color_score = cfg.BADGE_COLOR_POINTS.get(
        (existing.get("color") or "").lower(), fallback
    )
    if new_color_score != old_color_score:
        return new_color_score > old_color_score

    # Same strength + same color — tiebreak by evidence length
    new_ev_len = sum(
        len((e.get("claim") or "")) for e in (new_badge.get("evidence") or [])
        if isinstance(e, dict)
    )
    old_ev_len = sum(
        len((e.get("claim") or "")) for e in (existing.get("evidence") or [])
        if isinstance(e, dict)
    )
    return new_ev_len > old_ev_len


def _build_unified_customer_fit(products: list[dict]) -> dict | None:
    """Build the company-level Customer Fit block by aggregating the best
    evidence across every product in an analysis.

    Customer Fit is a property of the ORGANIZATION, not the product — every
    product from the same company gets the same Pillar 3 reading. This
    function builds that one canonical reading from whatever per-product CF
    data the AI produced; the result is then stored on the discovery dict
    (Phase F: discovery["_customer_fit"]) so Inspector, Prospector, and
    Designer can all read it from one place.

    Returns the unified customer_fit dict, or None if there's nothing to
    aggregate (zero products, or no products with CF data).

    Pure function — does NOT mutate the products list. The caller decides
    where to store the result.

    Aggregation logic ("best info wins" per Frank's 2026-04-07 directive):
      1. Collect every Customer Fit badge from every product
      2. Group by signal_category (the rubric-model "what this measures" tag)
      3. Per signal_category, pick the best badge via _badge_is_stronger:
           - Strongest strength tier wins (strong > moderate > weak)
           - Within same strength, prefer the most-positive color
             (sourced from cfg.BADGE_COLOR_POINTS — Define-Once)
           - Tiebreak by evidence length
      4. Build a unified customer_fit block in the canonical dimension order
    """
    products = products or []
    if not products:
        return None

    dim_best: dict[str, dict[str, dict]] = {}
    dim_meta: dict[str, dict] = {}
    dim_best_score: dict[str, int] = {}  # best dim score seen across products
    canonical_dim_order: list[str] = []

    for idx, p in enumerate(products):
        cf = (p.get("fit_score") or {}).get("customer_fit") or {}
        if not isinstance(cf, dict):
            continue
        for dim in cf.get("dimensions", []) or []:
            if not isinstance(dim, dict):
                continue
            dname = dim.get("name", "")
            if not dname:
                continue
            if dname not in dim_meta:
                dim_meta[dname] = {
                    "name": dname,
                    "weight": dim.get("weight", 0),
                }
                dim_best[dname] = {}
                dim_best_score[dname] = 0
                if idx == 0:
                    canonical_dim_order.append(dname)
            # Preserve the dimension score — "best showing wins" applied at
            # the dimension level too. In the current post-rebuild flow every
            # product shares the same CF reading produced once by
            # pillar_3_scorer, so this max() is a no-op. It matters only for
            # legacy data where per-product CF drifted.
            try:
                dim_score = int(dim.get("score") or 0)
            except (TypeError, ValueError):
                dim_score = 0
            if dim_score > dim_best_score[dname]:
                dim_best_score[dname] = dim_score

            for b in dim.get("badges", []) or []:
                if not isinstance(b, dict):
                    continue
                # Group key — prefer signal_category (rubric-model canonical
                # tag); fall back to badge name for any non-rubric badge.
                cat = (b.get("signal_category") or b.get("name") or "").strip()
                if not cat:
                    continue
                existing = dim_best[dname].get(cat)
                if existing is None or _badge_is_stronger(b, existing):
                    dim_best[dname][cat] = b

    # Append any dimensions found on later products that weren't on product 0
    for dname in dim_meta:
        if dname not in canonical_dim_order:
            canonical_dim_order.append(dname)

    if not canonical_dim_order:
        return None

    unified_dims = []
    pillar_score_total = 0
    for dname in canonical_dim_order:
        dim_score = dim_best_score[dname]
        pillar_score_total += dim_score
        unified_dims.append({
            "name": dname,
            "weight": dim_meta[dname]["weight"],
            "badges": list(dim_best[dname].values()),
            "score": dim_score,
        })

    # Pull the pillar-level metadata from the first product that has it
    pillar_weight = 30  # default Pillar 3 weight from cfg.PILLARS
    for p in products:
        cf = (p.get("fit_score") or {}).get("customer_fit") or {}
        if isinstance(cf, dict) and cf.get("weight"):
            pillar_weight = cf["weight"]
            break

    # Pillar score is sum of dim scores, capped at 100 (matches
    # PillarScore.recompute_pillar_score rule). score_override lives in
    # the dict when a Pillar 1 cap fires — not relevant for Pillar 3.
    unified_pillar_score = min(100, pillar_score_total)

    return {
        "name": "Customer Fit",
        "weight": pillar_weight,
        "dimensions": unified_dims,
        "score": unified_pillar_score,
        "score_override": None,
    }


def _apply_customer_fit_to_products(products: list[dict], customer_fit: dict) -> None:
    """Apply a pre-built unified Customer Fit block to every product in an
    analysis. Deep-copies so each product has its own reference and the
    per-product math loop can mutate scores independently without aliasing.

    Used by recompute_analysis() to broadcast the company-level CF (read
    from discovery["_customer_fit"] in the Phase F architecture) onto every
    product so the math loop produces identical Pillar 3 scores across
    products.

    Mutates the products list in place.
    """
    import copy
    if not customer_fit or not products:
        return
    for p in products:
        if not isinstance(p.get("fit_score"), dict):
            p["fit_score"] = {}
        p["fit_score"]["customer_fit"] = copy.deepcopy(customer_fit)


def aggregate_customer_fit_to_discovery(analysis: dict) -> bool:
    """Build the unified company-level Customer Fit from an analysis's
    products and store it on the parent discovery as `_customer_fit`.

    This is the Phase F architectural fix (2026-04-07): Customer Fit lives
    in ONE place — on the discovery dict, owned by the shared Intelligence
    layer — so Inspector, Prospector, and Designer can all read it without
    duplication. The previous interim merged-per-product approach is now
    just a fallback for legacy analyses without discovery._customer_fit.

    Called by intelligence.score() at the end of every score boundary
    (both fresh and cache-and-append paths). Loads the discovery, builds
    the unified CF from the analysis's just-scored products, writes it to
    discovery["_customer_fit"], and re-saves the discovery (preserving the
    existing version stamp + created_at).

    Returns True if a CF was built and stored, False otherwise.
    """
    import scoring_config as cfg

    discovery_id = analysis.get("discovery_id")
    if not discovery_id:
        return False

    products = analysis.get("products") or []
    unified = _build_unified_customer_fit(products)
    if unified is None:
        return False

    discovery = load_discovery(discovery_id)
    if not discovery:
        return False

    discovery["_customer_fit"] = unified
    # Preserve the original created_at + scoring logic version on re-save —
    # adding a derived field is not a re-discovery, so the discovery cache
    # remains valid for its original 45-day window.
    if not discovery.get("_scoring_logic_version"):
        discovery["_scoring_logic_version"] = cfg.SCORING_LOGIC_VERSION
    save_discovery(discovery_id, discovery)
    log.info("Customer Fit aggregated to discovery %s (%d signal categories)",
             discovery_id,
             sum(len(d.get("badges", []) or []) for d in unified.get("dimensions", []) or []))
    return True


def _compute_dominant_color(badges: list[dict]) -> str:
    """Pick the worst-of-group color for a list of badges, for the dimension
    score bar. Returns one of: red, amber, green, gray.

    Rule (matches the historical Jinja macro):
      - red wins if any red and red >= green count
      - amber wins if amber count > green count
      - else green if any green
      - else gray

    HIGH-3 in code-review-2026-04-07.md: this used to be a Jinja macro
    in tools/inspector/templates/_macros.html, re-implementing the same
    logic the Python display normalizer applies. Two implementations of
    the same rule in two languages — guaranteed to drift. Now lives once
    in Python and the template just reads dim.dominant_color.
    """
    from collections import defaultdict
    counts: dict[str, int] = defaultdict(int)
    for b in badges:
        if not isinstance(b, dict):
            continue
        c = b.get("color") or "gray"
        counts[c] += 1
    if counts["red"] > 0 and counts["red"] >= counts["green"]:
        return "red"
    if counts["amber"] > counts["green"]:
        return "amber"
    if counts["green"] > 0:
        return "green"
    return "gray"


def hydrate_analysis(analysis: dict) -> None:
    """Idempotently backfill company-context fields on an analysis dict from
    its parent discovery.

    Mutates the analysis dict in place. Sets only fields that aren't already
    populated:
      - company_description
      - competitive_products
      - _company_badge
      - _org_color

    Why this exists: analyses don't store the company-level context fields
    directly — those live on the parent discovery. The dossier UI needs them
    to render the company header widget consistently with the Product
    Selection page (Define-Once: one source of truth for company context,
    both pages display identical name + badge + description).

    HIGH-2 in code-review-2026-04-07.md: this backfill used to live inline
    in the inspector_full_analysis route. Moving it to the intelligence
    layer means Prospector and Designer can hydrate analyses the same way
    when they need company context, without duplicating the load+backfill
    walk in their own route handlers.

    No-op if discovery_id is missing or the discovery file can't be loaded.
    Idempotent — calling on an already-hydrated analysis touches nothing.
    """
    discovery_id = analysis.get("discovery_id")
    if not discovery_id:
        return
    disc = load_discovery(discovery_id)
    if not disc:
        return
    if not analysis.get("company_description"):
        analysis["company_description"] = disc.get("company_description", "")
    if not analysis.get("competitive_products"):
        analysis["competitive_products"] = disc.get("competitive_products", [])
    if not analysis.get("_company_badge"):
        analysis["_company_badge"] = disc.get("_company_badge", "")
    if not analysis.get("_org_color"):
        analysis["_org_color"] = disc.get("_org_color", "")


def _parse_user_base(value: str) -> int:
    """Parse estimated_user_base string to int for sorting.

    Handles "~14M", "~50K", "~2000", "14000000". Returns 0 on failure.
    """
    if not value:
        return 0
    s = str(value).replace("~", "").replace(",", "").strip().upper()
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


def enrich_discovery(discovery: dict) -> None:
    """Idempotently add tier / badge / color fields to a discovery dict.

    Mutates the discovery dict in place. Sets:
      - per-product `_tier` and `_tier_label`
      - top-level `_company_badge` (e.g. "ENTERPRISE SOFTWARE", "TRAINING ORG")
      - top-level `_org_color` (purple / teal / slate-blue group)

    This function is the SINGLE place these fields get computed across the
    platform. Inspector, Prospector, and Designer all call it. discover()
    calls it on every fresh discovery before save. Route handlers that load
    cached discoveries call it after load to ensure old caches get enriched
    too. The implementation is idempotent — re-running on an already-enriched
    discovery is a no-op (the values are deterministic given the same inputs).

    HIGH-1 in code-review-2026-04-07.md: this enrichment used to be computed
    inline in inspector_product_selection() in app.py — a Layer Discipline
    violation. Prospector and Designer would have either had to duplicate
    the logic or import from the Inspector Flask app file.

    Bug-fix note: the previous version of this enrichment in discover() called
    company_classification_label with an empty product list. The route called
    it with the actual products. The route was right — for software companies
    the function needs to inspect product categories to compute the badge.
    The new helper passes the actual products consistently.
    """
    from models import Product

    for p in discovery.get("products", []) or []:
        # Normalize satellite → secondary for old cached data
        if p.get("product_relationship") == "satellite":
            p["product_relationship"] = "secondary"
        # Format estimated_user_base with commas for display (e.g. ~40000 → ~40,000)
        raw_ub = str(p.get("estimated_user_base", ""))
        if raw_ub and raw_ub.replace("~", "").replace(",", "").strip().isdigit():
            num = int(raw_ub.replace("~", "").replace(",", "").strip())
            p["estimated_user_base"] = f"~{num:,}"
        # Support both old field name (discovery_score) and new (rough_labability_score)
        score = p.get("rough_labability_score", p.get("discovery_score", 0))
        if not p.get("_tier"):
            p["_tier"] = discovery_tier(score)
        if not p.get("_tier_label"):
            p["_tier_label"] = DISCOVERY_TIER_LABELS.get(p["_tier"], p["_tier"])

    # Sort products: flagship first, then by estimated user base (popularity)
    # descending. This is the intelligence layer's decision — the UX just
    # renders in the order it receives. GP4: the sort IS the ranking logic.
    def _popularity_sort_key(p: dict) -> tuple:
        relationship = 0 if p.get("product_relationship") == "flagship" else 1  # magic-allowed: sort priority
        user_base = _parse_user_base(p.get("estimated_user_base", ""))
        return (relationship, -user_base)

    products = discovery.get("products", []) or []
    if products:
        products.sort(key=_popularity_sort_key)
        discovery["products"] = products

    org_type = discovery.get("organization_type", "software_company")
    if not discovery.get("_company_badge"):
        product_objs = [
            Product(name=p.get("name", ""), category=p.get("category", ""))
            for p in discovery.get("products", []) or []
        ]
        # Use researcher's classification hint when available (v2 discoveries)
        badge_hint = discovery.get("company_badge", "")
        discovery["_company_badge"] = company_classification_label(
            org_type, product_objs, company_badge_hint=badge_hint,
        )
    if not discovery.get("_org_color"):
        discovery["_org_color"] = org_badge_color_group(org_type)


def recompute_analysis(analysis: dict) -> None:
    """Cache-reload revalidation against a saved analysis dict.

    This is the cache-revalidation contract. Inspector calls it on every
    page load. Prospector batch scoring should call it before rendering
    cached results. Designer (when product context is needed) should call
    it before reading any product's scores.

    POST-REBUILD CONTRACT (Step 5b, 2026-04-08):

    Pillar scores live in the saved analysis — they were computed at
    score-time by the per-pillar Python scorers reading typed fact
    drawers, and they are trusted here. If the saved analysis has a
    stale SCORING_LOGIC_VERSION, the cache-versioning layer at
    intelligence.score() will trigger a fresh per-product re-run
    through the full Score layer (with fresh facts + fresh grades);
    this function never re-runs the pillar scorers against the dict
    representation of a saved analysis.

    What this function DOES do on every page load:
      1. Unify Customer Fit across products (Phase F) — make sure every
         product of the same company shows identical Pillar 3 data
      2. Recompute ACV Potential from the AI's motion estimates using
         acv_calculator (the rate table + motions may have been retuned
         after the analysis was saved)
      3. Reassign verdict from the saved Fit Score + fresh ACV tier
      4. Sort products by Fit Score descending

    What this function DOES NOT do:
      - Re-run Pillar 1/2/3 scorers (trust saved scores)
      - Apply Technical Fit Multiplier (already baked into saved total_override)
      - Normalize badges for display (badge_selector produces canonical
        badges at score time — no runtime normalization needed)
      - Walk badges_by_dimension to feed badge-keyed math (that math is
        deleted in the rebuild — Score reads facts, not badges)

    Layer Discipline: lives in the intelligence layer so all three
    tools share one cache-revalidation path. Route handlers only
    handle true rendering concerns after this function returns.
    """
    import acv_calculator
    from core import assign_verdict

    # ── Unify Customer Fit across products (Phase F) ──────────────────────
    # Customer Fit is a property of the organization, not the product.
    # Every product from the same company must show the same Pillar 3
    # reading. Phase F rule: the canonical home is discovery["_customer_fit"].
    _phase_f_unified_cf: dict | None = None
    discovery_id = analysis.get("discovery_id")
    if discovery_id:
        discovery = load_discovery(discovery_id)
        if discovery:
            _phase_f_unified_cf = discovery.get("_customer_fit")
    if _phase_f_unified_cf is None:
        _phase_f_unified_cf = _build_unified_customer_fit(analysis.get("products") or [])
    if _phase_f_unified_cf is not None:
        _apply_customer_fit_to_products(
            analysis.get("products") or [], _phase_f_unified_cf,
        )

    import scoring_config as cfg
    products = analysis.get("products", [])
    for p in products:
        fs = p.get("fit_score")
        if not isinstance(fs, dict):
            p["fit_score"] = {"total": 0, "_total": 0}
            continue

        # Populate pillar.score on the dict form and precompute per-
        # dimension display fields (score_percentage, dominant_color).
        # PillarScore.score and FitScore.total are stored dataclass
        # fields since 2026-04-08, and the per-pillar scorers set them
        # at score-time. On cache reload we re-derive them from the
        # stored dimension scores so analyses saved before the fields
        # existed still render correctly. This is the single place the
        # rule lives in the dict path — mirrors recompute_pillar_score
        # and recompute_fit_total in models.py.
        pillar_weights: dict[str, int] = {}
        pillar_scores: dict[str, int] = {}
        for pillar_key in ("product_labability", "instructional_value", "customer_fit"):
            pillar_dict = fs.get(pillar_key)
            if not isinstance(pillar_dict, dict):
                continue
            # Per-dimension display fields
            for dim_dict in pillar_dict.get("dimensions") or []:
                if not isinstance(dim_dict, dict):
                    continue
                dim_weight = dim_dict.get("weight") or 1
                dim_score = dim_dict.get("score") or 0
                dim_dict["score_percentage"] = int((dim_score * 100) / dim_weight)
                dim_dict["dominant_color"] = _compute_dominant_color(
                    dim_dict.get("badges") or []
                )
            # Pillar score — override wins, else sum of dim scores capped at 100
            override = pillar_dict.get("score_override")
            if override is not None:
                pillar_score = int(override)
            else:
                pillar_score = min(100, sum(
                    int((d.get("score") or 0))
                    for d in (pillar_dict.get("dimensions") or [])
                ))
            pillar_dict["score"] = pillar_score
            pillar_scores[pillar_key] = pillar_score
            pillar_weights[pillar_key] = int(pillar_dict.get("weight") or 0)

        # Recompute ACV from motions × deterministic rate. The rate
        # table and motion semantics can evolve after the analysis
        # was saved, so this re-run keeps the displayed ACV fresh.
        acv_calculator.compute_acv_potential(p)

        # Fit Score total — ALWAYS recalculate from saved pillar scores
        # using the live composer config (weights, multiplier table).
        # Never trust a cached total_override — weight or multiplier
        # retunes must propagate instantly on every page load.
        pl = pillar_scores.get("product_labability", 0)
        iv = pillar_scores.get("instructional_value", 0)
        cf = pillar_scores.get("customer_fit", 0)
        # Read weights from LIVE config, not cached data — weight
        # retunes must propagate instantly.
        _cfg_weights = {
            p.name.lower().replace(" ", "_"): p.weight
            for p in cfg.PILLARS
        }
        pl_w = _cfg_weights.get("product_labability", 50)
        iv_w = _cfg_weights.get("instructional_value", 20)
        cf_w = _cfg_weights.get("customer_fit", 30)
        from fit_score_composer import get_technical_fit_multiplier
        mult = get_technical_fit_multiplier(pl, p.get("orchestration_method") or "")
        weighted = (
            pl * (pl_w / 100)
            + iv * (iv_w / 100) * mult
            + cf * (cf_w / 100) * mult
        )
        fit_total = max(0, min(100, round(weighted)))
        # Write back so the cached data stays current
        fs["total_override"] = int(fit_total)
        fs["technical_fit_multiplier"] = float(mult)

        acv_tier = (p.get("acv_potential") or {}).get("acv_tier") or "low"
        new_verdict = assign_verdict(int(fit_total), acv_tier)
        p["verdict"] = {
            "label": new_verdict.label,
            "color": new_verdict.color,
            "fit_label": new_verdict.fit_label,
            "acv_label": new_verdict.acv_label,
        }

        # Mirror the authoritative total into the display fields the
        # template reads for sort + hero rendering.
        fs["total"] = int(fit_total)
        fs["_total"] = int(fit_total)

    # Sort by Fit Score, descending
    products.sort(key=lambda p: (p.get("fit_score") or {}).get("_total", 0), reverse=True)
    analysis["top_products"] = products
    analysis["products"] = products

    # ── Company-level ACV computation ──────────────────────────────────
    # Sum per-product ACV across all scored products, then extrapolate
    # to all discovered products proportionally. This is the intelligence
    # layer's job — the template just reads the pre-computed values.
    # Moved from _hero_section.html template 2026-04-12 (template never
    # computes — GP4 Layer Discipline).
    scored_acv_low = 0
    scored_acv_high = 0
    scored_with_acv = 0
    scored_product_names: set[str] = set()
    for p in products:
        acv = p.get("acv_potential") or {}
        if (acv.get("acv_high") or 0) > 0:
            scored_acv_low += acv.get("acv_low") or 0
            scored_acv_high += acv.get("acv_high") or 0
            scored_with_acv += 1
            scored_product_names.add(p.get("name", ""))

    # ── Per-product ACV extrapolation (replaces flat multiplier) ──────
    # Instead of assuming unscored products have the same average ACV as
    # scored ones, estimate each unscored product's ACV from its discovery
    # data: estimated_user_base × conservative adoption × hours × rate.
    # GP3: every number is traceable to a per-product estimate.
    discovery_data = analysis.get("_discovery_data") or {}
    all_discovered = discovery_data.get("products") or []
    unscored_acv = 0
    for dp in all_discovered:
        dp_name = (dp.get("name") or "").strip()
        if dp_name in scored_product_names:
            continue  # already counted via real scoring
        user_base = 0
        try:
            user_base = int(dp.get("estimated_user_base") or 0)
        except (ValueError, TypeError):
            pass
        if user_base <= 0:
            continue
        # Conservative estimate: user_base × 4% adoption × 2 hrs × rate
        # from deployment model. This is deliberately conservative — the
        # deep dive will sharpen it.
        deploy = (dp.get("deployment_model") or "").strip().lower()
        if deploy in ("cloud", "saas-only"):
            rate = cfg.CLOUD_LABS_RATE
        elif deploy == "installable":
            rate = cfg.VM_MID_RATE
        else:
            rate = cfg.VM_LOW_RATE
        rough_acv = user_base * 0.04 * 2 * rate  # magic-allowed: conservative 4% adoption × 2 hrs default
        unscored_acv += rough_acv

    company_acv_low = round(scored_acv_low + unscored_acv)
    company_acv_high = round(scored_acv_high + unscored_acv)
    discovered_count = analysis.get("total_products_discovered") or len(products)

    analysis["_company_acv"] = {
        "company_low": company_acv_low,
        "company_high": company_acv_high,
        "scored_low": scored_acv_low,
        "scored_high": scored_acv_high,
        "scored_count": scored_with_acv,
        "discovered_count": discovered_count,
    }


def _stamp_for_save(data: dict, timestamp_field: str = "analyzed_at") -> dict:
    """Stamp an analysis or discovery dict with the current SCORING_LOGIC_VERSION
    and a fresh timestamp.

    The intelligence layer is the ONLY place that should ever set the version
    stamp + the scoring/discovery timestamp. Storage layer (save_analysis,
    save_discovery) now requires both fields to be present and rejects writes
    that don't have them.

    This helper exists so the score() and discover() functions stamp the same
    way every time and can never accidentally save a record with a stale or
    missing stamp. Briefcase generation does NOT call this — briefcase preserves
    the existing stamps from the loaded dict because it isn't a scoring change.

    timestamp_field: "analyzed_at" for analyses, "created_at" for discoveries.
    """
    import scoring_config as cfg
    data["_scoring_logic_version"] = cfg.SCORING_LOGIC_VERSION
    data[timestamp_field] = _now_iso()
    return data


# Discovery tier ordering for discrepancy detection
_TIER_ORDER = {
    "promising": 0,
    "potential": 1,
    "uncertain": 2,
    "unlikely": 3,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 1 — discover
# ═══════════════════════════════════════════════════════════════════════════════

def discover(company_name: str, known_products: list[str] | None = None,
             force_refresh: bool = False,
             progress_cb=None) -> dict:
    """Web research + Claude product identification.

    Returns the discovery dict (including discovery_id). Saves to storage.
    Hits the 45-day cache unless force_refresh=True OR the cached discovery
    was scored with an older SCORING_LOGIC_VERSION (in which case it's
    treated as stale and re-run automatically — closes the cache versioning
    gap so customers don't see degraded scores after scoring logic changes).

    progress_cb: optional callable accepting a single status string. Invoked
    at each phase boundary so callers (e.g. the SSE route) can stream real
    progress to the discovering page instead of relying on cycling hints.
    """
    import scoring_config as cfg

    def _progress(msg: str) -> None:
        if progress_cb:
            try:
                progress_cb(msg)
            except Exception:
                log.exception("progress_cb raised — ignoring")

    if not force_refresh:
        cached = find_discovery_by_company_name(company_name)
        if cached and cache_is_fresh(cached.get("created_at", "")):
            if not cfg.is_cached_logic_current(cached):
                log.info(
                    "Intelligence.discover: cached discovery for %s is stale "
                    "(logic version %r vs current %r) — re-running",
                    company_name,
                    cached.get("_scoring_logic_version", "<missing>"),
                    cfg.SCORING_LOGIC_VERSION,
                )
            else:
                log.info("Intelligence.discover: cache hit for %s → %s",
                         company_name, cached.get("discovery_id"))
                return cached

    log.info("Intelligence.discover: running research for %s", company_name)
    _progress("Locating the company website…")

    from concurrent.futures import ThreadPoolExecutor
    from researcher import scrape_product_families
    with ThreadPoolExecutor(max_workers=2) as pool:
        family_future = pool.submit(scrape_product_families, company_name)
        _progress("Identifying the product portfolio…")
        findings = discover_products(company_name, known_products)
        _progress("Extracting product families & categories…")
        scraped_families = []
        try:
            scraped_families = family_future.result(timeout=10)
        except Exception as e:
            log.warning("Product family scrape failed for %s: %s", company_name, e)

    _progress("Detecting deployment models & tech stack…")
    discovery = discover_products_with_claude(findings)
    # Log product count for validation — the product definition filter
    # should produce fewer, real products (not 40-60 features/libraries)
    product_count = len(discovery.get("products", []))
    log.info("Intelligence.discover: Claude returned %d products for %s",
             product_count, company_name)

    # ── Post-filter: remove delivery platforms, validate categories ──
    import post_filters
    company_signals = discovery.get("company_signals") or {}
    discovery["products"] = post_filters.filter_discovery_products(
        discovery.get("products", []),
        company_signals,
    )
    if company_signals:
        discovery["company_signals"] = company_signals
    filtered_count = len(discovery.get("products", []))
    if filtered_count < product_count:
        log.info("Intelligence.discover: post-filter reduced %d → %d products",
                 product_count, filtered_count)

    _progress("Mapping competitive products & vendor landscape…")

    # Preserve raw research signals alongside Claude output
    for key in ("training_programs", "atp_signals", "training_catalog",
                "partner_ecosystem", "partner_portal", "cs_signals",
                "lms_signals", "org_contacts", "page_contents",
                "lab_platform_signals"):
        discovery[key] = findings.get(key, [])

    discovery["discovery_id"] = _new_id()
    discovery["known_products"] = known_products or []
    # created_at + version stamp set explicitly via _stamp_for_save right
    # before save below — see CRIT-10 in code-review-2026-04-07.md.

    # Domain-based lab platform detection — already done by researcher
    lab_detections = findings.get("lab_platform_detections", [])
    if lab_detections:
        discovery["_lab_platform_detections"] = lab_detections
        log.info("Intelligence.discover: detected %d lab platform(s) for %s",
                 len(lab_detections), company_name)

    if scraped_families:
        discovery["_scraped_families"] = scraped_families

    # Add tier / badge / color fields via the shared enrichment helper.
    # Single source of truth — Inspector, Prospector, and Designer all call
    # the same function. See HIGH-1 in code-review-2026-04-07.md.
    enrich_discovery(discovery)

    _progress("Categorizing offerings against Skillable taxonomy…")
    # Stamp the discovery with version + created_at right before save.
    # save_discovery will reject the write if either field is missing.
    _stamp_for_save(discovery, timestamp_field="created_at")
    save_discovery(discovery["discovery_id"], discovery)
    log.info("Intelligence.discover: saved discovery %s for %s",
             discovery["discovery_id"], company_name)
    return discovery


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 2 — score
# ═══════════════════════════════════════════════════════════════════════════════

def score(company_name: str, selected_products: list[dict], discovery_id: str,
          discovery_data: dict | None = None,
          research_cache: dict | None = None,
          force_refresh: bool = False,
          progress_cb=None) -> tuple[str, list[str]]:
    """Deep per-product scoring with cache-and-append semantics.

    ARCHITECTURE — One persistent analysis per company (per discovery_id), forever.
    Each Deep Dive run accumulates products into the same analysis. Stable URL.

    LOGIC:
      1. Look up the existing analysis for this discovery_id.
      2. For each selected product, check if it's already scored in the existing analysis.
         - Cached → leave alone
         - New → score it (parallel Claude calls, only for new products)
      3. Append newly scored products to the existing analysis.
      4. Save back to the SAME analysis_id (or create one if first time).

    Returns: (analysis_id, names_of_newly_scored_products)
      The list of newly scored names is used by the briefcase phase to generate
      briefcases ONLY for new products (cached ones keep their cached briefcase).
    """
    from storage import find_analysis_by_discovery_id, save_analysis as _save
    import scoring_config as cfg

    if not discovery_data:
        discovery_data = load_discovery(discovery_id) or {}

    # Look up existing analysis for this discovery — stable URL principle
    existing = find_analysis_by_discovery_id(discovery_id)
    existing_product_names = set()
    if existing:
        # Cache versioning — if the existing analysis was scored with an
        # older SCORING_LOGIC_VERSION, treat ALL its products as stale and
        # force re-score. The analysis_id is preserved (stable URL principle)
        # but every product gets fresh scoring against the current logic.
        # Same behavior when the caller explicitly asks for force_refresh.
        if force_refresh or not cfg.is_cached_logic_current(existing):
            stale_count = len(existing.get("products", []) or [])
            reason = "force_refresh requested" if force_refresh else (
                f"stale logic version "
                f"({existing.get('_scoring_logic_version', '<missing>')!r} "
                f"vs current {cfg.SCORING_LOGIC_VERSION!r})"
            )
            log.info(
                "Intelligence.score: existing analysis %s — %s — wiping %d products",
                existing.get("analysis_id"), reason, stale_count,
            )
            # CRITICAL: wipe the legacy products list so they don't survive
            # the cache-and-append below. Previously this code only blanked
            # existing_product_names, leaving the legacy products in place
            # to be appended onto by new scores — that's how Trellix ended
            # up with 11 products (7 unique + 4 duplicates) all stamped with
            # a current version they were never actually scored under.
            # See investigation 2026-04-06 evening for the full root cause.
            existing["products"] = []
            # Don't pre-stamp here — _stamp_for_save below at the actual
            # save boundary is the only place that should set the stamps.
            # Pre-stamping here would lie about when the data was scored.
        else:
            for p in existing.get("products", []):
                existing_product_names.add(p.get("name", ""))
            log.info("Intelligence.score: existing analysis %s has %d products cached",
                     existing.get("analysis_id"), len(existing_product_names))

    # Split selected products into cached vs new
    new_to_score = [p for p in selected_products if p.get("name") not in existing_product_names]
    cached_count = len(selected_products) - len(new_to_score)
    log.info("Intelligence.score: %d products selected — %d cached, %d new to score",
             len(selected_products), cached_count, len(new_to_score))

    # Fast path: nothing new to score — return the existing analysis as-is
    if existing and not new_to_score:
        log.info("Intelligence.score: ALL selected products cached — returning existing analysis %s",
                 existing.get("analysis_id"))
        # Phase F: backfill the unified Customer Fit onto the discovery if
        # it isn't there yet. Cheap no-op when the discovery already has it.
        try:
            aggregate_customer_fit_to_discovery(existing)
        except Exception:
            log.exception("Phase F aggregate_customer_fit_to_discovery failed for %s",
                          existing.get("analysis_id"))
        return existing.get("analysis_id"), []

    new_product_names = []

    if new_to_score:
        # ── Research → Store layer (Step 2 of the rebuild, 2026-04-08) ──────
        # Per Platform-Foundation.md "Three Layers of Intelligence":
        # Research extracts structured facts → Store holds them → Score reads
        # them deterministically → Badge picks 2-4 storytellers.  This block
        # is Research + Store.  The legacy monolithic scoring call still runs
        # immediately after as a safety net until Step 5 of the rebuild
        # cuts over to pure-Python scoring against the fact drawer.
        #
        # Three structured fact extractions per Deep Dive:
        #   - Pillar 1 ProductLababilityFacts  (per product)
        #   - Pillar 2 InstructionalValueFacts (per product)
        #   - Pillar 3 CustomerFitFacts        (once per company)
        # All run in parallel.  Each is a focused Claude call with a
        # truth-only prompt — no Skillable judgment, no scoring, no badges.
        from researcher import (
            extract_customer_fit_facts,
            extract_instructional_value_facts,
            extract_product_labability_facts,
        )

        log.info("Intelligence.score: Research → Store phase starting for %s (%d new products)",
                 company_name, len(new_to_score))

        # Step 1 of Research → Store: deeper per-product web research.
        # research_products() runs all per-product search queries + page
        # fetches and returns raw search_results + page_contents that the
        # extractors will read.  This was dead code before today — now wired
        # in for real because the legacy "_research_cache" was never written
        # by the discover phase, leaving the monolithic scoring call to
        # invent product evidence from its training data.
        try:
            raw_product_research = research_products(company_name, new_to_score)
        except Exception:
            log.exception("Intelligence.score: research_products failed for %s — proceeding with empty research",
                          company_name)
            raw_product_research = {
                "company_name": company_name,
                "selected_products": new_to_score,
                "search_results": {},
                "page_contents": {},
            }

        # Step 2 of Research → Store: deeper company-level web research.
        # research_company_fit() gathers company-level evidence for the
        # Customer Fit dimensions — same dead-code situation as above.
        try:
            raw_company_research = research_company_fit(company_name, discovery_data)
        except Exception:
            log.exception("Intelligence.score: research_company_fit failed for %s — proceeding with empty research",
                          company_name)
            raw_company_research = {
                "company_name": company_name,
                "customer_fit_research": {},
                "customer_fit_pages": {},
            }

        search_results = raw_product_research.get("search_results", {}) or {}
        page_contents = raw_product_research.get("page_contents", {}) or {}
        cf_research = raw_company_research.get("customer_fit_research", {}) or {}
        cf_pages = raw_company_research.get("customer_fit_pages", {}) or {}

        # Step 3 of Research → Store: parallel structured fact extraction.
        # 2 extractors per product (Pillar 1 + Pillar 2) plus 1 company-level
        # extractor (Pillar 3).  Each extractor is a focused Claude call with
        # a truth-only prompt that produces typed dataclasses — no scoring,
        # no badges, no Skillable judgment.  Defensive: any extractor failure
        # falls back to an empty fact drawer for that product/company so the
        # whole scoring run never crashes.
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from models import (
            CustomerFitFacts, InstructionalValueFacts, ProductLababilityFacts,
        )

        product_labability_by_name: dict[str, ProductLababilityFacts] = {}
        instructional_value_by_name: dict[str, InstructionalValueFacts] = {}
        customer_fit_facts: CustomerFitFacts = CustomerFitFacts()

        # Run all extractors in parallel.  Worker cap protects against
        # rate limits when a single Deep Dive selects many products.
        max_workers = max(3, min(len(new_to_score) * 2 + 1, 8))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {}
            for p in new_to_score:
                pname = p.get("name", "")
                f1 = ex.submit(
                    extract_product_labability_facts,
                    pname, search_results, page_contents,
                    underlying_technologies=p.get("underlying_technologies"),
                )
                futures[f1] = ("p1", pname)
                f2 = ex.submit(
                    extract_instructional_value_facts,
                    pname, search_results, page_contents,
                )
                futures[f2] = ("p2", pname)
            f3 = ex.submit(
                extract_customer_fit_facts,
                company_name, discovery_data, cf_research, cf_pages,
            )
            futures[f3] = ("p3", company_name)

            for future in as_completed(futures, timeout=300):
                kind, key = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    log.warning("Fact extraction (%s/%s) failed: %s", kind, key, e)
                    continue
                if kind == "p1":
                    product_labability_by_name[key] = result
                elif kind == "p2":
                    instructional_value_by_name[key] = result
                elif kind == "p3":
                    customer_fit_facts = result

        log.info("Intelligence.score: Research → Store complete — P1: %d, P2: %d, P3: 1",
                 len(product_labability_by_name), len(instructional_value_by_name))

        # Build the research dict for the legacy monolithic scoring call.
        # We now pass REAL per-product research (search_results + page
        # contents) to the scorer so its product context isn't empty —
        # this alone should sharpen the legacy path while we work toward
        # cutting it over in Step 5.
        research = {
            "company_name": company_name,
            "selected_products": new_to_score,
            "search_results": search_results,
            "page_contents": page_contents,
            "discovery_data": discovery_data,
        }

        # Score only the NEW products in parallel.  The progress_cb
        # emits real per-completion events (not fake upfront dispatch)
        # so the scoring progress modal traces honestly back to actual
        # work completed — GP3 honest progress.
        new_analysis = score_selected_products(research, progress_cb=progress_cb)

        # ── Store layer: attach extracted facts onto Product / CompanyAnalysis ──
        # The fact drawers travel WITH the scored objects so they persist into
        # analysis_<id>.json and become the input substrate for Step 3 (pure
        # Python Pillar 1 scoring) and Step 4 (Pillars 2/3 rubric judgment).
        new_analysis.customer_fit_facts = customer_fit_facts
        for product in new_analysis.products:
            pname = product.name
            if pname in product_labability_by_name:
                product.product_labability_facts = product_labability_by_name[pname]
            if pname in instructional_value_by_name:
                product.instructional_value_facts = instructional_value_by_name[pname]

        # ── Score layer — per-pillar Python scorers populate fit_score ──
        # Three Layers of Intelligence (Platform-Foundation.md): Score reads
        # typed facts directly, never badges. Pure Python. Zero hardcoded
        # numbers. Every score comes from facts + config.
        #
        # Pillar 1 is pure Python via pillar_1_scorer.
        # Pillar 2 and 3 use the narrow Claude-in-Score rubric grader to
        # emit GradedSignal records (qualitative strength tiering is the
        # only step in the Score layer that legitimately needs Claude),
        # then pillar_2_scorer / pillar_3_scorer read those grades
        # deterministically with zero further AI calls.
        #
        # After the three per-pillar scorers finish, fit_score_composer
        # composes the final Fit Score with the Technical Fit Multiplier
        # applied to IV + CF contributions — the asymmetric coupling rule
        # that enforces "weak PL drags IV + CF contribution down."
        from pillar_1_scorer import score_product_labability, derive_orchestration_method
        from rubric_grader import grade_all_for_company, grade_all_for_product
        from pillar_2_scorer import score_instructional_value
        from pillar_3_scorer import score_customer_fit
        from fit_score_composer import compose_fit_score

        log.info(
            "Intelligence.score: Score layer starting for %d products + 1 company",
            len(new_analysis.products),
        )

        # Pillar 3 company-level grading + scoring (runs once, broadcast
        # to every product so all products share the same Customer Fit
        # reading — Phase F rule).
        cf_pillar_score = None
        try:
            cf_grades = grade_all_for_company(new_analysis)
            new_analysis.customer_fit_rubric_grades = cf_grades
            cf_pillar_score = score_customer_fit(
                new_analysis.organization_type,
                cf_grades,
            )
            log.info(
                "Intelligence.score: Pillar 3 score populated (%d dim grades)",
                len(cf_grades),
            )
        except Exception:
            log.exception(
                "Intelligence.score: Pillar 3 rubric grading/scoring failed for %s",
                company_name,
            )

        # Per-product: Pillar 1 + Pillar 2 scoring, then fit-score composition
        composed_count = 0
        for product in new_analysis.products:
            try:
                product.fit_score.product_labability = score_product_labability(
                    product.product_labability_facts
                )
                # Derive orchestration_method from the same facts the scorer
                # used.  This internal field drives ACV rate tier lookup and
                # Technical Fit Multiplier — the user never sees it.  Badges
                # remain fabric-neutral ("Runs in VM", not "Hyper-V").
                product.orchestration_method = derive_orchestration_method(
                    product.product_labability_facts,
                    underlying_technologies=product.underlying_technologies,
                )
            except Exception:
                log.exception(
                    "Intelligence.score: pillar_1_scorer failed for %r",
                    product.name,
                )

            try:
                p_grades = grade_all_for_product(product, new_analysis)
                product.rubric_grades = p_grades
                product.fit_score.instructional_value = score_instructional_value(
                    product.category,
                    p_grades,
                )
            except Exception:
                log.exception(
                    "Intelligence.score: Pillar 2 grading/scoring failed for %r",
                    product.name,
                )

            if cf_pillar_score is not None:
                product.fit_score.customer_fit = cf_pillar_score

            # Final composition — applies the Technical Fit Multiplier
            # and writes fit_score.total_override + .technical_fit_multiplier.
            try:
                compose_fit_score(
                    product.fit_score,
                    product.orchestration_method or "",
                )
                composed_count += 1
            except Exception:
                log.exception(
                    "Intelligence.score: fit_score_composer failed for %r",
                    product.name,
                )

        log.info(
            "Intelligence.score: Fit Score composition complete for %d/%d products",
            composed_count, len(new_analysis.products),
        )

        # ── ACV Potential: build motions from facts + compute dollars ──
        # Reads the per-product Market Demand audience facts (install_base,
        # employee_subset_size, cert_annual_sit_rate) plus the company-level
        # Customer Fit facts (channel_partner_se_population, events_attendance)
        # and populates product.acv_potential with fully computed motion
        # records, annual hours, ACV low/high dollars, and ACV tier.
        # See docs/Platform-Foundation.md → ACV Potential Model and
        # docs/Badging-and-Scoring-Reference.md → ACV Calculation.
        from acv_calculator import compute_acv_on_product
        acv_count = 0
        for product in new_analysis.products:
            try:
                compute_acv_on_product(product, new_analysis)
                acv_count += 1
            except Exception:
                log.exception(
                    "Intelligence.score: compute_acv_on_product failed for %r",
                    product.name,
                )
        log.info(
            "Intelligence.score: ACV Potential computed for %d/%d products",
            acv_count, len(new_analysis.products),
        )

        # ── Step 6-lite: attach display badges via badge_selector ──
        # After the cutover flip, fit_score contains the authoritative Python-
        # scored PillarScore objects with EMPTY badges lists. Badge selector
        # populates the badges list on each DimensionScore as a post-scoring
        # display concern — does not modify scores, only adds display metadata.
        # Reads the fact drawer + rubric grades + the computed pillar scores
        # and emits Badge objects per the naming rules locked 2026-04-08.
        from badge_selector import attach_badges_to_product
        badge_count = 0
        for product in new_analysis.products:
            try:
                attach_badges_to_product(product, new_analysis)
                badge_count += 1
            except Exception:
                log.exception(
                    "Intelligence.score: badge_selector failed for product %r — skipping",
                    product.name,
                )
        log.info(
            "Intelligence.score: Step 6-lite badge selector populated badges for %d/%d products",
            badge_count, len(new_analysis.products),
        )

        # Assign verdicts AFTER the cutover so they're based on the new scores
        for product in new_analysis.products:
            acv_tier = product.acv_potential.acv_tier or "medium"
            product.verdict = assign_verdict(product.fit_score.total, acv_tier)

        # Convert to dicts for merging into the existing analysis
        from dataclasses import asdict
        new_product_dicts = [asdict(p) for p in new_analysis.products]
        new_product_names = [p["name"] for p in new_product_dicts]

    if existing:
        # Append new products to existing analysis (preserves analysis_id and URL)
        existing_dict = existing
        if new_to_score:
            existing_dict["products"].extend(new_product_dicts)
            # Re-sort by fit_score total descending
            existing_dict["products"].sort(
                key=lambda p: (p.get("fit_score", {}) or {}).get("total", 0)
                              if isinstance(p.get("fit_score"), dict)
                              else 0,
                reverse=True,
            )
            existing_dict["total_products_discovered"] = len(discovery_data.get("products", []))
            # Stamp the just-modified analysis. analyzed_at gets bumped because
            # the analysis WAS just modified by appending new scored products.
            # See HIGH-7 in code-review-2026-04-07.md — this fixes the gap
            # where cache-and-append left a stale timestamp on the parent.
            _stamp_for_save(existing_dict)
            _save(existing_dict)
            log.info("Intelligence.score: appended %d new products to analysis %s",
                     len(new_product_dicts), existing_dict.get("analysis_id"))
        # Phase F: write the unified Customer Fit onto the discovery so
        # every tool reads it from one canonical place. Runs on cache-and-
        # append paths (including the no-new-products fast-return below
        # via the early-return path — handled there separately).
        try:
            aggregate_customer_fit_to_discovery(existing_dict)
        except Exception:
            log.exception("Phase F aggregate_customer_fit_to_discovery failed for %s",
                          existing_dict.get("analysis_id"))
        return existing_dict.get("analysis_id"), new_product_names

    # First-ever analysis for this discovery — save fresh with all new products
    new_analysis.discovery_id = discovery_id
    new_analysis.total_products_discovered = len(discovery_data.get("products", []))
    score_products_and_sort(new_analysis)
    new_analysis.briefcase = None  # Briefcase moved to product level
    # Convert to dict + stamp before save. The dataclass no longer carries
    # analyzed_at via default_factory (CRIT-6) so this is the canonical
    # moment to set both stamps for a fresh analysis.
    from dataclasses import asdict
    fresh_dict = asdict(new_analysis)
    _stamp_for_save(fresh_dict)
    analysis_id = save_analysis(fresh_dict)
    log.info("Intelligence.score: created new analysis %s with %d products",
             analysis_id, len(new_analysis.products))
    # Phase F: write the unified Customer Fit onto the discovery so every
    # tool (Inspector, Prospector, Designer) reads it from one canonical
    # place instead of recomputing per analysis.
    try:
        aggregate_customer_fit_to_discovery(fresh_dict)
    except Exception:
        log.exception("Phase F aggregate_customer_fit_to_discovery failed for %s", analysis_id)
    return analysis_id, new_product_names


def _build_briefcase_context_from_dict(p_dict: dict, company_context: str) -> str:
    """Build the per-product context string for briefcase generation, directly from
    a saved product dict (no Product object reconstruction needed).

    The saved JSON shape has contacts as a list and fit_score as a nested dict.
    This function extracts what generate_briefcase's prompt needs.
    """
    import json
    fit_score = p_dict.get("fit_score", {}) or {}
    pl = fit_score.get("product_labability", {}) or {}
    iv = fit_score.get("instructional_value", {}) or {}
    cf = fit_score.get("customer_fit", {}) or {}
    verdict = p_dict.get("verdict") or {}
    contacts_raw = p_dict.get("contacts", []) or []
    # Contacts may be a list (saved format) or a dict by role type (legacy)
    if isinstance(contacts_raw, dict):
        contacts_list = []
        for role_type, c in contacts_raw.items():
            if isinstance(c, dict) and c.get("name"):
                contacts_list.append({
                    "name": c.get("name", ""),
                    "title": c.get("title", ""),
                    "role_type": role_type,
                })
    else:
        contacts_list = [
            {
                "name": c.get("name", ""),
                "title": c.get("title", ""),
                "role_type": c.get("role_type", ""),
            }
            for c in contacts_raw if isinstance(c, dict) and c.get("name")
        ]

    scoring_summary = json.dumps({
        "product": p_dict.get("name", ""),
        "fit_score": fit_score.get("total", 0),
        "product_labability": pl.get("score", 0),
        "instructional_value": iv.get("score", 0),
        "customer_fit": cf.get("score", 0),
        "deployment_model": p_dict.get("deployment_model", ""),
        "orchestration_method": p_dict.get("orchestration_method", ""),
        "verdict": verdict.get("label", "") if isinstance(verdict, dict) else "",
        "contacts": contacts_list,
    }, indent=2)

    return f"## Scoring Results\n{scoring_summary}\n\n{company_context}"


def generate_briefcase_for_analysis(analysis_id: str,
                                    only_for_products: list[str] | None = None) -> bool:
    """Phase B: Generate Seller Briefcases for products in an analysis.

    Briefcase is per-product. Each product gets THREE Claude calls in parallel:
    Key Technical Questions (Opus), Conversation Starters (Haiku), Account
    Intelligence (Haiku). Across N products that's 3N parallel calls.

    only_for_products: if provided, generate ONLY for those product names.
                      Default: skip any product that already has a briefcase.

    Safe to run in a background thread. Returns True on success.
    """
    from storage import load_analysis as _load, save_analysis as _save
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from scorer import (
        _generate_briefcase_section,
        _KTQ_SYSTEM_PROMPT, _STARTERS_SYSTEM_PROMPT, _ACCT_SYSTEM_PROMPT,
        _BRIEFCASE_KTQ_MODEL, _BRIEFCASE_STARTERS_MODEL, _BRIEFCASE_ACCT_MODEL,
    )

    analysis_dict = _load(analysis_id)
    if not analysis_dict:
        log.error("generate_briefcase_for_analysis: analysis %s not found", analysis_id)
        return False

    company_name = analysis_dict.get("company_name", "")
    discovery_id = analysis_dict.get("discovery_id", "")
    discovery_data = load_discovery(discovery_id) or {}
    company_context = _build_company_context_for_briefcase(company_name, discovery_data)

    products_dicts = analysis_dict.get("products", [])

    # Decide which products need a briefcase
    target_names = set(only_for_products or [])
    products_to_generate = []  # list of (index, product_dict)
    for i, p_dict in enumerate(products_dicts):
        name = p_dict.get("name", "")
        already_has = p_dict.get("briefcase") is not None
        wanted = (not target_names) or (name in target_names)
        if wanted and not already_has:
            products_to_generate.append((i, p_dict))

    if not products_to_generate:
        log.info("Briefcase: nothing to generate for analysis %s — all targeted products cached",
                 analysis_id)
        return True

    log.info("Briefcase: generating for analysis %s (%d products: %s)",
             analysis_id, len(products_to_generate),
             ", ".join(p["name"] for _, p in products_to_generate))

    # Build flat list of (product_idx, section_key, prompt, model, max_tokens, user_content)
    SECTIONS = [
        ("ktq", _KTQ_SYSTEM_PROMPT, _BRIEFCASE_KTQ_MODEL, 800),
        ("starters", _STARTERS_SYSTEM_PROMPT, _BRIEFCASE_STARTERS_MODEL, 500),
        ("acct", _ACCT_SYSTEM_PROMPT, _BRIEFCASE_ACCT_MODEL, 500),
    ]

    work_items = []  # (product_idx, section_key, system_prompt, model, max_tokens, user_content)
    for idx, p_dict in products_to_generate:
        user_content = _build_briefcase_context_from_dict(p_dict, company_context)
        for section_key, system_prompt, model, max_tokens in SECTIONS:
            work_items.append((idx, section_key, system_prompt, model, max_tokens, user_content))

    # Run ALL section calls in parallel — across all products and all sections
    # 3 products × 3 sections = 9 parallel calls; gated by slowest Opus call
    section_results = {}  # (idx, section_key) -> bullets list
    with ThreadPoolExecutor(max_workers=min(len(work_items), 12)) as executor:
        futures = {
            executor.submit(_generate_briefcase_section, sp, model, uc, max_tok): (idx, key)
            for idx, key, sp, model, max_tok, uc in work_items
        }
        for future in as_completed(futures):
            idx, key = futures[future]
            try:
                bullets = future.result()
                section_results[(idx, key)] = bullets or []
            except Exception as e:
                log.error("Briefcase section failed for product %d %s: %s", idx, key, e)
                section_results[(idx, key)] = []

    # Assemble per-product briefcases and write back
    PILLARS = {"ktq": "Product Labability", "starters": "Instructional Value", "acct": "Customer Fit"}
    HEADINGS = {"ktq": "Key Technical Questions", "starters": "Conversation Starters", "acct": "Account Intelligence"}
    KEY_NAMES = {"ktq": "key_technical_questions", "starters": "conversation_starters", "acct": "account_intelligence"}

    for idx, _ in products_to_generate:
        briefcase_dict = {}
        for section_key in ("ktq", "starters", "acct"):
            briefcase_dict[KEY_NAMES[section_key]] = {
                "pillar": PILLARS[section_key],
                "heading": HEADINGS[section_key],
                "bullets": section_results.get((idx, section_key), []),
            }
        # Reload-modify-save to be safe with concurrent writes
        current = _load(analysis_id) or analysis_dict
        try:
            current["products"][idx]["briefcase"] = briefcase_dict
            # Per-product briefcase timestamp (HIGH-5 in code-review-2026-04-07.md).
            # Lets the dossier polling JS distinguish "briefcase still
            # generating" from "briefcase complete" on a per-product basis,
            # and gives an audit trail for when each briefcase was last
            # refreshed. NOT the analysis-level analyzed_at — briefcase
            # generation is intentionally NOT a scoring change, so the
            # parent analysis stamp is preserved.
            current["products"][idx]["briefcase_generated_at"] = _now_iso()
            _save(current)
            analysis_dict = current
            log.info("Briefcase: saved for product %d (%s) of analysis %s",
                     idx, current["products"][idx].get("name"), analysis_id)
        except Exception as e:
            log.error("Briefcase: failed to save for product %d: %s", idx, e)

    log.info("Briefcase: generation complete for analysis %s", analysis_id)
    return True


def _build_company_context_for_briefcase(company_name: str, discovery_data: dict) -> str:
    """Build company context string for the Seller Briefcase AI call."""
    lines = [f"# Company: {company_name}\n"]
    if discovery_data.get("company_description"):
        lines.append(f"**Description:** {discovery_data['company_description']}")
    if discovery_data.get("organization_type"):
        lines.append(f"**Organization type:** {discovery_data['organization_type']}")

    # Training signals
    for key in ("training_programs", "atp_signals"):
        items = discovery_data.get(key, [])
        if items:
            lines.append(f"\n## {key.replace('_', ' ').title()}")
            for r in items[:5]:
                lines.append(f"- {r.get('title', '')} — {r.get('snippet', '')}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 3 — refresh
# ═══════════════════════════════════════════════════════════════════════════════

def refresh(target_id: str, scope: str = "all") -> dict:
    """Rerun discovery or scoring on an existing record.

    scope: "discovery" | "products" | "all"
    """
    analysis_data = load_analysis(target_id)
    if not analysis_data:
        discovery_data = load_discovery(target_id)
        if discovery_data:
            return discover(discovery_data.get("company_name", ""), force_refresh=True)
        raise ValueError(f"No record found for ID: {target_id}")

    company_name = analysis_data.get("company_name", "")
    discovery_id = analysis_data.get("discovery_id", "")

    if scope in ("discovery", "all"):
        discover(company_name, force_refresh=True)

    if scope in ("products", "all"):
        products = analysis_data.get("products", [])
        selected = [{"name": p.get("name", "")} for p in products]
        _, updated = score(company_name, selected, discovery_id, force_refresh=True)
        return {"analysis_id": target_id, "status": "refreshed", "scope": scope}

    return {"analysis_id": target_id, "status": "refreshed", "scope": scope}


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 4 — expand
# ═══════════════════════════════════════════════════════════════════════════════

def expand(company_name: str, additional_products: list[dict],
           analysis_id: str) -> tuple[str, dict]:
    """Add products to an existing analysis without re-scoring existing ones."""
    existing = load_analysis(analysis_id)
    if not existing:
        raise ValueError(f"Analysis {analysis_id} not found")

    discovery_id = existing.get("discovery_id", "")
    new_id, updated = score(company_name, additional_products, discovery_id)

    log.info("Intelligence.expand: added %d products to %s → new analysis %s",
             len(additional_products), analysis_id, new_id)
    return new_id, updated


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 5 — qualify (Prospector mode)
# ═══════════════════════════════════════════════════════════════════════════════

def qualify(company_name: str, force_refresh: bool = False) -> dict | None:
    """Prospector-mode: discovery-depth research + scoring.

    Returns a Prospector-compatible row dict, or None if company has no products.
    Both Prospector batch scoring and Caseboard use this same depth.
    """
    # Run discovery
    disc = discover(company_name, force_refresh=force_refresh)
    if not disc or not disc.get("products"):
        return _no_fit_row(company_name, disc)

    products = disc.get("products", [])

    # Find top product by rough labability score (v2) with discovery_score fallback (v1)
    sorted_prods = sorted(products, key=lambda p: p.get("rough_labability_score", p.get("discovery_score", 0)), reverse=True)
    top = sorted_prods[0]

    # Use discovery-level data to build Prospector row
    fit = top.get("rough_labability_score", top.get("discovery_score", 0))
    tier = discovery_tier(fit)

    # Contacts
    contacts = disc.get("_contacts", [])
    dm = next((c for c in contacts if c.get("role_type") == "decision_maker"), {})
    inf = next((c for c in contacts if c.get("role_type") == "influencer"), {})

    return {
        "company_name": company_name,
        "company_url": disc.get("company_url", ""),
        "top_product": top.get("name", ""),
        "fit_score": fit,
        "orchestration_method": top.get("orchestration_method", ""),
        "verdict": DISCOVERY_TIER_LABELS.get(tier, tier),
        "top_contact_name": dm.get("name", ""),
        "top_contact_title": dm.get("title", ""),
        "top_contact_linkedin": dm.get("linkedin_url", ""),
        "second_contact_name": inf.get("name", ""),
        "second_contact_title": inf.get("title", ""),
        "second_contact_linkedin": inf.get("linkedin_url", ""),
        "analysis_id": disc.get("discovery_id", ""),
        "hubspot_icp_context": "",  # Generated on write-back to HubSpot (GP5)
    }


def _no_fit_row(company_name: str, discovery: dict | None) -> dict:
    """Build a Prospector row for a company with no viable products."""
    return {
        "company_name": company_name,
        "company_url": discovery.get("company_url", "") if discovery else "",
        "top_product": "",
        "fit_score": 0,
        "orchestration_method": "Not a Fit",
        "verdict": "Unlikely",
        "top_contact_name": "",
        "top_contact_title": "",
        "top_contact_linkedin": "",
        "second_contact_name": "",
        "second_contact_title": "",
        "second_contact_linkedin": "",
        "analysis_id": "",
        "hubspot_icp_context": "",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 6 — lookup
# ═══════════════════════════════════════════════════════════════════════════════

def lookup(company_name: str) -> dict:
    """Pure cache read — no research, no Claude calls.

    Returns {"analysis": dict|None, "discovery": dict|None, "found": bool}.
    """
    analysis = find_analysis_by_company_name(company_name)
    discovery = find_discovery_by_company_name(company_name)
    return {
        "analysis": analysis,
        "discovery": discovery,
        "found": bool(analysis or discovery),
    }
