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
