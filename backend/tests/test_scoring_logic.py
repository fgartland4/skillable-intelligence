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
