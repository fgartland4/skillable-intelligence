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
from models import CompanyAnalysis, FitScore, Product, Verdict

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
    # Use scoring_config's get_verdict — single source of truth
    vd = cfg.get_verdict(fit_score, acv_tier)
    return Verdict(
        label=vd.label,
        color=vd.color,
        fit_label=_fit_label(fit_score),
        acv_label=f"{acv_tier.upper()} ACV",
    )


def _score_band(score: int) -> str:
    """Determine which score color band a score falls into.

    Reads thresholds from scoring_config.py — Define-Once.
    """
    for color, threshold in sorted(cfg.SCORE_THRESHOLDS.items(),
                                    key=lambda x: x[1], reverse=True):
        if score >= threshold:
            return color
    return "red"


def _fit_label(score: int) -> str:
    """Generate the fit label (e.g., 'HIGH FIT') from score.

    Uses the green threshold from config as the HIGH FIT boundary.
    Strict reads — if SCORE_THRESHOLDS is missing the expected keys,
    that's a config bug we want to surface immediately, not paper over
    with a silent fallback. MED-9 in code-review-2026-04-07.md.
    """
    green_threshold = cfg.SCORE_THRESHOLDS["green"]
    amber_threshold = cfg.SCORE_THRESHOLDS["light_amber"]
    if score >= green_threshold:
        return "HIGH FIT"
    elif score >= amber_threshold:
        return "MODERATE FIT"
    else:
        return "LOW FIT"


# ═══════════════════════════════════════════════════════════════════════════════
# Discovery Tier Labels — Promising / Potential / Uncertain / Unlikely
# ═══════════════════════════════════════════════════════════════════════════════

def discovery_tier(score: int) -> str:
    """Assign a discovery tier label based on initial assessment score.

    These communicate confidence at discovery depth — not conclusions.
    Thresholds derived from scoring config (Define-Once). Strict reads —
    if SCORE_THRESHOLDS is missing the expected keys, that's a config
    bug we want to surface immediately. MED-9 in code-review-2026-04-07.md.

    Tier-to-threshold mapping (MED-10 — was previously documented only in
    comments, now expressed as code):
      promising   →  >= green        (e.g. 65+)
      potential   →  >= light_amber  (e.g. 45+)
      uncertain   →  >= amber        (e.g. 25+)
      unlikely    →  below amber

    Renamed 2026-04-12: Seems Promising → Promising, Likely → Potential.
    """
    green_threshold = cfg.SCORE_THRESHOLDS["green"]
    amber_threshold = cfg.SCORE_THRESHOLDS["light_amber"]
    red_threshold = cfg.SCORE_THRESHOLDS["amber"]

    if score >= green_threshold:
        return "promising"
    elif score >= amber_threshold:
        return "potential"
    elif score >= red_threshold:
        return "uncertain"
    else:
        return "unlikely"


DISCOVERY_TIER_LABELS = {
    "promising": "Promising",
    "potential": "Potential",
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


# Domain-based lab platform detection lives in researcher.py
# (uses knowledge/competitors.json, not scoring_config.py)


# ═══════════════════════════════════════════════════════════════════════════════
# Company Classification Badge
# ═══════════════════════════════════════════════════════════════════════════════

def company_classification_label(org_type: str, products: list[Product],
                                  company_badge_hint: str = "") -> str:
    """Generate the company classification badge text.

    Badge pattern: [Category] + [Org Type].
    - Software companies: "{CATEGORY} SOFTWARE" (or "ENTERPRISE SOFTWARE"
      when 5+ unrelated product categories — earned by breadth).
    - Non-software org types: mapped from organization type, with category
      prefix when focused (e.g. "Cybersecurity Industry Authority").

    company_badge_hint: optional badge suggested by the researcher during
    discovery. Used as the primary source when available — the researcher
    has context about how the company positions itself. Python derivation
    serves as fallback when the hint is missing (old cached discoveries).

    Locked 2026-04-12: badge pattern, Enterprise Software threshold (5+),
    academic badge types, Industry Authority category prefix.
    """
    # If the researcher provided a badge, trust it — the researcher has
    # richer context about the company than category-counting can provide.
    if company_badge_hint:
        return company_badge_hint

    # Non-software org types — fixed badges
    org_labels = {
        "industry_authority": "Industry Authority",
        "enterprise_learning_platform": "Enterprise Learning Platform",
        "ilt_training_organization": "ILT Training Organization",
        "systems_integrator": "Global Systems Integrator",
        "var": "Value Added Reseller",
        "technology_distributor": "Technology Distributor",
        "professional_services": "Professional Services",
        "content_development": "Content Development Partner",
        "lms_company": "LMS / Learning Platform",
        # Legacy org types — map to closest current badge
        "training_organization": "Industry Authority",
        "academic_institution": "Research University",
    }

    if org_type in org_labels:
        return org_labels[org_type]

    # Software companies — derive badge from product categories
    if products:
        categories = set(p.category for p in products
                        if p.category and p.category != "Training & Certification")
        if len(categories) >= 5:
            return "Enterprise Software"
        elif len(categories) == 2:
            cats = sorted(categories)
            return f"{cats[0]} & {cats[1]} Software"
        elif len(categories) == 1:
            return f"{next(iter(categories))} Software"

    return "Software"


def org_badge_color_group(org_type: str) -> str:
    """Return the color group for an org type badge.

    Purple — Product creators (software, enterprise)
    Teal — Learning-focused (training, academic, industry authority,
            enterprise learning platform, ILT training org)
    Warm blue — Channel/partners (GSI, VAR, distributor, services,
                LMS, content dev)
    """
    learning_focused = {
        "training_organization", "academic_institution",
        "industry_authority", "enterprise_learning_platform",
        "ilt_training_organization",
    }
    channel_partners = {
        "systems_integrator", "technology_distributor", "var",
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
