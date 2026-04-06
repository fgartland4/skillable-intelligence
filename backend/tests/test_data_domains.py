"""Category 6: Data Domain Separation

Guiding Principle: GP1 (Right Information, Right Person)

Validates the architectural wall between the three data domains.
"The separation must be architectural, not just a permissions layer."
— Platform Foundation

NOTE: These tests validate the NEW storage architecture once built.
Until then, they serve as the specification.

See docs/Test-Plan.md for the full test strategy.
"""

import pytest


# Company intelligence fields that must NEVER appear in product or program storage
COMPANY_INTELLIGENCE_FIELDS = {
    "fit_score", "acv_potential", "hubspot_icp_context",
    "buying_signals", "competitive_landscape",
}

# Program data fields that must NEVER appear in company intelligence storage
PROGRAM_DATA_FIELDS = {
    "program_objectives", "target_audience", "outline",
    "draft_instructions", "lab_series",
}


# ── Product data isolation ──────────────────────────────────────────────────

def test_product_storage_no_company_intelligence():
    """Product data storage must not contain company intelligence fields.

    No fit scores, contacts, ACV, or buying signals in product storage.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


def test_product_data_accessible_from_all_tools():
    """Product data must be readable by Inspector, Prospector, and Designer."""
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── Company intelligence isolation ──────────────────────────────────────────

def test_company_storage_no_program_data():
    """Company intelligence storage must not contain program data.

    No Designer programs, outlines, or instructions.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── Program data isolation ──────────────────────────────────────────────────

def test_program_storage_no_company_intelligence():
    """Program data storage must not contain company intelligence.

    Designer programs never touch fit scores, contacts, or competitive signals.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── The hard wall ───────────────────────────────────────────────────────────

def test_designer_cannot_access_company_intelligence():
    """A simulated Designer request must not return company intelligence data.

    The hard wall — even if you try, the data isn't there.
    Customers never see Prospector or Inspector data. Ever.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── Physical separation ─────────────────────────────────────────────────────

def test_storage_directories_are_separate():
    """The three data domains must be in physically separate storage locations.

    Not fields within shared files — separate directories or databases.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")
