"""Data models for the Skillable Intelligence Platform.

Built from Platform-Foundation.md and Badging-and-Scoring-Reference.md.
All field names use locked vocabulary (GP4 — Self-Evident Design).

Hierarchy: Fit Score → Pillars → Dimensions → Requirements (badges)
Three Pillars (50/20/30): Product Labability, Instructional Value, Customer Fit
Each Pillar scores out of 100 internally, then weighted to Fit Score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Evidence — the atomic unit of trustworthiness (GP3)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Evidence:
    """A single research finding with confidence coding.

    Every badge must carry evidence. No badge renders without it.
    Confidence is core logic — every finding carries level + explanation.
    """
    claim: str
    confidence_level: str          # "confirmed" | "indicated" | "inferred"
    confidence_explanation: str    # Short (1-2 sentences) — why this confidence level
    source_url: Optional[str] = None
    source_title: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Badge — a scored finding within a Dimension
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Badge:
    """A scored finding that surfaces as a visual indicator in the UX.

    Color = the assessment. Evidence = the basis. Together they're complete.

    Pillar 2/3 RUBRIC fields (strength, signal_category) are required for
    rubric-model dimensions and ignored elsewhere. They MUST be carried
    through from Claude's output via scorer._parse_badges_for_dimension
    so the math layer can credit points by (dimension, strength) lookup
    against the dimension's rubric tiers.
    """
    name: str
    color: str                     # "green" | "gray" | "amber" | "red"
    qualifier: str = ""            # "Strength" | "Opportunity" | "Context" | "Risk" | "Blocker"
    evidence: list[Evidence] = field(default_factory=list)
    # Pillar 2/3 rubric fields — empty string for Pillar 1 / non-rubric badges
    strength: str = ""             # "strong" | "moderate" | "weak" — math driver
    signal_category: str = ""      # one of the dimension's signal_categories — analytics tag


# ═══════════════════════════════════════════════════════════════════════════════
# Dimension — a scored area within a Pillar
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DimensionScore:
    """Score for one dimension within a Pillar.

    Score is 0 to dimension weight (e.g., Provisioning 0-35).
    Dimensions within a Pillar sum to the Pillar's score out of 100.
    """
    name: str
    score: int = 0
    weight: int = 0                # Max possible score for this dimension
    summary: str = ""
    badges: list[Badge] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar — a weighted component of the Fit Score
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PillarScore:
    """Score for one of the three Pillars.

    Each Pillar scores out of 100 internally (sum of its dimension scores),
    then gets weighted to its share of the Fit Score.

    **`score` is a stored field, not a computed property.** It must be set
    explicitly by the per-pillar scorer (pillar_1_scorer / pillar_2_scorer /
    pillar_3_scorer) after the dimensions are populated, so that when the
    scored Product is serialized via `dataclasses.asdict`, the pillar.score
    value survives into the saved JSON and the template can read it.

    Why this is a field, not a property: `asdict()` drops all @property
    methods, which silently zeroed every pillar header in the dossier on
    the first real Trellix run (2026-04-08). The fix is to make score a
    real dataclass field that the scorer always populates.

    `recompute_pillar_score()` is the helper every scorer uses to compute
    the right value from dimensions + score_override. Call it at the end
    of the scorer after building the dimensions and before returning the
    PillarScore. Cache-reload paths can call it again on a dict form via
    the parallel `recompute_pillar_score_on_dict` helper.

    `score_override` lets the scoring math layer set the pillar score
    explicitly — used when ceiling flags cap Product Labability below the
    raw dimension sum. Dimension scores remain authentic to the badges
    that matched; the override only affects the pillar-level score.
    """
    name: str
    weight: int                    # Percentage of Fit Score (50, 20, or 30)
    dimensions: list[DimensionScore] = field(default_factory=list)
    score: int = 0                 # Stored — set by the pillar scorer via recompute_pillar_score()
    score_override: Optional[int] = None  # Set by pillar_1_scorer when bare-metal / sandbox ceiling enforced

    @property
    def weighted_contribution(self) -> float:
        """This Pillar's contribution to the Fit Score."""
        return self.score * (self.weight / 100)


def recompute_pillar_score(pillar: PillarScore) -> int:
    """Compute a PillarScore.score from its dimensions + score_override.

    This is the ONE place the rule lives:
      - If score_override is set (Pillar 1 cap via bare_metal / sandbox red),
        use it.
      - Otherwise sum the dimensions, capped at 100.

    Called by pillar_1_scorer / pillar_2_scorer / pillar_3_scorer at the
    end of each scorer, AFTER the dimensions are populated. Also called
    by intelligence.recompute_analysis on the dict form so cache reloads
    populate the field for analyses saved before the field existed.
    """
    if pillar.score_override is not None:
        pillar.score = int(pillar.score_override)
    else:
        pillar.score = min(100, sum(int(d.score or 0) for d in pillar.dimensions))
    return pillar.score


# ═══════════════════════════════════════════════════════════════════════════════
# Fit Score — the composite of three Pillars
# ═══════════════════════════════════════════════════════════════════════════════


def _build_default_pillar(pillar_key: str) -> "PillarScore":
    """Build a default PillarScore for a FitScore field, sourced from
    scoring_config.PILLARS — the single Define-Once source of truth for
    pillar weights, dimension names, and dimension weights.

    pillar_key is the FitScore field name (e.g. "product_labability"),
    which matches the lowercase-snake form of the Pillar name in
    scoring_config.PILLARS.

    Lazy import on scoring_config to avoid a circular import at module
    load time. Called only at FitScore instantiation, never at import.

    CRIT-8 in code-review-2026-04-07.md: this replaces the previous
    pattern where every pillar/dimension weight was hardcoded in the
    FitScore default factories, duplicating values from scoring_config.
    """
    import scoring_config as cfg
    for pillar in cfg.PILLARS:
        pkey = pillar.name.lower().replace(" ", "_")
        if pkey == pillar_key:
            return PillarScore(
                name=pillar.name,
                weight=pillar.weight,
                dimensions=[
                    DimensionScore(name=dim.name, weight=dim.weight)
                    for dim in pillar.dimensions
                ],
            )
    raise ValueError(
        f"_build_default_pillar: no pillar in scoring_config.PILLARS matches "
        f"key {pillar_key!r}. Expected one of: "
        f"{[p.name.lower().replace(' ', '_') for p in cfg.PILLARS]}"
    )


@dataclass
class FitScore:
    """The composite Fit Score — three Pillars weighted 50/20/30.

    Product Labability (50%) + Instructional Value (20%) = 70% product
    Customer Fit (30%) = 30% organization

    Math layer audit trail:
      - `total_override` — set by fit_score_composer when the Technical Fit Multiplier or
        Technical Fit Multiplier change the result from a naive weighted sum.
      - `pl_score_pre_ceiling` — what Product Labability would have scored
        without ceiling enforcement.
      - `technical_fit_multiplier` — the multiplier applied to IV + CF.
      - `ceilings_applied` — list of flags that capped Product Labability.
    """
    # CRIT-8 in code-review-2026-04-07.md: pillar/dimension structure is
    # built dynamically from scoring_config.PILLARS at instantiation time.
    # Previously this dataclass hardcoded every pillar weight and every
    # dimension weight, duplicating values that already lived in the
    # config — the worst Define-Once violation in the codebase. Now there
    # are zero literal weight values in this file. If scoring_config.PILLARS
    # changes (e.g., a dimension weight is tweaked), every freshly-created
    # FitScore reflects it automatically.
    #
    # _build_default_pillar() is the helper. It takes the pillar key
    # (matching the field name) and returns a PillarScore built from
    # cfg.PILLARS. Imported lazily inside the lambda to avoid a circular
    # import (scoring_config doesn't import models, but models is imported
    # by scorer at module load time and we want this to resolve at
    # instantiation, not import time).
    product_labability: PillarScore = field(default_factory=lambda: _build_default_pillar("product_labability"))
    instructional_value: PillarScore = field(default_factory=lambda: _build_default_pillar("instructional_value"))
    customer_fit: PillarScore = field(default_factory=lambda: _build_default_pillar("customer_fit"))
    total: int = 0                 # Stored — set by fit_score_composer via recompute_fit_total()
    total_override: Optional[int] = None
    pl_score_pre_ceiling: Optional[int] = None
    technical_fit_multiplier: float = 1.0
    ceilings_applied: list[dict] = field(default_factory=list)

    @property
    def pillars(self) -> list[PillarScore]:
        return [self.product_labability, self.instructional_value, self.customer_fit]

    @property
    def verdict_inputs(self) -> dict:
        """Returns the inputs needed for verdict grid lookup."""
        return {
            "fit_score": self.total,
            "product_labability_score": self.product_labability.score,
        }


def recompute_fit_total(fit_score: "FitScore") -> int:
    """Compute FitScore.total from pillar scores + total_override.

    Called by fit_score_composer.compose_fit_score after writing
    total_override, and by intelligence.recompute_analysis's dict path
    for cache reloads of analyses saved before `total` was a stored
    field.

    Rule: if total_override is set (composer applied the Technical Fit
    Multiplier), use it. Otherwise fall back to the pure weighted sum
    of pillar contributions — which is what FitScore should read on
    freshly-constructed objects before the composer runs.
    """
    if fit_score.total_override is not None:
        fit_score.total = int(fit_score.total_override)
    else:
        fit_score.total = round(sum(p.weighted_contribution for p in fit_score.pillars))
    return fit_score.total


# ═══════════════════════════════════════════════════════════════════════════════
# Verdict — action-oriented label from Fit Score + ACV
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Verdict:
    """The verdict combines Fit Score and ACV Potential into an action label."""
    label: str                     # e.g., "Prime Target", "Worth Pursuing", "Poor Fit"
    color: str                     # "dark_green", "green", "light_amber", "amber", "red"
    fit_label: str = ""            # e.g., "HIGH FIT"
    acv_label: str = ""            # e.g., "HIGH ACV"


# ═══════════════════════════════════════════════════════════════════════════════
# ACV Potential — calculated, not scored
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConsumptionMotion:
    """One of six consumption motions feeding ACV calculation."""
    label: str = ""
    population_low: int = 0
    population_high: int = 0
    hours_low: float = 0
    hours_high: float = 0
    adoption_pct: float = 0.0
    rationale: str = ""


@dataclass
class ACVPotential:
    """Estimated annual contract value.

    ACV = Population x Adoption Rate x Hours per Learner x Rate
    Calculated, not scored. Separate hero metric from Fit Score.
    """
    motions: list[ConsumptionMotion] = field(default_factory=list)
    annual_hours_low: int = 0
    annual_hours_high: int = 0
    rate_per_hour: float = 0.0     # Determined by delivery path
    acv_low: float = 0.0
    acv_high: float = 0.0
    acv_tier: str = ""             # "high" | "medium" | "low"
    methodology_note: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Contacts — who to talk to
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Contact:
    """A person identified during research."""
    name: str
    title: str
    role_type: str                 # "decision_maker" | "influencer"
    linkedin_url: Optional[str] = None
    relevance: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Owning Organization — which department owns this product
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OrgUnit:
    """The organizational unit that owns a product's training."""
    name: str
    type: str                      # "department" | "subsidiary" | "business_unit"
    description: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Fact Drawer — structured truth from the Research layer
# ═══════════════════════════════════════════════════════════════════════════════
#
# The fact drawer is the canonical home for everything Research extracts about
# a product or a company.  It implements the "Research → Store → Score → Badge"
# architecture documented in Platform-Foundation.md → "The Three Layers of
# Intelligence."  Facts are stored as TRUTH (not pre-judged interpretations).
# Scoring reads the facts and applies framework rules; badging reads the facts
# AND the score to pick contextual storytellers.
#
# Two principles govern every field below:
#
#   1. **Truth, not interpretation.**  No `strength` field, no pre-baked
#      tier judgments.  Each fact is what the researcher observed, with
#      enough context that downstream scoring can make a real judgment.
#
#   2. **Define-Once.**  Each fact lives in exactly one location.
#      Cross-pillar reads are explicit (e.g., Pillar 2 Market Demand reads
#      `enterprise_reference_customers` from `CustomerFitFacts`); the same
#      fact never lives in two places.
#
# Field naming convention: typed primitives where possible (bool, str, enum
# strings, NumericRange, list[str], dict[str, ...]).  Qualitative dimensions
# use a `signals: dict[str, SignalEvidence]` where the keys come from the
# canonical signal_category list in scoring_config.py (Define-Once — the
# signal categories live there, not duplicated here).


@dataclass
class NumericRange:
    """A believable numeric range with provenance.

    Used for facts that are inherently ranges — install base, partner
    community size, employee count, event attendance, etc.  Single-point
    estimates are stored as `low == high`.

    Frank 2026-04-07: ranges must be **believable**.  A range of
    2,000–40,000 signals "we have no idea" and is forbidden.  The
    researcher produces tight, defendable ranges the seller can quote.
    """
    low: Optional[int] = None
    high: Optional[int] = None
    source_url: str = ""
    confidence: str = ""              # "confirmed" | "indicated" | "inferred"
    notes: str = ""                   # Researcher's free-text flag for anything unusual


@dataclass
class SignalEvidence:
    """Raw evidence that a qualitative signal is present.

    Used for rubric-model dimensions (Pillar 2, Pillar 3) where the
    research finding is genuinely qualitative — "is this product
    multi-phase workflow at strong strength?" can't be reduced to a
    typed primitive.

    NO `strength` field.  Strength is interpretation; this drawer holds
    truth only.  Scoring reads `observation` and decides strength tier
    via the rubric judgment step.

    Per Frank 2026-04-07: "We're storing facts that have enough context
    to be scored later."  The `observation` field is where that context
    lives — concrete enough that downstream judgment is grounded, not
    stripped of meaning.
    """
    present: bool = False
    observation: str = ""             # What the researcher observed — the raw truth
    source_url: str = ""
    confidence: str = ""              # "confirmed" | "indicated" | "inferred"


@dataclass
class GradedSignal:
    """A rubric signal that's been graded for strength and evidence text.

    Produced by `backend/rubric_grader.py` — one focused Claude call per
    rubric dimension reads the fact drawer for that dimension and emits
    a list of GradedSignal records.  The pure-Python Pillar 2/3 scorers
    then read these records deterministically (look up point values from
    `scoring_config.py` by `signal_category` + `strength`, apply
    baselines, apply caps).

    Architecturally this is the narrow slice of Claude-in-Score that
    the rebuild permits (lock-in #4 in docs/next-session-todo.md §0b).
    Strength grading and evidence phrasing are both qualitative work
    that can't reduce to Python heuristics without losing meaning.
    Every other step in the Score layer stays pure Python.

    Per Frank 2026-04-08 — the grader outputs live on `Product.
    rubric_grades` (per-product dims) and `CompanyAnalysis.
    customer_fit_rubric_grades` (per-company dims), KEEPING the
    underlying `SignalEvidence` truth-only fact drawer intact.  Facts
    stay truth-only; grades are a separate derived artifact.
    """
    signal_category: str              # e.g., "multi_vm_architecture", "atp_alp_program"
    strength: str                     # "strong" | "moderate" | "weak" | "informational"
    evidence_text: str                # Plain English with confidence hedging — feeds badge display
    confidence: str                   # "confirmed" | "indicated" | "inferred"
    color: str = ""                   # "green" | "amber" | "red" | "gray" — derived display signal
    source_fact_path: str = ""        # Traceability pointer to the fact field the grade reads


# ─────────────────────────────────────────────────────────────────────────────
# Pillar 1 — Product Labability fact drawer
#
# Capability-store model.  All typed primitives.  Pillar 1 scoring is a
# pure-Python lookup that maps facts to canonical badges and point values.
# No Claude call at scoring time.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProvisioningFacts:
    """Pillar 1.1 — How the product can be deployed and what fabric fits.

    Stores capability flags, not pre-classified delivery paths.  Scoring
    walks the priority order (M365 > VM > Cloud Native > Sandbox API >
    Simulation) at runtime to pick which fabric wins, respecting the
    `preferred_fabric` hint when set.
    """
    description: str = ""             # Narrative: what IS this product's deployment shape?
    runs_as_installable: bool = False
    runs_as_azure_native: bool = False
    runs_as_aws_native: bool = False
    runs_as_container: bool = False
    runs_as_saas_only: bool = False
    supported_host_os: list[str] = field(default_factory=list)  # ["windows", "linux"]
    has_sandbox_api: bool = False
    sandbox_api_granularity: str = ""  # "rich" | "partial" | "none"
    is_multi_vm_lab: bool = False
    has_complex_topology: bool = False
    is_large_lab: bool = False
    has_pre_instancing_opportunity: bool = False
    needs_gpu: bool = False
    needs_bare_metal: bool = False
    needs_gcp: bool = False

    # ── Frank 2026-04-08 additions — Issue #2 fabric priority + optionality ──
    # `preferred_fabric` is the extractor's judgment of which fabric best fits
    # this product based on a multi-factor decision: lab developer control
    # (VM default), VM resource intensity or cost (lean cloud), container
    # production-readiness, and vendor marketing as tiebreaker when technical
    # analysis is neutral. The scorer honors this hint when the fact predicate
    # for the preferred fabric is True, and falls back to static priority
    # order otherwise. See docs/next-session-todo.md §0 for the full rule.
    preferred_fabric: str = ""        # "hyper_v" | "vm" | "container" | "azure" | "aws" | "sandbox_api" | "m365_tenant" | "m365_admin" | "simulation" | ""
    preferred_fabric_rationale: str = ""   # Plain-English why this fabric wins

    # VM footprint context — captured as FACTS, not judgments. The scorer
    # reads these to decide whether a "big VM" product might lean cloud in
    # the preferred_fabric calculation. Normal-sized VMs stay False; only
    # resource-intensive or premium-cost cases set True.
    vm_is_resource_intensive: bool = False    # Big VM (16+ vCPU, 32GB+ RAM, specialized hw)
    vm_has_premium_cost_profile: bool = False # Meaningfully more expensive than cloud alternative
    vm_footprint_notes: str = ""              # Narrative: "Standard Hyper-V profile" or "Requires 16vCPU + 64GB + GPU"

    # Container disqualifier context — the four documented Skillable
    # container disqualifiers. When any of these are True, container is NOT
    # viable as a primary or secondary fabric (the scorer skips it). Capture
    # all four so the scorer + Step 6 badging can cite the specific reason.
    container_is_production_native: bool = False    # Positive when True (not an anti-signal when False)
    container_is_dev_only: bool = False              # Disqualifier: image is labeled dev-only, not production
    container_needs_windows_gui: bool = False        # Disqualifier: requires Windows desktop GUI
    container_needs_multi_vm_network: bool = False   # Disqualifier: needs multi-VM networking
    container_footprint_notes: str = ""              # Narrative context

    # ESX-specific constraints — when True, the scorer fires a separate
    # `ESX Required` amber badge alongside the VM primary (instead of
    # relying on a Hyper-V green that doesn't signal the constraint).
    requires_esx: bool = False
    requires_esx_reason: str = ""     # "Nested virtualization required" / "Socket licensing above 24 vCPUs" etc.

    # ── M365 scenario classification — Frank 2026-04-08 ──
    # Set by the extractor when the product is Microsoft 365-dependent.
    # The scorer picks M365 Tenant / M365 Admin as the primary fabric
    # BEFORE walking the VM/Cloud/Sandbox priority order. See
    # scoring_config.SKILLABLE_CAPABILITIES → M365 Tenant / M365 Admin entries for the
    # full capability context.
    m365_scenario: str = ""           # "" | "end_user" | "administration"


@dataclass
class LabAccessFacts:
    """Pillar 1.2 — How learners actually log in to the product.

    auth_model is pure truth — describes how authentication works from
    the user's perspective.  VM vs cloud delivery context is captured
    separately in ProvisioningFacts.runs_as_*.  Scoring combines the
    two at runtime to decide which Skillable canonical applies.
    """
    description: str = ""
    user_provisioning_api_granularity: str = ""  # "rich" | "partial" | "none"
    auth_model: str = ""              # see auth_model values below
    # Valid auth_model values:
    #   "entra_native_tenant" — Skillable provisions in a controlled Entra tenant;
    #                            displays uname+pword in lab
    #   "entra_msft_id"       — Product accepts learner's own Microsoft account;
    #                            Skillable doesn't pre-provision
    #   "sso_saml"            — Generic SAML SSO
    #   "sso_oidc"            — Generic OIDC SSO
    #   "oauth"               — OAuth-based (rare for human login)
    #   "product_credentials" — Product manages its own user database;
    #                            Skillable creates per-learner accounts
    #   "api_key"             — User authenticates via API key (developer products)
    #   "none"                — No documented auth model
    credential_lifecycle: str = ""    # "recyclable" | "pool_only" | "none"
    learner_isolation: str = ""       # "confirmed" | "unknown" | "absent"
    training_license: str = ""        # "low_friction" | "medium_friction" | "blocked" | "none"
    has_mfa_blocker: bool = False
    has_anti_automation: bool = False
    has_rate_limit_blocker: bool = False


@dataclass
class ScoringFacts:
    """Pillar 1.3 — What state-validation surfaces the product exposes.

    Pure capabilities of the product, not Skillable scoring decisions.
    Scoring logic uses the Grand Slam rule (AI Vision + Script OR API
    for full marks) at runtime.
    """
    description: str = ""
    state_validation_api_granularity: str = ""    # "rich" | "partial" | "none"
    scriptable_via_shell_granularity: str = ""    # "full" | "partial" | "none"
    gui_state_visually_evident_granularity: str = ""  # "full" | "partial" | "none"
    simulation_scoring_viable: bool = False


@dataclass
class TeardownFacts:
    """Pillar 1.4 — Vendor-side cleanup capabilities.

    Datacenter snapshot teardown is derived from ProvisioningFacts at
    scoring time (if the product runs in Hyper-V/Container/ESX, teardown
    is automatic).  These fields capture the cloud/SaaS case where
    Skillable depends on the vendor's API to clean up.
    """
    description: str = ""
    vendor_teardown_api_granularity: str = ""  # "rich" | "partial" | "none"
    has_orphan_risk: bool = False


@dataclass
class ProductLababilityFacts:
    """Pillar 1 fact drawer.  All typed primitives, capability-store model."""
    provisioning: ProvisioningFacts = field(default_factory=ProvisioningFacts)
    lab_access: LabAccessFacts = field(default_factory=LabAccessFacts)
    scoring: ScoringFacts = field(default_factory=ScoringFacts)
    teardown: TeardownFacts = field(default_factory=TeardownFacts)


# ─────────────────────────────────────────────────────────────────────────────
# Pillar 2 — Instructional Value fact drawer
#
# Three of four dimensions (Product Complexity, Mastery Stakes, Lab
# Versatility) are purely qualitative — the drawer holds a description and
# a `signals` dict keyed by signal_category.  Market Demand has both
# concrete numeric facts AND a signals dict for the remaining qualitative
# bits.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProductComplexityFacts:
    """Pillar 2.1 — Is this product hard enough to need hands-on practice?

    Almost entirely qualitative.  Signal categories are the canonical list
    from scoring_config.py (multi_vm_architecture, deep_configuration,
    multi_phase_workflow, role_diversity, troubleshooting_depth, etc.).
    """
    description: str = ""
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class MasteryStakesFacts:
    """Pillar 2.2 — What are the consequences of getting it wrong?

    Qualitative.  Signal categories: breach_exposure, compliance_consequences,
    data_integrity, business_continuity, safety_regulated, legal_liability,
    reputation_damage, financial_impact.
    """
    description: str = ""
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class LabVersatilityFacts:
    """Pillar 2.3 — Which lab types fit this product naturally?

    Qualitative.  Signal categories map to LAB_TYPE_MENU entries in
    scoring_config.py (adversarial_scenario, simulated_attack,
    incident_response, break_fix, team_handoff, bug_bounty, cyber_range,
    performance_tuning, migration_lab, architecture_challenge,
    compliance_audit, disaster_recovery, ctf).
    """
    description: str = ""
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class MarketDemandFacts:
    """Pillar 2.4 — How big is the worldwide population that needs this skill?

    Mixed: concrete numeric/list facts for the things that are genuinely
    countable, plus a signals dict for the remaining qualitative judgments.

    install_base is Define-Once — the same number feeds Motion 1 audience
    in ACV AND any Market Demand judgment about install base scale.
    """
    description: str = ""
    # Concrete numeric facts
    install_base: NumericRange = field(default_factory=NumericRange)            # → ACV Motion 1
    employee_subset_size: NumericRange = field(default_factory=NumericRange)    # → ACV Motion 3
    cert_annual_sit_rate: NumericRange = field(default_factory=NumericRange)    # → ACV Motion 4
    # Concrete list/dict facts
    cert_bodies_mentioning: list[str] = field(default_factory=list)             # ["CompTIA", "EC-Council", "SANS"]
    independent_training_course_counts: dict[str, int] = field(default_factory=dict)  # {"Pluralsight": 15, "Coursera": 5}
    # Concrete boolean facts
    is_ai_powered: bool = False
    is_ai_platform: bool = False
    # Remaining qualitative signals (e.g., niche_within_category, cert_ecosystem)
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class InstructionalValueFacts:
    """Pillar 2 fact drawer.  Holds the four dimension drawers."""
    product_complexity: ProductComplexityFacts = field(default_factory=ProductComplexityFacts)
    mastery_stakes: MasteryStakesFacts = field(default_factory=MasteryStakesFacts)
    lab_versatility: LabVersatilityFacts = field(default_factory=LabVersatilityFacts)
    market_demand: MarketDemandFacts = field(default_factory=MarketDemandFacts)


# ─────────────────────────────────────────────────────────────────────────────
# Pillar 3 — Customer Fit fact drawer
#
# Company-level facts.  Lives on CompanyAnalysis, NOT on Product.  Top-level
# shared facts feed multiple dimensions and ACV motions; per-dimension drawers
# hold dimension-specific concrete facts plus qualitative signal dicts.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TrainingCommitmentFacts:
    """Pillar 3.1 — Does this organization have a heart for teaching?"""
    description: str = ""
    has_on_demand_catalog: bool = False
    has_ilt_calendar: bool = False
    customer_enablement_team_name: str = ""
    certification_programs: list[str] = field(default_factory=list)
    training_leadership_titles: list[str] = field(default_factory=list)
    training_catalog_url: str = ""
    audiences_served: list[str] = field(default_factory=list)  # subset of ["employees", "customers", "partners", "end_users"]
    has_compliance_training: bool = False
    uses_hands_on_language: bool = False
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class BuildCapacityFacts:
    """Pillar 3.2 — Can the org create its own labs?

    `lab_build_platforms_in_use` is the strongest verifiable Build
    Capacity signal because it's outward-facing.  Values come from
    `backend/knowledge/competitors.json` — Define-Once.
    """
    description: str = ""
    lab_build_platforms_in_use: list[str] = field(default_factory=list)  # canonical names from competitors.json
    is_already_building_labs: bool = False
    content_team_name: str = ""
    authoring_roles_found: list[str] = field(default_factory=list)
    outsourcing_evidence: list[str] = field(default_factory=list)
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class DeliveryCapacityFacts:
    """Pillar 3.3 — Can the org get labs to learners at scale?

    Three delivery layers, with Layers 2 and 3 captured as separate
    field-sets so they can both be true at the same time (e.g., Cohesity
    in transition from informal partners to a new authorized program).

    Layer 2's open-market half (Pluralsight, Coursera, etc.) lives at the
    PRODUCT level in MarketDemandFacts.independent_training_course_counts;
    Delivery Capacity scoring reads it cross-pillar.
    """
    description: str = ""
    # Layer 1: Vendor has their own training
    has_vendor_delivered_training: bool = False
    vendor_training_modes: list[str] = field(default_factory=list)  # ["ilt", "self_paced", "vendor_labs", "bootcamps"]
    has_published_course_calendar: bool = False
    course_calendar_url: str = ""
    # Layer 2: Third parties deliver training (vendor-connected informal half)
    has_informal_training_partners: bool = False
    named_informal_training_partners: list[str] = field(default_factory=list)
    # Layer 3: Vendor sponsors an authorized program
    authorized_training_program_name: str = ""  # empty string = no formal program
    authorized_training_partners_count: NumericRange = field(default_factory=NumericRange)
    named_authorized_training_partners: list[str] = field(default_factory=list)
    # LMS + cert delivery infrastructure
    lms_platforms_in_use: list[str] = field(default_factory=list)
    cert_delivery_vendors: list[str] = field(default_factory=list)
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class OrganizationalDnaFacts:
    """Pillar 3.4 — Are these guys easy to do business with?

    Reframed per Frank 2026-04-07 — focus on ease-of-engagement signals
    rather than partnership counts.  funding_events and has_recent_layoffs
    moved here from Market Demand because they're about the company, not
    market appetite for the skill.
    """
    description: str = ""
    partnership_types: list[str] = field(default_factory=list)  # ["technology", "channel", "content", "delivery", "integration"]
    named_alliance_leadership: list[str] = field(default_factory=list)
    uses_external_platforms: list[str] = field(default_factory=list)  # Platform Buyer evidence — ["Salesforce", "Workday", "Okta"]
    funding_events: list[str] = field(default_factory=list)  # ["IPO 2024", "Series D $200M"]
    has_recent_layoffs: bool = False
    signals: dict[str, SignalEvidence] = field(default_factory=dict)


@dataclass
class CustomerFitFacts:
    """Pillar 3 fact drawer.  Lives on CompanyAnalysis (NOT on Product).

    Top-level shared facts feed multiple Customer Fit dimensions AND ACV
    motions.  channel_partners_size and channel_partner_se_population are
    Define-Once — channel_partner_se_population feeds ACV Motion 2.
    """
    description: str = ""
    # Top-level shared facts (company-level, feed multiple readers)
    total_employees: NumericRange = field(default_factory=NumericRange)
    channel_partners_size: NumericRange = field(default_factory=NumericRange)
    channel_partner_se_population: NumericRange = field(default_factory=NumericRange)  # → ACV Motion 2
    named_channel_partners: list[str] = field(default_factory=list)
    events_attendance: dict[str, NumericRange] = field(default_factory=dict)  # → ACV Motion 5; e.g. {"Cohesity Connect": NumericRange(5000, 5500)}
    enterprise_reference_customers: list[str] = field(default_factory=list)  # cross-pillar with Pillar 2 Market Demand
    geographic_reach_regions: list[str] = field(default_factory=list)        # cross-pillar with Pillar 2 + Delivery Capacity
    # Per-dimension drawers
    training_commitment: TrainingCommitmentFacts = field(default_factory=TrainingCommitmentFacts)
    build_capacity: BuildCapacityFacts = field(default_factory=BuildCapacityFacts)
    delivery_capacity: DeliveryCapacityFacts = field(default_factory=DeliveryCapacityFacts)
    organizational_dna: OrganizationalDnaFacts = field(default_factory=OrganizationalDnaFacts)


# ═══════════════════════════════════════════════════════════════════════════════
# Product — the center of everything
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Product:
    """A product analyzed for labability.

    The product is the center of the entire platform. Not the customer,
    not the persona — the product.
    """
    name: str
    category: str
    subcategory: str = ""
    description: str = ""
    product_url: str = ""
    deployment_model: str = ""     # "installable" | "hybrid" | "cloud" | "saas-only"
    orchestration_method: str = "" # e.g., "Hyper-V", "Azure Cloud Slice", "Custom API", "Simulation"
    # Frank 2026-04-08 — captured by the researcher when the vendor themselves
    # uses an acronym for this product (e.g., Trellix TIE, Microsoft SCCM,
    # Cisco ISE). The badge selector uses this field to render a concise
    # badge name when the full name exceeds the length limit. NEVER invented;
    # only used when the researcher finds vendor evidence of the acronym.
    vendor_official_acronym: str = ""
    # For wrapper orgs (universities, Industry Authorities, training orgs,
    # GSIs, etc.): the labable technologies taught/certified/deployed inside
    # this offering. Each entry: {"name": str, "deployment_model": str, "note": str}.
    # Drives Pillar 1 scoring and badge evidence. Empty for software companies
    # where the product IS the technology.
    underlying_technologies: list[dict] = field(default_factory=list)

    # ── Wrapper-org audience field ──────────────────────────────────────────
    # For wrapper org types ONLY (Academic, ILT Training Org, Enterprise
    # Learning Platform, GSI, VAR, Tech Distributor, Industry Authority,
    # Content Development): how many learners THIS organization serves
    # in THIS program per year. Distinct from `estimated_user_base`,
    # which is the underlying technology's global market.
    #
    # Used as the Motion 1 audience source via
    # ACV_AUDIENCE_SOURCE_BY_ORG_TYPE in scoring_config.py. Empty / 0
    # for Software and Enterprise Software org types — those use
    # estimated_user_base directly.
    #
    # Per Platform-Foundation → "Wrapper organizations — product vs.
    # audience". Frank 2026-04-13.
    annual_enrollments_estimate: int = 0
    annual_enrollments_evidence: str = ""
    annual_enrollments_confidence: str = ""  # "confirmed" | "indicated" | "inferred"
    user_personas: list[str] = field(default_factory=list)
    lab_highlight: str = ""        # Why this is a great hands-on candidate
    lab_concepts: list[str] = field(default_factory=list)
    poor_match_flags: list[str] = field(default_factory=list)
    recommendation: list[str] = field(default_factory=list)

    # ── Fact drawer (Research → Store layer) ──────────────────────────────
    # New 2026-04-07: structured facts populated by the researcher.  Pillar 1
    # facts are typed primitives (capability-store).  Pillar 2 facts are
    # qualitative SignalEvidence dicts plus concrete numeric facts on Market
    # Demand.  Pillar 3 facts (CustomerFit) live on CompanyAnalysis, not on
    # Product.  See Platform-Foundation.md → "Three Layers of Intelligence."
    product_labability_facts: ProductLababilityFacts = field(default_factory=ProductLababilityFacts)
    instructional_value_facts: InstructionalValueFacts = field(default_factory=InstructionalValueFacts)

    # ── Scoring (Score layer — derived from facts) ─────────────────────────
    # Old interpretive structures stay during the migration.  They're
    # populated by the legacy monolithic scoring call until Step 4/5 of
    # the rebuild shifts scoring to read from the fact drawer above.
    fit_score: FitScore = field(default_factory=FitScore)
    acv_potential: ACVPotential = field(default_factory=ACVPotential)
    verdict: Optional[Verdict] = None

    # ── Pillar 2 rubric grades ────────────────────────────────────────────
    # `rubric_grades` is the output of backend/rubric_grader.py — one
    # GradedSignal list per Pillar 2 dimension (product_complexity,
    # mastery_stakes, lab_versatility, market_demand).  Keyed by the
    # dimension's lowercase_underscore key.  Produced by a focused Claude
    # call per dimension that reads the truth-only fact drawer and emits
    # graded signals with strength + evidence text.  The pure-Python
    # pillar_2_scorer.py reads these records + facts and produces the
    # PillarScore deterministically.  Grades travel with the Product so
    # re-scoring from cached grades is instant and the UI can surface the
    # evidence text per badge.
    rubric_grades: dict[str, list[GradedSignal]] = field(default_factory=dict)

    # Classification review flag — raised when the product category or
    # organization type landed in "Unknown" during scoring.  The math layer
    # applies a neutral fallback baseline and surfaces this flag so the
    # dossier UX can prompt a human to verify the classification.
    classification_review_needed: bool = False

    # People
    owning_org: Optional[OrgUnit] = None
    contacts: list[Contact] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Seller Briefcase — actionable bullets per Pillar
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BriefcaseSection:
    """One section of the Seller Briefcase.

    Generated by a separate AI call after scoring — receives full
    scoring context to produce sharp, pointed seller guidance.
    """
    pillar: str                    # Which Pillar this section is under
    heading: str                   # "Key Technical Questions" | "Conversation Starters" | "Account Intelligence"
    bullets: list[str] = field(default_factory=list)


@dataclass
class SellerBriefcase:
    """Three sections below the Pillar cards — arms the seller for conversations."""
    key_technical_questions: BriefcaseSection = field(default_factory=lambda: BriefcaseSection(
        pillar="Product Labability",
        heading="Key Technical Questions",
    ))
    conversation_starters: BriefcaseSection = field(default_factory=lambda: BriefcaseSection(
        pillar="Instructional Value",
        heading="Conversation Starters",
    ))
    account_intelligence: BriefcaseSection = field(default_factory=lambda: BriefcaseSection(
        pillar="Customer Fit",
        heading="Account Intelligence",
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# Company Analysis — the full analysis record
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CompanyAnalysis:
    """A complete company analysis — products, scores, briefcase.

    This is COMPANY INTELLIGENCE (internal-only domain).
    Customers never see this. Designer never accesses this.
    """
    company_name: str
    company_url: Optional[str] = None
    company_description: str = ""
    organization_type: str = "software_company"
    products: list[Product] = field(default_factory=list)
    # Pillar 3 fact drawer — company-level facts shared across all products
    # of this company.  Per Three Layers of Intelligence: Customer Fit is
    # measured at the COMPANY level, not the product level.  Every product
    # of the same company reads from this single drawer.  See
    # Platform-Foundation.md → "Three Layers of Intelligence."
    customer_fit_facts: CustomerFitFacts = field(default_factory=CustomerFitFacts)

    # ── Pillar 3 rubric grades ────────────────────────────────────────────
    # Produced by backend/rubric_grader.py — one GradedSignal list per
    # Pillar 3 dimension (training_commitment, build_capacity,
    # delivery_capacity, organizational_dna).  Keyed by the dimension's
    # lowercase_underscore key.  Customer Fit is per-company, so these
    # grades live on the CompanyAnalysis, not on individual Products.
    # pillar_3_scorer.py reads these records + customer_fit_facts and
    # produces the Pillar 3 PillarScore deterministically.
    customer_fit_rubric_grades: dict[str, list[GradedSignal]] = field(default_factory=dict)

    briefcase: Optional[SellerBriefcase] = None
    # CRIT-6 in code-review-2026-04-07: analyzed_at MUST NOT be set at
    # dataclass instantiation. Setting it via default_factory means the
    # timestamp reflects when the Python object was created (deep inside
    # the parser), NOT when the analysis was actually finalized and saved.
    # In cache-and-append flows, the existing timestamp would survive
    # untouched even when new products were added. The intelligence layer
    # (intelligence.score / discover) is responsible for stamping this
    # field at the right boundary, and save_analysis updates it on every
    # write so the persisted timestamp always reflects when the file was
    # actually written.
    analyzed_at: str = ""
    analysis_id: str = ""
    discovery_id: str = ""
    total_products_discovered: int = 0

    @property
    def top_products(self) -> list[Product]:
        """Products sorted by Fit Score, highest first."""
        return sorted(self.products, key=lambda p: p.fit_score.total, reverse=True)

    @property
    def fit_score(self) -> int:
        """Company Fit Score = top product's Fit Score."""
        if not self.products:
            return 0
        return self.top_products[0].fit_score.total


# ═══════════════════════════════════════════════════════════════════════════════
# Prospector Row — summary for batch scoring
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProspectorRow:
    """Summary row for the Prospector results table.

    This is COMPANY INTELLIGENCE (internal-only domain).
    """
    company_name: str
    company_url: str = ""
    top_product: str = ""
    fit_score: int = 0
    orchestration_method: str = ""
    verdict: str = ""
    top_contact_name: str = ""
    top_contact_title: str = ""
    top_contact_linkedin: str = ""
    second_contact_name: str = ""
    second_contact_title: str = ""
    second_contact_linkedin: str = ""
    analysis_id: str = ""
    hubspot_icp_context: str = ""  # 1-2 sentence synthesis (GP5 — regenerated every time)
