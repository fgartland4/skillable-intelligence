"""Data models for the Skillable Intelligence Platform.

Built from Platform-Foundation.md and Badging-and-Scoring-Reference.md.
All field names use locked vocabulary (GP4 — Self-Evident Design).

Hierarchy: Fit Score → Pillars → Dimensions → Requirements (badges)
Three Pillars (40/30/30): Product Labability, Instructional Value, Customer Fit
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
    """
    name: str
    color: str                     # "green" | "gray" | "amber" | "red"
    qualifier: str = ""            # "Strength" | "Opportunity" | "Context" | "Risk" | "Blocker"
    evidence: list[Evidence] = field(default_factory=list)


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

    `score_override` lets the scoring math layer set the pillar score
    explicitly — used when ceiling flags cap Product Labability below the
    raw dimension sum. Dimension scores remain authentic to the badges that
    matched; the override only affects the pillar-level score and the
    weighted contribution.
    """
    name: str
    weight: int                    # Percentage of Fit Score (40, 30, or 30)
    dimensions: list[DimensionScore] = field(default_factory=list)
    score_override: Optional[int] = None  # Set by scoring_math when ceiling enforced

    @property
    def score(self) -> int:
        """Pillar score. If `score_override` is set (e.g., ceiling applied),
        use it. Otherwise sum the dimensions, capped at 100."""
        if self.score_override is not None:
            return self.score_override
        return min(100, sum(d.score for d in self.dimensions))

    @property
    def weighted_contribution(self) -> float:
        """This Pillar's contribution to the Fit Score."""
        return self.score * (self.weight / 100)


# ═══════════════════════════════════════════════════════════════════════════════
# Fit Score — the composite of three Pillars
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FitScore:
    """The composite Fit Score — three Pillars weighted 40/30/30.

    Product Labability (40%) + Instructional Value (30%) = 70% product
    Customer Fit (30%) = 30% organization

    Math layer audit trail:
      - `total_override` — set by scoring_math when ceiling flags or the
        Technical Fit Multiplier change the result from a naive weighted sum.
      - `pl_score_pre_ceiling` — what Product Labability would have scored
        without ceiling enforcement.
      - `technical_fit_multiplier` — the multiplier applied to IV + CF.
      - `ceilings_applied` — list of flags that capped Product Labability.
    """
    product_labability: PillarScore = field(default_factory=lambda: PillarScore(
        name="Product Labability", weight=40,
        dimensions=[
            DimensionScore(name="Provisioning", weight=35),
            DimensionScore(name="Lab Access", weight=25),
            DimensionScore(name="Scoring", weight=15),
            DimensionScore(name="Teardown", weight=25),
        ]
    ))
    instructional_value: PillarScore = field(default_factory=lambda: PillarScore(
        name="Instructional Value", weight=30,
        dimensions=[
            DimensionScore(name="Product Complexity", weight=40),
            DimensionScore(name="Mastery Stakes", weight=25),
            DimensionScore(name="Lab Versatility", weight=15),
            DimensionScore(name="Market Demand", weight=20),
        ]
    ))
    customer_fit: PillarScore = field(default_factory=lambda: PillarScore(
        name="Customer Fit", weight=30,
        dimensions=[
            DimensionScore(name="Training Commitment", weight=25),
            DimensionScore(name="Organizational DNA", weight=25),
            DimensionScore(name="Delivery Capacity", weight=30),
            DimensionScore(name="Build Capacity", weight=20),
        ]
    ))
    total_override: Optional[int] = None
    pl_score_pre_ceiling: Optional[int] = None
    technical_fit_multiplier: float = 1.0
    ceilings_applied: list[dict] = field(default_factory=list)

    @property
    def pillars(self) -> list[PillarScore]:
        return [self.product_labability, self.instructional_value, self.customer_fit]

    @property
    def total(self) -> int:
        """Fit Score. Uses `total_override` if set (e.g., math layer applied
        ceilings or the Technical Fit Multiplier), otherwise weighted sum."""
        if self.total_override is not None:
            return self.total_override
        return round(sum(p.weighted_contribution for p in self.pillars))

    @property
    def verdict_inputs(self) -> dict:
        """Returns the inputs needed for verdict grid lookup."""
        return {
            "fit_score": self.total,
            "product_labability_score": self.product_labability.score,
        }


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
    user_personas: list[str] = field(default_factory=list)
    lab_highlight: str = ""        # Why this is a great hands-on candidate
    lab_concepts: list[str] = field(default_factory=list)
    poor_match_flags: list[str] = field(default_factory=list)
    recommendation: list[str] = field(default_factory=list)

    # Scoring
    fit_score: FitScore = field(default_factory=FitScore)
    acv_potential: ACVPotential = field(default_factory=ACVPotential)
    verdict: Optional[Verdict] = None

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
    briefcase: Optional[SellerBriefcase] = None
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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
