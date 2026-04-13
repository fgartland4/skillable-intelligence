"""Web research orchestration for the Skillable Intelligence Platform.

Gathers evidence for all 12 dimensions across three Pillars, organized
so the AI scorer receives structured, dimension-mapped research.

Three research depths:
  - Discovery: broad company + product identification (Prospector, Caseboard)
  - Deep research: per-product evidence for all Product Labability + Instructional Value dimensions
  - Company research: evidence for all Customer Fit dimensions

Research is about THEM — what we know about the company and its products.
Skillable Knowledge (what WE can do) is separate (backend/knowledge/).
"""

from __future__ import annotations

import json
import logging
import os
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from models import (
    BuildCapacityFacts, CustomerFitFacts, DeliveryCapacityFacts,
    InstructionalValueFacts, LabAccessFacts, LabVersatilityFacts,
    MarketDemandFacts, MasteryStakesFacts, NumericRange,
    OrganizationalDnaFacts, ProductComplexityFacts, ProductLababilityFacts,
    ProvisioningFacts, ScoringFacts, SignalEvidence, TeardownFacts,
    TrainingCommitmentFacts,
)

log = logging.getLogger(__name__)

# Load .env for API keys
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

_SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

# Load Skillable knowledge for research targeting
_KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def _load_knowledge(filename: str) -> dict:
    """Load a Skillable knowledge JSON file."""
    path = _KNOWLEDGE_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    log.warning("Knowledge file not found: %s", path)
    return {}


_COMPETITORS = _load_knowledge("competitors.json")
_CAPABILITIES = _load_knowledge("skillable_capabilities.json")
_CONTACT_GUIDANCE = _load_knowledge("contact_guidance.json")


# ═══════════════════════════════════════════════════════════════════════════════
# Search Infrastructure — framework-agnostic HTTP and parsing
# ═══════════════════════════════════════════════════════════════════════════════

def _search_serper(query: str, num_results: int = 5) -> list[dict]:
    """Search via Serper.dev API (Google results)."""
    if not _SERPER_API_KEY:
        return []
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": _SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("organic", [])
        return [{"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
                for r in results[:num_results]]
    except Exception as e:
        log.warning("Serper search failed for '%s': %s", query, e)
        return []


def _search_duckduckgo(query: str, num_results: int = 5) -> list[dict]:
    """Search via DuckDuckGo HTML scraping (fallback)."""
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=10,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result"):
            title_el = r.select_one(".result__a")
            snippet_el = r.select_one(".result__snippet")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el.get("href", ""),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                })
            if len(results) >= num_results:
                break
        return results
    except Exception as e:
        log.warning("DuckDuckGo search failed for '%s': %s", query, e)
        return []


def _search_web(query: str, num_results: int = 5) -> list[dict]:
    """Search the web — Serper if available, DuckDuckGo fallback."""
    if _SERPER_API_KEY:
        results = _search_serper(query, num_results)
        if results:
            return results
    return _search_duckduckgo(query, num_results)


def _classify_source_type(url: str) -> str:
    """Classify URL as api_ref, docs, or marketing for fetch depth."""
    u = url.lower()
    if any(s in u for s in ["swagger", "openapi", "api-reference", "/api-docs", "redoc", "stoplight.io"]):
        return "api_ref"
    if any(s in u for s in ["docs.", "/docs/", "/documentation", "learn.", "/help/", "/reference/"]):
        return "docs"
    return "marketing"


_FETCH_DEPTH = {"marketing": 2500, "docs": 6000, "api_ref": 10000}


def _fetch_page_text(url: str, max_chars: int = 8000) -> str:
    """Fetch a web page and extract text content."""
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        return text[:max_chars]
    except Exception as e:
        log.warning("Failed to fetch %s: %s", url, e)
        return ""


def _fetch_page_html(url: str) -> str:
    """Fetch raw HTML for link scanning (domain-based detection)."""
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        return resp.text
    except Exception:
        return ""


def _run_searches_parallel(queries: list[tuple[str, str]], num_results: int = 5) -> dict[str, list[dict]]:
    """Run multiple search queries in parallel. Returns {key: [results]}."""
    results = {}
    from config import MAX_SEARCH_WORKERS
    with ThreadPoolExecutor(max_workers=MAX_SEARCH_WORKERS) as executor:
        futures = {
            executor.submit(_search_web, query, num_results): key
            for key, query in queries
        }
        for future in as_completed(futures, timeout=30):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                log.warning("Search failed for %s: %s", key, e)
                results[key] = []
    return results


def _fetch_pages_parallel(targets: list[tuple[str, str]], for_links: bool = False) -> dict[str, str]:
    """Fetch multiple pages in parallel. Returns {key: text_content}.

    If for_links=True, returns raw HTML for domain-based detection.
    """
    results = {}
    from config import MAX_FETCH_WORKERS
    with ThreadPoolExecutor(max_workers=MAX_FETCH_WORKERS) as executor:
        futures = {}
        for key, url in targets:
            if for_links:
                futures[executor.submit(_fetch_page_html, url)] = key
            else:
                source_type = _classify_source_type(url)
                depth = _FETCH_DEPTH.get(source_type, 2500)
                futures[executor.submit(_fetch_page_text, url, depth)] = key
        for future in as_completed(futures, timeout=30):
            key = futures[future]
            try:
                content = future.result()
                if content:
                    results[key] = content
            except Exception:
                pass
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Domain-Based Lab Platform Detection
# ═══════════════════════════════════════════════════════════════════════════════

def detect_lab_platforms_in_html(html_content: str) -> list[dict]:
    """Scan HTML for outbound links to known lab platform domains.

    URL links are stronger evidence than name mentions.
    Uses the competitor knowledge file for detection domains.
    """
    detections = []
    competitors = _COMPETITORS.get("competitors", [])

    for platform in competitors:
        domains = platform.get("detection_domains", [])
        signals = platform.get("detection_signals", [])
        found_urls = []
        found_mentions = []

        for domain in domains:
            if not domain:
                continue
            pattern = rf'https?://[^\s"\'<>]*{re.escape(domain)}[^\s"\'<>]*'
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            found_urls.extend(matches)

        if not found_urls:
            for signal in signals:
                if signal.lower() in html_content.lower():
                    found_mentions.append(signal)

        if found_urls or found_mentions:
            detections.append({
                "platform": platform.get("name", "Unknown"),
                "urls": list(set(found_urls)),
                "mentions": found_mentions,
                "evidence_type": "url" if found_urls else "mention",
                "is_skillable": platform.get("type") == "self",
            })

    return detections


# ═══════════════════════════════════════════════════════════════════════════════
# Product Family Scraping (for large portfolios)
# ═══════════════════════════════════════════════════════════════════════════════

_FAMILY_SKIP_EXACT = {
    # Generic site nav buttons that pass the product_keywords filter
    # because they're inside a product mega-menu, but aren't product
    # families themselves.
    "view all products", "all products", "view all", "see all", "browse all",
    "products", "solutions", "platform", "platforms", "services", "software",
    "search tips", "search", "clear", "filter", "filters", "sort",
    "demo", "request demo", "request a demo", "free trial", "get started",
    "learn more", "read more", "contact sales", "talk to sales",
    "sign in", "sign up", "log in", "log out",
}

_FAMILY_SKIP_TOKENS = {
    # Industry verticals — not product families
    "newsroom", "news", "press", "media",
    "government", "healthcare", "finance", "financial services", "retail",
    "manufacturing", "education", "energy", "utilities", "telecom",
    "industries", "verticals", "use cases",
    # Corporate / not-product
    "advanced research", "research center", "guardians", "professional services",
}


def _looks_like_product_family(text: str) -> bool:
    """Defensive filter for scraped homepage nav links.

    Returns True if `text` is plausibly a product family name. Filters out
    marketing copy, industry vertical labels, generic nav buttons, and
    long taglines that get scraped from product mega-menus.

    The route also filters out families with zero product matches as a
    second line of defense — see app.inspector_product_selection.
    """
    if not text:
        return False
    t = text.strip()
    # Length sanity — real family names are 1–4 words, ~2–35 chars
    if len(t) < 3 or len(t) > 45:
        return False
    if len(t.split()) > 5:
        return False
    # Marketing taglines often contain digits or percent signs
    if any(c.isdigit() for c in t) or "%" in t:
        return False
    # Exact-match denylist
    tl = t.lower()
    if tl in _FAMILY_SKIP_EXACT:
        return False
    # Token denylist (industry verticals, news labels, etc)
    for token in _FAMILY_SKIP_TOKENS:
        if token in tl:
            return False
    return True


def scrape_product_families(company_name: str) -> list[dict]:
    """Scrape company website navigation to extract product families.

    Returns [{"name": "Family Name", "url": "https://...", "product_count": N}].
    Used for large-portfolio companies to present a family picker.

    Two-stage filtering:
      1. Per-link sanity (_looks_like_product_family) catches obvious
         non-family text — marketing taglines, industry verticals, generic
         nav buttons. Runs in this scraper.
      2. Zero-product-match filter in the route discards any "family" that
         doesn't match a single discovered product. Runs in
         app.inspector_product_selection.
    """
    results = _search_web(f"{company_name} official website", num_results=3)
    homepage_url = None
    name_lower = company_name.lower().split()[0]
    for r in results:
        url = r.get("url", "")
        if name_lower in url.lower() and not any(s in url.lower() for s in ["linkedin", "wikipedia", "crunchbase"]):
            homepage_url = url
            break
    if not homepage_url and results:
        homepage_url = results[0].get("url", "")
    if not homepage_url:
        return []

    try:
        resp = requests.get(homepage_url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        log.warning("Failed to fetch homepage for %s: %s", company_name, e)
        return []

    families = []
    seen = set()
    product_keywords = {"product", "solution", "platform", "service", "software", "cloud", "suite"}
    skip_keywords = {"blog", "support", "contact", "career", "about", "investor", "press",
                     "login", "sign", "community", "pricing", "legal", "privacy", "terms"}

    for nav in soup.find_all(["nav", "header"]):
        for link in nav.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link.get("href", "").lower()
            if not _looks_like_product_family(text):
                continue
            if any(kw in href for kw in skip_keywords) or any(kw in text.lower() for kw in skip_keywords):
                continue
            parent_text = " ".join(p.get_text(" ", strip=True).lower()
                                   for p in link.parents if p.name in ("ul", "div", "li"))
            if any(kw in href for kw in product_keywords) or any(kw in parent_text[:200] for kw in product_keywords):
                if text not in seen:
                    full_url = link["href"]
                    if full_url.startswith("/"):
                        full_url = urljoin(homepage_url, full_url)
                    families.append({"name": text, "url": full_url})
                    seen.add(text)

    return families


# ═══════════════════════════════════════════════════════════════════════════════
# Company name resolution from product name
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_company_from_product(product_name: str) -> tuple[str, list[str]]:
    """Given a product name, identify the parent company."""
    results = _search_web(f'"{product_name}" company developer', num_results=3)
    if results:
        title = results[0].get("title", "")
        company = title.split(" - ")[0].split(" | ")[0].strip() if " - " in title or " | " in title else product_name
        return company, [product_name]
    return product_name, [product_name]


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: Discovery — broad research for product identification
# ═══════════════════════════════════════════════════════════════════════════════

def discover_products(company_name: str, known_products: Optional[list[str]] = None) -> dict:
    """Run discovery-depth research for a company.

    Searches for products, training programs, partner ecosystem, lab platforms,
    and contacts. Returns all raw findings for Claude to analyze.
    """
    queries = [
        ("product_discovery", f"{company_name} products software platform technology"),
        ("training_programs", f"{company_name} training certification program courses"),
        ("atp_signals", f"{company_name} authorized training partner learning partner ATP"),
        ("training_catalog", f"{company_name} training catalog course library academy"),
        ("partner_ecosystem", f"{company_name} partner program channel reseller ecosystem"),
        ("partner_portal", f"{company_name} partner portal technology alliance"),
        ("cs_signals", f"{company_name} customer success enablement onboarding"),
        ("lms_signals", f"{company_name} LMS learning management system Docebo Cornerstone"),
        ("org_contacts", f"{company_name} VP training education enablement certification LinkedIn"),
        # API presence at discovery — binary signal that bumps SaaS-only products
        # out of automatic Unlikely tier when the vendor has a public API surface.
        # Two queries (company-level developer portal + REST API surface) so the
        # discovery prompt has something to ground against for tier assignment.
        ("api_presence", f"{company_name} developer portal API documentation"),
        ("rest_api_check", f"{company_name} REST API public reference"),
    ]

    # Lab platform detection — Skillable + all competitors
    lab_queries = [
        ("lab_platform_signals", f"{company_name} hands-on labs virtual lab environment"),
    ]
    # Add Skillable-specific detection queries
    lab_queries.append(("skillable_signals", f"{company_name} labondemand.com OR learnondemandsystems.com OR Skillable OR \"Cloud Slice\""))

    # Competitor-specific queries
    for comp in _COMPETITORS.get("competitors", []):
        if comp.get("type") == "self":
            continue
        comp_name = comp.get("name", "").split("/")[0].strip()
        if comp_name:
            lab_queries.append((f"compete_{comp_name}", f"{company_name} {comp_name} labs"))

    all_queries = queries + lab_queries

    if known_products:
        for prod in known_products:
            all_queries.append((f"known_{prod}", f"{company_name} {prod} product features"))

    log.info("Discovery: running %d search queries for %s", len(all_queries), company_name)
    search_results = _run_searches_parallel(all_queries)

    # Fetch key pages for richer evidence
    pages_to_fetch = []

    # Company homepage
    prod_results = search_results.get("product_discovery", [])
    if prod_results:
        name_lower = company_name.lower().split()[0]
        for r in prod_results[:3]:
            url = r.get("url", "")
            if name_lower in url.lower():
                pages_to_fetch.append(("company_homepage", url))
                break

    # Training page
    train_results = search_results.get("training_programs", [])
    if train_results:
        pages_to_fetch.append(("training_page", train_results[0].get("url", "")))

    # ATP page
    atp_results = search_results.get("atp_signals", [])
    if atp_results:
        pages_to_fetch.append(("atp_page", atp_results[0].get("url", "")))

    # Partner portal
    partner_results = search_results.get("partner_portal", [])
    if partner_results:
        pages_to_fetch.append(("partner_portal_page", partner_results[0].get("url", "")))

    # Product pages (first 2 from product discovery)
    for i, r in enumerate(prod_results[:2]):
        pages_to_fetch.append((f"product_page_{i}", r.get("url", "")))

    page_contents = _fetch_pages_parallel(pages_to_fetch)

    # Domain-based lab platform detection on fetched pages
    pages_for_links = [(k, r.get("url", "")) for k, r in
                       [("homepage", prod_results[0] if prod_results else {}),
                        ("training", train_results[0] if train_results else {})]
                       if r.get("url")]
    raw_html = _fetch_pages_parallel(pages_for_links, for_links=True)
    all_html = "\n".join(raw_html.values())
    lab_platform_detections = detect_lab_platforms_in_html(all_html) if all_html else []

    return {
        "company_name": company_name,
        "search_results": search_results,
        "page_contents": page_contents,
        "lab_platform_detections": lab_platform_detections,
        "known_products": known_products or [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: Deep Product Research — per-product evidence for 8 dimensions
# ═══════════════════════════════════════════════════════════════════════════════

def research_products(company_name: str, selected_products: list[dict]) -> dict:
    """Run deep research on selected products.

    Gathers evidence for all Product Labability and Instructional Value dimensions.
    Returns research organized by product, ready for the scorer.
    """
    all_queries = []

    for product in selected_products:
        name = product.get("name", "")

        # ── Provisioning (Dimension 1.1) ──
        all_queries.extend([
            (f"tech_{name}", f"{name} deployment installation system requirements"),
            (f"deploy_{name}", f"{name} Azure Marketplace OR AWS Marketplace OR Docker Hub"),
            (f"docker_{name}", f"{name} Docker container image deployment"),
            (f"nfr_{name}", f"{name} NFR license developer trial free tier"),
        ])

        # ── Lab Access (Dimension 1.2) ──
        all_queries.extend([
            (f"api_{name}", f"{name} REST API documentation reference"),
            (f"openapi_{name}", f"{name} OpenAPI swagger API specification"),
            (f"api_auth_{name}", f"{name} API authentication SSO SAML Entra OAuth"),
            (f"api_lifecycle_{name}", f"{name} API create delete provision tenant account"),
            # Learner Isolation signals — per-user / per-tenant isolation capability.
            # Independent of SaaS classification; even SaaS products can have rich
            # per-user provisioning APIs that pass the isolation gate.
            (f"per_tenant_{name}", f"{name} per-tenant provisioning API multi-tenant create endpoint"),
            (f"sandbox_tenant_{name}", f"{name} sandbox tenant developer account isolated"),
            # Identity API signal — vendor API for user/role creation per learner.
            (f"identity_{name}", f"{name} user provisioning API role assignment RBAC"),
            # Cred Recycling signal — credentials reset and reusable between learners.
            (f"cred_recycle_{name}", f"{name} credential reset reuse account recycling"),
            # Training License signal — NFR / training / eval / dev license tier.
            (f"training_license_{name}", f"{name} NFR training license eval developer non-production tier"),
        ])

        # ── Scoring (Dimension 1.3) ──
        all_queries.extend([
            (f"api_state_{name}", f"{name} API GET configuration state query validate"),
            (f"cli_{name}", f"{name} CLI command line PowerShell Bash administration"),
        ])

        # ── Teardown (Dimension 1.4) ──
        all_queries.extend([
            (f"sandbox_{name}", f"{name} sandbox environment teardown cleanup delete API"),
        ])

        # ── Provisioning friction signals ──
        # Detect specific friction conditions that warrant friction badges
        # alongside the green canonical: GPU requirements, slow cluster init
        # (Pre-Instancing opportunity), nested virtualization (ESX evidence).
        all_queries.extend([
            (f"gpu_{name}", f"{name} GPU requirement CUDA hardware acceleration"),
            (f"init_time_{name}", f"{name} initialization time first launch cluster startup performance"),
            (f"nested_virt_{name}", f"{name} nested virtualization hypervisor ESX vSphere"),
        ])

        # ── Cloud preference signal (when product runs on Azure AND AWS) ──
        # Detect vendor preference between clouds so the AI can pick the right
        # canonical badge. Defaults to Azure when no preference signal found.
        all_queries.extend([
            (f"cloud_pref_{name}", f"{name} Azure AWS preferred cloud partnership marketplace"),
        ])

        # ── Product Complexity (Dimension 2.1) ──
        all_queries.extend([
            (f"docs_{name}", f"{name} documentation modules features configuration guide"),
            (f"ai_{name}", f"{name} AI machine learning artificial intelligence features"),
        ])

        # ── Mastery Stakes (Dimension 2.2) ──
        all_queries.extend([
            (f"stakes_{name}", f"{name} misconfiguration risk security breach compliance failure"),
        ])

        # ── Lab Versatility (Dimension 2.3) + Market Demand (Dimension 2.4) ──
        all_queries.extend([
            (f"train_{name}", f"{name} training certification hands-on lab"),
            (f"compete_{name}", f"{name} hands-on lab CloudShare OR Instruqt OR Skillable"),
            (f"marketplace_{name}", f"{name} marketplace integrations ecosystem"),
        ])

        # ── Popularity signals (Stack Overflow + GitHub) ──
        # These inform estimated_user_base and Market Demand evidence.
        all_queries.extend([
            (f"so_{name}", f"site:stackoverflow.com {name} tagged questions"),
            (f"gh_{name}", f"site:github.com {name} stars repository"),
        ])

    log.info("Deep research: running %d queries for %d products",
             len(all_queries), len(selected_products))
    search_results = _run_searches_parallel(all_queries)

    # Fetch key pages per product
    pages_to_fetch = []
    for product in selected_products:
        name = product.get("name", "")
        for key_prefix in [name, f"docs_{name}", f"api_{name}", f"openapi_{name}", f"api_lifecycle_{name}", f"train_{name}"]:
            results = search_results.get(key_prefix, [])
            if results:
                url = results[0].get("url", "")
                if url:
                    pages_to_fetch.append((key_prefix, url))

    page_contents = _fetch_pages_parallel(pages_to_fetch)

    return {
        "company_name": company_name,
        "selected_products": selected_products,
        "search_results": search_results,
        "page_contents": page_contents,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar 1 Fact Extraction — Research → Store layer
#
# Truth-only structured extraction.  Reads raw search results + fetched pages
# for one product and produces a ProductLababilityFacts dataclass.  No
# scoring, no badging, no Skillable interpretation — just typed primitives
# describing what the product IS.
#
# Per Frank 2026-04-07: "We're storing facts that have enough context to be
# scored later."  The prompt below describes the schema and demands JSON
# matching it exactly; downstream Pillar 1 scoring (Step 3) is a pure-Python
# lookup against these primitives.
# ═══════════════════════════════════════════════════════════════════════════════

_PRODUCT_LABABILITY_FACTS_PROMPT = """You are a research analyst extracting structured facts about a software product so they can be scored later by a separate system.

IMPORTANT: For non-software organizations (universities, GSIs, Industry Authorities, training companies), the "product" name you receive may be a degree program, practice area, or certification. Product Labability applies to the UNDERLYING TECHNOLOGY, not the wrapper. If you receive "BS in Cybersecurity" as the product, research the labability of the technologies taught in that program (Wireshark, Kali Linux, Splunk, etc.) — not the degree program itself. If you receive "SAP Practice" from a GSI, research SAP S/4HANA's labability.

Your job is TRUTH ONLY.  You are not scoring, not classifying as good/bad, not picking winners.  You are extracting typed facts about how the product can be deployed, how learners log in, how state can be validated, and how cleanup works.

Return a JSON object with EXACTLY this shape (no extra keys, no commentary, no markdown):

{
  "provisioning": {
    "description": "<1-3 sentence narrative of the product's deployment shape>",
    "runs_as_installable": <bool>,
    "runs_as_azure_native": <bool>,
    "runs_as_aws_native": <bool>,
    "runs_as_container": <bool>,
    "runs_as_saas_only": <bool>,
    "supported_host_os": [<"windows" and/or "linux">],
    "has_sandbox_api": <bool>,
    "sandbox_api_granularity": "<rich|partial|none>",
    "is_multi_vm_lab": <bool>,
    "has_complex_topology": <bool>,
    "is_large_lab": <bool>,
    "has_pre_instancing_opportunity": <bool>,
    "needs_gpu": <bool>,
    "needs_bare_metal": <bool>,
    "needs_gcp": <bool>,
    "m365_scenario": "<end_user|administration|>",
    "preferred_fabric": "<hyper_v|vm|container|azure|aws|sandbox_api|m365_tenant|m365_admin|simulation|gcp|>",
    "preferred_fabric_rationale": "<1-2 sentence explanation of why this fabric is preferred>",
    "vm_is_resource_intensive": <bool>,
    "vm_has_premium_cost_profile": <bool>,
    "vm_footprint_notes": "<narrative: 'Standard Hyper-V profile' or 'Requires 16vCPU + 64GB + GPU' etc.>",
    "container_is_production_native": <bool>,
    "container_is_dev_only": <bool>,
    "container_needs_windows_gui": <bool>,
    "container_needs_multi_vm_network": <bool>,
    "container_footprint_notes": "<narrative about container capabilities or limitations>",
    "requires_esx": <bool>,
    "requires_esx_reason": "<1-sentence specific constraint if requires_esx is true>"
  },
  "lab_access": {
    "description": "<1-3 sentence narrative of how learners actually authenticate>",
    "user_provisioning_api_granularity": "<rich|partial|none>",
    "auth_model": "<entra_native_tenant|entra_msft_id|sso_saml|sso_oidc|oauth|product_credentials|api_key|none>",
    "credential_lifecycle": "<recyclable|pool_only|none>",
    "learner_isolation": "<confirmed|unknown|absent>",
    "training_license": "<low_friction|medium_friction|blocked|none>",
    "has_mfa_blocker": <bool>,
    "has_anti_automation": <bool>,
    "has_rate_limit_blocker": <bool>
  },
  "scoring": {
    "description": "<1-3 sentence narrative of state-validation surfaces>",
    "state_validation_api_granularity": "<rich|partial|none>",
    "scriptable_via_shell_granularity": "<full|partial|none>",
    "gui_state_visually_evident_granularity": "<full|partial|none>",
    "simulation_scoring_viable": <bool>
  },
  "teardown": {
    "description": "<1-3 sentence narrative of vendor-side cleanup capabilities>",
    "vendor_teardown_api_granularity": "<rich|partial|none>",
    "has_orphan_risk": <bool>
  }
}

═══ FIELD GUIDANCE ═══

provisioning.runs_as_*: how the product can ACTUALLY be deployed BY A LEARNER for hands-on lab work. This is NOT about how the vendor runs their own infrastructure — it is about whether a learner (via a lab environment) can stand up their own instance.

  - runs_as_installable: TRUE when a learner can install the product on their own VM (Hyper-V, ESX, etc.) from vendor-published installers / images.
  - runs_as_container: TRUE when the vendor publishes a production-ready container image a learner can pull and run themselves.
  - runs_as_azure_native: TRUE when a LEARNER can spin up their own instance on Azure — for example, a published Azure Marketplace offer, an ARM template, or clear documentation for learner-driven Azure deployment. NOT true just because the vendor happens to host their SaaS on Azure.
  - runs_as_aws_native: TRUE when a LEARNER can spin up their own instance on AWS — AWS Marketplace AMI, CloudFormation template, or clear learner-driven deployment path. NOT true just because the vendor happens to host their SaaS on AWS.
  - runs_as_saas_only: TRUE when the ONLY way to use the product is the vendor's hosted managed service — the learner cannot install, containerize, or cloud-deploy their own instance. The vendor runs it for the customer as a service.

  HARD CONTRADICTION RULE: runs_as_saas_only=true is mutually exclusive with runs_as_installable, runs_as_container, runs_as_azure_native, and runs_as_aws_native. If runs_as_saas_only is true, ALL FOUR of the others MUST be false. A managed-service SaaS product that "runs on AWS under the hood" is STILL runs_as_saas_only=true with runs_as_aws_native=false — the learner has no path into the vendor's AWS account. Only set runs_as_aws_native / runs_as_azure_native when there is documented, learner-accessible deployment into THEIR OWN cloud account.

  Multiple NON-saas values may be true together (e.g. an installable product that also publishes a Docker image is runs_as_installable=true AND runs_as_container=true).

provisioning.sandbox_api_granularity: does the product expose an API that can spin up an isolated sandbox/tenant on demand?
  - "rich"    = full create/configure/delete cycle
  - "partial" = some endpoints but missing pieces (e.g. create works, delete doesn't)
  - "none"    = no documented sandbox provisioning API

provisioning.has_pre_instancing_opportunity: true ONLY when documentation explicitly indicates slow first-launch, slow cluster initialization, or slow tenant warm-up that would benefit from pre-warming environments.

provisioning.m365_scenario: classify Microsoft 365 dependency.
  - "end_user"       = product is Microsoft 365 End User scenario (Word, Excel, Teams, SharePoint, PowerBI, OneDrive, Outlook, OneNote training). Skillable has an automated M365 End User solution (E3/E5/E7 tiers) that handles this without credit card / MFA friction for learners.
  - "administration" = product is Microsoft 365 Administration scenario (Intune admin, Defender admin, Purview admin, Entra admin, anything requiring Global Administrator tenant access). Higher friction — requires MOC-provided tenant or learner-signed-up M365 Trial account.
  - ""               = product has no direct M365 dependency. Leave empty.
  Read the product description carefully — if the learning objectives involve Microsoft 365 apps or administering M365, classify accordingly.

provisioning.preferred_fabric: the fabric best matched to this product, based on multi-factor analysis (NOT just vendor marketing). Decision tree:
  1. Default to "hyper_v" (VM) for installable products — gives lab developers the most control and easiest scoring.
  2. Lean "azure" or "aws" when: (a) the VM footprint would be resource-intensive (set vm_is_resource_intensive=true), (b) the VM profile is meaningfully more expensive than cloud (vm_has_premium_cost_profile=true), OR (c) the vendor strongly prefers cloud in their marketing.
  3. Use "container" only when container is production-native AND no disqualifiers fire (see container_* fields).
  4. Use "m365_tenant" or "m365_admin" when m365_scenario is set.
  5. Use "sandbox_api" when the product is SaaS-only AND has a rich provisioning API.
  6. Use "simulation" only as last resort.
  7. Only use vendor marketing preference as a TIEBREAKER when technical analysis is neutral.
  Leave empty if you can't determine the preferred fabric with confidence.

provisioning.preferred_fabric_rationale: 1-2 sentences explaining WHY this fabric is preferred. Example: "Cisco Meraki is installable on a Hyper-V appliance, and the VM is lightweight (single small VM). Lab developers get full control over the network topology this way."

provisioning.vm_is_resource_intensive: true when the product would need a BIG VM (16+ vCPUs, 32GB+ RAM, specialized hardware). Normal small VMs stay false. This is a FACT about the product, not a judgment about VMs being bad.

provisioning.vm_has_premium_cost_profile: true when the VM footprint is meaningfully more expensive than the cloud alternative. Most products stay false.

provisioning.vm_footprint_notes: free-text narrative describing the VM profile. "Standard Hyper-V profile" for normal products. "Requires 16vCPU + 64GB RAM + GPU" for resource-intensive ones. "Premium licensing adds cost" for high-cost cases.

provisioning.container_is_production_native: true when the vendor publishes this product as a production-ready container (not just a dev image). Positive signal when true. Does NOT count as anti-signal when false.

provisioning.container_is_dev_only: true when the published image is labeled "for development only," "not for production," "demo use only," or equivalent. Disqualifier for container viability.

provisioning.container_needs_windows_gui: true when the product requires a Windows desktop GUI to use. Container GUI support is limited — this disqualifies container as a viable fabric.

provisioning.container_needs_multi_vm_network: true when the product requires multi-VM networking (segmentation, firewalls between VMs). Container isolation doesn't support this — disqualifier.

provisioning.container_footprint_notes: free-text narrative about what the container provides or the specific disqualifier reason if any apply.

provisioning.requires_esx: true when there's a specific technical constraint forcing VMware ESX over Hyper-V (nested virtualization required for hypervisor training scenarios, socket licensing above 24 vCPUs, legacy vSphere dependency). Most products stay false.

provisioning.requires_esx_reason: 1-sentence specific constraint when requires_esx is true. Example: "Nested virtualization required for hypervisor training scenarios — Hyper-V doesn't support nested virt."

lab_access.auth_model: how the END USER authenticates to the running product.
  - "entra_native_tenant" — Skillable provisions in a controlled Entra tenant; in-lab username + password are displayed
  - "entra_msft_id"       — Product accepts the learner's own personal/work Microsoft account
  - "sso_saml" / "sso_oidc" — Generic SAML / OIDC SSO
  - "oauth"               — OAuth flow (rare for human login)
  - "product_credentials" — Product manages its own user database; per-learner accounts are created inside the product
  - "api_key"             — Auth is via API key (developer-tool products)
  - "none"                — No documented auth model

lab_access.user_provisioning_api_granularity: does the vendor expose an API to create per-learner users / roles?
  - "rich"    = CONFIRMED: documented endpoints exist for creating users, assigning roles, AND managing lifecycle (update/delete) — with evidence from API reference docs, OpenAPI specs, or developer guides. If you cannot find specific endpoint documentation, this is NOT rich.
  - "partial" = API exists but coverage is UNCERTAIN or incomplete — some endpoints documented but gaps in lifecycle management, undocumented areas, or you found general API mention without specific user-provisioning endpoint evidence. DEFAULT TO THIS when the product has an API but you cannot confirm full user lifecycle coverage.
  - "none"    = no documented user provisioning API at all

  CRITICAL: For SaaS products, "partial" is the honest default unless you find SPECIFIC user-provisioning endpoint documentation. Finding a general REST API or admin console does NOT qualify as "rich" — that's "partial" until confirmed.

lab_access.credential_lifecycle:
  - "recyclable" — credentials can be reset and reused between learners
  - "pool_only"  — a pool of accounts must be reused; no per-learner reset
  - "none"       — no documented lifecycle

lab_access.learner_isolation: can two learners run side-by-side without seeing each other's data?
  - "confirmed" — explicitly documented
  - "unknown"   — not documented either way
  - "absent"    — explicitly shared / single-tenant only

lab_access.training_license: what's the friction to get a non-production / NFR / training license?
  - "low_friction"    — public NFR / dev tier / free trial available
  - "medium_friction" — partner / signup required
  - "blocked"         — no path documented
  - "none"            — N/A (e.g. open-source)

scoring.*_granularity: state-validation surfaces.  rich/full means broad coverage; partial means some areas; none means absent.  These are PRODUCT capabilities — not whether a particular lab uses them.

scoring.simulation_scoring_viable: would a simulation-based lab be a credible alternative for this product (true ONLY for products where the real thing is impossible to provision and the workflows could be faithfully reproduced).

teardown.vendor_teardown_api_granularity: only relevant when the product runs as SaaS / cloud-only.  For installable / container / Hyper-V products, datacenter snapshot teardown handles cleanup automatically and this field can be "none" without penalty downstream.

teardown.has_orphan_risk: true when there's documented risk of resources being left behind (orphaned tenants, dangling licenses, unbilled resources) after a learner session ends.

═══ TRUTH DISCIPLINE ═══

If the research doesn't say, use the conservative neutral value (false / "none" / "unknown").  Do not guess.  Do not apply your own knowledge of the product — use ONLY the research provided.  If a field cannot be determined from the research, leave it at the neutral default rather than fabricating.

Return ONLY the JSON object.  No prose, no markdown, no code fence."""


def _build_pillar_1_fact_context(
    name: str,
    search_results: dict,
    page_contents: dict,
    underlying_technologies: list[dict] | None = None,
) -> str:
    """Build the per-product research context for Pillar 1 fact extraction.

    Mirrors `scorer._build_product_context` shape so the AI sees the same
    raw research the legacy scoring path sees — but only the search keys
    relevant to Pillar 1 dimensions (provisioning, lab access, scoring,
    teardown).  Pillar 2 / Pillar 3 keys are intentionally excluded.

    For wrapper org products (certs, degrees, courses, practice areas),
    `underlying_technologies` provides the specific technologies inside
    the wrapper. The fact extractor should assess labability based on
    THESE technologies, not the wrapper's delivery mechanism.
    """
    lines = [f"# Research for: {name}"]

    # When the product is a wrapper (cert, degree, course), inject the
    # underlying technologies so the AI researches THOSE for labability.
    if underlying_technologies:
        lines.append("")
        lines.append("## WRAPPER PRODUCT — ASSESS UNDERLYING TECHNOLOGIES")
        lines.append(f"'{name}' is a wrapper (cert program / degree / course / practice area).")
        lines.append("The labability assessment must be based on the UNDERLYING TECHNOLOGIES")
        lines.append("taught inside this wrapper, NOT the wrapper's own delivery mechanism.")
        lines.append("The deployment_model should reflect how these technologies can be")
        lines.append("provisioned for hands-on labs (installable, cloud, hybrid), NOT the")
        lines.append("cert/course delivery platform (which is irrelevant to lab provisioning).")
        lines.append("")
        lines.append("Technologies inside this wrapper:")
        for tech in underlying_technologies:
            t_name = tech.get("name", "")
            t_deploy = tech.get("deployment_model", "")
            t_note = tech.get("note", "")
            lines.append(f"  - {t_name} ({t_deploy}): {t_note}")
        lines.append("")

    pillar_1_keys = [
        f"tech_{name}", f"deploy_{name}", f"docker_{name}", f"nfr_{name}",
        f"api_{name}", f"openapi_{name}", f"api_auth_{name}", f"api_lifecycle_{name}",
        f"per_tenant_{name}", f"sandbox_tenant_{name}", f"identity_{name}",
        f"cred_recycle_{name}", f"training_license_{name}",
        f"api_state_{name}", f"cli_{name}",
        f"sandbox_{name}",
        f"gpu_{name}", f"init_time_{name}", f"nested_virt_{name}", f"cloud_pref_{name}",
    ]
    for key in pillar_1_keys:
        for r in search_results.get(key, []):
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            lines.append(f"- **{title}** ({url}): {snippet}")

    page_key_labels = [
        (name, "Documentation"),
        (f"api_{name}", "API Reference"),
        (f"openapi_{name}", "OpenAPI / Swagger Spec"),
        (f"api_lifecycle_{name}", "API Lifecycle Docs"),
        (f"docs_{name}", "Docs Page"),
    ]
    for key, label in page_key_labels:
        if key in page_contents:
            lines.append(f"\n### {label}:")
            lines.append(page_contents[key])

    return "\n".join(lines)


def _coerce_facts_dict_to_dataclass(raw: dict) -> ProductLababilityFacts:
    """Parse the JSON the model returned into the typed dataclass.

    Defensive: drops unknown keys, supplies neutral defaults for missing
    keys, never raises on field-shape mismatch.  This keeps a single bad
    Claude response from blowing up the whole research run.
    """
    def _str(v) -> str: return str(v) if v is not None else ""
    def _bool(v) -> bool: return bool(v) if v is not None else False
    def _list_str(v) -> list:
        return [str(x) for x in v] if isinstance(v, list) else []

    prov_raw = raw.get("provisioning", {}) or {}
    provisioning = ProvisioningFacts(
        description=_str(prov_raw.get("description")),
        runs_as_installable=_bool(prov_raw.get("runs_as_installable")),
        runs_as_azure_native=_bool(prov_raw.get("runs_as_azure_native")),
        runs_as_aws_native=_bool(prov_raw.get("runs_as_aws_native")),
        runs_as_container=_bool(prov_raw.get("runs_as_container")),
        runs_as_saas_only=_bool(prov_raw.get("runs_as_saas_only")),
        supported_host_os=_list_str(prov_raw.get("supported_host_os")),
        has_sandbox_api=_bool(prov_raw.get("has_sandbox_api")),
        sandbox_api_granularity=_str(prov_raw.get("sandbox_api_granularity")),
        is_multi_vm_lab=_bool(prov_raw.get("is_multi_vm_lab")),
        has_complex_topology=_bool(prov_raw.get("has_complex_topology")),
        is_large_lab=_bool(prov_raw.get("is_large_lab")),
        has_pre_instancing_opportunity=_bool(prov_raw.get("has_pre_instancing_opportunity")),
        needs_gpu=_bool(prov_raw.get("needs_gpu")),
        needs_bare_metal=_bool(prov_raw.get("needs_bare_metal")),
        needs_gcp=_bool(prov_raw.get("needs_gcp")),
        # Frank 2026-04-08 additions
        m365_scenario=_str(prov_raw.get("m365_scenario")),
        preferred_fabric=_str(prov_raw.get("preferred_fabric")),
        preferred_fabric_rationale=_str(prov_raw.get("preferred_fabric_rationale")),
        vm_is_resource_intensive=_bool(prov_raw.get("vm_is_resource_intensive")),
        vm_has_premium_cost_profile=_bool(prov_raw.get("vm_has_premium_cost_profile")),
        vm_footprint_notes=_str(prov_raw.get("vm_footprint_notes")),
        container_is_production_native=_bool(prov_raw.get("container_is_production_native")),
        container_is_dev_only=_bool(prov_raw.get("container_is_dev_only")),
        container_needs_windows_gui=_bool(prov_raw.get("container_needs_windows_gui")),
        container_needs_multi_vm_network=_bool(prov_raw.get("container_needs_multi_vm_network")),
        container_footprint_notes=_str(prov_raw.get("container_footprint_notes")),
        requires_esx=_bool(prov_raw.get("requires_esx")),
        requires_esx_reason=_str(prov_raw.get("requires_esx_reason")),
    )

    la_raw = raw.get("lab_access", {}) or {}
    lab_access = LabAccessFacts(
        description=_str(la_raw.get("description")),
        user_provisioning_api_granularity=_str(la_raw.get("user_provisioning_api_granularity")),
        auth_model=_str(la_raw.get("auth_model")),
        credential_lifecycle=_str(la_raw.get("credential_lifecycle")),
        learner_isolation=_str(la_raw.get("learner_isolation")),
        training_license=_str(la_raw.get("training_license")),
        has_mfa_blocker=_bool(la_raw.get("has_mfa_blocker")),
        has_anti_automation=_bool(la_raw.get("has_anti_automation")),
        has_rate_limit_blocker=_bool(la_raw.get("has_rate_limit_blocker")),
    )

    sc_raw = raw.get("scoring", {}) or {}
    scoring = ScoringFacts(
        description=_str(sc_raw.get("description")),
        state_validation_api_granularity=_str(sc_raw.get("state_validation_api_granularity")),
        scriptable_via_shell_granularity=_str(sc_raw.get("scriptable_via_shell_granularity")),
        gui_state_visually_evident_granularity=_str(sc_raw.get("gui_state_visually_evident_granularity")),
        simulation_scoring_viable=_bool(sc_raw.get("simulation_scoring_viable")),
    )

    td_raw = raw.get("teardown", {}) or {}
    teardown = TeardownFacts(
        description=_str(td_raw.get("description")),
        vendor_teardown_api_granularity=_str(td_raw.get("vendor_teardown_api_granularity")),
        has_orphan_risk=_bool(td_raw.get("has_orphan_risk")),
    )

    return ProductLababilityFacts(
        provisioning=provisioning,
        lab_access=lab_access,
        scoring=scoring,
        teardown=teardown,
    )


def extract_product_labability_facts(
    product_name: str,
    search_results: dict,
    page_contents: dict,
    underlying_technologies: list[dict] | None = None,
) -> ProductLababilityFacts:
    """Extract Pillar 1 facts for one product from raw research.

    Builds a focused context (Pillar 1 search keys + relevant fetched
    pages), calls Claude with the truth-only fact-extraction prompt, and
    parses the JSON response into a ProductLababilityFacts dataclass.

    On any failure (API error, parse error, missing fields), returns an
    empty ProductLababilityFacts so the research run never crashes — the
    Pillar 1 scorer (Step 3) will treat empty fields as neutral defaults
    and surface that as a low-confidence dimension downstream.

    NOTE: imports `_call_claude` from scorer at call time to avoid an
    import cycle that would otherwise form once Step 5 lands.  Both
    modules are in the Intelligence layer per CLAUDE.md, and `_call_claude`
    is shared infrastructure — see Step 5 follow-up to extract it to a
    dedicated llm_client module if the cycle bites.
    """
    from scorer import _call_claude  # local import to avoid early cycle
    context = _build_pillar_1_fact_context(
        product_name, search_results, page_contents,
        underlying_technologies=underlying_technologies,
    )
    log.info("Pillar 1 fact extraction starting for %s", product_name)
    try:
        raw = _call_claude(
            _PRODUCT_LABABILITY_FACTS_PROMPT,
            context,
            max_tokens=4000,
        )
    except Exception as e:
        log.warning("Pillar 1 fact extraction Claude call failed for %s: %s", product_name, e)
        return ProductLababilityFacts()
    return _coerce_facts_dict_to_dataclass(raw)


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar 2 Fact Extraction — Instructional Value
#
# Truth-only extraction.  Reads the same per-product raw research used by the
# Pillar 1 extractor but looks at different signals and produces a different
# shape — mostly qualitative SignalEvidence dicts plus concrete numeric facts
# for Market Demand (install base, employee subset, cert sit rate).
#
# Per Frank 2026-04-07: no `strength` field in SignalEvidence.  Strength is
# interpretation and belongs in the scoring layer.  The observation field
# captures the raw fact with enough context for downstream judgment.
# ═══════════════════════════════════════════════════════════════════════════════

# Canonical signal category lists pulled from scoring_config at module load.
# Define-Once: the rubric in scoring_config owns the vocabulary; research
# reads it so Claude can only emit categories the scoring layer understands.
def _load_canonical_signal_categories() -> dict[str, tuple[str, ...]]:
    """Load canonical signal_category tuples per Pillar 2 dimension from config."""
    try:
        import scoring_config as cfg
        out: dict[str, tuple[str, ...]] = {}
        for pillar in cfg.PILLARS:
            if pillar.name != "Instructional Value":
                continue
            for dim in pillar.dimensions:
                key = dim.name.lower().replace(" ", "_")
                rubric = getattr(dim, "rubric", None)
                cats = getattr(rubric, "signal_categories", ()) if rubric else ()
                out[key] = tuple(cats)
        return out
    except Exception as e:
        log.warning("Could not load Pillar 2 signal categories from scoring_config: %s", e)
        return {}


_P2_SIGNAL_CATEGORIES = _load_canonical_signal_categories()


def _format_category_list(key: str) -> str:
    """Render a canonical category tuple as a comma-separated prompt fragment."""
    cats = _P2_SIGNAL_CATEGORIES.get(key, ())
    if not cats:
        return "(categories unavailable — use your best judgment)"
    return ", ".join(cats)


_INSTRUCTIONAL_VALUE_FACTS_PROMPT = f"""You are a research analyst extracting structured facts about whether a software product warrants hands-on training.

Your job is TRUTH ONLY.  You are NOT scoring, NOT classifying as good/bad, NOT picking winners, NOT applying any Skillable framework.  You are extracting observable facts about how complex the product is, what the stakes of getting it wrong are, what kinds of hands-on experiences the product naturally supports, and how big the worldwide market for training on it is.

Return a JSON object with EXACTLY this shape (no extra keys, no commentary, no markdown):

{{
  "product_complexity": {{
    "description": "<1-3 sentence narrative of how complex this product is to use and administer>",
    "signals": {{
      "<signal_category>": {{
        "present": <bool>,
        "observation": "<concrete one-sentence fact from the research>",
        "source_url": "<url>",
        "confidence": "<confirmed|indicated|inferred>"
      }}
    }}
  }},
  "mastery_stakes": {{
    "description": "<1-3 sentence narrative of the consequences of getting this product wrong>",
    "signals": {{
      "<signal_category>": {{
        "present": <bool>,
        "observation": "<concrete one-sentence fact>",
        "source_url": "<url>",
        "confidence": "<confirmed|indicated|inferred>"
      }}
    }}
  }},
  "lab_versatility": {{
    "description": "<1-3 sentence narrative of what kinds of hands-on experiences this product naturally supports>",
    "signals": {{
      "<signal_category>": {{
        "present": <bool>,
        "observation": "<concrete one-sentence fact>",
        "source_url": "<url>",
        "confidence": "<confirmed|indicated|inferred>"
      }}
    }}
  }},
  "market_demand": {{
    "description": "<1-3 sentence narrative of the worldwide market for training on this product>",
    "install_base": {{
      "value": <int or null>,
      "source_url": "<url>",
      "confidence": "<confirmed|indicated|inferred>",
      "notes": "<any unusual context>"
    }},
    "employee_subset_size": {{
      "value": <int or null>,
      "source_url": "<url>",
      "confidence": "<confirmed|indicated|inferred>",
      "notes": ""
    }},
    "cert_annual_sit_rate": {{
      "value": <int or null>,
      "source_url": "<url>",
      "confidence": "<confirmed|indicated|inferred>",
      "notes": ""
    }},
    "cert_bodies_mentioning": [<"CompTIA", "EC-Council", "SANS", etc.>],
    "independent_training_course_counts": {{<"Pluralsight": <int>, "Coursera": <int>, "LinkedIn Learning": <int>, "Udemy": <int>>}},
    "is_ai_powered": <bool>,
    "is_ai_platform": <bool>,
    "signals": {{
      "<signal_category>": {{
        "present": <bool>,
        "observation": "<concrete one-sentence fact>",
        "source_url": "<url>",
        "confidence": "<confirmed|indicated|inferred>"
      }}
    }}
  }}
}}

═══ CANONICAL SIGNAL CATEGORIES ═══

Use ONLY the signal category names listed below for each dimension.  If a signal doesn't match any canonical name, leave it out.  Do not invent new category names.

**product_complexity signals:** {_format_category_list("product_complexity")}

**mastery_stakes signals:** {_format_category_list("mastery_stakes")}

**lab_versatility signals:** {_format_category_list("lab_versatility")}

**market_demand signals:** {_format_category_list("market_demand")}

═══ FIELD GUIDANCE ═══

**description:** 1-3 sentences summarizing the dimension — what the research reveals about THIS product for THIS dimension.  Descriptive, not evaluative.

**signals:** one entry per signal you actually found evidence for.  Do NOT emit a signal you didn't see evidence for.  Missing signals are fine — leave the key out entirely.

**observation:** a concrete, specific one-sentence fact grounded in the research.  Not "the product is complex" — "the admin console has 12 top-level modules with 40+ configuration options each."  Not "stakes are high" — "a misconfigured policy can expose sensitive data to unauthorized users, reported in CVE-2024-XXXXX."

**source_url:** the URL the evidence came from.  Empty string if synthesized from multiple sources.

**confidence:**
  - "confirmed" = direct evidence from a primary source (vendor docs, official announcements)
  - "indicated" = strong indirect evidence across multiple signals
  - "inferred" = pattern-based / category norms / limited signals

**Market Demand numeric fields — CRITICAL for ACV Potential calculation.**

These fields feed the ACV math directly — they are the AUDIENCE for three of the five consumption motions. The ACV calculation uses population × adoption_pct × hours × rate per motion. SINGLE ESTIMATED NUMBER for each — not a range. One number the seller can quote. Better to be approximately right than precisely uncertain. A range like "2,000–40,000" signals "we have no idea" and is FORBIDDEN.

  - **install_base** → ACV Motion 1 (Customer Training). The TRAINING POPULATION for THIS product — people who would realistically take HANDS-ON TRAINING, not everyone who logs in. This is the critical distinction:
    - For ADMIN/CONFIG TOOLS (Workday HCM, ServiceNow, Salesforce admin): count ADMINISTRATORS and CONFIGURATORS who need deep hands-on skills, NOT end users who just log in to view their paycheck or submit a ticket. Workday HCM may have 10M end users but only ~50K HR admins/configurators who would take training.
    - For SECURITY TOOLS (Splunk, CrowdStrike): count security professionals/analysts who operate the tool.
    - For DEVELOPER TOOLS (Terraform, Kubernetes): count practitioners who need hands-on depth.
    - For GENERAL-PURPOSE TOOLS (Microsoft 365): count the full user base — everyone benefits from training.
    NOT customer accounts (Tanium has ~4,000 customer accounts but ~50,000 security professionals who use it). NOT how many people know about the vendor. Count the PRACTITIONERS, not the logos. Includes people who train through ATPs — they are customers, not partners. Do NOT double-count them in partner training. Single number.
    **CRITICAL FOR WRAPPER ORG TYPES (GSIs, universities, training orgs, VARs, distributors):**
    The install_base is THIS ORGANIZATION's audience for this practice area — NOT the underlying technology's global user base. For Accenture's "AWS Practice," the install_base is Accenture's own AWS consultants (~60K) plus client technical staff they train on AWS — NOT the 4 million AWS practitioners worldwide. For a university's "BS Cybersecurity," it's the students enrolled in that program (~500) — NOT all cybersecurity professionals globally. The question is always: "how many people does THIS ORGANIZATION train on this topic?"
    FOR UNIVERSITIES: students enrolled in technology-facing programs THIS YEAR, not total enrollment. FOR INDUSTRY AUTHORITIES: training candidates per year (people interested in taking the cert), not lifetime cert holders. FOR GSIs/VARs/DISTRIBUTORS: practitioners in THIS practice area at THIS company, plus client staff they hand off to — not the underlying technology's worldwide audience.

  - **employee_subset_size** → ACV Motion 3 (Employee Training). People at the COMPANY BEING ANALYZED whose job involves meaningfully using or supporting THIS product — product team, SEs, support engineers, customer success, trainers. NOT people at customer companies (those are install_base users in Motion 1). NOT total company headcount. For a cybersecurity vendor with 3,000 employees: maybe 500-800 are in product-facing roles (engineering, SE, support, CS). For a large enterprise like Microsoft: the Azure team might be 5,000-10,000 people. This is always a SMALL number relative to company size. A single estimated number, not a range. If uncertain, estimate conservatively — better to undercount than to inflate.

  - **cert_annual_sit_rate** → ACV Motion 4 (Certification / PBT). People who ACTUALLY SIT FOR THE EXAM each year — the smallest number in the funnel. NOT the training candidate population (that goes in install_base). NOT people interested in the cert. The people who literally sit down and take the exam. The funnel drops dramatically: if ~250K are interested, ~50K take training, maybe ~5K sit the exam. For a software company: ~2% of trainees sit the cert exam. For an Industry Authority: ~10% of trainees sit the exam. For academic: ~95% (coursework exams are required). **FOR WRAPPER ORG TYPES: this is how many people at THIS ORGANIZATION sit for certs annually — NOT the global cert candidate population.** Accenture's AWS cert sitters are ~6,000, not the 400,000 people worldwide who sit for AWS certs. Single estimated number. Look for published vendor cert stats. Do NOT guess — leave null when the research doesn't document the number.
  - **cert_bodies_mentioning**: list of independent certification bodies whose curriculum mentions THIS product (not the parent company).
  - **independent_training_course_counts**: dict of platform name → course count for THIS product on each independent training marketplace.  Example: {{"Pluralsight": 15, "Coursera": 3, "Udemy": 8}}.  Only include platforms you searched.
  - **is_ai_powered**: product has AI features requiring hands-on practice.
  - **is_ai_platform**: product IS an AI platform — labs teach building / training / deploying AI.

═══ TRUTH DISCIPLINE ═══

If the research doesn't say, use the conservative neutral value (null / empty / false).  Do NOT guess.  Do NOT apply your own knowledge of the product — use ONLY the research provided.  If a field cannot be determined from the research, leave it neutral rather than fabricating.

Return ONLY the JSON object.  No prose, no markdown, no code fence.
"""


def _build_pillar_2_fact_context(name: str, search_results: dict, page_contents: dict) -> str:
    """Build per-product research context for Pillar 2 fact extraction.

    Reads Pillar 2 search keys (product complexity, mastery stakes, lab
    versatility, market demand).  Some keys overlap with Pillar 1 (e.g.
    documentation pages carry signal for both dimensions) — that's fine,
    each extractor reads what it needs.
    """
    lines = [f"# Research for: {name}"]

    pillar_2_keys = [
        # Product Complexity signals
        f"docs_{name}", f"ai_{name}", f"tech_{name}",
        # Mastery Stakes signals
        f"stakes_{name}",
        # Lab Versatility + Market Demand signals
        f"train_{name}", f"compete_{name}", f"marketplace_{name}",
        f"api_{name}",  # shared with P1 but informs complexity too
    ]
    for key in pillar_2_keys:
        for r in search_results.get(key, []):
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            lines.append(f"- **{title}** ({url}): {snippet}")

    page_key_labels = [
        (name, "Documentation"),
        (f"docs_{name}", "Docs Page"),
        (f"train_{name}", "Training Page"),
    ]
    for key, label in page_key_labels:
        if key in page_contents:
            lines.append(f"\n### {label}:")
            lines.append(page_contents[key])

    return "\n".join(lines)


def _coerce_numeric_range(raw: dict | None) -> NumericRange:
    """Defensive parse of a NumericRange dict."""
    if not isinstance(raw, dict):
        return NumericRange()
    def _opt_int(v):
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None
    # Support both old format (low/high) and new format (single value).
    # New schema uses "value" → stored as low == high (single number).
    # Old cached data still uses low/high and is honored as-is.
    val = _opt_int(raw.get("value"))
    if val is not None:
        low = val
        high = val
    else:
        low = _opt_int(raw.get("low"))
        high = _opt_int(raw.get("high"))
    return NumericRange(
        low=low,
        high=high,
        source_url=str(raw.get("source_url") or ""),
        confidence=str(raw.get("confidence") or ""),
        notes=str(raw.get("notes") or ""),
    )


def _coerce_signal_evidence(raw: dict | None) -> SignalEvidence:
    """Defensive parse of a SignalEvidence dict (no strength field — truth only)."""
    if not isinstance(raw, dict):
        return SignalEvidence()
    return SignalEvidence(
        present=bool(raw.get("present") or False),
        observation=str(raw.get("observation") or ""),
        source_url=str(raw.get("source_url") or ""),
        confidence=str(raw.get("confidence") or ""),
    )


def _coerce_signals_dict(raw: dict | None) -> dict[str, SignalEvidence]:
    """Defensive parse of a dict of signal_category → SignalEvidence."""
    if not isinstance(raw, dict):
        return {}
    return {str(k): _coerce_signal_evidence(v) for k, v in raw.items()}


def _coerce_iv_facts_dict_to_dataclass(raw: dict) -> InstructionalValueFacts:
    """Parse the JSON Claude returned into InstructionalValueFacts.

    Defensive: drops unknown keys, supplies neutral defaults for missing
    keys, never raises on field-shape mismatch.
    """
    def _str(v) -> str: return str(v) if v is not None else ""

    pc_raw = raw.get("product_complexity", {}) or {}
    product_complexity = ProductComplexityFacts(
        description=_str(pc_raw.get("description")),
        signals=_coerce_signals_dict(pc_raw.get("signals")),
    )

    ms_raw = raw.get("mastery_stakes", {}) or {}
    mastery_stakes = MasteryStakesFacts(
        description=_str(ms_raw.get("description")),
        signals=_coerce_signals_dict(ms_raw.get("signals")),
    )

    lv_raw = raw.get("lab_versatility", {}) or {}
    lab_versatility = LabVersatilityFacts(
        description=_str(lv_raw.get("description")),
        signals=_coerce_signals_dict(lv_raw.get("signals")),
    )

    md_raw = raw.get("market_demand", {}) or {}
    cert_bodies = md_raw.get("cert_bodies_mentioning") or []
    if not isinstance(cert_bodies, list):
        cert_bodies = []
    course_counts_raw = md_raw.get("independent_training_course_counts") or {}
    course_counts: dict[str, int] = {}
    if isinstance(course_counts_raw, dict):
        for k, v in course_counts_raw.items():
            try:
                course_counts[str(k)] = int(v)
            except (TypeError, ValueError):
                continue

    market_demand = MarketDemandFacts(
        description=_str(md_raw.get("description")),
        install_base=_coerce_numeric_range(md_raw.get("install_base")),
        employee_subset_size=_coerce_numeric_range(md_raw.get("employee_subset_size")),
        cert_annual_sit_rate=_coerce_numeric_range(md_raw.get("cert_annual_sit_rate")),
        cert_bodies_mentioning=[str(b) for b in cert_bodies],
        independent_training_course_counts=course_counts,
        is_ai_powered=bool(md_raw.get("is_ai_powered") or False),
        is_ai_platform=bool(md_raw.get("is_ai_platform") or False),
        signals=_coerce_signals_dict(md_raw.get("signals")),
    )

    return InstructionalValueFacts(
        product_complexity=product_complexity,
        mastery_stakes=mastery_stakes,
        lab_versatility=lab_versatility,
        market_demand=market_demand,
    )


def extract_instructional_value_facts(
    product_name: str,
    search_results: dict,
    page_contents: dict,
) -> InstructionalValueFacts:
    """Extract Pillar 2 facts for one product from raw research.

    Truth-only.  One focused Claude call per product, populating the
    InstructionalValueFacts drawer with qualitative SignalEvidence dicts
    plus concrete numeric facts for Market Demand.  On failure, returns
    an empty InstructionalValueFacts so the research run never crashes.
    """
    from scorer import _call_claude  # local import to avoid circular dep
    context = _build_pillar_2_fact_context(product_name, search_results, page_contents)
    log.info("Pillar 2 fact extraction starting for %s", product_name)

    # Retry once on failure — Pillar 2 extractions intermittently return
    # empty drawers due to Claude call timeouts or malformed responses.
    # One retry catches transient failures without burning excessive tokens.
    max_attempts = 2  # magic-allowed: retry count for transient failures
    for attempt in range(max_attempts):
        try:
            raw = _call_claude(
                _INSTRUCTIONAL_VALUE_FACTS_PROMPT,
                context,
                max_tokens=4000,
            )
            result = _coerce_iv_facts_dict_to_dataclass(raw)
            # Check if the result is substantive — retry if key drawers are empty
            has_complexity = bool(getattr(result.product_complexity, "signals", None))
            has_stakes = bool(getattr(result.mastery_stakes, "signals", None))
            if has_complexity or has_stakes or attempt == max_attempts - 1:
                return result
            log.warning(
                "Pillar 2 fact extraction for %s returned empty drawers on "
                "attempt %d — retrying", product_name, attempt + 1,
            )
        except Exception as e:
            log.warning(
                "Pillar 2 fact extraction Claude call failed for %s "
                "(attempt %d): %s", product_name, attempt + 1, e,
            )
            if attempt == max_attempts - 1:
                return InstructionalValueFacts()

    return InstructionalValueFacts()


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar 3 Fact Extraction — Customer Fit (company-level, one call per company)
#
# Reads company-level research (training programs, partners, delivery infra,
# org DNA signals) and produces a CustomerFitFacts drawer with top-level
# shared facts plus four per-dimension sub-drawers.  This fires ONCE per
# company, not per product.
# ═══════════════════════════════════════════════════════════════════════════════

_CUSTOMER_FIT_FACTS_PROMPT = """You are a research analyst extracting structured facts about an organization's ability to build, deliver, and commit to hands-on training.

Your job is TRUTH ONLY.  You are NOT scoring, NOT classifying as good/bad, NOT picking winners, NOT applying any Skillable framework.  You are extracting observable facts about the company.

Return a JSON object with EXACTLY this shape (no extra keys, no commentary, no markdown):

{
  "description": "<1-3 sentence narrative of the company as a training/enablement organization>",
  "total_employees": {"low": <int or null>, "high": <int or null>, "source_url": "", "confidence": "", "notes": ""},
  "channel_partners_size": {"low": <int or null>, "high": <int or null>, "source_url": "", "confidence": "", "notes": ""},
  "channel_partner_se_population": {"low": <int or null>, "high": <int or null>, "source_url": "", "confidence": "", "notes": ""},
  "named_channel_partners": [<"Deloitte", "Accenture", ...>],
  "events_attendance": {"<event name>": {"low": <int or null>, "high": <int or null>, "source_url": "", "confidence": "", "notes": ""}},
  "enterprise_reference_customers": [<"Fortune 500 names from case studies">],
  "geographic_reach_regions": [<"NAMER", "EMEA", "APAC", "LATAM">],

  "training_commitment": {
    "description": "",
    "has_on_demand_catalog": <bool>,
    "has_ilt_calendar": <bool>,
    "customer_enablement_team_name": "",
    "certification_programs": [<"name of cert program", ...>],
    "training_leadership_titles": [<"VP of Education", "Chief Learning Officer", ...>],
    "training_catalog_url": "",
    "audiences_served": [<"employees", "customers", "partners", "end_users">],
    "has_compliance_training": <bool>,
    "uses_hands_on_language": <bool>,
    "signals": {}
  },

  "build_capacity": {
    "description": "",
    "lab_build_platforms_in_use": [<"Skillable", "Instruqt", "CloudShare", ...>],
    "is_already_building_labs": <bool>,
    "content_team_name": "",
    "authoring_roles_found": [<"Instructional Designer", "Lab Author", "Technical Writer", ...>],
    "outsourcing_evidence": [<"specific finding strings">],
    "signals": {}
  },

  "delivery_capacity": {
    "description": "",
    "has_vendor_delivered_training": <bool>,
    "vendor_training_modes": [<"ilt", "self_paced", "vendor_labs", "bootcamps">],
    "has_published_course_calendar": <bool>,
    "course_calendar_url": "",
    "has_informal_training_partners": <bool>,
    "named_informal_training_partners": [<"partner name", ...>],
    "authorized_training_program_name": "",
    "authorized_training_partners_count": {"low": <int or null>, "high": <int or null>, "source_url": "", "confidence": "", "notes": ""},
    "named_authorized_training_partners": [<"ATP name", ...>],
    "lms_platforms_in_use": [<"Docebo", "Cornerstone", "Moodle", ...>],
    "cert_delivery_vendors": [<"Pearson VUE", "Prometric", "PSI", ...>],
    "signals": {}
  },

  "organizational_dna": {
    "description": "",
    "partnership_types": [<"technology", "channel", "content", "delivery", "integration">],
    "named_alliance_leadership": [<"VP Alliances name or title">],
    "uses_external_platforms": [<"Salesforce", "Workday", "Okta", ...>],
    "funding_events": [<"IPO 2024", "Series D $200M", ...>],
    "has_recent_layoffs": <bool>,
    "signals": {}
  }
}

═══ FIELD GUIDANCE ═══

**Top-level shared facts** feed multiple downstream readers, including the ACV Potential calculation. Some of them are the AUDIENCE inputs for specific consumption motions — produce tight, defendable ranges because audience is the ONLY source of range in the final ACV number.

  - `total_employees`: the company's total headcount. NOT the training team, NOT the SE population.
  - `channel_partners_size`: total partner count — resellers, GSIs, distributors combined.
  - `channel_partner_se_population` → ACV Motion 2 (Partner Training). Approximate number of sales engineers, solution architects, and delivery consultants working INSIDE the channel partner ecosystem who would benefit from hands-on labs on the company's products. NOT the channel partner headcount (that's every employee at every partner) — the subset whose job actually requires hands-on skill. A global ATP network of 500 partners with ~5 SEs each is 2,500. A thin channel of 50 resellers with 2 SEs each is 100. Produce a tight believable range; leave null when research doesn't document this.
  - `named_channel_partners`: specific partner names mentioned in the research.
  - `events_attendance` → ACV Motion 5 (Events & Conferences). Flagship events the company runs — map of event name to attendance range. e.g. {"Cohesity Connect": {"low": 5000, "high": 5500, ...}, "Cohesity World Tour": {"low": 3000, "high": 4000, ...}}. The ACV calculator sums ALL named events' attendance as the Motion 5 audience. Include only real events with public attendance evidence; leave the dict empty when the company runs no events or when attendance isn't documented. Do NOT invent events. Tight ranges — conference pages usually publish attendance numbers.
  - `enterprise_reference_customers`: Fortune 500 names mentioned as customers in case studies.
  - `geographic_reach_regions`: where the company operates — NAMER / EMEA / APAC / LATAM.

**training_commitment.audiences_served**: ONLY the subset of {"employees", "customers", "partners", "end_users"} that the research actually documents training for.  Multi-audience breadth is a strong signal.

**training_commitment.uses_hands_on_language**: true if the company's training materials explicitly mention "hands-on", "lab", "interactive", "scenario-based" language.

**build_capacity.lab_build_platforms_in_use**: competitor lab platforms detected on the company's website or in their training materials.  Use canonical platform names.

**delivery_capacity** — separate field sets for informal vs authorized partner programs because a company can have both simultaneously (e.g., transitioning from informal to a new ATP).  Do not collapse them.

**delivery_capacity.authorized_training_program_name**: empty string if no formal program exists.  If a program exists, name it (e.g. "Cohesity Authorized Training Partner Program").

**delivery_capacity.lms_platforms_in_use**: named LMS platforms the company uses — Docebo, Cornerstone, Moodle, etc.

**organizational_dna.uses_external_platforms**: Platform Buyer evidence.  If the company publicly uses Salesforce, Workday, Okta, etc., name them.

**organizational_dna.funding_events**: recent IPOs, funding rounds, M&A activity that signal scale / stability.

═══ TRUTH DISCIPLINE ═══

If the research doesn't say, use the conservative neutral value (null / empty / false).  Do NOT guess.  Do NOT apply your own knowledge of the company — use ONLY the research provided.  If a field cannot be determined from the research, leave it neutral rather than fabricating.

Return ONLY the JSON object.  No prose, no markdown, no code fence.
"""


def _build_pillar_3_fact_context(
    company_name: str,
    discovery_data: dict | None,
    customer_fit_research: dict,
    customer_fit_pages: dict,
) -> str:
    """Build company-level research context for Pillar 3 fact extraction.

    Pulls from two sources:
      1. discovery_data — company homepage, training pages, partner pages
         already fetched during the Discover phase (cheap, cached).
      2. customer_fit_research / customer_fit_pages — the deeper
         company-level research fired by research_company_fit() at
         Deep Dive time.
    """
    lines = [f"# Company: {company_name}"]

    # From discovery data (already-fetched at search time)
    if discovery_data:
        if discovery_data.get("company_description"):
            lines.append(f"\n**Description:** {discovery_data['company_description']}")
        if discovery_data.get("company_url"):
            lines.append(f"**URL:** {discovery_data['company_url']}")

        disc_pages = discovery_data.get("page_contents") or {}
        for key in ("company_homepage", "training_page", "atp_page", "partner_portal_page"):
            if key in disc_pages:
                lines.append(f"\n## Discovery — {key.replace('_', ' ').title()}")
                lines.append(disc_pages[key])

        for key in ("training_programs", "atp_signals", "training_catalog",
                    "partner_ecosystem", "partner_portal", "cs_signals",
                    "lms_signals", "org_contacts"):
            results = discovery_data.get(key) or []
            if results:
                lines.append(f"\n## Discovery — {key.replace('_', ' ').title()}")
                for r in results[:8]:
                    lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    # From the deeper Pillar 3 research
    if customer_fit_research:
        for key, results in customer_fit_research.items():
            if not results:
                continue
            lines.append(f"\n## Deep Research — {key}")
            for r in results[:6]:
                lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    if customer_fit_pages:
        for key, content in customer_fit_pages.items():
            lines.append(f"\n### Fetched page — {key}:")
            lines.append(content[:3000])

    return "\n".join(lines)


def _coerce_cf_facts_dict_to_dataclass(raw: dict) -> CustomerFitFacts:
    """Parse the JSON Claude returned into CustomerFitFacts.

    Defensive: drops unknown keys, supplies neutral defaults for missing
    keys, never raises on field-shape mismatch.
    """
    def _str(v) -> str: return str(v) if v is not None else ""
    def _bool(v) -> bool: return bool(v) if v is not None else False
    def _list_str(v) -> list:
        return [str(x) for x in v] if isinstance(v, list) else []

    # ── Training Commitment ─────────────────────────────────────────────
    tc_raw = raw.get("training_commitment", {}) or {}
    training_commitment = TrainingCommitmentFacts(
        description=_str(tc_raw.get("description")),
        has_on_demand_catalog=_bool(tc_raw.get("has_on_demand_catalog")),
        has_ilt_calendar=_bool(tc_raw.get("has_ilt_calendar")),
        customer_enablement_team_name=_str(tc_raw.get("customer_enablement_team_name")),
        certification_programs=_list_str(tc_raw.get("certification_programs")),
        training_leadership_titles=_list_str(tc_raw.get("training_leadership_titles")),
        training_catalog_url=_str(tc_raw.get("training_catalog_url")),
        audiences_served=_list_str(tc_raw.get("audiences_served")),
        has_compliance_training=_bool(tc_raw.get("has_compliance_training")),
        uses_hands_on_language=_bool(tc_raw.get("uses_hands_on_language")),
        signals=_coerce_signals_dict(tc_raw.get("signals")),
    )

    # ── Build Capacity ──────────────────────────────────────────────────
    bc_raw = raw.get("build_capacity", {}) or {}
    build_capacity = BuildCapacityFacts(
        description=_str(bc_raw.get("description")),
        lab_build_platforms_in_use=_list_str(bc_raw.get("lab_build_platforms_in_use")),
        is_already_building_labs=_bool(bc_raw.get("is_already_building_labs")),
        content_team_name=_str(bc_raw.get("content_team_name")),
        authoring_roles_found=_list_str(bc_raw.get("authoring_roles_found")),
        outsourcing_evidence=_list_str(bc_raw.get("outsourcing_evidence")),
        signals=_coerce_signals_dict(bc_raw.get("signals")),
    )

    # ── Delivery Capacity ───────────────────────────────────────────────
    dc_raw = raw.get("delivery_capacity", {}) or {}
    delivery_capacity = DeliveryCapacityFacts(
        description=_str(dc_raw.get("description")),
        has_vendor_delivered_training=_bool(dc_raw.get("has_vendor_delivered_training")),
        vendor_training_modes=_list_str(dc_raw.get("vendor_training_modes")),
        has_published_course_calendar=_bool(dc_raw.get("has_published_course_calendar")),
        course_calendar_url=_str(dc_raw.get("course_calendar_url")),
        has_informal_training_partners=_bool(dc_raw.get("has_informal_training_partners")),
        named_informal_training_partners=_list_str(dc_raw.get("named_informal_training_partners")),
        authorized_training_program_name=_str(dc_raw.get("authorized_training_program_name")),
        authorized_training_partners_count=_coerce_numeric_range(dc_raw.get("authorized_training_partners_count")),
        named_authorized_training_partners=_list_str(dc_raw.get("named_authorized_training_partners")),
        lms_platforms_in_use=_list_str(dc_raw.get("lms_platforms_in_use")),
        cert_delivery_vendors=_list_str(dc_raw.get("cert_delivery_vendors")),
        signals=_coerce_signals_dict(dc_raw.get("signals")),
    )

    # ── Organizational DNA ──────────────────────────────────────────────
    od_raw = raw.get("organizational_dna", {}) or {}
    organizational_dna = OrganizationalDnaFacts(
        description=_str(od_raw.get("description")),
        partnership_types=_list_str(od_raw.get("partnership_types")),
        named_alliance_leadership=_list_str(od_raw.get("named_alliance_leadership")),
        uses_external_platforms=_list_str(od_raw.get("uses_external_platforms")),
        funding_events=_list_str(od_raw.get("funding_events")),
        has_recent_layoffs=_bool(od_raw.get("has_recent_layoffs")),
        signals=_coerce_signals_dict(od_raw.get("signals")),
    )

    # ── Events attendance dict ──────────────────────────────────────────
    events_raw = raw.get("events_attendance") or {}
    events_attendance: dict[str, NumericRange] = {}
    if isinstance(events_raw, dict):
        for ev_name, ev_raw in events_raw.items():
            events_attendance[str(ev_name)] = _coerce_numeric_range(ev_raw)

    return CustomerFitFacts(
        description=_str(raw.get("description")),
        total_employees=_coerce_numeric_range(raw.get("total_employees")),
        channel_partners_size=_coerce_numeric_range(raw.get("channel_partners_size")),
        channel_partner_se_population=_coerce_numeric_range(raw.get("channel_partner_se_population")),
        named_channel_partners=_list_str(raw.get("named_channel_partners")),
        events_attendance=events_attendance,
        enterprise_reference_customers=_list_str(raw.get("enterprise_reference_customers")),
        geographic_reach_regions=_list_str(raw.get("geographic_reach_regions")),
        training_commitment=training_commitment,
        build_capacity=build_capacity,
        delivery_capacity=delivery_capacity,
        organizational_dna=organizational_dna,
    )


def extract_customer_fit_facts(
    company_name: str,
    discovery_data: dict | None,
    customer_fit_research: dict,
    customer_fit_pages: dict,
) -> CustomerFitFacts:
    """Extract Pillar 3 facts for one company from raw research.

    Truth-only.  One focused Claude call per company (not per product),
    populating the CustomerFitFacts drawer.  On failure, returns an empty
    CustomerFitFacts so the scoring run never crashes.
    """
    from scorer import _call_claude  # local import to avoid circular dep
    context = _build_pillar_3_fact_context(
        company_name, discovery_data, customer_fit_research, customer_fit_pages,
    )
    log.info("Pillar 3 fact extraction starting for %s", company_name)
    try:
        raw = _call_claude(
            _CUSTOMER_FIT_FACTS_PROMPT,
            context,
            max_tokens=4000,
        )
    except Exception as e:
        log.warning("Pillar 3 fact extraction Claude call failed for %s: %s", company_name, e)
        return CustomerFitFacts()
    return _coerce_cf_facts_dict_to_dataclass(raw)


# ═══════════════════════════════════════════════════════════════════════════════
# Company Research — evidence for Customer Fit dimensions
# ═══════════════════════════════════════════════════════════════════════════════

def research_company_fit(company_name: str, discovery_data: dict | None = None) -> dict:
    """Gather evidence for the four Customer Fit dimensions.

    This runs alongside product research to provide company-level context.
    Returns evidence organized by dimension.
    """
    queries = [
        # ── Training Commitment (Dimension 3.1) ──
        ("tc_enablement", f"{company_name} customer enablement program onboarding"),
        ("tc_certification", f"{company_name} certification program exam credential"),
        ("tc_catalog", f"{company_name} training catalog courses learning library"),
        ("tc_compliance", f"{company_name} compliance training regulated industry audit"),
        ("tc_leadership", f"{company_name} VP training OR VP enablement OR Chief Learning Officer LinkedIn"),

        # ── Organizational DNA (Dimension 3.2) ──
        ("od_partners", f"{company_name} authorized training partner ATP learning partner count"),
        ("od_platform", f"{company_name} marketplace SDK API developer platform ecosystem"),
        ("od_size", f"{company_name} employees company size organization structure"),

        # ── Delivery Capacity (Dimension 3.3) ──
        ("dc_lms", f"{company_name} LMS Docebo OR Cornerstone OR Moodle OR \"learning management\""),
        ("dc_graymarket", f"{company_name} training Udemy OR Coursera OR \"LinkedIn Learning\" OR Pluralsight"),
        ("dc_events", f"{company_name} conference summit hands-on labs workshop annual event"),

        # ── Build Capacity (Dimension 3.4) ──
        ("bc_team", f"{company_name} instructional designer OR lab author OR training content developer"),
        ("bc_diy", f"{company_name} lab environment virtual lab custom training infrastructure"),
    ]

    log.info("Company fit research: running %d queries for %s", len(queries), company_name)
    search_results = _run_searches_parallel(queries)

    # Fetch key pages
    pages_to_fetch = []
    for key in ["tc_catalog", "tc_certification", "od_partners", "dc_events"]:
        results = search_results.get(key, [])
        if results:
            pages_to_fetch.append((key, results[0].get("url", "")))

    page_contents = _fetch_pages_parallel(pages_to_fetch)

    return {
        "company_name": company_name,
        "customer_fit_research": search_results,
        "customer_fit_pages": page_contents,
    }
