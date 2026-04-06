# Next Session — Todo List

Best current thinking on what's queued. Reorder freely.

---

## HIGH PRIORITY — ACV by Use Case widget (rebuild from POC)

**Frank's framing (2026-04-06):** "The ACV Potential 'by use case' view that was in the POC. Rows and columns. Listed the major use cases on a row, then a column for total possible audience, etc. This was the very top thing shown in the Product Detail cards at the very bottom of the Dossier pages. CRITICAL ACV Widget."

**Where it lived in the POC:** `tools/inspector/templates/_legacy_dossier.html` lines ~611–655. Class names: `.consumption-block`, `.consumption-table`. Reads from `product.consumption_potential`.

**Data shape (still in every cached analysis):**
```
product.consumption_potential = {
  motions: [
    {
      label: "Partner Training Channel" | "Events" | "Certification PBT" | ...,
      population_low: int,
      population_high: int,
      adoption_pct: float,        // e.g. 0.15 for 15%
      hours_low: float,           // hours per learner
      hours_high: float,
    },
    ...
  ],
  vm_rate_estimate: float,         // $/hour
  annual_hours_low: float,
  annual_hours_high: float,
  methodology_note: string,
}
```

**Layout (rows × columns):**
| Motion | Population | Adoption | Hrs / Learner | Est. Hours / Yr |
|---|---|---|---|---|
| Partner Training Channel | 2,500–4,000 | 15% | 4–8h | 1,500–4,800 |
| Events (Conferences) | 8,000–12,000 | 8% | 2–4h | 1,280–3,840 |
| Certification PBT | 500–1,200 | 60% | 1–2h | 300–1,440 |
| ... | ... | ... | ... | ... |
| **Annual Potential** (total row, spans 4 cols) | | | | **$X,XXX – $Y,YYY** |

The dollar range in the total row = `(annual_hours_low × vm_rate_estimate) – (annual_hours_high × vm_rate_estimate)`. Methodology note rendered below the table in muted text.

**Where it goes on the new page:** Inside `bottom-row-org` — the empty placeholder reserved tonight. Right column under Account Intelligence. The placeholder div `<div class="acv-widget-placeholder"></div>` is the insertion point.

**Build steps:**
1. New partial: `tools/inspector/templates/_acv_use_case_widget.html` — themed via CSS variables, takes `selected_product` as input.
2. Replace the placeholder div in `full_analysis.html` with `{% include '_acv_use_case_widget.html' %}`.
3. Wire it into the in-place product swap endpoint so switching products in the dropdown updates the widget alongside hero/pillars/briefcase. New return field: `acv_widget_html`.
4. Verify the data shape is still being emitted by the scorer (it was in the POC; check the new prompt template). If missing, add it back to the scoring prompt.
5. Optional: tie in with the next-session task "Move ACV math out of AI call into deterministic Python" — once that lands, the widget reads from Python-computed motion data instead of AI-emitted data, with the same shape.

**Why this is critical (Frank's words):** This is how sellers and SEs see *where the deal lives* — which use case is the volume driver, which one to talk to the customer about first, what the realistic upper bound looks like. Without it, the ACV number on the hero is a single opaque range with no story behind it.

---

## HIGH PRIORITY — Badge vocabulary vs scoring signal disconnect (found 2026-04-06 SOTI test)

**Symptom:** SOTI ONE Platform (and likely every other product with installable VM/cloud paths) is scoring much lower in Provisioning than the AI itself thinks it should. SOTI Provisioning: saved score = **6**, but the AI's own summary text says *"Scored at Hyper-V: Standard with two penalties applied"*. Hyper-V: Standard is a scoring signal worth **+30**. The 24-point gap propagates up into PL pillar, then into the Fit Score and verdict.

**Root cause:** The AI is emitting **badge vocabulary names** (`"Runs in Hyper-V"`) in the `badges` array, not **scoring signal names** (`"Hyper-V: Standard"`). In `scoring_config.py` these are two separate concepts:

- `_provisioning_badges` (line 228): visual chip vocabulary — `"Runs in Hyper-V"`, `"Runs in Azure"`, `"Runs in Containers"`, `"Bare Metal Required"`, etc.
- `_provisioning_signals` (line 262): point-bearing scoring signals — `"Hyper-V: Full Lifecycle API"` (+35), `"Hyper-V: CLI Scripting"` (+34), `"Hyper-V: Standard"` (+30), `"Hyper-V: Limited"` (+26), `"Hyper-V: Complex Install"` (+20), etc.

The scoring math in `scoring_math.py:compute_dimension_score()` checks `signal_lookup` first, then `penalty_lookup`, then falls back to `BADGE_COLOR_POINTS` for badges that don't match either. Vocabulary names always fall through to the color fallback — green = +6, amber = 0, red = -3 — so the rich 20-35 point signals are NEVER credited even when the AI's prose accurately identifies them.

**Three fix options to choose between:**

1. **Prompt fix (lowest risk):** Update `scoring_template.md` to instruct the AI to emit BOTH the visual badge AND the matching scoring signal in the `badges` array. Two badges per signal — one for the chip, one for the points. Easy to implement, depends on AI compliance.

2. **Prompt unification (cleanest long-term):** Collapse `_provisioning_badges` and `_provisioning_signals` into a single concept. Each badge name IS the scoring signal name. The visual chip displays whatever the AI emits and the same name carries the point value. Bigger config rewrite but eliminates the failure mode entirely.

3. **Python inference (most deterministic):** Given a badge like `"Runs in Hyper-V"`, a color qualifier, and `product.orchestration_method`, Python picks the right scoring signal automatically. Add a `_signal_for_badge()` helper that maps `(badge_name, color, orchestration_method)` → signal name. Most rules to write but no AI dependency.

**Recommended:** Option 2 (unification) followed by a re-test. Eliminates two-vocabulary confusion at the source and matches the architecture decision Frank already made for ACV math (move logic into config, not AI).

**Effect once fixed:** Every cached analysis of installable products should immediately gain back ~15-25 points in Provisioning, propagating up through PL, the Technical Fit Multiplier, and the Fit Score. Verdict labels for installable products will tend to climb one or two tiers.

**Why NOT hot-fixed:** Touches the prompt template, the scoring config, and the math fallback logic. Needs careful design + a test pass against multiple cached companies (SOTI, Cohesity, Tanium, Diligent) to confirm no regressions before shipping. Don't ship at midnight.

---

## HIGH PRIORITY — Scoring data quality bugs (found 2026-04-06 Diligent test)

### Bug 1 — Badge/evidence cross-wiring
**Symptom:** Hovering "Anti-Automation Controls" badge shows evidence about *Tenant Isolation* ("No per-learner tenant isolation mechanism is documented... Shared tenant use creates data bleed risk between learners"). The evidence text is correct content for a different dimension entirely.

**Likely root cause:** Either (a) the AI is writing evidence claims into the wrong badge during scoring — a prompt-discipline issue where the model groups all SaaS-isolation findings under whatever badge name it picks first; or (b) the parser in `_parse_product` is associating evidence rows with badges by ordinal position instead of explicit badge_id, and a misaligned list cascades.

**Investigation steps:**
1. Pull the raw scorer JSON for a Diligent product from the cache and inspect the `badges[].evidence` arrays — are the wrong claims actually in the wrong arrays at the JSON level, or is the rendering layer scrambling them?
2. If at the JSON level → fix is in the prompt (`scoring_template.md`) — add explicit "evidence under a badge MUST be about that badge's specific signal, not another dimension" instruction with examples.
3. If at the rendering level → fix is in `_parse_product` or the macro.

### Bug 2 — No Learner Isolation badge should always appear when condition is true
**Symptom:** The "No Learner Isolation" badge is missing on some products where it should be present. Today, badges are AI-suggested per dimension; there's no guarantee the model writes the badge even when the underlying signal is unmistakable (multi-tenant SaaS, shared customer accounts, etc.).

**Fix approach (architecturally consistent with the scoring math fix):** Derive the No Learner Isolation badge **deterministically in Python** from the ceiling flags. If `multi_tenant_only` or `saas_only` ceiling flag is set, append the No Learner Isolation badge with whatever evidence the AI provided (or a default rationale if none). AI is responsible for *evidence*; Python is responsible for *badge presence*. Same pattern as scoring math — AI for synthesis, Python for guarantees.

**Likely also true for other "always show if condition" badges** — once we fix this for Learner Isolation, audit the other ceiling-flag-implied badges (No API Automation, Bare Metal Required, etc.) and apply the same pattern.

**Owner note:** These two bugs need their own focused work — DO NOT hot-patch. They touch the scorer/prompt data flow, which is the most consequential layer. Get the data right at the source, then the UI is automatically right.

---

## Carry-over from prior sessions

- **Reusable modal component** — `?` icons show docs sections (per-pillar WHY/WHAT/HOW), doc icons show per-product reports. One modal, two content sources.
- **ACV math out of the AI call** — move to deterministic Python like scoring math. AI provides evidence/signals, Python computes ACV bands.
- **Foundation docs update** — add new scoring math (PL floor, technical fit multiplier, ceiling flags) and per-pillar WHY/WHAT/HOW content.
- **Comprehensive scoring framework alignment review** — walk every scored field against `Badging-and-Scoring-Reference.md` and confirm no drift.
- **Full hex color cleanup pass** — ~30 hardcoded colors still in templates. Replace with CSS variables.
- **Shared search/progress component** — used across Inspector, Prospector, Designer.

---

## Render deployment prep

Goal: get the current build into a state where Frank can share it with a couple of people via the existing Render service.

Effort estimate: ~30–60 minutes the first time, then auto-deploy on push.

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

**Pre-flight audit task for Claude (next session):** before doing any of the above, run a quick read-only audit of (a) how secrets are loaded today, (b) every place the cache writes to disk, and (c) any other filesystem writes. Report back so we know exactly what changes need to land.

---

## Standard Search Modal — design plan

A single, reusable progress modal used by **every** long-running operation in the platform: Discovery, Deep Dive, Prospector batch scoring, Designer research, future workflows. Today each tool reinvents its own progress UI; this consolidates to one component, one source of truth, one visual language.

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

### Variables / tokens the modal exposes

Theme tokens (already in `_theme_new.html` after tonight's additions):

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

Component props:

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

### Build sequence (when we get to it)

1. **Build the publisher** (`backend/progress.py`) and a fake operation that emits events on a timer. Verify the contract works.
2. **Build the modal component** against the fake operation. Get visuals right with no real backend dependency.
3. **Wire Discovery first** — simplest operation, proves the integration pattern.
4. **Wire Deep Dive** — the operation tonight's testing showed needs honest progress most.
5. **Wire Prospector batch** when batch scoring lands.
6. **Retire all the per-tool progress UIs** in a single cleanup pass.

---

## Search rework — Deep Dive performance + structure

**Observation from 2026-04-06 testing (Diligent run):** Deep Dive zips through products 1, 2, 3, 4 in under a minute, then **sits on 4/4 for a long time** before the page is ready. The progress bar is misleading — the per-product progress events fire as queries are dispatched, but the real bottleneck is at the tail: page fetches + scoring API calls + briefcase generation. Need to rework what "progress" means and where the time actually goes.

**Best current thinking — staged plan (refine when we get there):**

| Stage | What it does today | Problem | Proposed rework |
|---|---|---|---|
| **1. Discovery** | Single Claude call identifies products from web research. | Already fast and good. | Keep as-is. |
| **2. Product research** | For each selected product, dispatches ~16 web search queries in parallel via `_run_searches_parallel`, then fetches top pages per product via `_fetch_pages_parallel`. | Query fan-out is wide but uneven — some queries return junk, some pages are slow. The "products 1-4 done" UI signal fires when queries dispatch, not when they resolve. | (a) Reduce per-product query count by collapsing redundant queries; (b) Add query-level timeout caps (current calls can hang on slow upstream); (c) Surface real progress: dispatched / resolved / fetched, not just product counter. |
| **3. Page fetch** | Fetches top result URL per query family per product, sequentially per product. | Slowest upstream pages block everything behind them. | (a) Per-fetch timeout (5-8s hard cap); (b) Fail fast and move on — missing one page is fine; (c) Parallelize across all products at once, not per-product. |
| **4. Scoring** | Per-product Claude call (Sonnet) with assembled evidence context. Runs in `ThreadPoolExecutor` across products. | Often the actual tail-hang. One slow scoring call blocks the page. | (a) Stream results to the page as each product finishes scoring (don't wait for all); (b) Show "Scoring 3/4 complete" instead of static "4/4"; (c) Consider Haiku for first-pass scoring, Sonnet only on demand. |
| **5. Briefcase** | Per-product, three Claude calls (Opus KTQ, Haiku Conv, Haiku Intel), all in background thread after page renders. | This is correct architecture today — already non-blocking. | Keep, but make the briefcase progress indicator more visible so users know it's still running. |

**Concrete next-session tasks:**
1. **Instrument the deep dive** — add timing logs at each stage boundary so we know empirically where the 4/4 hang lives (queries? fetches? scoring? briefcase?). Don't tune blind.
2. **Replace the products counter** with stage-aware progress: `Searching → Fetching → Scoring → Ready`.
3. **Add per-fetch timeout** in `_fetch_pages_parallel` — 5-8 seconds, fail-and-continue.
4. **Stream scored products** to the Full Analysis page as they complete instead of waiting for the slowest one.
5. **Decide:** is per-product Sonnet scoring necessary, or does Haiku get us 95% there for a fraction of the time? Test on 2-3 known companies.

This is a sketch, not a commitment. Tune in priority order after we instrument and see real numbers.

---

## Tonight's fast set — all complete

1. ~~**Badge modal Fix #4**~~ — modal repositions when clipping right edge. **Done.**
2. ~~**Re-test multiplier 0.50 against Workday**~~ — validated by Diligent test (100% Unlikely confirms ceilings + multiplier are correct). **Done.**
3. ~~**Competitive section markup**~~ — 4-column layout, 22-char truncation, right-aligned search button. **Done.**
4. ~~**Targeted hex color cleanup**~~ — `#24ED98` → `var(--sk-score-high)` (10 spots), plus `.product-option-name`, `.dim-name`. **Done.**
5. ~~**Full hex color cleanup pass**~~ — completed in same session. **Done.**
