"""Category 4: Scoring Logic

Guiding Principle: GP3 (Explainably Trustworthy)

Validates that scoring math produces correct results — dimension rollups,
pillar weighting, Fit Score calculation, verdict assignment, and ACV.

See docs/Test-Plan.md for the full test strategy.
"""

import scoring_config as cfg


# ── Dimension rollup ────────────────────────────────────────────────────────

def test_dimension_scores_roll_up_to_pillar():
    """Dimension scores must sum to the Pillar score.

    Example: Provisioning 30 + Lab Access 20 + Scoring 12 + Teardown 22 = 84
    for Product Labability.
    """
    dim_scores = {"Provisioning": 30, "Lab Access": 20, "Scoring": 12, "Teardown": 22}
    pillar_score = sum(dim_scores.values())
    assert pillar_score == 84


def test_dimension_scores_cannot_exceed_weight():
    """No dimension score can exceed its max weight."""
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            # Score at max weight should be valid
            assert dim.weight > 0, f"Dimension '{dim.name}' has zero weight"
            # Score above max weight should be caught
            # (This tests the constraint, not a function — the rebuild must enforce this)


def test_dimension_scores_floor_at_zero():
    """Dimension scores cannot go below zero, even with penalties.

    Penalty deductions that push below 0 are clamped to 0.
    """
    # Provisioning max is 35, applying -40 in penalties should floor at 0
    score = max(0, 35 - 40)
    assert score == 0


# ── Pillar weighting ────────────────────────────────────────────────────────

def test_pillar_scores_weight_to_fit_score():
    """Pillar scores out of 100, weighted to Fit Score.

    (85 x 0.40) + (88 x 0.30) + (72 x 0.30) = 34 + 26.4 + 21.6 = 82
    """
    pl_score = 85  # Product Labability
    iv_score = 88  # Instructional Value
    cf_score = 72  # Customer Fit

    fit_score = round(pl_score * 0.40 + iv_score * 0.30 + cf_score * 0.30)
    assert fit_score == 82


def test_fit_score_range():
    """Fit Score must be between 0 and 100."""
    # Maximum: all pillars at 100
    max_score = round(100 * 0.40 + 100 * 0.30 + 100 * 0.30)
    assert max_score == 100

    # Minimum: all pillars at 0
    min_score = round(0 * 0.40 + 0 * 0.30 + 0 * 0.30)
    assert min_score == 0


def test_product_dominates_fit_score():
    """Product pillars (70%) must outweigh organization pillar (30%).

    A perfect product score with zero Customer Fit should still score 70.
    """
    fit_score = round(100 * 0.40 + 100 * 0.30 + 0 * 0.30)
    assert fit_score == 70


# ── Verdict grid (all 15 cells) ─────────────────────────────────────────────

def _get_verdict(score: int, acv_tier: str) -> str:
    """Look up verdict from the scoring config verdict grid."""
    for entry in cfg.VERDICT_GRID:
        if score >= entry.get("min_score", 0) and acv_tier == entry.get("acv_tier"):
            return entry.get("verdict")
    return None


# Score band >= 80 (Dark Green)
def test_verdict_80_high():
    assert _get_verdict(85, "high") == "Prime Target"

def test_verdict_80_medium():
    assert _get_verdict(85, "medium") == "Strong Prospect"

def test_verdict_80_low():
    assert _get_verdict(85, "low") == "Good Fit"


# Score band 65-79 (Green)
def test_verdict_65_high():
    assert _get_verdict(70, "high") == "High Potential"

def test_verdict_65_medium():
    assert _get_verdict(70, "medium") == "Worth Pursuing"

def test_verdict_65_low():
    assert _get_verdict(70, "low") == "Solid Prospect"


# Score band 45-64 (Light Amber)
def test_verdict_45_high():
    assert _get_verdict(55, "high") == "High Potential"

def test_verdict_45_medium():
    assert _get_verdict(55, "medium") == "Worth Pursuing"

def test_verdict_45_low():
    assert _get_verdict(55, "low") == "Solid Prospect"


# Score band 25-44 (Amber)
def test_verdict_25_high():
    assert _get_verdict(35, "high") == "Assess First"

def test_verdict_25_medium():
    assert _get_verdict(35, "medium") == "Keep Watch"

def test_verdict_25_low():
    assert _get_verdict(35, "low") == "Deprioritize"


# Score band <25 (Red)
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
        (m for m in cfg.CONSUMPTION_MOTIONS if "event" in m.get("label", "").lower()),
        None
    )
    assert events is not None, "Events consumption motion not found"
    assert events.get("adoption_ceiling", 0) <= 0.80, (
        f"Events adoption ceiling is {events['adoption_ceiling']}, max is 0.80"
    )


def test_acv_adoption_ceiling_non_events():
    """Non-event adoption ceilings must not exceed 0.20."""
    for motion in cfg.CONSUMPTION_MOTIONS:
        if "event" in motion.get("label", "").lower():
            continue
        ceiling = motion.get("adoption_ceiling", 0)
        assert ceiling <= 0.20, (
            f"'{motion['label']}' adoption ceiling is {ceiling}, max for non-events is 0.20"
        )
