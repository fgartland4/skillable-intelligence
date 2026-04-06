"""Category 2: Prompt Generation System

Guiding Principles: Define-Once Principle, End-to-End Principle

Validates the three-layer Prompt Generation System works correctly.

See docs/Test-Plan.md for the full test strategy.
"""

import re
import scoring_config as cfg
from prompt_generator import generate_scoring_prompt


def test_prompt_generates_without_error():
    """The generator must produce a prompt without errors."""
    prompt = generate_scoring_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_no_unreplaced_placeholders():
    """Every {PLACEHOLDER} must be filled — no orphans."""
    prompt = generate_scoring_prompt()
    orphans = re.findall(r"\{[A-Z][A-Z0-9_]+\}", prompt)
    assert len(orphans) == 0, f"Unreplaced placeholders: {orphans}"


def test_prompt_contains_all_pillar_names():
    """Generated prompt must contain all three Pillar names."""
    prompt = generate_scoring_prompt()
    for pillar in cfg.PILLARS:
        assert pillar.name in prompt, f"'{pillar.name}' not in prompt"


def test_prompt_contains_all_dimension_names():
    """Generated prompt must contain all 12 dimension names."""
    prompt = generate_scoring_prompt()
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            assert dim.name in prompt, f"'{dim.name}' not in prompt"


def test_prompt_contains_all_badge_names():
    """Every badge in the config must appear in the generated prompt."""
    prompt = generate_scoring_prompt()
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            for badge in dim.badges:
                assert badge.name in prompt, (
                    f"Badge '{badge.name}' ({pillar.name}/{dim.name}) not in prompt"
                )


def test_prompt_contains_locked_vocabulary():
    """Locked vocabulary canonical terms must be in the generated prompt."""
    prompt = generate_scoring_prompt()
    for lt in cfg.LOCKED_VOCABULARY:
        assert lt.use_this in prompt, f"'{lt.use_this}' not in prompt"


def test_prompt_does_not_contain_forbidden_vocabulary():
    """Forbidden terms must not appear outside the vocabulary table."""
    prompt = generate_scoring_prompt()
    vocab_start = prompt.find("Locked Vocabulary")
    if vocab_start == -1:
        vocab_start = prompt.find("LOCKED_VOCABULARY")
    before_vocab = prompt[:vocab_start] if vocab_start > 0 else ""

    forbidden = [
        "Composite Score", "Lab Score", "Technical Orchestrability",
        "Training Ecosystem", "Lab Maturity",
    ]
    for term in forbidden:
        assert term not in before_vocab, f"Forbidden '{term}' found in prompt"
