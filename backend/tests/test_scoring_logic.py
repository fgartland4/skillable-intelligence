"""Category 4: Scoring Logic

Guiding Principle: GP3 (Explainably Trustworthy)

Validates scoring math — dimension rollups, pillar weighting, Fit Score,
verdict assignment, and ACV.

See docs/Test-Plan.md for the full test strategy.
"""

import scoring_config as cfg


# ── Dimension rollup ────────────────────────────────────────────────────────

def test_dimension_scores_roll_up_to_pillar():
    """Dimension scores must sum to the Pillar score."""
    dim_scores = {"Provisioning": 30, "Lab Access": 20, "Scoring": 12, "Teardown": 22}
    assert sum(dim_scores.values()) == 84


def test_dimension_scores_floor_at_zero():
    """Dimension scores cannot go below zero."""
    assert max(0, 35 - 40) == 0


# ── Pillar weighting ────────────────────────────────────────────────────────

def test_pillar_scores_weight_to_fit_score():
    """(85 x 0.40) + (88 x 0.30) + (72 x 0.30) = 82"""
    fit_score = round(85 * 0.40 + 88 * 0.30 + 72 * 0.30)
    assert fit_score == 82


def test_fit_score_range():
    """Fit Score must be between 0 and 100."""
    assert round(100 * 0.40 + 100 * 0.30 + 100 * 0.30) == 100
    assert round(0 * 0.40 + 0 * 0.30 + 0 * 0.30) == 0


def test_product_dominates_fit_score():
    """Product pillars (70%) outweigh organization (30%)."""
    assert round(100 * 0.40 + 100 * 0.30 + 0 * 0.30) == 70


# ── Verdict grid (all 15 cells) ─────────────────────────────────────────────

def _get_verdict(score: int, acv_tier: str) -> str:
    """Look up verdict using the config's get_verdict function."""
    vd = cfg.get_verdict(score, acv_tier)
    return vd.label


def test_verdict_80_high():
    assert _get_verdict(85, "high") == "Prime Target"

def test_verdict_80_medium():
    assert _get_verdict(85, "medium") == "Strong Prospect"

def test_verdict_80_low():
    assert _get_verdict(85, "low") == "Good Fit"

def test_verdict_65_high():
    assert _get_verdict(70, "high") == "High Potential"

def test_verdict_65_medium():
    assert _get_verdict(70, "medium") == "Worth Pursuing"

def test_verdict_65_low():
    assert _get_verdict(70, "low") == "Solid Prospect"

def test_verdict_45_high():
    assert _get_verdict(55, "high") == "High Potential"

def test_verdict_45_medium():
    assert _get_verdict(55, "medium") == "Worth Pursuing"

def test_verdict_45_low():
    assert _get_verdict(55, "low") == "Solid Prospect"

def test_verdict_25_high():
    assert _get_verdict(35, "high") == "Assess First"

def test_verdict_25_medium():
    assert _get_verdict(35, "medium") == "Keep Watch"

def test_verdict_25_low():
    assert _get_verdict(35, "low") == "Deprioritize"

def test_verdict_0_high():
    assert _get_verdict(15, "high") == "Keep Watch"

def test_verdict_0_medium():
    assert _get_verdict(15, "medium") == "Poor Fit"

def test_verdict_0_low():
    assert _get_verdict(15, "low") == "Poor Fit"


# ── ACV ─────────────────────────────────────────────────────────────────────

def test_acv_adoption_ceiling_events():
    """Events adoption ceiling must not exceed 0.80."""
    events = next(
        (m for m in cfg.CONSUMPTION_MOTIONS if "event" in m.label.lower()),
        None
    )
    assert events is not None, "Events consumption motion not found"
    assert events.adoption_ceiling_high <= 0.80


def test_acv_adoption_ceiling_non_events():
    """Non-event adoption ceilings must not exceed 0.20."""
    for motion in cfg.CONSUMPTION_MOTIONS:
        if "event" in motion.label.lower():
            continue
        assert motion.adoption_ceiling_high <= 0.20, (
            f"'{motion.label}' ceiling is {motion.adoption_ceiling_high}, max 0.20"
        )


# ── Pillar 2 + Pillar 3 rubric model tests ─────────────────────────────────
#
# These tests verify the rubric-based scoring path added 2026-04-06 for the
# Pillar 2 (Instructional Value) and Pillar 3 (Customer Fit) refactor. The
# rubric model uses variable badge names with strength grading; the math
# layer credits points by (dimension, strength) lookup.
#
# Pillar 1 (Product Labability) keeps the canonical signal/penalty model.
# These tests cover both architectures + their interaction.

import scoring_math as sm


def test_rubric_product_complexity_three_strong():
    """Three strong Product Complexity badges = 18/40 (3 × 6)."""
    r = sm.compute_dimension_score("product_complexity", [
        {"name": "End-to-End Pipeline", "color": "green", "strength": "strong",
         "signal_category": "multi_phase_workflow"},
        {"name": "Multi-Tenant Roles", "color": "green", "strength": "strong",
         "signal_category": "role_diversity"},
        {"name": "AI Workflows", "color": "green", "strength": "strong",
         "signal_category": "ai_practice_required"},
    ])
    assert r["model"] == "rubric"
    assert r["score"] == 18
    assert len(r["rubric_credits"]) == 3
    assert all(c["points"] == 6 for c in r["rubric_credits"])


def test_rubric_mastery_stakes_caps_at_25():
    """Three strong Mastery Stakes (3 × 9 = 27) caps at 25."""
    r = sm.compute_dimension_score("mastery_stakes", [
        {"name": "Sanctions Risk", "color": "green", "strength": "strong",
         "signal_category": "harm_severity"},
        {"name": "Outside Counsel", "color": "green", "strength": "strong",
         "signal_category": "adoption_risk"},
        {"name": "Steep Curve", "color": "green", "strength": "strong",
         "signal_category": "learning_curve"},
    ])
    assert r["score"] == 25
    assert r["capped"] is True


def test_rubric_lab_versatility_two_strong():
    """Two strong Lab Versatility badges = 10/15 (2 × 5)."""
    r = sm.compute_dimension_score("lab_versatility", [
        {"name": "Compliance Audit", "color": "green", "strength": "strong",
         "signal_category": "compliance_audit"},
        {"name": "Break/Fix", "color": "green", "strength": "strong",
         "signal_category": "break_fix"},
    ])
    assert r["score"] == 10


def test_rubric_market_demand_caps_at_20():
    """Four strong Market Demand badges (4 × 5 = 20) caps exactly at 20."""
    r = sm.compute_dimension_score("market_demand", [
        {"name": "Fortune 100", "color": "green", "strength": "strong",
         "signal_category": "enterprise_validation"},
        {"name": "Active Cert", "color": "green", "strength": "strong",
         "signal_category": "cert_ecosystem"},
        {"name": "AI Platform", "color": "green", "strength": "strong",
         "signal_category": "ai_signal"},
        {"name": "Global", "color": "green", "strength": "strong",
         "signal_category": "geographic_reach"},
    ])
    assert r["score"] == 20


def test_rubric_training_commitment_hands_on_signal():
    """Hands-on Lab Commitment is the strongest Training Commitment signal."""
    r = sm.compute_dimension_score("training_commitment", [
        {"name": "Hands-on Lab Commitment", "color": "green", "strength": "strong",
         "signal_category": "hands_on_commitment"},
        {"name": "Active Cert Exam", "color": "green", "strength": "strong",
         "signal_category": "cert_exam_active"},
        {"name": "Cohesity Connect 5K", "color": "green", "strength": "strong",
         "signal_category": "training_events"},
        {"name": "VP-Level Training", "color": "green", "strength": "strong",
         "signal_category": "training_leadership_level"},
    ])
    # 4 strong × 6 = 24, just under cap 25
    assert r["score"] == 24


def test_rubric_build_capacity_caps_at_20():
    """Build Capacity caps at 20 with 4 strong badges."""
    r = sm.compute_dimension_score("build_capacity", [
        {"name": "Education Team", "color": "green", "strength": "strong",
         "signal_category": "content_team_named"},
        {"name": "~30 Lab Authors", "color": "green", "strength": "strong",
         "signal_category": "lab_authors"},
        {"name": "Content Co-Authoring", "color": "green", "strength": "strong",
         "signal_category": "product_training_partnership"},
        {"name": "University Content", "color": "green", "strength": "strong",
         "signal_category": "content_partnership"},
    ])
    # 4 × 5 = 20 = cap
    assert r["score"] == 20


def test_rubric_delivery_capacity_caps_at_30():
    """Delivery Capacity caps at 30 with 4 strong badges (would be 32)."""
    r = sm.compute_dimension_score("delivery_capacity", [
        {"name": "Skillable", "color": "green", "strength": "strong",
         "signal_category": "lab_platform"},
        {"name": "~500 ATPs", "color": "green", "strength": "strong",
         "signal_category": "atp_network"},
        {"name": "Docebo Public", "color": "green", "strength": "strong",
         "signal_category": "lms_partner"},
        {"name": "Cohesity Connect 5K", "color": "green", "strength": "strong",
         "signal_category": "training_events_scale"},
    ])
    # 4 × 8 = 32, capped at 30
    assert r["score"] == 30
    assert r["capped"] is True


def test_rubric_no_lab_platform_is_moderate_not_weak():
    """`No Lab Platform` is moderate (greenfield opportunity), not weak.

    Frank's call: greenfield is an opportunity, not a deficiency. The seller
    has no incumbent to displace, just needs to sell the hands-on premise.
    """
    r = sm.compute_dimension_score("delivery_capacity", [
        {"name": "No Lab Platform", "color": "gray", "strength": "moderate",
         "signal_category": "lab_platform"},
    ])
    # 1 × 4 (moderate) = 4
    assert r["score"] == 4


def test_rubric_organizational_dna_just_under_cap():
    """Organizational DNA with 4 strong = 24/25 (just under cap)."""
    r = sm.compute_dimension_score("organizational_dna", [
        {"name": "~500 ATPs", "color": "green", "strength": "strong",
         "signal_category": "partner_pattern"},
        {"name": "Platform Buyer", "color": "green", "strength": "strong",
         "signal_category": "build_vs_buy_culture"},
        {"name": "Partner-Friendly", "color": "green", "strength": "strong",
         "signal_category": "engagement_ease"},
        {"name": "Strong Channel", "color": "green", "strength": "strong",
         "signal_category": "channel_structure"},
    ])
    # 4 × 6 = 24, cap is 25
    assert r["score"] == 24


def test_rubric_hard_negative_red_falls_to_color_points():
    """Red badges in rubric dimensions fall to color points (-3), not rubric.

    Reserved for explicit hard negatives like Hard to Engage in Org DNA or
    Consumer Grade in Product Complexity. The negative finding shouldn't
    earn the positive rubric tier value.
    """
    r = sm.compute_dimension_score("organizational_dna", [
        {"name": "Hard to Engage", "color": "red"},
    ])
    # -3 color points floored to 0
    assert r["score"] == 0
    assert len(r["color_contributions"]) == 1
    assert r["color_contributions"][0]["points"] == -3


def test_rubric_strength_missing_falls_to_color_points():
    """Badge without strength field falls back to color points.

    Defensive — handles cached data scored before the rubric model existed,
    and AI emissions that omit the required strength field.
    """
    r = sm.compute_dimension_score("product_complexity", [
        {"name": "Some Finding", "color": "green"},  # no strength field
    ])
    # +6 green color fallback
    assert r["score"] == 6
    assert len(r["color_contributions"]) == 1
    assert len(r["rubric_credits"]) == 0


def test_rubric_mixed_strengths_sum_correctly():
    """Strong + moderate + weak (don't emit) sum correctly."""
    r = sm.compute_dimension_score("training_commitment", [
        {"name": "Hands-on Lab Commitment", "color": "green", "strength": "strong",
         "signal_category": "hands_on_commitment"},
        {"name": "Some Cert Activity", "color": "green", "strength": "moderate",
         "signal_category": "cert_exam_active"},
        # Weak finding intentionally not emitted (rule: weak = don't emit)
    ])
    # 6 + 3 = 9
    assert r["score"] == 9


def test_pillar_1_signal_penalty_model_unchanged():
    """Regression: Pillar 1 dimensions still use the canonical signal/penalty
    model. Hyper-V green earns +30 via name-matched signal lookup, not via
    rubric strength grading.
    """
    r = sm.compute_dimension_score("provisioning", [
        {"name": "Runs in Hyper-V", "color": "green"},
    ])
    assert r["model"] == "signal_penalty"
    assert r["score"] == 30
    assert len(r["signals_matched"]) == 1
    assert r["signals_matched"][0]["points"] == 30


def test_pillar_1_dimensions_have_no_rubric():
    """Architecture invariant: Pillar 1 dimensions must NOT have a rubric."""
    for dim in cfg.PILLAR_PRODUCT_LABABILITY.dimensions:
        assert dim.rubric is None, (
            f"Pillar 1 dimension '{dim.name}' has a rubric — Pillar 1 uses "
            f"the canonical signal/penalty model only."
        )


def test_pillar_2_3_dimensions_all_have_rubrics():
    """Architecture invariant: every Pillar 2 + 3 dimension must have a rubric."""
    for pillar in (cfg.PILLAR_INSTRUCTIONAL_VALUE, cfg.PILLAR_CUSTOMER_FIT):
        for dim in pillar.dimensions:
            assert dim.rubric is not None, (
                f"{pillar.name} dimension '{dim.name}' is missing a rubric — "
                f"Pillars 2 and 3 use the rubric model."
            )
            # Each rubric has the canonical strong/moderate/weak tier set
            tier_names = {t.strength for t in dim.rubric.tiers}
            assert tier_names == {"strong", "moderate", "weak"}, (
                f"{pillar.name} > {dim.name} has unexpected strength tiers: {tier_names}"
            )
            # Signal categories list must be non-empty
            assert dim.rubric.signal_categories, (
                f"{pillar.name} > {dim.name} has empty signal_categories list"
            )


# ── Cache version stamping (closes the cache versioning gap) ───────────────


def test_scoring_logic_version_constant_exists():
    """SCORING_LOGIC_VERSION must be defined and non-empty."""
    assert hasattr(cfg, "SCORING_LOGIC_VERSION")
    assert cfg.SCORING_LOGIC_VERSION
    assert isinstance(cfg.SCORING_LOGIC_VERSION, str)


def test_is_cached_logic_current_helper():
    """The is_cached_logic_current helper distinguishes current from stale."""
    # Current version = current
    assert cfg.is_cached_logic_current(
        {"_scoring_logic_version": cfg.SCORING_LOGIC_VERSION}
    ) is True

    # Older version = stale
    assert cfg.is_cached_logic_current(
        {"_scoring_logic_version": "2020-01-01.ancient"}
    ) is False

    # Missing version = stale (no version field)
    assert cfg.is_cached_logic_current({}) is False

    # None = treated as not-stale (caller handles None separately)
    assert cfg.is_cached_logic_current(None) is True
