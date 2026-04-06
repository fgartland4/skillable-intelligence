"""Category 7: Locked Vocabulary Enforcement

Guiding Principle: GP4 (Self-Evident Design)

Validates correct terms everywhere. No legacy vocabulary.

See docs/Test-Plan.md for the full test strategy.
"""

import scoring_config as cfg
from prompt_generator import generate_scoring_prompt


# ── Config field names ──────────────────────────────────────────────────────

def test_config_uses_fit_score_not_composite():
    """Prompt should say 'Fit Score' not 'Composite Score'."""
    prompt = generate_scoring_prompt()
    assert "Fit Score" in prompt
    vocab_start = prompt.find("Locked Vocabulary")
    before_vocab = prompt[:vocab_start] if vocab_start > 0 else prompt
    assert "Composite Score" not in before_vocab


def test_config_uses_customer_fit_not_organizational_readiness():
    """Third pillar must be 'Customer Fit'."""
    pillar_names = {p.name for p in cfg.PILLARS}
    assert "Customer Fit" in pillar_names
    assert "Organizational Readiness" not in pillar_names


def test_config_uses_market_demand():
    """Dimension must be 'Market Demand', not 'Market Fit' or 'Market Readiness'."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    dim_names = {d.name for d in iv.dimensions}
    assert "Market Demand" in dim_names
    assert "Market Fit" not in dim_names
    assert "Market Readiness" not in dim_names


def test_config_uses_product_complexity():
    """Dimension must be 'Product Complexity', not 'Difficult to Master'."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    dim_names = {d.name for d in iv.dimensions}
    assert "Product Complexity" in dim_names
    assert "Difficult to Master" not in dim_names


def test_config_uses_mastery_stakes():
    """Dimension must be 'Mastery Stakes', not 'Mastery Matters'."""
    iv = next(p for p in cfg.PILLARS if p.name == "Instructional Value")
    dim_names = {d.name for d in iv.dimensions}
    assert "Mastery Stakes" in dim_names
    assert "Mastery Matters" not in dim_names


def test_deployment_model_uses_installable():
    """Data value must be 'installable', not 'self-hosted'."""
    assert "installable" in cfg.DEPLOYMENT_MODELS
    assert "self-hosted" not in cfg.DEPLOYMENT_MODELS


# ── Vocabulary table consistency ────────────────────────────────────────────

def test_vocabulary_table_complete():
    """Locked vocabulary must have entries for all key terms."""
    use_terms = {lt.use_this for lt in cfg.LOCKED_VOCABULARY}
    required = {
        "Fit Score", "Product Labability", "Instructional Value",
        "Customer Fit", "Product Complexity", "Mastery Stakes",
        "Market Demand", "Provisioning", "Lab Access", "Teardown",
    }
    missing = required - use_terms
    assert len(missing) == 0, f"Locked vocabulary missing: {missing}"
