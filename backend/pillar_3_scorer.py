"""Pillar 3 (Customer Fit) scoring from facts + rubric grades.

Pure Python. No Claude. Reads:
  - Rubric grades produced by backend/rubric_grader.py (the narrow slice
    of Claude-in-Score the rebuild permits — strength grading +
    evidence text only)
  - Typed facts from CustomerFitFacts where applicable
  - Organization type for baseline lookup

Applies:
  - Org-type baseline from cfg.CF_ORG_BASELINES
  - Rubric credits (strength → tier points from the dimension's rubric)
  - Named penalties from cfg.RUBRIC_PENALTY_SIGNALS keyed by
    (dimension, signal_category)
  - Risk cap reduction (extended to Pillar 2/3 per Frank 2026-04-08)
  - Dimension cap + floor from cfg

Architecture layer: SCORE (pure Python, deterministic) per Three Layers
of Intelligence.

Customer Fit is per-COMPANY (not per-product). Each product from the
same company shares the same Pillar 3 score. Pillar 3 graders read
company-level facts plus a few cross-pillar reads from products (e.g.,
vendor_published_on_third_party for Build/Delivery Capacity).

NO HARDCODING. Every number, weight, threshold, and rule parameter
comes from scoring_config.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import scoring_config as cfg
from models import DimensionScore, GradedSignal, PillarScore


# ═══════════════════════════════════════════════════════════════════════════════
# Canonical name constants
# ═══════════════════════════════════════════════════════════════════════════════

_PILLAR_CF_NAME = "Customer Fit"
_DIM_TRAINING_COMMITMENT = "Training Commitment"
_DIM_BUILD_CAPACITY = "Build Capacity"
_DIM_DELIVERY_CAPACITY = "Delivery Capacity"
_DIM_ORGANIZATIONAL_DNA = "Organizational DNA"

_DIM_KEY_TC = "training_commitment"
_DIM_KEY_BC = "build_capacity"
_DIM_KEY_DC = "delivery_capacity"
_DIM_KEY_OD = "organizational_dna"


# ═══════════════════════════════════════════════════════════════════════════════
# Config lookups — resolved once at module load
# ═══════════════════════════════════════════════════════════════════════════════

def _find_pillar(name: str) -> cfg.Pillar:
    for p in cfg.PILLARS:
        if p.name == name:
            return p
    raise RuntimeError(f"pillar_3_scorer: pillar {name!r} not found")


def _find_dimension(pillar: cfg.Pillar, dim_name: str) -> cfg.Dimension:
    for d in pillar.dimensions:
        if d.name == dim_name:
            return d
    raise RuntimeError(
        f"pillar_3_scorer: dimension {dim_name!r} not found in pillar {pillar.name!r}"
    )


_CF_PILLAR = _find_pillar(_PILLAR_CF_NAME)
_TC_DIM = _find_dimension(_CF_PILLAR, _DIM_TRAINING_COMMITMENT)
_BC_DIM = _find_dimension(_CF_PILLAR, _DIM_BUILD_CAPACITY)
_DC_DIM = _find_dimension(_CF_PILLAR, _DIM_DELIVERY_CAPACITY)
_OD_DIM = _find_dimension(_CF_PILLAR, _DIM_ORGANIZATIONAL_DNA)


def _build_penalty_lookup() -> dict[tuple[str, str], cfg.PenaltySignal]:
    out: dict[tuple[str, str], cfg.PenaltySignal] = {}
    for penalty in cfg.RUBRIC_PENALTY_SIGNALS:
        out[(penalty.dimension, penalty.category)] = penalty
    return out


_PENALTY_LOOKUP = _build_penalty_lookup()


def _tier_points_lookup(dim: cfg.Dimension) -> dict[str, int]:
    if dim.rubric is None:
        return {}
    return {t.strength: t.points for t in dim.rubric.tiers}


_TC_TIER_POINTS = _tier_points_lookup(_TC_DIM)
_BC_TIER_POINTS = _tier_points_lookup(_BC_DIM)
_DC_TIER_POINTS = _tier_points_lookup(_DC_DIM)
_OD_TIER_POINTS = _tier_points_lookup(_OD_DIM)

_TC_VALID_CATS: set[str] = set(_TC_DIM.rubric.signal_categories) if _TC_DIM.rubric else set()
_BC_VALID_CATS: set[str] = set(_BC_DIM.rubric.signal_categories) if _BC_DIM.rubric else set()
_DC_VALID_CATS: set[str] = set(_DC_DIM.rubric.signal_categories) if _DC_DIM.rubric else set()
_OD_VALID_CATS: set[str] = set(_OD_DIM.rubric.signal_categories) if _OD_DIM.rubric else set()


# ═══════════════════════════════════════════════════════════════════════════════
# Intermediate result + helpers
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class _DimensionResult:
    dimension_score: DimensionScore
    baseline: int = 0
    signals_credited: list[tuple[str, int]] = field(default_factory=list)
    penalties_applied: list[tuple[str, int]] = field(default_factory=list)
    amber_risks: int = 0
    red_risks: int = 0
    positive_total: int = 0
    penalty_total: int = 0
    raw_total: int = 0
    effective_cap: int = 0
    positives_capped: bool = False
    floored: bool = False


def _dim_cap(dim: cfg.Dimension) -> int:
    return dim.cap if dim.cap is not None else dim.weight


def _dim_floor(dim: cfg.Dimension) -> int:
    return dim.floor if dim.floor is not None else 0


def _apply_risk_cap_reduction(
    positive_total: int,
    penalty_total: int,
    dim: cfg.Dimension,
    amber_risks: int,
    red_risks: int,
) -> tuple[int, int, bool, bool]:
    """Compose the final dimension score under the penalty-visibility rule.

    Penalty-visibility rule (Frank 2026-04-07, Trellix Org DNA 25/25
    regression): named penalties must ALWAYS be reflected in the final
    score, even when positive contributions would otherwise overflow
    the dimension cap.

    Math:
        capped_positive = min(positive_total, effective_cap)
        score           = max(capped_positive + penalty_total, floor)

    penalty_total is passed in as a negative number (already signed).
    Returns (score, effective_cap, positives_capped, floored).
    """
    base_cap = _dim_cap(dim)
    floor = _dim_floor(dim)
    knockdown = (
        amber_risks * cfg.AMBER_RISK_CAP_REDUCTION
        + red_risks * cfg.RED_RISK_CAP_REDUCTION
    )
    effective_cap = max(base_cap - knockdown, floor)

    capped_positive = min(positive_total, effective_cap)
    positives_capped = positive_total > effective_cap

    raw_with_penalties = capped_positive + penalty_total
    floored = raw_with_penalties < floor
    score = max(raw_with_penalties, floor)

    return int(score), int(effective_cap), positives_capped, floored


def _cf_org_baseline(dim_key: str, org_type: str | None) -> int:
    """Look up the per-org-type baseline for a Customer Fit dimension.

    Falls back to cfg.UNKNOWN_CLASSIFICATION if the org type isn't in
    the table.
    """
    org = (org_type or "").strip() or cfg.UNKNOWN_CLASSIFICATION
    lookup = cfg.CF_ORG_BASELINES.get(org)
    if lookup is None:
        lookup = cfg.CF_ORG_BASELINES.get(cfg.UNKNOWN_CLASSIFICATION, {})
    return int(lookup.get(dim_key, 0))


# ═══════════════════════════════════════════════════════════════════════════════
# Generic rubric dimension scorer (same pattern as pillar_2_scorer)
# ═══════════════════════════════════════════════════════════════════════════════

def _score_rubric_dimension(
    dim: cfg.Dimension,
    dim_key: str,
    tier_points: dict[str, int],
    valid_categories: set[str],
    grades: list[GradedSignal],
    baseline: int,
) -> _DimensionResult:
    positive_total = baseline
    penalty_total = 0
    signals_credited: list[tuple[str, int]] = []
    penalties_applied: list[tuple[str, int]] = []
    amber_risks = 0
    red_risks = 0

    best_by_category: dict[str, GradedSignal] = {}
    _tier_rank = {"strong": 3, "moderate": 2, "weak": 1, "informational": 0, "": 0}  # magic-allowed: rubric strength ordering
    for grade in grades:
        cat = grade.signal_category
        existing = best_by_category.get(cat)
        if existing is None:
            best_by_category[cat] = grade
            continue
        if _tier_rank.get(grade.strength, 0) > _tier_rank.get(existing.strength, 0):
            best_by_category[cat] = grade

    for cat, grade in best_by_category.items():
        if cat not in valid_categories:
            continue

        color = grade.color or ""
        if color == "amber":
            amber_risks += 1
        elif color == "red":
            red_risks += 1

        # Named penalty — tracked separately from positives so the
        # penalty-visibility rule preserves it past the cap.
        penalty = _PENALTY_LOOKUP.get((dim_key, cat))
        if penalty is not None:
            penalty_total -= penalty.hit
            penalties_applied.append((cat, -penalty.hit))
            continue

        pts = int(tier_points.get(grade.strength, 0))
        if pts:
            positive_total += pts
            signals_credited.append((cat, pts))

    score, effective_cap, positives_capped, floored = _apply_risk_cap_reduction(
        positive_total, penalty_total, dim, amber_risks, red_risks,
    )

    return _DimensionResult(
        dimension_score=DimensionScore(
            name=dim.name,
            score=score,
            weight=dim.weight,
        ),
        baseline=baseline,
        signals_credited=signals_credited,
        penalties_applied=penalties_applied,
        amber_risks=amber_risks,
        red_risks=red_risks,
        positive_total=positive_total,
        penalty_total=penalty_total,
        raw_total=positive_total + penalty_total,
        effective_cap=effective_cap,
        positives_capped=positives_capped,
        floored=floored,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Per-dimension scorers
# ═══════════════════════════════════════════════════════════════════════════════

def score_training_commitment(
    org_type: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _cf_org_baseline(_DIM_KEY_TC, org_type)
    return _score_rubric_dimension(
        _TC_DIM, _DIM_KEY_TC, _TC_TIER_POINTS, _TC_VALID_CATS, grades, baseline,
    )


def score_build_capacity(
    org_type: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _cf_org_baseline(_DIM_KEY_BC, org_type)
    return _score_rubric_dimension(
        _BC_DIM, _DIM_KEY_BC, _BC_TIER_POINTS, _BC_VALID_CATS, grades, baseline,
    )


def score_delivery_capacity(
    org_type: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _cf_org_baseline(_DIM_KEY_DC, org_type)
    return _score_rubric_dimension(
        _DC_DIM, _DIM_KEY_DC, _DC_TIER_POINTS, _DC_VALID_CATS, grades, baseline,
    )


def score_organizational_dna(
    org_type: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _cf_org_baseline(_DIM_KEY_OD, org_type)
    return _score_rubric_dimension(
        _OD_DIM, _DIM_KEY_OD, _OD_TIER_POINTS, _OD_VALID_CATS, grades, baseline,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar composer
# ═══════════════════════════════════════════════════════════════════════════════

def score_customer_fit(
    org_type: str | None,
    customer_fit_rubric_grades: dict[str, list[GradedSignal]],
) -> PillarScore:
    """Compose the four Pillar 3 dimensions into a PillarScore.

    Args:
        org_type: Organization type classification (drives baseline lookup)
        customer_fit_rubric_grades: {dim_key: [GradedSignal, ...]} as produced
            by rubric_grader.grade_all_for_company

    Returns a PillarScore with four DimensionScores attached.
    """
    tc = score_training_commitment(org_type, customer_fit_rubric_grades.get(_DIM_KEY_TC, []))
    bc = score_build_capacity(org_type, customer_fit_rubric_grades.get(_DIM_KEY_BC, []))
    dc = score_delivery_capacity(org_type, customer_fit_rubric_grades.get(_DIM_KEY_DC, []))
    od = score_organizational_dna(org_type, customer_fit_rubric_grades.get(_DIM_KEY_OD, []))

    return PillarScore(
        name=_CF_PILLAR.name,
        weight=_CF_PILLAR.weight,
        dimensions=[
            tc.dimension_score,
            bc.dimension_score,
            dc.dimension_score,
            od.dimension_score,
        ],
    )
