"""Web research orchestration for discovering company products and training programs."""

import logging
import os
import requests

log = logging.getLogger(__name__)
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

_SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

# Known Skillable customers — used to find alumni at prospect companies.
# Update when new active customers are added to CUSTOMER_BENCHMARKS in scorer.py.
_SKILLABLE_CUSTOMER_NAMES = [
    "Cohesity", "Tanium", "Tableau", "Salesforce", "Hyland", "Commvault",
    "Microsoft", "Cisco", "NVIDIA", "CompTIA", "ISACA", "SANS", "EC-Council",
    "CREST", "National Instruments", "Emerson",
]


# ---------------------------------------------------------------------------
# Source type classification — drives per-page fetch depth
# ---------------------------------------------------------------------------

def _classify_source_type(url: str) -> str:
    """Classify a URL as 'api_ref', 'docs', or 'marketing' for fetch depth decisions.

    Applied automatically by _fetch_pages_parallel — callers don't need to specify depth.
    Priority: api_ref > docs > marketing (most specific wins).
    """
    u = url.lower()
    if any(s in u for s in [
        "swagger", "openapi", "api-reference", "api_reference", "/api-docs", "apidocs",
        "redoc", "stoplight.io", "readme.io/reference", "/api/v",
    ]):
        return "api_ref"
    if any(s in u for s in [
        "docs.", "/docs/", "/documentation", "learn.", "/learn/", "help.",
        "support.", "/help/", "knowledge", "/guide", "/tutorial", "/manual",
        "techzone", "technet", "developer.microsoft", "developer.apple",
        "developer.android", "/kb/", "/reference/",
    ]):
        return "docs"
    return "marketing"


# Fetch depth per source type — api_ref gets the most content to catch DELETE endpoints,
# auth details, and lifecycle coverage that tend to appear deep in reference docs.
_FETCH_DEPTH: dict[str, int] = {
    "marketing": 2500,
    "docs":      6000,
    "api_ref":   10000,
}


def _fetch_page_text(url: str, max_chars: int = 8000) -> str:
    """Fetch a URL and return its text content."""
    try:
        resp = requests.get(url, timeout=5, headers={
            "User-Agent": "Mozilla/5.0 (compatible; LababilityEngine/1.0)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_chars]
    except Exception as e:
        return f"[Error fetching {url}: {e}]"


def _search_serper(query: str, num_results: int = 5) -> list[dict]:
    """Search via Serper.dev API (Google results). Requires SERPER_API_KEY."""
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": _SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=8,
        )
        if resp.status_code in (402, 429) or (resp.status_code == 403 and "credit" in resp.text.lower()):
            return [{"title": "Search credits exhausted", "url": "", "snippet":
                     "You guys are using this tool a ton! Looks like your admin needs to refresh "
                     "your search credits — please let them know."}]
        resp.raise_for_status()
        data = resp.json()
        results = []
        for r in data.get("organic", [])[:num_results]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            })
        return results
    except Exception as e:
        return [{"title": "Search error", "url": "", "snippet": str(e)}]


def _search_duckduckgo(query: str, num_results: int = 5) -> list[dict]:
    """Search via DuckDuckGo HTML (fallback when no Serper key)."""
    results = []
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=8,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        for result in soup.select(".result")[:num_results]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            if title_el:
                href = title_el.get("href", "")
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": href,
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                })
    except Exception as e:
        results.append({"title": "Search error", "url": "", "snippet": str(e)})
    return results


def _search_web(query: str, num_results: int = 5) -> list[dict]:
    """Search the web — uses Serper if API key is configured, falls back to DuckDuckGo."""
    if _SERPER_API_KEY:
        return _search_serper(query, num_results)
    return _search_duckduckgo(query, num_results)


def _run_searches_parallel(queries: list[tuple[str, str]], num_results: int = 5) -> dict[str, list[dict]]:
    """Run multiple searches in parallel. queries is a list of (label, query) tuples.
    Caps total wait time at 25 seconds — any search not finished by then returns empty."""
    results = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_label = {
            executor.submit(_search_web, query, num_results): label
            for label, query in queries
        }
        try:
            for future in as_completed(future_to_label, timeout=25):
                label = future_to_label[future]
                try:
                    results[label] = future.result()
                except Exception as e:
                    results[label] = [{"title": "Error", "url": "", "snippet": str(e)}]
        except TimeoutError:
            log.warning("Search batch timed out after 25s — using partial results (%d/%d complete)",
                        len(results), len(future_to_label))
            for future, label in future_to_label.items():
                if label not in results:
                    results[label] = []
    return results


def _fetch_pages_parallel(targets: list[tuple[str, str]], max_chars: int = 3000) -> dict[str, str]:
    """Fetch multiple pages in parallel. targets is a list of (label, url) tuples.

    max_chars is a fallback; source type classification automatically applies higher
    limits for documentation and API reference pages (_FETCH_DEPTH).
    """
    contents = {}
    valid = [(label, url) for label, url in targets if url and not url.startswith("[")]
    if not valid:
        return contents
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_label = {
            executor.submit(
                _fetch_page_text, url,
                _FETCH_DEPTH.get(_classify_source_type(url), max_chars)
            ): label
            for label, url in valid
        }
        for future in as_completed(future_to_label):
            label = future_to_label[future]
            try:
                contents[label] = future.result()
            except Exception as e:
                log.warning("Page fetch failed for %s: %s", label, e)
    return contents


def resolve_company_from_product(product_name: str) -> tuple[str, list[str]]:
    """Given only a product name, return (company_name_hint, [product_name]).
    Searches the web to find the vendor; falls back to the product name as seed
    so discovery searches still find the right context."""
    results = _search_web(f"{product_name} software company vendor", num_results=3)
    # Try to extract a company name from result titles (e.g. "OnBase | Hyland")
    for r in results:
        title = r.get("title", "")
        for sep in [" | ", " - ", " – ", " by ", " from "]:
            parts = title.split(sep)
            if len(parts) >= 2:
                # Take the last segment which is usually the company name
                candidate = parts[-1].strip()
                if candidate and len(candidate) < 60 and product_name.lower() not in candidate.lower():
                    return candidate, [product_name]
    # Fallback: use product name as the search seed; Claude will identify the real company
    return product_name, [product_name]


def discover_products(company_name: str, known_products: Optional[list[str]] = None) -> dict:
    """Product discovery phase — searches for products AND all company-level partnership signals.

    Company-level queries live here (not in research_products) so they run in a small, focused
    batch that reliably completes without DuckDuckGo rate-limiting. This data feeds both the
    product discovery Claude call and the partnership readiness scoring.
    """
    queries = [
        # Product discovery
        ("products",        f"{company_name} software products portfolio solutions"),
        ("products2",       f"{company_name} product catalog platform suite"),
        # Training & certification
        ("training",        f"{company_name} training academy certification program"),
        ("atp",             f"{company_name} authorized training partner learning partner program"),
        ("training_catalog",f"{company_name} training catalog courses certifications curriculum"),
        # Partner & channel
        ("partners",        f"{company_name} partner program technology alliance channel"),
        ("partner_portal",  f"{company_name} partner portal enablement resources technical training"),
        # Customer success & LMS
        ("cs",              f"{company_name} customer success onboarding professional services"),
        ("lms",             f"{company_name} LMS learning management system platform"),
        # Lab platform — Skillable / LOD detection (critical: most labs launch from non-Skillable URLs)
        # Hits all known Skillable signals: labondemand.com, LODS, Cloud Slice, LCAs, IDLX, legacy brand
        ("lab_skillable",   f"{company_name} (labondemand.com OR \"learnondemandsystems.com\" OR \"Learn on Demand Systems\" OR LODS OR \"Cloud Slice\" OR \"Lifecycle Actions\" OR LCA OR IDLX OR Skillable) labs training"),
        # Lab platform — direct competitors (broad)
        ("lab_compete",     f"{company_name} (Instruqt OR CloudShare OR Skytap OR Kyndryl OR GoDeploy OR Vocareum OR Appsembler OR ReadyTech OR \"Immersive Labs\" OR \"Hack The Box\" OR TryHackMe OR \"ACI Learning\" OR \"virtual lab\" OR \"we built our own\" OR \"internal lab\") training"),
        # Org & contacts — 2 consolidated LinkedIn queries (reduced from 5 to limit rate-limiting):
        # (1) VP-and-above across all three key functions: customer education, partner enablement, certification
        ("org_senior",    f"site:linkedin.com/in/ {company_name} (VP OR SVP OR EVP OR Chief OR \"Head of\") (\"customer education\" OR \"customer training\" OR \"customer enablement\" OR \"partner enablement\" OR \"channel enablement\" OR \"partner training\" OR \"certification program\" OR \"technical certification\")"),
        # (2) Director-level catch-all covering technical training, enablement, and certification
        ("org_directors", f"site:linkedin.com/in/ {company_name} (Director OR \"Head of\") (\"technical training\" OR \"technical enablement\" OR \"training and certification\" OR \"global training\" OR enablement OR certification)"),
    ]
    if known_products:
        queries.append(("known", f"{company_name} {' '.join(known_products)} software"))

    all_results = _run_searches_parallel(queries)

    # Merge product results
    product_results = all_results.get("products", []) + all_results.get("products2", [])
    if "known" in all_results:
        product_results += all_results["known"]

    # Fetch top pages: company homepage + 2 product pages + training page + ATP page + partner portal page
    fetch_targets = []
    # Company homepage — Claude uses this to confirm org type, description, and main URL
    company_search_url = next(
        (r["url"] for r in all_results.get("products", []) + all_results.get("products2", [])
         if r.get("url") and company_name.lower().split()[0] in r.get("url", "").lower()),
        None
    )
    if company_search_url:
        fetch_targets.append(("company_homepage", company_search_url))
    for r in (all_results.get("products", []) + all_results.get("products2", []))[:2]:
        if r.get("url"):
            fetch_targets.append((f"product_page_{len([t for t in fetch_targets if t[0].startswith('product_page_')])}", r["url"]))
    for r in all_results.get("training", [])[:1]:
        if r.get("url"):
            fetch_targets.append(("training_page", r["url"]))
    for r in all_results.get("atp", [])[:1]:
        if r.get("url"):
            fetch_targets.append(("atp_page", r["url"]))
    for r in all_results.get("partner_portal", [])[:1]:
        if r.get("url"):
            fetch_targets.append(("partner_portal_page", r["url"]))

    page_contents = _fetch_pages_parallel(fetch_targets)

    return {
        "company_name":     company_name,
        "known_products":   known_products or [],
        "product_discovery":product_results,
        "training_programs":all_results.get("training", []),
        "atp_signals":      all_results.get("atp", []),
        "training_catalog": all_results.get("training_catalog", []),
        "partner_ecosystem":all_results.get("partners", []),
        "partner_portal":   all_results.get("partner_portal", []),
        "cs_signals":       all_results.get("cs", []),
        "lms_signals":      all_results.get("lms", []),
        "org_contacts":     (all_results.get("org_senior", []) + all_results.get("org_directors", [])),
        "lab_platform_signals": (all_results.get("lab_skillable", []) + all_results.get("lab_compete", [])),
        "page_contents":    page_contents,
    }


def research_products(company_name: str, selected_products: list[dict]) -> dict:
    """Deep product research phase — purely product-targeted queries.

    Company-level queries have been moved to discover_products() where they run reliably
    in a small focused batch. This phase only runs product-specific queries so the batch
    stays small and DuckDuckGo rate-limiting is not an issue.
    """
    queries = []
    for p in selected_products:
        name = p.get("name", "")
        queries.append((f"tech_{name}",    f"{company_name} {name} deployment installation cloud VM documentation"))
        queries.append((f"train_{name}",   f"{company_name} {name} training certification hands-on lab"))
        queries.append((f"api_{name}",     f"{company_name} {name} REST API CLI PowerShell automation developer documentation"))
        queries.append((f"ai_{name}",      f"{company_name} {name} AI Copilot generative AI features hands-on practice"))
        # Labability intelligence signals
        queries.append((f"marketplace_{name}", f"{name} Azure Marketplace OR AWS Marketplace listing"))
        queries.append((f"docker_{name}",  f"{name} Docker image container deployment GitHub"))
        queries.append((f"nfr_{name}",     f"{name} developer license NFR trial free evaluation"))
        queries.append((f"deploy_{name}",  f"{name} deployment guide system requirements installation prerequisites"))
        queries.append((f"compete_{name}", f"{name} hands-on lab sandbox CloudShare Instruqt Appsembler"))
        # API lifecycle — critical for Gate 1 SaaS and automation scoring
        # Looks for OpenAPI/Swagger specs (highest evidence quality) and explicit DELETE/teardown endpoints
        queries.append((f"openapi_{name}", f"{name} openapi spec swagger site:github.com OR site:readme.io OR site:stoplight.io OR filetype:yaml OR filetype:json"))
        queries.append((f"api_lifecycle_{name}", f"{company_name} {name} REST API provision create configure delete teardown tenant lifecycle"))
        # SaaS delivery path signals — sandbox availability and authentication model
        queries.append((f"sandbox_{name}", f"{company_name} {name} sandbox trial developer account training environment partner"))
        queries.append((f"api_auth_{name}", f"{company_name} {name} API authentication service account OAuth token MFA SSO"))

    all_results = _run_searches_parallel(queries, num_results=3)

    # Fetch up to 5 pages per product:
    #   tech/doc page, training page, API/dev docs, OpenAPI/Swagger spec, API lifecycle
    # Source type classification in _fetch_pages_parallel automatically applies the right
    # depth per URL — api_ref pages (swagger, readme.io/reference, etc.) get 10,000 chars.
    fetch_targets = []
    for p in selected_products[:5]:
        name = p.get("name", "")
        tech_results = all_results.get(f"tech_{name}", [])
        if tech_results and tech_results[0].get("url"):
            fetch_targets.append((name, tech_results[0]["url"]))
        train_results = all_results.get(f"train_{name}", [])
        if train_results and train_results[0].get("url"):
            fetch_targets.append((f"train_{name}", train_results[0]["url"]))
        api_results = all_results.get(f"api_{name}", [])
        if api_results and api_results[0].get("url"):
            fetch_targets.append((f"api_{name}", api_results[0]["url"]))
        # OpenAPI/Swagger spec — fetch top result; classification gives it 10,000 chars
        openapi_results = all_results.get(f"openapi_{name}", [])
        if openapi_results and openapi_results[0].get("url"):
            fetch_targets.append((f"openapi_{name}", openapi_results[0]["url"]))
        # API lifecycle — fetch top result to look for provision/delete endpoints
        lifecycle_results = all_results.get(f"api_lifecycle_{name}", [])
        if lifecycle_results and lifecycle_results[0].get("url"):
            fetch_targets.append((f"api_lifecycle_{name}", lifecycle_results[0]["url"]))
        # ai_, sandbox_, api_auth_ are snippet-only — no page fetch needed

    page_contents = _fetch_pages_parallel(fetch_targets)

    return {
        "company_name":     company_name,
        "selected_products":selected_products,
        "search_results":   all_results,
        "page_contents":    page_contents,
    }
