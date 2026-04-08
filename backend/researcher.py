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
    LabAccessFacts, ProductLababilityFacts, ProvisioningFacts,
    ScoringFacts, TeardownFacts,
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

    # ── Step 2 (2026-04-08): Research → Store layer for Pillar 1 ────────────
    # Run structured fact extraction per product in parallel.  This populates
    # the ProductLababilityFacts drawer with truth-only typed primitives that
    # the Pillar 1 scorer (Step 3) will read.  The legacy monolithic scoring
    # call still runs in scorer.py until Step 5 — both paths coexist during
    # the rebuild so we never have a half-broken system.
    product_facts: dict[str, ProductLababilityFacts] = {}
    with ThreadPoolExecutor(max_workers=min(len(selected_products), 5) or 1) as ex:
        futures = {
            ex.submit(
                extract_product_labability_facts,
                p.get("name", ""),
                search_results,
                page_contents,
            ): p.get("name", "")
            for p in selected_products
        }
        for future in as_completed(futures, timeout=120):
            name = futures[future]
            try:
                product_facts[name] = future.result()
            except Exception as e:
                log.warning("Pillar 1 fact extraction failed for %s: %s", name, e)
                product_facts[name] = ProductLababilityFacts()

    return {
        "company_name": company_name,
        "selected_products": selected_products,
        "search_results": search_results,
        "page_contents": page_contents,
        "product_labability_facts": product_facts,
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
    "needs_gcp": <bool>
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

provisioning.runs_as_*: how the product can ACTUALLY be deployed.  Multiple may be true (a product that ships as both an installable and a Docker image is both runs_as_installable AND runs_as_container).  If the only way to use the product is the vendor's hosted service, runs_as_saas_only is true and the others are false.

provisioning.sandbox_api_granularity: does the product expose an API that can spin up an isolated sandbox/tenant on demand?
  - "rich"    = full create/configure/delete cycle
  - "partial" = some endpoints but missing pieces (e.g. create works, delete doesn't)
  - "none"    = no documented sandbox provisioning API

provisioning.has_pre_instancing_opportunity: true ONLY when documentation explicitly indicates slow first-launch, slow cluster initialization, or slow tenant warm-up that would benefit from pre-warming environments.

lab_access.auth_model: how the END USER authenticates to the running product.
  - "entra_native_tenant" — Skillable provisions in a controlled Entra tenant; in-lab username + password are displayed
  - "entra_msft_id"       — Product accepts the learner's own personal/work Microsoft account
  - "sso_saml" / "sso_oidc" — Generic SAML / OIDC SSO
  - "oauth"               — OAuth flow (rare for human login)
  - "product_credentials" — Product manages its own user database; per-learner accounts are created inside the product
  - "api_key"             — Auth is via API key (developer-tool products)
  - "none"                — No documented auth model

lab_access.user_provisioning_api_granularity: does the vendor expose an API to create per-learner users / roles?  Same rich/partial/none ladder.

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


def _build_pillar_1_fact_context(name: str, search_results: dict, page_contents: dict) -> str:
    """Build the per-product research context for Pillar 1 fact extraction.

    Mirrors `scorer._build_product_context` shape so the AI sees the same
    raw research the legacy scoring path sees — but only the search keys
    relevant to Pillar 1 dimensions (provisioning, lab access, scoring,
    teardown).  Pillar 2 / Pillar 3 keys are intentionally excluded.
    """
    lines = [f"# Research for: {name}"]

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
    context = _build_pillar_1_fact_context(product_name, search_results, page_contents)
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
