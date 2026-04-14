"""Retrofit cached discoveries with the new holistic ACV (Option 2).

Per Frank 2026-04-13: scans all cached discovery records and runs
`estimate_holistic_acv()` on each one using the cached discovery data
as input — no full re-research, just one targeted Claude call per
company that produces the new range + confidence + rationale + drivers
+ caveats.

Cost shape: ~1 Claude call per company × N companies ≈ N × ~$0.30. For
the current ~308 cached records: ~$90-120 total. Wall time with
parallelism: ~30-60 minutes.

Usage:
    python scripts/retrofit_acv.py                     # dry-run (count + cost estimate)
    python scripts/retrofit_acv.py --execute           # run on all cached records
    python scripts/retrofit_acv.py --execute --limit 5 # only first 5 (test before going wide)
    python scripts/retrofit_acv.py --execute --company "Nutanix"  # one specific company
    python scripts/retrofit_acv.py --execute --skip-existing       # skip records that already have _holistic_acv
"""

from __future__ import annotations

import sys
import os
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

from storage import _COMPANY_DIR, save_discovery  # noqa: E402

_DEFAULT_PARALLELISM = 5  # magic-allowed: parallel-Claude-call-throttle


def _load_all_discoveries() -> list[dict]:
    out = []
    for f in os.listdir(_COMPANY_DIR):
        if not (f.startswith("discovery_") and f.endswith(".json")):
            continue
        if ".archived-" in f:
            continue
        path = os.path.join(_COMPANY_DIR, f)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            out.append(d)
        except Exception as e:
            print(f"  WARN: failed to load {f}: {e}")
    return out


def _retrofit_one(disc: dict) -> tuple[str, dict | None, str | None]:
    """Run holistic ACV on one cached discovery. Returns (name, result, error)."""
    from researcher import estimate_holistic_acv  # local import — needs env loaded
    name = disc.get("company_name") or ""
    if not name:
        return ("?", None, "no company_name on record")
    try:
        result = estimate_holistic_acv(name, disc)
        return (name, result, None)
    except Exception as e:
        return (name, None, str(e))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="actually run (default: dry-run)")
    parser.add_argument("--limit", type=int, default=0, help="only process the first N records")
    parser.add_argument("--company", type=str, default="", help="only process records matching this company name (substring)")
    parser.add_argument("--skip-existing", action="store_true", help="skip records that already have _holistic_acv populated")
    parser.add_argument("--parallel", type=int, default=_DEFAULT_PARALLELISM, help=f"parallel Claude calls (default {_DEFAULT_PARALLELISM})")
    args = parser.parse_args()

    print(f"Loading discoveries from {_COMPANY_DIR}...")
    discoveries = _load_all_discoveries()
    print(f"  loaded {len(discoveries)} records")

    # Apply filters.
    if args.company:
        needle = args.company.lower()
        discoveries = [d for d in discoveries if needle in (d.get("company_name") or "").lower()]
        print(f"  filtered by company '{args.company}' → {len(discoveries)} records")

    if args.skip_existing:
        before = len(discoveries)
        discoveries = [
            d for d in discoveries
            if not (d.get("_holistic_acv") or {}).get("rationale")
        ]
        print(f"  skip-existing: {before} → {len(discoveries)} records")

    if args.limit and args.limit > 0:
        discoveries = discoveries[: args.limit]
        print(f"  limit applied → {len(discoveries)} records")

    # Cost estimate.
    n = len(discoveries)
    est_cost_low = n * 0.20  # magic-allowed: cost-estimator-low-bound
    est_cost_high = n * 0.50  # magic-allowed: cost-estimator-high-bound
    est_minutes_low = max(1, n // (args.parallel * 4))   # magic-allowed: time-estimator-low-bound
    est_minutes_high = max(2, n // (args.parallel * 2))  # magic-allowed: time-estimator-high-bound
    print()
    print(f"PLAN: retrofit holistic ACV on {n} records (parallel={args.parallel})")
    print(f"  estimated cost:  ${est_cost_low:.0f}-${est_cost_high:.0f}")
    print(f"  estimated time:  {est_minutes_low}-{est_minutes_high} min")
    print()

    if not args.execute:
        print("DRY RUN — no Claude calls made, no changes saved.")
        print("Re-run with --execute to actually retrofit.")
        return

    print("Executing retrofit...")
    started = datetime.now(timezone.utc)
    succeeded = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futures = {ex.submit(_retrofit_one, d): d for d in discoveries}
        for fut in as_completed(futures):
            disc = futures[fut]
            name, result, error = fut.result()
            if error:
                failed += 1
                print(f"  FAIL  {name}: {error}")
                continue
            if not result:
                failed += 1
                print(f"  FAIL  {name}: empty result")
                continue
            disc["_holistic_acv"] = result
            try:
                save_discovery(disc.get("discovery_id"), disc)
                succeeded += 1
                lo = result.get("acv_low") or 0
                hi = result.get("acv_high") or 0
                conf = result.get("confidence") or "?"
                print(f"  OK    {name}: ${lo:,}-${hi:,} ({conf})")
            except Exception as e:
                failed += 1
                print(f"  FAIL  {name}: save failed: {e}")

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    print()
    print(f"Done in {elapsed/60:.1f} min — {succeeded} succeeded, {failed} failed.")


if __name__ == "__main__":
    main()
