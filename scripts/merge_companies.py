"""Force-merge a specific set of company discoveries into one canonical record.

Use this when the automatic dedup runner (`dedup_discoveries.py`) cannot
catch a duplicate cluster because the normalized names differ — typically
parent/service-line pairs like:

  Deloitte / Deloitte Consulting / Deloitte Consulting LLP
  Grand Canyon University / Grand Canyon Education
  Cisco / Cisco Systems Inc / Cisco.com

The auto-dedup is deliberately conservative (string normalization only)
to avoid collapsing genuinely different entities. This script is the
"I know these are the same, merge them" escape hatch.

The canonical record is chosen by the same rules as auto-dedup:
cleanest name -> most recent -> most complete. Can be overridden by
passing `--canonical <exact_name>`.

Usage:
    # dry-run (default) — see what would happen
    python scripts/merge_companies.py "Deloitte" "Deloitte Consulting" "Deloitte Consulting LLP"

    # execute
    python scripts/merge_companies.py "Deloitte" "Deloitte Consulting" "Deloitte Consulting LLP" --execute

    # pick a specific canonical (must exactly match one of the --names)
    python scripts/merge_companies.py "Deloitte" "Deloitte Consulting LLP" \
        --canonical "Deloitte Consulting LLP" --execute

    # rename the merged record
    python scripts/merge_companies.py "Deloitte" "Deloitte Consulting" \
        --rename-to "Deloitte" --execute

Produces: the canonical record keeps its discovery_id and file; the
others are renamed to `.archived-<timestamp>.json`.
"""

from __future__ import annotations

import sys
import os
import argparse
from datetime import datetime, timezone

_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

from storage import _COMPANY_DIR, save_discovery  # noqa: E402

# Reuse the merge + archive helpers from the dedup runner - single
# source of truth for the merge semantics (Define-Once).
# `_load_all_discoveries` attaches `_source_file` to every record, which
# `_archive_record` needs. Plain `storage.list_discoveries` does not.
from dedup_discoveries import (  # noqa: E402
    _load_all_discoveries, _pick_canonical, _merge_records, _archive_record,
)


def _find_records_by_names(names: list[str]) -> tuple[list[dict], list[str]]:
    """Return (records_found, missing_names). Matching is exact on
    company_name, case-insensitive. When the same name maps to multiple
    records on disk (it happens — the auto-dedup runner didn't catch
    them), ALL matching records are included so the merge collapses
    them too."""
    wanted = {n.strip().lower() for n in names}
    found: list[dict] = []
    matched_names: set[str] = set()
    for d in _load_all_discoveries():
        n = (d.get("company_name") or "").strip().lower()
        if n in wanted:
            found.append(d)
            matched_names.add(n)
    missing = sorted(wanted - matched_names)
    return found, missing


def main():
    parser = argparse.ArgumentParser(
        description="Force-merge a specific set of company discoveries into one canonical record.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("names", nargs="+",
                        help="Exact company_name values to merge (case-insensitive)")
    parser.add_argument("--canonical", default=None,
                        help="Exact name of the record to keep as canonical. "
                             "If omitted, picks automatically (cleanest -> most-recent -> most-complete).")
    parser.add_argument("--rename-to", default=None,
                        help="Rename the merged record's company_name to this string. "
                             "Useful when the canonical auto-pick lands on a long variant "
                             "(e.g. 'Deloitte Consulting LLP') and you want the short form.")
    parser.add_argument("--execute", action="store_true",
                        help="Actually perform the merge (default: dry-run)")
    args = parser.parse_args()

    if len(args.names) < 2:
        parser.error("need at least 2 names to merge")

    # Resolve names -> records
    records, missing = _find_records_by_names(args.names)
    if missing:
        print(f"ERROR: could not find records for: {missing}")
        print("Run `python scripts/dedup_discoveries.py` to see all cached names.")
        sys.exit(1)

    # Pick canonical
    if args.canonical:
        want = args.canonical.strip().lower()
        canonical = next(
            (r for r in records if (r.get("company_name") or "").strip().lower() == want),
            None,
        )
        if not canonical:
            print(f"ERROR: --canonical '{args.canonical}' not in the input names")
            sys.exit(1)
    else:
        canonical = _pick_canonical(records)

    others = [r for r in records if r is not canonical]

    # Summarize
    print(f"\nMERGE PLAN ({len(records)} records -> 1):")
    print(f"  CANONICAL (keep): '{canonical.get('company_name')}'")
    print(f"    file: {canonical.get('_source_file')}")
    print(f"    discovery_id: {canonical.get('discovery_id')}")
    print(f"    created: {canonical.get('created_at')}")
    ha = canonical.get("_holistic_acv") or {}
    if ha.get("acv_low"):
        print(f"    ACV: ${ha['acv_low']:,}-${ha.get('acv_high', 0):,} "
              f"({ha.get('confidence', '?')})")
    print()
    for o in others:
        print(f"  ARCHIVE:  '{o.get('company_name')}'")
        print(f"    file: {o.get('_source_file')}")
        print(f"    discovery_id: {o.get('discovery_id')}")
        oha = o.get("_holistic_acv") or {}
        if oha.get("acv_low"):
            print(f"    ACV: ${oha['acv_low']:,}-${oha.get('acv_high', 0):,} "
                  f"({oha.get('confidence', '?')})")
    print()

    if args.rename_to:
        print(f"  RENAME merged record's company_name -> '{args.rename_to}'")
        print()

    if not args.execute:
        print("DRY RUN — no changes written. Re-run with --execute to merge.")
        return

    # Merge
    merged = _merge_records(canonical, others)
    if args.rename_to:
        merged["company_name"] = args.rename_to
    # Always bump updated_at to mark the merge
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Write merged record back under the canonical's discovery_id
    save_discovery(merged["discovery_id"], merged)
    print(f"  Saved merged record to discovery_{merged['discovery_id']}.json")

    # Archive the others
    for o in others:
        archived = _archive_record(o)
        if archived:
            print(f"  Archived: {os.path.basename(archived)}")

    print("\nMerge complete.")


if __name__ == "__main__":
    main()
