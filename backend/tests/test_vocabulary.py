"""Category 7: Locked Vocabulary Enforcement

Guiding Principle: GP4 (Self-Evident Design)

Validates that the codebase uses correct terms everywhere. No legacy vocabulary.
Self-evident design means the right words at every layer.

See docs/Test-Plan.md for the full test strategy.
"""

import os
import re

import scoring_config as cfg
from prompt_generator import generate_scoring_prompt


# Forbidden terms that must NEVER appear in new code or generated output
# (except in vocabulary tables that list them as "don't use this")
FORBIDDEN_TERMS = [
    "Composite Score",
    "Lab Score",
    "Technical Orchestrability",
    "Workflow Complexity",
    "Training Ecosystem",
    "Lab Maturity",
    "Training Motivation",
    "Content Delivery Ecosystem",
    "Content Development Capabilities",
    "Dedicated Content Dept",
    "Outsourced Content Creation",
    "Difficult to Master",
    "Mastery Matters",
    "Consequence of Failure",
    "Lab Format Opportunities",
    "Licensing & Accounts",
    "self-hosted",
]


# ── Config field names ──────────────────────────────────────────────────────

def test_config_uses_fit_score_not_composite():
    """Config should reference 'fit_score', never 'composite_score'."""
    # Check that PILLARS, verdict grid, and output template use correct term
    prompt = generate_scoring_prompt()
    # The prompt should say "Fit Score" not "Composite Score"
    assert "Fit Score" in prompt
    # "Composite Score" should not appear outside a vocabulary table
    vocab_start = prompt.find("Locked Vocabulary")
    before_vocab = prompt[:vocab_start] if vocab_start > 0 else prompt
    assert "Composite Score" not in before_vocab, (
        "'Composite Score' found in generated prompt outside vocabulary table"
    )


def test_config_uses_customer_fit_not_organizational_readiness():
    """Third pillar must be 'Customer Fit', not 'Organizational Readiness' as a pillar name."""
    pillar_names = {p.name for p in cfg.PILLARS}
    assert "Customer Fit" in pillar_names
    assert "Organizational Readiness" not in pillar_names


def test_config_uses_market_demand_not_market_fit():
    """Dimension must be 'Market Demand', not 'Market Fit' or 'Market Readiness'."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    dim_names = {d.name for d in iv.dimensions}
    assert "Market Demand" in dim_names
    assert "Market Fit" not in dim_names
    assert "Market Readiness" not in dim_names


def test_config_uses_product_complexity_not_difficult_to_master():
    """Dimension must be 'Product Complexity', not 'Difficult to Master'."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    dim_names = {d.name for d in iv.dimensions}
    assert "Product Complexity" in dim_names
    assert "Difficult to Master" not in dim_names


def test_config_uses_mastery_stakes_not_mastery_matters():
    """Dimension must be 'Mastery Stakes', not 'Mastery Matters'."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    dim_names = {d.name for d in iv.dimensions}
    assert "Mastery Stakes" in dim_names
    assert "Mastery Matters" not in dim_names


def test_deployment_model_uses_installable():
    """Deployment model data value must be 'installable', not 'self-hosted'."""
    assert "installable" in cfg.DEPLOYMENT_MODELS
    assert "self-hosted" not in cfg.DEPLOYMENT_MODELS


# ── Generated prompt vocabulary ─────────────────────────────────────────────

def test_generated_prompt_no_forbidden_terms():
    """The generated prompt must not contain forbidden vocabulary outside the vocabulary table."""
    prompt = generate_scoring_prompt()

    # Find vocabulary section to exclude it
    vocab_start = prompt.find("Locked Vocabulary")
    if vocab_start == -1:
        vocab_start = prompt.find("LOCKED_VOCABULARY")
    before_vocab = prompt[:vocab_start] if vocab_start > 0 else prompt

    for term in FORBIDDEN_TERMS:
        assert term not in before_vocab, (
            f"Forbidden term '{term}' found in generated prompt"
        )


# ── Vocabulary table internal consistency ───────────────────────────────────

def test_vocabulary_table_complete():
    """The locked vocabulary table must have entries for all key terms."""
    use_terms = {entry["use"] for entry in cfg.LOCKED_VOCABULARY}

    required = {
        "Fit Score",
        "Product Labability",
        "Instructional Value",
        "Customer Fit",
        "Product Complexity",
        "Mastery Stakes",
        "Market Demand",
        "Provisioning",
        "Lab Access",
        "Teardown",
    }

    missing = required - use_terms
    assert len(missing) == 0, f"Locked vocabulary missing entries for: {missing}"
