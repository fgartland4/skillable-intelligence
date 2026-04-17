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

def rebuild_acv_motions_from_facts(product: dict, analysis: dict) -> None:
    """Rebuild ACV motions from the fact drawer on a cached product dict.

    This is the cache-reload equivalent of populate_acv_motions(). It reads
    the serialized fact drawer (instructional_value_facts.market_demand,
    customer_fit_facts) from the dict form and rebuilds the five consumption
    motions with all unified model rules: org-type overrides, Industry
    Authority deflation, training maturity multipliers, open source tiers,
    wrapper org audience caps, cert sanity cap.

    Called by recompute_analysis() on every page load so ACV motions stay
    current when the model changes — without re-running the researcher.

    Pure Python. Zero Claude calls. Zero research.
    """
    # Read org type from discovery or analysis
    org_type = ""
    disc_data = analysis.get("_discovery_data") or {}
    if disc_data:
        org_type = disc_data.get("organization_type") or ""
    if not org_type:
        org_type = analysis.get("organization_type") or "software_company"
    normalized_org = cfg.ORG_TYPE_NORMALIZATION.get(
        org_type.lower().replace(" ", "_"), "")

    # Look up org-type overrides
    adoption_overrides = cfg.ACV_ORG_ADOPTION_OVERRIDES.get(normalized_org, {})
    label_overrides = cfg.ACV_ORG_MOTION_LABELS.get(normalized_org, {})
    hours_overrides = cfg.ACV_ORG_HOURS_OVERRIDES.get(normalized_org, {})

    # Read fact drawers from the product dict
    iv_facts = product.get("instructional_value_facts") or {}
    md = iv_facts.get("market_demand") or {}
    pl_facts = product.get("product_labability_facts") or {}
    la_facts = pl_facts.get("lab_access") or {}

    # Read company-level facts
    cf_facts = analysis.get("_customer_fit_facts") or {}
    # Also check per-product customer_fit_facts (Phase F broadcast)
    p_cf = product.get("customer_fit_facts") or {}
    if not cf_facts:
        cf_facts = p_cf

    # Detect open source
    is_open_source = False
    training_license = la_facts.get("training_license", "") or ""
    if training_license == "none":
        is_open_source = True

    # Detect training signals from the dict form
    company_signals = disc_data.get("company_signals", {}) or {}
    t_signals = {
        "atp_large": False, "cert_active": False,
        "no_signals": True, "license_blocked": False,
        "has_training_org": False,
    }

    atp = company_signals.get("atp_program", "") or ""
    if atp and atp.lower() not in ("no", "none", "n/a", ""):
        t_signals["no_signals"] = False
        t_signals["has_training_org"] = True
        for token in ("50+", "100+", "200+", "500+", "1000+", "1,000+"):
            if token in atp:
                t_signals["atp_large"] = True
                break

    training_programs = company_signals.get("training_programs", "") or ""
    if training_programs and training_programs.lower() not in ("no", "none", "n/a", ""):
        t_signals["no_signals"] = False
        t_signals["has_training_org"] = True

    cert_inc = product.get("cert_inclusion", "") or ""
    if not cert_inc:
        cert_inc = (iv_facts.get("market_demand") or {}).get("cert_bodies_mentioning", [])
        if cert_inc:
            t_signals["cert_active"] = True
            t_signals["no_signals"] = False
            t_signals["has_training_org"] = True
    elif isinstance(cert_inc, str) and cert_inc.lower() not in ("no", "none", "n/a", ""):
        t_signals["cert_active"] = True
        t_signals["no_signals"] = False
        t_signals["has_training_org"] = True

    if training_license == "blocked":
        t_signals["license_blocked"] = True

    # Helper to read a numeric range from the dict form
    def _nr(field_dict):
        if not isinstance(field_dict, dict):
            return 0, 0
        low = int(field_dict.get("low") or 0)
        high = int(field_dict.get("high") or 0)
        if low > high:
            low, high = high, low
        return low, high

    # ── Preserve-legacy-populations snapshot ──────────────────────────────
    # Frank's Rule #1: research is immutable. Older analyses (pre-fact-drawer
    # era) have real motion populations saved on the product — produced by
    # the original scoring run — but empty `instructional_value_facts` and
    # `customer_fit_facts` drawers. Rebuilding purely from null facts would
    # wipe those populations to zero, zeroing the product's ACV and making
    # it look like no Deep Dive exists. Capture the existing populations
    # BEFORE the rebuild so we can restore them when the fact drawer has
    # nothing new to say.
    #
    # Rule: fact-drawer value wins when present (facts are the new truth);
    # saved value preserved when fact is null/0 (never regress knowledge).
    _existing_populations: dict[str, tuple[int, int]] = {}
    _existing_motions = (product.get("acv_potential") or {}).get("motions") or []
    for _m in _existing_motions:
        try:
            _existing_populations[_m.get("label", "")] = (
                int(_m.get("population_low") or 0),
                int(_m.get("population_high") or 0),
            )
        except (TypeError, ValueError):
            pass

    # Build motions
    motions = []
    customer_pop = 0

    # Resolve the Motion 1 audience source for this org type.
    # Software / Enterprise Software → estimated_user_base (via install_base fact)
    # Wrapper orgs (Academic, ILT, ELP, GSI, VAR, Distributor, Content Dev) →
    #   annual_enrollments_estimate from the product dict
    # Industry Authority → install_base then deflated
    customer_audience_source = cfg.get_acv_audience_source_for_org_type(normalized_org)
    using_annual_enrollments = (
        customer_audience_source == cfg.ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS
    )

    for cfg_motion in cfg.CONSUMPTION_MOTIONS:
        pop_low, pop_high = 0, 0

        # Read population from the fact drawer
        source = cfg_motion.population_source
        if source == "product:install_base":
            # Motion 1 (Customer Training) audience — routed by org type.
            if using_annual_enrollments:
                # Wrapper org: use the wrapper's per-program enrollment count,
                # NOT the underlying technology's global user base.
                ann_enr = product.get("annual_enrollments_estimate") or 0
                try:
                    ae_int = int(ann_enr)
                except (TypeError, ValueError):
                    ae_int = 0
                pop_low = pop_high = ae_int
            else:
                # Software / Enterprise Software / Industry Authority:
                # use install_base from the Pillar 2 fact drawer.
                pop_low, pop_high = _nr(md.get("install_base"))
                # Fallback: when P2 research didn't populate install_base
                # (null values on cached analyses or thin research runs),
                # use the product's discovery-level estimated_user_base.
                # Never leave Customer Training audience at 0 when
                # discovery already has a number. Frank's Rule #1 — don't
                # regress what prior research knew. GitHub Enterprise case.
                if pop_low == 0 and pop_high == 0:
                    eub = product.get("estimated_user_base")
                    eub_int = 0
                    if isinstance(eub, (int, float)):
                        eub_int = int(eub)
                    elif isinstance(eub, str) and eub:
                        # Parse "~500K", "~2M", "~1B" etc.
                        s = eub.replace("~", "").replace(",", "").strip().upper()
                        try:
                            if s.endswith("M"):
                                eub_int = int(float(s[:-1]) * 1_000_000)  # magic-allowed: million multiplier
                            elif s.endswith("K"):
                                eub_int = int(float(s[:-1]) * 1_000)  # magic-allowed: thousand multiplier
                            elif s.endswith("B"):
                                eub_int = int(float(s[:-1]) * 1_000_000_000)  # magic-allowed: billion multiplier
                            else:
                                eub_int = int(float(s))
                        except (ValueError, IndexError):
                            eub_int = 0
                    if eub_int > 0:
                        pop_low = pop_high = eub_int

                # ── Archetype-aware audience cap (Frank 2026-04-16) ──────
                # Different product archetypes have different realistic
                # training populations. Full-ceiling enterprise products
                # (Azure, M365 admin, Workday) can legitimately have 1M+
                # trainable admins. Specialists (Fortinet, Nutanix) tighter.
                # IC / creative / consumer tighter still. See
                # scoring_config.AUDIENCE_TIERS_BY_ARCHETYPE.
                archetype = (product.get("archetype") or "").strip()
                tiers = cfg.get_audience_tiers_for_archetype(archetype)
                for threshold, cap in tiers:
                    if pop_high > threshold:
                        if cap is not None:
                            pop_low = min(pop_low, cap)
                            pop_high = cap
                        break
        elif source == "product:employee_subset_size":
            pop_low, pop_high = _nr(md.get("employee_subset_size"))
        elif source == "product:cert_annual_sit_rate":
            pop_low, pop_high = _nr(md.get("cert_annual_sit_rate"))
        elif source == "company:channel_partner_se_population":
            pop_low, pop_high = _nr(cf_facts.get("channel_partner_se_population"))
        elif source == "company:events_attendance_sum":
            events = cf_facts.get("events_attendance") or {}
            for evt_range in events.values():
                lo, hi = _nr(evt_range)
                pop_low += lo
                pop_high += hi

        # Preserve-legacy-populations: if the fact drawer yielded nothing
        # for this motion but we have a non-zero saved population from an
        # older scoring run, restore it. Honors Rule #1 — research is
        # immutable; we never regress what prior runs knew.
        if pop_low == 0 and pop_high == 0:
            # Look up by the canonical motion label (the org-type label
            # rewrite happens later, so we key off cfg_motion.label as the
            # saved motions may also be under the rewritten label — check
            # both)
            saved = _existing_populations.get(cfg_motion.label) or \
                    _existing_populations.get(
                        label_overrides.get(cfg_motion.label, cfg_motion.label)
                    )
            if saved and (saved[0] > 0 or saved[1] > 0):
                pop_low, pop_high = saved

        is_customer_motion = cfg_motion.label == "Customer Training & Enablement"

        # Industry Authority deflation — only IA still reads install_base for
        # Customer Training. TRAINING ORG now uses annual_enrollments_estimate
        # (no deflation needed — the field IS the wrapper's audience).
        if is_customer_motion and normalized_org == "INDUSTRY AUTHORITY":
            pop_low = _apply_industry_authority_deflation(pop_low)
            pop_high = _apply_industry_authority_deflation(pop_high)

        # Wrapper-org audience cap (R1) — applies ONLY when the wrapper org
        # is falling back to install_base (no annual_enrollments_estimate
        # populated yet on legacy records). When annual_enrollments_estimate
        # is present, that field IS the wrapper's audience — capping it
        # would undercount honest data.
        if (is_customer_motion
                and normalized_org in cfg.ACV_WRAPPER_ORG_TYPES
                and not using_annual_enrollments):
            total_emp = 0
            te = cf_facts.get("total_employees")
            if isinstance(te, dict):
                total_emp = int(te.get("low") or 0)
            if total_emp > 0:
                audience_cap = max(
                    int(total_emp * cfg.ACV_WRAPPER_ORG_AUDIENCE_CAP_FRACTION),
                    cfg.ACV_WRAPPER_ORG_AUDIENCE_FLOOR)
                pop_low = min(pop_low, audience_cap)
                pop_high = min(pop_high, audience_cap)

        if is_customer_motion:
            customer_pop = max(pop_low, pop_high)

        # Adoption with org-type override
        adoption = adoption_overrides.get(cfg_motion.label, cfg_motion.adoption_pct)
        display_label = label_overrides.get(cfg_motion.label, cfg_motion.label)
        hrs = hours_overrides.get(cfg_motion.label, cfg_motion.hours_low)

        # ── Archetype-aware hours override (Frank 2026-04-16) ──
        # Deep infrastructure / CAD / security ops labs are longer;
        # IC / creative / consumer shorter. Org-type override still wins.
        if cfg_motion.label not in hours_overrides:
            p_archetype = (product.get("archetype") or "").strip()
            hrs = cfg.get_hours_for_archetype_motion(p_archetype, cfg_motion.label, hrs)

        # Customer Training adoption by category tier — Software / Enterprise
        # Software only. Specialist categories (cybersecurity, cloud infra,
        # networking) get higher adoption (8%) than general-purpose (4%) or
        # consumer (1%). Wrapper orgs keep their org-level overrides because
        # their adoption dynamics come from delivery model, not category.
        # Per Platform-Foundation → "Customer Training adoption by category tier".
        if (is_customer_motion
                and normalized_org in cfg.CATEGORY_TIER_ELIGIBLE_ORG_TYPES):
            category = product.get("category") or ""
            adoption = cfg.get_customer_training_adoption_for_category(category)

        # Open source tiering
        if is_open_source and is_customer_motion:
            if t_signals["has_training_org"]:
                adoption *= cfg.OPEN_SOURCE_WITH_TRAINING_MULTIPLIER
            else:
                adoption *= cfg.OPEN_SOURCE_PURE_MULTIPLIER

        # Training maturity multipliers
        if is_customer_motion:
            if t_signals["atp_large"]:
                adoption *= cfg.ACV_TRAINING_MATURITY_MULTIPLIERS["atp_large"]
            if t_signals["cert_active"]:
                adoption *= cfg.ACV_TRAINING_MATURITY_MULTIPLIERS["cert_active"]
            if t_signals["no_signals"]:
                adoption *= cfg.ACV_TRAINING_MATURITY_MULTIPLIERS["no_signals"]
            if t_signals["license_blocked"]:
                adoption *= cfg.ACV_TRAINING_MATURITY_MULTIPLIERS["license_blocked"]
            adoption = min(adoption, cfg.ACV_TRAINING_MATURITY_ADOPTION_CAP)

            # ── Scale-aware adoption cap (Frank 2026-04-16) ──
            # After all multipliers, cap effective adoption based on
            # audience size. Skillable's realistic share of a giant
            # software-company training market is 1-3%, not 15%.
            # EXEMPT wrapper org types (ELP, ILT, Academic, GSI, etc.) —
            # their calibrated rates already encode realistic Skillable
            # share for their delivery model. See Skillsoft benchmark in
            # unified-acv-model.md.
            wrapper_org_types = (
                "ENTERPRISE LEARNING PLATFORM", "TRAINING ORG",
                "ACADEMIC", "SYSTEMS INTEGRATOR", "VAR",
                "TECH DISTRIBUTOR", "CONTENT DEVELOPMENT",
                "PROFESSIONAL SERVICES", "LMS PROVIDER",
            )
            if normalized_org not in wrapper_org_types:
                audience = max(pop_low, pop_high)
                scale_ceiling = cfg.get_scale_aware_adoption_ceiling(audience)
                if scale_ceiling is not None:
                    adoption = min(adoption, scale_ceiling)

        motions.append({
            "label": display_label,
            "population_low": pop_low,
            "population_high": pop_high,
            "hours_low": hrs,
            "hours_high": hrs,
            "adoption_pct": round(adoption, 4),  # magic-allowed: round for display
            "rationale": cfg_motion.description,
        })

    # Cert cap (R4)
    cert_labels = {"Certification (PBT)", "Course Exams"}
    customer_labels = {"Customer Training & Enablement", "Student Training",
                       "Training Participants", "Client End Users",
                       "Platform & ILT Learners", "Classroom Students",
                       "Internal Consultants", "Internal Practitioners"}
    cert_m = next((m for m in motions if m["label"] in cert_labels), None)
    cust_m = next((m for m in motions if m["label"] in customer_labels), None)
    if cert_m and cust_m:
        c_pop = max(cust_m.get("population_low", 0), cust_m.get("population_high", 0))
        cert_pop = max(cert_m.get("population_low", 0), cert_m.get("population_high", 0))
        if c_pop > 0:
            cert_cap = max(1, int(c_pop * cfg.ACV_CERT_MAX_FRACTION_OF_INSTALL_BASE))
            if cert_pop > cert_cap:
                cert_m["population_low"] = cert_cap
                cert_m["population_high"] = cert_cap
            elif cert_pop == 0:
                derived = max(1, int(c_pop * cfg.CERT_SIT_DERIVATION_PCT))
                cert_m["population_low"] = derived
                cert_m["population_high"] = derived

    # Write the rebuilt motions onto the product dict
    if "acv_potential" not in product or not isinstance(product.get("acv_potential"), dict):
        product["acv_potential"] = {}
    product["acv_potential"]["motions"] = motions


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
        log.warning("compute_acv_potential: product %s has no acv_potential dict",
                    product.get("name", "?"))
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

    # ── Fit Score gate (Frank 2026-04-16, replaces PL-only gate) ─────────
    # ACV scales linearly with the three-pillar Fit Score. Fit Score
    # already combines Product Labability (50%) + Instructional Value
    # (20%) + Customer Fit (30%) with the asymmetric Technical Fit
    # Multiplier that drags IV+CF when PL is low.
    # Using Fit Score as the gate means:
    #   - Low PL → Fit Score drops → ACV drops (previous PL-only behavior)
    #   - Low CF (weak training infrastructure) → Fit Score drops → ACV drops
    #     (new — "$10M from a company with no training infra isn't real")
    #   - Low IV (no training market) → Fit Score drops → ACV drops
    #     (new — Acrobat-class consumer tools)
    # One formula, three pillars, consistent with Fit Score composition.
    # Linear: gated_acv = raw_acv × (Fit_Score / 100).
    fit_score = 0
    try:
        fs = product.get("fit_score") or {}
        # Prefer authoritative total_override (recomputed with live config)
        # over cached .total. recompute_analysis computes Fit Score BEFORE
        # ACV so total_override is populated when this function runs.
        fit_score = int(fs.get("total_override") or fs.get("total") or fs.get("_total") or 0)
    except (TypeError, ValueError, AttributeError):
        fit_score = 0
    if fit_score > 0:
        fit_factor = fit_score / 100  # magic-allowed: linear fit score factor denominator (percentage)
        acv_low_dollars *= fit_factor
        acv_high_dollars *= fit_factor

    acv["annual_hours_low"] = round(total_hours_low)
    acv["annual_hours_high"] = round(total_hours_high)
    acv["acv_low"] = round(acv_low_dollars)
    acv["acv_high"] = round(acv_high_dollars)
    acv["rate_per_hour"] = rate
    acv["rate_tier_name"] = tier_name
    acv["acv_tier"] = _resolve_acv_tier(acv_high_dollars)
    acv["fit_score_factor"] = round(fit_score / 100, 2) if fit_score > 0 else 0.0  # magic-allowed: percentage denominator
    # Preserve the labability_factor for backwards-compat readers (briefcase,
    # old templates). Now mirrors fit_score_factor since the gate moved.
    acv["labability_factor"] = acv["fit_score_factor"]

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


def _discovery_install_base_fallback(product: Any) -> int:
    """R3: When the Deep Dive fact extractor returns null install_base,
    fall back to the discovery-level estimated_user_base for the same product.

    Discovery already researched and stored this number — using it is
    GP5 (intelligence compounds), not a guess.
    """
    disc_data = getattr(product, "discovery_data", None) or {}
    if isinstance(disc_data, dict):
        ub = disc_data.get("estimated_user_base", "")
    else:
        ub = ""
    if not ub:
        # Try the product dict directly (some paths store it here)
        ub = getattr(product, "estimated_user_base", "") or ""
    if not ub:
        return 0
    # Parse the discovery format: "~14M", "~50K", "~2000"
    s = str(ub).replace("~", "").replace(",", "").strip()
    try:
        if s.upper().endswith("M"):
            return int(float(s[:-1]) * 1_000_000)  # magic-allowed: million multiplier for parsing "~14M"
        elif s.upper().endswith("K"):
            return int(float(s[:-1]) * 1_000)  # magic-allowed: thousand multiplier for parsing "~50K"
        elif s.upper().endswith("B"):
            return int(float(s[:-1]) * 1_000_000_000)  # magic-allowed: billion multiplier for parsing "~1B"
        else:
            return int(float(s))
    except (ValueError, IndexError):
        return 0


def _apply_industry_authority_deflation(pop: int) -> int:
    """Deflate Industry Authority user base from lifetime holders to annual candidates.

    Researcher-reported numbers for Industry Authorities (CompTIA, EC-Council,
    SANS, ISACA) are inflated — they represent lifetime cert holders, not
    annual training candidates. This applies tiered deflation from
    cfg.INDUSTRY_AUTHORITY_DEFLATION_TIERS before the adoption math.

    Per Platform-Foundation → unified ACV model.
    """
    if pop <= 0:
        return pop
    for threshold, divisor in cfg.INDUSTRY_AUTHORITY_DEFLATION_TIERS:
        if pop > threshold:
            deflated = pop // divisor
            log.info(
                "Industry Authority deflation: %d > %d → ÷%d = %d",
                pop, threshold, divisor, deflated,
            )
            return deflated
    return pop


def _detect_training_signals(product: object, company_analysis: object) -> dict:
    """Detect training maturity signals from the fact drawer.

    Returns a dict with boolean flags:
      atp_large: ATP program with 50+ partners
      cert_active: Active cert exams for this product
      no_signals: No training programs, no ATPs, no certs
      license_blocked: Training license is blocked
      has_training_org: Open source product with commercial training signals
    """
    signals = {
        "atp_large": False,
        "cert_active": False,
        "no_signals": True,  # assume no signals until proven otherwise
        "license_blocked": False,
        "has_training_org": False,
    }

    # Check company-level signals
    cf_facts = getattr(company_analysis, "customer_fit_facts", None) if company_analysis else None
    disc_data = getattr(company_analysis, "discovery_data", None) if company_analysis else None
    if isinstance(disc_data, dict):
        company_signals = disc_data.get("company_signals", {}) or {}
    else:
        company_signals = {}

    # ATP program check
    atp = ""
    if cf_facts:
        atp = getattr(cf_facts, "atp_program", "") or ""
    if not atp and company_signals:
        atp = company_signals.get("atp_program", "") or ""
    if atp:
        atp_lower = atp.lower()
        if atp_lower not in ("no", "none", "n/a", ""):
            signals["no_signals"] = False
            signals["has_training_org"] = True
            # Check for large ATP (50+ partners)
            for token in ("50+", "100+", "200+", "500+", "1000+", "1,000+"):
                if token in atp:
                    signals["atp_large"] = True
                    break

    # Training programs check
    training_programs = ""
    if cf_facts:
        training_programs = getattr(cf_facts, "training_programs", "") or ""
    if not training_programs and company_signals:
        training_programs = company_signals.get("training_programs", "") or ""
    if training_programs and training_programs.lower() not in ("no", "none", "n/a", ""):
        signals["no_signals"] = False
        signals["has_training_org"] = True

    # Cert inclusion check (product-level)
    pl_facts = getattr(product, "product_labability_facts", None)
    if pl_facts:
        cert = getattr(pl_facts, "cert_inclusion", None)
        if cert is None:
            la = getattr(pl_facts, "lab_access", None)
            if la:
                cert = getattr(la, "cert_inclusion", "") or ""
        if cert and str(cert).lower() not in ("no", "none", "n/a", ""):
            signals["cert_active"] = True
            signals["no_signals"] = False
            signals["has_training_org"] = True

    # Also check product-level discovery data for cert
    disc = getattr(product, "discovery_data", None) or {}
    if isinstance(disc, dict):
        cert_inc = disc.get("cert_inclusion", "") or ""
        if cert_inc and cert_inc.lower() not in ("no", "none", "n/a", ""):
            signals["cert_active"] = True
            signals["no_signals"] = False
            signals["has_training_org"] = True

    # Training license blocked check
    if pl_facts:
        la = getattr(pl_facts, "lab_access", None)
        if la:
            license_val = getattr(la, "training_license", "") or ""
            if license_val == "blocked":
                signals["license_blocked"] = True

    return signals


def _apply_wrapper_org_audience_cap(
    pop_low: int, pop_high: int,
    normalized_org: str,
    company_analysis: Any,
) -> tuple[int, int]:
    """R1: For wrapper org types (GSI, university, training org, etc.),
    cap Motion 1 audience to a fraction of the org's total employees.

    The researcher often reports the underlying technology's global audience
    (e.g., 4M AWS practitioners) instead of the org's own practice headcount
    (e.g., 60K Accenture AWS consultants). This cap approximates the real
    training population from the org's own size.
    """
    if normalized_org not in cfg.ACV_WRAPPER_ORG_TYPES:
        return pop_low, pop_high

    # Read total employees from the company's fact drawer
    cf_facts = getattr(company_analysis, "customer_fit_facts", None)
    if cf_facts is None:
        return pop_low, pop_high

    total_emp_range = getattr(cf_facts, "total_employees", None)
    if total_emp_range is None:
        return pop_low, pop_high

    total_emp = 0
    if hasattr(total_emp_range, "low"):
        total_emp = int(total_emp_range.low or 0)
    elif isinstance(total_emp_range, dict):
        total_emp = int(total_emp_range.get("low", 0) or 0)

    if total_emp <= 0:
        return pop_low, pop_high

    # Cap = fraction of total employees, with a floor
    audience_cap = max(
        int(total_emp * cfg.ACV_WRAPPER_ORG_AUDIENCE_CAP_FRACTION),
        cfg.ACV_WRAPPER_ORG_AUDIENCE_FLOOR,
    )

    capped_low = min(pop_low, audience_cap)
    capped_high = min(pop_high, audience_cap)

    if capped_low < pop_low or capped_high < pop_high:
        log.info(
            "ACV wrapper org cap: %s employees × %.0f%% = %d cap. "
            "Audience %d→%d",
            total_emp, cfg.ACV_WRAPPER_ORG_AUDIENCE_CAP_FRACTION * 100,
            audience_cap, pop_high, capped_high,
        )

    return capped_low, capped_high


def populate_acv_motions(product: Any, company_analysis: Any) -> None:
    """Build the five ConsumptionMotion records on a Product dataclass.

    Reads per-product audience facts from
    `product.instructional_value_facts.market_demand` and company-level
    audience facts from `company_analysis.customer_fit_facts`. Uses the
    locked adoption_pct and hours values from `cfg.CONSUMPTION_MOTIONS`.

    Includes five audience guardrails from the 2026-04-13 ACV audit:
      R1: Wrapper org audience cap (GSI/university install_base capped
          to fraction of total employees)
      R3: Null install_base fallback from discovery data
      R4: Cert audience sanity cap (cert ≤ install_base × 10%)

    Mutates `product.acv_potential.motions` in place. Does NOT compute
    derived fields (hrs, acv, rate, tier) — call `compute_acv_on_product`
    after this if you want the full populated output.
    """
    from models import ConsumptionMotion as ModelMotion, ACVPotential

    # Look up org-type overrides. The default rates, labels, and hours on
    # CONSUMPTION_MOTIONS apply to software companies. Other org types
    # (academic, training org, GSI, etc.) have fundamentally different
    # adoption patterns, audience language, and lab hours — per
    # Platform-Foundation → "How Adoption Patterns Vary by Organization Type."
    org_type = ""
    if company_analysis is not None:
        org_type = getattr(company_analysis, "org_type", "") or ""
        if not org_type:
            disc = getattr(company_analysis, "discovery_data", None) or {}
            org_type = disc.get("organization_type") or ""
    # Normalize to the CF baseline key format
    normalized_org = cfg.ORG_TYPE_NORMALIZATION.get(org_type.lower().replace(" ", "_"), "")
    adoption_overrides = cfg.ACV_ORG_ADOPTION_OVERRIDES.get(normalized_org, {})
    label_overrides = cfg.ACV_ORG_MOTION_LABELS.get(normalized_org, {})
    hours_overrides = cfg.ACV_ORG_HOURS_OVERRIDES.get(normalized_org, {})

    # Detect open source — training_license "none" (OSS, no license needed).
    # Three-tier classification: commercial / open source with training / pure open source.
    # Per Platform-Foundation → unified ACV model. Frank 2026-04-13.
    is_open_source = False
    pl_facts = getattr(product, "product_labability_facts", None)
    if pl_facts:
        la = getattr(pl_facts, "lab_access", None)
        if la:
            license_val = getattr(la, "training_license", "") or ""
            if license_val == "none":
                is_open_source = True

    # Detect training maturity signals for multipliers + open source tiering
    training_signals = _detect_training_signals(product, company_analysis)

    motions: list[ModelMotion] = []
    customer_motion_pop = 0  # Track for R4 cert cap

    for cfg_motion in cfg.CONSUMPTION_MOTIONS:
        pop_low, pop_high = _read_population(
            cfg_motion.population_source, product, company_analysis,
        )

        # ── R3: Null install_base fallback ──
        # When the Deep Dive fact extractor returned null for install_base
        # but discovery already has the number, use it. GP5 — intelligence
        # compounds, lighter research enriches deeper research.
        is_customer_motion = cfg_motion.label == "Customer Training & Enablement"
        if is_customer_motion and pop_low == 0 and pop_high == 0:
            fallback = _discovery_install_base_fallback(product)
            if fallback > 0:
                pop_low = fallback
                pop_high = fallback
                log.info("ACV R3 fallback: using discovery install_base %d for %s",
                         fallback, getattr(product, "name", "?"))

        # ── Archetype-aware audience cap (Frank 2026-04-16) ──
        # Apply to Customer Training audience on Software / Enterprise
        # Software paths (the ones that use install_base). For wrapper
        # orgs the audience is annual_enrollments_estimate — that's
        # already the wrapper's real audience, don't cap. Industry
        # Authority has its own deflation pass below.
        #
        # See scoring_config.AUDIENCE_TIERS_BY_ARCHETYPE for the per-
        # archetype tier tables. Enterprise_admin / developer_platform /
        # data_platform get the biggest caps (realistic admin audiences
        # span millions globally). Specialists tighter. IC tightest.
        if is_customer_motion and normalized_org not in ("INDUSTRY AUTHORITY", "TRAINING ORG"):
            if normalized_org in ("SOFTWARE", "ENTERPRISE SOFTWARE", ""):
                archetype = (getattr(product, "archetype", "") or "").strip()
                tiers = cfg.get_audience_tiers_for_archetype(archetype)
                for threshold, cap in tiers:
                    if pop_high > threshold:
                        if cap is not None:
                            pop_low = min(pop_low, cap)
                            pop_high = cap
                        break

        # ── Industry Authority / Training Org deflation ──
        # Researcher numbers for these org types are inflated (lifetime holders,
        # not annual training candidates). Deflate before adoption math.
        if is_customer_motion and normalized_org in ("INDUSTRY AUTHORITY", "TRAINING ORG"):
            pop_low = _apply_industry_authority_deflation(pop_low)
            pop_high = _apply_industry_authority_deflation(pop_high)

        # ── R1: Wrapper org audience cap ──
        # For GSIs, universities, etc., cap Motion 1 audience to a fraction
        # of the org's total employees. The researcher often reports the
        # underlying technology's global audience, not the org's own.
        if is_customer_motion:
            pop_low, pop_high = _apply_wrapper_org_audience_cap(
                pop_low, pop_high, normalized_org, company_analysis,
            )
            customer_motion_pop = max(pop_low, pop_high)

        # Apply org-type overrides: adoption, label, hours
        adoption = adoption_overrides.get(cfg_motion.label, cfg_motion.adoption_pct)
        display_label = label_overrides.get(cfg_motion.label, cfg_motion.label)
        hrs = hours_overrides.get(cfg_motion.label, cfg_motion.hours_low)

        # ── Archetype-aware hours override (Frank 2026-04-16) ──
        # Deep infrastructure / CAD / security ops labs are longer (5 hr
        # Customer Training); IC productivity / creative / consumer are
        # shorter. Org-type overrides above win if both apply; archetype
        # override only fires when there's no org-type override.
        if cfg_motion.label not in hours_overrides:
            archetype = (getattr(product, "archetype", "") or "").strip()
            hrs = cfg.get_hours_for_archetype_motion(archetype, cfg_motion.label, hrs)

        # ── Three-tier open source classification (Customer Training only) ──
        if is_open_source and cfg_motion.label == "Customer Training & Enablement":
            if training_signals["has_training_org"]:
                adoption *= cfg.OPEN_SOURCE_WITH_TRAINING_MULTIPLIER
            else:
                adoption *= cfg.OPEN_SOURCE_PURE_MULTIPLIER

        # ── Training maturity multipliers (Customer Training only) ──
        # Nudge adoption up or down from baseline based on researcher signals.
        # Multipliers stack multiplicatively but cap at the ceiling.
        if cfg_motion.label == "Customer Training & Enablement":
            maturity_mult = cfg.ACV_TRAINING_MATURITY_MULTIPLIERS
            if training_signals["license_blocked"]:
                adoption *= maturity_mult["license_blocked"]
            elif training_signals["atp_large"]:
                adoption *= maturity_mult["atp_large"]
            elif training_signals["cert_active"]:
                adoption *= maturity_mult["cert_active"]
            elif training_signals["no_signals"]:
                adoption *= maturity_mult["no_signals"]
            # Cap adoption to prevent runaway
            adoption = min(adoption, cfg.ACV_TRAINING_MATURITY_ADOPTION_CAP)

            # ── Scale-aware adoption cap (Frank 2026-04-16) ──
            # After all multipliers, cap effective adoption based on
            # audience size. Skillable's realistic share of a giant
            # software-company training market (e.g., M365 admin) is
            # 1-3%, not 15%.
            #
            # EXEMPT wrapper org types (Enterprise Learning Platform,
            # ILT Training Org, Academic, GSI, VAR, Distributor). For
            # these, audience IS the wrapper's own classroom/enrollment
            # pop and Skillable can legitimately be the whole lab backend
            # for that wrapper — the calibrated 3%/5%/25% adoption rates
            # already encode the realistic share for their delivery model.
            # Skillsoft 4M learners x 3% = $5M matches real $5M only when
            # we don't secondarily cap 3% down to 2%. Frank's call.
            wrapper_org_types = (
                "ENTERPRISE LEARNING PLATFORM", "TRAINING ORG",
                "ACADEMIC", "SYSTEMS INTEGRATOR", "VAR",
                "TECH DISTRIBUTOR", "CONTENT DEVELOPMENT",
                "PROFESSIONAL SERVICES", "LMS PROVIDER",
            )
            if normalized_org not in wrapper_org_types:
                audience = max(pop_low, pop_high)
                scale_ceiling = cfg.get_scale_aware_adoption_ceiling(audience)
                if scale_ceiling is not None:
                    adoption = min(adoption, scale_ceiling)

        motions.append(ModelMotion(
            label=display_label,
            population_low=pop_low,
            population_high=pop_high,
            hours_low=hrs,
            hours_high=hrs,
            adoption_pct=adoption,
            rationale=cfg_motion.description,
        ))

    # ── R4: Cert audience sanity cap ──
    # Cert candidates can never exceed a fraction of the install_base.
    # If Accenture has 60K AWS practitioners, they can't have 400K cert
    # sitters. Mathematical constraint, not a heuristic.
    cert_labels = {"Certification (PBT)", "Course Exams"}
    customer_labels = {"Customer Training & Enablement", "Student Training",
                       "Training Participants", "Client End Users"}
    cert_motion = next((m for m in motions if m.label in cert_labels), None)
    customer_motion = next((m for m in motions if m.label in customer_labels), None)

    if cert_motion and customer_motion:
        customer_pop = max(customer_motion.population_low or 0,
                          customer_motion.population_high or 0)
        cert_pop = max(cert_motion.population_low or 0,
                       cert_motion.population_high or 0)

        if customer_pop > 0:
            # R4: cap cert to fraction of customer audience
            cert_cap = max(1, int(customer_pop * cfg.ACV_CERT_MAX_FRACTION_OF_INSTALL_BASE))
            if cert_pop > cert_cap:
                log.info("ACV R4 cert cap: %d → %d (%.0f%% of %d customer pop)",
                         cert_pop, cert_cap,
                         cfg.ACV_CERT_MAX_FRACTION_OF_INSTALL_BASE * 100,
                         customer_pop)
                cert_motion.population_low = cert_cap
                cert_motion.population_high = cert_cap
            elif cert_pop == 0:
                # Bug 13 derivation: no cert data found, derive from customer pop
                derived = max(1, int(customer_pop * cfg.CERT_SIT_DERIVATION_PCT))
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

    # ── Fit Score gate (Frank 2026-04-16, replaces PL-only gate) ─────────
    # ACV scales linearly with the three-pillar Fit Score (PL 50% + IV 20%
    # + CF 30%, with Technical Fit Multiplier asymmetric PL drag).
    # Matches compute_acv_potential (dict path). Fit Score is set by
    # fit_score_composer.compose_fit_score BEFORE this runs in score() and
    # rescore_products_from_saved_facts.
    fit_score = 0
    try:
        # Prefer total_override (composer's authoritative value) over .total
        fs = product.fit_score
        fit_score = int(getattr(fs, "total_override", None) or getattr(fs, "total", 0) or 0)
    except (TypeError, ValueError, AttributeError):
        fit_score = 0
    if fit_score > 0:
        fit_factor = fit_score / 100  # magic-allowed: linear fit score factor denominator (percentage)
        acv_low_dollars *= fit_factor
        acv_high_dollars *= fit_factor

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
