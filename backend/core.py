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
# Composite score helpers (single source of truth)
# ---------------------------------------------------------------------------

# Ceiling flags: fundamental delivery constraints that cap the labability tier
# regardless of raw score. Defined once here; all modules import this set.
_CEILING_FLAGS = {"bare_metal_required", "no_api_automation", "saas_only", "multi_tenant_only"}


def _verdict(score: int) -> str:
    """Canonical verdict label from composite score. Single source of truth."""
    if score >= 70:
        return "Strong Fit"
    if score >= 45:
        return "Pursue"
    if score >= 20:
        return "Monitor"
    return "Pass"


# Badge name → subsection within Product Labability (for dossier SE drill-down grouping)
_BADGE_SUBSECTION: dict[str, str] = {
    # Provisioning (1.1)
    "Runs in Hyper-V": "provisioning", "Runs in Azure": "provisioning",
    "Runs in AWS": "provisioning", "Requires GCP": "provisioning",
    "Runs in Containers": "provisioning", "ESX Required": "provisioning",
    "Provisioning APIs": "provisioning", "Lifecycle APIs": "provisioning",
    "Learner Isolation": "provisioning", "Bare Metal Required": "provisioning",
    "No Deployment Method": "provisioning", "Potential IaC Friction": "provisioning",
    "Full Tenant Required": "provisioning",
    # Licensing & Accounts (1.2)
    "AuthN/AuthZ APIs": "licensing", "Credential Pool": "licensing",
    "Account Recycling": "licensing", "Supports NFR Accounts": "licensing",
    "NFR License Path": "licensing", "High License Cost": "licensing",
    "Tenant Provisioning Lag": "licensing", "Provisioning Rate Limits": "licensing",
    "Anti-Automation Controls": "licensing", "MFA Required": "licensing",
    "Credit Card Required": "licensing",
    # Scoring (1.3)
    "Scoring APIs": "scoring", "Script Scorable": "scoring",
    # Teardown (1.4)
    "Teardown APIs": "teardown",
}


def _badge_subsection(badge_name: str) -> str:
    """Map a badge name to its Product Labability subsection key."""
    for known, section in _BADGE_SUBSECTION.items():
        if known.lower() in badge_name.lower():
            return section
    return "provisioning"  # default


def _parse_hero_badge(evidence_list: list) -> dict | None:
    """Extract the single most consequential badge from an evidence list.

    Priority: Blocker (0) > Risk/Caution (1) > Strength/Opportunity (3).
    Returns {name, qualifier} or None if no parseable evidence.
    """
    import re
    _priority = {"blocker": 0, "risk": 1, "caution": 1, "strength": 3, "opportunity": 3}
    best: dict | None = None
    best_pri = 99
    for ev in (evidence_list or []):
        claim = ev.get("claim", "") if isinstance(ev, dict) else getattr(ev, "claim", "")
        m = re.match(r'\*\*(.+?)\*\*', claim)
        if not m:
            continue
        label = m.group(1).rstrip(":")
        if " | " in label:
            name, qualifier = label.rsplit(" | ", 1)
        else:
            name, qualifier = label, "strength"
        name = name.strip()
        qualifier = qualifier.strip().lower()
        pri = _priority.get(qualifier, 99)
        if pri < best_pri:
            best_pri = pri
            best = {"name": name, "qualifier": qualifier}
    return best


def _labable_tier(product: dict) -> str:
    """Canonical tier derivation from a scored product dict.

    Requires _total_score to already be set on the product (i.e. call after
    compute_product_score or _attach_scores). Ceiling flags take precedence
    over score — a flagged product is capped at less_likely or not_likely
    regardless of how high the raw score came in.
    """
    score = product.get("_total_score", 0)
    flags = set(product.get("poor_match_flags", []) or [])
    if flags & _CEILING_FLAGS:
        return "less_likely" if score >= 20 else "not_likely"
    if score >= 70:
        return "highly_likely"
    if score >= 45:
        return "likely"
    if score >= 20:
        return "less_likely"
    return "not_likely"


def _attach_scores(data: dict) -> None:
    """Score products, sort by score, and set _composite_score on data in place.

    Single source of truth for all score computation across Inspector and Prospector.
    Safe to call on any analysis dict loaded from JSON storage.

    Composite score = top product score. The 40/30/20/10 model already incorporates
    all four dimensions (Product Labability, Instructional Value, Organizational
    Readiness, Market Readiness) — no separate company-level score needed.
    """
    products = data.get("products") or []
    for p in products:
        p["_total_score"] = compute_product_score(p)
        p["likely_labable"] = _labable_tier(p)
    products.sort(key=lambda p: p.get("_total_score", 0), reverse=True)
    data["products"] = products

    top_score = products[0].get("_total_score", 0) if products else 0
    data["_composite_score"] = top_score
    data["_composite_gated"] = top_score < 30


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
