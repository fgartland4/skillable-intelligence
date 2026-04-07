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
class Dimension:
    """A scored area within a Pillar.

    Each Pillar has four Dimensions.  Dimensions are weighted within their
    Pillar (weights sum to 100 within each Pillar) and contain badges,
    scoring signals, and penalties.
    """
    name: str
    weight: int
    question: str
    badges: tuple[Badge, ...] = ()
    scoring_signals: tuple[ScoringSignal, ...] = ()
    penalties: tuple[Penalty, ...] = ()
    cap: Optional[int] = None
    floor: Optional[int] = None
    notes: str = ""


@dataclass(frozen=True)
class Pillar:
    """A top-level scoring component.

    Three Pillars compose the Fit Score.  Each scores out of 100 internally,
    then gets weighted.  A score of 85/100 on a 40% Pillar contributes
    85 x 0.40 = 34 points to the Fit Score.
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

    Each motion represents a distinct way labs reach learners.  Population,
    adoption rate, hours, and rate combine to estimate annual revenue.
    """
    label: str
    adoption_ceiling_low: float
    adoption_ceiling_high: float
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
# PILLAR 1 — PRODUCT LABABILITY (40%)
#
# The gatekeeper.  If this fails, nothing else matters.  Measures whether
# Skillable can deliver a complete lab lifecycle for this product.  70% of
# the Fit Score is about the product — and this Pillar is the foundation.
# ═══════════════════════════════════════════════════════════════════════════════

_provisioning_badges = (
    Badge("Runs in Hyper-V", (
        BadgeColor("green", "Clean VM install confirmed"),
        BadgeColor("amber", "Installs with complexity"),
    )),
    Badge("Runs in Azure", (
        BadgeColor("green", "Azure-native service — viable for Azure Cloud Slice fabric"),
        BadgeColor("amber", "Azure path with friction"),
    ), notes="Means the product IS an Azure service viable for Cloud Slice fabric — NOT 'can be hosted on an Azure VM.' For installable products that happen to run on Azure VMs, use Runs in Hyper-V."),
    Badge("Runs in AWS", (
        BadgeColor("green", "AWS-native service — viable for AWS Cloud Slice fabric"),
        BadgeColor("amber", "AWS path with friction"),
    ), notes="Means the product IS an AWS service viable for Cloud Slice fabric — NOT 'can be hosted on an AWS VM.'"),
    Badge("Requires GCP", (
        BadgeColor("amber", "No native Skillable GCP path"),
    )),
    Badge("Runs in Container", (
        BadgeColor("green", "Container-native confirmed, no disqualifiers"),
        BadgeColor("amber", "Image exists but disqualifiers apply or research uncertain"),
    ), notes="Singular. Defaults to green when container-native confirmed. Don't emit if definitively not container-viable. Scores ~equivalent to Hyper-V Standard."),
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
    Badge("Pre-Instancing", (
        BadgeColor("green", "Slow first-launch or cluster init mitigated by Skillable Pre-Instancing — Skillable feature opportunity"),
    ), notes="Green opportunity badge when product has long initial provisioning time. Frames the slowness as a Skillable feature win (Pre-Instancing pre-builds warm instances), not friction."),
    Badge("Multi-VM Lab", (
        BadgeColor("green", "Multiple VMs working together — Skillable strength (competitors struggle here)"),
    ), notes="Skillable competitive advantage. Typical for cybersecurity (attacker + target + SIEM), data engineering pipelines, enterprise stacks. Drives ACV rate tier upward. Mutually exclusive with Large Lab."),
    Badge("Complex Topology", (
        BadgeColor("green", "Real network complexity — routers, switches, firewalls, segmentation, routing protocols"),
    ), notes="Skillable strength. Applies to networking vendors (Cisco, Juniper, Palo Alto, F5) AND cybersecurity products with real network-layer complexity. Can pair with Multi-VM Lab or Large Lab."),
    Badge("Large Lab", (
        BadgeColor("green", "Single environment with big footprint — RAM, CPU, GPU, datasets — Skillable strength"),
    ), notes="Skillable strength for products that need big single-machine resources (data science, AI/ML, GPU-heavy workloads). Mutually exclusive with Multi-VM Lab — pick whichever better describes the primary nature of the scale."),
    Badge("GPU Required", (
        BadgeColor("amber", "Product requires GPU — forces cloud VM with GPU instance, slower launch and higher cost"),
    ), notes="Genuine friction. Standard Hyper-V doesn't have GPU; routes to Azure/AWS with GPU instance via Compute Gallery. Was a hidden penalty; promoted to a visible badge so SEs see the warning."),
    Badge("Bare Metal Required", (
        BadgeColor("red", "Physical hardware required — no virtualization path"),
    )),
    Badge("No Deployment Method", (
        BadgeColor("red", "Cannot be provisioned or simulated in any software environment"),
    ), notes="Ultimate dead-end blocker. Only fires when no real provisioning path AND Simulation is also blocked. Diligent-style products where Simulation is viable do NOT get this badge — they get Sandbox API red + Simulation gray."),
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
    ScoringSignal("Runs in Hyper-V", 30, "Clean Hyper-V install — full base credit"),
    ScoringSignal("Runs in Azure", 30, "Azure-native service via Cloud Slice fabric"),
    ScoringSignal("Runs in AWS", 30, "AWS-native service via Cloud Slice fabric"),
    ScoringSignal("Runs in Container", 30, "Container-native confirmed — equivalent to Hyper-V Standard"),
    ScoringSignal("ESX Required", 26, "ESX path — 4 points below Hyper-V due to operational cost (Broadcom licensing)"),
    ScoringSignal("Sandbox API", 22, "Vendor provisioning API (BYOC) — viable per-learner provisioning, scored below native fabrics"),
    ScoringSignal("Simulation", 12, "Simulation as the chosen path — base credit when real provisioning is impractical"),
    # Strength badges (do not score in Provisioning directly — they drive
    # the ACV rate tier upward and add seller-relevant context)
    ScoringSignal("Multi-VM Lab", 0, "Skillable competitive strength — drives ACV rate tier"),
    ScoringSignal("Complex Topology", 0, "Skillable competitive strength — drives ACV rate tier"),
    ScoringSignal("Large Lab", 0, "Skillable competitive strength — drives ACV rate tier"),
    ScoringSignal("Pre-Instancing", 0, "Skillable feature opportunity — mitigates slow init"),
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
    Penalty("MFA Required", -10, "mfa_required",
            "Blocks automated task scoring; falls back to MCQ/AI Vision only"),
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
)

_scoring_signals = (
    ScoringSignal("Scoring API", 14, "Vendor REST API for state validation — green tier"),
    ScoringSignal("Script Scoring", 12, "Strong script-based validation"),
    ScoringSignal("AI Vision", 11, "AI Vision is the right tool for this GUI-heavy product — green tier (peer to API/Script, not a fallback)"),
    ScoringSignal("Simulation Scorable", 8, "Simulation scoring via guided interaction"),
    ScoringSignal("MCQ Scoring", 4, "Knowledge-check questions only — the genuine fallback"),
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
        BadgeColor("green", "Skillable hosts the environment (Hyper-V, ESX, Container, OR Simulation) — teardown is automatic via snapshot revert or platform cleanup"),
    ), notes="Renamed from 'Automatic (VM/Container)'. Cleaner name. Fires green for ANY Skillable-hosted path including Simulation (Frank: simulation runs in our infra, teardown is automatic there too)."),
    Badge("Teardown API", (
        BadgeColor("green", "Vendor API covers environment cleanup and deprovisioning"),
        BadgeColor("amber", "Some teardown API coverage but gaps remain"),
    ), notes="CONSOLIDATED. Replaces 'Teardown APIs (full)' + 'Teardown APIs (partial)' — one canonical, two color states. Per the meta-principle (one badge, color carries the nuance)."),
    Badge("Manual Teardown", (
        BadgeColor("red", "No teardown mechanism — manual cleanup required between learners"),
    ), notes="NEW red blocker badge. Replaces the hidden 'No Teardown API' penalty so SEs see the warning. When this fires, the seller knows teardown is going to be a real build task."),
    Badge("Orphan Risk", (
        BadgeColor("amber", "Incomplete teardown may leave orphaned resources or accounts even when API exists"),
    ), notes="Frank: keep this. Even Azure has services with orphan risk. Distinct from Manual Teardown — Orphan Risk fires alongside Teardown API amber when there's coverage but with gaps."),
)

_teardown_signals = (
    ScoringSignal("Datacenter", 25, "Skillable-hosted environment teardown — automatic via snapshot revert or platform cleanup"),
    ScoringSignal("Teardown API", 22, "Vendor API covers cleanup — green tier"),
)

_teardown_penalties = (
    Penalty("Manual Teardown", -10, "manual_teardown",
            "No programmatic teardown — manual cleanup required between learners"),
    Penalty("Orphan Risk", -5, "orphan_risk",
            "Incomplete teardown may leave orphaned resources, accounts, or data"),
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
    weight=40,
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
# PILLAR 2 — INSTRUCTIONAL VALUE (30%)
#
# The commercial case.  Measures whether this product genuinely warrants
# hands-on lab experiences.  Combined with Product Labability, these two
# product-level pillars represent 70% of the Fit Score.
# ═══════════════════════════════════════════════════════════════════════════════

_product_complexity_badges = (
    Badge("Deep Configuration", (
        BadgeColor("green", "Many options, real consequences"),
        BadgeColor("amber", "Some configuration, limited scope"),
    )),
    Badge("Multi-Phase Workflow", (
        BadgeColor("green", "Multiple distinct phases"),
        BadgeColor("amber", "Some depth, similar phases"),
    )),
    Badge("Role Diversity", (
        BadgeColor("green", "Many personas need separate programs"),
        BadgeColor("amber", "Few roles, not distinct enough for separate tracks"),
    )),
    Badge("Troubleshooting", (
        BadgeColor("green", "Rich fault scenarios confirmed"),
        BadgeColor("amber", "Some troubleshooting, limited scope"),
    )),
    Badge("Complex Networking", (
        BadgeColor("green", "VLANs, routing, multi-network topologies"),
        BadgeColor("amber", "Some networking, straightforward"),
    )),
    Badge("Integration Complexity", (
        BadgeColor("green", "External systems are primary workflow"),
        BadgeColor("amber", "Some integrations, not primary"),
    )),
    Badge("AI Practice Required", (
        BadgeColor("green", "AI features need iterative hands-on practice"),
        BadgeColor("amber", "AI present but shallow"),
    )),
    Badge("Consumer Grade", (
        BadgeColor("amber", "Might be consumer-oriented (inferred)"),
        BadgeColor("red", "Consumer app confirmed — not lab appropriate"),
    )),
    Badge("Simple UX", (
        BadgeColor("amber", "Might be too simple (inferred)"),
        BadgeColor("red", "Straightforward interface confirmed — minimal lab value"),
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

_product_complexity_dimension = Dimension(
    name="Product Complexity",
    weight=40,
    question="Is this product hard enough to require hands-on practice?",
    badges=_product_complexity_badges,
    scoring_signals=_product_complexity_signals,
    cap=40,
    notes="Documentation breadth is the primary signal — count modules, features per module, "
          "options per feature, interoperability.",
)


_mastery_stakes_badges = (
    Badge("High-Stakes Skills", (
        BadgeColor("green", "Misconfiguration causes real harm — breach, data loss, compliance failure, downtime"),
        BadgeColor("amber", "Stakes exist but moderate"),
    )),
    Badge("Steep Learning Curve", (
        BadgeColor("green", "Long path to competence, multiple stages"),
        BadgeColor("amber", "Some learning curve but manageable"),
    )),
    Badge("Adoption Risk", (
        BadgeColor("green", "Poor adoption is a documented concern — labs directly address this"),
        BadgeColor("amber", "Some adoption challenges"),
    )),
)

_mastery_stakes_signals = (
    ScoringSignal("High-stakes skills", 10, "Misconfiguration causes breach, data loss, compliance failure, downtime"),
    ScoringSignal("Steep learning curve", 8, "Long path from beginner to competent, multiple stages"),
    ScoringSignal("Adoption risk", 7, "Poor adoption or slow TTV is documented"),
)

_mastery_stakes_dimension = Dimension(
    name="Mastery Stakes",
    weight=25,
    question="How much does competence matter?",
    badges=_mastery_stakes_badges,
    scoring_signals=_mastery_stakes_signals,
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

_lab_versatility_dimension = Dimension(
    name="Lab Versatility",
    weight=15,
    question="What kinds of hands-on experiences can we build?",
    badges=_lab_versatility_badges,
    scoring_signals=(
        ScoringSignal("Lab type badge found", 5, "+5 per badge found; AI picks 1-2 per product"),
    ),
    cap=15,
    notes="These are special, high-value lab types — not standard step-by-step labs. "
          "AI picks 1-2 per product. Most simple products get none. All badges are green (opportunities). "
          "Dual purpose: conversational competence in Inspector, program recommendations in Designer.",
)


_market_demand_badges = (
    Badge("Rapid Growth", (
        BadgeColor("green", "Company or product showing rapid growth trajectory"),
    )),
    Badge("Series D $200M", (
        BadgeColor("green", "Significant funding round — strong market validation"),
    )),
    Badge("IPO 2024", (
        BadgeColor("green", "Recent IPO — scale and market maturity confirmed"),
    )),
    Badge("Layoffs Reported", (
        BadgeColor("amber", "Workforce reductions reported — potential instability"),
    )),
    Badge("~2M Users", (
        BadgeColor("green", "Large install base — significant training population"),
    )),
    Badge("~50K Users", (
        BadgeColor("gray", "Moderate install base"),
    )),
    Badge("~500 Users", (
        BadgeColor("amber", "Small install base — limited training population"),
    )),
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
    Badge("Active Certification", (
        BadgeColor("green", "Active certification program with exams"),
    )),
    Badge("Emerging Certification", (
        BadgeColor("gray", "Certification program in early stages"),
    )),
    Badge("Competitor Labs Confirmed", (
        BadgeColor("green", "Other providers invest in hands-on training for this product"),
    )),
    Badge("High-Demand Category", (
        BadgeColor("green", "Product category has inherent demand for hands-on training"),
    )),
    Badge("AI-Powered Product", (
        BadgeColor("green", "Product has AI features that require hands-on practice"),
    )),
    Badge("AI Platform", (
        BadgeColor("green", "Product IS an AI platform — labs teach building/training/deploying AI"),
    )),
    Badge("Enterprise Validated", (
        BadgeColor("green", "Enterprise adoption confirmed at scale"),
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

_market_demand_dimension = Dimension(
    name="Market Demand",
    weight=20,
    question="Does the broader market validate the need for hands-on training on this product?",
    badges=_market_demand_badges,
    scoring_signals=_market_demand_signals,
    cap=20,
    notes="AI looks at company-specific signals first, product signals second, category as the floor.",
)


PILLAR_INSTRUCTIONAL_VALUE = Pillar(
    name="Instructional Value",
    weight=30,
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
    # Product Adoption evidence
    Badge("Customer Enablement", (
        BadgeColor("green", "Dedicated customer enablement program confirmed"),
        BadgeColor("amber", "Mentioned but unstructured"),
    )),
    Badge("Customer Success", (
        BadgeColor("green", "Dedicated CS team confirmed"),
        BadgeColor("amber", "Mentioned but unclear scope"),
    )),
    Badge("Channel Enablement", (
        BadgeColor("green", "Partner training program confirmed"),
        BadgeColor("amber", "Channel exists, no formal enablement"),
    )),
    # Skill Development evidence
    Badge("Certification Program", (
        BadgeColor("green", "Active certification with exams"),
        BadgeColor("amber", "Mentioned, no active exams"),
    )),
    Badge("Training Catalog", (
        BadgeColor("green", "Published courses, meaningful scale"),
        BadgeColor("amber", "Small catalog or shallow"),
    )),
    # Compliance & Risk evidence
    Badge("Regulated Industry", (
        BadgeColor("green", "Healthcare, finance, cybersecurity — compliance inherent"),
        BadgeColor("gray", "Some regulation, not compliance-driven"),
    )),
    Badge("Compliance Training Program", (
        BadgeColor("green", "Training built around regulatory requirements"),
    )),
    Badge("Audit Requirements", (
        BadgeColor("green", "External audits require demonstrated competence"),
    )),
    # Cross-cutting
    Badge("Training Leadership", (
        BadgeColor("green", "C-level or VP dedicated to learning/enablement"),
        BadgeColor("gray", "Director-level training leader"),
        BadgeColor("amber", "Managers only"),
    )),
    Badge("Training Culture", (
        BadgeColor("green", "Training permeates the business — multiple teams across the lifecycle"),
        BadgeColor("gray", "Some investment, concentrated in one area"),
        BadgeColor("amber", "Minimal — one or two people"),
    )),
)

_training_commitment_dimension = Dimension(
    name="Training Commitment",
    weight=25,
    question="Have they invested in training? What's the evidence?",
    badges=_training_commitment_badges,
    notes="Badges are evidence of organizational commitment across three motivation categories "
          "(product adoption, skill development, compliance & risk). The three motivations also "
          "serve as a framing variable that shapes how recommendations are communicated.",
)


_organizational_dna_badges = (
    Badge("Partner Ecosystem", (
        BadgeColor("green", "Strong partner network"),
        BadgeColor("gray", "Some partnerships"),
        BadgeColor("amber", "No partner program or limited partners"),
    ), notes="Variable-driven: ~500 ATPs, Strong Channel Program, etc."),
    Badge("Build vs Buy", (
        BadgeColor("green", "Uses external platforms — Platform Buyer"),
        BadgeColor("gray", "Mixed Approach — some build, some buy"),
        BadgeColor("amber", "Builds In-House"),
    )),
    Badge("Integration Maturity", (
        BadgeColor("green", "Open Platform — rich APIs, marketplace, SDKs"),
        BadgeColor("gray", "APIs exist but limited"),
        BadgeColor("amber", "Closed System"),
    )),
    Badge("Ease of Engagement", (
        BadgeColor("green", "Accessible — mid-size, partner-friendly"),
        BadgeColor("gray", "Large but workable"),
        BadgeColor("amber", "Hard to Engage — complex organization"),
    )),
)

_organizational_dna_dimension = Dimension(
    name="Organizational DNA",
    weight=25,
    question="Are they the kind of company that partners and builds training programs?",
    badges=_organizational_dna_badges,
    notes="The character of the organization — do they partner or build in-house? "
          "Are they easy or hard to do business with? All badges are variable-driven.",
)


_delivery_capacity_badges = (
    Badge("ATP / Learning Partners", (
        BadgeColor("green", "Scaled network of authorized training partners"),
        BadgeColor("amber", "Limited partner network"),
    )),
    Badge("LMS Platform", (
        BadgeColor("green", "Skillable partner LMS (Docebo, Cornerstone, Skillable TMS)"),
        BadgeColor("gray", "Other LMS platform in use"),
    ), notes="Variable-driven: shows specific platform + audience (Public/Internal)"),
    Badge("Lab Platform", (
        BadgeColor("green", "Skillable (expansion opportunity)"),
        BadgeColor("amber", "Competitor platform (migration opportunity)"),
    ), notes="Variable-driven: shows exact platform name. DIY noted in evidence."),
    Badge("Gray Market Offering", (
        BadgeColor("amber", "Third-party training exists — conversation starter"),
    )),
)

_delivery_capacity_dimension = Dimension(
    name="Delivery Capacity",
    weight=30,
    question="Can they get labs to learners at scale?",
    badges=_delivery_capacity_badges,
    notes="Weighted highest within Customer Fit because having labs = cost, "
          "delivering labs = value. Without delivery channels, labs never reach "
          "learners and there is no business impact.",
)


_build_capacity_badges = (
    Badge("Content Dev Team", (
        BadgeColor("green", "Named training org, Lab Authors, IDs, Tech Writers"),
    )),
    Badge("Technical Build Team", (
        BadgeColor("green", "Can build lab environments, not just content"),
    )),
    Badge("DIY Labs", (
        BadgeColor("green", "Already building labs themselves — have the skills"),
    )),
    Badge("Content Outsourcing", (
        BadgeColor("amber", "Third parties build content — ProServ opportunity"),
    )),
)

_build_capacity_dimension = Dimension(
    name="Build Capacity",
    weight=20,
    question="Can they create the labs?",
    badges=_build_capacity_badges,
    notes="Weighted lowest because Skillable Professional Services or partners can fill this gap. "
          "Low Build Capacity + strong Delivery Capacity = Professional Services Opportunity.",
)


PILLAR_CUSTOMER_FIT = Pillar(
    name="Customer Fit",
    weight=30,
    level="organization",
    question="Is this organization a good match for Skillable?",
    dimensions=(
        _training_commitment_dimension,
        _organizational_dna_dimension,
        _delivery_capacity_dimension,
        _build_capacity_dimension,
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
    (45, "high"):   VerdictDefinition("High Potential", "Gaps to work through but significant upside justifies the investment.", "light_amber"),
    (45, "medium"): VerdictDefinition("Worth Pursuing", "Good fundamentals all around. Give it attention.", "light_amber"),
    (45, "low"):    VerdictDefinition("Solid Prospect", "Decent fit, modest opportunity. Steady.", "light_amber"),
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
    TechnicalFitMultiplier(32, 100, "any", 1.0),
    TechnicalFitMultiplier(24, 31, "datacenter", 1.0),
    TechnicalFitMultiplier(19, 31, "non-datacenter", 0.75),
    TechnicalFitMultiplier(10, 18, "any", 0.65),
    TechnicalFitMultiplier(0, 9, "any", 0.50),
)

DATACENTER_METHODS = ("Hyper-V", "ESX", "Container", "Azure VM", "AWS VM")


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


CEILING_FLAGS: dict[str, dict] = {
    # When the AI emits any of these flags, Product Labability cannot exceed
    # the listed max_score regardless of how the dimension math came out.
    # The math layer enforces this — the AI cannot bypass it.
    #
    # Architecture sharpening (in-progress refactor): `saas_only` and
    # `multi_tenant_only` were historically scoring caps. They are now
    # CLASSIFICATION METADATA ONLY — they describe what the product IS
    # (deployment shape) without capping the score. The scoring cap for
    # SaaS products comes from the new `Sandbox API` canonical badge: when
    # research confirms there is no provisioning API, the math layer applies
    # a cap based on whether Simulation is still viable.
    #
    # Both flags remain in POOR_MATCH_FLAGS so existing reporting and
    # filtering keeps working. Their max_score is set to 100 (no effective
    # cap) so old cached analyses don't suddenly drop in score.
    "bare_metal_required": {
        "max_score": 5,
        "reason": "Physical hardware required — no virtualization path",
    },
    "no_api_automation": {
        "max_score": 5,
        "reason": "No API automation feasible — manual provisioning only",
    },
    "saas_only": {
        "max_score": 100,
        "reason": "Classification metadata only — Sandbox API badge drives the cap",
    },
    "multi_tenant_only": {
        "max_score": 100,
        "reason": "Classification metadata only — Sandbox API badge drives the cap",
    },
}

# The historical render-time synthetic-injection machinery — empty
# ISOLATION_BLOCKING_CEILING_FLAGS frozenset, LAB_ACCESS_DIMENSION_NAME
# constant, and SYNTHETIC_BADGES dict — has been removed entirely. The
# `Learner Isolation` canonical badge in Lab Access (gatekeeper, green/
# amber/red, always emit) now carries this signal directly, sourced from
# research evidence about per-user provisioning capability. The call sites
# in app_new._normalize_badges_for_scoring have been removed.


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY PRIORS
#
# Product categories and their default demand ratings.  The category sets
# the floor for Market Demand scoring.  Company-specific signals come first,
# product signals second, category as the fallback.
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORY_PRIORS: tuple[CategoryPrior, ...] = (
    # High demand (+8)
    CategoryPrior("Cybersecurity", 8, "high"),
    CategoryPrior("Cloud Infrastructure", 8, "high"),
    CategoryPrior("Networking/SDN", 8, "high"),
    CategoryPrior("Data Science & Engineering", 8, "high"),
    CategoryPrior("Data & Analytics", 8, "high"),
    CategoryPrior("DevOps", 8, "high"),
    # Moderate demand (+4)
    CategoryPrior("Data Protection", 4, "moderate"),
    CategoryPrior("Infrastructure/Virtualization", 4, "moderate"),
    CategoryPrior("App Development", 4, "moderate"),
    CategoryPrior("ERP/CRM", 4, "moderate"),
    CategoryPrior("Healthcare IT", 4, "moderate"),
    CategoryPrior("FinTech", 4, "moderate"),
    CategoryPrior("Collaboration", 4, "moderate"),
    CategoryPrior("Content Management", 4, "moderate"),
    CategoryPrior("Legal Tech", 4, "moderate"),
    CategoryPrior("Industrial/OT", 4, "moderate"),
    # Low demand (+0)
    CategoryPrior("Simple SaaS", 0, "low"),
    CategoryPrior("Consumer", 0, "low"),
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
    # Simulation
    "simulation":        "Simulation",
    "simulated":         "Simulation",
}

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

CONSUMPTION_MOTIONS: tuple[ConsumptionMotion, ...] = (
    ConsumptionMotion(
        "Customer Onboarding & Enablement",
        0.02, 0.08,
        "New customers getting started with the product; onboarding programs, guided setup labs"),
    ConsumptionMotion(
        "Authorized Training Partners & Channel Enablement",
        0.05, 0.15,
        "ATP network, resellers, and channel partners who deliver or sell training"),
    ConsumptionMotion(
        "General Practice & Skilling Experiences",
        0.02, 0.08,
        "Ongoing skills development for existing users, admins, and practitioners"),
    ConsumptionMotion(
        "Certification / PBT",
        0.02, 0.10,
        "Performance-based testing and proctored certification exams"),
    ConsumptionMotion(
        "Employee Technical Enablement",
        0.05, 0.15,
        "Internal SEs, presales, professional services, and support staff"),
    ConsumptionMotion(
        "Events & Conferences",
        0.30, 0.70,
        "Annual flagship events, user conferences, product launch labs, trade show hands-on tracks"),
)

# Hard ceilings — never exceed these adoption rates
ADOPTION_CEILING_EVENTS = 0.80
ADOPTION_CEILING_NON_EVENTS = 0.20


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
    "ERP/CRM": (
        "Financial Management", "HR & HCM", "Supply Chain",
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
    """
    issues: list[str] = []

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

    # 10. Consumption motion adoption ceilings are valid
    for motion in CONSUMPTION_MOTIONS:
        if motion.adoption_ceiling_low > motion.adoption_ceiling_high:
            issues.append(
                f"Motion '{motion.label}' has low ceiling > high ceiling: "
                f"{motion.adoption_ceiling_low} > {motion.adoption_ceiling_high}"
            )
        if motion.label == "Events & Conferences":
            if motion.adoption_ceiling_high > ADOPTION_CEILING_EVENTS:
                issues.append(
                    f"Events motion ceiling {motion.adoption_ceiling_high} "
                    f"exceeds hard cap {ADOPTION_CEILING_EVENTS}"
                )
        else:
            if motion.adoption_ceiling_high > ADOPTION_CEILING_NON_EVENTS:
                issues.append(
                    f"Motion '{motion.label}' ceiling {motion.adoption_ceiling_high} "
                    f"exceeds non-events cap {ADOPTION_CEILING_NON_EVENTS}"
                )

    # 11. Technical Fit Multiplier ranges don't have gaps
    multiplier_ranges = sorted(TECHNICAL_FIT_MULTIPLIERS, key=lambda m: m.score_min)
    if multiplier_ranges[0].score_min != 0:
        issues.append("Technical Fit Multiplier does not start at score 0")

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
# SKILLABLE CAPABILITIES
#
# What Skillable can do — updated as features ship.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SkillableCapability:
    """A Skillable platform capability the AI should reference."""
    name: str
    description: str

SKILLABLE_CAPABILITIES: tuple[SkillableCapability, ...] = (
    SkillableCapability("Skillable Datacenter",
        "Purpose-built for ephemeral learning and skill validation. Three virtualization fabrics: "
        "Hyper-V (default), VMware ESX (use only for nested virt or socket licensing), Docker "
        "(container-native only). Full custom network topologies: private networks, NAT, VPNs, "
        "dedicated IP addressing, network traffic monitoring."),
    SkillableCapability("Cloud Slice - Azure",
        "Provisions isolated Azure environments per learner. Two modes: CSR (resource group) and "
        "CSS (subscription-level). ALL Azure services supported after Security Review. Bicep and "
        "ARM JSON templates. Access Control Policies restrict services, SKUs, and regions."),
    SkillableCapability("Cloud Slice - AWS",
        "Provisions a dedicated, isolated AWS account per learner. Supported services list maintained "
        "separately. Not yet supported services flagged explicitly."),
    SkillableCapability("Skillable Simulations",
        "For scenarios where real labs are impractical. AI Vision compute and platform overhead apply."),
    SkillableCapability("Automated Scoring",
        "Labs include automated scoring via API, PowerShell, CLI, Azure Resource Graph queries, and "
        "AI Vision."),
    SkillableCapability("Hyper-V Preference",
        "Always prefer Skillable Datacenter (Hyper-V) over cloud VMs when the product doesn't "
        "specifically require cloud infrastructure. Datacenter VMs launch predictably, no idle "
        "storage costs, no egress charges, no throttling."),
    SkillableCapability("M365 Tenant Provisioning",
        "Automated M365 tenant provisioning via Azure Cloud Slice. Three tiers: Base (E3), "
        "Full (E5), Full+AI (E7 coming soon)."),
    SkillableCapability("BIOS GUID Pinning",
        "Skillable can pin Custom UUID in VM profiles — handles hardware-fingerprinted licensing."),
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
                     "Explain why this question matters — what it unblocks if answered.",
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
                     "product, not generically.",
    ),
    BriefcaseSection(
        pillar_name="Customer Fit",
        section_title="Account Intelligence",
        description="Organizational signals — training leadership, org complexity, "
                    "LMS platform, competitive signals, news.",
        instructions="Surface the most important organizational context a seller should "
                     "know before a meeting. Include: key contacts and their relevance, "
                     "organizational complexity or dynamics (mergers, growth, restructuring), "
                     "training infrastructure signals (LMS, competitors, DIY labs), and any "
                     "signal that affects how to approach the account.",
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
