# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-13 (marathon session with Frank — largest single session of work on the platform to date)

**What shipped:** Three phases of work landed across ~20 commits.

**Phase 1 — Scoring plumbing (14-fix batch).** Fit Score always recalculates from live config. Orchestration method auto-derived from Pillar 1. Per-product ACV extrapolation (replaces flat multiplier). Org-type adoption rate overrides. Post-filters module (delivery platform removal, audience sanity, ACV caps). Wrapper org pipeline end-to-end. IV baseline recalibration. CF baseline recalibration. Badge naming enforcement (25+ deterministic overrides). Compliance grader sharpened. MFA penalty -15. Orphan Risk 3-tier spectrum. Pillar 2 extractor retry. Prospector search modal.

**Phase 2 — Validation-driven fixes.** Verdict grid 45-64 recalibrated (Assess First / Keep Watch / Deprioritize). Scoring dimension amber credit reduced to 1/3. Bar color 70% = amber (green starts above 70%). Typeahead deduplication. Badge evidence names underlying technologies. Context-aware absence badges (governance certs get gray Context). Product name truncation. BS/MS consolidation. ACV org-type motion labels (Student Training, Faculty Development for academics). ACV org-type hours overrides. ACV complexity-aware rate tier (Multi-VM → $45/hr). Search modal last stage 10s dwell. Hero ? icon alignment. Open source ACV adoption discount (25% of normal). Market Demand reframed as paid training demand.

**Phase 3 — Prospector features.** Deep Dive top product checkbox. Cost/time estimator (inline). Per-company timeouts (3 min discovery, 5 min Deep Dive). Parallel processing (3 concurrent). SSE timeout increased to 60 min with auto-reconnect. History page (/prospector/history). UX cleanup.

**Validated during session:** Trellix, Workday, CompTIA, EC-Council, ASU, MongoDB. Each validation drove targeted fixes. All fixes shipped.

**Documentation Job A — DONE.** Modal infrastructure built. Content dynamically sourced from scoring_config.py. WHY-WHAT-HOW per pillar, per dimension. Verdict grid. ACV explainer. All wired to ? icons.

Prior context: Pillar weights locked at 50/20/30. Technical Fit Multiplier retuned (≥60 full credit, 32-59 non-datacenter → 0.65). All 118 tests passing.

---

## Format

Three layers, in priority order:

1. **Start here** — the single first action of the next session
2. **Planned work** — sequenced items
3. **Big projects** — the major workstreams

Everything else is in `docs/roadmap.md`. Everything shipped is in `git log` and `docs/decision-log.md`.

---

## §1 — START HERE NEXT SESSION

**Fresh validation round — flush cache, run 7-10 companies through fresh discovery + Deep Dive.**

All fixes from the 2026-04-13 marathon session are in the code. Many were validated during the session but on data that preceded later fixes (open source ACV discount, Market Demand training-not-product, ACV complexity rate tier, academic motion labels). A clean validation with ALL fixes active will tell us if the platform is demo-ready.

| Company | Type | What to verify |
|---|---|---|
| **Trellix** | Cybersecurity software | ACV should be ~$1-2M (complexity rate $45/hr). IV should differentiate (not 97-100 for every product). Badge names clean. |
| **Workday** | SaaS ERP | Fit Score ~49. ACV rate $6/hr (cloud). Lab Access amber. Audience ~50K admins. Verdict = Keep Watch. |
| **MongoDB** | Open source database | ACV discount applied (25% adoption). Market Demand reflects paid training demand, not product popularity. |
| **CompTIA** | Industry Authority | Cert programs as products. No CertMaster in list. Underlying technologies in badge evidence. Compliance only on Security+/CySA+. |
| **EC-Council** | Cybersecurity Industry Authority | Same wrapper pattern. Underlying technologies in evidence. iLabs excluded. |
| **ASU** | Research University | Degree programs consolidated (BS/MS → one entry). Academic ACV labels (Student Training, Faculty Development). 90% adoption. |
| **Posit** | Small software company | Product count 3-5. ACV reasonable. |
| **Pluralsight** | Enterprise Learning Platform | Course categories as products. Platform features excluded. Light-touch scoring. |
| **Prospector batch** | 5-7 companies | Search modal with estimated time. Deep Dive checkbox. History page. Parallel processing. No timeout. |

**After validation:** If scores, ACV, badges, and verdicts look right across all company types, the platform is demo-ready.

### Known issues to fix during validation

**PL Provisioning badge sparsity.** Products scoring 30/35 on Provisioning sometimes show only 2 badges (Runs in VM + Pre-Instancing?). That's not enough to defend the score. If a product earns 30 points, the badges must explain WHY — Multi-VM Lab, Complex Topology, container viability, etc. The badge selector needs to emit more provisioning badges when the facts support them. Observed on Sage 50 and Sage 100.

**ACV end-user vs admin audience transparency.** Large companies like Sage serve millions of businesses, but the training population is administrators and accountants — not all end users. The ACV number may be correct for the admin population, but the seller needs to see WHY the ACV is modest for a large company. Consider a Market Demand badge like "Admin Training Focus" or "Niche Admin Audience" that explains the large user base doesn't translate to a large lab audience.

---

## §2 — PLANNED WORK

### 1. Prospector testing and validation

Run Prospector on a batch of 5-10 companies. Verify:
- Deep Dive checkbox works (top product scored, results sharpened)
- Cost/time estimator updates correctly
- Progress modal shows company names and estimated time
- No SSE timeout (auto-reconnect working)
- History page lists all researched companies
- Parallel processing reduces wall time
- Results table sorted by ACV, all columns populated

### 2. Documentation Job B — per-product report (doc icons)

Design conversation needed first. Three options on the table:
- Three-pillar summary modal
- Word doc preview
- Executive briefing

Frank's framing: "if somebody wants the Instructional Value report for a particular product" — suggests dimension-level drill-down. Modal vs separate tab — defer until content shape is clear.

### 3. Deployment — Render or Azure Web App

Decision needed from Frank's team. Frank won't demo on localhost.

Scope once decided: secrets loading, gunicorn entry point, persistent storage, auth decision (public URL + obscurity, or allowlist).

### 4. Designer — design + build

Biggest workstream. Existing design docs:
- `docs/Designer-Session-Prep.md`
- `docs/Designer-Session-Guide.md`

Read both before the design conversation. People → Purpose → Principles → Rubrics → UX.

---

## §3 — INFRASTRUCTURE + POLISH

| Item | When |
|---|---|
| **Parallel product scoring in Deep Dive** | Slot into next performance pass — run all products' extractors simultaneously instead of per-product rounds |
| **Skillable customer identification UX** | When an analyzed company is already a Skillable customer, show it. Source: CRM lookup / static config / HubSpot |
| **GP4 cleanup: centralize 8 dimension name constants** | Low priority — duplicated across pillar scorers and rubric_grader. Code quality, not a scoring bug. |

---

## §4 — DELIBERATELY DEFERRED

- **Auth** — tied to deployment decision
- **HubSpot write-back field mapping** — Stage 1 Company Records, Stage 2 Deal Records. Needs RevOps conversation.
- **Skillable customer identification source** — CRM / static config / HubSpot
- **Render vs Azure Web App** — Frank's team decision

---

## Working style reminders

- **Chunked responses, not walls of text.** Keep replies structured and terse.
- **Read Foundation docs before acting.** Three-pass startup sequence every session.
- **Layer discipline.** Intelligence logic → shared layer. Tool-specific → tool layer.
- **No hardcoded numbers outside scoring_config.py.** Pre-commit hook enforces this.
- **Commit + push after any code change.** Per CLAUDE.md rule.
- **Confirm alignment before acting on judgment calls.** Fix known broken immediately.
