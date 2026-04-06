"""Category 1: Scoring Configuration Validation

Guiding Principles: GP4 (Self-Evident Design), Define-Once Principle

Validates that scoring_config.py — the single source of truth for the entire
scoring framework — is internally consistent.

See docs/Test-Plan.md for the full test strategy.
"""

import scoring_config as cfg


# ── Pillar weights ──────────────────────────────────────────────────────────

def test_pillar_weights_sum_to_100():
    """All Pillar weights must sum to 100."""
    total = sum(p.weight for p in cfg.PILLARS)
    assert total == 100, f"Pillar weights sum to {total}, expected 100"


def test_exactly_three_pillars():
    """The framework has exactly three Pillars."""
    assert len(cfg.PILLARS) == 3, f"Expected 3 Pillars, found {len(cfg.PILLARS)}"


def test_pillar_names_match_locked_vocabulary():
    """Pillar names must match the locked vocabulary exactly."""
    expected = {"Product Labability", "Instructional Value", "Customer Fit"}
    actual = {p.name for p in cfg.PILLARS}
    assert actual == expected, f"Pillar names {actual} don't match expected {expected}"


# ── Dimension weights ───────────────────────────────────────────────────────

def test_dimension_weights_sum_to_100_per_pillar():
    """Dimension weights within each Pillar must sum to 100."""
    for pillar in cfg.PILLARS:
        total = sum(d.weight for d in pillar.dimensions)
        assert total == 100, (
            f"Dimension weights in '{pillar.name}' sum to {total}, expected 100"
        )


def test_each_pillar_has_four_dimensions():
    """Each Pillar has exactly four Dimensions."""
    for pillar in cfg.PILLARS:
        count = len(pillar.dimensions)
        assert count == 4, f"Pillar '{pillar.name}' has {count} dimensions, expected 4"


def test_dimension_names_product_labability():
    """Product Labability dimensions: Provisioning, Lab Access, Scoring, Teardown."""
    pl = next(p for p in cfg.PILLARS if p.name == "Product Labability")
    expected = {"Provisioning", "Lab Access", "Scoring", "Teardown"}
    actual = {d.name for d in pl.dimensions}
    assert actual == expected


def test_dimension_names_instructional_value():
    """Instructional Value dimensions: Product Complexity, Mastery Stakes, Lab Versatility, Market Demand."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    expected = {"Product Complexity", "Mastery Stakes", "Lab Versatility", "Market Demand"}
    actual = {d.name for d in iv.dimensions}
    assert actual == expected


def test_dimension_names_customer_fit():
    """Customer Fit dimensions: Training Commitment, Organizational DNA, Delivery Capacity, Build Capacity."""
    cf = next(p for p in cfg.PILLARS if p.name == "Customer Fit")
    expected = {"Training Commitment", "Organizational DNA", "Delivery Capacity", "Build Capacity"}
    actual = {d.name for d in cf.dimensions}
    assert actual == expected


# ── Badges ──────────────────────────────────────────────────────────────────

def test_every_badge_has_at_least_one_color():
    """Every badge must have at least one color defined (GP3)."""
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            for badge in dim.badges:
                assert len(badge.colors) > 0, (
                    f"Badge '{badge.name}' in {pillar.name}/{dim.name} has no color defined"
                )


# ── Verdict grid ────────────────────────────────────────────────────────────

def test_verdict_grid_covers_all_15_cells():
    """The verdict grid must cover all 5 score bands x 3 ACV tiers = 15 cells."""
    score_thresholds = sorted(cfg.SCORE_THRESHOLDS.values(), reverse=True)
    for threshold in score_thresholds:
        for tier in cfg.ACV_TIERS:
            key = (threshold, tier)
            assert key in cfg.VERDICT_GRID, f"No verdict for score={threshold}, ACV={tier}"


def test_verdict_labels_are_valid():
    """All verdict labels must be from the canonical set of 10."""
    valid = {
        "Prime Target", "Strong Prospect", "Good Fit",
        "High Potential", "Worth Pursuing", "Solid Prospect",
        "Assess First", "Keep Watch", "Deprioritize", "Poor Fit",
    }
    for key, vd in cfg.VERDICT_GRID.items():
        assert vd.label in valid, f"Verdict '{vd.label}' at {key} is not in the canonical set"


# ── Score thresholds ────────────────────────────────────────────────────────

def test_score_thresholds_descending():
    """Score thresholds must be in descending order: 80 > 65 > 45 > 25 > 0."""
    values = list(cfg.SCORE_THRESHOLDS.values())
    for i in range(len(values) - 1):
        assert values[i] > values[i + 1], (
            f"Score thresholds not descending: {values[i]} <= {values[i + 1]}"
        )


# ── Canonical lists ─────────────────────────────────────────────────────────

def test_lab_platform_list_not_empty():
    """The canonical lab platform list must not be empty."""
    assert len(cfg.CANONICAL_LAB_PLATFORMS) > 0


def test_lab_platform_list_includes_skillable():
    """Skillable must be in the canonical lab platform list."""
    assert any("Skillable" in p or "skillable" in p.lower()
               for p in cfg.CANONICAL_LAB_PLATFORMS)


def test_organization_types_not_empty():
    """The organization types list must not be empty."""
    assert len(cfg.ORGANIZATION_TYPES) > 0


def test_category_priors_not_empty():
    """Category priors must not be empty."""
    assert len(cfg.CATEGORY_PRIORS) > 0


def test_lab_type_menu_has_12_types():
    """The Lab Versatility menu must have exactly 12 lab types."""
    assert len(cfg.LAB_TYPE_MENU) == 12, (
        f"Lab type menu has {len(cfg.LAB_TYPE_MENU)} types, expected 12"
    )


# ── Locked vocabulary ───────────────────────────────────────────────────────

def test_locked_vocabulary_no_conflicts():
    """No term should appear in both 'use_this' and 'not_this' columns."""
    use_terms = {lt.use_this for lt in cfg.LOCKED_VOCABULARY}
    not_terms = set()
    for lt in cfg.LOCKED_VOCABULARY:
        for term in lt.not_this:
            not_terms.add(term)
    overlap = use_terms & not_terms
    assert len(overlap) == 0, f"Terms appear in both columns: {overlap}"


# ── Deployment models ───────────────────────────────────────────────────────

def test_deployment_model_installable_not_self_hosted():
    """Deployment model data value must be 'installable', not 'self-hosted' (GP4)."""
    assert "installable" in cfg.DEPLOYMENT_MODELS
    assert "self-hosted" not in cfg.DEPLOYMENT_MODELS


# ── Confidence levels ───────────────────────────────────────────────────────

def test_confidence_levels_defined():
    """Three confidence levels must be defined: confirmed, indicated, inferred."""
    expected = {"confirmed", "indicated", "inferred"}
    actual = {c.level for c in cfg.CONFIDENCE_LEVELS}
    assert actual == expected
