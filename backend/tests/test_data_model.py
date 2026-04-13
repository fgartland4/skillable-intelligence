"""Category 3: Data Model

Guiding Principles: GP4 (Self-Evident Design), GP3 (Explainably Trustworthy)

Validates that the data model correctly represents the three-pillar hierarchy,
evidence with confidence coding, and data domain separation.

NOTE: Most of the tests below are placeholder skips waiting for the rebuild
to land their relevant pieces.  As each rebuild step ships, the placeholder
tests get implemented (if they protect a current architectural promise) or
deleted (if they don't).  Per Frank 2026-04-07: "rewrite, not append"
applies to the test suite — never accumulate stale checks.

The Define-Once tests at the bottom are the live spot tests for the new
fact drawer (Step 1 of the Research → Store → Score → Badge rebuild).
"""

import pytest

import models


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
    """Fit Score = (PL x 0.50) + (IV x 0.20) + (CF x 0.30).

    Rebalanced 2026-04-12 from 40/30/30 to 50/20/30.
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


# ═══════════════════════════════════════════════════════════════════════════════
# Fact Drawer — Define-Once spot tests (Step 1 of the Research/Store/Score/Badge
# rebuild, 2026-04-07).  Each load-bearing fact lives in EXACTLY one location;
# cross-pillar reads are explicit and read from the canonical home.
# ═══════════════════════════════════════════════════════════════════════════════

# Canonical home for each load-bearing fact in the new fact drawer.
# Maps field name → the dataclass that owns it.  If a field appears anywhere
# else, that's a Define-Once violation.  This whitelist is the contract.
#
# Common-utility field names (description, signals, notes, source_url,
# confidence) are intentionally NOT in this map — they're shared shapes
# used across many drawers, not load-bearing facts.
_FACT_CANONICAL_HOME = {
    # ── Pillar 2 Market Demand (per-product) ─────────────────────────────
    "install_base": "MarketDemandFacts",
    "employee_subset_size": "MarketDemandFacts",
    "cert_annual_sit_rate": "MarketDemandFacts",
    "cert_bodies_mentioning": "MarketDemandFacts",
    "independent_training_course_counts": "MarketDemandFacts",
    "is_ai_powered": "MarketDemandFacts",
    "is_ai_platform": "MarketDemandFacts",
    # ── Pillar 3 top-level shared facts (company-level) ──────────────────
    "total_employees": "CustomerFitFacts",
    "channel_partners_size": "CustomerFitFacts",
    "channel_partner_se_population": "CustomerFitFacts",
    "named_channel_partners": "CustomerFitFacts",
    "events_attendance": "CustomerFitFacts",
    "enterprise_reference_customers": "CustomerFitFacts",
    "geographic_reach_regions": "CustomerFitFacts",
    # ── Pillar 3.2 Build Capacity ────────────────────────────────────────
    "lab_build_platforms_in_use": "BuildCapacityFacts",
    "is_already_building_labs": "BuildCapacityFacts",
    "content_team_name": "BuildCapacityFacts",
    "authoring_roles_found": "BuildCapacityFacts",
    "outsourcing_evidence": "BuildCapacityFacts",
    # ── Pillar 3.3 Delivery Capacity ─────────────────────────────────────
    "has_vendor_delivered_training": "DeliveryCapacityFacts",
    "vendor_training_modes": "DeliveryCapacityFacts",
    "has_published_course_calendar": "DeliveryCapacityFacts",
    "course_calendar_url": "DeliveryCapacityFacts",
    "has_informal_training_partners": "DeliveryCapacityFacts",
    "named_informal_training_partners": "DeliveryCapacityFacts",
    "authorized_training_program_name": "DeliveryCapacityFacts",
    "authorized_training_partners_count": "DeliveryCapacityFacts",
    "named_authorized_training_partners": "DeliveryCapacityFacts",
    "lms_platforms_in_use": "DeliveryCapacityFacts",
    "cert_delivery_vendors": "DeliveryCapacityFacts",
    # ── Pillar 3.4 Organizational DNA ────────────────────────────────────
    "partnership_types": "OrganizationalDnaFacts",
    "named_alliance_leadership": "OrganizationalDnaFacts",
    "uses_external_platforms": "OrganizationalDnaFacts",
    "funding_events": "OrganizationalDnaFacts",
    "has_recent_layoffs": "OrganizationalDnaFacts",
    # ── Pillar 3.1 Training Commitment ───────────────────────────────────
    "has_on_demand_catalog": "TrainingCommitmentFacts",
    "has_ilt_calendar": "TrainingCommitmentFacts",
    "customer_enablement_team_name": "TrainingCommitmentFacts",
    "certification_programs": "TrainingCommitmentFacts",
    "training_leadership_titles": "TrainingCommitmentFacts",
    "training_catalog_url": "TrainingCommitmentFacts",
    "audiences_served": "TrainingCommitmentFacts",
    "has_compliance_training": "TrainingCommitmentFacts",
    "uses_hands_on_language": "TrainingCommitmentFacts",
}

# Fact-drawer dataclasses to walk.  Sub-dataclasses inside ProductLababilityFacts
# (provisioning/lab_access/scoring/teardown) are walked as their own classes
# because they each hold distinct fact territories.
_FACT_DRAWER_CLASSES = [
    "NumericRange", "SignalEvidence",
    "ProvisioningFacts", "LabAccessFacts", "ScoringFacts", "TeardownFacts",
    "ProductLababilityFacts",
    "ProductComplexityFacts", "MasteryStakesFacts", "LabVersatilityFacts", "MarketDemandFacts",
    "InstructionalValueFacts",
    "TrainingCommitmentFacts", "BuildCapacityFacts", "DeliveryCapacityFacts", "OrganizationalDnaFacts",
    "CustomerFitFacts",
]


def _all_fact_drawer_fields():
    """Walk every fact-drawer dataclass and return [(class_name, field_name), ...]."""
    from dataclasses import fields
    out = []
    for cls_name in _FACT_DRAWER_CLASSES:
        cls = getattr(models, cls_name)
        for f in fields(cls):
            out.append((cls_name, f.name))
    return out


def test_fact_drawer_dataclasses_all_exist():
    """Every fact drawer dataclass listed in _FACT_DRAWER_CLASSES must exist
    in models.py.  If a class is removed in a refactor, this test catches
    the orphan reference in the test file."""
    for cls_name in _FACT_DRAWER_CLASSES:
        assert hasattr(models, cls_name), (
            f"Fact drawer dataclass {cls_name!r} missing from models.py"
        )


def test_fact_drawer_load_bearing_fields_live_in_canonical_home():
    """Each load-bearing fact in _FACT_CANONICAL_HOME lives in EXACTLY one
    dataclass — its declared canonical home.  This is the Define-Once spot
    test for Step 1: no fact may live in two places.

    Per Frank 2026-04-07: "Each fact lives once.  Cross-pillar reads happen,
    but the data lives in one location."  This test enforces that rule.
    """
    all_fields = _all_fact_drawer_fields()
    field_locations: dict[str, list[str]] = {}
    for cls_name, field_name in all_fields:
        field_locations.setdefault(field_name, []).append(cls_name)

    violations = []
    for field_name, expected_home in _FACT_CANONICAL_HOME.items():
        actual_homes = field_locations.get(field_name, [])
        if not actual_homes:
            violations.append(
                f"  - {field_name!r} expected in {expected_home}, but not found anywhere"
            )
        elif actual_homes != [expected_home]:
            violations.append(
                f"  - {field_name!r} expected in {expected_home}, but found in {actual_homes}"
            )

    assert not violations, (
        "Define-Once violation in fact drawer:\n" + "\n".join(violations)
    )


def test_no_unexpected_load_bearing_field_duplication():
    """Catch accidental duplication of fact field names across drawers.

    Common shared field names (description, signals, notes, source_url,
    confidence, present, observation, low, high) are allowed to appear
    in many places — they're shape primitives, not facts.  Any OTHER
    field name appearing in two or more drawers is a potential
    Define-Once violation that should be reviewed.
    """
    SHARED_SHAPE_FIELDS = {
        "description", "signals", "notes", "source_url", "confidence",
        "present", "observation", "low", "high",
    }
    all_fields = _all_fact_drawer_fields()
    field_locations: dict[str, list[str]] = {}
    for cls_name, field_name in all_fields:
        if field_name in SHARED_SHAPE_FIELDS:
            continue
        field_locations.setdefault(field_name, []).append(cls_name)

    duplicates = {
        name: locations
        for name, locations in field_locations.items()
        if len(locations) > 1
    }
    assert not duplicates, (
        "Field names duplicated across fact drawer dataclasses (potential "
        "Define-Once violation — review and either rename or add to the "
        "_FACT_CANONICAL_HOME whitelist if intentional):\n" +
        "\n".join(f"  - {name!r}: {locations}" for name, locations in duplicates.items())
    )


def test_product_holds_pillar_1_and_pillar_2_fact_drawers():
    """Per the Three Layers architecture, Product carries the Pillar 1 and
    Pillar 2 fact drawers.  Pillar 3 (Customer Fit) lives on
    CompanyAnalysis because it measures the organization, not the product.
    """
    from dataclasses import fields
    product_fields = {f.name: f.type for f in fields(models.Product)}
    assert "product_labability_facts" in product_fields, (
        "Product must carry product_labability_facts"
    )
    assert "instructional_value_facts" in product_fields, (
        "Product must carry instructional_value_facts"
    )
    # Customer Fit must NOT live on Product
    assert "customer_fit_facts" not in product_fields, (
        "customer_fit_facts must NOT live on Product (it's company-level — "
        "lives on CompanyAnalysis)"
    )


def test_company_analysis_holds_pillar_3_fact_drawer():
    """CompanyAnalysis carries CustomerFitFacts because Customer Fit is
    measured at the company level, not per-product."""
    from dataclasses import fields
    ca_fields = {f.name: f.type for f in fields(models.CompanyAnalysis)}
    assert "customer_fit_facts" in ca_fields, (
        "CompanyAnalysis must carry customer_fit_facts"
    )
