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

CACHE_TTL_DAYS = 45


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
             force_refresh: bool = False) -> dict:
    """Web research + Claude product identification.

    Returns the discovery dict (including discovery_id). Saves to storage.
    Hits the 45-day cache unless force_refresh=True.
    """
    if not force_refresh:
        cached = find_discovery_by_company_name(company_name)
        if cached and cache_is_fresh(cached.get("created_at", "")):
            log.info("Intelligence.discover: cache hit for %s → %s",
                     company_name, cached.get("discovery_id"))
            return cached

    log.info("Intelligence.discover: running research for %s", company_name)

    from concurrent.futures import ThreadPoolExecutor
    from researcher_new import scrape_product_families
    with ThreadPoolExecutor(max_workers=2) as pool:
        family_future = pool.submit(scrape_product_families, company_name)
        findings = discover_products(company_name, known_products)
        scraped_families = []
        try:
            scraped_families = family_future.result(timeout=10)
        except Exception as e:
            log.warning("Product family scrape failed for %s: %s", company_name, e)

    discovery = discover_products_with_claude(findings)

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
        score = p.get("_discovery_score", 0)
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
          force_refresh: bool = False) -> tuple[str, CompanyAnalysis]:
    """Deep per-product scoring via the Prompt Generation System.

    Returns (analysis_id, CompanyAnalysis).

    After scoring:
    1. Assigns verdicts to each product
    2. Generates Seller Briefcase (separate AI call per product)
    3. Runs discrepancy detection against discovery tiers
    4. Logs competitor candidates to Prospector feed
    """
    if not discovery_data:
        discovery_data = load_discovery(discovery_id) or {}

    cache = discovery_data.get("_research_cache", {}) if research_cache is None else research_cache
    research = {
        "company_name": company_name,
        "selected_products": selected_products,
        "search_results": cache.get("search_results", {}),
        "page_contents": cache.get("page_contents", {}),
        "discovery_data": discovery_data,
    }

    log.info("Intelligence.score: scoring %d products for %s",
             len(selected_products), company_name)

    # Phase 1: Score all products (parallel, one Claude call each)
    analysis = score_selected_products(research)
    analysis.discovery_id = discovery_id
    analysis.total_products_discovered = len(discovery_data.get("products", []))

    # Phase 2: Assign verdicts
    for product in analysis.products:
        acv_tier = product.acv_potential.acv_tier or "medium"
        product.verdict = assign_verdict(product.fit_score.total, acv_tier)

    # Phase 3: Generate Seller Briefcase (separate AI call — better quality)
    company_context = _build_company_context_for_briefcase(company_name, discovery_data)
    for product in analysis.products:
        try:
            product_briefcase = generate_briefcase(product, company_context)
            # Store on first product's analysis for now — will be refined
            if analysis.briefcase is None:
                from models_new import SellerBriefcase
                analysis.briefcase = product_briefcase
        except Exception as e:
            log.error("Briefcase generation failed for %s: %s", product.name, e)

    # Sort by Fit Score
    score_products_and_sort(analysis)

    # Save
    analysis_id = save_analysis(analysis)
    log.info("Intelligence.score: saved analysis %s for %s", analysis_id, company_name)

    return analysis_id, analysis


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
    sorted_prods = sorted(products, key=lambda p: p.get("_discovery_score", 0), reverse=True)
    top = sorted_prods[0]

    # Use discovery-level data to build Prospector row
    fit = top.get("_discovery_score", 0)
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
