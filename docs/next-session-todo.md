# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-12 (extended requirements + coding session with Frank. **Three workstreams landed.**

**Workstream 1: Researcher/discovery sharpening.** Product definition locked (what IS vs IS NOT a product), discovery data shape defined (three tiers: per-product light, per-product hints, per-company once), product relationships vocabulary locked (flagship/satellite/standalone), discovery tier labels renamed Promising/Potential/Uncertain/Unlikely, product chooser redesign agreed (popularity sort, labability as badge, three-column layout, interstitial only when 15-20+ products), unified search field (single input handles company names, product names, disambiguation, former names), company classification derived from products (`company_category`) separate from Pillar 3 baseline (`org_type`), "delivery partners" replaces "delivery channels," Seller Briefcase clarified Key Technical Questions vs Market Demand evidence, ACV estimation discipline changed from ranges to single numbers ("~14M" not "2,000-40,000").

**Workstream 2: Org-type models + strategic decisions.** Pillar weights locked at 50/20/30 (from 40/30/30) after running math on Cohesity/Trellix/Workday/Diligent. Company badge pattern locked: [Category] + [Org Type] (e.g. "Cybersecurity Software," "Cybersecurity Industry Authority"). Full org-type models written for: Software Companies (anchor/baseline), Universities (6 academic badge types: Engineering College, Research University, Liberal Arts College, Career & Technology College, Community College, K-12 School District), GSIs/VARs/Distributors, Industry Authorities, Enterprise Learning Platforms, ILT Training Organizations, Content Development Firms (partnership only, no Deep Dive), LMS/Learning Platforms (hybrid: product + partnership). ACV funnel clarified as universal — lab hours consumed is always the unit. Mark Mangelson's (CRO) labability prompt mapped to our framework — all 9 categories covered, product-level precision added. Prospector design completed — batch discovery, results table sorted by ACV, CSV export, partnership flags, intelligence sharpening from cached Deep Dives.

**Workstream 3: Code changes shipped.** Pillar weights changed to 50/20/30 in `scoring_config.py` + SCORING_LOGIC_VERSION bumped. Discovery tier labels changed to Promising/Potential/Uncertain/Unlikely across `core.py`, `intelligence.py`, `scoring_config.py`, `product_selection.html`, `_theme.html`, and tests. All 116 tests passing.

**Code safeguard rules agreed:** typed discovery schema, template never computes, classification is derived never assigned, old cache loads clean, one commit one concern. Discovery prompt v2 drafted (`backend/prompts/discovery_v2_draft.txt`) — ready to replace old prompt and wire parsing.

Prior context: Phase 1 live-bug batch shipped 2026-04-08, Phase 2 bugs still queued in §2a.)

---

## Format

Three layers, in priority order:

1. **Start here** — the single first action of the next session
2. **Live bugs** — small, fix-when-you-touch-the-area items
3. **Big projects** — the sequenced workstreams

Everything else is in `docs/roadmap.md`. Everything shipped is in `git log` and `docs/decision-log.md`.

---

## §1 — START HERE NEXT SESSION

**Implement researcher/discovery sharpening — the upstream fix.**

Decisions are locked and written into Platform-Foundation.md (see "The Center of Everything: Products" and "Discovery Data Shape" sections). Now build it.

**Step 1: Rewrite the discovery prompt** (`backend/prompts/discovery.txt`)
- Replace "aim for 40-60 products" with the product definition filter
- Add the three-tier data shape (per-product light, per-product hints, per-company once)
- Add product relationship field (flagship/satellite/standalone)
- Add estimated user base + evidence + confidence fields
- Add complexity signals, target personas, api_surface, cert_inclusion
- Add per-company fields (training programs, sales channel, atp_program, delivery partners, events, partnership pattern, engagement model, content team signals, lab platform)

**Step 2: Update discovery processing code**
- `backend/intelligence.py` discover() — parse and store the enriched discovery data
- `backend/core.py` — rename discovery tier labels (Promising/Potential/Uncertain/Unlikely), update thresholds
- `backend/scoring_config.py` — update tier label constants
- Company classification — derive from discovered product categories

**Step 3: Update product chooser UX**
- Sort by estimated user base (popularity), not labability tier
- Labability tier as badge in right column
- Three-column layout: product info | deployment | labability judgment
- Interstitial only when product count exceeds ~15-20

**Step 4: Test with Posit, Trellix, Cisco, Commvault, Sage**
- Verify product counts are sane (Posit: 3-5, Trellix: ~8, Cisco: 20-30)
- Verify flagship/satellite relationships are correct
- Verify popularity ranking puts the right products on top

**Why this first:** Bad product identification is the root cause of the Trellix 46-product bloat (§2b), the Posit 48-product bloat, and the ACV extrapolation inflation. Fixing the researcher is upstream of everything — scoring tuning, ACV accuracy, product chooser UX, and Prospector data quality.

**Still queued — Documentation Job A** (the ? modal content design conversation). Moved to §3 Big Projects. Still important — Frank won't demo without it — but the researcher fix is upstream and improves the data the documentation will explain.

**Open threads from 2026-04-12 session (continue if time permits):**
- ~~How enriched discovery data serves Prospector~~ — **RESOLVED.** Prospector design conversation completed. Full spec in Platform-Foundation.md → Prospector UX. Same discovery data, batch processing, results table sorted by ACV potential.
- ACV extrapolation — does the enriched discovery data change how we estimate company-level ACV? (The enriched discovery with real product counts and user bases should make the extrapolation dramatically more accurate than the old proportional scaling.)

---

## §2 — LIVE BUGS + PHASE 2 QUEUE (FROM 2026-04-08 LATE SESSION)

Phase 1 of the live-bug batch shipped in the commit that landed this doc update. Phase 2 is the queue for next session — investigate-first items, tuning decisions, and the original three deferred items that are still open.

### §2a — Phase 2 queue (investigate and/or fix next session)

| Bug | Kind | Why not in Phase 1 |
|---|---|---|
| **Bug 2 — IV Market Demand shows 7/20 with four green labels** (Trellix Advanced Threat Landscape Analysis System) | Investigate-first | Need to pull the analysis JSON and look at graded signals vs scored signals. Likely outcomes: (a) math correct + small install base dragging it down legitimately, (b) signals should be amber not green, (c) baseline/weights wrong. Report findings before any code change. |
| **Bug 4 — HIGH FIT · LOW ACV verdict on highest-scoring product** (Trellix Endpoint Security, confirmed again on Cohesity DataHawk) | Probably correct math — verify and close | Cohesity screenshot confirmed the pattern: product with high individual Fit Score but low individual ACV genuinely IS `HIGH FIT · LOW ACV`. Expected to close without a code change after a quick verification pass. |
| **Bug 12 — Audience populations flipped / use single values for known counts** (Cohesity: 13,000 customers + 7,500 employees, but Employee Training audience showed 15k-35k range) | Researcher prompt tightening | Prompt needs explicit guidance: "when employee count is known, use single value not range; customer count and employee count must not be swapped." |
| **Bug 13 — Certification audience = 5% of total (customers + partners + employees)** | Deterministic math in `acv_calculator.py` | Derive certification audience from the other motion audiences rather than asking the AI to estimate. Python computes it, AI doesn't touch it. |
| **Bug 18 — Increase MFA Required penalty weight** (Cohesity DataHawk: dropped Lab Access to 14/25 which Frank considers too soft) | Scoring config tuning | Investigate current penalty, propose new value, Frank decides. Look in Lab Access signal weights. |
| **Bug 19 — Increase Orphan Risk penalty weight** (Cohesity DataHawk: dropped Teardown to 20/25) | Scoring config tuning | Same pattern as Bug 18 — investigate and propose. Look in Teardown signal weights. |
| **Bug 20 — Workday Product Labability needs verification** (Workday HCM shows PL 45: Provisioning 11/35, Lab Access 19/25, Scoring 9/15, Teardown 6/25) | Investigate-first | Frank's gut says something's off. Pull the Workday analysis JSON, walk each dimension's credited signals against the scoring config, and either confirm the score is correct or flag what's miscounted. Workday HCM is a well-known product (SaaS, Sandbox API, Custom Cloud) so there's a lot of ground truth to compare against. |
| **Bug 21 — Workday Training Commitment 25/25 may be too high** (Workday is notoriously hard to do business with — enterprise procurement friction, long sales cycles, partner lock-in) | Investigate-first | Frank suspects the Training Commitment dimension isn't capturing the "friction to partner with this vendor" signal strongly enough. Look at the graded signals for Training Commitment on Workday. Is the maximum score a fair read? If not, what signal / penalty is missing? Likely pairs with a scoring config adjustment but depends on the investigation. |
| **Bug 22 — Weak Product Labability should drag Fit Score down harder** (Workday HCM: PL 45/100 — amber — but overall Fit Score 74 = HIGH POTENTIAL) | Tuning — requires the 50/20/30 pillar weight decision below first | Technical Fit Multiplier exists but may not be biting hard enough for mid-range PL scores (PL 19-49 band). This item is downstream of the bigger strategic question: should the pillar weights be rebalanced from 40/30/30 to 50/20/30? See §2c below. |

### §2c — ~~Big strategic question raised during Workday pass~~ DECIDED 2026-04-12

**Pillar weight rebalance: 40/30/30 → 50/20/30 — LOCKED.** Ran the math on Cohesity (PL 95), Trellix TIE (PL 86), Workday (PL 22), and Diligent (PL 25). Results: strong-PL companies unchanged or slightly up; weak-PL companies moved down 4–6 points. Workday dropped from 54 to 48 — honest. No company that should be strong got hurt. Product Labability is the gatekeeper; the math now matches the philosophy. Both Foundation docs updated. Code change: `scoring_config.py` pillar weights — one line, propagates everywhere.

---

### §2b — Still-open items from the original deferred list

| Bug | Investigate when |
|---|---|
| **Discovery bloat + family picker under-grouping** — Trellix returned ~46-49 products vs ~22 real; Posit returned 48 products vs ~5 real. Two stacked bugs (upstream over-extraction + coarse grouping). **Root cause identified 2026-04-12: researcher lacks a product definition filter.** Fix is §1 Step 1 (discovery prompt rewrite). Also causes Bug 3 (ACV total variance on refresh — downstream symptom of inflated product count in the extrapolation denominator). | **Resolved by §1 researcher sharpening work.** |
| **Pillar 2 extractor reliability** — intermittent empty `mastery_stakes` / `lab_versatility` / `market_demand` drawers even on products where facts clearly exist. Cross-pillar grader safety net in `rubric_grader.py::_product_shape_context` keeps grades flowing in the meantime. Investigate-first. | When touching Pillar 2 researcher / grader work. |
| **Bug 14 — Researcher missing flagship events** (Cohesity Catalyst was not captured) | **Resolved by §1 Step 1** — per-company `events` field is now part of the discovery data shape. Researcher explicitly searches for flagship annual event / user conference. |

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

### 4. Prospector — build (design conversation completed 2026-04-12)

**Design is done.** Full Prospector UX spec written into `Platform-Foundation.md → Prospector UX`. No legacy code or thinking — 100% new design based on the enriched discovery data shape.

**Scope:**
- **Rewrite, not port.** Zero legacy code. CLAUDE.md Legacy Boundary rule applies.
- Input: paste company names OR upload CSV. Unified search field with disambiguation.
- Processing: batch discovery on all input companies using the standard three-tier discovery data shape. All results cached for Inspector Deep Dives.
- Output: results table sorted by ACV potential — columns: Rank, Company + badge, Estimated ACV, Top Product, Why, Promising/Potential/Uncertain/Unlikely product counts, Lab Platform, Key Signal.
- CSV export with "Promising Products" / "Potential Products" column headers for spreadsheet context.
- Intelligence sharpens automatically — companies with existing Deep Dives show scored data instead of discovery estimates.
- Partnership flags: Content Development firms show as partners (no Deep Dive), LMS companies show as hybrid (product + distribution partner).
- Future: HubSpot authenticated write-back (Stage 1 company records, Stage 2 deal records). RevOps conversation needed for field mapping.

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
