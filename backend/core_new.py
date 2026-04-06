"""Core logic for the Skillable Intelligence Platform.

Verdict assignment, score helpers, lab platform detection, SSE progress
streaming, and error handling.
All logic reads from scoring_config.py — Define-Once Principle.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Optional

from backend import scoring_config as cfg
from models_new import CompanyAnalysis, FitScore, Product, Verdict

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SSE Progress Streaming — framework-agnostic infrastructure
# ═══════════════════════════════════════════════════════════════════════════════

_SSE_TIMEOUT = 600  # 10 minutes max for any operation

_progress: dict[str, list[str]] = {}
_progress_timestamps: dict[str, float] = {}
_progress_lock = threading.Lock()
_PROGRESS_MAX_JOBS = 50
_PROGRESS_EVICT_COUNT = 10
_PROGRESS_MAX_MSGS = 200
_PROGRESS_JOB_TTL = 300


def push(job_id: str, msg: str):
    """Push a progress message for a job. Thread-safe."""
    now = time.time()
    with _progress_lock:
        if job_id not in _progress:
            # Evict stale jobs
            stale = [jid for jid, ts in _progress_timestamps.items()
                     if now - ts > _PROGRESS_JOB_TTL]
            for jid in stale:
                _progress.pop(jid, None)
                _progress_timestamps.pop(jid, None)
            if len(_progress) >= _PROGRESS_MAX_JOBS:
                for old_key in list(_progress.keys())[:_PROGRESS_EVICT_COUNT]:
                    _progress.pop(old_key, None)
                    _progress_timestamps.pop(old_key, None)
            _progress[job_id] = []
            _progress_timestamps[job_id] = now

        msgs = _progress[job_id]
        if len(msgs) >= _PROGRESS_MAX_MSGS:
            _progress[job_id] = msgs[_PROGRESS_MAX_MSGS // 2:]
        _progress[job_id].append(msg)


def sse_stream(job_id: str, poll_interval: float = 0.3):
    """SSE generator: yields messages until done/error or timeout."""
    last = 0
    deadline = time.time() + _SSE_TIMEOUT
    last_yield = time.time()
    heartbeat_interval = 15
    while time.time() < deadline:
        with _progress_lock:
            msgs = list(_progress.get(job_id, []))
        sent = False
        for msg in msgs[last:]:
            last += 1
            sent = True
            last_yield = time.time()
            yield f"data: {msg}\n\n"
            if msg.startswith("done:") or msg.startswith("error:"):
                with _progress_lock:
                    _progress.pop(job_id, None)
                    _progress_timestamps.pop(job_id, None)
                return
        if not sent and time.time() - last_yield >= heartbeat_interval:
            yield ": heartbeat\n\n"
            last_yield = time.time()
        time.sleep(poll_interval)
    yield "data: error:Timed out — please try again.\n\n"


def poll_job(job_id: str) -> dict:
    """Polling fallback for SSE — returns job status as JSON."""
    with _progress_lock:
        msgs = list(_progress.get(job_id, []))
    if not msgs:
        return {"status": "unknown"}
    for msg in reversed(msgs):
        if msg.startswith("done:"):
            return {"status": "done", "result_id": msg[5:]}
        if msg.startswith("error:"):
            return {"status": "error", "message": msg[6:]}
    return {"status": "running"}


# ═══════════════════════════════════════════════════════════════════════════════
# Verdict Assignment — 10 verdicts across 5 score bands × 3 ACV tiers
# ═══════════════════════════════════════════════════════════════════════════════

def assign_verdict(fit_score: int, acv_tier: str) -> Verdict:
    """Look up the verdict from the scoring config verdict grid.

    Args:
        fit_score: 0-100 Fit Score
        acv_tier: "high", "medium", or "low"

    Returns:
        Verdict with label, color, fit_label, and acv_label
    """
    # Determine score band and color
    score_band = _score_band(fit_score)

    # Look up verdict from grid
    for entry in cfg.VERDICT_GRID:
        entry_min = entry.min_score if hasattr(entry, "min_score") else entry[0]
        entry_tier = entry.acv_tier if hasattr(entry, "acv_tier") else entry[1]
        entry_verdict = entry.verdict if hasattr(entry, "verdict") else entry[2]
        entry_color = entry.color if hasattr(entry, "color") else entry[3]

        if fit_score >= entry_min and acv_tier == entry_tier:
            return Verdict(
                label=entry_verdict,
                color=entry_color,
                fit_label=_fit_label(fit_score),
                acv_label=f"{acv_tier.upper()} ACV",
            )

    # Fallback — should never reach here if verdict grid is complete
    log.warning("No verdict found for fit_score=%d, acv_tier=%s", fit_score, acv_tier)
    return Verdict(label="Unknown", color="gray")


def _score_band(score: int) -> str:
    """Determine which score color band a score falls into."""
    if score >= 80:
        return "dark_green"
    elif score >= 65:
        return "green"
    elif score >= 45:
        return "light_amber"
    elif score >= 25:
        return "amber"
    else:
        return "red"


def _fit_label(score: int) -> str:
    """Generate the fit label (e.g., 'HIGH FIT') from score."""
    if score >= 65:
        return "HIGH FIT"
    elif score >= 45:
        return "MODERATE FIT"
    else:
        return "LOW FIT"


# ═══════════════════════════════════════════════════════════════════════════════
# Discovery Tier Labels — Seems Promising / Likely / Uncertain / Unlikely
# ═══════════════════════════════════════════════════════════════════════════════

def discovery_tier(score: int) -> str:
    """Assign a discovery tier label based on initial assessment score.

    These communicate confidence at discovery depth — not conclusions.
    """
    if score >= 70:
        return "seems_promising"
    elif score >= 45:
        return "likely"
    elif score >= 20:
        return "uncertain"
    else:
        return "unlikely"


DISCOVERY_TIER_LABELS = {
    "seems_promising": "Seems Promising",
    "likely": "Likely",
    "uncertain": "Uncertain",
    "unlikely": "Unlikely",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Score Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def compute_fit_score(product: Product) -> int:
    """Compute Fit Score from a product's pillar scores.

    Convenience wrapper — the FitScore.total property does the math.
    """
    return product.fit_score.total


def score_products_and_sort(analysis: CompanyAnalysis) -> None:
    """Sort products by Fit Score (highest first) and set company-level score.

    Mutates the analysis in place.
    """
    analysis.products.sort(key=lambda p: p.fit_score.total, reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Domain-Based Lab Platform Detection
# ═══════════════════════════════════════════════════════════════════════════════

def detect_lab_platforms(page_content: str) -> list[dict]:
    """Scan page content for outbound links to known lab platform domains.

    A URL link is stronger evidence than a name mention.
    Uses the canonical lab platform list from scoring_config.py.

    Args:
        page_content: Raw HTML or text content from a fetched page

    Returns:
        List of dicts: [{"platform": "Skillable", "domain": "labondemand.com", "urls": [...]}]
    """
    detections = []

    for platform in cfg.LAB_PLATFORMS:
        domains = platform.get("detection_domains", [])
        if not domains:
            # Fall back to the main domain if no detection_domains specified
            main_domain = platform.get("domain", "")
            if main_domain:
                domains = [main_domain]

        found_urls = []
        for domain in domains:
            if not domain:
                continue
            # Look for URLs containing this domain
            pattern = rf'https?://[^\s"\'<>]*{re.escape(domain)}[^\s"\'<>]*'
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            found_urls.extend(matches)

            # Also check for plain domain mentions (weaker signal)
            if domain.lower() in page_content.lower() and not found_urls:
                found_urls.append(f"mention:{domain}")

        if found_urls:
            detections.append({
                "platform": platform.get("name", "Unknown"),
                "domain": domains[0] if domains else "",
                "urls": list(set(found_urls)),
                "is_skillable": "skillable" in platform.get("name", "").lower(),
                "evidence_type": "url" if any(not u.startswith("mention:") for u in found_urls) else "mention",
            })

    return detections


# ═══════════════════════════════════════════════════════════════════════════════
# Company Classification Badge
# ═══════════════════════════════════════════════════════════════════════════════

def company_classification_label(org_type: str, products: list[Product]) -> str:
    """Generate the company classification badge text.

    Software companies: {CATEGORY} SOFTWARE (or ENTERPRISE SOFTWARE if 3+ categories)
    All others: mapped from organization type.
    """
    org_labels = {
        "training_organization": "TRAINING ORG",
        "academic_institution": "ACADEMIC",
        "systems_integrator": "SYSTEMS INTEGRATOR",
        "technology_distributor": "TECH DISTRIBUTOR",
        "professional_services": "PROFESSIONAL SERVICES",
        "content_development": "CONTENT DEVELOPMENT",
        "lms_company": "LMS PROVIDER",
    }

    if org_type in org_labels:
        return org_labels[org_type]

    # Software companies — derive from product categories
    if products:
        categories = set(p.category for p in products if p.category)
        if len(categories) >= 3:
            return "ENTERPRISE SOFTWARE"
        elif len(categories) == 1:
            return f"{next(iter(categories)).upper()} SOFTWARE"
        elif len(categories) == 2:
            return f"{next(iter(categories)).upper()} SOFTWARE"

    return "SOFTWARE"


def org_badge_color_group(org_type: str) -> str:
    """Return the color group for an org type badge.

    Purple — Product creators (software, enterprise)
    Teal — Learning-focused (training, academic)
    Warm blue — Channel/partners (GSI, distributor, services, LMS, content dev)
    """
    learning_focused = {"training_organization", "academic_institution"}
    channel_partners = {
        "systems_integrator", "technology_distributor",
        "professional_services", "content_development", "lms_company",
    }

    if org_type in learning_focused:
        return "teal"
    elif org_type in channel_partners:
        return "warm_blue"
    else:
        return "purple"


# ═══════════════════════════════════════════════════════════════════════════════
# Error Handling
# ═══════════════════════════════════════════════════════════════════════════════

def error_response(message: str, status_code: int = 500, is_api: bool = False):
    """Generate a consistent error response.

    Returns JSON for API/XHR requests, styled HTML for browser requests.
    """
    if is_api:
        from flask import jsonify
        return jsonify({"error": message}), status_code
    else:
        from flask import render_template_string
        return render_template_string(
            """<!DOCTYPE html><html><head><title>Error</title></head>
            <body style="background:#06100c;color:#e8f5f0;font-family:sans-serif;
            display:flex;align-items:center;justify-content:center;min-height:100vh;">
            <div style="text-align:center;">
            <h1 style="color:#f59e0b;">{{ message }}</h1>
            <a href="/" style="color:#24ED9B;">← Back to Inspector</a>
            </div></body></html>""",
            message=message
        ), status_code
