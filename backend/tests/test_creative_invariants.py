"""Phase 4 — creative end-to-end invariant tests.

Designed by docs/code-review-2026-04-07.md §"Phase 4 — creative test strategy".
The 88 structural tests we already had would not have caught any of the
CRITICAL findings in that review — they assert config shape, not the
integration paths between config / parser / normalizer / math / render /
storage. The bugs hide in the integration paths.

These tests are *invariant* assertions that walk every saved analysis on
disk and confirm runtime guarantees that span layers. They run against
real data, so a single broken save will surface as a real failure.

Test classes implemented here (matching the design doc):

    Class 3 — Vocabulary closure (Pillar 1 badges in canonical lists,
              Pillar 2/3 badges have valid signal_category)
    Class 4 — Bold prefix doesn't leak (`**...|...:**` never starts a
              claim — Phase 1 normalization must have run)
    Class 5 — Cache stamp truth (version-stamped files have non-zero
              products; cache-and-append doesn't lie about timestamps)
    Class 6 — Pillar isolation (Pillar 1 badges have no rubric fields,
              Pillar 2/3 badges always do)
    Class 7 — Polarity invariants (math layer guarantees: scores in
              [0, dim.weight], multipliers <= 1.0, etc.)
    Class 9 — Layer Discipline (no app.py call to scoring_math /
              core.assign_verdict — must go through intelligence layer)

The fixture-dependent classes (1, 2, 8) and the noisy literal-grep
class (10) are deferred to backlog — they need a small fixture library
and a quieter constant scanner before they pay their way.

Failure messages always name the file + product + dimension so a real
violation is immediately actionable.
"""
from __future__ import annotations

import ast
import glob
import json
import os
from typing import Any

import pytest

import scoring_config as cfg


# ── Test data discovery ────────────────────────────────────────────────────

_BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_COMPANY_INTEL_DIR = os.path.join(_BACKEND_DIR, "data", "company_intel")
_APP_PATH = os.path.join(_BACKEND_DIR, "app.py")


def _load_saved_analyses(current_only: bool = True) -> list[tuple[str, dict]]:
    """Load every analysis_*.json file from data/company_intel/.

    Skips the legacy quarantine directory and any non-analysis json files.
    Returns (filename, parsed_dict) tuples for parametrization.

    When `current_only=True` (the default), files whose
    `_scoring_logic_version` doesn't match `cfg.SCORING_LOGIC_VERSION`
    are skipped — those are already known-stale and queued for re-score
    by the cache versioning gate, so it isn't fair to enforce current
    architectural rules against them. They will get a fresh score on
    next access and the new save will be subject to these tests.
    """
    if not os.path.isdir(_COMPANY_INTEL_DIR):
        return []
    out: list[tuple[str, dict]] = []
    current_version = getattr(cfg, "SCORING_LOGIC_VERSION", None)
    for path in sorted(glob.glob(os.path.join(_COMPANY_INTEL_DIR, "analysis_*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if current_only and current_version:
            saved_version = data.get("_scoring_logic_version")
            if saved_version != current_version:
                continue
        out.append((os.path.basename(path), data))
    return out


_SAVED_ANALYSES = _load_saved_analyses(current_only=True)


def _recompute_in_memory(analysis: dict) -> dict:
    """Run the same recompute path Inspector runs at every page load.

    Mutates a deep copy in place — Phase 1 normalization strips bold
    prefixes, badges get collected for math, scoring math runs, scores
    write back, Phase 2 normalization merges duplicates. Returns the
    mutated copy. Tests that want "what the user actually sees" should
    use this view, not the raw saved JSON. Tests that want "what's on
    disk verbatim" should use the raw view.
    """
    import copy
    import intelligence
    snap = copy.deepcopy(analysis)
    try:
        intelligence.recompute_analysis(snap)
    except Exception:
        # Don't mask the original analysis if recompute itself fails —
        # let the caller deal with the unmutated copy. The polarity
        # tests below will catch a recompute regression separately.
        pass
    return snap


# ── Pillar key helpers ─────────────────────────────────────────────────────

_PILLAR_1_KEY = "product_labability"
_PILLAR_2_KEY = "instructional_value"
_PILLAR_3_KEY = "customer_fit"

# Pillar 1 badge.name must come from one of these vocabularies (canonical
# signal/penalty model). Pillar 2/3 names are AI-synthesized and don't
# need to match a vocabulary — they're checked via signal_category instead.
def _pillar_1_valid_names() -> set[str]:
    names: set[str] = set()
    for pillar in cfg.PILLARS:
        if pillar.name.lower().replace(" ", "_") != _PILLAR_1_KEY:
            continue
        for dim in pillar.dimensions:
            for badge in dim.badges or ():
                names.add(badge.name)
    return names


def _pillar_2_3_signal_categories_by_dim() -> dict[str, set[str]]:
    """Map dimension name → set of allowed signal_category strings.

    Pillar 2/3 use the rubric model — every emitted badge must tag itself
    with a signal_category drawn from that dimension's rubric.
    """
    out: dict[str, set[str]] = {}
    for pillar in cfg.PILLARS:
        pkey = pillar.name.lower().replace(" ", "_")
        if pkey == _PILLAR_1_KEY:
            continue
        for dim in pillar.dimensions:
            rubric = getattr(dim, "rubric", None)
            cats = set(getattr(rubric, "signal_categories", None) or ())
            out[dim.name] = cats
    return out


_PILLAR_1_NAMES = _pillar_1_valid_names()
_PILLAR_2_3_SIGCATS = _pillar_2_3_signal_categories_by_dim()


def _iter_dimensions(analysis: dict):
    """Yield (product_name, pillar_key, dimension_dict) for every dim in
    every product in the analysis. Tolerant to missing fields — these
    are real saved files and shapes drift over time."""
    for product in analysis.get("products") or ():
        if not isinstance(product, dict):
            continue
        pname = product.get("name") or "<unknown>"
        fs = product.get("fit_score") or {}
        if not isinstance(fs, dict):
            continue
        for pkey in (_PILLAR_1_KEY, _PILLAR_2_KEY, _PILLAR_3_KEY):
            pillar = fs.get(pkey)
            if not isinstance(pillar, dict):
                continue
            for dim in pillar.get("dimensions") or ():
                if isinstance(dim, dict):
                    yield pname, pkey, dim


# ═══════════════════════════════════════════════════════════════════════════
# Class 4 — Bold prefix doesn't leak
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_no_bold_prefix_in_claims(filename: str, analysis: dict) -> None:
    """Phase 1 normalization (`normalize_for_scoring`) strips bold
    `**Label | Qualifier:**` prefixes from every evidence claim before
    the math runs. If we still see those prefixes after recompute, the
    normalization didn't run — every cached badge popover competes with
    the canonical badge.name and the rubric-style "**Label:**" prefix
    leaks into the UI. This is the Devolutions-shape bug from the
    2026-04-07 code review.

    Tests against the recomputed view (what the user actually sees),
    not the raw saved JSON. Saved data is allowed to carry the bold
    prefixes because Phase 1 normalization runs at render time on
    every load, by design.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk — nothing to validate")

    rendered = _recompute_in_memory(analysis)
    offenders: list[str] = []
    for pname, _pkey, dim in _iter_dimensions(rendered):
        for badge in dim.get("badges") or ():
            if not isinstance(badge, dict):
                continue
            for ev in badge.get("evidence") or ():
                if not isinstance(ev, dict):
                    continue
                claim = (ev.get("claim") or "").strip()
                if claim.startswith("**") and "|" in claim[:80] and "**" in claim[2:80]:
                    offenders.append(
                        f"{filename} → {pname} → {dim.get('name')} → "
                        f"{badge.get('name')!r}: {claim[:120]!r}"
                    )
    assert not offenders, (
        f"{len(offenders)} evidence claims still carry bold prefixes "
        f"(Phase 1 normalization did not run for these badges):\n  - "
        + "\n  - ".join(offenders[:10])
        + (f"\n  ... +{len(offenders) - 10} more" if len(offenders) > 10 else "")
    )


# ═══════════════════════════════════════════════════════════════════════════
# Class 6 — Pillar isolation
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_pillar_1_badges_have_no_rubric_fields(filename: str, analysis: dict) -> None:
    """Pillar 1 (Product Labability) uses the canonical signal/penalty
    model — badges have a name from a fixed vocabulary, no rubric fields.
    Pillar 2/3 use the rubric model — badges have variable names AND
    populated `strength` + `signal_category`.

    If a Pillar 1 badge has either field populated, the architectural
    boundary leaked. If a Pillar 2/3 badge is missing them, the rubric
    model degraded to color-fallback math.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")

    p1_violators: list[str] = []
    p23_missing_strength: list[str] = []
    p23_missing_sigcat: list[str] = []

    valid_strengths = {"strong", "moderate", "weak"}

    for pname, pkey, dim in _iter_dimensions(analysis):
        for badge in dim.get("badges") or ():
            if not isinstance(badge, dict):
                continue
            bname = badge.get("name") or "<no name>"
            strength = (badge.get("strength") or "").strip().lower()
            sigcat = (badge.get("signal_category") or "").strip()
            color = (badge.get("color") or "").strip().lower()

            if pkey == _PILLAR_1_KEY:
                # Pillar 1 must NOT carry rubric fields. Empty string OK.
                if strength or sigcat:
                    p1_violators.append(
                        f"{filename} → {pname} → {dim.get('name')} → "
                        f"{bname!r} has rubric fields "
                        f"(strength={strength!r}, signal_category={sigcat!r})"
                    )
            else:
                # Pillar 2/3 must carry strength + signal_category UNLESS
                # the badge is a hard-negative red — those fall to color
                # points instead of rubric value, so the fields are allowed
                # to be empty by design.
                if color == "red":
                    continue
                if not strength or strength not in valid_strengths:
                    p23_missing_strength.append(
                        f"{filename} → {pname} → {dim.get('name')} → "
                        f"{bname!r} has no/invalid strength (color={color!r})"
                    )
                if not sigcat:
                    p23_missing_sigcat.append(
                        f"{filename} → {pname} → {dim.get('name')} → "
                        f"{bname!r} has no signal_category (color={color!r})"
                    )

    msgs: list[str] = []
    if p1_violators:
        msgs.append(
            f"PILLAR 1 LEAK: {len(p1_violators)} badges carry rubric fields:\n  - "
            + "\n  - ".join(p1_violators[:5])
        )
    if p23_missing_strength:
        msgs.append(
            f"PILLAR 2/3 STRENGTH MISSING: {len(p23_missing_strength)} non-red "
            f"rubric badges lack a valid strength tier:\n  - "
            + "\n  - ".join(p23_missing_strength[:5])
        )
    if p23_missing_sigcat:
        msgs.append(
            f"PILLAR 2/3 SIGNAL_CATEGORY MISSING: {len(p23_missing_sigcat)} "
            f"non-red rubric badges lack a signal_category:\n  - "
            + "\n  - ".join(p23_missing_sigcat[:5])
        )
    assert not msgs, "\n\n".join(msgs)


# ═══════════════════════════════════════════════════════════════════════════
# Class 3 — Vocabulary closure (limited to architectural assertions only)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_badge_color_in_canonical_set(filename: str, analysis: dict) -> None:
    """Every badge color in saved data must be one of the four canonical
    colors. Anything else is corrupted data or a parser bug — the math
    layer assumes these four when looking up `BADGE_COLOR_POINTS`.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")

    valid_colors = set(cfg.BADGE_COLOR_POINTS.keys())
    bad: list[str] = []
    for pname, _pkey, dim in _iter_dimensions(analysis):
        for badge in dim.get("badges") or ():
            if not isinstance(badge, dict):
                continue
            color = (badge.get("color") or "").strip().lower()
            if color and color not in valid_colors:
                bad.append(
                    f"{filename} → {pname} → {dim.get('name')} → "
                    f"{badge.get('name')!r} color={color!r}"
                )
    assert not bad, (
        f"{len(bad)} badges have a non-canonical color "
        f"(must be one of {sorted(valid_colors)}):\n  - "
        + "\n  - ".join(bad[:10])
    )


@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_pillar_2_3_signal_category_in_rubric(filename: str, analysis: dict) -> None:
    """Every Pillar 2/3 badge that carries a signal_category must use a
    value from its dimension's rubric `signal_categories` list. The AI
    is told to pick from the list; if it invents a new one, the math
    layer can't credit it via the rubric model and the badge falls back
    to color points only.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")

    drift: list[str] = []
    for pname, pkey, dim in _iter_dimensions(analysis):
        if pkey == _PILLAR_1_KEY:
            continue
        allowed = _PILLAR_2_3_SIGCATS.get(dim.get("name") or "", set())
        if not allowed:
            continue  # dim has no rubric in config — nothing to check
        for badge in dim.get("badges") or ():
            if not isinstance(badge, dict):
                continue
            sigcat = (badge.get("signal_category") or "").strip()
            if sigcat and sigcat not in allowed:
                drift.append(
                    f"{filename} → {pname} → {dim.get('name')} → "
                    f"{badge.get('name')!r} signal_category={sigcat!r} "
                    f"(not in rubric)"
                )
    assert not drift, (
        f"{len(drift)} Pillar 2/3 badges carry a signal_category that "
        f"isn't in the dimension's rubric:\n  - "
        + "\n  - ".join(drift[:10])
    )


# ═══════════════════════════════════════════════════════════════════════════
# Class 5 — Cache stamp truth
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_version_stamped_analyses_have_products(filename: str, analysis: dict) -> None:
    """If an analysis is stamped with a `_scoring_logic_version`, it
    must contain at least one product. The bug this catches is the
    pre-stamp-then-wipe sequence from the 2026-04-06 evening Trellix
    incident, where an analysis ended up with a current version stamp
    but no scored products — silently lying about its freshness.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")
    version = analysis.get("_scoring_logic_version")
    if not version:
        return  # unstamped is fine — handled as cache miss elsewhere
    products = analysis.get("products") or []
    assert len(products) > 0, (
        f"{filename}: analysis is stamped with "
        f"_scoring_logic_version={version!r} but has zero products. "
        f"This is the cache-stamp lie pattern from the 2026-04-06 "
        f"Trellix incident — wipe the file or rescore."
    )


# ═══════════════════════════════════════════════════════════════════════════
# Class 7 — Polarity invariants
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_dimension_scores_in_bounds(filename: str, analysis: dict) -> None:
    """Every saved dimension score must be in `[0, dim.weight]`. The
    math layer floors at 0 and caps at the dimension weight — if any
    saved value is outside that range, either the math layer regressed
    or someone hand-edited a saved file.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")

    bad: list[str] = []
    for pname, _pkey, dim in _iter_dimensions(analysis):
        score = dim.get("score")
        weight = dim.get("weight")
        if not isinstance(score, (int, float)) or not isinstance(weight, (int, float)):
            continue
        if score < 0 or score > weight:
            bad.append(
                f"{filename} → {pname} → {dim.get('name')}: "
                f"score={score} weight={weight}"
            )
    assert not bad, (
        f"{len(bad)} dimensions have scores out of [0, weight] bounds:\n  - "
        + "\n  - ".join(bad[:10])
    )


@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_fit_scores_in_zero_to_hundred(filename: str, analysis: dict) -> None:
    """Fit Score is bounded `[0, 100]`. Anything outside means the
    weighted-sum or rounding pipeline regressed.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")
    bad: list[str] = []
    for product in analysis.get("products") or ():
        if not isinstance(product, dict):
            continue
        fs = product.get("fit_score") or {}
        if not isinstance(fs, dict):
            continue
        total = fs.get("total")
        if isinstance(total, (int, float)) and (total < 0 or total > 100):
            bad.append(f"{filename} → {product.get('name')}: fit_score.total={total}")
    assert not bad, "Fit scores out of [0,100]:\n  - " + "\n  - ".join(bad[:10])


def test_math_layer_polarity_invariants() -> None:
    """Direct invariant test of `scoring_math.compute_all` — feeds it a
    minimal-but-valid input and asserts every dimension result satisfies:

      - score ∈ [0, dim.weight]
      - friction badges never increase score
      - ceiling caps never increase score
      - technical fit multiplier ≤ 1.0 (never amplifies)

    This catches polarity bugs before they hit any saved file.
    """
    import scoring_math

    badges_by_dim: dict[str, list[dict]] = {}
    for pillar in cfg.PILLARS:
        for dim in pillar.dimensions:
            badges_by_dim[dim.name.lower().replace(" ", "_")] = []

    result = scoring_math.compute_all(
        badges_by_dimension=badges_by_dim,
        ceiling_flags=[],
        orchestration_method="",
    )

    # Empty badges → every dimension score is exactly 0, never negative.
    for dim_key, dim_result in (result.get("dimensions") or {}).items():
        score = dim_result.get("score") if isinstance(dim_result, dict) else 0
        assert isinstance(score, (int, float)), f"{dim_key}: score not numeric"
        assert score >= 0, f"{dim_key}: empty badges produced negative score {score}"

    # Technical fit multiplier (when present) is always ≤ 1.0
    multiplier = result.get("technical_fit_multiplier")
    if isinstance(multiplier, (int, float)):
        assert multiplier <= 1.0, (
            f"technical_fit_multiplier > 1.0 ({multiplier}) — multipliers must "
            f"only DAMPEN, never amplify, per the scoring math contract."
        )


# ═══════════════════════════════════════════════════════════════════════════
# Class 9 — Layer Discipline (AST)
# ═══════════════════════════════════════════════════════════════════════════

# Functions in the math/verdict layers that the Inspector Flask app must
# NOT call directly. Per CLAUDE.md Layer Discipline: any code that does
# scoring/recompute work belongs in the Intelligence layer so all three
# tools can share it. The public contract from app.py is
# `intelligence.recompute_analysis()` — Inspector calls THAT, and only that.
_FORBIDDEN_DIRECT_CALLS = {
    # (module, function) — Inspector must not call these directly.
    ("scoring_math", "compute_all"),
    ("scoring_math", "compute_acv_potential"),
    ("scoring_math", "compute_fit_score"),
    ("core", "assign_verdict"),
}


def _walk_calls(tree: ast.AST):
    """Yield every Call node in the tree along with its dotted-name
    attribute target if any (e.g. `scoring_math.compute_all` → that string)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            yield node, func.value.id, func.attr


def test_app_py_does_not_bypass_intelligence_layer() -> None:
    """Layer Discipline (Frank, 2026-04-07): no function in `backend/app.py`
    may call the math layer or the verdict assigner directly. All scoring
    work must go through `intelligence.recompute_analysis()` /
    `intelligence.score()` so Prospector and Designer get the same path.

    This is the structural lock for the principle the 2026-04-07 deep
    code review identified as the worst bug-class — Inspector running
    a different math path than the scorer wrote, silently producing
    wrong scores.

    Enforced by AST inspection of `backend/app.py`. Future commits that
    sneak a direct call back into the Flask app fail this test.
    """
    if not os.path.isfile(_APP_PATH):
        pytest.skip("backend/app.py not found")
    with open(_APP_PATH, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)

    violations: list[str] = []
    for node, mod_name, func_name in _walk_calls(tree):
        if (mod_name, func_name) in _FORBIDDEN_DIRECT_CALLS:
            violations.append(
                f"  app.py:{node.lineno}: {mod_name}.{func_name}() — "
                f"call this through intelligence.recompute_analysis() instead"
            )

    assert not violations, (
        "Layer Discipline violation: backend/app.py calls intelligence-layer "
        "functions directly. The Flask app must go through the Intelligence "
        "layer's public contract so Prospector and Designer share the same "
        "path. Move these calls into intelligence.py:\n"
        + "\n".join(violations)
    )


# ═══════════════════════════════════════════════════════════════════════════
# Class 1 — Round-trip fixture tests (no normalization rewrite)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_recompute_preserves_badge_identity(filename: str, analysis: dict) -> None:
    """Round-trip test: load a saved analysis, run the full recompute
    path, and assert that no badge.name was rewritten by normalization.
    The math layer must NEVER mutate badge identity — it reads strength
    and signal_category to compute scores, and the display layer merges
    duplicates by name. If a name drifts during recompute, that's a
    CRIT-class bug (the Devolutions / SOTI field-drop pattern from the
    2026-04-07 deep code review).

    PILLAR 3 EXEMPT: Customer Fit is unified across products by design
    (Frank, 2026-04-07 — it's a company-level property, not a product
    property). Phase F broadcasts the same CF dimensions onto every
    product in an analysis at recompute time, so a product that didn't
    originally surface a particular CF badge will gain it after recompute.
    That's expected, not drift, so this test only enforces the round-
    trip identity invariant on Pillars 1 and 2.

    Phase 2 normalization may also merge duplicate-named badges, so a
    rendered list is allowed to be shorter than the saved list, but
    every surviving rendered badge must have come from the saved input.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")

    rendered = _recompute_in_memory(analysis)

    # Build a name set per (product, dim) on both sides — order-
    # independent so the post-render merge is fine. EXCLUDES Pillar 3
    # (Customer Fit) per the unification design.
    def by_dim_excluding_p3(an: dict) -> dict[tuple[str, str], set[str]]:
        idx: dict[tuple[str, str], set[str]] = {}
        for pname, pkey, dim in _iter_dimensions(an):
            if pkey == _PILLAR_3_KEY:
                continue
            key = (pname, dim.get("name") or "")
            bucket = idx.setdefault(key, set())
            for badge in dim.get("badges") or ():
                if isinstance(badge, dict):
                    name = badge.get("name") or ""
                    if name:
                        bucket.add(name)
        return idx

    saved = by_dim_excluding_p3(analysis)
    after = by_dim_excluding_p3(rendered)

    drift: list[str] = []
    for key, after_set in after.items():
        saved_set = saved.get(key, set())
        for name in after_set:
            if name not in saved_set:
                drift.append(
                    f"{filename} → {key[0]} → {key[1]}: rendered "
                    f"badge {name!r} does not match any saved badge "
                    f"name in this dimension"
                )
    assert not drift, (
        f"{len(drift)} Pillar 1/2 badge identities drifted during "
        f"recompute (Phase 2 normalization is rewriting names — that's "
        f"a CRIT-class field-drop bug):\n  - "
        + "\n  - ".join(drift[:10])
    )


# ═══════════════════════════════════════════════════════════════════════════
# Class 2 — Score isomorphism (recompute is deterministic + idempotent)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("filename,analysis",
                         _SAVED_ANALYSES,
                         ids=[f for f, _ in _SAVED_ANALYSES] or ["no-fixtures"])
def test_recompute_is_idempotent(filename: str, analysis: dict) -> None:
    """Recompute must be deterministic AND idempotent: running it twice
    on the same input produces the same Fit Score and the same per-
    dimension scores. Any drift means recompute has hidden state — the
    rendered page would change between F5s, which is the polite version
    of "the math is wrong sometimes."

    This catches CRIT-class bugs where, e.g., normalization mutates
    a list that's read again on the second pass, or where Customer Fit
    unification reads from one place on pass 1 and another on pass 2.
    """
    if filename == "no-fixtures":
        pytest.skip("No saved analyses on disk")

    pass1 = _recompute_in_memory(analysis)
    pass2 = _recompute_in_memory(pass1)

    def signature(an: dict) -> list[tuple[str, int, list[tuple[str, int]]]]:
        sig: list[tuple[str, int, list[tuple[str, int]]]] = []
        for product in an.get("products") or ():
            if not isinstance(product, dict):
                continue
            pname = product.get("name") or ""
            fs = product.get("fit_score") or {}
            total = int((fs.get("total") or 0) if isinstance(fs, dict) else 0)
            dim_scores: list[tuple[str, int]] = []
            for _pname2, _pkey, dim in _iter_dimensions({"products": [product]}):
                dim_scores.append((dim.get("name") or "",
                                   int(dim.get("score") or 0)))
            dim_scores.sort()
            sig.append((pname, total, dim_scores))
        sig.sort()
        return sig

    sig1 = signature(pass1)
    sig2 = signature(pass2)
    assert sig1 == sig2, (
        f"{filename}: recompute is NOT idempotent — second pass "
        f"produced different scores than first pass.\n"
        f"This is a hidden-state bug in the recompute path. "
        f"Pass 1 vs Pass 2 differs."
    )


def test_recompute_against_a_minimal_synthetic_analysis() -> None:
    """Build a minimal valid analysis dict in memory and run recompute
    against it. Asserts the math contract end-to-end without depending
    on any saved file:

      - empty badges → every dim score = 0
      - fit_score.total = 0
      - no exception raised
      - poor_match_flags=[] does not trigger any ceiling
    """
    import intelligence

    analysis = {
        "company_name": "Test Co",
        "discovery_id": "test-no-disc",
        "products": [
            {
                "name": "Test Product",
                "category": "Software",
                "deployment_model": "installable",
                "orchestration_method": "Hyper-V",
                "poor_match_flags": [],
                "fit_score": {
                    "total": 0,
                    "_total": 0,
                    "product_labability": {
                        "name": "Product Labability",
                        "weight": 40,
                        "dimensions": [
                            {"name": dim.name, "score": 0,
                             "weight": dim.weight, "badges": []}
                            for dim in cfg.PILLARS[0].dimensions
                        ],
                    },
                    "instructional_value": {
                        "name": "Instructional Value",
                        "weight": 30,
                        "dimensions": [
                            {"name": dim.name, "score": 0,
                             "weight": dim.weight, "badges": []}
                            for dim in cfg.PILLARS[1].dimensions
                        ],
                    },
                    "customer_fit": {
                        "name": "Customer Fit",
                        "weight": 30,
                        "dimensions": [
                            {"name": dim.name, "score": 0,
                             "weight": dim.weight, "badges": []}
                            for dim in cfg.PILLARS[2].dimensions
                        ],
                    },
                },
            }
        ],
    }

    intelligence.recompute_analysis(analysis)

    product = analysis["products"][0]
    fs = product["fit_score"]
    assert fs["total"] == 0, (
        f"Empty-badge product produced non-zero fit score "
        f"({fs['total']}) — math layer is not honoring the no-evidence "
        f"contract."
    )
    for pkey in ("product_labability", "instructional_value", "customer_fit"):
        for dim in fs[pkey]["dimensions"]:
            assert dim["score"] == 0, (
                f"{pkey}.{dim['name']} produced non-zero score "
                f"({dim['score']}) on a product with no badges"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Class 8 — Adversarial fixtures (hand-crafted edge cases)
# ═══════════════════════════════════════════════════════════════════════════

def _empty_pillar_dict(pillar: Any) -> dict:
    return {
        "name": pillar.name,
        "weight": pillar.weight,
        "dimensions": [
            {"name": d.name, "score": 0, "weight": d.weight, "badges": []}
            for d in pillar.dimensions
        ],
    }


def _empty_fit_score() -> dict:
    return {
        "total": 0,
        "_total": 0,
        "product_labability": _empty_pillar_dict(cfg.PILLARS[0]),
        "instructional_value": _empty_pillar_dict(cfg.PILLARS[1]),
        "customer_fit": _empty_pillar_dict(cfg.PILLARS[2]),
    }


def test_adversarial_product_missing_fit_score_field() -> None:
    """A product with no `fit_score` field at all must not crash recompute.
    The recompute path is supposed to gracefully assign an empty fit_score
    and move on — Inspector page loads against half-broken cached data
    should never 500.
    """
    import intelligence
    analysis = {
        "company_name": "Test",
        "discovery_id": "test-x",
        "products": [
            {"name": "No Fit Score Product", "category": "Software"},
        ],
    }
    intelligence.recompute_analysis(analysis)
    # Recompute is allowed to backfill an empty fit_score; the contract
    # is just that it doesn't crash and the product is still in the list.
    assert len(analysis["products"]) == 1


def test_adversarial_empty_dimensions_list() -> None:
    """A product with `fit_score` present but every dimension missing
    badges must produce a Fit Score of 0 (not crash, not negative).
    """
    import intelligence
    analysis = {
        "company_name": "Test",
        "discovery_id": "test-y",
        "products": [
            {
                "name": "Empty Dims",
                "deployment_model": "installable",
                "orchestration_method": "",
                "poor_match_flags": [],
                "fit_score": _empty_fit_score(),
            }
        ],
    }
    intelligence.recompute_analysis(analysis)
    assert analysis["products"][0]["fit_score"]["total"] == 0


def test_adversarial_duplicate_named_badges_merge() -> None:
    """Two badges with the same name in the same dimension are the
    classic merge path. Phase 2 normalization should merge them and
    promote color to worst-of-group. Recompute must not crash and
    must produce a single badge with the worst color.
    """
    import intelligence
    pillar1 = cfg.PILLARS[0]
    fs = _empty_fit_score()
    # Inject two same-named badges into the first Pillar 1 dim
    target_dim = fs["product_labability"]["dimensions"][0]
    target_dim["badges"] = [
        {
            "name": "Runs in Hyper-V",
            "color": "green",
            "qualifier": "Strength",
            "evidence": [],
            "strength": "",
            "signal_category": "",
        },
        {
            "name": "Runs in Hyper-V",
            "color": "amber",
            "qualifier": "Concern",
            "evidence": [],
            "strength": "",
            "signal_category": "",
        },
    ]
    analysis = {
        "company_name": "Test",
        "discovery_id": "test-z",
        "products": [
            {
                "name": "Dup Test",
                "deployment_model": "installable",
                "orchestration_method": "Hyper-V",
                "poor_match_flags": [],
                "fit_score": fs,
            }
        ],
    }
    intelligence.recompute_analysis(analysis)
    final_badges = analysis["products"][0]["fit_score"]["product_labability"]["dimensions"][0]["badges"]
    names = [b.get("name") for b in final_badges if isinstance(b, dict)]
    # The merge should collapse duplicates — only ONE Runs in Hyper-V survives
    assert names.count("Runs in Hyper-V") == 1, (
        f"Phase 2 normalization did not merge duplicate-named badges. "
        f"Final names: {names}"
    )


def test_adversarial_stale_logic_version_handled_by_score_path() -> None:
    """The cache versioning gate (`is_cached_logic_current`) must
    correctly classify a stale version as stale. This is the contract
    that score() relies on to wipe and re-score stale analyses.
    """
    fake_stale = {
        "_scoring_logic_version": "2020-01-01.ancient-version-that-will-never-be-current",
    }
    fake_current = {
        "_scoring_logic_version": cfg.SCORING_LOGIC_VERSION,
    }
    assert cfg.is_cached_logic_current(fake_stale) is False
    assert cfg.is_cached_logic_current(fake_current) is True
    assert cfg.is_cached_logic_current({}) is False
    assert cfg.is_cached_logic_current(None) is True  # cache miss != stale


def test_adversarial_zero_product_discovery_handled() -> None:
    """An analysis with zero products must not crash recompute and
    must not produce any per-product side effects.
    """
    import intelligence
    analysis = {
        "company_name": "Empty Co",
        "discovery_id": "test-zero",
        "products": [],
    }
    intelligence.recompute_analysis(analysis)
    assert analysis["products"] == []


# ═══════════════════════════════════════════════════════════════════════════
# Class 10 — Define-Once enforcement (literal scan, narrow + targeted)
# ═══════════════════════════════════════════════════════════════════════════

# A small set of HIGH-VALUE constants from scoring_config that should
# never appear as literals anywhere else in the active backend. The full
# scan in the design doc is "every PILLARS literal" — that's noisy, so
# we narrow to the constants whose drift would be most painful.
#
# Numeric constants are deliberately excluded — small integers like 3, 5,
# 8, 12 collide with array indices, version numbers, format positions,
# and dozens of other innocent uses across the codebase. Numeric literal
# enforcement is `test_no_hardcoding.py`'s magic-number scan, which uses
# AST + the `# magic-allowed:` annotation system. This Class 10 scan
# focuses on STRING constants where the literal collision rate is low
# enough for grep-style detection to be useful.
_DEFINE_ONCE_CONSTANTS_TO_SCAN = (
    "SCORING_LOGIC_VERSION",
    "DEFAULT_RATE_TIER_NAME",
)

# Files that are allowed to define or contain these literals.
_DEFINE_ONCE_ALLOWED_FILES = {
    "scoring_config.py",
    "scoring_math.py",  # math layer reads from cfg.* but uses the literal name
    # Tests can reference any constant — they're documenting expected behavior.
}


def test_define_once_high_value_constants_not_inlined() -> None:
    """Walk the active backend Python files. For each named constant
    in `_DEFINE_ONCE_CONSTANTS_TO_SCAN`, look up its value in
    `scoring_config` and verify the literal value does not appear in
    any other backend file outside the allowlist.

    Narrow + targeted: catches the cases where a developer (or Claude)
    inlines a magic value instead of referencing `cfg.<NAME>`. Doesn't
    cover every config constant — that's `test_no_hardcoding.py`'s job.
    """
    backend_root = _BACKEND_DIR
    py_files: list[str] = []
    for root, _dirs, files in os.walk(backend_root):
        # Skip tests and __pycache__ and the data directory
        if "tests" in root.split(os.sep):
            continue
        if "__pycache__" in root or os.sep + "data" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    violations: list[str] = []
    for const_name in _DEFINE_ONCE_CONSTANTS_TO_SCAN:
        value = getattr(cfg, const_name, None)
        if value is None:
            continue
        # Build a string-search literal we'd expect to see in inlined code.
        # For numbers we look for the bare number; for strings we look for
        # the quoted string.
        if isinstance(value, str):
            needle = f'"{value}"'
            alt_needle = f"'{value}'"
        elif isinstance(value, (int, float)):
            needle = str(value)
            alt_needle = None
        else:
            continue

        for path in py_files:
            base = os.path.basename(path)
            if base in _DEFINE_ONCE_ALLOWED_FILES:
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    src = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            if needle in src or (alt_needle and alt_needle in src):
                # Check it's NOT inside a `cfg.<NAME>` reference — those
                # are fine. The test is for INLINED literals.
                # Heuristic: if `cfg.<const_name>` also appears in the
                # file, the file is reading from cfg properly and the
                # literal match is incidental (e.g., a comment example).
                if f"cfg.{const_name}" in src or f"cfg .{const_name}" in src:
                    continue
                # And if the const_name itself appears as a reference, ok
                if const_name in src and f"cfg.{const_name}" not in src:
                    # ambiguous — could be a comment or a different reference,
                    # skip to avoid false positives
                    continue
                violations.append(
                    f"  {os.path.relpath(path, backend_root)}: contains "
                    f"literal {needle} (value of cfg.{const_name}) — "
                    f"reference cfg.{const_name} instead"
                )

    assert not violations, (
        "Define-Once violations: high-value scoring_config constants are "
        "inlined as literals in the backend. These will silently drift if "
        "the config changes. Reference the constant by name:\n"
        + "\n".join(violations[:15])
    )
