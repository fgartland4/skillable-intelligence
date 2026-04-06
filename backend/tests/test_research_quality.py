"""Category 5: Research and Evidence Quality

Guiding Principle: GP3 (Explainably Trustworthy)

Validates research output structure, badge compliance, and lab platform detection.

See docs/Test-Plan.md for the full test strategy.
"""

import pytest
import scoring_config as cfg


def test_canonical_badge_list_exists():
    """A canonical list of all valid badge names must exist."""
    all_badges = []
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            for badge in dim.badges:
                all_badges.append(badge.name)
    assert len(all_badges) > 0


def test_badge_output_matches_canonical_list():
    """Every badge in scoring output must exist in the canonical list."""
    pytest.skip("Awaiting scoring pipeline rebuild")


def test_every_badge_has_evidence():
    """Every badge must have at least one evidence item (GP3)."""
    pytest.skip("Awaiting scoring pipeline rebuild")


def test_evidence_has_confidence_and_explanation():
    """Every evidence item must have confidence level AND explanation."""
    pytest.skip("Awaiting scoring pipeline rebuild")


def test_badge_colors_match_config():
    """Badge colors in output must match config criteria."""
    pytest.skip("Awaiting scoring pipeline rebuild")


def test_evidence_format_standard():
    """Evidence bullets must follow the format standard."""
    pytest.skip("Awaiting scoring pipeline rebuild")


def test_soft_warning_above_five_badges():
    """Dimensions with >5 badges should log a warning."""
    pytest.skip("Awaiting scoring pipeline rebuild")


def test_lab_platform_list_has_domains():
    """Lab platform list should exist for detection."""
    assert len(cfg.CANONICAL_LAB_PLATFORMS) > 0


def test_skillable_in_platform_list():
    """Skillable must be in the lab platform list."""
    assert "Skillable" in cfg.CANONICAL_LAB_PLATFORMS


def test_domain_detection_finds_known_url():
    """Domain detection should find known platform URLs in page content."""
    pytest.skip("Awaiting domain detection module")


def test_discovery_produces_valid_products():
    """Discovery must produce products with name, category, deployment model."""
    pytest.skip("Awaiting scoring pipeline rebuild")
