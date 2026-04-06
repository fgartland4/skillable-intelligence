"""Category 2: Prompt Generation System

Guiding Principles: Define-Once Principle, End-to-End Principle

Validates that the three-layer Prompt Generation System works correctly:
Configuration flows into Template, Template produces a complete prompt, no gaps.
Proves the Define-Once Principle works at the code level.

See docs/Test-Plan.md for the full test strategy.
"""

import scoring_config as cfg
from prompt_generator import generate_scoring_prompt


# ── Generation succeeds ─────────────────────────────────────────────────────

def test_prompt_generates_without_error():
    """The generator must produce a prompt from config + template without errors."""
    prompt = generate_scoring_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0


# ── No orphan placeholders ──────────────────────────────────────────────────

def test_no_unreplaced_placeholders():
    """Every {PLACEHOLDER} in the template must be filled by the config.

    An unreplaced placeholder means the config is missing something the
    template expects — the AI would receive broken instructions.
    """
    prompt = generate_scoring_prompt()
    import re
    orphans = re.findall(r"\{[A-Z_]+\}", prompt)
    assert len(orphans) == 0, f"Unreplaced placeholders found: {orphans}"


# ── Pillar names present ────────────────────────────────────────────────────

def test_prompt_contains_all_pillar_names():
    """Generated prompt must contain all three Pillar names."""
    prompt = generate_scoring_prompt()
    for pillar in cfg.PILLARS:
        assert pillar.name in prompt, (
            f"Pillar name '{pillar.name}' not found in generated prompt"
        )


# ── Dimension names present ─────────────────────────────────────────────────

def test_prompt_contains_all_dimension_names():
    """Generated prompt must contain all 12 dimension names."""
    prompt = generate_scoring_prompt()
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            assert dim.name in prompt, (
                f"Dimension '{dim.name}' ({pillar.name}) not found in generated prompt"
            )


# ── Badge names present ─────────────────────────────────────────────────────

def test_prompt_contains_all_badge_names():
    """Every badge defined in the config must appear in the generated prompt."""
    prompt = generate_scoring_prompt()
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            for badge in getattr(dim, "badges", []):
                assert badge.name in prompt, (
                    f"Badge '{badge.name}' ({pillar.name}/{dim.name}) "
                    f"not found in generated prompt"
                )


# ── Locked vocabulary present ───────────────────────────────────────────────

def test_prompt_contains_locked_vocabulary():
    """The locked vocabulary table must be present in the generated prompt."""
    prompt = generate_scoring_prompt()
    for entry in cfg.LOCKED_VOCABULARY:
        assert entry["use"] in prompt, (
            f"Locked vocabulary term '{entry['use']}' not found in generated prompt"
        )


def test_prompt_does_not_contain_forbidden_vocabulary():
    """Forbidden vocabulary terms must not appear outside the vocabulary table."""
    prompt = generate_scoring_prompt()
    # Find the vocabulary table section and exclude it from the check
    # The table legitimately lists "not this" terms
    vocab_section_start = prompt.find("Locked Vocabulary")
    if vocab_section_start == -1:
        vocab_section_start = prompt.find("LOCKED_VOCABULARY")

    # Check the prompt BEFORE the vocabulary table for forbidden terms
    prompt_before_vocab = prompt[:vocab_section_start] if vocab_section_start > 0 else ""

    forbidden_standalone = [
        "Composite Score", "Lab Score", "Technical Orchestrability",
        "Training Ecosystem", "Lab Maturity",
    ]
    for term in forbidden_standalone:
        assert term not in prompt_before_vocab, (
            f"Forbidden term '{term}' found in generated prompt outside vocabulary table"
        )


# ── Define-Once proof ───────────────────────────────────────────────────────

def test_config_change_propagates_to_prompt():
    """Changing a value in config must change the generated prompt.

    This proves the Define-Once Principle works — one change, one place,
    propagates everywhere.
    """
    prompt_before = generate_scoring_prompt()

    # Temporarily modify a pillar weight
    original_weight = cfg.PILLARS[0].weight
    try:
        cfg.PILLARS[0].weight = 99
        prompt_after = generate_scoring_prompt()
        assert prompt_before != prompt_after, (
            "Changing config weight did not change the generated prompt — "
            "Define-Once is broken"
        )
        assert "99" in prompt_after, (
            "Modified weight (99) not found in generated prompt"
        )
    finally:
        # Restore original weight
        cfg.PILLARS[0].weight = original_weight
