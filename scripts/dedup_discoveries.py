"""Dedup duplicate company discoveries (Option C: auto-merge + human review).

Per Frank 2026-04-13: scans all cached discovery records, groups by
normalized company name, auto-merges obvious duplicates (Cisco / Cisco
Systems, Google / Google Cloud, VMware variants), and flags ambiguous
cases (different classification badges, conflicting org_types) to a
human-review queue.

The merge rule (locked):
  - Canonical name preference — the cleanest variant wins (no "Inc",
    no parenthetical, no division suffix). The shared
    `_normalize_company_name` is the source of truth for normalization.
  - Data union — all products from any record are merged into one list
    (deduped by name), all company_signals are taken from the most-
    complete record per field, deep dive analyses keyed by analysis_id
    are preserved across all records, dates use earliest created_at +
    latest updated_at.
  - Discovery_id of the canonical record is kept; older records are
    archived (renamed with `.archived-<timestamp>.json` suffix).

Usage:
    python scripts/dedup_discoveries.py              # dry run (default)
    python scripts/dedup_discoveries.py --execute    # actually merge
    python scripts/dedup_discoveries.py --review     # show ambiguous queue
"""

from __future__ import annotations

import sys
import os
import json
import argparse
from collections import defaultdict
from datetime import datetime, timezone

_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

from storage import (  # noqa: E402
    _COMPANY_DIR, list_discoveries, save_discovery, _normalize_company_name,
)


def _load_all_discoveries() -> list[dict]:
    """Load every discovery record from disk. Returns the parsed dicts."""
    out = []
    for f in os.listdir(_COMPANY_DIR):
        if not (f.startswith("discovery_") and f.endswith(".json")):
            continue
        path = os.path.join(_COMPANY_DIR, f)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            d["_source_file"] = f  # remember origin for archive operation
            out.append(d)
        except Exception as e:
            print(f"  WARN: failed to load {f}: {e}")
    return out


def _group_by_normalized_name(discoveries: list[dict]) -> dict[str, list[dict]]:
    """Group discoveries by normalized company name."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for d in discoveries:
        cn = d.get("company_name") or ""
        norm = _normalize_company_name(cn)
        if not norm:
            continue
        groups[norm].append(d)
    return groups


def _is_ambiguous(group: list[dict]) -> tuple[bool, str]:
    """Decide whether a group needs human review.

    Returns (is_ambiguous, reason). Ambiguous when records disagree on
    classification badge or organization type — likely two different
    real companies that happen to normalize the same way.
    """
    badges = {(d.get("company_badge") or "").strip().lower() for d in group}
    badges.discard("")
    if len(badges) > 1:
        return True, f"badges differ: {sorted(badges)}"
    org_types = {(d.get("organization_type") or "").strip().lower() for d in group}
    org_types.discard("")
    if len(org_types) > 1:
        return True, f"organization_types differ: {sorted(org_types)}"
    return False, ""


def _pick_canonical(group: list[dict]) -> dict:
    """Pick the canonical record from a group.

    Rule: the record whose company_name normalizes WITHOUT changes wins
    (cleanest source name). Tiebreak: most recent updated_at, then
    most-complete (most populated keys at top level).
    """
    def cleanliness(d):
        name = d.get("company_name") or ""
        norm = _normalize_company_name(name)
        return 0 if name.strip().lower() == norm else 1
    def recency(d):
        return d.get("updated_at") or d.get("created_at") or ""
    def completeness(d):
        return -sum(1 for v in d.values() if v)  # negative so more = earlier in sort
    return sorted(group, key=lambda d: (cleanliness(d), -1 if recency(d) else 0, completeness(d)))[0]


def _merge_records(canonical: dict, others: list[dict]) -> dict:
    """Union-merge other records into the canonical record.

    Products: dedup by name, union from all sources.
    Signals: take longest non-empty value per field across sources.
    Dates: earliest created_at, latest updated_at.
    Other top-level fields: prefer canonical, fall back to others when canonical is empty.
    """
    merged = dict(canonical)

    # Union products by name (case-insensitive).
    seen_names: set[str] = set()
    products: list[dict] = []
    for src in [canonical] + others:
        for p in (src.get("products") or []):
            key = (p.get("name") or "").strip().lower()
            if not key or key in seen_names:
                continue
            seen_names.add(key)
            products.append(p)
    if products:
        merged["products"] = products

    # Signals — longest non-empty value per field.
    sig_keys = set()
    for src in [canonical] + others:
        sig_keys.update((src.get("company_signals") or {}).keys())
    merged_signals = dict(canonical.get("company_signals") or {})
    for k in sig_keys:
        best = merged_signals.get(k) or ""
        for src in others:
            v = (src.get("company_signals") or {}).get(k) or ""
            if isinstance(v, str) and len(v) > len(best):
                best = v
        if best:
            merged_signals[k] = best
    if merged_signals:
        merged["company_signals"] = merged_signals

    # Dates.
    created_dates = [d.get("created_at") for d in [canonical] + others if d.get("created_at")]
    if created_dates:
        merged["created_at"] = min(created_dates)
    updated_dates = [d.get("updated_at") for d in [canonical] + others if d.get("updated_at")]
    if updated_dates:
        merged["updated_at"] = max(updated_dates)

    # Top-level fields canonical-empty fallback (description, badge, etc.)
    for k in ("company_description", "company_badge", "company_url", "organization_type"):
        if not merged.get(k):
            for src in others:
                v = src.get(k)
                if v:
                    merged[k] = v
                    break

    # Stamp the merge.
    merged["_merged_from"] = sorted(
        [canonical.get("discovery_id")] + [o.get("discovery_id") for o in others]
    )
    merged["_merged_at"] = datetime.now(timezone.utc).isoformat()

    # Strip transient _source_file marker
    merged.pop("_source_file", None)
    return merged


def _archive_record(record: dict) -> str:
    """Rename the source file to .archived-<timestamp>.json."""
    src_file = record.get("_source_file")
    if not src_file:
        return ""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archived_path = os.path.join(_COMPANY_DIR, src_file.replace(".json", f".archived-{ts}.json"))
    src_path = os.path.join(_COMPANY_DIR, src_file)
    os.rename(src_path, archived_path)
    return archived_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="actually merge (default: dry-run)")
    parser.add_argument("--review", action="store_true", help="only show ambiguous queue")
    args = parser.parse_args()

    print(f"Loading discoveries from {_COMPANY_DIR}...")
    discoveries = _load_all_discoveries()
    print(f"  loaded {len(discoveries)} records")

    groups = _group_by_normalized_name(discoveries)
    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"  found {len(dup_groups)} duplicate groups across {sum(len(v) for v in dup_groups.values())} records")

    auto_merge = []
    needs_review = []
    for norm_key, group in dup_groups.items():
        ambiguous, reason = _is_ambiguous(group)
        if ambiguous:
            needs_review.append((norm_key, group, reason))
        else:
            auto_merge.append((norm_key, group))

    print(f"  auto-mergeable: {len(auto_merge)}")
    print(f"  needs human review: {len(needs_review)}")
    print()

    if args.review or needs_review:
        print("=== HUMAN REVIEW QUEUE ===")
        for norm_key, group, reason in needs_review:
            print(f"  '{norm_key}' ({reason})")
            for d in group:
                print(f"    - {d.get('company_name')!r} | badge={d.get('company_badge')!r} | id={d.get('discovery_id')}")
        print()

    if args.review:
        return

    print("=== AUTO-MERGE PLAN ===")
    for norm_key, group in auto_merge[:30]:
        names = [d.get("company_name") for d in group]
        canon = _pick_canonical(group)
        print(f"  '{norm_key}' → canonical: {canon.get('company_name')!r}")
        for n in names:
            marker = " (canonical)" if n == canon.get("company_name") else ""
            print(f"    - {n!r}{marker}")
    if len(auto_merge) > 30:  # magic-allowed: console-output-truncation-threshold
        print(f"  ... and {len(auto_merge) - 30} more groups")  # magic-allowed: console-output-truncation-threshold
    print()

    if not args.execute:
        print("DRY RUN — no changes written. Re-run with --execute to merge.")
        return

    print("Executing merges...")
    for norm_key, group in auto_merge:
        canon = _pick_canonical(group)
        others = [d for d in group if d is not canon]
        merged = _merge_records(canon, others)
        # Save the canonical record (overwrites canon's file)
        save_discovery(merged.get("discovery_id"), merged)
        # Archive the others
        for o in others:
            _archive_record(o)
        print(f"  merged {len(group)} → 1 ({merged.get('company_name')})")

    print(f"\nDone. Merged {len(auto_merge)} groups. {len(needs_review)} need human review.")


if __name__ == "__main__":
    main()
