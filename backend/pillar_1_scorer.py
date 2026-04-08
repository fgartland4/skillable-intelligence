"""Pillar 1 (Product Labability) scoring from facts — pure Python.

Reads ProductLababilityFacts typed primitives and produces a PillarScore
directly.  No Claude.  No badge name inputs.  No hardcoded numbers.

Architecture layer: SCORE (per docs/Platform-Foundation.md → Three Layers
of Intelligence).  Companion to the rebuild described in
docs/next-session-todo.md §0c Step 3.

Runs alongside the legacy monolithic scoring Claude call as a comparison
path during the rebuild.  Step 5 cutover replaces the legacy path with
this one.

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

      Legacy:  badge.name == "Runs in Hyper-V" → +30 signal credit
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
_SIG_HYPER_V = "Runs in Hyper-V"
_SIG_AZURE = "Runs in Azure"
_SIG_AWS = "Runs in AWS"
_SIG_CONTAINER = "Runs in Container"
_SIG_ESX = "ESX Required"
_SIG_SANDBOX_API = "Sandbox API"
_SIG_SIMULATION = "Simulation"

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

# Ceiling flag names (match scoring_math / scoring_config where applicable)
_CEIL_SANDBOX_RED_SIM_VIABLE = "sandbox_api_red_sim_viable"
_CEIL_SANDBOX_RED_NOTHING_VIABLE = "sandbox_api_red_nothing_viable"
_CEIL_BARE_METAL = "bare_metal_required"
_CEIL_NO_API_AUTOMATION = "no_api_automation"


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
    _signal_points(_PROV_DIM, _SIG_HYPER_V)
    _signal_points(_PROV_DIM, _SIG_AZURE)
    _signal_points(_PROV_DIM, _SIG_AWS)
    _signal_points(_PROV_DIM, _SIG_CONTAINER)
    _signal_points(_PROV_DIM, _SIG_ESX)
    _signal_points(_PROV_DIM, _SIG_SANDBOX_API)
    _signal_points(_PROV_DIM, _SIG_SIMULATION)
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

def score_provisioning(facts: ProductLababilityFacts) -> _DimensionResult:
    """Compute Provisioning dimension score from facts.

    Walks the fabric priority order (VM → Cloud Slice → Sandbox API →
    Simulation) and picks the first viable path.  Adds friction penalties
    (GPU Required).  Raises Sandbox API red ceiling flag when SaaS-only
    with no provisioning API.

    Priority order per docs/Badging-and-Scoring-Reference.md §1.1:
      1. Runs in Hyper-V / Container — installable on VM or container-native
      2. Runs in Azure / Runs in AWS — cloud-native managed service
      3. Sandbox API — vendor exposes per-learner provisioning API
      4. Simulation — real fabric when nothing else is viable
    """
    p = facts.provisioning
    dim = _PROV_DIM

    signals: list[tuple[str, int]] = []
    penalties: list[tuple[str, int]] = []
    amber_risks = 0
    red_risks = 0
    ceiling_flags: list[str] = []
    fabric_chosen = False
    simulation_viable = False
    sandbox_red = False

    # ── Priority 1: VM fabric (installable or container-native) ──────────
    # Hyper-V is the default installable VM fabric.  Container is scored
    # equivalently and is mutually exclusive — pick whichever describes
    # the primary deployment shape.  The facts may set both (Docker image
    # exists for an installable product); Hyper-V wins by priority order.
    if p.runs_as_installable:
        signals.append((_SIG_HYPER_V, _signal_points(dim, _SIG_HYPER_V)))
        fabric_chosen = True
    elif p.runs_as_container:
        signals.append((_SIG_CONTAINER, _signal_points(dim, _SIG_CONTAINER)))
        fabric_chosen = True

    # ── Priority 2: Cloud Slice (Azure preferred over AWS) ───────────────
    if not fabric_chosen:
        if p.runs_as_azure_native:
            signals.append((_SIG_AZURE, _signal_points(dim, _SIG_AZURE)))
            fabric_chosen = True
        elif p.runs_as_aws_native:
            signals.append((_SIG_AWS, _signal_points(dim, _SIG_AWS)))
            fabric_chosen = True

    # ── Priority 3: Sandbox API (color-aware via granularity) ────────────
    if not fabric_chosen and p.has_sandbox_api:
        base_pts = _signal_points(dim, _SIG_SANDBOX_API)
        if p.sandbox_api_granularity == _GRAN_RICH:
            signals.append((_SIG_SANDBOX_API, base_pts))  # green = full credit
            fabric_chosen = True
        elif p.sandbox_api_granularity == _GRAN_PARTIAL:
            # amber = half credit (rounds via int division, same as scoring_math)
            signals.append((_SIG_SANDBOX_API, base_pts // 2))
            amber_risks += 1
            fabric_chosen = True
        else:
            # Has sandbox API claimed but granularity is "none" or missing
            # → treated as red (no coverage confirmed)
            sandbox_red = True
            red_risks += 1

    # ── SaaS-only with no provisioning API at all → Sandbox API red ──────
    if not fabric_chosen and p.runs_as_saas_only and not p.has_sandbox_api:
        sandbox_red = True
        red_risks += 1

    # ── Priority 4: Simulation (last-resort viable fabric) ───────────────
    if not fabric_chosen:
        if not p.needs_bare_metal and not p.needs_gcp:
            signals.append((_SIG_SIMULATION, _signal_points(dim, _SIG_SIMULATION)))
            simulation_viable = True
            fabric_chosen = True

    # ── Sandbox API red Pillar 1 ceiling flag ────────────────────────────
    if sandbox_red:
        if simulation_viable:
            ceiling_flags.append(_CEIL_SANDBOX_RED_SIM_VIABLE)
        else:
            ceiling_flags.append(_CEIL_SANDBOX_RED_NOTHING_VIABLE)

    # ── Bare metal / GCP ceiling flags ───────────────────────────────────
    if p.needs_bare_metal:
        ceiling_flags.append(_CEIL_BARE_METAL)
        red_risks += 1
    if p.needs_gcp:
        amber_risks += 1  # No native Skillable GCP path

    # ── Friction penalties ───────────────────────────────────────────────
    if p.needs_gpu:
        penalties.append((_PEN_GPU, _penalty_deduction(dim, _PEN_GPU)))
        amber_risks += 1

    # ── Compute raw total + apply risk cap reduction ─────────────────────
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
        signals.append((_SIG_IDENTITY_API, base // 2))
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
        signals.append((_SIG_TRAINING_LICENSE, base // 2))
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
    if has_api:
        base = _signal_points(dim, _SIG_SCORING_API)
        if sc.state_validation_api_granularity == _GRAN_RICH:
            signals.append((_SIG_SCORING_API, base))
        else:
            signals.append((_SIG_SCORING_API, base // 2))
            amber_risks += 1

    if has_script:
        base = _signal_points(dim, _SIG_SCRIPT_SCORING)
        if sc.scriptable_via_shell_granularity == _GRAN_FULL:
            signals.append((_SIG_SCRIPT_SCORING, base))
        else:
            signals.append((_SIG_SCRIPT_SCORING, base // 2))
            amber_risks += 1

    if has_ai_vision:
        base = _signal_points(dim, _SIG_AI_VISION)
        if sc.gui_state_visually_evident_granularity == _GRAN_FULL:
            signals.append((_SIG_AI_VISION, base))
        else:
            signals.append((_SIG_AI_VISION, base // 2))
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
            signals.append((_SIG_TEARDOWN_API, base // 2))
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

    # ── Orphan Risk stacks with partial teardown coverage ───────────────
    if td.has_orphan_risk:
        penalties.append((_PEN_ORPHAN_RISK, _penalty_deduction(dim, _PEN_ORPHAN_RISK)))
        amber_risks += 1

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

def score_product_labability(facts: ProductLababilityFacts) -> PillarScore:
    """Compose the four Pillar 1 dimensions into a PillarScore.

    Applies cross-dimension ceilings:
      - Sandbox API red cap (Pillar 1 ≤ 25 if Simulation viable, ≤ 5 otherwise)
        per scoring_config.SANDBOX_API_RED_CAP_SIM_VIABLE /
        SANDBOX_API_RED_CAP_NOTHING_VIABLE
      - bare_metal_required → Pillar 1 ≤ 5 (Platform-Foundation Pillar 1 note)

    Returns a PillarScore with the four dimensions attached and
    score_override set when a ceiling applies.
    """
    prov_result = score_provisioning(facts)
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

    return pillar
