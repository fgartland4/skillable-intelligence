"""Compute ACV Potential for non-saturated known customers.

One-time pass (can be re-run if prompts change). For each non-saturated
known customer that has a cached discovery record, runs the holistic
ACV call with `disable_known_customer_caps=True` so the ceiling cap
doesn't kick in, and saves the result as `acv_potential` on the
discovery's `_holistic_acv` field. The anonymized calibration block
then emits both `current_acv` and `acv_potential` per stage so Claude
anchors prospects on Potential (the "what could this be" question)
instead of Current (a different question).

Saturated customers are skipped — for them, current ≈ potential, so
the anchor is already correct.

Usage:
    python scripts/compute_customer_potentials.py              # dry run
    python scripts/compute_customer_potentials.py --execute    # save
    python scripts/compute_customer_potentials.py --limit 3    # smoke
"""

from __future__ import annotations

import sys
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

import scoring_config as cfg  # noqa: E402
from storage import find_discovery_by_company_name, save_discovery  # noqa: E402
from researcher import estimate_holistic_acv  # noqa: E402


def _unique_customer_names() -> list[str]:
    """Return one name per real customer.

    Dedup by the cached discovery_id the name resolves to — that's the
    real identity.  Records with no cached discovery fall back to name
    key so we still surface "no-cached-discovery" skips for them.
    """
    seen: set[str] = set()
    out: list[str] = []
    for name in cfg.KNOWN_CUSTOMER_CURRENT_ACV.keys():
        disc = find_discovery_by_company_name(name)
        key = disc.get("discovery_id") if disc else f"no-disc:{name}"
        if key in seen:
            continue
        seen.add(key)
        out.append(name)
    return out


def _compute_for(name: str) -> dict:
    """Run caps-disabled holistic for one customer, return summary."""
    disc = find_discovery_by_company_name(name)
    if not disc:
        return {"name": name, "status": "no-cached-discovery"}
    result = estimate_holistic_acv(
        name, disc, disable_known_customer_caps=True,
    )
    return {
        "name": name,
        "status": "ok",
        "discovery_id": disc.get("discovery_id"),
        "current_acv": int(cfg.KNOWN_CUSTOMER_CURRENT_ACV.get(
            name.lower(), {}).get("current_acv") or 0),
        "potential_low": result.get("acv_low") or 0,
        "potential_high": result.get("acv_high") or 0,
        "confidence": result.get("confidence"),
        "discovery": disc,
        "result": result,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="Actually save acv_potential to the cached discoveries (default: dry-run)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process first N customers (for smoke-testing)")
    parser.add_argument("--parallel", type=int, default=5,
                        help="Concurrent Claude calls (default: 5)")
    args = parser.parse_args()

    names = _unique_customer_names()

    # Skip saturated customers — current ~= potential for them.
    non_saturated = [
        n for n in names
        if cfg.KNOWN_CUSTOMER_CURRENT_ACV.get(n.lower(), {}).get("stage") != "saturated"
    ]

    if args.limit:
        non_saturated = non_saturated[:args.limit]

    print(f"Known customers total: {len(names)}")
    print(f"Non-saturated (will compute potential): {len(non_saturated)}")
    print()

    if not args.execute:
        print("DRY RUN (add --execute to save).")
    print()

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futures = {ex.submit(_compute_for, n): n for n in non_saturated}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            if r["status"] == "no-cached-discovery":
                print(f"  SKIP  {r['name']}: no cached discovery")
            else:
                cur = r["current_acv"]
                lo = r["potential_low"]
                hi = r["potential_high"]
                mult = (hi / cur) if cur else 0
                print(f"  OK    {r['name']:<35} current ${cur:>10,}  "
                      f"potential ${lo:>10,}-${hi:>10,} ({mult:.1f}x) "
                      f"{r['confidence']}")

    if args.execute:
        print("\nSaving acv_potential to known_customers.json...")
        import json as _json
        kc_path = os.path.join(_project_root, "backend", "known_customers.json")
        with open(kc_path, "r", encoding="utf-8") as fh:
            kc_raw = _json.load(fh)
        # Build map: name key -> discovery_id (so aliases pointing to the
        # same discovery can share the potential without cross-contaminating
        # unrelated companies that happen to have the same current_acv/stage).
        name_to_disc: dict[str, str] = {}
        for k in kc_raw.keys():
            if k.startswith("_") or k.startswith("comment"):
                continue
            disc = find_discovery_by_company_name(k)
            if disc:
                name_to_disc[k] = disc.get("discovery_id") or ""
        saved = 0
        for r in results:
            if r["status"] != "ok":
                continue
            src_disc_id = r.get("discovery_id") or ""
            for k, v in kc_raw.items():
                if not isinstance(v, dict):
                    continue
                if name_to_disc.get(k) != src_disc_id:
                    continue
                v["acv_potential_low"] = r["potential_low"]
                v["acv_potential_high"] = r["potential_high"]
                v["acv_potential_confidence"] = r["confidence"]
                saved += 1
        with open(kc_path, "w", encoding="utf-8") as fh:
            _json.dump(kc_raw, fh, indent=2)
            fh.write("\n")
        print(f"Updated {saved} entries in known_customers.json (aliases sharing a discovery_id get the same potential).")
    else:
        print("\nDRY RUN complete. Re-run with --execute to save.")


if __name__ == "__main__":
    main()
