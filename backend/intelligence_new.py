"""
Intelligence — the shared platform layer for Skillable Intelligence.

All product research, scoring, and Skillable-specific knowledge flows through
this module. Inspector, Prospector, and Designer call these six operations.
Researcher and scorer are implementation details — callers never import them.

Six named operations
--------------------
    discover(company_name, force_refresh=False)
        Web research + Claude product identification. Returns discovery dict.
        Cached for CACHE_TTL_DAYS; force_refresh bypasses the cache.

    score(company_name, products, discovery_id, force_refresh=False)
        Deep per-product scoring via Prompt Generation System.
        Returns (analysis_id, CompanyAnalysis).
        Runs discrepancy detection after scoring.

    refresh(target_id, scope="all")
        Rerun a specific phase on an existing record.
        Returns updated data dict.

    expand(company_name, additional_products, analysis_id)
        Add products to an existing analysis without re-scoring what's already there.
        Returns (analysis_id, updated CompanyAnalysis).

    qualify(company_name, force_refresh=False)
        Prospector-mode: discovery + scoring at caseboard depth.
        Returns a Prospector-compatible row dict.

    lookup(company_name)
        Pure cache read — no research, no Claude calls.
        Returns {"analysis": dict|None, "discovery": dict|None, "found": bool}.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta

log = logging.getLogger(__name__)

from researcher_new import discover_products, research_products, research_company_fit, scrape_product_families
from scorer_new import discover_products_with_claude, score_selected_products, generate_briefcase, _call_claude
from storage_new import (
    save_analysis, load_analysis,
    save_discovery, load_discovery,
    find_analysis_by_company_name, find_discovery_by_company_name,
    find_analysis_by_discovery_id,
    save_competitor_candidates,
)
from core_new import (
    assign_verdict, discovery_tier, DISCOVERY_TIER_LABELS,
    company_classification_label, org_badge_color_group,
    score_products_and_sort,
)
from models_new import CompanyAnalysis, Product
from config_new import ANTHROPIC_MODEL

# ═══════════════════════════════════════════════════════════════════════════════
# Cache TTL — single definition for the whole platform
# ═══════════════════════════════════════════════════════════════════════════════

from config_new import CACHE_TTL_DAYS


def cache_is_fresh(timestamp_str: str) -> bool:
    """Return True if an ISO timestamp is within CACHE_TTL_DAYS of now."""
    if not timestamp_str:
        return False
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days < CACHE_TTL_DAYS
    except Exception:
        return False


def _new_id() -> str:
    return str(uuid.uuid4())[:8]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Discovery tier ordering for discrepancy detection
_TIER_ORDER = {
    "seems_promising": 0,
    "likely": 1,
    "uncertain": 2,
    "unlikely": 3,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 1 — discover
# ═══════════════════════════════════════════════════════════════════════════════

def discover(company_name: str, known_products: list[str] | None = None,
             force_refresh: bool = False,
             progress_cb=None) -> dict:
    """Web research + Claude product identification.

    Returns the discovery dict (including discovery_id). Saves to storage.
    Hits the 45-day cache unless force_refresh=True OR the cached discovery
    was scored with an older SCORING_LOGIC_VERSION (in which case it's
    treated as stale and re-run automatically — closes the cache versioning
    gap so customers don't see degraded scores after scoring logic changes).

    progress_cb: optional callable accepting a single status string. Invoked
    at each phase boundary so callers (e.g. the SSE route) can stream real
    progress to the discovering page instead of relying on cycling hints.
    """
    import scoring_config as cfg

    def _progress(msg: str) -> None:
        if progress_cb:
            try:
                progress_cb(msg)
            except Exception:
                log.exception("progress_cb raised — ignoring")

    if not force_refresh:
        cached = find_discovery_by_company_name(company_name)
        if cached and cache_is_fresh(cached.get("created_at", "")):
            if not cfg.is_cached_logic_current(cached):
                log.info(
                    "Intelligence.discover: cached discovery for %s is stale "
                    "(logic version %r vs current %r) — re-running",
                    company_name,
                    cached.get("_scoring_logic_version", "<missing>"),
                    cfg.SCORING_LOGIC_VERSION,
                )
            else:
                log.info("Intelligence.discover: cache hit for %s → %s",
                         company_name, cached.get("discovery_id"))
                return cached

    log.info("Intelligence.discover: running research for %s", company_name)
    _progress("Locating the company website…")

    from concurrent.futures import ThreadPoolExecutor
    from researcher_new import scrape_product_families
    with ThreadPoolExecutor(max_workers=2) as pool:
        family_future = pool.submit(scrape_product_families, company_name)
        _progress("Identifying the product portfolio…")
        findings = discover_products(company_name, known_products)
        _progress("Extracting product families & categories…")
        scraped_families = []
        try:
            scraped_families = family_future.result(timeout=10)
        except Exception as e:
            log.warning("Product family scrape failed for %s: %s", company_name, e)

    _progress("Detecting deployment models & tech stack…")
    discovery = discover_products_with_claude(findings)
    _progress("Mapping competitive products & vendor landscape…")

    # Preserve raw research signals alongside Claude output
    for key in ("training_programs", "atp_signals", "training_catalog",
                "partner_ecosystem", "partner_portal", "cs_signals",
                "lms_signals", "org_contacts", "page_contents",
                "lab_platform_signals"):
        discovery[key] = findings.get(key, [])

    discovery["discovery_id"] = _new_id()
    discovery["created_at"] = _now_iso()
    discovery["known_products"] = known_products or []

    # Assign discovery tiers using new labels
    for p in discovery.get("products", []):
        score = p.get("discovery_score", 0)
        p["_tier"] = discovery_tier(score)
        p["_tier_label"] = DISCOVERY_TIER_LABELS.get(p["_tier"], p["_tier"])

    # Domain-based lab platform detection — already done by researcher
    lab_detections = findings.get("lab_platform_detections", [])
    if lab_detections:
        discovery["_lab_platform_detections"] = lab_detections
        log.info("Intelligence.discover: detected %d lab platform(s) for %s",
                 len(lab_detections), company_name)

    # Company classification
    discovery["_company_badge"] = company_classification_label(
        discovery.get("organization_type", "software_company"), []
    )
    discovery["_org_color"] = org_badge_color_group(
        discovery.get("organization_type", "software_company")
    )

    if scraped_families:
        discovery["_scraped_families"] = scraped_families

    _progress("Categorizing offerings against Skillable taxonomy…")
    save_discovery(discovery["discovery_id"], discovery)
    log.info("Intelligence.discover: saved discovery %s for %s",
             discovery["discovery_id"], company_name)
    return discovery


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 2 — score
# ═══════════════════════════════════════════════════════════════════════════════

def score(company_name: str, selected_products: list[dict], discovery_id: str,
          discovery_data: dict | None = None,
          research_cache: dict | None = None,
          force_refresh: bool = False) -> tuple[str, list[str]]:
    """Deep per-product scoring with cache-and-append semantics.

    ARCHITECTURE — One persistent analysis per company (per discovery_id), forever.
    Each Deep Dive run accumulates products into the same analysis. Stable URL.

    LOGIC:
      1. Look up the existing analysis for this discovery_id.
      2. For each selected product, check if it's already scored in the existing analysis.
         - Cached → leave alone
         - New → score it (parallel Claude calls, only for new products)
      3. Append newly scored products to the existing analysis.
      4. Save back to the SAME analysis_id (or create one if first time).

    Returns: (analysis_id, names_of_newly_scored_products)
      The list of newly scored names is used by the briefcase phase to generate
      briefcases ONLY for new products (cached ones keep their cached briefcase).
    """
    from storage_new import find_analysis_by_discovery_id, save_analysis as _save
    import scoring_config as cfg

    if not discovery_data:
        discovery_data = load_discovery(discovery_id) or {}

    # Look up existing analysis for this discovery — stable URL principle
    existing = find_analysis_by_discovery_id(discovery_id)
    existing_product_names = set()
    if existing:
        # Cache versioning — if the existing analysis was scored with an
        # older SCORING_LOGIC_VERSION, treat ALL its products as stale and
        # force re-score. The analysis_id is preserved (stable URL principle)
        # but every product gets fresh scoring against the current logic.
        if not cfg.is_cached_logic_current(existing):
            stale_count = len(existing.get("products", []) or [])
            log.info(
                "Intelligence.score: existing analysis %s has stale logic version "
                "(%r vs current %r) — wiping %d legacy products",
                existing.get("analysis_id"),
                existing.get("_scoring_logic_version", "<missing>"),
                cfg.SCORING_LOGIC_VERSION,
                stale_count,
            )
            # CRITICAL: wipe the legacy products list so they don't survive
            # the cache-and-append below. Previously this code only blanked
            # existing_product_names, leaving the legacy products in place
            # to be appended onto by new scores — that's how Trellix ended
            # up with 11 products (7 unique + 4 duplicates) all stamped with
            # a current version they were never actually scored under.
            # See investigation 2026-04-06 evening for the full root cause.
            existing["products"] = []
            existing["_scoring_logic_version"] = cfg.SCORING_LOGIC_VERSION
        else:
            for p in existing.get("products", []):
                existing_product_names.add(p.get("name", ""))
            log.info("Intelligence.score: existing analysis %s has %d products cached",
                     existing.get("analysis_id"), len(existing_product_names))

    # Split selected products into cached vs new
    new_to_score = [p for p in selected_products if p.get("name") not in existing_product_names]
    cached_count = len(selected_products) - len(new_to_score)
    log.info("Intelligence.score: %d products selected — %d cached, %d new to score",
             len(selected_products), cached_count, len(new_to_score))

    # Fast path: nothing new to score — return the existing analysis as-is
    if existing and not new_to_score:
        log.info("Intelligence.score: ALL selected products cached — returning existing analysis %s",
                 existing.get("analysis_id"))
        return existing.get("analysis_id"), []

    new_product_names = []

    if new_to_score:
        cache = discovery_data.get("_research_cache", {}) if research_cache is None else research_cache
        research = {
            "company_name": company_name,
            "selected_products": new_to_score,
            "search_results": cache.get("search_results", {}),
            "page_contents": cache.get("page_contents", {}),
            "discovery_data": discovery_data,
        }

        # Score only the NEW products in parallel
        new_analysis = score_selected_products(research)

        # Assign verdicts
        for product in new_analysis.products:
            acv_tier = product.acv_potential.acv_tier or "medium"
            product.verdict = assign_verdict(product.fit_score.total, acv_tier)

        # Convert to dicts for merging into the existing analysis
        from dataclasses import asdict
        new_product_dicts = [asdict(p) for p in new_analysis.products]
        new_product_names = [p["name"] for p in new_product_dicts]

    if existing:
        # Append new products to existing analysis (preserves analysis_id and URL)
        existing_dict = existing
        if new_to_score:
            existing_dict["products"].extend(new_product_dicts)
            # Re-sort by fit_score total descending
            existing_dict["products"].sort(
                key=lambda p: (p.get("fit_score", {}) or {}).get("total", 0)
                              if isinstance(p.get("fit_score"), dict)
                              else 0,
                reverse=True,
            )
            existing_dict["total_products_discovered"] = len(discovery_data.get("products", []))
            _save(existing_dict)
            log.info("Intelligence.score: appended %d new products to analysis %s",
                     len(new_product_dicts), existing_dict.get("analysis_id"))
        return existing_dict.get("analysis_id"), new_product_names

    # First-ever analysis for this discovery — save fresh with all new products
    new_analysis.discovery_id = discovery_id
    new_analysis.total_products_discovered = len(discovery_data.get("products", []))
    score_products_and_sort(new_analysis)
    new_analysis.briefcase = None  # Briefcase moved to product level
    analysis_id = save_analysis(new_analysis)
    log.info("Intelligence.score: created new analysis %s with %d products",
             analysis_id, len(new_analysis.products))
    return analysis_id, new_product_names


def _build_briefcase_context_from_dict(p_dict: dict, company_context: str) -> str:
    """Build the per-product context string for briefcase generation, directly from
    a saved product dict (no Product object reconstruction needed).

    The saved JSON shape has contacts as a list and fit_score as a nested dict.
    This function extracts what generate_briefcase's prompt needs.
    """
    import json
    fit_score = p_dict.get("fit_score", {}) or {}
    pl = fit_score.get("product_labability", {}) or {}
    iv = fit_score.get("instructional_value", {}) or {}
    cf = fit_score.get("customer_fit", {}) or {}
    verdict = p_dict.get("verdict") or {}
    contacts_raw = p_dict.get("contacts", []) or []
    # Contacts may be a list (saved format) or a dict by role type (legacy)
    if isinstance(contacts_raw, dict):
        contacts_list = []
        for role_type, c in contacts_raw.items():
            if isinstance(c, dict) and c.get("name"):
                contacts_list.append({
                    "name": c.get("name", ""),
                    "title": c.get("title", ""),
                    "role_type": role_type,
                })
    else:
        contacts_list = [
            {
                "name": c.get("name", ""),
                "title": c.get("title", ""),
                "role_type": c.get("role_type", ""),
            }
            for c in contacts_raw if isinstance(c, dict) and c.get("name")
        ]

    scoring_summary = json.dumps({
        "product": p_dict.get("name", ""),
        "fit_score": fit_score.get("total", 0),
        "product_labability": pl.get("score", 0),
        "instructional_value": iv.get("score", 0),
        "customer_fit": cf.get("score", 0),
        "deployment_model": p_dict.get("deployment_model", ""),
        "orchestration_method": p_dict.get("orchestration_method", ""),
        "verdict": verdict.get("label", "") if isinstance(verdict, dict) else "",
        "contacts": contacts_list,
    }, indent=2)

    return f"## Scoring Results\n{scoring_summary}\n\n{company_context}"


def generate_briefcase_for_analysis(analysis_id: str,
                                    only_for_products: list[str] | None = None) -> bool:
    """Phase B: Generate Seller Briefcases for products in an analysis.

    Briefcase is per-product. Each product gets THREE Claude calls in parallel:
    Key Technical Questions (Opus), Conversation Starters (Haiku), Account
    Intelligence (Haiku). Across N products that's 3N parallel calls.

    only_for_products: if provided, generate ONLY for those product names.
                      Default: skip any product that already has a briefcase.

    Safe to run in a background thread. Returns True on success.
    """
    from storage_new import load_analysis as _load, save_analysis as _save
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from scorer_new import (
        _generate_briefcase_section,
        _KTQ_SYSTEM_PROMPT, _STARTERS_SYSTEM_PROMPT, _ACCT_SYSTEM_PROMPT,
        _BRIEFCASE_KTQ_MODEL, _BRIEFCASE_STARTERS_MODEL, _BRIEFCASE_ACCT_MODEL,
    )

    analysis_dict = _load(analysis_id)
    if not analysis_dict:
        log.error("generate_briefcase_for_analysis: analysis %s not found", analysis_id)
        return False

    company_name = analysis_dict.get("company_name", "")
    discovery_id = analysis_dict.get("discovery_id", "")
    discovery_data = load_discovery(discovery_id) or {}
    company_context = _build_company_context_for_briefcase(company_name, discovery_data)

    products_dicts = analysis_dict.get("products", [])

    # Decide which products need a briefcase
    target_names = set(only_for_products or [])
    products_to_generate = []  # list of (index, product_dict)
    for i, p_dict in enumerate(products_dicts):
        name = p_dict.get("name", "")
        already_has = p_dict.get("briefcase") is not None
        wanted = (not target_names) or (name in target_names)
        if wanted and not already_has:
            products_to_generate.append((i, p_dict))

    if not products_to_generate:
        log.info("Briefcase: nothing to generate for analysis %s — all targeted products cached",
                 analysis_id)
        return True

    log.info("Briefcase: generating for analysis %s (%d products: %s)",
             analysis_id, len(products_to_generate),
             ", ".join(p["name"] for _, p in products_to_generate))

    # Build flat list of (product_idx, section_key, prompt, model, max_tokens, user_content)
    SECTIONS = [
        ("ktq", _KTQ_SYSTEM_PROMPT, _BRIEFCASE_KTQ_MODEL, 800),
        ("starters", _STARTERS_SYSTEM_PROMPT, _BRIEFCASE_STARTERS_MODEL, 500),
        ("acct", _ACCT_SYSTEM_PROMPT, _BRIEFCASE_ACCT_MODEL, 500),
    ]

    work_items = []  # (product_idx, section_key, system_prompt, model, max_tokens, user_content)
    for idx, p_dict in products_to_generate:
        user_content = _build_briefcase_context_from_dict(p_dict, company_context)
        for section_key, system_prompt, model, max_tokens in SECTIONS:
            work_items.append((idx, section_key, system_prompt, model, max_tokens, user_content))

    # Run ALL section calls in parallel — across all products and all sections
    # 3 products × 3 sections = 9 parallel calls; gated by slowest Opus call
    section_results = {}  # (idx, section_key) -> bullets list
    with ThreadPoolExecutor(max_workers=min(len(work_items), 12)) as executor:
        futures = {
            executor.submit(_generate_briefcase_section, sp, model, uc, max_tok): (idx, key)
            for idx, key, sp, model, max_tok, uc in work_items
        }
        for future in as_completed(futures):
            idx, key = futures[future]
            try:
                bullets = future.result()
                section_results[(idx, key)] = bullets or []
            except Exception as e:
                log.error("Briefcase section failed for product %d %s: %s", idx, key, e)
                section_results[(idx, key)] = []

    # Assemble per-product briefcases and write back
    PILLARS = {"ktq": "Product Labability", "starters": "Instructional Value", "acct": "Customer Fit"}
    HEADINGS = {"ktq": "Key Technical Questions", "starters": "Conversation Starters", "acct": "Account Intelligence"}
    KEY_NAMES = {"ktq": "key_technical_questions", "starters": "conversation_starters", "acct": "account_intelligence"}

    for idx, _ in products_to_generate:
        briefcase_dict = {}
        for section_key in ("ktq", "starters", "acct"):
            briefcase_dict[KEY_NAMES[section_key]] = {
                "pillar": PILLARS[section_key],
                "heading": HEADINGS[section_key],
                "bullets": section_results.get((idx, section_key), []),
            }
        # Reload-modify-save to be safe with concurrent writes
        current = _load(analysis_id) or analysis_dict
        try:
            current["products"][idx]["briefcase"] = briefcase_dict
            _save(current)
            analysis_dict = current
            log.info("Briefcase: saved for product %d (%s) of analysis %s",
                     idx, current["products"][idx].get("name"), analysis_id)
        except Exception as e:
            log.error("Briefcase: failed to save for product %d: %s", idx, e)

    log.info("Briefcase: generation complete for analysis %s", analysis_id)
    return True


def _build_company_context_for_briefcase(company_name: str, discovery_data: dict) -> str:
    """Build company context string for the Seller Briefcase AI call."""
    lines = [f"# Company: {company_name}\n"]
    if discovery_data.get("company_description"):
        lines.append(f"**Description:** {discovery_data['company_description']}")
    if discovery_data.get("organization_type"):
        lines.append(f"**Organization type:** {discovery_data['organization_type']}")

    # Training signals
    for key in ("training_programs", "atp_signals"):
        items = discovery_data.get(key, [])
        if items:
            lines.append(f"\n## {key.replace('_', ' ').title()}")
            for r in items[:5]:
                lines.append(f"- {r.get('title', '')} — {r.get('snippet', '')}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 3 — refresh
# ═══════════════════════════════════════════════════════════════════════════════

def refresh(target_id: str, scope: str = "all") -> dict:
    """Rerun discovery or scoring on an existing record.

    scope: "discovery" | "products" | "all"
    """
    analysis_data = load_analysis(target_id)
    if not analysis_data:
        discovery_data = load_discovery(target_id)
        if discovery_data:
            return discover(discovery_data.get("company_name", ""), force_refresh=True)
        raise ValueError(f"No record found for ID: {target_id}")

    company_name = analysis_data.get("company_name", "")
    discovery_id = analysis_data.get("discovery_id", "")

    if scope in ("discovery", "all"):
        discover(company_name, force_refresh=True)

    if scope in ("products", "all"):
        products = analysis_data.get("products", [])
        selected = [{"name": p.get("name", "")} for p in products]
        _, updated = score(company_name, selected, discovery_id, force_refresh=True)
        return {"analysis_id": target_id, "status": "refreshed", "scope": scope}

    return {"analysis_id": target_id, "status": "refreshed", "scope": scope}


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 4 — expand
# ═══════════════════════════════════════════════════════════════════════════════

def expand(company_name: str, additional_products: list[dict],
           analysis_id: str) -> tuple[str, dict]:
    """Add products to an existing analysis without re-scoring existing ones."""
    existing = load_analysis(analysis_id)
    if not existing:
        raise ValueError(f"Analysis {analysis_id} not found")

    discovery_id = existing.get("discovery_id", "")
    new_id, updated = score(company_name, additional_products, discovery_id)

    log.info("Intelligence.expand: added %d products to %s → new analysis %s",
             len(additional_products), analysis_id, new_id)
    return new_id, updated


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 5 — qualify (Prospector mode)
# ═══════════════════════════════════════════════════════════════════════════════

def qualify(company_name: str, force_refresh: bool = False) -> dict | None:
    """Prospector-mode: discovery-depth research + scoring.

    Returns a Prospector-compatible row dict, or None if company has no products.
    Both Prospector batch scoring and Caseboard use this same depth.
    """
    # Run discovery
    disc = discover(company_name, force_refresh=force_refresh)
    if not disc or not disc.get("products"):
        return _no_fit_row(company_name, disc)

    products = disc.get("products", [])

    # Find top product by discovery score
    sorted_prods = sorted(products, key=lambda p: p.get("discovery_score", 0), reverse=True)
    top = sorted_prods[0]

    # Use discovery-level data to build Prospector row
    fit = top.get("discovery_score", 0)
    tier = discovery_tier(fit)

    # Contacts
    contacts = disc.get("_contacts", [])
    dm = next((c for c in contacts if c.get("role_type") == "decision_maker"), {})
    inf = next((c for c in contacts if c.get("role_type") == "influencer"), {})

    return {
        "company_name": company_name,
        "company_url": disc.get("company_url", ""),
        "top_product": top.get("name", ""),
        "fit_score": fit,
        "orchestration_method": top.get("orchestration_method", ""),
        "verdict": DISCOVERY_TIER_LABELS.get(tier, tier),
        "top_contact_name": dm.get("name", ""),
        "top_contact_title": dm.get("title", ""),
        "top_contact_linkedin": dm.get("linkedin_url", ""),
        "second_contact_name": inf.get("name", ""),
        "second_contact_title": inf.get("title", ""),
        "second_contact_linkedin": inf.get("linkedin_url", ""),
        "analysis_id": disc.get("discovery_id", ""),
        "hubspot_icp_context": "",  # Generated on write-back to HubSpot (GP5)
    }


def _no_fit_row(company_name: str, discovery: dict | None) -> dict:
    """Build a Prospector row for a company with no viable products."""
    return {
        "company_name": company_name,
        "company_url": discovery.get("company_url", "") if discovery else "",
        "top_product": "",
        "fit_score": 0,
        "orchestration_method": "Not a Fit",
        "verdict": "Unlikely",
        "top_contact_name": "",
        "top_contact_title": "",
        "top_contact_linkedin": "",
        "second_contact_name": "",
        "second_contact_title": "",
        "second_contact_linkedin": "",
        "analysis_id": "",
        "hubspot_icp_context": "",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Operation 6 — lookup
# ═══════════════════════════════════════════════════════════════════════════════

def lookup(company_name: str) -> dict:
    """Pure cache read — no research, no Claude calls.

    Returns {"analysis": dict|None, "discovery": dict|None, "found": bool}.
    """
    analysis = find_analysis_by_company_name(company_name)
    discovery = find_discovery_by_company_name(company_name)
    return {
        "analysis": analysis,
        "discovery": discovery,
        "found": bool(analysis or discovery),
    }
