"""Claude API-powered scoring engine for labability analysis."""

import json
import logging
import os
import time
import anthropic

log = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import (
    CompanyAnalysis, Product, ProductLababilityScore,
    DimensionScore, Evidence, Contact, OrgUnit,
    ConsumptionMotion, ConsumptionPotential,
)
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

# ---------------------------------------------------------------------------
# Calibration benchmarks — loaded from benchmarks.json
# Edit benchmarks.json to add/update/remove company benchmarks.
# ---------------------------------------------------------------------------

_BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), "benchmarks.json")
with open(_BENCHMARKS_PATH, "r", encoding="utf-8") as _f:
    CUSTOMER_BENCHMARKS = json.load(_f)

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

# ---------------------------------------------------------------------------
# Phase 1: Fast product discovery
# ---------------------------------------------------------------------------

__DISCOVERY_PROMPT_PATH = os.path.join(_PROMPTS_DIR, "discovery.txt")
with open(__DISCOVERY_PROMPT_PATH, "r", encoding="utf-8") as _f:
    DISCOVERY_PROMPT = _f.read()

# ---------------------------------------------------------------------------
# Product scoring prompt
# ---------------------------------------------------------------------------

__PRODUCT_SCORING_PROMPT_PATH = os.path.join(_PROMPTS_DIR, "product_scoring.txt")
with open(__PRODUCT_SCORING_PROMPT_PATH, "r", encoding="utf-8") as _f:
    PRODUCT_SCORING_PROMPT = _f.read()


def _call_claude(system_prompt: str, user_content: str, max_tokens: int = 4000) -> dict:
    """Call Claude and parse JSON response. Retries on rate limit errors with exponential backoff."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    last_exc = None
    for attempt in range(4):
        if attempt > 0:
            wait = 15 * (2 ** (attempt - 1))  # 15s, 30s, 60s
            log.warning("Rate limit hit — retrying in %ss (attempt %d/4)", wait, attempt + 1)
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
            stop_reason = message.stop_reason
            if "```json" in text:
                # Use the LAST ```json block in case Claude prefaces with explanation
                text = text.rsplit("```json", 1)[1].split("```")[0]
            elif "```" in text:
                text = text.rsplit("```", 2)[-2] if text.count("```") >= 2 else text
            text = text.strip()
            if stop_reason == "max_tokens":
                raise ValueError(
                    "The analysis was too large to complete in one pass. "
                    "Please go back and select fewer products (3-5 recommended), then try again."
                )
            return json.loads(text)
        except anthropic.RateLimitError as e:
            last_exc = e
            continue
        except anthropic.APIStatusError as e:
            if e.status_code == 529:  # Anthropic overloaded
                last_exc = e
                continue
            if e.status_code == 400 and "credit balance" in str(e).lower():
                raise ValueError(
                    "You guys are using this tool a ton! Looks like your admin needs to refresh "
                    "your Anthropic API credits — please let them know."
                )
            raise
    raise last_exc


def discover_products_with_claude(findings: dict) -> dict:
    """Phase 1: Product discovery — passes all research signals to Claude for accurate product identification."""
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

    return _call_claude(DISCOVERY_PROMPT, "\n".join(lines), max_tokens=3000)


def _build_benchmarks_text() -> str:
    """Build calibration benchmarks text for product scoring calls."""
    lines = ["\n## Scoring Calibration: Known Skillable Customers",
             "Use these benchmarks to calibrate scores. Do not copy — use to ensure consistency."]
    for b in CUSTOMER_BENCHMARKS:
        lines.append(f"\n### {b['company']} ({b['relationship']})")
        if "products_and_paths" in b:
            lines.append(f"Products and paths: {'; '.join(b['products_and_paths'])}")
        if "expansion_arc" in b:
            lines.append("Customer expansion arc (use this to calibrate consumption motions and partnership trajectory):")
            for phase in b["expansion_arc"]:
                lines.append(f"  - {phase}")
        for dim, desc in b.get("key_signals", {}).items():
            lines.append(f"- **{dim}**: {desc}")
        if b.get("warning"):
            lines.append(f"⚠️ WARNING: {b['warning']}")
        lines.append(f"**Scoring guidance**: {b['score_guidance']}")
    return "\n".join(lines)


def _build_company_context(company_name: str, discovery_data: dict | None = None) -> str:
    """Build company-level context for partnership scoring.

    Discovery data is the PRIMARY source — it's reliably fetched in a small focused batch.
    Phase-2 product research results are not included here (they're product-specific).
    """
    def _good(results: list) -> list:
        return [r for r in results if r.get("title", "") not in ("Search error", "Error")
                and r.get("snippet", "").strip()
                and not r.get("snippet", "").startswith("[Error")]

    lines = [f"# Company: {company_name}\n"]

    if not discovery_data:
        return "\n".join(lines)

    disc = discovery_data
    disc_pages = disc.get("page_contents", {})

    # Company description (from Claude discovery response)
    if disc.get("company_description"):
        lines.append(f"**Company description:** {disc['company_description']}")
    if disc.get("company_url"):
        lines.append(f"**Company URL:** {disc['company_url']}")

    # Company homepage (fetched during discovery)
    if "company_homepage" in disc_pages:
        lines.append("\n## Company Homepage")
        lines.append(disc_pages["company_homepage"])

    # Product pages from discovery (give partnership scorer product context)
    for key in ["product_page_0", "product_page_1"]:
        if key in disc_pages:
            lines.append(f"\n## {key.replace('_', ' ').title()} (from product discovery)")
            lines.append(disc_pages[key])

    # Training & certification (ATP, catalog, programs)
    training = _good(disc.get("training_programs", []) + disc.get("atp_signals", []) + disc.get("training_catalog", []))
    if training:
        lines.append("## Training & Certification Programs")
        for r in training:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    for key in ["training_page", "atp_page"]:
        if key in disc_pages:
            lines.append(f"\n## {key.replace('_page','').title()} Page")
            lines.append(disc_pages[key])

    # Partner program & ecosystem
    partners = _good(disc.get("partner_ecosystem", []) + disc.get("partner_portal", []))
    if partners:
        lines.append("\n## Partner Program & Ecosystem")
        for r in partners:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    if "partner_portal_page" in disc_pages:
        lines.append("\n## Partner Portal Page")
        lines.append(disc_pages["partner_portal_page"])

    # Customer success & LMS
    cs_lms = _good(disc.get("cs_signals", []) + disc.get("lms_signals", []))
    if cs_lms:
        lines.append("\n## Customer Success & LMS Signals")
        for r in cs_lms:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    # Org & contacts
    org = _good(disc.get("org_contacts", []))
    if org:
        lines.append("\n## Training & Enablement Leadership Contacts")
        for r in org:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    return "\n".join(lines)


def _build_product_context(name: str, all_results: dict, page_contents: dict) -> str:
    """Build per-product research context string."""
    lines = [f"## Research: {name}"]
    search_keys = [
        f"tech_{name}", f"train_{name}", f"api_{name}", f"ai_{name}",
        f"marketplace_{name}", f"docker_{name}", f"nfr_{name}", f"deploy_{name}", f"compete_{name}",
    ]
    for key in search_keys:
        for r in all_results.get(key, []):
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    for key in [name, f"train_{name}", f"api_{name}"]:
        if key in page_contents:
            label = "Documentation" if key == name else key.replace(f"_{name}", "").replace("_", " ").title()
            lines.append(f"\n### {label} page for {name}:")
            lines.append(page_contents[key])
    return "\n".join(lines)


def _score_single_product(company_name: str, product: dict, product_context: str,
                           company_context: str, benchmarks_text: str) -> dict:
    """Score one product via Claude. Returns the raw product dict."""
    user_content = "\n".join([
        f"# Score this product for: {company_name}",
        f"Product: {product.get('name', '')}",
        product_context,
        company_context,
        benchmarks_text,
    ])
    data = _call_claude(PRODUCT_SCORING_PROMPT, user_content, max_tokens=7500)
    return data


def score_selected_products(research: dict) -> CompanyAnalysis:
    """Phase 2: Parallel scoring — one Claude call per product."""
    company_name = research["company_name"]
    selected = research["selected_products"]
    all_results = research.get("search_results", {})
    page_contents = research.get("page_contents", {})

    discovery_data = research.get("discovery_data")
    company_context = _build_company_context(company_name, discovery_data)
    benchmarks_text = _build_benchmarks_text()

    # Fire one call per product in parallel
    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        product_futures = {
            executor.submit(
                _score_single_product,
                company_name, p,
                _build_product_context(p["name"], all_results, page_contents),
                company_context, benchmarks_text
            ): p["name"]
            for p in selected
        }

        # Collect product results — 5-minute per-call timeout so a hung Claude call can't block forever
        product_results = {}
        for future in as_completed(product_futures, timeout=300):
            name = product_futures[future]
            try:
                product_results[name] = future.result()
            except Exception as e:
                product_results[name] = {"_error": str(e)}

    # Log any product scoring failures and skip them — don't let errors produce "Unknown" products
    failed = {name: r for name, r in product_results.items() if "_error" in r}
    successful = {name: r for name, r in product_results.items() if "_error" not in r}
    for name, r in failed.items():
        log.error("Product scoring failed for '%s': %s", name, r['_error'])

    if not successful:
        raise ValueError(
            "Scoring failed for all selected products — this is usually a temporary API issue. "
            "Please try again in a moment. If the problem persists, try selecting fewer products."
        )

    # Use first successful result for company-level metadata
    first = next(iter(successful.values()))
    products_list = []
    for p in selected:
        result = product_results.get(p["name"], {})
        if "_error" in result:
            continue  # skip failed products rather than emitting an "Unknown" entry
        product_obj = result.get("product") or result
        products_list.append(product_obj)

    data = {
        "company_description": first.get("company_description", ""),
        "company_url": first.get("company_url", ""),
        "organization_type": first.get("organization_type", "software_company"),
        "products": products_list,
    }
    return _parse_response_to_models(company_name, data)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_consumption(d: dict) -> ConsumptionPotential:
    motions = [
        ConsumptionMotion(
            label=m.get("label", ""),
            population_low=int(m.get("population_low", 0)),
            population_high=int(m.get("population_high", 0)),
            hours_low=float(m.get("hours_low", 0)),
            hours_high=float(m.get("hours_high", 0)),
            adoption_pct=float(m.get("adoption_pct", 0.5)),
            rationale=m.get("rationale", ""),
        )
        for m in d.get("motions", [])
    ]
    # Recompute totals from motion math — don't trust Claude's arithmetic
    computed_low = round(sum(m.population_low * m.hours_low * m.adoption_pct for m in motions))
    computed_high = round(sum(m.population_high * m.hours_high * m.adoption_pct for m in motions))
    return ConsumptionPotential(
        motions=motions,
        annual_hours_low=computed_low,
        annual_hours_high=computed_high,
        vm_rate_estimate=int(d.get("vm_rate_estimate", 0)),
        methodology_note=d.get("methodology_note", ""),
    )


def _parse_dimension(d: dict) -> DimensionScore:
    raw_evidence = d.get("evidence", [])
    if len(raw_evidence) > 5:
        log.warning("Dimension returned %d evidence items — truncating to 5", len(raw_evidence))
        raw_evidence = raw_evidence[:5]
    return DimensionScore(
        score=d.get("score", 0),
        summary=d.get("summary", ""),
        evidence=[
            Evidence(
                claim=e.get("claim", ""),
                source_url=e.get("source_url"),
                source_title=e.get("source_title"),
            )
            for e in raw_evidence
        ],
    )


def _parse_response_to_models(company_name: str, data: dict) -> CompanyAnalysis:
    products = []
    for p in data.get("products", []):
        scores = p.get("scores", {})
        owning_org = None
        if p.get("owning_org"):
            o = p["owning_org"]
            owning_org = OrgUnit(
                name=o.get("name", "Unknown"),
                type=o.get("type", "department"),
                description=o.get("description", ""),
            )
        contacts = [
            Contact(
                name=c.get("name", ""),
                title=c.get("title", ""),
                role_type=c.get("role_type", "influencer"),
                linkedin_url=c.get("linkedin_url"),
                relevance=c.get("relevance", ""),
            )
            for c in p.get("contacts", [])
        ]
        cp_raw = p.get("consumption_potential", {})
        _valid_paths = {"A1", "A1-AWS", "A2", "B", "C", "Unknown"}
        _path = {"A": "A1"}.get(p.get("skillable_path", ""), p.get("skillable_path", "Unknown"))
        if _path not in _valid_paths:
            _path = "Unknown"
        product = Product(
            name=p.get("name", "Unknown"),
            product_url=p.get("product_url", ""),
            category=p.get("category", ""),
            description=p.get("description", ""),
            deployment_model=p.get("deployment_model", "unknown"),
            skillable_path=_path,
            path_tier=p.get("path_tier", "Unknown"),
            skillable_mechanism=p.get("skillable_mechanism", ""),
            fabric=p.get("fabric", ""),
            user_personas=p.get("user_personas", []),
            lab_highlight=p.get("lab_highlight", ""),
            poor_match_flags=p.get("poor_match_flags", []),
            api_scoring_potential=p.get("api_scoring_potential", ""),
            recommendation=p.get("recommendation") if isinstance(p.get("recommendation"), list) else ([p["recommendation"]] if p.get("recommendation") else []),
            labability_score=ProductLababilityScore(
                # Accept both new and legacy key names for backward compat with cached analyses
                product_labability=_parse_dimension(
                    scores.get("product_labability") or scores.get("technical_orchestrability", {})
                ),
                instructional_value=_parse_dimension(
                    scores.get("instructional_value") or scores.get("workflow_complexity", {})
                ),
                organizational_readiness=_parse_dimension(
                    scores.get("organizational_readiness") or scores.get("training_ecosystem", {})
                ),
                market_readiness=_parse_dimension(
                    scores.get("market_readiness") or scores.get("market_fit", {})
                ),
                path=_path,
            ),
            owning_org=owning_org,
            contacts=contacts,
            lab_concepts=p.get("lab_concepts", []),
            consumption_potential=_parse_consumption(cp_raw) if cp_raw else ConsumptionPotential(),
        )
        products.append(product)

    return CompanyAnalysis(
        company_name=company_name,
        company_url=data.get("company_url"),
        company_description=data.get("company_description", ""),
        organization_type=data.get("organization_type", "software_company"),
        products=products,
    )
