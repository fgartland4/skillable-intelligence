# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-13 (extended validation + bug fix session with Frank. **Six workstreams + 14-fix batch + continued validation fixes.**)

**Workstream 1: Critical scoring plumbing fixes.** Bug A — `recompute_analysis` now always recalculates Fit Score from live config (never trusts cached `total_override`). Bug B — `orchestration_method` auto-derived from Pillar 1 primary fabric via Define-Once mapping in `pillar_1_scorer.py`. Fixes SaaS products defaulting to VM rate ($14/hr) instead of cloud ($6/hr) and ensures Technical Fit Multiplier correctly classifies non-datacenter products.

**Workstream 2: Researcher prompt sharpening.** Lab Access confidence — "partial" is the honest default for SaaS products unless specific user-provisioning endpoint documentation confirmed. Audience estimates — training population, not total user base (Workday HCM has 10M end users but ~50K admins who would take training). "Other" removed as valid category.

**Workstream 3: IV baseline recalibration.** All IV_CATEGORY_BASELINES lowered to create proper differentiation bands. Old baselines were too close to caps (Lab Versatility 93%, Mastery Stakes 88%). New baselines represent a WEAK implementation of each category (~55-70% of cap). Two strong findings needed to reach cap.

**Workstream 4: Badge naming enforcement.** Deterministic post-processing overrides in `badge_selector.py` for 25+ signal categories. "Content Team Named" → "Content Team", "ID IDs" → "IDs on Staff", "Published Course Calendar" → "ILT Calendar", CTF/SIEM/EDR/SOC/ILT added to ALL-CAPS acronyms.

**Workstream 5: Compliance grader sharpened.** Mastery Stakes `compliance_consequences` signal now has explicit "is_not_about" guidance — only fires when subject matter directly involves regulatory/audit/legal obligations. CompTIA A+ and Linux+ should no longer show compliance badges.

**Workstream 6: Wrapper organization pattern.** Universal logic for all non-software org types — the wrapper (cert, degree, course, practice area) stays as the product entry; new `underlying_technologies` field captures labable technologies inside. Discovery prompt rewritten with universal extraction rules. CertMaster/iLabs/LMS platforms excluded as delivery platforms, not products.

**14-fix batch (continued session).** Post-filters module, ACV per-product extrapolation, org-type adoption overrides, cert derivation constant, wrapper org pipeline, IV badge quality tightening, MFA penalty -15, Orphan Risk 3-tier spectrum, CF baseline recalibration, Pillar 2 extractor retry, Prospector search modal, SSE progress modal.

**Continued validation fixes (post-batch).** Verdict grid 45-64 recalibrated (Assess First / Keep Watch / Deprioritize). Scoring amber credit reduced to 1/3 for Scoring dimension (`SCORING_AMBER_CREDIT_FRACTION = 3`). Bar color threshold: 70% is amber, green starts above 70%. Typeahead deduplication. Badge evidence names underlying technologies. Context-aware absence badges (governance/leadership certs get gray Context, not red Blocker). Product name truncation with CSS ellipsis. BS/MS consolidation in discovery prompt. ACV org-type motion labels (Student Training, Faculty Development, etc.). ACV org-type hours overrides (academic 8 hrs). ACV complexity-aware rate tier (multi-VM/complex topology -> Large VM $45/hr). Search modal last stage 10s dwell. Hero ? icon alignment.

**Validation tested so far:** Trellix, Workday, EC-Council, ASU. Bugs found during validation drove the continued fixes above (verdict labels too optimistic at 45-64, amber credit too generous on Scoring dimension, bar colors off at 70% boundary, badge evidence missing underlying tech names for wrapper orgs).

Prior context: Pillar weights locked at 50/20/30 (2026-04-12). Technical Fit Multiplier retuned — ≥60 full credit, 32-59 non-datacenter → 0.65 (2026-04-12). All 118 tests passing.

---

## Format

Three layers, in priority order:

1. **Start here** — the single first action of the next session
2. **Live bugs** — small, fix-when-you-touch-the-area items
3. **Big projects** — the sequenced workstreams

Everything else is in `docs/roadmap.md`. Everything shipped is in `git log` and `docs/decision-log.md`.

---

## §1 — START HERE NEXT SESSION

**Validate with fresh data — run 5-10 companies through fresh discovery + Deep Dive.**

All scoring, researcher, and badge fixes from 2026-04-12/13 are in the code but need validation against real data. Flush cache and run:

| Company | Why this one | What to verify |
|---|---|---|
| **Trellix** | Anchor company, cybersecurity software | IV baselines recalibrated — should score ~75-85 IV instead of 97-100. Fit Score should reflect 50/20/30 weights. Badge names clean. |
| **Workday** | SaaS product, non-datacenter | Orchestration method → "Custom API" (cloud rate $6/hr). Fit Score ~49 (not 68). Lab Access amber (not green). Audience ~50K admins (not 10M users). |
| **CompTIA** | Industry Authority, wrapper org | Wrapper pattern: cert programs as products, underlying technologies in evidence. CertMaster excluded. No "Other" category. Compliance badges only on Security+/CySA+, NOT on A+/Linux+. |
| **Posit** | Small software company | Product count 3-5 (not 48). Popularity ranking correct. |
| **Cisco** | Large software company | Product count 20-30. Interstitial grouping by category. |
| **Arizona State** or **GCU** | University | Degree programs as products. Underlying technologies in evidence. Academic vocabulary. |
| **Deloitte** or **Accenture** | GSI | Practice areas as products. Underlying technologies extracted. |

**Why this first:** Every fix ships blind without validation. The validation round tells us what works and what still needs tuning. Each finding drives a targeted fix.

---

## §2 — LIVE BUGS + OPEN ITEMS

### §2a — Items from prior sessions that may self-resolve with fresh data

| Bug | Status | Expected outcome |
|---|---|---|
| **Bug 2 — IV Market Demand 7/20 with four green labels** (Trellix) | Investigate on fresh run | May resolve with IV baseline recalibration |
| **Bug 4 — HIGH FIT · LOW ACV on highest-scoring product** | Probably correct math | Verify and close |
| **Bug 12 — Audience populations flipped / use single values** | Partially fixed | Researcher prompt sharpened; verify on fresh data |
| **Bug 13 — Certification audience = 5% of total** | Still open | Deterministic derivation in `acv_calculator.py` still pending |
| **Bug 18 — MFA Required penalty too soft** | Investigate on fresh run | Check Lab Access scores on products with MFA |
| **Bug 19 — Orphan Risk penalty too soft** | Investigate on fresh run | Check Teardown scores on products with orphan risk |
| **Bug 20 — Workday PL verification** | Should resolve | Orchestration method fix + Lab Access confidence fix |
| **Bug 21 — Workday Training Commitment 25/25 too high** | Investigate on fresh run | CF baselines may need recalibration similar to IV |

### §2b — Known issues from 2026-04-13 session

| Issue | Status | Fix when |
|---|---|---|
| **underlying_technologies not yet wired into Pillar 1 scoring** | Discovery prompt written, badge evidence now names underlying technologies | Partial — evidence layer done, scoring layer wiring still needed during next validation pass |
| **CF baselines may need similar recalibration to IV** | CF baselines recalibrated in 14-fix batch | Resolved — verify on fresh data |
| **Pillar 2 extractor reliability** — intermittent empty mastery_stakes/lab_versatility drawers | Extractor retry logic added in 14-fix batch | Verify on fresh data — retry should handle transient failures |

---

## §3 — BIG PROJECTS (SEQUENCED)

In priority order — do not parallelize. Each one has its own design conversation before build.

### 1. Documentation Job A — content polish on the ? modals

**Already built.** The info modal infrastructure is shipped: `MODAL_CONTENT` in `scoring_config.py` builds WHY-WHAT-HOW content dynamically from pillar/dimension config. The `openInfoModal()` JS in `full_analysis.html` renders it. ? icons are wired on every Pillar card, Fit Score, ACV, and Seller Briefcase.

**What's left:** Content polish — verify the seller-facing copy reads well, tone is right, per-dimension WHY text is sharp enough for a demo. Frank won't demo without reviewing the modal content. This is a review + edit session, not a build.

### 2. Deployment — Render or Azure Web App

Prerequisite: Job A shipped. Decision needed from Frank's team.

### 3. Documentation Job B — per-product report (doc icons)

Design conversation needed first: what does a per-product report contain?

### 4. Prospector — enhancements (design completed 2026-04-13)

Three new features agreed with Frank 2026-04-13:

**Feature A — "Deep Dive top product" checkbox.**
A checkbox on the Prospector input form: "Perform Deep Dive on top product for each company." When checked, after discovery, automatically selects the top product (highest popularity ranking — same sort as the product chooser) and runs a full Deep Dive. Prospector results table shows sharpened Fit Score and ACV instead of rough discovery estimates. GP5: intelligence compounds — the Deep Dive data is immediately available in Inspector.

**Feature B — Cost and time estimator.**
A live counter in a right-side column next to the paste/upload input area. Updates as the user adds companies. Shows:
- Estimated API cost (mid-to-mid-high estimate, never low)
- Estimated wall time (fair estimate, close to actual)
- Updates when "Deep Dive top product" is checked (adds ~$1.50-2.50 per company + ~3-5 min per company)

Layout: narrow the paste list and upload list areas slightly to create space for the estimator column on the right. Same overall page width, just redistributed.

Cost estimate basis: discovery ~$0.15-0.25 per company (one large Claude call). Deep Dive adds ~$1.50-2.50 per product (research + grading + briefcase). Use mid-tier model pricing.

**Feature C — Per-company timeouts + parallel processing.**
- Per-company timeout: 3 minutes for discovery, 5 minutes for Deep Dive
- On timeout: log the error, skip to next company, show which ones failed in results so user can re-run
- Run companies in parallel where possible to reduce wall time (same API cost, just faster)
- Products within a Deep Dive run their extractors in parallel (already partially implemented — extend to score all products simultaneously)

**Implementation notes:**
- SSE progress modal already shipped (Fix 14 from this session)
- Parallel processing: extend the ThreadPoolExecutor in intelligence.score() to run all products' extractors simultaneously instead of per-product rounds
- Timeouts: wrap each company's discovery/scoring in a timeout context manager
- Cost estimator: new Jinja template element + lightweight JS calculator, no backend needed (counts × rates)

### 5. Designer — design + build

Biggest workstream. Read `docs/Designer-Session-Prep.md` and `docs/Designer-Session-Guide.md` before design conversation.

---

## §4 — INFRASTRUCTURE + POLISH (SLOT IN WHERE IT FITS)

| Item | Slot into | Why |
|---|---|---|
| **Standard Search Modal** — full contract + progress.py publisher | Before Prospector build | Drift prevention |
| **Skillable customer identification UX** | Job A or Job B sessions | Demo polish |

---

## §5 — DELIBERATELY DEFERRED (DECISIONS NEEDED BEFORE WORK)

See `docs/roadmap.md §I` for the full decisions-needed list.

---

## Working style reminders

- **Chunked responses, not walls of text.** Keep replies structured and terse.
- **Read Foundation docs before acting.** Three-pass startup sequence every session.
- **Layer discipline.** Intelligence logic → shared layer. Tool-specific → tool layer.
- **No hardcoded numbers outside scoring_config.py.** Pre-commit hook enforces this.
- **Commit + push after any code change.** Per CLAUDE.md rule.
- **Confirm alignment before acting on judgment calls.** Fix known broken immediately.
