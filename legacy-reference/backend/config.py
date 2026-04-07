"""Configuration for the Skillable Intelligence Platform.

Environment variables are read at import time. Required values are validated
at startup so the app fails fast with a clear message rather than crashing
with an unhelpful error minutes into an analysis.
"""

import logging
import os
import sys

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Optional: Serper.dev API key for Google search results (serper.dev/dashboard)
# When set, all web searches use Serper instead of DuckDuckGo.
# Add SERPER_API_KEY=your_key to .env
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "results")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Startup validation — called once when app.py imports this module and then
# explicitly via validate_startup().  Logs warnings for optional issues,
# raises SystemExit for critical ones.
# ---------------------------------------------------------------------------

_BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), "benchmarks.json")
_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def validate_startup() -> None:
    """Validate that all required config, files, and directories exist.

    Call this once during app initialization (e.g. in app.py after imports).
    Exits with a clear error message if anything critical is missing.
    """
    errors = []

    # Required: Anthropic API key
    if not ANTHROPIC_API_KEY:
        errors.append(
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env or set it as an "
            "environment variable. Without it, all scoring and discovery calls will fail."
        )

    # Required: benchmarks.json (loaded by scorer.py at import time)
    if not os.path.exists(_BENCHMARKS_PATH):
        errors.append(
            f"benchmarks.json not found at {_BENCHMARKS_PATH}. "
            "This file contains customer calibration data required for scoring."
        )

    # Required: prompt files
    for prompt_file in ["discovery.txt", "product_scoring.txt"]:
        path = os.path.join(_PROMPTS_DIR, prompt_file)
        if not os.path.exists(path):
            errors.append(f"Required prompt file not found: {path}")

    # Optional: Serper API key (DuckDuckGo fallback works without it)
    if not SERPER_API_KEY:
        log.info("SERPER_API_KEY not set — web searches will use DuckDuckGo fallback")

    # Report errors
    if errors:
        for err in errors:
            log.critical("STARTUP ERROR: %s", err)
        print("\n=== STARTUP VALIDATION FAILED ===", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)

    log.info("Startup validation passed — API key set, prompts found, benchmarks loaded")
