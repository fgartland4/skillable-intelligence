"""Fit Score composer — the final step of the Score layer.

Architectural role
------------------
This is the composer that turns three per-pillar PillarScore objects
into a single composite Fit Score, applying the Technical Fit
Multiplier on the way down.

Input:   a FitScore with product_labability / instructional_value /
         customer_fit PillarScores already populated by the three
         per-pillar scorers (pillar_1_scorer, pillar_2_scorer,
         pillar_3_scorer).
Output:  mutates the same FitScore in place — sets total_override
         (the composed final number) and technical_fit_multiplier
         (the audit-trail field) so FitScore.total returns the
         composed value.

This module is the only place in the Score layer that is allowed to
combine pillars. Everything else sits strictly inside one pillar.

Guiding principles honored here (Three Layers of Intelligence —
Platform-Foundation.md):
  - Score reads typed values, not badges
  - No Claude, no AI judgment, deterministic
  - No hardcoded numbers — every value comes from scoring_config.py
  - Define-Once — the multiplier table lives in one place
  - One file, one job — composition only, no pillar-internal math

Why the Technical Fit Multiplier exists
---------------------------------------
The 40/30/30 weighted sum alone lets a product with weak Product
Labability (i.e., "we basically can't lab this") still score Solid
Prospect when Instructional Value and Customer Fit are strong.  That
is not honest — if we cannot run the lab, great instructional signals
and a training-mature customer do not recover the situation.  The
multiplier scales IV + CF contributions by a factor derived from the
PL score and orchestration method, enforcing:

    weak PL → diminished IV + CF contribution → honest Fit Score

Risk cap reduction inside each pillar is NOT a substitute for this
coupling — per-pillar caps only reduce THAT pillar's score.  The
multiplier is the only primitive that couples pillars together.

See `scoring_config.TECHNICAL_FIT_MULTIPLIERS` for the full table and
Define-Once source of every value.
"""
from __future__ import annotations

import logging

import scoring_config as cfg
from models import FitScore

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pillar lookup — built once from config at module load
# ═══════════════════════════════════════════════════════════════════════════════

def _build_pillar_lookup() -> dict[str, cfg.Pillar]:
    """Map pillar key (lowercase, underscores) to the Pillar config object."""
    out: dict[str, cfg.Pillar] = {}
    for pillar in cfg.PILLARS:
        key = pillar.name.lower().replace(" ", "_")
        out[key] = pillar
    return out


_PILLAR_LOOKUP: dict[str, cfg.Pillar] = _build_pillar_lookup()


# ═══════════════════════════════════════════════════════════════════════════════
# Technical Fit Multiplier lookup
# ═══════════════════════════════════════════════════════════════════════════════

def get_technical_fit_multiplier(pl_score: int, orchestration_method: str) -> float:
    """Look up the multiplier that scales the downstream IV + CF pillars.

    The multiplier table is keyed on (pl_score range, orchestration method
    class).  Method classes:
      - "datacenter"     → orchestration method is in cfg.DATACENTER_METHODS
      - "non-datacenter" → orchestration method is non-empty and not datacenter
      - "any"            → fallback when nothing specific matches

    Walk order: method-specific match first, then "any" fallback.  First
    match wins within each pass (declaration order in cfg).

    Args:
        pl_score: Final Product Labability score (0-100, post pillar-internal
                  risk cap reduction and score_override).
        orchestration_method: Product's orchestration method string, e.g.,
                              "Hyper-V", "Azure Cloud Slice".  Empty string
                              falls back to the "any" method class.

    Returns:
        Multiplier in [0, 1] that scales IV + CF contributions.  Defaults
        to 1.0 (no-op) when no rule matches — logged as a config warning.
    """
    if not orchestration_method:
        method_class = "any"
    elif orchestration_method in cfg.DATACENTER_METHODS:
        method_class = "datacenter"
    else:
        method_class = "non-datacenter"

    for m in cfg.TECHNICAL_FIT_MULTIPLIERS:
        if m.score_min <= pl_score <= m.score_max and m.method == method_class:
            return m.multiplier

    for m in cfg.TECHNICAL_FIT_MULTIPLIERS:
        if m.score_min <= pl_score <= m.score_max and m.method == "any":
            return m.multiplier

    log.warning(
        "fit_score_composer.get_technical_fit_multiplier: no rule matched "
        "(pl=%d, method=%s) — defaulting to 1.0",
        pl_score, orchestration_method,
    )
    return 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Composition
# ═══════════════════════════════════════════════════════════════════════════════

def compose_fit_score(fit_score: FitScore, orchestration_method: str) -> None:
    """Compose the final Fit Score on a FitScore object in place.

    Pre-conditions:
      - fit_score.product_labability, .instructional_value, and
        .customer_fit PillarScore objects are already populated by the
        three per-pillar scorers.
      - orchestration_method is the product's orchestration method
        string (empty string is valid and maps to the "any" method class).

    Post-conditions:
      - fit_score.total_override is set to the composed Fit Score.
      - fit_score.technical_fit_multiplier is set to the multiplier used.
      - fit_score.pl_score_pre_ceiling and fit_score.ceilings_applied
        are NOT touched here — those are audit fields owned by the
        Pillar 1 scorer (or are None in the new path since CEILING_FLAGS
        has been retired in favor of in-pillar score_override).
      - fit_score.total returns the composed number going forward
        because FitScore.total uses total_override when set.

    Math:
        pl_contrib  = pl_score × (pl_weight / 100)
        iv_contrib  = iv_score × (iv_weight / 100) × multiplier
        cf_contrib  = cf_score × (cf_weight / 100) × multiplier
        fit_score   = clamp(round(pl_contrib + iv_contrib + cf_contrib), 0, 100)

    The multiplier applies ONLY to IV + CF (the "downstream" pillars) —
    never to PL.  That is the asymmetric coupling rule:

        Weak PL drags IV + CF contribution down.
        Weak IV or weak CF does NOT drag PL contribution down.

    Rationale: a product we cannot lab is a lab-delivery problem, and
    our framework's value proposition is lab-based training.  A great
    instructional case does not recover a product we cannot run.  But
    a great lab experience is still credited at full weight even when
    the instructional case or customer fit is weak — those pillars
    just contribute their normal weighted share.

    Returns:
        None — FitScore is mutated in place.  Callers read the
        composed value via fit_score.total.
    """
    pl_pillar = _PILLAR_LOOKUP.get("product_labability")
    iv_pillar = _PILLAR_LOOKUP.get("instructional_value")
    cf_pillar = _PILLAR_LOOKUP.get("customer_fit")
    if not (pl_pillar and iv_pillar and cf_pillar):
        log.error(
            "fit_score_composer.compose_fit_score: pillar config missing "
            "from scoring_config.PILLARS — cannot compose. Leaving "
            "fit_score.total_override unset."
        )
        return

    pl_score = int(fit_score.product_labability.score or 0)
    iv_score = int(fit_score.instructional_value.score or 0)
    cf_score = int(fit_score.customer_fit.score or 0)

    multiplier = get_technical_fit_multiplier(pl_score, orchestration_method or "")

    pl_contrib = pl_score * (pl_pillar.weight / 100)
    iv_contrib = iv_score * (iv_pillar.weight / 100) * multiplier
    cf_contrib = cf_score * (cf_pillar.weight / 100) * multiplier

    weighted_sum = pl_contrib + iv_contrib + cf_contrib
    total = max(0, min(100, round(weighted_sum)))

    fit_score.total_override = int(total)
    fit_score.technical_fit_multiplier = float(multiplier)

    # Populate the stored `total` field so it survives asdict() serialization.
    # FitScore.total is a dataclass field (not a property) since 2026-04-08.
    from models import recompute_fit_total
    recompute_fit_total(fit_score)
