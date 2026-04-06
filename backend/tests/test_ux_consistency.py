"""Category 9: UX Consistency and Vocabulary

Guiding Principles: GP4 (Self-Evident Design), GP1 (Right Information, Right Person)

Validates that all templates use correct vocabulary, colors, classification
badges, and theme variables. No legacy terminology, no hardcoded colors,
no inconsistency across pages.

NOTE: These tests validate the NEW templates once built.
Until then, they serve as the specification.

See docs/Test-Plan.md for the full test strategy.
"""

import pytest

import scoring_config as cfg


# ── Theme variables ─────────────────────────────────────────────────────────

def test_templates_use_css_variables_only():
    """All templates must use CSS theme variables — no hardcoded hex values
    outside of _theme.html.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Navigation consistency ──────────────────────────────────────────────────

def test_nav_consistent_across_pages():
    """The same nav header must render on Inspector, Product Selection,
    Full Analysis, Prospector, and Designer.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Org type badge colors ──────────────────────────────────────────────────

def test_org_badges_use_correct_color_groups():
    """Org type badges must use classification colors, not scoring colors.

    Purple — Software companies, Enterprise/multi-product
    Teal — Training & certification orgs, Academic institutions
    Warm blue — GSIs, Distributors, Professional services, LMS companies, Content dev firms

    Never green, amber, or red — those are scoring colors.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Deployment model badges ─────────────────────────────────────────────────

def test_deployment_badges_correct():
    """Deployment model badges must use correct labels and colors.

    Installable (green), Hybrid (gray), Cloud-Native (green), SaaS-Only (amber).
    """
    assert "installable" in cfg.DEPLOYMENT_MODELS
    assert cfg.DEPLOYMENT_MODELS["installable"]["display"] == "Installable"


def test_deployment_data_value_is_installable():
    """Data value must be 'installable', not 'self-hosted' (GP4)."""
    assert "self-hosted" not in cfg.DEPLOYMENT_MODELS


# ── Discovery tier labels ──────────────────────────────────────────────────

def test_discovery_tier_labels():
    """Discovery tier labels must be: Seems Promising, Likely, Uncertain, Unlikely.

    These communicate confidence at discovery depth — not conclusions.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Product selection limit ─────────────────────────────────────────────────

def test_product_selection_limit_configurable():
    """Product selection limit must be configurable, not hardcoded."""
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Page names ──────────────────────────────────────────────────────────────

def test_no_forbidden_page_names():
    """User-facing text must not contain retired page names.

    No 'Seller Action Plan', 'Dossier', or 'Caseboard' visible to users.
    'Product Selection' and 'Full Analysis' are the correct names.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")


# ── Classification vs scoring colors ────────────────────────────────────────

def test_classification_badges_never_use_scoring_colors():
    """Classification badges (org type, subcategory) must never use
    green, amber, or red — those are reserved for scoring assessment.

    Classification colors: purple, teal, warm blue.
    """
    pytest.skip("Awaiting new templates — rebuild in progress")
