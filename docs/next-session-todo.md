# Next Session — Todo List

**Last updated:** 2026-04-08 (late session — scoring viable_fabrics refactor shipped `dd62c87`, researcher SaaS/cloud contradiction fix shipped `a296e29`, docs audit + refresh landed this commit. Both planning docs are now trimmed to best current thinking. Read this doc first when you sit down for the next session, then `docs/roadmap.md` for the long arc.)

---

## Format

Three layers, in priority order:

1. **Start here** — the single first action of the next session
2. **Live bugs** — small, fix-when-you-touch-the-area items
3. **Big projects** — the sequenced workstreams

Everything else is in `docs/roadmap.md`. Everything shipped is in `git log` and `docs/decision-log.md`.

---

## §1 — START HERE NEXT SESSION

**Documentation Job A — content design conversation.**

Walk `docs/Platform-Foundation.md` and `docs/Badging-and-Scoring-Reference.md` together with Frank and decide:
- Which sections of each doc become extractable "pull into UI" content
- Where the tone needs polish to read as seller-facing (30-second read target)
- How to mark extractable sections (proposed: HTML-comment anchors like `<!-- modal:pillar-1-why -->...<!-- /modal:pillar-1-why -->`)
- How Platform-Foundation (WHY / WHAT) and Badging-and-Scoring (HOW) compose into one pillar modal

**Why this first:** Frank needs to get external eyeballs on the platform. Without the ? modal content in place, every demo generates the question "how are you scoring this?" and he ends up explaining the methodology manually. The content already exists in the Foundation docs — what's missing is the design of how to surface it in the UI without duplicating anything.

**Slow part:** the design conversation. Must happen live. Do not skip.

**Fast parts after design:**
1. Write small Python extractor helper (~20 lines — reads MD file, pulls section by anchor name)
2. Wire the existing reusable info modal to consume extracted content, themed per job (Job A = green/blue, Job B = orange — Frank's direction)
3. Per-pillar ? icon content lands automatically on next app refresh

---

## §2 — LIVE BUGS (FIX WHEN YOU TOUCH THE AREA)

| Bug | Investigate when |
|---|---|
| **Discovery bloat + family picker under-grouping** — Trellix returns ~46-49 products vs ~22 real; then family picker collapses 42 under one "Cybersecurity" header making it useless as a filter. Two stacked bugs (upstream over-extraction + coarse grouping), one investigation. Test case: Trellix. | When touching discovery, or as a dedicated pass if external testers hit it first. Has a screenshot in the conversation log. |
| **Pillar 2 extractor reliability** — intermittent empty `mastery_stakes` / `lab_versatility` / `market_demand` drawers even on products where facts clearly exist. Cross-pillar grader safety net in `rubric_grader.py::_product_shape_context` keeps grades flowing in the meantime, but the root cause is in the extractor. Requires investigate-first: look at a failing product, diagnose whether it's prompt, schema, or model behavior. | When touching Pillar 2 researcher / grader work, or as a dedicated pass. Not blocking anything right now. |

**Batch bugs during documentation work.** Frank will queue up small bugs during Job A / Job B sessions — pause at natural breakpoints (between extractor helper + wiring, between Job A and Job B) to batch them rather than context-switch mid-design-conversation.

---

## §3 — BIG PROJECTS (SEQUENCED)

In priority order — do not parallelize. Each one has its own design conversation before build.

### 1. Documentation Job A — the ? modal (how does this work)

Prerequisite: §1 design conversation.

**Scope:**
- Reformat Platform-Foundation.md and Badging-and-Scoring-Reference.md to mark extractable sections with anchor comments
- Tone polish where needed for seller-facing read
- Small Python extractor helper
- Wire the existing reusable info modal, themed per job
- Content flows automatically from docs → UI on next refresh (Define-Once for documentation)

**Per pillar, the ? modal assembles:**
- WHY (from Platform-Foundation) — why this pillar matters in Fit
- WHAT (from Platform-Foundation) — what it measures concretely
- HOW (from Badging-and-Scoring-Reference) — how we score it

### 2. Deployment — Render or Azure Web App

Prerequisite: Job A shipped. Frank has said he will not put this in front of people without the documentation in place — calls would eat his day.

**Decision needed:** Render vs Azure Web App. Frank wants to talk to his team before deciding.

**Scope once decided:** secrets loading, gunicorn entry point, persistent storage decision (cache writes, briefcase generation), auth decision (public URL + obscurity, or allowlist).

### 3. Documentation Job B — per-product report (doc icons)

**Scope:**
- Design conversation first: what does a per-product report contain? Three options outlined earlier — three-pillar summary, Word doc preview, executive briefing
- Frank's framing: "if somebody wants the Instructional Value report for a particular product" — suggests dimension-level drill-down, not just whole-product summary
- Modal vs separate tab — defer the decision until the content shape is clear (3-page content wants a tab, 1-screen wants a modal)
- Same shared info-modal infrastructure as Job A, different theme color

### 4. Prospector — design + build

**Scope:**
- Design conversation first. UX may differ from the old Prospector based on what we've learned
- **Rewrite, not port.** Old Prospector exists in a different git repo and should be read as reference only. CLAUDE.md Legacy Boundary rule applies — no silent reuse of pre-rebuild code, prompts, or data
- Core workstream: batch scoring (import list → research → output spreadsheet) then lookalikes (product-fit matching from competitor pairings)
- Relies on the shared Intelligence layer already built in this repo

### 5. Designer — design + build

**Scope:**
- Biggest of the three project workstreams
- Has existing design docs: `docs/Designer-Session-Prep.md` and `docs/Designer-Session-Guide.md` — read both before the design conversation
- People → Purpose → Principles → Rubrics → UX
- Deferred until Job A + Deploy + Job B + Prospector land, or until Frank's team pushes the new Designer code

---

## §4 — INFRASTRUCTURE + POLISH (SLOT IN WHERE IT FITS)

Not big enough to be their own projects; not small enough to be bugs. Slot into an existing workstream at the right moment.

| Item | Slot into | Why |
|---|---|---|
| **Standard Search Modal (shared progress UI)** — reusable progress modal contract for all long-running operations across Inspector, Prospector, Designer. Partial implementation shipped via stale-cache decision mode (`7c69eb1`); full contract + `progress.py` publisher + Discovery wiring still pending. CLAUDE.md has the "ONE and ONLY" rule: build once, reuse thrice. | Before Prospector design. Build it as the first infrastructure step of the Prospector workstream so Prospector gets it for free. | Drift prevention. |
| **Skillable customer identification UX** — when an analyzed company is already a Skillable customer, the UI should make that obvious ("You're already a Skillable customer — here are your current lab platforms"). Decision needed on source: CRM lookup / static config / HubSpot integration. | Job A or Job B sessions as a polish pass. | Demo polish; big "aha" moment for the seller using the tool. |

---

## §5 — DELIBERATELY DEFERRED (DECISIONS NEEDED BEFORE WORK)

See `docs/roadmap.md §I` for the full decisions-needed list. The ones most likely to come up in the near-term workstreams above:

- **Auth** — tied to deployment decision. If the tool goes on a public URL, who can use it?
- **Per-product report content (doc icon modal)** — three options on the table; decide before Job B build
- **HubSpot write-back field mapping** — Stage 1 → Company Record, Stage 2 → Deal Records. Needs RevOps conversation
- **Skillable customer identification source** — CRM / static config / HubSpot
- **Render vs Azure Web App** — Frank's team decision before Deploy workstream

---

## Working style reminders

- **Chunked responses, not walls of text.** Frank has said "wow. wall. can you chunk these up?" — keep replies structured and terse
- **Read Foundation docs before acting.** Everything you need is in `docs/collaboration-with-frank.md`, `docs/Platform-Foundation.md`, `docs/Badging-and-Scoring-Reference.md`. Read in that order at session start
- **Layer discipline.** Intelligence logic → shared intelligence layer. Tool-specific work → tool layer. When in doubt, default to shared. See CLAUDE.md "Layer Discipline" section
- **No hardcoded numbers outside scoring_config.py.** Pre-commit hook enforces this
- **Commit + push after any code change.** Per CLAUDE.md "Always Commit and Push" rule
