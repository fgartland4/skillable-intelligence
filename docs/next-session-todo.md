# Next Session — Todo List

**Last updated:** 2026-04-08 (mid-rebuild — Research→Store→Score→Badge layered architecture, Steps 1 + 2 shipped, Step 3 in progress)
**Read this first when you sit down for the next session.**

---

## Format note

This doc uses a two-column table format per Frank's 2026-04-07 directive: narrow column 1 = item name, wider column 2 = description. Sections are kept thin so the long arc lives in `docs/roadmap.md` and the historical record lives in `docs/decision-log.md`.

---

## §0 — START HERE (THE REBUILD IS IN PROGRESS)

**The Intelligence layer is being rebuilt to align the code with the Three Layers of Intelligence architecture described in `docs/Platform-Foundation.md` (lines 182–233).** Everything below §0 reflects the pre-rebuild backlog; those items are still valid but are on hold until the rebuild reaches Step 6. **The rebuild is the ONLY priority until it lands.**

**Why we're rebuilding.** The old Intelligence layer collapsed three layers into one big Claude call per product — the call did research, applied Skillable judgment, and emitted scoring badges all at once. That was the forbidden pattern Platform-Foundation.md explicitly names ("Research + Score in one Claude call"). Symptoms: badge inconsistency, score drift, logic that kept changing because judged data was colliding with the math layer. Frank's diagnosis: **"The math is right. The problem was badges were the only way to get points, so the AI was emitting multiple similar badges to hit the right score and the math couldn't be clean."**

**Where to read the target architecture:** `docs/Platform-Foundation.md` → "The Three Layers of Intelligence — Research, Score, Badge" (lines 182–233). That section defines the four sub-layers (Research, Store, Score, Badge), the forbidden collapse patterns, and what each layer is allowed to use. Read it before making any rebuild decisions.

### §0a — Where we are right now

| Item | Status |
|---|---|
| **Step 1 — Fact drawer dataclasses** | **SHIPPED** (commit `14e0c44`). Added `ProductLababilityFacts`, `InstructionalValueFacts`, `CustomerFitFacts` + all sub-dataclasses to `backend/models.py`. Truth-only typed primitives. No `strength` field. Attached to `Product` / `CompanyAnalysis`. Define-Once spot tests pass. |
| **Step 2 — Research → Store layer** | **SHIPPED** (commits `68ff479`, `eb44327`). Three per-pillar Claude extractors in `backend/researcher.py` (`extract_product_labability_facts`, `extract_instructional_value_facts`, `extract_customer_fit_facts`) wired into the live Deep Dive path in `intelligence.score()`. Extractors run in parallel per product (P1 + P2) plus one per company (P3). Each extractor uses a focused, truth-only prompt describing its slice of the fact drawer schema. Results attach to the `Product` / `CompanyAnalysis` objects before the legacy monolithic scoring call runs. |
| **Trellix smoke test (Step 2 validation)** | **PASSED** 2026-04-08. Deep Dive completed end-to-end on Trellix with forced cache refresh. Fact drawers populated. No regressions. The legacy monolithic scoring call still runs alongside as a safety net until Step 5. |
| **Step 3 — Pillar 1 Python scoring from facts** | **IN PROGRESS.** Not yet written. See §0c for plan. |
| **Step 4 through Step 6** | Pending. See §0c. |

### §0b — Architectural lock-ins (these are non-negotiable for the rebuild)

These lock-ins came out of multiple clarifying conversations during the rebuild. They override any prior guidance in any other doc. Platform-Foundation.md's Three Layers of Intelligence section is their home; this list is the working checklist.

| # | Lock-in | What it means operationally |
|---|---|---|
| **1** | **Score reads facts directly. Never badges.** | The Score layer takes typed primitives from the fact drawer as input and computes `DimensionScore` objects directly. It does NOT match against badge names or look up points by badge. The existing `scoring_math.compute_dimension_score()` is badge-keyed and will be deleted at Step 5. |
| **2** | **The math is right. Only the input format changes.** | Point values, caps, formulas, and rules in `scoring_config.py` stay exactly as they are: Hyper-V = +30, Sandbox API = +22, Grand Slam cap = 15, risk cap reduction (-3 amber, -8 red), Sandbox API red Pillar 1 cap (25/5), Technical Fit Multiplier, Ceiling Flags. What changes is HOW values get fed to the math. Old way: badge name → signal lookup. New way: `facts.provisioning.runs_as_installable` → direct signal credit. |
| **3** | **Badges are post-scoring display only.** | Badges are the Step 6 layer. They read facts + computed scores and pick 2–4 contextual storytellers per dimension to explain WHY the score is what it is. Badges never affect the math. Badges never feed scoring. A badge that tried to do both was the "badge-as-scoring" drift Platform-Foundation.md explicitly names as forbidden. |
| **4** | **Claude runs PRIMARILY in Research. Two open questions for Steps 4 and 6.** | Current direction: Score is pure Python. Badge is pure Python. Research is where Claude is called. **Not yet locked:** (a) Pillar 2 / Pillar 3 strength tiering at Step 4 may legitimately need a small Claude call because strength is qualitative judgment — candidate approaches in §0c Step 4. (b) Badge evidence phrasing at Step 6 may use a tiny Claude call per dimension. Both decisions happen at the step boundary, with Frank, before the code is written. This lock-in is **current direction, not locked**. |
| **5** | **Facts are truth-only. No `strength`, no Skillable judgment, no interpretation.** | `SignalEvidence` has `{present, observation, source_url, confidence}` — NO `strength` field. Strength is interpretation; the drawer holds facts. Define-Once spot tests in `tests/test_data_model.py` enforce this contract. Any future fact addition must go through the same spot-test gate. |
| **6** | **NO HARDCODING ANYWHERE. EVER.** | Every number, every threshold, every magic string, every point value, every cap, every weight, every rule parameter — all of it comes from a Define-Once source (`scoring_config.py`, `skillable_capabilities.json`, `competitors.json`, `contact_guidance.json`, `delivery_patterns.json`, etc.). If a rebuild scorer has a literal `15` or `+30` or `"rich"` or `"Hyper-V"` in it, that's a bug — lift the value to config. This rule is stronger than "Define-Once" as usually stated; it is the **hard zero-hardcoding standard** applied to every line of rebuild code. Pre-commit review will scan for literals that look like framework constants. |
| **7** | **The UX doesn't change during the rebuild.** | No new screens. No new buttons. No new progress modals. No new Product Chooser. The rebuild is internal — swap out the engine. Same entry points, same flows, same modal. |
| **8** | **Legacy paths stay alive until cutover.** | Each new step adds code alongside the old code, not in place of it. The monolithic scoring call keeps running as a safety net while Steps 3 and 4 build the new path in parallel. Step 5 is the cutover — delete the monolithic call, delete `compute_dimension_score()`, flip the Product model field from comparison to authoritative. |

### §0c — The rebuild plan (Steps 1 through 6)

| Step | What it does | Status |
|---|---|---|
| **1 — Fact drawer dataclasses** | Add typed-primitive dataclasses for all three pillars to `backend/models.py`. Attach to `Product` and `CompanyAnalysis`. Define-Once spot tests enforce canonical homes and truth-only contract. | **SHIPPED** (`14e0c44`) |
| **2 — Research → Store layer** | Three per-pillar Claude extractors in `backend/researcher.py`. Truth-only prompts. Wire into live Deep Dive path in `intelligence.score()`. Parallel per-product execution. Fact drawers attach to `Product` / `CompanyAnalysis` before the legacy monolithic call runs. | **SHIPPED** (`68ff479`, `eb44327`) |
| **3 — Pillar 1 Python scoring from facts** | New module `backend/pillar_1_scorer.py`. Four functions: `score_provisioning(facts)`, `score_lab_access(facts)`, `score_scoring(facts)`, `score_teardown(facts)`. Plus a composing `score_product_labability(facts, context)`. Each reads `ProductLababilityFacts`, applies priority order / Grand Slam / risk cap reduction / Sandbox API red cap using point values from `scoring_config.py`, returns a `DimensionScore` (signals matched, penalties applied, caps applied, raw total, final score). Wired into `intelligence.score()` to produce `product.pillar_1_python_score` alongside the legacy monolithic result for side-by-side comparison. The monolithic call still runs. Pass criteria: Trellix Endpoint Security Python-derived Pillar 1 score lands within ~5 points of the monolithic-call Pillar 1 score (directional match). Covered by new canned-fact unit tests in `tests/test_pillar_1_scorer.py`. | **IN PROGRESS** |
| **4 — Pillars 2/3 Python scoring from facts** | New modules `backend/pillar_2_scorer.py` and `backend/pillar_3_scorer.py`. Pillar 2 is per-product; Pillar 3 is per-company. Both read rubric dimensions from facts (qualitative `SignalEvidence` dicts + concrete numerics) and apply category/org-type baselines from `IV_CATEGORY_BASELINES` and `CF_ORG_BASELINES`. **Open architectural question:** the rubric model uses strength tiers (`strong`/`moderate`/`weak`) to grade signal credits. Strength is interpretation, which is scoring-layer work, but today the only way strength is determined is via Claude judgment at score time. Three candidate approaches — (a) derive strength from `SignalEvidence.confidence` + presence + observation length heuristics in pure Python; (b) derive strength from concrete typed primitives expanded into the fact drawer at Step 2 refresh; (c) a tiny per-dimension Claude call at Score time used ONLY for strength grading (partially violates "no Claude in Score" but keeps rubric rich). **Must be discussed and resolved with Frank before Step 4 code starts.** | Pending |
| **5 — Cutover** | Delete the legacy monolithic per-product scoring Claude call. Delete `scoring_math.compute_dimension_score()` and `_compute_rubric_dimension_score()` (badge-keyed paths). Flip `Product.fit_score` to be populated by the Python scorers. Remove `Product.pillar_1_python_score` comparison field. Keep `compute_pillar_score()`, `apply_ceiling_flags()`, `get_technical_fit_multiplier()`, `compute_fit_score()`, `compute_acv_potential()`, `detect_sandbox_api_red_cap()` — those operate above the dimension-score level and stay. | Pending |
| **6 — Badging layer** | New module `backend/badge_selector.py`. Reads fact drawer + computed scores, picks 2–4 contextual badges per dimension that best explain the score. Pure Python by default; optional tiny Claude call per dimension for evidence phrasing (decision deferred). Replaces every place badges come out of the scoring call today. Badges are display-only — they have no effect on math and cannot be fed back into scoring. | Pending |
| **7 — UX followups (post-rebuild)** | The two UX workstreams explicitly deferred until after the rebuild lands: **(a) ACV hero widget** — the 3-line structure defined in `docs/Platform-Foundation.md` lines 711–734 (company-level range, descriptor, scored subtotal with the word `ONLY`). **(b) Three-Box Bottom Row consistency pass** — same font, size, vertical spacing, column spacing, padding, and alignment across Scored Products / Competitive Products / ACV by Use Case, per `docs/Platform-Foundation.md` lines 766–800. Slate blue font on the middle box is the one intentional differentiator. Both plans are already well-written in Platform-Foundation — Step 7 is the implementation pass, not a re-design. | Pending |
| **8 — Docs major rewrite (rebuild capstone)** | After Steps 1–7 are in, **both `docs/Platform-Foundation.md` and `docs/Badging-and-Scoring-Reference.md` get a major refactor/rewrite pass** to be *best and most current thinking* — synthesized, not appended. The standard: (1) every section reflects exactly what the rebuilt code does, why, and how; (2) zero conflicts between the two docs, zero conflicts with the code, zero conflicts between sections of the same doc; (3) zero duplication — if a concept is defined in one place, the other references it rather than restating. This is load-bearing under GP3 (Explainably Trustworthy), GP4 (Self-Evident Design), GP5 (Intelligence Compounds — never resets), and the "Best Current Thinking, Always" rule in `docs/collaboration-with-frank.md`. The rebuild is not complete until both foundation docs read like they were written from scratch today with full knowledge of what the rebuilt code does. Stale references to "the AI emits badges that the math scores" must be gone. Stale badge-keyed scoring mechanics must be gone. Fact drawer architecture, per-pillar Python scorers, and the post-scoring badging layer must be first-class in both docs. | Pending |

### §0d — What NOT to touch during the rebuild

| Don't touch | Why |
|---|---|
| UX (templates, CSS, layouts, the progress modal, Product Chooser, the hero widget, the three-box bottom row) | The rebuild is backend-only. User-visible behavior should stay identical until Step 5 cutover, at which point scores may move because the math is now fed better evidence — but no layout or flow changes. |
| `scoring_config.py` | All point values, caps, thresholds, penalties, rubric definitions, baselines, canonical lists. Define-Once stays untouched. |
| Top-of-pillar math: `compute_pillar_score`, `apply_ceiling_flags`, `get_technical_fit_multiplier`, `compute_fit_score`, `compute_acv_potential`, `detect_sandbox_api_red_cap` in `scoring_math.py` | Those operate above the dimension-score level. They compose dimension scores into pillar scores and apply global caps. They stay. Only `compute_dimension_score()` and its rubric sibling get deleted at Step 5. |
| The fact extractors from Step 2 | They work. Don't retune them during Step 3/4 work. If a fact is missing, add a new typed field to the dataclass and a new line to the extractor prompt — don't refactor the extractors themselves. |
| Everything in §1 and below | Pre-rebuild backlog. Valid work, on hold. |

---

## §1 — Search Modal Migration (demoted from §0 by the rebuild — still valid)

The Standard Search Modal unification is half-done. `discovering.html` was migrated in commit `e6784dc` (2026-04-07 late evening). `scoring.html` — the Deep Dive progress page — is still on its 417-line legacy custom implementation. Picks back up after the rebuild lands.

| Item | Description |
|---|---|
| **Migrate `scoring.html` to the shared `_search_modal.html`** | Deep Dive must render through the one shared modal like every other long-running flow. `scoring.html` currently has its own custom CSS, custom EventSource handler, rotating hint messages, three-stage "orchestration bars," and a research-to-Claude phase transition — all of which must move into a "deep dive" variant of the shared modal's middle section. Pattern to follow: the `discovering.html` migration in commit `e6784dc` (41-line shell that imports the shared modal, calls `openSearchModal()`, and wires the SSE stream). The SSE contract (`status:` / `done:` / `error:`) is already compatible — no backend changes should be needed, only template + frontend work. After migrating, delete the legacy `scoring.html` custom UI and add a regression test in `tests/test_ux_consistency.py` that scans Inspector templates for "custom progress" patterns (any `new EventSource(` outside `_search_modal.html`). Frank 2026-04-07: "We should not have multiple search. There should be one search modal, and the middle is the part that should be different." |

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
