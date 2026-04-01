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
        Deep per-product scoring + lab maturity. Returns (analysis_id, data dict).
        Runs discrepancy detection after scoring: if deep scores disagree with
        discovery-tier likely_labable classifications, the discovery record is
        patched and the discrepancy is logged.

    refresh(target_id, scope="all")
        Rerun a specific phase on an existing record. scope in
        {"discovery", "products", "all"}. Returns updated data dict.

    expand(company_name, additional_products, analysis_id)
        Add products to an existing analysis without re-scoring what's already there.
        Returns (analysis_id, updated data dict).

    qualify(company_name, force_refresh=False)
        Prospector-mode lightweight scoring: discovery + one-product Claude call,
        no deep research_products() phase. Returns a Prospector-compatible row dict.

    lookup(company_name)
        Pure cache read — no research, no Claude calls.
        Returns {"analysis": dict|None, "discovery": dict|None, "found": bool}.

Vocabulary generation (for Designer)
--------------------------------------
    generate_vocabulary(company_name, analysis_id=None)
        Builds a blended naming vocabulary: ~60% Skillable domain seeds,
        ~40% from the company/product vocabulary extracted from Intelligence data.
        Returns a VocabularyPack dict that Designer draws from for program names,
        lab series titles, and skill level labels.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta

log = logging.getLogger(__name__)

from researcher import discover_products, research_products
from scorer import discover_products_with_claude, score_selected_products, _call_claude
from storage import (
    save_analysis, load_analysis,
    save_discovery, load_discovery,
    find_analysis_by_company_name, find_discovery_by_company_name,
    find_analysis_by_discovery_id,
)
from core import _attach_scores
from config import ANTHROPIC_MODEL

# ---------------------------------------------------------------------------
# Cache TTL — single definition for the whole platform
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return str(uuid.uuid4())[:8]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _labable_tier(product: dict) -> str:
    """Compute the labability tier label from a scored product dict."""
    score = product.get("_total_score", 0)
    if score >= 70:
        return "highly_likely"
    if score >= 45:
        return "likely"
    if score >= 20:
        return "less_likely"
    return "not_likely"


# ---------------------------------------------------------------------------
# Operation 1 — discover
# ---------------------------------------------------------------------------

def discover(company_name: str, known_products: list[str] | None = None,
             force_refresh: bool = False) -> dict:
    """Web research + Claude product identification.

    Returns the discovery dict (including discovery_id). Saves to storage.
    Hits the 45-day cache unless force_refresh=True.

    Callers (Inspector, Prospector) should check discovery["discovery_id"] for
    the storage key they'll pass to score() or caseboard rendering.
    """
    if not force_refresh:
        cached = find_discovery_by_company_name(company_name)
        if cached and cache_is_fresh(cached.get("created_at", "")):
            log.info("Intelligence.discover: cache hit for %s → %s",
                     company_name, cached.get("discovery_id"))
            return cached

    log.info("Intelligence.discover: running research for %s", company_name)
    findings = discover_products(company_name, known_products)
    discovery = discover_products_with_claude(findings)

    # Preserve all raw research signals alongside the Claude output
    for key in ("training_programs", "atp_signals", "training_catalog",
                "partner_ecosystem", "partner_portal", "cs_signals",
                "lms_signals", "org_contacts", "page_contents"):
        discovery[key] = findings.get(key, [])

    discovery["discovery_id"] = _new_id()
    discovery["created_at"] = _now_iso()
    discovery["known_products"] = known_products or []
    save_discovery(discovery["discovery_id"], discovery)

    log.info("Intelligence.discover: saved discovery %s for %s",
             discovery["discovery_id"], company_name)
    return discovery


# ---------------------------------------------------------------------------
# Operation 2 — score
# ---------------------------------------------------------------------------

def score(company_name: str, selected_products: list[dict], discovery_id: str,
          discovery_data: dict | None = None,
          research_cache: dict | None = None,
          force_refresh: bool = False) -> tuple[str, dict]:
    """Deep per-product scoring + lab maturity.

    Returns (analysis_id, data_dict).

    discovery_id     — links this analysis to the source discovery record
    discovery_data   — if provided, used for company context (avoids a storage round-trip)
    research_cache   — optional pre-computed product research results
    force_refresh    — ignored here (callers checked the cache before deciding to call score)

    After scoring, runs discrepancy detection: deep scores that disagree with
    discovery-tier likely_labable values are reconciled and the pattern is logged
    for future prompt improvement.
    """
    if not discovery_data:
        discovery_data = load_discovery(discovery_id) or {}

    # Build research input
    cache = discovery_data.get("_research_cache", {}) if not research_cache else research_cache
    research = {
        "company_name": company_name,
        "selected_products": selected_products,
        "search_results": cache.get("search_results", {}),
        "page_contents": cache.get("page_contents", {}),
        "discovery_data": discovery_data,
    }

    log.info("Intelligence.score: scoring %d products for %s", len(selected_products), company_name)
    analysis = score_selected_products(research)
    analysis.discovery_id = discovery_id
    analysis.total_products_discovered = len(discovery_data.get("products", []))
    analysis_id = save_analysis(analysis)

    # Reload as dict for discrepancy detection and return
    data = load_analysis(analysis_id)
    _attach_scores(data)

    _detect_and_patch_discrepancies(data, discovery_id, discovery_data)

    log.info("Intelligence.score: saved analysis %s for %s", analysis_id, company_name)
    return analysis_id, data


# ---------------------------------------------------------------------------
# Discrepancy detection (internal)
# ---------------------------------------------------------------------------

_TIER_ORDER = {"highly_likely": 0, "likely": 1, "less_likely": 2, "not_likely": 3}


def _detect_and_patch_discrepancies(analysis_data: dict, discovery_id: str,
                                     discovery_data: dict) -> None:
    """Compare deep scoring tiers to discovery-tier likely_labable values.

    If the deep score disagrees by more than one tier, patch the discovery record
    and log the discrepancy pattern for prompt improvement.

    A one-tier difference (e.g. likely → highly_likely) is normal refinement and
    is silently patched. Two-tier+ differences are logged as significant.
    """
    disc_products = {p["name"]: p for p in discovery_data.get("products", []) if p.get("name")}
    if not disc_products:
        return

    patched = False
    for scored_p in analysis_data.get("products", []):
        name = scored_p.get("name", "")
        disc_p = disc_products.get(name)
        if not disc_p:
            continue

        disc_tier = disc_p.get("likely_labable", "not_likely")
        deep_tier = _labable_tier(scored_p)

        disc_rank = _TIER_ORDER.get(disc_tier, 3)
        deep_rank = _TIER_ORDER.get(deep_tier, 3)
        delta = abs(disc_rank - deep_rank)

        if delta == 0:
            continue

        if delta >= 2:
            log.warning(
                "Intelligence discrepancy [%s]: '%s' was %s at discovery → %s after deep scoring "
                "(score=%d). Prompt calibration candidate.",
                discovery_data.get("company_name", "?"), name, disc_tier, deep_tier,
                scored_p.get("_total_score", 0)
            )

        # Patch the discovery record regardless of delta size
        disc_p["likely_labable"] = deep_tier
        patched = True
        log.info("Intelligence: patched likely_labable for '%s' %s → %s", name, disc_tier, deep_tier)

    if patched:
        try:
            save_discovery(discovery_id, discovery_data)
        except Exception as e:
            log.warning("Intelligence: failed to save patched discovery %s: %s", discovery_id, e)


# ---------------------------------------------------------------------------
# Operation 3 — refresh
# ---------------------------------------------------------------------------

def refresh(target_id: str, scope: str = "all") -> dict:
    """Rerun a phase on an existing record. scope: 'discovery' | 'products' | 'all'.

    target_id may be an analysis_id or discovery_id — the function detects which.
    Returns the updated data dict.
    """
    # Try to resolve to analysis + discovery
    analysis_data = load_analysis(target_id)
    if analysis_data:
        discovery_id = analysis_data.get("discovery_id", "")
        discovery_data = load_discovery(discovery_id) if discovery_id else {}
        company_name = analysis_data.get("company_name", "")
    else:
        discovery_data = load_discovery(target_id)
        if not discovery_data:
            raise ValueError(f"No analysis or discovery found for id: {target_id}")
        discovery_id = target_id
        company_name = discovery_data.get("company_name", "")
        analysis_data = None

    if scope in ("discovery", "all"):
        log.info("Intelligence.refresh: re-discovering %s", company_name)
        known = discovery_data.get("known_products") if discovery_data else None
        fresh_discovery = discover(company_name, known_products=known, force_refresh=True)
        # Preserve the original discovery_id so existing analyses remain linked
        fresh_discovery["discovery_id"] = discovery_id
        save_discovery(discovery_id, fresh_discovery)
        discovery_data = fresh_discovery

    if scope in ("products", "all") and analysis_data:
        products = analysis_data.get("products", [])
        selected = [{"name": p["name"]} for p in products]
        _, refreshed_data = score(
            company_name, selected, discovery_id,
            discovery_data=discovery_data,
            force_refresh=True,
        )
        return refreshed_data

    _attach_scores(analysis_data)
    return analysis_data


# ---------------------------------------------------------------------------
# Operation 4 — expand
# ---------------------------------------------------------------------------

def expand(company_name: str, additional_products: list[dict],
           analysis_id: str) -> tuple[str, dict]:
    """Add products to an existing analysis without re-scoring existing ones.

    Returns (analysis_id, updated_data_dict). The analysis_id returned is the
    same as the input — expand updates in place and saves.
    """
    data = load_analysis(analysis_id)
    if not data:
        raise ValueError(f"Analysis not found: {analysis_id}")

    discovery_id = data.get("discovery_id", "")
    discovery_data = load_discovery(discovery_id) if discovery_id else {}

    existing_names = {p["name"] for p in data.get("products", [])}
    new_products = [p for p in additional_products if p.get("name") not in existing_names]
    if not new_products:
        _attach_scores(data)
        return analysis_id, data

    log.info("Intelligence.expand: adding %d products to analysis %s for %s",
             len(new_products), analysis_id, company_name)

    from researcher import research_products
    from scorer import score_selected_products

    research = research_products(company_name, new_products)
    research["discovery_data"] = discovery_data

    from models import CompanyAnalysis
    import dataclasses

    # Score only the new products
    new_analysis = score_selected_products(research)
    new_analysis.discovery_id = discovery_id

    # Merge: keep existing products, append new ones
    # Reload from JSON to get a clean dict
    new_data = load_analysis(save_analysis(new_analysis))
    merged_products = data.get("products", []) + new_data.get("products", [])

    data["products"] = merged_products
    data["analyzed_at"] = _now_iso()

    # Re-save merged data
    from storage import save_analysis as _save
    from models import _parse_response_to_models  # not public but we need it for type

    # Simplest path: overwrite the JSON directly
    import json, os
    from config import DATA_DIR
    filepath = os.path.join(DATA_DIR, f"{analysis_id}.json")
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)

    _attach_scores(data)
    _detect_and_patch_discrepancies(data, discovery_id, discovery_data)
    return analysis_id, data


# ---------------------------------------------------------------------------
# Operation 5 — qualify  (Prospector lightweight path)
# ---------------------------------------------------------------------------

_LABABLE_ORDER = {"highly_likely": 0, "likely": 1, "less_likely": 2, "not_likely": 3}


def qualify(company_name: str, force_refresh: bool = False) -> dict | None:
    """Prospector-mode lightweight scoring.

    Runs: discover() → top-1 product selection → score() with empty research
    (no research_products() call — discovery context only).

    Returns a Prospector-compatible row dict, or None on failure.
    This is the clean, shared version of the logic previously embedded in
    prospector_routes._quick_analyze_company().
    """
    log.info("Intelligence.qualify: %s (force_refresh=%s)", company_name, force_refresh)

    if not force_refresh:
        cached = find_analysis_by_company_name(company_name)
        if cached and cache_is_fresh(cached.get("analyzed_at", "")):
            log.info("Intelligence.qualify: cache hit for %s", company_name)
            return _build_qualify_row(cached, from_cache=True)

    try:
        discovery = discover(company_name, force_refresh=force_refresh)

        org_type = discovery.get("organization_type", "software_company")

        # Academic pre-filter: institutions with no tech programs skip deep scoring
        if org_type == "academic_institution":
            if not _has_academic_tech_programs(discovery):
                return _academic_no_fit_row(company_name, discovery)

        all_products = discovery.get("products", [])
        labable = [p for p in all_products if p.get("likely_labable") != "not_likely"] or all_products
        labable.sort(key=lambda p: _LABABLE_ORDER.get(p.get("likely_labable", "not_likely"), 4))
        selected = labable[:1]
        if not selected:
            return None

        # Score with discovery context only — no research_products() call
        analysis_id, data = score(
            company_name, selected,
            discovery_id=discovery["discovery_id"],
            discovery_data=discovery,
            research_cache={"search_results": {}, "page_contents": {}},
        )
        return _build_qualify_row(data, discovery=discovery, from_cache=False)

    except Exception:
        log.exception("Intelligence.qualify failed for %s", company_name)
        return None


def _build_qualify_row(data: dict, discovery: dict | None = None,
                        from_cache: bool = False) -> dict:
    """Build a Prospector row dict from a scored analysis data dict."""
    _attach_scores(data)
    from core import _fmt_ondemand, _fmt_cert

    products = data.get("products") or []
    top_product = products[0] if products else {}
    lab_score = top_product.get("_total_score", 0)
    pr_total = data["_pr_total"]
    composite = data["_composite_score"]
    org_type = data.get("organization_type", "software_company")

    contacts = top_product.get("contacts") or []
    if org_type == "academic_institution":
        dm = _pick_academic_contact(contacts)
        dm2 = next((c for c in contacts if c != dm), None)
    else:
        dm = (next((c for c in contacts if c.get("role_type") == "decision_maker"), None)
              or (contacts[0] if contacts else None))
        dm2 = (next((c for c in contacts if c != dm and c.get("role_type") in ("influencer", "champion")), None)
               or next((c for c in contacts if c != dm), None))

    # Load discovery for product counts + partnership signals
    disc = discovery
    if disc is None:
        discovery_id = data.get("discovery_id")
        disc = load_discovery(discovery_id) if discovery_id else {}

    all_disc = (disc or {}).get("products", []) or products
    total_highly = sum(1 for p in all_disc if p.get("likely_labable") == "highly_likely")
    total_likely = sum(1 for p in all_disc if p.get("likely_labable") == "likely")
    total_not    = sum(1 for p in all_disc if p.get("likely_labable") in ("less_likely", "not_likely"))
    ps = (disc or {}).get("partnership_signals") or {}

    skillable_path = top_product.get("skillable_path", "")
    if org_type == "academic_institution":
        academic_sigs = (disc or {}).get("academic_signals") or {}
        school_name = academic_sigs.get("engineering_school_name")
        has_tech = _has_academic_tech_programs(disc or {})
        skillable_path = _derive_academic_path(lab_score, school_name, has_tech)
    else:
        skillable_path = _fmt_labability_method(skillable_path)

    row = {
        "company_name": data.get("company_name", ""),
        "company_url":  data.get("company_url", ""),
        "top_product":  top_product.get("name", ""),
        "lab_score":    lab_score,
        "lab_maturity_score": pr_total,
        "composite_score":    composite,
        "skillable_path":     skillable_path,
        "top_contact_name":    dm.get("name", "")         if dm  else "",
        "top_contact_title":   dm.get("title", "")        if dm  else "",
        "top_contact_linkedin":dm.get("linkedin_url", "") if dm  else "",
        "second_contact_name":    dm2.get("name", "")         if dm2 else "",
        "second_contact_title":   dm2.get("title", "")        if dm2 else "",
        "second_contact_linkedin":dm2.get("linkedin_url", "") if dm2 else "",
        "analysis_id":         data.get("analysis_id", ""),
        "total_highly_labable":total_highly,
        "total_likely_labable":total_likely,
        "total_not_labable":   total_not,
        "atp_program":         ps.get("atp_program") or "",
        "channel_program":     ps.get("channel_program") or "",
        "ondemand_library":    _fmt_ondemand(ps.get("ondemand_library")),
        "cert_program":        _fmt_cert(ps.get("cert_program")),
        "existing_lab_partner":ps.get("existing_lab_partner") or "",
        "ilt_vilt":            "✓" if ps.get("ilt_vilt") else "",
        "gray_market":         "✓" if ps.get("gray_market") else "",
    }
    if from_cache:
        row["_from_cache"] = True
        row["_cache_date"] = _fmt_cache_date(data.get("analyzed_at", ""))
    return row


def _academic_no_fit_row(company_name: str, discovery: dict) -> dict:
    return {
        "company_name": discovery.get("company_name", company_name),
        "company_url":  discovery.get("company_url", ""),
        "top_product": "", "lab_score": 0, "lab_maturity_score": 0,
        "composite_score": 0, "skillable_path": "Not a Fit",
        "top_contact_name": "", "top_contact_title": "", "top_contact_linkedin": "",
        "second_contact_name": "", "second_contact_title": "", "second_contact_linkedin": "",
        "analysis_id": "",
        "total_highly_labable": 0, "total_likely_labable": 0, "total_not_labable": 0,
        "atp_program": "", "channel_program": "", "ondemand_library": "",
        "cert_program": "", "existing_lab_partner": "", "ilt_vilt": "", "gray_market": "",
        "_academic_prefilter": True,
    }


# ---------------------------------------------------------------------------
# Operation 6 — lookup  (cache read only)
# ---------------------------------------------------------------------------

def lookup(company_name: str) -> dict:
    """Pure cache read — no research, no Claude calls.

    Returns {"analysis": dict|None, "discovery": dict|None, "found": bool}.
    "found" is True if either an analysis or discovery exists.
    """
    analysis = find_analysis_by_company_name(company_name)
    if analysis:
        _attach_scores(analysis)

    discovery_id = (analysis or {}).get("discovery_id")
    discovery = load_discovery(discovery_id) if discovery_id else find_discovery_by_company_name(company_name)

    found = bool(analysis or discovery)
    return {"analysis": analysis, "discovery": discovery, "found": found}


# ---------------------------------------------------------------------------
# Vocabulary generation  (Designer fuel)
# ---------------------------------------------------------------------------

_SKILLABLE_SEEDS = [
    "skill", "lab", "hands-on", "build", "configure", "deploy", "enable",
    "certify", "practice", "validate", "master", "operate", "mission",
    "challenge", "scenario", "prove", "live", "ready", "achieve", "real",
    "job-ready", "proficiency", "craft", "forge", "ground", "arena", "quest",
]

_VOCABULARY_PROMPT = """You are a creative naming consultant for Skillable, a hands-on lab platform.
Your job is to generate a fun, memorable naming vocabulary for a training program.

You will be given:
1. The SKILLABLE vocabulary seeds — core platform/learning concepts
2. The COMPANY vocabulary seeds — extracted from their products and domain

Your output must be a JSON object with these keys:

{
  "program_name_seeds": [
    // 4-6 short, punchy program name concepts (2-4 words each)
    // Mix Skillable + company vocabulary; can be playful portmanteaus
    // Examples: "FortiSkills Live", "ConfigQuest", "CohesityAcademy Forge"
  ],
  "lab_series_labels": [
    // 4-6 series naming patterns (noun + action/concept)
    // Used to group related labs into a series
    // Examples: "Deploy Series", "Admin Arena", "Config Challenge"
  ],
  "skill_level_labels": {
    "beginner": "...",       // Fun alternative to "Beginner" (e.g. "Explorer", "Recruit", "Initiate")
    "intermediate": "...",   // e.g. "Practitioner", "Builder", "Operator"
    "advanced": "..."        // e.g. "Expert", "Architect", "Master"
  },
  "action_verb_palette": [
    // 6-8 strong action verbs for lab titles
    // Company-specific where possible (e.g. "Configure", "Provision", "Orchestrate")
  ],
  "domain_terms": [
    // 5-8 extracted company/product domain terms that should appear in program names
    // These are the 40% company-specific contribution
  ]
}

Rules:
- Approximately 60% of the vocabulary should draw from Skillable seeds
- Approximately 40% should draw from the company/product vocabulary
- Keep it professional but allow warmth and energy — these are for learners
- Avoid generic words like "training", "course", "module" (boring)
- Portmanteaus and compound words are encouraged
- Return only the JSON object, no explanation"""


def generate_vocabulary(company_name: str, analysis_id: str | None = None) -> dict:
    """Generate a blended naming vocabulary pack for Designer.

    Draws ~60% from Skillable's domain vocabulary and ~40% from the company's
    own product and domain language extracted from Intelligence data.

    Returns a VocabularyPack dict. If the analysis or discovery is not found,
    falls back to Skillable-only vocabulary.
    """
    # Gather company/product terms from Intelligence data
    company_seeds = []

    if analysis_id:
        data = load_analysis(analysis_id)
        if data:
            _attach_scores(data)
            # Extract product names + categories + domain terms
            for p in data.get("products", []):
                name = p.get("name", "")
                if name:
                    company_seeds.append(name)
                    # Add abbreviated/stem version if multi-word (e.g. "Data Fabric" → "Fabric")
                    words = name.split()
                    if len(words) > 1:
                        company_seeds.extend(words)
                cat = p.get("category", "")
                if cat:
                    company_seeds.append(cat)
                # Pull meaningful words from lab_highlight
                highlight = p.get("lab_highlight", "")
                if highlight:
                    # Extract capitalized words as domain terms
                    for word in highlight.split():
                        w = word.strip(".,;:()").replace("-", "")
                        if w and w[0].isupper() and len(w) > 3:
                            company_seeds.append(w)

            company_name_actual = data.get("company_name", company_name)
        else:
            company_name_actual = company_name
    else:
        # Try lookup for just the discovery
        cached = lookup(company_name)
        company_name_actual = company_name
        if cached["discovery"]:
            for p in cached["discovery"].get("products", []):
                name = p.get("name", "")
                if name:
                    company_seeds.append(name)
                    company_seeds.extend(name.split())

    # Deduplicate and limit
    seen = set()
    unique_company = []
    for t in company_seeds:
        t_clean = t.strip()
        if t_clean and t_clean.lower() not in seen and len(t_clean) > 2:
            seen.add(t_clean.lower())
            unique_company.append(t_clean)
    unique_company = unique_company[:20]

    user_content = f"""Company: {company_name_actual}

SKILLABLE vocabulary seeds (use ~60%):
{", ".join(_SKILLABLE_SEEDS)}

COMPANY vocabulary seeds (use ~40%):
{", ".join(unique_company) if unique_company else "(none found — use Skillable seeds only)"}

Generate the vocabulary pack for {company_name_actual}'s training program."""

    try:
        result = _call_claude(_VOCABULARY_PROMPT, user_content, max_tokens=1200)
        # Ensure required keys are present
        result.setdefault("program_name_seeds", [])
        result.setdefault("lab_series_labels", [])
        result.setdefault("skill_level_labels", {"beginner": "Explorer", "intermediate": "Practitioner", "advanced": "Expert"})
        result.setdefault("action_verb_palette", [])
        result.setdefault("domain_terms", unique_company[:5])
        result["_company_name"] = company_name_actual
        result["_generated_at"] = _now_iso()
        log.info("Intelligence.generate_vocabulary: generated for %s (%d program seeds)",
                 company_name_actual, len(result["program_name_seeds"]))
        return result
    except Exception as e:
        log.warning("Intelligence.generate_vocabulary failed for %s: %s", company_name, e)
        return {
            "program_name_seeds": [f"{company_name_actual} Skills Lab", f"{company_name_actual} Live Lab"],
            "lab_series_labels": ["Deploy Series", "Config Challenge", "Admin Arena"],
            "skill_level_labels": {"beginner": "Explorer", "intermediate": "Practitioner", "advanced": "Expert"},
            "action_verb_palette": ["Configure", "Deploy", "Validate", "Operate", "Build", "Prove"],
            "domain_terms": unique_company[:5],
            "_company_name": company_name_actual,
            "_generated_at": _now_iso(),
            "_fallback": True,
        }


# ---------------------------------------------------------------------------
# Prospector helper functions  (shared with qualify and prospector_routes)
# ---------------------------------------------------------------------------

_ACADEMIC_TECH_CATEGORIES = {
    "Computer Science", "Cybersecurity", "Cloud Computing", "Information Technology",
    "Engineering", "Data Science", "Software Engineering", "Network Engineering",
    "Academic Program", "Technology Platform",
}

_ACADEMIC_CONTACT_KEYWORDS = ("faculty", "curriculum", "dean", "professor", "chair",
                               "director", "ed tech", "edtech", "learning technology")


def _has_academic_tech_programs(discovery: dict) -> bool:
    academic_sigs = discovery.get("academic_signals") or {}
    if academic_sigs.get("tech_program_areas"):
        return True
    return any(p.get("category", "") in _ACADEMIC_TECH_CATEGORIES
               for p in discovery.get("products", []))


def _pick_academic_contact(contacts: list) -> dict | None:
    for kw in _ACADEMIC_CONTACT_KEYWORDS:
        match = next((c for c in contacts if kw in (c.get("title") or "").lower()), None)
        if match:
            return match
    return contacts[0] if contacts else None


_PATH_LABELS = {
    "A1": "Cloud Slice", "A2": "Custom API",
    "A":  "Cloud Slice", "B":  "VM Lab", "C": "Simulation",
}


def _fmt_labability_method(path: str) -> str:
    return _PATH_LABELS.get(path or "", "")


def _derive_academic_path(lab_score: int, school_name: str | None,
                           has_tech_programs: bool) -> str:
    if not has_tech_programs:
        return "Not a Fit"
    if school_name:
        return school_name
    return "Academic — High Potential" if lab_score >= 40 else "Academic — Emerging"


def _fmt_cache_date(analyzed_at: str) -> str:
    if not analyzed_at:
        return ""
    try:
        dt = datetime.fromisoformat(analyzed_at.replace("Z", "+00:00"))
        return f"{dt.month}/{dt.day}/{dt.year}"
    except Exception:
        return ""
