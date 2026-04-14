"""Retrofit cached discoveries to the current ACV standard.

Three gap-fill modes Frank approved 2026-04-13:

  --mode holistic     (default) Option 2 holistic ACV on every cached
                      discovery. Writes discovery["_holistic_acv"].
  --mode enrollments  For wrapper org records only (ILT, Academic, ELP,
                      GSI, VAR, Distributor, Industry Authority,
                      Content Development). Fills
                      annual_enrollments_estimate per program.
  --mode gap-fill     For companies with cached Deep Dive analyses
                      only. Re-populates channel_partner_se_population
                      + events_attendance on the analysis fact drawer
                      so the ACV calculator can recompose motions on
                      next read.

Each mode is ONE targeted Claude call per record — no full re-research.
Modes compose: run them in sequence (holistic → enrollments → gap-fill)
to bring cached records fully up to current standard.

Usage:
    python scripts/retrofit_acv.py                          # dry-run holistic
    python scripts/retrofit_acv.py --execute                # holistic on all
    python scripts/retrofit_acv.py --execute --skip-existing
    python scripts/retrofit_acv.py --mode enrollments --execute
    python scripts/retrofit_acv.py --mode gap-fill --execute
    python scripts/retrofit_acv.py --mode enrollments --execute --company "LLPA"
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

from storage import _COMPANY_DIR, save_discovery, save_analysis, load_analysis  # noqa: E402
import scoring_config as cfg  # noqa: E402

_DEFAULT_PARALLELISM = 10  # magic-allowed: parallel-Claude-call-throttle (bumped 2026-04-14 from 5; rate-limit headroom confirmed over long Prospector runs)


# ── Mode registry — each mode declares a filter + a worker ────────────

def _filter_all(d: dict) -> bool:
    return True


def _filter_wrapper_orgs(d: dict) -> bool:
    """Only wrapper org types carry annual_enrollments_estimate."""
    ot = (d.get("organization_type") or "").lower().replace(" ", "_")
    normalized = cfg.ORG_TYPE_NORMALIZATION.get(ot, "")
    return normalized in cfg.ACV_WRAPPER_ORG_TYPES


def _filter_has_analysis(d: dict) -> bool:
    """Only companies with cached Deep Dive analyses."""
    from storage import find_analysis_by_discovery_id
    disc_id = d.get("discovery_id") or ""
    if not disc_id:
        return False
    return find_analysis_by_discovery_id(disc_id) is not None


def _worker_holistic(disc: dict) -> tuple[str, str, str | None]:
    """Run holistic ACV. Returns (name, summary, error_or_None)."""
    from researcher import estimate_holistic_acv
    name = disc.get("company_name") or "?"
    try:
        result = estimate_holistic_acv(name, disc)
        if not result:
            return (name, "empty-result", "empty result from Claude")
        disc["_holistic_acv"] = result
        save_discovery(disc.get("discovery_id"), disc)
        lo = result.get("acv_low") or 0
        hi = result.get("acv_high") or 0
        conf = result.get("confidence") or "?"
        return (name, f"${lo:,}-${hi:,} ({conf})", None)
    except Exception as e:
        return (name, "exception", str(e))


def _worker_enrollments(disc: dict) -> tuple[str, str, str | None]:
    """Estimate annual_enrollments_estimate per program. Merges into products."""
    from researcher import estimate_annual_enrollments
    name = disc.get("company_name") or "?"
    try:
        results = estimate_annual_enrollments(name, disc)
        if not results:
            return (name, "empty-result", "Claude returned no program estimates")
        # Merge onto each product by name match.
        products = disc.get("products") or []
        by_name = {(r.get("program_name") or "").strip().lower(): r for r in results}
        merged_count = 0
        for p in products:
            key = (p.get("name") or "").strip().lower()
            match = by_name.get(key)
            if not match:
                continue
            p["annual_enrollments_estimate"] = match["annual_enrollments_estimate"]
            p["annual_enrollments_evidence"] = match["annual_enrollments_evidence"]
            p["annual_enrollments_confidence"] = match["annual_enrollments_confidence"]
            merged_count += 1
        save_discovery(disc.get("discovery_id"), disc)
        return (name, f"filled {merged_count}/{len(products)} programs", None)
    except Exception as e:
        return (name, "exception", str(e))


def _worker_re_research(disc: dict) -> tuple[str, str, str | None]:
    """Full re-research — runs intelligence.discover(force_refresh=True).

    Use when the original researcher missed products / returned thin data
    and the cached record can't be salvaged with gap-fills. This is a
    FULL discovery pipeline re-run per company: fresh searches, fresh
    Claude call for product identification + signals + holistic ACV.

    Archives the old discovery (so prior state is recoverable) and
    replaces it with the fresh one.
    """
    from intelligence import discover
    name = disc.get("company_name") or "?"
    old_id = disc.get("discovery_id") or ""
    try:
        fresh = discover(name, force_refresh=True)
        if not fresh:
            return (name, "empty-result", "discover() returned no record")
        new_id = fresh.get("discovery_id", "")
        fresh_products = len(fresh.get("products") or [])
        fresh_acv = fresh.get("_holistic_acv") or {}
        lo = fresh_acv.get("acv_low") or 0
        hi = fresh_acv.get("acv_high") or 0
        conf = fresh_acv.get("confidence") or "?"
        summary = f"{fresh_products} products, ${lo:,}-${hi:,} ({conf})"
        if new_id and new_id != old_id:
            summary += f" [new id: {new_id}]"
        return (name, summary, None)
    except Exception as e:
        return (name, "exception", str(e))


def _worker_gap_fill(disc: dict) -> tuple[str, str, str | None]:
    """Gap-fill channel_partner_se_population + events_attendance on analysis."""
    from researcher import gap_fill_cf_audience_facts
    from storage import find_analysis_by_discovery_id
    name = disc.get("company_name") or "?"
    try:
        disc_id = disc.get("discovery_id") or ""
        analysis = find_analysis_by_discovery_id(disc_id) if disc_id else None
        if not analysis:
            return (name, "no-analysis", "no Deep Dive analysis cached")
        filled = gap_fill_cf_audience_facts(name, disc)
        if not filled:
            return (name, "empty-result", "Claude returned no gap-fill data")
        # Merge into the analysis's Customer Fit facts drawer.
        cf_facts = analysis.get("_customer_fit_facts") or {}
        if "channel_partner_se_population" in filled:
            cf_facts["channel_partner_se_population"] = filled["channel_partner_se_population"]
        if "events_attendance" in filled:
            cf_facts["events_attendance"] = filled["events_attendance"]
        analysis["_customer_fit_facts"] = cf_facts
        # Broadcast onto per-product CF facts too (Phase F pattern — same
        # unified block lives on each product so per-product recompose works).
        for p in (analysis.get("products") or []):
            p["customer_fit_facts"] = cf_facts
        save_analysis(analysis)
        parts = []
        if "channel_partner_se_population" in filled:
            cp = filled["channel_partner_se_population"]
            parts.append(f"partner SEs={cp.get('low', 0)}-{cp.get('high', 0)}")
        if "events_attendance" in filled:
            evs = filled["events_attendance"]
            parts.append(f"events={len(evs)}")
        return (name, ", ".join(parts) or "filled", None)
    except Exception as e:
        return (name, "exception", str(e))


_MODES = {
    "holistic":    (_filter_all,           _worker_holistic,    "_holistic_acv"),
    "enrollments": (_filter_wrapper_orgs,  _worker_enrollments, None),
    "gap-fill":    (_filter_has_analysis,  _worker_gap_fill,    None),
    "re-research": (_filter_all,           _worker_re_research, None),
}


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=list(_MODES.keys()), default="holistic",
                        help="gap-fill mode (default: holistic)")
    parser.add_argument("--execute", action="store_true", help="actually run (default: dry-run)")
    parser.add_argument("--limit", type=int, default=0, help="only process the first N records")
    parser.add_argument("--company", type=str, default="", help="only records matching this substring")
    parser.add_argument("--names-from-file", type=str, default="", help="path to a file with one company name per line; only records whose name matches (exact lowercase) any listed name will run")
    parser.add_argument("--skip-existing", action="store_true",
                        help="skip records that already have the mode's output (holistic: _holistic_acv; "
                             "enrollments: any product with annual_enrollments_estimate set)")
    parser.add_argument("--parallel", type=int, default=_DEFAULT_PARALLELISM,
                        help=f"parallel Claude calls (default {_DEFAULT_PARALLELISM})")
    args = parser.parse_args()

    mode_filter, worker, skip_field = _MODES[args.mode]

    print(f"Loading discoveries from {_COMPANY_DIR}...")
    discoveries = _load_all_discoveries()
    print(f"  loaded {len(discoveries)} records")

    # Mode-specific filter
    discoveries = [d for d in discoveries if mode_filter(d)]
    print(f"  mode '{args.mode}' filter → {len(discoveries)} records")

    # --company filter
    if args.company:
        needle = args.company.lower()
        discoveries = [d for d in discoveries if needle in (d.get("company_name") or "").lower()]
        print(f"  --company '{args.company}' → {len(discoveries)} records")

    # --names-from-file filter — one company name per line
    if args.names_from_file:
        with open(args.names_from_file, "r", encoding="utf-8") as fh:
            wanted = {line.strip().lower() for line in fh if line.strip() and not line.startswith(("#", " "))}
        before = len(discoveries)
        discoveries = [d for d in discoveries if (d.get("company_name") or "").strip().lower() in wanted]
        print(f"  --names-from-file '{args.names_from_file}' → {before} → {len(discoveries)} records")

    # --skip-existing filter
    if args.skip_existing:
        before = len(discoveries)
        if args.mode == "holistic":
            discoveries = [
                d for d in discoveries
                if not (d.get("_holistic_acv") or {}).get("rationale")
            ]
        elif args.mode == "enrollments":
            discoveries = [
                d for d in discoveries
                if not any((p.get("annual_enrollments_estimate") or 0) > 0 for p in (d.get("products") or []))
            ]
        # gap-fill skip-existing: skip analyses whose CF facts already have populated fields
        elif args.mode == "gap-fill":
            from storage import find_analysis_by_discovery_id
            filtered = []
            for d in discoveries:
                a = find_analysis_by_discovery_id(d.get("discovery_id") or "")
                if not a:
                    continue
                cf = a.get("_customer_fit_facts") or {}
                cp = cf.get("channel_partner_se_population") or {}
                evs = cf.get("events_attendance") or {}
                has_cp = (cp.get("low") or 0) > 0 or (cp.get("high") or 0) > 0
                has_evs = bool(evs)
                if not (has_cp or has_evs):
                    filtered.append(d)
            discoveries = filtered
        print(f"  --skip-existing → {before} → {len(discoveries)} records")

    # --limit
    if args.limit and args.limit > 0:
        discoveries = discoveries[: args.limit]
        print(f"  --limit → {len(discoveries)} records")

    # Cost estimate (all modes are ~1 Claude call per record).
    n = len(discoveries)
    est_cost_low = n * 0.20   # magic-allowed: cost-estimator-low-bound
    est_cost_high = n * 0.50  # magic-allowed: cost-estimator-high-bound
    est_minutes_low = max(1, n // (args.parallel * 4))   # magic-allowed: time-estimator-low-bound
    est_minutes_high = max(2, n // (args.parallel * 2))  # magic-allowed: time-estimator-high-bound
    print()
    print(f"PLAN: mode='{args.mode}' on {n} records (parallel={args.parallel})")
    print(f"  estimated cost:  ${est_cost_low:.0f}-${est_cost_high:.0f}")
    print(f"  estimated time:  {est_minutes_low}-{est_minutes_high} min")
    print()

    if not args.execute:
        print("DRY RUN — no Claude calls made, no changes saved.")
        print("Re-run with --execute to actually retrofit.")
        return

    print(f"Executing mode='{args.mode}'...")
    started = datetime.now(timezone.utc)
    succeeded = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futures = {ex.submit(worker, d): d for d in discoveries}
        for fut in as_completed(futures):
            name, summary, error = fut.result()
            if error:
                failed += 1
                print(f"  FAIL  {name}: {summary} ({error[:60]})")
            else:
                succeeded += 1
                print(f"  OK    {name}: {summary}")

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    print()
    print(f"Done in {elapsed/60:.1f} min — {succeeded} succeeded, {failed} failed.")


if __name__ == "__main__":
    main()
