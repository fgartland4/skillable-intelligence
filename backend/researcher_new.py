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
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

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
    with ThreadPoolExecutor(max_workers=12) as executor:
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
    with ThreadPoolExecutor(max_workers=10) as executor:
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

def scrape_product_families(company_name: str) -> list[dict]:
    """Scrape company website navigation to extract product families.

    Returns [{"name": "Family Name", "url": "https://...", "product_count": N}].
    Used for large-portfolio companies to present a family picker.
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
            if not text or len(text) < 3 or len(text) > 60:
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

    return {
        "company_name": company_name,
        "selected_products": selected_products,
        "search_results": search_results,
        "page_contents": page_contents,
    }


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
