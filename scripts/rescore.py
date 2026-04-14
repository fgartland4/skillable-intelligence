"""Re-score cached analyses without re-running researcher.

Usage:
    python scripts/rescore.py                    # re-score ALL cached analyses
    python scripts/rescore.py "Cisco"            # re-score one company by name
    python scripts/rescore.py "Cisco" "Google"   # re-score specific companies

What it does:
    1. Loads each company's existing analysis + discovery data
    2. Re-runs Pillar 1 scorer (pure Python, zero API cost)
    3. Re-runs Pillar 2/3 rubric graders (Claude calls — small API cost per dimension)
    4. Re-runs ACV calculator with new guardrails
    5. Re-runs Fit Score composer and badge selector
    6. Saves the updated analysis

What it does NOT do:
    - Does NOT re-run the researcher (no new web searches, no new fact extraction)
    - Does NOT change the fact drawer (install_base, deployment_model, etc.)
    - Uses existing cached facts as the input substrate

When to use:
    - After scoring logic changes (pillar weights, caps, penalties, ACV guardrails)
    - After rubric grader prompt changes (DIY lab platform detection, etc.)
    - When SCORING_LOGIC_VERSION has been bumped
"""

import sys
import os

# Add project root to path so 'from backend import ...' works,
# AND add backend/ so direct imports like 'from intelligence import ...' work.
_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

# Load .env for API keys
from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("rescore")


def rescore_company(company_name: str) -> bool:
    """Re-score one company's cached analysis."""
    from storage import find_discovery_by_company_name, find_analysis_by_discovery_id, _normalize_company_name
    from intelligence import score

    # Find the discovery
    disc = find_discovery_by_company_name(company_name)
    if not disc:
        log.warning("No discovery found for '%s'", company_name)
        return False

    disc_id = disc.get("discovery_id", "")
    real_name = disc.get("company_name", company_name)
    log.info("Found discovery for %s (disc_id=%s, %d products)",
             real_name, disc_id, len(disc.get("products", [])))

    # Find existing analysis
    analysis = find_analysis_by_discovery_id(disc_id)
    if not analysis:
        log.warning("No existing analysis for %s — need a Deep Dive first", real_name)
        return False

    scored_products = analysis.get("products") or analysis.get("top_products") or []
    if not scored_products:
        log.warning("Analysis for %s has no scored products", real_name)
        return False

    log.info("Re-scoring %s (%d products)...", real_name, len(scored_products))

    # Re-run scoring pipeline
    try:
        result = score(real_name, scored_products, disc_id, discovery_data=disc)
        if result:
            log.info("Re-score complete for %s", real_name)
            return True
        else:
            log.error("Re-score returned None for %s", real_name)
            return False
    except Exception as e:
        log.error("Re-score failed for %s: %s", real_name, e)
        return False


def rescore_all() -> tuple[int, int]:
    """Re-score all cached analyses. Returns (success_count, failure_count)."""
    from storage import list_discoveries, find_analysis_by_discovery_id

    # Find all discoveries that have analyses
    companies_to_rescore = []
    seen = set()
    for disc in list_discoveries():
        disc_id = disc.get("discovery_id", "")
        name = disc.get("company_name", "")
        if not disc_id or not name:
            continue
        # Dedup by name
        from storage import _normalize_company_name
        key = _normalize_company_name(name)
        if key in seen:
            continue
        seen.add(key)
        # Only rescore if analysis exists
        analysis = find_analysis_by_discovery_id(disc_id)
        if analysis:
            companies_to_rescore.append(name)

    total = len(companies_to_rescore)
    log.info("Found %d companies with cached analyses to re-score", total)

    success = 0
    failure = 0
    for i, name in enumerate(companies_to_rescore, 1):
        log.info("--- Re-scoring %d of %d: %s ---", i, total, name)
        if rescore_company(name):
            success += 1
        else:
            failure += 1

    return success, failure


def main():
    if len(sys.argv) > 1:
        # Re-score specific companies
        for name in sys.argv[1:]:
            rescore_company(name)
    else:
        # Re-score all
        success, failure = rescore_all()
        log.info("Done. %d succeeded, %d failed.", success, failure)


if __name__ == "__main__":
    main()
