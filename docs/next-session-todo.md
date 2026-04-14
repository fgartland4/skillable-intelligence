# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-13 (three marathon sessions — the single biggest day of work on the platform)

**What shipped in this session:**

**ADR + Auth Design:**
- ADR-0000 Solution Overview sent to engineering team
- RBAC refined to 7 roles / 4 boundary lines, Skillable Capabilities Editor role
- Standalone "Authentication and Access Control" section in Platform-Foundation.md

**Prospector UX Overhaul:**
- Results-first home page (All Companies default tab, Recent Batches tab, dynamic batch tab)
- 2×2 action button grid (Upload List, Paste List, Find Lookalikes, Configure HubSpot)
- Background batch processing — batches run without blocking the app
- Async company list loading (instant page load, data fills via fetch)
- Search filter + sortable columns (Company, Est. ACV)
- Company-wide discovery ACV with tiered user base caps
- Deep Dive indicator (green dot) on companies with scored analyses
- GP5 sharpening — Deep Dive ACV overwrites discovery estimate in Prospector
- Merged four input pages into one tabbed page at /prospector/input
- Consolidated field mapper into Configure HubSpot tab with +/- collapsible tree
- Dedup normalization (Cisco/Cisco Systems, Google/Google Cloud, VMware variants)
- Badge display fix, cert column fix, export filename standard, checkbox moved to far left
- Research + Deep Dive buttons replace per-row Inspect link

**Unified ACV Model (all 6 org types — locked and implemented):**
- Software: 4%/2hrs + three-tier open source (4%/3%/1%) + training maturity multipliers
- Academic: 25%/15hrs, course exams bundled
- Industry Authority: tiered deflation (>500K ÷10, 100-500K ÷5, <100K ÷2) + 5%/10hrs
- Enterprise Learning Platform: 3%/3hrs "Platform & ILT Learners"
- ILT Training Org: 25%/18hrs
- GSI: 5%/8hrs, VAR: 5%/8hrs, Distributor: 3%/5hrs
- Full spec in `docs/unified-acv-model.md`
- All constants in scoring_config.py, implemented in acv_calculator.py + app.py
- Platform-Foundation.md + B&S Reference updated

**Scoring Fixes:**
- Sandbox API downgrades to amber when No GCP Path present
- DIY lab platform → amber in Build Capacity + Org DNA (grader now sees discovery_data)
- Strong signals capped at 2 per dimension (IV differentiation)
- ACV guardrails R1-R5 (wrapper org cap, null fallback, cert cap, company cap, prompt fix)
- Discovery cache no longer re-researches on SCORING_LOGIC_VERSION bump

**Infrastructure:**
- Server-side 60s cache for Prospector company list
- Normalized name lookup in storage.py (find_discovery_by_company_name)
- Exhaustive code audit (3 parallel agents) — all critical issues fixed
- rescore.py utility (needs lightweight path — currently triggers full re-research)

---

## §1 — START HERE NEXT SESSION

**Badge-to-Score Consistency Investigation**

Badges are not consistently defending the scores they accompany. Provisioning is the most visible example (products scoring 30/35 with only 1 badge), but the inconsistency likely exists across dimensions. This is NOT a badge selector problem — it's a pipeline investigation.

**The investigation:**

| Step | What to do |
|---|---|
| **1** | Pick a 1-badge Provisioning product and a 4-badge Provisioning product from the same analysis. Trace BOTH through the full pipeline: researcher fact extraction → fact drawer → scorer signals → badge selector output. |
| **2** | For the 1-badge product: identify exactly WHERE information is lost. Is the researcher not extracting facts? Is the scorer crediting signals the badge selector doesn't see? Is the badge selector filtering too aggressively? |
| **3** | For the 4-badge product: what facts does it have that the 1-badge product is missing? Are those facts genuinely absent, or did the researcher fail to extract them? |
| **4** | Extend the investigation to Lab Access, Scoring, and Teardown. Same pattern — compare thin-badge products against rich-badge products. |
| **5** | Extend to Pillar 2 and Pillar 3 rubric dimensions. The rubric grader emits variable badges — are there dimensions consistently producing only 1-2 badges when the score warrants more? |
| **6** | Document the root cause(s) and recommend structural fixes — not band-aids. |

**The principle:** Badges explain the score. If the score is 30/35, the badges must show WHY it's 30/35. If the score is 8/35, the badges must show WHY it's 8/35. Every scored dimension should have 2-4 badges that defend the number. One badge is not enough evidence. Zero badges with a score is a trust failure.

**Context from Frank (2026-04-13):** "I believe this is why badging has been so painful — I think we might be putting hack on top of hack on top of hack. While it's most evident in provisioning because it's so obvious... I wonder if there are inconsistencies in the way we're doing this that we should go and find out what's the real problem." A band-aid (minimum badge floor) was built and reverted in the same session — the right answer is to find and fix the root cause across the full pipeline, not patch the badge selector.

**Known examples of thin badging:**
- Sage 50, Sage 100: Provisioning scoring 30/35 with only "Runs in VM" + "Pre-Instancing?" — 2 badges, one of which is a suggestion, not evidence
- Simple installable products generally: the scorer credits the VM fabric at full points but the researcher doesn't extract enough secondary facts (is_multi_vm_lab, has_complex_topology, container viability, OS details) for the badge selector to emit additional badges
- The badge selector can only emit badges for facts that exist in the fact drawer — if the researcher doesn't extract them, and the scorer doesn't need them (it credits the fabric directly), the badges are thin

**Key files to investigate:**
- `backend/researcher.py` — Pillar 1 fact extractor prompt (what does it ask for? what does it miss?)
- `backend/pillar_1_scorer.py` — what signals does it credit vs what the badge selector can emit?
- `backend/badge_selector.py` — `_pillar_1_provisioning_badges()` and the elif chain for primary fabrics
- `backend/models.py` — `ProvisioningFacts` dataclass (what fields exist but are often unpopulated?)

### After the investigation — Prospector modal documentation

The ? icons on Prospector pages are wired but show "Coming soon." Content needs to be written sourced from Platform-Foundation.md and B&S Reference — same pattern as Inspector modals. Do this AFTER the badge investigation because the modal content references how scoring and badging work, and that needs to be right first.

---

## Full Priority List

**See `docs/roadmap.md`** — the single consolidated inventory of everything active, backlog, decisions needed, and done. This file does not duplicate that list.

**Key upcoming items (in priority order):**

| # | Item | Notes |
|---|---|---|
| **1** | Badge-to-Score Consistency Investigation | §1 above — root cause, not patches |
| **2** | Prospector ? modal documentation content | After badge investigation |
| **3** | Validation round | CompTIA, EC-Council, WGU, GCU, Skillsoft, QA, Accenture, Cisco, Google Cloud — verify ACV and scores |
| **4** | Lightweight rescore utility | Current rescore.py triggers full re-research. Need a path that re-runs only scorers + ACV on existing facts. |
| **5** | Inspector↔Prospector cache verification | HashiCorp test case — confirm normalized lookup works end-to-end |
| **6** | Background processing toast notifications | "Run in Background" button on Deep Dive + toast on completion |
| **7** | Designer | Foundation session + build. Design docs ready. Biggest workstream. |
| **8** | Deployment | Render or Azure Web App — blocks auth |

---

## Working style reminders

- **Chunked responses, not walls of text.** Keep replies structured and terse.
- **Read Foundation docs before acting.** Three-pass startup sequence every session.
- **Layer discipline.** Intelligence logic → shared layer. Tool-specific → tool layer.
- **No hardcoded numbers outside scoring_config.py.** Pre-commit hook enforces this.
- **Commit + push after any code change.** Per CLAUDE.md rule.
- **Confirm alignment before acting on judgment calls.** Fix known broken immediately.
- **Docs → Config → Code → UX.** Always in this order. Docs are the authority.
