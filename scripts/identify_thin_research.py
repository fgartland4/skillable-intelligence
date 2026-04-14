"""Identify cached discoveries whose researcher data is too thin to score.

Surfaces candidates for full re-research. No Claude calls — pure Python
analysis over the cached `_holistic_acv` output + product list + signals.

Heuristics that flag a record as thin:
  - Holistic ACV midpoint is very small relative to other companies in
    the same org_type cohort (bottom decile by midpoint).
  - Confidence is "low" AND midpoint is below a configurable floor
    (default $100k).
  - Product count is < 2 (researcher couldn't surface meaningful portfolio).
  - The holistic rationale mentions phrases like "limited research",
    "thin signals", "could not determine", "no specific products found".
  - Total user_base across products is 0 or trivially small.

Usage:
    python scripts/identify_thin_research.py
    python scripts/identify_thin_research.py --floor 50000
    python scripts/identify_thin_research.py --csv /tmp/thin.csv
    python scripts/identify_thin_research.py --names-only      # just print company names

Output is a ranked candidate list (ordered by how thin the data looks),
not destructive. Caller decides which to re-research.
"""

from __future__ import annotations

import sys
import os
import json
import argparse
import re
from collections import defaultdict

_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

from storage import _COMPANY_DIR  # noqa: E402

_THIN_RATIONALE_PATTERNS = [
    r"\blimited\s+research\b",
    r"\bthin\s+signals?\b",
    r"\bcould\s+not\s+determine\b",
    r"\bno\s+specific\s+products?\s+found\b",
    r"\bsparse\s+data\b",
    r"\binsufficient\s+evidence\b",
    r"\bunable\s+to\s+find\b",
    r"\bvery\s+limited\b",
]
_THIN_RATIONALE_RE = re.compile("|".join(_THIN_RATIONALE_PATTERNS), re.IGNORECASE)


def _load_all_discoveries() -> list[dict]:
    out = []
    for f in os.listdir(_COMPANY_DIR):
        if not (f.startswith("discovery_") and f.endswith(".json")):
            continue
        if ".archived-" in f:
            continue
        try:
            with open(os.path.join(_COMPANY_DIR, f), "r", encoding="utf-8") as fh:
                d = json.load(fh)
            out.append(d)
        except Exception:
            continue
    return out


def _parse_user_base_str(s: str) -> int:
    if not s:
        return 0
    s = str(s).replace("~", "").replace(",", "").strip().upper()
    try:
        if s.endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        if s.endswith("K"):
            return int(float(s[:-1]) * 1_000)
        if s.endswith("B"):
            return int(float(s[:-1]) * 1_000_000_000)
        return int(float(s))
    except (ValueError, IndexError):
        return 0


def _score_thinness(disc: dict, cohort_p10_midpoints: dict[str, int], floor: int) -> tuple[int, list[str]]:
    """Return (thinness_score, list_of_reasons). Higher score = thinner."""
    reasons = []
    score = 0
    holistic = disc.get("_holistic_acv") or {}
    acv_low = int(holistic.get("acv_low") or 0)
    acv_high = int(holistic.get("acv_high") or 0)
    midpoint = (acv_low + acv_high) // 2
    confidence = (holistic.get("confidence") or "").lower()
    rationale = str(holistic.get("rationale") or "")
    products = disc.get("products") or []
    org_type = (disc.get("organization_type") or "").lower()

    # 1. Low confidence + below floor
    if confidence == "low" and midpoint < floor:
        score += 30
        reasons.append(f"low confidence + midpoint ${midpoint:,} below floor ${floor:,}")

    # 2. Cohort outlier (bottom decile of org_type)
    cohort_p10 = cohort_p10_midpoints.get(org_type, 0)
    if cohort_p10 > 0 and midpoint < cohort_p10:
        score += 25
        reasons.append(f"bottom decile of {org_type} cohort (cohort p10 ${cohort_p10:,})")

    # 3. Few products
    if len(products) < 2:
        score += 20
        reasons.append(f"only {len(products)} product(s) discovered")

    # 4. Thin rationale phrases
    if rationale and _THIN_RATIONALE_RE.search(rationale):
        score += 15
        reasons.append("rationale mentions thin / limited research")

    # 5. Trivial total user base
    total_users = sum(_parse_user_base_str(p.get("estimated_user_base", "")) for p in products)
    if total_users < 1_000:
        score += 15
        reasons.append(f"total user_base across products is {total_users:,}")

    # 6. No holistic ACV at all (retrofit didn't run or failed)
    if not holistic or midpoint == 0:
        score += 50
        reasons.append("no _holistic_acv on record (retrofit didn't run or failed)")

    return (score, reasons)


def _compute_cohort_p10(discoveries: list[dict]) -> dict[str, int]:
    """For each org_type, compute the 10th percentile midpoint."""
    by_type: dict[str, list[int]] = defaultdict(list)
    for d in discoveries:
        ot = (d.get("organization_type") or "").lower()
        h = d.get("_holistic_acv") or {}
        lo = int(h.get("acv_low") or 0)
        hi = int(h.get("acv_high") or 0)
        mid = (lo + hi) // 2
        if mid > 0:
            by_type[ot].append(mid)
    out = {}
    for ot, vals in by_type.items():
        vals.sort()
        if len(vals) < 5:
            continue
        p10_idx = max(0, int(len(vals) * 0.10))
        out[ot] = vals[p10_idx]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--floor", type=int, default=100_000,
                        help="ACV midpoint floor below which low-confidence records are flagged (default 100000)")
    parser.add_argument("--top", type=int, default=50,
                        help="show top N candidates (default 50)")
    parser.add_argument("--csv", type=str, default="",
                        help="write full candidate list to this CSV path")
    parser.add_argument("--names-only", action="store_true",
                        help="print only company names (one per line) — pipe to retrofit_acv.py")
    args = parser.parse_args()

    print(f"Loading discoveries from {_COMPANY_DIR}...")
    discoveries = _load_all_discoveries()
    print(f"  loaded {len(discoveries)} records")

    cohort_p10 = _compute_cohort_p10(discoveries)
    print(f"  computed bottom-decile midpoints for {len(cohort_p10)} org_types")

    candidates = []
    for d in discoveries:
        score, reasons = _score_thinness(d, cohort_p10, args.floor)
        if score == 0:
            continue
        candidates.append({
            "name": d.get("company_name") or "?",
            "score": score,
            "midpoint": (((d.get("_holistic_acv") or {}).get("acv_low") or 0) +
                         ((d.get("_holistic_acv") or {}).get("acv_high") or 0)) // 2,
            "confidence": ((d.get("_holistic_acv") or {}).get("confidence") or ""),
            "products": len(d.get("products") or []),
            "org_type": (d.get("organization_type") or ""),
            "discovery_id": d.get("discovery_id") or "",
            "reasons": reasons,
        })

    candidates.sort(key=lambda c: -c["score"])

    if args.names_only:
        for c in candidates:
            print(c["name"])
        return

    print()
    print(f"FOUND {len(candidates)} thin candidates (sorted by thinness score):")
    print()
    print(f"{'score':>5}  {'midpoint':>12}  {'conf':>6}  {'prods':>5}  {'org_type':<22}  {'name':<45}  reasons")
    print("-" * 140)
    for c in candidates[: args.top]:
        reasons_str = "; ".join(c["reasons"])
        print(f"{c['score']:>5}  ${c['midpoint']:>11,}  {c['confidence']:>6}  {c['products']:>5}  "
              f"{c['org_type'][:22]:<22}  {c['name'][:45]:<45}  {reasons_str[:80]}")

    if args.csv:
        import csv
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["score", "name", "midpoint", "confidence", "products", "org_type", "discovery_id", "reasons"])
            for c in candidates:
                w.writerow([c["score"], c["name"], c["midpoint"], c["confidence"],
                            c["products"], c["org_type"], c["discovery_id"], "; ".join(c["reasons"])])
        print()
        print(f"Wrote {len(candidates)} candidates to {args.csv}")


if __name__ == "__main__":
    main()
