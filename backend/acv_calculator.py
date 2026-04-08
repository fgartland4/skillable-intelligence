"""ACV Potential calculator — deterministic Python math.

Architectural role
------------------
Annual Contract Value (ACV) is calculated, not scored.  The AI's job
is to estimate per-motion population, adoption %, and hours per
learner.  This module's job is everything else: per-motion hours,
total hours, rate lookup by orchestration method, dollar conversion,
and tier assignment from dollar thresholds.

Pure Python.  Zero Claude.  Zero hardcoded numbers — every rate,
threshold, and mapping comes from `scoring_config.py` (Define-Once).

Frank's model (locked 2026-04-06):
    For each motion:
        hours_low  = pop_low  × adoption × hours_per_learner_low
        hours_high = pop_high × adoption × hours_per_learner_high
        acv_low    = hours_low  × rate
        acv_high   = hours_high × rate
    Total ACV = sum across motions.

Rate per hour is looked up from the four named rate variables in
scoring_config.py (CLOUD_LABS_RATE, VM_LOW_RATE, VM_MID_RATE,
VM_HIGH_RATE, SIMULATION_RATE) via the cfg.ORCHESTRATION_TO_RATE_TIER
mapping — seller-facing rate tiers keyed on orchestration method.

Public surface
--------------
    compute_acv_potential(product: dict) -> dict
        Recompute ACV on a product dict in place.  Returns the updated
        acv_potential sub-dict (or {} if there's nothing to compute).

This module lives alongside fit_score_composer.py as the second
"composition" module in the Score layer — pillar scorers produce the
three PillarScores, the composer composes the Fit Score, this module
calculates the ACV Potential.  Each has one job.
"""
from __future__ import annotations

import logging

import scoring_config as cfg

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _resolve_acv_tier(acv_high_dollars: float) -> str:
    """Map a computed ACV high-end dollar value to a tier label.

    Reads thresholds from cfg.ACV_TIER_HIGH_THRESHOLD and
    cfg.ACV_TIER_MEDIUM_THRESHOLD.  Evaluated against the high end of
    the range so a deal is sized at its upside potential.
    """
    if acv_high_dollars >= cfg.ACV_TIER_HIGH_THRESHOLD:
        return "high"
    if acv_high_dollars >= cfg.ACV_TIER_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def _resolve_rate(orchestration_method: str) -> tuple[str, float]:
    """Map a product's orchestration method to (tier_name, $/hour).

    Falls back to cfg.DEFAULT_RATE_TIER_NAME at cfg.VM_MID_RATE when
    the orchestration method is empty, unknown, or doesn't map to any
    known tier — the everyday admin-lab default, conservatively
    neither cheap nor pricey.

    Reads RateTier.delivery_path and RateTier.rate_low from
    cfg.RATE_TABLES (single-value model — rate_low == rate_high per
    Frank's locked rates).
    """
    key = (orchestration_method or "").strip().lower()
    tier_name = cfg.ORCHESTRATION_TO_RATE_TIER.get(key, cfg.DEFAULT_RATE_TIER_NAME)
    for tier in cfg.RATE_TABLES:
        if tier.delivery_path == tier_name:
            return tier_name, float(tier.rate_low)
    # Should not happen — RATE_TABLES is the source of truth and the
    # mapping only points at delivery_path values that exist in it.
    # Final safety net.
    return cfg.DEFAULT_RATE_TIER_NAME, float(cfg.VM_MID_RATE)


# ═══════════════════════════════════════════════════════════════════════════════
# Public: compute_acv_potential
# ═══════════════════════════════════════════════════════════════════════════════

def compute_acv_potential(product: dict) -> dict:
    """Recompute ACV from the AI's motion estimates using deterministic math.

    Reads from product:
      - acv_potential.motions[] — AI-emitted population / adoption /
        hours-per-learner estimates per consumption motion
      - orchestration_method    — AI-emitted fabric choice (used for
        rate lookup)

    Mutates product["acv_potential"] in place with computed fields:
      - motions[i].hrs_low / hrs_high   — per-motion annual hours
      - motions[i].acv_low / acv_high   — per-motion dollar contribution
      - annual_hours_low / annual_hours_high — totals across motions
      - acv_low / acv_high               — total dollar range
      - rate_per_hour                    — looked-up hourly rate
      - rate_tier_name                   — which RATE_TABLES tier was chosen
      - acv_tier                         — "high" | "medium" | "low"

    Returns the updated acv_potential dict, or {} if there's nothing
    to compute (missing or malformed acv_potential on the product).

    Defends against missing or malformed motion data — any motion
    that's not a dict or has zero/missing inputs contributes zero
    hours rather than raising.
    """
    acv = product.get("acv_potential")
    if not isinstance(acv, dict):
        return {}

    motions = acv.get("motions") or []
    if not isinstance(motions, list):
        motions = []

    tier_name, rate = _resolve_rate(product.get("orchestration_method") or "")

    total_hours_low = 0.0
    total_hours_high = 0.0

    for m in motions:
        if not isinstance(m, dict):
            continue
        try:
            pop_low = float(m.get("population_low") or 0)
            pop_high = float(m.get("population_high") or 0)
            adopt = float(m.get("adoption_pct") or 0)
            hrs_low = float(m.get("hours_low") or 0)
            hrs_high = float(m.get("hours_high") or 0)
        except (TypeError, ValueError):
            continue

        m_hours_low = pop_low * adopt * hrs_low
        m_hours_high = pop_high * adopt * hrs_high
        m_acv_low = m_hours_low * rate
        m_acv_high = m_hours_high * rate

        # Stash per-motion computed fields so the widget can render
        # them without redoing the math in Jinja.
        m["hrs_low"] = round(m_hours_low)
        m["hrs_high"] = round(m_hours_high)
        m["acv_low"] = round(m_acv_low)
        m["acv_high"] = round(m_acv_high)

        total_hours_low += m_hours_low
        total_hours_high += m_hours_high

    acv_low_dollars = total_hours_low * rate
    acv_high_dollars = total_hours_high * rate

    acv["annual_hours_low"] = round(total_hours_low)
    acv["annual_hours_high"] = round(total_hours_high)
    acv["acv_low"] = round(acv_low_dollars)
    acv["acv_high"] = round(acv_high_dollars)
    acv["rate_per_hour"] = rate
    acv["rate_tier_name"] = tier_name
    acv["acv_tier"] = _resolve_acv_tier(acv_high_dollars)

    return acv
