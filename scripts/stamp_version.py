"""Stamp all cached analyses with the current SCORING_LOGIC_VERSION.

This prevents stale-version re-research when visiting Inspector pages.
Use after scoring config changes that affect ACV calculation (rates,
adoption, hours, deflation) but NOT pillar scoring logic (weights,
signals, baselines, penalties).

The ACV is recomputed by recompute_analysis() on every page load, so
the ACV numbers will be correct regardless of the stamp. The stamp
just prevents the version check from triggering a full re-research.

Usage:
    python scripts/stamp_version.py              # stamp all analyses
    python scripts/stamp_version.py --dry-run    # show what would change
"""

import sys
import os
import json

_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

import scoring_config as cfg


def main():
    dry_run = "--dry-run" in sys.argv

    data_dir = os.path.join(_project_root, "backend", "data", "company_intel")
    if not os.path.exists(data_dir):
        print("No data directory found.")
        return

    current = cfg.SCORING_LOGIC_VERSION
    updated = 0
    skipped = 0

    for filename in sorted(os.listdir(data_dir)):
        if not filename.startswith("analysis_"):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath) as f:
            data = json.load(f)

        old_version = data.get("_scoring_logic_version", "<missing>")
        company = data.get("company_name", "?")

        if old_version == current:
            skipped += 1
            continue

        print(f"  {company}: {old_version} -> {current}")
        if not dry_run:
            data["_scoring_logic_version"] = current
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)  # magic-allowed: JSON formatting
        updated += 1

    # Also stamp discoveries
    for filename in sorted(os.listdir(data_dir)):
        if not filename.startswith("discovery_"):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath) as f:
            data = json.load(f)

        old_version = data.get("_scoring_logic_version", "<missing>")
        if old_version == current:
            continue

        company = data.get("company_name", "?")
        print(f"  [discovery] {company}: {old_version} -> {current}")
        if not dry_run:
            data["_scoring_logic_version"] = current
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)  # magic-allowed: JSON formatting
        updated += 1

    action = "Would update" if dry_run else "Updated"
    print(f"\n{action} {updated} files. Skipped {skipped} already current.")
    print(f"Current version: {current}")


if __name__ == "__main__":
    main()
