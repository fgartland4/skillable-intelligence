# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-08 (late session, Phase 1 live-bug batch shipped. Earlier in session: `dd62c87` viable_fabrics + No Scoring Methods canonical label, `a296e29` researcher SaaS/cloud contradiction fix, `9682ba2` docs audit + refresh. This update adds the Phase 1 live-bug commit which resolved 10 small items from the late-session testing round: Simulation override normalized to 12/12/0/12 with gray bars across all three symmetric dims, briefcase markdown stripped, ACV table separator + wider columns + ANNUAL ACV POTENTIAL rename + Use Case column font uniformity, "Hands On Learning" renamed to "Hands On", "Instructor Authors Dual" renamed to "Dual Instructors/Authors", "Customer Enablement Team" label now pulls the vendor's actual named program from `customer_enablement_team_name` fact (e.g. "Cohesity Academy"), and product chooser link placement standardized above the Deep Dive button. Phase 2 queue in §2a is what to pick up next session. Read this doc first, then `docs/roadmap.md` for the long arc.)

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

## §2 — LIVE BUGS + PHASE 2 QUEUE (FROM 2026-04-08 LATE SESSION)

Phase 1 of the live-bug batch shipped in the commit that landed this doc update. Phase 2 is the queue for next session — investigate-first items, tuning decisions, and the original three deferred items that are still open.

### §2a — Phase 2 queue (investigate and/or fix next session)

| Bug | Kind | Why not in Phase 1 |
|---|---|---|
| **Bug 2 — IV Market Demand shows 7/20 with four green badges** (Trellix Advanced Threat Landscape Analysis System) | Investigate-first | Need to pull the analysis JSON and look at graded signals vs scored signals. Likely outcomes: (a) math correct + small install base dragging it down legitimately, (b) signals should be amber not green, (c) baseline/weights wrong. Report findings before any code change. |
| **Bug 4 — HIGH FIT · LOW ACV verdict on highest-scoring product** (Trellix Endpoint Security, confirmed again on Cohesity DataHawk) | Probably correct math — verify and close | Cohesity screenshot confirmed the pattern: product with high individual Fit Score but low individual ACV genuinely IS `HIGH FIT · LOW ACV`. Expected to close without a code change after a quick verification pass. |
| **Bug 12 — Audience populations flipped / use single values for known counts** (Cohesity: 13,000 customers + 7,500 employees, but Employee Training audience showed 15k-35k range) | Researcher prompt tightening | Prompt needs explicit guidance: "when employee count is known, use single value not range; customer count and employee count must not be swapped." |
| **Bug 13 — Certification audience = 5% of total (customers + partners + employees)** | Deterministic math in `acv_calculator.py` | Derive certification audience from the other motion audiences rather than asking the AI to estimate. Python computes it, AI doesn't touch it. |
| **Bug 18 — Increase MFA Required penalty weight** (Cohesity DataHawk: dropped Lab Access to 14/25 which Frank considers too soft) | Scoring config tuning | Investigate current penalty, propose new value, Frank decides. Look in Lab Access signal weights. |
| **Bug 19 — Increase Orphan Risk penalty weight** (Cohesity DataHawk: dropped Teardown to 20/25) | Scoring config tuning | Same pattern as Bug 18 — investigate and propose. Look in Teardown signal weights. |

### §2b — Still-open items from the original deferred list

| Bug | Investigate when |
|---|---|
| **Discovery bloat + family picker under-grouping** — Trellix returned ~46-49 products vs ~22 real; then family picker collapsed 42 under one "Cybersecurity" header making it useless as a filter. Two stacked bugs (upstream over-extraction + coarse grouping), one investigation. Test case: Trellix. Also causes Bug 3 (ACV total variance on refresh — downstream symptom of the same root cause). | When touching discovery, or as a dedicated pass if external testers hit it first. |
| **Pillar 2 extractor reliability** — intermittent empty `mastery_stakes` / `lab_versatility` / `market_demand` drawers even on products where facts clearly exist. Cross-pillar grader safety net in `rubric_grader.py::_product_shape_context` keeps grades flowing in the meantime. Investigate-first. | When touching Pillar 2 researcher / grader work. |
| **Bug 14 — Researcher missing flagship events** (Cohesity Catalyst was not captured) | Researcher prompt tightening — explicit guidance to search for the vendor's flagship annual event / user conference. |

**Batch bugs during documentation work.** Frank queues small bugs during Job A / Job B sessions — pause at natural breakpoints to batch them rather than context-switch mid-design-conversation. Pattern worked well in the 2026-04-08 session that shipped 10 quick fixes as a single Phase 1 commit.

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
