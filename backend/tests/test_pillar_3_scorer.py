"""Pillar 3 (Customer Fit) Python scorer — canned-grade spot tests.

Step 4 of the rebuild. Same pattern as test_pillar_2_scorer but for
Customer Fit dimensions. NO hardcoded expected values — everything
computed from scoring_config.py.
"""

from __future__ import annotations

import scoring_config as cfg
import pillar_3_scorer as p3
from models import GradedSignal


def _baseline(dim_key: str, org_type: str) -> int:
    return int(cfg.CF_ORG_BASELINES.get(org_type, {}).get(dim_key, 0))


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


def _penalty(dim_key: str, category: str) -> int:
    for p in cfg.RUBRIC_PENALTY_SIGNALS:
        if p.dimension == dim_key and p.category == category:
            return p.hit
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Baseline-only scoring
# ─────────────────────────────────────────────────────────────────────────────

def test_training_commitment_baseline_only_training_org():
    result = p3.score_training_commitment("TRAINING ORG", [])
    assert result.dimension_score.score == _baseline("training_commitment", "TRAINING ORG")


def test_delivery_capacity_baseline_only_enterprise_software():
    result = p3.score_delivery_capacity("ENTERPRISE SOFTWARE", [])
    assert result.dimension_score.score == _baseline("delivery_capacity", "ENTERPRISE SOFTWARE")


def test_unknown_org_type_falls_back_to_unknown_baseline():
    result = p3.score_build_capacity("NotAnOrgType", [])
    expected = _baseline("build_capacity", cfg.UNKNOWN_CLASSIFICATION)
    assert result.dimension_score.score == expected


# ─────────────────────────────────────────────────────────────────────────────
# Positive rubric credits
# ─────────────────────────────────────────────────────────────────────────────

def test_delivery_capacity_strong_atp_credits_strong_tier():
    grades = [
        GradedSignal(
            signal_category="atp_alp_program",
            strength="strong",
            evidence_text="Global Partner Network confirmed — ~500 ATPs",
            confidence="confirmed",
            color="green",
        ),
    ]
    result = p3.score_delivery_capacity("ENTERPRISE SOFTWARE", grades)
    baseline = _baseline("delivery_capacity", "ENTERPRISE SOFTWARE")
    strong_pts = _tier_points("Delivery Capacity", "strong")
    expected_raw = baseline + strong_pts
    expected_score = min(expected_raw, _dim_weight("Delivery Capacity"))
    assert result.dimension_score.score == expected_score


def test_build_capacity_strong_lab_infrastructure_credits_tier_points():
    """lab_build_capability — the new Frank 2026-04-08 category."""
    grades = [
        GradedSignal(
            signal_category="lab_build_capability",
            strength="strong",
            evidence_text="Skillable lab platform in place",
            confidence="confirmed",
            color="green",
        ),
    ]
    result = p3.score_build_capacity("SOFTWARE", grades)
    baseline = _baseline("build_capacity", "SOFTWARE")
    strong_pts = _tier_points("Build Capacity", "strong")
    assert result.raw_total == baseline + strong_pts


# ─────────────────────────────────────────────────────────────────────────────
# Penalties + risk cap reduction
# ─────────────────────────────────────────────────────────────────────────────

def test_delivery_capacity_red_no_classroom_delivery_applies_penalty():
    grades = [
        GradedSignal(
            signal_category="no_classroom_delivery",
            strength="strong",
            evidence_text="Zero public training calendar found",
            confidence="confirmed",
            color="red",
        ),
    ]
    result = p3.score_delivery_capacity("SOFTWARE", grades)
    baseline = _baseline("delivery_capacity", "SOFTWARE")
    pen = _penalty("delivery_capacity", "no_classroom_delivery")
    assert result.raw_total == baseline - pen
    assert result.red_risks == 1


def test_red_penalty_triggers_risk_cap_reduction_by_cfg_constant():
    """One red signal knocks cfg.RED_RISK_CAP_REDUCTION off the effective cap."""
    grades = [
        GradedSignal(
            signal_category="no_training_partners",
            strength="strong",
            evidence_text="zero ATP network",
            confidence="confirmed",
            color="red",
        ),
    ]
    result = p3.score_delivery_capacity("ENTERPRISE SOFTWARE", grades)
    cap = _dim_weight("Delivery Capacity")
    assert result.effective_cap == cap - cfg.RED_RISK_CAP_REDUCTION


def test_multiple_amber_risks_accumulate_cap_reduction():
    grades = [
        GradedSignal(signal_category="single_region_only", strength="strong", evidence_text="e", confidence="confirmed", color="amber"),
        GradedSignal(signal_category="regional_atp_network", strength="moderate", evidence_text="e", confidence="confirmed", color="amber"),
    ]
    result = p3.score_delivery_capacity("ENTERPRISE SOFTWARE", grades)
    cap = _dim_weight("Delivery Capacity")
    assert result.effective_cap == cap - (2 * cfg.AMBER_RISK_CAP_REDUCTION)


# ─────────────────────────────────────────────────────────────────────────────
# Masking protection: strong positives + red blocker must not hit cap
# ─────────────────────────────────────────────────────────────────────────────

def test_five_strong_positives_plus_one_red_blocker_does_not_hit_cap():
    """Regression test for Frank's masking concern — a dimension with lots of
    strong positives should NOT be able to mask a red blocker. The risk cap
    reduction makes the red visible at the final score level."""
    grades = [
        GradedSignal(signal_category="vendor_delivered_training", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        GradedSignal(signal_category="atp_alp_program", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        GradedSignal(signal_category="lms_partner", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        GradedSignal(signal_category="training_events_scale", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        GradedSignal(signal_category="cert_delivery_infrastructure", strength="strong", evidence_text="e", confidence="confirmed", color="green"),
        # One red blocker in the middle of five positives
        GradedSignal(signal_category="no_classroom_delivery", strength="strong", evidence_text="e", confidence="confirmed", color="red"),
    ]
    result = p3.score_delivery_capacity("ENTERPRISE SOFTWARE", grades)
    full_cap = _dim_weight("Delivery Capacity")
    # The red blocker should cap the dimension below the full cap
    assert result.dimension_score.score < full_cap
    # Specifically, the red risk cap reduction applies
    assert result.effective_cap == full_cap - cfg.RED_RISK_CAP_REDUCTION


# ─────────────────────────────────────────────────────────────────────────────
# Pillar composer
# ─────────────────────────────────────────────────────────────────────────────

def test_pillar_composer_returns_all_four_dimensions():
    pillar = p3.score_customer_fit("ENTERPRISE SOFTWARE", {})
    assert len(pillar.dimensions) == 4
    names = [d.name for d in pillar.dimensions]
    assert "Training Commitment" in names
    assert "Build Capacity" in names
    assert "Delivery Capacity" in names
    assert "Organizational DNA" in names


def test_pillar_weights_sum_to_100():
    total = (
        _dim_weight("Training Commitment")
        + _dim_weight("Build Capacity")
        + _dim_weight("Delivery Capacity")
        + _dim_weight("Organizational DNA")
    )
    assert total == 100


def test_pillar_cf_weight_matches_config():
    pillar = p3.score_customer_fit(None, {})
    expected_weight = 0
    for p in cfg.PILLARS:
        if p.name == "Customer Fit":
            expected_weight = p.weight
            break
    assert pillar.weight == expected_weight


def test_empty_grades_returns_baseline_pillar_score():
    """No grades → each dim scores its baseline → pillar is sum of baselines."""
    pillar = p3.score_customer_fit("ENTERPRISE SOFTWARE", {})
    expected = (
        _baseline("training_commitment", "ENTERPRISE SOFTWARE")
        + _baseline("build_capacity", "ENTERPRISE SOFTWARE")
        + _baseline("delivery_capacity", "ENTERPRISE SOFTWARE")
        + _baseline("organizational_dna", "ENTERPRISE SOFTWARE")
    )
    assert pillar.score == min(expected, 100)


# ─────────────────────────────────────────────────────────────────────────────
# Penalty-visibility rule — Trellix Organizational DNA 25/25 regression
# ─────────────────────────────────────────────────────────────────────────────

def test_cap_never_eats_penalty_trellix_org_dna_regression():
    """The Trellix Organizational DNA 25/25 bug (Frank 2026-04-07):
    named penalties must ALWAYS be visible in the final score, even
    when positive contributions overflow the dimension cap.

    Under the OLD buggy math:
        raw_total = baseline + positives + penalties
        score     = min(raw_total, effective_cap)
        → A -4 penalty on a dimension where positives overflow by
          5+ silently became `effective_cap` — the penalty absorbed
          into the overflow. Trellix Org DNA rendered 25/25 instead
          of the correct 21/25.

    Under the NEW correct math:
        capped_positive = min(baseline + positives, effective_cap)
        score           = capped_positive + penalty_total
        → Penalty is visible regardless of how high positives went.

    The fix lives in pillar_3_scorer._apply_risk_cap_reduction. This
    test is the regression gate against ever silently reintroducing
    the bug.
    """
    # Pick enough strong positive grades to overflow the Org DNA cap
    # even after the amber risk cap reduction from the penalty grade.
    strong_positives = [
        GradedSignal(
            signal_category="many_partnership_types",
            strength="strong", color="green",
            evidence_text="Multi-type partnership ecosystem",
            confidence="confirmed",
        ),
        GradedSignal(
            signal_category="strategic_asset_partnerships",
            strength="strong", color="green",
            evidence_text="Strategic alliance program documented",
            confidence="confirmed",
        ),
        GradedSignal(
            signal_category="platform_buyer_behavior",
            strength="strong", color="green",
            evidence_text="Platform buyer behavior pattern",
            confidence="confirmed",
        ),
        GradedSignal(
            signal_category="formal_channel_program",
            strength="strong", color="green",
            evidence_text="Formal channel program with tiers",
            confidence="confirmed",
        ),
        GradedSignal(
            signal_category="named_alliance_leadership",
            strength="strong", color="green",
            evidence_text="Named VP of Alliances",
            confidence="confirmed",
        ),
    ]
    # The penalty grade — exact category Trellix hit
    penalty_grade = GradedSignal(
        signal_category="long_rfp_process",
        strength="moderate", color="amber",
        evidence_text="9+ month RFP cycles documented",
        confidence="indicated",
    )
    grades = strong_positives + [penalty_grade]

    result = p3.score_organizational_dna("ENTERPRISE SOFTWARE", grades)

    # Derive all expected values from config — zero hardcoded numbers.
    baseline = _baseline("organizational_dna", "ENTERPRISE SOFTWARE")
    strong_pts = _tier_points("Organizational DNA", "strong")
    positive_total = baseline + (len(strong_positives) * strong_pts)
    penalty_hit = _penalty("organizational_dna", "long_rfp_process")

    # The penalty is amber, so amber_risks = 1 → effective_cap drops
    # by cfg.AMBER_RISK_CAP_REDUCTION from the base dimension cap.
    base_cap = _dim_weight("Organizational DNA")
    effective_cap = base_cap - cfg.AMBER_RISK_CAP_REDUCTION

    # Test setup guard: positives MUST overflow the effective cap,
    # otherwise the cap-eats-penalty path isn't exercised.
    assert positive_total > effective_cap, (
        f"Test setup: positive_total {positive_total} must exceed "
        f"effective_cap {effective_cap} to exercise the bug path."
    )

    # Correct math: positives clamp to effective_cap, THEN subtract
    # the penalty on top. Penalty is fully visible in the final score.
    expected_score = effective_cap - penalty_hit

    assert result.positives_capped is True
    assert result.dimension_score.score == expected_score, (
        f"Penalty must be visible. Expected {expected_score}, "
        f"got {result.dimension_score.score}. "
        f"positive_total={result.positive_total}, "
        f"penalty_total={result.penalty_total}, "
        f"effective_cap={result.effective_cap}."
    )

    # Penalty must be recorded in penalties_applied (not silently dropped)
    assert any(
        cat == "long_rfp_process" for cat, _ in result.penalties_applied
    ), f"Penalty must appear in penalties_applied. Got: {result.penalties_applied}"
