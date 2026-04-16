"""Run flagship Deep Dives on companies that don't have any yet.

Takes the top N companies (by holistic ACV midpoint, descending) from
the without-Deep-Dive bucket, picks each company's flagship product,
and runs intelligence.score() for just that product.

Leaves companies that already have a Deep Dive untouched.
Flagship pick order: product_relationship="flagship" → highest
rough_labability_score → first in the list.

Usage:
    python backend/scripts/run_flagship_deep_dives.py [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Make backend/ importable — add BOTH the project root (so `from backend import ...`
# works for modules like core.py) AND backend/ itself (so `import intelligence`,
# `from storage import ...` work).
_BACKEND = Path(__file__).resolve().parents[1]
_ROOT = _BACKEND.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_BACKEND))

import intelligence
from storage import list_discoveries, list_analyses

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("flagship_runner")


def _companies_without_deep_dive() -> list[dict]:
    """Return discoveries that have no analysis attached."""
    analyses_by_disc = set()
    for a in list_analyses():
        did = a.get("discovery_id")
        if did:
            analyses_by_disc.add(did)

    out = []
    for disc in list_discoveries():
        did = disc.get("discovery_id")
        if did and did not in analyses_by_disc:
            out.append(disc)
    return out


def _acv_midpoint(disc: dict) -> int:
    """Extract the holistic ACV midpoint for sorting."""
    h = disc.get("_holistic_acv") or {}
    low = int(h.get("acv_low") or 0)
    high = int(h.get("acv_high") or 0)
    return (low + high) // 2


def _pick_flagship(disc: dict) -> dict | None:
    """Choose the flagship product for this company.

    Order: product_relationship="flagship" → highest rough_labability_score
    → first product in the list. Returns None if no products.
    """
    products = disc.get("products") or []
    if not products:
        return None

    # 1) Explicit flagship
    for p in products:
        if p.get("product_relationship") == "flagship":
            return p

    # 2) Highest rough labability score
    scored = [p for p in products if p.get("rough_labability_score") is not None]
    if scored:
        return max(scored, key=lambda p: int(p.get("rough_labability_score") or 0))

    # 3) First product
    return products[0]


def _run_one(disc: dict) -> tuple[str, str, bool, str]:
    """Run Deep Dive on one company's flagship. Returns (company_name, product_name, ok, detail)."""
    company_name = disc.get("company_name", "")
    discovery_id = disc.get("discovery_id", "")

    flagship = _pick_flagship(disc)
    if flagship is None:
        return company_name, "", False, "no products in discovery"

    product_name = flagship.get("name", "")
    t0 = time.time()
    try:
        analysis_id, new_names = intelligence.score(
            company_name,
            selected_products=[flagship],
            discovery_id=discovery_id,
            discovery_data=disc,
        )
        elapsed = time.time() - t0
        detail = f"analysis_id={analysis_id} newly_scored={len(new_names)} {elapsed:.1f}s"
        return company_name, product_name, True, detail
    except Exception as e:
        elapsed = time.time() - t0
        return company_name, product_name, False, f"error after {elapsed:.1f}s: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100,
                        help="How many flagship Deep Dives to run (default 100)")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="Parallel Deep Dives (default 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List the companies that would be run, don't actually run")
    args = parser.parse_args()

    log.info("Loading discoveries without Deep Dives...")
    candidates = _companies_without_deep_dive()
    log.info("Found %d companies without Deep Dives out of %d total discoveries",
             len(candidates), len(list_discoveries()))

    # Sort by ACV midpoint descending
    candidates.sort(key=_acv_midpoint, reverse=True)
    targets = candidates[: args.limit]

    log.info("Will run %d flagship Deep Dives (concurrency=%d)",
             len(targets), args.concurrency)

    if args.dry_run:
        for i, disc in enumerate(targets, 1):
            flagship = _pick_flagship(disc)
            flagship_name = (flagship or {}).get("name", "(no products)")
            acv = _acv_midpoint(disc)
            log.info("[%3d] %s — flagship: %s — ACV midpoint: $%s",
                     i, disc.get("company_name", ""), flagship_name, f"{acv:,}")
        return

    successes = 0
    failures = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(_run_one, disc): disc for disc in targets}
        for i, fut in enumerate(as_completed(futures), 1):
            disc = futures[fut]
            try:
                company, product, ok, detail = fut.result()
            except Exception as e:
                company = disc.get("company_name", "?")
                product = ""
                ok = False
                detail = f"runner exception: {e}"

            if ok:
                successes += 1
                log.info("[%3d/%d] OK   %s / %s — %s",
                         i, len(targets), company, product, detail)
            else:
                failures += 1
                log.warning("[%3d/%d] FAIL %s / %s — %s",
                            i, len(targets), company, product, detail)

    elapsed = time.time() - start
    log.info("=" * 72)
    log.info("Completed %d/%d successful, %d failed, wall time %.1f min",
             successes, len(targets), failures, elapsed / 60)


if __name__ == "__main__":
    main()
