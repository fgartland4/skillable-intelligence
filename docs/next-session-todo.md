# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-14 (ACV low-end pattern fixes A/B/D/E/F + Deep Dive docs modal restored to white design)

**What shipped today:**

**Docs modal restored** — the beautiful white Deep Dive info modal design that got flattened during the shared-modal migration (commit 14a1252) is back. The shared `_search_modal.html` now has a proper `is-docs` mode using `--sk-modal-*` theme tokens: 920px max width, white surface, dark text, accent rule under the header, WHY/WHAT/HOW eyebrow section labels, scannable tables. Progress / decision / info modes keep their dark chrome — only docs mode flips to white. One component, one API, matches original design.

**ACV low-end pattern fixes — A, B, D, E, F (five of six diagnosed from the Parkway / Multiverse / Zero-Point / New Horizons low-estimate cluster):**

  - **A** — Softened "fraction who actually consume labs" deflator language in the researcher prompt. Mature cert programs with confirmed annual enrollments now trust the platform's calibrated adoption rates directly, instead of Claude layering a second "minority subset" discount on top.
  - **B** — Added explicit rule: prefer annual enrollments; if only cumulative is available, divide by 2-3yr program life (4yr for academic degrees). Prevents the Zero-Point-class 3-8× swing where cumulative and annual got silently substituted.
  - **D** — Known-customer floor now INFORMS the low bound without COLLAPSING range-width. Previously when Claude's original (low, high) were both below floor F, we'd clamp both to F, producing zero-width ranges and artificial uniformity across duplicate records (all three New Horizons records pinned identically). Now: floor sets low; high preserves width — either Claude's original high (if above floor), the stage-derived ceiling, or a 2× floor expansion for very-early stage.
  - **E** — Reframed existing DIY / self-hosted lab platform in the prompt as a POSITIVE ICP signal, not a displacement discount. Companies already running their own labs have already decided they need labs — that's existing demand, not a displacement haircut on top of adoption-rate conservatism.
  - **F** — Rate tier now determined by workload complexity, not deployment label. "SaaS" or "cloud-delivered" curricula can still need VM-class labs (cybersecurity, networking, platform eng). Deployment alone doesn't determine rate.

Pattern **C** (K-12 district budget-signal audience) — deferred. Needs a new researcher field + routing rule. Not a prompt tweak. Queued below.

Pattern **G** (entity dedup drift: GCU vs GCE, multiple Parkway records) — deferred per Frank's decision 2026-04-14: "I think you'd almost have to go organization by organization by organization. I think it'd be tough to write that as a trustworthy thing. They probably need to stay separate."

SCORING_LOGIC_VERSION bumped to `2026-04-14.acv-holistic-patterns-ABDEF-plus-docs-modal-restore`.

---

**Last updated:** 2026-04-13 (extended into the ACV refresh — Discovery Option 2 + Deep Dive cleanup, four phases shipped end-to-end)

**What shipped in the ACV refresh (commits caca521 → c8909e7 → 43a745f + final version bump):**

**Pt 1 — Docs + Researcher prompt fixes (Motions 2/3/5):**
- unified-acv-model.md / Platform-Foundation.md / Badging-and-Scoring-Reference.md updated with category-tier adoption (8/4/1%) + wrapper-org audience split (annual_enrollments_estimate)
- Researcher Motion 2 (channel_partner_se_population): removed "leave null" rule; tiered estimation heuristics from partner-ecosystem signals
- Researcher Motion 5 (events_attendance): removed "leave null" rule; tiered attendance estimation by vendor scale (~30-50k major / 8-15k mid / 5-12k specialized / 1-5k regional)
- Researcher Motion 3 (employee_subset_size): per-product variation by product_relationship (flagship 8-15% / satellite 3-6% / standalone 50-80%); `_build_pillar_2_fact_context` + `extract_instructional_value_facts` accept product_metadata; intelligence.py caller passes product dict

**Pt 2 — Category tier + wrapper-org audience split (code):**
- scoring_config.py: CUSTOMER_TRAINING_ADOPTION_BY_TIER + CATEGORY_TO_TIER + get_customer_training_adoption_for_category() + CATEGORY_TIER_ELIGIBLE_ORG_TYPES + ACV_AUDIENCE_SOURCE_BY_ORG_TYPE + get_acv_audience_source_for_org_type()
- models.py: annual_enrollments_estimate + evidence + confidence fields on Product
- prompts/discovery.txt: wrapper-org annual_enrollments fields documented in schema
- acv_calculator.py: Motion 1 audience routed by org type; category tier replaces flat 4% for SOFTWARE/Enterprise Software; IA deflation scoped to IA only; wrapper-org cap skipped when annual_enrollments is the source

**Pt 3 — Option 2 holistic discovery ACV + Prospector UX:**
- scoring_config.py: HOLISTIC_ACV_ANCHORS (8 calibrated comparables: CompTIA $5.8M, EC-Council $2.2M, WGU $4.7M, GCU $1.7M, Skillsoft $5M, Pluralsight $2.5M, QA $700k, Accenture $2.8M) + guardrails
- researcher.py: _HOLISTIC_ACV_PROMPT + estimate_holistic_acv() with hard cap + range-width + sanity-check guardrail enforcement
- intelligence.py: discover() invokes holistic call after enrich_discovery, stores on discovery["_holistic_acv"]; non-blocking on failure
- app.py: retired ~100 lines of per-product Python ACV math; row dict reads _holistic_acv; key_signal removed (replaced by rationale); CSV exports updated with new columns (acv_low/high/midpoint/confidence + driver_1..5 + caveats)
- _search_modal.html: shared modal extended with info mode + openSearchModalInfo() — NOT forked. Info mode renders rationale + drivers + caveats with confidence chip. Theme tokens only, no hardcoded hex.
- prospector.html: column order updated (Rank · Company · ACV · Deep Dives · Top Product · Why · 4 tiers · Lab Platform · Cert Program · Sales Channel); ACV cell shows range + confidence chip + click → modal; Deep Dive coverage column with N/M + color-coded pill; escapeAttr() helper

**Pt 4 — Dedup runner + Retrofit runner:**
- scripts/dedup_discoveries.py: Option C (auto-merge obvious + flag ambiguous to human review). Tested on cached state — 347 records → 31 dup groups, 24 auto-mergeable, 7 surface for review. Default dry-run; --execute / --review flags.
- scripts/retrofit_acv.py: holistic ACV retrofit — runs estimate_holistic_acv() against cached discoveries with no re-research. ThreadPool for parallelism. Filters: --limit / --company / --skip-existing. Cost + time estimator in dry-run.

**Pt 5 — Final wiring + version bump:**
- prospector_input.html: cost + time estimator recalibrated for 2-call discovery flow ($0.45/co, 180s/co)
- SCORING_LOGIC_VERSION bumped to `2026-04-13.acv-holistic-option-2-plus-wrapper-split-plus-motion-fixes`

**All 118 tests pass.** Pre-commit anti-hardcoding tests pass.

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

**Deep Dive ACV Rebuild (critical fix, end of session):**
- `rebuild_acv_motions_from_facts()` added to `acv_calculator.py` — rebuilds ACV motions from the serialized fact drawer on every page load using the current unified model
- Wired into `recompute_analysis()` so ALL Inspector analysis pages reflect the unified ACV model immediately — zero re-research, zero Claude calls, pure Python
- `stamp_version.py` utility stamped all 185 cached files with current SCORING_LOGIC_VERSION to prevent unnecessary re-research

**Prospector Modal Documentation (first pass):**
- Three modal content blocks written in `scoring_config.PROSPECTOR_MODAL_CONTENT`: "Researched Companies", "How ACV is Estimated", "How Companies Are Scored"
- Wired to ? icons on Prospector home page — real modals, not tooltips
- Content references actual adoption rates, hours, and rate tiers from config (Define-Once)

**Infrastructure:**
- Server-side 60s cache for Prospector company list
- Normalized name lookup in storage.py (find_discovery_by_company_name)
- Exhaustive code audit (3 parallel agents) — all critical issues fixed

---

## §1 — START HERE NEXT SESSION

**Run the dedup + retrofit on the cached 347 records, then validate.**

The ACV refresh shipped end-to-end in the prior session — code is in
production, version bumped. Three things remain operational, not
architectural:

| Step | Command | Why |
|---|---|---|
| **1. Dedup review** | `python scripts/dedup_discoveries.py --review` | See the 7 ambiguous cases that need human judgment (Workday split between badges, Akamai variants, Tencent / Tencent Cloud, Huawei variants). Decide each. |
| **2. Dedup execute** | `python scripts/dedup_discoveries.py --execute` | Auto-merge the 24 obvious dup groups (Cisco / Cisco Systems class). Older records archived, not deleted. |
| **3. Retrofit dry-run** | `python scripts/retrofit_acv.py` | See cost + time estimate for retrofitting all cached records with the new holistic ACV (Option 2). Expected: ~$50-$150, ~30-60 min. |
| **4. Retrofit validation** | `python scripts/retrofit_acv.py --execute --limit 5 --company "Nutanix"` (then LLPA, Boeing, Accenture, one Academic) | Validate on a handful of known companies before going wide. Verify Nutanix lands in the multi-million range, LLPA collapses to ~$200-500k, Boeing reflects its real opportunity. |
| **5. Retrofit full** | `python scripts/retrofit_acv.py --execute --skip-existing` | Run on the rest. Skip-existing avoids re-running on validated records. |

After retrofit completes, the Prospector list reflects the new ACV
shape across all cached companies. SCORING_LOGIC_VERSION already
bumped — cache reads pick up the new logic immediately.

### After retrofit — return to the prior open work

The badge-to-score consistency investigation that was §1 going into
the ACV refresh remains the next architectural item. It was paused
because the ACV problem was higher-leverage. Original §1 below for
context.

---

### Badge-to-Score Consistency Investigation (still open after ACV refresh)

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
| **2** | Prospector ? modal documentation refinement | First pass shipped — three modals wired. Refine content after badge investigation confirms how scoring/badging is described. |
| **3** | Validation round | CompTIA, EC-Council, WGU, GCU, Skillsoft, QA, Accenture, Cisco, Google Cloud — verify ACV and scores. Retrofit the records touched by Patterns A/B/D/E/F fixes: Parkway, Multiverse, Zero-Point Security, Power Academics, Kaosoft. |
| **3a** | **Pattern C — K-12 budget-signal audience (deferred from 2026-04-14)** | Parkway School District has a ~$750k CTE/PD budget line that never enters the math — model multiplies ~135 students × cloud-tier rate and lands at $18-52k. Need: (1) new researcher field for "training-dedicated budget" when visible; (2) routing rule that lets budget feed Motion 2/3-style partner/employee audience sizing. Not a prompt tweak — structural. ~1-day work. |
| **4** | Lightweight rescore utility | ACV portion solved — `rebuild_acv_motions_from_facts` runs on every page load. Still need a path to re-run pillar scorers + rubric graders on existing facts without re-researching. |
| **5** | Inspector↔Prospector cache verification | HashiCorp test case — confirm normalized lookup works end-to-end |
| **6** | Background processing toast notifications | "Run in Background" button on Deep Dive + toast on completion |
| **7** | Designer | Foundation session + build. Design docs ready. Biggest workstream. |
| **8** | Deployment | Render or Azure Web App — blocks auth implementation |
| **9** | Authentication + RBAC | 7 roles, 4 boundary lines designed and documented in Platform-Foundation.md + ADR-0000. Implementation blocked on deployment (#8). Design is locked. |

---

## Working style reminders

- **Chunked responses, not walls of text.** Keep replies structured and terse.
- **Read Foundation docs before acting.** Three-pass startup sequence every session.
- **Layer discipline.** Intelligence logic → shared layer. Tool-specific → tool layer.
- **No hardcoded numbers outside scoring_config.py.** Pre-commit hook enforces this.
- **Commit + push after any code change.** Per CLAUDE.md rule.
- **Confirm alignment before acting on judgment calls.** Fix known broken immediately.
- **Docs → Config → Code → UX.** Always in this order. Docs are the authority.
