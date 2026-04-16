"""Configuration for the Skillable Intelligence Platform.

Environment variables are read at import time. Startup validation ensures
the app fails fast with clear messages rather than crashing mid-analysis.

Updated for the Prompt Generation System — validates scoring_config.py
and the per-pillar Python scorers instead of a static prompt file.
"""

import logging
import os
import sys

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Operational constants — single source for all modules ──
CACHE_TTL_DAYS = 45
MAX_SCORING_WORKERS = 10  # bumped from 6 -> 10 on 2026-04-07 for Deep Dive throughput
SCORING_TIMEOUT_SECS = 300
MAX_SEARCH_WORKERS = 12
MAX_FETCH_WORKERS = 10

# ── Framework version timestamp ──
# Updated whenever scoring_config.py, knowledge files, or prompt template change.
# Compared against cached scores to determine if re-scoring is needed.
import os as _os
from pathlib import Path as _Path

def _get_framework_last_modified() -> str:
    """Get the most recent modification time across all framework files.

    If any of these files are newer than a cached score, the score is stale
    and should be regenerated from cached research.
    """
    framework_files = [
        _Path(__file__).parent / "scoring_config.py",
        _Path(__file__).parent / "prompts" / "discovery.txt",
        # skillable_capabilities.json retired 2026-04-16 — SKILLABLE_CAPABILITIES
        # now lives exclusively in scoring_config.py as the Python tuple.
        _Path(__file__).parent / "knowledge" / "delivery_patterns.json",
        _Path(__file__).parent / "knowledge" / "competitors.json",
        _Path(__file__).parent / "knowledge" / "contact_guidance.json",
        _Path(__file__).parent / "benchmarks.json",
    ]
    latest = 0
    for f in framework_files:
        if f.exists():
            mtime = _os.path.getmtime(f)
            if mtime > latest:
                latest = mtime
    from datetime import datetime, timezone
    return datetime.fromtimestamp(latest, tz=timezone.utc).isoformat()


FRAMEWORK_LAST_MODIFIED = _get_framework_last_modified()

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
        errors.append(f"benchmarks_new.json not found at {_BENCHMARKS_PATH}")

    # Discovery prompt (used by scorer.discover_products_with_claude)
    discovery_path = os.path.join(_PROMPTS_DIR, "discovery.txt")
    if not os.path.exists(discovery_path):
        errors.append(f"Discovery prompt not found: {discovery_path}")

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

    if not SERPER_API_KEY:
        log.info("SERPER_API_KEY not set — web searches will use DuckDuckGo fallback")

    if errors:
        for err in errors:
            log.critical("STARTUP ERROR: %s", err)
        print("\n=== STARTUP VALIDATION FAILED ===", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    log.info("Startup validation passed — API key set, scoring config valid")
