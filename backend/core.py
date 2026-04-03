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
#
# Memory management:
#   _PROGRESS_MAX_JOBS     — evict oldest jobs when this many are tracked
#   _PROGRESS_EVICT_COUNT  — how many to evict at once
#   _PROGRESS_MAX_MSGS     — hard cap on messages per job (prevents unbounded growth
#                            on long-running or stuck jobs)
#   _PROGRESS_JOB_TTL      — seconds after which a completed job is eligible for
#                            removal (streaming is fast; 5 min is generous)
# ---------------------------------------------------------------------------

_progress: dict[str, list[str]] = {}
_progress_timestamps: dict[str, float] = {}   # job_id → creation time
_progress_lock = threading.Lock()
_PROGRESS_MAX_JOBS   = 50
_PROGRESS_EVICT_COUNT = 10
_PROGRESS_MAX_MSGS   = 200    # no legitimate job needs more than ~20 messages
_PROGRESS_JOB_TTL    = 300    # 5 minutes
_cancelled_jobs: set[str] = set()


def _push(job_id: str, msg: str):
    now = time.time()
    with _progress_lock:
        if job_id not in _progress:
            # Evict stale jobs first (TTL), then oldest-by-count if still over limit
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

        # Per-job message cap — drop oldest messages if over limit
        msgs = _progress[job_id]
        if len(msgs) >= _PROGRESS_MAX_MSGS:
            # Keep the last half; the front is already consumed by the SSE stream
            _progress[job_id] = msgs[_PROGRESS_MAX_MSGS // 2:]

        _progress[job_id].append(msg)


def _sse_stream(job_id: str, poll_interval: float = 0.3):
    """Generic SSE generator: yields messages for job_id until done/error or timeout."""
    last = 0
    deadline = time.time() + _SSE_TIMEOUT
    while time.time() < deadline:
        with _progress_lock:
            msgs = list(_progress.get(job_id, []))
        for msg in msgs[last:]:
            last += 1
            yield f"data: {msg}\n\n"
            if msg.startswith("done:") or msg.startswith("error:"):
                # Clean up immediately on completion — no need to keep the job in memory
                with _progress_lock:
                    _progress.pop(job_id, None)
                    _progress_timestamps.pop(job_id, None)
                return
        time.sleep(poll_interval)
    yield "data: error:Timed out — the operation took too long. Please try again.\n\n"


# ---------------------------------------------------------------------------
# Composite score helper (single source of truth)
# ---------------------------------------------------------------------------

_CHANNEL_ORGS = {"training_organization", "systems_integrator", "technology_distributor", "professional_services", "academic_institution"}


def _compute_composite(top_lab: int, pr_score: int, org_type: str) -> tuple[int, bool, str]:
    """Return (composite_score, is_gated, weights_label).

    Company-level composite used in Prospector. Blends top product labability score
    with organizational readiness score. Weights differ by org type:
    - Software companies: Product Labability gates (65% product / 35% org readiness)
    - Channel orgs (training, GSI, distributor, etc.): Org Readiness gates (35% product / 65% org readiness)
    """
    if org_type in _CHANNEL_ORGS:
        raw = round(top_lab * 0.35 + pr_score * 0.65)
        gate_threshold, gate_cap = 20, 30
        weights = "35% Product Labability / 65% Org Readiness"
    else:
        raw = round(top_lab * 0.65 + pr_score * 0.35)
        gate_threshold, gate_cap = 30, 25
        weights = "65% Product Labability / 35% Org Readiness"

    if top_lab < gate_threshold:
        return min(raw, gate_cap), True, weights
    return min(100, raw), False, weights


# Raw max for org readiness scores = 35+27+35+10+10 = 117; divide to normalize to 0-100
_PR_NORMALIZATION = 1.17


def _attach_scores(data: dict) -> None:
    """Score products, sort by score, and set _pr_total/_composite_* on data in place.

    Single source of truth for all score computation across Inspector and Prospector.
    Safe to call on any analysis dict loaded from JSON storage.
    """
    products = data.get("products") or []
    for p in products:
        p["_total_score"] = compute_product_score(p)
        # Mirror of intelligence._labable_tier — update both if thresholds change.
        _score = p.get("_total_score", 0)
        _flags = set(p.get("poor_match_flags", []) or [])
        # Ceiling flags: fundamental delivery constraints that cap Product Labability score
        # regardless of raw score. Any of these present → less_likely or not_likely.
        _CEILING = {"bare_metal_required", "no_api_automation", "saas_only", "multi_tenant_only"}
        if _flags & _CEILING:
            p["likely_labable"] = "less_likely" if _score >= 20 else "not_likely"
        elif _score >= 70:
            p["likely_labable"] = "highly_likely"
        elif _score >= 45:
            p["likely_labable"] = "likely"
        elif _score >= 20:
            p["likely_labable"] = "less_likely"
        else:
            p["likely_labable"] = "not_likely"
    products.sort(key=lambda p: p.get("_total_score", 0), reverse=True)
    data["products"] = products

    # Org readiness score — always stored under "lab_maturity" key; "partnership_readiness" is legacy
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
    """Normalise on-demand library value: bool/yes/true/-1 → '✓', count → number string."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return "✓" if val else ""
    if val == -1:
        return "✓"
    if isinstance(val, (int, float)) and val > 0:
        return str(int(val))
    s = str(val).strip().lower()
    if s in ("yes", "true", "y", "1"):
        return "✓"
    if s in ("", "no", "false", "null", "none", "0"):
        return ""
    return str(val).strip()


def _fmt_cert(val) -> str:
    """Normalise cert program value: bool/yes/true → '✓', counts stay as numbers."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return "✓" if val else ""
    s = str(val).strip().lower()
    if s in ("yes", "true", "y", "1"):
        return "✓"
    if s in ("", "no", "false", "null", "none", "0"):
        return ""
    return str(val).strip()
