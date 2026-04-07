# Next Session — Todo List

**Last updated:** 2026-04-06 (extended through afternoon — Pillar 1 architecture refactor + Pillar 2/3 rubric architecture both shipped)
**Read this first when you sit down for the next session.**

---

## Heads-up — major Pillar 1 + Pillar 2/3 refactors shipped 2026-04-06 afternoon

A long collaboration session with Frank produced two complete architectural sharpenings:

**Pillar 1 — Product Labability** (canonical model). Five commits landed: `4e56133`, `45a1678`, `b133b10`, `498ad04`, `68989a9`. Every Pillar 1 sharpening is in the code, the prompt, the math layer, and `Badging-and-Scoring-Reference.md`. **Read those commit messages before doing any Pillar 1 work** — they capture every decision (new canonicals, retired vocabulary, ceiling flag changes, color-aware math, meta-principle).

**Pillar 2 (Instructional Value) + Pillar 3 (Customer Fit) — rubric model** (variable badge names + strength grading + signal_category tags). One big commit: `f46dcc9`. The two pillars use a fundamentally different scoring architecture from Pillar 1, by design — see the new "Two Architectures Across Pillars" section in `Badging-and-Scoring-Reference.md` for the rationale. Pillar 3 dimensions also reordered to chronological reading order: Training Commitment → Build Capacity → Delivery Capacity → Organizational DNA.

The "verify SOTI re-score" task in §1 below is now PARTIALLY OBSOLETE — the universal variable-badge rule was retired in favor of flat-tier scoring. SOTI should still be re-run to verify the new vocabulary fires correctly with the live AI, but the expected mechanism is different from what §1 describes.

---

## §0b — Product Selection limit applies to NEW products only (raised 2026-04-06 evening)

The Product Selection page caps how many products can be selected per Deep Dive. The cap exists to control how many fresh Claude calls one Deep Dive triggers — **cached products are free to include**, since they don't trigger new scoring work.

**Today (wrong):** the cap is on total selected products. If a company has 6 cached products and the cap is 4, the user can't select all 6 cached even though doing so triggers zero new work.

**Should be:** the cap counts only NEW (uncached) products. Cached products always come along for free. So with cap=4:
- 6 cached + 0 new: ✅ allowed (zero new Claude calls)
- 6 cached + 4 new: ✅ allowed (4 new Claude calls)
- 6 cached + 5 new: ❌ blocked (5 new Claude calls > cap)
- 0 cached + 4 new: ✅ allowed
- 0 cached + 5 new: ❌ blocked

**UX:** the counter chip should reflect "X of N new products selected" rather than "X of N selected." Cached products should show their cached chip and be selectable without counting against the cap.

**SHIPPED 2026-04-06 evening:** see the relevant commit in the Shipped section. Status of cap-counting + UX update.

---

## §0a — Product Family Picker (raised 2026-04-06 evening)

**Spec source:** `docs/archive/inspector.md` line 50 — the canonical rule.

> Product Family Selection applies when discovery identifies a large portfolio (20+ products). Companies like Oracle, Microsoft, IBM, and SAP have hundreds of products — too many to display on a single caseboard. Instead of showing all products at once, Inspector scrapes the company's website navigation to extract their product families (the vendor's own portfolio organization), then presents a family picker modal. The user selects a family (e.g., "Oracle Database" or "Microsoft Azure"), and a focused discovery runs against just that family's products.

**Current state:** the picker exists in code but is wrong vs spec on two counts.

1. **Threshold is 30, should be 20.** `inspector_routes.py:195` has `FAMILY_THRESHOLD = 30`. Drop to 20 per Frank's 2026-04-06 directive (spec doc says 15 — outdated). Update both code and spec doc to 20.
2. **Picker renders ON Caseboard, should be a separate interstitial step BETWEEN discovery completion and Caseboard.** Today it's surfaced as a `product_families` block on the same page; the spec calls for a modal interstitial that runs a focused discovery against the chosen family's products before landing on Caseboard.
3. **Scraped families come from `_scraped_families` (vendor nav).** That part is already wired correctly via `researcher_new.scrape_product_families`. Don't break it.
4. **The "focused discovery" step doesn't exist yet.** Today picking a family just filters the existing discovery's products. The spec implies a *second* discovery pass scoped to the family. Decide whether to: (a) implement focused-discovery pass, or (b) keep filter-only behavior and update the spec to match. Frank has not weighed in on this — ask.

**Where to put the picker UX:** between Discovery completion and Product Selection. Either as its own route (`/inspector/family-picker/<discovery_id>`) or as a modal that opens on Product Selection load when families ≥ 15. Frank's instinct is "in the search flow" — most consistent reading is interstitial route, not modal-on-caseboard.

---

## §0 — Frank's Backlog (added 2026-04-06 afternoon, post Pillar 2/3 ship)

These 7 items came out of Frank's QA pass while reviewing the dossier UX. Concrete, ready to pick up. None are blocked on SE clarifications.

### 0.1 — M365 Provisioning in Product Labability

The M365 tenant provisioning capability (E3 / E5 / E7 — see `skillable_capabilities.json` `m365_tenants` block) is currently underrepresented in Provisioning scoring. M365-dependent products (Microsoft 365, Defender for Office 365, Purview, Copilot, etc.) should benefit from a clean canonical or scoring path that recognizes Skillable's automated M365 tenant provisioning via Azure Cloud Slice. **Today the AI doesn't know to credit M365-tenant-dependent products for this Skillable strength.** Investigate where to land it: a new Provisioning canonical badge (e.g., `M365 Tenant`) or a refinement of the existing `Runs in Azure` to recognize M365 as a first-class case.

### 0.2 — Product in-cache indicator on Product Selection page

When a product has already been scored (cached), the Product Selection page should visually indicate that with a small chip or icon. Today the seller has to click in to discover whether a product is already scored or needs a fresh Deep Dive. A small "cached" indicator with a timestamp tooltip would make the state visible at a glance and help the seller pick the right path (re-use cached vs force refresh).

### 0.3 — Company Description field consistency (Product Selection + Deep Dive)

The Company Description field renders differently on the Product Selection page vs the Full Analysis (Deep Dive) page — different font, different position, possibly different content. Should be consistent: same field, same source of truth, same rendering treatment, same prominence. Audit both pages and unify.

### 0.4 — Sales Briefcase: box size consistency / alignment

The three Sales Briefcase boxes (Key Technical Questions / Conversation Starters / Account Intelligence) don't render with consistent box sizes or alignment. They should match each other in width, height (or min-height), padding, and vertical alignment. Affects visual polish and seller credibility.

### 0.5 — Sales Briefcase: standard for bolding and phrasing

The three Sales Briefcase sections use inconsistent bolding patterns and phrasing styles. Need a documented standard for what gets bolded (entity names? action items? vendor terms?) and how each section's bullets are phrased (sentence length, tone, opening pattern). Land the standard in the prompt template for each of the three briefcase generators (Opus KTQ, Haiku Conv, Haiku Intel) so they produce consistent output.

### 0.6 — Bottom three boxes: full consistency pass

The three boxes in the bottom-row of the Full Analysis page (Scored Products / Competitive / ACV by Use Case) need a consistency pass: font, font size, vertical spacing, column spacing, padding, alignment. They should feel like one designed row, not three independent components. Audit all three and unify.

### 0.7 — ACV Table bottom — names below, audience size logic, lab rate per hour logic

The ACV by Use Case table needs three things landed together:

- **Motion names below the row** (instead of as the leftmost column), or as a clearer label treatment so the seller can scan the row easily
- **Logic for audience size** — better grounding for the AI's per-motion population estimates, anchored to vendor scale signals (links into the deferred §5.5 ACV review)
- **Logic for lab rate per hour** — the rate selection logic should be transparent and auditable, with a clear mapping from orchestration method to rate tier

The five motions are:
1. Customer training / enablement (direct)
2. Training partner programs
3. Certification programs
4. Employee enablement
5. Events & Conference

(Note: this list overlaps with the existing `CONSUMPTION_MOTIONS` in `scoring_config.py` but uses slightly different labels. Worth reconciling — Frank's labels here may be the better naming.)

---

## SE Clarification Queue — answers needed from a sales engineer

These four items are gates on completing Pillar 1. Frank to gather answers from a Skillable sales engineer; once received, the answers feed into the prompt template, the math layer cap values, and the friction badge inventory.

| # | Question | Why it matters |
|---|---|---|
| **SE-1** | **Bare Metal Required** — when evaluating a vendor product, what specific signals in their docs or marketing tell us "this requires bare metal hardware orchestration that we can't virtualize"? Examples of products that hit this — what gave it away? | Today the AI guesses at this. We need detection signals for the canonical `Bare Metal Required` red Blocker badge so it fires reliably and doesn't fire spuriously. |
| **SE-2** | **Container Disqualifiers** — we have four documented disqualifiers (dev-use-only image, Windows GUI required, multi-VM network, not container-native in production). Which is the most common practical reason to skip containers? When Windows is needed, is "Windows container" ever the right call, or do we always default to a Windows VM? | Pillar 1 work (commits above) added `Runs in Container` as a green/amber/don't-emit canonical, but the disqualifier list needs SE input to be sharp enough for the AI. |
| **SE-3** | **Simulation Scorable** — when a lab is delivered via Simulation, when CAN we score it (via AI Vision) and when CAN'T we? Should `Simulation Scorable` ever be a red blocker, or is it always green/amber depending on what's visible on screen? | The `Simulation Scorable` canonical is currently amber-only in `scoring_config.py`. Frank flagged this for SE input — the answer determines whether we add a red state and what triggers it. |
| **SE-4** | **SaaS Path Cap Values (graduated)** — for a SaaS product where the only path is Simulation (no provisioning API + Simulation viable, e.g., Epiq, Diligent), what's the right Product Labability cap? Current framework tiers: Hyper-V 30–35, Cloud Slice 28–33, Custom API 19–25, Simulation 7–14. Where should "SaaS, no API, Simulation only" cap out? And for the dead-end case (Workday-style: no API + no Simulation viable), where should the cap be — 5? 0? | This is the LAST blocker on `scoring_math.py` — when `Sandbox API` is red, the math layer needs to apply a PL cap. Tentative values are 20 (Simulation viable) and 5 (nothing viable), but Frank wanted to see them in graduated context against the other path tiers before locking. SE input on the right cap relative to other paths will lock these numbers. |

**Where the answers land in code once received:**

| Answer | Lands in |
|---|---|
| SE-1 (Bare Metal detection) | `prompts/scoring_template.md` Pillar 1 section + possibly new research queries in `researcher_new.py` |
| SE-2 (Container disqualifiers) | `prompts/scoring_template.md` Pillar 1 section under the `Runs in Container` canonical |
| SE-3 (Simulation Scorable color states) | `backend/scoring_config.py` `_scoring_badges` `Simulation Scorable` definition + `prompts/scoring_template.md` Pillar 1 Scoring section |
| SE-4 (Sandbox API red PL cap values) | `backend/scoring_math.py` cap logic — currently the cap is NOT applied (the math just uses color points -3 for red Sandbox API). A new mechanism reads the badge state and caps PL based on whether Simulation is viable. |

---

## Read me first — what shipped recently, what's open

The 2026-04-06 session was long and productive across THREE stretches: a late-night architectural push, a morning continuation focused on anti-hardcoding test infrastructure, and an afternoon Pillar 1 architecture refactor. A LOT changed. Skim **§ "Shipped recently (so this list isn't lying)"** at the bottom before doing anything — it's the historical record so you don't accidentally re-do completed work.

**This doc is the focused near-term action list.** For the complete inventory of every item (active, backlog, done, decisions needed) across every tool and area, see **`docs/roadmap.md`** — that's where ideas live until they're prioritized and pulled into this doc.

The single most important thing when you sit down: **the SE Clarification Queue above**. Pillar 1 is feature-complete in code but four answers are gates on the final cap value mechanism, the friction badge details, and a few canonical color states. After the SE clarifications come back, the next move is to re-run cached customers (Trellix, Cohesity, SOTI, Epiq, Diligent, Workday) with the live AI to verify direction-of-movement against the synthetic math verification already done in commits `b133b10`.

---

## §1 — FIRST THING: Verify the universal variable-badge rule actually fires (~15 min)

The biggest architectural change of the 2026-04-06 session. The scoring prompt now tells the AI:

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

## §5.5 — Exhaustive ACV calculation review (HIGH PRIORITY)

The deterministic ACV math from last night is **doing the math correctly** but the **inputs from the AI are coming out way too low** for global vendors with large user bases. We need a focused review of the AI's per-motion population and adoption estimates against ground truth.

**Confirmed undersized cases (Frank 2026-04-06):**

| Company | What we see | Why it feels wrong |
|---|---|---|
| **Cohesity** | $34K–$167K total ACV across 2 of 15 scored products. Cohesity Data Cloud alone: $25K–$129K | 15 globally-deployed enterprise data protection products. Cohesity has hundreds of thousands of admins/operators worldwide. Even at modest adoption rates the ACV should be in the hundreds of thousands to low millions, not $34K. |
| **(more to come — Frank flagging as he tests)** | | |

**Two distinct problems probably contributing:**

1. **AI is undersizing per-motion populations.** When the AI estimates `population_low/high` for each motion, it appears to be conservative to the point of inaccuracy for large vendors. A "Customer Onboarding & Enablement" motion for Cohesity should reflect tens of thousands of customers, not a few hundred.
2. **Hero number is "scored only" but reads as "whole company."** The hero shows `$34K–$167K` with subtext "Across 2 scored of 15 discovered products" — the headline number represents 13% of the portfolio but visually presents as the answer. Either:
   - **Extrapolate to full-company estimate** in the hero (`$34K–$167K from scored, ~$255K–$1.25M extrapolated to all 15`)
   - **Or reword the label** so it's clearly partial (`Partial ACV (2 of 15 products): $34K–$167K`)
   - **Or score all products by default** instead of only the user-selected subset

**Investigation steps:**

1. **Pull the Cohesity raw scorer JSON** from the cache and inspect each motion's `population_low/high` and `adoption_pct`. Are they realistic for a vendor of Cohesity's size?
2. **Compare to known benchmarks** in `backend/benchmarks_new.json` — Cohesity is listed there with relationship/scale signals. The AI should be using those signals to inform population sizing.
3. **Check the prompt's CONSUMPTION_MOTIONS guidance** — the adoption ceiling rules and population guidance. Are we instructing the AI to "be conservative" in a way that produces unrealistically small numbers?
4. **Add 3-5 known anchor companies** with hand-validated population/adoption estimates to the test fixtures, run scoring, compare AI output to anchors. Anything more than ~25% off is a flag.
5. **Decide on the hero display semantics** (extrapolate, reword, or score-all). This is a UX call.

**Why HIGH priority:** ACV is the dollar number sellers and execs see first. If it's wrong by 5–10x, it undermines trust in the whole platform. This needs to be right before any external user sees the tool.

**Pairs naturally with §1 (SOTI verification)** — both are scoring data quality validations. Could be the focus of one dedicated "scoring trust" session.

---

## §6 — Smaller carry-overs

These four are still relevant near-term but the full descriptions now live in `docs/roadmap.md` (the consolidated inventory). Keep this section short — pull items from the roadmap when actually starting them.

- **Migrate Designer + Prospector tools off legacy `_nav.html` / `_theme.html`** — see roadmap §D and §C. Deferred until the new Designer code push lands.
- **Update Foundation docs** with new scoring math, deterministic ACV model, locked rates, universal variable-badge rule, per-pillar WHY/WHAT/HOW — see roadmap §B.
- **Comprehensive scoring framework alignment review** — walk every scored field against `Badging-and-Scoring-Reference.md`. See roadmap §B.
- **Audit other ceiling-flag-implied synthetic badges** (`bare_metal_required`, `no_api_automation`) — same pattern as `No Learner Isolation`. See roadmap §B.

For the **complete inventory** of every item (active, backlog, done, decisions needed) → `docs/roadmap.md`.

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

## Shipped recently (so this list isn't lying)

Historical record of what landed in the 2026-04-06 session (split into a late-night architectural push and a morning continuation focused on test infrastructure). Don't redo any of these — read it for context if a current behavior surprises you.

### Shipped during the morning continuation (2026-04-06 AM)

- **CLAUDE.md startup sequence updated** — added `docs/next-session-todo.md` as **step 4** in the read-first list. Without this, next-session Claude would read the foundation docs and present a status that's missing the most recent architectural work (because the foundation docs lag the universal variable-badge rule, deterministic ACV math, etc.). The todo doc is now the explicit bridge until the foundation docs sync forward.
- **Anti-hardcoding test suite (Phases 1-4)** — `backend/tests/test_no_hardcoding.py` with 5 tests, all passing. Catches the exact class of bug that bit us during the late-night push. Documented in **Test Plan Category 10** with a deliberate "False-Positive Watch" section explaining the pre-release strict-mode philosophy.
  - **Phase 1A** — hex literal scan in active templates. Theme files allow hex inside `:root` variable definitions only. Inspector + new shared theme: clean.
  - **Phase 1B** — inline `style="color: #..."` attribute scan. Catches hex bypassing the theme system entirely.
  - **Phase 2A** — Python dict-with-color-keys scan. Walks AST of `app_new.py` + `scoring_math.py` for dict literals where ≥2 keys are color names — almost always a duplicate of `BADGE_COLOR_POINTS` or `BADGE_COLOR_DISPLAY_PRIORITY`. **Caught 1 real violation:** `badge_color_class_filter` in `app_new.py` had a hardcoded `{"green": "badge-green", ...}` dict. **Fixed:** derive from `f"badge-{color}"` against `cfg.BADGE_COLOR_POINTS`.
  - **Manual catch during Phase 2 triage:** `deployment_display_filter` had the same anti-pattern with deployment-model keys (`installable`/`hybrid`/`cloud`/`saas-only`) — Phase 2A missed it because the keys aren't color names. **Fixed:** read from `cfg.DEPLOYMENT_MODELS[model]["display"]`.
  - **Phase 2B** — cross-file scan for distinctive scoring_config string constants (currently `DEFAULT_RATE_TIER_NAME`). Catches inlined values that should reference cfg.
  - **Phase 3** — magic-number scan with `# magic-allowed: <reason>` annotation system. Allowed barewords: 0, 1, -1, 100, plus standard HTTP status codes (200/400/404/etc). Slice indices (`uuid[:8]`) handled via `ast.Slice`. Initial run on `app_new.py` surfaced 23 violations → triaged: 14 HTTP codes added to allowed barewords, 3 slice indices handled by detector improvement, 4 money formatting thresholds annotated, 1 Flask dev port annotated, 1 regex group index annotated. `scoring_math.py` had **zero** unannotated magic numbers — last night's cleanup pass was thorough.
  - **Phase 4** — pre-commit hook integration. `.git/hooks/pre-commit` now runs `validate-badge-names.py` AND the anti-hardcoding test suite on every commit. Tracked copies at `scripts/git-hooks/pre-commit` + `scripts/git-hooks/install.sh` so the hook content survives across clones. Hook overhead: ~0.5s per commit. To install on a fresh clone: `bash scripts/git-hooks/install.sh`. To bypass in an emergency: `git commit --no-verify` (don't use routinely).
- **Test Plan Category 10 added** — full philosophy section with the false-positive watch protocol. Documents the decision tree when a violation comes up (real → fix; non-applicable → annotate with reason; pattern too broad → narrow the rule and document; adding more friction than value → skip the specific test as last resort). GP Traceability matrix updated.
- **Cohesity ACV undersizing observation captured** — flagged that Cohesity Data Cloud + 1 other product = $34K-$167K total, which feels WAY too low for a vendor with 15 globally-deployed enterprise data protection products. Documented as **§5.5 HIGH PRIORITY** with two distinct potential causes (AI undersizing populations + hero shows partial-as-whole) and concrete investigation steps. Pairs naturally with §1 SOTI verification as a "scoring trust" session.
- **Designer + Prospector deferral confirmed** — both tools' templates explicitly excluded from the anti-hardcoding scan with documented reasons (Designer waiting for new code push, Prospector grouped for migration with Designer). Exclusions are visible in `backend/tests/test_no_hardcoding.py` `_EXCLUDED_PATHS` so future me knows when they can be removed.

### Shipped during the late-night push (2026-04-05/06)

#### Major architectural shipments

- **Deterministic Python ACV math** — `scoring_math.compute_acv_potential()` runs at every page render. The AI estimates per-motion population, adoption %, and hours per learner; Python computes hours, dollars, rate lookup (by orchestration method), and tier label. AI no longer touches dollars at all. Locked rates: Cloud Labs $6, VM Low $8, VM Mid $14, VM High $45, Simulation = VM Low. Tier thresholds: HIGH ≥ $250K, MEDIUM ≥ $50K, LOW < $50K.
- **ACV by Use Case widget** — Built and live in the bottom-right column under Account Intelligence. Reads `acv_potential.motions[]`, displays per-motion audience / adoption / hours / hours-per-year, plus Annual Hours and Annual Potential totals, plus a methodology footer showing the chosen rate ($X/hr · tier name). Has its own `?` icon wired to a WHY/WHAT/HOW info modal entry.
- **Universal variable-badge rule** — Frank's architectural insight. When the AI emits more than one badge for the same canonical name, the second one MUST be renamed using a more specific variable from the dimension's vocabulary (preferred: a scoring signal name; fallback: a qualifier-derived label). Solves visual duplicate problem AND closes the badge-vocabulary-vs-scoring-signal disconnect that was capping Provisioning scores at +6 on installable products. Math layer needed zero changes — the prompt now teaches the AI to disambiguate at the source.
- **Visual changes never affect scoring** — architectural principle promoted to the decision log. Badge normalization is split into `_normalize_badges_for_scoring` (Phase 1, runs BEFORE math; does only legitimate transforms like splitter + synthetic injection) and `_normalize_badges_for_display` (Phase 2, runs AFTER math; does only display transforms like merging same-named badges and color promotion). The math sees the unmerged list with original colors; the user sees the merged list with worst-color promoted.
- **Bug 1 fix — badge/evidence cross-wiring splitter** — When the AI groups multiple distinct signals under one umbrella badge with multiple `**Label | Qualifier:**` evidence claims, the splitter unpacks them into separate badges. (Now works in concert with the universal variable-badge rule.)
- **Bug 2 fix — synthetic No Learner Isolation injection** — When `saas_only` or `multi_tenant_only` ceiling flags are set on a product, `_normalize_badges_for_scoring` injects a `No Learner Isolation` red Blocker badge into Lab Access. Metadata reads from `cfg.SYNTHETIC_BADGES` (Define-Once). This fires regardless of whether the AI emits the badge.
- **Reusable info modal** — `?` icons next to all three pillar names (Product Labability, Instructional Value, Customer Fit) and the ACV widget title open a modal showing per-pillar WHY / WHAT / HOW. Modal infra is generic — `openInfoModal(key)` accepts any `{eyebrow, title, sections}` payload. Doc icons next to products are still decorative; wiring them to per-product reports is the next-session task in §2.

#### Visual + UX shipments

- **Bottom row aligned with briefcase row** — `bottom-row` is now `flex 7:3` matching `.briefcase`. `bottom-row-product` (flex 7) holds Products and Competitive as two equal-width children. `bottom-row-org` (flex 3) holds the ACV by Use Case widget. Every box aligns edge-for-edge with the box above it.
- **Hero ACV display fix** — big hero number is now the **company total** (sum of `acv_low`/`acv_high` across every scored product), with the selected product's individual contribution shown smaller below for context. Was previously showing the single selected product on top — felt flipped.
- **Verdict ACV tier label is now Python-derived** — was AI-guessed before, now `scoring_math._resolve_acv_tier()` reads dollar thresholds from `cfg.ACV_TIER_HIGH_THRESHOLD` / `ACV_TIER_MEDIUM_THRESHOLD`.
- **Compete box layout** — Product name (210px fixed, 32-char truncate) | Subcategory badge (left-aligned in its own column) | Run link (right-aligned to box edge, plain link, same color as Scored Products name links). Run links match `.pt-name-link` color treatment exactly.
- **Browser back button fix** — `discovering_new.html` and `scoring_new.html` waiting pages now use `window.location.replace()` instead of `window.location.href = ...`. Browser back from Full Analysis → Product Selection → Inspector home (skips the dead waiting pages).
- **Badge evidence modal** — right-edge clipping detection (Fix #4), inline_md filter for bullet formatting, confidence color (green confirmed / gray other), wider modal max-width (540px).
- **Score color buckets decision** — five logical thresholds (`SCORE_THRESHOLDS` in config) collapse to three visible color buckets (green / amber / red) with the verdict label text carrying the finer-grained nuance. Decided intentionally — see decision log.

#### Scoring + math shipments

- **Best-color-wins dedupe** — when the math layer sees two badges with the same name but different colors, it now picks the version with the highest BADGE_COLOR_POINTS (preferred: green +6) instead of first-encountered. Fixes a regression where Frank's earlier merger color promotion silently dropped points.
- **PL floor enforcement** — `compute_fit_score()` enforces `fit_score = max(weighted_sum, pl_score)`. Strong IV/CF can pull Fit Score above PL but never below.
- **Technical Fit Multiplier softened** — PL 0-9 now 0.50 (was 0.15), PL 10-18 now 0.65 (was 0.40). Lets strong IV/CF lift weak-PL products modestly.
- **SaaS hard cap** — `saas_only` ceiling flag caps PL at 18, `multi_tenant_only` caps at 15.
- **Heartbeat logging** — scorer log heartbeat interval reduced from 15s to 60s to cut log noise.

#### Cleanup + audit shipments (late-night push)

- **Hardcoding violations removed** in tonight's added code:
  - `BADGE_COLOR_POINTS` is now read from config in `scoring_math` (was duplicated).
  - `BADGE_COLOR_DISPLAY_PRIORITY` added to config and read from `_normalize_badges_for_display` (was hardcoded local dict).
  - `SYNTHETIC_BADGES` config dict added for the No Learner Isolation injection — name, color, qualifier, claim template, and friendly flag labels all live in config.
  - `ISOLATION_BLOCKING_CEILING_FLAGS` frozenset added so the trigger condition is config-driven.
  - `LAB_ACCESS_DIMENSION_NAME` constant added for the dimension lookup.
  - `DEFAULT_RATE_TIER_NAME` constant added for the rate fallback (was duplicated string in two places).
  - `BADGE_UNKNOWN_COLOR_SCORE_FALLBACK` constant added for unknown-color graceful degradation.
- **One stray hex color** in `_theme_new.html` (`.badge-deploy-gray #94a3b8`) replaced with `var(--sk-context)`.

#### Decisions logged to `docs/decision-log.md`

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
