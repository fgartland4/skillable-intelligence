"""Tests for storage._normalize_company_name.

Covers:
  - Regex cleanup preserves existing behavior (corporate suffixes,
    parentheticals, "by X" suffix, product/division suffixes)
  - LLP / GmbH / AG / Pty added to corporate-suffix regex
    (Accenture / Accenture LLP case)
  - Explicit alias map catches the cases regex cannot:
      * Grand Canyon University / Grand Canyon Education
      * SAP / SAP Canada / SAP Ariba

Define-Once for name normalization lives in storage._normalize_company_name;
these tests are its contract.
"""

from __future__ import annotations

from storage import _normalize_company_name


# ─────────────────────────────────────────────────────────────────────────
# Existing behavior — should not regress
# ─────────────────────────────────────────────────────────────────────────

def test_cisco_variants_collapse():
    # Classic case the original regex was designed for
    assert _normalize_company_name("Cisco") == _normalize_company_name("Cisco Systems")
    assert _normalize_company_name("Cisco Systems") == "cisco"


def test_google_variants_collapse():
    assert _normalize_company_name("Google") == _normalize_company_name("Google Cloud")


def test_vmware_variants_collapse():
    assert _normalize_company_name("VMware (by Broadcom)") == _normalize_company_name("VMware by Broadcom")
    assert _normalize_company_name("VMware") == "vmware"


def test_parenthetical_removed():
    assert _normalize_company_name("Foo (subsidiary)") == "foo"


def test_common_corporate_suffixes_stripped():
    # The existing suffix list — should not regress
    assert _normalize_company_name("Acme Inc.") == "acme"
    assert _normalize_company_name("Acme Corporation") == "acme"
    assert _normalize_company_name("Acme LLC") == "acme"
    assert _normalize_company_name("Acme Ltd.") == "acme"
    assert _normalize_company_name("Acme Limited") == "acme"
    assert _normalize_company_name("Acme PLC") == "acme"


# ─────────────────────────────────────────────────────────────────────────
# New: LLP added to corporate-suffix regex
# ─────────────────────────────────────────────────────────────────────────

def test_accenture_llp_collapses_to_accenture():
    """LLP must strip so 'Accenture' and 'Accenture LLP' dedupe.

    Previous session observed duplicate Accenture rows in Prospector
    with both showing super-high ACV — double-counting because the
    normalized keys didn't match.
    """
    assert _normalize_company_name("Accenture") == "accenture"
    assert _normalize_company_name("Accenture LLP") == "accenture"


def test_llp_stripped_with_punctuation():
    """LLP should strip whether followed by comma or space."""
    assert _normalize_company_name("Deloitte LLP") == "deloitte"
    assert _normalize_company_name("Deloitte, LLP") == "deloitte"


# ─────────────────────────────────────────────────────────────────────────
# New: alias map cases the regex cannot handle
# ─────────────────────────────────────────────────────────────────────────

def test_grand_canyon_education_collapses_to_university():
    """GCE (for-profit parent) and GCU (the school) are legally distinct
    but the same Skillable opportunity. Alias map collapses to GCU.
    """
    gcu = _normalize_company_name("Grand Canyon University")
    gce = _normalize_company_name("Grand Canyon Education")
    assert gcu == gce
    assert gcu == "grand canyon university"


def test_sap_variants_collapse_to_sap():
    """SAP / SAP Canada / SAP Ariba all fold to 'sap'."""
    assert _normalize_company_name("SAP") == "sap"
    assert _normalize_company_name("SAP Canada") == "sap"
    assert _normalize_company_name("SAP Ariba") == "sap"
