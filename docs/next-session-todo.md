# Next Session — Todo List

**Last updated:** 2026-04-06 (end of session)
**Read this first when you sit down tomorrow.**

---

## Read me first — what shipped tonight, what's open

Tonight was a long, productive session. A LOT changed. Skim **§ "Shipped tonight (so this list isn't lying)"** at the bottom before doing anything — it's the reference for what's already done so you don't accidentally re-do completed work.

The single most important thing for tomorrow: **§ 1 — Verify SOTI re-score**. The universal variable-badge rule landed late tonight and changes how the AI emits scoring signals. The math layer didn't change at all, but the AI's output should now credit the +30-ish signal values that were missing all session. Run this BEFORE anything else so you know the new prompt actually does what we expect.

---

## §1 — FIRST THING: Verify the universal variable-badge rule actually fires (~15 min)

Tonight's biggest architectural change. The scoring prompt now tells the AI:

> "When you have more than one badge to emit for the same canonical name, give every badge a unique name. First occurrence keeps the canonical name. Subsequent occurrences pick a matching scoring signal name (e.g., `Hyper-V: Standard`) — preferred — or a qualifier-derived label as fallback."

The math layer is unchanged. Whether this works depends entirely on AI compliance with the new prompt. **Test it before doing anything else.**

**Steps:**

1. Restart Flask cleanly.
2. Run a fresh discovery + Deep Dive on **SOTI ONE Platform** (force_refresh = true so you get a brand new AI run, not cached data).
3. Open the Full Analysis page. Check **MobiControl Server** (or whichever SOTI product runs in Hyper-V):
   - **Provisioning dimension score** should be in the **30-ish range** (was 6 all night before this fix). The score gain comes from the AI emitting `Hyper-V: Standard` (+30 signal) as a SECOND badge alongside `Runs in Hyper-V` (+6 color fallback).
   - **Hover the badges** in Provisioning. You should see TWO badges: `Runs in Hyper-V` (the canonical chip) AND `Hyper-V: Standard` (or whatever scoring signal the AI picked).
   - **Fit Score** should rise correspondingly. PL is the gatekeeper, so a 24-point lift in Provisioning ripples up.
4. **Cross-check three other companies** to confirm no regressions:
   - **Cohesity** — should keep its Hyper-V signal
   - **Tanium** — same
   - **Diligent** — should still be 100% Unlikely (SaaS-only, no Hyper-V signal applies)
   - None of these should DROP in score. Only installable products with viable scoring signals should GAIN.

**If it works:** great, log validation in the decision log and move to §2.

**If the AI doesn't comply** (still emits only the canonical badge name, ignores the signal vocabulary):
- The fix is in the prompt. Look at `backend/prompt_generator._format_badge_naming_principles()` and `_format_canonical_badge_names()` — both updated tonight. The signal vocabulary is now grouped per-dimension in the canonical names section.
- May need to make the instruction more emphatic, add a worked example in the prompt for SOTI/Hyper-V specifically, or move the rule from the principles section into the per-dimension guidance.
- **Do NOT touch the math layer.** It's correct. The math credits any name that matches `signal_lookup` and falls back to color points otherwise. The fix is always in the prompt.

**Why this matters:** If this fix works, every cached installable product instantly gains 15-30 points in Provisioning the next time it's rescored. Big lift across the whole portfolio.

---

## §2 — High-impact, ready to build

### Reusable doc-icon modal — show per-product reports
The `?` icons are wired to the info modal for per-pillar WHY/WHAT/HOW (shipped tonight). The doc icons next to each product are still decorative — they need to open the same modal but populated with a per-product report.

- **Modal infra:** ready. `openInfoModal(key)` in `full_analysis.html` accepts `{eyebrow, title, sections}` and renders. Just needs a content payload per product.
- **Open question:** what IS the per-product report content? Options:
  1. A formatted summary of the product's three pillars + verdict + ACV widget data
  2. The Word doc export content rendered in HTML for preview
  3. A new "executive briefing" view we haven't built yet
- **Design first, then build.** This is a fresh decision worth a short conversation before coding.

### Refresh button bug — navigates to SSE endpoint instead of HTML page
- **Where:** `tools/inspector/templates/full_analysis.html` line ~479.
- **What it does today:** clicking Refresh fires `POST /inspector/analysis/<id>/refresh`, gets back a `job_id`, then runs `window.location.href = '/inspector/score/progress/' + job_id`. That URL is the SSE endpoint — navigating to it renders the raw SSE event stream as text in the browser.
- **The fix:** the Refresh button should redirect to the existing scoring waiting page (`scoring_new.html`) with the job_id, not to the raw SSE endpoint. Look at how the main flow does it in `inspector_score()` for the right pattern.
- **Effort:** ~10 minutes.

### Move ACV widget content (`INFO_MODAL_CONTENT`) from JS to scoring_config
- **Today:** the per-pillar WHY/WHAT/HOW + ACV by Use Case explanation live as a JS object literal at the top of `full_analysis.html` (`INFO_MODAL_CONTENT`).
- **Should live in:** `scoring_config.py` (preferred — Define-Once) or a new `docs/explainability-content.md` file consumed via a Jinja filter.
- **Why:** so non-engineers can edit the explainability text without touching the template.
- **Effort:** ~30 minutes.

---

## §3 — Render deployment prep (ready when you are)

Goal: get the current build into a state where Frank can share it with a couple of people via the existing Render service.

**Effort:** ~30–60 minutes the first time, then auto-deploy on push.

**Pre-flight audit task — do this first:** run a quick read-only audit of (a) how secrets are loaded today, (b) every place the cache writes to disk, and (c) any other filesystem writes. Report back so we know exactly what changes need to land.

**Checklist:**

1. **Entry point** — add `gunicorn` to `requirements.txt`. Render start command becomes `gunicorn backend.app_new:app` (or correct module path). Verify the Flask app object is importable as `app`.
2. **Persistent file storage** — current cache writes to local disk. Render's filesystem is **ephemeral** and wipes on every deploy/restart. Decision needed:
   - **Render Disk** (~$1/mo, 5-min setup) — recommended for "share with a couple people"
   - **Postgres on Render free tier** — better long-term, more setup
   - **Accept ephemeral cache** — fine for a pure demo, analyses regenerate on demand
3. **Background threads** — briefcase generation runs in a background thread. Survives normal operation but is lost if the worker restarts mid-generation. Acceptable for demo. Document the limitation.
4. **Secrets audit** — confirm `ANTHROPIC_API_KEY` (and any other keys) are read from `os.environ` only. No hardcoded keys, no `.env` files committed. Quick grep before pushing.
5. **Auth gate** — the previous Render site's access posture is unknown. For sharing with a couple people, options:
   - Basic password gate (Flask middleware)
   - Render's built-in auth
   - IP allowlist
   Decide before going live.

---

## §4 — Standard Search Modal (designed, not built)

A single, reusable progress modal used by **every** long-running operation in the platform: Discovery, Deep Dive, Prospector batch scoring, Designer research, future workflows. Today each tool reinvents its own progress UI; this consolidates to one component, one source of truth, one visual language.

The full design is in this doc below at **§ "Standard Search Modal — design plan"**. Read it before starting. The build is ~half a day of focused work.

**Build sequence (when you get to it):**
1. Build the publisher (`backend/progress.py`) and a fake operation that emits events on a timer. Verify the contract works.
2. Build the modal component against the fake operation. Get visuals right with no real backend dependency.
3. Wire Discovery first — simplest operation, proves the integration pattern.
4. Wire Deep Dive — the operation that needs honest progress most.
5. Wire Prospector batch when batch scoring lands.
6. Retire all the per-tool progress UIs in a single cleanup pass.

---

## §5 — Search rework (Deep Dive performance + structure)

**Observation from 2026-04-06 Diligent test:** Deep Dive zips through products 1, 2, 3, 4 in under a minute, then **sits on 4/4 for a long time** before the page is ready. The progress bar is misleading — the per-product progress events fire as queries are dispatched, but the real bottleneck is at the tail: page fetches + scoring API calls + briefcase generation.

This pairs naturally with §4 (the standard search modal). When you build the modal, this is the operation that benefits most from honest stage-aware progress.

**Best current thinking — staged plan:**

| Stage | What it does today | Problem | Proposed rework |
|---|---|---|---|
| **1. Discovery** | Single Claude call identifies products from web research. | Already fast and good. | Keep as-is. |
| **2. Product research** | For each selected product, dispatches ~16 web search queries in parallel via `_run_searches_parallel`, then fetches top pages per product via `_fetch_pages_parallel`. | Query fan-out is wide but uneven — some queries return junk, some pages are slow. The "products 1-4 done" UI signal fires when queries dispatch, not when they resolve. | (a) Reduce per-product query count by collapsing redundant queries; (b) Add query-level timeout caps (current calls can hang on slow upstream); (c) Surface real progress: dispatched / resolved / fetched, not just product counter. |
| **3. Page fetch** | Fetches top result URL per query family per product, sequentially per product. | Slowest upstream pages block everything behind them. | (a) Per-fetch timeout (5-8s hard cap); (b) Fail fast and move on — missing one page is fine; (c) Parallelize across all products at once, not per-product. |
| **4. Scoring** | Per-product Claude call (Sonnet) with assembled evidence context. Runs in `ThreadPoolExecutor` across products. | Often the actual tail-hang. One slow scoring call blocks the page. | (a) Stream results to the page as each product finishes scoring (don't wait for all); (b) Show "Scoring 3/4 complete" instead of static "4/4"; (c) Consider Haiku for first-pass scoring, Sonnet only on demand. |
| **5. Briefcase** | Per-product, three Claude calls (Opus KTQ, Haiku Conv, Haiku Intel), all in background thread after page renders. | This is correct architecture today — already non-blocking. | Keep, but make the briefcase progress indicator more visible so users know it's still running. |

**Concrete next-session tasks (when you start):**
1. **Instrument the deep dive** — add timing logs at each stage boundary so we know empirically where the 4/4 hang lives. Don't tune blind.
2. **Replace the products counter** with stage-aware progress: `Searching → Fetching → Scoring → Ready`.
3. **Add per-fetch timeout** in `_fetch_pages_parallel` — 5-8 seconds, fail-and-continue.
4. **Stream scored products** to the Full Analysis page as they complete instead of waiting for the slowest one.
5. **Decide:** is per-product Sonnet scoring necessary, or does Haiku get us 95% there for a fraction of the time? Test on 2-3 known companies.

This is a sketch, not a commitment. Tune in priority order after we instrument and see real numbers.

---

## §6 — Smaller carry-overs

- **Migrate Designer + Prospector tools off the legacy `_nav.html` / `_theme.html` shared templates** onto `_nav_new.html` / `_theme_new.html`. Once they're migrated, the old `_nav.html` and `_theme.html` can be deleted (currently they're still referenced by `tools/designer/templates/designer_home.html`, `tools/prospector/templates/prospector.html`, `tools/prospector/templates/prospector_results.html`). The old theme has hardcoded hex colors that should flow through the variable system after migration.
- **Update Foundation docs** — add new scoring math (PL floor, technical fit multiplier, ceiling flags), the deterministic ACV math model, the locked rate variables, the universal variable-badge rule, and per-pillar WHY/WHAT/HOW content. Most of this lives in the decision log — sync it forward.
- **Comprehensive scoring framework alignment review** — walk every scored field against `Badging-and-Scoring-Reference.md` and confirm no drift between docs / config / math / template / cached data.
- **Audit the other ceiling-flag-implied synthetic badges** — tonight we added `No Learner Isolation` injection for `saas_only` / `multi_tenant_only`. Same pattern should apply to `bare_metal_required` (synthetic "Bare Metal Required" badge) and `no_api_automation` (synthetic "No API Automation" badge). Check `cfg.SYNTHETIC_BADGES` for the place to add them.

---

## Standard Search Modal — design plan (reference for §4)

A single, reusable progress modal used by **every** long-running operation.

### Why one modal

- **Consistency** — users learn it once
- **Define-Once** — one place to fix bugs, tune timings, change copy
- **Honest progress** — current bars lie because each tool implements progress differently. A standard modal forces a standard progress contract.
- **Real estate** — modal overlays the page being worked on, so users keep their context. No full-page route changes.

### Visual structure

```
┌────────────────────────────────────────────────────────────┐
│  ANALYZING DILIGENT                                    ×   │   ← title + close (close = cancel)
│  Deep Dive · 4 products                                    │   ← operation type + scope
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ●━━━━━━━●━━━━━━━●━━━━━━━○━━━━━━━○                       │   ← stage stepper (5 stages)
│   Discover  Search  Fetch  Score   Ready                   │
│                                                            │
│   Currently: Scoring product 3 of 4                        │   ← live status line
│   Diligent Boards · Diligent One · HighBond · Galvanize    │   ← per-item live state (✓ ✓ ⏵ ○)
│                                                            │
│   Elapsed: 1m 24s · Est. remaining: ~30s                  │   ← time signals
│                                                            │
│   [────────────────────────────────] 78%                  │   ← optional fine-grained bar
│                                                            │
│   ▸ Activity log (collapsed)                              │   ← optional verbose log
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### State contract — what every operation must publish

Every operation that uses the modal must publish events matching this shape (over SSE today, can become WebSocket later):

```json
{
  "operation_id": "uuid",
  "operation_type": "deep_dive | discovery | prospector_batch | designer_research",
  "title": "Analyzing Diligent",
  "subtitle": "Deep Dive · 4 products",
  "stages": ["Discover", "Search", "Fetch", "Score", "Ready"],
  "current_stage_index": 3,
  "current_status": "Scoring product 3 of 4",
  "items": [
    {"name": "Diligent Boards", "state": "done"},
    {"name": "Diligent One", "state": "done"},
    {"name": "HighBond", "state": "active"},
    {"name": "Galvanize", "state": "pending"}
  ],
  "elapsed_seconds": 84,
  "estimated_remaining_seconds": 30,
  "progress_pct": 78,
  "log_lines": ["..."],
  "terminal_state": null
}
```

`terminal_state` is `null` until done; then one of `success | partial | error | cancelled`.

### Theme tokens the modal exposes

| Token | Used for |
|---|---|
| `--sk-bg-card` | Modal background |
| `--sk-border-card` | Modal border |
| `--sk-text-strong` | Title |
| `--sk-text-body` | Status line |
| `--sk-text-muted` | Subtitle, time signals |
| `--sk-text-dim` | Activity log |
| `--sk-classify-purple` | Stage stepper accent (matches pillar accent) |
| `--sk-score-high` | Completed stage / item-done indicator |
| `--sk-score-mid` | Active stage / item-active indicator |
| `--sk-text-faint` | Pending stage / item-pending indicator |
| `--sk-score-low-soft` | Error state |

### Component props

| Prop | Type | Required | Notes |
|---|---|---|---|
| `operation_id` | string | yes | Used to subscribe to SSE stream |
| `operation_type` | enum | yes | Drives copy and default stage list |
| `title` | string | yes | Top-line label |
| `subtitle` | string | no | Secondary label |
| `stages` | string[] | yes | Stage names for stepper |
| `cancellable` | bool | no, default true | Show × close button |
| `on_complete` | callback | yes | What to do when terminal_state = success |
| `on_error` | callback | no | Defaults to alert |
| `auto_dismiss_ms` | int | no, default 0 | If > 0, auto-close on success after delay |

### Where it lives in code

```
tools/shared/templates/
  _search_modal.html          ← markup + scoped styles (uses theme vars only)
  _search_modal.js            ← SSE subscription, DOM updates, lifecycle
backend/
  progress.py                 ← shared event publisher (operation_id → SSE channel)
```

Each operation (`research_products`, `discover_products`, etc.) gets a `ProgressPublisher` injected. It calls `publisher.stage("Search")`, `publisher.item("Diligent Boards", "done")`, `publisher.status("Scoring 3 of 4")`. The publisher fans out to the right SSE channel by operation_id.

### Behavior rules

1. **Modal overlays the current page** — does not navigate away
2. **Cancel kills the operation** — backend honors cancellation tokens, no orphaned work
3. **On success: dismiss + reload page (or call `on_complete`)**
4. **On error: stay open, show error in red, offer Retry**
5. **Stage stepper shows truth, not lies** — stages only advance when the stage actually completes server-side
6. **Time estimates use rolling history** — measure last N runs of each operation type, show median
7. **Activity log is opt-in** — collapsed by default, expand for power users / debugging
8. **Mobile/narrow** — stage stepper collapses to a single "Stage 3 of 5: Scoring" line

### Out of scope for first build

- Multi-operation queue (one operation at a time is fine)
- Operation history view (separate feature)
- WebSocket — SSE is sufficient

---

## Shipped tonight (so this list isn't lying)

This section is the historical record of what landed in the 2026-04-06 session. Don't redo any of these — read it for context if a current behavior surprises you.

### Major architectural shipments

- **Deterministic Python ACV math** — `scoring_math.compute_acv_potential()` runs at every page render. The AI estimates per-motion population, adoption %, and hours per learner; Python computes hours, dollars, rate lookup (by orchestration method), and tier label. AI no longer touches dollars at all. Locked rates: Cloud Labs $6, VM Low $8, VM Mid $14, VM High $45, Simulation = VM Low. Tier thresholds: HIGH ≥ $250K, MEDIUM ≥ $50K, LOW < $50K.
- **ACV by Use Case widget** — Built and live in the bottom-right column under Account Intelligence. Reads `acv_potential.motions[]`, displays per-motion audience / adoption / hours / hours-per-year, plus Annual Hours and Annual Potential totals, plus a methodology footer showing the chosen rate ($X/hr · tier name). Has its own `?` icon wired to a WHY/WHAT/HOW info modal entry.
- **Universal variable-badge rule** — Frank's architectural insight. When the AI emits more than one badge for the same canonical name, the second one MUST be renamed using a more specific variable from the dimension's vocabulary (preferred: a scoring signal name; fallback: a qualifier-derived label). Solves visual duplicate problem AND closes the badge-vocabulary-vs-scoring-signal disconnect that was capping Provisioning scores at +6 on installable products. Math layer needed zero changes — the prompt now teaches the AI to disambiguate at the source.
- **Visual changes never affect scoring** — architectural principle promoted to the decision log. Badge normalization is split into `_normalize_badges_for_scoring` (Phase 1, runs BEFORE math; does only legitimate transforms like splitter + synthetic injection) and `_normalize_badges_for_display` (Phase 2, runs AFTER math; does only display transforms like merging same-named badges and color promotion). The math sees the unmerged list with original colors; the user sees the merged list with worst-color promoted.
- **Bug 1 fix — badge/evidence cross-wiring splitter** — When the AI groups multiple distinct signals under one umbrella badge with multiple `**Label | Qualifier:**` evidence claims, the splitter unpacks them into separate badges. (Now works in concert with the universal variable-badge rule.)
- **Bug 2 fix — synthetic No Learner Isolation injection** — When `saas_only` or `multi_tenant_only` ceiling flags are set on a product, `_normalize_badges_for_scoring` injects a `No Learner Isolation` red Blocker badge into Lab Access. Metadata reads from `cfg.SYNTHETIC_BADGES` (Define-Once). This fires regardless of whether the AI emits the badge.
- **Reusable info modal** — `?` icons next to all three pillar names (Product Labability, Instructional Value, Customer Fit) and the ACV widget title open a modal showing per-pillar WHY / WHAT / HOW. Modal infra is generic — `openInfoModal(key)` accepts any `{eyebrow, title, sections}` payload. Doc icons next to products are still decorative; wiring them to per-product reports is the next-session task in §2.

### Visual + UX shipments

- **Bottom row aligned with briefcase row** — `bottom-row` is now `flex 7:3` matching `.briefcase`. `bottom-row-product` (flex 7) holds Products and Competitive as two equal-width children. `bottom-row-org` (flex 3) holds the ACV by Use Case widget. Every box aligns edge-for-edge with the box above it.
- **Hero ACV display fix** — big hero number is now the **company total** (sum of `acv_low`/`acv_high` across every scored product), with the selected product's individual contribution shown smaller below for context. Was previously showing the single selected product on top — felt flipped.
- **Verdict ACV tier label is now Python-derived** — was AI-guessed before, now `scoring_math._resolve_acv_tier()` reads dollar thresholds from `cfg.ACV_TIER_HIGH_THRESHOLD` / `ACV_TIER_MEDIUM_THRESHOLD`.
- **Compete box layout** — Product name (210px fixed, 32-char truncate) | Subcategory badge (left-aligned in its own column) | Run link (right-aligned to box edge, plain link, same color as Scored Products name links). Run links match `.pt-name-link` color treatment exactly.
- **Browser back button fix** — `discovering_new.html` and `scoring_new.html` waiting pages now use `window.location.replace()` instead of `window.location.href = ...`. Browser back from Full Analysis → Product Selection → Inspector home (skips the dead waiting pages).
- **Badge evidence modal** — right-edge clipping detection (Fix #4), inline_md filter for bullet formatting, confidence color (green confirmed / gray other), wider modal max-width (540px).
- **Score color buckets decision** — five logical thresholds (`SCORE_THRESHOLDS` in config) collapse to three visible color buckets (green / amber / red) with the verdict label text carrying the finer-grained nuance. Decided intentionally — see decision log.

### Scoring + math shipments

- **Best-color-wins dedupe** — when the math layer sees two badges with the same name but different colors, it now picks the version with the highest BADGE_COLOR_POINTS (preferred: green +6) instead of first-encountered. Fixes a regression where Frank's earlier merger color promotion silently dropped points.
- **PL floor enforcement** — `compute_fit_score()` enforces `fit_score = max(weighted_sum, pl_score)`. Strong IV/CF can pull Fit Score above PL but never below.
- **Technical Fit Multiplier softened** — PL 0-9 now 0.50 (was 0.15), PL 10-18 now 0.65 (was 0.40). Lets strong IV/CF lift weak-PL products modestly.
- **SaaS hard cap** — `saas_only` ceiling flag caps PL at 18, `multi_tenant_only` caps at 15.
- **Heartbeat logging** — scorer log heartbeat interval reduced from 15s to 60s to cut log noise.

### Cleanup + audit shipments (this very session)

- **Hardcoding violations removed** in tonight's added code:
  - `BADGE_COLOR_POINTS` is now read from config in `scoring_math` (was duplicated).
  - `BADGE_COLOR_DISPLAY_PRIORITY` added to config and read from `_normalize_badges_for_display` (was hardcoded local dict).
  - `SYNTHETIC_BADGES` config dict added for the No Learner Isolation injection — name, color, qualifier, claim template, and friendly flag labels all live in config.
  - `ISOLATION_BLOCKING_CEILING_FLAGS` frozenset added so the trigger condition is config-driven.
  - `LAB_ACCESS_DIMENSION_NAME` constant added for the dimension lookup.
  - `DEFAULT_RATE_TIER_NAME` constant added for the rate fallback (was duplicated string in two places).
  - `BADGE_UNKNOWN_COLOR_SCORE_FALLBACK` constant added for unknown-color graceful degradation.
- **One stray hex color** in `_theme_new.html` (`.badge-deploy-gray #94a3b8`) replaced with `var(--sk-context)`.

### Decisions logged to `docs/decision-log.md`

- Visual changes must NEVER affect scoring (architectural principle)
- Universal variable-badge rule (Frank's framing verbatim)
- ACV tier thresholds locked: $250K HIGH / $50K MEDIUM
- Verdict ACV labels stay (LOW/MEDIUM/HIGH ACV under verdict badge)
- Three visible color buckets, five logical thresholds — intentional, not a bug

---

## Open questions (none blocking, but worth a thought tomorrow)

1. **Should the doc icons next to products show a per-product report?** And what should that report contain? See §2.
2. **Are there other ceiling-flag-implied synthetic badges to add?** `bare_metal_required` and `no_api_automation` could follow the same pattern as `No Learner Isolation`. See §6.
3. **The Designer + Prospector tools still use `_nav.html` and `_theme.html`** (the legacy shared templates). Migration to `_nav_new.html` / `_theme_new.html` is queued in §6 but the timing is your call.
