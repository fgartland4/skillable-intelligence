"""Category 1: Scoring Configuration Validation

Guiding Principles: GP4 (Self-Evident Design), Define-Once Principle

Validates that scoring_config.py — the single source of truth for the entire
scoring framework — is internally consistent. These are structural tests.
The config either passes or it doesn't.

See docs/Test-Plan.md for the full test strategy.
"""

import scoring_config as cfg


# ── Pillar weights ──────────────────────────────────────────────────────────

def test_pillar_weights_sum_to_100():
    """All Pillar weights must sum to 100 (Define-Once Principle).

    Three Pillars: Product Labability (40) + Instructional Value (30) + Customer Fit (30).
    """
    total = sum(p.weight for p in cfg.PILLARS)
    assert total == 100, f"Pillar weights sum to {total}, expected 100"


def test_exactly_three_pillars():
    """The framework has exactly three Pillars — no more, no less."""
    assert len(cfg.PILLARS) == 3, f"Expected 3 Pillars, found {len(cfg.PILLARS)}"


def test_pillar_names_match_locked_vocabulary():
    """Pillar names must match the locked vocabulary exactly."""
    expected = {"Product Labability", "Instructional Value", "Customer Fit"}
    actual = {p.name for p in cfg.PILLARS}
    assert actual == expected, f"Pillar names {actual} don't match expected {expected}"


# ── Dimension weights ───────────────────────────────────────────────────────

def test_dimension_weights_sum_to_100_per_pillar():
    """Dimension weights within each Pillar must sum to 100.

    Each Pillar scores out of 100 internally (sum of dimension scores),
    then gets weighted to its share of the Fit Score.
    """
    for pillar in cfg.PILLARS:
        total = sum(d.weight for d in pillar.dimensions)
        assert total == 100, (
            f"Dimension weights in '{pillar.name}' sum to {total}, expected 100"
        )


def test_each_pillar_has_four_dimensions():
    """Each Pillar has exactly four Dimensions."""
    for pillar in cfg.PILLARS:
        count = len(pillar.dimensions)
        assert count == 4, (
            f"Pillar '{pillar.name}' has {count} dimensions, expected 4"
        )


def test_dimension_names_product_labability():
    """Product Labability dimensions must be: Provisioning, Lab Access, Scoring, Teardown."""
    pl = next(p for p in cfg.PILLARS if p.name == "Product Labability")
    expected = {"Provisioning", "Lab Access", "Scoring", "Teardown"}
    actual = {d.name for d in pl.dimensions}
    assert actual == expected, f"Product Labability dimensions {actual} don't match {expected}"


def test_dimension_names_instructional_value():
    """Instructional Value dimensions must be: Product Complexity, Mastery Stakes, Lab Versatility, Market Demand."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    expected = {"Product Complexity", "Mastery Stakes", "Lab Versatility", "Market Demand"}
    actual = {d.name for d in iv.dimensions}
    assert actual == expected, f"Instructional Value dimensions {actual} don't match {expected}"


def test_dimension_names_customer_fit():
    """Customer Fit dimensions must be: Training Commitment, Organizational DNA, Delivery Capacity, Build Capacity."""
    cf = next(p for p in cfg.PILLARS if p.name == "Customer Fit")
    expected = {"Training Commitment", "Organizational DNA", "Delivery Capacity", "Build Capacity"}
    actual = {d.name for d in cf.dimensions}
    assert actual == expected, f"Customer Fit dimensions {actual} don't match {expected}"


# ── Badges ──────────────────────────────────────────────────────────────────

def test_every_badge_has_at_least_one_color():
    """Every badge must have at least one color defined (green, gray, amber, or red).

    GP3 — a badge without a color has no meaning.
    """
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            for badge in getattr(dim, "badges", []):
                colors = [c for c in ["green", "gray", "amber", "red"]
                          if getattr(badge, c, None)]
                assert len(colors) > 0, (
                    f"Badge '{badge.name}' in {pillar.name}/{dim.name} has no color defined"
                )


def test_badge_colors_are_valid():
    """Badge colors must only be green, gray, amber, or red — never yellow, pass, partial, or fail."""
    valid_colors = {"green", "gray", "amber", "red"}
    forbidden = {"yellow", "pass", "partial", "fail"}
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            for badge in getattr(dim, "badges", []):
                for attr in dir(badge):
                    if attr in forbidden:
                        assert not getattr(badge, attr, None), (
                            f"Badge '{badge.name}' uses forbidden color '{attr}'"
                        )


# ── Verdict grid ────────────────────────────────────────────────────────────

def test_verdict_grid_covers_all_15_cells():
    """The verdict grid must cover all 5 score bands x 3 ACV tiers = 15 cells.

    No gaps allowed — every combination must produce a verdict.
    """
    score_bands = [80, 65, 45, 25, 0]
    acv_tiers = ["high", "medium", "low"]

    for score in score_bands:
        for tier in acv_tiers:
            verdict = None
            for entry in cfg.VERDICT_GRID:
                if score >= entry.get("min_score", 0) and tier == entry.get("acv_tier"):
                    verdict = entry.get("verdict")
                    break
            assert verdict is not None, (
                f"No verdict found for score={score}, ACV tier={tier}"
            )


def test_verdict_labels_are_valid():
    """All verdict labels must be from the canonical set of 10."""
    valid = {
        "Prime Target", "Strong Prospect", "Good Fit",
        "High Potential", "Worth Pursuing", "Solid Prospect",
        "Assess First", "Keep Watch", "Deprioritize", "Poor Fit",
    }
    for entry in cfg.VERDICT_GRID:
        verdict = entry.get("verdict")
        assert verdict in valid, f"Verdict '{verdict}' is not in the canonical set"


# ── Score thresholds ────────────────────────────────────────────────────────

def test_score_thresholds_descending():
    """Score thresholds must be in descending order: 80 > 65 > 45 > 25."""
    thresholds = cfg.SCORE_THRESHOLDS
    for i in range(len(thresholds) - 1):
        assert thresholds[i] > thresholds[i + 1], (
            f"Score thresholds not descending: {thresholds[i]} <= {thresholds[i + 1]}"
        )


# ── Canonical lists ─────────────────────────────────────────────────────────

def test_lab_platform_list_not_empty():
    """The canonical lab platform provider list must not be empty."""
    assert len(cfg.LAB_PLATFORMS) > 0, "Lab platform list is empty"


def test_lab_platform_list_includes_skillable():
    """Skillable must be in the canonical lab platform list."""
    names = [p.get("name", "").lower() for p in cfg.LAB_PLATFORMS]
    assert any("skillable" in n for n in names), "Skillable not found in lab platform list"


def test_organization_types_not_empty():
    """The organization types list must not be empty."""
    assert len(cfg.ORGANIZATION_TYPES) > 0, "Organization types list is empty"


def test_category_priors_not_empty():
    """Category priors (demand ratings by product category) must not be empty."""
    assert len(cfg.CATEGORY_PRIORS) > 0, "Category priors list is empty"


def test_lab_type_menu_has_12_types():
    """The Lab Versatility menu must have exactly 12 lab types."""
    assert len(cfg.LAB_TYPE_MENU) == 12, (
        f"Lab type menu has {len(cfg.LAB_TYPE_MENU)} types, expected 12"
    )


# ── Locked vocabulary ───────────────────────────────────────────────────────

def test_locked_vocabulary_no_conflicts():
    """No term should appear in both 'use this' and 'not this' columns."""
    use_terms = {entry["use"] for entry in cfg.LOCKED_VOCABULARY}
    not_terms = set()
    for entry in cfg.LOCKED_VOCABULARY:
        for term in entry.get("not_this", []):
            not_terms.add(term)
    overlap = use_terms & not_terms
    assert len(overlap) == 0, f"Terms appear in both columns: {overlap}"


# ── Deployment models ───────────────────────────────────────────────────────

def test_deployment_model_installable_not_self_hosted():
    """Deployment model data value must be 'installable', not 'self-hosted' (GP4)."""
    assert "installable" in cfg.DEPLOYMENT_MODELS, (
        "'installable' not found in deployment models"
    )
    assert "self-hosted" not in cfg.DEPLOYMENT_MODELS, (
        "'self-hosted' still in deployment models — should be 'installable'"
    )


# ── Confidence levels ───────────────────────────────────────────────────────

def test_confidence_levels_defined():
    """Three confidence levels must be defined: confirmed, indicated, inferred."""
    expected = {"confirmed", "indicated", "inferred"}
    actual = {c.level for c in cfg.CONFIDENCE_LEVELS}
    assert actual == expected, f"Confidence levels {actual} don't match {expected}"
