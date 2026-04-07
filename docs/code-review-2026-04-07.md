# Deep Code Review — 2026-04-07

**Trigger:** Frank reviewed Devolutions and Trellix Deep Dive output and found symptoms of fundamental scoring bugs ("almost none of our agreed-upon rules are in effect"). The session that followed exposed several architectural defects that required emergency fixes (`e5c95c7`, `120e3c9`) before this review could even begin.

**Goal:** find every other bug of the same shape — and others — before Prospector and Designer get built on top of broken foundations.

**Method:** read the priority docs first (`collaboration-with-frank.md`, `Platform-Foundation.md`, `Badging-and-Scoring-Reference.md`, `decision-log.md`, `next-session-todo.md`). Then launch six parallel Explore subagents, each hunting a specific bug-class cluster that the Devolutions/Trellix incidents teach us to look for. Compile findings here.

**Status:** review complete. Fixes NOT applied — Frank decides priority order.

---

## Bug-class summary

| # | Bug class | Findings | Highest severity |
|---|---|---|---|
| 1 | Field-drop bugs (parser/normalizer rebuilds drop fields) | 1 confirmed + 1 secondary | **CRITICAL** |
| 2 | Visual-vs-scoring violations (display work in scoring path) | 4 | High |
| 3 | Duplicate paths and legacy code (orphaned files, drifted pairs) | 16 | **CRITICAL** |
| 4 | Cache version lies and GP5 violations (stamp at wrong time, dedup bugs) | 10 | **CRITICAL** |
| 5 | Define-Once and polarity errors (hardcoded duplicates, dead constants) | 11 | **CRITICAL** |
| 6 | **Layer coupling violations (intelligence work in Inspector)** | 19 | **CRITICAL** |
| **Total** | | **61 findings** | |

The four CRITICAL bug classes all reinforce each other: layer coupling created the conditions where field-drop bugs and visual-vs-scoring violations could ship. Cache lies hid them from sight. Legacy code drift kept old patterns alive.

---

## CRITICAL FINDINGS — block before Prospector/Designer can be built

These are fixes that need to land soon. Each one either causes wrong scores today or blocks safe future work.

### CRIT-1 — `_normalize_badges_for_display()` drops `strength` and `signal_category` on merge

**File:** `backend/app_new.py:622-627` (Bug Class 1)

**The code:**
```python
merged_by_name[name] = {
    "name": name,
    "color": b.get("color", ""),
    "qualifier": b.get("qualifier", ""),
    "evidence": list(b.get("evidence") or []),
}
```

**Why critical:** This is the EXACT same bug class as `scorer_new.py:512` (fixed in `e5c95c7`) and `app_new.py:713` (fixed in `120e3c9`), but in a third location I missed. When two same-named badges get merged at display time, the merge constructs a new dict with only `name`, `color`, `qualifier`, `evidence` — and **silently drops `strength` and `signal_category`**. For Pillar 2/3 dimensions (rubric model), this means the merged badge has no strength field, the math layer falls back to color points, and the score is wrong.

The bug is currently masked because (a) Frank's "universal variable-badge rule" tells Claude not to emit duplicate-named badges in the first place, so the merge path rarely fires; (b) when it does fire, the result is written AFTER the math runs. But on the NEXT page load, `_prepare_analysis_for_render` reads the merged dict, finds no `strength` field, and falls back to color points.

**Fix (one line):**
```python
merged_by_name[name] = {
    "name": name,
    "color": b.get("color", ""),
    "qualifier": b.get("qualifier", ""),
    "evidence": list(b.get("evidence") or []),
    "strength": b.get("strength", ""),           # ADD THIS
    "signal_category": b.get("signal_category", ""),  # AND THIS
}
```

**Severity:** CRITICAL — same shape as the bug class we just spent a session fixing.

---

### CRIT-2 — `_prepare_analysis_for_render()` lives in Inspector but is intelligence-layer work

**File:** `backend/app_new.py:639` (Bug Class 6 — Layer coupling)

**What it does:** Reads a saved analysis dict, recomputes every dimension score via `scoring_math.compute_all()`, recomputes ACV via `scoring_math.compute_acv_potential()`, reassigns verdict via `core_new.assign_verdict()`, normalizes badges for scoring (Phase 1) AND for display (Phase 2), and sorts products by Fit Score.

**Why critical:** The function name says "render" but the body is the **entire scoring recompute pipeline**. This is the cache-revalidation contract. Prospector batch scoring needs to call this same function on every cached company it loads. Designer (when it pulls product context from Inspector analyses) needs the same recompute. Today both would either have to import `app_new._prepare_analysis_for_render` (coupling Prospector to the Inspector Flask app) or duplicate the logic (drift risk).

This is the **single largest layer-discipline violation in the codebase**. Until it's moved, Prospector cannot be built without coupling.

**Fix:** rename and move to `backend/intelligence_new.py` as `recompute_analysis(analysis_dict)`. Keep a thin wrapper in `app_new.py` that calls it (so the inline route handler still has a one-liner). Update the docstring to make clear that this is the cache-revalidation contract that all tools call before rendering.

**Severity:** CRITICAL — blocks Prospector/Designer buildout.

---

### CRIT-3 — `_normalize_badges_for_scoring()` and `_normalize_badges_for_display()` live in Inspector

**File:** `backend/app_new.py:499` and `backend/app_new.py:559` (Bug Class 6)

**Why critical:** Same coupling issue as CRIT-2. Both functions are pure intelligence work — they normalize badge data for the scoring math (Phase 1) and for display (Phase 2). Neither should live in the Inspector Flask app file. When Prospector batch scoring runs, it needs the same normalization to happen, in the same order, with the same rules. Today there's no way for Prospector to call them without importing from `app_new.py`.

The 120e3c9 fix in `_normalize_badges_for_scoring` is correct, but it's in the wrong file. If Prospector ships before this moves, Prospector will silently apply different (or no) normalization.

**Fix:** move both to `backend/scorer_new.py` or a new `backend/badge_normalization.py` shared utility. Keep the Phase 1 / Phase 2 separation explicit in the new home.

**Severity:** CRITICAL — same blocker as CRIT-2.

---

### CRIT-4 — `prospector_routes.py` imports from legacy `intelligence.py`

**File:** `backend/routes/prospector_routes.py:22` (Bug Class 3 + Bug Class 6)

**The code:**
```python
from intelligence import qualify as intel_qualify
from storage import (...)
```

**Why critical:** Prospector routes import from the **legacy** `intelligence.py` and `storage.py`, NOT from `intelligence_new.py` and `storage_new.py`. This means:
- Prospector will not benefit from any fix that lands in `intelligence_new.py` (including the e5c95c7 and 120e3c9 fixes from this session)
- The scoring logic Prospector applies is structurally different from what Inspector applies
- The `routes/` directory is currently orphaned (`app_new.py` doesn't mount it), so Prospector technically isn't running today — but the moment someone tries to wire it up, it will use stale logic

This is an active landmine. CLAUDE.md's "Legacy Boundary" rule says "never silently reuse old files." This is a silent reuse waiting to be activated.

**Fix:** Decide whether `routes/prospector_routes.py` will be the production Prospector path or whether Prospector will get inline routes in `app_new.py` like Inspector. Either way, every import must come from the `_new` files. Same fix needed for `routes/designer_routes.py`.

**Severity:** CRITICAL.

---

### CRIT-5 — `scorer.py` is completely orphaned dead code

**File:** `backend/scorer.py` (490 lines) (Bug Class 3)

**Why critical:** `scorer.py` is never imported anywhere in active code. Not by `app_new.py`, not by `intelligence_new.py`, not by any active route. The legacy `intelligence.py` still imports it, but `intelligence.py` itself is only imported by the orphaned `routes/` files. **490 lines of scoring code with zero callers.**

This violates CLAUDE.md's Legacy Boundary rule cleanly. There's no ambiguity — it's dead.

**Fix:** delete `backend/scorer.py` outright. Verify no imports break. Do the same audit for the rest of the legacy file pairs (`intelligence.py`, `models.py`, `researcher.py`, `storage.py`, `core.py`, `config.py`) and delete any that have zero callers from active code. Each one is a future foot-gun.

**Severity:** CRITICAL — actively misleading future readers.

---

### CRIT-6 — `models_new.py:343` sets `analyzed_at` at dataclass instantiation, not at save

**File:** `backend/models_new.py:343` (Bug Class 4)

**The code:**
```python
analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

**Why critical:** `analyzed_at` is set when the `CompanyAnalysis` Python object is instantiated — which happens during `score_selected_products()` in `scorer_new.py`, BEFORE the analysis is actually persisted. By the time `save_analysis()` runs, the timestamp is already stale by 1-10+ seconds. Worse: in cache-and-append flows, the existing analysis keeps its OLD `analyzed_at` even when new products are appended. Users can see "analyzed on April 5" but the products in the file include some scored on April 7.

This is the same shape of bug as the cache version stamp lying — the timestamp doesn't reflect when the data was actually finalized.

**Fix:** Remove the `default_factory`. Set `data["analyzed_at"] = _now_iso()` in `save_analysis()` right before write — that timestamp reflects the actual moment of persistence. For cache-and-append, also update `analyzed_at` in `intelligence_new.score()` after appending new products, so the timestamp tracks the most recent change.

**Severity:** CRITICAL — undermines GP3 (Explainably Trustworthy) at the timestamp level.

---

### CRIT-7 — `inspector_refresh_cache` wipes products + saves with old `analyzed_at`

**File:** `backend/app_new.py:822-825` (Bug Class 4)

**The code:**
```python
# Wipe the current analysis's products so they re-score fresh (force_refresh)
analysis["products"] = []
from storage_new import save_analysis as _save
_save(analysis)
```

**Why critical:** The refresh handler blanks the products list and saves the (now empty) analysis BEFORE re-scoring runs. The blank analysis is persisted with the OLD `analyzed_at` stamp. If the user navigates away and back during the refresh, they see a blank dossier with an old date — looks like data corruption.

Pairs with CRIT-6: both bugs hide because `analyzed_at` is set in the wrong place.

**Fix:** Either don't pre-save the wiped state at all (let `score()` handle the full load-mutate-save cycle), or set `analysis["analyzed_at"] = None` and a `_refreshing = True` flag so the page can show "refreshing in progress" instead of "analyzed on April 5".

**Severity:** CRITICAL — visible UX bug that looks like corruption.

---

### CRIT-8 — `models_new.FitScore` hardcodes pillar/dimension weights (Define-Once violation)

**File:** `backend/models_new.py:134-160` (Bug Class 5)

**Why critical:** The `FitScore` dataclass default factory hardcodes:
- Pillar weights: 40, 30, 30
- Pillar 1 dimension weights: 35, 25, 15, 25
- Pillar 2 dimension weights: 40, 25, 15, 20
- Pillar 3 dimension weights: 25, 20, 30, 25

These are duplicated from `scoring_config.py PILLARS`. If anyone changes a weight in `scoring_config.py`, the model defaults silently keep the old values. New `FitScore` objects get instantiated with stale weights. The math layer reads from config and computes correctly, but the model object the templates render from has the wrong weights.

This is the most egregious Define-Once violation in the codebase.

**Fix:** Build the `FitScore` default dimensions dynamically from `scoring_config.PILLARS` at runtime. There should be **zero** literal weight values in `models_new.py`.

**Severity:** CRITICAL — breaks Define-Once at the data model layer.

---

### CRIT-9 — `backend/constants.py` is dead legacy code with stale duplicate constants

**File:** `backend/constants.py` (Bug Class 5)

**Why critical:** The file defines `WEIGHT_PRODUCT_LABABILITY = 40`, `WEIGHT_INSTRUCTIONAL_VALUE = 30`, `WEIGHT_ORGANIZATIONAL_READINESS = 20`, plus verdict thresholds (`VERDICT_PURSUE = 45`, `TIER_LIKELY = 45`) — and these don't match the current `SCORE_THRESHOLDS` in `scoring_config.py`. The values in `constants.py` are STALE and INCONSISTENT with the live config.

It's a trap: if a future developer reads `constants.py` thinking it's authoritative, they'll get the wrong numbers. Or worse, edit it expecting the system to change.

**Fix:** Delete `backend/constants.py` entirely after verifying no active code imports from it.

**Severity:** CRITICAL — actively misleading.

---

### CRIT-10 — Version stamp applied AFTER mutation, not as part of an atomic write

**File:** `backend/intelligence_new.py:314` + `backend/storage_new.py:144` (Bug Class 4)

**Why critical:** This was the root cause of the Trellix file having 11 products / 7 unique / 4 duplicates with the current version stamp. The fix in commit `e5c95c7` wipes legacy products before append, which closes the immediate symptom — but the underlying structural issue remains: the version stamp is set in `save_analysis()` AFTER `intelligence_new.score()` mutates the analysis dict. There's no atomic "score these products + stamp the result" boundary. Any future code path that mutates the analysis dict and saves it (without going through `score()`) will silently re-stamp it with the current version, even if the data isn't really current.

**Fix:** Move version stamping out of `save_analysis()` and into `intelligence_new.score()` and `intelligence_new.discover()` — the only two functions that should ever set the stamp. Make `save_analysis()` REJECT writes that don't have a version stamp set by the caller. This forces the stamp to be intentional.

**Severity:** CRITICAL — same shape as the bug we just fixed; the underlying gap is still there.

---

## HIGH-SEVERITY FINDINGS

### HIGH-1 — Discovery enrichment (tier, badge, color) computed in Inspector route

**File:** `backend/app_new.py:310 inspector_product_selection()` lines 318-331 (Bug Class 6)

The route computes `_tier`, `_tier_label`, `_company_badge`, `_org_color` on every product after loading the discovery. These are deterministic mappings (discovery_score → tier, organization_type + products → badge, organization_type → color group). Prospector and Designer would need the same enrichments. Today they'd have to either re-implement them or call into Inspector's route handler.

**Fix:** Move enrichment to `intelligence_new.discover()` — the discovery dict returned by `discover()` should already have these fields populated. Inspector, Prospector, and Designer all get the same enriched discovery without doing the work themselves.

---

### HIGH-2 — `inspector_full_analysis` backfills company context from discovery at render time

**File:** `backend/app_new.py:928-938` (Bug Class 6)

The route loads the analysis, then loads the discovery, then conditionally copies `company_description`, `competitive_products`, `_company_badge`, `_org_color` into the analysis dict. This implies the analysis isn't a complete record on its own — it depends on the discovery still existing.

**Fix:** Move the backfill into `intelligence_new.score()` so the analysis is captured complete at creation time. Once the analysis is saved, it should be self-contained. Don't make the render path responsible for assembling fields that the score path should have set.

---

### HIGH-3 — `_macros.html dominant_color()` re-implements badge merging logic in template

**File:** `tools/inspector/templates/_macros.html:21` (Bug Class 6)

The macro computes the "worst" badge color for a dimension (red > amber > green > gray) at template render time. This is the same logic as `_normalize_badges_for_display()` in Python. Two implementations of the same rule in two languages — guaranteed to drift.

**Fix:** Compute `dominant_color` in Python during render preparation. Pass it as a field on the dimension dict. Template becomes `{{ dim.dominant_color }}`.

---

### HIGH-4 — `full_analysis.html` `INFO_MODAL_CONTENT` hardcodes pillar percentages and ceiling caps

**File:** `tools/inspector/templates/full_analysis.html:27-100` (Bug Class 5)

The JS object contains hardcoded strings like `'PILLAR · GATEKEEPER · 40% OF FIT SCORE'` and `'caps at 18, multi-tenant only caps at 15, bare metal required caps at 5'`. If the pillar weight changes from 40% to anything else, the modal will lie about it. Same for the ceiling caps.

**Fix:** Move modal content to `scoring_config.py` as a structured `ModalContent` dataclass. Serialize to JS in the template via a Jinja filter. When config changes, modal updates automatically.

---

### HIGH-5 — Briefcase generation reload race + does NOT update `analyzed_at`

**File:** `backend/intelligence_new.py:474-478` (Bug Class 4)

`generate_briefcase_for_analysis()` reloads the analysis to get a fresh copy, modifies `current["products"][idx]["briefcase"]`, and saves. But the reload is from a stale starting point — and the save doesn't update `analyzed_at` (which is correct, briefcase generation shouldn't bump the analysis-level timestamp). Race condition: if two users hit the page during briefcase generation, one might see a partially-updated analysis.

**Fix:** Use per-product briefcase timestamps instead of relying on the analysis-level timestamp. Add `briefcase_generated_at` per product so the loading state can poll based on product, not analysis.

---

### HIGH-6 — `inspector_routes.py` mutates loaded `discovery` dict in place at render time

**File:** `backend/routes/inspector_routes.py:144, 146, 165, 192, 208` (Bug Class 2 + Bug Class 3)

The legacy `caseboard` route adds `priority`, `cached`, `competitive_landscape`, `_company_badge` to the loaded discovery dict and overwrites `discovery["products"]` with the family-filtered list. These are display-only mutations that contaminate the loaded copy. If any other code path re-saves the discovery after rendering, the synthetic fields persist to disk.

This file is currently orphaned (CRIT-4 / CRIT-5 territory), so the bug is dormant. But if anyone resurrects the route, the mutations will start affecting saved data.

**Fix:** Either delete the file (per CRIT-4 / CRIT-5 cleanup) or refactor to compute display projections instead of mutating the loaded copy.

---

### HIGH-7 — Cache-and-append doesn't update `analyzed_at` when appending new products

**File:** `backend/intelligence_new.py:305-314` (Bug Class 4)

When new products are appended to an existing analysis, `total_products_discovered` gets updated but `analyzed_at` is not touched. Pairs with CRIT-6 — both reflect that the codebase doesn't have a clear "this analysis was just modified" hook.

**Fix:** Set `existing_dict["analyzed_at"] = _now_iso()` after the extend/sort, before save. This is the GP5 "data sharpens" timestamp.

---

### HIGH-8 — `is_cached_logic_current()` exact-string match is brittle

**File:** `backend/scoring_config.py:2102-2103` (Bug Class 4)

The cache freshness check is `cached_version == SCORING_LOGIC_VERSION` — exact equality. If the version format ever uses semver or any structured form, this won't handle it. There's also no logging when the check fails (just returns False), so there's no breadcrumb when an analysis is rejected as stale.

**Fix:** Add a log line at the call site noting which file was rejected and what version it had vs. expected. Optionally support a "minimum compatible version" field in scoring_config so non-breaking changes don't invalidate the entire cache.

---

### HIGH-9 — Implicit assumption: exactly 3 pillars, 4 dimensions per pillar

**File:** `backend/scoring_config.py PILLARS` (Bug Class 5)

The code assumes exactly 3 pillars and exactly 4 dimensions per pillar throughout `app_new.py`, the templates, the math layer, and `models_new.py`. None of these places assert the assumption. If anyone adds a 4th pillar or restructures dimensions, the system breaks in subtle ways.

**Fix:** Add assertions in `scoring_config.py` validation:
```python
assert len(PILLARS) == 3, f"Expected 3 pillars, got {len(PILLARS)}"
for p in PILLARS:
    dim_total = sum(d.weight for d in p.dimensions)
    assert dim_total == 100, f"{p.name} dimension weights sum to {dim_total}, not 100"
```

---

### HIGH-10 — `app_new.py` deployment-model color mapping hardcoded

**File:** `backend/app_new.py:132` (Bug Class 5)

```python
return {"installable": "badge-deploy-green", "hybrid": "badge-deploy-gray",
        "cloud": "badge-deploy-green", "saas-only": "badge-deploy-amber"}.get(model, "")
```

Should be in `scoring_config.py` so that if a new deployment model is added, the color mapping updates with it.

---

### HIGH-11 — `app_new.py` discovery-tier CSS class mapping hardcoded

**File:** `backend/app_new.py:98` (Bug Class 5)

```python
{"seems_promising": "t-sp", "likely": "t-l", "uncertain": "t-u", "unlikely": "t-ul"}
```

Same issue as HIGH-10 — should be in config, paired with `DISCOVERY_TIER_LABELS`.

---

## MEDIUM-SEVERITY FINDINGS

### MED-1 — `_normalize_badges_for_display` overwrites qualifier with potentially empty value

**File:** `backend/app_new.py:633-634` (Bug Class 1)

When merging by color priority, the code overwrites `qualifier` even if the new badge's qualifier is empty. Loses the existing badge's qualifier context.

**Fix:** Only overwrite if non-empty.

---

### MED-2 — `models.py` and `models_new.py` define different class hierarchies

**File:** `backend/models.py` vs `backend/models_new.py` (Bug Class 3)

Legacy `models.py` is missing `Badge`, `PillarScore`, `FitScore`, `Verdict`, `BriefcaseSection`, `SellerBriefcase`, `ACVPotential` — the new classes that came with the rebuild. `routes/inspector_routes.py:24` conditionally imports `compute_product_score` from legacy `models.py`. If both code paths are ever live, they'll produce structurally different `Product` objects.

**Fix:** Delete `models.py` once `routes/` is decommissioned.

---

### MED-3 — `storage_new.py` is missing functions Prospector needs

**File:** `backend/storage_new.py` vs `backend/storage.py` (Bug Class 3)

Missing from storage_new: `save_prospector_run`, `load_prospector_run`, `append_poor_fit_feedback`, `load_poor_fit_companies`, `list_designer_programs`, `save_designer_program`, `delete_designer_program`, `load_all_discoveries`, `clear_competitor_candidates`. `prospector_routes.py` calls these. When Prospector is wired into the new code path, it will fail.

**Fix:** Migrate the needed functions into `storage_new.py`. Audit which are still needed first — some may be obsolete.

---

### MED-4 — `core.py` contains legacy vocabulary in badge mappings

**File:** `backend/core.py:195-269` (Bug Class 3)

Contains hardcoded subsection names like `"difficult_to_master"`, `"mastery_matters"`, `"workflow_complexity"` — all legacy vocabulary that should not appear anywhere in active code. The file is orphaned (only imported by legacy routes), but the names are a trap.

**Fix:** Delete `core.py` once routes/ is decommissioned.

---

### MED-5 — Briefcase generation doesn't sharpen contacts (GP5 violation)

**File:** `backend/intelligence_new.py:410-486` (Bug Class 4)

If the briefcase AI discovers a better contact during briefcase generation, there's no mechanism to fold it back into the product's contact list. GP5 says "every interaction makes the data sharper" — this interaction doesn't.

**Fix:** After briefcase generation, merge any new contacts into the product's contact list with a `confirmed_by_briefcase` flag. Optional but aligned with GP5.

---

### MED-6 — `save_analysis` dedup uses product `name` only

**File:** `backend/storage_new.py:154-162` (Bug Class 4)

The dedup pass added in commit `e5c95c7` uses `name.strip()` as the key. But two products can legitimately share a name (Azure DevOps cloud vs Azure DevOps Server, Microsoft Training v1 vs v2). The dedup wipes one of them.

**Fix:** Dedup by `(name, category)` or `(name, deployment_model)`.

---

### MED-7 — Stale prompts: `prompts/discovery.txt`, `prompts/product_scoring.txt`

**File:** `backend/prompts/` (Bug Class 3)

`discovery.txt` and `product_scoring.txt` are referenced only by legacy code. If `scorer.py` and the legacy intelligence files get deleted (CRIT-5), these prompt files become orphaned too.

**Fix:** Delete after dependent legacy files are removed.

---

### MED-8 — Routes orphaning: `routes/inspector_routes.py` is never mounted

**File:** `backend/routes/inspector_routes.py` (Bug Class 3)

Inspector routes are defined inline in `app_new.py`, not via blueprint. The blueprint file at `routes/inspector_routes.py` is orphaned but still exists. Future developers might assume it's the canonical source.

**Fix:** Delete after verifying no imports.

---

### MED-9 — `core_new.py` fallback defaults are magic numbers

**File:** `backend/core_new.py:143-150` (Bug Class 5)

`cfg.SCORE_THRESHOLDS.get("green", 65)` and `.get("light_amber", 45)` use magic-number defaults. Defensive coding is fine, but these should be either constants or assertions that the keys MUST exist.

**Fix:** Add `DEFAULT_SCORE_THRESHOLDS` constants to `scoring_config.py`, or assert key presence on load.

---

### MED-10 — Threshold-to-tier mapping documented only in comments

**File:** `backend/scoring_config.py:1364-1370` (Bug Class 5)

`SCORE_THRESHOLDS` is correctly centralized but the mapping from threshold values to discovery tier labels lives in **comments** in `core_new.py:165-168`. If thresholds change, the comments lie.

**Fix:** Move the mapping into a structured dict in `scoring_config.py`.

---

### MED-11 — `designer_routes.py` imports from legacy intelligence and storage

**File:** `backend/routes/designer_routes.py:18` (Bug Class 3 + Bug Class 6)

Same pattern as CRIT-4 (Prospector). Designer routes import from legacy `intelligence.py` and `storage.py`, not the `_new` versions. Designer is mostly stub code today, but when it gets implemented it will inherit the legacy imports.

**Fix:** Same as CRIT-4 — rewrite imports or merge routes into `app_new.py`.

---

### MED-12 — `inspector_routes.py` filters discovery products in place at render time

**File:** `backend/routes/inspector_routes.py:208` (Bug Class 2)

`discovery["products"] = [filtered list]` mutates the loaded discovery dict for display purposes. Same shape as HIGH-6 — display work in the Phase 1 / pre-math path. Currently dormant because the file is orphaned.

**Fix:** Delete file (CRIT-5 territory) or refactor to display projection.

---

## LOW-SEVERITY FINDINGS

### LOW-1 — `models.py:135` legacy comment uses "self-hosted" instead of "installable"

**Fix:** Update comment or delete file.

---

### LOW-2 — `scoring_math.py` makes implicit assumptions about config shape

**Fix:** Add validation function in `scoring_config.py` that runs on import.

---

### LOW-3 — `backend/app_new.py:145-146` money formatting magic numbers

`if value >= 1_000_000` — flagged as `magic-allowed` in comment. Universal standard, acceptable as-is.

---

### LOW-4 — Variable names in `scorer_new.py` use generic `result`, `data`, `m`

Mostly acceptable in context. Could be sharpened.

---

### LOW-5 — `inspector_routes.py:144,146,165,192` adds synthetic fields to discovery dict

Same shape as HIGH-6 / MED-12. Currently dormant. Delete file.

---

## ARCHITECTURE DECISIONS NEEDED

These are not bugs but choice points the platform needs to resolve before more code lands.

| # | Decision | Recommendation |
|---|---|---|
| AD-1 | Should `_prepare_analysis_for_render()` become a public `intelligence_new.recompute_analysis()` callable by all tools? | **YES.** This is the cache-revalidation contract. Move it. |
| AD-2 | Should badge normalization (Phase 1 + Phase 2) live in `scoring_math.py`, `scorer_new.py`, or a new `badge_normalization.py`? | New file `backend/badge_normalization.py`. The two phases are clearly named. Both `scorer_new.py` and `intelligence_new.recompute_analysis` import from it. |
| AD-3 | Should `routes/prospector_routes.py` be rewritten or merged into `app_new.py`? | **Merge into `app_new.py`** under `/prospector` route prefix. Single Flask app, single source of truth for routes. Delete `routes/` entirely. |
| AD-4 | Should `routes/designer_routes.py` be merged into `app_new.py`? | **YES**, same reason as AD-3. |
| AD-5 | Should modal content (`INFO_MODAL_CONTENT`) move to `scoring_config.py`? | **YES.** When config changes, explanations update. Prospector and Designer can also surface explanations. |
| AD-6 | Should `analyzed_at` be set in `save_analysis()` or in `intelligence_new.score()`? | In `save_analysis()` for the persisted timestamp + in `intelligence_new.score()` for the "this analysis was just modified" hook on cache-and-append. |
| AD-7 | What's the dedup key for products in an analysis? | `(name, category)` tuple. Allows same-name products with different deployment models / categories. |
| AD-8 | Should there be a `recompute_minimum_version` field in `scoring_config.py` to support semver-style cache invalidation? | Optional. Today's exact-string match works for one-bump-at-a-time changes. Defer until needed. |

---

## RECOMMENDED FIX ORDER

This is my proposed ship order. Each phase is bounded so the platform stays in a buildable state between phases.

### Phase A — close the active scoring bugs (1 commit)

1. CRIT-1 (`_normalize_badges_for_display` field-drop) — 2-line fix
2. MED-1 (qualifier overwrite with empty) — 2-line fix
3. CRIT-6 (`analyzed_at` at instantiation) + HIGH-7 (cache-and-append doesn't update analyzed_at) + CRIT-7 (refresh wipe with old stamp) — coordinated fix to centralize timestamp setting
4. CRIT-10 (atomic version stamp) — refuse writes without explicit stamp

### Phase B — kill the dead code (1 commit)

5. CRIT-5 (delete `scorer.py`)
6. MED-2 / MED-4 / MED-7 / MED-8 / MED-12 / LOW-5 / HIGH-6 (delete `routes/`, `core.py`, `models.py`, legacy prompts after verifying zero callers)
7. CRIT-9 (delete `constants.py`)

### Phase C — move intelligence to the Intelligence layer (multi-commit refactor)

8. AD-2 (create `badge_normalization.py`)
9. CRIT-3 (move `_normalize_badges_for_scoring` and `_normalize_badges_for_display`)
10. CRIT-2 (rename + move `_prepare_analysis_for_render` → `intelligence_new.recompute_analysis`)
11. HIGH-1 (move discovery enrichment into `intelligence_new.discover()`)
12. HIGH-2 (move analysis backfill into `intelligence_new.score()`)
13. HIGH-3 (move `dominant_color` from template macro to Python)
14. HIGH-4 (move `INFO_MODAL_CONTENT` to scoring_config)
15. CRIT-8 (build `FitScore` dimensions from `scoring_config.PILLARS`)
16. HIGH-9 (add validation assertions to `scoring_config.py`)
17. HIGH-10 / HIGH-11 (move hardcoded deployment color + tier class maps to config)

### Phase D — fix Prospector / Designer imports

18. CRIT-4 (rewrite `prospector_routes.py` imports OR merge into `app_new.py` per AD-3)
19. MED-11 (same for `designer_routes.py` per AD-4)
20. MED-3 (port needed Prospector storage functions into `storage_new.py`)

### Phase E — small polish

21. HIGH-5 (per-product briefcase timestamps)
22. HIGH-8 (better cache version mismatch logging)
23. MED-5 (briefcase contact sharpening — GP5 enhancement)
24. MED-6 (dedup by (name, category))
25. MED-9 / MED-10 (threshold defaults / mapping centralization)

---

## What changes about how we work

1. **Layer Discipline is now in the session-opening docs** (commit 3140622) — `CLAUDE.md`, `Platform-Foundation.md`, `collaboration-with-frank.md`. Future Claude sessions will read these in order and apply the principle to any code work.
2. **Bug-class vocabulary** — these six classes (field-drop, visual-vs-scoring, legacy code, cache lies, define-once / polarity, layer coupling) should become a checklist that any code review walks through. Each is severe enough that finding even one in a PR should pause the merge.
3. **Test strategy** — Phase 4 (next section of this doc) proposes the creative end-to-end tests that would have caught these.

---

## Phase 4 — creative test strategy

The 88 existing tests would not have caught any of the CRITICAL findings above. Tests today are structural assertions on `scoring_config.py` shape. The bugs hide in the integration paths between config, parser, normalizer, math, render, and storage.

The test strategy below targets each bug-class with end-to-end fixtures + invariant assertions.

### Test Class 1 — Round-trip fixture tests (catches field-drop bugs)

For each saved JSON fixture in `backend/tests/fixtures/`, run the full render path and assert:
- `badge.name` is unchanged from the saved value (no normalization rewrite)
- `badge.color` is unchanged
- For Pillar 2/3 badges: `badge.strength` is non-empty after render
- For Pillar 2/3 badges: `badge.signal_category` is non-empty after render
- For Pillar 1 badges: `badge.strength` and `badge.signal_category` ARE empty (rubric model isolation)

Fixtures should include:
- A clean Trellix-shape product (canonical badges, populated rubric)
- A Devolutions-shape product (canonical badges + bold prefixes in evidence)
- A product with duplicate-named badges (the merge path)
- A product with hard-negative red badges (color-fallback path)
- A product with no badges in some dimensions (empty-list path)

### Test Class 2 — Score isomorphism (catches CRIT-2 / CRIT-3 layer-coupling regressions)

For each fixture:
1. Compute scores at "score time" by feeding badges directly into `scoring_math.compute_all`
2. Save to JSON
3. Load and run `_prepare_analysis_for_render` (or its future intelligence-layer replacement)
4. Assert dimension scores from step 1 == dimension scores from step 3
5. Assert pillar scores match
6. Assert Fit Score matches
7. Assert verdict matches

Any divergence is a render-vs-score drift bug.

### Test Class 3 — Vocabulary closure (catches Devolutions-shape bugs)

For every saved analysis in `data_new/company_intel/`:
- For each Pillar 1 badge, assert `badge.name` is in `cfg.SCORING_SIGNALS` or in `cfg.PENALTIES`
- For each Pillar 2/3 badge, assert `badge.signal_category` is in the dimension's `signal_categories` list
- For each badge, assert `badge.color` is in `{"green", "amber", "red", "gray"}`
- Assert no badge.name appears in the locked-vocabulary "Not this" list

This single test would have caught the Devolutions bug instantly.

### Test Class 4 — Bold prefix doesn't leak

For every saved analysis:
- For every evidence claim, assert `**...|...:**` substring does NOT appear at the start
- This enforces that `_normalize_badges_for_scoring` ran successfully

### Test Class 5 — Cache stamp truth (catches CRIT-6 / CRIT-7 / CRIT-10)

For every saved analysis with version stamp `V`:
- Assert at least one product has `analyzed_at >= V's release date` (sanity check)
- For cache-and-append: the analysis-level `analyzed_at` must be `>=` every product's individual scoring time
- A version-stamped file must have non-zero products

### Test Class 6 — Pillar isolation

For every saved product:
- Pillar 1 badges have `strength == ""` and `signal_category == ""`
- Pillar 2/3 badges have `strength in {strong, moderate, weak}` and `signal_category` non-empty

### Test Class 7 — Polarity invariants

For every dimension result from `scoring_math.compute_all`:
- The score is `>= 0`
- The score is `<= dim.weight`
- Friction badges always reduce raw score
- Ceiling flags always cap (max), never floor (min)
- Technical fit multiplier always `<= 1.0` (never amplifies)
- Red badges always result in negative or capped contribution

### Test Class 8 — Adversarial fixtures

Hand-crafted fixtures specifically designed to trigger known bug-classes:
- Two badges with the same name in the same dimension (the merge path)
- A badge with a malformed evidence claim (no bold prefix)
- A product missing the `fit_score` field
- A product with an empty `dimensions` list
- An analysis with a stale `_scoring_logic_version`
- An analysis with no `_scoring_logic_version` at all
- A discovery with 0 products
- A discovery with 100 products

### Test Class 9 — Layer discipline (catches future regressions)

A test that asserts: no function in `backend/app_new.py` calls `scoring_math.compute_all`, `scoring_math.compute_acv_potential`, or `core_new.assign_verdict` directly. These calls must go through `intelligence_new.recompute_analysis` (the public contract) so Prospector and Designer can use the same path.

This is enforceable via AST inspection. It's the test that locks in the layer-discipline principle so future commits can't drift.

### Test Class 10 — Define-Once enforcement

For every value in `scoring_config.py PILLARS`:
- Search the rest of the codebase for the literal value
- If the literal appears in an active file outside config, fail the test

This is grep-based and noisy but catches CRIT-8 / CRIT-9 / HIGH-4 / HIGH-10 / HIGH-11 cleanly.

---

## Final note

Six parallel subagents covering 10 bug classes returned **61 findings**. The platform is buildable today and the critical scoring bugs are fixed (commits e5c95c7, 120e3c9, 3140622). But there's substantial structural work to do before Prospector and Designer can be built on top of a clean foundation.

The good news: most of the critical findings are concentrated in a small number of files (`app_new.py`, `models_new.py`, `intelligence_new.py`, `storage_new.py`, `scoring_config.py`) and the fixes are bounded. Phase A through Phase E above is roughly 3-4 focused sessions of work.

The other good news: the CLAUDE.md / Platform-Foundation / collaboration-with-frank Layer Discipline updates (commit 3140622) close the door on this bug class growing further. Future Claude sessions will read those docs first and apply the principle to any code work.

**Recommended next step:** start Phase A. The four CRIT-1 / CRIT-6 / CRIT-7 / CRIT-10 fixes are small and would close every active scoring bug we know about. Then Frank decides whether to keep going through Phase B–E in this session or break across multiple sessions.
