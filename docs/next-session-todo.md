# Next Session — Todo List

**Last updated:** 2026-04-07 (late evening — after Pillar 1 risk caps, CF unification, Diligent Five Fixes, briefcase routing, Phase F, and Phase 4 creative test strategy all shipped)
**Read this first when you sit down for the next session.**

---

## Format note

This doc uses a two-column table format per Frank's 2026-04-07 directive: narrow column 1 = item name, wider column 2 = description. Sections are kept thin so the long arc lives in `docs/roadmap.md` and the historical record lives in `docs/decision-log.md`.

---

## §0 — START HERE (the tonight-shipped feature set needs validation)

A long late-night session shipped substantial scoring + UX refinements. The next session's first job is to verify the architecture is producing what the prompts intend, then knock down the §1 backlog Frank flagged during QA.

| Item | Description |
|---|---|
| **Reload Flask + re-score Diligent** | The Pillar 3 judgment badge rule + the Account Intelligence Elevate prompt + the briefcase routing rule + Phase F all need a fresh AI run to be visible. Diligent is the canonical test case — it had `Build vs Buy` / `DIY Labs` generic names, missing Elevate-as-action, and inconsistent CF across products. After re-score, every Customer Fit badge should read like a finding (`Light Content Dev`, `Few Tech SMEs`, `Long RFP Process`), the Elevate 2026 conference should be the FIRST Account Intelligence bullet with a "find the head of Elevate 2026" action, and every product should show identical Pillar 3 dimension scores. If any of these fail, the prompt rules need another pass. |
| **Verify the stale-cache modal fires on Product Selection** | Tonight's commit `7c69eb1` added the decision modal to the `inspector_product_selection` → `inspector_score` path. Verify by: clear the cached analysis, score Diligent, bump `SCORING_LOGIC_VERSION` artificially, reload Product Selection, click Deep Dive — the modal should fire with "Refresh first" / "Use cached" buttons. Once the user has chosen on a given page load, a second click of Deep Dive goes straight through. |
| **Cross-check Trellix + Cohesity for regressions** | Trellix EPS Pillar 1 should still be 92/100 (Hyper-V Grand Slam path). Cohesity should still show its Hyper-V signal credits. Neither should drop in score from any of tonight's changes — Pillar 1 math is unchanged, only Pillar 2/3 prompts and the math layer's CF unification shifted. |

---

## §1 — Frank's QA-pass backlog (carry-over from 2026-04-06 + 2026-04-07)

These came out of Frank's review of dossiers across the 2026-04-06 and 2026-04-07 sessions. Concrete, ready to pick up. None blocked on SE clarifications.

| Item | Description |
|---|---|
| **M365 Provisioning canonical** | The M365 tenant provisioning capability (E3 / E5 / E7 — see `skillable_capabilities.json` `m365_tenants` block) is currently underrepresented in Provisioning scoring. M365-dependent products (Microsoft 365, Defender for Office 365, Purview, Copilot, etc.) should benefit from a clean canonical or scoring path that recognizes Skillable's automated M365 tenant provisioning via Azure Cloud Slice. **Today the AI doesn't know to credit M365-tenant-dependent products for this Skillable strength.** Investigate where to land it: a new Provisioning canonical badge (e.g., `M365 Tenant`) or a refinement of the existing `Runs in Azure` to recognize M365 as a first-class case. Frank §0.1. |
| **Company Description consistency** | The Company Description field renders differently on the Product Selection page vs the Full Analysis (Deep Dive) page — different font, different position, possibly different content. Should be consistent: same field, same source of truth, same rendering treatment, same prominence. Audit both pages and unify. Frank §0.3. |
| **Briefcase box size + alignment** | The three Sales Briefcase boxes (Key Technical Questions / Conversation Starters / Account Intelligence) don't render with consistent box sizes or alignment. They should match each other in width, height (or min-height), padding, and vertical alignment. Affects visual polish and seller credibility. Frank §0.4. |
| **Briefcase bolding + phrasing standard** | The three Sales Briefcase sections use inconsistent bolding patterns and phrasing styles. Need a documented standard for what gets bolded (entity names? action items? vendor terms?) and how each section's bullets are phrased (sentence length, tone, opening pattern). Land the standard in the prompt template for each of the three briefcase generators (Opus KTQ, Haiku Conv, Haiku Intel) so they produce consistent output. Frank §0.5. The 2026-04-07 commit `c91b819` already locked the routing rule (KTQ technical / Conv Starters strategic / Acct Intel leaders) — this item is the formatting half. |
| **Bottom three boxes consistency pass** | The three boxes in the bottom row of the Full Analysis page (Scored Products / Competitive / ACV by Use Case) need a consistency pass: font, font size, vertical spacing, column spacing, padding, alignment. They should feel like one designed row, not three independent components. Audit all three and unify. Frank §0.6. |
| **ACV Table polish** | The ACV by Use Case table needs three things landed together: (a) **Motion names below the row** instead of as the leftmost column, or as a clearer label treatment so the seller can scan the row easily; (b) **Logic for audience size** — better grounding for the AI's per-motion population estimates, anchored to vendor scale signals (links to §5.5 ACV review); (c) **Logic for lab rate per hour** — the rate selection logic should be transparent and auditable, with a clear mapping from orchestration method to rate tier. Frank §0.7. The five canonical motions: Customer training/enablement (direct), Training partner programs, Certification programs, Employee enablement, Events & Conference. (Worth reconciling against `CONSUMPTION_MOTIONS` in `scoring_config.py` — Frank's labels here may be the better naming.) |
| **Product Family Picker — cache awareness** | When a discovery has multiple product families and the family picker fires, the picker doesn't know what's in the cache. The user picks a family blind, without knowing which one would re-use cached scoring vs trigger fresh scoring. **Fix:** decorate each family chip with a `(N cached)` count so the user can pick the cache-leverage option. Frank flagged 2026-04-07 evening. |
| **Product Family Picker — interstitial position + threshold** | The picker currently renders ON the Product Selection page; the spec calls for a separate interstitial step BETWEEN discovery completion and Product Selection. Threshold is 30; should be 20 per Frank's 2026-04-06 directive. And: the "focused discovery" step (a second discovery pass scoped to the family) doesn't exist yet — today picking a family just filters the existing discovery. Decide: implement focused-discovery, or keep filter-only behavior and update the spec to match. Frank §0a. |

---

## §2 — Mid-priority deferred work (still relevant near-term)

| Item | Description |
|---|---|
| **Reusable doc-icon modal — per-product report** | The `?` icons next to each pillar are wired to the info modal for per-pillar WHY/WHAT/HOW. The doc icons next to each product are still decorative — they need to open the same modal but populated with a per-product report. Modal infra is ready (`openInfoModal(key)` accepts `{eyebrow, title, sections}`). **Open question:** what IS the per-product report content? Three options: (a) formatted summary of three pillars + verdict + ACV widget data; (b) Word doc export content rendered in HTML for preview; (c) new "executive briefing" view we haven't built yet. Design first, then build. |
| **Refresh button bug** | The Refresh button on Full Analysis (`tools/inspector/templates/full_analysis.html` ~L479) fires `POST /inspector/analysis/<id>/refresh`, gets back a `job_id`, then runs `window.location.href = '/inspector/score/progress/' + job_id`. That URL is the SSE endpoint — navigating to it renders the raw SSE event stream as text in the browser. Fix: redirect to the existing scoring waiting page (`scoring.html`) with the job_id, not the raw SSE endpoint. ~10 min. |
| **Move INFO_MODAL_CONTENT to scoring_config** | The per-pillar WHY/WHAT/HOW + ACV by Use Case explanation lives as a JS object literal at the top of `full_analysis.html` (`INFO_MODAL_CONTENT`). Should live in `scoring_config.py` (preferred — Define-Once) or a new `docs/explainability-content.md` consumed via a Jinja filter, so non-engineers can edit explainability text without touching the template. ~30 min. |

---

## §3 — Render deployment prep

Get the current build into a state Frank can share with a couple of people via the existing Render service.

| Item | Description |
|---|---|
| **Pre-flight audit** | Read-only audit of (a) how secrets are loaded today, (b) every place the cache writes to disk, (c) any other filesystem writes. Report back so we know exactly what changes need to land. |
| **Entry point** | Add `gunicorn` to `requirements.txt`. Render start command becomes `gunicorn backend.app:app`. Verify the Flask app object is importable as `app`. |
| **Persistent file storage decision** | Current cache writes to local disk; Render's filesystem is **ephemeral** and wipes on every deploy/restart. Three options: **Render Disk** (~$1/mo, 5-min setup, recommended for "share with a couple people"); **Postgres on Render free tier** (better long-term, more setup); **Accept ephemeral cache** (fine for pure demo, analyses regenerate on demand). |
| **Background threads** | Briefcase generation runs in a background thread. Survives normal operation but is lost if the worker restarts mid-generation. Acceptable for demo. Document the limitation. |
| **Secrets audit** | Confirm `ANTHROPIC_API_KEY` (and any other keys) are read from `os.environ` only. No hardcoded keys, no `.env` files committed. Quick grep before pushing. |
| **Auth gate** | The previous Render site's access posture is unknown. For sharing with a couple people: basic password gate (Flask middleware) / Render's built-in auth / IP allowlist. Decide before going live. |

---

## §4 — Standard Search Modal (designed; partially shipped via stale-cache modal)

The full design is in this doc's appendix. The 2026-04-07 stale-cache modal commit (`7c69eb1`) shipped the partial pattern (decision mode + transition to progress) — it's the right time to formalize the contract and use it everywhere.

| Item | Description |
|---|---|
| **Build the publisher** | `backend/progress.py` and a fake operation that emits events on a timer. Verify the contract works against the existing modal. |
| **Wire Discovery first** | Simplest operation, proves the integration pattern. |
| **Wire Deep Dive** | The operation that needs honest progress most. Pairs naturally with §5 Deep Dive performance work. |
| **Wire Prospector batch** | When batch scoring lands. |
| **Retire per-tool progress UIs** | Single cleanup pass once everything is on the standard modal. |

---

## §5 — Deep Dive performance rework

Frank observed during the 2026-04-06 Diligent test: Deep Dive zips through products 1, 2, 3, 4 in under a minute, then **sits on 4/4 for a long time** before the page is ready. The progress bar lies because per-product progress events fire as queries are dispatched, but the real bottleneck is at the tail.

| Item | Description |
|---|---|
| **Instrument the deep dive** | Add timing logs at each stage boundary so we know empirically where the 4/4 hang lives. Don't tune blind. |
| **Replace the products counter** | Stage-aware progress: `Searching → Fetching → Scoring → Ready` instead of "4/4". |
| **Per-fetch timeout** | 5–8 second hard cap in `_fetch_pages_parallel`. Fail fast and move on — missing one page is fine. |
| **Stream scored products** | Stream results to the page as each product finishes scoring. Don't wait for the slowest one. Show "Scoring 3/4 complete" instead of static "4/4". |
| **Sonnet vs Haiku for first-pass scoring** | Test on 2-3 known companies. Is per-product Sonnet necessary, or does Haiku get us 95% there for a fraction of the time? |

---

## §5.5 — ACV calculation review (HIGH PRIORITY)

The deterministic ACV math is **doing the math correctly** but the **inputs from the AI are coming out way too low** for global vendors with large user bases. Confirmed undersized cases: Cohesity ($34K–$167K total ACV across 2 of 15 products — should be hundreds of thousands to low millions), Epiq Discover (similar undersizing pattern).

| Item | Description |
|---|---|
| **Pull Cohesity raw scorer JSON** | Inspect each motion's `population_low/high` and `adoption_pct`. Are they realistic for a vendor of Cohesity's size? |
| **Compare to benchmarks** | `backend/benchmarks.json` lists Cohesity with relationship/scale signals. The AI should be using those signals to inform population sizing. |
| **Audit CONSUMPTION_MOTIONS prompt guidance** | The adoption ceiling rules and population guidance. Are we instructing the AI to "be conservative" in a way that produces unrealistically small numbers? |
| **Add anchor companies** | 3-5 known companies with hand-validated population/adoption estimates to test fixtures. Run scoring, compare AI output to anchors. Anything more than ~25% off is a flag. |
| **Hero display semantics decision** | The hero shows `$34K–$167K` with subtext "Across 2 scored of 15 discovered products" — the headline number represents 13% of the portfolio but visually presents as the answer. Either: extrapolate to full-company estimate; reword the label as clearly partial; or score all products by default. |

**Why HIGH:** ACV is the dollar number sellers and execs see first. If it's wrong by 5–10x, it undermines trust in the whole platform.

---

## §6 — Smaller carry-overs

Full descriptions live in `docs/roadmap.md`. Pull from there when starting.

| Item | Description |
|---|---|
| **Migrate Designer + Prospector off legacy templates** | Both still use `_nav.html` / `_theme.html` with hardcoded hex. Migration to the new shared theme. Deferred until the new Designer code push lands. Roadmap §D + §C. |
| **Update Foundation docs with new architecture** | Sync forward: PL floor, technical fit multiplier, ceiling flags, deterministic ACV math, locked rate variables, the Layer Discipline principle, the rubric model architecture, Phase F Customer Fit centralization. Most of it lives in the decision log — sync it forward. |
| **Comprehensive scoring framework alignment review** | Walk every scored field against `Badging-and-Scoring-Reference.md` and confirm no drift between docs / config / math / template / cached data. |
| **Audit other ceiling-flag-implied synthetic badges** | `bare_metal_required` and `no_api_automation` could follow the same pattern as the (now-removed) `No Learner Isolation` injection. Decide whether to reintroduce. |

---

## SE Clarification Queue — answers needed from a sales engineer

Three open SE questions remain from the 2026-04-06 session. SE-4 was resolved tonight when the Sandbox API red Pillar 1 cap shipped (Diligent five fixes commit `8b9d6be`).

| # | Question | Why it matters |
|---|---|---|
| **SE-1** | **Bare Metal Required** — when evaluating a vendor product, what specific signals in their docs or marketing tell us "this requires bare metal hardware orchestration that we can't virtualize"? Examples of products that hit this — what gave it away? | Today the AI guesses at this. We need detection signals for the canonical `Bare Metal Required` red Blocker badge so it fires reliably and doesn't fire spuriously. Lands in `prompts/scoring_template.md` Pillar 1 + possibly new research queries in `researcher.py`. |
| **SE-2** | **Container Disqualifiers** — we have four documented disqualifiers (dev-use-only image, Windows GUI required, multi-VM network, not container-native in production). Which is the most common practical reason to skip containers? When Windows is needed, is "Windows container" ever the right call, or do we always default to a Windows VM? | Pillar 1 has `Runs in Container` as a green/amber/don't-emit canonical, but the disqualifier list needs SE input to be sharp enough for the AI. Lands in `prompts/scoring_template.md` under the `Runs in Container` canonical. |
| **SE-3** | **Simulation Scorable** — when a lab is delivered via Simulation, when CAN we score it (via AI Vision) and when CAN'T we? Should `Simulation Scorable` ever be a red blocker, or is it always green/amber depending on what's visible on screen? | The `Simulation Scorable` canonical is currently amber-only. The answer determines whether we add a red state and what triggers it. Lands in `scoring_config.py` `_scoring_badges` + `prompts/scoring_template.md` Pillar 1 Scoring section. |

---

## Roadmap-only HIGH items (carry from `docs/roadmap.md`)

These live in the roadmap but should be in active rotation soon.

| Item | Description |
|---|---|
| **Variable-driven badge logic across all 3 pillars** | Extend the variable-badge rule pattern from Provisioning to every dimension across all three pillars. Test case: Epiq Discover — verify variable-driven badge names appear correctly in all three pillars, not just Provisioning/Lab Access. |
| **Discovery tier assignment refinement** | The Seems Promising / Likely / Uncertain / Unlikely assignment needs refinement. Test case: Epiq Discover — initial product search is putting products in the wrong tier in some cases. Revisit discovery scoring thresholds + prompt guidance + initial-pass signals. |
| **Finalize WHY/WHAT/HOW story for ? modal + doc modal** | The reusable info modal has placeholder content for Product Labability, Instructional Value, Customer Fit, and the ACV by Use Case widget. Each pillar's WHY/WHAT/HOW needs to be tight enough that a seller reads it in 30 seconds and walks away understanding the pillar. Pairs with the Skillable capabilities propagation work and the doc-icon report wiring. |
| **Skillable customer identification UX** | When the company being analyzed is already a Skillable customer, the UI should make that visually obvious — both on Product Selection and on Full Analysis. Drives different seller conversation (expansion vs acquisition). Source-of-truth question (decision needed): how do we know which companies are customers? CRM lookup? Static config? HubSpot integration? |
| **CTF in Lab Versatility** | Verify CTF (Capture The Flag) is one of the 12 lab types in `LAB_TYPE_MENU` with the right product category mappings (cybersecurity, security training, offensive security tooling). If it's there but named ambiguously, rename to "CTF / Capture The Flag". CTF is a primary lab format for cybersecurity training and needs to be a first-class option, not buried under "Cyber Range" or "Simulated Attack." |

---

## Deferred / shipped already (do not redo)

The historical record of what's been shipped is split: the 2026-04-06 session shipments are in this doc's "Shipped recently" section below; the 2026-04-07 evening shipments are listed in `docs/decision-log.md`.

Highlights from the 2026-04-07 evening session:

| Commit | What shipped |
|---|---|
| `00123cc` | Risk Cap Reduction — Pillar 1 dimensions can never be at full cap when amber/red risks present (-3 amber, -8 red as cap reduction, not deduction) |
| `a6f7b74` | Customer Fit unification across products (interim merge — Phase F was the proper fix below) |
| `8b9d6be` | Diligent Five Fixes: SE-4 Sandbox API cap (25/5), Datacenter excludes Simulation + new Simulation Reset gray badge, Scoring breadth Grand Slam rule, Fit Score floor drop, Pillar 2/3 prompt sharpening |
| `7c69eb1` | Stale-cache decision modal on Product Selection → Deep Dive |
| `7bb8d04` | Pillar 3 badge JUDGMENT rule — forbidden generic names (`Build vs Buy`, `DIY Labs`, etc.) + judgment-form alternatives (`Light Content Dev`, `Few Tech SMEs`, `Long RFP Process`, `Soft Skills Focus`) |
| `9e5d174` | Account Intelligence prompt — time-bounded events (Elevate-style) as TOP recommendations with concrete next-step actions and Skillable framework anchoring |
| `c91b819` | Briefcase routing rule — KTQ targets technical engineers only (Principal Engineers, API leads, SAs, SEs, customer onboarding); Conversation Starters target strategic VPs/Directors/CLOs; Account Intelligence targets named leaders + named events |
| `b5c981d` | Phase F — Customer Fit lives on the discovery (`discovery["_customer_fit"]`), `intelligence.score()` writes it at every save boundary, `intelligence.recompute_analysis()` reads from there first with per-product merge as fallback |
| `a414723` | Phase 4 creative test strategy — Category 11 with all 10 test classes (round-trip, idempotence, vocabulary closure, bold prefix, cache stamp, pillar isolation, polarity, adversarial, layer discipline AST, define-once string scan). 27 new tests, 115 total passing, pre-commit hook enforces. |

Decisions logged tonight (see `docs/decision-log.md` for details): Layer Discipline as a stated principle; Risk Cap Reduction calibration (-3/-8); Customer Fit unification with "best showing wins" merge rule; legacy quarantine of `_new` suffix files; Phase F as the canonical CF home; Diligent Five Fixes; the stale-cache modal trigger; the Pillar 3 judgment rule (badges as findings, not topics); the briefcase routing rule.

---

## Standard Search Modal — design plan (reference for §4)

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
│   ●━━━━━━━●━━━━━━━●━━━━━━━○━━━━━━━○                       │   ← stage stepper (5 stages)
│   Discover  Search  Fetch  Score   Ready                   │
│   Currently: Scoring product 3 of 4                        │   ← live status line
│   Diligent Boards · Diligent One · HighBond · Galvanize    │   ← per-item live state (✓ ✓ ⏵ ○)
│   Elapsed: 1m 24s · Est. remaining: ~30s                   │   ← time signals
│   [────────────────────────────────] 78%                   │   ← optional fine-grained bar
│   ▸ Activity log (collapsed)                               │   ← optional verbose log
└────────────────────────────────────────────────────────────┘
```

### State contract — every operation publishes this shape

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

### Where it lives in code

```
tools/shared/templates/
  _search_modal.html          ← markup + scoped styles (uses theme vars only) — already exists
  _search_modal.js            ← SSE subscription, DOM updates, lifecycle — already exists in macro form
backend/
  progress.py                 ← shared event publisher (operation_id → SSE channel) — TO BUILD
```

Each operation (`research_products`, `discover_products`, etc.) gets a `ProgressPublisher` injected. It calls `publisher.stage("Search")`, `publisher.item("Diligent Boards", "done")`, `publisher.status("Scoring 3 of 4")`. The publisher fans out to the right SSE channel by operation_id.

### Behavior rules

1. Modal overlays the current page — does not navigate away
2. Cancel kills the operation — backend honors cancellation tokens, no orphaned work
3. On success: dismiss + reload page (or call `on_complete`)
4. On error: stay open, show error in red, offer Retry
5. Stage stepper shows truth, not lies — stages only advance when the stage actually completes server-side
6. Time estimates use rolling history — measure last N runs, show median
7. Activity log is opt-in — collapsed by default
8. Mobile/narrow — stage stepper collapses to a single "Stage 3 of 5: Scoring" line

### Out of scope for first build

- Multi-operation queue (one operation at a time is fine)
- Operation history view (separate feature)
- WebSocket — SSE is sufficient

---

## Open questions (none blocking)

| Question | Notes |
|---|---|
| **Per-product report content for the doc-icon modal** | Three options in §2 — formatted three-pillar summary, Word doc preview, or new "executive briefing" view. Design first, then build. |
| **Other ceiling-flag-implied synthetic badges** | `bare_metal_required` and `no_api_automation` could follow the No Learner Isolation pattern (the latter has been removed). Reintroduce that pattern or skip? |
| **Designer + Prospector tools still on legacy `_nav.html` / `_theme.html`** | Migration is queued but timing depends on the new Designer code push. |
