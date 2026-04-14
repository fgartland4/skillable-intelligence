# Next Session — Todo List

> **Fresh Claude on this project?** Skip the "Last updated" block below and jump straight to **§1 — START HERE NEXT SESSION**. That's your entry point. The Last updated block is continuity context for returning Claude — it assumes you already know what happened in the prior session. You don't need it to start working.
>
> **Returning Claude?** Read the Last updated block to catch up on what landed in the prior session, then proceed to §1 for the next action.

---

**Last updated:** 2026-04-14 EOD (saturated-only cap + ACV Potential calibration + full 549-record retrofit + core docs synced)

**What shipped this session (in order):**

| Commit | What |
|---|---|
| `2474b13` | Content Dev partnership ACV + Prospector column tooltips + "Why"→"Top Signal" rename |
| `c42a515` | Amber pulsing dot for running batches (visually distinct from completed green) |
| `943a012` | White docs modal design restored + Patterns A/B/D/E/F prompt fixes |
| `17acc1d` | Core docs synced — Option 2 Holistic, known-customer calibration, partnership, pitfalls |
| `ed14343` | Modal docs rewrite — three Prospector `?` modals + Inspector ACV rate fix |
| `8c2d7c4` | Concurrency bump: 3 → 10 for Prospector batch + retrofit runner |
| `ddaf4e3` | `scripts/merge_companies.py` (force-merge parent/service-line pairs like Deloitte) + `scripts/rescore_pillars.py` (pure-Python pillar rescore, zero Claude) + legacy `.info-modal-*` CSS consolidated into shared modal |
| `e870361` | **Saturated-only ceiling cap + two-column calibration (current + Potential) + `_raw_claude` preservation for free future guardrail tuning** |

**Design evolution today (big one) — known-customer floor/ceiling redesign.**

The previous design capped every stage at a multiple of current ACV (1.3× saturated / 1.5× mature-small / 3× mid / 8× first-year / 15× early / uncapped very-early). That "anchored small customers to their starting place" (Frank's phrase 2026-04-14): a growing customer's ACV Potential is a function of their portfolio size, not their current Skillable spend.

**New rule, locked:**
- **Floor** = `current_acv` for ALL stages (safety — never undersell an existing contract)
- **Ceiling cap** = 1.3× current ONLY for `saturated` customers
- **Every other stage** = no cap from current; Claude's holistic reasoning produces the high, subject only to the universal $30M hard cap
- **Expected-low multipliers abandoned** as fake precision

**Two-column calibration block.** The anonymized block Claude sees now emits BOTH `current ACV` AND `estimated ACV Potential` per stage. Prospects are anchored on Potential (what could this be if we win fully) instead of on Current (what we charge today). `scripts/compute_customer_potentials.py` populates `acv_potential_low`/`high` in the gitignored `known_customers.json` via a one-time caps-disabled holistic pass.

**`_raw_claude` preservation.** `estimate_holistic_acv` now saves Claude's original numeric output alongside the post-guardrail result. Future guardrail tuning (hard cap / range ratio / per-user ceiling / known-customer floor/ceiling rules) can propagate via pure-Python re-application — zero additional Claude calls. Only prompt text changes or calibration-block changes require a retrofit run.

**Customer stage relabeling (per Frank's walk-through 2026-04-14).** Only 4 customers are `saturated` (CompTIA, EC-Council, SANS, Skillsoft). Everyone else is in a growth stage with no cap — including Microsoft, Omnissa, Deloitte, Siemens, Eaton, Commvault, Epiq, Cengage, Trellix, Cisco, GCU, Multiverse, LLPA, Zero-Point, Boxhill, New Horizons.

**Full 549-record retrofit at 10-way concurrency** — 14.6 min, 0 failures. Post-retrofit distribution:

| Band | Count |
|---|---|
| <$100k | 22 |
| $100k–$500k | 174 |
| $500k–$1M | 58 |
| $1M–$5M | 148 |
| $5M–$15M | 97 |
| $15M+ | 35 (top-tier enterprise hitting $30M hard cap correctly) |
| partnership | 7 |

Key corrections visible in the retrofit:
- **Nutanix** historically $434k → **$6M-$12M** (orders-of-magnitude correction)
- **Deloitte** consolidated 3 records into 1 at **$12M-$22M** (was $410k-$820k)
- **Multiverse** finally unpinned from $111k floor → **$350k-$950k**
- **Infosec** $350k → $1.8M-$3.6M
- Top enterprise (Microsoft, Google, AWS, Salesforce, Oracle, Adobe, VMware, ServiceNow, Cisco, IBM) → $18M-$30M — hitting the universal hard cap correctly
- Parkway School District stays low at $18k-$55k (Pattern C deferred as expected)

**Auto-dedup pass** — 47 obvious duplicate groups merged (Cisco variants, Cengage, LLPA, GP Strategies, Docebo, Alibaba Cloud, etc.). 22 still need human review.

---

## §1 — START HERE NEXT SESSION

**Validate 10 diverse ACV numbers with Frank. If they look right, the data is ready for Marketing.**

Today's work was a major ACV design correction. The full retrofit completed cleanly with no blowouts and the spot-checks I ran look good, but a human pass across the diversity of the cache is the right next step before Marketing uses any of this in their ICP targeting.

**Suggested 10-company spot-check (mix of org types + sizes):**

| Company | Org type | Expect |
|---|---|---|
| CompTIA | Industry Authority (saturated) | ~$5M (current) — 1.3× cap binding |
| SANS Institute | Industry Authority (saturated) | ~$624k-$810k |
| Skillsoft | Enterprise Learning Platform (saturated) | ~$5.5M-$7.2M |
| Microsoft | Software (mid) | ~$22M-$30M — hard cap binding |
| Cisco (known customer view) | Software (first-year) | Sharp up from $255k |
| Deloitte | Systems Integrator (very-early) | ~$12M-$22M — Frank's "gross" call |
| Multiverse | ILT Training Org (early) | ~$350k-$950k (finally above floor) |
| Parkway School District | K-12 (Pattern C deferred) | ~$18k-$55k — EXPECTED low |
| Nutanix | Software prospect | ~$6M-$12M — the original problem case |
| GP Strategies | Content Development (partnership) | "Partnership" chip, no dollar range |

**Process.** Open each in Prospector, click the ACV cell → read the rationale + drivers + caveats. Flag any that feel wrong to Frank. If a number looks off, use `scripts/retrofit_acv.py --mode holistic --execute --company "<name>"` to rerun one at a time.

**After validation:** CSV export → hand to Marketing. That was the whole goal of this work.

### Then — continue with the longstanding architectural item

**Badge-to-Score Consistency Investigation** remains the next architectural work. Frank's exact framing (2026-04-13): "I believe this is why badging has been so painful — I think we might be putting hack on top of hack on top of hack... I wonder if there are inconsistencies in the way we're doing this that we should go and find out what's the real problem." See §1b below.

---

### §1b — Badge-to-Score Consistency Investigation (still open)

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

**The principle:** Badges explain the score. If the score is 30/35, the badges must show WHY it's 30/35. Every scored dimension should have 2-4 badges that defend the number.

`scripts/rescore_pillars.py` (shipped 2026-04-14) now lets us propagate Python-only scoring changes across the whole cache with zero Claude calls. That unblocks iterative tuning during the investigation.

---

## Backlog (structural deferrals from 2026-04-14)

| Item | Why deferred |
|---|---|
| **Pattern C — K-12 district budget-signal audience** | Parkway has a ~$750k CTE/PD budget line that never enters the math. Need new researcher field + routing rule. ~1-day structural work. |
| **Pattern G — parent/subsidiary entity dedup** (GCU/GCE, Deloitte/Deloitte Consulting class) | Per Frank: "I think you'd almost have to go organization by organization by organization. I think it'd be tough to write that as a trustworthy thing. They probably need to stay separate." Manual merge via `scripts/merge_companies.py` when needed. |
| **LLPA-class federating associations** | Rare pattern. Punted. |
| **Lightweight Pillar rescore for rubric-text changes** | `rescore_pillars.py` handles weight/tier/baseline/penalty changes. Text changes to rubric tiers still need a re-grade (Claude call per dimension). Not yet built. |

---

**Prior session notes (historical — consolidated into the top summary above):**

Patterns A/B/D/E/F prompt fixes shipped earlier in the day; superseded by the bigger saturated-only design correction and full 549-record retrofit at session end. SCORING_LOGIC_VERSION now at `2026-04-14.saturated-only-cap-plus-potential-calibration`.

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
