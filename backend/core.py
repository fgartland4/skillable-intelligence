"""Shared state and helpers used by all route modules."""

import logging
import threading
import time

from models import compute_product_score

log = logging.getLogger(__name__)

# SSE stream timeout
_SSE_TIMEOUT = 600  # 10 minutes

# ---------------------------------------------------------------------------
# In-memory progress store for SSE streaming
# ---------------------------------------------------------------------------

_progress: dict[str, list[str]] = {}
_progress_lock = threading.Lock()
_PROGRESS_MAX_JOBS = 50
_PROGRESS_EVICT_COUNT = 10
_cancelled_jobs: set[str] = set()


def _push(job_id: str, msg: str):
    with _progress_lock:
        if job_id not in _progress:
            if len(_progress) >= _PROGRESS_MAX_JOBS:
                for old_key in list(_progress.keys())[:_PROGRESS_EVICT_COUNT]:
                    del _progress[old_key]
            _progress[job_id] = []
        _progress[job_id].append(msg)


def _sse_stream(job_id: str, poll_interval: float = 0.3):
    """Generic SSE generator: yields messages for job_id until done/error or timeout."""
    last = 0
    deadline = time.time() + _SSE_TIMEOUT
    while time.time() < deadline:
        with _progress_lock:
            msgs = _progress.get(job_id, [])
        for msg in msgs[last:]:
            last += 1
            yield f"data: {msg}\n\n"
            if msg.startswith("done:") or msg.startswith("error:"):
                return
        time.sleep(poll_interval)
    yield "data: error:Timed out — the operation took too long. Please try again.\n\n"


# ---------------------------------------------------------------------------
# Composite score helper (single source of truth)
# ---------------------------------------------------------------------------

_CHANNEL_ORGS = {"training_organization", "systems_integrator", "technology_distributor", "professional_services", "academic_institution"}


def _compute_composite(top_lab: int, pr_score: int, org_type: str) -> tuple[int, bool, str]:
    """Return (composite_score, is_gated, weights_label)."""
    if org_type in _CHANNEL_ORGS:
        raw = round(top_lab * 0.35 + pr_score * 0.65)
        gate_threshold, gate_cap = 20, 30
        weights = "35% Product / 65% Lab Maturity"
    else:
        raw = round(top_lab * 0.65 + pr_score * 0.35)
        gate_threshold, gate_cap = 30, 25
        weights = "65% Product / 35% Lab Maturity"

    if top_lab < gate_threshold:
        return min(raw, gate_cap), True, weights
    return min(100, raw), False, weights


# Raw max for partnership scores = 35+27+35+10+10 = 117; divide to normalize to 0-100
_PR_NORMALIZATION = 1.17


def _attach_scores(data: dict) -> None:
    """Score products, sort by score, and set _pr_total/_composite_* on data in place.

    Single source of truth for all score computation across Inspector and Prospector.
    Safe to call on any analysis dict loaded from JSON storage.
    """
    products = data.get("products") or []
    for p in products:
        p["_total_score"] = compute_product_score(p)
    products.sort(key=lambda p: p.get("_total_score", 0), reverse=True)
    data["products"] = products

    pr = data.get("lab_maturity") or data.get("partnership_readiness") or {}
    pr_raw = sum(s.get("score", 0) for s in pr.values() if isinstance(s, dict))
    pr_total = min(100, round(pr_raw / _PR_NORMALIZATION))
    data["_pr_total"] = pr_total

    org_type = data.get("organization_type", "software_company")
    top_lab = products[0].get("_total_score", 0) if products else 0
    composite, gated, weights = _compute_composite(top_lab, pr_total, org_type)
    data["_composite_score"] = composite
    data["_composite_gated"] = gated
    data["_composite_weights"] = weights or "65% Product / 35% Lab Maturity"


def _fmt_ondemand(val) -> str:
    if val is None:
        return ""
    if val == -1:
        return "Yes"
    return str(val) if val and val > 0 else ""


def _fmt_cert(val) -> str:
    if val is None:
        return ""
    return str(val)
