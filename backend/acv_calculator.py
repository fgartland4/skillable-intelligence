"""ACV Potential calculator — deterministic Python math.

Architectural role
------------------
Annual Contract Value (ACV) is calculated, not scored.  The researcher's
job is to extract per-product and per-company AUDIENCE facts into the
fact drawer (install base, partner community, employee subset, cert
exam takers, event attendees).  This module's job is everything else:
build the list of consumption motions from those facts, compute per-
motion hours × rate, sum to total ACV, and assign the ACV tier.

Pure Python.  Zero Claude.  Zero hardcoded numbers — every rate,
threshold, motion, and mapping comes from `scoring_config.py`.

The ACV model (Platform-Foundation 2026-04-08):
    For each of the five motions:
        hours_low  = pop_low  × adoption_pct × hours_low
        hours_high = pop_high × adoption_pct × hours_high
        acv_low    = hours_low  × rate
        acv_high   = hours_high × rate
    Total ACV = sum across motions.

The only source of range in the final number is AUDIENCE (population).
Adoption and hours are single locked values from `cfg.CONSUMPTION_MOTIONS`.
Rate is single per tier from `cfg.RATE_TABLES`, looked up by orchestration
method via `cfg.ORCHESTRATION_TO_RATE_TIER`.

Two-step pipeline
-----------------
    populate_acv_motions(product, company_analysis) -> None
        Reads the fact drawer and builds the five ConsumptionMotion
        records on `product.acv_potential.motions`.  Run once, at
        score-time, immediately after the three pillar scorers finish.
        Company-level motions (Partner, Events) read from the shared
        CustomerFitFacts; per-product motions (Customer, Employee, Cert)
        read from that product's InstructionalValueFacts.market_demand.

    compute_acv_potential(product_dict) -> dict
        Reads the motions already populated on the product dict and
        computes per-motion annual hours + dollars, total ACV range,
        rate tier, and ACV tier.  Mutates in place.  Run at save-time
        AND on every cache reload so rate-table retunes propagate.

This module lives alongside fit_score_composer.py as the second
"composition" module in the Score layer.  Each module has one job.
"""
from __future__ import annotations

import logging
from typing import Any

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


# ═══════════════════════════════════════════════════════════════════════════════
# Public: populate_acv_motions — score-time fact → motions bridge
# ═══════════════════════════════════════════════════════════════════════════════

def _numeric_range_to_tuple(nr: Any) -> tuple[int, int]:
    """Coerce a NumericRange dataclass OR a dict into (low, high)."""
    if nr is None:
        return 0, 0
    low = getattr(nr, "low", None)
    high = getattr(nr, "high", None)
    if low is None and high is None and isinstance(nr, dict):
        low = nr.get("low")
        high = nr.get("high")
    low = int(low or 0)
    high = int(high or 0)
    if low > high:
        low, high = high, low
    return low, high


def _read_population(source: str, product: Any, company_analysis: Any) -> tuple[int, int]:
    """Resolve a motion's population range from the fact drawer.

    `source` is one of the strings named on
    `scoring_config.ConsumptionMotion.population_source`:

      "product:install_base"
      "product:employee_subset_size"
      "product:cert_annual_sit_rate"
      "company:channel_partner_se_population"
      "company:events_attendance_sum"

    Returns (0, 0) when the fact drawer is missing or the named field
    isn't populated — the motion will contribute 0 to the total, which
    is the honest zero-when-absent semantics per Platform-Foundation.
    """
    if not source or ":" not in source:
        return 0, 0

    scope, field = source.split(":", 1)

    if scope == "product":
        iv_facts = getattr(product, "instructional_value_facts", None)
        if iv_facts is None:
            return 0, 0
        market_demand = getattr(iv_facts, "market_demand", None)
        if market_demand is None:
            return 0, 0
        nr = getattr(market_demand, field, None)
        return _numeric_range_to_tuple(nr)

    if scope == "company":
        cf_facts = getattr(company_analysis, "customer_fit_facts", None)
        if cf_facts is None:
            return 0, 0
        if field == "events_attendance_sum":
            # Sum all named events. events_attendance is dict[str, NumericRange].
            events = getattr(cf_facts, "events_attendance", None) or {}
            if not isinstance(events, dict):
                return 0, 0
            low_total = 0
            high_total = 0
            for event_range in events.values():
                lo, hi = _numeric_range_to_tuple(event_range)
                low_total += lo
                high_total += hi
            return low_total, high_total
        nr = getattr(cf_facts, field, None)
        return _numeric_range_to_tuple(nr)

    return 0, 0


def populate_acv_motions(product: Any, company_analysis: Any) -> None:
    """Build the five ConsumptionMotion records on a Product dataclass.

    Reads per-product audience facts from
    `product.instructional_value_facts.market_demand` and company-level
    audience facts from `company_analysis.customer_fit_facts`. Uses the
    locked adoption_pct and hours values from `cfg.CONSUMPTION_MOTIONS`.

    Mutates `product.acv_potential.motions` in place. Does NOT compute
    derived fields (hrs, acv, rate, tier) — call `compute_acv_on_product`
    after this if you want the full populated output.

    Best-effort: any missing fact yields zero population for that motion,
    which contributes zero to the final ACV. Honest zeros beat invented
    numbers.
    """
    from models import ConsumptionMotion as ModelMotion, ACVPotential

    # Look up org-type adoption overrides. The default rates on
    # CONSUMPTION_MOTIONS apply to software companies. Other org types
    # (academic, training org, GSI, etc.) have fundamentally different
    # adoption patterns — per Platform-Foundation.
    org_type = ""
    if company_analysis is not None:
        org_type = getattr(company_analysis, "org_type", "") or ""
        if not org_type:
            # Try the discovery-level org_type
            disc = getattr(company_analysis, "discovery_data", None) or {}
            org_type = disc.get("organization_type") or ""
    # Normalize to the CF baseline key format
    normalized_org = cfg.ORG_TYPE_NORMALIZATION.get(org_type.lower().replace(" ", "_"), "")
    adoption_overrides = cfg.ACV_ORG_ADOPTION_OVERRIDES.get(normalized_org, {})

    motions: list[ModelMotion] = []
    for cfg_motion in cfg.CONSUMPTION_MOTIONS:
        pop_low, pop_high = _read_population(
            cfg_motion.population_source, product, company_analysis,
        )
        # Apply org-type adoption override if available
        adoption = adoption_overrides.get(cfg_motion.label, cfg_motion.adoption_pct)
        motions.append(ModelMotion(
            label=cfg_motion.label,
            population_low=pop_low,
            population_high=pop_high,
            hours_low=cfg_motion.hours_low,
            hours_high=cfg_motion.hours_high,
            adoption_pct=adoption,
            rationale=cfg_motion.description,
        ))

    # ── Bug 13 fix: derive cert audience deterministically when missing ──
    # If the researcher didn't find cert_annual_sit_rate but install_base
    # exists, derive it as ~2% of install_base (software companies) or
    # ~10% (training orgs / industry authorities). Python computes, AI
    # doesn't touch it. Per Platform-Foundation ACV adoption patterns.
    cert_motion = next((m for m in motions if m.label == "Certification (PBT)"), None)
    customer_motion = next((m for m in motions if m.label == "Customer Training & Enablement"), None)
    if cert_motion and customer_motion:
        if (cert_motion.population_low or 0) == 0 and (customer_motion.population_low or 0) > 0:
            # Derive: ~2% of customer training audience for software companies
            derived = max(1, int(customer_motion.population_low * cfg.CERT_SIT_DERIVATION_PCT))
            cert_motion.population_low = derived
            cert_motion.population_high = derived

    if getattr(product, "acv_potential", None) is None:
        product.acv_potential = ACVPotential()
    product.acv_potential.motions = motions


def compute_acv_on_product(product: Any, company_analysis: Any) -> None:
    """Score-time ACV: populate motions from facts + compute derived fields.

    Called from `intelligence.score()` after the three per-pillar scorers
    finish, before products are serialized to dicts. Operates entirely on
    the Product dataclass + CompanyAnalysis dataclass.

    Steps:
      1. Populate motions from the fact drawer (populate_acv_motions).
      2. Look up the rate tier from the product's orchestration method.
      3. Compute per-motion annual hours × rate, sum to total.
      4. Assign the ACV tier from the computed high-end dollars.

    Mutates `product.acv_potential` in place with fully populated fields.
    The serialized form (via `asdict(product)`) then carries everything
    the template needs to render the hero widget and the ACV by Use Case
    table without any further computation.

    `compute_acv_potential(product_dict)` does the same math on the dict
    form and is the cache-reload path. Both share the helpers below.
    """
    populate_acv_motions(product, company_analysis)

    orchestration_method = getattr(product, "orchestration_method", "") or ""
    tier_name, rate = _resolve_rate(orchestration_method)

    acv = product.acv_potential
    total_hours_low = 0.0
    total_hours_high = 0.0

    for m in acv.motions:
        try:
            pop_low = float(m.population_low or 0)
            pop_high = float(m.population_high or 0)
            adopt = float(m.adoption_pct or 0)
            hrs_low = float(m.hours_low or 0)
            hrs_high = float(m.hours_high or 0)
        except (TypeError, ValueError):
            continue

        m_hours_low = pop_low * adopt * hrs_low
        m_hours_high = pop_high * adopt * hrs_high
        total_hours_low += m_hours_low
        total_hours_high += m_hours_high

    acv_low_dollars = total_hours_low * rate
    acv_high_dollars = total_hours_high * rate

    acv.annual_hours_low = round(total_hours_low)
    acv.annual_hours_high = round(total_hours_high)
    acv.acv_low = round(acv_low_dollars)
    acv.acv_high = round(acv_high_dollars)
    acv.rate_per_hour = rate
    acv.acv_tier = _resolve_acv_tier(acv_high_dollars)
    # Audit trail — one line the widget can render for transparency.
    acv.methodology_note = (
        f"{len(acv.motions)} motion ACV · rate tier {tier_name} @ ${rate:.0f}/hr"
    )
