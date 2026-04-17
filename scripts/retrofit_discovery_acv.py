"""Retrofit every cached discovery's `_holistic_acv` via the unified framework.

Replaces the legacy Claude holistic output on every cached
`discovery_*.json` under `backend/data/company_intel/` with the
deterministic framework result from
`acv_calculator.compute_discovery_company_acv`.

Pure Python.  Zero Claude calls.  Idempotent — safe to run multiple
times.  Reads each file, recomputes, writes back only when the new
result is non-zero (leaves legacy output in place for companies whose
data is too thin for the framework).

Usage (from repo root):

    PYTHONIOENCODING=utf-8 python scripts/retrofit_discovery_acv.py

Flags:
    --dry-run       compute but don't write
    --only NAME     process only companies whose name contains this substring
                    (case-insensitive).  Useful for spot-checks.
    --verbose       log the rationale line for each company processed

Output: table of companies with old-vs-new ACV numbers + summary counts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_backend() -> None:
    """Put backend + repo root on sys.path.  Backend modules inconsistently
    use flat imports (`from scoring_config import ...`) vs package imports
    (`from backend import scoring_config`); both paths must resolve."""
    here = Path(__file__).resolve().parent
    repo_root = here.parent
    backend = repo_root / "backend"
    for p in (str(repo_root), str(backend)):
        if p not in sys.path:
            sys.path.insert(0, p)


def _fmt(v: int | None) -> str:
    if not v:
        return "—"
    v = int(v)
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v // 1_000}k"
    return f"${v}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="compute but don't write files")
    parser.add_argument("--only", default="",
                        help="substring match on company name (case-insensitive)")
    parser.add_argument("--include-org-types", default="",
                        help="comma-separated list of org_types to include "
                             "(e.g. 'software_company,enterprise_learning_platform'). "
                             "If set, all other org types are skipped.")
    parser.add_argument("--exclude-org-types", default="",
                        help="comma-separated list of org_types to EXCLUDE "
                             "(e.g. 'ilt_training_organization'). "
                             "Applied after --include-org-types if both are set.")
    parser.add_argument("--verbose", action="store_true",
                        help="log rationale per company")
    args = parser.parse_args()

    include_types = {s.strip() for s in args.include_org_types.split(",") if s.strip()}
    exclude_types = {s.strip() for s in args.exclude_org_types.split(",") if s.strip()}

    _load_backend()
    from acv_calculator import compute_discovery_company_acv

    ci_dir = Path(__file__).resolve().parent.parent / "backend" / "data" / "company_intel"
    if not ci_dir.exists():
        print(f"ERROR: {ci_dir} does not exist", file=sys.stderr)
        return 2

    discoveries = sorted(ci_dir.glob("discovery_*.json"))
    print(f"Found {len(discoveries)} discovery files")
    if args.only:
        print(f"Filtering by name substring: {args.only!r}")

    rows = []
    errors = 0
    skipped_filter = 0
    written = 0
    kept_legacy = 0

    for f in discoveries:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [read error] {f.name}: {e}")
            errors += 1
            continue

        name = data.get("company_name") or "(unnamed)"
        if args.only and args.only.lower() not in name.lower():
            skipped_filter += 1
            continue

        org_type = data.get("organization_type") or ""
        if include_types and org_type not in include_types:
            skipped_filter += 1
            continue
        if org_type in exclude_types:
            skipped_filter += 1
            continue

        old = data.get("_holistic_acv") or {}
        old_low = int(old.get("acv_low") or 0)
        old_high = int(old.get("acv_high") or 0)
        old_source = old.get("_source") or "legacy_claude"

        try:
            new = compute_discovery_company_acv(data)
        except Exception as e:
            print(f"  [compute error] {name} ({f.name}): {e}")
            errors += 1
            continue

        new_low = int(new.get("acv_low") or 0)
        new_high = int(new.get("acv_high") or 0)
        new_source = new.get("_source") or "framework"

        # Write only when framework produced a non-zero result.  Companies
        # with no usable audience data keep their legacy _holistic_acv —
        # honest signal that they need re-research, not a zero that wipes
        # out existing knowledge.
        if new_high > 0 or new_low > 0:
            if not args.dry_run:
                data["_holistic_acv"] = new
                f.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            written += 1
            action = "WROTE" if not args.dry_run else "would-write"
        else:
            kept_legacy += 1
            action = "KEPT-LEGACY (framework 0)"

        rows.append({
            "name": name,
            "action": action,
            "org_type": data.get("organization_type") or "",
            "n_products": len(data.get("products") or []),
            "old_source": old_source,
            "old_low": old_low, "old_high": old_high,
            "new_source": new_source,
            "new_low": new_low, "new_high": new_high,
            "confidence": new.get("confidence") or "",
        })

        if args.verbose:
            print(f"  {name} ({action}): old={_fmt(old_high)} → new={_fmt(new_high)}")
            rationale = (new.get("rationale") or "")[:160]
            if rationale:
                print(f"    └ {rationale}")

    # Summary table — biggest ACV changes first
    rows.sort(
        key=lambda r: abs(r["new_high"] - r["old_high"]) if r["new_high"] else 0,
        reverse=True,
    )
    print()
    print(
        f"{'Company':38s} {'OrgType':28s} {'Prods':>5s}  "
        f"{'OldACV':>9s} → {'NewACV':>9s}  {'Conf':>6s}  Action"
    )
    print("-" * 130)
    for r in rows[:100]:
        print(
            f"{r['name'][:38]:38s} {r['org_type'][:28]:28s} {r['n_products']:>5d}  "
            f"{_fmt(r['old_high']):>9s} → {_fmt(r['new_high']):>9s}  "
            f"{r['confidence']:>6s}  {r['action']}"
        )
    if len(rows) > 100:
        print(f"... and {len(rows) - 100} more")
    print("-" * 130)
    print(
        f"\n{len(rows):4d} processed  "
        f"{written:4d} {'written' if not args.dry_run else 'would-write'}  "
        f"{kept_legacy:4d} kept legacy (framework 0)  "
        f"{skipped_filter:4d} skipped (filter)  "
        f"{errors:4d} errors"
    )
    if args.dry_run:
        print("(dry run — no writes applied)")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
