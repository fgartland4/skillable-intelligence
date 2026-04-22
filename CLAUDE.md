# Skillable Intelligence — LEGACY (Reference Only)

> ## ⚠️ LEGACY — Reference Only ⚠️
>
> **This repository is the Python/Flask proof-of-concept. Active development lives in [`../intelligence/`](../intelligence/).**
>
> Read [`../intelligence/CLAUDE.md`](../intelligence/CLAUDE.md) for the current project rules and [`../intelligence/docs/`](../intelligence/docs/) for the locked specs (platform, scoring, roadmap).
>
> **You are here only for:**
> - Re-mining specific mechanics when the new specs cite legacy behavior (e.g., risk cap reduction formulas, CF merge logic, legacy signal-name translation)
> - Reading `backend/known_customers.json` (gitignored — Frank's real-world calibration anchors)
> - Studying legacy UX patterns that inform the rewrite (e.g., contact-pulling, competitive-products display, Standard Search Modal behavior)
>
> **You are NOT here to:**
> - Build new features — that work happens in `../intelligence/`
> - Edit legacy code to change behavior
> - Treat anything here as current truth — the new specs supersede everything below this banner
>
> If a Claude session opens in this repo by mistake, switch to `../intelligence/` before doing any work beyond reference lookup.

---

## Historical Project-Specific Rules (Below)

The content below was the active rulebook during the legacy proof-of-concept era. It is preserved for historical context and is referenced by the new specs where legacy mechanics carry forward. Do not treat it as current instruction — the new repo's `CLAUDE.md` and specs are authoritative.

For how we work together, the startup sequence, and the thinking system, see the new repo's [`docs/collaboration-with-frank.md`](../intelligence/docs/collaboration-with-frank.md).

---

## Project-Specific Rules

### Layer Discipline — Intelligence Belongs in the Intelligence Layer

The platform has THREE tools — **Inspector**, **Prospector**, **Designer** — that all sit on top of a shared **Intelligence layer**. The Intelligence layer owns ALL the logic about *what we know and how we evaluate it*: research, discovery, per-pillar scoring, rubric grading, Fit Score composition, ACV calculation, badge selection, cache versioning, validation, briefcase generation, model definitions, locked vocabulary, classification, verdicts. The three tool layers own ONLY *the things that are tool-specific*: URL patterns, request parsing, template selection, view orchestration.

**The discipline rule:** if a function does intelligence work — scoring, grading, composing, calculating, classifying, recomputing, deciding — it belongs in the **Intelligence layer** (`backend/intelligence.py`, `backend/scorer.py`, `backend/researcher.py`, `backend/pillar_1_scorer.py`, `backend/pillar_2_scorer.py`, `backend/pillar_3_scorer.py`, `backend/rubric_grader.py`, `backend/fit_score_composer.py`, `backend/acv_calculator.py`, `backend/badge_selector.py`, `backend/post_filters.py`, `backend/scoring_config.py`, `backend/storage.py`, `backend/models.py`, `backend/core.py`) where ALL three tools can call it. If it does view work — rendering a template, parsing a query string, redirecting, picking a default product index — it stays in the tool layer (`backend/app.py` Inspector routes, future Prospector routes, future Designer routes).

**How to test:** ask "would Prospector or Designer also need this if they were calling it?" If yes, it belongs in the shared layer. If no, it belongs in the tool. **When in doubt, default to shared.**

**Why this matters:** Prospector batch scoring + lookalikes are real work coming next, and Designer needs product intelligence (with the hard wall against company intelligence). Three tools cannot have three drifted copies of the same scoring logic. Several of the worst bugs in the codebase to date came from intelligence logic mistakenly placed in `app.py` (the Inspector Flask app), where it ran differently than the path the scorer took at score time, silently producing wrong scores.

| Belongs in the **Intelligence layer** | Belongs in the **tool layer** |
|---|---|
| `discover()`, `score()`, `recompute_analysis()`, `refresh()` | URL handlers, route decorators |
| Per-pillar scoring, rubric grading, Fit Score composition, ACV calculation | Request parsing, query param extraction |
| Badge selection (post-scoring display layer) | Template selection, response shaping |
| Cache versioning + invalidation (`SCORING_LOGIC_VERSION`) | Tool-only progress orchestration |
| Verdict assignment | Tool-only UI defaults (e.g. selected product index) |
| Discovery tier / classification / org color computation | Anything no other tool would ever call |
| Loading models and knowledge from JSON | |
| Anything another tool would also need | |

When you find intelligence logic living in a tool layer, **flag it as a bug-class violation** — it is the same severity as vocabulary drift or cache version lies. Fix or document the move to the shared layer.

### Legacy Boundary

Everything built before the Platform Foundation (April 4, 2026) is proof-of-concept. Never silently reuse old files, old prompts, old data, or old vocabulary. If it wasn't built from the Platform Foundation forward, it doesn't belong. Flag and fix — don't carry forward.

### Always Commit and Push

After completing any code changes, automatically stage, commit, and push without prompting.

### The Standard Search Modal — THE ONE AND ONLY

**There is ONE search / progress modal in this entire platform. It lives in `tools/shared/templates/_search_modal.html` and is used for every long-running operation across Inspector and Prospector today, and will be used by Designer when that tool is built.**

Before you build ANY new progress UI, loading spinner, overlay, decision prompt, or "wait while we search" experience — STOP. The answer is always the same shared modal. No exceptions.

**If you find yourself about to:**
- Create a new `<div>` for a progress bar
- Add `new EventSource(` to any file that isn't `_search_modal.html`
- Build a decision prompt ("Refresh? / Use cached?") with its own markup
- Render a full-page progress template (like the pre-2026-04-07 `scoring.html`)
- Copy/paste the modal markup to tweak a per-flow variant
- Add a "loading..." inline UI to any long-running action

...then you are doing the wrong thing. Reuse the shared modal. If the modal's middle section needs a new variant, add the variant INSIDE `_search_modal.html`, do not fork.

**API (from `_search_modal.html`):**
- `openSearchModal({eyebrow, title, sseUrl, onComplete, onError})` — progress mode
- `openSearchModalDecision({eyebrow, title, message, onRefresh, onIgnore})` — decision mode
- `transitionSearchModalToProgress({...})` — in-place decision → progress transition

**SSE contract** the modal expects the backend `push(job_id, ...)` to follow:
- `status:<text>` → updates the visible status line
- `done:<payload>` → calls `onComplete(payload)`
- `error:<message>` → calls `onError(message)` or shows inline error

**Why this is non-negotiable:** Every time someone has built "just a small custom progress page for this one flow," the platform has ended up with drifted UI, different timer behavior, different error handling, inconsistent status updates, and users who can't tell which Skillable tool they're in. There is ONE progress experience across the platform. It's the shared modal.

**When Prospector and Designer come online:** they reuse `_search_modal.html`. The component has zero Inspector-specific code. Just `{% import '_search_modal.html' as sm %}` from anywhere in the tools tree and call the same API.

See also: GP4 (Self-Evident Design) and GP6 (Slow Down to Go Faster) in `docs/Platform-Foundation.md`.

### Never Mention the Preview Panel

The preview tool renders raw Jinja2 template syntax, not the running Flask app. After editing any template, do not mention the preview panel. To see changes, reload the Flask app.

### Grid Uniformity

Consistent 2-column grids. Field widths match across sections. Full-width sections with inner grids. Narrow dropdowns for short values. Vertical alignment via proper grid rows. Buttons match adjacent input height. Use `settings-grid` or `settings-grid-4cell` patterns.

### Skillable Terminology

Two cloud fabrics (Azure Cloud Slice, AWS Cloud Slice). Three virtualization fabrics (Hyper-V, ESX, Docker/Container). "Fabric" is correct for these. **Never say "network fabric"** — networking is a capability of the virtualization fabrics, not a separate entity.

**Badge vs implementation.** The badge name `Runs in VM` is fabric-neutral (user-facing); the internal fabric enum `hyper_v` names the actual implementation. Both are correct at their layer — do not rename the enum to match the badge or vice versa.

### No Inspector-to-Designer In-App Handoff

Intentional — tools serve different personas, accessed separately. The `analysis_id` bridges them at the data level. Never flag this as a missing feature.

### Decision Log

Decisions made during sessions are logged in `docs/decision-log.md`. This is write-only — never read it to determine what's current. The Foundation docs are best current thinking.

---

## Build Roadmap

See `docs/roadmap.md` for the consolidated inventory of everything we know we want to do, are doing, have done, or need to decide.

## Ops Scripts

See `scripts/README.md` for the index of every operational tool — rescore, retrofit, dedup, merge, thin-research detection, flagship Deep Dive runner, etc. If you're about to build a tool, check there first — there's a good chance it already exists. If you build a new one, add it to that README in the same commit.

---

## Key Architecture

### Score Layer Modules — one file, one job

There is **no monolithic scoring prompt**. Score reads the typed fact drawer directly and applies deterministic rules. The only Claude call the Score layer is allowed to make is the narrow **rubric grader**, which tiers qualitative findings for Pillars 2 / 3 (strong / moderate / weak / informational). Everything else is pure Python.

| Module | What it does |
|---|---|
| `backend/scoring_config.py` | Define-Once source of every variable the math layer touches — pillar weights, dimension weights, scoring signals, rubric tiers, baselines, penalty tables, risk cap reduction constants, Technical Fit Multiplier table, rate tables, ACV tier thresholds, Verdict Grid, locked vocabulary. **No hardcoded numbers anywhere else in the Score layer.** |
| `backend/researcher.py` + three fact extractors | Research layer — parallel Claude calls per Deep Dive populate `ProductLababilityFacts`, `InstructionalValueFacts`, `CustomerFitFacts`. Truth-only — no scoring judgments. |
| `backend/pillar_1_scorer.py` | Pillar 1 Product Labability — **pure Python, zero Claude.** Reads capability-store facts and produces a `PillarScore` with four dimension scores. Handles Simulation hard override, fabric priority + optionality bonus, container disqualifiers, bare-metal + Sandbox API score_override caps. |
| `backend/rubric_grader.py` | The **narrow Claude-in-Score slice.** One focused Claude call per Pillar 2 / Pillar 3 dimension grades qualitative findings into `GradedSignal` records. |
| `backend/pillar_2_scorer.py` | Pillar 2 Instructional Value — pure Python. Reads `GradedSignal` records + category-aware baselines, applies strength tiers, honors the penalty-visibility rule (capped positives, then subtract penalties). |
| `backend/pillar_3_scorer.py` | Pillar 3 Customer Fit — pure Python. Same rubric math as Pillar 2 with organization-type baselines. Per-company, not per-product. |
| `backend/fit_score_composer.py` | Composes the three pillar scores into the final Fit Score with the Technical Fit Multiplier applied to IV + CF contributions (asymmetric coupling — weak PL drags IV + CF down). Writes `FitScore.total_override` + `FitScore.technical_fit_multiplier`. |
| `backend/acv_calculator.py` | Pure Python. Computes ACV Potential from per-motion audience / adoption / hours estimates + the rate tier lookup keyed on orchestration method. |
| `backend/badge_selector.py` | Post-scoring display layer. Reads facts + pillar scores and emits 2–4 canonical badges per dimension with evidence text. Honors the locked naming rules. Zero scoring impact. |
| `backend/post_filters.py` | Deterministic guardrails for AI output quality. Removes delivery platforms from product lists, validates categories, sanity-checks audience estimates and ACV motions. Runs after discovery parsing and after scoring. Millisecond execution, no API calls. |
| `backend/intelligence.py` + `backend/scorer.py` | Orchestration — wire the above together for `discover()`, `score()`, `recompute_analysis()`, briefcase generation. |
| `backend/models.py` + `backend/storage.py` | Data model (typed dataclasses) + JSON persistence. |
| `backend/core.py` | Shared helpers — verdict assignment, classification label, sorting, etc. |

Deleted in the 2026-04-08 rebuild: `scoring_math.py`, `badge_normalization.py`, `prompt_generator.py`, `prompts/scoring_template.md`, and the monolithic `SCORING_PROMPT`. If you see a reference to any of these in old commits, decision-log entries, code-review artifacts, or legacy-reference code, **it is stale — do not reconstruct it.** Route the concept to its new home:

| Deleted module / concept | New home |
|---|---|
| `scoring_math.py` (monolithic scoring) | Split into `pillar_1_scorer.py`, `pillar_2_scorer.py`, `pillar_3_scorer.py`, `fit_score_composer.py`, `acv_calculator.py` — one file per concern |
| `prompt_generator.py` + `prompts/scoring_template.md` | Prompts assembled inline in `researcher.py` (three per-pillar fact extractors) + the narrow Claude slice in `rubric_grader.py` |
| `badge_normalization.py` | Replaced by post-scoring `badge_selector.py` — display layer, zero scoring impact |
| `SCORING_PROMPT` (single monolithic Claude call) | Removed entirely. Score layer reads typed fact drawers directly and applies deterministic Python rules. The only Claude calls in the Score layer are the rubric grader's per-dimension calls for Pillar 2/3 qualitative grading. |
| `app_new.py` | Renamed to `app.py` during cleanup. Any `app_new.py` reference is stale. |
| `legacy-reference/` directory | **Off-limits for code reuse.** Reference only — never copy, import, or port. Pre-Foundation work is proof-of-concept. See "Legacy Boundary" above. |

Route the concept. Do not reconstruct the module.

### Data Architecture — Three Domains

| Domain | What it contains | Access |
|---|---|---|
| **Product data** | What products are, labability assessments, orchestration details | Open — all tools including Designer |
| **Program data** | Lab series, outlines, activities, instructions (Designer) | Scoped — only your own programs |
| **Company intelligence** | Fit scores, badges, contacts, ACV estimates | Internal-only — Skillable roles only |

### Page Names

| Page | Name |
|---|---|
| Inspector home | **Inspector** |
| Product selection | **Product Selection** |
| Deep dive results | **Full Analysis** |

Discovery tier labels: Promising, Potential, Uncertain, Unlikely

---

## Word Document Standards

**Font:** Calibri 10pt body, 8pt footer
**Logo:** `C:\Users\Frank.Gartland\OneDrive - Skillable\Sales Enablement\Keep\z-Skillable Logos\Skillable Logo\Default@4x.png` — right-aligned, ~1.1" wide
**Footer:** "Page X of Y" right-aligned, 8pt Calibri gray (#888888)

For full Word doc generation standards, see `docs/` reference files.
