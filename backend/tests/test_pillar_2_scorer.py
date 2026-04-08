"""Pillar 2 (Instructional Value) Python scorer — canned-grade spot tests.

Step 4 of the Research → Store → Score → Badge rebuild.  Feeds canned
GradedSignal lists into backend/pillar_2_scorer.py and asserts the
resulting dimension scores match expectations derived from
scoring_config.py baselines, tier points, penalties, and caps.

NO hardcoded expected score values in assertions — every expected
number is computed from scoring_config.py constants so a config tweak
automatically updates the assertions.
"""

from __future__ import annotations

import scoring_config as cfg
import pillar_2_scorer as p2
from models import GradedSignal


def _baseline(dim_key: str, category: str) -> int:
    """Helper: baseline value from cfg for a given category/dim."""
    return int(cfg.IV_CATEGORY_BASELINES.get(category, {}).get(dim_key, 0))


def _tier_points(dim_name: str, strength: str) -> int:
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            if dim.name == dim_name and dim.rubric:
                for t in dim.rubric.tiers:
                    if t.strength == strength:
                        return t.points
    return 0


def _dim_weight(dim_name: str) -> int:
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            if dim.name == dim_name:
                return dim.weight
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Baseline-only scoring
# ─────────────────────────────────────────────────────────────────────────────

def test_product_complexity_baseline_only_cybersecurity():
    """No grades → Cybersecurity baseline flows directly into the dimension."""
    result = p2.score_product_complexity("Cybersecurity", [])
    expected = _baseline("product_complexity", "Cybersecurity")
    assert result.dimension_score.score == expected
    assert result.baseline == expected


def test_mastery_stakes_baseline_only_fintech():
    result = p2.score_mastery_stakes("FinTech", [])
    expected = _baseline("mastery_stakes", "FinTech")
    assert result.dimension_score.score == expected


def test_unknown_category_falls_back_to_unknown_baseline():
    """A category not in IV_CATEGORY_BASELINES → Unknown classification baseline."""
    result = p2.score_product_complexity("NoSuchCategory", [])
    expected = _baseline("product_complexity", cfg.UNKNOWN_CLASSIFICATION)
    assert result.dimension_score.score == expected


# ─────────────────────────────────────────────────────────────────────────────
# Positive rubric credits (strength tiers)
# ─────────────────────────────────────────────────────────────────────────────

def test_strong_signal_adds_tier_points_on_top_of_baseline():
    """Single strong positive signal = baseline + strong tier points (capped)."""
    # Use Cybersecurity because it already has a high baseline
    grades = [
        GradedSignal(
            signal_category="multi_vm_architecture",
            strength="strong",
            evidence_text="confirmed multi-VM topology",
            confidence="confirmed",
            color="green",
        ),
    ]
    result = p2.score_product_complexity("Cybersecurity", grades)
    baseline = _baseline("product_complexity", "Cybersecurity")
    strong_pts = _tier_points("Product Complexity", "strong")
    expected_raw = baseline + strong_pts
    # Capped at dimension weight
    expected_score = min(expected_raw, _dim_weight("Product Complexity"))
    assert result.dimension_score.score == expected_score


def test_moderate_signal_credits_moderate_tier_points():
    grades = [
        GradedSignal(
            signal_category="deep_configuration",
            strength="moderate",
            evidence_text="indicated by docs",
            confidence="indicated",
            color="green",
        ),
    ]
    result = p2.score_product_complexity("CRM", grades)
    baseline = _baseline("product_complexity", "CRM")
    mod_pts = _tier_points("Product Complexity", "moderate")
    assert result.raw_total == baseline + mod_pts


def test_multiple_positive_signals_stack_up_to_cap():
    """Many strong signals should stack but get capped at dimension weight."""
    grades = [
        GradedSignal(signal_category="multi_vm_architecture", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        GradedSignal(signal_category="deep_configuration", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        GradedSignal(signal_category="role_diversity", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
    ]
    result = p2.score_product_complexity("Cybersecurity", grades)
    cap = _dim_weight("Product Complexity")
    # Raw should exceed cap
    assert result.raw_total > cap
    # Final score should be capped at the dimension weight
    assert result.dimension_score.score == cap


# ─────────────────────────────────────────────────────────────────────────────
# Negative signals (penalties + risk cap reduction)
# ─────────────────────────────────────────────────────────────────────────────

def test_red_penalty_subtracts_hit_and_counts_as_red_risk():
    """A red penalty signal subtracts its hit AND counts toward cap reduction."""
    # Use a Market Demand penalty since that's where it lives now
    grades = [
        GradedSignal(
            signal_category="no_independent_training_market",
            strength="strong",
            evidence_text="zero courses found",
            confidence="confirmed",
            color="amber",  # This penalty is amber per config
        ),
    ]
    result = p2.score_market_demand("Cybersecurity", grades)
    # Baseline should have been reduced by the penalty hit
    baseline = _baseline("market_demand", "Cybersecurity")
    penalty = None
    for p in cfg.RUBRIC_PENALTY_SIGNALS:
        if p.dimension == "market_demand" and p.category == "no_independent_training_market":
            penalty = p
            break
    assert penalty is not None
    assert result.raw_total == baseline - penalty.hit
    assert result.amber_risks == 1


def test_risk_cap_reduction_extends_to_pillar_2():
    """A dimension with amber risks should have its cap reduced by
    cfg.AMBER_RISK_CAP_REDUCTION per amber (Frank 2026-04-08)."""
    grades = [
        # Positive strong — but also an amber risk
        GradedSignal(signal_category="install_base_scale", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        # Amber penalty pulls cap down
        GradedSignal(signal_category="no_independent_training_market", strength="strong", evidence_text="e", confidence="confirmed", color="amber"),
    ]
    result = p2.score_market_demand("Cybersecurity", grades)
    cap = _dim_weight("Market Demand")
    expected_effective_cap = cap - cfg.AMBER_RISK_CAP_REDUCTION
    assert result.effective_cap == expected_effective_cap


# ─────────────────────────────────────────────────────────────────────────────
# Dedupe: same signal_category emitted twice, keep strongest
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_signal_category_keeps_strongest_strength():
    """If a grader emits the same signal_category twice, keep the strongest."""
    grades = [
        GradedSignal(signal_category="multi_vm_architecture", strength="weak", evidence_text="e", confidence="inferred", color="green"),
        GradedSignal(signal_category="multi_vm_architecture", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
    ]
    result = p2.score_product_complexity("Cybersecurity", grades)
    baseline = _baseline("product_complexity", "Cybersecurity")
    strong_pts = _tier_points("Product Complexity", "strong")
    assert result.raw_total == baseline + strong_pts


# ─────────────────────────────────────────────────────────────────────────────
# Unknown signal categories get dropped
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_signal_category_is_dropped():
    """A grade with a signal_category not in the rubric should be silently dropped."""
    grades = [
        GradedSignal(signal_category="not_a_real_category", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
    ]
    result = p2.score_product_complexity("Cybersecurity", grades)
    baseline = _baseline("product_complexity", "Cybersecurity")
    # Raw should be the baseline — the unknown signal credited nothing
    assert result.raw_total == baseline


# ─────────────────────────────────────────────────────────────────────────────
# Pillar composer — full Pillar 2 from grades-by-dim dict
# ─────────────────────────────────────────────────────────────────────────────

def test_pillar_composer_returns_all_four_dimensions():
    grades_by_dim = {
        "product_complexity": [
            GradedSignal(signal_category="multi_vm_architecture", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        ],
        "mastery_stakes": [],
        "lab_versatility": [],
        "market_demand": [],
    }
    pillar = p2.score_instructional_value("Cybersecurity", grades_by_dim)
    assert len(pillar.dimensions) == 4
    names = [d.name for d in pillar.dimensions]
    assert "Product Complexity" in names
    assert "Mastery Stakes" in names
    assert "Lab Versatility" in names
    assert "Market Demand" in names


def test_pillar_weights_sum_to_100():
    total = (
        _dim_weight("Product Complexity")
        + _dim_weight("Mastery Stakes")
        + _dim_weight("Lab Versatility")
        + _dim_weight("Market Demand")
    )
    assert total == 100


def test_pillar_iv_weight_matches_config():
    pillar = p2.score_instructional_value(None, {})
    # weight should come from cfg.PILLARS
    expected_weight = 0
    for p in cfg.PILLARS:
        if p.name == "Instructional Value":
            expected_weight = p.weight
            break
    assert pillar.weight == expected_weight


def test_empty_grades_returns_baseline_pillar_score():
    """No grades at all → each dim scores its baseline → pillar is sum of baselines."""
    pillar = p2.score_instructional_value("Cybersecurity", {})
    expected = (
        _baseline("product_complexity", "Cybersecurity")
        + _baseline("mastery_stakes", "Cybersecurity")
        + _baseline("lab_versatility", "Cybersecurity")
        + _baseline("market_demand", "Cybersecurity")
    )
    assert pillar.score == min(expected, 100)
