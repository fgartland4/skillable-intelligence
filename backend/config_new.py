"""Configuration for the Skillable Intelligence Platform.

Environment variables are read at import time. Startup validation ensures
the app fails fast with clear messages rather than crashing mid-analysis.

Updated for the Prompt Generation System — validates scoring_config.py
and scoring_template.md instead of the old static product_scoring.txt.
"""

import logging
import os
import sys

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data_new")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Operational constants — single source for all modules ──
CACHE_TTL_DAYS = 45
MAX_SCORING_WORKERS = 6
SCORING_TIMEOUT_SECS = 300
MAX_SEARCH_WORKERS = 12
MAX_FETCH_WORKERS = 10

_BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), "benchmarks.json")
_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def validate_startup() -> None:
    """Validate that all required config, files, and directories exist."""
    errors = []

    if not ANTHROPIC_API_KEY:
        errors.append(
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env or set it as an "
            "environment variable."
        )

    if not os.path.exists(_BENCHMARKS_PATH):
        errors.append(f"benchmarks.json not found at {_BENCHMARKS_PATH}")

    # Discovery prompt (still a static file — not part of Prompt Generation System)
    discovery_path = os.path.join(_PROMPTS_DIR, "discovery.txt")
    if not os.path.exists(discovery_path):
        errors.append(f"Discovery prompt not found: {discovery_path}")

    # Scoring template (part of Prompt Generation System)
    template_path = os.path.join(_PROMPTS_DIR, "scoring_template.md")
    if not os.path.exists(template_path):
        errors.append(f"Scoring template not found: {template_path}")

    # Validate scoring_config loads without error
    try:
        from backend import scoring_config as cfg
        # Quick structural check
        if len(cfg.PILLARS) != 3:
            errors.append(f"scoring_config.py has {len(cfg.PILLARS)} pillars, expected 3")
        pillar_weight_sum = sum(p.weight for p in cfg.PILLARS)
        if pillar_weight_sum != 100:
            errors.append(f"Pillar weights sum to {pillar_weight_sum}, expected 100")
    except Exception as e:
        errors.append(f"scoring_config.py failed to load: {e}")

    # Validate prompt generation works
    try:
        from prompt_generator import generate_scoring_prompt, validate_generated_prompt
        prompt = generate_scoring_prompt()
        unresolved = validate_generated_prompt(prompt)
        if unresolved:
            errors.append(f"Prompt generation has unresolved placeholders: {unresolved}")
    except Exception as e:
        errors.append(f"Prompt generation failed: {e}")

    if not SERPER_API_KEY:
        log.info("SERPER_API_KEY not set — web searches will use DuckDuckGo fallback")

    if errors:
        for err in errors:
            log.critical("STARTUP ERROR: %s", err)
        print("\n=== STARTUP VALIDATION FAILED ===", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    log.info("Startup validation passed — API key set, scoring config valid, prompt generates cleanly")
