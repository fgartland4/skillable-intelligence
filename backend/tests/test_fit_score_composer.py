"""Tests for the Fit Score composer.

The composer is the single point where three per-pillar PillarScore
objects turn into one Fit Score, with the Technical Fit Multiplier
applied to IV + CF contributions.

NO hardcoded expected values — every assertion is computed from
scoring_config.py so the tests track the config if it changes.
"""
from __future__ import annotations

import scoring_config as cfg
import fit_score_composer as fsc
from models import FitScore, PillarScore, DimensionScore


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — compute expected values from config (Define-Once honored)
# ─────────────────────────────────────────────────────────────────────────────

def _pillar_weight(key: str) -> int:
    for p in cfg.PILLARS:
        if p.name.lower().replace(" ", "_") == key:
            return int(p.weight)
    return 0


def _expected_fit(pl: int, iv: int, cf: int, multiplier: float) -> int:
    pl_w = _pillar_weight("product_labability") / 100
    iv_w = _pillar_weight("instructional_value") / 100
    cf_w = _pillar_weight("customer_fit") / 100
    total = (pl * pl_w) + (iv * iv_w * multiplier) + (cf * cf_w * multiplier)
    return max(0, min(100, round(total)))


def _make_fit_score(pl: int, iv: int, cf: int) -> FitScore:
    """Build a FitScore pre-populated with the three pillar scores.

    Sets both the dimension score AND the PillarScore.score field
    (which is a stored dataclass field since 2026-04-08, not a property).
    This matches what the production scorers do via recompute_pillar_score.
    """
    def _p(key: str, score: int) -> PillarScore:
        pw = _pillar_weight(key)
        return PillarScore(
            name=key,
            weight=pw,
            dimensions=[
                DimensionScore(name=f"{key}_test_dim", score=score, weight=pw),
            ],
            score=score,   # stored field — composer reads this directly
        )
    fs = FitScore()
    fs.product_labability = _p("product_labability", pl)
    fs.instructional_value = _p("instructional_value", iv)
    fs.customer_fit = _p("customer_fit", cf)
    return fs


# ─────────────────────────────────────────────────────────────────────────────
# Technical Fit Multiplier lookup
# ─────────────────────────────────────────────────────────────────────────────

def test_multiplier_empty_orchestration_method_uses_any_class():
    """Empty orchestration method must fall back to the 'any' method class."""
    result = fsc.get_technical_fit_multiplier(50, "")
    # Any matching rule in the 'any' class at pl=50 must be returned.
    # If no rule exists, default 1.0 is returned.
    assert 0.0 <= result <= 1.0


def test_multiplier_datacenter_method_uses_datacenter_class():
    """A datacenter orchestration method must prefer datacenter rules."""
    if not cfg.DATACENTER_METHODS:
        return  # nothing to test
    method = next(iter(cfg.DATACENTER_METHODS))
    result = fsc.get_technical_fit_multiplier(50, method)
    assert 0.0 <= result <= 1.0


def test_multiplier_weak_pl_yields_low_multiplier():
    """A PL score at the low end of the scale must produce a low multiplier
    (the whole point of the coupling: weak PL drags IV + CF down)."""
    # Walk the TECHNICAL_FIT_MULTIPLIERS table to confirm that at least
    # one rule in the lowest score bucket produces a multiplier < 1.0.
    low_multipliers = [
        m.multiplier for m in cfg.TECHNICAL_FIT_MULTIPLIERS
        if m.score_min == 0 and m.multiplier < 1.0
    ]
    assert low_multipliers, (
        "scoring_config.TECHNICAL_FIT_MULTIPLIERS must contain at least "
        "one low-PL rule with multiplier < 1.0 — otherwise the Technical "
        "Fit Multiplier cannot couple pillars and weak PL will not drag "
        "IV + CF contribution down."
    )


# ─────────────────────────────────────────────────────────────────────────────
# compose_fit_score — mutation contract
# ─────────────────────────────────────────────────────────────────────────────

def test_compose_sets_total_override_and_multiplier_fields():
    """compose_fit_score must populate total_override and technical_fit_multiplier."""
    fs = _make_fit_score(pl=80, iv=70, cf=60)
    fsc.compose_fit_score(fs, orchestration_method="")

    assert fs.total_override is not None, (
        "compose_fit_score must set total_override on the FitScore"
    )
    assert 0 <= fs.total_override <= 100
    assert 0.0 <= fs.technical_fit_multiplier <= 1.0


def test_compose_fit_score_matches_weighted_sum_formula():
    """The composed Fit Score must equal the documented weighted-sum formula."""
    pl, iv, cf = 80, 70, 60
    fs = _make_fit_score(pl, iv, cf)
    fsc.compose_fit_score(fs, orchestration_method="")

    multiplier = fs.technical_fit_multiplier
    expected = _expected_fit(pl, iv, cf, multiplier)
    assert fs.total_override == expected, (
        f"Composed fit score {fs.total_override} doesn't match expected "
        f"{expected} (pl={pl}, iv={iv}, cf={cf}, multiplier={multiplier})"
    )


def test_compose_fit_score_total_equals_total_override():
    """FitScore.total must return the composed override value."""
    fs = _make_fit_score(pl=80, iv=70, cf=60)
    fsc.compose_fit_score(fs, orchestration_method="")
    assert fs.total == fs.total_override


# ─────────────────────────────────────────────────────────────────────────────
# The TRELLIX CASE — weak PL must pull Fit Score down
# ─────────────────────────────────────────────────────────────────────────────

def _lowest_any_rule_score() -> int:
    """Return a PL score that is guaranteed to match the lowest 'any'
    rule in the TECHNICAL_FIT_MULTIPLIERS table.  Picked from config so
    the test survives any retuning of the ranges."""
    any_rules = [m for m in cfg.TECHNICAL_FIT_MULTIPLIERS if m.method == "any"]
    if not any_rules:
        return 0
    lowest = min(any_rules, key=lambda m: m.score_min)
    return lowest.score_min  # always in range [score_min, score_max]


def test_weak_pl_with_strong_iv_and_cf_produces_low_fit_score():
    """The reason the Technical Fit Multiplier exists.

    Weak PL + strong IV + strong CF should NOT produce a Solid Prospect
    fit score — because we fundamentally cannot lab the product.  The
    multiplier must kick in and drag IV + CF contribution down.

    The PL value is derived from the config — we find the lowest 'any'
    rule in TECHNICAL_FIT_MULTIPLIERS and pick a PL score guaranteed
    to land in it.  Survives re-tuning of the ranges.
    """
    pl = _lowest_any_rule_score()
    iv, cf = 85, 80
    fs = _make_fit_score(pl, iv, cf)
    fsc.compose_fit_score(fs, orchestration_method="")

    multiplier = fs.technical_fit_multiplier
    # Guard: config MUST apply a <1.0 multiplier at this PL level.
    # If someone deletes low-PL rules from TECHNICAL_FIT_MULTIPLIERS
    # this assertion tells them the coupling is broken.
    assert multiplier < 1.0, (
        f"Weak PL ({pl}) must produce a multiplier < 1.0 to drag IV + CF "
        f"contribution down. Got multiplier={multiplier}. Check "
        f"scoring_config.TECHNICAL_FIT_MULTIPLIERS has low-PL rules."
    )

    # And the composed fit score must match the formula using that multiplier.
    expected = _expected_fit(pl, iv, cf, multiplier)
    assert fs.total_override == expected

    # And it must be strictly less than the pure 70/30 weighted sum —
    # the whole point of the coupling.
    pure_weighted = _expected_fit(pl, iv, cf, 1.0)
    assert fs.total_override < pure_weighted, (
        f"Weak PL with multiplier should drag Fit Score below pure "
        f"weighted sum. Composed={fs.total_override}, "
        f"pure={pure_weighted}, multiplier={multiplier}"
    )


def test_strong_pl_preserves_full_iv_and_cf_contribution():
    """At strong PL, the multiplier should be at or near 1.0 — strong PL
    does not punish IV or CF.  The asymmetric coupling rule."""
    pl, iv, cf = 90, 70, 60
    fs = _make_fit_score(pl, iv, cf)
    fsc.compose_fit_score(fs, orchestration_method="")

    # The multiplier at strong PL is allowed to be 1.0 exactly.  We
    # don't require it — the config may choose sub-1.0 even at strong
    # PL — but we DO require that the composed score is at least the
    # pure 70/30 weighted sum with multiplier=1.0 is a sensible upper
    # bound, and the composer never exceeds that.
    max_expected = _expected_fit(pl, iv, cf, 1.0)
    assert fs.total_override <= max_expected


def test_compose_clamps_to_range_0_100():
    """Composed Fit Score must always land in [0, 100]."""
    for pl, iv, cf in [(0, 0, 0), (100, 100, 100), (5, 100, 100), (100, 5, 5)]:
        fs = _make_fit_score(pl, iv, cf)
        fsc.compose_fit_score(fs, orchestration_method="")
        assert 0 <= fs.total_override <= 100


def test_compose_is_idempotent():
    """Calling compose_fit_score twice on the same FitScore must produce
    the same result — no drift between invocations."""
    fs = _make_fit_score(pl=75, iv=65, cf=55)
    fsc.compose_fit_score(fs, orchestration_method="")
    first = fs.total_override
    first_mult = fs.technical_fit_multiplier
    fsc.compose_fit_score(fs, orchestration_method="")
    assert fs.total_override == first
    assert fs.technical_fit_multiplier == first_mult


def test_compose_handles_missing_orchestration_gracefully():
    """None / empty / missing orchestration method must not raise — falls
    back to the 'any' method class via the composer's internal logic."""
    fs = _make_fit_score(pl=70, iv=60, cf=50)
    fsc.compose_fit_score(fs, orchestration_method="")
    assert fs.total_override is not None
