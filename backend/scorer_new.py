"""Scoring engine for the Skillable Intelligence Platform.

Uses the Prompt Generation System (scoring_config → scoring_template → generated prompt)
instead of a static prompt file. Parses AI output into the new three-pillar data model.

Infrastructure (API calls, retries, parallel scoring, context building) is proven
from the proof-of-concept. Parsing and prompt loading are rebuilt for the new framework.
"""

from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from config_new import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from models_new import (
    ACVPotential, Badge, CompanyAnalysis, ConsumptionMotion, Contact,
    DimensionScore, Evidence, FitScore, OrgUnit, PillarScore, Product,
    ProspectorRow, SellerBriefcase, BriefcaseSection, Verdict,
)
from prompt_generator import generate_scoring_prompt

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Calibration benchmarks
# ═══════════════════════════════════════════════════════════════════════════════

_BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), "benchmarks_new.json")
with open(_BENCHMARKS_PATH, "r", encoding="utf-8") as _f:
    CUSTOMER_BENCHMARKS = json.load(_f)

# ═══════════════════════════════════════════════════════════════════════════════
# Discovery prompt (Phase 1 — fast product identification)
# ═══════════════════════════════════════════════════════════════════════════════

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
_DISCOVERY_PROMPT_PATH = os.path.join(_PROMPTS_DIR, "discovery_new.txt")
with open(_DISCOVERY_PROMPT_PATH, "r", encoding="utf-8") as _f:
    DISCOVERY_PROMPT = _f.read()

# ═══════════════════════════════════════════════════════════════════════════════
# Scoring prompt — generated at runtime from config + template (Define-Once)
# ═══════════════════════════════════════════════════════════════════════════════

SCORING_PROMPT = generate_scoring_prompt()
log.info("Scoring prompt generated: %d characters", len(SCORING_PROMPT))


# ═══════════════════════════════════════════════════════════════════════════════
# Claude API — proven infrastructure
# ═══════════════════════════════════════════════════════════════════════════════

def _call_claude(system_prompt: str, user_content: str, max_tokens: int = 4000) -> dict:
    """Call Claude and parse JSON response. Retries on rate limit with exponential backoff."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    last_exc = None
    for attempt in range(4):
        if attempt > 0:
            wait = 15 * (2 ** (attempt - 1))
            log.warning("Rate limit — retrying in %ss (attempt %d/4)", wait, attempt + 1)
            time.sleep(wait)
        try:
            with client.messages.stream(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            ) as stream:
                message = stream.get_final_message()
            text = message.content[0].text
            if message.stop_reason == "max_tokens":
                raise ValueError(
                    "Analysis too large for one pass. Select fewer products (3-5 recommended)."
                )
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                text = text.rsplit("```json", 1)[1].split("```")[0]
            elif "```" in text:
                text = text.rsplit("```", 2)[-2] if text.count("```") >= 2 else text
            return json.loads(text.strip())
        except anthropic.RateLimitError as e:
            last_exc = e
            continue
        except anthropic.APIStatusError as e:
            if e.status_code == 529:
                last_exc = e
                continue
            if e.status_code == 400 and "credit balance" in str(e).lower():
                raise ValueError(
                    "API credits need refreshing — please let your admin know."
                )
            raise
    raise last_exc


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: Product Discovery
# ═══════════════════════════════════════════════════════════════════════════════

def discover_products_with_claude(findings: dict) -> dict:
    """Phase 1: Product discovery — passes research signals to Claude."""
    def _good(results: list) -> list:
        return [r for r in results if r.get("title", "") not in ("Search error", "Error")
                and not r.get("snippet", "").startswith("[Error")]

    lines = [f"# Company: {findings['company_name']}\n"]

    lines.append("## Product Search Results")
    for r in _good(findings.get("product_discovery", [])):
        lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    lines.append("\n## Training & Certification Programs")
    for r in _good(findings.get("training_programs", []) + findings.get("atp_signals", []) + findings.get("training_catalog", []))[:8]:
        lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    lines.append("\n## Partner Program & Ecosystem")
    for r in _good(findings.get("partner_ecosystem", []) + findings.get("partner_portal", []))[:5]:
        lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    if findings.get("known_products"):
        lines.append(f"\n## Known Products (user-provided): {', '.join(findings['known_products'])}")

    page_contents = findings.get("page_contents", {})
    if page_contents:
        lines.append("\n## Fetched Page Content")
        for key, content in page_contents.items():
            lines.append(f"\n### {key}:")
            lines.append(content[:2000])

    return _call_claude(DISCOVERY_PROMPT, "\n".join(lines), max_tokens=8000)


# ═══════════════════════════════════════════════════════════════════════════════
# Context builders — proven infrastructure
# ═══════════════════════════════════════════════════════════════════════════════

def _build_benchmarks_text() -> str:
    """Build calibration benchmarks text for scoring calls."""
    lines = ["\n## Scoring Calibration: Known Skillable Customers",
             "Use these benchmarks to calibrate scores. Do not copy — use to ensure consistency."]
    for b in CUSTOMER_BENCHMARKS:
        lines.append(f"\n### {b['company']} ({b['relationship']})")
        if "products_and_paths" in b:
            lines.append(f"Products and paths: {'; '.join(b['products_and_paths'])}")
        if "expansion_arc" in b:
            lines.append("Customer expansion arc:")
            for phase in b["expansion_arc"]:
                lines.append(f"  - {phase}")
        for dim, desc in b.get("key_signals", {}).items():
            lines.append(f"- **{dim}**: {desc}")
        if b.get("warning"):
            lines.append(f"WARNING: {b['warning']}")
        lines.append(f"**Scoring guidance**: {b['score_guidance']}")
    return "\n".join(lines)


def _build_company_context(company_name: str, discovery_data: dict | None = None) -> str:
    """Build company-level context for scoring."""
    def _good(results: list) -> list:
        return [r for r in results if r.get("title", "") not in ("Search error", "Error")
                and r.get("snippet", "").strip()
                and not r.get("snippet", "").startswith("[Error")]

    lines = [f"# Company: {company_name}\n"]
    if not discovery_data:
        return "\n".join(lines)

    disc = discovery_data
    disc_pages = disc.get("page_contents", {})

    if disc.get("company_description"):
        lines.append(f"**Company description:** {disc['company_description']}")
    if disc.get("company_url"):
        lines.append(f"**Company URL:** {disc['company_url']}")

    if "company_homepage" in disc_pages:
        lines.append("\n## Company Homepage")
        lines.append(disc_pages["company_homepage"])

    for key in ["product_page_0", "product_page_1"]:
        if key in disc_pages:
            lines.append(f"\n## {key.replace('_', ' ').title()}")
            lines.append(disc_pages[key])

    training = _good(disc.get("training_programs", []) + disc.get("atp_signals", []) + disc.get("training_catalog", []))
    if training:
        lines.append("## Training & Certification Programs")
        for r in training:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    for key in ["training_page", "atp_page"]:
        if key in disc_pages:
            lines.append(f"\n## {key.replace('_page','').title()} Page")
            lines.append(disc_pages[key])

    partners = _good(disc.get("partner_ecosystem", []) + disc.get("partner_portal", []))
    if partners:
        lines.append("\n## Partner Program & Ecosystem")
        for r in partners:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    cs_lms = _good(disc.get("cs_signals", []) + disc.get("lms_signals", []))
    if cs_lms:
        lines.append("\n## Customer Success & LMS Signals")
        for r in cs_lms:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    lab_platforms = _good(disc.get("lab_platform_signals", []))
    if lab_platforms:
        lines.append("\n## Lab Platform Signals (Skillable / Competitors)")
        for r in lab_platforms:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    org = _good(disc.get("org_contacts", []))
    if org:
        lines.append("\n## Training & Enablement Leadership Contacts")
        for r in org:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    return "\n".join(lines)


def _build_product_context(name: str, all_results: dict, page_contents: dict) -> str:
    """Build per-product research context string."""
    lines = [f"## Research: {name}"]

    core_keys = [
        f"tech_{name}", f"train_{name}", f"api_{name}", f"ai_{name}",
        f"marketplace_{name}", f"docker_{name}", f"nfr_{name}", f"deploy_{name}", f"compete_{name}",
    ]
    for key in core_keys:
        for r in all_results.get(key, []):
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    api_lifecycle_keys = [
        f"openapi_{name}", f"api_lifecycle_{name}", f"sandbox_{name}", f"api_auth_{name}",
    ]
    api_lines = []
    for key in api_lifecycle_keys:
        for r in all_results.get(key, []):
            api_lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    if api_lines:
        lines.append(f"\n### API Lifecycle & SaaS Path Signals for {name}:")
        lines.extend(api_lines)

    page_key_labels = [
        (name, "Documentation"),
        (f"train_{name}", "Training"),
        (f"api_{name}", "API Reference"),
        (f"openapi_{name}", "OpenAPI / Swagger Spec"),
        (f"api_lifecycle_{name}", "API Lifecycle Docs"),
    ]
    for key, label in page_key_labels:
        if key in page_contents:
            lines.append(f"\n### {label} page for {name}:")
            lines.append(page_contents[key])

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: Scoring — uses generated prompt, parses into new model
# ═══════════════════════════════════════════════════════════════════════════════

def _score_single_product(company_name: str, product: dict, product_context: str,
                          company_context: str, benchmarks_text: str) -> dict:
    """Score one product via Claude. Returns raw dict from AI."""
    user_content = "\n".join([
        f"# Score this product for: {company_name}",
        f"Product: {product.get('name', '')}",
        product_context,
        company_context,
        benchmarks_text,
    ])
    return _call_claude(SCORING_PROMPT, user_content, max_tokens=7500)


def score_selected_products(research: dict) -> CompanyAnalysis:
    """Phase 2: Parallel scoring — one Claude call per product."""
    company_name = research["company_name"]
    selected = research["selected_products"]
    all_results = research.get("search_results", {})
    page_contents = research.get("page_contents", {})

    discovery_data = research.get("discovery_data")
    company_context = _build_company_context(company_name, discovery_data)
    benchmarks_text = _build_benchmarks_text()

    # Fire one call per product in parallel — cap at 6 workers
    from config_new import MAX_SCORING_WORKERS, SCORING_TIMEOUT_SECS
    with ThreadPoolExecutor(max_workers=min(len(selected), MAX_SCORING_WORKERS)) as executor:
        product_futures = {
            executor.submit(
                _score_single_product,
                company_name, p,
                _build_product_context(p["name"], all_results, page_contents),
                company_context, benchmarks_text
            ): p["name"]
            for p in selected
        }

        product_results = {}
        for future in as_completed(product_futures, timeout=SCORING_TIMEOUT_SECS):
            name = product_futures[future]
            try:
                product_results[name] = future.result()
            except Exception as e:
                product_results[name] = {"_error": str(e)}

    failed = {name: r for name, r in product_results.items() if "_error" in r}
    successful = {name: r for name, r in product_results.items() if "_error" not in r}
    for name, r in failed.items():
        log.error("Scoring failed for '%s': %s", name, r["_error"])

    if not successful:
        raise ValueError(
            "Scoring failed for all products — usually a temporary API issue. "
            "Try again in a moment, or select fewer products."
        )

    first = next(iter(successful.values()))
    products = []
    for p in selected:
        result = product_results.get(p["name"], {})
        if "_error" in result:
            continue
        products.append(_parse_product(result))

    return CompanyAnalysis(
        company_name=company_name,
        company_url=first.get("company_url"),
        company_description=first.get("company_description", ""),
        organization_type=first.get("organization_type", "software_company"),
        products=products,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Parsing — AI output → new data model
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_evidence(raw: dict) -> Evidence:
    """Parse a single evidence item from AI output."""
    return Evidence(
        claim=raw.get("claim", ""),
        confidence_level=raw.get("confidence", "inferred"),
        confidence_explanation=raw.get("confidence_explanation", ""),
        source_url=raw.get("source_url"),
        source_title=raw.get("source_title"),
    )


def _parse_badges_for_dimension(dim_name: str, evidence_dict: dict) -> list[Badge]:
    """Parse badges from the evidence section for a specific dimension."""
    key = dim_name.lower().replace(" ", "_")
    raw_items = evidence_dict.get(key, [])
    badges = []
    for item in raw_items:
        badge = Badge(
            name=item.get("badge", ""),
            color=item.get("color", "gray"),
            qualifier=item.get("qualifier", ""),
            evidence=[_parse_evidence(item)],
        )
        badges.append(badge)
    return badges


def _parse_pillar(pillar_name: str, pillar_data: dict, evidence_dict: dict) -> PillarScore:
    """Parse a Pillar from AI output into PillarScore."""
    dims_data = pillar_data.get("dimensions", {})
    weight = pillar_data.get("weight", 0)

    # Map dimension names to their config weights
    dim_weights = {
        # Product Labability
        "provisioning": 35, "lab_access": 25, "scoring": 15, "teardown": 25,
        # Instructional Value
        "product_complexity": 40, "mastery_stakes": 25, "lab_versatility": 15, "market_demand": 20,
        # Customer Fit
        "training_commitment": 25, "organizational_dna": 25, "delivery_capacity": 30, "build_capacity": 20,
    }

    dimensions = []
    for dim_key, dim_data in dims_data.items():
        display_name = dim_key.replace("_", " ").title()
        dimensions.append(DimensionScore(
            name=display_name,
            score=min(dim_data.get("score", 0), dim_weights.get(dim_key, 100)),
            weight=dim_weights.get(dim_key, 0),
            summary=dim_data.get("summary", ""),
            badges=_parse_badges_for_dimension(display_name, evidence_dict),
        ))

    return PillarScore(
        name=pillar_name,
        weight=weight,
        dimensions=dimensions,
    )


def _parse_consumption(raw: dict) -> ACVPotential:
    """Parse consumption potential from AI output."""
    motions = [
        ConsumptionMotion(
            label=m.get("label", ""),
            population_low=int(m.get("population_low", 0)),
            population_high=int(m.get("population_high", 0)),
            hours_low=float(m.get("hours_low", 0)),
            hours_high=float(m.get("hours_high", 0)),
            adoption_pct=float(m.get("adoption_pct", 0)),
            rationale=m.get("rationale", ""),
        )
        for m in raw.get("motions", [])
    ]
    # Recompute — don't trust Claude's arithmetic
    computed_low = round(sum(
        m.population_low * m.hours_low * m.adoption_pct for m in motions
    ))
    computed_high = round(sum(
        m.population_high * m.hours_high * m.adoption_pct for m in motions
    ))
    return ACVPotential(
        motions=motions,
        annual_hours_low=computed_low,
        annual_hours_high=computed_high,
        acv_low=float(raw.get("total_acv_low", 0)),
        acv_high=float(raw.get("total_acv_high", 0)),
        acv_tier=raw.get("acv_tier", ""),
        methodology_note=raw.get("methodology_note", ""),
    )


def _parse_verdict(raw: dict) -> Verdict:
    """Parse verdict from AI output."""
    return Verdict(
        label=raw.get("label", ""),
        color=raw.get("color", ""),
    )


def _parse_product(data: dict) -> Product:
    """Parse a complete product from AI scoring output into the new model."""
    pillar_scores = data.get("pillar_scores", {})
    evidence_dict = data.get("evidence", {})

    # Parse the three Pillars
    fit = FitScore()
    for pillar_name, pillar_data in pillar_scores.items():
        parsed = _parse_pillar(pillar_name, pillar_data, evidence_dict)
        if "Labability" in pillar_name:
            fit.product_labability = parsed
        elif "Instructional" in pillar_name:
            fit.instructional_value = parsed
        elif "Customer" in pillar_name:
            fit.customer_fit = parsed

    # Contacts
    contacts_raw = data.get("contacts", {})
    contacts = []
    for role_type in ["decision_maker", "influencer"]:
        c = contacts_raw.get(role_type, {})
        if c.get("name"):
            contacts.append(Contact(
                name=c["name"],
                title=c.get("title", ""),
                role_type=role_type,
                linkedin_url=c.get("linkedin_url"),
                relevance=c.get("relevance", ""),
            ))

    # Owning org
    owning_org = None
    if data.get("owning_org"):
        o = data["owning_org"]
        owning_org = OrgUnit(
            name=o.get("name", ""),
            type=o.get("type", "department"),
            description=o.get("description", ""),
        )

    # Consumption potential
    cp_raw = data.get("consumption_potential", {})

    # Verdict
    verdict_raw = data.get("verdict", {})

    return Product(
        name=data.get("product_name", data.get("name", "Unknown")),
        category=data.get("product_category", data.get("category", "")),
        subcategory=data.get("product_subcategory", data.get("subcategory", "")),
        description=data.get("description", ""),
        product_url=data.get("product_url", ""),
        deployment_model=data.get("deployment_model", ""),
        orchestration_method=data.get("orchestration_method", ""),
        user_personas=data.get("user_personas", []),
        lab_highlight=data.get("lab_highlight", ""),
        lab_concepts=[
            lc.get("title", "") if isinstance(lc, dict) else str(lc)
            for lc in data.get("lab_concepts", [])
        ],
        poor_match_flags=data.get("poor_match_flags", []),
        recommendation=[
            r.get("text", "") if isinstance(r, dict) else str(r)
            for r in data.get("recommendations", [])
        ],
        fit_score=fit,
        acv_potential=_parse_consumption(cp_raw) if cp_raw else ACVPotential(),
        verdict=_parse_verdict(verdict_raw) if verdict_raw else None,
        owning_org=owning_org,
        contacts=contacts,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Seller Briefcase — separate AI call after scoring (GP3)
# ═══════════════════════════════════════════════════════════════════════════════

_BRIEFCASE_SYSTEM_PROMPT = """You are a sales enablement expert for Skillable, a hands-on lab platform.
You are given complete scoring results for a product. Generate three briefcase sections
that arm the seller for conversations. Be sharp, specific, and actionable.

Output JSON with this structure:
{
  "key_technical_questions": {
    "bullets": ["Who to find, what department, what to ask, why it matters"]
  },
  "conversation_starters": {
    "bullets": ["Product-specific talking points about why hands-on training matters"]
  },
  "account_intelligence": {
    "bullets": ["Organizational signals, training leadership, competitive intel, news"]
  }
}

Rules:
- Each section: 2-3 bullets maximum
- Every bullet is specific to THIS company and THIS product — never generic
- Key Technical Questions: include a verbatim question the champion can send
- Conversation Starters: make the seller credible without being technical
- Account Intelligence: show the seller has done their homework
"""


def generate_briefcase(product: Product, company_context: str) -> SellerBriefcase:
    """Generate Seller Briefcase from complete scoring results.

    Separate AI call — receives full scoring context for sharper output.
    """
    # Build context from the scored product
    scoring_summary = json.dumps({
        "product": product.name,
        "fit_score": product.fit_score.total,
        "product_labability": product.fit_score.product_labability.score,
        "instructional_value": product.fit_score.instructional_value.score,
        "customer_fit": product.fit_score.customer_fit.score,
        "deployment_model": product.deployment_model,
        "orchestration_method": product.orchestration_method,
        "verdict": product.verdict.label if product.verdict else "",
        "contacts": [{"name": c.name, "title": c.title, "role_type": c.role_type}
                     for c in product.contacts],
    }, indent=2)

    user_content = f"# Generate Seller Briefcase\n\n## Scoring Results\n{scoring_summary}\n\n{company_context}"

    try:
        result = _call_claude(_BRIEFCASE_SYSTEM_PROMPT, user_content, max_tokens=2000)
    except Exception as e:
        log.error("Briefcase generation failed: %s", e)
        return SellerBriefcase()

    return SellerBriefcase(
        key_technical_questions=BriefcaseSection(
            pillar="Product Labability",
            heading="Key Technical Questions",
            bullets=result.get("key_technical_questions", {}).get("bullets", []),
        ),
        conversation_starters=BriefcaseSection(
            pillar="Instructional Value",
            heading="Conversation Starters",
            bullets=result.get("conversation_starters", {}).get("bullets", []),
        ),
        account_intelligence=BriefcaseSection(
            pillar="Customer Fit",
            heading="Account Intelligence",
            bullets=result.get("account_intelligence", {}).get("bullets", []),
        ),
    )
