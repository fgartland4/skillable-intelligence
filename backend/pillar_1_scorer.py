"""Pillar 1 (Product Labability) scoring from facts — pure Python.

Reads ProductLababilityFacts typed primitives and produces a PillarScore
directly.  No Claude.  No badge name inputs.  No hardcoded numbers.

Architecture layer: SCORE (per docs/Platform-Foundation.md → Three Layers
of Intelligence).  The sole Pillar 1 scoring path — the legacy monolithic
Claude call was removed in the April 2026 rebuild.

─── Architectural lock-ins honored here ────────────────────────────────────
  1. Score reads facts directly, never badges.
  2. Math is right — point values, caps, rules all come from scoring_config.
  3. Badges are post-scoring display only (Step 6), not an input here.
  4. Claude runs only in Research — this module is pure Python.
  5. Facts are truth-only (no strength field in the drawer).
  6. NO HARDCODING ANYWHERE EVER — every number comes from scoring_config.
     The only string literals in this file are canonical signal/penalty
     names used as identifiers; each appears exactly once in the canonical
     name block near the top of the file.

─── Design ─────────────────────────────────────────────────────────────────
  - One scoring function per dimension:
      score_provisioning(facts) → _DimensionResult
      score_lab_access(facts)   → _DimensionResult
      score_scoring(facts)      → _DimensionResult
      score_teardown(facts)     → _DimensionResult
  - Each walks the facts, collects fired signals and penalties, counts
    amber/red risks, and applies the same risk cap reduction logic the
    legacy math uses (sourced from scoring_config.AMBER_RISK_CAP_REDUCTION
    and RED_RISK_CAP_REDUCTION).
  - score_product_labability(facts) composes the four dimensions into a
    PillarScore and applies the Sandbox API red Pillar 1 cap when
    applicable.

─── What "fact → signal" means ─────────────────────────────────────────────
  The legacy scorer matched badge names emitted by Claude against the
  dimension's scoring_signals table.  This module matches fact-drawer
  fields against the same table:

      Legacy:  badge.name == "Runs in VM" → +30 signal credit
      New:     facts.provisioning.runs_as_installable → +30 signal credit

  The point values are identical.  The rules are identical.  Only the
  decision of "does this signal fire?" moves from Claude judgment at
  scoring time to deterministic fact inspection at scoring time.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import scoring_config as cfg
from models import (
    DimensionScore,
    PillarScore,
    ProductLababilityFacts,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Canonical signal / penalty / dimension / pillar name constants
#
# Each string appears exactly once in this file.  The rest of the module
# references these constants.  All strings are verified at module load to
# match the scoring_config.py source of truth (see _verify_canonical_names
# below) — a typo or rename in config is caught immediately.
# ═══════════════════════════════════════════════════════════════════════════════

# Pillar + dimension names (match scoring_config.PILLARS exactly)
_PILLAR_PL = "Product Labability"
_DIM_PROV = "Provisioning"
_DIM_LA = "Lab Access"
_DIM_SC = "Scoring"
_DIM_TD = "Teardown"

# Provisioning signals
_SIG_VM = "Runs in VM"
_SIG_AZURE = "Runs in Azure"
_SIG_AWS = "Runs in AWS"
_SIG_CONTAINER = "Runs in Container"
_SIG_ESX = "ESX Required"
_SIG_SANDBOX_API = "Sandbox API"
_SIG_SIMULATION = "Simulation"
# Frank 2026-04-08 additions:
_SIG_M365_TENANT = "M365 Tenant"
_SIG_M365_ADMIN = "M365 Admin"
_SIG_CUSTOM_CLOUD = "Custom Cloud"
_SIG_NO_GCP_PATH = "No GCP Path"

# Provisioning penalties
_PEN_GPU = "GPU Required"
_PEN_SOCKET = "Socket licensing (ESX) >24 vCPUs"

# Lab Access signals
_SIG_FULL_LIFECYCLE_API = "Full Lifecycle API"
_SIG_ENTRA_SSO = "Entra ID SSO"
_SIG_IDENTITY_API = "Identity API"
_SIG_CRED_RECYCLING = "Cred Recycling"
_SIG_CRED_POOL = "Credential Pool"
_SIG_TRAINING_LICENSE = "Training License"
_SIG_MANUAL_SSO = "Manual SSO"

# Lab Access penalties
_PEN_MFA = "MFA Required"
_PEN_ANTI_AUTOMATION = "Anti-Automation Controls"
_PEN_RATE_LIMITS = "Rate Limits"

# Scoring signals
_SIG_SCORING_API = "Scoring API"
_SIG_SCRIPT_SCORING = "Script Scoring"
_SIG_AI_VISION = "AI Vision"
_SIG_SIMULATION_SCORABLE = "Simulation Scorable"
_SIG_MCQ_SCORING = "MCQ Scoring"
_SIG_NO_SCORING_METHODS = "No Scoring Methods"

# Teardown signals
_SIG_DATACENTER = "Datacenter"
_SIG_SIMULATION_RESET = "Simulation Reset"
_SIG_TEARDOWN_API = "Teardown API"

# Teardown penalties
_PEN_MANUAL_TEARDOWN = "Manual Teardown"
_PEN_ORPHAN_RISK = "Orphan Risk"

# Granularity values (appear in fact drawer fields like sandbox_api_granularity)
_GRAN_RICH = "rich"
_GRAN_PARTIAL = "partial"
_GRAN_FULL = "full"
_GRAN_NONE = "none"

# Auth model values (match the fact drawer LabAccessFacts.auth_model enum)
_AUTH_ENTRA_NATIVE_TENANT = "entra_native_tenant"
_AUTH_ENTRA_MSFT_ID = "entra_msft_id"
_AUTH_SSO_SAML = "sso_saml"
_AUTH_SSO_OIDC = "sso_oidc"
_AUTH_OAUTH = "oauth"
_AUTH_PRODUCT_CREDENTIALS = "product_credentials"
_AUTH_API_KEY = "api_key"

# Credential lifecycle values
_CRED_RECYCLABLE = "recyclable"
_CRED_POOL_ONLY = "pool_only"

# Training license values
_TL_LOW = "low_friction"
_TL_MEDIUM = "medium_friction"
_TL_BLOCKED = "blocked"

# Ceiling flag names (match scoring_config where applicable)
_CEIL_SANDBOX_RED_SIM_VIABLE = "sandbox_api_red_sim_viable"
_CEIL_SANDBOX_RED_NOTHING_VIABLE = "sandbox_api_red_nothing_viable"
_CEIL_BARE_METAL = "bare_metal_required"
_CEIL_NO_API_AUTOMATION = "no_api_automation"

# M365 scenario values (match ProvisioningFacts.m365_scenario)
_M365_END_USER = "end_user"
_M365_ADMIN = "administration"

# Preferred fabric values (match ProvisioningFacts.preferred_fabric)
_FABRIC_M365_TENANT = "m365_tenant"
_FABRIC_M365_ADMIN = "m365_admin"
_FABRIC_HYPER_V = "hyper_v"
_FABRIC_VM = "vm"
_FABRIC_CONTAINER = "container"
_FABRIC_AZURE = "azure"
_FABRIC_AWS = "aws"
_FABRIC_SANDBOX_API = "sandbox_api"
_FABRIC_SIMULATION = "simulation"
_FABRIC_GCP = "gcp"


# ═══════════════════════════════════════════════════════════════════════════════
# Config lookups — resolved once at module load, zero runtime walks
# ═══════════════════════════════════════════════════════════════════════════════

def _find_pillar(name: str) -> cfg.Pillar:
    for p in cfg.PILLARS:
        if p.name == name:
            return p
    raise RuntimeError(
        f"pillar_1_scorer: pillar {name!r} not found in scoring_config.PILLARS"
    )


def _find_dimension(pillar: cfg.Pillar, dim_name: str) -> cfg.Dimension:
    for d in pillar.dimensions:
        if d.name == dim_name:
            return d
    raise RuntimeError(
        f"pillar_1_scorer: dimension {dim_name!r} not found in pillar {pillar.name!r}"
    )


def _signal_points(dim: cfg.Dimension, signal_name: str) -> int:
    for s in dim.scoring_signals:
        if s.name == signal_name:
            return s.points
    raise RuntimeError(
        f"pillar_1_scorer: signal {signal_name!r} not found in dimension {dim.name!r}"
    )


def _penalty_deduction(dim: cfg.Dimension, penalty_name: str) -> int:
    for p in dim.penalties:
        if p.name == penalty_name:
            return p.deduction
    raise RuntimeError(
        f"pillar_1_scorer: penalty {penalty_name!r} not found in dimension {dim.name!r}"
    )


# Resolve all the config structures we need exactly once at module load.
# If any canonical name drifts, the import fails loudly — no silent drift.
_PL_PILLAR: cfg.Pillar = _find_pillar(_PILLAR_PL)
_PROV_DIM: cfg.Dimension = _find_dimension(_PL_PILLAR, _DIM_PROV)
_LA_DIM: cfg.Dimension = _find_dimension(_PL_PILLAR, _DIM_LA)
_SC_DIM: cfg.Dimension = _find_dimension(_PL_PILLAR, _DIM_SC)
_TD_DIM: cfg.Dimension = _find_dimension(_PL_PILLAR, _DIM_TD)


def _verify_canonical_names() -> None:
    """Verify every canonical name constant in this module maps to a real
    entry in scoring_config.py.  Run at module load — raises if any name
    has drifted from the config source of truth.
    """
    _signal_points(_PROV_DIM, _SIG_VM)
    _signal_points(_PROV_DIM, _SIG_AZURE)
    _signal_points(_PROV_DIM, _SIG_AWS)
    _signal_points(_PROV_DIM, _SIG_CONTAINER)
    _signal_points(_PROV_DIM, _SIG_ESX)
    _signal_points(_PROV_DIM, _SIG_SANDBOX_API)
    _signal_points(_PROV_DIM, _SIG_SIMULATION)
    # Frank 2026-04-08 new Provisioning signals:
    _signal_points(_PROV_DIM, _SIG_M365_TENANT)
    _signal_points(_PROV_DIM, _SIG_M365_ADMIN)
    _signal_points(_PROV_DIM, _SIG_CUSTOM_CLOUD)
    _penalty_deduction(_PROV_DIM, _PEN_GPU)
    _penalty_deduction(_PROV_DIM, _PEN_SOCKET)

    _signal_points(_LA_DIM, _SIG_FULL_LIFECYCLE_API)
    _signal_points(_LA_DIM, _SIG_ENTRA_SSO)
    _signal_points(_LA_DIM, _SIG_IDENTITY_API)
    _signal_points(_LA_DIM, _SIG_CRED_RECYCLING)
    _signal_points(_LA_DIM, _SIG_CRED_POOL)
    _signal_points(_LA_DIM, _SIG_TRAINING_LICENSE)
    _signal_points(_LA_DIM, _SIG_MANUAL_SSO)
    _penalty_deduction(_LA_DIM, _PEN_MFA)
    _penalty_deduction(_LA_DIM, _PEN_ANTI_AUTOMATION)
    _penalty_deduction(_LA_DIM, _PEN_RATE_LIMITS)

    _signal_points(_SC_DIM, _SIG_SCORING_API)
    _signal_points(_SC_DIM, _SIG_SCRIPT_SCORING)
    _signal_points(_SC_DIM, _SIG_AI_VISION)
    _signal_points(_SC_DIM, _SIG_SIMULATION_SCORABLE)
    _signal_points(_SC_DIM, _SIG_MCQ_SCORING)
    _signal_points(_SC_DIM, _SIG_NO_SCORING_METHODS)

    _signal_points(_TD_DIM, _SIG_DATACENTER)
    _signal_points(_TD_DIM, _SIG_SIMULATION_RESET)
    _signal_points(_TD_DIM, _SIG_TEARDOWN_API)
    _penalty_deduction(_TD_DIM, _PEN_MANUAL_TEARDOWN)
    _penalty_deduction(_TD_DIM, _PEN_ORPHAN_RISK)


_verify_canonical_names()


# ═══════════════════════════════════════════════════════════════════════════════
# Intermediate result type
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class _DimensionResult:
    """Intermediate result from a per-dimension scorer.

    Carries the final DimensionScore plus ceiling flags the dimension
    wants to raise at the pillar level (Sandbox API red, bare_metal_required,
    etc.), plus diagnostic breakdown used for comparison against the
    legacy monolithic output.
    """
    dimension_score: DimensionScore
    ceiling_flags: list[str] = field(default_factory=list)
    signals_matched: list[tuple[str, int]] = field(default_factory=list)
    penalties_applied: list[tuple[str, int]] = field(default_factory=list)
    amber_risks: int = 0
    red_risks: int = 0
    raw_total: int = 0
    effective_cap: int = 0
    simulation_viable: bool = False  # for Sandbox API red cap resolution
    simulation_chosen: bool = False  # Frank 2026-04-08 — Simulation is the primary fabric; triggers hard override on the other three dimensions via the composer


def _dim_cap(dim: cfg.Dimension) -> int:
    """Resolve the effective cap for a dimension (dim.cap if set, else dim.weight)."""
    return dim.cap if dim.cap is not None else dim.weight


def _dim_floor(dim: cfg.Dimension) -> int:
    """Resolve the floor for a dimension (dim.floor if set, else 0)."""
    return dim.floor if dim.floor is not None else 0


def _apply_risk_cap_reduction(raw_total: int,
                              dim: cfg.Dimension,
                              amber_risks: int,
                              red_risks: int,
                              preset_cap: int | None = None) -> tuple[int, int]:
    """Apply the Pillar 1 risk cap reduction rule.

    Per scoring_config.AMBER_RISK_CAP_REDUCTION and RED_RISK_CAP_REDUCTION:
    each amber risk knocks the effective cap down by 3, each red by 8,
    hard-floored at the dimension's floor.

    `preset_cap` lets the Scoring dimension pass in its Grand Slam cap as
    the starting point for risk cap reduction (whichever is tighter wins
    in the final min()).

    Returns (final_score, effective_cap).
    """
    base_cap = preset_cap if preset_cap is not None else _dim_cap(dim)
    floor = _dim_floor(dim)
    knockdown = (amber_risks * cfg.AMBER_RISK_CAP_REDUCTION
                 + red_risks * cfg.RED_RISK_CAP_REDUCTION)
    effective_cap = max(base_cap - knockdown, floor)
    score = max(min(raw_total, effective_cap), floor)
    return int(score), int(effective_cap)


# ═══════════════════════════════════════════════════════════════════════════════
# Dimension 1.1 — Provisioning
# ═══════════════════════════════════════════════════════════════════════════════

def _container_is_viable(p: "ProvisioningFacts") -> bool:
    """Container is viable only when production-native AND none of the four
    documented disqualifiers fire. Frank 2026-04-08."""
    if not p.runs_as_container:
        return False
    if not p.container_is_production_native:
        return False
    if p.container_is_dev_only:
        return False
    if p.container_needs_windows_gui:
        return False
    if p.container_needs_multi_vm_network:
        return False
    return True


# ── Preferred-fabric hint → canonical signal name mapping ──────────────
# Used by _pick_primary_fabric to translate the researcher's preferred_fabric
# hint into the canonical signal name. Kept as a module-level constant so the
# picker is a thin chooser and all fabric vocabulary lives in one place.
_PREFERRED_FABRIC_TO_SIGNAL: dict[str, str] = {
    _FABRIC_HYPER_V: _SIG_VM,
    _FABRIC_VM: _SIG_VM,
    _FABRIC_CONTAINER: _SIG_CONTAINER,
    _FABRIC_AZURE: _SIG_AZURE,
    _FABRIC_AWS: _SIG_AWS,
    _FABRIC_SANDBOX_API: _SIG_SANDBOX_API,
}


def _list_viable_fabrics(p: "ProvisioningFacts") -> list[str]:
    """Single source of truth for which per-learner provisioning fabrics
    are viable for this product. Used by the primary fabric picker AND by
    the multi-fabric optionality bonus counter — both reads the same list,
    no drift possible.

    Rules (Frank 2026-04-08):
      - Researcher escape hatch: preferred_fabric == "simulation" returns []
        (the researcher judged this product has NO real per-learner fabric;
        picker falls through to Simulation last-resort)
      - SaaS-only contradiction rule: when runs_as_saas_only == True AND
        has_sandbox_api == False, the vendor runs it as a managed service
        and there is no per-learner path into the vendor's cloud.
        runs_as_aws_native / runs_as_azure_native in that state means
        "hosted on X by vendor", NOT "learner can provision on X" — strip
        those signals from the viable list. Without this rule, Trellix
        Intelligence as a Service (runs_as_saas_only=True AND
        runs_as_aws_native=True) gets scored 30 points for AWS provisioning
        despite having no per-learner path at all.
      - M365 scenarios map to M365 Tenant / M365 Admin (owned branch)
      - VM requires runs_as_installable
      - Container requires production-native + no disqualifiers
      - Sandbox API only counts at rich granularity (partial is too weak
        for optionality; picker handles partial as a weaker primary-only
        fallback below)
      - Simulation is NOT in this list — it is a last-resort fallback, not
        a real per-learner fabric
    """
    # Researcher's explicit escape hatch — empty list means "no real fabric,
    # fall through to Simulation". All other rules are short-circuited.
    if p.preferred_fabric == _FABRIC_SIMULATION:
        return []

    # SaaS-only managed service with no Sandbox API → vendor runs the cloud,
    # not the learner. Strip cloud-native signals to prevent false credit.
    saas_managed = p.runs_as_saas_only and not p.has_sandbox_api

    viable: list[str] = []
    if p.m365_scenario == _M365_END_USER:
        viable.append(_SIG_M365_TENANT)
    if p.m365_scenario == _M365_ADMIN:
        viable.append(_SIG_M365_ADMIN)
    if p.runs_as_installable:
        viable.append(_SIG_VM)
    if _container_is_viable(p):
        viable.append(_SIG_CONTAINER)
    if p.runs_as_azure_native and not saas_managed:
        viable.append(_SIG_AZURE)
    if p.runs_as_aws_native and not saas_managed:
        viable.append(_SIG_AWS)
    if p.has_sandbox_api and p.sandbox_api_granularity == _GRAN_RICH:
        viable.append(_SIG_SANDBOX_API)
    return viable


def _pick_primary_fabric(p: "ProvisioningFacts") -> str | None:
    """Pick the primary fabric from _list_viable_fabrics. The picker is a
    thin chooser over that list — every contradiction rule lives in
    _list_viable_fabrics, which is the single source of truth.

    Priority order within the viable list:
      1. M365 Tenant / M365 Admin — owned branch, highest priority when set
      2. Researcher's preferred_fabric hint, if it names a signal in the
         viable list (tiebreaker between otherwise-equal options)
      3. Static priority: VM > Container > Azure > AWS > Sandbox API

    Weaker fallback when the viable list is empty:
      - Partial-granularity Sandbox API can still be the primary fabric
        (it earns half credit via the granularity penalty path) even though
        it does not count toward the optionality bonus.

    Returns None only when nothing at all is pickable — caller falls
    through to Simulation last-resort or emits a no-deployment-method
    ceiling flag when bare metal or GCP blocks simulation.
    """
    viable = _list_viable_fabrics(p)

    # M365 owned branch wins when present.
    if _SIG_M365_TENANT in viable:
        return _SIG_M365_TENANT
    if _SIG_M365_ADMIN in viable:
        return _SIG_M365_ADMIN

    # Researcher's preferred fabric, if it names a signal in the viable list.
    preferred_sig = _PREFERRED_FABRIC_TO_SIGNAL.get(p.preferred_fabric or "")
    if preferred_sig and preferred_sig in viable:
        return preferred_sig

    # Static priority walk over the viable list.
    for sig in (_SIG_VM, _SIG_CONTAINER, _SIG_AZURE, _SIG_AWS, _SIG_SANDBOX_API):
        if sig in viable:
            return sig

    # Weaker primary-only fallback: partial-granularity Sandbox API is
    # pickable as primary (scored at half credit) but does not count for
    # the optionality bonus, so it is deliberately excluded from the
    # viable list and handled here as a last step before None.
    if p.has_sandbox_api and p.sandbox_api_granularity == _GRAN_PARTIAL:
        return _SIG_SANDBOX_API

    return None


def score_provisioning(facts: ProductLababilityFacts) -> _DimensionResult:
    """Compute Provisioning dimension score from facts.

    Updated Frank 2026-04-08 with multiple refinements:
      - M365 scenario is first-priority (M365 Tenant / M365 Admin fabrics)
      - Simulation is a HARD OVERRIDE (all 4 dims get fixed values via composer)
      - preferred_fabric hint is honored when fact predicate supports it
      - Multi-fabric optionality bonus (+3 per extra, capped at +6)
      - Container disqualifier check (production-native + no disqualifiers)
      - GCP No GCP Path badge fires amber (simple) — full red+workaround
        multi-badge nuance deferred to Step 5.5 tuning
      - ESX Required fires as a separate amber badge when requires_esx=True
      - Custom Cloud fires as a Skillable-strength context badge alongside
        Sandbox API when Sandbox API is viable at rich or partial granularity
    """
    p = facts.provisioning
    dim = _PROV_DIM

    signals: list[tuple[str, int]] = []
    penalties: list[tuple[str, int]] = []
    amber_risks = 0
    red_risks = 0
    ceiling_flags: list[str] = []
    simulation_chosen = False
    simulation_viable = False
    sandbox_red = False

    # ── Pick the primary fabric ──
    primary_fabric = _pick_primary_fabric(p)

    if primary_fabric is None:
        # Nothing at all viable. Simulation is the last-resort fallback
        # UNLESS bare_metal or GCP blocks it.
        if not p.needs_bare_metal and not p.needs_gcp:
            primary_fabric = _SIG_SIMULATION
            simulation_chosen = True
            simulation_viable = True
        else:
            # Bare metal or GCP-only with no alternative → no deployment method
            ceiling_flags.append(_CEIL_BARE_METAL if p.needs_bare_metal else _CEIL_SANDBOX_RED_NOTHING_VIABLE)

    # ── Simulation hard override case ──
    # When the primary fabric resolves to Simulation, all four Pillar 1
    # dimensions get HARD OVERRIDE values (Frank 2026-04-08). The composer
    # detects this via simulation_chosen=True in the result.
    if primary_fabric == _SIG_SIMULATION:
        simulation_chosen = True
        simulation_viable = True
        score = cfg.SIMULATION_PROVISIONING_POINTS
        dimension_score = DimensionScore(
            name=dim.name,
            score=score,
            weight=dim.weight,
            summary=p.description,
        )
        return _DimensionResult(
            dimension_score=dimension_score,
            ceiling_flags=ceiling_flags,
            signals_matched=[(_SIG_SIMULATION, score)],
            penalties_applied=[],
            amber_risks=0,
            red_risks=0,
            raw_total=score,
            effective_cap=cfg.SIMULATION_PROVISIONING_POINTS,
            simulation_viable=True,
            simulation_chosen=True,
        )

    # ── Credit the primary fabric ──
    if primary_fabric is not None:
        base_points = _signal_points(dim, primary_fabric)
        # Color-aware half-credit for partial Sandbox API
        if primary_fabric == _SIG_SANDBOX_API and p.sandbox_api_granularity == _GRAN_PARTIAL:
            signals.append((primary_fabric, base_points // 2))  # magic-allowed: amber fires at half the green signal credit
            amber_risks += 1
        # Sandbox API downgrades to amber when needs_gcp — the product is
        # GCP-native and Skillable has no native GCP fabric. Green Sandbox
        # API + "No GCP Path" is a contradiction. (Fix 1, 2026-04-13)
        elif primary_fabric == _SIG_SANDBOX_API and p.needs_gcp:
            signals.append((primary_fabric, base_points // 2))  # magic-allowed: amber for GCP limitation
            amber_risks += 1
        else:
            signals.append((primary_fabric, base_points))

    # ── M365 Admin counts as amber risk (friction from trial/tenant path) ──
    if primary_fabric == _SIG_M365_ADMIN:
        amber_risks += 1

    # ── Sandbox API red cap (SaaS-only with no API) ──
    if primary_fabric is None and p.runs_as_saas_only and not p.has_sandbox_api:
        sandbox_red = True
        red_risks += 1
    # Sandbox API claimed but granularity is "none" → red
    if p.has_sandbox_api and p.sandbox_api_granularity == _GRAN_NONE:
        sandbox_red = True

    if sandbox_red:
        if simulation_viable:
            ceiling_flags.append(_CEIL_SANDBOX_RED_SIM_VIABLE)
        else:
            ceiling_flags.append(_CEIL_SANDBOX_RED_NOTHING_VIABLE)
            red_risks += 1

    # ── Multi-fabric optionality bonus — Frank 2026-04-08 ──
    viable = _list_viable_fabrics(p)
    secondary_count = max(0, sum(1 for v in viable if v != primary_fabric))
    if secondary_count > 0:
        bonus = min(
            secondary_count * cfg.MULTI_FABRIC_OPTIONALITY_BONUS_PER_EXTRA,
            cfg.MULTI_FABRIC_OPTIONALITY_BONUS_CAP,
        )
        # Append as a synthetic signal entry so the math sums it correctly
        signals.append(("Multi-Fabric Bonus", bonus))

    # ── Custom Cloud Skillable-strength context badge ──
    # Fires alongside Sandbox API whenever the vendor has a real provisioning
    # API (rich or partial). Zero scoring impact — it's display/context only.
    if p.has_sandbox_api and p.sandbox_api_granularity in (_GRAN_RICH, _GRAN_PARTIAL):
        signals.append((_SIG_CUSTOM_CLOUD, 0))

    # ── ESX Required amber badge (fires alongside VM primary) ──
    if p.requires_esx:
        signals.append((_SIG_ESX, 0))
        amber_risks += 1

    # ── Bare metal ceiling flag ──
    if p.needs_bare_metal:
        if _CEIL_BARE_METAL not in ceiling_flags:
            ceiling_flags.append(_CEIL_BARE_METAL)
        red_risks += 1

    # ── GCP handling (Frank 2026-04-08 simplified) ──
    # needs_gcp fires No GCP Path amber; the full red+workaround multi-badge
    # nuance is deferred to Step 5.5 tuning once we see real data.
    if p.needs_gcp:
        signals.append((_SIG_NO_GCP_PATH, 0))
        amber_risks += 1

    # ── Friction penalties ──
    if p.needs_gpu:
        penalties.append((_PEN_GPU, _penalty_deduction(dim, _PEN_GPU)))
        amber_risks += 1

    # ── Compute raw total + apply risk cap reduction ──
    raw_total = sum(pts for _, pts in signals) + sum(d for _, d in penalties)
    score, effective_cap = _apply_risk_cap_reduction(
        raw_total, dim, amber_risks, red_risks,
    )

    dimension_score = DimensionScore(
        name=dim.name,
        score=score,
        weight=dim.weight,
        summary=p.description,
    )

    return _DimensionResult(
        dimension_score=dimension_score,
        ceiling_flags=ceiling_flags,
        signals_matched=signals,
        penalties_applied=penalties,
        amber_risks=amber_risks,
        red_risks=red_risks,
        raw_total=raw_total,
        effective_cap=effective_cap,
        simulation_viable=simulation_viable,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Dimension 1.2 — Lab Access
# ═══════════════════════════════════════════════════════════════════════════════

def score_lab_access(facts: ProductLababilityFacts) -> _DimensionResult:
    """Compute Lab Access dimension score from facts.

    Maps the auth model / credential lifecycle / training license / user
    provisioning API facts to the canonical Lab Access signals, applies
    penalties for MFA / Anti-Automation / Rate Limits, and applies the
    standard risk cap reduction.
    """
    la = facts.lab_access
    prov = facts.provisioning
    dim = _LA_DIM

    signals: list[tuple[str, int]] = []
    penalties: list[tuple[str, int]] = []
    amber_risks = 0
    red_risks = 0

    # ── Identity / auth path ─────────────────────────────────────────────
    # Entra ID SSO is Azure-native only — preempts Identity API when the
    # product runs as an Azure-native service.  See the config note on
    # Entra ID SSO: "Scope is AZURE-NATIVE APPLICATIONS ONLY."
    #
    # Mutually exclusive choice — pick the strongest identity path that
    # the facts support.  Entra ID SSO > Identity API (rich) >
    # Identity API (partial) > Manual SSO > product_credentials fallback.
    identity_path_set = False
    if la.auth_model == _AUTH_ENTRA_NATIVE_TENANT and prov.runs_as_azure_native:
        signals.append((_SIG_ENTRA_SSO, _signal_points(dim, _SIG_ENTRA_SSO)))
        identity_path_set = True
    elif la.user_provisioning_api_granularity == _GRAN_RICH:
        signals.append((_SIG_IDENTITY_API, _signal_points(dim, _SIG_IDENTITY_API)))
        identity_path_set = True
    elif la.user_provisioning_api_granularity == _GRAN_PARTIAL:
        base = _signal_points(dim, _SIG_IDENTITY_API)
        signals.append((_SIG_IDENTITY_API, base // 2))  # magic-allowed: amber fires at half the green signal credit
        amber_risks += 1
        identity_path_set = True
    elif la.auth_model in (_AUTH_SSO_SAML, _AUTH_SSO_OIDC):
        # Generic SSO without API-level provisioning = Manual SSO (amber)
        signals.append((_SIG_MANUAL_SSO, _signal_points(dim, _SIG_MANUAL_SSO)))
        amber_risks += 1
        identity_path_set = True

    # ── Credential lifecycle (independent of identity path) ─────────────
    if la.credential_lifecycle == _CRED_RECYCLABLE:
        signals.append((_SIG_CRED_RECYCLING, _signal_points(dim, _SIG_CRED_RECYCLING)))
    elif la.credential_lifecycle == _CRED_POOL_ONLY:
        signals.append((_SIG_CRED_POOL, _signal_points(dim, _SIG_CRED_POOL)))

    # ── Training License (consolidated canonical, three color states) ──
    if la.training_license == _TL_LOW:
        signals.append((_SIG_TRAINING_LICENSE, _signal_points(dim, _SIG_TRAINING_LICENSE)))
    elif la.training_license == _TL_MEDIUM:
        base = _signal_points(dim, _SIG_TRAINING_LICENSE)
        signals.append((_SIG_TRAINING_LICENSE, base // 2))  # magic-allowed: amber fires at half the green signal credit
        amber_risks += 1
    elif la.training_license == _TL_BLOCKED:
        red_risks += 1  # Red — no credit, just a risk counted for cap reduction

    # ── Red blocker penalties ────────────────────────────────────────────
    if la.has_mfa_blocker:
        penalties.append((_PEN_MFA, _penalty_deduction(dim, _PEN_MFA)))
        red_risks += 1
    if la.has_anti_automation:
        penalties.append((_PEN_ANTI_AUTOMATION, _penalty_deduction(dim, _PEN_ANTI_AUTOMATION)))
        red_risks += 1
    if la.has_rate_limit_blocker:
        penalties.append((_PEN_RATE_LIMITS, _penalty_deduction(dim, _PEN_RATE_LIMITS)))
        red_risks += 1

    # ── Compute raw total + risk cap reduction ──────────────────────────
    raw_total = sum(pts for _, pts in signals) + sum(d for _, d in penalties)
    score, effective_cap = _apply_risk_cap_reduction(
        raw_total, dim, amber_risks, red_risks,
    )

    dimension_score = DimensionScore(
        name=dim.name,
        score=score,
        weight=dim.weight,
        summary=la.description,
    )

    return _DimensionResult(
        dimension_score=dimension_score,
        signals_matched=signals,
        penalties_applied=penalties,
        amber_risks=amber_risks,
        red_risks=red_risks,
        raw_total=raw_total,
        effective_cap=effective_cap,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Dimension 1.3 — Scoring (with Grand Slam breadth cap)
# ═══════════════════════════════════════════════════════════════════════════════

def score_scoring(facts: ProductLababilityFacts) -> _DimensionResult:
    """Compute Scoring dimension score from facts.

    Applies the Grand Slam breadth rule per Frank 2026-04-07:
      AI Vision + Script Scoring  → cap 15 (Grand Slam, VM)
      AI Vision + Scoring API     → cap 15 (Grand Slam, cloud)
      Script Scoring alone        → cap 15 (VM context)
      Scoring API alone           → cap SCORING_API_ALONE_CAP (12)
      AI Vision alone             → cap SCORING_AI_VISION_ALONE_CAP (10)
      MCQ only / nothing          → cap 0

    MCQ earns 0 points (Frank: "anyone can do MCQs, it's not lab work")
    and does not count toward breadth.
    """
    sc = facts.scoring
    dim = _SC_DIM

    signals: list[tuple[str, int]] = []
    amber_risks = 0

    # ── Presence detection from facts (granularity color mapping) ───────
    has_api = sc.state_validation_api_granularity in (_GRAN_RICH, _GRAN_PARTIAL)
    has_script = sc.scriptable_via_shell_granularity in (_GRAN_FULL, _GRAN_PARTIAL)
    has_ai_vision = sc.gui_state_visually_evident_granularity in (_GRAN_FULL, _GRAN_PARTIAL)

    # ── Credit signals (color-aware via granularity) ────────────────────
    # Scoring dimension uses a tighter amber fraction (1/3 vs 1/2) because
    # "can't really tell" on scoring methods should not produce 12/15.
    # Frank 2026-04-13: uncertain methods should land ~6/15.
    _sc_amber_div = cfg.SCORING_AMBER_CREDIT_FRACTION

    if has_api:
        base = _signal_points(dim, _SIG_SCORING_API)
        if sc.state_validation_api_granularity == _GRAN_RICH:
            signals.append((_SIG_SCORING_API, base))
        else:
            signals.append((_SIG_SCORING_API, base // _sc_amber_div))
            amber_risks += 1

    if has_script:
        base = _signal_points(dim, _SIG_SCRIPT_SCORING)
        if sc.scriptable_via_shell_granularity == _GRAN_FULL:
            signals.append((_SIG_SCRIPT_SCORING, base))
        else:
            signals.append((_SIG_SCRIPT_SCORING, base // _sc_amber_div))
            amber_risks += 1

    if has_ai_vision:
        base = _signal_points(dim, _SIG_AI_VISION)
        if sc.gui_state_visually_evident_granularity == _GRAN_FULL:
            signals.append((_SIG_AI_VISION, base))
        else:
            signals.append((_SIG_AI_VISION, base // _sc_amber_div))
            amber_risks += 1

    if sc.simulation_scoring_viable and not (has_api or has_script or has_ai_vision):
        # Simulation scoring is amber-only per config — only credit it
        # when nothing else is viable (otherwise the real methods above
        # already carry the dimension).
        signals.append((_SIG_SIMULATION_SCORABLE, _signal_points(dim, _SIG_SIMULATION_SCORABLE)))
        amber_risks += 1

    # ── Grand Slam breadth cap ──────────────────────────────────────────
    # Full marks require AI Vision PLUS at least one programmatic method.
    full_cap = _dim_cap(dim)
    if has_ai_vision and (has_script or has_api):
        breadth_cap = full_cap
    elif has_script:
        breadth_cap = full_cap  # VM context, Script alone can hit full
    elif has_api:
        breadth_cap = cfg.SCORING_API_ALONE_CAP
    elif has_ai_vision:
        breadth_cap = cfg.SCORING_AI_VISION_ALONE_CAP
    else:
        breadth_cap = 0

    # ── Raw total + apply whichever cap is tighter (breadth vs risk) ────
    raw_total = sum(pts for _, pts in signals)
    score, effective_cap = _apply_risk_cap_reduction(
        raw_total, dim, amber_risks, red_risks=0, preset_cap=breadth_cap,
    )

    dimension_score = DimensionScore(
        name=dim.name,
        score=score,
        weight=dim.weight,
        summary=sc.description,
    )

    return _DimensionResult(
        dimension_score=dimension_score,
        signals_matched=signals,
        penalties_applied=[],
        amber_risks=amber_risks,
        red_risks=0,
        raw_total=raw_total,
        effective_cap=effective_cap,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Dimension 1.4 — Teardown
# ═══════════════════════════════════════════════════════════════════════════════

def score_teardown(facts: ProductLababilityFacts) -> _DimensionResult:
    """Compute Teardown dimension score from facts.

    Datacenter (+25) applies when the product runs in Skillable's real
    infrastructure (Hyper-V / Container / ESX implied by installable).
    Simulation paths earn Simulation Reset (+0, display only) per
    Frank 2026-04-07 — simulations don't have an operational teardown
    story, so the full 25 was misleading.

    SaaS / cloud paths depend on vendor APIs:
      Teardown API rich/partial → +22 green / half amber
      No teardown API           → Manual Teardown penalty (-10)

    Orphan Risk (-5) stacks alongside a partial Teardown API.
    """
    td = facts.teardown
    p = facts.provisioning
    dim = _TD_DIM

    signals: list[tuple[str, int]] = []
    penalties: list[tuple[str, int]] = []
    amber_risks = 0
    red_risks = 0

    # ── Does Skillable host the real environment? (Datacenter green) ────
    runs_in_real_fabric = p.runs_as_installable or p.runs_as_container

    if runs_in_real_fabric:
        # Datacenter = automatic teardown via snapshot revert or container destroy
        signals.append((_SIG_DATACENTER, _signal_points(dim, _SIG_DATACENTER)))
    else:
        # Cloud / SaaS path — rely on vendor teardown API
        if td.vendor_teardown_api_granularity == _GRAN_RICH:
            signals.append((_SIG_TEARDOWN_API, _signal_points(dim, _SIG_TEARDOWN_API)))
        elif td.vendor_teardown_api_granularity == _GRAN_PARTIAL:
            base = _signal_points(dim, _SIG_TEARDOWN_API)
            signals.append((_SIG_TEARDOWN_API, base // 2))  # magic-allowed: amber fires at half the green signal credit
            amber_risks += 1
        else:
            # Check for Simulation fallback before penalizing
            if p.runs_as_saas_only and not (p.runs_as_azure_native or p.runs_as_aws_native):
                # Pure SaaS with no teardown API — Simulation may be the lab path
                # Simulation Reset earns zero points but isn't a penalty
                signals.append((_SIG_SIMULATION_RESET, _signal_points(dim, _SIG_SIMULATION_RESET)))
            else:
                # No teardown mechanism confirmed → manual teardown penalty
                penalties.append(
                    (_PEN_MANUAL_TEARDOWN, _penalty_deduction(dim, _PEN_MANUAL_TEARDOWN))
                )
                red_risks += 1

    # ── Orphan Risk three-tier spectrum (Frank 2026-04-13) ───────────────
    # Low Orphan Risk (green, 0 pts): rich teardown API with minor gaps
    # Orphan Risk (amber, -5): partial API, gaps remain
    # High Orphan Risk (red, -15): no API or major cleanup gaps
    if td.has_orphan_risk:
        if td.vendor_teardown_api_granularity == _GRAN_RICH:
            # Rich API but still flagged orphan risk → minor gaps → green context
            signals.append(("Low Orphan Risk", 0))
        elif td.vendor_teardown_api_granularity == _GRAN_PARTIAL:
            # Partial API + orphan risk → amber
            penalties.append((_PEN_ORPHAN_RISK, _penalty_deduction(dim, _PEN_ORPHAN_RISK)))
            amber_risks += 1
        else:
            # No API + orphan risk → red, severe
            penalties.append(("High Orphan Risk", _penalty_deduction(dim, "High Orphan Risk")))
            red_risks += 1

    # ── Raw total + risk cap reduction ──────────────────────────────────
    raw_total = sum(pts for _, pts in signals) + sum(d for _, d in penalties)
    score, effective_cap = _apply_risk_cap_reduction(
        raw_total, dim, amber_risks, red_risks,
    )

    dimension_score = DimensionScore(
        name=dim.name,
        score=score,
        weight=dim.weight,
        summary=td.description,
    )

    return _DimensionResult(
        dimension_score=dimension_score,
        signals_matched=signals,
        penalties_applied=penalties,
        amber_risks=amber_risks,
        red_risks=red_risks,
        raw_total=raw_total,
        effective_cap=effective_cap,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar composer — Product Labability
# ═══════════════════════════════════════════════════════════════════════════════

def _build_simulation_override_dimensions() -> list[DimensionScore]:
    """Build the four hard-override DimensionScore objects for Simulation fabric.

    Frank 2026-04-08: when Simulation is the chosen fabric, all four Pillar 1
    dimensions get hard override values. Normal scoring is suppressed. Values
    come from scoring_config.SIMULATION_*_POINTS constants — zero hardcoding.
    """
    return [
        DimensionScore(
            name=_PROV_DIM.name,
            score=cfg.SIMULATION_PROVISIONING_POINTS,
            weight=_PROV_DIM.weight,
            summary="Simulation is the chosen fabric — fallback when real provisioning isn't possible. Middle credit, no badges, gray bar: simulation elides the real fabric entirely, so nothing was evidenced to earn or lose points against.",
        ),
        DimensionScore(
            name=_LA_DIM.name,
            score=cfg.SIMULATION_LAB_ACCESS_POINTS,
            weight=_LA_DIM.weight,
            summary="Simulation Lab Access — middle credit, no badges, gray bar. Learners log into the simulation environment directly, no identity / licensing friction of the vendor's real product. Symmetric with Provisioning and Teardown in the override state.",
        ),
        DimensionScore(
            name=_SC_DIM.name,
            score=cfg.SIMULATION_SCORING_POINTS,
            weight=_SC_DIM.weight,
            summary="Simulation Scoring — zero credit. Automated scoring within simulations is not supported today. Feature request, not a current capability. Can be changed as the product evolves.",
        ),
        DimensionScore(
            name=_TD_DIM.name,
            score=cfg.SIMULATION_TEARDOWN_POINTS,
            weight=_TD_DIM.weight,
            summary="Simulation Teardown — middle credit, no badges, gray bar. Simulation sessions end with the learner session, so there's no operational teardown to evaluate. Symmetric with Provisioning and Lab Access in the override state.",
        ),
    ]


def score_product_labability(facts: ProductLababilityFacts) -> PillarScore:
    """Compose the four Pillar 1 dimensions into a PillarScore.

    Applies cross-dimension ceilings + Simulation hard override:
      - **Simulation hard override** (Frank 2026-04-08) — when the primary
        fabric resolves to Simulation, the composer skips the normal scorers
        for Lab Access, Scoring, and Teardown and uses the
        SIMULATION_*_POINTS constants directly. Provisioning, Lab Access,
        and Teardown all render symmetrically (12 / 12 / 0 / 12 = 36/100)
        with no badges — gray bars only. No dimension gets "full credit"
        just because simulation elides it; no dimension gets rock-bottom
        credit just because simulation doesn't use it.
      - Sandbox API red cap (Pillar 1 ≤ 25 if Simulation viable, ≤ 5 otherwise)
      - bare_metal_required → Pillar 1 ≤ 5

    Returns a PillarScore with the four dimensions attached and
    score_override set when a ceiling applies.
    """
    prov_result = score_provisioning(facts)

    if prov_result.simulation_chosen:
        # ── Simulation hard override — all four dimensions use fixed values ──
        dimensions = _build_simulation_override_dimensions()
        pillar = PillarScore(
            name=_PL_PILLAR.name,
            weight=_PL_PILLAR.weight,
            dimensions=dimensions,
        )
        # No ceiling flags flipped here — the hard override IS the cap.
        # Pillar total = sum of the four SIMULATION_*_POINTS constants = 36.
        from models import recompute_pillar_score
        recompute_pillar_score(pillar)
        return pillar

    # ── Normal path — run the other three dimension scorers ──
    la_result = score_lab_access(facts)
    sc_result = score_scoring(facts)
    td_result = score_teardown(facts)

    dimensions = [
        prov_result.dimension_score,
        la_result.dimension_score,
        sc_result.dimension_score,
        td_result.dimension_score,
    ]

    # Aggregate all ceiling flags raised by any dimension
    all_ceiling_flags: list[str] = []
    for r in (prov_result, la_result, sc_result, td_result):
        all_ceiling_flags.extend(r.ceiling_flags)

    pillar = PillarScore(
        name=_PL_PILLAR.name,
        weight=_PL_PILLAR.weight,
        dimensions=dimensions,
    )

    # ── Apply Sandbox API red Pillar 1 cap ──────────────────────────────
    raw_pillar_total = sum(d.score for d in dimensions)
    override: int | None = None

    if _CEIL_SANDBOX_RED_NOTHING_VIABLE in all_ceiling_flags:
        override = min(raw_pillar_total, cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE)
    elif _CEIL_SANDBOX_RED_SIM_VIABLE in all_ceiling_flags:
        override = min(raw_pillar_total, cfg.SANDBOX_API_RED_CAP_SIM_VIABLE)

    # ── Apply bare_metal_required ceiling (hardest cap) ─────────────────
    if _CEIL_BARE_METAL in all_ceiling_flags:
        # Use the nothing-viable cap constant as the bare-metal cap per
        # Badging-and-Scoring-Reference: "Product Labability ≤ 5"
        hard_cap = cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE
        override = hard_cap if override is None else min(override, hard_cap)

    if override is not None:
        pillar.score_override = override

    # Populate the stored `score` field — PillarScore.score is a dataclass
    # field (not a property) so it survives asdict() serialization. Every
    # pillar scorer is responsible for setting it before returning.
    from models import recompute_pillar_score
    recompute_pillar_score(pillar)

    return pillar


# ═══════════════════════════════════════════════════════════════════════════════
# Orchestration method derivation — internal plumbing for ACV rate tier
# and Technical Fit Multiplier.
#
# The user-facing badge is fabric-neutral ("Runs in VM" — the SE decides
# whether it's Hyper-V or ESX).  The orchestration_method string is
# INTERNAL ONLY — it drives two things behind the scenes:
#   1. ACV rate tier lookup (cloud $6/hr vs VM $14/hr vs large VM $45/hr)
#   2. Technical Fit Multiplier (datacenter vs non-datacenter method class)
#
# The user never sees this field.  Badges are unchanged.
# ═══════════════════════════════════════════════════════════════════════════════

# Map primary-fabric signal name → internal orchestration_method string.
# These strings must match the keys in scoring_config.ORCHESTRATION_TO_RATE_TIER
# and the values checked in scoring_config.DATACENTER_METHODS.
_SIGNAL_TO_ORCHESTRATION: dict[str, str] = {
    _SIG_VM:          "Hyper-V",
    _SIG_ESX:         "ESX",
    _SIG_CONTAINER:   "Container",
    _SIG_AZURE:       "Azure Cloud Slice",
    _SIG_AWS:         "AWS Cloud Slice",
    _SIG_SANDBOX_API: "Custom API",
    _SIG_M365_TENANT: "Hyper-V",       # M365 labs run on Hyper-V VMs
    _SIG_M365_ADMIN:  "Hyper-V",       # M365 Admin also runs on Hyper-V VMs
    _SIG_SIMULATION:  "Simulation",
}


def derive_orchestration_method(
    facts: ProductLababilityFacts,
    underlying_technologies: list[dict] | None = None,
) -> str:
    """Derive the internal orchestration_method from Pillar 1 facts.

    Reuses _pick_primary_fabric (the same logic the scorer uses) to
    determine which fabric won, then maps it to the orchestration_method
    string that drives ACV rate tier and Technical Fit Multiplier lookups.

    For wrapper org products (certs, degrees, courses): when provisioning
    facts are empty or SaaS-only but underlying_technologies exist, derive
    the orchestration method from the dominant deployment_model of the
    technologies inside the wrapper. This ensures a cybersecurity cert
    (wrapper = SaaS) gets the VM rate (underlying tools are installable),
    not the cloud rate.

    Returns an empty string only when no fabric is pickable at all
    (bare metal / GCP-only with no alternative).
    """
    primary = _pick_primary_fabric(facts.provisioning)

    # ── Wrapper org fallback: use underlying technologies ──
    # When the provisioning facts point to SaaS/Simulation but the product
    # has underlying technologies with real deployment models, use the
    # dominant technology deployment model instead.
    if (primary in (_SIG_SIMULATION, _SIG_SANDBOX_API, None)
            and underlying_technologies):
        deploy_counts: dict[str, int] = {}
        for tech in underlying_technologies:
            dm = (tech.get("deployment_model") or "").lower()
            if dm:
                deploy_counts[dm] = deploy_counts.get(dm, 0) + 1
        if deploy_counts:
            dominant = max(deploy_counts, key=deploy_counts.get)  # type: ignore[arg-type]
            _DEPLOY_TO_SIGNAL = {
                "installable": _SIG_VM,
                "hybrid": _SIG_VM,
                "cloud": _SIG_AZURE,
                "saas-only": _SIG_SANDBOX_API,
            }
            tech_signal = _DEPLOY_TO_SIGNAL.get(dominant)
            if tech_signal:
                return _SIGNAL_TO_ORCHESTRATION.get(tech_signal, "")

    if primary is None:
        if not facts.provisioning.needs_bare_metal and not facts.provisioning.needs_gcp:
            primary = _SIG_SIMULATION
        else:
            return ""

    base_method = _SIGNAL_TO_ORCHESTRATION.get(primary, "")

    # ── Complexity escalation for VM products ──────────────────────────
    # When the product runs on VMs (Hyper-V/ESX) and has multi-VM or
    # complex topology facts, escalate to the large/complex VM rate tier.
    # This ensures Trellix-class cybersecurity platforms get $45/hr
    # instead of $14/hr. The rate tier is internal plumbing — badges
    # are unchanged.
    if base_method in ("Hyper-V", "ESX"):
        p = facts.provisioning
        if p.is_multi_vm_lab or p.has_complex_topology or p.is_large_lab:
            return "Large VM"  # maps to VM_HIGH_RATE via ORCHESTRATION_TO_RATE_TIER

    return base_method
