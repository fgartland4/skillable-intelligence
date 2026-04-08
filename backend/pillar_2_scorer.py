"""Pillar 2 (Instructional Value) scoring from facts + rubric grades.

Pure Python. No Claude. Reads:
  - Rubric grades produced by backend/rubric_grader.py (the narrow slice
    of Claude-in-Score the rebuild permits — strength grading +
    evidence text only)
  - Typed primitives from InstructionalValueFacts where applicable
  - Product category for baseline lookup

Applies:
  - Category baseline from cfg.IV_CATEGORY_BASELINES
  - Rubric credits (strength → tier points from the dimension's rubric)
  - Named penalties from cfg.RUBRIC_PENALTY_SIGNALS keyed by
    (dimension, signal_category)
  - Risk cap reduction (extended to Pillar 2/3 per Frank 2026-04-08 —
    reuses cfg.AMBER_RISK_CAP_REDUCTION and cfg.RED_RISK_CAP_REDUCTION)
  - Dimension cap + floor from cfg

Architecture layer: SCORE (pure Python, deterministic) per Three Layers
of Intelligence in docs/Platform-Foundation.md.

NO HARDCODING. Every number, weight, threshold, and rule parameter
comes from scoring_config.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import scoring_config as cfg
from models import DimensionScore, GradedSignal, PillarScore


# ═══════════════════════════════════════════════════════════════════════════════
# Canonical name constants (each string appears once)
# ═══════════════════════════════════════════════════════════════════════════════

_PILLAR_IV_NAME = "Instructional Value"
_DIM_PRODUCT_COMPLEXITY = "Product Complexity"
_DIM_MASTERY_STAKES = "Mastery Stakes"
_DIM_LAB_VERSATILITY = "Lab Versatility"
_DIM_MARKET_DEMAND = "Market Demand"

_DIM_KEY_PC = "product_complexity"
_DIM_KEY_MS = "mastery_stakes"
_DIM_KEY_LV = "lab_versatility"
_DIM_KEY_MD = "market_demand"


# ═══════════════════════════════════════════════════════════════════════════════
# Config lookups — resolved once at module load
# ═══════════════════════════════════════════════════════════════════════════════

def _find_pillar(name: str) -> cfg.Pillar:
    for p in cfg.PILLARS:
        if p.name == name:
            return p
    raise RuntimeError(f"pillar_2_scorer: pillar {name!r} not found")


def _find_dimension(pillar: cfg.Pillar, dim_name: str) -> cfg.Dimension:
    for d in pillar.dimensions:
        if d.name == dim_name:
            return d
    raise RuntimeError(
        f"pillar_2_scorer: dimension {dim_name!r} not found in pillar {pillar.name!r}"
    )


_IV_PILLAR = _find_pillar(_PILLAR_IV_NAME)
_PC_DIM = _find_dimension(_IV_PILLAR, _DIM_PRODUCT_COMPLEXITY)
_MS_DIM = _find_dimension(_IV_PILLAR, _DIM_MASTERY_STAKES)
_LV_DIM = _find_dimension(_IV_PILLAR, _DIM_LAB_VERSATILITY)
_MD_DIM = _find_dimension(_IV_PILLAR, _DIM_MARKET_DEMAND)


def _build_penalty_lookup() -> dict[tuple[str, str], cfg.PenaltySignal]:
    """Build a (dim_key, signal_category) → PenaltySignal lookup from config."""
    out: dict[tuple[str, str], cfg.PenaltySignal] = {}
    for penalty in cfg.RUBRIC_PENALTY_SIGNALS:
        out[(penalty.dimension, penalty.category)] = penalty
    return out


_PENALTY_LOOKUP = _build_penalty_lookup()


def _tier_points_lookup(dim: cfg.Dimension) -> dict[str, int]:
    """Map strength tier name to point value from a dimension's rubric."""
    if dim.rubric is None:
        return {}
    return {t.strength: t.points for t in dim.rubric.tiers}


_PC_TIER_POINTS = _tier_points_lookup(_PC_DIM)
_MS_TIER_POINTS = _tier_points_lookup(_MS_DIM)
_LV_TIER_POINTS = _tier_points_lookup(_LV_DIM)
_MD_TIER_POINTS = _tier_points_lookup(_MD_DIM)

_PC_VALID_CATS: set[str] = set(_PC_DIM.rubric.signal_categories) if _PC_DIM.rubric else set()
_MS_VALID_CATS: set[str] = set(_MS_DIM.rubric.signal_categories) if _MS_DIM.rubric else set()
_LV_VALID_CATS: set[str] = set(_LV_DIM.rubric.signal_categories) if _LV_DIM.rubric else set()
_MD_VALID_CATS: set[str] = set(_MD_DIM.rubric.signal_categories) if _MD_DIM.rubric else set()


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
    raw_total: int = 0
    effective_cap: int = 0


def _dim_cap(dim: cfg.Dimension) -> int:
    return dim.cap if dim.cap is not None else dim.weight


def _dim_floor(dim: cfg.Dimension) -> int:
    return dim.floor if dim.floor is not None else 0


def _apply_risk_cap_reduction(
    raw_total: int,
    dim: cfg.Dimension,
    amber_risks: int,
    red_risks: int,
) -> tuple[int, int]:
    """Risk cap reduction extended to Pillar 2/3 (Frank 2026-04-08).

    Same mechanic as Pillar 1: each amber knocks cfg.AMBER_RISK_CAP_REDUCTION
    off the cap, each red knocks cfg.RED_RISK_CAP_REDUCTION off. Hard
    floored at the dimension's floor.
    """
    base_cap = _dim_cap(dim)
    floor = _dim_floor(dim)
    knockdown = (
        amber_risks * cfg.AMBER_RISK_CAP_REDUCTION
        + red_risks * cfg.RED_RISK_CAP_REDUCTION
    )
    effective_cap = max(base_cap - knockdown, floor)
    score = max(min(raw_total, effective_cap), floor)
    return int(score), int(effective_cap)


def _iv_category_baseline(dim_key: str, product_category: str | None) -> int:
    """Look up the per-category baseline for an IV dimension.

    Falls back to cfg.UNKNOWN_CLASSIFICATION if the category isn't in
    the table, and then to 0 if even that baseline isn't configured.
    """
    category = (product_category or "").strip() or cfg.UNKNOWN_CLASSIFICATION
    lookup = cfg.IV_CATEGORY_BASELINES.get(category)
    if lookup is None:
        lookup = cfg.IV_CATEGORY_BASELINES.get(cfg.UNKNOWN_CLASSIFICATION, {})
    return int(lookup.get(dim_key, 0))


# ═══════════════════════════════════════════════════════════════════════════════
# Generic rubric dimension scorer
# ═══════════════════════════════════════════════════════════════════════════════

def _score_rubric_dimension(
    dim: cfg.Dimension,
    dim_key: str,
    tier_points: dict[str, int],
    valid_categories: set[str],
    grades: list[GradedSignal],
    baseline: int,
) -> _DimensionResult:
    """Score one rubric dimension from its GradedSignal list + a baseline.

    Walks the grades, splits them into positive credits vs named
    penalties, counts color risks, applies risk cap reduction, clamps
    to [floor, effective_cap].
    """
    raw = baseline
    signals_credited: list[tuple[str, int]] = []
    penalties_applied: list[tuple[str, int]] = []
    amber_risks = 0
    red_risks = 0

    # Dedupe by signal_category — keep the STRONGEST instance of each
    # category. Graders are instructed to emit one signal per category,
    # but defensive dedupe keeps the math stable if they slip.
    best_by_category: dict[str, GradedSignal] = {}
    _tier_rank = {"strong": 3, "moderate": 2, "weak": 1, "informational": 0, "": 0}
    for grade in grades:
        cat = grade.signal_category
        existing = best_by_category.get(cat)
        if existing is None:
            best_by_category[cat] = grade
            continue
        if _tier_rank.get(grade.strength, 0) > _tier_rank.get(existing.strength, 0):
            best_by_category[cat] = grade

    for cat, grade in best_by_category.items():
        # Skip unknown signal categories — a grader that emits something
        # outside the rubric's signal_categories list is malformed. Log
        # via raw_total (no credit, no penalty).
        if cat not in valid_categories:
            continue

        # Track color risks for the cap reduction at the end
        color = grade.color or ""
        if color == "amber":
            amber_risks += 1
        elif color == "red":
            red_risks += 1

        # Named penalty?
        penalty = _PENALTY_LOOKUP.get((dim_key, cat))
        if penalty is not None:
            raw -= penalty.hit
            penalties_applied.append((cat, -penalty.hit))
            continue

        # Positive rubric credit from tier points
        pts = int(tier_points.get(grade.strength, 0))
        if pts:
            raw += pts
            signals_credited.append((cat, pts))

    score, effective_cap = _apply_risk_cap_reduction(raw, dim, amber_risks, red_risks)

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
        raw_total=raw,
        effective_cap=effective_cap,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Per-dimension scorers
# ═══════════════════════════════════════════════════════════════════════════════

def score_product_complexity(
    product_category: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _iv_category_baseline(_DIM_KEY_PC, product_category)
    return _score_rubric_dimension(
        _PC_DIM, _DIM_KEY_PC, _PC_TIER_POINTS, _PC_VALID_CATS, grades, baseline,
    )


def score_mastery_stakes(
    product_category: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _iv_category_baseline(_DIM_KEY_MS, product_category)
    return _score_rubric_dimension(
        _MS_DIM, _DIM_KEY_MS, _MS_TIER_POINTS, _MS_VALID_CATS, grades, baseline,
    )


def score_lab_versatility(
    product_category: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _iv_category_baseline(_DIM_KEY_LV, product_category)
    return _score_rubric_dimension(
        _LV_DIM, _DIM_KEY_LV, _LV_TIER_POINTS, _LV_VALID_CATS, grades, baseline,
    )


def score_market_demand(
    product_category: str | None,
    grades: list[GradedSignal],
) -> _DimensionResult:
    baseline = _iv_category_baseline(_DIM_KEY_MD, product_category)
    return _score_rubric_dimension(
        _MD_DIM, _DIM_KEY_MD, _MD_TIER_POINTS, _MD_VALID_CATS, grades, baseline,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar composer
# ═══════════════════════════════════════════════════════════════════════════════

def score_instructional_value(
    product_category: str | None,
    rubric_grades_by_dim: dict[str, list[GradedSignal]],
) -> PillarScore:
    """Compose the four Pillar 2 dimensions into a PillarScore.

    Args:
        product_category: top-level product category (drives baseline lookup)
        rubric_grades_by_dim: {dim_key: [GradedSignal, ...]} as produced
            by rubric_grader.grade_all_for_product

    Returns a PillarScore with four DimensionScores attached.
    """
    pc = score_product_complexity(product_category, rubric_grades_by_dim.get(_DIM_KEY_PC, []))
    ms = score_mastery_stakes(product_category, rubric_grades_by_dim.get(_DIM_KEY_MS, []))
    lv = score_lab_versatility(product_category, rubric_grades_by_dim.get(_DIM_KEY_LV, []))
    md = score_market_demand(product_category, rubric_grades_by_dim.get(_DIM_KEY_MD, []))

    return PillarScore(
        name=_IV_PILLAR.name,
        weight=_IV_PILLAR.weight,
        dimensions=[
            pc.dimension_score,
            ms.dimension_score,
            lv.dimension_score,
            md.dimension_score,
        ],
    )
