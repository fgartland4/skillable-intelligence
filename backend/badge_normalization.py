"""Badge normalization — shared Intelligence-layer module.

This module owns the two-phase badge normalization that ALL three tools
(Inspector, Prospector, Designer) need to apply when rendering scored
products. Per the Layer Discipline principle in Platform-Foundation.md,
intelligence work like this lives in the shared layer, NEVER in a tool's
own files. Inspector previously had these functions inline in app_new.py
which would have forced Prospector and Designer to either duplicate the
logic or import from the Inspector Flask app file (coupling them to
Inspector's lifecycle).

The two phases are deliberately separated per the 2026-04-06 decision-log
principle: "Visual changes must NEVER affect scoring." Phase 1 runs BEFORE
the scoring math and only does data-shape work that's safe for the math
to see. Phase 2 runs AFTER the scoring math and does display-only
transforms that the user sees but the math never does.

Public functions
================

normalize_for_scoring(p: dict) -> None
    Phase 1. Mutates the product dict in place. Strips evidence-claim
    bold prefixes so the popover text doesn't show a parallel non-canonical
    label competing with the canonical badge.name. NEVER touches
    badge.name, badge.color, badge.strength, or badge.signal_category —
    those are scoring inputs. Run this BEFORE collecting badges to feed
    into scoring_math.compute_all().

normalize_for_display(p: dict) -> None
    Phase 2. Mutates the product dict in place. Merges any same-named
    badges within a dimension and promotes color to the worst of the
    group (red > amber > green > gray) so risks aren't hidden. Carries
    rubric fields (strength, signal_category) through the merge so the
    next page load can still feed the math layer correctly. Run this
    AFTER scoring math + score writeback so visual merging cannot
    silently distort scores.

History
=======

These functions used to live in backend/app_new.py — the Inspector Flask
app. The deep code review on 2026-04-07 (docs/code-review-2026-04-07.md)
flagged this as a Layer Discipline violation under findings CRIT-2 and
CRIT-3: intelligence-layer work was buried in a tool file where Prospector
and Designer couldn't reach it. Phase C of the fix sequence relocated
them here.

Three concrete bugs in the same shape have shipped to production from
this code, all caused by parser/normalizer functions silently dropping
fields:

1. scorer_new.py:512 dropped strength + signal_category when feeding the
   math layer (commit e5c95c7)
2. app_new.py:_prepare_analysis_for_render did the same drop on every
   page load (commit 120e3c9)
3. app_new.py:_normalize_badges_for_display dropped them on the merge
   path (commit 0a6801d / Phase A)

The lesson is that there must be exactly ONE place that constructs badge
dicts from saved JSON. This module is that place. Any future tool that
needs to render or recompute scored products imports from here. Adding
a fourth function elsewhere is a bug class, not a stylistic choice.
"""

import re

# The bold-prefix pattern Claude consistently emits at the start of evidence
# claims: `**Label | Qualifier:** ...`. Phase 1 strips this prefix from the
# claim text so the popover doesn't show a non-canonical label competing
# with the canonical badge.name in the chip.
_EVIDENCE_LABEL_RE = re.compile(r'^\*\*([^*|]+?)\s*\|\s*([^*]+?):\*\*\s*')


def normalize_for_scoring(p: dict) -> None:
    """Phase 1 of badge normalization — runs BEFORE the scoring math.

    Strips the `**Label | Qualifier:**` bold prefix from each evidence
    claim so the popover text doesn't show a parallel non-canonical label
    competing with the canonical badge.name. NEVER replaces badge.name
    itself — that's canonical from Claude's output and the math layer
    matches it against scoring_config.SCORING_SIGNALS to credit points.

    Why this exists: Claude consistently produces bold prefix labels in
    evidence claims (e.g. `**Client-Side VM Path | Strength:** ...`).
    Without stripping, those labels render in the badge hover popover
    and compete visually with the canonical chip name. They look like
    a second badge name and confuse the reader.

    HISTORY: A previous version of this function "split" any badge whose
    evidence items all carried embedded labels into N new badges — using
    the embedded label as the new badge.name. That destroyed the canonical
    name BEFORE the math layer ran, causing every product to fall back to
    color-points scoring. Bug surfaced 2026-04-06 evening on Devolutions
    review. The fix is this version: never replace badge.name, only strip
    the prefix from claim text.

    Mutates the product dict in place. Display-only transforms (merging
    same-named badges, color promotion) live in normalize_for_display()
    and run AFTER the math.
    """
    fs = p.get("fit_score")
    if not isinstance(fs, dict):
        return

    for pillar_key, pillar_dict in fs.items():
        if not isinstance(pillar_dict, dict):
            continue
        for dim_dict in pillar_dict.get("dimensions", []) or []:
            if not isinstance(dim_dict, dict):
                continue
            for b in dim_dict.get("badges", []) or []:
                if not isinstance(b, dict):
                    continue
                ev_list = b.get("evidence", []) or []
                cleaned_ev = []
                for ev in ev_list:
                    if not isinstance(ev, dict):
                        cleaned_ev.append(ev)
                        continue
                    claim = ev.get("claim", "") or ""
                    m = _EVIDENCE_LABEL_RE.match(claim)
                    if m:
                        new_ev = dict(ev)
                        new_ev["claim"] = claim[m.end():].lstrip()
                        cleaned_ev.append(new_ev)
                    else:
                        cleaned_ev.append(ev)
                b["evidence"] = cleaned_ev


def normalize_for_display(p: dict) -> None:
    """Phase 2 of badge normalization — runs AFTER the scoring math.

    Decision-log principle (2026-04-06): visual changes must NEVER affect
    scoring. This function only does transforms that affect what the user
    sees, not what the math saw. By the time it runs, scores are already
    written into the product dict — these mutations cannot retroactively
    change them.

    **Defensive safety net for the universal variable-badge rule.**

    The scoring prompt now tells the AI to disambiguate same-name badges
    at the source — first occurrence keeps the canonical name, subsequent
    occurrences are renamed to a scoring signal name (preferred) or a
    qualifier-derived label (fallback). When the AI complies, this function
    has nothing to do because every badge in a dimension is already
    uniquely named.

    But two cases still produce duplicates:
      1. **Legacy cached analyses** scored before the prompt change. These
         still have raw duplicate-name badges from the old AI output. The
         merger collapses them so old pages render cleanly.
      2. **AI non-compliance** — the AI occasionally still emits duplicates
         despite the prompt instruction. The merger is the backstop.

    Merge behavior: combine all evidence items into one badge and promote
    the color to the worst of the group (red > amber > green > gray) so
    risks aren't hidden by an adjacent positive signal. The hover modal
    still shows every evidence item, so no information is lost.

    The math layer in Phase 1 has already been called against the
    pre-merge badge list, so dropping the count or changing colors here
    has zero effect on scores.

    Carries strength + signal_category through the merge construction
    AND through the color-promotion branch so the next page load (which
    re-feeds the math layer) doesn't lose rubric data and fall back to
    color points. CRIT-1 in code-review-2026-04-07.md was the third
    instance of this bug class shipping to production — same shape as
    the bugs fixed in commits e5c95c7 and 120e3c9.
    """
    import scoring_config as cfg

    fs = p.get("fit_score")
    if not isinstance(fs, dict):
        return

    # Read display severity ranking from config (Define-Once). Separate from
    # BADGE_COLOR_POINTS which is the scoring concept — these two dicts are
    # deliberately distinct per the 2026-04-06 decision-log principle.
    color_priority = cfg.BADGE_COLOR_DISPLAY_PRIORITY

    for pillar_key, pillar_dict in fs.items():
        if not isinstance(pillar_dict, dict):
            continue
        for dim_dict in pillar_dict.get("dimensions", []) or []:
            if not isinstance(dim_dict, dict):
                continue
            badges = dim_dict.get("badges", []) or []
            merged_by_name: dict[str, dict] = {}
            ordered_names: list[str] = []
            for b in badges:
                if not isinstance(b, dict):
                    continue
                name = (b.get("name") or "").strip()
                if not name:
                    continue
                if name not in merged_by_name:
                    merged_by_name[name] = {
                        "name": name,
                        "color": b.get("color", ""),
                        "qualifier": b.get("qualifier", ""),
                        "evidence": list(b.get("evidence") or []),
                        "strength": b.get("strength", ""),
                        "signal_category": b.get("signal_category", ""),
                    }
                    ordered_names.append(name)
                else:
                    existing = merged_by_name[name]
                    # Promote color to the worst (highest-priority) of the two
                    if color_priority.get(b.get("color", ""), 0) > color_priority.get(existing["color"], 0):
                        existing["color"] = b.get("color", "")
                        # MED-1: only overwrite qualifier if the new one is
                        # non-empty — otherwise the merge silently loses the
                        # existing badge's qualifier context.
                        new_qualifier = b.get("qualifier", "")
                        if new_qualifier:
                            existing["qualifier"] = new_qualifier
                    # Preserve rubric fields from whichever badge has them
                    # populated. If the first badge had empty rubric fields
                    # and the second has them, take the second's.
                    if not existing.get("strength") and b.get("strength"):
                        existing["strength"] = b.get("strength", "")
                    if not existing.get("signal_category") and b.get("signal_category"):
                        existing["signal_category"] = b.get("signal_category", "")
                    existing["evidence"].extend(b.get("evidence") or [])
            dim_dict["badges"] = [merged_by_name[n] for n in ordered_names]


def collect_badges_for_math(p: dict, dim_key_to_pillar_key: dict[str, str] | None = None) -> dict[str, list]:
    """Build the badges_by_dimension dict that scoring_math.compute_all expects.

    Walks every pillar/dimension/badge in the product dict and produces a
    {dim_key: [badge_dict, ...]} mapping where each badge_dict carries the
    SIX fields the math layer needs: name, color, qualifier, evidence,
    strength, signal_category. Carrying ALL six is the only safe pattern —
    omitting any of strength/signal_category silently breaks rubric scoring
    on Pillar 2/3 (CRIT-1 / e5c95c7 / 120e3c9).

    Used by intelligence_new.recompute_analysis() to feed the math layer
    from a saved analysis dict. Future Prospector and Designer code that
    needs the same recompute behavior should also call this rather than
    walking the product dict by hand.

    The dim_key_to_pillar_key mapping is optional — when provided, only
    dimensions that map to a known pillar are collected. When omitted,
    every dimension found in the product is included.
    """
    badges_by_dim: dict[str, list] = {}
    fs = p.get("fit_score")
    if not isinstance(fs, dict):
        return badges_by_dim

    for pillar_key, pillar_dict in fs.items():
        if not isinstance(pillar_dict, dict):
            continue
        for dim_dict in pillar_dict.get("dimensions", []) or []:
            if not isinstance(dim_dict, dict):
                continue
            dim_name = dim_dict.get("name", "")
            dim_key = dim_name.lower().replace(" ", "_")
            if dim_key_to_pillar_key is not None and dim_key not in dim_key_to_pillar_key:
                continue
            badge_objs: list[dict] = []
            for b in dim_dict.get("badges", []) or []:
                if isinstance(b, dict) and b.get("name"):
                    badge_objs.append({
                        "name": b["name"],
                        "color": b.get("color", ""),
                        "strength": b.get("strength", ""),
                        "signal_category": b.get("signal_category", ""),
                    })
            badges_by_dim[dim_key] = badge_objs
    return badges_by_dim
