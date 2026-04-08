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

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from models import (
    ACVPotential, Badge, CompanyAnalysis, ConsumptionMotion, Contact,
    DimensionScore, Evidence, FitScore, OrgUnit, PillarScore, Product,
    ProspectorRow, SellerBriefcase, BriefcaseSection, Verdict,
)
from prompt_generator import generate_scoring_prompt

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Calibration benchmarks
# ═══════════════════════════════════════════════════════════════════════════════

_BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), "benchmarks.json")
with open(_BENCHMARKS_PATH, "r", encoding="utf-8") as _f:
    CUSTOMER_BENCHMARKS = json.load(_f)

# ═══════════════════════════════════════════════════════════════════════════════
# Discovery prompt (Phase 1 — fast product identification)
# ═══════════════════════════════════════════════════════════════════════════════

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
_DISCOVERY_PROMPT_PATH = os.path.join(_PROMPTS_DIR, "discovery.txt")
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

def _call_claude(system_prompt: str, user_content: str, max_tokens: int = 4000,
                 model_override: str | None = None) -> dict:
    """Call Claude and parse JSON response. Retries on rate limit with exponential backoff.

    model_override: pass a specific model ID (e.g. 'claude-opus-4-6' or
    'claude-haiku-4-5-20251001') to use a different model for this call.
    Defaults to the global ANTHROPIC_MODEL.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    model_to_use = model_override or ANTHROPIC_MODEL
    last_exc = None
    for attempt in range(4):
        if attempt > 0:
            wait = 15 * (2 ** (attempt - 1))
            log.warning("Rate limit — retrying in %ss (attempt %d/4)", wait, attempt + 1)
            time.sleep(wait)
        try:
            call_start = time.time()
            log.info("Claude call starting (model=%s, max_tokens=%d)", model_to_use, max_tokens)
            token_count = 0
            last_heartbeat = call_start
            with client.messages.stream(
                model=model_to_use,
                max_tokens=max_tokens,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            ) as stream:
                # Stream events to track progress and emit heartbeats
                for event in stream:
                    if event.type == "content_block_delta":
                        token_count += 1
                    now = time.time()
                    if now - last_heartbeat >= 60:
                        log.info("Claude call still running — %ds elapsed, ~%d chunks received",
                                 int(now - call_start), token_count)
                        last_heartbeat = now
                message = stream.get_final_message()
            elapsed = time.time() - call_start
            log.info("Claude call complete in %.1fs (%d output tokens)",
                     elapsed, message.usage.output_tokens if message.usage else 0)
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
    """Score one product via Claude. Returns raw dict from AI.

    max_tokens raised from 16000 to 32000 2026-04-07 after Trellix
    Wise + Trellix Endpoint Security hit the 16K ceiling mid-output
    on a 6-product scoring run.  Claude Opus 4.6 supports 32K output
    tokens; giving the full scoring prompt headroom avoids the
    defensive "Analysis too large" raise path when the answer-format
    badge vocabulary + all three pillars produce long JSON.
    """
    user_content = "\n".join([
        f"# Score this product for: {company_name}",
        f"Product: {product.get('name', '')}",
        product_context,
        company_context,
        benchmarks_text,
    ])
    return _call_claude(SCORING_PROMPT, user_content, max_tokens=32000)


def score_selected_products(research: dict, progress_cb=None) -> CompanyAnalysis:
    """Phase 2 stub — REBUILD Step 5b-lite (Frank 2026-04-08).

    The legacy monolithic per-product Claude scoring call is COMMENTED OUT.
    Running both the new Python scorers (Steps 3/4/5) and the monolithic
    call at the same time was producing timeouts and corrupted the Deep
    Dive flow, so Frank directed us to stub the old path so the new one
    can be tested in isolation on Trellix.

    This function now:
      1. Reads company_name, selected products, and discovery metadata
         from the `research` dict
      2. Builds minimal Product objects from selected_products + whatever
         metadata lives in discovery_data (name, category, description,
         subcategory, product_url). No Claude call.
      3. Attaches the Pillar 1 fact drawer from research["product_labability_facts"]
         (populated by the Step 2 fact extractors).
      4. Emits progress events for each product so the UX progress bar
         still moves.
      5. Returns a CompanyAnalysis with empty fit_score placeholders —
         `intelligence.score()` will populate them via the Python scorers
         (Steps 3/4) and the Step 5 cutover flip.

    Full Step 5b (delete the dead legacy code + the badge-keyed math in
    scoring_math.py + the _parse_product / _parse_pillar / _parse_* helpers)
    is still pending. This stub is the minimum viable cutover that lets us
    test the new scoring path end-to-end.

    Lost by the stub vs the old monolithic path:
      - owning_org per product (Claude used to synthesize from research)
      - contacts per product (Claude used to extract from research)
      - lab_highlight, lab_concepts, deployment_model, orchestration_method,
        user_personas, recommendation (all from the monolithic call)
      - description / subcategory / product_url (if not present on the
        selected_products entries)
      - poor_match_flags (Claude-derived ceiling flag hints)

    Most of these become empty strings or empty lists. The UI will render
    with gaps in those areas — acceptable for the rebuild test window.
    A future metadata extractor (a focused small Claude call for metadata
    only) will refill them at Step 5b proper.

    Args:
        research: research dict with company_name, selected_products, etc.
        progress_cb: optional callback invoked as each product is built.
            Signature: progress_cb(product_name: str, completed: int, total: int).
    """
    company_name = research["company_name"]
    selected = research["selected_products"]
    discovery_data = research.get("discovery_data") or {}

    total = len(selected)

    def _emit_progress(name: str, done: int) -> None:
        if progress_cb is None:
            return
        try:
            progress_cb(name, done, total)
        except Exception:
            log.exception("score_selected_products (stub): progress_cb raised — ignoring")

    # Build a lookup of discovery-data products by name so we can grab
    # whatever metadata was emitted at discovery time (category,
    # description, subcategory, product_url).
    discovery_products_by_name: dict[str, dict] = {}
    for dp in discovery_data.get("products", []) or []:
        if isinstance(dp, dict) and dp.get("name"):
            discovery_products_by_name[dp["name"]] = dp

    # Attach the Pillar 1 fact drawer extracted by researcher.research_products().
    # The other fact drawers (InstructionalValueFacts, CustomerFitFacts) are
    # attached by intelligence.score() after this function returns — see the
    # Step 2 wiring there. This keeps `score_selected_products`'s contract
    # narrow: build Products with metadata + Pillar 1 facts, let intelligence.py
    # do the rest.
    facts_by_product = research.get("product_labability_facts", {}) or {}

    products: list[Product] = []
    completed = 0
    for p in selected:
        name = p.get("name", "")
        disc_entry = discovery_products_by_name.get(name, {})

        # Merge: selected_products entry first, discovery_data entry as fallback
        category = p.get("category") or disc_entry.get("category") or ""
        subcategory = p.get("subcategory") or disc_entry.get("subcategory") or ""
        description = p.get("description") or disc_entry.get("description") or ""
        product_url = p.get("product_url") or disc_entry.get("product_url") or ""
        deployment_model = p.get("deployment_model") or disc_entry.get("deployment_model") or ""
        orchestration_method = p.get("orchestration_method") or disc_entry.get("orchestration_method") or ""

        product = Product(
            name=name,
            category=category,
            subcategory=subcategory,
            description=description,
            product_url=product_url,
            deployment_model=deployment_model,
            orchestration_method=orchestration_method,
        )

        facts = facts_by_product.get(name)
        if facts is not None:
            product.product_labability_facts = facts

        products.append(product)
        completed += 1
        _emit_progress(name, completed)

    if not products:
        raise ValueError(
            "score_selected_products (stub): zero products in research['selected_products']"
        )

    log.info(
        "score_selected_products (stub): built %d products from discovery data — "
        "monolithic Claude call SKIPPED (Step 5b-lite). Pillar scoring will be "
        "populated by intelligence.score() via the Python scorers.",
        len(products),
    )

    # Company-level metadata comes from discovery_data.
    return CompanyAnalysis(
        company_name=company_name,
        company_url=discovery_data.get("company_url"),
        company_description=discovery_data.get("company_description", ""),
        organization_type=discovery_data.get("organization_type", "software_company"),
        products=products,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY score_selected_products — DEAD CODE pending Step 5b proper deletion
#
# Kept below (inside this comment block) as a one-place reference of what
# the old monolithic path did, until Step 5b removes both the code and the
# _score_single_product / _parse_product / _parse_* helpers that supported
# it. The old behavior:
#
#   1. Build product_context from search_results + page_contents
#   2. Build company_context from discovery_data
#   3. Build benchmarks_text from benchmarks.json
#   4. Fire one Claude call per product in parallel (SCORING_PROMPT)
#      via _score_single_product
#   5. Parse each response via _parse_product which called
#      scoring_math.compute_all to run badge-keyed math
#   6. Return CompanyAnalysis with fit_score populated from the AI output
#
# All of that is now dead. The new path (Steps 2/3/4/5) reads facts
# directly and computes scores via the pure-Python pillar scorers. The
# rubric grader handles the narrow Claude-in-Score slice for Pillar 2/3.
# ─────────────────────────────────────────────────────────────────────────────


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
    """Parse badges from the evidence section for a specific dimension.

    Carries the rubric fields (strength + signal_category) through onto the
    persisted Badge object so the dossier UX can render them and downstream
    analytics can group by signal_category. For Pillar 1 dimensions both
    fields will be empty strings — that's expected and not an error.
    """
    key = dim_name.lower().replace(" ", "_")
    raw_items = evidence_dict.get(key, [])
    badges = []
    for item in raw_items:
        badge = Badge(
            name=item.get("badge", ""),
            color=item.get("color", "gray"),
            qualifier=item.get("qualifier", ""),
            evidence=[_parse_evidence(item)],
            strength=(item.get("strength") or "").strip().lower(),
            signal_category=(item.get("signal_category") or "").strip(),
        )
        badges.append(badge)
    return badges


def _parse_pillar(pillar_name: str, pillar_data: dict, evidence_dict: dict,
                  computed_dim_scores: dict | None = None) -> PillarScore:
    """Parse a Pillar from AI output into PillarScore.

    `computed_dim_scores` is the dict from `scoring_math.compute_all`'s
    "dimensions" key — keyed by dimension key (lowercase, underscores).
    When provided, dimension scores AND weights come from the math layer
    rather than from the AI output. The AI's claimed scores are discarded.
    """
    import scoring_config as cfg

    dims_data = pillar_data.get("dimensions", {})

    # Map dimension key -> weight from the config (NO HARD CODING)
    dim_weights: dict[str, int] = {}
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            key = dim.name.lower().replace(" ", "_")
            dim_weights[key] = dim.weight

    # Pillar weight from config too
    weight = pillar_data.get("weight", 0)
    for pillar in cfg.PILLARS:
        if pillar.name == pillar_name:
            weight = pillar.weight
            break

    dimensions = []
    for dim_key, dim_data in dims_data.items():
        display_name = dim_key.replace("_", " ").title()
        # Prefer computed score from scoring_math; fall back to AI output only
        # if math wasn't run (defensive — should not happen in normal flow)
        if computed_dim_scores and dim_key in computed_dim_scores:
            score = computed_dim_scores[dim_key]["score"]
        else:
            score = min(dim_data.get("score", 0), dim_weights.get(dim_key, 100))
        dimensions.append(DimensionScore(
            name=display_name,
            score=score,
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


# Scoring context construction lives in scoring_config.build_scoring_context
# (Define-Once seam). scorer.py and intelligence.py both call that helper —
# this module no longer carries its own copy.


def _parse_product(data: dict) -> Product:
    """Parse a complete product from AI scoring output into the new model.

    The AI is responsible for evidence synthesis (badges + bullets). All scoring
    math is performed deterministically by `scoring_math.compute_all()` from the
    badges the AI emitted. The AI's claimed dimension scores are IGNORED — the
    Python math is the source of truth for every number on the page.
    """
    import scoring_math

    pillar_scores = data.get("pillar_scores", {})
    evidence_dict = data.get("evidence", {})
    poor_match_flags = data.get("poor_match_flags", []) or []
    orchestration_method = data.get("orchestration_method", "") or ""

    # ─── Build scoring context for the rubric model baselines ────────────
    # Pillar 2 (IV) dimensions look up category-aware baselines via
    # product_category. Pillar 3 (CF) dimensions look up organization-type
    # baselines via org_type. Missing values fall back to UNKNOWN_CLASSIFICATION
    # which triggers the classification review flag in the dossier UX.
    import scoring_config as _cfg_for_context
    scoring_context = _cfg_for_context.build_scoring_context(
        raw_org_type=data.get("organization_type"),
        raw_product_category=data.get("product_category") or data.get("category"),
    )

    # ─── Build badges_by_dimension from the AI's evidence output ─────────
    # Each evidence entry has a "badge" name and a "color". We pass both to
    # the math layer so it can apply color-based fallback scoring for
    # badge-presence dimensions (Customer Fit, parts of Instructional Value).
    badges_by_dimension: dict[str, list] = {}
    for dim_key, items in evidence_dict.items():
        if not isinstance(items, list):
            continue
        # Carry the Pillar 2/3 rubric fields (strength + signal_category)
        # through to the math layer. scoring_math._compute_rubric_dimension_score
        # reads `badge.get("strength")` and `badge.get("signal_category")` from
        # these dicts to credit points by (dimension, strength) lookup. Dropping
        # them here was the root cause of the rubric architecture being non-
        # functional from f46dcc9 through bf930d0.
        badge_objs = [
            {
                "name": item.get("badge", ""),
                "color": item.get("color", ""),
                "strength": item.get("strength", ""),
                "signal_category": item.get("signal_category", ""),
            }
            for item in items
            if isinstance(item, dict) and item.get("badge")
        ]
        badges_by_dimension[dim_key.lower()] = badge_objs

    # ─── Run the deterministic math ──────────────────────────────────────
    math_result = scoring_math.compute_all(
        badges_by_dimension=badges_by_dimension,
        ceiling_flags=poor_match_flags,
        orchestration_method=orchestration_method,
        context=scoring_context,
    )

    if math_result.get("ceilings_applied"):
        log.info("Ceiling flags applied for %s: %s",
                 data.get("product_name") or data.get("name", "?"),
                 [c["flag"] for c in math_result["ceilings_applied"]])

    # ─── Parse pillars, OVERRIDING dimension scores with computed values ─
    fit = FitScore()
    for pillar_name, pillar_data in pillar_scores.items():
        parsed = _parse_pillar(
            pillar_name, pillar_data, evidence_dict,
            computed_dim_scores=math_result["dimensions"],
        )
        if "Labability" in pillar_name:
            fit.product_labability = parsed
        elif "Instructional" in pillar_name:
            fit.instructional_value = parsed
        elif "Customer" in pillar_name:
            fit.customer_fit = parsed

    # ─── Apply post-ceiling pillar score override and Fit Score override ─
    # Product Labability gets the post-ceiling score from the math layer.
    # The dimension scores remain authentic (so the badge story holds), but
    # the pillar header reflects the ceiling cap.
    pl_post_ceiling = math_result["pillars"]["product_labability"]
    fit.product_labability.score_override = pl_post_ceiling
    fit.pl_score_pre_ceiling = math_result["pillar_labability_pre_ceiling"]
    fit.ceilings_applied = math_result["ceilings_applied"]
    fit.technical_fit_multiplier = math_result["technical_fit_multiplier"]
    fit.total_override = math_result["fit_score"]

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
        classification_review_needed=bool(math_result.get("classification_review_needed", False)),
        owning_org=owning_org,
        contacts=contacts,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Seller Briefcase — separate AI call after scoring (GP3)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# Seller Briefcase — split into three independent AI calls per product
#
# Each section uses the right brain for its job:
#
#   Key Technical Questions  → Opus 4.6  — sales-critical, sharp synthesis
#   Conversation Starters    → Haiku 4.5 — pattern-matched, fast
#   Account Intelligence     → Haiku 4.5 — surface signals, fast
#
# All three calls per product run in parallel. Across N products, that's
# 3N parallel calls — total time gated by the slowest (Opus KTQ).
# ═══════════════════════════════════════════════════════════════════════════════

_BRIEFCASE_KTQ_MODEL = "claude-opus-4-6"
_BRIEFCASE_STARTERS_MODEL = "claude-haiku-4-5-20251001"
_BRIEFCASE_ACCT_MODEL = "claude-haiku-4-5-20251001"

_KTQ_SYSTEM_PROMPT = """You are a sales enablement expert for Skillable, a hands-on lab platform.

Your job: write Key Technical Questions for a seller about a specific product. These questions
will be used to start a conversation with a TECHNICAL contact at the customer who can actually
answer them. The seller will forward your exact question to that person via email or Slack.

These questions unblock the lab build. They surface the technical details Skillable needs —
BUT ONLY THE ONES THAT ACTUALLY APPLY TO THIS PRODUCT.

═══ HARD RULE: ONLY ASK QUESTIONS THAT APPLY TO THIS PRODUCT ═══

Before writing any question, read the `deployment_model`, `orchestration_method`, and
`pillar_1_dimensions` you were given in the scoring context. The questions you ask MUST
match the actual shape of this product. If a question doesn't apply, DO NOT ask it — pick
a different question that does apply, or return fewer bullets.

**Product-shape decision tree — apply BEFORE writing questions:**

| If the product is... | DO ask about... | DO NOT ask about... |
|---|---|---|
| A VM-hosted application (Hyper-V / ESX / Docker orchestration) | NFR / eval licensing for lab use, snapshot/revert timing, identity INSIDE the VM, sample datasets for the lab, multi-VM topology, learner isolation at the VM level | Public REST APIs, Sandbox API, Scoring API, Teardown API — the VM IS the lab; teardown is snapshot revert, not an API call |
| A SaaS / cloud service consumed via API | Sandbox API availability, rate limits, per-learner credentials, Scoring API surface for state validation, Teardown API for resource cleanup, OAuth/auth model | VM licensing, snapshot/revert — there is no VM |
| A hybrid (SaaS queried from a VM lab) | BOTH: VM-level questions (snapshot, licensing) AND cloud-service questions (shared credential handling, API key rotation, per-learner sandbox) | Whichever side doesn't apply to the specific integration |
| A desktop / on-prem appliance | Installer availability, license key model for non-production, default config reset between learners, hardware requirements | REST APIs unless the product specifically exposes one |
| A physical device / hardware | Simulators, emulators, remote hands, hardware-in-the-loop options | Anything software-API-specific |

**The Pillar 1 dimension summaries tell you what's already known.** If the Provisioning dimension summary says "the VM is the lab, GTI is the external service," the seller does NOT need to ask "does this have a Sandbox API" — the research already answered that. Ask about the NEXT unknown instead (licensing, snapshot timing, shared credential model).

**Forbidden failure mode:** Emitting a generic `Validate Teardown API` or `Confirm API Surface` question on a product whose orchestration_method is Hyper-V and whose description makes clear it's a VM-hosted application with no public API. That's a template response, not product-specific sales enablement — and it embarrasses the seller.

═══ WHO to target — TECHNICAL ROLES ONLY ═══

Every KTQ bullet must name a specific TECHNICAL role at the customer who has the actual
technical knowledge to answer the question. These are the people the seller should reach:

✅ TARGET THESE ROLES:
- Principal Engineer / Staff Engineer (the deep technical IC)
- API Team Lead / API Platform Lead / Platform Engineering Lead
- Solution Architect / Field Solution Architect
- Sales Engineer / Solution Engineer / Solutions Consultant
- Customer Onboarding Engineer / Technical Onboarding Lead
- DevRel / Developer Relations / Developer Experience Engineer
- Site Reliability Engineer (SRE) on the product team
- Product team technical lead (engineering manager on the product line)

❌ DO NOT TARGET THESE ROLES — they belong in Conversation Starters or Account Intelligence:
- VP of Customer Education / VP of Training
- Director of Customer Success / Director of Customer Education
- Director of Training / Director of Enablement
- Chief Learning Officer / Head of Learning
- Any C-suite role
- Any pure-management or pure-strategy role

Why this matters: VPs and Directors are strategic decision-makers, not technical answerers.
Forwarding "does the REST API support DELETE on user records?" to a VP wastes the seller's
credibility — the VP either has to forward it themselves or guess. Go directly to the engineer.

Output JSON with this structure:
{
  "bullets": [
    "<short label> — <technical role + team>. <Verbatim question the engineer can paste into a reply>",
    ...
  ]
}

Rules:
- 2-3 bullets maximum — **but at least ONE bullet always. Never return an empty list.** If scoring evidence is thin, surface the single most important unknown you can identify (API surface, identity model, NFR licensing, etc.) and ask the clearest answerable question you can.
- **Each bullet STARTS with a 2-3 word BOLD LABEL framed as the PROBLEM TO SOLVE** (not a topic, not a category). The label is an imperative phrase the seller reads as "this is what needs to happen." Choose labels that match the product's actual shape:
  * **`**Unlock Sandbox API**`** — for SaaS/API products that need a per-learner sandbox
  * **`**Confirm NFR Path**`** — for VM-hosted software that needs eval licensing
  * **`**Secure Snapshot Revert**`** — for VM-hosted products torn down via snapshot
  * **`**Resolve Identity Model**`** — for products where learner identity/auth inside the lab is unclear
  * **`**Pursue POC Credentials**`** — when access itself is the unblocker
  * **`**Clarify Shared Creds**`** — for hybrid products using shared vendor API keys
  * **`**Rate Sample Data**`** — for products that need seeded datasets in the lab
  WRONG — topic labels with no verb: `Provisioning Path`, `Identity Model`, `API Scoring`, `NFR Licensing`. Those are categories, not problems to solve.
  **ALSO WRONG — emitting an API-shaped label on a product with no API.** Never emit `Validate Teardown API`, `Confirm API Surface`, or `Unlock Sandbox API` on a product whose orchestration is Hyper-V / ESX and whose description makes clear it's a VM-hosted application without a public API. Read the `pillar_1_dimensions` first.
- **Target 30 words maximum per bullet.** If you have more to say, it's a second bullet. Short and specific beats long and comprehensive.
- **Anchor strictly to THIS product** — never reference similar products from the same company. If you're scoring Trellix Global Threat Intelligence, do NOT mention Trellix Insights or Trellix Endpoint Security in the same bullet; each product has its own briefcase.
- Every bullet identifies a TECHNICAL role from the list above
- Every bullet contains a VERBATIM question the engineer can answer in 1-2 sentences
- Every bullet is specific to THIS product and THIS company — never generic
- The questions must be answerable. Don't ask "what's your strategy" — ask "does the REST API support DELETE on user records?"
- Lead with the highest-value unknown — the one that unblocks the most downstream decisions
"""

_STARTERS_SYSTEM_PROMPT = """You are a sales enablement expert for Skillable, a hands-on lab platform.

Your job: write Conversation Starters that help a seller talk credibly with a STRATEGIC
buyer (VP-level or Director-level) about why hands-on training matters for a specific
product. The seller is not technical — they need product-specific talking points they can
use in a discovery call without sounding scripted.

═══ WHO this is for — STRATEGIC LEADERS ═══

Conversation Starters are the talking points the seller uses with VPs, Directors, and
strategic decision-makers. These are the people who own training budgets, set learning
strategy, and decide whether to invest in a hands-on platform. They're not the right
audience for technical "does your API support X" questions — they're the right audience
for "here's why your customers struggle with $PRODUCT and what hands-on labs do about it."

✅ TARGET AUDIENCE for Conversation Starters:
- VP of Customer Education / VP of Training / VP of Customer Success
- Director of Customer Education / Director of Enablement
- Chief Learning Officer / Head of Learning
- Director of Customer Success / Director of Customer Outcomes
- VP of Product (when training is part of GTM)

The talking point should be something the VP can RESPOND TO with a strategic concern of
their own ("yeah, that's exactly why we're doing X") — not something they have to forward
to engineering to answer.

Output JSON with this structure:
{
  "bullets": [
    "<one product-specific strategic talking point>",
    ...
  ]
}

Rules:
- 2-3 bullets maximum — **but at least ONE bullet always. Never return an empty list.** If there's nothing strong to say about this product's complexity or stakes, pivot to an adjacent strategic angle (recent press release, executive hire, flagship product release, market timing) — something the seller can legitimately open with.
- **Each bullet STARTS with a 2-3 word BOLD LABEL framed as the STRATEGIC ANGLE the seller should open with** (not a topic, not a category). Examples of correct bold labels:
  * **`**Pitch Breach Anchor**`** — copy explains how
  * **`**Lead With NRR**`** — copy explains how
  * **`**Frame Time-To-Value**`** — copy explains how
  * **`**Anchor On Compliance**`** — copy explains how
  * **`**Open On Retention**`** — copy explains how
  WRONG — topic labels: `Customer Retention`, `Product Complexity`, `Strategic Angle`. Those are categories, not angles to open with.
- **Target 30 words maximum per bullet.** Short and specific beats long and comprehensive.
- **Anchor strictly to THIS product** — never reference similar products from the same company. Each product has its own briefcase; don't bleed context across them.
- Each bullet is a complete, conversational sentence the seller could say out loud TO A VP
- Each bullet ties THIS product's complexity, stakes, regulatory exposure, customer outcomes,
  or workflows to why hands-on training matters at the STRATEGIC level (not the API level)
- Frame around business outcomes: customer retention, time-to-productivity, certification
  pass rates, regulatory readiness, expansion revenue, NRR, churn risk
- Never generic ("hands-on training is important") — always grounded in this specific product
- Never technical ("does your API support DELETE") — that belongs in KTQ
- Make the seller sound credible without making them sound like an SE
- Include one stat, anchor, or specific detail per bullet when possible
"""

_ACCT_SYSTEM_PROMPT = """You are a sales enablement expert for Skillable, a hands-on lab platform.

Your job: write Account Intelligence bullets that show the seller has done their homework
AND give them concrete actions to take. Not just "they have a conference" — "find the
person who runs that conference and talk to them, here's why it matters."

Output JSON with this structure:
{
  "bullets": [
    "<one actionable organizational signal with specific detail and a concrete next step>",
    ...
  ]
}

═══ Rules ═══

- 2-3 bullets maximum — **but at least ONE bullet always. Never return an empty list.** If there's no strong scoring signal, find ANYTHING real from the company research to anchor a bullet: a recent press release, a newly hired executive, a product launch, an earnings-call mention of training, an industry event they sponsor. Something. An empty Account Intelligence box is a research failure, not a valid result.
- **Each bullet STARTS with a 2-3 word BOLD LABEL framed as the CONCRETE NEXT STEP** (not a topic, not a category). Examples of correct bold labels:
  * **`**Find Elevate Lead**`** — copy explains the event and the ask
  * **`**Research New VP**`** — copy explains the hire and the angle
  * **`**Validate CloudShare Gap**`** — copy explains the displacement angle
  * **`**Pilot ATP Enablement**`** — copy explains the partner motion
  * **`**Anchor On Greenfield**`** — copy explains the no-incumbent opportunity
  WRONG — topic labels: `Annual Conference`, `Training Leader`, `Competitive Landscape`. Those are categories, not next steps.
- **Target 30 words maximum per bullet.** Short and specific beats long and comprehensive.
- **Anchor strictly to THIS product** — never reference similar products from the same company. Each product has its own briefcase; don't bleed context across them.
- Each bullet surfaces a SPECIFIC organizational signal anchored to a named entity:
  * Named LMS (Cornerstone, Docebo, etc.)
  * Named certification program (specific cert name, exam, recent updates)
  * Named training leader or department (e.g., "Diligent's Board Education & Certifications team")
  * Named competitive lab platform detected
  * Named partner program with size if known (e.g., "~500 ATPs")
  * Named annual conference / flagship event with date if known
- Never generic ("they care about training") — always anchored to a named entity
- If a piece of intel is missing from the scoring data, do NOT invent it
- Lead with the most actionable signal — the one a seller would actually open with

═══ PRIORITY ORDER — what to surface FIRST ═══

The Account Intelligence section has a strict priority order. The FIRST bullet must come from the highest-priority category that has real evidence in the scoring data. Only drop to a lower category when the higher one has no supporting evidence:

1. **Customer and partner events are HUGE — top priority.** Any named conference, flagship event, training summit, partner summit, community event, or customer conference with dates (even approximate ones) is the highest-value Account Intelligence signal. Events are Skillable's lowest-friction consumption motion: defined audience, defined timeline, defined opportunity. If the scoring evidence mentions ANY customer or partner event (Cisco Live, Cohesity Connect, Elevate, Dreamforce, Trailblazer Community events, RSA, Ignite, etc.), that bullet is FIRST.

2. **Already using a lab platform — equally critical.** If the scoring evidence shows the customer already uses Skillable or a competitor lab platform, surface this IMMEDIATELY as its own bullet (second at latest). This is the single most commercially consequential piece of Account Intelligence:
   - Skillable incumbent → **expansion play**, lead with "Find the account owner for the existing Skillable relationship and align on expansion into {product} training..."
   - Competitor incumbent (CloudShare, Instruqt, Skytap, Kyndryl, ReadyTech) → **displacement play**, lead with "Validate the displacement angle by asking the Director of Customer Education where the current {competitor} environment falls short on {specific gap}..."
   - No incumbent → **greenfield play**, lead with "Pitch Skillable as the first lab platform in their stack — no displacement work required..."

3. **Named training leader, department, or competitive intelligence** — VP-level training leadership, named Customer Education team, recent strategic hires.

4. **Active certification program or product launch** — named cert with exam details, recently updated cert, new flagship product release.

5. **Strategic press signals** — earnings calls mentioning training investment, recent M&A relevant to training footprint, investor mentions of enablement.

═══ Time-bounded opportunities are GOLD — surface them HARD ═══

When the scoring evidence mentions a specific conference, flagship event, certification
launch, product release, or other time-bounded signal, that bullet should be FIRST and
should include:

1. The named event with date if known (e.g., "Elevate 2026, Atlanta, April 22-24")
2. A concrete person/role to find (e.g., "the Director of Events" or "the head of
   conference programming")
3. WHY it matters as a specific Skillable opportunity, anchored to the framework:
   "Events are Skillable's lowest-friction consumption motion — a hands-on lab track
   at the conference is a defined audience, defined timeline, and zero competing lab
   platform to displace."

Worked example for Diligent (governance/compliance company with Elevate 2026 conference):

❌ WEAK:
"Diligent hosts an annual conference called Elevate."

✅ STRONG:
"Find the head of Elevate 2026 (Atlanta, April 22-24) — Diligent's annual flagship
event with registration already open. Events are Skillable's lowest-friction
consumption motion: defined audience, defined timeline, no incumbent lab platform
to displace. A hands-on governance audit lab track at Elevate would be the fastest
path from first conversation to live deployment."

═══ Other actionable signal types worth surfacing ═══

- **Greenfield lab platform opportunity**: "No incumbent lab platform detected — Skillable
  would be the first lab platform in their stack. No displacement work, just sell the
  hands-on premise."
- **Cert program with hands-on language**: "Their cert program already uses 'hands-on'
  language but no PBT — they're a half-step from needing a PBT delivery platform."
- **Named training leadership**: "Director of Customer Education named: <name>. Hands-on
  training is in their org's documented mandate."
- **Competitive platform with displacement angle**: "They use <competitor lab platform>
  today — known weaknesses are <specific gap>; lead with that."

These are not exhaustive — anything from the scoring evidence that translates to "here's
who to find and here's the angle" qualifies. Lead with the highest-leverage one.
"""


def _build_briefcase_context(product: Product, company_context: str) -> str:
    """Build the per-product context string used by all three section calls.

    KTQ needs Pillar 1 dimension summaries and badge names so it can write
    product-shape-aware questions — e.g., "this product runs in Hyper-V and
    is torn down by snapshot revert, so don't ask about a Teardown API."
    Without this context the AI falls back to generic "Confirm API surface"
    templates regardless of whether the product even has an API.
    """
    pl = product.fit_score.product_labability

    def _dim_summary(dim):
        return {
            "name": dim.name,
            "score": f"{dim.score}/{dim.weight}",
            "summary": (dim.summary or "")[:400],
            "badges": [
                {"name": b.name, "color": b.color, "qualifier": b.qualifier}
                for b in (dim.badges or [])
            ],
        }

    scoring_summary = json.dumps({
        "product": product.name,
        "category": product.category,
        "subcategory": product.subcategory,
        "description": (product.description or "")[:600],
        "fit_score": product.fit_score.total,
        "product_labability": pl.score,
        "instructional_value": product.fit_score.instructional_value.score,
        "customer_fit": product.fit_score.customer_fit.score,
        "deployment_model": product.deployment_model,
        "orchestration_method": product.orchestration_method,
        # Pillar 1 dimensions + badges drive KTQ product-shape awareness.
        # The AI reads these to know what's already confirmed vs. still
        # unknown about provisioning, lab access, scoring, and teardown
        # for THIS specific product.
        "pillar_1_dimensions": [_dim_summary(d) for d in pl.dimensions],
        "verdict": product.verdict.label if product.verdict else "",
        "contacts": [{"name": c.name, "title": c.title, "role_type": c.role_type}
                     for c in product.contacts],
    }, indent=2)
    return f"## Scoring Results\n{scoring_summary}\n\n{company_context}"


def _generate_briefcase_section(system_prompt: str, model: str,
                                user_content: str, max_tokens: int) -> list[str]:
    """Generate one briefcase section. Returns the bullets list, or empty on failure."""
    try:
        result = _call_claude(system_prompt, user_content,
                              max_tokens=max_tokens, model_override=model)
        return result.get("bullets", []) or []
    except Exception as e:
        log.error("Briefcase section generation failed (model=%s): %s", model, e)
        return []


def generate_briefcase(product: Product, company_context: str) -> SellerBriefcase:
    """Generate the three Seller Briefcase sections in parallel.

    Each section is its own Claude call with its own model:
      - Key Technical Questions → Opus (sales-critical)
      - Conversation Starters   → Haiku (fast)
      - Account Intelligence    → Haiku (fast)

    Total time is gated by the slowest call (Opus KTQ ≈ 20 seconds).
    """
    user_content = _build_briefcase_context(product, company_context)

    sections = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            "ktq": executor.submit(
                _generate_briefcase_section,
                _KTQ_SYSTEM_PROMPT, _BRIEFCASE_KTQ_MODEL, user_content, 800),
            "starters": executor.submit(
                _generate_briefcase_section,
                _STARTERS_SYSTEM_PROMPT, _BRIEFCASE_STARTERS_MODEL, user_content, 500),
            "acct": executor.submit(
                _generate_briefcase_section,
                _ACCT_SYSTEM_PROMPT, _BRIEFCASE_ACCT_MODEL, user_content, 500),
        }
        for key, fut in futures.items():
            sections[key] = fut.result()

    return SellerBriefcase(
        key_technical_questions=BriefcaseSection(
            pillar="Product Labability",
            heading="Key Technical Questions",
            bullets=sections.get("ktq", []),
        ),
        conversation_starters=BriefcaseSection(
            pillar="Instructional Value",
            heading="Conversation Starters",
            bullets=sections.get("starters", []),
        ),
        account_intelligence=BriefcaseSection(
            pillar="Customer Fit",
            heading="Account Intelligence",
            bullets=sections.get("acct", []),
        ),
    )
