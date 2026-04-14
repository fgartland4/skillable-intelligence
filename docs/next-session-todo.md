# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-13 (three marathon sessions — massive day. ADR, Prospector UX batch, background batch processing, ACV guardrails R1-R5, scoring fixes 1-4, exhaustive audit, Prospector results-first redesign, unified ACV model design for all 6 org types, and implementation batch in progress)

**IMPLEMENTATION BATCH IN PROGRESS (if session ended mid-batch):**
All 6 org types locked in `docs/unified-acv-model.md`. Implementation order:
1. Rewrite Platform-Foundation.md ACV section (best current thinking)
2. Rewrite B&S Reference ACV operational detail
3. Implement in scoring_config.py (constants)
4. Update acv_calculator.py + app.py (code)
5. Server-side cache for Prospector company list (performance)
6. Merge four input pages into one tabbed page (UX)
7. Consolidate field mapper into Configure HubSpot tab (+/- tree)
8. Deep Dive indicator + in-modal docs on Prospector
9. Run rescore.py on all cached analyses
10. Verify: HashiCorp cache sharing, ACV spot checks against benchmarks

Additional Prospector UX items agreed:
- "Configure Integration" → "Configure HubSpot" everywhere
- Input pages merge into one tabbed page with deep-link params (/prospector/input?tab=upload)
- Field mapper consolidated into Configure HubSpot tab with +/- collapsible tree
- ACV label: "Discovery & Deep Dive" not "Deep Dive only"
- Prospector ? modal documentation content needed

**What shipped in session 2 (2026-04-13 afternoon/evening):**

**ADR + Auth Design:**
- ADR-0000 Solution Overview written and sent to engineering team (`docs/adr/adr-0000-solution-overview.md`)
- RBAC refined from 12 roles → 7 roles with 4 boundary lines
- New role: Skillable Capabilities Editor (Sales Engineering + Product — gates knowledge files)
- Customer product visibility scoping documented (pre-release products in Designer)
- New standalone "Authentication and Access Control" section in Platform-Foundation.md
- ADR references Platform-Foundation.md as single source of truth for auth (Define-Once)

**Prospector UX Batch (P1–P11):**
- P1: "How it works" collapsed to separate inline line
- P2: "View Researched Companies" as button, right-aligned
- P3: Estimate font matches timer on progress modal
- P4: TIME_PER_DISCOVERY bumped to 150s (Cisco took 189s at 75s estimate)
- P5: Full-page results with truncation, tooltips, cert/sales columns
- P6: Discovery ACV — company-wide dollar estimate summed across all products with tiered user base caps
- P7: Post-run redirects to results page
- P8: Two-tab toggle: "This Batch (N)" / "All Companies (N)"
- P9: Export CSV per active tab + disabled "Send to HubSpot" with tooltip
- P10: Checkbox per row → "Run Deep Dive" button (single-select, moved to far left)
- P11: ? icon placeholder on results page

**Prospector Background Batch Processing (PB1–PB6):**
- Batches run in background — no more app lockout during batch runs
- Batch Status Panel on Prospector home (status dot, description, started, progress, est. remaining, actions)
- Submit returns JSON, adds row to panel, connects SSE — no page redirect
- Cancel endpoint for running batches
- Page reload resilience — reconnects SSE for running batches
- Full spec saved to `docs/prospector-background-batch-spec.md`

**Additional fixes:**
- Discovery timeout bumped 180→300s, Deep Dive 300→420s
- Dedup: 51 discovery files → 43 unique companies (normalized names catch Cisco/Cisco Systems, VMware variants)
- Badge display fix: underscore→hyphen CSS class mapping
- ACV cap at $5M + tiered user base caps for inflated numbers
- Cert column mapped to product-level data (was reading empty company signals)
- Export filenames: `prospector-YYYY-MM-DD-batch-{id}.csv` / `prospector-YYYY-MM-DD-all.csv`
- "Estimates refreshed [date]" line with ? icon tooltip explaining zero-cost refresh
- Company column widened + badge wrapping fix
- Back to Prospector link moved above buttons
- HubSpot button visibility improved

**Roadmap rewritten** as single prioritized list (was scattered across 3 files). `next-session-todo.md` trimmed to point at `docs/roadmap.md` for everything beyond "start here."

**Discovery-level ACV model documented** in Platform-Foundation.md → "Discovery-Level ACV Estimation" section.

**What shipped:** Three phases of work landed across ~20 commits.

**Phase 1 — Scoring plumbing (14-fix batch).** Fit Score always recalculates from live config. Orchestration method auto-derived from Pillar 1. Per-product ACV extrapolation (replaces flat multiplier). Org-type adoption rate overrides. Post-filters module (delivery platform removal, audience sanity, ACV caps). Wrapper org pipeline end-to-end. IV baseline recalibration. CF baseline recalibration. Badge naming enforcement (25+ deterministic overrides). Compliance grader sharpened. MFA penalty -15. Orphan Risk 3-tier spectrum. Pillar 2 extractor retry. Prospector search modal.

**Phase 2 — Validation-driven fixes.** Verdict grid 45-64 recalibrated (Assess First / Keep Watch / Deprioritize). Scoring dimension amber credit reduced to 1/3. Bar color 70% = amber (green starts above 70%). Typeahead deduplication. Badge evidence names underlying technologies. Context-aware absence badges (governance certs get gray Context). Product name truncation. BS/MS consolidation. ACV org-type motion labels (Student Training, Faculty Development for academics). ACV org-type hours overrides. ACV complexity-aware rate tier (Multi-VM → $45/hr). Search modal last stage 10s dwell. Hero ? icon alignment. Open source ACV adoption discount (25% of normal). Market Demand reframed as paid training demand.

**Phase 3 — Prospector features.** Deep Dive top product checkbox. Cost/time estimator (inline). Per-company timeouts (3 min discovery, 5 min Deep Dive). Parallel processing (3 concurrent). SSE timeout increased to 60 min with auto-reconnect. History page (/prospector/history). UX cleanup.

**Validated during session:** Trellix, Workday, CompTIA, EC-Council, ASU, MongoDB. Each validation drove targeted fixes. All fixes shipped.

**Documentation Job A — DONE.** Modal infrastructure built. Content dynamically sourced from scoring_config.py. WHY-WHAT-HOW per pillar, per dimension. Verdict grid. ACV explainer. All wired to ? icons.

Prior context: Pillar weights locked at 50/20/30. Technical Fit Multiplier retuned (≥60 full credit, 32-59 non-datacenter → 0.65). All 118 tests passing.

---

## Format

This file names the **first action** of the next session and provides focused context for that action. The **complete prioritized list** of everything — active, backlog, decisions needed, and done — lives in `docs/roadmap.md`. That is the single source of truth for priorities. This file points there for everything beyond "start here."

---

## §1 — START HERE NEXT SESSION

**Fresh validation round — flush cache, run 7-10 companies through fresh discovery + Deep Dive.**

All fixes from the 2026-04-13 marathon session are in the code. Many were validated during the session but on data that preceded later fixes (open source ACV discount, Market Demand training-not-product, ACV complexity rate tier, academic motion labels). A clean validation with ALL fixes active will tell us if the platform is demo-ready.

**After validation:** If scores, ACV, badges, and verdicts look right across all company types, the platform is demo-ready.

### Validation Batch A — Per-Company Deep Dive Checks

| # | Company | Type | What to verify | Status |
|---|---|---|---|---|
| **A1** | **Cisco** | Enterprise Software | See Cisco-specific findings below. ACV motions populating per product. IV differentiation across products. Events captured. | ☐ |
| **A2** | **Trellix** | Cybersecurity software | ACV ~$1-2M (complexity rate $45/hr). IV should differentiate (not 97-100 for every product). Badge names clean. | ☐ |
| **A3** | **Workday** | SaaS ERP | Fit Score ~49. ACV rate $6/hr (cloud). Lab Access amber. Audience ~50K admins. Verdict = Keep Watch. | ☐ |
| **A4** | **MongoDB** | Open source database | ACV discount applied (25% adoption). Market Demand reflects paid training demand, not product popularity. | ☐ |
| **A5** | **CompTIA** | Industry Authority | Cert programs as products. No CertMaster in list. Underlying technologies in badge evidence. Compliance only on Security+/CySA+. | ☐ |
| **A6** | **EC-Council** | Cybersecurity Industry Authority | Same wrapper pattern. Underlying technologies in evidence. iLabs excluded. | ☐ |
| **A7** | **ASU** | Research University | Degree programs consolidated (BS/MS → one entry). Academic ACV labels (Student Training, Faculty Development). 90% adoption. | ☐ |
| **A8** | **Posit** | Small software company | Product count 3-5. ACV reasonable. | ☐ |
| **A9** | **Pluralsight** | Enterprise Learning Platform | Course categories as products. Platform features excluded. Light-touch scoring. | ☐ |
| **A10** | **Accenture** | Global Systems Integrator | ACV should reflect Accenture's practice headcount, not underlying tech's global audience. R1 wrapper org cap applied. Udacity should appear as a product (acquired 2024). | ☐ |
| **A11** | **Google Cloud** | Enterprise Software | PL Provisioning should drop (Sandbox API amber for GCP). CF should show DIY lab amber (Qwiklabs). IV should differentiate across products (strong signal cap). | ☐ |

### Validation Batch B — Prospector UX Checks (shipped 2026-04-13)

| # | What to verify | Status |
|---|---|---|
| **B1** | **Home page layout** — "How it works" is inline phrase, not green box. "View Researched Companies" is a button, right-aligned next to description. | ☐ |
| **B2** | **Time estimates** — estimate font matches timer on progress modal. Estimated time for 1 company is ~3 min, not ~1 min. | ☐ |
| **B3** | **Post-run redirect** — after batch completes, lands on `/prospector/results/<batch_id>`, not inline below the form. | ☐ |
| **B4** | **Results page tabs** — "This Batch (N)" active after a run. "All Companies (N)" active when navigating from button. Switching tabs works. | ☐ |
| **B5** | **Results table** — single-row per company. Long fields truncated with `...` and tooltip on hover. Cert Program and Sales Channel columns populated. | ☐ |
| **B6** | **Discovery ACV** — shows dollar estimate (`~$448k` for Cisco, not `~2M users`). Estimates in the right neighborhood. | ☐ |
| **B7** | **"Estimates refreshed" line** — shows today's date. ? icon tooltip explains zero-cost refresh. | ☐ |
| **B8** | **Export CSV** — works on both tabs (batch export + export-all). File downloads correctly. | ☐ |
| **B9** | **"Send to HubSpot"** — disabled with "Coming Soon" tooltip. Not clickable. | ☐ |
| **B10** | **Checkbox → Run Deep Dive** — selecting a row shows the button. Only one checkbox at a time. Links to product selection for that company. | ☐ |
| **B11** | **Prospector batch** — run 5-7 companies. No timeout. Progress modal shows estimated time. Parallel processing reduces wall time. | ☐ |

### Validation Batch C — Known Issues to Fix During Validation

| # | Issue | What to look for | Status |
|---|---|---|---|
| **C1** | **PL Provisioning badge sparsity** | Products scoring 30/35 showing only 2 badges (Runs in VM + Pre-Instancing?). Badge selector needs to emit more when facts support them. Observed on Sage 50 and Sage 100. | ☐ |
| **C2** | **ACV audience transparency** | Large companies with small training populations — ACV is modest but no badge explains why. Consider "Admin Training Focus" or "Niche Admin Audience" badge. | ☐ |
| **C3** | **Cisco: ACV motions empty** | Customer Training audience showing ~0 for first two products. `acv_motions` dict is `{}`. Investigate `acv_calculator.py` output path. | ☐ |
| **C4** | **Cisco: Audiences not differentiating per product** | Secure Firewall (~400K) and Catalyst Wireless (~150K) should have different customer training audiences. All products sharing same numbers. | ☐ |
| **C5** | **Cisco: 100/100 IV on all four products** | Cybersecurity baselines + strong signals overflow every cap. Fixed: strong signal cap at 2 per dimension (Fix 4). Re-verify after re-score. | ☐ |
| **C6** | **Accenture: ACV Customer Training inflated** | AWS Practice showed ~4M audience (AWS global) instead of ~60K (Accenture's practice). Fixed: R1 wrapper org cap + R2 prompt fix. Re-verify after fresh Deep Dive. | ☐ |
| **C7** | **Accenture: Cert audience inflated** | ~400K cert candidates (AWS global) instead of Accenture's own. Fixed: R4 cert cap at 10% of install_base. Re-verify. | ☐ |
| **C8** | **Accenture: Udacity missing** | Acquired by Accenture in 2024. Should appear as a product. Researcher didn't surface it. Re-run discovery to verify. | ☐ |
| **C9** | **Google Cloud: PL too high for GCP products** | Sandbox API firing green alongside No GCP Path. Fixed: Sandbox API downgrades to amber when needs_gcp. Re-verify. | ☐ |
| **C10** | **Google Cloud: CF 100/100 — build-everything not detected** | Qwiklabs not triggering build_everything_culture penalty. Fixed: DIY lab platform injection in rubric grader (C2 audit fix threads discovery_data). Re-verify after fresh Deep Dive. | ☐ |

---

## Full Priority List

**See `docs/roadmap.md`** — the single consolidated inventory of everything active, backlog, decisions needed, and done. This file does not duplicate that list.

---

## Working style reminders

- **Chunked responses, not walls of text.** Keep replies structured and terse.
- **Read Foundation docs before acting.** Three-pass startup sequence every session.
- **Layer discipline.** Intelligence logic → shared layer. Tool-specific → tool layer.
- **No hardcoded numbers outside scoring_config.py.** Pre-commit hook enforces this.
- **Commit + push after any code change.** Per CLAUDE.md rule.
- **Confirm alignment before acting on judgment calls.** Fix known broken immediately.
