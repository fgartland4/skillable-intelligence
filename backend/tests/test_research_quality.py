"""Category 5: Research and Evidence Quality

Guiding Principle: GP3 (Explainably Trustworthy)

Validates research output structure, badge compliance, and lab platform detection.

See docs/Test-Plan.md for the full test strategy.
"""

from unittest.mock import patch

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


# ═══════════════════════════════════════════════════════════════════════════════
# Research → Store layer spot test (Step 2 of the rebuild, 2026-04-08)
#
# ONE focused architectural regression test for Pillar 1 fact extraction:
# mock Claude with a canned JSON response and verify the extractor returns a
# ProductLababilityFacts dataclass with every typed primitive preserved — no
# strength fields, no badges, no points.  This locks in the Research → Store
# boundary: the extractor is truth-only, typed-primitive-only, and never
# leaks scoring concepts into the fact drawer.
#
# When Pillar 2 + Pillar 3 extractors land (Step 2.5), add one sibling test
# each.  Keep the pattern identical — one canned response, one assertion
# block per pillar's canonical home.
# ═══════════════════════════════════════════════════════════════════════════════

_CANNED_PRODUCT_LABABILITY_FACTS_JSON = {
    "provisioning": {
        "description": "Runs as a native Windows installer on Windows Server 2019+.",
        "runs_as_installable": True,
        "runs_as_azure_native": False,
        "runs_as_aws_native": False,
        "runs_as_container": False,
        "runs_as_saas_only": False,
        "supported_host_os": ["windows"],
        "has_sandbox_api": False,
        "sandbox_api_granularity": "none",
        "is_multi_vm_lab": True,
        "has_complex_topology": False,
        "is_large_lab": False,
        "has_pre_instancing_opportunity": False,
        "needs_gpu": False,
        "needs_bare_metal": False,
        "needs_gcp": False,
    },
    "lab_access": {
        "description": "Product manages its own local user database; admin creates accounts inside the product.",
        "user_provisioning_api_granularity": "partial",
        "auth_model": "product_credentials",
        "credential_lifecycle": "recyclable",
        "learner_isolation": "confirmed",
        "training_license": "low_friction",
        "has_mfa_blocker": False,
        "has_anti_automation": False,
        "has_rate_limit_blocker": False,
    },
    "scoring": {
        "description": "REST API exposes full state query for policies, users, and scan results.",
        "state_validation_api_granularity": "rich",
        "scriptable_via_shell_granularity": "partial",
        "gui_state_visually_evident_granularity": "full",
        "simulation_scoring_viable": False,
    },
    "teardown": {
        "description": "Installable deployment — datacenter snapshot handles teardown; no vendor orphan risk.",
        "vendor_teardown_api_granularity": "none",
        "has_orphan_risk": False,
    },
}


def test_extract_product_labability_facts_parses_canned_response():
    """The Pillar 1 fact extractor must parse a canned Claude JSON response
    into a fully populated ProductLababilityFacts dataclass.

    This is the Research → Store contract: truth-only typed primitives
    land in their canonical home with no scoring interpretation.  If this
    test fails, the extractor is drifting from the Research layer into
    Score or Badge territory — STOP and re-read Platform-Foundation.md
    "Three Layers of Intelligence."
    """
    from models import (
        LabAccessFacts, ProductLababilityFacts, ProvisioningFacts,
        ScoringFacts, TeardownFacts,
    )
    from researcher import extract_product_labability_facts

    with patch("scorer._call_claude", return_value=_CANNED_PRODUCT_LABABILITY_FACTS_JSON):
        facts = extract_product_labability_facts(
            product_name="Acme Endpoint Sentinel",
            search_results={},
            page_contents={},
        )

    # Shape: returned the correct dataclass, with all four sub-drawers as the
    # correct dataclass types (no leaked dicts).
    assert isinstance(facts, ProductLababilityFacts)
    assert isinstance(facts.provisioning, ProvisioningFacts)
    assert isinstance(facts.lab_access, LabAccessFacts)
    assert isinstance(facts.scoring, ScoringFacts)
    assert isinstance(facts.teardown, TeardownFacts)

    # Provisioning: typed primitives preserved faithfully.
    assert facts.provisioning.runs_as_installable is True
    assert facts.provisioning.runs_as_saas_only is False
    assert facts.provisioning.supported_host_os == ["windows"]
    assert facts.provisioning.sandbox_api_granularity == "none"
    assert facts.provisioning.is_multi_vm_lab is True

    # Lab access: auth_model enum + granularity strings survive verbatim.
    assert facts.lab_access.auth_model == "product_credentials"
    assert facts.lab_access.user_provisioning_api_granularity == "partial"
    assert facts.lab_access.credential_lifecycle == "recyclable"
    assert facts.lab_access.learner_isolation == "confirmed"
    assert facts.lab_access.training_license == "low_friction"

    # Scoring: capability granularities preserved.
    assert facts.scoring.state_validation_api_granularity == "rich"
    assert facts.scoring.scriptable_via_shell_granularity == "partial"
    assert facts.scoring.gui_state_visually_evident_granularity == "full"
    assert facts.scoring.simulation_scoring_viable is False

    # Teardown: installable products are "none" without penalty implied.
    assert facts.teardown.vendor_teardown_api_granularity == "none"
    assert facts.teardown.has_orphan_risk is False

    # TRUTH-ONLY CONTRACT — the extracted facts must NOT contain any scoring
    # or badge concepts.  If these attributes ever appear, it means the
    # Research layer is silently absorbing Score or Badge work.
    assert not hasattr(facts.provisioning, "strength")
    assert not hasattr(facts.lab_access, "badge")
    assert not hasattr(facts.scoring, "points")
    assert not hasattr(facts.teardown, "verdict")


def test_extract_product_labability_facts_returns_defaults_on_claude_failure():
    """If the Claude call raises, the extractor must return an empty
    ProductLababilityFacts instead of crashing the research run.

    This protects the architecture rule that research is best-effort —
    one flaky fact extraction cannot take down the whole research phase
    and block downstream layers.
    """
    from models import ProductLababilityFacts
    from researcher import extract_product_labability_facts

    with patch("scorer._call_claude", side_effect=RuntimeError("simulated API failure")):
        facts = extract_product_labability_facts(
            product_name="Broken Widget",
            search_results={},
            page_contents={},
        )

    assert isinstance(facts, ProductLababilityFacts)
    # All fields at neutral defaults — no guessing from a failed call.
    assert facts.provisioning.runs_as_installable is False
    assert facts.lab_access.auth_model == ""
    assert facts.scoring.state_validation_api_granularity == ""
    assert facts.teardown.vendor_teardown_api_granularity == ""


# ─────────────────────────────────────────────────────────────────────────────
# Pillar 2 spot test — InstructionalValueFacts canned-response parse
#
# Same shape as Pillar 1: mock Claude with a canned JSON, verify the
# extractor produces a fully-populated dataclass with no `strength` field
# leaking into SignalEvidence (truth-only contract).
# ─────────────────────────────────────────────────────────────────────────────

_CANNED_INSTRUCTIONAL_VALUE_FACTS_JSON = {
    "product_complexity": {
        "description": "Multi-VM enterprise security product with deep configuration surface area.",
        "signals": {
            "multi_vm_architecture": {
                "present": True,
                "observation": "Reference architecture shows manager + sensor + collector across three VMs.",
                "source_url": "https://docs.example.com/architecture",
                "confidence": "confirmed",
            },
            "deep_configuration": {
                "present": True,
                "observation": "Admin console exposes 14 top-level policy categories with 60+ tunables.",
                "source_url": "https://docs.example.com/admin",
                "confidence": "indicated",
            },
        },
    },
    "mastery_stakes": {
        "description": "Misconfiguration can expose sensitive data and trigger compliance findings.",
        "signals": {
            "breach_exposure": {
                "present": True,
                "observation": "Misconfigured policy can leave endpoints unprotected during rollout.",
                "source_url": "https://example.com/cve",
                "confidence": "confirmed",
            },
        },
    },
    "lab_versatility": {
        "description": "Defensive product with strong incident-response and break-fix lab fit.",
        "signals": {
            "incident_response": {
                "present": True,
                "observation": "Documented playbooks for triaging detections under simulated load.",
                "source_url": "",
                "confidence": "indicated",
            },
            "break_fix": {
                "present": True,
                "observation": "Common failure modes documented in support knowledge base.",
                "source_url": "",
                "confidence": "inferred",
            },
        },
    },
    "market_demand": {
        "description": "Mid-market install base with active certification ecosystem.",
        "install_base": {
            "low": 40000,
            "high": 60000,
            "source_url": "https://example.com/about",
            "confidence": "indicated",
            "notes": "Combined commercial + government deployments.",
        },
        "employee_subset_size": {
            "low": 200000,
            "high": 300000,
            "source_url": "",
            "confidence": "inferred",
            "notes": "",
        },
        "cert_annual_sit_rate": {
            "low": 1500,
            "high": 2500,
            "source_url": "",
            "confidence": "inferred",
            "notes": "",
        },
        "cert_bodies_mentioning": ["CompTIA", "SANS"],
        "independent_training_course_counts": {"Pluralsight": 12, "Coursera": 4, "Udemy": 7},
        "is_ai_powered": True,
        "is_ai_platform": False,
        "signals": {
            "category_demand": {
                "present": True,
                "observation": "Cybersecurity is a high-demand training category.",
                "source_url": "",
                "confidence": "confirmed",
            },
        },
    },
}


def test_extract_instructional_value_facts_parses_canned_response():
    """Pillar 2 fact extractor must parse a canned Claude JSON response into
    a fully populated InstructionalValueFacts dataclass.

    Verifies the truth-only contract: SignalEvidence dicts have NO strength
    field, the qualitative description survives, the four sub-drawers are
    all the correct dataclass type, and Market Demand's mixed
    numeric/list/dict facts coerce correctly.
    """
    from models import (
        InstructionalValueFacts, LabVersatilityFacts, MarketDemandFacts,
        MasteryStakesFacts, NumericRange, ProductComplexityFacts,
        SignalEvidence,
    )
    from researcher import extract_instructional_value_facts

    with patch("scorer._call_claude", return_value=_CANNED_INSTRUCTIONAL_VALUE_FACTS_JSON):
        facts = extract_instructional_value_facts(
            product_name="Acme Endpoint Sentinel",
            search_results={},
            page_contents={},
        )

    # Shape — all four sub-drawers are the correct dataclass type.
    assert isinstance(facts, InstructionalValueFacts)
    assert isinstance(facts.product_complexity, ProductComplexityFacts)
    assert isinstance(facts.mastery_stakes, MasteryStakesFacts)
    assert isinstance(facts.lab_versatility, LabVersatilityFacts)
    assert isinstance(facts.market_demand, MarketDemandFacts)

    # Product Complexity — signals dict round-trips with SignalEvidence values.
    pc = facts.product_complexity
    assert "multi_vm_architecture" in pc.signals
    assert isinstance(pc.signals["multi_vm_architecture"], SignalEvidence)
    assert pc.signals["multi_vm_architecture"].present is True
    assert "manager + sensor + collector" in pc.signals["multi_vm_architecture"].observation
    assert pc.signals["multi_vm_architecture"].confidence == "confirmed"

    # TRUTH-ONLY: SignalEvidence must NOT have a strength field.
    assert not hasattr(pc.signals["multi_vm_architecture"], "strength")

    # Mastery Stakes — qualitative signal preserved.
    assert facts.mastery_stakes.signals["breach_exposure"].present is True

    # Lab Versatility — multiple lab type signals coexist.
    assert "incident_response" in facts.lab_versatility.signals
    assert "break_fix" in facts.lab_versatility.signals

    # Market Demand — concrete numeric facts coerce into NumericRange.
    md = facts.market_demand
    assert isinstance(md.install_base, NumericRange)
    assert md.install_base.low == 40000
    assert md.install_base.high == 60000
    assert md.install_base.confidence == "indicated"
    assert isinstance(md.employee_subset_size, NumericRange)
    assert md.employee_subset_size.low == 200000

    # Market Demand — concrete list/dict facts.
    assert md.cert_bodies_mentioning == ["CompTIA", "SANS"]
    assert md.independent_training_course_counts == {"Pluralsight": 12, "Coursera": 4, "Udemy": 7}

    # Market Demand — boolean flags.
    assert md.is_ai_powered is True
    assert md.is_ai_platform is False

    # Market Demand — qualitative signals dict still works alongside concrete facts.
    assert md.signals["category_demand"].present is True


def test_extract_instructional_value_facts_returns_defaults_on_claude_failure():
    """If the Pillar 2 Claude call raises, the extractor must return an
    empty InstructionalValueFacts instead of crashing the research run.
    """
    from models import InstructionalValueFacts, NumericRange
    from researcher import extract_instructional_value_facts

    with patch("scorer._call_claude", side_effect=RuntimeError("simulated API failure")):
        facts = extract_instructional_value_facts(
            product_name="Broken Widget",
            search_results={},
            page_contents={},
        )

    assert isinstance(facts, InstructionalValueFacts)
    assert facts.product_complexity.description == ""
    assert facts.product_complexity.signals == {}
    assert facts.market_demand.signals == {}
    assert facts.market_demand.cert_bodies_mentioning == []
    assert facts.market_demand.independent_training_course_counts == {}
    assert isinstance(facts.market_demand.install_base, NumericRange)
    assert facts.market_demand.install_base.low is None
    assert facts.market_demand.install_base.high is None


# ─────────────────────────────────────────────────────────────────────────────
# Pillar 3 spot test — CustomerFitFacts canned-response parse
#
# Pillar 3 is company-level (not per-product) and has the most complex
# shape: top-level shared facts feeding multiple downstream readers, plus
# four per-dimension drawers.  Tests verify the full nested structure
# round-trips and the truth-only contract holds.
# ─────────────────────────────────────────────────────────────────────────────

_CANNED_CUSTOMER_FIT_FACTS_JSON = {
    "description": "Mid-market enterprise software vendor with established partner program.",
    "total_employees": {"low": 5000, "high": 5500, "source_url": "", "confidence": "confirmed", "notes": ""},
    "channel_partners_size": {"low": 800, "high": 1200, "source_url": "", "confidence": "indicated", "notes": ""},
    "channel_partner_se_population": {"low": 4000, "high": 6000, "source_url": "", "confidence": "inferred", "notes": ""},
    "named_channel_partners": ["Deloitte", "Accenture", "KPMG"],
    "events_attendance": {
        "Acme Connect": {"low": 5000, "high": 5500, "source_url": "", "confidence": "confirmed", "notes": ""},
    },
    "enterprise_reference_customers": ["Fortune Co A", "Fortune Co B"],
    "geographic_reach_regions": ["NAMER", "EMEA", "APAC"],
    "training_commitment": {
        "description": "Established customer enablement org with multi-audience reach.",
        "has_on_demand_catalog": True,
        "has_ilt_calendar": True,
        "customer_enablement_team_name": "Acme Customer Education",
        "certification_programs": ["ACA", "ACP", "ACE"],
        "training_leadership_titles": ["VP of Education", "Director of Customer Enablement"],
        "training_catalog_url": "https://acme.example.com/training",
        "audiences_served": ["employees", "customers", "partners"],
        "has_compliance_training": True,
        "uses_hands_on_language": True,
        "signals": {},
    },
    "build_capacity": {
        "description": "Multiple lab platforms in use with active in-house authoring team.",
        "lab_build_platforms_in_use": ["Skillable", "Instruqt"],
        "is_already_building_labs": True,
        "content_team_name": "Acme Learning Studio",
        "authoring_roles_found": ["Instructional Designer", "Lab Author"],
        "outsourcing_evidence": [],
        "signals": {},
    },
    "delivery_capacity": {
        "description": "Vendor-delivered ILT with formal authorized partner program.",
        "has_vendor_delivered_training": True,
        "vendor_training_modes": ["ilt", "self_paced", "vendor_labs"],
        "has_published_course_calendar": True,
        "course_calendar_url": "https://acme.example.com/courses",
        "has_informal_training_partners": True,
        "named_informal_training_partners": ["LearningTree"],
        "authorized_training_program_name": "Acme Authorized Training Partner",
        "authorized_training_partners_count": {"low": 200, "high": 250, "source_url": "", "confidence": "indicated", "notes": ""},
        "named_authorized_training_partners": ["Global Knowledge", "ExitCertified"],
        "lms_platforms_in_use": ["Docebo"],
        "cert_delivery_vendors": ["Pearson VUE"],
        "signals": {},
    },
    "organizational_dna": {
        "description": "Platform buyer culture with multi-type partnership program.",
        "partnership_types": ["technology", "channel", "delivery"],
        "named_alliance_leadership": ["VP Strategic Alliances"],
        "uses_external_platforms": ["Salesforce", "Workday", "Okta"],
        "funding_events": ["IPO 2022"],
        "has_recent_layoffs": False,
        "signals": {},
    },
}


def test_extract_customer_fit_facts_parses_canned_response():
    """Pillar 3 fact extractor must parse a canned Claude JSON response into
    a fully populated CustomerFitFacts dataclass.

    Verifies the company-level fact drawer round-trips: top-level shared
    facts (NumericRange + named lists), all four per-dimension sub-drawers,
    nested events_attendance dict of NumericRange, and the separate
    informal vs authorized partner field sets (Option B from 2026-04-07
    — Cohesity-style transitions need both populated simultaneously).
    """
    from models import (
        BuildCapacityFacts, CustomerFitFacts, DeliveryCapacityFacts,
        NumericRange, OrganizationalDnaFacts, TrainingCommitmentFacts,
    )
    from researcher import extract_customer_fit_facts

    with patch("scorer._call_claude", return_value=_CANNED_CUSTOMER_FIT_FACTS_JSON):
        facts = extract_customer_fit_facts(
            company_name="Acme Corp",
            discovery_data=None,
            customer_fit_research={},
            customer_fit_pages={},
        )

    # Shape — all four sub-drawers are the correct dataclass type.
    assert isinstance(facts, CustomerFitFacts)
    assert isinstance(facts.training_commitment, TrainingCommitmentFacts)
    assert isinstance(facts.build_capacity, BuildCapacityFacts)
    assert isinstance(facts.delivery_capacity, DeliveryCapacityFacts)
    assert isinstance(facts.organizational_dna, OrganizationalDnaFacts)

    # Top-level shared facts — these feed multiple downstream readers + ACV motions.
    assert isinstance(facts.total_employees, NumericRange)
    assert facts.total_employees.low == 5000
    assert isinstance(facts.channel_partner_se_population, NumericRange)  # → ACV Motion 2
    assert facts.channel_partner_se_population.low == 4000
    assert facts.named_channel_partners == ["Deloitte", "Accenture", "KPMG"]
    assert facts.geographic_reach_regions == ["NAMER", "EMEA", "APAC"]

    # events_attendance — dict of {event_name: NumericRange}, feeds ACV Motion 5.
    assert "Acme Connect" in facts.events_attendance
    assert isinstance(facts.events_attendance["Acme Connect"], NumericRange)
    assert facts.events_attendance["Acme Connect"].low == 5000

    # Training Commitment — multi-audience signal + cert programs + catalog flags.
    tc = facts.training_commitment
    assert tc.has_on_demand_catalog is True
    assert tc.audiences_served == ["employees", "customers", "partners"]
    assert tc.certification_programs == ["ACA", "ACP", "ACE"]
    assert tc.uses_hands_on_language is True

    # Build Capacity — competitor lab platforms detected, authoring roles found.
    bc = facts.build_capacity
    assert bc.lab_build_platforms_in_use == ["Skillable", "Instruqt"]
    assert bc.is_already_building_labs is True
    assert "Instructional Designer" in bc.authoring_roles_found

    # Delivery Capacity — both informal AND authorized partner sets populated
    # simultaneously (Option B field-set split — Cohesity-in-transition pattern).
    dc = facts.delivery_capacity
    assert dc.has_vendor_delivered_training is True
    assert dc.has_informal_training_partners is True
    assert "LearningTree" in dc.named_informal_training_partners
    assert dc.authorized_training_program_name == "Acme Authorized Training Partner"
    assert isinstance(dc.authorized_training_partners_count, NumericRange)
    assert dc.authorized_training_partners_count.low == 200
    assert "Global Knowledge" in dc.named_authorized_training_partners
    assert dc.lms_platforms_in_use == ["Docebo"]

    # Organizational DNA — Platform Buyer evidence + funding events + partnership types.
    od = facts.organizational_dna
    assert "channel" in od.partnership_types
    assert od.uses_external_platforms == ["Salesforce", "Workday", "Okta"]
    assert od.funding_events == ["IPO 2022"]
    assert od.has_recent_layoffs is False


def test_extract_customer_fit_facts_returns_defaults_on_claude_failure():
    """If the Pillar 3 Claude call raises, the extractor must return an
    empty CustomerFitFacts instead of crashing the research run.
    """
    from models import CustomerFitFacts, NumericRange
    from researcher import extract_customer_fit_facts

    with patch("scorer._call_claude", side_effect=RuntimeError("simulated API failure")):
        facts = extract_customer_fit_facts(
            company_name="Broken Co",
            discovery_data=None,
            customer_fit_research={},
            customer_fit_pages={},
        )

    assert isinstance(facts, CustomerFitFacts)
    assert facts.named_channel_partners == []
    assert facts.events_attendance == {}
    assert isinstance(facts.total_employees, NumericRange)
    assert facts.total_employees.low is None
    assert facts.training_commitment.audiences_served == []
    assert facts.delivery_capacity.named_authorized_training_partners == []
    assert facts.organizational_dna.uses_external_platforms == []
