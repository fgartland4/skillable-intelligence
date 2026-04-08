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
