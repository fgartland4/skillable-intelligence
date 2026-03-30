"""JSON file storage for analysis and discovery results."""

import json
import os
import uuid
from dataclasses import asdict
from models import CompanyAnalysis, compute_labability_total
from config import DATA_DIR

DISCOVERY_DIR = os.path.join(os.path.dirname(__file__), "data", "discoveries")
BATCH_DIR = os.path.join(os.path.dirname(__file__), "data", "batch")
FEEDBACK_DIR = os.path.join(os.path.dirname(__file__), "data", "feedback")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DISCOVERY_DIR, exist_ok=True)
os.makedirs(BATCH_DIR, exist_ok=True)
os.makedirs(FEEDBACK_DIR, exist_ok=True)


def save_discovery(discovery_id: str, data: dict) -> str:
    filepath = os.path.join(DISCOVERY_DIR, f"{discovery_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return discovery_id


def load_discovery(discovery_id: str) -> dict | None:
    filepath = os.path.join(DISCOVERY_DIR, f"{discovery_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_analysis(analysis: CompanyAnalysis) -> str:
    if not analysis.analysis_id:
        analysis.analysis_id = str(uuid.uuid4())[:8]
    filepath = os.path.join(DATA_DIR, f"{analysis.analysis_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(asdict(analysis), f, indent=2, default=str)
    return analysis.analysis_id


def load_analysis(analysis_id: str) -> dict | None:
    filepath = os.path.join(DATA_DIR, f"{analysis_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def find_analysis_by_company_name(company_name: str) -> dict | None:
    """Return the most recent full analysis dict for a company name (case-insensitive), or None."""
    if not os.path.exists(DATA_DIR):
        return None
    needle = company_name.lower().strip()
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(DATA_DIR, f)), reverse=True)
    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("company_name", "").lower().strip() == needle:
                return data
        except Exception:
            continue
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
        except Exception:
            continue
    return None


def save_batch_job(job_id: str, data: dict) -> None:
    filepath = os.path.join(BATCH_DIR, f"{job_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_batch_job(job_id: str) -> dict | None:
    filepath = os.path.join(BATCH_DIR, f"{job_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prospector_run(job_id: str, data: dict) -> None:
    """Store a Prospector batch run (reuses batch storage)."""
    save_batch_job(job_id, data)


def load_prospector_run(job_id: str) -> dict | None:
    return load_batch_job(job_id)


def append_poor_fit_feedback(feedback: dict) -> None:
    """Append a poor fit flag (with optional reason) to the feedback log."""
    filepath = os.path.join(FEEDBACK_DIR, "poor_fit.json")
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except Exception:
                existing = []
    existing.append(feedback)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def load_poor_fit_companies() -> set:
    """Return lowercase set of company names previously flagged as poor fit."""
    filepath = os.path.join(FEEDBACK_DIR, "poor_fit.json")
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return {d.get("company_name", "").lower() for d in data}
        except Exception:
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
                s = p.get("labability_score") or {}
                tech = s.get("technical_orchestrability", {}).get("score", 0)
                other = sum(
                    d.get("score", 0) for k, d in s.items()
                    if k != "technical_orchestrability" and isinstance(d, dict)
                )
                total = compute_labability_total(tech, other, p.get("skillable_path", ""))
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
        except Exception:
            # Skip corrupted files rather than crashing the home page
            continue
    return results
