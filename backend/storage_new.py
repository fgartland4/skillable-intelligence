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

_BASE_DIR = os.path.join(os.path.dirname(__file__), "data_new")
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
    """Save a discovery record. Returns the discovery_id."""
    filepath = os.path.join(_COMPANY_DIR, f"discovery_{discovery_id}.json")
    _atomic_write(filepath, data)
    log.info("Saved discovery %s", discovery_id)
    return discovery_id


def load_discovery(discovery_id: str) -> Optional[dict]:
    """Load a discovery record by ID."""
    filepath = os.path.join(_COMPANY_DIR, f"discovery_{discovery_id}.json")
    return _read_json(filepath)


def find_discovery_by_company_name(company_name: str) -> Optional[dict]:
    """Find the most recent discovery for a company by name."""
    if not company_name:
        return None
    target = company_name.lower().strip()
    best = None
    best_time = ""
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("discovery_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        data = _read_json(filepath)
        if data and data.get("company_name", "").lower().strip() == target:
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

    filepath = os.path.join(_COMPANY_DIR, f"analysis_{analysis_id}.json")
    _atomic_write(filepath, data)
    log.info("Saved analysis %s", analysis_id)
    return analysis_id


def load_analysis(analysis_id: str) -> Optional[dict]:
    """Load an analysis record by ID."""
    filepath = os.path.join(_COMPANY_DIR, f"analysis_{analysis_id}.json")
    return _read_json(filepath)


def find_analysis_by_company_name(company_name: str) -> Optional[dict]:
    """Find the most recent analysis for a company by name."""
    if not company_name:
        return None
    target = company_name.lower().strip()
    best = None
    best_time = ""
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("analysis_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        data = _read_json(filepath)
        if data and data.get("company_name", "").lower().strip() == target:
            analyzed = data.get("analyzed_at", "")
            if analyzed > best_time:
                best = data
                best_time = analyzed
    return best


def find_analysis_by_discovery_id(discovery_id: str) -> Optional[dict]:
    """Find an analysis linked to a specific discovery."""
    if not discovery_id:
        return None
    for filename in os.listdir(_COMPANY_DIR):
        if not filename.startswith("analysis_"):
            continue
        filepath = os.path.join(_COMPANY_DIR, filename)
        data = _read_json(filepath)
        if data and data.get("discovery_id") == discovery_id:
            return data
    return None


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
