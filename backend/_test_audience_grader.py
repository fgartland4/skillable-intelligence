"""TEMPORARY test runner — end-to-end dry run of the new ACV pipeline.

Loads a real cached discovery JSON, runs audience_grader + compute_company_acv,
prints the output. Does NOT write anything back to disk. Safe to delete
after validation.

Usage: python _test_audience_grader.py [discovery_filename]
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

# Load .env (same pattern as researcher.py)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

from acv_calculator import compute_company_acv

TEST_DISCOVERIES = [
    ("discovery_5f47ed90.json", "Trellix",       "software · current $750K, potential $2.5-3.5M"),
    ("discovery_8e444a4c.json", "CBT Nuggets",   "ELP · non-customer, slide/estimate ~$0.5-2M"),
    ("discovery_82409fa6.json", "Skillsoft",     "ELP · $5.5M saturated"),
    ("discovery_3d52f554.json", "Pluralsight",   "ELP · non-customer, slide-inspired ~$5-10M"),
    ("discovery_3d52775d.json", "Deloitte",      "GSI · current $410K, potential $12-22M"),
    ("discovery_892e80c8.json", "CompTIA",       "Industry Authority · $5M saturated"),
    ("discovery_8a92e701.json", "EC-Council",    "Industry Authority · $2.1M saturated"),
    ("discovery_594374c6.json", "Sage Group",    "software ERP · non-customer, slide implies $1-3M"),
    ("discovery_6e41edea.json", "Calix",         "software networking · non-customer, slide $1.5M"),
]


def run_one(filename: str, expected_label: str) -> None:
    path = Path("data/company_intel") / filename
    if not path.exists():
        print(f"SKIP: {path} not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        discovery = json.load(f)

    print()
    print("=" * 72)
    print(f"Company: {discovery.get('company_name')}")
    print(f"Org type: {discovery.get('organization_type')}")
    print(f"Product count: {len(discovery.get('products') or [])}")
    print(f"Expected: {expected_label}")
    print("=" * 72)

    try:
        result = compute_company_acv(discovery)
    except Exception as e:
        print(f"FAILED: {e}")
        return

    acv = result["acv"]
    raw = result["raw_acv_before_harness"]
    pl = result["popularity_weighted_pl"]
    harness = result["harness"]
    confidence = result["confidence"]

    print()
    print(f"  Company ACV:        ${acv:,}")
    print(f"  Raw before harness: ${raw:,}")
    print(f"  PL weighted:        {pl}")
    print(f"  Harness factor:     {harness}")
    print(f"  Confidence:         {confidence}")
    print()
    print("  Motion breakdown:")
    for motion_key, motion_data in result["motions"].items():
        label = motion_data["label"]
        audience = motion_data["audience"]
        rate = motion_data["rate"]
        rate_unit = motion_data["rate_unit"]
        motion_acv = motion_data["acv"]
        per_conf = motion_data["confidence"]
        print(
            f"    {label:22s}  audience={audience:>10,}  × ${rate}/{rate_unit} "
            f"= ${motion_acv:>13,}   [{per_conf}]"
        )
    print()
    print("  Rationale:")
    rationale = result["rationale"]
    if len(rationale) > 400:
        rationale = rationale[:400] + "..."
    print(f"    {rationale}")
    print()
    print("  Market Demand story:")
    print(f"    {result['market_demand_story']}")
    if result.get("key_drivers"):
        print()
        print("  Key drivers:")
        for driver in result["key_drivers"][:5]:
            print(f"    • {driver}")
    if result.get("caveats"):
        print()
        print("  Caveats:")
        for caveat in result["caveats"][:3]:
            print(f"    • {caveat}")
    print()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        run_one(target, "(manual)")
    else:
        for filename, name, expected in TEST_DISCOVERIES:
            run_one(filename, expected)
