"""Skillable Intelligence Platform — Scoring Configuration.

SINGLE SOURCE OF TRUTH for the entire scoring model.

Every pillar name, dimension name, weight, badge definition, scoring signal,
penalty, threshold, verdict label, canonical list, and vocabulary term is
defined HERE and referenced everywhere else — code, AI prompts, UX templates,
documentation generation.  Nothing is hard-coded elsewhere.  If a name or
weight changes, it changes in this one file and propagates through the
entire system.

Implements the Define-Once Principle (Platform-Foundation.md) and
Self-Evident Design (GP4).

Canonical source documents:
  - docs/Platform-Foundation.md  (strategic authority)
  - docs/Badging-and-Scoring-Reference.md  (operational detail)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class BadgeColor:
    """Criteria for a single badge color assignment.

    Each badge can have up to four color criteria — green, gray, amber, red.
    The AI uses these descriptions to decide which color to assign based on
    the evidence it finds.
    """
    color: str           # "green", "gray", "amber", "red"
    criterion: str       # Plain-English description of when this color applies


@dataclass(frozen=True)
class Badge:
    """A single badge definition.

    Badges are the visual layer of requirements — the most granular scoring
    unit.  Each badge has a name, belongs to a dimension, and has color
    criteria that the AI evaluates during scoring.
    """
    name: str
    colors: tuple[BadgeColor, ...]
    qualifier_labels: tuple[str, ...] = ()  # e.g. ("Strength", "Risk", "Blocker")
    notes: str = ""


@dataclass(frozen=True)
class ScoringSignal:
    """A discrete signal that contributes points to a dimension score.

    Signals are what the AI looks for during research.  Each has a point
    value and a description of what constitutes that signal.
    """
    name: str
    points: int
    description: str


@dataclass(frozen=True)
class Penalty:
    """A deduction applied to a dimension score when a constraint is found.

    Penalties reduce the score to honestly reflect limitations.  They stack
    freely — a product with multiple constraints reflects the cumulative
    impact.
    """
    name: str
    deduction: int       # Negative value (e.g., -5)
    flag: str            # poor_match_flags key (e.g., "gpu_required")
    description: str


@dataclass(frozen=True)
class RubricTier:
    """One strength tier within a dimension's rubric.

    Used by Pillar 2 (Instructional Value) and Pillar 3 (Customer Fit) where
    badge names are variable and AI-synthesized rather than canonical. The AI
    grades each badge it emits against the dimension's rubric and tags it
    with a strength level (`strong` / `moderate` / `weak`). The math layer
    credits points based on (dimension, strength) lookup.

    Pillar 1 does NOT use rubrics — its canonical badge names map directly
    to scoring signals via name match.
    """
    strength: str        # "strong", "moderate", "weak"
    points: int          # Points credited per badge at this strength tier
    criterion: str       # Plain-English description of what qualifies for this tier


@dataclass(frozen=True)
class Rubric:
    """A complete rubric for one dimension.

    Bundles the strength tiers, the IS/IS NOT routing boundaries, and the
    fixed list of signal categories the AI must pick from when emitting a
    badge in this dimension. The signal_categories list is the hidden
    canonical hedge — it preserves cross-product comparability and
    auditability without forcing canonical visible names.
    """
    tiers: tuple[RubricTier, ...]
    is_about: tuple[str, ...]            # What the dimension IS about (positive boundary)
    is_not_about: tuple[str, ...]        # What the dimension is NOT about (negative boundary — explicit routing rules)
    signal_categories: tuple[str, ...]   # Fixed list of category tags the AI must pick from per badge


@dataclass(frozen=True)
class Dimension:
    """A scored area within a Pillar.

    Each Pillar has four Dimensions.  Dimensions are weighted within their
    Pillar (weights sum to 100 within each Pillar) and contain either:
      - badges + scoring_signals + penalties (Pillar 1 — canonical model)
      - badges + a rubric (Pillars 2 and 3 — rubric model with variable badge names)

    The two architectures are intentional: Pillar 1 measures concrete
    technical facts where canonical names work cleanly; Pillars 2 and 3
    measure interpretive subject-matter and organizational fit where the
    domain-specific terminology that makes badges useful varies per product.
    See `Badging-and-Scoring-Reference.md` for the rationale.
    """
    name: str
    weight: int
    question: str
    badges: tuple[Badge, ...] = ()
    scoring_signals: tuple[ScoringSignal, ...] = ()
    penalties: tuple[Penalty, ...] = ()
    rubric: Optional[Rubric] = None     # Rubric model (Pillars 2 and 3) — None for Pillar 1
    cap: Optional[int] = None
    floor: Optional[int] = None
    notes: str = ""


@dataclass(frozen=True)
class Pillar:
    """A top-level scoring component.

    Three Pillars compose the Fit Score.  Each scores out of 100 internally,
    then gets weighted.  A score of 85/100 on a 50% Pillar contributes
    85 x 0.50 = 42.5 points to the Fit Score.
    """
    name: str
    weight: int          # Percentage of Fit Score (e.g., 40)
    level: str           # "product" or "organization"
    question: str
    dimensions: tuple[Dimension, ...]


@dataclass(frozen=True)
class VerdictDefinition:
    """A single verdict in the verdict grid.

    The verdict combines Fit Score range and ACV tier into an action-oriented
    label that tells the seller what to do — without predicting customer
    behavior or dictating effort.
    """
    label: str
    description: str
    color: str


@dataclass(frozen=True)
class ConsumptionMotion:
    """A consumption motion that feeds the ACV calculation.

    Each motion represents a distinct way labs reach learners.  Per the
    Platform-Foundation ACV model: the only source of range in the final
    number is AUDIENCE — adoption_pct and hours are single locked values.
    The population is read from the fact drawer at ACV-population time
    via the named source field.

    Fields:
      label              — the motion's display name (locked vocabulary)
      adoption_pct       — single adoption rate, used directly (no range)
      hours_low/high     — single values in the typical case; kept as a
                           range only because a few motions have a narrow
                           hours spread (e.g., events 1-2hr per session).
                           When locked as a single value, set low == high.
      population_source  — the fact-drawer field the ACV builder reads
                           for this motion's audience. Two forms:
                             "product:<field>" — read from
                               product.instructional_value_facts.market_demand.<field>
                             "company:<field>" — read from
                               company_analysis.customer_fit_facts.<field>
                             "company:events_attendance_sum" — special
                               case: sum all events_attendance values
      description        — guidance sentence for the hero tooltip and the
                           ACV by Use Case widget row label
    """
    label: str
    adoption_pct: float
    hours_low: float
    hours_high: float
    population_source: str
    description: str


@dataclass(frozen=True)
class LabType:
    """A high-value lab type from the Lab Versatility menu.

    These are special lab types beyond standard step-by-step labs.  The AI
    picks 1-2 per product based on specific product research.  They serve
    dual purpose: conversational competence in Inspector, program
    recommendations in Designer.
    """
    name: str
    description: str
    likely_product_types: str


@dataclass(frozen=True)
class CategoryPrior:
    """A product category with its default demand rating.

    Category priors set the floor for Market Demand scoring.  The AI looks
    at company-specific signals first, product signals second, and falls
    back to the category prior.
    """
    category: str
    points: int
    demand_level: str    # "high", "moderate", "low"


@dataclass(frozen=True)
class RateTier:
    """A delivery path rate for ACV calculation.

    The rate depends on the delivery path determined by Product Labability.
    Platform rate only — cloud consumption is billed separately.
    """
    delivery_path: str
    rate_low: float
    rate_high: float
    notes: str = ""


@dataclass(frozen=True)
class TechnicalFitMultiplier:
    """A multiplier applied after scoring Product Labability.

    Adjusts the weight of downstream pillars based on how strong the
    technical foundation is.  Strong technical fit = full weight.
    Weak technical fit = reduced weight on everything else.
    """
    score_min: int
    score_max: int
    method: str          # "any", "datacenter", "non-datacenter"
    multiplier: float


@dataclass(frozen=True)
class ConfidenceLevel:
    """An evidence confidence level.

    Confidence coding is core logic — every finding carries a confidence
    level as a stored field.  It influences badge color, surfaces in
    evidence language, and is available to all downstream consumers.
    """
    level: str
    meaning: str
    example_phrasing: str


@dataclass(frozen=True)
class LockedTerm:
    """A vocabulary term with its canonical form and prohibited alternatives.

    Locked vocabulary ensures consistency across code, prompts, UX, and
    documentation.  The 'use_this' form is the only acceptable term.
    """
    use_this: str
    not_this: tuple[str, ...]


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 1 — PRODUCT LABABILITY (50%)
#
# The gatekeeper.  If this fails, nothing else matters.  Measures whether
# Skillable can deliver a complete lab lifecycle for this product.  70% of
# the Fit Score is about the product — and this Pillar is the foundation.
# ═══════════════════════════════════════════════════════════════════════════════

_provisioning_badges = (
    Badge("Runs in VM", (
        BadgeColor("green", "Clean VM install confirmed"),
        BadgeColor("amber", "Installs with complexity"),
    ), notes="Frank 2026-04-08 — renamed from 'Runs in Hyper-V' to fabric-neutral 'Runs in VM'. Skillable's VM fabric is Hyper-V under the hood but the badge names the product's shape, not the implementation detail."),
    Badge("Runs in Azure", (
        BadgeColor("green", "Azure-native service — viable for Azure Cloud Slice fabric"),
        BadgeColor("amber", "Azure path with friction"),
    ), notes="Means the product IS an Azure service viable for Cloud Slice fabric — NOT 'can be hosted on an Azure VM.' For installable products that happen to run on Azure VMs, use Runs in VM."),
    Badge("Runs in AWS", (
        BadgeColor("green", "AWS-native service — viable for AWS Cloud Slice fabric"),
        BadgeColor("amber", "AWS path with friction"),
    ), notes="Means the product IS an AWS service viable for Cloud Slice fabric — NOT 'can be hosted on an AWS VM.'"),
    Badge("Runs in Container", (
        BadgeColor("green", "Container-native confirmed, no disqualifiers"),
        BadgeColor("amber", "Image exists but disqualifiers apply or research uncertain"),
    ), notes="Singular. Defaults to green when container-native confirmed. Don't emit if definitively not container-viable. Scores ~equivalent to Runs in VM Standard."),
    Badge("ESX Required", (
        BadgeColor("amber", "Nested virtualization or socket licensing requires ESX (details in evidence)"),
    )),
    Badge("Simulation", (
        BadgeColor("gray", "Simulation is the chosen path — viable when real provisioning is impractical"),
    ), notes="Gray Context (not amber Risk) when Simulation is correctly chosen as the path. Carries base credit (+7 to +14 per the framework). Simulation is a real fabric, not a fallback."),
    Badge("Sandbox API", (
        BadgeColor("green", "Vendor has rich provisioning / sandbox / management API for per-learner environments"),
        BadgeColor("amber", "API exists but coverage uncertain or partial"),
        BadgeColor("red", "No provisioning API confirmed — no path to per-learner environments via vendor API"),
    ), notes="Gatekeeper canonical for the 'can we provision per learner via the vendor's API?' question. Replaces the older Custom API (BYOC) signal name. Always emit (gatekeeper) — green/amber/red based on evidence."),
    Badge("Pre-Instancing?", (
        BadgeColor("green", "Slow first-launch or cluster init mitigated by Skillable Pre-Instancing — Skillable feature opportunity"),
    ), notes="Frank 2026-04-08 — trailing question mark signals this is a Skillable feature SUGGESTION to explore, not a confirmed product property. Fires when product has long initial provisioning time and/or is_large_lab. Frames the slowness as a Skillable feature win (Pre-Instancing pre-builds warm instances), not friction."),
    Badge("Multi-VM Lab", (
        BadgeColor("green", "Multiple VMs working together — Skillable strength (competitors struggle here)"),
    ), notes="Skillable competitive advantage. Typical for cybersecurity (attacker + target + SIEM), data engineering pipelines, enterprise stacks. Drives ACV rate tier upward."),
    Badge("Complex Topology", (
        BadgeColor("green", "Real network complexity — routers, switches, firewalls, segmentation, routing protocols"),
    ), notes="Skillable strength. Applies to networking vendors (Cisco, Juniper, Palo Alto, F5) AND cybersecurity products with real network-layer complexity. Can pair with Multi-VM Lab."),
    Badge("GPU Required", (
        BadgeColor("amber", "Product requires GPU — forces cloud VM with GPU instance, slower launch and higher cost"),
    ), notes="Genuine friction. Standard Hyper-V doesn't have GPU; routes to Azure/AWS with GPU instance via Compute Gallery. Was a hidden penalty; promoted to a visible badge so SEs see the warning."),
    Badge("Bare Metal Required", (
        BadgeColor("red", "Physical hardware required — no virtualization path"),
    )),
    Badge("No Deployment Method", (
        BadgeColor("red", "Cannot be provisioned or simulated in any software environment"),
    ), notes="Ultimate dead-end blocker. Only fires when no real provisioning path AND Simulation is also blocked. Diligent-style products where Simulation is viable do NOT get this badge — they get Sandbox API red + Simulation gray."),
    # Frank 2026-04-08 additions:
    Badge("M365 Tenant", (
        BadgeColor("green", "Microsoft 365 End User scenario — Skillable's automated tenant provisioning applies. Low-friction learner experience: no credit card, no MFA, Skillable-owned tenant with the right M365 tier (Base/Full/Full+AI)."),
    ), notes="Frank 2026-04-08 — M365 as a first-class Provisioning fabric peer to VM/Azure/AWS/Container. Fires when m365_scenario == 'end_user'. See scoring_config.SKILLABLE_CAPABILITIES → m365_tenants → scenarios → end_user for the capability detail."),
    Badge("M365 Admin", (
        BadgeColor("amber", "Microsoft 365 Administration scenario — requires Global Admin tenant. Path is either MOC-provided tenant (Learning Partners only) or learner-signed-up M365 Trial account (may require credit card / MFA identity verification by Microsoft)."),
    ), notes="Frank 2026-04-08 — M365 Administration fires amber because tenant path has identity verification friction. Evidence text should explain the MOC vs trial distinction. See scoring_config.SKILLABLE_CAPABILITIES → m365_tenants → scenarios → administration."),
    Badge("Custom Cloud", (
        BadgeColor("gray", "Skillable's Custom Cloud Labs (BYOC) pattern orchestrates this product's vendor API through Lifecycle Actions + Automated Activities + Custom Start Page. Named operational pattern for SaaS/cloud products with per-learner provisioning APIs."),
    ), notes="Frank 2026-04-08 — Skillable-strength context badge that fires alongside Sandbox API (when Sandbox API is green or amber). Zero scoring points (strength context only, credit lives on Sandbox API itself). Multi-badge pattern: Sandbox API names the vendor finding, Custom Cloud names the Skillable operational capability. See scoring_config.SKILLABLE_CAPABILITIES → byoc_custom_cloud_labs."),
    Badge("No GCP Path", (
        BadgeColor("amber", "Product runs on GCP AND has another viable fabric — GCP is a limitation but we can route around it via the alternative path. SE validates the alternative path."),
        BadgeColor("red", "GCP is required or preferred by the vendor AND no native Skillable GCP path exists — either the product is GCP-only, or the vendor's preferred deployment is GCP and going against their grain means real friction."),
    ), notes="Frank 2026-04-08 — replaces the old 'Requires GCP' amber-only badge with a finding-oriented name. Multi-badge pattern for GCP-preferred products: No GCP Path red + the workaround fabric fires at amber (instead of its normal green) to signal it's a workaround, not the happy path."),
)

_provisioning_signals = (
    # FLAT-TIER scoring per the architecture sharpening:
    # The historical Hyper-V/ESX/Cloud Slice/Custom API tier modifiers
    # (Standard / Moderate / Weak) have been retired. Each canonical badge
    # earns its full base credit when emitted green, and friction is
    # expressed via SEPARATE friction badges (GPU Required, Multi-VM Lab as
    # a strength, ESX Required with evidence, etc.). The math layer sums
    # the green credit + the friction adjustments — no hidden tier modifier.
    #
    # Each scoring signal name below MATCHES the canonical badge name above
    # so the math layer credits the canonical badge directly. No more
    # "emit two badges to get the points" hack.
    ScoringSignal("Runs in VM", 30, "Clean VM install — full base credit"),
    ScoringSignal("Runs in Azure", 30, "Azure-native service via Cloud Slice fabric"),
    ScoringSignal("Runs in AWS", 30, "AWS-native service via Cloud Slice fabric"),
    ScoringSignal("Runs in Container", 30, "Container-native confirmed — equivalent to Runs in VM Standard"),
    ScoringSignal("ESX Required", 26, "ESX path — 4 points below Runs in VM due to operational cost (Broadcom licensing)"),
    ScoringSignal("Sandbox API", 22, "Vendor provisioning API (BYOC) — viable per-learner provisioning, scored below native fabrics"),
    # Frank 2026-04-08: Simulation is now a HARD OVERRIDE case — when the
    # scorer picks Simulation as the fabric, it applies SIMULATION_PROVISIONING_POINTS
    # directly rather than walking signals. This row stays for backward compat
    # but the scorer doesn't read it for Simulation-chosen products anymore.
    ScoringSignal("Simulation", 5, "Simulation as the chosen path — low base credit (Frank 2026-04-08 override, reduced from 12)"),
    # Frank 2026-04-08: M365 as first-class Provisioning fabric peer.
    ScoringSignal("M365 Tenant", 25, "Microsoft 365 End User scenario — Skillable's automated tenant provisioning (Base/Full/Full+AI). Low-friction learner path."),
    ScoringSignal("M365 Admin", 18, "Microsoft 365 Administration scenario — trial tenant or MOC-provided tenant path; identity verification friction."),
    # Strength badges (do not score in Provisioning directly — they drive
    # the ACV rate tier upward and add seller-relevant context)
    ScoringSignal("Multi-VM Lab", 0, "Skillable competitive strength — drives ACV rate tier"),
    ScoringSignal("Complex Topology", 0, "Skillable competitive strength — drives ACV rate tier"),
    ScoringSignal("Pre-Instancing?", 0, "Skillable feature suggestion — mitigates slow init or large-footprint cold starts"),
    # Frank 2026-04-08: BYOC / Custom Cloud Labs Skillable-strength context badge.
    # Fires alongside Sandbox API when Sandbox API is green or amber. Zero points —
    # credit lives on Sandbox API itself; Custom Cloud is display/context only.
    ScoringSignal("Custom Cloud", 0, "Skillable's Custom Cloud Labs (BYOC) pattern — context/strength badge, credit lives on Sandbox API"),
)

_provisioning_penalties = (
    # GPU Required is now also a visible amber badge above (GPU Required)
    # — the penalty stays for backward compatibility with cached data and
    # for the math contribution. The badge is the visible warning to the SE.
    Penalty("GPU Required", -5, "gpu_required",
            "Forces Azure/AWS VM via Compute Gallery; significantly slower launch and higher cost"),
    # GUI-only setup penalty RETIRED per Frank (2026-04-06): once the image
    # is built, the learner doesn't experience the GUI install. Not friction
    # worth surfacing.
    # Provisioning time over 30 min penalty RETIRED — replaced by the
    # Pre-Instancing green opportunity badge that frames slow init as a
    # Skillable feature win, not friction.
    # No NFR / dev license penalty RETIRED — moves to Lab Access via the
    # Training License canonical badge.
    Penalty("Socket licensing (ESX) >24 vCPUs", -2, "socket_licensing_high",
            "VMs split across 2 sockets above 24 vCPUs — surfaces as evidence on the ESX Required badge"),
)

_provisioning_dimension = Dimension(
    name="Provisioning",
    weight=35,
    question="How do we get this product into Skillable?",
    badges=_provisioning_badges,
    scoring_signals=_provisioning_signals,
    penalties=_provisioning_penalties,
    notes="Provisioning determines difficulty for everything else. When a product runs in "
          "Skillable's infrastructure (VM, container, Cloud Slice), the other dimensions are "
          "largely within Skillable's control. When a product runs in the vendor's own cloud, "
          "every dimension depends on the vendor's APIs and policies.",
)


_lab_access_badges = (
    # NEW canonicals from the architecture sharpening (2026-04-06+):
    Badge("Identity API", (
        BadgeColor("green", "Vendor API can create users and assign roles per learner"),
        BadgeColor("amber", "API exists but coverage uncertain or partial"),
    ), notes="The user/identity/role-management piece of a Management API. When Entra ID SSO is supported on an Azure-native product, that preempts Identity API (native fabric integration beats manual API wiring)."),
    Badge("Cred Recycling", (
        BadgeColor("green", "Customer credentials can be reset and recycled between learners — low operational overhead"),
        BadgeColor("amber", "Recycling exists but coverage uncertain"),
    ), notes="Distinct from Credential Pool. Credential Pool = batch of consumable credentials that need replenishment. Cred Recycling = credentials that can be reset and reused. Scores between Entra ID SSO and Credential Pool."),
    Badge("Training License", (
        BadgeColor("green", "NFR / training / eval / dev license path confirmed, low friction"),
        BadgeColor("amber", "License exists with friction — sales call, cost, short trial, enterprise-only"),
        BadgeColor("red", "License is effectively blocked — credit card required + high cost + no negotiation path"),
    ), notes="CONSOLIDATED canonical. Replaces the historical NFR Accounts, Trial Account, Credit Card Required, High License Cost badges/penalties. One canonical, three states, one source of truth for the 'can learners get into the product without prohibitive licensing friction?' question."),
    Badge("Learner Isolation", (
        BadgeColor("green", "Per-user / per-tenant isolation confirmed via API evidence"),
        BadgeColor("amber", "Research can't confirm either way"),
        BadgeColor("red", "Explicitly absent — confirmed shared multi-tenant with no isolation mechanism"),
    ), notes="Gatekeeper canonical — always emit (green/amber/red), never 'don't emit.' Determined from API evidence about per-user provisioning capability, NOT a proxy for SaaS-only deployment. Replaces the synthetic 'No Learner Isolation' injection."),
    # EXISTING canonicals — kept (Frank confirmed each one is distinct):
    Badge("Full Lifecycle API", (
        BadgeColor("green", "Full lifecycle API for user provisioning and management"),
    ), notes="Historical umbrella canonical. The Management API decomposition pattern means a comprehensive vendor API surfaces as four dimension-specific badges (Sandbox API in Provisioning, Identity API + Cred Recycling here in Lab Access, Scoring API in Scoring, Teardown API in Teardown). Full Lifecycle API stays as a single-badge shorthand for the rare case where a vendor truly has it all."),
    Badge("Entra ID SSO", (
        BadgeColor("green", "App pre-configured to use Entra ID tenant — zero credential management"),
    ), notes="Scope is AZURE-NATIVE APPLICATIONS ONLY. Not a generic SSO badge. For non-Azure products with SAML/OAuth, use Identity API or Manual SSO as appropriate."),
    Badge("Credential Pool", (
        BadgeColor("green", "Pre-provisioned pool of credentials, distributed to learners (not recycled)"),
    ), notes="Distinct from Cred Recycling. This is the consumable-pool model: customer hands over a batch of licenses, we distribute them to learners, when we run low we have to ask for more. Operationally painful but works."),
    Badge("Manual SSO", (
        BadgeColor("amber", "Azure SSO but requires manual learner login steps"),
    ), notes="Distinct from Identity API. Manual SSO means SSO works but the learner has to type credentials. Identity API means we can provision per-learner identities programmatically."),
    Badge("MFA Required", (
        BadgeColor("red", "Multi-factor authentication blocks automated provisioning"),
    ), notes="Visible warning badge for SEs. Big penalty. Promoted to its own badge (already was) so the warning is unmissable."),
    Badge("Anti-Automation Controls", (
        BadgeColor("red", "Platform actively blocks automated account creation"),
    ), notes="Distinct from Learner Isolation. Anti-Automation = active blocking (CAPTCHA, bot detection, enforced rate limits). Learner Isolation = whether per-user provisioning is even possible."),
    Badge("Rate Limits", (
        BadgeColor("red", "API rate limits constrain concurrent learner provisioning"),
    ), notes="Stays as its own visible badge — SE warning signal."),
)

_lab_access_signals = (
    ScoringSignal("Full Lifecycle API", 23, "Complete API for user provisioning and management (+21 to +25) — historical umbrella, see Identity API + Cred Recycling for the decomposed badges"),
    ScoringSignal("Entra ID SSO", 20, "App uses Entra ID tenant for automatic authentication — Azure-native applications only (+18 to +22)"),
    ScoringSignal("Identity API", 19, "Vendor API can create users and assign roles per learner — slightly below Entra ID SSO because it requires manual API wiring vs native fabric integration"),
    ScoringSignal("Cred Recycling", 18, "Credentials reset and recycled between learners — low operational overhead (between Entra ID SSO and Credential Pool)"),
    ScoringSignal("Credential Pool", 16, "Pre-provisioned consumable credential pool — operationally painful but works (+14 to +18)"),
    ScoringSignal("Training License", 16, "NFR / training / eval / dev license path confirmed — green state of the consolidated badge (+14 to +18)"),
    ScoringSignal("Manual SSO", 12, "SSO available but manual login steps required (+10 to +14)"),
)

_lab_access_penalties = (
    Penalty("MFA Required", -15, "mfa_required",
            "Blocks automated provisioning and scoring; severe friction for lab delivery"),
    Penalty("Anti-Automation Controls", -5, "anti_automation",
            "Platform actively blocks automated account creation"),
    Penalty("Rate Limits", -5, "rate_limits",
            "API rate limits constrain concurrent learner provisioning"),
    # Credit Card Required, Tenant Provisioning Lag, High License Cost
    # penalties removed — folded into Training License (red state) and
    # Sandbox API (amber state) as evidence on the consolidated canonical
    # badges. The visible badges carry both the user warning and the math.
)

_lab_access_dimension = Dimension(
    name="Lab Access",
    weight=25,
    question="Can we get people in with their own identity, reliably, at scale?",
    badges=_lab_access_badges,
    scoring_signals=_lab_access_signals,
    penalties=_lab_access_penalties,
    floor=0,
)


_scoring_badges = (
    Badge("Scoring API", (
        BadgeColor("green", "Vendor REST API for validating learner work programmatically — rich state validation"),
        BadgeColor("amber", "API exists but coverage uncertain or partial"),
    ), notes="Canonical name (replaces 'API Scorable (rich)' / 'API Scorable (partial)' which were dimension-confusing). When emitted, the product-specific REST API details (Diligent's developer.diligent.com, Cohesity's REST API v2, etc.) live in evidence on hover, NEVER in the badge name."),
    Badge("Script Scoring", (
        BadgeColor("green", "PowerShell/CLI/Bash scripts can validate config state comprehensively"),
        BadgeColor("amber", "Some scriptable surface but gaps in coverage"),
    ), notes="Frank: don't flatten this one. Two states (green/amber) reflecting whether the product has rich scripting surface or limited."),
    Badge("AI Vision", (
        BadgeColor("green", "GUI-driven product where state is visually evident — AI Vision is the right tool"),
        BadgeColor("amber", "AI Vision usable but visual state ambiguous"),
    ), notes="Renamed from 'AI Vision Scorable' (drop 'Scorable' suffix — already in Scoring dimension, no need to repeat). AI Vision is a PEER scoring method, not a fallback. Green when it's the right tool for a GUI-heavy product. Retire 'fallback' language everywhere."),
    Badge("Simulation Scorable", (
        BadgeColor("amber", "Simulation environment supports scoring via guided interaction"),
    ), notes="SE clarification pending: when can/can't we score within a simulation? Should this ever be red? Frank flagged for SE input."),
    Badge("MCQ Scoring", (
        BadgeColor("amber", "No programmatic surface — knowledge-check questions only"),
    ), notes="The genuine fallback. Used when no environment state is available to validate (knowledge-only assessment)."),
    Badge("No Scoring Methods", (
        BadgeColor("red", "No viable scoring method found — no Scoring API, no Script Scoring, no AI Vision, no Simulation scoring. The product cannot be scored."),
    ), notes="Frank 2026-04-08 Trellix Intelligence as a Service: when every scoring fact is null/False, the Scoring dimension scores 0 and previously rendered with zero badges — a blank dimension that looked broken. This canonical red blocker fires from badge_selector when all four scoring paths are unviable so the user sees WHY the dimension is zero. Parallel to 'No Deployment Method' in Provisioning and 'Manual Teardown' in Teardown — every Pillar 1 dimension has a canonical absence-finding badge."),
)

_scoring_signals = (
    # Recalibrated 2026-04-07 per Frank's "Scoring is about OPTIONS" rule.
    # The Scoring dimension uses a SPECIAL CAP rule on top of these point
    # values — see _SCORING_BREADTH_CAP in pillar_1_scorer.py. Numbers below
    # are the standalone values (single method only); the breadth rule
    # caps full marks at 15 only when AI Vision is paired with Script
    # Scoring (VM context) OR Scoring API (cloud context).
    #
    #   MCQ Scoring     → 0 pts. Anyone can do MCQs. It's not lab work.
    #                     Display as gray Context so the seller sees the
    #                     fallback option, but earns nothing.
    #   AI Vision alone → 10 pts. Real differentiator (Skillable's AI
    #                     vision is rare in the lab platform space and
    #                     has only existed for ~1 year), but not enough
    #                     for high-stakes scoring like a certification
    #                     exam. Caps at 10 standalone.
    #   Scoring API alone → 12 pts. Real programmatic surface, but a
    #                     sparse API caps at less than 12; the standalone
    #                     ceiling is 12 (rich suite). Cloud products
    #                     need API since there's no shell access.
    #   Script Scoring alone → 15 pts. VM context where you have shell
    #                     access — you can write whatever Bash/PS script
    #                     you need. No artificial cap.
    #   Grand Slam      → 15 pts. AI Vision + (Script for VM OR API for
    #                     cloud). The breadth rule below enforces that
    #                     full marks require AI Vision PLUS one of the
    #                     two programmatic methods, except in the
    #                     Script-alone case where 15 is reachable on
    #                     its own.
    ScoringSignal("Scoring API", 12, "Vendor REST API for state validation — caps standalone at 12 (rich suite); needs AI Vision pairing for full marks"),
    ScoringSignal("Script Scoring", 15, "Bash/PowerShell scripts for state validation — VM context, full standalone capability"),
    ScoringSignal("AI Vision", 10, "Skillable's AI observes the GUI to validate state — strong differentiator, caps standalone at 10"),
    ScoringSignal("Simulation Scorable", 8, "Simulation scoring via guided interaction"),
    ScoringSignal("MCQ Scoring", 0, "Knowledge-check questions — display only, zero credit (Frank 2026-04-07: anyone can do MCQs, not lab work)"),
    ScoringSignal("No Scoring Methods", 0, "No viable scoring method — display-only red blocker emitted by badge_selector when all four paths are unviable. Zero points; the dimension already scores 0 on the math side by virtue of having no credited signals."),
)

_scoring_dimension = Dimension(
    name="Scoring",
    weight=15,
    question="Can we assess what they did, and how granularly?",
    badges=_scoring_badges,
    scoring_signals=_scoring_signals,
    notes="Scoring always has a fallback (AI Vision, MCQ). The score reflects the quality of the method.",
)


_teardown_badges = (
    # NEW canonicals from the architecture sharpening:
    Badge("Datacenter", (
        BadgeColor("green", "Skillable hosts a real environment (Hyper-V, ESX, OR Container) — teardown is automatic via snapshot revert or container destroy. Does NOT apply to Simulation (use Simulation Reset instead)."),
    ), notes="Renamed from 'Automatic (VM/Container)'. Cleaner name. As of 2026-04-07 (Diligent review), explicitly EXCLUDES Simulation — a Simulation lab for a SaaS web app doesn't have anything to 'tear down' in the operational sense, so earning the full Datacenter credit was misleading. Simulation paths now use the new Simulation Reset badge instead, which is gray Context for 0 points."),
    Badge("Simulation Reset", (
        BadgeColor("gray", "Simulation environment ends when the session ends — no teardown work, no operational cost. Earns ZERO Teardown points (per Frank 2026-04-07)."),
    ), notes="NEW 2026-04-07 (Diligent review). For Simulation-only paths. Replaces the historical mistake of letting Datacenter green fire for Simulation. Frank's call: Simulation labs don't really have a teardown story (the simulation IS the lab; ending the session ends everything), so this badge is display-only with zero credit. Kept as a visible badge so the seller sees Teardown was considered."),
    Badge("Teardown API", (
        BadgeColor("green", "Vendor API covers environment cleanup and deprovisioning"),
        BadgeColor("amber", "Some teardown API coverage but gaps remain"),
    ), notes="CONSOLIDATED. Replaces 'Teardown APIs (full)' + 'Teardown APIs (partial)' — one canonical, two color states. Per the meta-principle (one badge, color carries the nuance)."),
    Badge("Manual Teardown", (
        BadgeColor("red", "No teardown mechanism — manual cleanup required between learners"),
    ), notes="NEW red blocker badge. Replaces the hidden 'No Teardown API' penalty so SEs see the warning. When this fires, the seller knows teardown is going to be a real build task."),
    Badge("Low Orphan Risk", (
        BadgeColor("green", "Rich teardown API with minor gaps — low risk of orphaned resources"),
    ), notes="Frank 2026-04-13: green tier for products with comprehensive cleanup APIs. Context badge — the seller sees cleanup is covered."),
    Badge("Orphan Risk", (
        BadgeColor("amber", "Partial teardown API — gaps remain that may leave orphaned resources or accounts"),
    ), notes="Frank 2026-04-13: amber tier for products with teardown API coverage but known gaps. SE should verify cleanup completeness."),
    Badge("High Orphan Risk", (
        BadgeColor("red", "No teardown API or major cleanup gaps — significant orphan risk across services"),
    ), notes="Frank 2026-04-13: red tier for products with no documented cleanup path for significant services."),
)

_teardown_signals = (
    ScoringSignal("Datacenter", 25, "Skillable-hosted environment teardown — automatic via snapshot revert or container destroy. VM/ESX/Container ONLY, NOT Simulation."),
    ScoringSignal("Simulation Reset", 0, "Simulation session ends with the session — display-only, zero credit (Frank 2026-04-07)."),
    ScoringSignal("Teardown API", 22, "Vendor API covers cleanup — green tier"),
    ScoringSignal("Low Orphan Risk", 0, "Rich teardown API with minor gaps — green context badge"),
)

_teardown_penalties = (
    Penalty("Manual Teardown", -10, "manual_teardown",
            "No programmatic teardown — manual cleanup required between learners"),
    Penalty("Orphan Risk", -5, "orphan_risk",
            "Partial teardown API — gaps remain, amber severity"),
    Penalty("High Orphan Risk", -15, "high_orphan_risk",
            "No teardown API or major cleanup gaps — significant orphan risk, red severity"),
)

_teardown_dimension = Dimension(
    name="Teardown",
    weight=25,
    question="Can we clean it up when it's over?",
    badges=_teardown_badges,
    scoring_signals=_teardown_signals,
    penalties=_teardown_penalties,
    floor=0,
    notes="For VM/container labs, teardown is automatic and scores full marks. "
          "Badges only surface when there's a finding. For BYOC/custom API products, "
          "teardown IS a real build task.",
)


PILLAR_PRODUCT_LABABILITY = Pillar(
    name="Product Labability",
    weight=50,
    level="product",
    question="How labable is this product?",
    dimensions=(
        _provisioning_dimension,
        _lab_access_dimension,
        _scoring_dimension,
        _teardown_dimension,
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 2 — INSTRUCTIONAL VALUE (20%)
#
# The commercial case.  Measures whether this product genuinely warrants
# hands-on lab experiences.  Combined with Product Labability, these two
# product-level pillars represent 70% of the Fit Score.
# ═══════════════════════════════════════════════════════════════════════════════

_product_complexity_badges = (
    # ANSWERS, not topics. Each badge label is a finding the seller can
    # read out loud and understand without context. The rubric model
    # allows variable AI-synthesized names — these are example patterns.
    Badge("Deeply Configurable", (
        BadgeColor("green", "Many options with real consequences — deeply configurable product"),
        BadgeColor("amber", "Some configuration depth but limited scope"),
    )),
    Badge("Multi-Phase Workflow Present", (
        BadgeColor("green", "Multiple distinct phases — design, build, deploy, troubleshoot"),
        BadgeColor("amber", "Some depth, similar phases"),
    )),
    Badge("Multiple Admin Roles", (
        BadgeColor("green", "Many personas need separate hands-on programs"),
        BadgeColor("amber", "Few roles, not distinct enough for separate tracks"),
    )),
    Badge("Rich Troubleshooting Scenarios", (
        BadgeColor("green", "Rich fault scenarios documented — real failure modes to practice"),
        BadgeColor("amber", "Some troubleshooting, limited scope"),
    )),
    Badge("Complex Network Topology", (
        BadgeColor("green", "VLANs, routing, multi-network topologies — learned only by manipulation"),
        BadgeColor("amber", "Some networking, straightforward"),
    )),
    Badge("Integration-Heavy Workflow", (
        BadgeColor("green", "External systems are primary workflow — the product's real work lives in integrations"),
        BadgeColor("amber", "Some integrations, not primary workflow"),
    )),
    Badge("AI Practice Required", (
        BadgeColor("green", "AI features require iterative hands-on prompt + verify + tune cycles"),
        BadgeColor("amber", "AI present but shallow"),
    )),
    Badge("Multi-VM Architecture", (
        BadgeColor("green", "Product requires multiple VMs working together — cross-pillar with P1 Multi-VM Lab"),
    )),
    Badge("Consumer Grade", (
        BadgeColor("amber", "Might be consumer-oriented (inferred)"),
        BadgeColor("red", "Consumer app confirmed — not lab appropriate"),
    )),
    Badge("Simple UX", (
        BadgeColor("amber", "Might be too simple (inferred)"),
        BadgeColor("red", "Wizard-driven or overly simple interface confirmed — minimal lab value"),
    )),
)

_product_complexity_signals = (
    ScoringSignal("Design & Architecture topics", 5, "Architecture planning, topology/schema decisions, capacity modeling"),
    ScoringSignal("Configuration & Tuning topics", 5, "Policy creation, configuration, customization to environment"),
    ScoringSignal("Deployment & Provisioning topics", 5, "Installation, provisioning, release pipeline, migrations"),
    ScoringSignal("Support Scenarios", 5, "Monitoring, alerting, incident response, lifecycle management"),
    ScoringSignal("Troubleshooting topics", 5, "Diagnosing failures in realistic broken states"),
    ScoringSignal("Creating AI", 5, "Product builds, trains, or deploys AI models"),
    ScoringSignal("Learning AI-embedded features", 4, "AI capabilities embedded in a larger product requiring hands-on practice"),
    ScoringSignal("Integration complexity", 3, "External systems are primary workflow, not incidental"),
    ScoringSignal("Role breadth", 2, "Multiple distinct personas each need separate lab programs"),
    ScoringSignal("Multi-component topology", 2, "Lab requires multiple VMs or services"),
    ScoringSignal("Consumer Grade", -20, "Consumer-grade product — not lab appropriate"),
    ScoringSignal("Simple UX", -15, "Wizard-driven or overly simple interface"),
)

_product_complexity_rubric = Rubric(
    tiers=(
        RubricTier(
            "strong", 6,
            "A strong positive answer — deep multi-system work, multi-phase workflows with real "
            "state transitions, multiple distinct admin/operator roles, rich troubleshooting, "
            "multi-VM architecture, or genuine AI requiring iterative practice",
        ),
        RubricTier(
            "moderate", 3,
            "A partial positive answer — some depth or some complexity but limited scope — "
            "single-phase, narrow role set, light troubleshooting",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., deprecated "
            "features, upcoming version changes, specific integrations worth mentioning",
        ),
        RubricTier(
            "weak", 0,
            "No answer — thin documentation, mostly straightforward, single-stage workflow — don't emit",
        ),
    ),
    is_about=(
        "Whether using this product requires repeated, practiced skill",
        "Documentation breadth — module count, features per module, options per feature, interoperability",
        "Multi-phase workflows that span design, build, deploy, monitor, troubleshoot",
        "Role diversity — admin vs operator vs end user vs developer",
        "Multi-VM architecture (cross-pillar with P1 Multi-VM Lab)",
        "AI features that require iterative hands-on practice (cannot be learned by watching)",
    ),
    is_not_about=(
        "Whether the product is easy or hard to PROVISION (that is Pillar 1)",
        "Whether labs can be SCORED (that is Pillar 1 Scoring dimension)",
        "Whether the customer org has training infrastructure (that is Pillar 3)",
        "The mastery STAKES of getting it wrong (that is the Mastery Stakes dimension)",
        "Generic complexity claims — 'enterprise-grade', 'comprehensive platform', 'powerful tool' "
        "are not evidence of hands-on complexity. Look for SPECIFIC signals: how many distinct "
        "configuration surfaces exist? How many admin roles operate independently? How many "
        "workflow stages require different skills? If you can't name the specific complexity, "
        "don't emit the signal.",
    ),
    signal_categories=(
        "multi_vm_architecture",   # cross-pillar with P1 Multi-VM Lab
        "deep_configuration",
        "multi_phase_workflow",
        "role_diversity",
        "troubleshooting_depth",
        "complex_networking",      # cross-pillar with P1 Complex Topology
        "integration_complexity",
        "ai_practice_required",
        "state_persistence",
        "compliance_depth",
        # Negative answers (hard negatives — fall back to color points):
        "consumer_grade",          # red
        "simple_ux",               # red
        "wizard_driven",           # amber/red
        # Informational:
        "product_complexity_context",
    ),
)

_product_complexity_dimension = Dimension(
    name="Product Complexity",
    weight=40,
    question="Is this product hard enough to require hands-on practice?",
    badges=_product_complexity_badges,
    rubric=_product_complexity_rubric,
    cap=40,
    notes="Pillar 2 — rubric model. Badge names are variable and AI-synthesized to capture "
          "domain-specific complexity (subject matter terminology). The AI grades each badge "
          "against the rubric tiers and tags it with a signal_category from the fixed list. "
          "Math is rubric-driven, not name-matched.",
)


_mastery_stakes_badges = (
    # ANSWERS — each badge names a specific consequence of failure, not a
    # topic like "High-Stakes Skills." Variable AI-synthesized names are
    # preferred (e.g., "HIPAA Exposure", "PCI-DSS Audit Risk", "Board
    # Privilege Exposure") — these are example patterns.
    Badge("Breach Exposure", (
        BadgeColor("green", "Security mistakes expose data, credentials, or systems to attack"),
    )),
    Badge("Compliance Audit Risk", (
        BadgeColor("green", "Regulatory framework (HIPAA, PCI, SOX, GDPR, SOC 2) creates direct audit / fine exposure"),
    )),
    Badge("Data Integrity Failure", (
        BadgeColor("green", "Errors corrupt data, break reporting, poison downstream systems"),
    )),
    Badge("Production Outage Risk", (
        BadgeColor("green", "Failures cause outages, SLA breaches, missed transactions"),
    )),
    Badge("Patient Safety Critical", (
        BadgeColor("green", "Safety-critical environment — physical harm, patient safety, OT control systems"),
    )),
    Badge("Legal Liability Exposure", (
        BadgeColor("green", "Malpractice, privilege breaches, contractual liability"),
    )),
    Badge("Material Financial Impact", (
        BadgeColor("green", "Direct dollar impact — incorrect transactions, pricing errors, reconciliation failures"),
    )),
    Badge("Steep Learning Curve", (
        BadgeColor("green", "Long path to competence, multiple stages — onboarding risk"),
        BadgeColor("amber", "Some learning curve but manageable"),
    )),
    Badge("High Churn Risk", (
        BadgeColor("green", "Documented adoption risk — customers churn when they can't become competent"),
        BadgeColor("amber", "Some adoption challenges"),
    )),
)

_mastery_stakes_signals = (
    ScoringSignal("High-stakes skills", 10, "Misconfiguration causes breach, data loss, compliance failure, downtime"),
    ScoringSignal("Steep learning curve", 8, "Long path from beginner to competent, multiple stages"),
    ScoringSignal("Adoption risk", 7, "Poor adoption or slow TTV is documented"),
)

_mastery_stakes_rubric = Rubric(
    tiers=(
        RubricTier(
            "strong", 9,
            "A strong positive answer — misconfiguration causes breach, data loss, compliance "
            "failure, sanctions, malpractice, material downtime, or physical harm",
        ),
        RubricTier(
            "moderate", 5,
            "A partial positive answer — errors create rework / reputation cost but are recoverable",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., recent incident "
            "reported in the news, known vulnerability class",
        ),
        RubricTier(
            "weak", 0,
            "No answer — mostly inconvenience, easily fixed, no lasting consequences — don't emit",
        ),
    ),
    is_about=(
        "What are the CONSEQUENCES of getting it wrong — named, specific consequences",
        "Breach exposure, compliance audit risk, data integrity failures, production outages",
        "Patient safety, legal liability, material financial impact",
        "Steep learning curves and adoption / churn risk",
    ),
    is_not_about=(
        "How HARD the product is to use (that is Product Complexity)",
        "Whether the product can be SCORED (that is Pillar 1 Scoring)",
        "How important the product is to the customer's business in general (that is Market Demand)",
        "Generic compliance risk — 'compliance_consequences' is ONLY for products whose SUBJECT "
        "MATTER is directly about regulatory compliance, security policy, audit, data protection, "
        "or legal obligations. General IT, Linux admin, RPA, collaboration tools do NOT have "
        "compliance consequences just because they involve technology. Ask: 'if a learner fails "
        "this topic, does a regulator or auditor care?' If no, do NOT emit compliance_consequences.",
        "Generic breach exposure — 'breach_exposure' is ONLY for products in cybersecurity, "
        "identity management, data protection, or network security where misconfiguration directly "
        "enables unauthorized access. RPA tools (UiPath), ERP systems, collaboration platforms, "
        "and general IT tools do not have breach exposure just because they process data. Ask: "
        "'does misconfiguring THIS product directly open an attack vector?' If no, do NOT emit.",
        "Generic business continuity — 'business_continuity' is ONLY for products that ARE the "
        "continuity infrastructure (backup systems, DR platforms, HA clusters, load balancers) or "
        "whose failure demonstrably causes organization-wide outages. A single application going "
        "down is not business continuity — it's downtime for that application's users.",
    ),
    signal_categories=(
        "breach_exposure",
        "compliance_consequences",
        "data_integrity",
        "business_continuity",
        "safety_regulated",
        "legal_liability",
        "reputation_damage",
        "financial_impact",
        "harm_severity",
        "learning_curve",
        "adoption_risk",
        # Informational:
        "mastery_stakes_context",
    ),
)

_mastery_stakes_dimension = Dimension(
    name="Mastery Stakes",
    weight=25,
    question="How much does competence matter?",
    badges=_mastery_stakes_badges,
    rubric=_mastery_stakes_rubric,
    cap=25,
)


_lab_versatility_badges = (
    Badge("Red vs Blue", (
        BadgeColor("green", "Adversarial team scenarios applicable"),
    ), notes="Cybersecurity — EDR, SIEM, network security"),
    Badge("Simulated Attack", (
        BadgeColor("green", "Realistic attack, learner responds"),
    ), notes="Cybersecurity — any defensive product"),
    Badge("Incident Response", (
        BadgeColor("green", "Production down, diagnose under pressure"),
    ), notes="Infrastructure, security, cloud, databases"),
    Badge("Break/Fix", (
        BadgeColor("green", "Something's broken, figure it out"),
    ), notes="Broad — any product with complex failure modes"),
    Badge("Team Handoff", (
        BadgeColor("green", "Multi-person sequential workflow"),
    ), notes="DevOps, data engineering, SDLC"),
    Badge("Bug Bounty", (
        BadgeColor("green", "Find the flaws — competitive discovery"),
    ), notes="Development platforms, data, security"),
    Badge("Cyber Range", (
        BadgeColor("green", "Full realistic network, live threats"),
    ), notes="Network security, SOC operations"),
    Badge("Performance Tuning", (
        BadgeColor("green", "System works but needs optimization"),
    ), notes="Databases, infrastructure, cloud, data"),
    Badge("Migration Lab", (
        BadgeColor("green", "Move from A to B"),
    ), notes="Enterprise software, cloud, infrastructure"),
    Badge("Architecture Challenge", (
        BadgeColor("green", "Design and build from requirements"),
    ), notes="Cloud, infrastructure, networking, data"),
    Badge("Compliance Audit", (
        BadgeColor("green", "Validate configurations against regulations"),
    ), notes="Healthcare, finance, security, regulated industries"),
    Badge("Disaster Recovery", (
        BadgeColor("green", "Systems failed, recover operations"),
    ), notes="Infrastructure, cloud, data protection"),
)

_lab_versatility_rubric = Rubric(
    tiers=(
        RubricTier(
            "strong", 5,
            "A strong positive answer — a clear high-value lab type fits naturally (Red vs Blue, "
            "Cyber Range, Incident Response, Performance Tuning, Migration Lab, Compliance Audit, "
            "Break/Fix, CTF) — the product genuinely supports it without shoehorning",
        ),
        RubricTier(
            "moderate", 3,
            "A partial positive answer — lab type is adaptable to the product but requires some shoehorning",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., a lab type "
            "supported via a third-party integration, an emerging lab modality worth mentioning",
        ),
        RubricTier(
            "weak", 0,
            "No answer — lab type doesn't fit, product doesn't support hands-on in any recognizable form — don't emit",
        ),
    ),
    is_about=(
        "What kinds of high-value hands-on experiences could be DESIGNED and DELIVERED on Skillable for this product",
        "Lab types that fit the product naturally — adversarial scenarios, cyber ranges, "
        "incident response, break/fix, migration, compliance audit, performance tuning, CTF",
        "Lab types that serve dual purpose — conversational competence in Inspector + "
        "program recommendations in Designer",
    ),
    is_not_about=(
        "Who will actually build the labs (Skillable Professional Services, customer team, content partner)",
        "Standard step-by-step labs (those exist for every product, not credit-worthy here)",
        "How the lab is provisioned (that is Pillar 1)",
        "Whether the customer can deliver labs (that is Delivery Capacity)",
        "Cybersecurity lab types forced onto non-security products — 'adversarial_scenario', "
        "'simulated_attack', 'incident_response', 'cyber_range', 'ctf' are ONLY for cybersecurity, "
        "network security, and identity management products. An RPA tool does not have adversarial "
        "scenarios. An ERP system does not have a cyber range. Match the lab type to the product's "
        "actual domain.",
    ),
    signal_categories=(
        "adversarial_scenario",
        "simulated_attack",
        "incident_response",
        "break_fix",
        "team_handoff",
        "bug_bounty",
        "cyber_range",
        "performance_tuning",
        "migration_lab",
        "architecture_challenge",
        "compliance_audit",
        "disaster_recovery",
        "ctf",
        # Informational:
        "lab_versatility_context",
    ),
)

_lab_versatility_dimension = Dimension(
    name="Lab Versatility",
    weight=15,
    question="What kinds of hands-on experiences can we build?",
    badges=_lab_versatility_badges,
    rubric=_lab_versatility_rubric,
    cap=15,
    notes="Pillar 2 — rubric model. The AI picks 1-3 lab types per product based on specific "
          "research, grades each against the rubric, and tags with a signal_category. Dual "
          "purpose: conversational competence in Inspector + program recommendations in Designer.",
)


_market_demand_badges = (
    # ANSWERS — each badge is a specific fact about the product's market.
    # Every badge answers: "how big is the worldwide population of people
    # who need to learn THIS specific product at hands-on depth?"
    # Category demand is the baseline (cybersecurity is inherently high);
    # product-specific evidence comes from cert bodies (CompTIA, EC-Council,
    # SANS, ISC2) AND independent training markets (Coursera, Pluralsight,
    # LinkedIn Learning, Udemy). Variable AI-synthesized names preferred.
    #
    # Scale & population answers:
    Badge("~2M Users", (
        BadgeColor("green", "Large install base — significant specialist training population"),
    )),
    Badge("~50K Users", (
        BadgeColor("gray", "Moderate install base"),
    )),
    Badge("~500 Users", (
        BadgeColor("amber", "Small install base — limited training population. Emit with signal_category=small_install_base so the penalty fires."),
    )),
    Badge("Enterprise Validated", (
        BadgeColor("green", "Enterprise adoption confirmed at scale — Fortune 500 customers named"),
    )),
    # Geographic reach answers:
    Badge("Global", (
        BadgeColor("green", "Global geographic presence"),
    )),
    Badge("NAMER & EMEA", (
        BadgeColor("gray", "North America and EMEA presence"),
    )),
    Badge("US Only", (
        BadgeColor("gray", "US-only geographic presence"),
    )),
    Badge("APAC Only", (
        BadgeColor("gray", "APAC-only geographic presence"),
    )),
    # Independent training market answers (Frank 2026-04-07: check
    # CompTIA, EC-Council, SANS, Coursera, Pluralsight, LinkedIn Learning):
    Badge("CompTIA Curriculum", (
        BadgeColor("green", "CompTIA curriculum mentions THIS product — independent cert body validation"),
    )),
    Badge("EC-Council Track", (
        BadgeColor("green", "EC-Council / SANS / ISC2 track mentions THIS product"),
    )),
    Badge("~15 Pluralsight Courses", (
        BadgeColor("green", "Pluralsight has substantial courses on THIS product — count it"),
    )),
    Badge("~5 Coursera Courses", (
        BadgeColor("green", "Coursera / LinkedIn Learning / Udemy have courses on THIS product — count it"),
    )),
    Badge("No Independent Courses Found", (
        BadgeColor("amber", "Search of Coursera, Pluralsight, LinkedIn Learning, Udemy found fewer than 3 courses on THIS product — cross-pillar with Delivery Capacity"),
    )),
    # Certification ecosystem answers:
    Badge("Active Cert Ecosystem", (
        BadgeColor("green", "Vendor's own active certification program with published pass rates"),
    )),
    Badge("Emerging Cert", (
        BadgeColor("gray", "Certification program in early stages"),
    )),
    Badge("Competitor Labs Confirmed", (
        BadgeColor("green", "Other lab platforms sell hands-on training for this product — demand is proven"),
    )),
    # Funding / growth answers:
    Badge("Rapid Growth", (
        BadgeColor("green", "Company or product showing rapid growth trajectory"),
    )),
    Badge("Series D $200M", (
        BadgeColor("green", "Significant funding round — strong market validation (example — use actual round)"),
    )),
    Badge("IPO 2024", (
        BadgeColor("green", "Recent IPO — scale and market maturity confirmed (example — use actual year)"),
    )),
    Badge("Layoffs Reported", (
        BadgeColor("amber", "Workforce reductions reported — potential market instability"),
    )),
    # AI / category answers:
    Badge("AI-Powered Product", (
        BadgeColor("green", "Product has AI features that require hands-on practice — surging skill demand"),
    )),
    Badge("AI Platform", (
        BadgeColor("green", "Product IS an AI platform — labs teach building / training / deploying AI"),
    )),
    Badge("High-Demand Category", (
        BadgeColor("green", "Product category has inherent high demand for hands-on training (cybersecurity, cloud, DevOps, data, AI)"),
    )),
    Badge("Niche Within Category", (
        BadgeColor("amber", "Product sits inside a hot category but is itself a narrow specialty (e.g., a specific threat-intel feed inside the broader cybersecurity market). Emit with signal_category=niche_within_category so the penalty fires against the category-demand baseline."),
    )),
)

_market_demand_signals = (
    ScoringSignal("High-demand category prior", 8, "Cybersecurity, Cloud Infrastructure, Networking/SDN, Data Science & Engineering, Data & Analytics, DevOps"),
    ScoringSignal("Moderate-demand category prior", 4, "Data Protection, Infrastructure/Virtualization, App Development, ERP/CRM, Healthcare IT, FinTech, Collaboration, Content Management, Legal Tech, Industrial/OT"),
    ScoringSignal("Low-demand category prior", 0, "Simple SaaS, Consumer"),
    ScoringSignal("Creating AI signal", 3, "Product builds, trains, or deploys AI models"),
    ScoringSignal("Learning AI-embedded features signal", 3, "AI capabilities embedded in product requiring hands-on practice"),
    ScoringSignal("Active Certification", 2, "Credentialing ecosystem exists"),
    ScoringSignal("Competitor Labs Confirmed", 2, "Other providers invest in hands-on training"),
    ScoringSignal("Large/growing install base", 2, "Significant and/or growing user community"),
    ScoringSignal("Growing category", 1, "Product category is expanding"),
)

_market_demand_rubric = Rubric(
    tiers=(
        RubricTier(
            "strong", 5,
            "A strong positive answer — a named cert body mentions THIS product (CompTIA, "
            "EC-Council, SANS, ISC2), Coursera / Pluralsight / LinkedIn Learning has 10+ courses "
            "on THIS product, Fortune 500 adoption confirmed, active cert with tested pass rates, "
            "AI platform at scale, IPO or major funding, global reach",
        ),
        RubricTier(
            "moderate", 3,
            "A partial positive answer — moderate install base, 3-9 independent courses on THIS "
            "product, emerging certification, regional presence, recent series funding",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., parent company, "
            "recent rebrand, competitive landscape context",
        ),
        RubricTier(
            "weak", 0,
            "Thin signal — small install base, niche category, no certification — don't emit",
        ),
    ),
    is_about=(
        "Whether the broader market validates the need for PAID HANDS-ON TRAINING on this product — "
        "not demand for the product itself. A product can have millions of users but low training "
        "demand if most users learn for free (open source, community docs, YouTube). Market Demand "
        "measures whether people PAY to learn this product through structured training programs.",
        "Install base scale (~2M Users, ~50K Users, ~500 Users) — but DISCOUNT for open source: "
        "MongoDB has 40M+ developers but most learn for free. The PAID training population is a "
        "fraction of the total user base. Score based on the paid training market, not the user base.",
        "Geographic reach (Global, NAMER+EMEA, Regional)",
        "Certification ecosystem (Active Cert, Emerging Cert)",
        "Funding and growth signals (IPO, Series D, Rapid Growth, Layoffs)",
        "Category demand priors (cybersecurity, cloud, networking are inherently high-demand)",
        "Competitor labs confirmed (other providers invest in hands-on for this product)",
        "AI signals (product builds AI, product has embedded AI features)",
        "Independent third-party training market — Coursera, Pluralsight, LinkedIn Learning, "
        "Udemy, Skillsoft course counts where the publisher is NOT the vendor. Independent "
        "trainers wouldn't invest without market demand, so course counts are a direct demand "
        "signal. (Vendor-published courses on those same platforms are Delivery Capacity + "
        "Build Capacity, NOT Market Demand — Frank 2026-04-08.)",
        "Cert body curricula — CompTIA, EC-Council, SANS, ISC2 mentioning THIS product in "
        "their curricula. External recognition by cert bodies is a demand signal. (Frank "
        "2026-04-08 — moved from Delivery Capacity.)",
        "Formal Authorized Training Partner networks — ATPs / ALPs prove demand exists, "
        "because partners wouldn't invest in certification and delivery infrastructure "
        "without underlying skill demand. This is a CROSS-CREDIT with Delivery Capacity: "
        "the same ATP fact produces a Delivery Capacity Layer 2 signal AND a Market Demand "
        "signal. Both credits fire legitimately.",
    ),
    is_not_about=(
        "How the customer org is structured (that is Organizational DNA)",
        "Whether the customer has training programs (that is Training Commitment)",
        "Technical depth of the product (that is Product Complexity)",
        "Vendor-direct training (Delivery Capacity — Layer 1 vendor-delivered)",
        "LMS infrastructure (Delivery Capacity)",
        "Lab infrastructure / lab platforms (Build Capacity)",
        "Raw product popularity for OPEN SOURCE products — GitHub stars, Stack Overflow questions, "
        "npm downloads, and Docker Hub pulls measure PRODUCT adoption, not TRAINING demand. For open "
        "source products (MongoDB, PostgreSQL, Redis, Kubernetes, Terraform), score Market Demand "
        "based on PAID training signals (enterprise training programs, cert ecosystems, paid course "
        "platforms with 10+ courses) NOT free community usage. Open source with 40M users but 3 paid "
        "courses scores LOWER than commercial software with 500K users and 50 paid courses + a cert.",
    ),
    signal_categories=(
        # Scale + population answers (for product-specific differentiation within a category)
        "install_base_scale",
        "enterprise_validation",
        "geographic_reach",
        # Independent training market answers (Market Demand only per Frank
        # 2026-04-08). Product-specific evidence from WHO TEACHES THIS
        # PRODUCT externally via independent publishers.
        "cert_body_mentions",          # CompTIA / EC-Council / SANS / ISC2 mention THIS product
        "independent_training_market", # Coursera / Pluralsight / LinkedIn Learning / Udemy — independent publishers only
        # ATP cross-credit from Delivery Capacity (Frank 2026-04-08):
        # same fact produces two credits — Delivery Layer 2 AND Market
        # Demand validation.
        "atp_alp_program",             # formal ATPs prove demand exists
        # Vendor's own ecosystem:
        "cert_ecosystem",              # vendor's own certification program
        "competitor_labs",             # other lab platforms sell training for this product
        # Funding / growth:
        "funding_growth",
        # Category baseline:
        "category_demand",
        "ai_signal",
        # Penalty answers (fire via RUBRIC_PENALTY_SIGNALS → MARKET_DEMAND_PENALTIES):
        # These are negative findings — research asymmetry favors aggressive
        # penalization here because the evidence is outward-facing and easy
        # to verify.  The AI emits these as amber badges and the math layer
        # subtracts the configured hit.
        "no_independent_training_market",  # fewer than 3 courses found (Market Demand only now)
        "small_install_base",              # < ~1K users / tens of logos / no press
        "niche_within_category",           # hot category, narrow specialty inside it (e.g., Trellix GTI inside cyber)
    ),
)

_market_demand_dimension = Dimension(
    name="Market Demand",
    weight=20,
    question="Does the broader market validate the need for hands-on training on this product?",
    badges=_market_demand_badges,
    rubric=_market_demand_rubric,
    cap=20,
    notes="Pillar 2 — rubric model. Variable badge names carry the actual data (~2M Users, "
          "Series D $200M, IPO 2024, Cisco Live 30K). Compact 2-3 word names with abbreviations.",
)


PILLAR_INSTRUCTIONAL_VALUE = Pillar(
    name="Instructional Value",
    weight=20,
    level="product",
    question="Does this product have instructional value for hands-on training?",
    dimensions=(
        _product_complexity_dimension,
        _mastery_stakes_dimension,
        _lab_versatility_dimension,
        _market_demand_dimension,
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 3 — CUSTOMER FIT (30%)
#
# Everything about the organization in one Pillar.  Combines training
# commitment, organizational character, delivery capacity, and build
# capability.  30% of the Fit Score — meaningful but never overriding
# the product truth.
# ═══════════════════════════════════════════════════════════════════════════════

_training_commitment_badges = (
    # ANSWERS — each badge names a specific finding about the customer's
    # training commitment, not a topic. Variable AI-synthesized names are
    # preferred (e.g., "Named Customer Enablement Team", "~200 Courses",
    # "VP of Education Named") — these are example patterns.
    Badge("Named Customer Enablement Team", (
        BadgeColor("green", "Dedicated customer enablement team with named leadership documented"),
    )),
    Badge("Dedicated Customer Success Org", (
        BadgeColor("green", "Standalone customer success organization with training mandate"),
    )),
    Badge("Formal Partner Academy", (
        BadgeColor("green", "Named partner / channel training program with structured curriculum"),
    )),
    Badge("Active Cert Exam", (
        BadgeColor("green", "Active certification with tested exams and pass-rate publication"),
    )),
    Badge("Published Training Catalog", (
        BadgeColor("green", "Meaningful catalog of published courses — use the count if known (e.g. ~200 Courses)"),
    )),
    Badge("Regulated Industry", (
        BadgeColor("green", "Regulated industry — compliance-inherent training driver"),
        BadgeColor("gray", "Some regulation, not compliance-driven"),
    )),
    Badge("Regulated Compliance Training", (
        BadgeColor("green", "Training built around specific regulatory requirements (HIPAA, SOX, PCI, etc.)"),
    )),
    Badge("External Audit-Driven Training", (
        BadgeColor("green", "External audits require demonstrated competence — training is table-stakes"),
    )),
    Badge("VP of Education Named", (
        BadgeColor("green", "VP-level or C-level training leadership documented — level only, not personal name"),
    )),
    Badge("Hands-On Training Culture", (
        BadgeColor("green", "Explicit hands-on / lab / interactive / scenario-based language in published programs"),
    )),
    Badge("Multi-Audience Training Commitment", (
        BadgeColor("green", "Training spans employees + customers + partners — deepest breadth signal"),
    )),
    Badge("Slide-Deck Only Training", (
        BadgeColor("amber", "Training exists but content-only — no hands-on evidence"),
    )),
)

_training_commitment_rubric = Rubric(
    tiers=(
        # Every badge is one of four ANSWERS: good (strong), pause (moderate),
        # context-only (informational), or nothing to say (weak).
        RubricTier(
            "strong", 6,
            "A strong positive answer — named customer enablement team, active cert exam, hands-on / "
            "lab / interactive language in published programs, VP-level training leadership, "
            "multi-audience commitment (employees + customers + partners)",
        ),
        RubricTier(
            "moderate", 3,
            "A partial positive answer — catalog exists but slide-deck-only, director-level training "
            "leader, single-audience commitment, some compliance training",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., recent hire of a "
            "VP of Education, announced investment in customer success, regulated-industry framing",
        ),
        RubricTier(
            "weak", 0,
            "No answer — generic 'we train our customers' with no specifics — don't emit",
        ),
    ),
    is_about=(
        "Whether the org is COMMITTED to customer competence (not just checking a training box)",
        "Named customer enablement teams, customer success orgs with training mandate",
        "Active certification programs with tested exam pass rates",
        "Multi-audience breadth: employees + customers + partners = deepest commitment",
        "Hands-on / interactive / scenario-based language in published programs",
        "Regulated-industry compliance training (inherent driver)",
    ),
    is_not_about=(
        "Technical openness of products (that is Pillar 1)",
        "Org culture / decision-making (that is Organizational DNA)",
        "Lab platform infrastructure (that is Delivery Capacity)",
        "Content creation roles (that is Build Capacity)",
    ),
    signal_categories=(
        # Positive answers:
        "customer_enablement_team",
        "customer_success_investment",
        "partner_enablement_program",
        "employee_learning_investment",
        "multi_audience_commitment",
        "cert_exam_active",
        "onboarding_program",
        "training_leadership_level",
        "training_events_at_scale",
        "hands_on_learning_language",
        "compliance_training_program",
        "training_catalog_present",
        # Negative answers (fire via RUBRIC_PENALTY_SIGNALS):
        "no_customer_training",
        "thin_cert_program",
        "no_customer_success_team",
        "minimal_training_language",
        # Informational context:
        "training_org_context",
    ),
)

_training_commitment_dimension = Dimension(
    name="Training Commitment",
    weight=25,
    question="Have they invested in training? What's the evidence?",
    badges=_training_commitment_badges,
    rubric=_training_commitment_rubric,
    notes="Pillar 3 — rubric model. Three motivation categories (product adoption, skill "
          "development, compliance & risk) serve as framing variables that shape how "
          "recommendations are communicated. The hands-on / lab / interactive language pattern "
          "is the single strongest Training Commitment signal.",
)


_organizational_dna_badges = (
    # ALL badges are ANSWERS (findings the seller can read out loud), never
    # questions or topic labels. The rubric model allows variable AI-
    # synthesized names — these tuples are EXAMPLES the prompt shows the
    # AI as starting patterns. Finding-as-name discipline (GP4).
    #
    # Positive findings — things that are TRUE about the organization:
    Badge("Platform Buyer", (
        BadgeColor("green", "Uses external platforms (Salesforce, Workday, Okta, etc.) for things companies might build in-house — evidence of platform-buyer culture"),
    )),
    Badge("Multi-Type Partnerships", (
        BadgeColor("green", "Multiple distinct kinds of partnerships documented — technology + channel + delivery + content + integration"),
    )),
    Badge("Strategic Alliance Program", (
        BadgeColor("green", "Formal alliance program with tiers, certifications, incentives, named leadership"),
    )),
    Badge("Partner-Friendly", (
        BadgeColor("green", "Accessible contact paths, documented fast decision-making, partner-friendly posture"),
    )),
    Badge("Named Alliance Leadership", (
        BadgeColor("green", "VP of Partnerships / Head of Alliances / Chief Alliance Officer documented"),
    )),
    # Negative findings — things that are TRUE but bad for Skillable.
    # The math layer treats these via RUBRIC_PENALTY_SIGNALS; the badge list
    # here exists so the AI sees the finding-as-name pattern and so
    # _format_canonical_badge_names shows the prompt the valid labels.
    Badge("Builds Everything", (
        BadgeColor("amber", "IBM-style 'we build it ourselves' posture documented — outside platforms treated as inferior by default"),
    )),
    Badge("Long RFP Process", (
        BadgeColor("amber", "Documented 9+ month vendor engagement cycles, exhaustive committees, multiple approval gates"),
    )),
    Badge("Heavy Procurement", (
        BadgeColor("amber", "Large vendor management bureaucracy — vendors treated as cost centers to extract value from"),
    )),
    Badge("Closed Platform", (
        BadgeColor("amber", "Proprietary everything — no public APIs, no ecosystem investment, no developer community"),
    )),
    Badge("Hard to Engage", (
        BadgeColor("red", "Documented hostility or legendary bureaucratic slowness toward outside partners — direct evidence"),
    )),
)

_organizational_dna_rubric = Rubric(
    tiers=(
        # Every badge is one of four ANSWERS (never a question or topic):
        #   strong        → good answer — green, positive contribution
        #   moderate      → pause answer — amber, smaller positive
        #   informational → context-only answer — zero scoring impact
        #   weak          → don't emit (no answer to give)
        # Negative answers (penalties) are handled by RUBRIC_PENALTY_SIGNALS,
        # not by the rubric tiers below.
        RubricTier(
            "strong", 6,
            "A strong positive answer — clear evidence of multi-type partnerships, "
            "platform-buyer culture, formal alliance program with tiers and certifications, "
            "named VP-level alliance leadership, or documented nimble partner-friendly engagement",
        ),
        RubricTier(
            "moderate", 3,
            "A partial positive answer — some partnerships but not multi-type, mixed buyer-"
            "builder posture, alliance program below VP level, moderate partner engagement",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., org size, "
            "parent company relationship, recent M&A activity affecting partnership posture. "
            "Emits the badge for conversational value but credits zero points",
        ),
        RubricTier(
            "weak", 0,
            "No answer — generic 'they're an organization' with no specific pattern — don't emit",
        ),
    ),
    is_about=(
        "How the company operates as a business — culturally",
        "Whether they see outside platforms as STRATEGIC ASSETS or as PROCUREMENT LINE ITEMS",
        "Partnership breadth: multiple distinct kinds (technology, channel, delivery, content)",
        "Platform-buyer behavior: using Salesforce, Workday, Okta etc. vs. building in-house",
        "Formal alliance program structure (tiers, certifications, named leadership)",
        "Engagement posture — nimble and partner-friendly vs. long RFPs and heavy procurement",
        "Closed-culture signals: 'we build everything here' (IBM pattern) documented explicitly",
    ),
    is_not_about=(
        "The technical architecture of their products (Pillar 1: Sandbox API, Identity API, etc.)",
        "API openness, platform extensibility, integration maturity (Pillar 1)",
        "Whether their software is technically modular (Pillar 1)",
        "Cloud-native vs on-prem deployment shape (classification metadata)",
        "Their product line structure (this dimension is about the ORG, not the products)",
        "'Open Platform Architecture' or similar technical openness signals (Pillar 1)",
        "Whether they have training at all (that is Training Commitment)",
        "Whether they can build labs (that is Build Capacity)",
        "Whether they can deliver labs at scale (that is Delivery Capacity)",
    ),
    signal_categories=(
        # Positive signal categories — each describes an ANSWER the badge represents.
        "many_partnership_types",          # answer: "they have many different kinds of partners"
        "strategic_asset_partnerships",    # answer: "they partner to build strategic assets"
        "platform_buyer_behavior",         # answer: "they use external platforms instead of building"
        "formal_channel_program",          # answer: "they have a structured partner program"
        "nimble_engagement",               # answer: "they're fast and accessible"
        "named_alliance_leadership",       # answer: "VP / head of alliances documented"
        # Negative signal categories — RUBRIC_PENALTY_SIGNALS mirrors these for
        # penalty application. Listed here so the prompt's valid-signal list
        # shows them as emittable answers.
        "long_rfp_process",                # answer: "their RFPs take 9+ months"
        "heavy_procurement",               # answer: "procurement treats vendors as cost centers"
        "build_everything_culture",        # answer: "IBM-style build-everything culture"
        "closed_platform_culture",         # answer: "proprietary everything, no ecosystem"
        "hard_to_engage",                  # answer: "documented hostility to outside partners"
        # Informational category — for context-only findings.
        "org_context",                     # answer: general context (size, parent, M&A)
    ),
)

_organizational_dna_dimension = Dimension(
    name="Organizational DNA",
    weight=25,
    question="Are they the kind of company that partners and builds training programs?",
    badges=_organizational_dna_badges,
    rubric=_organizational_dna_rubric,
    notes="Pillar 3 — rubric model. The character of the organization — partner vs build-in-house, "
          "easy or hard to engage. CRITICAL: this dimension is about the COMPANY, not the company's "
          "products. Technical architecture findings (API openness, platform extensibility) belong "
          "in Pillar 1, NOT here.",
)


_delivery_capacity_badges = (
    # ANSWERS — each badge names a specific delivery capability or gap.
    # Delivery Capacity is the vendor's apparatus for REACHING LEARNERS:
    # vendor-direct training, ATP/ALP networks, LMS platforms, events,
    # published course calendars, cert delivery infrastructure, and
    # geographic reach. It is NOT about lab infrastructure (Skillable,
    # CloudShare, Instruqt, DIY lab platforms) — lab infrastructure is
    # BUILD CAPACITY. It is NOT about independent third-party training
    # markets (Pluralsight, Coursera, LinkedIn Learning, Udemy) or cert
    # body curricula (CompTIA, EC-Council, SANS, ISC2) — those are
    # MARKET DEMAND. See Frank's 2026-04-08 rebuild routing decisions
    # in docs/next-session-todo.md §0b.
    #
    # ONE FACT, ONE BADGE (Frank 2026-04-07): the fact "the vendor delivers
    # its own training" is a single finding. Don't split it into three
    # badges (ILT + self-paced + labs) — the seller reads three labels for
    # one reality. Use ONE badge whose evidence text names the specific
    # delivery modes found (ILT, self-paced portal, vendor-run labs).
    #
    # Vendor-Delivered Training is independent from Partner-Delivered
    # Training (the next layer). A vendor can deliver its own training
    # strongly AND have zero training partners — those are two different
    # facts and get two different badges.
    #
    # ── Layer 1: Vendor-controlled (direct) training delivery ────────
    Badge("Vendor-Delivered Training", (
        BadgeColor("green", "Vendor runs its own training directly — list the modes found (ILT, self-paced portal, vendor-run labs, bootcamps) in the evidence text. Strong green when multiple modes exist at scale; name the depth you actually saw."),
        BadgeColor("amber", "Vendor-run training exists but is thin — e.g., slide-deck-only, one short course, limited scope"),
    )),
    # ── Layer 2: Auth-Partner-delivered (ATP / ALP programs) ─────────
    # Formal vendor-built partner programs for delivering training at
    # scale. Cross-credit with Market Demand: ATPs prove demand exists
    # (partners wouldn't invest without skill demand).
    Badge("Global Partner Network", (
        BadgeColor("green", "Scaled global Authorized Training Partner / Authorized Learning Partner network — use the count if known (e.g. ~500 ATPs)"),
    )),
    Badge("Regional Partner Network", (
        BadgeColor("amber", "ATP / ALP program exists but regionally limited"),
    )),
    # ── LMS infrastructure (how training is delivered to learners) ──
    Badge("Docebo-Hosted", (
        BadgeColor("green", "Docebo is their current LMS — Skillable-compatible partner LMS"),
    )),
    Badge("Cornerstone-Hosted", (
        BadgeColor("green", "Cornerstone is their current LMS — Skillable-compatible partner LMS"),
    )),
    Badge("Other LMS In Place", (
        BadgeColor("gray", "Non-Skillable-partner LMS in use — variable, name the platform in evidence"),
    )),
    Badge("Skillable Customer", (
        BadgeColor("green", "Already a Skillable customer — expansion opportunity"),
    )),
    # ── Events / calendar / cert delivery infrastructure ─────────────
    Badge("Flagship Event at Scale", (
        BadgeColor("green", "Major flagship event with hands-on tracks at scale — use the event name and attendance (e.g. Cisco Live 30K)"),
    )),
    Badge("Published Course Calendar", (
        BadgeColor("green", "Vendor has a public course registration page / training calendar — real evidence of active ILT delivery"),
    )),
    Badge("Cert Delivery Infrastructure", (
        BadgeColor("green", "Pearson VUE / Certiport / PSI / Certiverse integration — cert delivery reach"),
    )),
    # ── Penalty answers (fire via RUBRIC_PENALTY_SIGNALS) ───────────
    Badge("No Training Partners", (
        BadgeColor("red", "Zero ATP / reseller / channel training network where partners should exist"),
    )),
    Badge("No Classroom Delivery", (
        BadgeColor("red", "Zero evidence of instructor-led training, bootcamps, workshops, or published course calendar"),
    )),
    Badge("Single-Region Reach", (
        BadgeColor("amber", "Delivery presence limited to one state or country"),
    )),
)

_delivery_capacity_rubric = Rubric(
    tiers=(
        RubricTier(
            "strong", 8,
            "A strong positive answer — the two delivery layers stack for BONUS POINTS:\n"
            "  - Layer 1 (base): vendor-delivered training — ILT, self-paced portal, vendor-run "
            "labs, bootcamps, published course calendar at scale\n"
            "  - Layer 2 (TOP bonus): formal ATP / ALP program — scaled multi-partner delivery "
            "maturity where the vendor has built a certified partner network\n"
            "Also strong: Skillable-partner LMS already in place (Docebo, Cornerstone); flagship "
            "events at scale with hands-on tracks; cert delivery infrastructure (Pearson VUE, "
            "Certiport, PSI, Certiverse). **One fact, one badge.** Emit exactly one badge per "
            "layer found. Layer 1 is a single `Vendor-Delivered Training` badge whose evidence "
            "text names the modes found. Layer 2 is a separate `Global Partner Network` (or "
            "regional) badge.",
        ),
        RubricTier(
            "moderate", 4,
            "A partial positive answer — any single layer delivered in limited form. Regional "
            "(not global) ATP network; vendor-direct training without a formal partner program; "
            "other LMS in place (non-Skillable partner); smaller events with hands-on tracks.",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., recent partner "
            "program reorganization, geographic expansion plans, LMS migration in progress",
        ),
        RubricTier(
            "weak", 0,
            "No answer — plain 'they offer training' with no delivery infrastructure named — don't emit",
        ),
    ),
    is_about=(
        "Whether the org has the CAPACITY to reach learners at scale — the vendor's own delivery "
        "apparatus and distribution network",
        "",
        "TWO DELIVERY LAYERS — each is a separate signal and both are worth surfacing:",
        "",
        "  1. VENDOR-DELIVERED — the vendor runs training directly. Official ILT, self-paced "
        "portal, vendor-run hands-on labs, bootcamps, published course calendar. Positive "
        "signal bounded to what the vendor alone reaches. **Emit ONE badge** "
        "(`Vendor-Delivered Training`) whose evidence text names the specific modes you found. "
        "Do NOT split ILT, self-paced, and labs into three separate badges — that's three "
        "labels for one fact.",
        "",
        "  2. AUTH-PARTNER-DELIVERED — formal Authorized Training Partner / Authorized Learning "
        "Partner program. ATPs and ALPs are certified partners the vendor has authorized to "
        "deliver training at scale. This is the TOP delivery signal because it represents "
        "scaled multi-partner delivery maturity — the vendor has built a program, invested in "
        "partner certification, and has a network of named partners doing the delivery. Use "
        "badges like `Global Partner Network`, `Regional Partner Network`, `~500 ATPs`. "
        "**Cross-credit with Market Demand**: ATPs also prove demand exists (partners wouldn't "
        "invest without skill demand), so ATP facts fire a Market Demand signal in parallel.",
        "",
        "A vendor can have both layers (ideal), just one, or none (red flag).",
        "",
        "VENDOR-PUBLISHED THIRD-PARTY COURSES are a special case: when the vendor themselves "
        "is the publisher of courses on a third-party platform (e.g., Google Cloud Training on "
        "Coursera, AWS Training on LinkedIn Learning, Microsoft Learn content on edX), that "
        "counts as vendor-delivered training distributed through a third-party channel AND as "
        "Build Capacity (they built the content). Do NOT confuse this with independent third "
        "party courses on those same platforms — independent third-party courses belong to "
        "Market Demand, not Delivery Capacity.",
        "",
        "LMS platforms at scale (Skillable-partner LMS scores higher — Docebo, Cornerstone)",
        "Flagship events with hands-on tracks (Cohesity Connect, Cisco Live)",
        "Published course calendars — real evidence of active ILT delivery",
        "Cert delivery infrastructure (Pearson VUE, Certiport, PSI)",
        "Geographic reach (Indiana < US < Hemisphere < Global)",
        "Research asymmetry: Delivery Capacity is outward-facing and easy to verify — penalize "
        "aggressively on absence of public evidence",
    ),
    is_not_about=(
        "Content creation roles (Build Capacity)",
        "Lab infrastructure — Skillable, CloudShare, Instruqt, Skytap, Kyndryl, ReadyTech, "
        "DIY lab platforms, owned VM farm. Lab infrastructure lives in Build Capacity, not "
        "Delivery Capacity (Frank 2026-04-08).",
        "Independent third-party courses on Coursera / Pluralsight / LinkedIn Learning / "
        "Udemy / Skillsoft where the publisher is NOT the vendor. Those are Market Demand "
        "signals — the market showing up independently, not the vendor delivering. (Exception: "
        "vendor-published courses on those same platforms ARE Delivery Capacity + Build "
        "Capacity — see is_about.)",
        "Cert body curricula (CompTIA / EC-Council / SANS / ISC2 mentioning the product) — "
        "that's external market recognition, a Market Demand signal, not the vendor's "
        "delivery.",
        "Just having a training catalog (Training Commitment)",
        "Org culture / partnerships in general (Organizational DNA)",
        "Whether the labs themselves are good (that is content quality, not delivery)",
    ),
    signal_categories=(
        # Two delivery layers — ONE BADGE PER LAYER FOUND. Layers stack
        # for bonus points. One fact, one badge.
        #
        # Layer 1: VENDOR-DELIVERED (base) — vendor runs training directly.
        # Single signal category; the evidence text names the modes found
        # (ILT, self-paced portal, vendor-run labs, bootcamps).
        "vendor_delivered_training",       # vendor runs its own training directly (any/all modes)
        # Layer 2: AUTH-PARTNER-DELIVERED (top bonus) — ATP / ALP programs
        # Cross-credit with Market Demand — same fact fires atp_alp_program
        # in both Delivery (vendor's partner network) and Market Demand
        # (partners prove demand exists). Both credits are legitimate.
        "atp_alp_program",                 # formal global ATP / ALP program
        "regional_atp_network",            # smaller-scale regional version
        # Vendor-published content on third-party platforms (Google on
        # Coursera, AWS on LinkedIn Learning, Microsoft on edX). The
        # vendor authored the content (Build Capacity) AND chose the
        # distribution channel (Delivery Capacity). Same fact, two
        # credits. NOT to be confused with independent third-party
        # courses (those are Market Demand only).
        "vendor_published_on_third_party",
        # LMS infrastructure — how training is delivered to learners:
        "lms_partner",                     # Skillable-compatible LMS (Docebo, Cornerstone)
        "lms_other",                       # other LMS in place
        # Events / calendar / cert delivery:
        "training_events_scale",
        "cert_delivery_infrastructure",    # Pearson VUE / Certiport / PSI
        "geographic_reach",
        "published_course_calendar",
        # Negative answers (fire via RUBRIC_PENALTY_SIGNALS):
        "no_training_partners",
        "no_classroom_delivery",
        "single_region_only",
        # Informational context:
        "delivery_capacity_context",
    ),
)

_delivery_capacity_dimension = Dimension(
    name="Delivery Capacity",
    weight=30,
    question="Can they get labs to learners at scale?",
    badges=_delivery_capacity_badges,
    rubric=_delivery_capacity_rubric,
    notes="Pillar 3 — rubric model. Weighted highest within Customer Fit because having labs = "
          "cost, delivering labs = value. Lab platform badges are named for the platform itself "
          "(Skillable, CloudShare, Instruqt) — no 'Lab Platform:' prefix. 'No Lab Platform' is "
          "moderate (greenfield) NOT weak.",
)


_build_capacity_badges = (
    # ANSWERS — each badge names a specific finding about the customer's
    # build capacity.  Short abbreviated labels per Frank 2026-04-07:
    # "use abbreviations... Tech Build Team is fine."  Variable
    # AI-synthesized names with counts are still preferred when the
    # research finds them (e.g., "~30 Lab Authors").
    #
    # Build Capacity is about CREATING lab content: content development
    # roles, lab authors, instructional designers, tech writers, AND the
    # LAB INFRASTRUCTURE itself (Skillable, CloudShare, Instruqt, DIY lab
    # platforms, owned VM farm).  Lab infrastructure lives HERE, not in
    # Delivery Capacity — Frank's 2026-04-08 rebuild routing decision:
    # "if they have lab infrastructure, a bunch of VMs at their place or
    # they've got infrastructure to build labs, that's build capacity."
    Badge("Content Dev Team", (
        BadgeColor("green", "Named training organization with documented Lab Authors, IDs, Tech Writers"),
    )),
    Badge("Tech Build Team", (
        BadgeColor("green", "Can build lab environments, not just content — technical SMEs and lab engineers named"),
    )),
    Badge("Already Building Labs", (
        BadgeColor("green", "DIY lab authoring happening today — strongest possible Build Capacity signal"),
    )),
    # ── Lab infrastructure in place (Frank 2026-04-08) ──────────────
    # Having the infrastructure to build labs is build capacity, even if
    # the org isn't actively authoring labs today. Moved from Delivery
    # Capacity where these used to live erroneously.
    Badge("Skillable-Hosted", (
        BadgeColor("green", "Skillable is their lab platform — expansion opportunity, and lab infrastructure is in place for building labs"),
    )),
    Badge("Competitor Lab Platform", (
        BadgeColor("amber", "Competitor lab platform (CloudShare, Instruqt, Skytap, Kyndryl, ReadyTech) — they already have lab build infrastructure; displacement opportunity"),
    )),
    Badge("DIY Lab Platform", (
        BadgeColor("gray", "They built their own lab platform — they have lab infrastructure; replacement opportunity"),
    )),
    Badge("No Lab Platform", (
        BadgeColor("gray", "No incumbent lab platform detected — greenfield for lab infrastructure"),
    )),
    Badge("Outsourced Content", (
        BadgeColor("amber", "Third parties build content — explicit outsourcing documented (ProServ opportunity)"),
    )),
    # Build Capacity is inward-facing and hard to verify from outside
    # (GP3 research asymmetry).  Never emit this badge to mean "we
    # proved no one exists" — it means "we couldn't find public
    # evidence of content authoring roles after thorough research."
    # Label reflects the uncertainty: the absence is an information
    # gap, not a confirmed negative.  Softens the overconfident
    # "No Content Authors" label Frank flagged on Trellix.
    Badge("Build Team Unverified", (
        BadgeColor("amber", "Thorough LinkedIn / job-posting / company-page research found no public evidence of Instructional Designer / Lab Author / Tech Writer roles.  Absence of evidence, not evidence of absence — flag for discovery call."),
    )),
    Badge("Review-Only SMEs", (
        BadgeColor("amber", "SMEs mentioned only in review / accuracy-validation roles, never as authors"),
    )),
)

_build_capacity_rubric = Rubric(
    tiers=(
        RubricTier(
            "strong", 5,
            "A strong positive answer — DIY lab authoring happening today, named content dev "
            "team, Instructional Designers / Lab Authors / Tech Writers documented, a lab "
            "platform already in place (Skillable, CloudShare, Instruqt, Skytap, Kyndryl, "
            "ReadyTech, or their own DIY lab platform / VM farm), product-training partnership "
            "documented as collaborative content development. Lab infrastructure is a strong "
            "signal because it means they have the capacity to build labs, even if they aren't "
            "actively authoring today.",
        ),
        RubricTier(
            "moderate", 3,
            "A partial positive answer — SME participation in content development mentioned; "
            "named training department with some authoring signals; third-party content firm "
            "engagement; instructors with explicit dual-role authoring evidence; greenfield "
            "(no incumbent lab platform detected but also no capacity gap proven).",
        ),
        RubricTier(
            "informational", 0,
            "Context the seller should know that doesn't change the score — e.g., recent hire of "
            "a VP of Content, announced investment in a content team, a university relationship",
        ),
        RubricTier(
            "weak", 0,
            "No answer — just 'training department exists' with no creation evidence, plain instructor "
            "headcount, SMEs whose role is review only — don't emit",
        ),
    ),
    is_about=(
        "Whether the org has the CAPACITY to create technical / hands-on training content AND "
        "the infrastructure to build labs",
        "Named content dev teams, Instructional Designers, Lab Authors, Tech Writers",
        "DIY lab evidence — already building their own labs (strongest signal)",
        "Lab infrastructure in place — Skillable, CloudShare, Instruqt, Skytap, Kyndryl, "
        "ReadyTech, DIY lab platforms, owned VM farm. Having the platform means they have the "
        "capacity to build labs (Frank 2026-04-08). This used to live in Delivery Capacity "
        "erroneously — lab infrastructure is build, not delivery.",
        "Vendor-published training content on third-party platforms (e.g., Google Cloud "
        "publishing official courses on Coursera, AWS Training on LinkedIn Learning). Vendor "
        "authorship of that content is Build Capacity; the distribution channel is Delivery "
        "Capacity — cross-credit with Delivery Capacity for that specific case.",
        "Product-Training partnership documented as collaborative content development",
        "Documented content development partnerships (third-party content firms)",
        "SMEs WHEN explicitly paired with content authoring (not review-only)",
        "Research asymmetry: content authoring roles are inward-facing and hard to verify — "
        "penalize ONLY on positive evidence of outsourcing, never on absence of evidence. "
        "Lab infrastructure, however, is outward-facing and can be verified from public "
        "evidence.",
    ),
    is_not_about=(
        "Pure delivery instructors / trainers / workshop leaders (those go to Delivery Capacity)",
        "Generic 'training department' without creation evidence",
        "LMS infrastructure (Docebo, Cornerstone, other LMSes) — those deliver training to "
        "learners, they don't build labs. LMSes belong to Delivery Capacity.",
        "Authorized Training Partner programs (ATPs / ALPs) — those are how the vendor "
        "delivers training through partners. ATPs belong to Delivery Capacity (and cross-"
        "credit into Market Demand as a demand signal).",
        "Training catalog SIZE or scope (that is Training Commitment)",
        "SMEs whose role is content review or accuracy validation only",
    ),
    signal_categories=(
        # Content authoring — named roles and teams
        "diy_labs",
        "content_team_named",
        "instructional_designers",
        "lab_authors",
        "tech_writers",
        "product_training_partnership",
        "content_partnership",
        "instructor_authors_dual_role",
        "sme_content_authoring",
        # Lab infrastructure (Frank 2026-04-08 routing correction)
        "lab_build_capability",            # Skillable / CloudShare / Instruqt / DIY lab platform / owned VM farm
        # Vendor-published training on third-party platforms
        # (Google on Coursera, AWS on LinkedIn Learning, etc.) — the content
        # itself is Build; the channel is also Delivery, so this is a
        # two-credit fact.
        "vendor_published_on_third_party",
        # Negative answers (fire via RUBRIC_PENALTY_SIGNALS, cautious):
        "confirmed_outsourcing",
        "no_authoring_roles_found",
        "review_only_smes",
        # Informational context:
        "build_capacity_context",
    ),
)

_build_capacity_dimension = Dimension(
    name="Build Capacity",
    weight=20,
    question="Can they create the labs?",
    badges=_build_capacity_badges,
    rubric=_build_capacity_rubric,
    notes="Pillar 3 — rubric model. CRITICAL distinction: Build Capacity is about CREATE roles "
          "(IDs, content devs, tech writers, lab authors), NOT delivery roles (instructors, "
          "trainers). Plain instructor headcount routes to Delivery Capacity. Build Capacity only "
          "credits instructors when there's explicit dual-role authoring evidence. Weighted lowest "
          "because Skillable Professional Services or partners can fill this gap.",
)


PILLAR_CUSTOMER_FIT = Pillar(
    name="Customer Fit",
    weight=30,
    level="organization",
    question="Is this organization a good match for Skillable?",
    # Dimensions in chronological reading order (Frank, 2026-04-06):
    # Training Commitment → Build Capacity → Delivery Capacity → Organizational DNA
    # Single source of truth — code, docs, and UX rendering all read this order.
    dimensions=(
        _training_commitment_dimension,
        _build_capacity_dimension,
        _delivery_capacity_dimension,
        _organizational_dna_dimension,
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# ALL PILLARS
# ═══════════════════════════════════════════════════════════════════════════════

PILLARS: tuple[Pillar, ...] = (
    PILLAR_PRODUCT_LABABILITY,
    PILLAR_INSTRUCTIONAL_VALUE,
    PILLAR_CUSTOMER_FIT,
)

"""The 70/30 split: 70% of the Fit Score is about the product (Product Labability
+ Instructional Value). 30% is about the organization (Customer Fit). The
product is the center of everything."""


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE THRESHOLDS AND VERDICT GRID
#
# The verdict combines Fit Score and ACV Potential into a single
# action-oriented label.  It tells the seller what the opportunity looks
# like and what action makes sense — without predicting customer behavior.
# ═══════════════════════════════════════════════════════════════════════════════

SCORE_THRESHOLDS = {
    "dark_green": 80,    # >= 80
    "green": 65,         # 65-79
    "light_amber": 45,   # 45-64
    "amber": 25,         # 25-44
    "red": 0,            # < 25
}

ACV_TIERS = ("high", "medium", "low")

# Verdict grid: (score_range, acv_tier) -> VerdictDefinition
# Score ranges are defined by their minimum threshold
VERDICT_GRID: dict[tuple[int, str], VerdictDefinition] = {
    (80, "high"):   VerdictDefinition("Prime Target", "Best possible combination. Build a strategy, align the team.", "dark_green"),
    (80, "medium"): VerdictDefinition("Strong Prospect", "Great fit, meaningful opportunity. Pursue with confidence.", "dark_green"),
    (80, "low"):    VerdictDefinition("Good Fit", "The fit is real. Worth your time.", "dark_green"),
    (65, "high"):   VerdictDefinition("High Potential", "Gaps to work through but significant upside justifies the investment.", "green"),
    (65, "medium"): VerdictDefinition("Worth Pursuing", "Good fundamentals all around. Give it attention.", "green"),
    (65, "low"):    VerdictDefinition("Solid Prospect", "Decent fit, modest opportunity. Steady.", "green"),
    (45, "high"):   VerdictDefinition("Assess First", "Low fit today, but the opportunity is big. Do the homework before deciding.", "light_amber"),
    (45, "medium"): VerdictDefinition("Keep Watch", "Not ready today. Opportunity is big enough to stay close and revisit when conditions change.", "light_amber"),
    (45, "low"):    VerdictDefinition("Deprioritize", "Low fit, small opportunity. Focus elsewhere.", "light_amber"),
    (25, "high"):   VerdictDefinition("Assess First", "Low fit today, but the opportunity is big. Do the homework before deciding.", "amber"),
    (25, "medium"): VerdictDefinition("Keep Watch", "Not ready today. Opportunity is big enough to stay close and revisit when conditions change.", "amber"),
    (25, "low"):    VerdictDefinition("Deprioritize", "Low fit, small opportunity. Focus elsewhere.", "amber"),
    (0, "high"):    VerdictDefinition("Keep Watch", "Not ready today. Opportunity is big enough to stay close and revisit when conditions change.", "red"),
    (0, "medium"):  VerdictDefinition("Poor Fit", "Products don't align. Be honest about it.", "red"),
    (0, "low"):     VerdictDefinition("Poor Fit", "Products don't align. Be honest about it.", "red"),
}


# ═══════════════════════════════════════════════════════════════════════════════
# TECHNICAL FIT MULTIPLIER
#
# Applied after scoring Product Labability.  Adjusts how much weight
# downstream pillars carry based on the strength of the technical
# foundation.
# ═══════════════════════════════════════════════════════════════════════════════

TECHNICAL_FIT_MULTIPLIERS: tuple[TechnicalFitMultiplier, ...] = (
    # Full credit: strong PL, no drag on IV + CF
    TechnicalFitMultiplier(60, 100, "any", 1.0),  # magic-allowed: threshold tuned 2026-04-12
    # Datacenter protection: VM/ESX/Container products get full credit down to 32
    TechnicalFitMultiplier(32, 59, "datacenter", 1.0),  # magic-allowed: datacenter carve-out
    # Mid-range non-datacenter: meaningful drag — SaaS/cloud products with
    # uncertain provisioning (Workday PL 45 → Fit ~49, not 66)
    TechnicalFitMultiplier(32, 59, "non-datacenter", 0.65),  # magic-allowed: retuned 2026-04-12
    # Weak-but-viable: significant drag
    TechnicalFitMultiplier(19, 31, "datacenter", 0.75),  # magic-allowed: low-datacenter band
    TechnicalFitMultiplier(19, 31, "non-datacenter", 0.60),  # magic-allowed: low-non-datacenter band
    # Very weak: heavy drag
    TechnicalFitMultiplier(10, 18, "any", 0.50),  # magic-allowed: very weak PL
    TechnicalFitMultiplier(0, 9, "any", 0.35),  # magic-allowed: nearly unlabable
)

DATACENTER_METHODS = ("Hyper-V", "ESX", "Container", "Azure VM", "AWS VM", "Large VM")


# ═══════════════════════════════════════════════════════════════════════════════
# CEILING FLAGS
#
# Hard caps on Product Labability score when specific conditions are present.
# These override tier scoring — a product with a ceiling flag cannot score
# above the cap regardless of other signals.
# ═══════════════════════════════════════════════════════════════════════════════

BADGE_COLOR_POINTS: dict[str, int] = {
    # Default points per badge color, applied to dimensions that use the
    # badge-presence pattern instead of explicit scoring_signals (typically
    # the Customer Fit pillar and parts of Instructional Value).
    # Define-Once: every dimension that doesn't define its own signals reads
    # these values to convert badge color into points.
    "green": 6,
    "gray": 2,
    "amber": 0,
    "red": -3,
}

# Display severity priority — higher number = more attention-grabbing.
# Used by render-time display normalizers to pick which color "wins" when
# multiple badges with the same name need to collapse to one. NOT used for
# scoring (that's BADGE_COLOR_POINTS above) — these two concepts are
# deliberately separate per the 2026-04-06 decision-log principle that
# visual changes must never affect scoring.
BADGE_COLOR_DISPLAY_PRIORITY: dict[str, int] = {
    "red":   4,   # most attention-grabbing — risks must be visible
    "amber": 3,
    "green": 2,
    "gray":  1,
    "":      0,   # missing color sorts last
}

# Fallback used when a badge has a color value not present in either
# BADGE_COLOR_POINTS or BADGE_COLOR_DISPLAY_PRIORITY (i.e., the AI emitted
# something off-spec). Conservative: assume worse than worst-known.
BADGE_UNKNOWN_COLOR_SCORE_FALLBACK = -2


# ═══════════════════════════════════════════════════════════════════════════════
# RISK CAP REDUCTIONS — a Pillar 1 dimension can never be at full cap when
# there's a known risk. Even if the green canonical badges overflow the cap,
# an amber Risk or red Blocker should visibly reduce the dimension score so
# the user can see the friction. Per Frank's 2026-04-07 directive after
# reviewing Trellix Endpoint Security · Lab Access at 25/25 with a Training
# License Risk badge.
#
# How it works (signal_penalty model only — Pillar 1):
#   1. Compute the raw_total normally (canonical signals, penalties, color
#      contributions). Amber half-credit and red color-fallback already
#      apply at this stage.
#   2. Count visible risk badges in the dimension:
#        amber_count = badges with color "amber"
#        red_count   = badges with color "red"
#   3. Compute the knockdown:
#        knockdown = amber_count * AMBER_RISK_CAP_REDUCTION
#                  + red_count   * RED_RISK_CAP_REDUCTION
#   4. effective_cap = max(dim.weight - knockdown, dim.floor or 0)
#   5. score = min(raw_total, effective_cap)
#
# This is a CAP REDUCTION, not a deduction — if the raw is already below
# the lowered cap, there's no further effect (no double-counting with the
# half-credit / color-fallback that already applied).
#
# Linear compounding: each risk knocks more off. Two ambers = -6, three
# reds = -24, etc. Hard floor at the dimension's existing floor (0 for
# most) prevents pathological negatives.
#
# DOES NOT apply to the rubric model (Pillar 2 / Pillar 3) — strength
# tiers there already encode "moderate / weak" friction. Adding this
# knockdown would double-count.
#
# Calibration:
#   - Amber Risk: -3 from cap (~9-20% reduction depending on dim weight)
#     A dimension with one amber risk reads as "strong with friction to
#     manage" (still well above 50%).
#   - Red Blocker: -8 from cap (~23-53% reduction)
#     A dimension with one red reads as "this needs to be resolved before
#     we can ship" (mid-amber verdict territory, can't be ignored).
# ═══════════════════════════════════════════════════════════════════════════════

AMBER_RISK_CAP_REDUCTION = 3
RED_RISK_CAP_REDUCTION = 8


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING DIMENSION BREADTH CAPS — Frank 2026-04-07 ("Scoring is about OPTIONS")
#
# The Scoring dimension uses a special "Grand Slam" cap rule on top of the
# normal signal point lookup. Full marks (15/15) require AI Vision PLUS
# at least one programmatic method (Script Scoring for VM context OR
# Scoring API for cloud context). Single-method-alone caps below 15.
#
# These caps reflect Frank's mental model of what it actually takes to
# score lab work credibly:
#
#   AI Vision alone           → cap at 10
#   Scoring API alone         → cap at 12 (sparse APIs ding it; even rich
#                                          APIs alone don't earn full marks)
#   Script Scoring alone      → cap at 15 (VM context = anything goes —
#                                          you have shell access, you can
#                                          write whatever validation script
#                                          you want)
#   AI Vision + Script        → cap at 15 (Grand Slam, VM)
#   AI Vision + API           → cap at 15 (Grand Slam, cloud)
#   MCQ Scoring               → 0 (display only, anyone can do MCQs)
#
# pillar scorers() reads these to enforce
# the breadth rule when computing the Scoring dimension specifically.
# ═══════════════════════════════════════════════════════════════════════════════

SCORING_AI_VISION_ALONE_CAP = 10
SCORING_API_ALONE_CAP = 12

# Amber credit fraction for the Scoring dimension. Uncertain/partial
# scoring methods get this fraction of the green credit instead of the
# default 1/2 used by other Pillar 1 dimensions. Two uncertain methods
# at 1/3 credit each ≈ 6/15, which reads as "some potential but SE
# needs to validate" rather than the over-generous 12/15 from 1/2.
# Frank 2026-04-13: "should probably be around six out of fifteen."
SCORING_AMBER_CREDIT_FRACTION = 3  # divisor — base // 3 = one-third credit


# ═══════════════════════════════════════════════════════════════════════════════
# SANDBOX API RED PILLAR 1 CAPS — SE-4, Frank 2026-04-07
#
# When a product has no real provisioning path AND its Sandbox API badge is
# red, the entire Pillar 1 should reflect that gap. The other dimensions
# can't independently rack up points on a product that essentially can't be
# provisioned. Two cap tiers based on whether Simulation is at least viable:
#
#   Sandbox API red + Simulation viable    → Pillar 1 capped at 25
#   Sandbox API red + nothing viable       → Pillar 1 capped at  5
#
# pillar_1_scorer() reads these.
# ═══════════════════════════════════════════════════════════════════════════════

SANDBOX_API_RED_CAP_SIM_VIABLE = 25
SANDBOX_API_RED_CAP_NOTHING_VIABLE = 5


# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATION HARD OVERRIDE VALUES — Frank 2026-04-08
#
# When Simulation is the chosen fabric (last-resort fallback after VM, Cloud,
# Sandbox API, and M365 all fail), ALL FOUR Pillar 1 dimensions get HARD
# OVERRIDE values regardless of what the other facts say. The normal per-
# dimension computation is suppressed.
#
# Rationale (Frank): "If it's a sim, the product isn't really running in the
# classic sense, so the other dimensions' normal questions don't apply. You
# can't penalize teardown when there's nothing to tear down. Lab access is
# middle — learners just log into the sim. Scoring doesn't exist for sims
# yet (feature request). Provisioning, Lab Access, and Teardown are all
# treated symmetrically — fallback credit, no badges, gray bars across
# the board. No dimension gets "full credit" just because simulation
# elides it; no dimension gets rock-bottom credit just because simulation
# doesn't use it. 12 + 12 + 0 + 12 = 36 is the honest middle-ground total
# for a product with no real per-learner provisioning path.
#
# Total Simulation Pillar 1 = 12 + 12 + 0 + 12 = 36/100 (Amber).
# ═══════════════════════════════════════════════════════════════════════════════

SIMULATION_PROVISIONING_POINTS = 12    # Uniform with Lab Access / Teardown — gray bar, no badge
SIMULATION_LAB_ACCESS_POINTS = 12      # Middle of Lab Access 25 cap
SIMULATION_SCORING_POINTS = 0          # No scoring for sims today (feature request)
SIMULATION_TEARDOWN_POINTS = 12        # Uniform with Lab Access / Provisioning — gray bar, no badge


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-FABRIC OPTIONALITY BONUS — Frank 2026-04-08
#
# When a product has MULTIPLE viable Pillar 1 Provisioning fabrics (e.g., a
# product that runs in Hyper-V AND on Azure as a cloud-native service), the
# primary fabric's base credit is credited normally, PLUS an optionality bonus
# for each additional viable secondary fabric. Reflects Frank's insight that
# multi-fabric products give lab developers more design choices and enable
# more lab types (cross-pillar with Pillar 2 Lab Versatility).
#
# Rules:
#   - Simulation does NOT count as a secondary fabric (it's a fallback)
#   - Partial-granularity Sandbox API does NOT count (too weak to count)
#   - Container with disqualifiers does NOT count
#   - Bonus caps at MULTI_FABRIC_OPTIONALITY_BONUS_CAP (diminishing returns)
# ═══════════════════════════════════════════════════════════════════════════════

MULTI_FABRIC_OPTIONALITY_BONUS_PER_EXTRA = 3
MULTI_FABRIC_OPTIONALITY_BONUS_CAP = 6


# ═══════════════════════════════════════════════════════════════════════════════
# M365 SCENARIO FABRIC POINTS — Frank 2026-04-08
#
# M365 is a first-class Provisioning fabric in Skillable (peer to Hyper-V /
# Cloud Slice / Sandbox API / Simulation). Two distinct scenarios with
# different friction profiles:
#
#   End User (automated Skillable-owned tenants, low friction):  25 points
#   Administration (MOC or trial tenant, higher friction):        18 points
#
# When m365_scenario is set, the scorer picks M365 as the primary fabric
# BEFORE walking the VM/Cloud/Sandbox priority order. Training License in
# Lab Access separately fires amber for both scenarios (SE has real licensing
# design questions regardless of scenario — tier, concurrent user count,
# add-ons, identity verification).
# ═══════════════════════════════════════════════════════════════════════════════

M365_TENANT_POINTS = 25                # End User scenario — automated lane
M365_ADMIN_POINTS = 18                 # Administration scenario — trial/MOC path


# CEILING_FLAGS deleted 2026-04-08 (Step 5b rebuild cleanup).
#
# The old AI-emitted ceiling flag mechanism (bare_metal_required, saas_only,
# no_api_automation, multi_tenant_only) has been fully replaced by the new
# Score layer:
#
#   - bare_metal_required → pillar_1_scorer raises its own score_override
#     when facts indicate physical-hardware requirement (same effective cap)
#   - saas_only / multi_tenant_only → the Sandbox API canonical badge drives
#     the Pillar 1 cap when there's no per-learner provisioning API
#   - no_api_automation → structurally replaced by risk cap reduction on the
#     red Sandbox API finding (-8 per red knocks the pillar cap down)
#
# Nothing in the new Python path reads CEILING_FLAGS. The three Pillar
# scorers produce authoritative PillarScore objects; fit_score_composer
# handles the Technical Fit Multiplier coupling. Score reads facts, not
# ceiling-flag strings.


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY PRIORS
#
# Product categories and their default demand ratings.
#
# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  RELATIONSHIP TO IV_CATEGORY_BASELINES — read this before editing     ║
# ╠═══════════════════════════════════════════════════════════════════════╣
# ║                                                                       ║
# ║  CATEGORY_PRIORS has a DIFFERENT purpose than IV_CATEGORY_BASELINES:  ║
# ║                                                                       ║
# ║    CATEGORY_PRIORS → Market Demand ACV RATE PRIORS                    ║
# ║      The `points` field (8 / 4 / 0) is a rough demand hint fed to     ║
# ║      the AI prompt via the {CATEGORY_PRIORS} placeholder.  It         ║
# ║      guides the AI's per-motion population / adoption estimates       ║
# ║      for the ACV calculation.  It does NOT drive the scoring math.   ║
# ║                                                                       ║
# ║    IV_CATEGORY_BASELINES → SCORING MATH BASELINES                     ║
# ║      Per-dimension baselines (Product Complexity, Mastery Stakes,     ║
# ║      Lab Versatility, Market Demand) applied by the Python pillar scorers       ║
# ║      BEFORE the AI's findings are added.  This is the default-        ║
# ║      positive posture Frank directed on 2026-04-07.                   ║
# ║                                                                       ║
# ║  Market Demand shows up in BOTH structures, at different scales:     ║
# ║    - CATEGORY_PRIORS: 0 / 4 / 8 (demand hint for ACV consumption)     ║
# ║    - IV_CATEGORY_BASELINES.market_demand: 0-17 (scoring baseline)     ║
# ║                                                                       ║
# ║  When you add or rename a category, update BOTH structures.  The      ║
# ║  category names should stay in sync.                                  ║
# ╚═══════════════════════════════════════════════════════════════════════╝
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORY_PRIORS: tuple[CategoryPrior, ...] = (
    # High demand (+8) — large global specialist populations, active cert ecosystems
    CategoryPrior("Cybersecurity", 8, "high"),
    CategoryPrior("Cloud Infrastructure", 8, "high"),
    CategoryPrior("Networking/SDN", 8, "high"),
    CategoryPrior("Data Science & Engineering", 8, "high"),
    CategoryPrior("Data & Analytics", 8, "high"),
    CategoryPrior("DevOps", 8, "high"),
    CategoryPrior("AI Platforms & Tooling", 8, "high"),
    # Moderate demand (+4)
    CategoryPrior("Data Protection", 4, "moderate"),
    CategoryPrior("Infrastructure/Virtualization", 4, "moderate"),
    CategoryPrior("App Development", 4, "moderate"),
    CategoryPrior("ERP", 4, "moderate"),
    CategoryPrior("CRM", 4, "moderate"),
    CategoryPrior("Healthcare IT", 4, "moderate"),
    CategoryPrior("FinTech", 4, "moderate"),
    CategoryPrior("Collaboration", 4, "moderate"),
    CategoryPrior("Content Management", 4, "moderate"),
    CategoryPrior("Legal Tech", 4, "moderate"),
    CategoryPrior("Industrial/OT", 4, "moderate"),
    # Low demand (+0) — no professional training market
    CategoryPrior("Social / Entertainment", 0, "low"),
)


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER TRAINING ADOPTION BY CATEGORY TIER — Software / Enterprise Software
#
# Motion 1 (Customer Training & Enablement) adoption rate, keyed on the
# CATEGORY_PRIORS tier of the product's category. Specialist categories
# with career-gated training (cybersecurity, cloud infra, networking)
# have ~2× the formal-training uptake of general-purpose categories
# (collaboration, CRM end-user). Flat 4% systematically undercount the
# specialist categories that are Skillable's strongest fit.
#
# Applies ONLY to Software and Enterprise Software org types. Wrapper
# orgs (Academic, ILT, ELP, GSI/VAR/Distributor) keep their existing
# org-level overrides in ACV_ORG_ADOPTION_OVERRIDES because their
# adoption dynamics come from delivery model, not product category.
#
# Per Platform-Foundation → "Customer Training adoption by category
# tier". Frank 2026-04-13.
# ═══════════════════════════════════════════════════════════════════════════════

CUSTOMER_TRAINING_ADOPTION_BY_TIER: dict[str, float] = {
    "high": 0.08,     # specialist categories — Nutanix, Cisco, Splunk
    "moderate": 0.04, # general-purpose enterprise — same as old flat baseline
    "low": 0.01,      # consumer / no professional training market
}
# Fallback when the product's category is unknown / unclassified.
# Treat as Moderate — a conservative middle.
CUSTOMER_TRAINING_ADOPTION_TIER_DEFAULT = 0.04

# Org types that USE the category-tier Motion 1 adoption.
# Other org types use ACV_ORG_ADOPTION_OVERRIDES (wrapper orgs) or the
# motion's default (anything else).
CATEGORY_TIER_ELIGIBLE_ORG_TYPES = frozenset({
    "SOFTWARE", "ENTERPRISE SOFTWARE",
})


def _build_category_to_tier_map() -> dict[str, str]:
    """Build {category_name: tier_label} from CATEGORY_PRIORS.

    Used by acv_calculator to look up a product's tier from its category.
    Define-Once: CATEGORY_PRIORS is the source of truth; this map is
    derived, not duplicated.
    """
    return {prior.category: prior.demand_level for prior in CATEGORY_PRIORS}


# Eager build — CATEGORY_PRIORS is immutable at module load time.
CATEGORY_TO_TIER: dict[str, str] = _build_category_to_tier_map()


def get_customer_training_adoption_for_category(category: str | None) -> float:
    """Return the Motion 1 adoption rate for a product's category.

    Reads CATEGORY_TO_TIER (derived from CATEGORY_PRIORS) and looks up
    the rate in CUSTOMER_TRAINING_ADOPTION_BY_TIER. Falls back to the
    default when the category is empty, None, or not in the map.
    """
    if not category:
        return CUSTOMER_TRAINING_ADOPTION_TIER_DEFAULT
    tier = CATEGORY_TO_TIER.get(category)
    if not tier:
        return CUSTOMER_TRAINING_ADOPTION_TIER_DEFAULT
    return CUSTOMER_TRAINING_ADOPTION_BY_TIER.get(
        tier, CUSTOMER_TRAINING_ADOPTION_TIER_DEFAULT)

# ═══════════════════════════════════════════════════════════════════════════════
# UNKNOWN CLASSIFICATION — canonical fallback label
#
# Single source of truth for the "Unknown" fallback used in both IV category
# baselines and CF organization-type baselines.  Every module that needs to
# reference the Unknown fallback reads this constant — NO hardcoded "Unknown"
# literal anywhere else in the codebase.  Define-Once.
#
# When the discovery phase fails to classify a product's category or a
# company's organization type, the scoring context falls back to this label.
# The math layer applies a neutral baseline for Unknown and sets
# `classification_review_needed = True` on the product result so the dossier
# UX surfaces a "Review Classification" flag for human follow-up.
# ═══════════════════════════════════════════════════════════════════════════════

UNKNOWN_CLASSIFICATION = "Unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 2 / INSTRUCTIONAL VALUE — CATEGORY-AWARE BASELINES
#
# Each IV dimension starts from a baseline derived from the product's
# top-level category.  Findings move the score up (positive signals) or down
# (explicit negatives like `Consumer Grade`).  Missing evidence means
# baseline, not zero.  Default-positive posture.
#
# Baseline values are in dimension-native units (Product Complexity cap 40,
# Mastery Stakes cap 25, Lab Versatility cap 15, Market Demand cap 20).
#
# Per Frank's calibration 2026-04-07, retuned 2026-04-13 to fix the
# differentiation problem: baselines were too close to caps (Lab Versatility
# at 93%, Mastery Stakes at 88%), leaving no room for grader findings to
# differentiate strong from weak products within a category.
#
# Design principle: baselines represent a WEAK implementation of the
# category — the starting point for a product that has category membership
# but no standout signals. The grader's findings earn the score FROM
# baseline TO cap. Two strong findings should reach the cap; baseline
# alone should be mid-range (50-65% of cap), not near-cap.
#
# Target differentiation bands:
#   Product Complexity (cap 40): ~12 point gap → baseline 26-28
#   Mastery Stakes (cap 25):     ~10 point gap → baseline 14-16
#   Lab Versatility (cap 15):    ~6 point gap  → baseline 8-10
#   Market Demand (cap 20):      ~8 point gap  → baseline 10-12
#
# Canonical source: docs/Badging-and-Scoring-Reference.md Pillar 2 sections.
# ═══════════════════════════════════════════════════════════════════════════════

# Shape: category_name -> {dimension_key: baseline}
# The UNKNOWN_CLASSIFICATION constant is used as the fallback dict key so
# callers reference the canonical label without re-typing the literal.
IV_CATEGORY_BASELINES: dict[str, dict[str, int]] = {
    # Top tier — technical / specialist categories with deep multi-system work
    "Cybersecurity": {"product_complexity": 28, "mastery_stakes": 16, "lab_versatility": 10, "market_demand": 12},
    "Cloud Infrastructure": {"product_complexity": 28, "mastery_stakes": 15, "lab_versatility": 10, "market_demand": 12},
    "Networking/SDN": {"product_complexity": 28, "mastery_stakes": 15, "lab_versatility": 10, "market_demand": 11},
    "Data Science & Engineering": {"product_complexity": 28, "mastery_stakes": 16, "lab_versatility": 9, "market_demand": 10},
    "Data & Analytics": {"product_complexity": 26, "mastery_stakes": 13, "lab_versatility": 8, "market_demand": 9},
    "DevOps": {"product_complexity": 28, "mastery_stakes": 15, "lab_versatility": 10, "market_demand": 11},
    "AI Platforms & Tooling": {"product_complexity": 28, "mastery_stakes": 16, "lab_versatility": 10, "market_demand": 12},

    # Very high
    "Data Protection": {"product_complexity": 26, "mastery_stakes": 15, "lab_versatility": 8, "market_demand": 8},

    # High — enterprise business systems with real depth and stakes
    "ERP": {"product_complexity": 24, "mastery_stakes": 15, "lab_versatility": 8, "market_demand": 8},
    "CRM": {"product_complexity": 22, "mastery_stakes": 12, "lab_versatility": 7, "market_demand": 7},
    "Healthcare IT": {"product_complexity": 24, "mastery_stakes": 16, "lab_versatility": 8, "market_demand": 8},
    "FinTech": {"product_complexity": 24, "mastery_stakes": 16, "lab_versatility": 8, "market_demand": 8},
    "Legal Tech": {"product_complexity": 22, "mastery_stakes": 16, "lab_versatility": 7, "market_demand": 7},
    "Industrial/OT": {"product_complexity": 24, "mastery_stakes": 15, "lab_versatility": 8, "market_demand": 8},
    "Infrastructure/Virtualization": {"product_complexity": 24, "mastery_stakes": 15, "lab_versatility": 8, "market_demand": 8},
    "App Development": {"product_complexity": 22, "mastery_stakes": 10, "lab_versatility": 8, "market_demand": 9},

    # Moderate — collaboration and content with real but bounded depth
    "Collaboration": {"product_complexity": 18, "mastery_stakes": 10, "lab_versatility": 7, "market_demand": 6},
    "Content Management": {"product_complexity": 18, "mastery_stakes": 10, "lab_versatility": 7, "market_demand": 6},

    # No professional training market
    "Social / Entertainment": {"product_complexity": 4, "mastery_stakes": 2, "lab_versatility": 1, "market_demand": 0},

    # Neutral fallback — flagged for classification review in UX.
    # Keyed by the canonical UNKNOWN_CLASSIFICATION constant (Define-Once).
    UNKNOWN_CLASSIFICATION: {"product_complexity": 18, "mastery_stakes": 10, "lab_versatility": 7, "market_demand": 7},
}


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 3 / CUSTOMER FIT — ORGANIZATION-TYPE BASELINES
#
# Each CF dimension starts from a baseline derived from the organization's
# type, identified during discovery via the company classification.  Positive
# findings raise the score; negative findings (penalties) lower it.  Missing
# evidence means baseline.
#
# Baseline values are in dimension-native units (Training Commitment cap 25,
# Build Capacity cap 20, Delivery Capacity cap 30, Organizational DNA cap 25).
#
# Research asymmetry:
#   - Delivery Capacity is outward-facing, easy to verify, penalize aggressively
#   - Build Capacity is inward-facing, hard to verify, penalize cautiously
#     (only on positive evidence of outsourcing, not on absence of evidence)
#   - Training Commitment and Organizational DNA fall in between
#
# Per Frank's calibration 2026-04-07:
#   - TRAINING ORG near-max on commitment, strong on delivery
#   - ACADEMIC and CONTENT DEVELOPMENT top tier on commitment
#   - LMS PROVIDER lower on commitment (they host, not teach themselves)
#   - TECH DISTRIBUTOR lowest on commitment (historically weak at training)
#   - Build Capacity baselines cluster in the middle (hard to verify)
#   - Delivery Capacity baselines lean higher (start higher, penalize absence)
#   - Organizational DNA baselines lean higher (most orgs partner in some form)
#
# Canonical source: docs/Badging-and-Scoring-Reference.md Pillar 3 sections.
# ═══════════════════════════════════════════════════════════════════════════════

# Maps the AI-emitted organization_type strings (lowercase snake_case) to
# the CF_ORG_BASELINES keys (uppercase human-readable).  The AI output
# format comes from the discovery-phase classification (researcher.py);
# the baselines use the format that renders cleanly in docs and the
# dossier UX.  This is the Define-Once seam — every caller normalizes
# via this dict.
# UNKNOWN_CLASSIFICATION is defined at the top of the baselines section
# (before IV_CATEGORY_BASELINES) so both baseline dicts can reference it
# as a dict key.  Single source of truth — see that definition for full docs.

ORG_TYPE_NORMALIZATION: dict[str, str] = {
    "software_company": "SOFTWARE",
    "enterprise_software": "ENTERPRISE SOFTWARE",
    "training_organization": "TRAINING ORG",
    "academic_institution": "ACADEMIC",
    "systems_integrator": "SYSTEMS INTEGRATOR",
    "technology_distributor": "TECH DISTRIBUTOR",
    "professional_services": "PROFESSIONAL SERVICES",
    "content_development": "CONTENT DEVELOPMENT",
    "lms_company": "LMS PROVIDER",
    "lms_provider": "LMS PROVIDER",
    "industry_authority": "INDUSTRY AUTHORITY",
    "ilt_training_org": "ILT TRAINING ORG",
    "ilt_training_organization": "ILT TRAINING ORG",
    "enterprise_learning_platform": "LMS PROVIDER",
}


def build_scoring_context(raw_org_type: str | None, raw_product_category: str | None) -> dict:
    """Build the scoring context dict used by `fit_score_composer.compose_fit_score`.

    Normalizes raw AI-emitted values into the canonical baseline lookup keys.
    Missing or unrecognized values fall back to `UNKNOWN_CLASSIFICATION`,
    which both applies the neutral fallback baseline and raises the
    classification review flag.

    This is the Define-Once seam for scoring context construction — both
    `scorer._parse_product` (direct AI output path) and
    `intelligence.recompute_analysis` (cached analysis path) MUST use this
    helper so the two scoring paths produce identical context dicts.

    Args:
        raw_org_type: AI-emitted organization_type string (e.g., "software_company")
                      or None.  Normalized via ORG_TYPE_NORMALIZATION.
        raw_product_category: AI-emitted product_category string (e.g.,
                              "Cybersecurity") or None.  Kept as-is (the
                              master category list uses human-readable
                              casing).

    Returns:
        A dict with shape:
          {"product_category": str, "org_type": str}
        Both fields are always populated — UNKNOWN_CLASSIFICATION is used
        as the fallback.  No hardcoded literals.
    """
    category = (raw_product_category or "").strip() or UNKNOWN_CLASSIFICATION

    normalized_org = ORG_TYPE_NORMALIZATION.get(
        (raw_org_type or "").strip().lower(), ""
    ) or UNKNOWN_CLASSIFICATION

    return {
        "product_category": category,
        "org_type": normalized_org,
    }


# Shape: org_type -> {dimension_key: baseline}
# Recalibrated 2026-04-13 — same principle as IV baselines: baselines represent
# a WEAK implementation of each org type. The grader's findings earn the score
# from baseline to cap. Two strong findings should reach the cap.
# Target: ~55-70% of cap for top-tier orgs, proportionally lower for others.
# Caps: TC=25, BC=20, DC=30, DNA=25.
CF_ORG_BASELINES: dict[str, dict[str, int]] = {
    "TRAINING ORG": {"training_commitment": 17, "build_capacity": 12, "delivery_capacity": 18, "organizational_dna": 15},
    "ACADEMIC": {"training_commitment": 16, "build_capacity": 11, "delivery_capacity": 14, "organizational_dna": 13},
    "CONTENT DEVELOPMENT": {"training_commitment": 16, "build_capacity": 13, "delivery_capacity": 12, "organizational_dna": 15},
    "ENTERPRISE SOFTWARE": {"training_commitment": 14, "build_capacity": 10, "delivery_capacity": 17, "organizational_dna": 14},
    "PROFESSIONAL SERVICES": {"training_commitment": 14, "build_capacity": 11, "delivery_capacity": 15, "organizational_dna": 14},
    "SOFTWARE": {"training_commitment": 12, "build_capacity": 9, "delivery_capacity": 14, "organizational_dna": 13},
    "SYSTEMS INTEGRATOR": {"training_commitment": 12, "build_capacity": 10, "delivery_capacity": 16, "organizational_dna": 14},
    "LMS PROVIDER": {"training_commitment": 9, "build_capacity": 8, "delivery_capacity": 18, "organizational_dna": 13},
    "TECH DISTRIBUTOR": {"training_commitment": 7, "build_capacity": 8, "delivery_capacity": 17, "organizational_dna": 13},
    # Keyed by the canonical UNKNOWN_CLASSIFICATION constant (Define-Once).
    UNKNOWN_CLASSIFICATION: {"training_commitment": 10, "build_capacity": 9, "delivery_capacity": 14, "organizational_dna": 12},
}


# ═══════════════════════════════════════════════════════════════════════════════
# PENALTY SIGNAL CATEGORIES — PILLAR 3 CUSTOMER FIT
#
# Customer Fit is diagnosed as much by what's missing as by what's present.
# These penalty signal categories define the negative findings the AI can
# emit for each CF dimension.  The scoring math applies the hit as a
# subtraction from (baseline + positive findings), flooring at 0.
#
# Research asymmetry is encoded here: Delivery Capacity penalties fire
# aggressively on absence of evidence; Build Capacity penalties fire only on
# positive evidence of outsourcing.  The prompt template teaches the AI this
# distinction explicitly.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PenaltySignal:
    """A negative finding category for any rubric-model dimension (Pillar 2 + Pillar 3).

    The AI emits these when it finds positive evidence of a negative
    condition (e.g., confirmed outsourcing) or, for outward-facing
    dimensions, when research fails to find evidence that should exist
    (e.g., no partner network for a scaled software vendor, no independent
    training market for a supposedly in-demand product).

    Lookup is keyed by ``(dimension, signal_category)`` so the same
    signal_category can fire in multiple dimensions with different weights —
    for example, ``no_independent_training_market`` is a strong penalty in
    Delivery Capacity (vendor failed to build partner reach) AND an amber
    penalty in Market Demand (the open market doesn't see enough demand to
    invest in training).  Cross-pillar compounding is deliberate; the AI is
    taught to emit the same badge in both dimensions when the evidence
    supports it.
    """
    category: str        # signal_category key (e.g., "no_training_partners")
    dimension: str       # dimension key (e.g., "delivery_capacity")
    color: str           # "amber" or "red"
    hit: int             # Points subtracted (positive integer — the math layer negates)
    badge_name: str      # Finding-as-name badge label shown to the user
    description: str     # Plain-English description of when this fires


# Delivery Capacity penalties — outward-facing, penalize aggressively on absence
DELIVERY_CAPACITY_PENALTIES: tuple[PenaltySignal, ...] = (
    PenaltySignal(
        "no_training_partners", "delivery_capacity", "red", 10, "No Training Partners",
        "Software vendor with zero ATP / reseller / channel training network where partners should exist. Hard signal the vendor hasn't invested in delivery.",
    ),
    PenaltySignal(
        "no_classroom_delivery", "delivery_capacity", "red", 10, "No Classroom Delivery",
        "Zero evidence of instructor-led training, bootcamps, workshops, or a published course calendar. Nobody teaches the product.",
    ),
    PenaltySignal(
        "single_region_only", "delivery_capacity", "amber", 3, "Single-Region Reach",
        "Delivery presence limited to one state or country. Real ceiling on reach.",
    ),
    # Frank 2026-04-08 routing correction: `no_independent_training_market`
    # and `gray_market_only` moved to MARKET_DEMAND_PENALTIES only. Both
    # signals are about the market not showing up for the product, which
    # is a demand concern, not a delivery concern.
)

# Build Capacity penalties — inward-facing, penalize CAUTIOUSLY (positive evidence only)
BUILD_CAPACITY_PENALTIES: tuple[PenaltySignal, ...] = (
    PenaltySignal(
        "confirmed_outsourcing", "build_capacity", "amber", 3, "Outsourced Content",
        "Research finds explicit statements or case studies documenting that the organization buys off-the-shelf content (Pluralsight, Udemy, generic e-learning vendors) and has no internal authoring mandate. Only fires on positive evidence of outsourcing.",
    ),
    PenaltySignal(
        "no_authoring_roles_found", "build_capacity", "amber", 3, "Build Team Unverified",
        "After thorough LinkedIn/job-posting/company-page research, zero evidence of Instructional Designer, Curriculum Developer, Lab Author, or Tech Writer roles. Combined with explicit buying language.",
    ),
    PenaltySignal(
        "review_only_smes", "build_capacity", "amber", 2, "Review-Only SMEs",
        "SMEs mentioned only in review / accuracy-validation roles, never as authors.",
    ),
)

# Training Commitment penalties
TRAINING_COMMITMENT_PENALTIES: tuple[PenaltySignal, ...] = (
    PenaltySignal(
        "no_customer_training", "training_commitment", "amber", 4, "No Customer Training",
        "Research finds zero evidence of training offered to customers — no customer courses, no enablement programs, no cert paths, no published training calendar for external learners.",
    ),
    PenaltySignal(
        "thin_cert_program", "training_commitment", "amber", 3, "Thin Cert Program",
        "Certification program is absent or present only as one or two nominal offerings with no tested exam pass rates or career value.",
    ),
    PenaltySignal(
        "no_customer_success_team", "training_commitment", "amber", 3, "No Customer Success Team",
        "No named customer success, customer enablement, or customer onboarding team. Training is not organizationally owned.",
    ),
    PenaltySignal(
        "minimal_training_language", "training_commitment", "amber", 2, "Training Not Prioritized",
        "Vendor website, marketing, and investor materials barely mention training, enablement, certification, or customer success.",
    ),
)

# Organizational DNA penalties
ORGANIZATIONAL_DNA_PENALTIES: tuple[PenaltySignal, ...] = (
    PenaltySignal(
        "long_rfp_process", "organizational_dna", "amber", 4, "Long RFP Process",
        "Documented 9+ month vendor engagement cycles, exhaustive RFP committees, multiple approval gates. Direct evidence from press, case studies, or vendor complaints.",
    ),
    PenaltySignal(
        "heavy_procurement", "organizational_dna", "amber", 3, "Heavy Procurement",
        "Large vendor management bureaucracy; vendors treated as cost centers to extract value from rather than strategic relationships.",
    ),
    PenaltySignal(
        "build_everything_culture", "organizational_dna", "amber", 4, "Builds Everything",
        "Explicit 'we build it ourselves' posture documented (IBM pattern). Outside platforms treated as inferior by default.",
    ),
    PenaltySignal(
        "closed_platform_culture", "organizational_dna", "amber", 3, "Closed Platform",
        "Proprietary everything — no public APIs, no ecosystem investment, no developer community.",
    ),
    PenaltySignal(
        "hard_to_engage", "organizational_dna", "red", 6, "Hard to Engage",
        "Documented hostility or legendary bureaucratic slowness toward outside partners. Direct evidence required.",
    ),
)

# ─── Pillar 2 (Instructional Value) penalties ──────────────────────────────

# Market Demand penalties — penalize when the open training market has NOT
# invested in this product.  Independent courses, install base size, and
# category breadth are the three evidence anchors.
#
# Research asymmetry: Market Demand is outward-facing (public course
# catalogs, analyst reports, install-base claims) — penalize aggressively
# on absence of public evidence, just like Delivery Capacity.
#
# Frank 2026-04-08 routing correction: `no_independent_training_market`
# used to be cross-pillar with Delivery Capacity. It is now Market Demand
# ONLY — independent third-party courses on Coursera / Pluralsight /
# LinkedIn Learning / Udemy are a demand signal (who teaches this
# independently?), not a delivery signal (vendor's apparatus for reaching
# learners). See docs/next-session-todo.md §0b lock-in #5.
MARKET_DEMAND_PENALTIES: tuple[PenaltySignal, ...] = (
    PenaltySignal(
        "no_independent_training_market", "market_demand", "amber", 4, "No Independent Training",
        "Fewer than 3 courses found on Coursera / Pluralsight / LinkedIn Learning / Udemy / Skillsoft combined where the publisher is NOT the vendor. The open training market hasn't invested independently — a real demand red flag even when the product is in a 'hot' category. Market Demand only (Frank 2026-04-08 routing correction).",
    ),
    PenaltySignal(
        "small_install_base", "market_demand", "amber", 3, "Small Install Base",
        "Public evidence of a small or undocumented customer footprint (< ~1K users / tens of logos / no press) for a product in a supposedly hot category. Specialist niche, not broad demand.",
    ),
    PenaltySignal(
        "niche_within_category", "market_demand", "amber", 3, "Niche Within Category",
        "Product sits inside a high-demand category but is itself a narrow specialty used by a small population (e.g., a specific threat intelligence feed inside the broader cybersecurity market). The category is hot; this product is not.",
    ),
)

# All rubric-model penalty signals (Pillar 2 + Pillar 3), consolidated for
# easy lookup.  The math layer builds a ``(dimension, signal_category) ->
# PenaltySignal`` dict from this list.  Adding a new penalty = append to the
# appropriate dimension tuple and extend this concatenation.
RUBRIC_PENALTY_SIGNALS: tuple[PenaltySignal, ...] = (
    # Pillar 2 — Instructional Value
    MARKET_DEMAND_PENALTIES
    # Pillar 3 — Customer Fit
    + DELIVERY_CAPACITY_PENALTIES
    + BUILD_CAPACITY_PENALTIES
    + TRAINING_COMMITMENT_PENALTIES
    + ORGANIZATIONAL_DNA_PENALTIES
)




# ═══════════════════════════════════════════════════════════════════════════════
# LAB TYPE MENU
#
# High-value lab types for the Lab Versatility dimension.  The AI picks
# 1-2 per product based on specific product research.  These serve dual
# purpose: conversational competence in Inspector, program recommendations
# in Designer.
# ═══════════════════════════════════════════════════════════════════════════════

LAB_TYPE_MENU: tuple[LabType, ...] = (
    LabType("Red vs Blue", "Adversarial team scenarios", "Cybersecurity — EDR, SIEM, network security"),
    LabType("Simulated Attack", "Realistic attack, learner responds", "Cybersecurity — any defensive product"),
    LabType("Incident Response", "Production down, diagnose under pressure", "Infrastructure, security, cloud, databases"),
    LabType("Break/Fix", "Something's broken, figure it out", "Broad — any product with complex failure modes"),
    LabType("Team Handoff", "Multi-person sequential workflow", "DevOps, data engineering, SDLC"),
    LabType("Bug Bounty", "Find the flaws — competitive discovery", "Development platforms, data, security"),
    LabType("Cyber Range", "Full realistic network, live threats", "Network security, SOC operations"),
    LabType("Performance Tuning", "System works but needs optimization", "Databases, infrastructure, cloud, data"),
    LabType("Migration Lab", "Move from A to B", "Enterprise software, cloud, infrastructure"),
    LabType("Architecture Challenge", "Design and build from requirements", "Cloud, infrastructure, networking, data"),
    LabType("Compliance Audit", "Validate configurations against regulations", "Healthcare, finance, security, regulated industries"),
    LabType("Disaster Recovery", "Systems failed, recover operations", "Infrastructure, cloud, data protection"),
)


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL LAB PLATFORM LIST
#
# One list, referenced everywhere — company-level research, product-level
# research, discovery extraction, badging framework.  When a new competitor
# is identified, add it once here and it propagates to all consumers.
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_LAB_PLATFORMS: tuple[str, ...] = (
    # Skillable (and legacy brands)
    "Skillable",
    "Learn on Demand Systems",
    "labondemand.com",
    "learnondemandsystems.com",
    # Direct competitors
    "Kyndryl / Skytap",
    "CloudShare",
    "Instruqt",
    "Appsembler",
    "GoDeploy",
    "Vocareum",
    "ReadyTech",
    # Cybersecurity-focused platforms
    "Immersive Labs",
    "Hack The Box",
    "TryHackMe",
    "ACI Learning",
    # DIY signal
    "DIY",
)


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL LMS PARTNER LIST
#
# LMS and LXP platforms that matter for integration assessment.  Skillable
# partner LMS platforms are flagged — they represent a proven integration
# path and faster time to delivery.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LMSPartner:
    """An LMS/LXP platform with its Skillable partnership status."""
    name: str
    is_skillable_partner: bool
    notes: str = ""


CANONICAL_LMS_PARTNERS: tuple[LMSPartner, ...] = (
    LMSPartner("Docebo", True, "Tight Skillable LMS partner — pre-built connector, proven path"),
    LMSPartner("Cornerstone", True, "Tight Skillable LMS partner — pre-built connector, proven path"),
    LMSPartner("Skillable TMS", True, "Skillable's native LMS — best when vendor has no existing platform"),
    LMSPartner("Moodle", False, "Open source LMS — widely used in education"),
    LMSPartner("Canvas", False, "Instructure LMS — common in higher education"),
    LMSPartner("Blackboard", False, "Higher education LMS"),
    LMSPartner("Brightspace (D2L)", False, "Higher education and corporate LMS"),
    LMSPartner("NetExam", False, "Channel/partner enablement LMS"),
    LMSPartner("SAP SuccessFactors Learning", False, "Enterprise HCM LMS"),
    LMSPartner("Workday Learning", False, "Enterprise HCM LMS"),
    LMSPartner("Absorb LMS", False, "Mid-market corporate LMS"),
    LMSPartner("TalentLMS", False, "SMB-focused LMS"),
    LMSPartner("Litmos", False, "Corporate LMS"),
    LMSPartner("360Learning", False, "Collaborative learning platform"),
    LMSPartner("Thought Industries", False, "External training / customer education platform"),
    LMSPartner("Skilljar", False, "Customer education platform"),
    LMSPartner("LearnUpon", False, "Corporate and partner training LMS"),
)

# LMS integration paths in priority order
LMS_INTEGRATION_PRIORITY = (
    "LTI 1.3",        # Best choice when LMS is LTI 1.3 compliant
    "API integration", # Maximum flexibility, works regardless of LMS
    "Skillable TMS",   # When vendor has no existing delivery platform
    "Custom Connector", # For tight system coupling without LTI/API
    "SCORM",           # Legacy standard — speed of deployment only
)


# ═══════════════════════════════════════════════════════════════════════════════
# EXAM DELIVERY PROVIDERS
#
# Confirmed Skillable EDP integrations.  When any of these appears in
# research, it removes what would otherwise look like an integration risk
# and elevates the certification motion confidence.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExamDeliveryProvider:
    """An exam delivery provider with Skillable integration status."""
    name: str
    is_confirmed: bool
    notes: str


EXAM_DELIVERY_PROVIDERS: tuple[ExamDeliveryProvider, ...] = (
    ExamDeliveryProvider("Pearson VUE", True,
        "Microsoft all exams, CompTIA, SANS/GIAC, EC-Council, CREST — major Skillable partner"),
    ExamDeliveryProvider("Certiport", True,
        "Pearson company — tight Skillable integration; entry-level IT: MOS, IC3, Adobe, Autodesk"),
    ExamDeliveryProvider("PSI", True, "ISACA"),
    ExamDeliveryProvider("Certiverse", True, "NVIDIA — fast-growing EDP, increasingly common"),
)


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL ORGANIZATION TYPES
#
# Every organization that Skillable evaluates falls into one of these types.
# The type determines how you find the products and how you approach the
# conversation.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class OrganizationType:
    """An organization type with its relationship to products."""
    type_key: str
    display_label: str
    relationship_to_products: str
    how_to_find_products: str


ORGANIZATION_TYPES: tuple[OrganizationType, ...] = (
    OrganizationType("software_company", "SOFTWARE",
        "They create the software products",
        "Product pages, documentation, API docs"),
    OrganizationType("training_organization", "TRAINING ORG",
        "Their products are training courses and certifications",
        "Course catalogs — extract the underlying technologies taught"),
    OrganizationType("academic_institution", "ACADEMIC",
        "Their courses and degrees cover technologies",
        "Published curriculum"),
    OrganizationType("systems_integrator", "SYSTEMS INTEGRATOR",
        "They implement and deploy other companies' products",
        "Client engagements — what technologies are involved"),
    OrganizationType("technology_distributor", "TECH DISTRIBUTOR",
        "They sell and resell products and build training",
        "Training catalogs and distribution portfolio"),
    OrganizationType("professional_services", "PROFESSIONAL SERVICES",
        "They build learning programs around other companies' products",
        "Their program portfolio"),
    OrganizationType("content_development", "CONTENT DEVELOPMENT",
        "They build learning programs around other companies' products",
        "Their program portfolio"),
    OrganizationType("lms_company", "LMS PROVIDER",
        "They host and deliver learning programs",
        "Their customers' products"),
)


# ═══════════════════════════════════════════════════════════════════════════════
# ACV RATE TABLES AND CONSUMPTION MOTIONS
#
# ACV Potential is calculated, not scored.  It is the estimated annual
# contract value if a customer standardized on Skillable for all training
# and enablement motions.
#
# ACV = Population x Adoption Rate x Hours per Learner x Rate
# ═══════════════════════════════════════════════════════════════════════════════

#  Frank's four named price variables — single source of truth for every
#  $/hour the platform quotes. Tweaking a rate is a one-line edit; no
#  rescore needed because Python recomputes ACV at render time. Plus a
#  separate Simulation rate (it's a real fabric, just priced differently).
# ── ACV derivation constants ──────────────────────────────────────────────
# Bug 13: when the researcher doesn't find cert_annual_sit_rate, derive
# it as this percentage of the customer training audience. ~2% for software
# companies per Platform-Foundation ACV adoption patterns.
CERT_SIT_DERIVATION_PCT = 0.02

# Org-type adoption rate overrides. The default adoption rates on
# CONSUMPTION_MOTIONS apply to software companies. Other org types have
# fundamentally different relationships to lab consumption.
# Key: org type (matches ORG_TYPE_NORMALIZATION values or raw discovery).
# Value: dict of motion label → overridden adoption_pct.
# Per Platform-Foundation → "How Adoption Patterns Vary by Organization Type"
ACV_ORG_ADOPTION_OVERRIDES: dict[str, dict[str, float]] = {
    "ACADEMIC": {
        "Customer Training & Enablement": 0.25,    # 25% — ~half enrolled in lab courses, not all courses have labs yet
        "Employee Training & Enablement": 0.30,    # faculty & staff development
        "Events & Conferences": 0.30,
        # Certification (PBT) removed — course exams bundled into Student Training
    },
    "TRAINING ORG": {
        "Customer Training & Enablement": 0.04,    # training candidates
        "Certification (PBT)": 1.00,               # exam sitters — 100% by definition
        "Events & Conferences": 0.30,
    },
    "INDUSTRY AUTHORITY": {
        "Customer Training & Enablement": 0.05,    # 5% — cert seekers are motivated, slightly above software baseline
        "Certification (PBT)": 1.00,               # exam sitters — 100% by definition
        "Events & Conferences": 0.30,
    },
    "LMS PROVIDER": {
        "Customer Training & Enablement": 0.03,    # 3% — blended platform & ILT learners
        "Events & Conferences": 0.30,
    },
    "ILT TRAINING ORG": {
        "Customer Training & Enablement": 0.25,    # 25% — percentage of courses that currently have labs
        "Employee Training & Enablement": 0.30,    # instructor training
        "Events & Conferences": 0.30,
    },
    "SYSTEMS INTEGRATOR": {
        "Customer Training & Enablement": 0.05,    # 5% — internal consultants
        "Events & Conferences": 0.30,
    },
    "TECH DISTRIBUTOR": {
        "Customer Training & Enablement": 0.03,    # 3% — training is emerging, not core
        "Events & Conferences": 0.30,
    },
}

# Org-type motion LABEL overrides. Different org types use different
# language for the same economic motions. The math is the same — only the
# display label changes so the seller reads language appropriate to the
# org type. Per Platform-Foundation → org-type sections.
# Three-tier open source classification — replaces the single multiplier.
# Commercial = baseline (no multiplier). Open source with training org = 0.75.
# Pure open source = 0.25. Detection: training_license + training signals.
# Per Platform-Foundation → unified ACV model. Frank 2026-04-13.
OPEN_SOURCE_WITH_TRAINING_MULTIPLIER = 0.75  # 3% effective (0.75 × 4%)
OPEN_SOURCE_PURE_MULTIPLIER = 0.25           # 1% effective (0.25 × 4%)

# Training maturity multipliers — nudge adoption up or down from baseline
# based on researcher-captured signals. Apply to all org types.
# Per Platform-Foundation → unified ACV model. Frank 2026-04-13.
ACV_TRAINING_MATURITY_MULTIPLIERS = {
    "atp_large": 1.5,      # ATP program with 50+ partners
    "cert_active": 1.25,   # Active cert exams for this product
    "no_signals": 0.75,    # No training programs, no ATPs, no certs
    "license_blocked": 0.5, # Training license is blocked
}

# Training maturity adoption ceiling — prevents runaway multipliers
# from exceeding a realistic maximum adoption rate for software companies.
ACV_TRAINING_MATURITY_ADOPTION_CAP = 0.35  # 35% ceiling

# Industry Authority user base deflation — researcher numbers are inflated
# (lifetime cert holders, not annual training candidates).
# Per Platform-Foundation → unified ACV model. Frank 2026-04-13.
INDUSTRY_AUTHORITY_DEFLATION_TIERS = [
    (500_000, 10),   # >500K reported → divide by 10
    (100_000, 5),    # 100K-500K → divide by 5
    (0, 2),          # <100K → divide by 2
]

# ── ACV audience source by org type ───────────────────────────────────
# Routes the Motion 1 (Customer Training & Enablement) audience field
# per org type. Software / Enterprise Software use estimated_user_base
# (the product's user count). Wrapper orgs use annual_enrollments_estimate
# (the wrapper's own per-program enrollment count) — a separate field
# the researcher populates only for wrapper orgs because the underlying
# technology's user base and the wrapper's classroom audience are
# different things.
#
# Per Platform-Foundation → "Wrapper organizations — product vs.
# audience" section.  Frank 2026-04-13.
ACV_AUDIENCE_SOURCE_USER_BASE = "estimated_user_base"
ACV_AUDIENCE_SOURCE_USER_BASE_DEFLATED = "estimated_user_base_deflated"
ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS = "annual_enrollments_estimate"

# org_type → audience source key for Motion 1.
# Org types not in this map fall back to estimated_user_base (Software default).
ACV_AUDIENCE_SOURCE_BY_ORG_TYPE: dict[str, str] = {
    "SOFTWARE": ACV_AUDIENCE_SOURCE_USER_BASE,
    "ENTERPRISE SOFTWARE": ACV_AUDIENCE_SOURCE_USER_BASE,
    "INDUSTRY AUTHORITY": ACV_AUDIENCE_SOURCE_USER_BASE_DEFLATED,
    "ACADEMIC": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
    "TRAINING ORG": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
    "ILT TRAINING ORG": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
    "LMS PROVIDER": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
    "SYSTEMS INTEGRATOR": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
    "TECH DISTRIBUTOR": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
    "PROFESSIONAL SERVICES": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
    "CONTENT DEVELOPMENT": ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS,
}


def get_acv_audience_source_for_org_type(normalized_org: str | None) -> str:
    """Return the Motion 1 audience field key for a given org type."""
    if not normalized_org:
        return ACV_AUDIENCE_SOURCE_USER_BASE
    return ACV_AUDIENCE_SOURCE_BY_ORG_TYPE.get(
        normalized_org, ACV_AUDIENCE_SOURCE_USER_BASE)


# HOLISTIC_ACV_ANCHORS — RETIRED 2026-04-14.
# Previously held named anchor companies in committed source with rough
# ACV estimates. Retired because:
#   1. Customer names in committed code = confidentiality risk.
#   2. Duplicated data with KNOWN_CUSTOMER_CURRENT_ACV (gitignored).
#   3. Define-Once violation — two sources of truth for customer magnitude.
# Replaced entirely by the anonymized calibration block that reads
# KNOWN_CUSTOMER_CURRENT_ACV and emits stage-grouped ranges with NO
# customer names. See researcher._format_anonymized_calibration_block.


# ── Holistic ACV guardrails — RETIRED 2026-04-17 ──────────────────────
# HOLISTIC_ACV_MAX_RANGE_RATIO, HOLISTIC_ACV_PER_USER_CEILING, and
# HOLISTIC_ACV_COMPANY_HARD_CAP guarded the legacy `estimate_holistic_acv`
# Claude shortcut.  The Claude call + its entire calibration / guardrail
# stack is retired — discovery-time company ACV is now computed by the
# deterministic framework in acv_calculator.compute_discovery_company_acv.
# See decision-log.md → 2026-04-17 late entry.


# ── Known Skillable customers — ground-truth ACV anchors ──────────────
# CONFIDENTIAL CUSTOMER REVENUE DATA. The actual values live in a
# gitignored file (backend/known_customers.json) loaded at runtime.
# This module-level constant is populated by _load_known_customers() and
# is empty when the file is missing (development / fork / deploy without
# secrets).
#
# Purpose (post 2026-04-17 ACV architecture):
#   - HARD FLOOR — ACV estimate must be >= current actual ACV.  Applied
#     in acv_calculator.compute_discovery_company_acv so a customer we
#     are actively charging $X cannot show a discovery-time estimate
#     below $X.  Accessed via get_known_customer_record() below.
# The legacy KNOWN_CUSTOMER_STAGE_CEILING_MULT is retired with the Claude
# holistic shortcut — the calibration / stage-ceiling machinery it fed
# is gone.


# ── Org types that skip direct ACV estimation (partnership-only ICPs) ──
# Some org types don't fit the audience × adoption × hours × rate model
# because they don't have a direct-adoption relationship with Skillable —
# they're partnership plays. Content Development firms (GP Strategies,
# Cprime, etc.) build labs on behalf of their clients; they have no
# "programs" that map to lab consumption directly. The right ACV for
# them is downstream-partnership-dependent, not a direct estimate.
#
# For these org types, estimate_holistic_acv returns a special
# "partnership" result with acv_low / acv_high = 0, a rationale that
# explains the partnership opportunity, and confidence = "partnership".
# The Prospector row displays "Partnership" instead of a dollar range.
# Marketing can filter the export on ACV Type = "partnership" for
# dedicated partnership campaigns.
#
# Per Platform-Foundation.md → Content Development firms section.
# Frank 2026-04-14.
ACV_PARTNERSHIP_ONLY_ORG_TYPES: frozenset[str] = frozenset({
    "CONTENT DEVELOPMENT",
    # Note: LLPA-class federating associations could be added here if
    # we identify more of them. Punted to backlog 2026-04-14 — small
    # population, pattern well-understood from LLPA itself.
})


def _load_known_customers() -> dict[str, dict]:
    """Load known-customer ACV data from the gitignored JSON file.

    Returns empty dict when the file doesn't exist (no leak, no error).
    Keys in the file are pre-normalized customer names matching
    storage._normalize_company_name output. Keys beginning with "_" or
    "comment" are structural metadata (schema notes, stage-group dividers)
    and filtered out — only real customer records are returned.
    """
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), "known_customers.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        # Filter out metadata + stage-divider comments.
        # A valid customer entry has a dict value with a numeric current_acv.
        return {
            k: v for k, v in data.items()
            if not k.startswith("_")
            and not k.startswith("comment")
            and isinstance(v, dict)
            and isinstance(v.get("current_acv"), (int, float))
            and v.get("current_acv", 0) > 0
        }
    except Exception:
        return {}


KNOWN_CUSTOMER_CURRENT_ACV: dict[str, dict] = _load_known_customers()


def get_known_customer_record(company_name: str | None) -> dict | None:
    """Return the known-customer record for a given company name (normalized).

    Returns None if not a known customer or if the data file is absent.
    """
    if not company_name or not KNOWN_CUSTOMER_CURRENT_ACV:
        return None
    from storage import _normalize_company_name
    key = _normalize_company_name(company_name)
    return KNOWN_CUSTOMER_CURRENT_ACV.get(key)


# ── Researcher estimation heuristics (read INTO prompt text — Define-Once) ──
# These are the tiered defaults the researcher Claude calls use when exact
# numbers aren't documented in the research. Formerly inline in prompt
# strings; extracted here so they can be tuned without editing prompts.
# Adjust a value, next Deep Dive / retrofit picks it up automatically.

# Partner SE population — Motion 2 audience estimation tiers.
# Applied when the research shows a channel/partner ecosystem but doesn't
# document the exact SE count (the common case — partners list is public,
# SE headcount per partner rarely is).
RESEARCHER_PARTNER_SE_PER_PARTNER_ORG_DEEP = 10     # deep strategic alliance
RESEARCHER_PARTNER_SE_PER_PARTNER_ORG_STANDARD = 8  # general partner ecosystem average
RESEARCHER_PARTNER_SE_PER_PARTNER_ORG_TRANSACTIONAL = 5  # reseller / transactional
RESEARCHER_PARTNER_ORGS_GLOBAL_LOW = 300   # "global program, no count" low end
RESEARCHER_PARTNER_ORGS_GLOBAL_HIGH = 500  # "global program, no count" high end
RESEARCHER_PARTNER_ORGS_REGIONAL_LOW = 30  # "regional / emerging" low end
RESEARCHER_PARTNER_ORGS_REGIONAL_HIGH = 100  # "regional / emerging" high end

# Event attendance — Motion 5 audience estimation tiers.
# Applied when a flagship event is named but attendance isn't published.
RESEARCHER_EVENT_MAJOR_LOW = 30_000   # Salesforce Dreamforce, Microsoft Ignite, AWS re:Invent class
RESEARCHER_EVENT_MAJOR_HIGH = 50_000
RESEARCHER_EVENT_MID_LOW = 8_000      # Splunk .conf, Tableau, Cohesity Connect class
RESEARCHER_EVENT_MID_HIGH = 15_000
RESEARCHER_EVENT_SPECIALIZED_LOW = 5_000   # Nutanix .NEXT, Trellix XPAND class — single-vendor technical
RESEARCHER_EVENT_SPECIALIZED_HIGH = 12_000
RESEARCHER_EVENT_REGIONAL_LOW = 1_000      # regional / virtual / community
RESEARCHER_EVENT_REGIONAL_HIGH = 5_000

# Employee subset size — Motion 3 audience estimation by product significance.
# Percentages apply to total company employees. Flagship products carry the
# largest product teams; satellites smaller dedicated teams plus shared
# support; standalone products at single-product companies = most of the
# company.
RESEARCHER_EMPLOYEE_SUBSET_FLAGSHIP_LOW_PCT = 0.08    # 8% of total company employees
RESEARCHER_EMPLOYEE_SUBSET_FLAGSHIP_HIGH_PCT = 0.15   # 15%
RESEARCHER_EMPLOYEE_SUBSET_SATELLITE_LOW_PCT = 0.03   # 3%
RESEARCHER_EMPLOYEE_SUBSET_SATELLITE_HIGH_PCT = 0.06  # 6%
RESEARCHER_EMPLOYEE_SUBSET_STANDALONE_LOW_PCT = 0.50  # 50% — whole company is product-facing
RESEARCHER_EMPLOYEE_SUBSET_STANDALONE_HIGH_PCT = 0.80 # 80%


# ── ACV audience guardrails (R1–R5 from 2026-04-13 ACV audit) ─────────
# Wrapper org types (GSI, university, training org, etc.) report the
# underlying technology's global audience as their install_base. The real
# audience is the org's own practice headcount. These constants cap the
# audience to a reasonable fraction of the org's total employees.
ACV_WRAPPER_ORG_TYPES = frozenset({
    "SYSTEMS INTEGRATOR", "ACADEMIC", "TRAINING ORG",
    "TECH DISTRIBUTOR", "PROFESSIONAL SERVICES", "LMS PROVIDER",
    "CONTENT DEVELOPMENT", "INDUSTRY AUTHORITY", "ILT TRAINING ORG",
})
# For wrapper orgs: Motion 1 audience capped at this fraction of total_employees
ACV_WRAPPER_ORG_AUDIENCE_CAP_FRACTION = 0.25
# Minimum audience cap for wrapper orgs — even small orgs have some training pop
ACV_WRAPPER_ORG_AUDIENCE_FLOOR = 1_000
# Cert audience can never exceed this fraction of the install_base for the same product
ACV_CERT_MAX_FRACTION_OF_INSTALL_BASE = 0.10
# Company-level ACV sanity cap: total ACV cannot exceed total_employees × this amount
# Represents a rough ceiling on training spend per employee per year
ACV_PER_EMPLOYEE_ANNUAL_CAP = 500

# ── IV differentiation: strong signal cap per dimension ───────────────
# When a dimension receives more than this many "strong" signals, the
# extras are downgraded to "moderate" credit. This creates differentiation
# within high-baseline categories (Cybersecurity, Cloud Infrastructure)
# where every product would otherwise hit 100/100. A product with 2
# strong signals + 1 moderate scores differently than 3+ strong.
# Per Frank 2026-04-13 — Option A from the IV differentiation discussion.
MAX_STRONG_SIGNALS_PER_DIMENSION = 2

ACV_ORG_MOTION_LABELS: dict[str, dict[str, str]] = {
    "ACADEMIC": {
        "Customer Training & Enablement": "Student Training",
        "Partner Training & Enablement": "Research Partnerships",
        "Employee Training & Enablement": "Faculty & Staff Development",
        "Events & Conferences": "Campus Events",
    },
    "TRAINING ORG": {
        "Customer Training & Enablement": "Training Participants",
        "Employee Training & Enablement": "Internal Trainers",
    },
    "INDUSTRY AUTHORITY": {
        "Customer Training & Enablement": "Training Participants",
        "Certification (PBT)": "Cert Exam Sitters",
    },
    "ILT TRAINING ORG": {
        "Customer Training & Enablement": "Classroom Students",
        "Employee Training & Enablement": "Instructor Training",
    },
    "LMS PROVIDER": {
        "Customer Training & Enablement": "Platform & ILT Learners",
    },
    "SYSTEMS INTEGRATOR": {
        "Customer Training & Enablement": "Internal Consultants",
    },
    "TECH DISTRIBUTOR": {
        "Customer Training & Enablement": "Internal Practitioners",
    },
}

# Org-type hours overrides. Academic students spend more time in labs
# (coursework, not elective). ILT students do 20-30 hours in a week.
# Per Platform-Foundation → "How Adoption Patterns Vary by Organization Type"
ACV_ORG_HOURS_OVERRIDES: dict[str, dict[str, float]] = {
    "ACADEMIC": {
        "Customer Training & Enablement": 15.0,   # 15hrs — realistic semester lab consumption including practice labs
    },
    "ILT TRAINING ORG": {
        "Customer Training & Enablement": 18.0,   # 18hrs — intensive multi-day classroom format (4-5 day courses)
    },
    "LMS PROVIDER": {
        "Customer Training & Enablement": 3.0,    # 3hrs — average across on-demand (1-2hrs) and ILT (15+hrs) weighted toward on-demand
    },
    "INDUSTRY AUTHORITY": {
        "Customer Training & Enablement": 10.0,   # 10hrs — cert prep is intensive, structured lab time
    },
    "TECH DISTRIBUTOR": {
        "Customer Training & Enablement": 5.0,    # 5hrs — services arm, emerging training
    },
}

# ── Prospector batch processing constants ─────────────────────────────────
PROSPECTOR_DISCOVERY_TIMEOUT = 300   # 5 minutes per company discovery (Cisco took 189s with 21 products)
PROSPECTOR_DEEP_DIVE_TIMEOUT = 420   # 7 minutes per company deep dive
PROSPECTOR_MAX_PARALLEL = 10         # concurrent companies; bumped 2026-04-14 (was 3). Rate-limit headroom confirmed over long runs.
PROSPECTOR_RECENT_BATCHES_LIMIT = 10 # max recent batches shown in the status panel

# ── Rate tiers ────────────────────────────────────────────────────────────
CLOUD_LABS_RATE = 6.00    # Cloud Slice / BYOC — platform fee only, customer pays cloud bill
VM_LOW_RATE     = 8.00    # Container or lightweight single VM
VM_MID_RATE     = 14.00   # Clean single VM through 2-3 VMs with minor service deps
VM_HIGH_RATE    = 45.00   # Demanding multi-VM, exotic, GPU-required, networking topologies
SIMULATION_RATE = VM_LOW_RATE  # Frank: Sims priced same as VM Low ($8)

#  Six fabric tiers — Frank's locked categorization. Each tier reads its
#  dollar value from one of the named variables above so every price in
#  the codebase traces back to a single line.
RATE_TABLES: tuple[RateTier, ...] = (
    RateTier("Azure/AWS Cloud Slice", CLOUD_LABS_RATE, CLOUD_LABS_RATE,
        "Cloud Labs rate. Platform fee only — cloud consumption billed "
        "separately through customer's cloud subscription"),
    RateTier("Custom API (BYOC)", CLOUD_LABS_RATE, CLOUD_LABS_RATE,
        "Cloud Labs rate. Platform fee only — vendor cloud costs separate"),
    RateTier("Container", VM_LOW_RATE, VM_LOW_RATE,
        "VM Low rate. Container labs and lightweight pre-baked images"),
    RateTier("Standard VM (1-3 VMs)", VM_MID_RATE, VM_MID_RATE,
        "VM Mid rate. Clean single-VM install through 2-3 VMs with minor "
        "service dependencies — the everyday admin lab"),
    RateTier("Large/complex VM", VM_HIGH_RATE, VM_HIGH_RATE,
        "VM High rate. Demanding multi-VM, exotic builds, GPU-required, "
        "or networking topologies with 4+ VMs"),
    RateTier("Simulation", SIMULATION_RATE, SIMULATION_RATE,
        "Simulation rate. No live environment — AI Vision compute and "
        "platform overhead only. Used when real provisioning is impractical."),
)

# ─────────────────────────────────────────────────────────────────────────
# ACV tier thresholds — map a computed annual ACV (dollar value) to a
# tier label (high / medium / low). Used by the verdict grid at render
# time. Thresholds are evaluated against the HIGH end of the ACV range
# so a deal is sized at its upside potential, not its floor.
#
# Locked 2026-04-06 (Frank). Tweaking is a one-line edit; the next page
# render picks up the new value with zero rescore needed.
# ─────────────────────────────────────────────────────────────────────────
ACV_TIER_HIGH_THRESHOLD   = 250_000  # ACV high >= $250K  → "high"
ACV_TIER_MEDIUM_THRESHOLD = 50_000   # ACV high >= $50K   → "medium"
                                     # else                → "low"

# Default rate tier when an orchestration_method is empty, unknown, or
# doesn't map to any known tier. Conservatively neither the cheap nor the
# expensive end of the table — the everyday admin lab default.
DEFAULT_RATE_TIER_NAME = "Standard VM (1-3 VMs)"

# Map raw orchestration_method strings the AI emits to a canonical rate
# tier name. Used by the deterministic Python ACV math at render time.
# Anything not matched falls through to DEFAULT_RATE_TIER_NAME above.
ORCHESTRATION_TO_RATE_TIER = {
    # Cloud Labs family
    "azure cloud slice": "Azure/AWS Cloud Slice",
    "aws cloud slice":   "Azure/AWS Cloud Slice",
    "cloud slice":       "Azure/AWS Cloud Slice",
    "custom api":        "Custom API (BYOC)",
    "byoc":              "Custom API (BYOC)",
    # Container
    "container":         "Container",
    "containers":        "Container",
    "docker":            "Container",
    # Standard VM is the default for Hyper-V and ESX without complexity signals
    "hyper-v":           "Standard VM (1-3 VMs)",
    "hyperv":            "Standard VM (1-3 VMs)",
    "esx":               "Standard VM (1-3 VMs)",
    "esxi":              "Standard VM (1-3 VMs)",
    "vmware":            "Standard VM (1-3 VMs)",
    # Large/complex VM — multi-VM, complex topology, or large footprint
    "large vm":          "Large/complex VM",
    "large/complex vm":  "Large/complex VM",
    # Simulation
    "simulation":        "Simulation",
    "simulated":         "Simulation",
}

# ── Discovery-level ACV estimation (rough, pre-Deep Dive) ─────────────────
# Same methodology as the full ACV model (audience × adoption × hours × rate)
# but with only discovery-level data. One product, one motion (customer training).
# Deep Dive replaces this with the full five-motion calculation.
DISCOVERY_ACV_ADOPTION_RATE = 0.04    # Motion 1 default adoption rate
DISCOVERY_ACV_HOURS = 2               # Motion 1 default hours per learner
DISCOVERY_ACV_RATE_BY_DEPLOYMENT = {
    "installable": VM_MID_RATE,       # $14/hr — typical VM
    "hybrid": VM_MID_RATE,            # $14/hr — assume VM path
    "cloud": CLOUD_LABS_RATE,         # $6/hr — cloud labs
    "saas-only": CLOUD_LABS_RATE,     # $6/hr — BYOC/cloud path
}
DISCOVERY_ACV_DEFAULT_RATE = VM_MID_RATE  # fallback when deployment model unknown
DISCOVERY_ACV_CAP = 5_000_000            # hard cap — no discovery estimate exceeds $5M
# Tiered discount for inflated user bases — more aggressive as the number grows.
# The researcher is supposed to report training population, not total users,
# but compliance varies. These tiers approximate real training populations.
DISCOVERY_ACV_USER_BASE_TIERS = [
    # (threshold, effective_training_pop) — if user_base > threshold, use the fixed pop
    # LEGACY default tier (used when archetype is unknown). Frank 2026-04-16:
    # archetype-aware tiers below are preferred; this default stays for the
    # fall-through case and for unscored-extrapolation paths that don't have
    # archetype resolved.
    (10_000_000, 200_000),   # 10M+ users → ~200K realistic training pop
    (3_000_000, 150_000),    # 3-10M users → ~150K
    (1_000_000, 100_000),    # 1-3M users → ~100K
    (500_000, None),         # 500K-1M → no adjustment
]


# ─────────────────────────────────────────────────────────────────────────
# Archetype-aware audience tiers (Frank 2026-04-16)
#
# The realistic Skillable-addressable training population depends on the
# ARCHETYPE of the product — full-ceiling enterprise products can have
# admin audiences of 1M+ (Microsoft 365 admin side, Azure admin, SAP),
# specialist products are tighter (Fortinet, Nutanix), and IC productivity
# / consumer tools tighter still. One-size-fits-all caps either undercount
# big-portfolio admin vendors or over-count consumer tools.
#
# Tiers are applied the same way as DISCOVERY_ACV_USER_BASE_TIERS — the
# first threshold the audience exceeds wins. A cap of None means no
# adjustment at that size.
# ─────────────────────────────────────────────────────────────────────────

# Full-ceiling enterprise archetypes — biggest audience caps because the
# admin/operator/developer training population for these products really
# does span millions globally (Azure admin, M365 admin, Workday admin, etc.)
_AUDIENCE_TIERS_ENTERPRISE = [
    (100_000_000, 3_000_000),  # 100M+ seats → 3M trainable (M365-class)
    (10_000_000, 1_000_000),   # 10M+ seats → 1M (Azure-class)
    (3_000_000, 500_000),      # 3M+ seats → 500K (Power BI-class)
    (1_000_000, 250_000),      # 1M+ seats → 250K
    (500_000, None),           # below 1M → no cap
]

# Specialist archetypes (security ops, deep infrastructure, integration
# middleware, engineering CAD) — tighter than enterprise because the
# addressable training population is specialists, not broad admin layers.
_AUDIENCE_TIERS_SPECIALIST = [
    (10_000_000, 500_000),
    (3_000_000, 300_000),
    (1_000_000, 150_000),
    (500_000, None),
]

# IC productivity / creative professional — narrow lab-training addressable
# population, the rest of the audience trains via e-learning/video.
_AUDIENCE_TIERS_IC = [
    (10_000_000, 200_000),
    (3_000_000, 150_000),
    (1_000_000, 100_000),
    (500_000, None),
]

# Consumer app — tightest, labs barely apply
_AUDIENCE_TIERS_CONSUMER = [
    (1_000_000, 50_000),
    (100_000, 25_000),
    (50_000, None),
]

AUDIENCE_TIERS_BY_ARCHETYPE: dict[str, list[tuple]] = {
    "enterprise_admin":       _AUDIENCE_TIERS_ENTERPRISE,
    "developer_platform":     _AUDIENCE_TIERS_ENTERPRISE,
    "data_platform":          _AUDIENCE_TIERS_ENTERPRISE,
    "security_operations":    _AUDIENCE_TIERS_SPECIALIST,
    "deep_infrastructure":    _AUDIENCE_TIERS_SPECIALIST,
    "integration_middleware": _AUDIENCE_TIERS_SPECIALIST,
    "engineering_cad":        _AUDIENCE_TIERS_SPECIALIST,
    "ic_productivity":        _AUDIENCE_TIERS_IC,
    "creative_professional":  _AUDIENCE_TIERS_IC,
    "consumer_app":           _AUDIENCE_TIERS_CONSUMER,
}


def get_audience_tiers_for_archetype(archetype: str) -> list[tuple]:
    """Return the audience-tier table for the given archetype.

    Falls back to the legacy DISCOVERY_ACV_USER_BASE_TIERS when the
    archetype is empty or not in the map — conservative default.
    """
    if archetype and archetype in AUDIENCE_TIERS_BY_ARCHETYPE:
        return AUDIENCE_TIERS_BY_ARCHETYPE[archetype]
    return DISCOVERY_ACV_USER_BASE_TIERS


# ─────────────────────────────────────────────────────────────────────────
# Scale-aware adoption cap (Frank 2026-04-16)
#
# After all the training-maturity multipliers (ATP large 1.5x, cert active
# 1.25x) compound the base category-tier adoption, the effective % can
# hit 15-30%. That implies Skillable captures 15-30% of the global training
# market for that product annually. For small-audience products this is
# realistic (cert prep candidates are a motivated, small population).
# For huge-audience products (Microsoft 365 admins, Azure admins), 15%
# capture is not defensible — Skillable's global share of the enterprise-
# admin training market is realistically 1-3%, not 15%.
#
# Graduated cap: the bigger the audience, the smaller Skillable's realistic
# share. Applied AFTER all other adoption multipliers in the motion math.
# ─────────────────────────────────────────────────────────────────────────

ADOPTION_CEILING_BY_AUDIENCE = [
    # (audience_threshold, max_effective_adoption_%)
    (1_000_000, 0.02),    # > 1M trainable → max 2% Skillable share
    (250_000, 0.04),      # 250K-1M → max 4%
    (50_000, 0.08),       # 50K-250K → max 8%
    # below 50K → no ceiling beyond the existing 35% overall cap
]


def get_scale_aware_adoption_ceiling(audience: int) -> float | None:
    """Return the max effective adoption % for a given audience size.

    Returns None when the audience is small enough that no scale-aware
    ceiling applies (the overall 35% cap still governs).
    """
    if audience <= 0:
        return None
    for threshold, ceiling in ADOPTION_CEILING_BY_AUDIENCE:
        if audience >= threshold:
            return ceiling
    return None


# ─────────────────────────────────────────────────────────────────────────
# Archetype-aware hours per motion (Frank 2026-04-16)
#
# Default motion hours are calibrated for enterprise admin products (2 hrs
# Customer Training, 5 Partner, 8 Employee). Deep infrastructure / CAD /
# security ops labs are meaningfully longer — setup is complex, full
# workflow takes time. IC productivity tools the other way — shorter labs.
# ─────────────────────────────────────────────────────────────────────────

HOURS_BY_ARCHETYPE: dict[str, dict[str, int]] = {
    # Full-ceiling enterprise — keep the defaults (2/5/8/1/1)
    "enterprise_admin":       {},
    "developer_platform":     {},
    "data_platform":          {},
    # Specialist — deep labs (5 hrs customer training)
    "security_operations":    {"Customer Training & Enablement": 5},
    "deep_infrastructure":    {"Customer Training & Enablement": 5},
    "integration_middleware": {"Customer Training & Enablement": 4},
    "engineering_cad":        {"Customer Training & Enablement": 5},
    # IC / creative / consumer — shorter labs
    "ic_productivity":        {"Customer Training & Enablement": 1,
                               "Partner Training & Enablement": 2,
                               "Employee Training & Enablement": 4},
    "creative_professional":  {"Customer Training & Enablement": 2,
                               "Partner Training & Enablement": 3,
                               "Employee Training & Enablement": 4},
    "consumer_app":           {"Customer Training & Enablement": 1,
                               "Partner Training & Enablement": 0,
                               "Employee Training & Enablement": 2},
}


def get_hours_for_archetype_motion(archetype: str, motion_label: str,
                                    default_hours: int) -> int:
    """Return hours for a given motion, archetype-aware."""
    if archetype and archetype in HOURS_BY_ARCHETYPE:
        overrides = HOURS_BY_ARCHETYPE[archetype]
        if motion_label in overrides:
            return overrides[motion_label]
    return default_hours

PRODUCT_CATEGORY_RATE_PRIORS = (
    {"category": "Networking", "typical_vms": "2-6", "rate_tier": "complex", "rate_range": "$45-55/hr", "seat_time": "60-90+ min",
     "examples": "Cisco, Fortinet, F5, Juniper, Aruba"},
    {"category": "Cybersecurity", "typical_vms": "2-5 (burst to 15)", "rate_tier": "complex", "rate_range": "$45-55/hr", "seat_time": "60-90 min",
     "examples": "SIEM, EDR, identity, threat detection, incident response"},
    {"category": "Data Science / Data Engineering", "typical_vms": "2-4", "rate_tier": "complex", "rate_range": "$45-55/hr", "seat_time": "75-120 min",
     "examples": "Pipelines, ML infra, warehousing"},
    {"category": "Enterprise Server Software", "typical_vms": "2-3", "rate_tier": "standard-complex", "rate_range": "$15-45/hr", "seat_time": "45-75 min",
     "examples": "Backup, monitoring, ITSM, data protection"},
    {"category": "Developer Tools / IDEs / CI-CD", "typical_vms": "1-2 or Docker", "rate_tier": "standard", "rate_range": "$12-15/hr", "seat_time": "30-60 min",
     "examples": "Developer tools, IDEs, CI-CD pipelines"},
    {"category": "Single-Product Admin", "typical_vms": "1-2", "rate_tier": "standard", "rate_range": "$12-15/hr", "seat_time": "45-60 min",
     "examples": "Standard enterprise software administration"},
)

# The five consumption motions — Platform-Foundation ACV model (2026-04-08).
#
# Each motion has a single adoption_pct and single hours values (low == high
# except where the hours spread is a defendable real range). The ONLY source
# of range in the final ACV number is the audience (population), because
# that's where the real uncertainty lives. Adoption and hours are locked.
#
# population_source names a fact-drawer field the ACV builder reads:
#   "product:install_base"              → instructional_value_facts.market_demand.install_base
#   "product:employee_subset_size"      → instructional_value_facts.market_demand.employee_subset_size
#   "product:cert_annual_sit_rate"      → instructional_value_facts.market_demand.cert_annual_sit_rate
#   "company:channel_partner_se_population" → customer_fit_facts.channel_partner_se_population
#   "company:events_attendance_sum"     → sum of customer_fit_facts.events_attendance values
CONSUMPTION_MOTIONS: tuple[ConsumptionMotion, ...] = (
    ConsumptionMotion(
        label="Customer Training & Enablement",
        adoption_pct=0.04,
        hours_low=2.0, hours_high=2.0,
        population_source="product:install_base",
        description="End learners — anyone taking a lab to learn the product, "
                    "regardless of whether they enrolled directly or through an "
                    "ATP or training partner. This is the total user population "
                    "of the product. Do NOT double-count people who happen to "
                    "train through an ATP — they are customers, not partners."),
    ConsumptionMotion(
        label="Partner Training & Enablement",
        adoption_pct=0.15,
        hours_low=5.0, hours_high=5.0,
        population_source="company:channel_partner_se_population",
        description="People at CHANNEL PARTNER organizations (GSIs, VARs, "
                    "distributors, resellers) who need product knowledge to "
                    "sell, deploy, implement, or support the product. These are "
                    "the partner's own employees — consultants, SEs, solution "
                    "architects. NOT the end customers who learn through "
                    "partners (those are in Motion 1). Zero when the company "
                    "doesn't sell through a channel."),
    ConsumptionMotion(
        label="Employee Training & Enablement",
        adoption_pct=0.30,
        hours_low=8.0, hours_high=8.0,
        population_source="product:employee_subset_size",
        description="People at the COMPANY BEING ANALYZED who work on the "
                    "product — product team, SEs, support engineers, customer "
                    "success, trainers. NOT total headcount. NOT people at "
                    "customer companies (those are in Motion 1). This is always "
                    "a small number relative to company size."),
    ConsumptionMotion(
        label="Certification (PBT)",
        adoption_pct=1.00,
        hours_low=1.0, hours_high=1.0,
        population_source="product:cert_annual_sit_rate",
        description="People who sit for the certification exam each year. 100% "
                    "adoption is exact — if a lab is in the exam, every taker "
                    "takes the lab. Zero when the product has no cert or the "
                    "cert has no lab component."),
    ConsumptionMotion(
        label="Events & Conferences",
        adoption_pct=0.30,
        hours_low=1.0, hours_high=1.0,
        population_source="company:events_attendance_sum",
        description="Total attendees at the company's flagship events. Events "
                    "without labs today are the opportunity, NOT zero. Zero only "
                    "when the company runs no events at all."),
)

# Hard ceilings — never exceed these adoption rates in future tuning.
# Motion 4 (Certification) is exempt — its 100% is exact by definition.
ADOPTION_CEILING_EVENTS = 0.80
ADOPTION_CEILING_NON_EVENTS = 0.35

# ── Org-type adoption rate guidance ──────────────────────────────────
#
# The flat adoption rates in CONSUMPTION_MOTIONS above are the DEFAULT
# for software companies. Different org types have fundamentally
# different adoption patterns because the relationship between the
# audience and the lab experience is different.
#
# Software companies: voluntary — users choose to train and certify.
# Industry Authorities: intentional — candidates pursue a credential.
# Academic: required — coursework is assigned, not optional.
#
# This table documents the expected adoption rate adjustments by org
# type. The researcher should use these as guidance when estimating
# audience sizes — the adoption rate in the ACV calculator is applied
# to the audience number the researcher provides, so if the researcher
# gives us the RIGHT audience, the default adoption rates work.
# The key is: the researcher must give the right AUDIENCE for each
# org type, not adjust the rate.
#
# | Context           | Motion 1 audience             | Motion 4 audience              | Adoption pattern              |
# |-------------------|-------------------------------|--------------------------------|-------------------------------|
# | Software company  | Product users worldwide       | Annual exam sitters (~2% of    | Voluntary — low adoption      |
# |                   |                               | training population)           |                               |
# | Industry Authority| Training candidates per year  | Annual exam sitters (~10% of   | Intentional — moderate        |
# |                   | (people interested in cert)   | training population)           | adoption                      |
# | Academic          | Students enrolled in tech     | Students taking exams (~95%    | Required — near-100%          |
# |                   | programs this year            | of enrolled, it's coursework)  | adoption                      |
# | GSI               | Consultants in practice area  | Practice-specific cert sitters | Varies by practice            |
# | ILT Training Org  | Students per year in classes  | N/A (they deliver, not certify)| High — every student labs      |
#
# The critical insight: for Industry Authorities, the cert_annual_sit_rate
# must be the ACTUAL annual exam volume (people who literally sit the exam),
# NOT the training candidate population. The training population goes in
# install_base (Motion 1). These are very different numbers — ~250K people
# may be interested in CEH, ~50K take training, ~5K sit the exam.


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER MOTIVATIONS
#
# Every organization that invests in hands-on training does so for one or
# more of these reasons.  Not mutually exclusive — a single product can
# have multiple motivations.
# ═══════════════════════════════════════════════════════════════════════════════

CUSTOMER_MOTIVATIONS = (
    {
        "name": "Product Adoption",
        "core_drive": "People use it, love it, don't churn",
        "stakes": "Revenue — if they don't adopt, they cancel",
        "learner_outcome": "Confident in the product",
    },
    {
        "name": "Skill Development",
        "core_drive": "People are competent, certified, employable",
        "stakes": "Careers — if they can't do it, they can't get the job",
        "learner_outcome": "Confident in themselves",
    },
    {
        "name": "Compliance & Risk Reduction",
        "core_drive": "People don't make dangerous mistakes",
        "stakes": "Consequences — if they get it wrong, real harm happens",
        "learner_outcome": "Confident under pressure",
    },
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIDENCE LEVELS
#
# Confidence coding is core logic — every finding carries a confidence
# level as a stored field.  It influences badge color assignment, surfaces
# in evidence language, and is available to downstream consumers.
# ═══════════════════════════════════════════════════════════════════════════════

CONFIDENCE_LEVELS: tuple[ConfidenceLevel, ...] = (
    ConfidenceLevel(
        "confirmed",
        "Direct evidence from a primary source",
        'REST API **confirmed** — OpenAPI spec at docs.vendor.com',
    ),
    ConfidenceLevel(
        "indicated",
        "Strong indirect evidence, multiple signals",
        'VM deployment **indicated** — installation guide references Windows Server',
    ),
    ConfidenceLevel(
        "inferred",
        "AI-informed assumption based on patterns or limited signals",
        'Troubleshooting lab potential **inferred** from category norms',
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LOCKED VOCABULARY
#
# Ensures consistency across code, prompts, UX, and documentation.
# The 'use_this' form is the only acceptable term everywhere in the system.
# ═══════════════════════════════════════════════════════════════════════════════

LOCKED_VOCABULARY: tuple[LockedTerm, ...] = (
    LockedTerm("Fit Score", ("Composite Score", "Lab Score")),
    LockedTerm("Pillar", ("Dimension (as top-level component)",)),
    LockedTerm("Product Labability", ("Technical Orchestrability",)),
    LockedTerm("Instructional Value", ("Product Demand", "Workflow Complexity")),
    LockedTerm("Customer Fit", ("Customer Motivation", "Organizational Readiness (as separate pillar)")),
    LockedTerm("Provisioning", ("Orchestration Method", "Gate 1")),
    LockedTerm("Lab Access", ("Licensing & Accounts", "Gate 2", "Configure")),
    LockedTerm("Scoring", ("Gate 3",)),
    LockedTerm("Teardown", ("Gate 4",)),
    LockedTerm("Product Complexity", ("Difficult to Master",)),
    LockedTerm("Mastery Stakes", ("Mastery Matters", "Consequence of Failure")),
    LockedTerm("Lab Versatility", ("Lab Format Opportunities",)),
    LockedTerm("Market Demand", ("Market Fit", "Market Readiness", "Strategic Fit")),
    LockedTerm("Training Commitment", ("Training Motivation",)),
    LockedTerm("Organizational DNA", ()),
    LockedTerm("Delivery Capacity", ("Content Delivery Ecosystem",)),
    LockedTerm("Build Capacity", ("Content Development Capabilities",)),
    LockedTerm("Content Dev Team", ("Dedicated Content Dept",)),
    LockedTerm("Content Outsourcing", ("Outsourced Content Creation",)),
    LockedTerm("DIY Labs", ("DIY",)),
    LockedTerm("Green / Gray / Amber / Red", ("Pass / Partial / Fail / Yellow",)),
    LockedTerm("Blocker", ("Red (in badge context)",)),
)


# ═══════════════════════════════════════════════════════════════════════════════
# BADGE COLORS AND QUALIFIER LABELS
#
# The four badge colors and their semantic meaning.  Every badge in the
# system uses exactly these four colors — no others exist.
# ═══════════════════════════════════════════════════════════════════════════════

BADGE_COLORS = {
    "green":  {"meaning": "Strength / Opportunity", "qualifier_labels": ("Strength", "Opportunity")},
    "gray":   {"meaning": "Neutral / Context", "qualifier_labels": ("Context",)},
    "amber":  {"meaning": "Risk / Caution", "qualifier_labels": ("Risk",)},
    "red":    {"meaning": "Blocker", "qualifier_labels": ("Blocker",)},
}

EVIDENCE_FORMAT = '**[Badge Name] | [Qualifier]:** [Specific finding] — [source title]. [What it means for lab delivery.]'

EVIDENCE_ORDERING = ("green", "gray", "amber", "red")
"""Badge order within each dimension: Strengths/Opportunities first,
then Context, then Risks, then Blockers."""


# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT MODELS
#
# The deployment model determines the starting point for the Provisioning
# assessment.  SaaS-only triggers the isolation pre-screen.
# ═══════════════════════════════════════════════════════════════════════════════

DEPLOYMENT_MODELS = {
    "installable":  {"display": "Installable", "color": "green_muted",
                     "description": "Downloadable installer, container image, or VM image"},
    "hybrid":       {"display": "Hybrid", "color": "gray",
                     "description": "Available as both installable and cloud/SaaS"},
    "cloud":        {"display": "Cloud-Native", "color": "green_muted",
                     "description": "Deployed on customer-controlled cloud infrastructure"},
    "saas-only":    {"display": "SaaS-Only", "color": "amber",
                     "description": "Vendor-managed only — learner isolation and API questions ahead"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# POOR MATCH FLAGS
#
# Flags that indicate specific constraints or blockers.  Stored on the
# product record and used for filtering, reporting, and UX display.
# ═══════════════════════════════════════════════════════════════════════════════

POOR_MATCH_FLAGS = (
    # Hard blockers / ceilings
    "bare_metal_required",
    "no_api_automation",
    # Classification metadata (no longer scoring caps — see CEILING_FLAGS notes)
    "saas_only",
    "multi_tenant_only",
    # Friction badges with math impact
    "gpu_required",
    "mfa_required",
    "anti_automation",
    "rate_limits",
    "socket_licensing_high",
    # Pillar 2 / instructional flags
    "pii_required",
    "consumer_product",
    # Teardown flags
    "orphan_risk",
    "manual_teardown",
)


# ═══════════════════════════════════════════════════════════════════════════════
# DISCOVERY STAGE — Product Subcategories
#
# Top-level product categories and their subcategories.  Used during
# discovery research before the full scoring run.
# ═══════════════════════════════════════════════════════════════════════════════

PRODUCT_SUBCATEGORIES = {
    "Cybersecurity": (
        "Endpoint Protection", "Detection & Response", "Data Protection",
        "Network Security", "Email Security", "Threat Intelligence",
        "SIEM/SOAR", "Identity & Access",
    ),
    "Cloud Infrastructure": (
        "Compute", "Networking", "Storage", "Containers & Kubernetes",
        "Serverless", "Database", "Identity & Access",
    ),
    "Data Protection": (
        "Backup & Recovery", "Disaster Recovery", "Data Management",
        "Archive & Compliance",
    ),
    "DevOps": (
        "CI/CD", "Infrastructure as Code", "Monitoring & Observability",
        "Configuration Management",
    ),
    "AI Platforms & Tooling": (
        "LLM Platforms", "Agent Frameworks", "Vector Databases",
        "LLMOps", "Fine-Tuning Platforms", "AI Dev Tools",
    ),
    "ERP": (
        "Financial Management", "HR & HCM", "Supply Chain",
    ),
    "CRM": (
        "Sales & Marketing", "Customer Service",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPETITIVE LANDSCAPE
#
# Key competitors with their strengths and gaps versus Skillable.
# Used to inform scoring evidence and competitive positioning.
# ═══════════════════════════════════════════════════════════════════════════════

COMPETITOR_PROFILES = {
    "Skytap": {
        "positioning": "Most frequently encountered",
        "strengths": "Windows workloads, legacy enterprise software, IBM enterprise credibility",
        "gaps_vs_skillable": "No PBT or scoring engine. No certified exam delivery. Weaker events infrastructure. IBM ownership adds sales cycle friction.",
    },
    "CloudShare": {
        "positioning": "Demo/POC-focused",
        "strengths": "Polished sharing and invite flows, SE demo environments, prospect engagement analytics",
        "gaps_vs_skillable": "Cannot handle complex multi-VM environments with private networks. Thin on complex enterprise applications. No PBT. Not built for training at scale.",
    },
    "Instruqt": {
        "positioning": "Developer-focused",
        "strengths": "Browser-native labs, excellent for CLI and cloud-native developer workflows, strong developer relations",
        "gaps_vs_skillable": "Primarily Docker/cloud-native only — weak on Windows enterprise, complex app stacks, or VM depth. No PBT. No networking depth.",
    },
    "Appsembler": {
        "positioning": "Niche — rarely encountered",
        "strengths": "Open source communities (open edX/Tahoe-LMS)",
        "gaps_vs_skillable": "Niche player. Not a meaningful competitor for enterprise prospects.",
    },
}

SKILLABLE_DECISIVE_ADVANTAGES = (
    "Performance-Based Testing (PBT) and Scoring — no competitor has a native scoring engine",
    "Complex multi-VM environments and flexible networking — CloudShare cannot support private networks",
    "Scale for events — proven at 30K+ attendees (Cisco Live, Hyland CommunityLIVE)",
    "Complex enterprise software depth — any software on Windows or Linux runs on Skillable",
    "Exam delivery (EDP) — integration with Pearson VUE, Certiport, PSI, Certiverse",
)


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING LOGIC VERSIONS — three tiers
#
# Frank's Rule #1 (2026-04-16): research is immutable. Logic changes never
# force re-research. To make that true in practice, version stamps are split
# into three tiers so cache invalidation can pick the cheapest path that
# satisfies the change:
#
#   SCORING_MATH_VERSION — bump when point values, dimension weights,
#     pillar weights, multiplier tables, penalty values, ACV rate tiers,
#     Verdict Grid thresholds, or any deterministic math change. Invalidation
#     path: pure-Python rescore against saved facts + saved rubric grades.
#     **Zero Claude calls. Milliseconds.**
#
#   RUBRIC_VERSION — bump when rubric tier definitions, signal categories,
#     grading criteria, or rubric_grader prompts change. Invalidation path:
#     re-run rubric_grader against saved raw facts, then pure-Python rescore.
#     **Paid Claude calls for grading (1 per dimension per product) but
#     zero re-research.**
#
#   RESEARCH_SCHEMA_VERSION — bump ONLY when the shape of the fact drawer
#     itself changes (fields added/removed, types changed). Invalidation
#     path: full re-research. **This is the only bump that burns research
#     dollars — deliberate human decision, rare.**
#
# Stamping contract:
#   Every saved discovery and analysis carries all three version fields.
#   The legacy `_scoring_logic_version` stamp is preserved for backwards
#   compatibility with existing caches stamped before this split.
#
# Bump format: "YYYY-MM-DD.short-description"
# ═══════════════════════════════════════════════════════════════════════════════

SCORING_MATH_VERSION = "2026-04-17.unscored-extrapolation-archetype-aware"
RUBRIC_VERSION = "2026-04-16.archetype-aware-iv-rubric"
RESEARCH_SCHEMA_VERSION = "2026-04-16.tiered-version-split-initial"

# Legacy single-string version — retained for backwards-compat reading of
# caches stamped before the three-tier split landed. New writes carry this
# field set to SCORING_MATH_VERSION so any consumer still reading the old
# field sees a current-looking value that tracks with the math tier.
SCORING_LOGIC_VERSION = SCORING_MATH_VERSION


# Sentinel returned by is_cached_logic_current_tiered() to describe exactly
# which tier of work is needed to bring a cached record current.
class CacheStatus:
    """What a cached record needs to be current.

    Returned by `is_cached_logic_current_tiered`. The caller uses this to
    pick the cheapest path that restores freshness.
    """
    CURRENT = "current"                    # All three versions match — cache hit, no work
    MATH_STALE = "math_stale"              # Math bump only — pure-Python recompute
    RUBRIC_STALE = "rubric_stale"          # Rubric bump — re-grade + recompute (no re-research)
    RESEARCH_STALE = "research_stale"      # Schema bump — re-research required
    UNSTAMPED = "unstamped"                # Legacy record, no tiered stamps — treat as research stale
                                           # to be safe (this should be rare after one-time migration)


def is_cached_logic_current(cached_data: dict | None) -> bool:
    """Legacy single-bit check — kept for backwards compatibility.

    Returns True when the cached record is fully current across all three
    tiers (MATH, RUBRIC, RESEARCH_SCHEMA). Returns False when any tier is
    stale OR when the record carries no version stamp at all.

    Prefer `is_cached_logic_current_tiered()` for new code — it returns
    fine-grained status so the caller can pick the cheapest invalidation
    path. This function remains the drop-in replacement for the legacy
    single-version check.
    """
    status = is_cached_logic_current_tiered(cached_data)
    return status == CacheStatus.CURRENT


def is_cached_logic_current_tiered(cached_data: dict | None) -> str:
    """Fine-grained version check — returns a CacheStatus string.

    Compares the three stamped versions (`_scoring_math_version`,
    `_rubric_version`, `_research_schema_version`) against the current
    constants and returns which (if any) tier is stale. The caller uses
    this to decide: pure-Python recompute (math), re-grade + recompute
    (rubric), or re-research (schema).

    Returns:
        CacheStatus.CURRENT        — all three match, no work needed
        CacheStatus.MATH_STALE     — math differs; rubric + schema current
        CacheStatus.RUBRIC_STALE   — rubric (and maybe math) differs; schema current
        CacheStatus.RESEARCH_STALE — schema differs; re-research required
        CacheStatus.UNSTAMPED      — legacy record with no tiered stamps

    Precedence: research > rubric > math. Schema drift implies everything
    downstream is also stale, so we return RESEARCH_STALE even if math is
    also different. Same logic for rubric.
    """
    if cached_data is None:
        return CacheStatus.CURRENT  # Caller handles None separately as a cache miss

    import logging
    _log = logging.getLogger(__name__)
    record_id = (
        cached_data.get("analysis_id")
        or cached_data.get("discovery_id")
        or "<unknown>"
    )

    cached_math = cached_data.get("_scoring_math_version", "")
    cached_rubric = cached_data.get("_rubric_version", "")
    cached_schema = cached_data.get("_research_schema_version", "")

    # Legacy record path: if none of the tiered stamps are present BUT the
    # old single-string stamp is, treat as UNSTAMPED so the caller can
    # apply a one-time migration (stamp with current versions, optionally
    # trigger rescoring paths).
    if not (cached_math or cached_rubric or cached_schema):
        legacy = cached_data.get("_scoring_logic_version", "")
        if legacy:
            _log.info(
                "is_cached_logic_current_tiered: record %s carries legacy "
                "_scoring_logic_version=%r but no tiered stamps — UNSTAMPED",
                record_id, legacy,
            )
            return CacheStatus.UNSTAMPED
        _log.info(
            "is_cached_logic_current_tiered: record %s has NO version stamps "
            "at all — UNSTAMPED", record_id,
        )
        return CacheStatus.UNSTAMPED

    # Precedence: schema drift wins (most expensive), then rubric, then math.
    if cached_schema != RESEARCH_SCHEMA_VERSION:
        _log.info(
            "is_cached_logic_current_tiered: record %s research_schema stamped "
            "%r, current %r — RESEARCH_STALE (re-research required)",
            record_id, cached_schema, RESEARCH_SCHEMA_VERSION,
        )
        return CacheStatus.RESEARCH_STALE
    if cached_rubric != RUBRIC_VERSION:
        _log.info(
            "is_cached_logic_current_tiered: record %s rubric stamped %r, "
            "current %r — RUBRIC_STALE (re-grade + recompute, no re-research)",
            record_id, cached_rubric, RUBRIC_VERSION,
        )
        return CacheStatus.RUBRIC_STALE
    if cached_math != SCORING_MATH_VERSION:
        _log.info(
            "is_cached_logic_current_tiered: record %s math stamped %r, "
            "current %r — MATH_STALE (pure-Python recompute, no Claude)",
            record_id, cached_math, SCORING_MATH_VERSION,
        )
        return CacheStatus.MATH_STALE
    return CacheStatus.CURRENT


# ═══════════════════════════════════════════════════════════════════════════════
# DEEP DIVE — SELECTION TUNABLES
#
# Caps and thresholds that govern the Product Selection page on Inspector.
# Centralized here so the value is the single source of truth — the template
# reads it through the Flask context, no hardcoded magic numbers in JS.
# ═══════════════════════════════════════════════════════════════════════════════

# Maximum number of NEW (uncached) products that can be added to a single
# Deep Dive run. Cached products reuse existing scores and never count
# against this cap — they always come along free. With cap=4, a company
# with 6 cached products can run a Deep Dive with all 6 cached + up to 4
# new = 10 total selected, triggering only 4 fresh Claude scoring calls.
#
# Bump this when:
#   - Claude throughput improves enough that more parallel scores are safe
#   - Frank decides Deep Dive should accept larger batches
# Don't bump it for one-off needs — the cap exists to keep one Deep Dive
# from monopolizing the API budget.
DEEP_DIVE_MAX_NEW_PRODUCTS = 4

# CSS class mapping for discovery tier labels (HIGH-11 in code-review-2026-04-07).
# Used by the tier_class Jinja filter in app.py. Centralized here so the
# template's CSS classes and the tier vocabulary stay in sync — if a new
# tier is added to DISCOVERY_TIER_LABELS, its CSS class lives next to it
# rather than buried in a hardcoded dict in the route file.
TIER_CSS_CLASSES = {
    "promising": "t-pr",
    "potential": "t-po",
    "uncertain": "t-u",
    "unlikely": "t-ul",
}

# CSS class mapping for deployment model badges (HIGH-10 in code-review-2026-04-07).
# Used by the deployment_color Jinja filter in app.py. Adding a new
# deployment model means adding it here AND to the canonical deployment
# model vocabulary, in one place.
DEPLOYMENT_MODEL_BADGE_CLASSES = {
    "installable": "badge-deploy-green",
    "hybrid": "badge-deploy-gray",
    "cloud": "badge-deploy-green",
    "saas-only": "badge-deploy-amber",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DOSSIER INFO MODAL CONTENT
#
# Why-What-How explanations for each Pillar and the ACV by Use Case widget.
# Surfaces in the dossier when the user clicks the (?) icon. Lives here in
# scoring_config rather than in the template JavaScript so:
#   1. Pillar weight references (50%, 20%, 30%) are computed dynamically
#      from PILLARS instead of hardcoded — they can never drift if you
#      change a pillar weight in this file.
#   2. Prospector and Designer can render the same explanations from the
#      same source when they need to.
#   3. Non-engineers can edit the explanatory copy without touching JS.
#
# HIGH-4 in code-review-2026-04-07.md.
# ═══════════════════════════════════════════════════════════════════════════════

def _build_modal_content() -> dict:
    """Build all info modal content from current pillar/dimension config.

    WHY → WHAT → HOW at every level. In-modal navigation via dimension
    links inside pillar modals. Eyebrow strings reference PILLARS
    dynamically so weight numbers never drift from config.

    Content hierarchy mirrors the scoring framework:
      Hero metrics (Fit Score, ACV Potential, Verdict)
        → Pillars (3)
          → Dimensions (4 per pillar = 12)
        → Seller Briefcase (3 sections)
        → Labability Tiers (discovery)
    """
    pl = next(p for p in PILLARS if p.name == "Product Labability")
    iv = next(p for p in PILLARS if p.name == "Instructional Value")
    cf = next(p for p in PILLARS if p.name == "Customer Fit")

    # Helper: scroll-to link for in-modal dimension navigation
    def _dim_scroll(anchor_id: str, label: str) -> str:
        return f'<a href="javascript:scrollToModalSection(\'{anchor_id}\')" class="info-modal-dim-link">{label}</a>'

    # Helper: dimension nav list with scroll-to links (stays within the same modal)
    def _dim_nav(dims: list[tuple[str, str, int]]) -> str:
        items = [f'<li>{_dim_scroll(k, n)} <span class="info-modal-dim-weight">({w} pts)</span></li>' for k, n, w in dims]
        return '<ul class="info-modal-dim-nav">' + ''.join(items) + '</ul>'

    # Helper: back-to-top link after each dimension section
    _back_top = '<a href="javascript:document.querySelector(\'.info-modal\').scrollTop=0" class="info-modal-back-top">↑ Back to top</a>'

    # Helper: framework map at the top of every pillar modal.
    # Produces a 3-column × 4-row table showing all three pillars and
    # their four dimensions in one glance.  The current pillar's column
    # is highlighted (accent color, "YOU ARE HERE" eyebrow, accent top
    # rule).  Pillar headers are clickable — jumping to a sibling pillar
    # opens that modal; the current pillar's header stays inert.  Current
    # dimensions link via in-modal scroll; sibling dimensions are passive
    # display (orientation only, not cross-modal navigation).
    #
    # This view is repeated at the top of every pillar modal so the reader
    # always sees where the current pillar sits inside the whole framework
    # — one document, connected to the overall structure.
    def _framework_map(current: str) -> str:
        pillars = [
            ("product_labability", "Product Labability", pl.weight, p1_dims),
            ("instructional_value", "Instructional Value", iv.weight, p2_dims),
            ("customer_fit", "Customer Fit", cf.weight, p3_dims),
        ]
        # Header row
        head_cells = []
        for key, name, weight, _dims in pillars:
            is_current = (key == current)
            klass = ' class="current"' if is_current else ""
            you_here = '<span class="fw-you-here">You are here</span>' if is_current else ""
            if is_current:
                pname = f'<span class="fw-pillar-name">{name}</span>'
            else:
                pname = f'<span class="fw-pillar-name"><a href="javascript:openInfoModal(\'{key}\')">{name}</a></span>'
            head_cells.append(f'<th{klass}>{pname}<span class="fw-weight">{weight}% of Fit Score</span>{you_here}</th>')
        # Body rows — 4 rows of dimensions, one cell per pillar per row
        body_rows = []
        for row_i in range(4):
            row_cells = []
            for key, _name, _weight, dims in pillars:
                is_current = (key == current)
                dim_key, dim_name, dim_weight = dims[row_i]
                if is_current:
                    # Current pillar's dimensions scroll within this modal
                    cell = f'{_dim_scroll(dim_key, dim_name)} <span class="fw-weight">({dim_weight} pts)</span>'
                    row_cells.append(f'<td class="current">{cell}</td>')
                else:
                    # Sibling pillar's dimensions — passive display; the pillar
                    # header above is already a clickable jump point.
                    row_cells.append(f'<td>{dim_name} <span class="fw-weight">({dim_weight} pts)</span></td>')
            body_rows.append("<tr>" + "".join(row_cells) + "</tr>")
        return ('<table class="info-modal-framework">'
                '<thead><tr>' + "".join(head_cells) + '</tr></thead>'
                '<tbody>' + "".join(body_rows) + '</tbody>'
                '</table>')

    # Helper: richer navigation footer at the end of each dimension section.
    # Produces a compact strip of cross-links: siblings in the same pillar,
    # back to the pillar overview (top of this modal), and a link to the
    # platform overview.  The seller or exec can jump between dimensions
    # without closing and re-opening a different help modal.
    def _dim_footer(siblings: list[tuple[str, str]], pillar_label: str = "pillar overview") -> str:
        sib_links = " · ".join(_dim_scroll(k, n) for k, n in siblings)
        parts = []
        if sib_links:
            parts.append(f'<span class="info-modal-nav-label">Related dimensions:</span> {sib_links}')
        parts.append(f'<a href="javascript:document.querySelector(\'.info-modal\').scrollTop=0" class="info-modal-dim-link">↑ Back to {pillar_label}</a>')
        parts.append('<a href="javascript:openInfoModal(\'platform_overview\')" class="info-modal-dim-link">Platform overview</a>')
        return '<div class="info-modal-dim-footer">' + ' &nbsp;·&nbsp; '.join(parts) + '</div>'

    # ── Pillar 1 dimensions ──
    p1_dims = [
        ("dim_provisioning", "Provisioning", 35),  # magic-allowed: dimension weight display
        ("dim_lab_access", "Lab Access", 25),  # magic-allowed: dimension weight display
        ("dim_scoring", "Scoring", 15),  # magic-allowed: dimension weight display
        ("dim_teardown", "Teardown", 25),  # magic-allowed: dimension weight display
    ]
    # ── Pillar 2 dimensions ──
    p2_dims = [
        ("dim_product_complexity", "Product Complexity", 40),  # magic-allowed: dimension weight display
        ("dim_mastery_stakes", "Mastery Stakes", 25),  # magic-allowed: dimension weight display
        ("dim_lab_versatility", "Lab Versatility", 15),  # magic-allowed: dimension weight display
        ("dim_market_demand", "Market Demand", 20),  # magic-allowed: dimension weight display
    ]
    # ── Pillar 3 dimensions ──
    p3_dims = [
        ("dim_training_commitment", "Training Commitment", 25),  # magic-allowed: dimension weight display
        ("dim_build_capacity", "Build Capacity", 20),  # magic-allowed: dimension weight display
        ("dim_delivery_capacity", "Delivery Capacity", 30),  # magic-allowed: dimension weight display
        ("dim_organizational_dna", "Organizational DNA", 25),  # magic-allowed: dimension weight display
    ]

    content = {}

    # ═══════════════════════════════════════════════════════════════════
    # PLATFORM OVERVIEW — tool-level WHY / WHAT / HOW
    #
    # Executive entry point.  Linked from every dimension footer so any
    # reader can zoom out from a specific number to the whole story of
    # what Skillable Intelligence does, who it serves, and how the three
    # tools compose.  Content sourced from Platform-Foundation.md.
    # ═══════════════════════════════════════════════════════════════════

    content["platform_overview"] = {
        "eyebrow": "SKILLABLE INTELLIGENCE · PLATFORM OVERVIEW",
        "title": "What this platform is, and why it matters",
        "sections": [
            {"label": "Why", "body":
                "<strong>Two questions decide every Skillable pursuit: should we pursue this, and how big is it if we win?</strong> For years those questions have been answered by gut feel, company size, and industry hype — none of which predict whether a product can actually be delivered as a lab or whether the customer is a training buyer. Skillable Intelligence replaces that guesswork with evidence. Every answer traces back to a specific product fact, a specific organizational signal, and a specific Skillable capability — so a seller, a marketer, or an exec can defend the recommendation end-to-end."
                "<br><br>"
                "The platform is <strong>product-up</strong>, not company-down. A product's fit with Skillable determines whether we can help a company at all. Start anywhere else and you get answers that look right and don't hold up."
            },
            {"label": "What", "body":
                "One shared intelligence layer feeds three tools. Each tool serves a different audience and a different moment in the pursuit."
                '<table class="info-modal-table"><thead><tr><th>Tool</th><th>Audience</th><th>Purpose</th></tr></thead><tbody>'
                '<tr><td><strong>Prospector</strong></td><td>Marketing · RevOps</td><td>Take a target-company list and re-rank by ACV potential with evidence-based rationale. Ship the sharpened list into HubSpot.</td></tr>'
                '<tr><td><strong>Inspector</strong></td><td>Sellers · SEs · CSMs · TSMs</td><td>Deep-dive any single company. See the Fit Score, the three pillars, the Seller Briefcase, the ACV by use case.</td></tr>'
                '<tr><td><strong>Designer</strong></td><td>Program owners · IDs · ProServ</td><td>Turn product intelligence into a buildable lab program — series, activities, scoring, bill of materials.</td></tr>'
                '</tbody></table>'
                "Customers never see Prospector or Inspector. Designer is the only customer-facing surface. This is an <em>architectural</em> wall, not a permission setting."
            },
            {"label": "How", "body":
                "Three layers of intelligence, each with a different job:"
                '<table class="info-modal-table"><thead><tr><th>Layer</th><th>Role</th><th>Refreshable?</th></tr></thead><tbody>'
                '<tr><td><strong>Research</strong></td><td>Pull raw, contextual facts about the company and its products — what it is, who uses it, how it installs, what APIs exist. Evidence + source + confidence.</td><td>Only when source data changes</td></tr>'
                '<tr><td><strong>Skillable capabilities</strong></td><td>The separate knowledge of what Skillable can do — fabrics, Sandbox API, AI Vision, Script Scoring, M365 tenants, rate tiers.</td><td>When capabilities evolve</td></tr>'
                '<tr><td><strong>Scoring + badges</strong></td><td>Apply the capabilities to the raw facts. Produce the Fit Score, the ACV, the Verdict, and the evidence badges that defend each number.</td><td>Any time — pure Python, milliseconds</td></tr>'
                '</tbody></table>'
                "Two hero numbers — <a href=\"javascript:openInfoModal('fit_score')\" class=\"info-modal-dim-link\">Fit Score</a> and <a href=\"javascript:openInfoModal('acv_potential')\" class=\"info-modal-dim-link\">ACV Potential</a> — compose into a single <a href=\"javascript:openInfoModal('verdict')\" class=\"info-modal-dim-link\">Verdict</a>. Three pillars make up the Fit Score: <a href=\"javascript:openInfoModal('product_labability')\" class=\"info-modal-dim-link\">Product Labability</a>, <a href=\"javascript:openInfoModal('instructional_value')\" class=\"info-modal-dim-link\">Instructional Value</a>, and <a href=\"javascript:openInfoModal('customer_fit')\" class=\"info-modal-dim-link\">Customer Fit</a>. Click any of them to see how the score is built from evidence."
            },
            {"label": "In practice", "body":
                "<strong>Reading the platform at a glance:</strong> the right rank in Prospector surfaces the company that matters. The right Fit Score in Inspector tells the seller whether to invest. The right ACV tells them how much the deal is worth if they win. The right Verdict tells them what to do — pursue, assess, watch, or walk. Nothing on any screen is opinion. Every score, every tier, every badge traces back to a specific fact, a specific capability, and a specific rule. That's what makes it defensible in a deal review, a board conversation, or a marketing brief."
            },
        ],
    }

    # ═══════════════════════════════════════════════════════════════════
    # HERO METRICS
    # ═══════════════════════════════════════════════════════════════════

    content["fit_score"] = {
        "eyebrow": "HERO METRIC · COMPOSITE SCORE",
        "title": "Fit Score",
        "sections": [
            {"label": "Why", "body": "Sellers and executives ask one question about every opportunity: <strong>should we pursue this?</strong> The Fit Score answers it with a single number (0–100) grounded in evidence — not gut feel, not company size, not industry hype. A high Fit Score means Skillable can deliver real lab value for this product at this company. A low one means the path isn't there today."},
            {"label": "What", "body": f"The Fit Score is a weighted composite of three Pillars:"
                f'<table class="info-modal-table"><thead><tr><th>Pillar</th><th>Weight</th><th>Level</th><th>Question</th></tr></thead><tbody>'
                f'<tr><td><a href="javascript:openInfoModal(\'product_labability\')" class="info-modal-dim-link">Product Labability</a></td><td><strong>{pl.weight}%</strong></td><td>Product</td><td>Can we build a lab for this product?</td></tr>'
                f'<tr><td><a href="javascript:openInfoModal(\'instructional_value\')" class="info-modal-dim-link">Instructional Value</a></td><td><strong>{iv.weight}%</strong></td><td>Product</td><td>Does this product warrant hands-on training?</td></tr>'
                f'<tr><td><a href="javascript:openInfoModal(\'customer_fit\')" class="info-modal-dim-link">Customer Fit</a></td><td><strong>{cf.weight}%</strong></td><td>Organization</td><td>Is this organization a good match for Skillable?</td></tr>'
                f'</tbody></table>'
                f"{pl.weight + iv.weight}% of the score is about the product (Product Labability + Instructional Value). {cf.weight}% is about the organization. The product is the hard constraint — a great customer with an unlabable product is not a Skillable opportunity."
            },
            {"label": "How", "body": "Each Pillar scores out of 100 internally, then gets weighted. The <em>Technical Fit Multiplier</em> enforces an asymmetric rule:"
                '<table class="info-modal-table"><thead><tr><th>Product Labability Score</th><th>Multiplier on IV + CF</th><th>Effect</th></tr></thead><tbody>'
                '<tr><td>≥ 60</td><td>1.0</td><td>Full contribution — strong product, no drag</td></tr>'
                '<tr><td>32–59 (datacenter)</td><td>1.0</td><td>Datacenter products protected — VM/ESX/Container</td></tr>'
                '<tr><td>32–59 (non-datacenter)</td><td>0.65</td><td>Meaningful drag — SaaS/cloud with uncertain provisioning</td></tr>'
                '<tr><td>19–31 (datacenter)</td><td>0.75</td><td>Moderate drag even for datacenter products</td></tr>'
                '<tr><td>19–31 (non-datacenter)</td><td>0.60</td><td>Significant drag — weak SaaS labability</td></tr>'
                '<tr><td>10–18</td><td>0.50</td><td>Heavy drag — very weak labability</td></tr>'
                '<tr><td>0–9</td><td>0.35</td><td>Near-total drag — product is nearly unlabable</td></tr>'
                '</tbody></table>'
                "Weak PL drags IV + CF down. Weak IV or CF does NOT drag PL down. A perfectly labable product with weak organizational signals is still a viable deal; a perfectly committed customer with an unlabable product is not."
            },
        ],
    }

    content["acv_potential"] = {
        "eyebrow": "HERO METRIC · DEAL SIZE",
        "title": "ACV Potential",
        "sections": [
            {"label": "Why", "body": "<strong>How big is this if we win?</strong> The Fit Score tells you whether to pursue. ACV Potential tells you how much the pursuit is worth. A product with a high Fit Score and low ACV is a real opportunity but a small one. A product with high ACV and low Fit Score is big but blocked. The seller needs both numbers to prioritize."},
            {"label": "What", "body": "ACV Potential is the estimated annual contract value if the customer standardized on Skillable across all training motions for the product. It's built from five consumption motions: Customer Training, Partner Training, Employee Training, Certification, and Events. Each motion has an audience (the people), an adoption rate (what percentage engage), and lab hours per learner. The bottom line is always <strong>lab hours consumed</strong>."},
            {"label": "How", "body": "Audience × Adoption × Hours = Annual Lab Hours. Annual Lab Hours × Rate = ACV."
                '<table class="info-modal-table"><thead><tr><th>Delivery Path</th><th>Rate</th><th>When it applies</th></tr></thead><tbody>'
                f'<tr><td>Cloud Labs</td><td>~${CLOUD_LABS_RATE:.0f}/hr</td><td>Azure-native, AWS-native, or Sandbox API products</td></tr>'
                f'<tr><td>Small VM / Container / Simulation</td><td>~${VM_LOW_RATE:.0f}/hr</td><td>Single VM, container-native, or simulation</td></tr>'
                f'<tr><td>Typical VM</td><td>~${VM_MID_RATE:.0f}/hr</td><td>1–3 VMs, standard footprint</td></tr>'
                f'<tr><td>Large / Complex VM</td><td>~${VM_HIGH_RATE:.0f}/hr</td><td>Multi-VM labs, complex topology, networking</td></tr>'
                '</tbody></table>'
                "Every input is a single estimated number, not a range. The rate is determined once during Product Labability scoring — the ACV calculation looks it up, never redefines it. Rate tier is driven by workload complexity (what the lab actually needs), not by the deployment label — a SaaS-delivered cybersecurity course still runs on VMs."
            },
        ],
    }

    content["verdict"] = {
        "eyebrow": "HERO METRIC · ACTION LABEL",
        "title": "Verdict",
        "sections": [
            {"label": "Why", "body": "\"Score = 74\" doesn't tell a seller what to <em>do</em>. The verdict combines the Fit Score and ACV Potential into an action label — <strong>Prime Target</strong>, <strong>Worth Pursuing</strong>, <strong>Keep Watch</strong>, <strong>Poor Fit</strong> — so the seller can prioritize without interpreting the numbers."},
            {"label": "What", "body": "Ten verdict labels on a grid. Fit Score determines the row. ACV tier determines the column. The intersection is the verdict."
                '<table class="info-modal-table"><thead><tr><th>Score</th><th>High ACV</th><th>Medium ACV</th><th>Low ACV</th></tr></thead><tbody>'
                '<tr><td><strong>≥ 80</strong></td><td>Prime Target</td><td>Strong Prospect</td><td>Good Fit</td></tr>'
                '<tr><td><strong>65–79</strong></td><td>High Potential</td><td>Worth Pursuing</td><td>Solid Prospect</td></tr>'
                '<tr><td><strong>25–64</strong></td><td>Assess First</td><td>Keep Watch</td><td>Deprioritize</td></tr>'
                '<tr><td><strong>&lt; 25</strong></td><td>Keep Watch</td><td>Poor Fit</td><td>Poor Fit</td></tr>'
                '</tbody></table>'
            },
            {"label": "How", "body": "The verdict is computed deterministically from Fit Score + ACV tier — no AI judgment. It updates automatically when the Fit Score or ACV changes. <strong>Prime Target</strong> = best possible combination, build a strategy. <strong>Poor Fit</strong> = products don't align, be honest about it."},
        ],
    }

    # ═══════════════════════════════════════════════════════════════════
    # PILLAR 1 — PRODUCT LABABILITY
    # ═══════════════════════════════════════════════════════════════════

    content["product_labability"] = {
        "eyebrow": f"PILLAR · GATEKEEPER · {pl.weight}% OF FIT SCORE",
        "title": pl.name,
        "sections": [
            {"label": "Where Product Labability sits in the framework", "body":
                "Three pillars compose the Fit Score. Product Labability is the heaviest because it's the gatekeeper — if Skillable cannot deliver the lab, nothing else matters. The four dimensions below are the lab lifecycle in sequence."
                + _framework_map("product_labability")
            },
            {"label": "Why Product Labability matters", "body": "<strong>Can we actually build a hands-on lab for this product?</strong> If Skillable cannot provision it, give every learner an isolated environment, automatically score what they do, and tear it down between sessions, nothing else matters. Product Labability is the gatekeeper — it carries the heaviest weight in the Fit Score because the product truth is the hard constraint."},
            {"label": "What Product Labability measures", "body": "Four dimensions, each answering one step of the lab lifecycle:" + _dim_nav(p1_dims)},
            {"label": "How the Product Labability score is built", "body":
                "Product Labability uses the <strong>canonical scoring model</strong> — fixed badge vocabulary, deterministic point lookup, color-aware credit (green = full points, amber = half, red = penalty). Zero AI in the scoring math."
                '<table class="info-modal-table"><thead><tr><th>Color</th><th>Meaning</th><th>Credit</th></tr></thead><tbody>'
                '<tr><td><strong>Green</strong></td><td>Works — confident, no action needed</td><td>Full points</td></tr>'
                '<tr><td><strong>Amber</strong></td><td>Uneasy — needs SE validation</td><td>Half points</td></tr>'
                '<tr><td><strong>Red</strong></td><td>Blocked — this specific thing is unavailable</td><td>Penalty</td></tr>'
                '<tr><td><strong>Gray</strong></td><td>Context — informational, no scoring impact</td><td>0 points</td></tr>'
                '</tbody></table>'
                "Risk cap reduction: each amber risk badge shaves -3 from the dimension cap. Each red blocker shaves -8. Caps never go below the dimension floor."
            },
            # ── Embedded dimension sections ──
            {"id": "dim_provisioning", "label": "Provisioning", "subtitle": "DIMENSION · 35 / 100 POINTS · HEAVIEST IN PILLAR 1", "body":
                "<strong>How do we get this product into Skillable?</strong> Provisioning is the heaviest dimension in Product Labability (35 of 100 points) because it determines difficulty for everything else. When a product runs in Skillable's own infrastructure (VM, container, Cloud Slice), Lab Access, Scoring, and Teardown are largely within Skillable's control. When it depends on a vendor's cloud API, every downstream dimension inherits that dependency. A provisioning failure cascades — if we can't deploy it, nothing else matters."
                "<br><br>The scorer walks a priority order of deployment fabrics and picks the FIRST viable path:"
                '<table class="info-modal-table"><thead><tr><th>Priority</th><th>Path</th><th>Badge</th><th>Green Credit</th></tr></thead><tbody>'
                '<tr><td>1</td><td>M365 Tenant / Admin</td><td>M365 Tenant / M365 Admin</td><td>+25 / +18</td></tr>'
                '<tr><td>2</td><td>VM fabric</td><td>Runs in VM / Runs in Container / ESX Required</td><td>+30 / +30 / +26</td></tr>'
                '<tr><td>3</td><td>Cloud Slice</td><td>Runs in Azure / Runs in AWS</td><td>+30</td></tr>'
                '<tr><td>4</td><td>Sandbox API (BYOC)</td><td>Sandbox API</td><td>+22</td></tr>'
                '<tr><td>5</td><td>Simulation</td><td>Simulation (gray)</td><td>Hard override: PL = 42</td></tr>'
                '</tbody></table>'
                "Penalties: GPU Required (-5), Socket Licensing (-2). Multi-fabric optionality: +3 per extra fabric, capped at +6."
                "<br><br>The order matters. The scorer picks the FIRST viable path, not the 'best' — by design. A datacenter VM is almost always easier to operate than a vendor's Sandbox API, even when both work, because everything downstream (identity, scoring, teardown) stays within Skillable's control. Cloud Slice sits third because it brings an extra vendor dependency. Sandbox API is a legitimate fourth because 'bring your own cloud' puts environment control in the vendor's hands. Simulation is last because nothing about it is a real environment — it's a narrative with points where an environment used to be."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 28 means Skillable has a native deployment path — the seller can commit to build without architectural improvisation. 18 to 28 means viable with real SE work to resolve (licensing, API coverage, partner coordination). Below 18 means the product fights against lab delivery today — either the underlying fabric isn't a fit or the vendor hasn't built the surfaces a per-learner environment needs. A Simulation fallback is a directional signal, not a commitment."
                + _dim_footer([("dim_lab_access", "Lab Access"), ("dim_scoring", "Scoring"), ("dim_teardown", "Teardown")], "Product Labability")
            },
            {"id": "dim_lab_access", "label": "Lab Access", "subtitle": "DIMENSION · 25 / 100 POINTS", "body":
                "<strong>Can each learner get an isolated environment with their own identity?</strong> Provisioning gets the environment built. Lab Access gets the <em>learner</em> into the environment — with their own credentials, reliably, without manual intervention at scale. A product can provision perfectly and still fail Lab Access if there's no way to give 500 learners their own credential path. This is where identity lifecycle, credential management, training licenses, and learner isolation live."
                '<table class="info-modal-table"><thead><tr><th>Badge</th><th>Green Credit</th><th>Notes</th></tr></thead><tbody>'
                '<tr><td>Full Lifecycle API</td><td>+23</td><td>Complete user provisioning API</td></tr>'
                '<tr><td>Entra ID SSO</td><td>+20</td><td>Azure-native only — zero credential management</td></tr>'
                '<tr><td>Identity API</td><td>+19</td><td>Create users and assign roles per learner</td></tr>'
                '<tr><td>Cred Recycling</td><td>+18</td><td>Self-sustaining credential pool</td></tr>'
                '<tr><td>Credential Pool / Training License</td><td>+16</td><td>Training License defaults to amber</td></tr>'
                '<tr><td>Manual SSO</td><td>+12</td><td>Azure SSO with manual learner login</td></tr>'
                '</tbody></table>'
                "Penalties: MFA Required (-15), Rate Limits (-5), Anti-Automation Controls (-5). Training License defaults to amber — real SE conversations happen around almost every licensing arrangement."
                "<br><br>The defaults are worth understanding. Training License defaulting to amber isn't a warning that the license is necessarily a problem — it's an acknowledgment that there's always a tier choice (Base vs Full vs Full+AI for M365, Commercial vs Training for most vendors), a concurrent-user count, or a regional restriction worth confirming. Green is reserved for truly zero-friction cases: open source with no concurrent-user model, or native SSO where identity is automatic. Everything in between deserves the SE's eyes."
                '<span class="info-modal-in-practice">In practice</span>'
                "Strong Lab Access (above 20) means every learner gets their own identity reliably at scale — zero manual intervention per run. Middle scores (12 to 20) mean an identity path exists but carries friction the SE needs to validate before committing to a cohort size. Low scores (below 12) mean shared credentials, MFA walls, or rate limits will drag every cohort — this is usually the blocker sellers hear about three weeks into implementation, not on day one."
                + _dim_footer([("dim_provisioning", "Provisioning"), ("dim_scoring", "Scoring"), ("dim_teardown", "Teardown")], "Product Labability")
            },
            {"id": "dim_scoring", "label": "Scoring", "subtitle": "DIMENSION · 15 / 100 POINTS", "body":
                "<strong>Can Skillable assess what the learner actually did?</strong> A lab that can't be scored isn't a lab — it's a guided tour. Without scoring, there's no proof the learner practiced, no certification evidence, and no way to measure learning outcomes. Scoring is about OPTIONS — full marks require more than one viable assessment path, because no single method covers every lab scenario. When a dimension shows 0/15 with no badges, the seller knows immediately: we have no way to validate learner work on this product."
                '<table class="info-modal-table"><thead><tr><th>Methods Present</th><th>Cap</th></tr></thead><tbody>'
                '<tr><td>AI Vision + Script Scoring (Grand Slam, VM)</td><td><strong>15</strong></td></tr>'
                '<tr><td>AI Vision + Scoring API (Grand Slam, cloud)</td><td><strong>15</strong></td></tr>'
                '<tr><td>Script Scoring alone</td><td><strong>15</strong> (VM — anything goes with shell access)</td></tr>'
                '<tr><td>Scoring API alone</td><td>12</td></tr>'
                '<tr><td>AI Vision alone</td><td>10</td></tr>'
                '<tr><td>Nothing (only MCQ or zero methods)</td><td>0</td></tr>'
                '</tbody></table>'
                "AI Vision is a peer to API/Script, not a fallback. GUI-driven products where state is visually evident. A real Skillable differentiator."
                "<br><br>The Grand Slam rule isn't arbitrary. Script Scoring covers what can be verified from inside a VM — files, services, configs, the real state of the machine. Scoring API covers what requires an external call because the environment doesn't give you shell access (cloud services, SaaS products). AI Vision covers what's only visible in the UI and can't be introspected any other way. Each method covers scenarios the others can't, which is why a single-method product caps below 15 — the coverage gap is real even when the one method works well."
                '<span class="info-modal-in-practice">In practice</span>'
                "A full 15 means we can prove the learner did the work — API, script, or vision validating actual state. 10 to 14 means one path (AI Vision alone or Scoring API alone) — scorable but narrower, and the seller should know which scenarios won't be covered. Zero means we can only test knowledge via multiple-choice, not performance. MCQ-only training isn't hands-on training — it's a quiz, and the seller should reframe the deal shape accordingly."
                + _dim_footer([("dim_provisioning", "Provisioning"), ("dim_lab_access", "Lab Access"), ("dim_teardown", "Teardown")], "Product Labability")
            },
            {"id": "dim_teardown", "label": "Teardown", "subtitle": "DIMENSION · 25 / 100 POINTS", "body":
                "<strong>Can we clean it up when it's over?</strong> Every lab has to end cleanly. Environment left behind = cost left behind, orphaned credentials left behind, data left behind, and the next learner contaminating the previous learner's session. Teardown failure is a Day 2 operational cost that outweighs Day 1 convenience. At 25 points, Teardown carries the same weight as Lab Access — cleanup is as important as setup."
                '<table class="info-modal-table"><thead><tr><th>Badge</th><th>Green Credit</th><th>Notes</th></tr></thead><tbody>'
                '<tr><td>Datacenter</td><td>+25 (full marks)</td><td>VM/ESX/Container — automatic teardown</td></tr>'
                '<tr><td>Teardown API</td><td>+22</td><td>Vendor API covers cleanup</td></tr>'
                '<tr><td>Simulation Reset</td><td>0 (display only)</td><td>Nothing to tear down — no credit for work that isn\'t real</td></tr>'
                '</tbody></table>'
                "Penalties: Manual Teardown (-10 red). Orphan Risk spectrum: Low Orphan Risk (green, 0 — rich API with minor gaps), Orphan Risk (-5 amber — partial API, gaps remain), High Orphan Risk (-15 red — no API or major cleanup gaps)."
                "<br><br>Orphan Risk is a spectrum, not a flag. Rich teardown APIs with minor gaps don't deduct — they're acknowledged as low-risk context. Partial API coverage with meaningful gaps (amber -5) means residue is likely if the SE doesn't build manual cleanup steps. No API at all or major cleanup gaps (red -15) means Skillable carries the operational cost every cohort. Every orphan-risk tier represents real Day-2 work and real Day-2 dollars — teardown isn't a feature checklist, it's a commitment to show up cleanly every session."
                '<span class="info-modal-in-practice">In practice</span>'
                "A clean Teardown score (above 20) means every cohort ends without leftover state — no orphaned tenants, no resource spend leaking, no previous-learner data bleeding into the next session. Middle scores mean some residue risk the SE needs to plan around. Low or zero means manual teardown between every learner — prohibitive at cohort scale, fatal at 1000-plus learners. High Orphan Risk is the deal sign that the customer will call us angry six months after go-live."
                + _dim_footer([("dim_provisioning", "Provisioning"), ("dim_lab_access", "Lab Access"), ("dim_scoring", "Scoring")], "Product Labability")
            },
            # ── Pillar-level closing rationale ──
            {"label": "In practice", "body":
                "<strong>Reading a Product Labability score:</strong> 70 and up means the product is genuinely lab-ready — the seller can commit to timeline without hedging. 50 to 69 means labable with known SE work to do; call the gaps out but don't walk away. 30 to 49 means the product fights us somewhere meaningful — a licensing wall, a missing API, or a fabric mismatch — and the deal conversation needs to shape around what the customer can change. Below 30 means the product isn't Skillable-addressable today without the customer changing something fundamental."
                "<br><br>"
                "Because Product Labability is the gatekeeper (50% of Fit Score, with asymmetric coupling), a weak PL score drags the whole deal — the Technical Fit Multiplier scales down Instructional Value and Customer Fit contributions. A strong training story and a training-mature customer cannot rescue an unlabable product. That's why this pillar carries the heaviest weight: the product truth is the hard constraint."
                "<br><br>"
                "<strong>Where to next?</strong> "
                "<a href=\"javascript:openInfoModal('instructional_value')\" class=\"info-modal-dim-link\">Instructional Value</a> — does this product warrant hands-on training at all? &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('customer_fit')\" class=\"info-modal-dim-link\">Customer Fit</a> — is the organization a training buyer? &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('fit_score')\" class=\"info-modal-dim-link\">Fit Score</a> — how the three pillars compose. &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('platform_overview')\" class=\"info-modal-dim-link\">Platform overview</a>."
            },
        ],
    }

    # ═══════════════════════════════════════════════════════════════════
    # PILLAR 2 — INSTRUCTIONAL VALUE
    # ═══════════════════════════════════════════════════════════════════

    content["instructional_value"] = {
        "eyebrow": f"PILLAR · {iv.weight}% OF FIT SCORE",
        "title": iv.name,
        "sections": [
            {"label": "Where Instructional Value sits in the framework", "body":
                "Three pillars compose the Fit Score. Instructional Value sits alongside Product Labability on the product side of the 70 / 30 split — together they answer whether this product is worth a hands-on training investment at all."
                + _framework_map("instructional_value")
            },
            {"label": "Why Instructional Value matters", "body": "Product Labability tells us <em>can</em> we lab this product. Instructional Value tells us <strong>should</strong> we — does this product genuinely warrant hands-on lab experiences, or is it a read-the-manual product? Combined with Product Labability, Instructional Value makes up 70% of the Fit Score."},
            {"label": "What Instructional Value measures", "body": "Four dimensions:" + _dim_nav(p2_dims)},
            {"label": "How the Instructional Value score is built", "body":
                "Instructional Value uses the <strong>rubric scoring model</strong> — category-aware baselines, AI-synthesized variable badge names, strength tiers (strong +6, moderate +3, informational 0). The posture is <em>default-positive</em>: most real software has instructional value for the right audience."
                '<table class="info-modal-table"><thead><tr><th>Strength Tier</th><th>Points (typical)</th><th>What it means</th></tr></thead><tbody>'
                '<tr><td><strong>Strong</strong></td><td>+5 to +9</td><td>Clear, compelling evidence</td></tr>'
                '<tr><td><strong>Moderate</strong></td><td>+3</td><td>Present but not dominant</td></tr>'
                '<tr><td><strong>Weak</strong></td><td>Don\'t emit</td><td>Too thin to carry a badge</td></tr>'
                '<tr><td><strong>Informational</strong></td><td>0</td><td>Context only — gray badge</td></tr>'
                '</tbody></table>'
                "Contributes to the Fit Score through the Technical Fit Multiplier — scaled by how labable the product actually is."
            },
            # ── Embedded dimension sections ──
            {"id": "dim_product_complexity", "label": "Product Complexity", "subtitle": "DIMENSION · 40 / 100 POINTS · HEAVIEST IN PILLAR 2", "body":
                "<strong>Is this product hard enough that someone needs hands-on practice?</strong> Product Complexity is the heaviest dimension in Instructional Value (40 of 100 points) because it answers the most fundamental instructional question: does hands-on practice actually matter for this product? A simple tool with a wizard UI doesn't need labs — reading the docs is enough. A multi-component security platform with 200+ configuration options, multiple admin roles, and cross-system integrations? Reading isn't enough. Practice is the difference between competence and confusion."
                '<table class="info-modal-table"><thead><tr><th>Category</th><th>Baseline</th></tr></thead><tbody>'
                '<tr><td>Cybersecurity, Cloud Infra, Networking, Data Science, DevOps, AI Platforms</td><td>32 / 40 (80%)</td></tr>'
                '<tr><td>ERP, CRM, Healthcare IT, FinTech, Legal Tech, App Dev</td><td>28 / 40 (70%)</td></tr>'
                '<tr><td>Collaboration, Content Management</td><td>24 / 40 (60%)</td></tr>'
                '<tr><td>Social / Entertainment</td><td>4 / 40 (10%)</td></tr>'
                '</tbody></table>'
                "Positive signals: multi_vm_architecture, deep_configuration, multi_phase_workflow, role_diversity, troubleshooting_depth, complex_networking, integration_complexity, ai_practice_required. Strong = +6, Moderate = +3."
                "<br><br>The baselines aren't arbitrary. Cybersecurity, Cloud, Networking, and AI Platforms sit at 80% because these categories are inherently multi-component, cross-role, and deeply configured — practice is how competence is built, not an optional supplement. ERP, CRM, Healthcare, FinTech sit at 70% because workflow depth varies widely product to product. Collaboration and Content Management sit at 60% because the workflow is real but the stakes and complexity are narrower. Social and entertainment sit at 10% because there is rarely a professional training market at all."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 32 means this product genuinely demands hands-on practice — the seller can anchor the deal on labs being necessary, not optional. 24 to 32 means practice matters but the customer might accept a lighter-touch curriculum. Below 24 means the product's complexity does not justify labs for most audiences — keep the conversation focused on specialist subsets where complexity does apply. A dimension this heavy carries the weight it does because every pillar below it leans on 'does practice matter here at all?'"
                + _dim_footer([("dim_mastery_stakes", "Mastery Stakes"), ("dim_lab_versatility", "Lab Versatility"), ("dim_market_demand", "Market Demand")], "Instructional Value")
            },
            {"id": "dim_mastery_stakes", "label": "Mastery Stakes", "subtitle": "DIMENSION · 25 / 100 POINTS", "body":
                "<strong>What are the consequences of getting it wrong?</strong> A product can be simple with high stakes (don't press the big red button) or complex with low stakes (a CI/CD pipeline where mistakes cost time, not money). Mastery Stakes asks whether getting it wrong in production has real consequences — breach, data loss, compliance failure, patient harm, financial damage. High stakes transform 'it's hard to learn' into 'they MUST be competent before they touch production.' This is why hands-on practice in a safe environment isn't just useful — it's necessary."
                '<table class="info-modal-table"><thead><tr><th>Category</th><th>Baseline</th></tr></thead><tbody>'
                '<tr><td>Cybersecurity, Healthcare IT, FinTech, Legal Tech, AI Platforms</td><td>22 / 25 (88%)</td></tr>'
                '<tr><td>ERP, Data Protection, Industrial/OT, Cloud Infra, DevOps</td><td>20 / 25 (80%)</td></tr>'
                '<tr><td>CRM, Collaboration</td><td>16 / 25 (64%)</td></tr>'
                '<tr><td>Social / Entertainment</td><td>2 / 25 (8%)</td></tr>'
                '</tbody></table>'
                "Strong tier credit = <strong>+9</strong> (higher than Product Complexity's +6) because a single high-stakes finding carries more weight."
                "<br><br>Stakes and complexity are distinct questions, and the framework treats them separately for a reason. Categories at 88% (cybersecurity, healthcare, fintech, legal, AI) get the highest baseline because a production mistake has consequences that cascade — regulatory, reputational, sometimes physical. Categories at 80% (ERP, data protection, industrial/OT) have serious business consequences but are usually recoverable. Categories at 64% have real consequences that are typically recoverable with work. The 8% floor for social and entertainment reflects the reality that mistakes there cost brand moments, not business continuity."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 20 means the stakes alone justify hands-on practice — the seller can anchor on 'prepare them before they touch production.' 14 to 20 means stakes are meaningful but recoverable — practice helps but isn't strictly necessary. Below 14 means a mistake costs time or inconvenience, not damage — the deal has to rest on Product Complexity or Market Demand, not consequence. When Mastery Stakes is high and Product Complexity is low (simple-but-dangerous products), the training story is 'procedure discipline.' When both are high, the story is 'deep competence.'"
                + _dim_footer([("dim_product_complexity", "Product Complexity"), ("dim_lab_versatility", "Lab Versatility"), ("dim_market_demand", "Market Demand")], "Instructional Value")
            },
            {"id": "dim_lab_versatility", "label": "Lab Versatility", "subtitle": "DIMENSION · 15 / 100 POINTS", "body":
                "<strong>What kinds of high-value hands-on experiences could we build?</strong> Lab Versatility is the bridge from Inspector to Designer. It asks whether the product naturally supports diverse lab types — adversarial scenarios, break/fix, migration labs, compliance audits, performance tuning. A product that only supports one kind of lab is less commercially valuable than one that supports many. The lab types identified here become starting points for Designer's program recommendations and give sellers specific conversational competence points."
                '<table class="info-modal-table"><thead><tr><th>Lab Types (from the Lab Type Menu)</th></tr></thead><tbody>'
                '<tr><td>Red vs Blue · Simulated Attack · Incident Response · Break/Fix · Team Handoff · Bug Bounty · Cyber Range · Performance Tuning · Migration Lab · Architecture Challenge · Compliance Audit · Disaster Recovery · CTF</td></tr>'
                '</tbody></table>'
                "Cybersecurity, Cloud Infra, Networking = 14/15 (93%). Data Science = 13/15. ERP, Healthcare = 12/15. Social = 1/15. Strong = +5, Moderate = +3."
                "<br><br>Versatility isn't about supporting every lab type — it's about supporting some lab type naturally, without forcing the design. Cybersecurity products support Red vs Blue, Incident Response, CTF, and Cyber Range out of the box. Cloud products support Migration, Architecture Challenge, and Disaster Recovery. A product that only fits one lab type is less commercially valuable than one that fits many — because the same product can then serve different learners in different ways. This dimension also bridges Inspector to Designer: the lab types identified here seed Designer's program recommendations."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 12 means the product offers rich program variety — the seller can pitch multi-course curricula and different learner audiences. 9 to 12 means a solid core set of lab types. Below 9 means the product supports one or two lab patterns — still valuable for that one motion, but the deal has to be shaped around a focused story rather than a broad program. Versatility is where a strong Fit Score turns into a strong Designer brief."
                + _dim_footer([("dim_product_complexity", "Product Complexity"), ("dim_mastery_stakes", "Mastery Stakes"), ("dim_market_demand", "Market Demand")], "Instructional Value")
            },
            {"id": "dim_market_demand", "label": "Market Demand", "subtitle": "DIMENSION · 20 / 100 POINTS", "body":
                "<strong>How big is the worldwide population of people who need to learn this product?</strong> Market Demand is the legitimacy check — does the outside world validate that training on this product is worth delivering? A product can be complex and high-stakes but if nobody's building training for it, the market may not be ready. ATP networks, cert exams, conference presence, and the independent training market (Coursera, Pluralsight, LinkedIn Learning) are strong signals. A perfect 20/20 is rare — reserved for products with demonstrably massive training demand like CrowdStrike or AWS."
                '<table class="info-modal-table"><thead><tr><th>Category</th><th>Baseline</th></tr></thead><tbody>'
                '<tr><td>Cybersecurity, Cloud Infra, AI Platforms</td><td>14 / 20 (70%)</td></tr>'
                '<tr><td>Networking, DevOps</td><td>13 / 20 (65%)</td></tr>'
                '<tr><td>Data Science</td><td>12 / 20 (60%)</td></tr>'
                '<tr><td>CRM, Collaboration, Content Management</td><td>8 / 20 (40%)</td></tr>'
                '<tr><td>Social / Entertainment</td><td>0 / 20 (0%)</td></tr>'
                '</tbody></table>'
                "Signals: install base scale, cert ecosystem, independent training market (Coursera/Pluralsight/LinkedIn Learning counts), competitor labs. Important: user population is NOT training population — 2 billion casual users with 200 admins = small Market Demand. Strong = +5, Moderate = +3."
                "<br><br>User population is not training population, and this dimension enforces the distinction. A product with 2 billion casual users and 200 administrators has a small Market Demand — the seller's audience is the 200 admins, not the 2 billion users. ATP networks, cert programs, independent training catalogs, and conference presence are the signals that a product already has a training market worth serving. A 20 of 20 is rare by design — reserved for products with demonstrably massive training demand like AWS, Azure, or CrowdStrike."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 16 means there's a validated training market — the seller doesn't have to justify demand, just capture share. 11 to 16 means real demand but narrower — niche-specialist audiences with clear buying signals. Below 11 means the platform can lab the product, but the question 'who actually wants this training?' hasn't been answered. A gap between a high Product Complexity score and a low Market Demand score is a tell: the product is interesting, but not commercial."
                + _dim_footer([("dim_product_complexity", "Product Complexity"), ("dim_mastery_stakes", "Mastery Stakes"), ("dim_lab_versatility", "Lab Versatility")], "Instructional Value")
            },
            # ── Pillar-level closing rationale ──
            {"label": "In practice", "body":
                "<strong>Reading an Instructional Value score:</strong> 80 and up means this product genuinely warrants hands-on training — complex, high-stakes, versatile lab opportunities, real market demand. The seller can pitch broad, multi-audience programs with confidence. 60 to 79 means a solid instructional case with one or two dimensions softer than the rest; know which one and shape the pitch accordingly. 40 to 59 means the case exists for specialist audiences but the broad training story is strained. Below 40 means the product doesn't earn hands-on training today — it might be labable, but the 'should we' answer is thin."
                "<br><br>"
                "Like Customer Fit, Instructional Value contributes through the Technical Fit Multiplier — strong IV cannot rescue weak Product Labability, and weak IV drags a strong PL deal the same way. This pillar answers the commercial question every exec asks: 'is the training market for this product worth Skillable's effort?'"
                "<br><br>"
                "<strong>Where to next?</strong> "
                "<a href=\"javascript:openInfoModal('product_labability')\" class=\"info-modal-dim-link\">Product Labability</a> — can we actually build the lab? &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('customer_fit')\" class=\"info-modal-dim-link\">Customer Fit</a> — is the organization a training buyer? &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('fit_score')\" class=\"info-modal-dim-link\">Fit Score</a> — how the three pillars compose. &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('platform_overview')\" class=\"info-modal-dim-link\">Platform overview</a>."
            },
        ],
    }

    # ═══════════════════════════════════════════════════════════════════
    # PILLAR 3 — CUSTOMER FIT
    # ═══════════════════════════════════════════════════════════════════

    content["customer_fit"] = {
        "eyebrow": f"PILLAR · {cf.weight}% OF FIT SCORE",
        "title": cf.name,
        "sections": [
            {"label": "Where Customer Fit sits in the framework", "body":
                "Three pillars compose the Fit Score. Customer Fit is the 30% organizational side of the 70 / 30 split — a great product still needs a training buyer, and every product from the same company shares this one Customer Fit reading."
                + _framework_map("customer_fit")
            },
            {"label": "Why Customer Fit matters", "body": "Even the most labable product with the highest instructional value goes nowhere if the customer isn't a training buyer. <strong>Is this organization actually the kind of place Skillable can help?</strong> Customer Fit measures the organization, not the product — every product from the same company gets the same Customer Fit reading."},
            {"label": "What Customer Fit measures", "body": "Four dimensions, in the order a seller naturally thinks about a customer's training maturity:" + _dim_nav(p3_dims)},
            {"label": "How the Customer Fit score is built", "body":
                "Customer Fit uses the <strong>rubric scoring model</strong> with organization-type baselines (not product category baselines like Pillar 2)."
                '<table class="info-modal-table"><thead><tr><th>Organization Type</th><th>Typical Baseline Range</th></tr></thead><tbody>'
                '<tr><td>Training Org / Industry Authority</td><td>80–92%</td></tr>'
                '<tr><td>Enterprise Software / Professional Services</td><td>64–72%</td></tr>'
                '<tr><td>Software (category-specific)</td><td>50–64%</td></tr>'
                '<tr><td>LMS Provider / Tech Distributor</td><td>36–45%</td></tr>'
                '</tbody></table>'
                "Like Instructional Value, Customer Fit contributes through the Technical Fit Multiplier — the strongest training story doesn't close a deal if the product can't be lab-delivered."
            },
            # ── Embedded dimension sections ──
            {"id": "dim_training_commitment", "label": "Training Commitment", "subtitle": "DIMENSION · 25 / 100 POINTS", "body":
                "<strong>Does this organization have a heart for teaching?</strong> Training Commitment is philosophical, not operational — it's about whether the company believes in investing in people's skills. A training catalog that exists is a start. Named leadership, multi-audience programs (customers AND partners AND employees), and a culture of investing in people show deeper commitment. This dimension separates companies that genuinely care about enablement from those that check a box."
                '<table class="info-modal-table"><thead><tr><th>Org Type</th><th>Baseline</th></tr></thead><tbody>'
                '<tr><td>Training Org</td><td>23 / 25 (92%)</td></tr>'
                '<tr><td>Academic / Content Development</td><td>22 / 25 (88%)</td></tr>'
                '<tr><td>Enterprise Software / Professional Services</td><td>18 / 25 (72%)</td></tr>'
                '<tr><td>Software / Systems Integrator</td><td>16 / 25 (64%)</td></tr>'
                '<tr><td>Tech Distributor</td><td>9 / 25 (36%)</td></tr>'
                '</tbody></table>'
                "Audiences served: employees, customers, partners, end-users at scale. An organization that trains ONE audience is making some commitment. All three = highest level. Strong = +6, Moderate = +3. Penalties: no_customer_training (-4), thin_cert_program (-3)."
                "<br><br>An organization that trains only one audience (employees, or customers, or partners) is making a real but partial commitment. An organization that trains employees AND customers AND partners AND delivers at scale is operating at the highest level — this is what separates Salesforce, Microsoft, and CompTIA from companies that publish a training catalog as marketing. Named enablement leadership, formal customer success investment, and a culture of continuous learning are the durable signals. Penalties fire when external evidence of customer training is thin — vendor marketing doesn't count as proof."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 20 means a training-mature organization — the seller is talking to a buyer who already believes in the investment. 15 to 20 means commitment is real but uneven; expect a longer education cycle. Below 15 means the customer is not yet a training buyer — the deal requires someone inside the company to champion the category itself, not just the Skillable-vs-alternative decision. Training Commitment is the first dimension to check because a weak score here predicts a longer, harder sell on everything downstream."
                + _dim_footer([("dim_build_capacity", "Build Capacity"), ("dim_delivery_capacity", "Delivery Capacity"), ("dim_organizational_dna", "Organizational DNA")], "Customer Fit")
            },
            {"id": "dim_build_capacity", "label": "Build Capacity", "subtitle": "DIMENSION · 20 / 100 POINTS · LOWEST WEIGHT — PROSERV CAN FILL THIS GAP", "body":
                "<strong>Can they create the labs?</strong> Build Capacity carries the lowest weight in Pillar 3 (20 points) because Skillable Professional Services can fill this gap — if a company has strong Training Commitment and Delivery Capacity but weak Build Capacity, that's a ProServ opportunity, not a dead end. The dimension is also inward-facing and hard to verify from external research, so baselines are cautious and penalties fire only with direct evidence."
                '<table class="info-modal-table"><thead><tr><th>Org Type</th><th>Baseline</th></tr></thead><tbody>'
                '<tr><td>Content Development</td><td>14 / 20 (70%)</td></tr>'
                '<tr><td>Academic / Training Org / Professional Services</td><td>12 / 20 (60%)</td></tr>'
                '<tr><td>Systems Integrator / Enterprise Software</td><td>11 / 20 (55%)</td></tr>'
                '<tr><td>Software / Unknown</td><td>10 / 20 (50%)</td></tr>'
                '</tbody></table>'
                "Strongest signal: <strong>DIY Labs</strong> — already building hands-on labs today. CREATE roles, not delivery roles. Cautious penalties only: confirmed_outsourcing (-3), no_authoring_roles_found (-3, requires explicit evidence). Strong = +5, Moderate = +3."
                "<br><br>The strongest positive signal is DIY Labs — if the organization already builds hands-on labs today (internal platforms like Qwiklabs for Google, CML for Cisco, iLabs for EC-Council), they understand the value and the work. That same signal is also an amber risk: we're pitching Skillable against something the customer already invested in. Build Capacity is also the dimension where 'absence of evidence is not evidence of absence' applies strongest — internal authoring teams rarely show up in public research, so baselines cluster in the middle and penalties require explicit signals (case studies of outsourcing, documented absence of authoring roles)."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 16 means the customer can build with us or even author independently — ProServ scope is limited, the customer is the co-pilot. 12 to 16 means middle capacity — ProServ scope is moderate, some handoff to internal teams is possible. Below 12 means the customer lacks the roles to build; ProServ becomes the full engagement. A low Build Capacity score isn't a deal-killer, it's a scope signal — it tells the Skillable team how big the ProServ attach needs to be."
                + _dim_footer([("dim_training_commitment", "Training Commitment"), ("dim_delivery_capacity", "Delivery Capacity"), ("dim_organizational_dna", "Organizational DNA")], "Customer Fit")
            },
            {"id": "dim_delivery_capacity", "label": "Delivery Capacity", "subtitle": "DIMENSION · 30 / 100 POINTS · HEAVIEST IN PILLAR 3", "body":
                "<strong>Can they get labs to learners at scale?</strong> Delivery Capacity is the heaviest dimension in Customer Fit (30 of 100 points) because having labs = cost, but delivering labs to learners = value. Without delivery infrastructure — ATPs, partner networks, ILT calendar, conference presence — labs are a cost center that never reaches the audience. This dimension is where commercial value lives. Penalties are aggressive: no training partners or no classroom delivery are both red blockers (-10 each)."
                "<br><br>Three delivery layers that stack:"
                '<table class="info-modal-table"><thead><tr><th>Layer</th><th>What it is</th><th>Tier credit</th></tr></thead><tbody>'
                '<tr><td><strong>1. Vendor-Delivered</strong></td><td>Official ILT, self-paced portal, vendor-run labs</td><td>Base</td></tr>'
                '<tr><td><strong>2. Third-Party-Delivered</strong></td><td>Independent training market + cert body curricula</td><td>Bonus</td></tr>'
                '<tr><td><strong>3. Auth-Partner-Delivered</strong></td><td>Formal ATP/ALP program at scale</td><td>Top bonus</td></tr>'
                '</tbody></table>'
                "Strong = <strong>+8</strong>, Moderate = +4 (highest tier credits in the framework). Aggressive penalties: no_training_partners (-10 red), no_classroom_delivery (-10 red), no_independent_training_market (-4 amber, cross-pillar with Market Demand)."
                "<br><br>The three delivery layers stack, and each additional layer is a real multiplier on reach. Vendor-Delivered is the base — official ILT, self-paced portals, and vendor-run labs. Third-Party-Delivered adds Coursera, Pluralsight, LinkedIn Learning counts, plus cert body curricula — evidence that independent training markets have formed around the product. Authorized-Partner-Delivered adds formal ATP or ALP programs at scale, multiplying geographic reach. Penalties fire aggressively here because outward-facing delivery infrastructure is public — if we can't find it, that's strong evidence it doesn't exist at the scale the deal needs."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 24 means the customer has real reach — ATP networks, independent training markets, conference scale. The seller doesn't have to build distribution. 18 to 24 means one or two delivery layers but not all three; know which layer is missing and how that shapes the deal. Below 18 means the customer can buy labs but has limited ability to reach learners — every seat has to be sold one at a time. Red blockers (no training partners, no classroom delivery) collapse this dimension fastest and signal the deal will struggle to scale even if it closes."
                + _dim_footer([("dim_training_commitment", "Training Commitment"), ("dim_build_capacity", "Build Capacity"), ("dim_organizational_dna", "Organizational DNA")], "Customer Fit")
            },
            {"id": "dim_organizational_dna", "label": "Organizational DNA", "subtitle": "DIMENSION · 25 / 100 POINTS", "body":
                "<strong>If Skillable proposes a strategic relationship, will they see it as a partnership or a procurement line item?</strong> Organizational DNA is the most consequential partnership question. Some companies see outside platforms as strategic assets (Salesforce for CRM, Workday for HR, Okta for identity). Others see every vendor as a cost to control. The first kind makes a great Skillable customer. The second kind makes a painful one. This dimension captures the cultural pattern, not individual partnerships."
                '<table class="info-modal-table"><thead><tr><th>Org Type</th><th>Baseline</th></tr></thead><tbody>'
                '<tr><td>Training Org / Content Development</td><td>19 / 25 (76%)</td></tr>'
                '<tr><td>Professional Services / Systems Integrator</td><td>18 / 25 (72%)</td></tr>'
                '<tr><td>Enterprise Software / Tech Distributor</td><td>17 / 25 (68%)</td></tr>'
                '<tr><td>Software / LMS Provider</td><td>16 / 25 (64%)</td></tr>'
                '</tbody></table>'
                "Positive: many_partnership_types, strategic_asset_partnerships, platform_buyer_behavior, named_alliance_leadership. Penalties: long_rfp_process (-4), build_everything_culture (-4), heavy_procurement (-3), hard_to_engage (-6 red)."
                "<br><br>This is the partnership question, not the product question. Some companies treat outside platforms as strategic assets and work with them accordingly — joint roadmap sessions, executive sponsorship, named alliance leadership. Others treat every vendor as a procurement line to squeeze — long RFPs, heavy legal cycles, a build-everything culture that sees external partners as cost centers. The first kind becomes a reference customer; the second kind becomes a painful one, and the pattern usually doesn't change inside a single deal cycle. This dimension captures the cultural pattern, not any single partnership."
                '<span class="info-modal-in-practice">In practice</span>'
                "Above 20 means a partnership-culture organization — expect a strategic conversation, joint planning, and real executive engagement. 15 to 20 means partnerships are possible but transactional — the seller will do more of the relationship-building work. Below 15 means a procurement-culture organization — the deal will be commoditized fast and the seller should either accept commodity terms or decline the cycle. A red Blocker here (hard-to-engage, -6) is usually a sign the deal isn't worth the time."
                + _dim_footer([("dim_training_commitment", "Training Commitment"), ("dim_build_capacity", "Build Capacity"), ("dim_delivery_capacity", "Delivery Capacity")], "Customer Fit")
            },
            # ── Pillar-level closing rationale ──
            {"label": "In practice", "body":
                "<strong>Reading a Customer Fit score:</strong> 75 and up means a training-mature, partnership-oriented organization — the seller is talking to a buyer, not a browser. 55 to 74 means real fit with some dimensions softer than others; know which one (Build Capacity? Delivery Capacity?) and shape the deal accordingly. 35 to 54 means the customer isn't yet ready for the category, for Skillable, or for both — the cycle needs to start with category education, not vendor differentiation. Below 35 means the customer is fundamentally misaligned with Skillable today; revisit when something structural changes (new training leadership, new buying center, public partnership announcement)."
                "<br><br>"
                "Because Customer Fit measures the organization rather than the product, every product from the same company receives the same Customer Fit reading — one organization, one reading. This is why a strong Product Labability score on product X and a weak Customer Fit score on that same company means: we can build the lab, but they can't buy it. The seller's job then is either to find the right buying center inside the organization or to accept that this isn't a Skillable cycle yet."
                "<br><br>"
                "<strong>Where to next?</strong> "
                "<a href=\"javascript:openInfoModal('product_labability')\" class=\"info-modal-dim-link\">Product Labability</a> — can we actually build the lab? &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('instructional_value')\" class=\"info-modal-dim-link\">Instructional Value</a> — does this product warrant hands-on training? &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('fit_score')\" class=\"info-modal-dim-link\">Fit Score</a> — how the three pillars compose. &nbsp;·&nbsp; "
                "<a href=\"javascript:openInfoModal('platform_overview')\" class=\"info-modal-dim-link\">Platform overview</a>."
            },
        ],
    }

    # ═══════════════════════════════════════════════════════════════════
    # SELLER BRIEFCASE
    # ═══════════════════════════════════════════════════════════════════

    content["briefcase_ktq"] = {
        "eyebrow": "SELLER BRIEFCASE · PRODUCT LABABILITY",
        "title": "Key Technical Questions",
        "sections": [
            {"label": "Why", "body": "The seller needs to know <strong>who to find at the customer, what department, and what specific technical questions unblock the lab build</strong>. These are questions TO ASK — action items for the seller, not evidence about the product."},
            {"label": "What", "body": "2–3 sharp, specific, answerable questions. Each names the person or department to find and includes a verbatim question the champion can send. The questions target gaps discovered during Product Labability research — licensing clarity, API access, identity provisioning, environment availability."},
            {"label": "How", "body": "Generated by a focused Claude call (Opus) using the Product Labability fact drawer. The prompt emphasizes: specific, answerable, names a person. Not generic. Not a list of everything we don't know."},
        ],
    }

    content["briefcase_conversation"] = {
        "eyebrow": "SELLER BRIEFCASE · INSTRUCTIONAL VALUE",
        "title": "Conversation Starters",
        "sections": [
            {"label": "Why", "body": "Sellers talking to technical buyers need conversational competence — <strong>they need to understand the product well enough to be credible without being technical</strong>. Conversation Starters make the seller sound prepared, not scripted."},
            {"label": "What", "body": "2–3 product-specific talking points about why hands-on training matters for THIS product. Market Demand evidence belongs here — \"47,000 Stack Overflow questions\" or \"~14M active users\" is proof the training market exists. This is NOT a Key Technical Question — it's ammunition for the conversation."},
            {"label": "How", "body": "Generated by a focused Claude call (Haiku) using the Instructional Value fact drawer. Pattern-matched, fast. Product-specific, not boilerplate."},
        ],
    }

    content["briefcase_intel"] = {
        "eyebrow": "SELLER BRIEFCASE · CUSTOMER FIT",
        "title": "Account Intelligence",
        "sections": [
            {"label": "Why", "body": "<strong>Context that shows the seller has done their homework.</strong> When the seller walks into a meeting knowing the customer's training leadership, LMS platform, competitive lab landscape, and recent news, the conversation starts at a higher level."},
            {"label": "What", "body": "Organizational signals — training leadership (names and titles), org complexity, LMS platform, competitive signals (who else is in the lab space for this customer), recent news. Delivery partner network context: \"CompTIA has ~3,000 ATPs globally, Pearson handles exam delivery.\""},
            {"label": "How", "body": "Generated by a focused Claude call (Haiku) using the Customer Fit fact drawer and company signals. Surfaces organizational patterns, not product details."},
        ],
    }

    # ═══════════════════════════════════════════════════════════════════
    # ACV USE CASE WIDGET
    # ═══════════════════════════════════════════════════════════════════

    content["acv_use_case"] = {
        "eyebrow": "WIDGET · DEAL STORY BY MOTION",
        "title": "ACV by Use Case",
        "sections": [
            {"label": "Why", "body": "A single ACV number hides the real story. <strong>Where does the deal actually live?</strong> Is it driven by partner channel training? Annual conference events? Certification? Internal enablement? The motions that make up the total are not interchangeable — sellers need to know which one to talk about first."},
            {"label": "What", "body": "Five consumption motions: <strong>Customer Training</strong> (total product users × ~4% × 2 hrs — the big one, includes learners who train through ATPs), <strong>Partner Training</strong> (channel partner employees — GSI/VAR consultants and SEs who sell, deploy, implement × ~15% × 5 hrs), <strong>Employee Training</strong> (the company's own product team, support, SEs × ~30% × 8 hrs — always small), <strong>Certification</strong> (exam candidates × 100% × 1 hr), <strong>Events</strong> (conference attendees × ~30% × 1 hr). Each row: Audience × Adoption × Hours = Annual Lab Hours."},
            {"label": "How", "body": "Every input is a single estimated number — not a range. The rate comes from the product's delivery path (determined during Pillar 1 scoring). Audiences are concrete research signals: partner program size, conference attendance, certification volume, employee count, install base. The total should match the ACV Potential in the hero section."
                "<br><br><strong>Adoption varies by org type.</strong> Software companies: voluntary (~4% training adoption). Industry Authorities: intentional (~4% training, but cert exam audience is much smaller than training audience — ~10% of trainees sit the exam). Academic: required (~90%+ adoption — coursework is assigned). The audience numbers in each row reflect these patterns — the adoption rate is applied to the right-sized audience for this organization type."},
        ],
    }

    # ═══════════════════════════════════════════════════════════════════
    # LABABILITY TIERS (DISCOVERY)
    # ═══════════════════════════════════════════════════════════════════

    content["labability_tiers"] = {
        "eyebrow": "DISCOVERY · PRE-DEEP DIVE ESTIMATES",
        "title": "Labability Tiers",
        "sections": [
            {"label": "Why", "body": "Before a full Deep Dive, the platform provides a <strong>directional estimate</strong> of how likely each product is to work on Skillable. These tiers help the seller and marketing prioritize which products to investigate further — without overpromising."},
            {"label": "What", "body": "<strong>Promising</strong> (score ≥ 65) — strong signals, this looks good. <strong>Potential</strong> (score ≥ 45) — something here, needs validation. <strong>Uncertain</strong> (score ≥ 25) — could go either way. <strong>Unlikely</strong> (score < 25) — significant barriers visible. These are pre-Deep Dive estimates, not conclusions."},
            {"label": "How", "body": "The score is based on deployment model (installable = 65–90, cloud = 50–75, SaaS with API = 30–45, SaaS without API = 10–25), technical depth, market category, and training signals. Thresholds align with the Verdict Grid color bands (Green ≥ 65, Light Amber ≥ 45, Amber ≥ 25, Red < 25) for consistency across the platform."},
        ],
    }

    return content


MODAL_CONTENT = _build_modal_content()


# ═══════════════════════════════════════════════════════════════════════════════
# PROSPECTOR MODAL CONTENT
#
# In-app documentation for Prospector ? icons. Same pattern as Inspector
# modals — content lives in scoring_config so it's Define-Once and can
# reference actual pillar weights, rates, and thresholds without drift.
# ═══════════════════════════════════════════════════════════════════════════════

PROSPECTOR_MODAL_CONTENT = {
    "company_list": {
        "eyebrow": "PROSPECTOR",
        "title": "Researched Companies",
        "sections": [
            {
                "heading": "What this list shows",
                "body": (
                    "Every company the platform has researched — through Prospector batch runs or "
                    "Inspector searches. Rows are ranked by ACV Potential midpoint (highest first). "
                    "Each row shows the company's classification badge, ACV Potential range with "
                    "confidence, Deep Dive coverage, the top product, and a one-line top signal. "
                    "Click any ACV cell to open the full rationale + drivers + caveats."
                ),
            },
            {
                "heading": "How ACV Potential is produced",
                "body": (
                    "ACV Potential comes from one of two paths depending on whether a Deep Dive "
                    "has been run:<br><br>"
                    "<strong>Discovery-level (default)</strong> — a single holistic Claude call at "
                    "research time reasons across all products, training signals, partner ecosystem, "
                    "certification programs, and known-customer relationships to produce one defensible "
                    "range with confidence, rationale, and 3–5 key drivers. The call is anchored by "
                    "deterministic guardrails — a hard cap per company, a range-width ratio (tight "
                    "range = higher confidence), a per-user ceiling sanity check, and known-customer "
                    "floor/ceiling enforcement when applicable.<br><br>"
                    "<strong>Deep Dive (sharpened)</strong> — when a Deep Dive has been run in Inspector, "
                    "the discovery holistic estimate is replaced by a full five-motion ACV calculation "
                    "(Customer Training, Partner Training, Employee Training, Certification, Events) "
                    "with per-product precision. GP5 — intelligence compounds."
                ),
            },
            {
                "heading": "The Deep Dives pill",
                "body": (
                    "The <strong>Deep Dives</strong> column shows N/M — how many of M discovered "
                    "products have been scored through a full Deep Dive. Full coverage renders "
                    "green, partial amber, none muted. This signals where the ACV Potential has "
                    "been hardened against evidence and where it's still the discovery-level estimate."
                ),
            },
            {
                "heading": "Confidence chips — what they mean",
                "body": (
                    "<strong>HIGH</strong> — tight range, strong signals, no guardrail trips.<br>"
                    "<strong>MEDIUM</strong> — confident magnitude, some uncertainty in motion mix.<br>"
                    "<strong>LOW</strong> — thin data, wide range, or a guardrail check failed. "
                    "Treat the low end as the conservative assumption.<br>"
                    "<strong>PARTNERSHIP</strong> — Content Development firms (GP Strategies class). "
                    "No direct ACV; Skillable's opportunity is labs embedded in the programs they "
                    "build for clients."
                ),
            },
            {
                "heading": "How the list refreshes",
                "body": (
                    "Refreshing this page recalculates display values from cached research data at "
                    "zero API cost. To regenerate the holistic ACV for a company after a prompt or "
                    "guardrail update, use the retrofit runner "
                    "(<code>scripts/retrofit_acv.py --mode holistic</code>) — one Claude call per "
                    "company, no re-research. Full Deep Dives are run from Inspector."
                ),
            },
        ],
    },
    "acv_estimation": {
        "eyebrow": "ACV POTENTIAL",
        "title": "How ACV is Estimated",
        "sections": [
            {
                "heading": "Two layers, same goal",
                "body": (
                    "Every ACV Potential number in the platform traces to one of two computations. "
                    "Both answer the same question — <em>how big is this if we win?</em> — but with "
                    "different evidence:<br><br>"
                    "<strong>Discovery-level (Option 2 Holistic)</strong> — a single Claude call "
                    "reasons across all discovered products + company-level training signals + "
                    "calibration anchors and returns one typed JSON object: "
                    "<code>{acv_low, acv_high, confidence, rationale, key_drivers, caveats}</code>. "
                    "Used for every company in Prospector that hasn't had a Deep Dive.<br><br>"
                    "<strong>Deep Dive five-motion</strong> — pure Python, zero Claude at ACV time. "
                    "Sums Customer Training + Partner Training + Employee Training + Certification + "
                    "Events using per-product audience × adoption × hours × rate. Replaces the "
                    "discovery estimate once a Deep Dive has run."
                ),
            },
            {
                "heading": "The five motions — Deep Dive level",
                "body": (
                    f"<strong>Customer Training</strong> — product users. Software/Enterprise: "
                    f"{int(CUSTOMER_TRAINING_ADOPTION_BY_TIER['high'] * 100)}% adoption for high-intensity categories "
                    f"(Cybersecurity, Cloud, Data Science), "
                    f"{int(CUSTOMER_TRAINING_ADOPTION_BY_TIER['moderate'] * 100)}% for moderate, "
                    f"{int(CUSTOMER_TRAINING_ADOPTION_BY_TIER['low'] * 100)}% for low. "
                    f"Wrapper orgs use their own adoption rates tied to delivery model.<br>"
                    f"<strong>Partner Training</strong> — channel partner SEs at 15% adoption, 5 hrs.<br>"
                    f"<strong>Employee Training</strong> — product-facing employees at 30% adoption, 8 hrs.<br>"
                    f"<strong>Certification (PBT)</strong> — annual exam sitters at 100% (lab IS the exam).<br>"
                    f"<strong>Events</strong> — flagship event attendees at 30% adoption, 1 hr."
                ),
            },
            {
                "heading": "Rate tiers — determined by workload complexity",
                "body": (
                    f"<table>"
                    f"<tr><th>Delivery path</th><th>Rate</th></tr>"
                    f"<tr><td>Cloud labs (Azure/AWS Cloud Slice, Sandbox API)</td><td>~${CLOUD_LABS_RATE:.0f}/hr</td></tr>"
                    f"<tr><td>Small VM / Container / Simulation</td><td>~${VM_LOW_RATE:.0f}/hr</td></tr>"
                    f"<tr><td>Typical VM (1–3 VMs)</td><td>~${VM_MID_RATE:.0f}/hr</td></tr>"
                    f"<tr><td>Large / Complex VM (multi-VM, complex topology)</td><td>~${VM_HIGH_RATE:.0f}/hr</td></tr>"
                    f"</table>"
                    f"Rate tier is driven by what the workload actually needs, not by the delivery label. "
                    f"A cybersecurity curriculum delivered via a SaaS portal still runs on VMs — it gets "
                    f"the VM rate, not the cloud rate."
                ),
            },
            {
                "heading": "Guardrails — the trust layer",
                "body": (
                    f"The holistic Claude call is anchored by deterministic Python rules that run before "
                    f"the output reaches the user:<br>"
                    f"<strong>Company hard cap</strong> — absolute ceiling per estimate. If exceeded, "
                    f"<code>acv_high</code> clamps and confidence drops to LOW.<br>"
                    f"<strong>Range-width ratio</strong> — if <code>acv_high / acv_low</code> is too wide "
                    f"at HIGH confidence, drops to MEDIUM. Too wide at MEDIUM drops to LOW. "
                    f"Wider range = less trust.<br>"
                    f"<strong>Per-user ceiling</strong> — if the midpoint implies a dollar-per-user value "
                    f"the platform has never seen, confidence drops to LOW.<br>"
                    f"<strong>Known-customer floor</strong> — when the target is a known Skillable "
                    f"customer, the low bound is the current ACV (cannot undersell an existing relationship). "
                    f"Floor informs the low, never collapses the range — the high preserves genuine upside."
                ),
            },
            {
                "heading": "Common pitfalls — built into the prompt",
                "body": (
                    "Five anti-patterns that used to shave estimates downward are now explicitly named "
                    "in the prompt:<br><br>"
                    "<strong>A — Fraction deflator.</strong> Adoption rates already encode realistic "
                    "consumption. Don't apply \"minority subset\" on top.<br>"
                    "<strong>B — Cumulative vs annual.</strong> Use annual enrollments where available; "
                    "if only cumulative, divide by 2–3 yr program life (4 yr academic).<br>"
                    "<strong>D — Floor-collapse (Python-enforced).</strong> Known-customer floor sets "
                    "the low bound only; high preserves width via Claude's original, stage ceiling, "
                    "or 2× floor.<br>"
                    "<strong>E — DIY as discount.</strong> An existing in-house lab platform is a "
                    "<em>positive</em> ICP signal (proven demand + budget), not a displacement discount.<br>"
                    "<strong>F — Rate tier by deployment label.</strong> Workload complexity drives "
                    "rate, not the delivery label (SaaS cybersecurity still needs VM rates)."
                ),
            },
        ],
    },
    "scoring_framework": {
        "eyebrow": "SCORING FRAMEWORK",
        "title": "How Companies Are Scored",
        "sections": [
            {
                "heading": "Three Pillars — the Fit Score",
                "body": (
                    f"The Fit Score (0–100) is a weighted composite of three Pillars:<br>"
                    f"<strong>Product Labability ({PILLARS[0].weight}%)</strong> — can Skillable run a "
                    f"hands-on lab on this product? Product-level.<br>"
                    f"<strong>Instructional Value ({PILLARS[1].weight}%)</strong> — does this product "
                    f"warrant hands-on training? Product-level.<br>"
                    f"<strong>Customer Fit ({PILLARS[2].weight}%)</strong> — is this organization a "
                    f"training buyer? Organization-level.<br><br>"
                    f"70% of the score is about the product (Labability + Instructional Value). 30% is "
                    f"about the organization. Product Labability carries the highest weight because if "
                    f"we can't lab the product, nothing else matters. A Technical Fit Multiplier applies "
                    f"asymmetric drag — weak Labability drags the organization-level contributions down; "
                    f"weak organization signals do not drag Labability down."
                ),
            },
            {
                "heading": "Discovery vs Deep Dive — two levels of signal",
                "body": (
                    "<strong>Discovery level</strong> — products are tiered into Promising / Potential / "
                    "Uncertain / Unlikely based on deployment model, API surface, category, and training "
                    "signals. A directional estimate, not a score. Company gets a holistic ACV Potential "
                    "from a single Claude call. This is the Prospector default view.<br><br>"
                    "<strong>Deep Dive</strong> — full three-Pillar scoring across 12 dimensions with "
                    "evidence-backed badges, strength-tiered rubric grading for Pillars 2 and 3, a precise "
                    "five-motion ACV, and a Seller Briefcase. Produces the definitive Fit Score and Verdict."
                ),
            },
            {
                "heading": "The Verdict Grid",
                "body": (
                    "The Verdict combines Fit Score and ACV tier into an action label — what to <em>do</em>, "
                    "not just what the numbers are:<br><br>"
                    "<table>"
                    "<tr><th>Score</th><th>High ACV</th><th>Medium ACV</th><th>Low ACV</th></tr>"
                    "<tr><td><strong>≥ 80</strong></td><td>Prime Target</td><td>Strong Prospect</td><td>Good Fit</td></tr>"
                    "<tr><td><strong>65–79</strong></td><td>High Potential</td><td>Worth Pursuing</td><td>Solid Prospect</td></tr>"
                    "<tr><td><strong>25–64</strong></td><td>Assess First</td><td>Keep Watch</td><td>Deprioritize</td></tr>"
                    "<tr><td><strong>&lt; 25</strong></td><td>Keep Watch</td><td>Poor Fit</td><td>Poor Fit</td></tr>"
                    "</table>"
                    "Score below 25 lands Poor Fit regardless of ACV — an unlabable product isn't a "
                    "Skillable opportunity even if the organization is huge."
                ),
            },
        ],
    },
}

# Threshold above which the Product Family picker activates on the Product
# Selection page. When a discovery returns this many or more non-TC products
# AND the website nav scrape produced multiple families, the page surfaces
# the family picker modal so the user can narrow the focus before selecting
# products for Deep Dive. Below this threshold, the picker is skipped — there
# isn't enough product volume to make narrowing worthwhile.
#
# Was 30 historically, dropped to 20 on 2026-04-06 per Frank's directive.
# Spec source: docs/archive/inspector.md "Product Family Selection" rule.
PRODUCT_FAMILY_PICKER_THRESHOLD = 20

# Minimum number of products required for a candidate family to appear
# as a pickable option in the Product Family picker.  Families with
# fewer than this many products are "noise" — they slipped into the
# scraped nav list (marketing buckets, one-off offerings, tagline
# links) or into the category-fallback grouping by accident.  Frank
# 2026-04-07: Workday shows 13 single-product families; the picker
# should surface only the meaningful ones.
# A family with 1 product is no choice at all — the user has to pick
# it and then sees a single product anyway.
PRODUCT_FAMILY_MIN_PRODUCTS = 2

# A family that claims more than this fraction of all discovered products
# is almost certainly a generic nav link ("All Products", "The Platform",
# "Product Tours") rather than a real product family. Frank 2026-04-08
# Trellix: the scraper pulled "Trellix Thrive", "Trellix Marketplace",
# "Trellix Partner Portal", and 4 more nav links that each token-matched
# 40/41 products on the vendor-name token. Even with the vendor-name
# strip in app.py, this ratio cap is the belt-and-braces guard.
PRODUCT_FAMILY_MAX_PRODUCT_RATIO = 0.80


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
#
# Automated checks that run on import.  Ensures the configuration is
# internally consistent — weights sum correctly, all badges have colors,
# no orphan references.  If validation fails, the system refuses to start.
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigValidationError(Exception):
    """Raised when the scoring configuration fails validation."""
    pass


def validate() -> list[str]:
    """Validate the scoring configuration for internal consistency.

    Returns a list of issues found.  An empty list means the config is valid.
    Raises ConfigValidationError if critical issues are found.

    Checks performed:
    1. Pillar weights sum to 100
    2. Dimension weights sum to 100 within each Pillar
    3. All badges have at least one color defined
    4. No duplicate badge names within a Pillar
    5. All pillars have exactly four dimensions
    6. Score thresholds are in descending order
    7. Verdict grid covers all score/ACV combinations
    8. Lab type menu has exactly 12 entries
    9. Category priors have valid demand levels
    10. Consumption motions have valid adoption ceilings
    11. Architecture invariant — Pillar 1 dims have NO rubric (canonical model);
        Pillar 2 + Pillar 3 dims DO have a rubric (rubric model)
    """
    issues: list[str] = []

    # 0. Exactly 3 pillars (HIGH-9 in code-review-2026-04-07.md)
    # Multiple files (models.FitScore, app.py templates, the 70/30 split logic)
    # assume exactly 3 pillars. If anyone adds a 4th, the assumption breaks
    # silently in subtle places. Assert explicitly so the failure mode is loud.
    if len(PILLARS) != 3:
        issues.append(
            f"Expected exactly 3 pillars, found {len(PILLARS)}. "
            f"Pillars: {[p.name for p in PILLARS]}. "
            f"Multiple files (models.FitScore, the 70/30 split, the dossier "
            f"templates) assume exactly 3 pillars — adding a 4th will break "
            f"them in subtle places. If this is intentional, audit every "
            f"caller of cfg.PILLARS first."
        )

    # 1. Pillar weights must sum to 100
    pillar_weight_sum = sum(p.weight for p in PILLARS)
    if pillar_weight_sum != 100:
        issues.append(
            f"Pillar weights sum to {pillar_weight_sum}, expected 100. "
            f"Pillars: {[(p.name, p.weight) for p in PILLARS]}"
        )

    # 2. Dimension weights must sum to 100 within each Pillar
    for pillar in PILLARS:
        dim_weight_sum = sum(d.weight for d in pillar.dimensions)
        if dim_weight_sum != 100:
            issues.append(
                f"Dimension weights in '{pillar.name}' sum to {dim_weight_sum}, expected 100. "
                f"Dimensions: {[(d.name, d.weight) for d in pillar.dimensions]}"
            )

    # 3. All badges must have at least one color defined
    for pillar in PILLARS:
        for dim in pillar.dimensions:
            for badge in dim.badges:
                if not badge.colors:
                    issues.append(
                        f"Badge '{badge.name}' in {pillar.name} > {dim.name} has no colors defined"
                    )

    # 4. No duplicate badge names within a Pillar
    for pillar in PILLARS:
        seen_names: set[str] = set()
        for dim in pillar.dimensions:
            for badge in dim.badges:
                if badge.name in seen_names:
                    issues.append(
                        f"Duplicate badge name '{badge.name}' in Pillar '{pillar.name}'"
                    )
                seen_names.add(badge.name)

    # 5. All pillars should have exactly four dimensions
    for pillar in PILLARS:
        if len(pillar.dimensions) != 4:
            issues.append(
                f"Pillar '{pillar.name}' has {len(pillar.dimensions)} dimensions, expected 4"
            )

    # 6. Score thresholds in descending order
    threshold_values = sorted(SCORE_THRESHOLDS.values(), reverse=True)
    actual_values = list(SCORE_THRESHOLDS.values())
    if actual_values != threshold_values:
        issues.append(
            f"Score thresholds are not in descending order: {SCORE_THRESHOLDS}"
        )

    # 7. Verdict grid completeness
    expected_acv_tiers = set(ACV_TIERS)
    expected_score_ranges = {0, 25, 45, 65, 80}
    grid_score_ranges = set()
    grid_acv_tiers = set()
    for (score, acv) in VERDICT_GRID:
        grid_score_ranges.add(score)
        grid_acv_tiers.add(acv)
    missing_scores = expected_score_ranges - grid_score_ranges
    missing_acvs = expected_acv_tiers - grid_acv_tiers
    if missing_scores:
        issues.append(f"Verdict grid missing score ranges: {missing_scores}")
    if missing_acvs:
        issues.append(f"Verdict grid missing ACV tiers: {missing_acvs}")

    # 8. Lab type menu count
    if len(LAB_TYPE_MENU) != 12:
        issues.append(
            f"Lab type menu has {len(LAB_TYPE_MENU)} entries, expected 12"
        )

    # 9. Category priors have valid demand levels
    valid_demand_levels = {"high", "moderate", "low"}
    for cp in CATEGORY_PRIORS:
        if cp.demand_level not in valid_demand_levels:
            issues.append(
                f"Category prior '{cp.category}' has invalid demand level: {cp.demand_level}"
            )

    # 10. Consumption motion adoption + hours + population source shape
    _valid_pop_sources = {
        "product:install_base",
        "product:employee_subset_size",
        "product:cert_annual_sit_rate",
        "company:channel_partner_se_population",
        "company:events_attendance_sum",
    }
    for motion in CONSUMPTION_MOTIONS:
        if motion.hours_low > motion.hours_high:
            issues.append(
                f"Motion '{motion.label}' has hours_low > hours_high: "
                f"{motion.hours_low} > {motion.hours_high}"
            )
        if motion.adoption_pct < 0 or motion.adoption_pct > 1.0:
            issues.append(
                f"Motion '{motion.label}' adoption_pct {motion.adoption_pct} "
                f"out of range [0, 1.0]"
            )
        # Certification is exempt from the non-events ceiling — its 1.0
        # is exact by definition. Events has its own higher ceiling.
        if motion.label == "Events & Conferences":
            if motion.adoption_pct > ADOPTION_CEILING_EVENTS:
                issues.append(
                    f"Events motion adoption {motion.adoption_pct} "
                    f"exceeds events hard cap {ADOPTION_CEILING_EVENTS}"
                )
        elif motion.label != "Certification (PBT)":
            if motion.adoption_pct > ADOPTION_CEILING_NON_EVENTS:
                issues.append(
                    f"Motion '{motion.label}' adoption {motion.adoption_pct} "
                    f"exceeds non-events cap {ADOPTION_CEILING_NON_EVENTS}"
                )
        if motion.population_source not in _valid_pop_sources:
            issues.append(
                f"Motion '{motion.label}' population_source "
                f"'{motion.population_source}' is not a recognized source; "
                f"valid: {sorted(_valid_pop_sources)}"
            )

    # 11. Technical Fit Multiplier ranges don't have gaps
    multiplier_ranges = sorted(TECHNICAL_FIT_MULTIPLIERS, key=lambda m: m.score_min)
    if multiplier_ranges[0].score_min != 0:
        issues.append("Technical Fit Multiplier does not start at score 0")

    # 12. Architecture invariant — two scoring architectures across pillars
    # Pillar 1 (Product Labability) uses the canonical model: name-matched
    # signal/penalty lookup, NO rubric.
    # Pillar 2 (Instructional Value) and Pillar 3 (Customer Fit) use the
    # rubric model: variable badge names, strength grading, signal_category
    # tags, AND a rubric defined per dimension.
    # This invariant catches a future maintainer accidentally adding a rubric
    # to Pillar 1 or removing one from Pillar 2/3 — would silently change
    # how badges score and break the cross-architecture contract.
    if PILLAR_PRODUCT_LABABILITY.dimensions:
        for dim in PILLAR_PRODUCT_LABABILITY.dimensions:
            if dim.rubric is not None:
                issues.append(
                    f"Architecture invariant violated: Pillar 1 dimension "
                    f"'{dim.name}' has a rubric defined. Pillar 1 uses the "
                    f"canonical model (name-matched signal lookup), not the "
                    f"rubric model. Remove the rubric or move the dimension."
                )
    for pillar in (PILLAR_INSTRUCTIONAL_VALUE, PILLAR_CUSTOMER_FIT):
        for dim in pillar.dimensions:
            if dim.rubric is None:
                issues.append(
                    f"Architecture invariant violated: {pillar.name} dimension "
                    f"'{dim.name}' is missing a rubric. Pillar 2 and Pillar 3 "
                    f"dimensions use the rubric model — every dimension must "
                    f"define a Rubric with strength tiers, IS/IS NOT boundaries, "
                    f"and signal_categories."
                )
            else:
                # Validate rubric structure
                if not dim.rubric.tiers:
                    issues.append(
                        f"Rubric for {pillar.name} > {dim.name} has no tiers"
                    )
                if not dim.rubric.signal_categories:
                    issues.append(
                        f"Rubric for {pillar.name} > {dim.name} has no "
                        f"signal_categories — empty signal_category list "
                        f"defeats the analytics hedge"
                    )
                # Each rubric MUST include strong / moderate / weak. Optional
                # informational tier (zero points, context-only) is allowed
                # but not required. Per Frank 2026-04-07: every badge is one
                # of four answers — good (strong), pause (moderate), context
                # (informational), or nothing to say (weak don't emit).
                strength_names = {t.strength for t in dim.rubric.tiers}
                required_strengths = {"strong", "moderate", "weak"}
                allowed_strengths = required_strengths | {"informational"}
                missing = required_strengths - strength_names
                extra = strength_names - allowed_strengths
                if missing or extra:
                    msg = f"Rubric for {pillar.name} > {dim.name} has unexpected strength tiers"
                    if missing:
                        msg += f" (missing: {missing})"
                    if extra:
                        msg += f" (extra: {extra})"
                    issues.append(msg)

    if issues:
        raise ConfigValidationError(
            f"Scoring configuration validation failed with {len(issues)} issue(s):\n"
            + "\n".join(f"  - {i}" for i in issues)
        )

    return issues


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE ACCESSORS
#
# Helper functions for common lookups used by the prompt generator,
# scorer, and UX templates.
# ═══════════════════════════════════════════════════════════════════════════════

def get_pillar(name: str) -> Pillar:
    """Look up a Pillar by name. Raises KeyError if not found."""
    for p in PILLARS:
        if p.name == name:
            return p
    raise KeyError(f"No pillar named '{name}'")


def get_dimension(pillar_name: str, dimension_name: str) -> Dimension:
    """Look up a Dimension by Pillar and Dimension name. Raises KeyError if not found."""
    pillar = get_pillar(pillar_name)
    for d in pillar.dimensions:
        if d.name == dimension_name:
            return d
    raise KeyError(f"No dimension '{dimension_name}' in pillar '{pillar_name}'")


def get_all_badges() -> list[Badge]:
    """Return a flat list of all badges across all pillars and dimensions."""
    badges = []
    for pillar in PILLARS:
        for dim in pillar.dimensions:
            badges.extend(dim.badges)
    return badges


def get_all_badge_names() -> list[str]:
    """Return a flat list of all badge names for prompt injection."""
    return [b.name for b in get_all_badges()]


def get_verdict(score: int, acv_tier: str) -> VerdictDefinition:
    """Look up the verdict for a given score and ACV tier.

    Args:
        score: The Fit Score (0-100)
        acv_tier: One of 'high', 'medium', 'low'

    Returns:
        The VerdictDefinition for this score/tier combination.
    """
    if acv_tier not in ACV_TIERS:
        raise ValueError(f"Invalid ACV tier '{acv_tier}'. Must be one of {ACV_TIERS}")

    # Find the matching score range
    for threshold in sorted(SCORE_THRESHOLDS.values(), reverse=True):
        if score >= threshold:
            return VERDICT_GRID[(threshold, acv_tier)]

    # Score < 0 — should never happen but handle gracefully
    return VERDICT_GRID[(0, acv_tier)]


def get_locked_term(term: str) -> Optional[LockedTerm]:
    """Look up a locked term. Returns None if not found."""
    for lt in LOCKED_VOCABULARY:
        if lt.use_this == term:
            return lt
    return None


def is_skillable_partner_lms(lms_name: str) -> bool:
    """Check whether an LMS platform is a Skillable partner."""
    for lms in CANONICAL_LMS_PARTNERS:
        if lms.name.lower() == lms_name.lower():
            return lms.is_skillable_partner
    return False


def is_confirmed_edp(edp_name: str) -> bool:
    """Check whether an exam delivery provider has a confirmed Skillable integration."""
    for edp in EXAM_DELIVERY_PROVIDERS:
        if edp.name.lower() == edp_name.lower():
            return edp.is_confirmed
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# REASONING SEQUENCE
#
# The step-by-step order the AI follows when scoring a product.  Each step
# builds on the previous one.  Steps can be added, reordered, or removed
# as the platform evolves.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ReasoningStep:
    """A single step in the AI's scoring reasoning sequence."""
    number: int
    name: str
    instruction: str
    skip_condition: str = ""  # When to skip this step (empty = never skip)

REASONING_SEQUENCE: tuple[ReasoningStep, ...] = (
    ReasoningStep(0, "Bare Metal Hard Stop",
        "Does this product require orchestrating physical bare metal hardware — actual physical "
        "servers, network gear, HSMs, or hardware with no virtualization layer? If YES: Score "
        "Product Labability 0-5, total score 5-15, add bare_metal_required. Set recommendation "
        "to Do Not Pursue. Important: hardware-locked licensing (BIOS GUID-based activation) is "
        "NOT a blocker — Skillable can pin BIOS GUIDs in VM profiles."),
    ReasoningStep(1, "API Automation Gate",
        "Can provisioning, user account creation, license application, and environment configuration "
        "be done programmatically without learner action? If NONE feasible: Score Product Labability "
        "0-5, add no_api_automation. SaaS Isolation Pre-Screen: if pure SaaS with no per-learner "
        "sandbox API and no self-hosted option, flag saas_only. If shared demo tenant only, additionally "
        "flag multi_tenant_only. Critical: Entra ID SSO does NOT equal per-learner isolation."),
    ReasoningStep(2, "User Persona Filter",
        "List 2-4 personas from: Architect, Administrator, Security Engineer/Analyst, Infrastructure "
        "Engineer, Networking Engineer, Data Scientist, Data Engineer, Data Analyst, Business Analyst, "
        "Business User, Developer, Software Engineer, Consumer. All except Consumer are highly labable. "
        "Consumer: Score 0-3, add consumer_product."),
    ReasoningStep(3, "Determine Orchestration Method",
        "Check Hyper-V/ESX/Container FIRST — does it run in VMs or containers? The VM or container "
        "image IS the lab. Hyper-V is the default — prefer over ESX due to Broadcom pricing. ESX only "
        "when nested virtualization or socket licensing requires it. Container only when ALL FOUR "
        "conditions hold. Then check Cloud Slice (Azure/AWS). Then Custom API. Simulation is the "
        "correct method when real provisioning is cost-prohibitive, time-impractical, or all paths blocked."),
    ReasoningStep(4, "Score All Dimensions",
        "Score each dimension within each pillar using the signals, badges, and penalties defined "
        "in the configuration. Each pillar scores out of 100 internally."),
    ReasoningStep(5, "Technical Fit Multiplier",
        "Applied automatically after Product Labability scoring. Adjusts how much weight downstream "
        "pillars carry based on the strength of the technical foundation."),
    ReasoningStep(6, "Intelligence Signals",
        "Flag special signals found in research: M365 tenant provisioning, Entra ID SSO, marketplace "
        "listings, IaC templates, NFR licenses, existing competitor labs, existing Skillable labs, "
        "deployment guides, xAPI requirements, exam delivery provider integrations, flagship events."),
    ReasoningStep(7, "Generate Recommendations",
        "3-5 bullets. Lead with WHY, not HOW. Required: Delivery Path, Scoring Approach, Help your "
        "champion find. Optional: Program Fit, Similar Products, Blockers. Every bullet must state WHY."),
    ReasoningStep(8, "Consumption Potential",
        "Estimate annual lab consumption across six motions. CONSERVATIVE BY DEFAULT — an estimate that "
        "proves accurate builds trust; an estimate that proves inflated destroys it."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# EVIDENCE STANDARDS
#
# Writing rules for how the AI produces evidence bullets.  Configurable as
# writing quality expectations evolve.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EvidenceStandard:
    """A single evidence writing rule."""
    rule: str
    description: str

EVIDENCE_STANDARDS: tuple[EvidenceStandard, ...] = (
    EvidenceStandard("Bold label required",
        "Every evidence claim bullet MUST start with a 2-3 word bold label followed by a colon."),
    EvidenceStandard("Label clarity",
        "Labels must make sense to someone who has never read the product docs. No vendor-specific "
        "acronyms, internal terms, or jargon."),
    EvidenceStandard("Directional qualifier",
        "Every bullet must convey whether the signal is positive or negative: Strength (green), "
        "Opportunity (green), Context (gray), Risk (amber), Blocker (red)."),
    EvidenceStandard("URL placement",
        "Never embed URLs in claim text. Source citations belong in structured source_url and "
        "source_title fields."),
    EvidenceStandard("Maximum per dimension",
        "MAXIMUM 5 evidence items per dimension. Fewer is better — 2-3 sharp items is the norm."),
    EvidenceStandard("Uniqueness",
        "Evidence MUST be unique across all dimensions — do not reword or repeat the same fact."),
    EvidenceStandard("Lab concepts limit",
        "Lab concepts: 2-6 items max, covering the range of learning phases and personas."),
    EvidenceStandard("Clear, concise, complete",
        "Every bullet must be all three. No filler. No vague language. Specific details, specific "
        "sources, specific reasoning."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# DELIVERY PATTERN SIGNALS
#
# Specific technology patterns and their guidance for the AI.  New patterns
# added as Skillable supports new delivery methods.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DeliveryPattern:
    """A specific delivery pattern the AI should recognize and apply."""
    name: str
    guidance: str

DELIVERY_PATTERNS: tuple[DeliveryPattern, ...] = (
    DeliveryPattern("Azure DevOps (ADO)",
        "Cloud Slice provisioning available. ~85% launches <2 min, 15% take 5-15 min due to "
        "Microsoft provisioning queue. Pre-Instancing mitigates. Self-paced only."),
    DeliveryPattern("GitHub",
        "Cloud Slice provisioning available. Inverse of ADO — ~85% slow (5-15+ min), 15% instant. "
        "Pre-Instancing required. Self-paced only."),
    DeliveryPattern("VMware vSphere / ESXi management",
        "Shared licensed ESX server with application-layer isolation. Risks: Broadcom licensing "
        "compliance (~$5K/server); collaborative-only delivery."),
    DeliveryPattern("Identity lifecycle management",
        "Products like Quest Active Roles, One Identity. Pre-provisioned credential pool of real "
        "Entra tenants. Risks: recycling completeness; per-tenant license cost."),
    DeliveryPattern("Virtual appliance / OVA format",
        "OVA Import to ESX fabric. Constraints: hardware version <=19, single VM only, ESX format required."),
    DeliveryPattern("Hardware-fingerprinted licensing",
        "Skillable can pin Custom UUID. If product ALSO requires Public IP, only one concurrent "
        "launch is viable."),
    DeliveryPattern("Conditional Access / Zero Trust MFA",
        "Requires Hyper-V VM + Entra P1 license, not Cloud Slice."),
    DeliveryPattern("Complex pre-sales evaluation",
        "Pre-sales POC motion is likely highest-priority use case. 7x higher expansion revenue "
        "from hands-on POC (Tanium data)."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# SKILLABLE CAPABILITIES (re-exported from Layer 2)
#
# 2026-04-17 — the `SkillableCapability` dataclass and the `SKILLABLE_CAPABILITIES`
# tuple moved out of this file and into `backend/skillable_knowledge.py`
# (Layer 2 self-knowledge, distinct from Layer 3 scoring rules).  Re-exported
# here so existing `scoring_config.SKILLABLE_CAPABILITIES` and
# `scoring_config.SkillableCapability` lookups continue to resolve.  New code
# should import from `backend.skillable_knowledge` directly.
# ═══════════════════════════════════════════════════════════════════════════════

from skillable_knowledge import (  # noqa: E402 — intentional re-export at end of file
    SkillableCapability,
    SKILLABLE_CAPABILITIES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTACT GUIDANCE
#
# Rules for identifying decision makers and influencers.  Sharpened over
# time as we learn what works.
# ═══════════════════════════════════════════════════════════════════════════════

CONTACT_GUIDANCE = {
    "decision_maker_titles": (
        "CLO", "Chief Education Officer", "Chief Enablement Officer",
        "EVP of Training", "SVP of Training", "VP of Training",
        "VP of Partner Enablement", "VP of Technical Enablement",
        "VP of Customer Education", "Head of Customer Education",
        "Head of Global Enablement", "Head of Certification",
        "GM of Academy", "GM of University",
        "Senior Director of Training (only if they run the function end-to-end)",
    ),
    "decision_maker_test": "Does this person OWN the function and have authority to sign a vendor agreement?",
    "not_decision_makers": (
        "Directors and Managers of Training (unless running whole function)",
        "Instructors", "Trainers", "Specialists", "Individual contributors", "SEs",
    ),
    "influencer_titles": (
        "Director of Training", "Director of Partner Enablement",
        "Director of Customer Education", "Director of Certification",
        "Senior Director (when VP exists above)", "Solutions Engineering Director",
    ),
    "influencer_minimum_level": "Director",
    "not_influencers": "Managers, Specialists, Coordinators, IDs, anyone below Director level",
    "exclude_entirely": "L&D roles — Learning & Development owns internal employee training, not external technical lab content",
    "alumni_signal": "If contact previously worked at a known Skillable customer in training/education/enablement, flag as highest-priority warm outreach",
    "unknown_fallback": "If no qualifying person found, use 'Unknown - search for [title]' — do NOT name a lower-level person to fill the slot",
}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPETITOR PROFILES
#
# How Skillable positions against competitors when detected in research.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CompetitorProfile:
    """Competitive positioning against a specific lab platform."""
    name: str
    skillable_advantage: str

COMPETITOR_PROFILES: tuple[CompetitorProfile, ...] = (
    CompetitorProfile("CloudShare",
        "Cannot support complex multi-VM environments connected by private networks. "
        "Thin enterprise software depth. Skillable offers real multi-VM networking with "
        "private VLANs, isolated network segments, custom IP, NAT, VPNs, and traffic monitoring."),
    CompetitorProfile("Instruqt",
        "Cannot go deep into Windows Server, legacy enterprise, or multi-component stacks. "
        "Skillable runs any Windows or Linux software in datacenter VMs with full network control."),
    CompetitorProfile("General",
        "When to surface competitive context: if a product requires PBT/certification exams, "
        "multi-VM private networking, or if research shows existing competitor labs — flag "
        "Skillable advantages in evidence."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# SELLER BRIEFCASE
#
# Below each Pillar in the dossier, a briefcase section provides 2-3 sharp,
# actionable bullets that arm the seller for conversations.  This is
# conversational competence (GP2) delivered in practical form.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class BriefcaseSection:
    """A seller briefcase section tied to a Pillar."""
    pillar_name: str
    section_title: str
    description: str
    instructions: str

SELLER_BRIEFCASE: tuple[BriefcaseSection, ...] = (
    BriefcaseSection(
        pillar_name="Product Labability",
        section_title="Key Technical Questions",
        description="The 2-3 questions that unblock the lab build — who to ask, "
                    "what to ask, what department.",
        instructions="Identify the specific technical blocker for this product's lab build. "
                     "Name the department or role at the customer most likely to have the answer. "
                     "Write a verbatim question the champion can send in Slack or email. "
                     "Explain why this question matters — what it unblocks if answered. "
                     "FORMAT: Each bullet starts with a **Bold Label:** (colon, not em dash) "
                     "followed by the content. Example: **Confirm NFR Path:** Solution Architect...",
    ),
    BriefcaseSection(
        pillar_name="Instructional Value",
        section_title="Conversation Starters",
        description="Product-specific talking points about why hands-on training matters "
                    "for this product. Makes the seller credible without being technical.",
        instructions="Generate 2-3 talking points that a non-technical seller can use in a "
                     "meeting. Each should reference a specific aspect of this product — "
                     "its complexity, the stakes of getting it wrong, or the types of labs "
                     "that would be valuable. Frame each as why hands-on matters for THIS "
                     "product, not generically. Market Demand evidence (Stack Overflow activity, "
                     "install base size, cert ecosystem) belongs here as proof the training "
                     "market exists — this is NOT a Key Technical Question. "
                     "FORMAT: Each bullet starts with a **Bold Label:** (colon, not em dash) "
                     "followed by the content.",
    ),
    BriefcaseSection(
        pillar_name="Customer Fit",
        section_title="Account Intelligence",
        description="COMPANY-LEVEL organizational signals — same regardless of which product "
                    "is selected. Training leadership, org complexity, LMS, competitive context, news.",
        instructions="Surface the most important COMPANY-LEVEL context a seller should "
                     "know before a meeting. This section is about the ORGANIZATION, not "
                     "the product. Do NOT reference product-specific labability or product-specific "
                     "capabilities. Include: key contacts and their relevance, leadership changes, "
                     "funding rounds, new partnerships, organizational dynamics (mergers, growth, "
                     "restructuring), training infrastructure signals (LMS platform, lab platform, "
                     "competitor presence), events, and news. This section must make sense "
                     "regardless of which product the seller is viewing. "
                     "FORMAT: Each bullet starts with a **Bold Label:** (colon, not em dash) "
                     "followed by the content.",
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-VALIDATE ON IMPORT
#
# The configuration validates itself when the module loads.  If any check
# fails, the system refuses to start with a clear error message.
# This ensures no broken configuration ever reaches the AI.
# ═══════════════════════════════════════════════════════════════════════════════

validate()
