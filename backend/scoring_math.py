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
# Baseline + penalty lookups for the rubric model (Pillars 2 + 3)
# ─────────────────────────────────────────────────────────────────────────────

def _dimension_keys_for_pillar(pillar: cfg.Pillar) -> set[str]:
    """Return the set of dimension keys for a Pillar object.

    Takes a Pillar object directly (not a name string) so there is NO
    hardcoded pillar name anywhere in this module.  Derived from
    `scoring_config.PILLARS` at module load time so renames in the config
    propagate automatically.  Define-Once.
    """
    return {dim.name.lower().replace(" ", "_") for dim in pillar.dimensions}


# Which dimension keys belong to Instructional Value (category-aware baselines)
# and Customer Fit (organization-type baselines).  Built from the Pillar
# objects in scoring_config.py — no hardcoded pillar names, no hardcoded
# dimension key strings.
_IV_DIMENSION_KEYS: set[str] = _dimension_keys_for_pillar(cfg.PILLAR_INSTRUCTIONAL_VALUE)
_CF_DIMENSION_KEYS: set[str] = _dimension_keys_for_pillar(cfg.PILLAR_CUSTOMER_FIT)


def _get_dimension_baseline(dim_key: str, context: dict | None) -> int:
    """Look up the baseline for a dimension given the scoring context.

    IV dimensions (Product Complexity, Mastery Stakes, Lab Versatility,
    Market Demand) use per-category baselines from `IV_CATEGORY_BASELINES`
    keyed by the product's top-level category.

    CF dimensions (Training Commitment, Build Capacity, Delivery Capacity,
    Organizational DNA) use per-organization-type baselines from
    `CF_ORG_BASELINES` keyed by the company classification.

    Returns 0 if no baseline is configured or context is missing — the
    caller treats missing baselines as "no posture shift applied."
    """
    if not context:
        return 0

    if dim_key in _IV_DIMENSION_KEYS:
        category = (context.get("product_category") or "").strip()
        if not category:
            return 0
        lookup = cfg.IV_CATEGORY_BASELINES.get(category)
        if lookup is None:
            # Fall back to the canonical Unknown baseline — neutral,
            # with the classification review flag raised in compute_all.
            lookup = cfg.IV_CATEGORY_BASELINES.get(cfg.UNKNOWN_CLASSIFICATION, {})
        return int(lookup.get(dim_key, 0))

    if dim_key in _CF_DIMENSION_KEYS:
        org_type = (context.get("org_type") or "").strip()
        if not org_type:
            return 0
        lookup = cfg.CF_ORG_BASELINES.get(org_type)
        if lookup is None:
            lookup = cfg.CF_ORG_BASELINES.get(cfg.UNKNOWN_CLASSIFICATION, {})
        return int(lookup.get(dim_key, 0))

    return 0


def _build_cf_penalty_lookup() -> dict[tuple[str, str], cfg.PenaltySignal]:
    """Map (dimension_key, signal_category) -> PenaltySignal for CF penalties.

    The AI emits a badge with one of the penalty signal_category values
    defined in the CF_PENALTY_SIGNALS list.  The math layer detects these
    and applies the hit as a subtraction (positive integer in the
    PenaltySignal.hit field, negated when applied).
    """
    out: dict[tuple[str, str], cfg.PenaltySignal] = {}
    for pen in cfg.CF_PENALTY_SIGNALS:
        out[(pen.dimension, pen.category)] = pen
    return out


_CF_PENALTY_LOOKUP = _build_cf_penalty_lookup()


# ─────────────────────────────────────────────────────────────────────────────
# Dimension score computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_dimension_score(dim_key: str,
                            badges: Iterable,
                            context: dict | None = None) -> dict:
    """Compute the score for one dimension from the badges the AI emitted.

    THREE scoring patterns are supported and chosen automatically:

    1. **Rubric pattern** (Pillar 2 Instructional Value, Pillar 3 Customer Fit):
       the dimension defines a `rubric` with strength tiers (strong/moderate/weak).
       Scoring applies a **posture baseline** derived from the product's
       category (IV) or the organization's type (CF), then adds positive
       findings (rubric credits) and subtracts penalty-signal hits and red
       color contributions.  Default-positive posture: missing evidence
       means baseline, not zero.

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
        context: Optional dict with scoring context used by the rubric model:
                 - "product_category" — top-level category from discovery,
                   used for IV dimension baseline lookup
                 - "org_type" — organization classification from discovery,
                   used for CF dimension baseline lookup
                 Missing context values fall back to zero baseline (legacy
                 behavior) so callers can be upgraded incrementally.

    Returns:
        A dict with the score breakdown so the result is auditable:
        {
            "score": int,
            "weight": int,
            "model": "rubric" | "signal_penalty",
            "baseline": int (rubric model only),
            "signals_matched": [...] (signal/penalty model),
            "penalties_applied": [...] (signal/penalty model + CF rubric penalties),
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
            "baseline": 0,
            "signals_matched": [], "penalties_applied": [], "rubric_credits": [],
            "color_contributions": [],
            "raw_total": 0, "capped": False, "floored": False,
            "unknown_badges": [],
        }

    # Rubric model (Pillar 2 + Pillar 3) — branch early so the rest of this
    # function only handles signal/penalty dimensions.
    if dim.rubric is not None:
        return _compute_rubric_dimension_score(dim, dim_key, badges, context)

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

    # ── Risk cap reduction (Pillar 1 only) ─────────────────────────────────
    # A dimension can never be at full cap when there's a known risk badge.
    # Count visible risk badges (amber or red color) in the dimension and
    # lower the effective cap by AMBER_RISK_CAP_REDUCTION per amber and
    # RED_RISK_CAP_REDUCTION per red. This is a CAP REDUCTION, not a
    # deduction — if raw_total is already below the lowered cap, there's
    # no further effect (no double-counting with the half-credit and
    # color-fallback rules that already apply above).
    #
    # Linear compounding: each risk knocks more off. Hard floor at the
    # dimension's existing floor prevents pathological negatives.
    #
    # See scoring_config.AMBER_RISK_CAP_REDUCTION docstring for the full
    # rationale and calibration. Per Frank's 2026-04-07 directive after
    # reviewing Trellix Endpoint Security · Lab Access at 25/25 despite
    # a Training License Risk badge.
    amber_count = sum(1 for _, color in best_by_name.values() if color == "amber")
    red_count = sum(1 for _, color in best_by_name.values() if color == "red")
    risk_knockdown = (
        amber_count * cfg.AMBER_RISK_CAP_REDUCTION
        + red_count * cfg.RED_RISK_CAP_REDUCTION
    )
    if risk_knockdown > 0:
        effective_cap = max(cap - risk_knockdown, floor)
    else:
        effective_cap = cap

    # ── Scoring dimension breadth cap (Frank 2026-04-07) ────────────────────
    # The Scoring dimension specifically uses a "Grand Slam" rule: full marks
    # (15/15) require AI Vision PLUS at least one programmatic method
    # (Script Scoring for VM context OR Scoring API for cloud context).
    # Any single method alone caps at less:
    #   - AI Vision alone           → cap at 10
    #   - Scoring API alone         → cap at 12 (sparse APIs ding it)
    #   - Script Scoring alone      → cap at 15 (VM = anything goes)
    #   - AI Vision + Script        → cap at 15 (Grand Slam, VM)
    #   - AI Vision + API           → cap at 15 (Grand Slam, cloud)
    #   - MCQ Scoring               → 0 points (display only, anyone can MCQ)
    #
    # Implementation: when this is the Scoring dimension, count how many
    # distinct positive scoring methods are present (excluding MCQ since
    # it earns 0 anyway), and cap based on the combination.
    scoring_breadth_cap = None
    if dim.name == "Scoring":
        present_methods = set()
        for name_lower, (_, color) in best_by_name.items():
            if color == "red":
                continue  # red methods don't count toward breadth
            nm = name_lower
            if nm == "ai vision":
                present_methods.add("ai_vision")
            elif nm == "scoring api":
                present_methods.add("scoring_api")
            elif nm == "script scoring":
                present_methods.add("script_scoring")
        has_ai_vision = "ai_vision" in present_methods
        has_api = "scoring_api" in present_methods
        has_script = "script_scoring" in present_methods
        # Grand Slam: AI Vision + (Script OR API) hits the full cap (15)
        if has_ai_vision and (has_script or has_api):
            scoring_breadth_cap = cap  # full marks possible
        # Script Scoring alone: VM context, can do whatever — full cap
        elif has_script:
            scoring_breadth_cap = cap
        # Scoring API alone: cloud context, max from cfg
        elif has_api:
            scoring_breadth_cap = cfg.SCORING_API_ALONE_CAP
        # AI Vision alone: max from cfg
        elif has_ai_vision:
            scoring_breadth_cap = cfg.SCORING_AI_VISION_ALONE_CAP
        # No positive methods (only MCQ or nothing): cap at 0
        else:
            scoring_breadth_cap = 0
        # Combine with the risk-cap reduction (whichever is tighter wins)
        if scoring_breadth_cap < effective_cap:
            effective_cap = scoring_breadth_cap

    score = raw_total
    capped = False
    floored = False
    risk_capped = False
    breadth_capped = False
    if score > effective_cap:
        breadth_capped = (scoring_breadth_cap is not None
                          and effective_cap == scoring_breadth_cap
                          and scoring_breadth_cap < cap)
        score = effective_cap
        capped = True
        if effective_cap < cap and not breadth_capped:
            risk_capped = True
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
        "risk_capped": risk_capped,
        "risk_knockdown": int(risk_knockdown),
        "amber_risk_count": amber_count,
        "red_risk_count": red_count,
        "breadth_capped": breadth_capped,
        "scoring_breadth_cap": scoring_breadth_cap,
        "unknown_badges": unknown,
    }


def _compute_rubric_dimension_score(dim: cfg.Dimension,
                                    dim_key: str,
                                    badges: Iterable,
                                    context: dict | None) -> dict:
    """Rubric-based scoring for Pillar 2 + Pillar 3 dimensions.

    Each badge carries:
      - name (variable, AI-synthesized — used for display only)
      - color (green / amber / red — visual + secondary signal)
      - strength (strong / moderate / weak — required, math driver)
      - signal_category (one of the dimension's fixed category list — for analytics)

    **Scoring flow (updated 2026-04-07):**

      raw_total = baseline + rubric_credits + color_contributions + penalty_hits
      score     = clamp(raw_total, floor, cap)

    Where:

      - **baseline** comes from `IV_CATEGORY_BASELINES[product_category]` for
        IV dimensions or `CF_ORG_BASELINES[org_type]` for CF dimensions.
        The baseline is the realistic starting point for a typical product
        in this category or a typical organization of this type.  Missing
        context falls back to zero baseline for backward compatibility.

      - **rubric credits** are positive contributions from strong/moderate
        badges the AI emitted, graded against the dimension's rubric tiers.

      - **color contributions** include explicit hard negatives (red badges
        like `Consumer Grade`) and legacy fallbacks when strength is missing.

      - **penalty hits** are subtractions triggered by badges whose
        signal_category matches an entry in `CF_PENALTY_SIGNALS` (Customer
        Fit only).  These represent diagnostic absences — no training
        partners, no classroom delivery, long RFP process, etc.  Research
        asymmetry matters: Delivery Capacity penalties fire on absence of
        public evidence; Build Capacity penalties fire only on positive
        evidence of outsourcing (taught in the prompt template).

    Strength → color cross-check (when both present):
      green ↔ strong, amber ↔ moderate, red ↔ hard negative (uses color points)
    """
    rubric = dim.rubric
    assert rubric is not None  # caller already checked

    # Build strength → points lookup from the rubric tiers
    strength_lookup: dict[str, int] = {tier.strength: tier.points for tier in rubric.tiers}

    # Valid signal categories for this dimension (for tag validation, not scoring)
    valid_categories: set[str] = set(rubric.signal_categories)

    rubric_credits: list[dict] = []
    color_contributions: list[dict] = []
    penalties_applied: list[dict] = []
    unknown: list[str] = []

    fallback = cfg.BADGE_UNKNOWN_COLOR_SCORE_FALLBACK

    # Apply the category-aware or org-type baseline first.  Zero if no
    # context is provided — legacy callers still work with old behavior.
    baseline = _get_dimension_baseline(dim_key, context)

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

        # CF penalty signals: if the badge's signal_category matches a
        # PenaltySignal for this dimension, apply the penalty hit instead
        # of normal rubric credit.  This is the mechanism for
        # "No Training Partners", "No Classroom Delivery", "Long RFP
        # Process", "Builds Everything", "Hard to Engage", etc.
        penalty = _CF_PENALTY_LOOKUP.get((dim_key, category))
        if penalty is not None:
            penalties_applied.append({
                "name": raw_name.strip(),
                "signal_category": category,
                "color": penalty.color,
                "badge_name": penalty.badge_name,
                "deduction": -penalty.hit,
            })
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

    # Compute raw total: baseline + positives + negatives + penalties
    rubric_total = sum(c["points"] for c in rubric_credits)
    color_total = sum(c["points"] for c in color_contributions)
    penalty_total = sum(p["deduction"] for p in penalties_applied)
    raw_total = baseline + rubric_total + color_total + penalty_total

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
        "baseline": int(baseline),
        "signals_matched": [],   # not used in rubric model
        "penalties_applied": penalties_applied,
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

def detect_sandbox_api_red_cap(badges_by_dimension: dict[str, list]) -> tuple[int | None, str | None]:
    """Detect when a red Sandbox API badge should cap Pillar 1 at a low value.

    SE-4 from the deep code review backlog. Frank's directive 2026-04-07
    after Diligent review: when there's no per-learner provisioning API
    (Sandbox API red), the entire Pillar 1 should reflect that gap —
    Lab Access / Scoring / Teardown shouldn't independently rack up points
    on a product that essentially can't be provisioned.

    Cap values (Frank 2026-04-07):
      - Sandbox API red + Simulation viable     → cap PL at 25
      - Sandbox API red + nothing else viable   → cap PL at 5

    "Simulation viable" is detected by the presence of the Simulation badge
    in Provisioning (gray Context = chosen path) or the Simulation Reset
    badge in Teardown.

    Returns:
        (cap_value, reason) — both None if no cap applies.
    """
    prov_badges = badges_by_dimension.get("provisioning") or []
    teardown_badges = badges_by_dimension.get("teardown") or []

    # Find Sandbox API badge state
    sandbox_color = None
    for b in prov_badges:
        if not isinstance(b, dict):
            continue
        if (b.get("name") or "").strip().lower() == "sandbox api":
            sandbox_color = (b.get("color") or "").strip().lower()
            break

    if sandbox_color != "red":
        return None, None

    # Sandbox API is red — check if any other path is viable
    # Real provisioning paths: Runs in Hyper-V, Runs in Container, Runs in Azure,
    # Runs in AWS, ESX Required (all green/amber). If any of these is present
    # (not red), the product DOES have a real provisioning path and Sandbox API
    # red is just one of many findings — no cap needed.
    real_path_canonicals = {
        "runs in hyper-v", "runs in container", "runs in azure", "runs in aws",
        "esx required",
    }
    for b in prov_badges:
        if not isinstance(b, dict):
            continue
        nm = (b.get("name") or "").strip().lower()
        col = (b.get("color") or "").strip().lower()
        if nm in real_path_canonicals and col != "red":
            return None, None  # there's a real path; Sandbox API red doesn't cap

    # Sandbox API is red AND no real path is present.
    # Now check if Simulation is at least viable.
    simulation_viable = False
    for b in prov_badges:
        if not isinstance(b, dict):
            continue
        if (b.get("name") or "").strip().lower() == "simulation":
            col = (b.get("color") or "").strip().lower()
            if col != "red":
                simulation_viable = True
                break
    # Also check Teardown for Simulation Reset (alternative signal)
    if not simulation_viable:
        for b in teardown_badges:
            if not isinstance(b, dict):
                continue
            if (b.get("name") or "").strip().lower() == "simulation reset":
                simulation_viable = True
                break

    if simulation_viable:
        return cfg.SANDBOX_API_RED_CAP_SIM_VIABLE, (
            f"Sandbox API red + Simulation viable: no per-learner provisioning "
            f"API and no real fabric path. Simulation is the only viable lab "
            f"delivery method. Pillar 1 capped at {cfg.SANDBOX_API_RED_CAP_SIM_VIABLE}."
        )
    else:
        return cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE, (
            f"Sandbox API red + nothing viable: no per-learner provisioning "
            f"API, no real fabric path, no Simulation viable. The product "
            f"cannot be labbed in any meaningful way. Pillar 1 capped at "
            f"{cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE}."
        )


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
      3. **Pure 70/30 weighted sum.** No PL floor anymore — Pillars 2 and
         3 can drag the Fit Score below the PL score when the product
         lacks instructional value or the company isn't a training buyer.
         A perfectly labable product with zero training case isn't a
         high Fit Score.

    HISTORY: Earlier versions of this function used `max(weighted_sum, pl_score)`
    so PL acted as a floor — IV/CF could only LIFT the score, never drag it
    down. Removed 2026-04-07 after Frank's Diligent review surfaced the
    case where Diligent Boards had PL=66 (technically labable) but IV=33
    (thin instructional case) and CF=23 (no training maturity), and the
    floor pinned the Fit Score at 66 (Solid Prospect) instead of 43 (Keep
    Watch — the honest signal). The framework's 70/30 product/org weighting
    is the right formula; the floor was fighting the framework.

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

    return max(0, min(100, round(weighted_sum)))


# ─────────────────────────────────────────────────────────────────────────────
# All-in-one entry point
# ─────────────────────────────────────────────────────────────────────────────

def compute_all(badges_by_dimension: dict[str, list[str]],
                ceiling_flags: Iterable[str],
                orchestration_method: str,
                context: dict | None = None) -> dict:
    """Compute the full scoring breakdown for one product.

    Args:
        badges_by_dimension: Map of dimension key -> list of badge names the
            AI assigned. Dimension keys are lowercase with underscores
            (e.g., "lab_access", "product_complexity").
        ceiling_flags: Flags the AI emitted (e.g., {"saas_only"}).
        orchestration_method: e.g., "Hyper-V", "Azure Cloud Slice", etc.
        context: Optional scoring context dict carrying metadata used by
            the rubric model to apply category-aware baselines:
              - "product_category" — top-level category from discovery
                (used for IV dimension baselines: Product Complexity,
                Mastery Stakes, Lab Versatility, Market Demand)
              - "org_type" — company classification from discovery
                (used for CF dimension baselines: Training Commitment,
                Build Capacity, Delivery Capacity, Organizational DNA)
            Missing keys fall back to zero baseline.  The presence of
            "Unknown" as product_category or org_type triggers the
            classification review flag in the dossier UX.

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
            "classification_review_needed": bool,
        }
    """
    dim_results: dict[str, dict] = {}
    dim_scores: dict[str, int] = {}

    # Detect the Unknown classification flag once up front so the scorer
    # can surface "Review Classification" in the dossier UX.  This fires
    # whenever the product category or organization type matches the
    # canonical UNKNOWN_CLASSIFICATION constant (from a failed or
    # low-confidence classification upstream).  Define-Once — no hardcoded
    # "Unknown" literal anywhere in this module.
    classification_review_needed = False
    if context:
        unknown_label = cfg.UNKNOWN_CLASSIFICATION
        if (context.get("product_category") or "").strip() == unknown_label:
            classification_review_needed = True
        if (context.get("org_type") or "").strip() == unknown_label:
            classification_review_needed = True

    for dim_key, badges in badges_by_dimension.items():
        result = compute_dimension_score(dim_key, badges, context)
        dim_results[dim_key] = result
        dim_scores[dim_key] = result["score"]

    pl_pre = compute_pillar_score("product_labability", dim_scores)
    iv_score = compute_pillar_score("instructional_value", dim_scores)
    cf_score = compute_pillar_score("customer_fit", dim_scores)

    # SE-4: Sandbox API red cap. When the product has no real provisioning
    # path and no per-learner provisioning API, cap Pillar 1 low so the
    # other dimensions can't independently run up the score on a product
    # that essentially can't be labbed. Per Frank's directive 2026-04-07
    # after Diligent review.
    sandbox_red_cap, sandbox_red_reason = detect_sandbox_api_red_cap(badges_by_dimension)
    if sandbox_red_cap is not None and pl_pre > sandbox_red_cap:
        log.info("compute_all: Sandbox API red cap applied — PL %d → %d (%s)",
                 pl_pre, sandbox_red_cap, sandbox_red_reason)
        pl_pre = sandbox_red_cap

    pl_score, ceilings_applied = apply_ceiling_flags(pl_pre, ceiling_flags)
    if sandbox_red_cap is not None:
        # Add the sandbox-api-red cap to the audit trail so the dossier can
        # surface it like any other ceiling.
        ceilings_applied = list(ceilings_applied) + [{
            "flag": "sandbox_api_red",
            "max_score": sandbox_red_cap,
            "reason": sandbox_red_reason,
        }]
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
        "classification_review_needed": classification_review_needed,
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
