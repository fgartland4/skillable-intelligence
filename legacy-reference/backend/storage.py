"""JSON file storage for analysis and discovery results.

All writes use atomic temp-file + os.replace() to prevent corruption from
concurrent access.  Read-modify-write operations (append_poor_fit_feedback,
save_competitor_candidates) use a threading lock to serialize updates.

A lightweight in-memory company-name index accelerates the three
find_*_by_company_name() lookups that previously required a full directory
scan + JSON parse on every call.
"""

import json
import logging
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone

log = logging.getLogger(__name__)
from dataclasses import asdict
from models import CompanyAnalysis, compute_product_score
from config import DATA_DIR

DISCOVERY_DIR = os.path.join(os.path.dirname(__file__), "data", "discoveries")
BATCH_DIR = os.path.join(os.path.dirname(__file__), "data", "batch")
FEEDBACK_DIR = os.path.join(os.path.dirname(__file__), "data", "feedback")
DESIGNER_DIR = os.path.join(os.path.dirname(__file__), "data", "designer")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DISCOVERY_DIR, exist_ok=True)
os.makedirs(BATCH_DIR, exist_ok=True)
os.makedirs(FEEDBACK_DIR, exist_ok=True)
os.makedirs(DESIGNER_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Atomic write helper
# ---------------------------------------------------------------------------

def _atomic_write_json(filepath: str, data, *, indent: int = 2, default=None) -> None:
    """Write JSON atomically: write to a temp file in the same directory, then
    os.replace() into the target path.  os.replace() is atomic on both POSIX
    and Windows (same volume), so concurrent readers never see a half-written file."""
    dirpath = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=default)
        os.replace(tmp_path, filepath)
    except BaseException:
        # Clean up the temp file if anything goes wrong
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Read-modify-write lock for feedback files (poor_fit.json,
# competitor_candidates.json) that are appended to by multiple threads.
# ---------------------------------------------------------------------------

_feedback_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Company-name index — avoids full directory scan + JSON parse on every lookup
# ---------------------------------------------------------------------------
# Maps lowercase company name → (filepath, mtime) for the most recent file.
# Populated lazily; invalidated on every save.

_analysis_index: dict[str, tuple[str, float]] = {}   # name → (filepath, mtime)
_discovery_index: dict[str, tuple[str, float]] = {}   # name → (filepath, mtime)
_index_lock = threading.Lock()
_analysis_index_built = False
_discovery_index_built = False


def _rebuild_analysis_index() -> None:
    """Scan DATA_DIR once and build the company-name → filepath index."""
    global _analysis_index_built
    idx: dict[str, tuple[str, float]] = {}
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(DATA_DIR, filename)
            try:
                mtime = os.path.getmtime(filepath)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("company_name", "").lower().strip()
                if name:
                    existing = idx.get(name)
                    if existing is None or mtime > existing[1]:
                        idx[name] = (filepath, mtime)
            except Exception as e:
                log.warning("Index build: skipping corrupted analysis %s: %s", filename, e)
    with _index_lock:
        _analysis_index.clear()
        _analysis_index.update(idx)
        _analysis_index_built = True


def _rebuild_discovery_index() -> None:
    """Scan DISCOVERY_DIR once and build the company-name → filepath index."""
    global _discovery_index_built
    idx: dict[str, tuple[str, float]] = {}
    if os.path.exists(DISCOVERY_DIR):
        for filename in os.listdir(DISCOVERY_DIR):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(DISCOVERY_DIR, filename)
            try:
                mtime = os.path.getmtime(filepath)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("company_name", "").lower().strip()
                if name:
                    existing = idx.get(name)
                    if existing is None or mtime > existing[1]:
                        idx[name] = (filepath, mtime)
            except Exception as e:
                log.warning("Index build: skipping corrupted discovery %s: %s", filename, e)
    with _index_lock:
        _discovery_index.clear()
        _discovery_index.update(idx)
        _discovery_index_built = True


def _update_analysis_index(filepath: str, company_name: str) -> None:
    """Update the index after a save (avoids a full rebuild)."""
    name = company_name.lower().strip()
    if not name:
        return
    mtime = os.path.getmtime(filepath)
    with _index_lock:
        _analysis_index[name] = (filepath, mtime)


def _update_discovery_index(filepath: str, company_name: str) -> None:
    """Update the index after a save (avoids a full rebuild)."""
    name = company_name.lower().strip()
    if not name:
        return
    mtime = os.path.getmtime(filepath)
    with _index_lock:
        _discovery_index[name] = (filepath, mtime)


# ---------------------------------------------------------------------------
# Discovery storage
# ---------------------------------------------------------------------------

def save_discovery(discovery_id: str, data: dict) -> str:
    filepath = os.path.join(DISCOVERY_DIR, f"{discovery_id}.json")
    _atomic_write_json(filepath, data)
    _update_discovery_index(filepath, data.get("company_name", ""))
    return discovery_id


def load_discovery(discovery_id: str) -> dict | None:
    filepath = os.path.join(DISCOVERY_DIR, f"{discovery_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Analysis storage
# ---------------------------------------------------------------------------

def save_analysis(analysis: CompanyAnalysis) -> str:
    if not analysis.analysis_id:
        analysis.analysis_id = str(uuid.uuid4())[:8]
    filepath = os.path.join(DATA_DIR, f"{analysis.analysis_id}.json")
    _atomic_write_json(filepath, asdict(analysis), default=str)
    _update_analysis_index(filepath, analysis.company_name)
    return analysis.analysis_id


def save_analysis_dict(analysis_id: str, data: dict) -> str:
    """Save a pre-assembled analysis dict (e.g. merged cached + newly scored products)."""
    filepath = os.path.join(DATA_DIR, f"{analysis_id}.json")
    _atomic_write_json(filepath, data, default=str)
    _update_analysis_index(filepath, data.get("company_name", ""))
    return analysis_id


def load_analysis(analysis_id: str) -> dict | None:
    filepath = os.path.join(DATA_DIR, f"{analysis_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def find_analysis_by_company_name(company_name: str) -> dict | None:
    """Return the most recent full analysis dict for a company name (case-insensitive), or None."""
    global _analysis_index_built
    if not _analysis_index_built:
        _rebuild_analysis_index()
    needle = company_name.lower().strip()
    with _index_lock:
        entry = _analysis_index.get(needle)
    if entry is None:
        return None
    filepath, _ = entry
    if not os.path.exists(filepath):
        # File was deleted externally — remove stale index entry
        with _index_lock:
            _analysis_index.pop(needle, None)
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning("Failed to load indexed analysis %s: %s", filepath, e)
        return None


def find_discovery_by_company_name(company_name: str) -> dict | None:
    """Return the most recent discovery dict for a company name (case-insensitive), or None."""
    global _discovery_index_built
    if not _discovery_index_built:
        _rebuild_discovery_index()
    needle = company_name.lower().strip()
    with _index_lock:
        entry = _discovery_index.get(needle)
    if entry is None:
        return None
    filepath, _ = entry
    if not os.path.exists(filepath):
        with _index_lock:
            _discovery_index.pop(needle, None)
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning("Failed to load indexed discovery %s: %s", filepath, e)
        return None


def find_analysis_by_discovery_id(discovery_id: str) -> dict | None:
    """Return the most recent analysis that came from this discovery_id, or None."""
    if not os.path.exists(DATA_DIR):
        return None
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(DATA_DIR, f)), reverse=True)
    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("discovery_id") == discovery_id:
                return {
                    "analysis_id": data.get("analysis_id", filename.replace(".json", "")),
                    "company_name": data.get("company_name", ""),
                    "analyzed_at": data.get("analyzed_at", ""),
                }
        except Exception as e:
            log.warning("Skipping corrupted analysis file %s: %s", filename, e)
            continue
    return None


# ---------------------------------------------------------------------------
# Prospector storage
# ---------------------------------------------------------------------------

def save_prospector_run(job_id: str, data: dict) -> None:
    filepath = os.path.join(BATCH_DIR, f"{job_id}.json")
    _atomic_write_json(filepath, data)


def load_prospector_run(job_id: str) -> dict | None:
    filepath = os.path.join(BATCH_DIR, f"{job_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Feedback storage (read-modify-write — protected by _feedback_lock)
# ---------------------------------------------------------------------------

def append_poor_fit_feedback(feedback: dict) -> None:
    """Append a poor fit flag (with optional reason) to the feedback log."""
    filepath = os.path.join(FEEDBACK_DIR, "poor_fit.json")
    with _feedback_lock:
        existing = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except Exception as e:
                    log.warning("poor_fit.json corrupted, starting fresh: %s", e)
                    existing = []
        existing.append(feedback)
        _atomic_write_json(filepath, existing)


def load_poor_fit_companies() -> set:
    """Return lowercase set of company names previously flagged as poor fit."""
    filepath = os.path.join(FEEDBACK_DIR, "poor_fit.json")
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return {d.get("company_name", "").lower() for d in data}
        except Exception as e:
            log.warning("Failed to load poor_fit.json: %s", e)
            return set()


def list_analyses() -> list[dict]:
    results = []
    if not os.path.exists(DATA_DIR):
        return results
    for filename in sorted(os.listdir(DATA_DIR), reverse=True):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            top_score = 0
            total_hours_low = 0
            total_hours_high = 0
            for p in data.get("products") or []:
                total = compute_product_score(p)
                if total > top_score:
                    top_score = total
                cp = p.get("consumption_potential") or {}
                total_hours_low += cp.get("annual_hours_low", 0)
                total_hours_high += cp.get("annual_hours_high", 0)
            results.append({
                "analysis_id": data.get("analysis_id", filename.replace(".json", "")),
                "company_name": data.get("company_name", "Unknown"),
                "analyzed_at": data.get("analyzed_at", ""),
                "product_count": len(data.get("products") or []),
                "top_score": top_score,
                "total_hours_low": total_hours_low,
                "total_hours_high": total_hours_high,
            })
        except Exception as e:
            log.warning("Skipping corrupted analysis file %s: %s", filename, e)
            continue
    return results


def load_all_discoveries() -> list[dict]:
    """Return all discovery dicts, newest-modified first."""
    results = []
    if not os.path.exists(DISCOVERY_DIR):
        return results
    files = [f for f in os.listdir(DISCOVERY_DIR) if f.endswith(".json")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(DISCOVERY_DIR, f)), reverse=True)
    for filename in files:
        filepath = os.path.join(DISCOVERY_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append(data)
        except Exception as e:
            log.warning("Skipping corrupted discovery file %s: %s", filename, e)
            continue
    return results


# ---------------------------------------------------------------------------
# Competitor candidate storage (read-modify-write — protected by _feedback_lock)
# ---------------------------------------------------------------------------

def save_competitor_candidates(candidates: list[dict]) -> None:
    """Append new competitor candidates to the competitor_candidates log.

    Each candidate: { company_name, discovered_from_company, discovered_from_product, discovered_at }
    Deduplicates by company_name (case-insensitive) — no duplicates added.
    """
    filepath = os.path.join(FEEDBACK_DIR, "competitor_candidates.json")
    with _feedback_lock:
        existing = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except Exception as e:
                    log.warning("competitor_candidates.json corrupted, starting fresh: %s", e)
                    existing = []

        existing_names = {c.get("company_name", "").lower() for c in existing}
        added = 0
        for candidate in candidates:
            name_lower = candidate.get("company_name", "").lower()
            if name_lower and name_lower not in existing_names:
                existing.append(candidate)
                existing_names.add(name_lower)
                added += 1

        if added:
            _atomic_write_json(filepath, existing)
            log.info("save_competitor_candidates: added %d new candidates", added)


def load_competitor_candidates() -> list[dict]:
    """Return all logged competitor candidates, newest first."""
    filepath = os.path.join(FEEDBACK_DIR, "competitor_candidates.json")
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return list(reversed(data))
        except Exception as e:
            log.warning("Failed to load competitor_candidates.json: %s", e)
            return []


def clear_competitor_candidates() -> None:
    """Clear the competitor candidates log."""
    filepath = os.path.join(FEEDBACK_DIR, "competitor_candidates.json")
    _atomic_write_json(filepath, [])
    log.info("clear_competitor_candidates: cleared")


# ---------------------------------------------------------------------------
# Designer storage
# ---------------------------------------------------------------------------

def save_designer_program(program_id: str, data: dict) -> str:
    """Save designer program state. Returns program_id."""
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    filepath = os.path.join(DESIGNER_DIR, f"{program_id}.json")
    _atomic_write_json(filepath, data)
    return program_id


def delete_designer_program(program_id: str) -> bool:
    """Delete a designer program by ID. Returns True if deleted, False if not found."""
    filepath = os.path.join(DESIGNER_DIR, f"{program_id}.json")
    if not os.path.exists(filepath):
        return False
    try:
        os.remove(filepath)
    except FileNotFoundError:
        return False
    return True


def load_designer_program(program_id: str) -> dict | None:
    """Load designer program by ID. Returns None if not found."""
    filepath = os.path.join(DESIGNER_DIR, f"{program_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_designer_programs() -> list[dict]:
    """Return summary list of all programs, newest first.

    Each entry: { program_id, program_name, company_name, current_phase, created_at, updated_at }
    """
    results = []
    if not os.path.exists(DESIGNER_DIR):
        return results
    files = [f for f in os.listdir(DESIGNER_DIR) if f.endswith(".json")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(DESIGNER_DIR, f)), reverse=True)
    for filename in files:
        filepath = os.path.join(DESIGNER_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            program_id = filename.replace(".json", "")
            results.append({
                "program_id": program_id,
                "program_name": data.get("program_name", "Untitled Program"),
                "company_name": data.get("company_name", ""),
                "current_phase": data.get("current_phase", 1),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
            })
        except Exception as e:
            log.warning("Skipping corrupted designer file %s: %s", filename, e)
            continue
    return results
