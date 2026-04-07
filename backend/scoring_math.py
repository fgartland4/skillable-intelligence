"""Deterministic scoring math.

The AI is responsible for evidence synthesis — it reads research, picks the
right badges from the locked vocabulary, and writes evidence bullets.

This module is responsible for ALL scoring math. It is pure Python, fully
deterministic, and reads every value from `scoring_config.py`. No hardcoded
numbers, weights, thresholds, or multipliers anywhere in this file.

Design contract:
  - Same inputs always produce the same outputs.
  - The AI's claimed scores are ignored; this module is the source of truth.
  - All thresholds, weights, signal points, penalty deductions, and ceiling
    caps come from `scoring_config.py`.
  - Define-Once is honored at every level.

Public functions:
  - compute_dimension_score(dim_name, badge_names) -> int
  - compute_pillar_score(pillar_name, dimension_scores) -> int
  - apply_ceiling_flags(pl_score, ceiling_flags) -> tuple[int, list[str]]
  - get_technical_fit_multiplier(pl_score, orchestration_method) -> float
  - compute_fit_score(pl_score, iv_score, cf_score, multiplier) -> int
  - compute_all(badges_by_dimension, ceiling_flags, orchestration_method)
        -> dict with full breakdown
"""
from __future__ import annotations

import logging
from typing import Iterable

import scoring_config as cfg

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Internal lookups — built once from the config so we don't re-walk it
# ─────────────────────────────────────────────────────────────────────────────

def _build_dimension_lookup() -> dict[str, cfg.Dimension]:
    """Map dimension key (lowercase, underscores) to Dimension object."""
    out: dict[str, cfg.Dimension] = {}
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            key = dim.name.lower().replace(" ", "_")
            out[key] = dim
    return out


def _build_signal_lookup(dim: cfg.Dimension) -> dict[str, int]:
    """Map signal name (case-insensitive) to its point value for a dimension."""
    return {sig.name.lower(): sig.points for sig in dim.scoring_signals}


def _build_penalty_lookup(dim: cfg.Dimension) -> dict[str, int]:
    """Map penalty name (case-insensitive) to its deduction (negative)."""
    return {pen.name.lower(): pen.deduction for pen in dim.penalties}


def _build_pillar_lookup() -> dict[str, cfg.Pillar]:
    """Map pillar key (lowercase, underscores) to Pillar object."""
    out: dict[str, cfg.Pillar] = {}
    for pillar in cfg.PILLARS:
        key = pillar.name.lower().replace(" ", "_")
        out[key] = pillar
    return out


_DIMENSION_LOOKUP = _build_dimension_lookup()
_PILLAR_LOOKUP = _build_pillar_lookup()


# ─────────────────────────────────────────────────────────────────────────────
# Dimension score computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_dimension_score(dim_key: str,
                            badges: Iterable) -> dict:
    """Compute the score for one dimension from the badges the AI emitted.

    THREE scoring patterns are supported and chosen automatically:

    1. **Rubric pattern** (Pillar 2 Instructional Value, Pillar 3 Customer Fit):
       the dimension defines a `rubric` with strength tiers (strong/moderate/weak).
       Each badge carries a `strength` field; the math credits points by
       (dimension, strength) lookup. Variable badge names are expected and
       supported — no name matching against canonicals.

    2. **Signal/penalty pattern** (Pillar 1 Product Labability): the dimension
       defines explicit `scoring_signals` and `penalties`. Each badge name is
       matched against those tables; matched signals add their points (color-
       aware: green = full, gray = full, amber = half, red = color fallback),
       matched penalties subtract their deductions.

    3. **Badge-color pattern** (legacy fallback): each badge contributes points
       based on its color, using `cfg.BADGE_COLOR_POINTS`. Used for any dimension
       without rubric or scoring_signals, and for badges in signal/penalty
       dimensions whose names don't match the lookup tables.

    Args:
        dim_key: Dimension key in lowercase with underscores (e.g., "lab_access").
        badges: Iterable of either bare badge name strings (legacy callers) OR
                dicts with "name", "color", optional "strength" (rubric), and
                optional "signal_category" fields.

    Returns:
        A dict with the score breakdown so the result is auditable:
        {
            "score": int,
            "weight": int,
            "model": "rubric" | "signal_penalty",
            "signals_matched": [...] (signal/penalty model),
            "penalties_applied": [...] (signal/penalty model),
            "rubric_credits": [...] (rubric model — name + strength + points + category),
            "color_contributions": [...],
            "raw_total": int,
            "capped": bool,
            "floored": bool,
            "unknown_badges": [str, ...],
        }
    """
    dim = _DIMENSION_LOOKUP.get(dim_key)
    if dim is None:
        log.warning("compute_dimension_score: unknown dimension '%s'", dim_key)
        return {
            "score": 0, "weight": 0, "model": "unknown",
            "signals_matched": [], "penalties_applied": [], "rubric_credits": [],
            "color_contributions": [],
            "raw_total": 0, "capped": False, "floored": False,
            "unknown_badges": [],
        }

    # Rubric model (Pillar 2 + Pillar 3) — branch early so the rest of this
    # function only handles signal/penalty dimensions.
    if dim.rubric is not None:
        return _compute_rubric_dimension_score(dim, badges)

    signal_lookup = _build_signal_lookup(dim)
    penalty_lookup = _build_penalty_lookup(dim)

    signals_matched: list[dict] = []
    penalties_applied: list[dict] = []
    color_contributions: list[dict] = []
    unknown: list[str] = []

    # Dedupe by name BUT keep the highest-points color version when the same
    # name appears with multiple colors. The AI sometimes emits two evidence
    # items under the same embedded label with different colors (one as a
    # strength, one as a risk). The math should credit the positive signal
    # rather than penalize for AI inconsistency. The visual layer (Phase 2
    # display normalizer) is free to display the worst color so risks are
    # still visible to the user.
    #
    # Reads cfg.BADGE_COLOR_POINTS (Define-Once — same source the color
    # fallback below uses) so any future tweak to color scoring values
    # automatically updates the dedupe ranking too.
    fallback = cfg.BADGE_UNKNOWN_COLOR_SCORE_FALLBACK
    best_by_name: dict[str, tuple[str, str]] = {}  # name_lower -> (raw_name, color)
    for badge in badges:
        if not badge:
            continue
        if isinstance(badge, dict):
            raw_name = badge.get("name", "")
            color = (badge.get("color") or "").strip().lower()
        else:
            raw_name = str(badge)
            color = ""
        if not raw_name:
            continue
        name_lower = raw_name.strip().lower()
        existing = best_by_name.get(name_lower)
        new_score = cfg.BADGE_COLOR_POINTS.get(color, fallback)
        existing_score = cfg.BADGE_COLOR_POINTS.get(existing[1], fallback) if existing else fallback
        if existing is None or new_score > existing_score:
            best_by_name[name_lower] = (raw_name, color)

    for name_lower, (raw_name, color) in best_by_name.items():
        if name_lower in signal_lookup:
            # Signal credit is COLOR-AWARE. Multi-state canonical badges
            # (Sandbox API, Training License, Scoring API, Teardown API,
            # Learner Isolation, etc.) use the same canonical name across
            # green/amber/red states. Crediting the full signal value
            # regardless of color would let a red gatekeeper badge earn the
            # same points as a green confirmation, which is structurally
            # wrong.
            #
            # Rule:
            #   green or empty → full signal value
            #   gray            → full signal value (e.g., Simulation gray
            #                     Context as the chosen path)
            #   amber           → half signal value (uncertain / partial coverage)
            #   red             → fall back to color points (-3) — negative
            #                     finding does NOT credit the positive signal
            signal_pts = signal_lookup[name_lower]
            if color == "red":
                color_contributions.append({
                    "name": raw_name.strip(),
                    "color": color,
                    "points": cfg.BADGE_COLOR_POINTS.get(color, fallback),
                })
            elif color == "amber":
                signals_matched.append({
                    "name": raw_name.strip(),
                    "points": signal_pts // 2,  # magic-allowed: half-credit for amber/uncertain signal
                })
            else:  # green, gray, or no color
                signals_matched.append({
                    "name": raw_name.strip(),
                    "points": signal_pts,
                })
        elif name_lower in penalty_lookup:
            penalties_applied.append({
                "name": raw_name.strip(),
                "deduction": penalty_lookup[name_lower],
            })
        elif color and color in cfg.BADGE_COLOR_POINTS:
            color_contributions.append({
                "name": raw_name.strip(),
                "color": color,
                "points": cfg.BADGE_COLOR_POINTS[color],
            })
        else:
            unknown.append(raw_name.strip())

    # Compute raw total: signals + penalties + color-based contributions
    signal_total = sum(s["points"] for s in signals_matched)
    penalty_total = sum(p["deduction"] for p in penalties_applied)
    color_total = sum(c["points"] for c in color_contributions)
    raw_total = signal_total + penalty_total + color_total

    # Apply cap (defaults to dimension weight) and floor (defaults to 0)
    cap = dim.cap if dim.cap is not None else dim.weight
    floor = dim.floor if dim.floor is not None else 0

    score = raw_total
    capped = False
    floored = False
    if score > cap:
        score = cap
        capped = True
    if score < floor:
        score = floor
        floored = True

    return {
        "score": int(score),
        "weight": dim.weight,
        "model": "signal_penalty",
        "signals_matched": signals_matched,
        "penalties_applied": penalties_applied,
        "rubric_credits": [],  # not used in signal/penalty model
        "color_contributions": color_contributions,
        "raw_total": int(raw_total),
        "capped": capped,
        "floored": floored,
        "unknown_badges": unknown,
    }


def _compute_rubric_dimension_score(dim: cfg.Dimension, badges: Iterable) -> dict:
    """Rubric-based scoring for Pillar 2 + Pillar 3 dimensions.

    Each badge carries:
      - name (variable, AI-synthesized — used for display only)
      - color (green / amber / red — visual + secondary signal)
      - strength (strong / moderate / weak — required, math driver)
      - signal_category (one of the dimension's fixed category list — for analytics)

    The math credits points by (dimension, strength) lookup against the
    dimension's rubric tiers. Color is preserved for visual rendering and
    used as a fallback when strength is missing.

    Strength → color cross-check (when both present):
      green ↔ strong, amber ↔ moderate, red ↔ hard negative (uses color points)

    Mitigation #1 (anti-inflation): the AI must explicitly grade each badge
    against the rubric. Missing strength field falls back to color points.
    """
    rubric = dim.rubric
    assert rubric is not None  # caller already checked

    # Build strength → points lookup from the rubric tiers
    strength_lookup: dict[str, int] = {tier.strength: tier.points for tier in rubric.tiers}

    # Valid signal categories for this dimension (for tag validation, not scoring)
    valid_categories: set[str] = set(rubric.signal_categories)

    rubric_credits: list[dict] = []
    color_contributions: list[dict] = []
    unknown: list[str] = []

    fallback = cfg.BADGE_UNKNOWN_COLOR_SCORE_FALLBACK

    for badge in badges:
        if not badge:
            continue
        if isinstance(badge, dict):
            raw_name = badge.get("name", "")
            color = (badge.get("color") or "").strip().lower()
            strength = (badge.get("strength") or "").strip().lower()
            category = (badge.get("signal_category") or "").strip()
        else:
            raw_name = str(badge)
            color = ""
            strength = ""
            category = ""

        if not raw_name:
            continue

        # Red color = hard negative — uses color points (-3) regardless of strength.
        # Reserved for explicit hard negatives like Consumer Grade or Hard to Engage.
        if color == "red":
            color_contributions.append({
                "name": raw_name.strip(),
                "color": color,
                "points": cfg.BADGE_COLOR_POINTS.get(color, fallback),
            })
            continue

        # Rubric path — strength is required for full credit.
        if strength and strength in strength_lookup:
            pts = strength_lookup[strength]
            rubric_credits.append({
                "name": raw_name.strip(),
                "strength": strength,
                "points": pts,
                "signal_category": category if category in valid_categories else "",
                "color": color,
            })
            continue

        # Strength missing or invalid — fall back to color points so cached
        # data and AI errors don't silently zero out.
        if color and color in cfg.BADGE_COLOR_POINTS:
            color_contributions.append({
                "name": raw_name.strip(),
                "color": color,
                "points": cfg.BADGE_COLOR_POINTS[color],
            })
        else:
            unknown.append(raw_name.strip())

    # Compute raw total
    rubric_total = sum(c["points"] for c in rubric_credits)
    color_total = sum(c["points"] for c in color_contributions)
    raw_total = rubric_total + color_total

    # Apply cap (defaults to dimension weight) and floor (defaults to 0)
    cap = dim.cap if dim.cap is not None else dim.weight
    floor = dim.floor if dim.floor is not None else 0

    score = raw_total
    capped = False
    floored = False
    if score > cap:
        score = cap
        capped = True
    if score < floor:
        score = floor
        floored = True

    return {
        "score": int(score),
        "weight": dim.weight,
        "model": "rubric",
        "signals_matched": [],   # not used in rubric model
        "penalties_applied": [],  # not used in rubric model
        "rubric_credits": rubric_credits,
        "color_contributions": color_contributions,
        "raw_total": int(raw_total),
        "capped": capped,
        "floored": floored,
        "unknown_badges": unknown,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pillar score computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_pillar_score(pillar_key: str, dimension_scores: dict[str, int]) -> int:
    """Sum the dimension scores for a pillar. Capped at 100 (matches model).

    Args:
        pillar_key: Pillar key in lowercase with underscores
                    (e.g., "product_labability").
        dimension_scores: Map of dimension key -> computed score.

    Returns:
        Pillar score, 0-100.
    """
    pillar = _PILLAR_LOOKUP.get(pillar_key)
    if pillar is None:
        log.warning("compute_pillar_score: unknown pillar '%s'", pillar_key)
        return 0

    total = 0
    for dim in pillar.dimensions:
        dim_key = dim.name.lower().replace(" ", "_")
        total += dimension_scores.get(dim_key, 0)

    # Pillar scores cap at 100 (sum of dimension weights == 100 by design)
    return min(100, max(0, total))


# ─────────────────────────────────────────────────────────────────────────────
# Ceiling flag enforcement
# ─────────────────────────────────────────────────────────────────────────────

def apply_ceiling_flags(pl_score: int, ceiling_flags: Iterable[str]) -> tuple[int, list[dict]]:
    """Apply Product Labability ceiling flags to the PL score.

    If any flag is present, the PL score is capped at the lowest applicable
    max_score. The most restrictive flag wins.

    Args:
        pl_score: The pre-ceiling Product Labability score (0-100).
        ceiling_flags: Iterable of flag names the AI emitted.

    Returns:
        (capped_score, list of {"flag": name, "max_score": int, "reason": str}
        entries describing which flags were applied)
    """
    if not ceiling_flags:
        return pl_score, []

    applied: list[dict] = []
    new_score = pl_score
    for flag in ceiling_flags:
        if not flag:
            continue
        rule = cfg.CEILING_FLAGS.get(flag)
        if not rule:
            continue
        max_score = rule.get("max_score")
        if max_score is None:
            continue
        if new_score > max_score:
            new_score = max_score
        applied.append({
            "flag": flag,
            "max_score": max_score,
            "reason": rule.get("reason", ""),
        })

    return new_score, applied


# ─────────────────────────────────────────────────────────────────────────────
# Technical Fit Multiplier
# ─────────────────────────────────────────────────────────────────────────────

def get_technical_fit_multiplier(pl_score: int, orchestration_method: str) -> float:
    """Look up the multiplier that scales downstream pillars.

    Args:
        pl_score: Final Product Labability score (after ceilings).
        orchestration_method: e.g., "Hyper-V", "ESX", "Azure Cloud Slice", etc.

    Returns:
        Multiplier in [0, 1] applied to the IV + CF contribution.
    """
    if not orchestration_method:
        method_class = "any"
    elif orchestration_method in cfg.DATACENTER_METHODS:
        method_class = "datacenter"
    else:
        method_class = "non-datacenter"

    # Walk multipliers in declaration order; first match wins. Try the
    # method-specific match first, then fall back to "any".
    for m in cfg.TECHNICAL_FIT_MULTIPLIERS:
        if m.score_min <= pl_score <= m.score_max and m.method == method_class:
            return m.multiplier

    for m in cfg.TECHNICAL_FIT_MULTIPLIERS:
        if m.score_min <= pl_score <= m.score_max and m.method == "any":
            return m.multiplier

    # No match — log and default to 1.0 to avoid silently zeroing the score
    log.warning(
        "get_technical_fit_multiplier: no rule matched (pl=%d, method=%s)",
        pl_score, orchestration_method,
    )
    return 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Final Fit Score
# ─────────────────────────────────────────────────────────────────────────────

def compute_fit_score(pl_score: int, iv_score: int, cf_score: int,
                      multiplier: float) -> int:
    """Compute the final Fit Score from the three pillar scores and the
    Technical Fit Multiplier.

    Architecture:

      1. Compute the weighted sum normally (each pillar contributes its
         weight × score / 100).
      2. The Technical Fit Multiplier scales DOWNSTREAM pillars (IV + CF) —
         a weak PL means strong instructional/organizational signals can't
         fully compensate.
      3. **Product Labability is the floor.** The Fit Score is never less
         than the PL score itself. Strong IV/CF can pull the Fit Score
         ABOVE the PL score, but they can NEVER push it below.
         If PL is 5, Fit cannot be lower than 5.

    Args:
        pl_score: Product Labability pillar score (0-100, post-ceilings).
        iv_score: Instructional Value pillar score (0-100).
        cf_score: Customer Fit pillar score (0-100).
        multiplier: Technical Fit Multiplier (typically 0.15-1.0).

    Returns:
        Final Fit Score, 0-100.
    """
    pl_pillar = _PILLAR_LOOKUP.get("product_labability")
    iv_pillar = _PILLAR_LOOKUP.get("instructional_value")
    cf_pillar = _PILLAR_LOOKUP.get("customer_fit")
    if not (pl_pillar and iv_pillar and cf_pillar):
        log.error("compute_fit_score: pillar config missing")
        return 0

    pl_contrib = pl_score * (pl_pillar.weight / 100)
    iv_contrib = iv_score * (iv_pillar.weight / 100) * multiplier
    cf_contrib = cf_score * (cf_pillar.weight / 100) * multiplier

    weighted_sum = pl_contrib + iv_contrib + cf_contrib

    # PL is the floor. IV and CF can pull the fit UP above PL but never below.
    fit = max(weighted_sum, pl_score)

    return max(0, min(100, round(fit)))


# ─────────────────────────────────────────────────────────────────────────────
# All-in-one entry point
# ─────────────────────────────────────────────────────────────────────────────

def compute_all(badges_by_dimension: dict[str, list[str]],
                ceiling_flags: Iterable[str],
                orchestration_method: str) -> dict:
    """Compute the full scoring breakdown for one product.

    Args:
        badges_by_dimension: Map of dimension key -> list of badge names the
            AI assigned. Dimension keys are lowercase with underscores
            (e.g., "lab_access", "product_complexity").
        ceiling_flags: Flags the AI emitted (e.g., {"saas_only"}).
        orchestration_method: e.g., "Hyper-V", "Azure Cloud Slice", etc.

    Returns:
        A dict with the full breakdown:
        {
            "dimensions": {dim_key: <result from compute_dimension_score>, ...},
            "pillars": {
                "product_labability": int,    # post-ceilings
                "instructional_value": int,
                "customer_fit": int,
            },
            "pillar_labability_pre_ceiling": int,
            "ceilings_applied": [...],
            "technical_fit_multiplier": float,
            "fit_score": int,
        }
    """
    dim_results: dict[str, dict] = {}
    dim_scores: dict[str, int] = {}

    for dim_key, badges in badges_by_dimension.items():
        result = compute_dimension_score(dim_key, badges)
        dim_results[dim_key] = result
        dim_scores[dim_key] = result["score"]

    pl_pre = compute_pillar_score("product_labability", dim_scores)
    iv_score = compute_pillar_score("instructional_value", dim_scores)
    cf_score = compute_pillar_score("customer_fit", dim_scores)

    pl_score, ceilings_applied = apply_ceiling_flags(pl_pre, ceiling_flags)
    multiplier = get_technical_fit_multiplier(pl_score, orchestration_method)
    fit_score = compute_fit_score(pl_score, iv_score, cf_score, multiplier)

    return {
        "dimensions": dim_results,
        "pillars": {
            "product_labability": pl_score,
            "instructional_value": iv_score,
            "customer_fit": cf_score,
        },
        "pillar_labability_pre_ceiling": pl_pre,
        "ceilings_applied": ceilings_applied,
        "technical_fit_multiplier": multiplier,
        "fit_score": fit_score,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ACV Potential — deterministic Python math (Frank's locked model)
# ─────────────────────────────────────────────────────────────────────────────
#
# The AI's job is to estimate per-motion population, adoption %, and hours
# per learner. Python's job is everything else: per-motion hours, total
# hours, rate lookup by orchestration method, and dollar conversion.
#
# Frank's model (2026-04-06):
#   For each motion:
#     hours_low  = pop_low  * adoption * hours_per_learner_low
#     hours_high = pop_high * adoption * hours_per_learner_high
#     acv_low    = hours_low  * rate
#     acv_high   = hours_high * rate
#   Total ACV = sum across motions.
#
# Rate per hour comes from the four named variables in scoring_config.py:
#   CLOUD_LABS_RATE / VM_LOW_RATE / VM_MID_RATE / VM_HIGH_RATE / SIMULATION_RATE
# Looked up by orchestration_method via cfg.ORCHESTRATION_TO_RATE_TIER.
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_acv_tier(acv_high_dollars: float) -> str:
    """Map a computed ACV high-end dollar value to a tier label.

    Reads thresholds from cfg.ACV_TIER_HIGH_THRESHOLD and
    cfg.ACV_TIER_MEDIUM_THRESHOLD. Evaluating against the high end of the
    range so a deal is sized at its upside potential.
    """
    if acv_high_dollars >= cfg.ACV_TIER_HIGH_THRESHOLD:
        return "high"
    if acv_high_dollars >= cfg.ACV_TIER_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def _resolve_rate(orchestration_method: str) -> tuple[str, float]:
    """Map a product's orchestration method to (tier_name, $/hour).

    Falls back to cfg.DEFAULT_RATE_TIER_NAME at cfg.VM_MID_RATE when the
    orchestration method is empty, unknown, or doesn't map to any known
    tier — the everyday-admin-lab default, conservatively neither cheap
    nor pricey.

    Reads RateTier.delivery_path and RateTier.rate_low (single-value model
    — rate_low == rate_high per Frank's locked rates).
    """
    key = (orchestration_method or "").strip().lower()
    tier_name = cfg.ORCHESTRATION_TO_RATE_TIER.get(key, cfg.DEFAULT_RATE_TIER_NAME)
    for tier in cfg.RATE_TABLES:
        if tier.delivery_path == tier_name:
            return tier_name, float(tier.rate_low)
    # Should not happen — RATE_TABLES is the source of truth and the mapping
    # only points at delivery_path values that exist in it. Final safety net.
    return cfg.DEFAULT_RATE_TIER_NAME, float(cfg.VM_MID_RATE)


def compute_acv_potential(product: dict) -> dict:
    """Recompute ACV from the AI's motion estimates using deterministic math.

    Reads from product:
      - acv_potential.motions[]    — AI-emitted population/adoption/hours
      - orchestration_method        — AI-emitted fabric choice

    Mutates product["acv_potential"] in place with computed fields:
      - motions[i].hrs_low / hrs_high   — per-motion annual hours (computed)
      - motions[i].acv_low / acv_high   — per-motion dollar contribution
      - annual_hours_low / high          — total across motions
      - acv_low / acv_high               — total dollar range
      - rate_per_hour                    — the looked-up rate
      - rate_tier_name                   — which tier was chosen

    Returns the updated acv_potential dict (or an empty dict if there's
    nothing to compute).

    Defends against missing or malformed motion data — any motion that's
    not a dict or has zero/missing inputs contributes zero hours rather
    than raising.
    """
    acv = product.get("acv_potential")
    if not isinstance(acv, dict):
        return {}

    motions = acv.get("motions") or []
    if not isinstance(motions, list):
        motions = []

    tier_name, rate = _resolve_rate(product.get("orchestration_method") or "")

    total_hours_low = 0.0
    total_hours_high = 0.0

    for m in motions:
        if not isinstance(m, dict):
            continue
        try:
            pop_low = float(m.get("population_low") or 0)
            pop_high = float(m.get("population_high") or 0)
            adopt = float(m.get("adoption_pct") or 0)
            hrs_low = float(m.get("hours_low") or 0)
            hrs_high = float(m.get("hours_high") or 0)
        except (TypeError, ValueError):
            continue

        m_hours_low = pop_low * adopt * hrs_low
        m_hours_high = pop_high * adopt * hrs_high
        m_acv_low = m_hours_low * rate
        m_acv_high = m_hours_high * rate

        # Stash per-motion computed fields so the widget can render them
        # without redoing the math in Jinja
        m["hrs_low"] = round(m_hours_low)
        m["hrs_high"] = round(m_hours_high)
        m["acv_low"] = round(m_acv_low)
        m["acv_high"] = round(m_acv_high)

        total_hours_low += m_hours_low
        total_hours_high += m_hours_high

    acv_low_dollars = total_hours_low * rate
    acv_high_dollars = total_hours_high * rate

    acv["annual_hours_low"] = round(total_hours_low)
    acv["annual_hours_high"] = round(total_hours_high)
    acv["acv_low"] = round(acv_low_dollars)
    acv["acv_high"] = round(acv_high_dollars)
    acv["rate_per_hour"] = rate
    acv["rate_tier_name"] = tier_name
    acv["acv_tier"] = _resolve_acv_tier(acv_high_dollars)

    return acv
