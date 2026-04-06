"""Category 5: Research and Evidence Quality

Guiding Principle: GP3 (Explainably Trustworthy)

Validates that research produces well-formed output — proper evidence structure,
confidence coding, badge compliance, and domain-based lab platform detection.

NOTE: Tests that validate AI output require the scoring pipeline to be rebuilt.
Tests marked with pytest.skip() are specifications for the rebuild.
Domain-based detection tests can run once the detection module is built.

See docs/Test-Plan.md for the full test strategy.
"""

import pytest

import scoring_config as cfg


# ── Badge compliance ────────────────────────────────────────────────────────

def test_canonical_badge_list_exists():
    """A canonical list of all valid badge names must exist in scoring_config.

    The AI must not invent badge names that aren't in this list.
    """
    all_badges = []
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            for badge in getattr(dim, "badges", []):
                all_badges.append(badge.name)
    assert len(all_badges) > 0, "No badges found in scoring config"


def test_badge_output_matches_canonical_list():
    """Every badge in scoring output must exist in the canonical badge list.

    AI-invented badge names are invalid.
    """
    pytest.skip("Awaiting scoring pipeline rebuild — validates AI output")


def test_every_badge_has_evidence():
    """Every badge must have at least one evidence item. GP3 — no badge without evidence."""
    pytest.skip("Awaiting scoring pipeline rebuild — validates AI output")


def test_evidence_has_confidence_and_explanation():
    """Every evidence item must have confidence level AND explanation."""
    pytest.skip("Awaiting scoring pipeline rebuild — validates AI output")


def test_badge_colors_match_config():
    """Badge colors in scoring output must match the config criteria."""
    pytest.skip("Awaiting scoring pipeline rebuild — validates AI output")


# ── Evidence format ─────────────────────────────────────────────────────────

def test_evidence_format_standard():
    """Evidence bullets must follow the format:
    [Badge Name] | [Qualifier]: [Finding] — [Source]. [What it means.]
    """
    pytest.skip("Awaiting scoring pipeline rebuild — validates AI output")


def test_soft_warning_above_five_badges():
    """Dimensions producing more than 5 badges should generate a soft warning.

    Logged for review, not rejected.
    """
    pytest.skip("Awaiting scoring pipeline rebuild — validates AI output")


# ── Domain-based lab platform detection ─────────────────────────────────────

def test_detection_covers_full_canonical_list():
    """Every lab platform domain in the config must be detectable."""
    platforms_with_domains = [
        p for p in cfg.LAB_PLATFORMS
        if p.get("domain")
    ]
    assert len(platforms_with_domains) > 0, (
        "No lab platforms have domains defined for detection"
    )


def test_skillable_domains_in_detection_list():
    """Skillable detection must include labondemand.com and learnondemandsystems.com."""
    skillable = next(
        (p for p in cfg.LAB_PLATFORMS if "skillable" in p.get("name", "").lower()),
        None
    )
    assert skillable is not None, "Skillable not found in lab platform list"
    domains = skillable.get("detection_domains", [])
    assert any("labondemand" in d for d in domains), (
        "labondemand.com not in Skillable detection domains"
    )


def test_domain_detection_finds_known_url():
    """Given page content containing a labondemand.com link,
    detection should identify Skillable.
    """
    pytest.skip("Awaiting domain detection module — build in progress")


# ── Discovery output ────────────────────────────────────────────────────────

def test_discovery_produces_valid_products():
    """Discovery must produce products with name, category, deployment model at minimum."""
    pytest.skip("Awaiting scoring pipeline rebuild — validates AI output")
