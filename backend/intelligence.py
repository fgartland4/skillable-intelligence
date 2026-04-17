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


# ─────────────────────────────────────────────────────────────────────────
# Dict → dataclass reconstruction
#
# When intelligence.score() enters the "stale math/rubric, rescore from
# saved facts" path (Frank 2026-04-16 Rule #1), it needs to reconstruct
# typed dataclasses from the serialized-dict form stored on disk. The
# pillar scorers + rubric grader expect dataclass objects (attribute
# access: `facts.provisioning.has_sandbox_api`), not dicts.
#
# Standard `dataclasses` has asdict() but no from_dict(). This helper
# closes that gap for the specific types the Score layer consumes.
# Generic enough to walk nested dataclasses, list[dataclass], and
# dict[str, dataclass] fields — sufficient for ProductLababilityFacts,
# InstructionalValueFacts, CustomerFitFacts, and GradedSignal.
# ─────────────────────────────────────────────────────────────────────────

def _dict_to_dataclass(cls, data):
    """Reconstruct a dataclass instance from a dict, walking nested types.

    Handles:
      - Plain dataclass fields (recurses)
      - list[SomeDataclass] (reconstructs each element)
      - dict[str, SomeDataclass] (reconstructs each value)
      - Optional[SomeDataclass] (unwraps and recurses)
      - Primitives (pass through)

    Returns cls() with defaults if `data` is None or not a dict. Ignores
    keys in `data` that aren't fields of `cls` — forward-compatible with
    old caches that carry extra keys from legacy shapes.

    On any coercion error, falls back to the default for that field so
    one malformed field doesn't crash the whole reconstruction. A legacy
    cache that predates a field addition returns a fresh default there.
    """
    import dataclasses
    import typing
    if data is None:
        try:
            return cls()
        except TypeError:
            return data
    if not isinstance(data, dict):
        return data
    if not dataclasses.is_dataclass(cls):
        return data

    try:
        hints = typing.get_type_hints(cls)
    except Exception:
        hints = {}

    kwargs = {}
    for f in dataclasses.fields(cls):
        if f.name not in data:
            continue
        raw = data[f.name]
        field_type = hints.get(f.name, f.type)
        try:
            kwargs[f.name] = _coerce_value(field_type, raw)
        except Exception as exc:
            log.debug(
                "_dict_to_dataclass: field %s.%s coercion failed (%s); "
                "using default", cls.__name__, f.name, exc,
            )
    try:
        return cls(**kwargs)
    except TypeError as exc:
        log.warning(
            "_dict_to_dataclass: instantiation failed for %s (%s); "
            "falling back to defaults", cls.__name__, exc,
        )
        return cls()


def _coerce_value(field_type, val):
    """Coerce a raw (dict/list/primitive) value to its declared dataclass type."""
    import dataclasses
    import typing
    if val is None:
        return None

    origin = typing.get_origin(field_type)
    args = typing.get_args(field_type)

    # Unwrap Optional[X] / Union[X, None]
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _coerce_value(non_none[0], val)
        # Unhandled multi-type unions — pass through as-is
        return val

    # list[X]
    if origin is list:
        inner = args[0] if args else None
        if inner and dataclasses.is_dataclass(inner) and isinstance(val, list):
            return [
                _dict_to_dataclass(inner, v) if isinstance(v, dict) else v
                for v in val
            ]
        return val if isinstance(val, list) else val

    # dict[K, V]
    if origin is dict:
        inner_val = args[1] if len(args) >= 2 else None
        if inner_val and dataclasses.is_dataclass(inner_val) and isinstance(val, dict):
            return {
                k: _dict_to_dataclass(inner_val, v) if isinstance(v, dict) else v
                for k, v in val.items()
            }
        return val if isinstance(val, dict) else val

    # Plain dataclass
    if dataclasses.is_dataclass(field_type) and isinstance(val, dict):
        return _dict_to_dataclass(field_type, val)

    # Primitive or unknown — pass through
    return val


# ─────────────────────────────────────────────────────────────────────────
# Rescore from saved facts (Stage 2 of Frank's Rule #1 enforcement)
#
# When intelligence.score() detects a stale scored record (math or rubric
# version differs from current) AND the fact drawers are intact, rescore
# against the saved facts rather than wiping + re-researching. This is
# the path that makes Rule #1 structurally true in practice — the saved
# research investment is preserved across every logic retune.
#
# Two modes:
#   regrade=False (MATH_STALE):
#     Pure-Python rescore. Saved rubric grades reused as-is. Zero Claude.
#   regrade=True  (RUBRIC_STALE):
#     Re-run rubric_grader against saved raw facts. Then Python rescore.
#     Paid Claude calls for grading; zero re-research.
# ─────────────────────────────────────────────────────────────────────────


def _reconstruct_product(p_dict: dict):
    """Reconstruct a Product dataclass with its fact drawers + rubric grades
    from the saved dict form. Used by the rescore path so the pillar
    scorers can operate on typed objects.
    """
    from models import (
        Product,
        ProductLababilityFacts,
        InstructionalValueFacts,
        GradedSignal,
    )

    pl_facts = _dict_to_dataclass(
        ProductLababilityFacts, p_dict.get("product_labability_facts") or {},
    )
    iv_facts = _dict_to_dataclass(
        InstructionalValueFacts, p_dict.get("instructional_value_facts") or {},
    )

    rubric_grades: dict[str, list] = {}
    raw_grades = p_dict.get("rubric_grades") or {}
    if isinstance(raw_grades, dict):
        for dim_key, raw_list in raw_grades.items():
            if not isinstance(raw_list, list):
                continue
            rubric_grades[dim_key] = [
                _dict_to_dataclass(GradedSignal, g)
                for g in raw_list if isinstance(g, dict)
            ]

    return Product(
        name=p_dict.get("name", ""),
        category=p_dict.get("category", ""),
        subcategory=p_dict.get("subcategory", ""),
        description=p_dict.get("description", ""),
        product_url=p_dict.get("product_url", ""),
        deployment_model=p_dict.get("deployment_model", ""),
        orchestration_method=p_dict.get("orchestration_method", ""),
        vendor_official_acronym=p_dict.get("vendor_official_acronym", ""),
        underlying_technologies=p_dict.get("underlying_technologies") or [],
        annual_enrollments_estimate=int(p_dict.get("annual_enrollments_estimate") or 0),
        annual_enrollments_evidence=p_dict.get("annual_enrollments_evidence", ""),
        annual_enrollments_confidence=p_dict.get("annual_enrollments_confidence", ""),
        user_personas=p_dict.get("user_personas") or [],
        product_labability_facts=pl_facts,
        instructional_value_facts=iv_facts,
        rubric_grades=rubric_grades,
    )


def _reconstruct_company_analysis(analysis_dict: dict, products: list):
    """Reconstruct a minimal CompanyAnalysis dataclass carrying the company-
    level customer_fit_facts + rubric grades, plus the reconstructed
    products. Used by the rescore path for Pillar 3 scoring and grading.
    """
    from models import CompanyAnalysis, CustomerFitFacts, GradedSignal

    cf_facts = _dict_to_dataclass(
        CustomerFitFacts, analysis_dict.get("customer_fit_facts") or {},
    )

    cf_grades: dict[str, list] = {}
    raw_cf = analysis_dict.get("customer_fit_rubric_grades") or {}
    if isinstance(raw_cf, dict):
        for dim_key, raw_list in raw_cf.items():
            if not isinstance(raw_list, list):
                continue
            cf_grades[dim_key] = [
                _dict_to_dataclass(GradedSignal, g)
                for g in raw_list if isinstance(g, dict)
            ]

    return CompanyAnalysis(
        company_name=analysis_dict.get("company_name", ""),
        company_url=analysis_dict.get("company_url"),
        company_description=analysis_dict.get("company_description", ""),
        organization_type=analysis_dict.get("organization_type", "software_company"),
        products=products,
        customer_fit_facts=cf_facts,
        customer_fit_rubric_grades=cf_grades,
        analyzed_at=analysis_dict.get("analyzed_at", ""),
        analysis_id=analysis_dict.get("analysis_id", ""),
        discovery_id=analysis_dict.get("discovery_id", ""),
        total_products_discovered=int(analysis_dict.get("total_products_discovered") or 0),
    )


def rescore_products_from_saved_facts(
    analysis: dict, regrade: bool = False,
) -> int:
    """Rescore every product in a cached analysis without re-researching.

    Reconstructs Product + CompanyAnalysis dataclass objects from the
    saved dict form, runs the pillar scorers against them, and writes
    the fresh pillar scores + badges + ACV back onto the analysis dict.

    Args:
        analysis: the saved analysis dict (mutated in place)
        regrade: when True, re-runs rubric_grader against saved raw
            facts before scoring (paid Claude calls per Pillar 2/3
            dimension). When False, saved rubric grades are reused
            directly — pure Python rescore, zero Claude calls.

    Returns the number of products successfully rescored. Products
    with missing / malformed fact drawers are skipped (caller can
    then decide whether to selectively re-research just those).

    NOTE: this function does NOT save the analysis. The caller
    (intelligence.score) is responsible for stamping versions via
    _stamp_for_save and persisting via save_analysis.
    """
    from pillar_1_scorer import (
        score_product_labability, derive_orchestration_method,
    )
    from pillar_2_scorer import score_instructional_value
    from pillar_3_scorer import score_customer_fit
    from fit_score_composer import compose_fit_score
    from acv_calculator import compute_acv_on_product
    from badge_selector import attach_badges_to_product
    from core import assign_verdict
    from dataclasses import asdict

    products_dict = analysis.get("products") or []
    if not products_dict:
        return 0

    # Skip products with no fact drawer at all — reconstruction would
    # produce meaningless defaults. Caller handles these separately
    # (selective re-research for legacy records without facts).
    rescorable: list[tuple[int, dict]] = []
    for idx, p_dict in enumerate(products_dict):
        pl_facts = p_dict.get("product_labability_facts") or {}
        if not pl_facts.get("provisioning"):
            log.info(
                "rescore: product %r has no Pillar 1 fact drawer — skipping",
                p_dict.get("name"),
            )
            continue
        rescorable.append((idx, p_dict))

    if not rescorable:
        return 0

    # Reconstruct Product dataclasses
    reconstructed = [(idx, _reconstruct_product(p)) for idx, p in rescorable]
    company = _reconstruct_company_analysis(
        analysis, [r[1] for r in reconstructed],
    )

    # ── Pillar 3 (company-level) — once per analysis ──
    cf_pillar_score = None
    if regrade:
        try:
            from rubric_grader import grade_all_for_company
            cf_grades = grade_all_for_company(company)
            company.customer_fit_rubric_grades = cf_grades
        except Exception:
            log.exception("rescore: Pillar 3 re-grade failed — using saved grades")
            cf_grades = company.customer_fit_rubric_grades or {}
    else:
        cf_grades = company.customer_fit_rubric_grades or {}

    try:
        cf_pillar_score = score_customer_fit(company.organization_type, cf_grades)
    except Exception:
        log.exception("rescore: Pillar 3 score_customer_fit failed")

    # ── Per-product: Pillar 1 + Pillar 2 + compose + ACV + badges ──
    successes = 0
    for idx, product in reconstructed:
        try:
            product.fit_score.product_labability = score_product_labability(
                product.product_labability_facts,
            )
            product.orchestration_method = derive_orchestration_method(
                product.product_labability_facts,
                underlying_technologies=product.underlying_technologies,
            )
        except Exception:
            log.exception(
                "rescore: pillar_1_scorer failed for %r — skipping product",
                product.name,
            )
            continue

        # Archetype classification — deterministic Python, zero Claude.
        # Drives IV ceiling in Pillar 2 + ACV floors. Frank 2026-04-16.
        try:
            from archetype_classifier import classify_archetype
            product.archetype, product.archetype_rationale = classify_archetype(
                product, analysis,
            )
        except Exception:
            log.exception("rescore: classify_archetype failed for %r", product.name)

        # Pillar 2 — regrade or reuse saved grades
        if regrade:
            try:
                from rubric_grader import grade_all_for_product
                p_grades = grade_all_for_product(product, company)
                product.rubric_grades = p_grades
            except Exception:
                log.exception(
                    "rescore: Pillar 2 re-grade failed for %r — using saved",
                    product.name,
                )
                p_grades = product.rubric_grades or {}
        else:
            p_grades = product.rubric_grades or {}

        try:
            product.fit_score.instructional_value = score_instructional_value(
                product.category, p_grades,
                archetype=product.archetype or "",
            )
        except Exception:
            log.exception("rescore: pillar_2_scorer failed for %r", product.name)

        if cf_pillar_score is not None:
            product.fit_score.customer_fit = cf_pillar_score

        try:
            compose_fit_score(
                product.fit_score, product.orchestration_method or "",
            )
        except Exception:
            log.exception("rescore: compose_fit_score failed for %r", product.name)

        try:
            compute_acv_on_product(product, company)
        except Exception:
            log.exception("rescore: compute_acv_on_product failed for %r", product.name)

        try:
            attach_badges_to_product(product, company)
        except Exception:
            log.exception("rescore: attach_badges failed for %r", product.name)

        acv_tier = product.acv_potential.acv_tier or "medium"
        product.verdict = assign_verdict(product.fit_score.total, acv_tier)

        # Write the freshly scored Product back into the analysis dict form
        products_dict[idx] = asdict(product)
        successes += 1

    # Also write back the re-graded customer fit facts + grades onto the
    # analysis dict so downstream Phase F aggregation sees the fresh values.
    if regrade:
        analysis["customer_fit_rubric_grades"] = {
            k: [asdict(g) for g in v] for k, v in (company.customer_fit_rubric_grades or {}).items()
        }

    log.info(
        "rescore_products_from_saved_facts: rescored %d/%d products (regrade=%s)",
        successes, len(rescorable), regrade,
    )
    return successes


# ─────────────────────────────────────────────────────────────────────────
# Compound-research merge — best-of-best across discovery runs
#
# Frank 2026-04-16: when a second research run for the same company finds
# less than a prior run (thinner search results, missed docs page, AI
# non-determinism), the new discovery should NOT regress the prior findings.
# Persistent signals (has_api, is_flagship, confirmed estimated_user_base)
# stay carried forward; freshness signals (rough_labability_score, holistic
# ACV, organization_type classification) prefer the newer run.
#
# Mirrors the `_build_unified_customer_fit` best-of-best pattern already in
# use inside a single analysis — extended to "best of best across discovery
# runs of the same company".
# ─────────────────────────────────────────────────────────────────────────

_CONFIDENCE_RANK = {"confirmed": 3, "indicated": 2, "inferred": 1, "": 0}
_RELATIONSHIP_RANK = {"flagship": 3, "secondary": 2, "satellite": 2, "standalone": 1, "": 0}


def _merge_product_entry(existing: dict, new: dict) -> dict:
    """Merge one product's discovery-level fields — best-of-best per field.

    Returns a merged dict. Neither input is mutated. The new dict's field
    values win when they're non-empty and the existing is empty; otherwise
    per-field rules (confidence rank, longer narrative wins, persistent-
    truth preservation) apply.
    """
    merged: dict = dict(new)  # start from the new research

    # Product identity — new wins unless empty, then fall back to existing
    for key in ("name", "category", "subcategory"):
        if not merged.get(key) and existing.get(key):
            merged[key] = existing[key]

    # Narrative fields — prefer the longer/richer text so we never lose
    # detail a prior run surfaced. Applies to description, complexity_signals,
    # target_personas, cert_inclusion, api_surface, user_base_evidence.
    for key in (
        "description", "complexity_signals", "target_personas",
        "cert_inclusion", "api_surface", "user_base_evidence",
    ):
        old = (existing.get(key) or "").strip()
        new_val = (merged.get(key) or "").strip()
        if len(old) > len(new_val):
            merged[key] = old

    # Persistent truth — is_core_product: once flagged True, never regress
    if existing.get("is_core_product") and not merged.get("is_core_product"):
        merged["is_core_product"] = True

    # Relationship — flagship > secondary/satellite > standalone > ""
    old_rel = existing.get("product_relationship", "")
    new_rel = merged.get("product_relationship", "")
    if _RELATIONSHIP_RANK.get(old_rel, 0) > _RELATIONSHIP_RANK.get(new_rel, 0):
        merged["product_relationship"] = old_rel

    # deployment_model — prefer non-empty; if both set, prefer new (freshest)
    if not merged.get("deployment_model") and existing.get("deployment_model"):
        merged["deployment_model"] = existing["deployment_model"]

    # estimated_user_base — prefer the higher-confidence source
    old_ub_conf = existing.get("user_base_confidence", "")
    new_ub_conf = merged.get("user_base_confidence", "")
    if _CONFIDENCE_RANK.get(old_ub_conf, 0) > _CONFIDENCE_RANK.get(new_ub_conf, 0):
        for key in ("estimated_user_base", "user_base_confidence", "user_base_evidence"):
            if existing.get(key):
                merged[key] = existing[key]

    # annual_enrollments_estimate — wrapper-org audience; same confidence rule
    old_ae_conf = existing.get("annual_enrollments_confidence", "")
    new_ae_conf = merged.get("annual_enrollments_confidence", "")
    if _CONFIDENCE_RANK.get(old_ae_conf, 0) > _CONFIDENCE_RANK.get(new_ae_conf, 0):
        for key in (
            "annual_enrollments_estimate", "annual_enrollments_confidence",
            "annual_enrollments_evidence",
        ):
            if existing.get(key):
                merged[key] = existing[key]

    # rough_labability_score — prefer the newer value (fresher scoring
    # heuristic), but if new has no score and existing does, keep the old.
    if not merged.get("rough_labability_score") and existing.get("rough_labability_score"):
        merged["rough_labability_score"] = existing["rough_labability_score"]

    # _rough_labability_score_initial — preserve if already set on either side
    # (diagnostic history from earlier Phase F-PL write-backs)
    for key in ("_rough_labability_score_initial", "_tier", "_tier_label"):
        if existing.get(key) and not merged.get(key):
            merged[key] = existing[key]

    # underlying_technologies (list of dicts) — union by name
    old_techs = existing.get("underlying_technologies") or []
    new_techs = merged.get("underlying_technologies") or []
    if old_techs or new_techs:
        seen = {t.get("name", "").strip().lower(): t for t in new_techs if isinstance(t, dict)}
        for t in old_techs:
            if not isinstance(t, dict):
                continue
            key = t.get("name", "").strip().lower()
            if key and key not in seen:
                seen[key] = t
        merged["underlying_technologies"] = list(seen.values())

    return merged


def _merge_company_signals(existing: dict, new: dict) -> dict:
    """Merge the `company_signals` block. Prefer non-empty over empty."""
    if not isinstance(existing, dict):
        return new or {}
    if not isinstance(new, dict):
        return existing or {}
    merged = dict(new)
    for key, old_val in existing.items():
        if not merged.get(key) and old_val:
            merged[key] = old_val
    return merged


def merge_discovery_facts(existing: dict, new: dict) -> dict:
    """Merge `existing` discovery's best-of-best findings into `new`.

    Returns `new` (mutated in place) with fields carried forward from
    `existing` where doing so preserves richer evidence. Keys preserved:
      - per-product narrative fields (longer wins)
      - per-product confidence-ranked numeric facts (higher-confidence wins)
      - product list (union by name — don't lose products seen before)
      - company_signals (non-empty wins)
      - _customer_fit (Phase F aggregation already saved on existing)
      - _rough_labability_score_initial and tier fields (Phase F-PL history)

    Keys that always take from `new` (fresh research wins):
      - organization_type / company_badge (freshest classification)
      - _holistic_acv (reflects current config / anchors)
      - rough_labability_score (per product, when new has a non-zero value)

    The intent is compound-research per GP5: re-running discovery never
    regresses prior findings — it augments them.
    """
    if not isinstance(existing, dict) or not existing:
        return new
    if not isinstance(new, dict):
        return new

    # ── Merge product list (union by normalized name) ──
    old_products = existing.get("products") or []
    new_products = new.get("products") or []

    def _norm(name: str) -> str:
        return (name or "").strip().lower()

    old_by_name: dict[str, dict] = {}
    for p in old_products:
        if isinstance(p, dict):
            key = _norm(p.get("name", ""))
            if key:
                old_by_name[key] = p

    merged_products: list[dict] = []
    seen_new_keys: set[str] = set()
    for np in new_products:
        if not isinstance(np, dict):
            continue
        key = _norm(np.get("name", ""))
        if not key:
            merged_products.append(np)
            continue
        seen_new_keys.add(key)
        if key in old_by_name:
            merged_products.append(_merge_product_entry(old_by_name[key], np))
        else:
            merged_products.append(np)

    # Products only in existing (missing from the new run) — keep them.
    # This is the "don't lose what we found before" rule.
    for key, op in old_by_name.items():
        if key not in seen_new_keys:
            merged_products.append(op)

    new["products"] = merged_products

    # ── Merge company_signals ──
    new["company_signals"] = _merge_company_signals(
        existing.get("company_signals") or {},
        new.get("company_signals") or {},
    )

    # ── Preserve Phase F customer_fit if new run didn't produce one ──
    if not new.get("_customer_fit") and existing.get("_customer_fit"):
        new["_customer_fit"] = existing["_customer_fit"]

    # ── organization_type / company_badge — prefer new (fresher) unless empty ──
    for key in ("organization_type", "company_badge", "company_description", "company_url"):
        if not new.get(key) and existing.get(key):
            new[key] = existing[key]

    # ── _holistic_acv — prefer new (reflects current anchors) unless empty ──
    if not new.get("_holistic_acv") and existing.get("_holistic_acv"):
        new["_holistic_acv"] = existing["_holistic_acv"]

    # ── Track merge provenance so archival + audit works ──
    merged_from = list(new.get("_merged_from") or [])
    old_id = existing.get("discovery_id")
    if old_id and old_id != new.get("discovery_id") and old_id not in merged_from:
        merged_from.append(old_id)
    if merged_from:
        new["_merged_from"] = merged_from

    return new


def aggregate_product_labability_to_discovery(analysis: dict) -> bool:
    """Write Deep Dive Pillar 1 scores back onto the parent discovery so
    Prospector's tier labels reflect real scoring, not the pre-Deep-Dive
    rough guess.

    Mirrors the Phase F pattern used for Customer Fit, extended to PL
    per Frank's Rule 2026-04-16 ("Deep Dive findings should sharpen
    discovery-level data"). Prospector's tier columns (Prom./Pot./Unc./
    Unl.) count products by `rough_labability_score` thresholds. Without
    this write-back, a product scored PL 75 in Deep Dive would still be
    counted in whatever tier its rough guess landed in.

    Behavior per product:
      - If the product has a Deep Dive PL score, save the original rough
        guess as `_rough_labability_score_initial` (first time only — never
        overwrite so we preserve the original estimate for diagnostics) and
        replace `rough_labability_score` with the real Deep Dive score.
      - If the product lacks a Deep Dive score, leave the rough score
        alone.

    Re-runs `enrich_discovery` after the write so `_tier` and `_tier_label`
    reflect the sharpened numbers.

    Called by intelligence.score() at the end of every score boundary,
    alongside `aggregate_customer_fit_to_discovery`. Pure Python. Zero
    Claude calls. Zero re-research.

    Returns True if at least one product got a sharpened PL score written
    back, False otherwise.
    """
    discovery_id = analysis.get("discovery_id")
    if not discovery_id:
        return False

    analysis_products = analysis.get("products") or []
    if not analysis_products:
        return False

    discovery = load_discovery(discovery_id)
    if not discovery:
        return False

    disc_products = discovery.get("products") or []
    if not disc_products:
        return False

    # Build a name → real-PL-score lookup from the analysis's scored products
    name_to_pl: dict[str, int] = {}
    for p in analysis_products:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        pl = (p.get("fit_score") or {}).get("product_labability") or {}
        pl_score = pl.get("score")
        if pl_score is None:
            continue
        try:
            name_to_pl[name] = int(pl_score)
        except (TypeError, ValueError):
            continue

    if not name_to_pl:
        return False

    # Write back onto the discovery products that have matches
    sharpened = 0
    for dp in disc_products:
        name = (dp.get("name") or "").strip()
        if not name or name not in name_to_pl:
            continue
        real_pl = name_to_pl[name]
        original_rough = dp.get("rough_labability_score", 0)
        # Preserve the original rough guess once, never overwrite it on
        # subsequent write-backs — this keeps diagnostic history.
        if "_rough_labability_score_initial" not in dp:
            dp["_rough_labability_score_initial"] = original_rough
        dp["rough_labability_score"] = real_pl
        sharpened += 1

    if sharpened == 0:
        return False

    # Re-enrich the discovery so _tier / _tier_label reflect the sharpened
    # scores. enrich_discovery only overwrites _tier if it isn't already
    # set, so clear the derived fields on products we just touched to force
    # a fresh tier derivation.
    for dp in disc_products:
        if (dp.get("name") or "").strip() in name_to_pl:
            dp.pop("_tier", None)
            dp.pop("_tier_label", None)
    enrich_discovery(discovery)

    # Preserve created_at + version stamps on re-save (adding derived fields
    # is not a re-discovery — see aggregate_customer_fit_to_discovery for
    # the same rule).
    import scoring_config as cfg
    if not discovery.get("_scoring_logic_version"):
        discovery["_scoring_logic_version"] = cfg.SCORING_LOGIC_VERSION
    save_discovery(discovery_id, discovery)

    log.info(
        "Product Labability aggregated to discovery %s (%d products sharpened)",
        discovery_id, sharpened,
    )
    return True


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

        # Rebuild ACV motions from the fact drawer using the unified
        # model, then recompute the math. This ensures every page load
        # reflects the current org-type overrides, deflation tiers,
        # training maturity multipliers, and rate tables — even for
        # analyses scored under an older SCORING_LOGIC_VERSION.
        # Pure Python. Zero Claude calls. Zero research.
        acv_calculator.rebuild_acv_motions_from_facts(p, analysis)
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
        # Conservative estimate using the default Customer Training motion
        # config (adoption_pct + hours) × rate from deployment model.
        # Org-type overrides apply to scored products via populate_acv_motions;
        # unscored rough estimates use the default motion as a floor.
        _default_motion = cfg.CONSUMPTION_MOTIONS[0]  # Customer Training & Enablement
        adopt = _default_motion.adoption_pct
        hrs = _default_motion.hours_low

        # Org-type adoption override if available
        org_type = (discovery_data.get("organization_type") or "").lower().replace(" ", "_")
        norm_org = cfg.ORG_TYPE_NORMALIZATION.get(org_type, "")
        org_overrides = cfg.ACV_ORG_ADOPTION_OVERRIDES.get(norm_org, {})
        if _default_motion.label in org_overrides:
            adopt = org_overrides[_default_motion.label]

        # Apply tiered user base caps — same as discovery-level ACV.
        # Prevents inflated user bases from blowing up the company total.
        for threshold, cap in cfg.DISCOVERY_ACV_USER_BASE_TIERS:
            if user_base > threshold:
                if cap is not None:
                    user_base = cap
                break

        deploy = (dp.get("deployment_model") or "").strip().lower()
        if deploy in ("cloud", "saas-only"):
            rate = cfg.CLOUD_LABS_RATE
        elif deploy == "installable":
            rate = cfg.VM_MID_RATE
        else:
            rate = cfg.VM_LOW_RATE
        rough_acv = user_base * adopt * hrs * rate
        unscored_acv += rough_acv

    company_acv_low = round(scored_acv_low + unscored_acv)
    company_acv_high = round(scored_acv_high + unscored_acv)
    discovered_count = analysis.get("total_products_discovered") or len(products)

    # ── R5: Company-level ACV sanity cap ──
    # Total ACV cannot exceed total_employees × per-employee annual cap.
    # Backstop that catches any remaining inflation from any source.
    total_employees = 0
    disc_signals = discovery_data.get("company_signals", {})
    if disc_signals:
        # Try to parse total employee count from discovery signals
        emp_str = disc_signals.get("total_employees", "")
        if emp_str:
            try:
                emp_clean = str(emp_str).replace(",", "").replace("~", "").strip()
                if emp_clean.upper().endswith("K"):
                    total_employees = int(float(emp_clean[:-1]) * 1_000)
                elif emp_clean.upper().endswith("M"):
                    total_employees = int(float(emp_clean[:-1]) * 1_000_000)
                else:
                    total_employees = int(float(emp_clean))
            except (ValueError, TypeError):
                pass

    if total_employees > 0:
        employee_cap = total_employees * cfg.ACV_PER_EMPLOYEE_ANNUAL_CAP
        if company_acv_high > employee_cap:
            log.info("ACV R5 company cap: $%d → $%d (%d employees × $%d)",
                     company_acv_high, employee_cap,
                     total_employees, cfg.ACV_PER_EMPLOYEE_ANNUAL_CAP)
            company_acv_high = min(company_acv_high, round(employee_cap))
            company_acv_low = min(company_acv_low, company_acv_high)

    analysis["_company_acv"] = {
        "company_low": company_acv_low,
        "company_high": company_acv_high,
        "scored_low": scored_acv_low,
        "scored_high": scored_acv_high,
        "scored_count": scored_with_acv,
        "discovered_count": discovered_count,
    }


def _stamp_for_save(data: dict, timestamp_field: str = "analyzed_at") -> dict:
    """Stamp an analysis or discovery dict with the current version stamps
    and a fresh timestamp.

    The intelligence layer is the ONLY place that should ever set the version
    stamps + the scoring/discovery timestamp. Storage layer (save_analysis,
    save_discovery) now requires both fields to be present and rejects writes
    that don't have them.

    **Three-tier version stamps** (Frank's Rule #1, 2026-04-16):
      - `_scoring_math_version`: bumps on math-only changes (pure Python rescore)
      - `_rubric_version`: bumps on rubric vocabulary changes (re-grade, no re-research)
      - `_research_schema_version`: bumps on fact drawer shape changes (re-research)
      - `_scoring_logic_version`: retained for backwards-compat with pre-split caches.
        Always mirrors `_scoring_math_version` going forward.

    timestamp_field: "analyzed_at" for analyses, "created_at" for discoveries.
    """
    import scoring_config as cfg
    data["_scoring_math_version"] = cfg.SCORING_MATH_VERSION
    data["_rubric_version"] = cfg.RUBRIC_VERSION
    data["_research_schema_version"] = cfg.RESEARCH_SCHEMA_VERSION
    # Backwards-compat — legacy readers still look at this field. Kept in
    # lockstep with the math version so any existing consumer sees a sensible
    # "current" marker. Remove once all readers are migrated.
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
            # Discovery data (products, user bases, company signals) is still
            # valid even when SCORING_LOGIC_VERSION changes. Only SCORING
            # needs to re-run — not research. Return the cached discovery
            # regardless of version. The scoring path checks the version
            # separately and triggers a fresh Deep Dive when needed.
            if not cfg.is_cached_logic_current(cached):
                log.info(
                    "Intelligence.discover: cached discovery for %s has older "
                    "logic version %r (current %r) — returning cached data "
                    "(scoring will re-run on Deep Dive, not re-research)",
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

    # Discovery Option 2 — holistic ACV estimate (one Claude call, replaces
    # the retired per-product Python ACV math). Reads the cached discovery
    # we just built and produces a defendable range + confidence + rationale.
    # Safe to call here because the discovery dict already has products,
    # company_signals, and badge populated by the discover prompt above.
    _progress("Estimating ACV potential…")
    try:
        from researcher import estimate_holistic_acv
        holistic = estimate_holistic_acv(company_name, discovery)
        discovery["_holistic_acv"] = holistic
        log.info(
            "Intelligence.discover: holistic ACV for %s = $%s-$%s (%s)",
            company_name, f"{holistic.get('acv_low', 0):,}",
            f"{holistic.get('acv_high', 0):,}",
            holistic.get("confidence", "?"),
        )
    except Exception as e:
        log.warning("Intelligence.discover: holistic ACV failed for %s: %s",
                    company_name, e)
        # Don't block discovery on holistic ACV failure — display layer
        # will show "—" and a retry hint when _holistic_acv is missing.
        discovery["_holistic_acv"] = {}

    _progress("Categorizing offerings against Skillable taxonomy…")

    # ── Compound-research merge (Frank 2026-04-16) ────────────────────────
    # Before saving this fresh discovery, check if an earlier discovery for
    # the same company exists. If so, merge best-of-best findings from the
    # existing record into the new one so this run never regresses prior
    # research. Persistent signals carry forward; freshness signals (holistic
    # ACV, rough_labability_score) take the new values. See
    # merge_discovery_facts above for the full merge rules.
    try:
        existing_for_merge = find_discovery_by_company_name(company_name)
        # Skip the merge if the existing record IS this new record (only
        # happens when force_refresh reuses an id path — defensive check).
        if existing_for_merge and existing_for_merge.get("discovery_id") != discovery["discovery_id"]:
            old_id = existing_for_merge.get("discovery_id", "<unknown>")
            log.info(
                "Intelligence.discover: merging prior discovery %s into fresh "
                "research for %s (best-of-best)",
                old_id, company_name,
            )
            merge_discovery_facts(existing_for_merge, discovery)
    except Exception:
        log.exception(
            "merge_discovery_facts failed for %s — proceeding with unmerged "
            "fresh discovery (no data loss; just missing prior-run enrichment)",
            company_name,
        )

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
    # Phase C (2026-04-16): tiered stale dispatch.  True when we rescored
    # existing products in-place via the cheap paths — the fast-return block
    # below must stamp + save before returning, otherwise the rescore is
    # lost.  False for wipe paths (there's new work to do, the normal
    # save at function tail handles it) and for the CURRENT path (no change).
    rescored_in_place = False
    if existing:
        # Tiered cache versioning (Frank's Rule #1 — research is immutable).
        # Pick the cheapest path that restores freshness:
        #   CURRENT        → no work, append new products normally
        #   MATH_STALE     → pure-Python rescore of saved facts (zero Claude)
        #   RUBRIC_STALE   → re-grade Pillar 2/3 + rescore (partial Claude)
        #   RESEARCH_STALE → fact drawer shape changed, must re-research
        #   UNSTAMPED      → legacy record carrying only the old single-
        #                    version stamp. Fact drawer shape is the same
        #                    as current RESEARCH_SCHEMA_VERSION, so we
        #                    treat it as MATH_STALE — pure-Python rescore
        #                    against saved facts, zero Claude calls. Honors
        #                    Rule #1 (research is immutable). The rescore
        #                    function self-protects by skipping products
        #                    missing fact drawers, so a truly-ancient
        #                    record gracefully degrades to 0 rescored.
        # force_refresh always wipes, regardless of tier state.
        status = cfg.is_cached_logic_current_tiered(existing)
        stale_count = len(existing.get("products", []) or [])

        if force_refresh:
            log.info(
                "Intelligence.score: analysis %s — force_refresh=True — wiping %d products",
                existing.get("analysis_id"), stale_count,
            )
            # CRITICAL: wipe the legacy products list so they don't survive
            # the cache-and-append below. See investigation 2026-04-06.
            existing["products"] = []
        elif status == cfg.CacheStatus.RESEARCH_STALE:
            log.info(
                "Intelligence.score: analysis %s — RESEARCH_STALE — wiping %d products (re-research required)",
                existing.get("analysis_id"), stale_count,
            )
            existing["products"] = []
        elif status in (cfg.CacheStatus.RUBRIC_STALE, cfg.CacheStatus.UNSTAMPED):
            # Rubric vocabulary changed — re-grade Pillar 2/3 qualitative
            # findings + rescore. Research (facts) preserved.
            #
            # UNSTAMPED legacy records land here too (Frank 2026-04-16):
            # we don't know what rubric version they were graded under,
            # and the research is still on disk. Regrading against the
            # current rubric + rescoring against the current math is the
            # honest expression of "cached data gets the latest scoring
            # for free". The only cost is the focused rubric grader
            # Claude calls (cents per company, not dollars) — research
            # is never re-run. Honors Rule #1.
            log.info(
                "Intelligence.score: analysis %s — %s — re-grading + rescoring %d products",
                existing.get("analysis_id"), status, stale_count,
            )
            try:
                n = rescore_products_from_saved_facts(existing, regrade=True)
                rescored_in_place = True
                log.info(
                    "Intelligence.score: %s rescore completed %d/%d products",
                    status, n, stale_count,
                )
                if n == 0 and stale_count > 0:
                    # Truly-ancient record with no fact drawers at all —
                    # rescore skipped everything. Fall back to wipe so the
                    # downstream path re-researches; otherwise we'd carry
                    # unscored products forward with stale scores.
                    log.info(
                        "Intelligence.score: analysis %s — %s with no "
                        "fact drawers — wiping to trigger re-research",
                        existing.get("analysis_id"), status,
                    )
                    existing["products"] = []
            except Exception:
                log.exception(
                    "Intelligence.score: %s rescore failed for %s — "
                    "falling back to full wipe",
                    status, existing.get("analysis_id"),
                )
                existing["products"] = []
            for p in existing.get("products", []):
                existing_product_names.add(p.get("name", ""))
        elif status == cfg.CacheStatus.MATH_STALE:
            # Pure-Python rescore — zero Claude calls, milliseconds.
            # Math-only bump; rubric + research stamps are current, so
            # saved rubric grades are trustworthy. No regrade needed.
            log.info(
                "Intelligence.score: analysis %s — MATH_STALE — pure-Python rescore of %d products",
                existing.get("analysis_id"), stale_count,
            )
            try:
                n = rescore_products_from_saved_facts(existing, regrade=False)
                rescored_in_place = True
                log.info(
                    "Intelligence.score: MATH_STALE rescore completed %d/%d products",
                    n, stale_count,
                )
            except Exception:
                log.exception(
                    "Intelligence.score: rescore failed for %s — "
                    "falling back to full wipe",
                    existing.get("analysis_id"),
                )
                existing["products"] = []
            for p in existing.get("products", []):
                existing_product_names.add(p.get("name", ""))
        else:
            # CURRENT — cache hit, append any new products selected
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
        # Phase C: if we rescored in-place via MATH_STALE / RUBRIC_STALE
        # dispatch above, we must stamp + save before returning so the
        # fresh scores persist. Without this, rescored values live only
        # in memory for this request and disappear on the next load.
        if rescored_in_place:
            _stamp_for_save(existing)
            _save(existing)
            log.info(
                "Intelligence.score: rescored analysis %s saved via tiered-stale dispatch",
                existing.get("analysis_id"),
            )
        log.info("Intelligence.score: ALL selected products cached — returning existing analysis %s",
                 existing.get("analysis_id"))
        # Phase F: backfill the unified Customer Fit onto the discovery if
        # it isn't there yet. Cheap no-op when the discovery already has it.
        try:
            aggregate_customer_fit_to_discovery(existing)
        except Exception:
            log.exception("Phase F aggregate_customer_fit_to_discovery failed for %s",
                          existing.get("analysis_id"))
        # Phase F-PL: write Deep Dive PL scores back onto the discovery so
        # Prospector tier columns reflect real scoring. Cheap no-op on the
        # all-cached fast path since nothing new was scored.
        try:
            aggregate_product_labability_to_discovery(existing)
        except Exception:
            log.exception("aggregate_product_labability_to_discovery failed for %s",
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
                    product_metadata=p,
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
        # Attach discovery_data so Pillar 3 graders can read lab_platform
        # for DIY lab platform detection (Fix 3 / C2 audit fix, 2026-04-13).
        new_analysis.discovery_data = discovery_data
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

            # Archetype classification — deterministic Python, zero Claude.
            # Drives IV ceiling in Pillar 2 + ACV floors. Frank 2026-04-16.
            try:
                from archetype_classifier import classify_archetype
                _disc = discovery_data if isinstance(discovery_data, dict) else {}
                product.archetype, product.archetype_rationale = classify_archetype(
                    product, _disc,
                )
            except Exception:
                log.exception(
                    "Intelligence.score: classify_archetype failed for %r",
                    product.name,
                )

            try:
                p_grades = grade_all_for_product(product, new_analysis)
                product.rubric_grades = p_grades
                product.fit_score.instructional_value = score_instructional_value(
                    product.category,
                    p_grades,
                    archetype=product.archetype or "",
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
        # Phase F-PL: sharpen per-product rough_labability_score with real
        # Deep Dive PL scores so Prospector tier counts reflect reality.
        try:
            aggregate_product_labability_to_discovery(existing_dict)
        except Exception:
            log.exception("aggregate_product_labability_to_discovery failed for %s",
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
    # Phase F-PL: sharpen per-product rough_labability_score on the parent
    # discovery with the real Deep Dive PL scores. Enables Prospector's tier
    # columns to reflect Deep Dive reality instead of the AI's pre-DD guess.
    try:
        aggregate_product_labability_to_discovery(fresh_dict)
    except Exception:
        log.exception("aggregate_product_labability_to_discovery failed for %s", analysis_id)
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
