"""Storage layer for the Skillable Intelligence Platform.

Three data domains, stored separately from day one (GP1, architectural separation):
  - product_data/    — what products are, labability assessments
  - company_intel/   — fit scores, badges, contacts, ACV (internal-only)
  - program_data/    — Designer lab programs (scoped per program)

Each domain is a separate directory. No mixing. When auth comes later,
it's access control on clean boundaries — not a retrofit.

All writes use atomic temp-file + os.replace() pattern.
Read-modify-write operations protected by threading.Lock().
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger(__name__)

_BASE_DIR = os.path.join(os.path.dirname(__file__), "data")
_PRODUCT_DIR = os.path.join(_BASE_DIR, "product_data")
_COMPANY_DIR = os.path.join(_BASE_DIR, "company_intel")
_PROGRAM_DIR = os.path.join(_BASE_DIR, "program_data")

# Create all three domain directories
for _d in (_PRODUCT_DIR, _COMPANY_DIR, _PROGRAM_DIR):
    os.makedirs(_d, exist_ok=True)

_write_lock = threading.Lock()


# ═══════════════════════════════════════════════════════════════════════════════
# Atomic file operations
# ═══════════════════════════════════════════════════════════════════════════════

def _atomic_write(filepath: str, data: dict) -> None:
    """Write JSON atomically — temp file + os.replace()."""
    dir_path = os.path.dirname(filepath)
    with _write_lock:
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp_path, filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


def _read_json(filepath: str) -> Optional[dict]:
    """Read a JSON file. Returns None if not found."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.error("Failed to read %s: %s", filepath, e)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Discovery Storage (Company Intelligence domain)
# ═══════════════════════════════════════════════════════════════════════════════

def save_discovery(discovery_id: str, data: dict) -> str:
    """Save a discovery record. Returns the discovery_id.

    CONTRACT: the caller MUST set `_scoring_logic_version` and `created_at`
    on the data before calling save_discovery. The storage layer no longer
    auto-stamps either field — see save_analysis docstring for the rationale.
    """
    if not data.get("_scoring_logic_version"):
        raise ValueError(
            f"save_discovery({discovery_id}): _scoring_logic_version is missing. "
            f"The intelligence layer (intelligence.discover) must stamp "
            f"this field before calling save_discovery."
        )
    if not data.get("created_at"):
        raise ValueError(
            f"save_discovery({discovery_id}): created_at is missing. "
            f"The intelligence layer must set this on every discovery boundary."
        )
    filepath = os.path.join(_COMPANY_DIR, f"discovery_{discovery_id}.json")
    _atomic_write(filepath, data)
    log.info("Saved discovery %s (logic version %s, created_at %s)",
             discovery_id, data["_scoring_logic_version"], data["created_at"])
    return discovery_id


def load_discovery(discovery_id: str) -> Optional[dict]:
    """Load a discovery record by ID."""
    filepath = os.path.join(_COMPANY_DIR, f"discovery_{discovery_id}.json")
    return _read_json(filepath)


def _normalize_company_name(name: str) -> str:
    """Normalize company name for matching — catches 'Cisco' vs 'Cisco Systems',
    'Google' vs 'Google Cloud', 'VMware (by Broadcom)' vs 'VMware by Broadcom'.

    Used by find_discovery_by_company_name and the Prospector dedup logic.
    Shared function — Define-Once for name normalization.
    """
    import re
    key = name.lower().strip()
    key = re.sub(r'\s*\(.*?\)', '', key)          # remove parentheticals
    key = re.sub(r'\s+by\s+\w+$', '', key)         # "VMware by Broadcom" → "VMware"
    key = re.sub(r',?\s*(inc\.?|corp\.?|llc|ltd\.?|limited|plc|systems|technologies|group|corporation)\s*$', '', key)
    # Remove common product/division suffixes that differ between searches
    key = re.sub(r'\s+(cloud|platform|software|labs|digital|online|services)\s*$', '', key)
    key = re.sub(r'\s+', ' ', key).strip()
    return key


def find_discovery_by_company_name(company_name: str) -> Optional[dict]:
    """Find the most recent discovery for a company by normalized name.

    Uses _normalize_company_name to match 'Google' → 'Google Cloud',
    'Cisco' → 'Cisco Systems', etc. Returns the most recent discovery
    when multiple exist for the same normalized name.
    """
    if not company_name:
        return None
    target = _normalize_company_name(company_name)
    best = None
    best_time = ""
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("discovery_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        data = _read_json(filepath)
        if data and _normalize_company_name(data.get("company_name", "")) == target:
            created = data.get("created_at", "")
            if created > best_time:
                best = data
                best_time = created
    return best


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Storage (Company Intelligence domain)
# ═══════════════════════════════════════════════════════════════════════════════

def save_analysis(analysis) -> str:
    """Save an analysis record. Accepts CompanyAnalysis or dict.

    CONTRACT: the caller MUST set `_scoring_logic_version` and `analyzed_at`
    on the data before calling save_analysis. The storage layer no longer
    auto-stamps either field — that allowed save_analysis to lie about
    when an analysis was actually scored (CRIT-6 / CRIT-10 in code-review-
    2026-04-07.md). The intelligence layer (intelligence.score and
    discover) is the only place that should set these stamps, and it does
    so atomically with the actual scoring work via the _stamp_for_save
    helper.

    Briefcase generation correctly preserves existing stamps because it
    loads an analysis from disk (which already has both stamps set from
    its previous scoring) and never overwrites them.

    save_analysis will REJECT any write that doesn't have both stamps set
    on the dict, with a clear error message pointing at the contract.

    Returns the analysis_id.
    """
    if hasattr(analysis, "__dataclass_fields__"):
        # Convert dataclass to dict for JSON serialization
        import dataclasses
        data = dataclasses.asdict(analysis)
        analysis_id = analysis.analysis_id
    else:
        data = analysis
        analysis_id = data.get("analysis_id", "")

    if not analysis_id:
        import uuid
        analysis_id = str(uuid.uuid4())[:8]
        data["analysis_id"] = analysis_id

    # Enforce the contract — both stamps must be set by the caller.
    if not data.get("_scoring_logic_version"):
        raise ValueError(
            f"save_analysis({analysis_id}): _scoring_logic_version is missing. "
            f"The intelligence layer (intelligence.score / discover) must "
            f"stamp this field via _stamp_for_save before calling save_analysis. "
            f"If this is a briefcase save, the loaded analysis dict should already "
            f"have the stamp from its previous scoring — verify the load path."
        )
    if not data.get("analyzed_at"):
        raise ValueError(
            f"save_analysis({analysis_id}): analyzed_at is missing. "
            f"The intelligence layer must set this on every score boundary. "
            f"Briefcase saves should preserve the existing analyzed_at from the "
            f"loaded dict (briefcase generation does not bump the scoring timestamp)."
        )

    # Belt-and-braces: dedupe products by (name, category) on every save,
    # keeping the LAST occurrence (which is the freshest score from the
    # cache-and-append flow). MED-6 in code-review-2026-04-07.md: deduping
    # by name alone would lose legitimate same-name-different-category
    # products like "Azure DevOps" (cloud) vs "Azure DevOps Server" (on-prem),
    # or distinct e-learning vs ILT versions of the same training program.
    # The (name, category) tuple is narrow enough to keep distinct products
    # apart while still catching true duplicates from re-score collisions.
    products = data.get("products") or []
    if products:
        seen: dict[tuple[str, str], dict] = {}
        for p in products:
            nm = (p.get("name") or "").strip()
            cat = (p.get("category") or "").strip()
            if nm:
                seen[(nm, cat)] = p   # last write wins
        if len(seen) != len(products):
            log.info("save_analysis %s: deduped %d products → %d unique",
                     analysis_id, len(products), len(seen))
            data["products"] = list(seen.values())

    filepath = os.path.join(_COMPANY_DIR, f"analysis_{analysis_id}.json")
    _atomic_write(filepath, data)
    log.info("Saved analysis %s (logic version %s, analyzed_at %s)",
             analysis_id, data["_scoring_logic_version"], data["analyzed_at"])
    return analysis_id


def load_analysis(analysis_id: str) -> Optional[dict]:
    """Load an analysis record by ID."""
    filepath = os.path.join(_COMPANY_DIR, f"analysis_{analysis_id}.json")
    return _read_json(filepath)


def find_analysis_by_company_name(company_name: str) -> Optional[dict]:
    """Find the most recent analysis for a company by normalized name."""
    if not company_name:
        return None
    target = _normalize_company_name(company_name)
    best = None
    best_time = ""
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("analysis_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        data = _read_json(filepath)
        if data and _normalize_company_name(data.get("company_name", "")) == target:
            analyzed = data.get("analyzed_at", "")
            if analyzed > best_time:
                best = data
                best_time = analyzed
    return best


def find_analysis_by_discovery_id(discovery_id: str) -> Optional[dict]:
    """Find the MOST RECENT analysis linked to a specific discovery.

    Multiple analyses may exist for the same discovery (from before the
    stable-URL/cache logic was added). Always pick the most recent so cache
    hits use the freshest data — and so newly appended products land on the
    same analysis the user is viewing.
    """
    if not discovery_id:
        return None
    candidates = []
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("analysis_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            continue
        data = _read_json(filepath)
        if data and data.get("discovery_id") == discovery_id:
            candidates.append((mtime, data))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def list_discoveries() -> list[dict]:
    """List all discoveries, most recent first.

    Used by the typeahead API to suggest cached companies.
    Returns lightweight dicts — only the fields needed for display.
    """
    discoveries = []
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("discovery_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        data = _read_json(filepath)
        if data:
            discoveries.append(data)
    discoveries.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return discoveries


def list_analyses() -> list[dict]:
    """List all analyses, most recent first."""
    analyses = []
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("analysis_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        data = _read_json(filepath)
        if data:
            analyses.append(data)
    analyses.sort(key=lambda a: a.get("analyzed_at", ""), reverse=True)
    return analyses


# ═══════════════════════════════════════════════════════════════════════════════
# Program Storage (Program Data domain — Designer)
# ═══════════════════════════════════════════════════════════════════════════════

def save_program(program_id: str, data: dict) -> str:
    """Save a Designer program."""
    filepath = os.path.join(_PROGRAM_DIR, f"program_{program_id}.json")
    _atomic_write(filepath, data)
    return program_id


def load_program(program_id: str) -> Optional[dict]:
    """Load a Designer program by ID."""
    filepath = os.path.join(_PROGRAM_DIR, f"program_{program_id}.json")
    return _read_json(filepath)


def list_programs() -> list[dict]:
    """List all programs."""
    programs = []
    for filename in os.listdir(_PROGRAM_DIR):
        if not filename.startswith("program_"):
            continue
        filepath = os.path.join(_PROGRAM_DIR, filename)
        data = _read_json(filepath)
        if data:
            programs.append(data)
    return programs


# ═══════════════════════════════════════════════════════════════════════════════
# Competitor Candidates (Company Intelligence domain)
# ═══════════════════════════════════════════════════════════════════════════════

_COMPETITOR_FILE = os.path.join(_COMPANY_DIR, "_competitor_candidates.json")


def save_competitor_candidates(candidates: list[dict]) -> None:
    """Save competitor candidates for Prospector feed."""
    _atomic_write(_COMPETITOR_FILE, {"candidates": candidates})


def load_competitor_candidates() -> list[dict]:
    """Load competitor candidates."""
    data = _read_json(_COMPETITOR_FILE)
    return data.get("candidates", []) if data else []
