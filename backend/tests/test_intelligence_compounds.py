"""Category 8: Intelligence Compounds (GP5)

Guiding Principle: GP5 (Intelligence Compounds — It Never Resets)

Validates that the system builds on what it knows. Deeper research sharpens
lighter data. Nothing is lost. Intelligence compounds over time.

NOTE: These tests validate the caching and enrichment behavior once built.
Until then, they serve as the specification.

See docs/Test-Plan.md for the full test strategy.
"""

import pytest


# ── Research enrichment ─────────────────────────────────────────────────────

def test_dossier_updates_discovery_data():
    """Full dossier research must update discovery-level data.

    Deeper research sharpens lighter data, never overwrites it with less.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


def test_dossier_never_reduces_data():
    """A dossier run must never result in less data than existed before.

    Intelligence compounds — no update loses prior knowledge.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── Cache architecture ──────────────────────────────────────────────────────

def test_cache_separates_research_and_scoring():
    """Cache must store research and scoring results separately.

    Research can be preserved even if the scoring framework evolves.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


def test_rescoring_preserves_research():
    """Re-scoring a company must preserve existing research.

    GP5 — intelligence never resets. Only the scoring interpretation changes.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── Evidence freshness ──────────────────────────────────────────────────────

def test_newer_evidence_replaces_older():
    """Newer evidence replaces older evidence for the same finding.

    Fresher data wins, but nothing is lost silently.
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── Cache expiry ────────────────────────────────────────────────────────────

def test_cache_expiry_triggers_refresh_not_deletion():
    """After 45 days, cache triggers a re-research — data refreshes, doesn't disappear.

    GP5 — intelligence never resets. Expiry means "refresh," not "delete."
    """
    pytest.skip("Awaiting new storage architecture — rebuild in progress")


# ── Compound-research merge (Frank 2026-04-16) ─────────────────────────────
#
# When a second research run for the same company finds less than an earlier
# run, merge_discovery_facts carries forward the prior findings so the new
# discovery never regresses. Persistent signals (is_core_product, flagship
# relationship, higher-confidence estimates) stay; freshness signals (holistic
# ACV, fresh rough scores) take the new values.


def test_merge_preserves_flagship_classification():
    """Once a product is classified as flagship, a later thinner run that
    misses the classification must not downgrade it to standalone."""
    from backend.intelligence import merge_discovery_facts

    existing = {
        "discovery_id": "old",
        "products": [{
            "name": "RStudio IDE",
            "product_relationship": "flagship",
            "is_core_product": True,
            "description": "Comprehensive IDE for R with extensive debugging, plotting, and package management.",
        }],
    }
    new = {
        "discovery_id": "new",
        "products": [{
            "name": "RStudio IDE",
            "product_relationship": "standalone",  # second run missed the flagship read
            "is_core_product": False,              # and the core-product flag
            "description": "R IDE.",               # thinner description
        }],
    }

    merged = merge_discovery_facts(existing, new)
    prod = merged["products"][0]
    assert prod["product_relationship"] == "flagship", "flagship must not regress"
    assert prod["is_core_product"] is True, "core-product flag must not regress"
    assert "debugging, plotting, and package management" in prod["description"], (
        "richer description must be preserved"
    )


def test_merge_preserves_higher_confidence_user_base():
    """A confirmed estimate from a prior run beats an inferred estimate from
    a later run — higher-confidence evidence wins."""
    from backend.intelligence import merge_discovery_facts

    existing = {
        "products": [{
            "name": "Splunk Enterprise",
            "estimated_user_base": "~8M",
            "user_base_confidence": "confirmed",
            "user_base_evidence": "Splunk 2024 annual report, earnings call",
        }],
    }
    new = {
        "products": [{
            "name": "Splunk Enterprise",
            "estimated_user_base": "~2M",
            "user_base_confidence": "inferred",
        }],
    }

    merged = merge_discovery_facts(existing, new)
    prod = merged["products"][0]
    assert prod["estimated_user_base"] == "~8M"
    assert prod["user_base_confidence"] == "confirmed"
    assert "earnings call" in prod["user_base_evidence"]


def test_merge_unions_product_lists():
    """Products found by an earlier run that a later run missed must still
    appear in the merged discovery — don't lose what we discovered."""
    from backend.intelligence import merge_discovery_facts

    existing = {
        "products": [
            {"name": "Azure Dynamics", "category": "ERP"},
            {"name": "Azure AI", "category": "AI Platforms & Tooling"},
        ],
    }
    new = {
        "products": [
            {"name": "Azure Dynamics", "category": "ERP"},
            # second run missed Azure AI entirely
        ],
    }

    merged = merge_discovery_facts(existing, new)
    names = {p["name"] for p in merged["products"]}
    assert "Azure Dynamics" in names
    assert "Azure AI" in names, "products only in existing must be preserved"


def test_merge_tracks_provenance():
    """merged_from list records the prior discovery id so downstream code
    (load_discovery archived fallback) can resolve references to the old id."""
    from backend.intelligence import merge_discovery_facts

    existing = {"discovery_id": "old-123", "products": []}
    new = {"discovery_id": "new-456", "products": []}
    merged = merge_discovery_facts(existing, new)
    assert "old-123" in merged.get("_merged_from", [])
    assert merged["discovery_id"] == "new-456"  # new id is canonical


def test_merge_keeps_newer_holistic_acv():
    """Holistic ACV reflects current config / anchors — newer always wins."""
    from backend.intelligence import merge_discovery_facts

    existing = {"_holistic_acv": {"acv_low": 1_000_000, "acv_high": 2_000_000}}
    new = {"_holistic_acv": {"acv_low": 5_000_000, "acv_high": 10_000_000}}
    merged = merge_discovery_facts(existing, new)
    assert merged["_holistic_acv"]["acv_low"] == 5_000_000, "newer ACV wins"


def test_merge_preserves_holistic_acv_when_new_empty():
    """If new run failed to produce holistic ACV, fall back to prior value
    rather than losing it."""
    from backend.intelligence import merge_discovery_facts

    existing = {"_holistic_acv": {"acv_low": 1_000_000, "acv_high": 2_000_000}}
    new = {}  # fresh run's holistic ACV call failed
    merged = merge_discovery_facts(existing, new)
    assert merged["_holistic_acv"]["acv_low"] == 1_000_000


def test_merge_no_op_when_existing_empty():
    """With no existing record, merge returns new unchanged."""
    from backend.intelligence import merge_discovery_facts

    new = {"products": [{"name": "X"}]}
    merged = merge_discovery_facts({}, new)
    assert merged is new
    assert merged["products"][0]["name"] == "X"


# ── Dict → dataclass reconstruction (Stage 2 foundation) ───────────────────
#
# When intelligence.score() enters the rescore-from-saved-facts path, it
# needs to reconstruct typed dataclasses from the serialized-dict form
# stored on disk. Tests here lock down the reconstruction behavior so
# scorers can trust they're getting what they expect.


def test_reconstruct_product_labability_facts_nested():
    """Reconstructing ProductLababilityFacts walks all four sub-dataclasses
    (provisioning, lab_access, scoring, teardown) and attribute-access
    works end-to-end on the result."""
    from backend.intelligence import _dict_to_dataclass
    from models import ProductLababilityFacts

    raw = {
        "provisioning": {
            "has_sandbox_api": True,
            "sandbox_api_granularity": "partial",
            "runs_as_saas_only": True,
            "preferred_fabric": "sandbox_api",
        },
        "lab_access": {
            "auth_model": "product_credentials",
            "training_license": "medium_friction",
        },
        "scoring": {
            "state_validation_api_granularity": "partial",
        },
        "teardown": {
            "has_orphan_risk": True,
        },
    }
    pl = _dict_to_dataclass(ProductLababilityFacts, raw)
    assert pl.provisioning.has_sandbox_api is True
    assert pl.provisioning.sandbox_api_granularity == "partial"
    assert pl.lab_access.auth_model == "product_credentials"
    assert pl.scoring.state_validation_api_granularity == "partial"
    assert pl.teardown.has_orphan_risk is True


def test_reconstruct_instructional_value_facts_with_numeric_range():
    """InstructionalValueFacts.market_demand has nested NumericRange fields
    and a signals dict of SignalEvidence. Reconstruction handles both."""
    from backend.intelligence import _dict_to_dataclass
    from models import InstructionalValueFacts, NumericRange, SignalEvidence

    raw = {
        "market_demand": {
            "install_base": {
                "low": 40_000, "high": 50_000,
                "confidence": "confirmed",
            },
            "cert_bodies_mentioning": ["CompTIA", "SANS"],
            "signals": {
                "install_base_scale": {
                    "present": True,
                    "observation": "~50K specialists documented in vendor earnings call",
                    "confidence": "confirmed",
                },
            },
        },
        "product_complexity": {
            "description": "Multi-system cybersecurity platform.",
            "signals": {},
        },
    }
    iv = _dict_to_dataclass(InstructionalValueFacts, raw)
    assert isinstance(iv.market_demand.install_base, NumericRange)
    assert iv.market_demand.install_base.low == 40_000
    assert iv.market_demand.install_base.confidence == "confirmed"
    assert iv.market_demand.cert_bodies_mentioning == ["CompTIA", "SANS"]
    assert isinstance(iv.market_demand.signals["install_base_scale"], SignalEvidence)
    assert iv.market_demand.signals["install_base_scale"].present is True


def test_reconstruct_graded_signal_list():
    """list[GradedSignal] reconstruction — each dict in the list becomes
    a GradedSignal dataclass instance."""
    from backend.intelligence import _dict_to_dataclass
    from models import GradedSignal

    raw = [
        {"signal_category": "multi_vm_architecture", "strength": "strong",
         "evidence_text": "Multi-VM labs confirmed", "confidence": "confirmed",
         "color": "green"},
        {"signal_category": "deep_configuration", "strength": "moderate",
         "evidence_text": "Many configuration options", "confidence": "indicated",
         "color": "green"},
    ]
    # GradedSignal is flat; reconstruct each element directly
    out = [_dict_to_dataclass(GradedSignal, g) for g in raw]
    assert len(out) == 2
    assert all(isinstance(g, GradedSignal) for g in out)
    assert out[0].signal_category == "multi_vm_architecture"
    assert out[0].strength == "strong"
    assert out[1].strength == "moderate"


def test_reconstruct_passes_unknown_keys():
    """Extra keys in the dict that aren't fields of the dataclass must be
    silently ignored so legacy caches don't crash reconstruction."""
    from backend.intelligence import _dict_to_dataclass
    from models import GradedSignal

    raw = {
        "signal_category": "x", "strength": "strong", "evidence_text": "",
        "confidence": "inferred", "color": "green",
        "_legacy_field_no_longer_in_schema": "oops",  # should not crash
    }
    g = _dict_to_dataclass(GradedSignal, raw)
    assert g.signal_category == "x"
    assert g.strength == "strong"


def test_reconstruct_handles_none_and_missing():
    """None input returns a default-constructed dataclass. Missing fields
    get their default values."""
    from backend.intelligence import _dict_to_dataclass
    from models import ProductLababilityFacts

    # None → defaults
    pl = _dict_to_dataclass(ProductLababilityFacts, None)
    assert pl.provisioning.has_sandbox_api is False

    # Partial dict → missing fields default, present fields populated
    pl = _dict_to_dataclass(ProductLababilityFacts, {
        "provisioning": {"has_sandbox_api": True},
    })
    assert pl.provisioning.has_sandbox_api is True
    assert pl.provisioning.sandbox_api_granularity == ""  # default
    assert pl.lab_access.auth_model == ""  # untouched default


def test_reconstruct_round_trip_preserves_identity():
    """asdict() → _dict_to_dataclass() round-trip preserves every field
    value. Confirms the reconstruction is lossless for the types the
    Score layer consumes."""
    from dataclasses import asdict
    from backend.intelligence import _dict_to_dataclass
    from models import ProductLababilityFacts, ProvisioningFacts

    original = ProductLababilityFacts(
        provisioning=ProvisioningFacts(
            has_sandbox_api=True,
            sandbox_api_granularity="rich",
            runs_as_installable=False,
            runs_as_saas_only=True,
            supported_host_os=["linux", "windows"],
            preferred_fabric="sandbox_api",
            preferred_fabric_rationale="SaaS product with rich API",
        ),
    )
    roundtrip = _dict_to_dataclass(ProductLababilityFacts, asdict(original))
    assert roundtrip.provisioning.has_sandbox_api is True
    assert roundtrip.provisioning.sandbox_api_granularity == "rich"
    assert roundtrip.provisioning.supported_host_os == ["linux", "windows"]
    assert roundtrip.provisioning.preferred_fabric == "sandbox_api"
    assert roundtrip.provisioning.preferred_fabric_rationale == "SaaS product with rich API"


# ── Phase B: rescore_products_from_saved_facts — pure-Python rescore ────────
#
# Frank 2026-04-16: Stage 2 of the tiered versioning work.  When
# SCORING_MATH_VERSION bumps (rules change) but RESEARCH_SCHEMA_VERSION is
# stable, we must be able to rescore cached analyses WITHOUT re-running
# Claude research — reconstruct facts from the saved dict, run the pure-
# Python pillar scorers, write fresh scores back.  Zero Claude calls,
# millisecond execution, intelligence preserved.


def _minimal_analysis_with_one_product() -> dict:
    """Build a minimal saved-analysis dict good enough to exercise rescore.

    Uses a clean installable product so Pillar 1 Provisioning earns the
    canonical 'Runs in VM' signal.  Pillar 2 has an empty rubric_grades
    dict (no graded signals), which exercises the 'use saved grades
    directly' branch (regrade=False).
    """
    return {
        "company": "RescoreTestCo",
        "organization_type": "Software",
        "products": [{
            "name": "RescoreWidget",
            "category": "DevOps / Developer Tooling",
            "subcategory": "",
            "product_labability_facts": {
                "provisioning": {
                    "runs_as_installable": True,
                    "supported_host_os": ["linux"],
                    "preferred_fabric": "hyper_v",
                },
                "lab_access": {},
                "scoring": {},
                "teardown": {},
            },
            "instructional_value_facts": {},
            "rubric_grades": {},
            "fit_score": {},
            "acv_potential": {},
        }],
        "customer_fit_facts": {},
        "customer_fit_rubric_grades": {},
        "contacts": [],
    }


def test_rescore_writes_fresh_pillar_1_score():
    """After rescore, the product dict has a non-empty Pillar 1 score
    with a positive raw_total for a clean installable product."""
    from backend.intelligence import rescore_products_from_saved_facts

    analysis = _minimal_analysis_with_one_product()
    count = rescore_products_from_saved_facts(analysis, regrade=False)

    assert count == 1
    product = analysis["products"][0]
    pl = product["fit_score"]["product_labability"]
    # Pillar 1 ran — has a populated PillarScore with dimensions and positive total
    assert pl is not None
    assert pl.get("score", 0) > 0
    assert len(pl.get("dimensions", [])) == 4  # Prov, Access, Scoring, Teardown


def test_rescore_skips_product_missing_fact_drawer():
    """Products without a Pillar 1 fact drawer (legacy records) are
    skipped — caller handles re-research separately."""
    from backend.intelligence import rescore_products_from_saved_facts

    analysis = {
        "company": "LegacyCo",
        "organization_type": "Software",
        "products": [{
            "name": "LegacyProduct",
            "category": "Unknown",
            # no product_labability_facts key at all
            "fit_score": {},
        }],
        "customer_fit_facts": {},
        "customer_fit_rubric_grades": {},
    }

    count = rescore_products_from_saved_facts(analysis, regrade=False)
    assert count == 0
    # Legacy product untouched
    assert "product_labability" not in (analysis["products"][0].get("fit_score") or {}) or \
        not analysis["products"][0]["fit_score"].get("product_labability")


def test_rescore_derives_orchestration_method():
    """Rescore writes a fresh orchestration_method derived from facts —
    not the stale saved value."""
    from backend.intelligence import rescore_products_from_saved_facts

    analysis = _minimal_analysis_with_one_product()
    # Start with a stale / wrong orchestration_method
    analysis["products"][0]["orchestration_method"] = "STALE_VALUE"

    rescore_products_from_saved_facts(analysis, regrade=False)

    # Fresh derivation ran — stale string was replaced
    assert analysis["products"][0]["orchestration_method"] != "STALE_VALUE"


def test_rescore_assigns_verdict():
    """Rescore runs assign_verdict so the product ends with a populated
    verdict reflecting the fresh fit_score + ACV tier."""
    from backend.intelligence import rescore_products_from_saved_facts

    analysis = _minimal_analysis_with_one_product()
    rescore_products_from_saved_facts(analysis, regrade=False)

    verdict = analysis["products"][0].get("verdict")
    assert verdict is not None  # assign_verdict returned a Verdict dict


def test_rescore_does_not_make_claude_calls_when_regrade_false():
    """regrade=False must be pure Python — no imports of rubric_grader
    should execute any Claude-calling path.  Enforced by asserting that
    with an empty rubric_grades dict, the rescore still completes and
    product pillar_2 score exists (using the empty-grades baseline)."""
    from backend.intelligence import rescore_products_from_saved_facts

    analysis = _minimal_analysis_with_one_product()
    # Explicitly no grades saved
    analysis["products"][0]["rubric_grades"] = {}

    count = rescore_products_from_saved_facts(analysis, regrade=False)
    assert count == 1

    product = analysis["products"][0]
    iv = product["fit_score"].get("instructional_value")
    # Pillar 2 scorer ran on empty grades — produces baseline (not None)
    assert iv is not None


def test_rescore_returns_zero_on_empty_products_list():
    """An analysis with no products returns 0 rescored."""
    from backend.intelligence import rescore_products_from_saved_facts

    analysis = {
        "company": "EmptyCo",
        "organization_type": "Software",
        "products": [],
        "customer_fit_facts": {},
        "customer_fit_rubric_grades": {},
    }
    assert rescore_products_from_saved_facts(analysis, regrade=False) == 0


def test_rescore_preserves_non_scored_fields():
    """Rescore must not wipe product name, category, URL, description —
    intelligence compounds, only the score-layer values are refreshed."""
    from backend.intelligence import rescore_products_from_saved_facts

    analysis = _minimal_analysis_with_one_product()
    analysis["products"][0]["product_url"] = "https://example.com/widget"
    analysis["products"][0]["description"] = "Preserved description text."

    rescore_products_from_saved_facts(analysis, regrade=False)

    p = analysis["products"][0]
    assert p["name"] == "RescoreWidget"
    assert p["category"] == "DevOps / Developer Tooling"
    assert p["product_url"] == "https://example.com/widget"
    assert p["description"] == "Preserved description text."
