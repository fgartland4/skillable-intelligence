"""Category 3: Data Model

Guiding Principles: GP4 (Self-Evident Design), GP3 (Explainably Trustworthy)

Validates that the data model correctly represents the three-pillar hierarchy,
evidence with confidence coding, and data domain separation.

NOTE: These tests will validate the NEW data model once it's built.
Until then, they serve as the specification — the rebuild must make them pass.

See docs/Test-Plan.md for the full test strategy.
"""

import pytest


# ── Pillar hierarchy ────────────────────────────────────────────────────────

def test_fit_score_model_has_three_pillars():
    """Fit Score model must have exactly three Pillars:
    Product Labability, Instructional Value, Customer Fit.

    This validates the data model structure, not the config.
    """
    pytest.skip("Awaiting new data model — rebuild in progress")


def test_each_pillar_has_four_dimensions():
    """Each Pillar in the data model must have exactly four Dimensions
    with correct names and weights.
    """
    pytest.skip("Awaiting new data model — rebuild in progress")


# ── Evidence and confidence ─────────────────────────────────────────────────

def test_evidence_has_confidence_level():
    """Every Evidence object must have a confidence level field.

    Valid values: 'confirmed', 'indicated', 'inferred'.
    """
    pytest.skip("Awaiting new data model — rebuild in progress")


def test_evidence_has_confidence_explanation():
    """Every Evidence object must have a confidence explanation field.

    A short (1-2 sentence) AI-generated explanation of why that
    confidence level was assigned. Both level and explanation are required.
    """
    pytest.skip("Awaiting new data model — rebuild in progress")


def test_evidence_without_confidence_is_invalid():
    """Evidence missing confidence level or explanation must be rejected."""
    pytest.skip("Awaiting new data model — rebuild in progress")


def test_confidence_level_values_restricted():
    """Confidence level must be one of: confirmed, indicated, inferred.

    No other values accepted.
    """
    pytest.skip("Awaiting new data model — rebuild in progress")


# ── Fit Score calculation ───────────────────────────────────────────────────

def test_fit_score_calculation():
    """Fit Score = (PL x 0.40) + (IV x 0.30) + (CF x 0.30).

    Verified against hand-calculated examples.
    """
    pytest.skip("Awaiting new data model — rebuild in progress")


# ── Field names ─────────────────────────────────────────────────────────────

def test_field_names_match_locked_vocabulary():
    """Data model field names must use locked vocabulary.

    fit_score not composite_score.
    customer_fit not organizational_readiness.
    market_demand not market_readiness.
    installable not self_hosted.
    """
    pytest.skip("Awaiting new data model — rebuild in progress")


# ── Data domain separation ──────────────────────────────────────────────────

def test_product_data_contains_no_company_intelligence():
    """Product data model must not contain fit scores, contacts, ACV, or buying signals."""
    pytest.skip("Awaiting new data model — rebuild in progress")


def test_company_intelligence_contains_no_program_data():
    """Company intelligence must not contain Designer programs, outlines, or instructions."""
    pytest.skip("Awaiting new data model — rebuild in progress")
