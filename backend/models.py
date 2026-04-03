"""Data models for the Skillable Intelligence platform."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class Evidence:
    claim: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None


@dataclass
class DimensionScore:
    score: int = 0
    evidence: list[Evidence] = field(default_factory=list)
    summary: str = ""


def compute_product_score(p: dict) -> int:
    """Compute the labability total from a product dict loaded from JSON storage."""
    scores = p.get("labability_score") or {}
    # Accept both new field names and legacy names for backward compat with cached analyses
    tech = (
        scores.get("product_labability", {}) or scores.get("technical_orchestrability", {})
    ).get("score", 0)
    other = sum(
        s.get("score", 0)
        for k, s in scores.items()
        if k not in ("product_labability", "technical_orchestrability") and isinstance(s, dict)
    )
    return compute_labability_total(tech, other, p.get("skillable_path", ""))


def compute_labability_total(tech: int, other: int, path: str = "") -> int:
    """Single source of truth for the labability total score with multiplier logic.

    Composite scoring model (40/30/20/10):
      Product Labability      40%  (0–40)  — Can we orchestrate this product?
      Instructional Value     30%  (0–30)  — Does this product need labs?
      Organizational Readiness 20% (0–20)  — Do they have resources to create and deliver labs?
      Market Readiness        10%  (0–10)  — Is the world interested?

    tech  — product_labability score (0-40)
    other — sum of instructional_value (0-30) + organizational_readiness (0-20) + market_readiness (0-10) = 0-60
    path  — skillable_path string ("A1", "A2", "B", "C", "Unknown")

    Multiplier: Product Labability gates the composite. A product that cannot be
    orchestrated gets no credit for how strong the other dimensions are — the multiplier
    enforces this gate. Thresholds scaled proportionally from legacy 0-25 → 0-40 range.

    """
    if tech >= 32:
        multiplier = 1.0
    elif tech >= 24 and path == "B":
        # VM/Datacenter path: the VM image IS the lab — no cloud APIs needed.
        # Any viable VM product with tech ≥ 24 gets full 1.0x multiplier.
        multiplier = 1.0
    elif tech >= 19:
        multiplier = 0.75
    elif tech >= 10:
        multiplier = 0.40
    else:
        multiplier = 0.15
    return min(100, tech + round(other * multiplier))


@dataclass
class ProductLababilityScore:
    product_labability: DimensionScore = field(default_factory=DimensionScore)       # 40% — Can we orchestrate this product?
    instructional_value: DimensionScore = field(default_factory=DimensionScore)       # 30% — Does this product need labs?
    organizational_readiness: DimensionScore = field(default_factory=DimensionScore)  # 20% — Do they have resources to build and deliver?
    market_readiness: DimensionScore = field(default_factory=DimensionScore)          # 10% — Is the world interested?
    path: str = ""  # mirrors Product.skillable_path for correct multiplier in .total

    @property
    def total(self) -> int:
        tech = self.product_labability.score
        other = (
            self.instructional_value.score
            + self.organizational_readiness.score
            + self.market_readiness.score
        )
        return compute_labability_total(tech, other, self.path)


@dataclass
class Contact:
    name: str
    title: str
    role_type: str  # "decision_maker" or "influencer"
    linkedin_url: Optional[str] = None
    relevance: str = ""  # Why this person matters for this product


@dataclass
class OrgUnit:
    name: str  # e.g., "Global Partner Enablement", "Cohesity Academy"
    type: str  # "department", "subsidiary", "business_unit"
    description: str = ""


@dataclass
class ConsumptionMotion:
    label: str = ""                 # e.g. "Technical Enablement (Internal)"
    population_low: int = 0
    population_high: int = 0
    hours_low: float = 0
    hours_high: float = 0
    adoption_pct: float = 0.5       # 0.0–1.0 — fraction of population actually using labs
    rationale: str = ""             # 1-2 sentence explanation of estimates


@dataclass
class ConsumptionPotential:
    motions: list[ConsumptionMotion] = field(default_factory=list)
    annual_hours_low: int = 0
    annual_hours_high: int = 0
    vm_rate_estimate: int = 0       # $/hr: Cloud $10.50, Standard VM $12–15, Large VM $45–55, Simulation $5
    methodology_note: str = ""      # visible caveat displayed in report


@dataclass
class Product:
    name: str
    category: str
    description: str = ""
    deployment_model: str = ""          # "self-hosted", "cloud", "hybrid", "SaaS-only"
    skillable_path: str = ""            # "A1", "A2", "B", "C", "Unknown"
    path_tier: str = ""                 # "Best - Rich APIs", "Next Best - Credential Pool", etc.
    skillable_mechanism: str = ""       # "Skillable Datacenter", "Cloud Slice - Azure/AWS", etc.
    fabric: str = ""                    # "Hyper-V", "ESX", "Docker", "Azure Cloud Slice", "AWS Cloud Slice", "Custom API", "Simulation", "Unclear"
    user_personas: list[str] = field(default_factory=list)  # e.g. ["IT Admin / Operator", "Developer / Engineer"]
    product_url: str = ""               # canonical product page URL
    lab_highlight: str = ""              # free-form short phrase — what makes this a great hands-on candidate
    poor_match_flags: list[str] = field(default_factory=list)
    api_scoring_potential: str = ""
    recommendation: list[str] = field(default_factory=list)
    labability_score: ProductLababilityScore = field(default_factory=ProductLababilityScore)
    owning_org: Optional[OrgUnit] = None
    contacts: list[Contact] = field(default_factory=list)
    lab_concepts: list[str] = field(default_factory=list)
    consumption_potential: ConsumptionPotential = field(default_factory=ConsumptionPotential)


@dataclass
class LabMaturityScore:
    # Raw max = 35 + 27 + 35 + 10 + 10 = 117 → normalized ÷ 1.17 → 0-100
    training_org_maturity: DimensionScore = field(default_factory=DimensionScore)   # 0-35
    partner_program: DimensionScore = field(default_factory=DimensionScore)          # 0-27
    customer_success: DimensionScore = field(default_factory=DimensionScore)         # 0-35
    organizational_dna: DimensionScore = field(default_factory=DimensionScore)       # 0-10
    tech_readiness: DimensionScore = field(default_factory=DimensionScore)           # 0-10

    @property
    def raw_total(self) -> int:
        return (
            self.training_org_maturity.score
            + self.partner_program.score
            + self.customer_success.score
            + self.organizational_dna.score
            + self.tech_readiness.score
        )

    @property
    def total(self) -> int:
        return min(100, round(self.raw_total / 1.17))


@dataclass
class CompanyAnalysis:
    company_name: str
    company_url: Optional[str] = None
    company_description: str = ""
    organization_type: str = "software_company"
    # "software_company" | "academic_institution" | "training_organization" |
    # "systems_integrator" | "technology_distributor" | "professional_services" | "other"
    products: list[Product] = field(default_factory=list)
    lab_maturity: LabMaturityScore = field(
        default_factory=LabMaturityScore
    )
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    analysis_id: str = ""
    discovery_id: str = ""
    total_products_discovered: int = 0

    @property
    def top_products(self) -> list[Product]:
        return sorted(self.products, key=lambda p: p.labability_score.total, reverse=True)


@dataclass
class ProspectorRow:
    """Summary row for the Prospector results table."""
    company_name: str
    company_url: str = ""
    top_product: str = ""
    lab_score: int = 0
    lab_maturity_score: int = 0
    composite_score: int = 0
    skillable_path: str = ""          # "Labable" | "Simulations" | "Do Not Pursue"
    top_contact_name: str = ""
    top_contact_title: str = ""
    top_contact_linkedin: str = ""
    second_contact_name: str = ""
    second_contact_title: str = ""
    second_contact_linkedin: str = ""
    analysis_id: str = ""
    flagged_poor_fit: bool = False
    # Product labability counts (from discovery phase)
    total_highly_labable: int = 0
    total_likely_labable: int = 0
    total_not_labable: int = 0
    # Partnership signals (from discovery phase)
    atp_program: str = ""             # program name or blank
    channel_program: str = ""         # program name or blank
    ondemand_library: str = ""        # course count or blank
    cert_program: str = ""            # cert count or blank
    existing_lab_partner: str = ""    # platform name, "DIY", or blank
    ilt_vilt: str = ""                # "true" or blank
    gray_market: str = ""             # "true" or blank


