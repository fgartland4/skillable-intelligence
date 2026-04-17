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


# ─────────────────────────────────────────────────────────────────────────
# Second batch of "listed twice" cases (Frank 2026-04-16)
# ─────────────────────────────────────────────────────────────────────────

def test_f5_networks_collapses():
    """F5 / F5 Networks — 'networks' added to corporate-suffix regex."""
    assert _normalize_company_name("F5") == _normalize_company_name("F5 Networks")


def test_honeywell_international_collapses():
    """Honeywell / Honeywell International — 'international' added to suffix regex."""
    assert _normalize_company_name("Honeywell") == _normalize_company_name("Honeywell International")


def test_regional_suffix_stripped():
    """Regional suffixes (USA, UK, Canada, etc.) strip from company names."""
    assert _normalize_company_name("Kaspersky") == _normalize_company_name("Kaspersky USA")
    assert _normalize_company_name("Siemens") == _normalize_company_name("Siemens UK")
    assert _normalize_company_name("Foo") == _normalize_company_name("Foo EMEA")


def test_polish_llc_suffix_stripped():
    """Sp. z o.o. (Polish LLC) strips — CLICO case."""
    assert _normalize_company_name("CLICO") == _normalize_company_name("CLICO Sp. z o.o.")
    assert _normalize_company_name("CLICO") == _normalize_company_name("CLICO sp z o o")


def test_german_corporate_forms_stripped():
    """SE + Co. KG, AG & Co. KG, GmbH & Co. KG — TRUMPF case.

    German corporate forms are multi-token; the regex strips them before
    the general corporate-suffix regex runs so they don't leak through.
    """
    assert _normalize_company_name("TRUMPF") == _normalize_company_name("TRUMPF SE + Co. KG")
    assert _normalize_company_name("Foo") == _normalize_company_name("Foo AG & Co. KG")
    assert _normalize_company_name("Foo") == _normalize_company_name("Foo GmbH & Co. KG")


def test_confluent_ibm_ownership_collapses():
    """Confluent kept its brand after IBM acquisition.

    'Confluent, an IBM Company' is the same company as 'Confluent' for
    Skillable analysis purposes. Alias map handles the ", an X Company"
    pattern explicitly — no general regex because brand survival after
    acquisition is a judgment call per target company, not a universal rule.
    """
    assert _normalize_company_name("Confluent") == _normalize_company_name("Confluent, an IBM Company")


# ─────────────────────────────────────────────────────────────────────────
# Explicit NON-collapse cases — product lines treated as distinct companies
# ─────────────────────────────────────────────────────────────────────────

def test_product_lines_do_not_collapse_to_parent():
    """Amazon/AWS pattern: legally one company, practically distinct entities
    with their own customers, training audiences, and ACV profiles.

    The normalizer intentionally does NOT collapse these — analyzing Oracle
    NetSuite or IBM Watson as independent opportunities is valid and loses
    fidelity if folded to the parent.

    Manual merges (via scripts/merge_companies.py) are the right path when
    a specific case warrants it. This test documents the intentional gap.
    """
    # Oracle product lines stay distinct
    assert _normalize_company_name("Oracle") != _normalize_company_name("Oracle NetSuite")
    assert _normalize_company_name("Oracle") != _normalize_company_name("Oracle Cloud Infrastructure")
    # IBM product lines stay distinct
    assert _normalize_company_name("IBM") != _normalize_company_name("IBM Watson")
