"""Lightweight Pillar rescore — rerun Python scorers against cached facts.

When scoring logic changes — a pillar weight, dimension weight, strength
tier, signal point value, baseline, penalty, or Technical Fit Multiplier
range — cached analyses scored under the old logic produce stale scores.
The normal path is to bump `SCORING_LOGIC_VERSION` and let the next
Inspector visit trigger a full re-Deep-Dive (3 fact extractors + 8
rubric grader calls + 3 briefcase calls per product — ~$5-15 per
company, minutes per company).

This runner does the CHEAP half: re-runs the pure-Python pillar scorers
+ fit-score composer against the ALREADY-CACHED fact drawers and
rubric grades.  Zero Claude calls.  Milliseconds per product.

When NOT to use:
  - A rubric tier definition itself changed (the Claude-graded text) —
    you need to re-run the rubric grader too.  Use
    `intelligence.score()` on affected records instead.
  - Facts themselves are wrong — you need fresh research.  Use
    retrofit_acv.py --mode re-research.

Usage:
    python scripts/rescore_pillars.py                    # dry-run (default)
    python scripts/rescore_pillars.py --execute          # actually save
    python scripts/rescore_pillars.py --company "Cisco"  # filter by name
    python scripts/rescore_pillars.py --limit 5          # test on a few first
    python scripts/rescore_pillars.py --execute --verbose  # log before/after per product

On each save: stamps SCORING_LOGIC_VERSION to the current value so the
record won't get re-researched by Inspector's cache-versioning check.
"""

from __future__ import annotations

import sys
import os
import json
import argparse
import copy
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone

_project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "backend", ".env"))

import scoring_config as cfg  # noqa: E402
from storage import list_analyses, save_analysis  # noqa: E402
from models import (  # noqa: E402
    Product, ProductLababilityFacts, InstructionalValueFacts,
    CustomerFitFacts, GradedSignal, FitScore, PillarScore,
    ProvisioningFacts, LabAccessFacts, ScoringFacts, TeardownFacts,
    ProductComplexityFacts, MasteryStakesFacts, LabVersatilityFacts,
    MarketDemandFacts, SignalEvidence, NumericRange,
)
from pillar_1_scorer import score_product_labability  # noqa: E402
from pillar_2_scorer import score_instructional_value  # noqa: E402
from pillar_3_scorer import score_customer_fit  # noqa: E402
from fit_score_composer import compose_fit_score  # noqa: E402


# ── Dict → dataclass reconstructor ────────────────────────────────────────
#
# The cached analyses are dicts produced by `dataclasses.asdict(...)` at
# save-time.  To re-run the typed scorers we need to rebuild the dataclass
# instances from those dicts.  `fields()` gives us the schema; the type
# annotations tell us how to recurse.  Handles:
#   - Nested dataclasses (SignalEvidence, NumericRange, etc.)
#   - Lists of dataclasses (GradedSignal lists)
#   - Dicts of dataclasses (signals dicts keyed by category)
#   - Primitives pass through.


def _reconstruct(cls, data):
    """Rebuild an instance of `cls` from dict `data`.  Recursive."""
    if data is None:
        return cls() if is_dataclass(cls) else None
    if not is_dataclass(cls):
        return data
    kwargs = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        raw = data[f.name]
        kwargs[f.name] = _reconstruct_field(f.type, raw)
    return cls(**kwargs)


def _reconstruct_field(type_hint, raw):
    """Reconstruct a single field's value based on its type hint."""
    if raw is None:
        return None
    # Resolve string annotations (PEP 563 `from __future__ import annotations`)
    # to the actual type object.  The dataclasses live in `models`, so
    # resolve against that module's namespace.
    if isinstance(type_hint, str):
        import models as models_mod
        try:
            type_hint = eval(type_hint, vars(models_mod))  # safe: controlled module
        except Exception:
            return raw

    origin = getattr(type_hint, "__origin__", None)
    if origin is list:
        inner = type_hint.__args__[0]
        return [_reconstruct_field(inner, item) for item in raw]
    if origin is dict:
        _, val_type = type_hint.__args__
        return {k: _reconstruct_field(val_type, v) for k, v in raw.items()}
    if is_dataclass(type_hint):
        return _reconstruct(type_hint, raw)
    # Primitive — pass through
    return raw


# ── Per-product rescore ───────────────────────────────────────────────────


def _rescore_product(p_dict: dict, analysis: dict, verbose: bool = False) -> dict:
    """Rescore one product in place.  Returns a dict summarizing the delta
    so the runner can log before/after comparisons."""
    product_name = p_dict.get("name", "?")
    delta = {"product": product_name, "pillars": {}}

    # Reconstruct the typed fact drawers
    pl_facts = _reconstruct(
        ProductLababilityFacts, p_dict.get("product_labability_facts") or {}
    )
    iv_grades_raw = p_dict.get("rubric_grades") or {}
    iv_grades: dict[str, list[GradedSignal]] = {
        dim_key: [_reconstruct(GradedSignal, g) for g in grade_list]
        for dim_key, grade_list in iv_grades_raw.items()
    }

    # Pillar 1 — pure Python, reads facts
    pl_pillar = score_product_labability(pl_facts)
    if verbose:
        old_score = (p_dict.get("fit_score") or {}).get("product_labability", {}).get("score", 0)
        delta["pillars"]["product_labability"] = {"old": old_score, "new": pl_pillar.score}

    # Pillar 2 — pure Python, reads grades
    product_category = p_dict.get("category") or ""
    iv_pillar = score_instructional_value(product_category, iv_grades)
    if verbose:
        old_score = (p_dict.get("fit_score") or {}).get("instructional_value", {}).get("score", 0)
        delta["pillars"]["instructional_value"] = {"old": old_score, "new": iv_pillar.score}

    # Pillar 3 — reads company-level grades from the analysis, not from the product
    cf_grades_raw = analysis.get("customer_fit_rubric_grades") or {}
    cf_grades: dict[str, list[GradedSignal]] = {
        dim_key: [_reconstruct(GradedSignal, g) for g in grade_list]
        for dim_key, grade_list in cf_grades_raw.items()
    }
    org_type = analysis.get("organization_type") or ""
    cf_pillar = score_customer_fit(org_type, cf_grades)
    if verbose:
        old_score = (p_dict.get("fit_score") or {}).get("customer_fit", {}).get("score", 0)
        delta["pillars"]["customer_fit"] = {"old": old_score, "new": cf_pillar.score}

    # Compose the fit score.  Use the product's current orchestration method
    # for the Technical Fit Multiplier calculation.
    orchestration = str(p_dict.get("orchestration_method") or "").lower()
    from dataclasses import asdict
    fit = FitScore(
        product_labability=pl_pillar,
        instructional_value=iv_pillar,
        customer_fit=cf_pillar,
    )
    compose_fit_score(fit, orchestration)

    if verbose:
        old_total = (p_dict.get("fit_score") or {}).get("total", 0)
        delta["total"] = {"old": old_total, "new": fit.total}

    # Serialize back to dict form.
    p_dict["fit_score"] = asdict(fit)
    return delta


# ── Main ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="actually save (default: dry-run)")
    parser.add_argument("--company", default=None,
                        help="only rescore analyses whose company_name contains this (case-insensitive)")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after N analyses (useful for smoke tests)")
    parser.add_argument("--verbose", action="store_true",
                        help="print before/after pillar deltas per product")
    args = parser.parse_args()

    all_analyses = list_analyses()
    print(f"Loaded {len(all_analyses)} analyses from cache.")

    if args.company:
        needle = args.company.lower()
        all_analyses = [a for a in all_analyses
                        if needle in (a.get("company_name") or "").lower()]
        print(f"Filtered by --company '{args.company}' -> {len(all_analyses)} analyses.")

    if args.limit:
        all_analyses = all_analyses[:args.limit]
        print(f"Limited to first {args.limit} analyses.")

    if not all_analyses:
        print("Nothing to rescore.")
        return

    print(f"\nPLAN: rescore {len(all_analyses)} analyses using current "
          f"SCORING_LOGIC_VERSION = '{cfg.SCORING_LOGIC_VERSION}'")
    print("Zero Claude calls, pure Python.  Expected wall time: a few seconds.\n")

    if not args.execute:
        print("DRY RUN - no changes written.  Re-run with --execute to save.")
        print("Tip: --verbose shows per-product pillar deltas.")

    changed = 0
    errors = 0
    for analysis in all_analyses:
        company = analysis.get("company_name", "?")
        products = analysis.get("products") or []
        try:
            for p in products:
                delta = _rescore_product(p, analysis, verbose=args.verbose)
                if args.verbose:
                    print(f"  {company} > {delta['product']}: "
                          f"PL {delta['pillars'].get('product_labability', {})} "
                          f"IV {delta['pillars'].get('instructional_value', {})} "
                          f"CF {delta['pillars'].get('customer_fit', {})} "
                          f"Total {delta.get('total', {})}")

            if args.execute:
                # Stamp and save.  save_analysis requires _scoring_logic_version
                # and analyzed_at to be pre-set by the caller (Phase 6 rule).
                analysis["_scoring_logic_version"] = cfg.SCORING_LOGIC_VERSION
                analysis["analyzed_at"] = (
                    analysis.get("analyzed_at")
                    or datetime.now(timezone.utc).isoformat()
                )
                save_analysis(analysis)
                changed += 1
            else:
                changed += 1  # count as "would-change" in dry-run
        except Exception as e:
            errors += 1
            print(f"  ERROR on {company}: {type(e).__name__}: {e}")

    print(f"\nDone.  {'Saved' if args.execute else 'Would save'}: {changed}/{len(all_analyses)} analyses.  "
          f"Errors: {errors}.")


if __name__ == "__main__":
    main()
