"""Rubric grader — Claude-in-Score for Pillar 2 and Pillar 3 qualitative dims.

Architecture note: per Frank's 2026-04-08 decision (lock-in #4 in
docs/next-session-todo.md §0b), Pillar 2 and Pillar 3 rubric dimensions
cannot be scored with pure Python heuristics because strength tiering is
genuinely qualitative judgment. This module is the narrow slice of
Claude-in-Score the rebuild permits: ONE small focused Claude call per
rubric dimension, reading the truth-only fact drawer, emitting graded
signals with strength + evidence text.

The grader output is a list[GradedSignal] keyed by dimension. The
pure-Python pillar_2_scorer and pillar_3_scorer consume these records
plus facts and produce deterministic PillarScores (baseline + rubric
credits + penalties + caps) — no Claude in the math layer.

Folding strength grading and evidence-text writing together is
deliberate: both were going to need Claude anyway (strength for the
math, evidence text for the badge hover display at Step 6), and one
call per dimension produces both for free.

Design:
  - `build_rubric_grader_prompt(dimension, facts_context, subject_label)`
    assembles the grader prompt at runtime from the Dimension object in
    scoring_config.py. Define-Once: the is_about, is_not_about,
    signal_categories, and rubric tiers all come from config.
  - `grade_dimension(dimension, facts_context, subject_label)` is the
    low-level Claude call.
  - Per-dimension wrapper functions (`grade_product_complexity`,
    `grade_market_demand`, etc.) prepare the facts_context for their
    specific dimension and call grade_dimension.
  - Parallel helpers `grade_all_for_product` and `grade_all_for_company`
    run the per-dimension grader calls concurrently.
  - Output: list[GradedSignal] with signal_category from the locked
    rubric list, strength from the locked tier list, evidence_text
    written by Claude with confidence hedging.

No hardcoded numbers. All rubric vocabulary comes from scoring_config.
Circular import avoidance: _call_claude is imported locally inside
grade_dimension (same pattern as researcher.py).
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, is_dataclass
from typing import Optional

import scoring_config as cfg
from models import (
    CompanyAnalysis,
    GradedSignal,
    Product,
)

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Dimension-name constants (strings appear once; references use these)
# ═══════════════════════════════════════════════════════════════════════════════

_PILLAR_IV = "Instructional Value"
_PILLAR_CF = "Customer Fit"

_DIM_PRODUCT_COMPLEXITY = "Product Complexity"
_DIM_MASTERY_STAKES = "Mastery Stakes"
_DIM_LAB_VERSATILITY = "Lab Versatility"
_DIM_MARKET_DEMAND = "Market Demand"

_DIM_TRAINING_COMMITMENT = "Training Commitment"
_DIM_BUILD_CAPACITY = "Build Capacity"
_DIM_DELIVERY_CAPACITY = "Delivery Capacity"
_DIM_ORGANIZATIONAL_DNA = "Organizational DNA"


# ═══════════════════════════════════════════════════════════════════════════════
# Config lookups — resolved once at module load
# ═══════════════════════════════════════════════════════════════════════════════

def _find_dimension(pillar_name: str, dim_name: str) -> cfg.Dimension:
    for pillar in cfg.PILLARS:
        if pillar.name != pillar_name:
            continue
        for dim in pillar.dimensions:
            if dim.name == dim_name:
                return dim
    raise RuntimeError(
        f"rubric_grader: dimension {dim_name!r} not found in pillar {pillar_name!r}"
    )


# Resolve Pillar 2 + Pillar 3 dimensions at module load. Any drift from
# scoring_config.py fails the import loudly.
_PRODUCT_COMPLEXITY_DIM = _find_dimension(_PILLAR_IV, _DIM_PRODUCT_COMPLEXITY)
_MASTERY_STAKES_DIM = _find_dimension(_PILLAR_IV, _DIM_MASTERY_STAKES)
_LAB_VERSATILITY_DIM = _find_dimension(_PILLAR_IV, _DIM_LAB_VERSATILITY)
_MARKET_DEMAND_DIM = _find_dimension(_PILLAR_IV, _DIM_MARKET_DEMAND)

_TRAINING_COMMITMENT_DIM = _find_dimension(_PILLAR_CF, _DIM_TRAINING_COMMITMENT)
_BUILD_CAPACITY_DIM = _find_dimension(_PILLAR_CF, _DIM_BUILD_CAPACITY)
_DELIVERY_CAPACITY_DIM = _find_dimension(_PILLAR_CF, _DIM_DELIVERY_CAPACITY)
_ORGANIZATIONAL_DNA_DIM = _find_dimension(_PILLAR_CF, _DIM_ORGANIZATIONAL_DNA)


# ═══════════════════════════════════════════════════════════════════════════════
# Shared grader prompt builder
# ═══════════════════════════════════════════════════════════════════════════════

_SHARED_HARD_RULES = """
═══ HARD RULES ═══

1. Grade ONLY signals you find evidence for in the facts provided.
2. Never invent facts. If the fact drawer is silent on something, do not
   fill it in from general knowledge.
3. Every signal you emit needs a strength tier AND evidence text grounded
   in the actual observation field of the fact drawer.
4. Evidence text MUST use confidence hedging language that matches the
   fact's confidence field: "confirmed" for direct evidence, "indicated"
   for strong indirect evidence, "inferred" for pattern-based assumption.
5. **STAY IN THIS DIMENSION.** If you see something that's really about
   a different dimension (read the "NOT about" list), do NOT emit it here.
   A separate grader call handles that other dimension.
6. **Mandatory negative emission.** If you find evidence of ANY negative
   signal category in the list, you MUST emit it. Do not smooth over
   findings. A dimension with one strong positive and one red blocker is
   an accurate grading; a dimension with the red blocker omitted is a lie.
7. Maximum 6 signals per dimension total. Up to 4 positive and up to 2
   negative — the negative budget is independent of the positive budget.
   Pick the strongest and most load-bearing signals.
8. For each signal, set `color` based on strength + sign:
   - positive strong → green
   - positive moderate → green (or gray if informational)
   - positive weak → don't emit
   - informational → gray
   - negative → amber for soft penalties, red for hard blockers
9. **Badge naming rules — the evidence_text IS the badge name source.**
   - Name the SPECIFIC provider, not the category: "Pearson VUE" not
     "Cert Delivery Infra". "ILT Calendar" not "Published Course".
   - "Content Team" not "Content Team Named". "IDs on Staff" not "ID IDs".
   - Use count-based names when data exists: "~12 Pluralsight Courses"
     not "Indep Training Market".
   - Evidence-specific names allow nuanced findings to coexist: "~12
     Pluralsight Courses" (green) alongside "Thin Training Market" (amber)
     is not a contradiction — both are true.
   - For small training populations, use "Niche Audience" (amber).
10. **Academic vocabulary override.** When the organization is a university
    or school, use academic language: "Curriculum" not "Training Catalog",
    "Faculty" not "Training Leadership", "Degree Programs" not "Training
    Programs", "Lab-Based Courses" not "Hands On".
11. **Market Demand differentiation.** A perfect 20/20 is rare. Within a
    category (e.g. cybersecurity), differentiate product-level market
    position. A market leader (CrowdStrike, Palo Alto) scores higher than
    a mid-tier vendor (Trellix, Tanium). Use install base scale, independent
    training market size, and cert ecosystem breadth to differentiate.
"""

_OUTPUT_SCHEMA = """
═══ OUTPUT ═══

Return ONLY a JSON array, no prose, no markdown code fences. Each element:

{
  "signal_category": "<one of the signal categories listed above>",
  "strength": "strong" | "moderate" | "weak" | "informational",
  "evidence_text": "<plain-English grounded in the observation field, with confidence hedging>",
  "confidence": "confirmed" | "indicated" | "inferred",
  "color": "green" | "amber" | "red" | "gray",
  "source_fact_path": "<dotted path to the fact field you read, e.g. customer_fit_facts.build_capacity.is_already_building_labs>"
}

Return an empty array [] if the facts don't support any gradable signals.
"""


def _format_tier_line(tier: cfg.RubricTier) -> str:
    return f"  • {tier.strength} ({tier.points} pts): {tier.criterion}"


def _format_bullet_list(items: tuple[str, ...]) -> str:
    return "\n".join(f"  • {it}" if it else "" for it in items)


def build_rubric_grader_prompt(
    dimension: cfg.Dimension,
    facts_context: str,
    subject_label: str,
) -> str:
    """Build the full rubric grader prompt for one dimension.

    Reads is_about / is_not_about / signal_categories / rubric tiers
    directly from the Dimension object in scoring_config.py. Define-Once:
    any vocabulary change in the config propagates automatically.
    """
    rubric = dimension.rubric
    if rubric is None:
        raise RuntimeError(
            f"build_rubric_grader_prompt: dimension {dimension.name!r} has no rubric"
        )

    tiers_text = "\n".join(_format_tier_line(t) for t in rubric.tiers)
    is_about_text = _format_bullet_list(rubric.is_about)
    is_not_about_text = _format_bullet_list(rubric.is_not_about)
    categories_text = "\n".join(f"  • {c}" for c in rubric.signal_categories)

    return f"""You are a research analyst grading qualitative signals for the **{dimension.name}** dimension of the Skillable scoring framework.

Your only job is to look at the facts provided and grade each relevant signal against the {dimension.name} rubric. You are not scoring other dimensions. You are not inventing facts. You are not writing badges for display. You are producing graded signal records that the Skillable math layer will consume deterministically.

═══ DIMENSION QUESTION ═══

{dimension.question}

═══ WHAT {dimension.name.upper()} IS ABOUT ═══

{is_about_text}

═══ WHAT {dimension.name.upper()} IS **NOT** ABOUT ═══

{is_not_about_text}

═══ SIGNAL CATEGORIES YOU MAY EMIT ═══

Pick from ONLY these categories — do not invent new ones. Each category
maps to a specific finding type the math layer knows how to score.

{categories_text}

═══ STRENGTH TIERS ═══

{tiers_text}

{_SHARED_HARD_RULES}

═══ SUBJECT ═══

{subject_label}

═══ FACTS YOU CAN READ ═══

{facts_context}

{_OUTPUT_SCHEMA}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Claude call + response parsing
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_graded_signals(raw: object) -> list[GradedSignal]:
    """Coerce the grader's JSON response into a list of GradedSignal records.

    Defensive: drops malformed entries, never raises on shape mismatch.
    """
    if not isinstance(raw, list):
        log.warning("rubric_grader: grader response was not a list — dropping all signals")
        return []

    out: list[GradedSignal] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        signal_category = str(entry.get("signal_category") or "").strip()
        strength = str(entry.get("strength") or "").strip().lower()
        if not signal_category or not strength:
            continue
        out.append(GradedSignal(
            signal_category=signal_category,
            strength=strength,
            evidence_text=str(entry.get("evidence_text") or "").strip(),
            confidence=str(entry.get("confidence") or "").strip().lower(),
            color=str(entry.get("color") or "").strip().lower(),
            source_fact_path=str(entry.get("source_fact_path") or "").strip(),
        ))
    return out


def grade_dimension(
    dimension: cfg.Dimension,
    facts_context: str,
    subject_label: str,
) -> list[GradedSignal]:
    """Run one rubric grader call for the given dimension.

    Imports `_call_claude` locally to avoid circular imports (same pattern
    as researcher.py). On any exception, returns an empty list — grader
    failure must NEVER crash scoring.
    """
    from scorer import _call_claude  # local import to avoid cycle

    if not facts_context or not facts_context.strip():
        # No facts for this dimension — nothing to grade. This is a legitimate
        # result (e.g., Market Demand for a company with no market-demand
        # facts extracted yet). Return empty, let the scorer fall back to
        # baseline-only math.
        return []

    prompt = build_rubric_grader_prompt(dimension, facts_context, subject_label)

    try:
        raw = _call_claude(
            "You are a truth-only rubric grader. Follow the instructions exactly.",
            prompt,
            max_tokens=2000,
        )
    except Exception as e:
        log.warning(
            "rubric_grader: Claude call failed for %s / %s: %s",
            dimension.name, subject_label, e,
        )
        return []

    return _parse_graded_signals(raw)


# ═══════════════════════════════════════════════════════════════════════════════
# Facts-context serialization
# ═══════════════════════════════════════════════════════════════════════════════

def _json_dumps_dataclass(obj) -> str:
    """Serialize a dataclass to indented JSON. Used to build facts_context."""
    if is_dataclass(obj):
        return json.dumps(asdict(obj), indent=2, default=str, sort_keys=True)
    if isinstance(obj, dict):
        return json.dumps(obj, indent=2, default=str, sort_keys=True)
    return json.dumps(obj, default=str)


def _format_facts_section(label: str, body: str) -> str:
    return f"### {label}\n```json\n{body}\n```"


def _product_context_label(product: Product) -> str:
    parts = [f"Product: {product.name}"]
    if product.category:
        parts.append(f"Category: {product.category}")
    if product.subcategory:
        parts.append(f"Subcategory: {product.subcategory}")
    return " | ".join(parts)


def _product_shape_context(product: Product) -> str:
    """A compact description + Pillar 1 facts section that every Pillar 2
    grader can read as cross-pillar context.

    Frank 2026-04-08: the Pillar 2 fact extractor sometimes comes back
    empty (intermittent Claude call failure or thin research for a
    specific product) and when that happens, Mastery Stakes / Lab
    Versatility / Market Demand have nothing to grade from their own
    dimension facts. Providing the product description + Pillar 1
    capability-store facts gives the grader a reliable floor of
    evidence — the grader still honors TRUTH ONLY (no invention) but
    can tier signals from the cross-pillar facts when the per-dimension
    facts are empty. Same pattern Product Complexity already uses.
    """
    pl = product.product_labability_facts
    prov = getattr(pl, "provisioning", None)
    la = getattr(pl, "lab_access", None)
    sc = getattr(pl, "scoring", None)
    td = getattr(pl, "teardown", None)

    lines = [f"**Product description:** {product.description or '(not provided)'}"]
    if prov is not None:
        lines.append(
            _format_facts_section(
                "Cross-pillar read: Pillar 1 Provisioning facts",
                _json_dumps_dataclass({
                    "description": getattr(prov, "description", ""),
                    "runs_as_installable": getattr(prov, "runs_as_installable", False),
                    "runs_as_azure_native": getattr(prov, "runs_as_azure_native", False),
                    "runs_as_aws_native": getattr(prov, "runs_as_aws_native", False),
                    "runs_as_container": getattr(prov, "runs_as_container", False),
                    "runs_as_saas_only": getattr(prov, "runs_as_saas_only", False),
                    "has_sandbox_api": getattr(prov, "has_sandbox_api", False),
                    "sandbox_api_granularity": getattr(prov, "sandbox_api_granularity", ""),
                    "is_multi_vm_lab": getattr(prov, "is_multi_vm_lab", False),
                    "has_complex_topology": getattr(prov, "has_complex_topology", False),
                    "is_large_lab": getattr(prov, "is_large_lab", False),
                    "needs_gpu": getattr(prov, "needs_gpu", False),
                    "m365_scenario": getattr(prov, "m365_scenario", ""),
                    "supported_host_os": getattr(prov, "supported_host_os", []),
                    "vm_is_resource_intensive": getattr(prov, "vm_is_resource_intensive", False),
                    "vm_has_premium_cost_profile": getattr(prov, "vm_has_premium_cost_profile", False),
                }),
            )
        )
    if la is not None:
        lines.append(
            _format_facts_section(
                "Cross-pillar read: Pillar 1 Lab Access facts",
                _json_dumps_dataclass({
                    "auth_model": getattr(la, "auth_model", ""),
                    "has_identity_api": getattr(la, "has_identity_api", False),
                    "training_license": getattr(la, "training_license", ""),
                    "has_mfa_required": getattr(la, "has_mfa_required", False),
                    "has_rate_limits": getattr(la, "has_rate_limits", False),
                    "has_anti_automation": getattr(la, "has_anti_automation", False),
                }),
            )
        )
    if sc is not None:
        lines.append(
            _format_facts_section(
                "Cross-pillar read: Pillar 1 Scoring facts",
                _json_dumps_dataclass({
                    "has_scoring_api": getattr(sc, "has_scoring_api", False),
                    "scoring_api_granularity": getattr(sc, "scoring_api_granularity", ""),
                    "script_scoring_viable": getattr(sc, "script_scoring_viable", False),
                    "ai_vision_viable": getattr(sc, "ai_vision_viable", False),
                }),
            )
        )
    if td is not None:
        lines.append(
            _format_facts_section(
                "Cross-pillar read: Pillar 1 Teardown facts",
                _json_dumps_dataclass({
                    "vendor_teardown_api": getattr(td, "vendor_teardown_api", False),
                    "vendor_teardown_api_granularity": getattr(td, "vendor_teardown_api_granularity", ""),
                }),
            )
        )
    return "\n\n".join(lines)


def _company_context_label(company: CompanyAnalysis) -> str:
    parts = [f"Company: {company.company_name}"]
    if company.organization_type:
        parts.append(f"Org type: {company.organization_type}")
    return " | ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar 2 — Instructional Value (per-product graders)
# ═══════════════════════════════════════════════════════════════════════════════

def grade_product_complexity(product: Product, company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Product Complexity signals for one product.

    Reads the ProductComplexityFacts drawer plus cross-reads from
    Pillar 1 ProvisioningFacts (multi-VM architecture signals fire in
    both pillars per the CROSS_PILLAR_RULES pattern).
    """
    iv_facts = product.instructional_value_facts
    pl_facts = product.product_labability_facts
    facts_context = "\n\n".join([
        _format_facts_section(
            "Product Complexity facts (primary)",
            _json_dumps_dataclass(iv_facts.product_complexity),
        ),
        _format_facts_section(
            "Cross-pillar read: Pillar 1 Provisioning (multi_vm, complex_topology, large_lab)",
            _json_dumps_dataclass({
                "is_multi_vm_lab": pl_facts.provisioning.is_multi_vm_lab,
                "has_complex_topology": pl_facts.provisioning.has_complex_topology,
                "is_large_lab": pl_facts.provisioning.is_large_lab,
                "supported_host_os": pl_facts.provisioning.supported_host_os,
                "description": pl_facts.provisioning.description,
            }),
        ),
    ])
    return grade_dimension(
        _PRODUCT_COMPLEXITY_DIM,
        facts_context,
        _product_context_label(product),
    )


def grade_mastery_stakes(product: Product, company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Mastery Stakes signals for one product.

    Reads the MasteryStakesFacts drawer plus cross-reads product
    description + Pillar 1 capability facts so the grader has a
    reliable evidence floor when the Pillar 2 fact extractor comes
    back empty for this product (intermittent — see Trellix
    Endpoint Security 2026-04-08). Still honors TRUTH ONLY: the
    grader will only emit signals whose evidence is visible in
    the context, including the cross-pillar context.
    """
    iv_facts = product.instructional_value_facts
    facts_context = "\n\n".join([
        _format_facts_section(
            "Mastery Stakes facts (primary)",
            _json_dumps_dataclass(iv_facts.mastery_stakes),
        ),
        _product_shape_context(product),
    ])
    return grade_dimension(
        _MASTERY_STAKES_DIM,
        facts_context,
        _product_context_label(product),
    )


def grade_lab_versatility(product: Product, company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Lab Versatility signals for one product.

    Reads the LabVersatilityFacts drawer plus cross-reads product
    description + Pillar 1 capability facts. Lab versatility is
    particularly well-served by Pillar 1 cross-reads: a product with
    Multi-VM + Complex Topology naturally supports Adversarial
    Scenario, Cyber Range, and Incident Response lab types; a
    container-native product supports Team Handoff and Break/Fix.
    """
    iv_facts = product.instructional_value_facts
    facts_context = "\n\n".join([
        _format_facts_section(
            "Lab Versatility facts (primary)",
            _json_dumps_dataclass(iv_facts.lab_versatility),
        ),
        _product_shape_context(product),
    ])
    return grade_dimension(
        _LAB_VERSATILITY_DIM,
        facts_context,
        _product_context_label(product),
    )


def grade_market_demand(product: Product, company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Market Demand signals for one product.

    CRITICAL DESIGN RULE (Frank 2026-04-16): Market Demand is PER-PRODUCT,
    not per-company. Company-level signals (HPE has an ATP program, HPE
    has F500 customers, HPE is global) cannot anchor a 'strong' tier on
    any single product — otherwise every product in a strong-company
    portfolio inherits the same 20/20 score (HPE OneView, Aruba Central,
    SimpliVity all landed at 20/20 Market Demand because the grader read
    company-level facts as strong evidence for every product).

    The grader receives two sections:
      - PRIMARY (product-specific facts) — drives the tier directly
      - COMPANY CONTEXT (informational only) — can reinforce a product-
        specific finding but cannot, on its own, justify a strong rating

    The prompt explicitly instructs the grader: "signals found only in
    COMPANY CONTEXT and not corroborated by PRODUCT-SPECIFIC evidence
    are at most 'moderate' or 'informational' — never 'strong'."
    """
    iv_facts = product.instructional_value_facts
    cf_facts = company.customer_fit_facts
    facts_context = "\n\n".join([
        _format_facts_section(
            "PRIMARY — Market Demand facts for THIS PRODUCT (drive the tier)",
            _json_dumps_dataclass(iv_facts.market_demand),
        ),
        _product_shape_context(product),
        _format_facts_section(
            "COMPANY CONTEXT — informational only; cannot alone justify 'strong' tier",
            _json_dumps_dataclass({
                "_note": (
                    "These are company-level signals shared across ALL products "
                    "in this portfolio. They MUST NOT drive a strong Market Demand "
                    "tier on this product unless corroborated by product-specific "
                    "evidence in the PRIMARY section above. Otherwise every "
                    "product in a strong-company portfolio would inherit the same "
                    "Market Demand score, which is the bug we're preventing."
                ),
                "channel_partners_size": asdict(cf_facts.channel_partners_size),
                "channel_partner_se_population": asdict(cf_facts.channel_partner_se_population),
                "named_channel_partners": cf_facts.named_channel_partners,
                "enterprise_reference_customers": cf_facts.enterprise_reference_customers,
                "geographic_reach_regions": cf_facts.geographic_reach_regions,
                "authorized_training_program_name": cf_facts.delivery_capacity.authorized_training_program_name,
                "authorized_training_partners_count": asdict(cf_facts.delivery_capacity.authorized_training_partners_count),
                "named_authorized_training_partners": cf_facts.delivery_capacity.named_authorized_training_partners,
            }),
        ),
    ])
    return grade_dimension(
        _MARKET_DEMAND_DIM,
        facts_context,
        _product_context_label(product),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar 3 — Customer Fit (per-company graders)
# ═══════════════════════════════════════════════════════════════════════════════

def grade_training_commitment(company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Training Commitment signals for one company."""
    cf_facts = company.customer_fit_facts
    facts_context = _format_facts_section(
        "Training Commitment facts",
        _json_dumps_dataclass(cf_facts.training_commitment),
    )
    return grade_dimension(
        _TRAINING_COMMITMENT_DIM,
        facts_context,
        _company_context_label(company),
    )


def _aggregate_vendor_published_counts(products: list[Product]) -> dict:
    """Aggregate vendor-published-course counts across all products in a company.

    Cross-pillar helper used by Build Capacity (they built the content)
    and Delivery Capacity (they chose the distribution channel) graders.
    """
    total: dict[str, int] = {}
    any_found = False
    for p in products:
        md = p.instructional_value_facts.market_demand
        # NOTE: the vendor_published_course_counts field is planned but
        # not yet part of MarketDemandFacts. Defensive lookup via
        # attribute access falls back to an empty dict if the field
        # doesn't exist yet, so this grader continues to work during
        # the rebuild window when extractor schema is still in flight.
        counts = getattr(md, "vendor_published_course_counts", None) or {}
        if counts:
            any_found = True
            for platform, n in counts.items():
                total[platform] = total.get(platform, 0) + int(n)
    return {"platforms": total, "any_found": any_found}


def grade_build_capacity(company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Build Capacity signals for one company.

    Cross-reads `vendor_published_on_third_party` from Products (per
    Frank's 2026-04-08 two-credit rule — vendor publishing official
    courses on Coursera/LinkedIn Learning counts as Build AND Delivery).
    Also cross-reads lab_build_platforms_in_use which lives in
    BuildCapacityFacts but is shared with Delivery Capacity in the
    rebuild routing.

    Fix 3 (2026-04-13): injects lab_platform signal so the grader can
    emit a `diy_labs` amber finding when the company operates its own
    lab platform (Qwiklabs, CML, etc.). The capability is real (they
    CAN build), but the DIY platform is amber because the seller is
    pitching against an internal solution.
    """
    cf_facts = company.customer_fit_facts
    vendor_published = _aggregate_vendor_published_counts(company.products)

    # Lab platform signal — detect DIY / competitor / Skillable
    disc = getattr(company, "discovery_data", None) or {}
    lab_platform = (disc.get("company_signals", {}) or {}).get("lab_platform", "")
    lab_platform_context = (
        f"IMPORTANT: This company operates its own lab platform: '{lab_platform}'. "
        f"A DIY lab platform means strong build capability (they CAN build labs) — "
        f"but it is also an amber Risk signal because the seller must pitch against "
        f"an internal solution. Emit `diy_labs` as amber Risk with evidence naming "
        f"the specific platform."
    ) if lab_platform and "no " not in lab_platform.lower() and lab_platform.lower() not in ("none", "greenfield", "no lab platform") else ""

    facts_context = "\n\n".join(filter(None, [
        _format_facts_section(
            "Build Capacity facts (primary)",
            _json_dumps_dataclass(cf_facts.build_capacity),
        ),
        _format_facts_section(
            "Cross-pillar read: vendor-published third-party course counts (aggregated across products)",
            _json_dumps_dataclass(vendor_published),
        ),
        lab_platform_context,
    ]))
    return grade_dimension(
        _BUILD_CAPACITY_DIM,
        facts_context,
        _company_context_label(company),
    )


def grade_delivery_capacity(company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Delivery Capacity signals for one company.

    Cross-reads vendor-published-on-third-party counts (same
    two-credit fact as Build Capacity reads) so the Delivery Capacity
    grader can credit the vendor's chosen distribution channels.
    """
    cf_facts = company.customer_fit_facts
    vendor_published = _aggregate_vendor_published_counts(company.products)
    facts_context = "\n\n".join([
        _format_facts_section(
            "Delivery Capacity facts (primary)",
            _json_dumps_dataclass(cf_facts.delivery_capacity),
        ),
        _format_facts_section(
            "Top-level shared facts (events, geographic reach, channel partners)",
            _json_dumps_dataclass({
                "channel_partners_size": asdict(cf_facts.channel_partners_size),
                "named_channel_partners": cf_facts.named_channel_partners,
                "events_attendance": {k: asdict(v) for k, v in cf_facts.events_attendance.items()},
                "geographic_reach_regions": cf_facts.geographic_reach_regions,
            }),
        ),
        _format_facts_section(
            "Cross-pillar read: vendor-published third-party course counts",
            _json_dumps_dataclass(vendor_published),
        ),
    ])
    return grade_dimension(
        _DELIVERY_CAPACITY_DIM,
        facts_context,
        _company_context_label(company),
    )


def grade_organizational_dna(company: CompanyAnalysis) -> list[GradedSignal]:
    """Grade Organizational DNA signals for one company.

    Fix 3 (2026-04-13): injects lab_platform signal so the grader can
    emit a `build_everything_culture` amber finding when the company
    operates its own lab platform. A company that has already built
    their own version of what Skillable does is less likely to partner.
    """
    cf_facts = company.customer_fit_facts

    # Lab platform signal — detect DIY / competitor as build-everything culture
    disc = getattr(company, "discovery_data", None) or {}
    lab_platform = (disc.get("company_signals", {}) or {}).get("lab_platform", "")
    lab_platform_context = (
        f"IMPORTANT: This company operates its own lab platform: '{lab_platform}'. "
        f"A company that has already built their own lab delivery platform is "
        f"exhibiting `build_everything_culture` — they prefer to build rather "
        f"than partner. Emit `build_everything_culture` as amber Risk with "
        f"evidence naming the specific platform."
    ) if lab_platform and "no " not in lab_platform.lower() and lab_platform.lower() not in ("none", "greenfield", "no lab platform", "skillable") else ""

    facts_context = "\n\n".join(filter(None, [
        _format_facts_section(
            "Organizational DNA facts",
            _json_dumps_dataclass(cf_facts.organizational_dna),
        ),
        lab_platform_context,
    ]))
    return grade_dimension(
        _ORGANIZATIONAL_DNA_DIM,
        facts_context,
        _company_context_label(company),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Parallel orchestrators
# ═══════════════════════════════════════════════════════════════════════════════

def _dim_key(name: str) -> str:
    return name.lower().replace(" ", "_")


_P2_GRADERS = {
    _dim_key(_DIM_PRODUCT_COMPLEXITY): grade_product_complexity,
    _dim_key(_DIM_MASTERY_STAKES): grade_mastery_stakes,
    _dim_key(_DIM_LAB_VERSATILITY): grade_lab_versatility,
    _dim_key(_DIM_MARKET_DEMAND): grade_market_demand,
}

_P3_GRADERS = {
    _dim_key(_DIM_TRAINING_COMMITMENT): grade_training_commitment,
    _dim_key(_DIM_BUILD_CAPACITY): grade_build_capacity,
    _dim_key(_DIM_DELIVERY_CAPACITY): grade_delivery_capacity,
    _dim_key(_DIM_ORGANIZATIONAL_DNA): grade_organizational_dna,
}


def grade_all_for_product(
    product: Product,
    company: CompanyAnalysis,
) -> dict[str, list[GradedSignal]]:
    """Run all 4 Pillar 2 graders in parallel for one product.

    Returns {dim_key: [GradedSignal, ...]} ready to attach to
    Product.rubric_grades.
    """
    results: dict[str, list[GradedSignal]] = {}
    with ThreadPoolExecutor(max_workers=len(_P2_GRADERS)) as executor:
        futures = {
            executor.submit(grader, product, company): key
            for key, grader in _P2_GRADERS.items()
        }
        for future in as_completed(futures, timeout=180):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                log.warning(
                    "rubric_grader: Pillar 2 grader %s failed for %s: %s",
                    key, product.name, e,
                )
                results[key] = []
    return results


def grade_all_for_company(
    company: CompanyAnalysis,
) -> dict[str, list[GradedSignal]]:
    """Run all 4 Pillar 3 graders in parallel for one company.

    Returns {dim_key: [GradedSignal, ...]} ready to attach to
    CompanyAnalysis.customer_fit_rubric_grades.
    """
    results: dict[str, list[GradedSignal]] = {}
    with ThreadPoolExecutor(max_workers=len(_P3_GRADERS)) as executor:
        futures = {
            executor.submit(grader, company): key
            for key, grader in _P3_GRADERS.items()
        }
        for future in as_completed(futures, timeout=180):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                log.warning(
                    "rubric_grader: Pillar 3 grader %s failed for %s: %s",
                    key, company.company_name, e,
                )
                results[key] = []
    return results
