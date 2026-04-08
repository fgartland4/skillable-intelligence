# Next Session — Todo List

**Last updated:** 2026-04-08 (late session — Rebuild Steps 1 through 5 + Step 5b pristine cleanup shipped; follow-up commit 06391b0 landed the deferred 5.5 items (Runs in VM rename, Pre-Instancing? rename, Large Lab / Requires GCP deletions, Training License universal amber, vendor_official_acronym, ACV hero 3-line widget, three-box bottom row consistency, SCORING_LOGIC_VERSION bump); subsequent commit rewrote `docs/Platform-Foundation.md` and `docs/Badging-and-Scoring-Reference.md` from scratch under WHY/WHAT/HOW discipline with zero cross-doc duplication, plus CLAUDE.md updated to match the new module structure. Trellix verification is the next step.)
**Read this first when you sit down for the next session.**

---

## Format note

This doc uses a two-column table format per Frank's 2026-04-07 directive: narrow column 1 = item name, wider column 2 = description. Sections are kept thin so the long arc lives in `docs/roadmap.md` and the historical record lives in `docs/decision-log.md`.

---

## §0 — START HERE (THE REBUILD IS IN PROGRESS)

**The Intelligence layer is being rebuilt to align the code with the Three Layers of Intelligence architecture described in `docs/Platform-Foundation.md` (lines 182–233).** Everything below §0 reflects the pre-rebuild backlog; those items are still valid but are on hold until the rebuild reaches Step 6. **The rebuild is the ONLY priority until it lands.**

**Why we're rebuilding.** The old Intelligence layer collapsed three layers into one big Claude call per product — the call did research, applied Skillable judgment, and emitted scoring badges all at once. That was the forbidden pattern Platform-Foundation.md explicitly names ("Research + Score in one Claude call"). Symptoms: badge inconsistency, score drift, logic that kept changing because judged data was colliding with the math layer. Frank's diagnosis: **"The math is right. The problem was badges were the only way to get points, so the AI was emitting multiple similar badges to hit the right score and the math couldn't be clean."**

**Where to read the target architecture:** `docs/Platform-Foundation.md` → "The Three Layers of Intelligence — Research, Score, Badge" (lines 182–233). That section defines the four sub-layers (Research, Store, Score, Badge), the forbidden collapse patterns, and what each layer is allowed to use. Read it before making any rebuild decisions.

### §0a — Where we are right now

| Item | Status |
|---|---|
| **Step 1 — Fact drawer dataclasses** | **SHIPPED** (`14e0c44`). `ProductLababilityFacts` + `InstructionalValueFacts` + `CustomerFitFacts` + all sub-dataclasses. Truth-only typed primitives. No `strength` field. Define-Once spot tests pass. |
| **Step 2 — Research → Store layer** | **SHIPPED** (`68ff479` + `eb44327`). Three per-pillar Claude extractors in `backend/researcher.py`, wired into the live Deep Dive path. Parallel per-product for P1/P2, once-per-company for P3. |
| **Step 3 — Pillar 1 pure-Python scoring** | **SHIPPED** (`1dbe66f`). New `backend/pillar_1_scorer.py`. Capability-store model reads typed primitives directly. Zero Claude. Zero hardcoded numbers. 25 unit tests. |
| **Step 4a — scoring_config.py routing fix** | **SHIPPED** (`66c0b67` + `4f9f202`). Lab infrastructure moved Delivery → Build. Independent third-party courses + cert bodies confined to Market Demand only. ATP cross-credit between Delivery + Market Demand. `lab_build_capability` + `vendor_published_on_third_party` signal categories added. SCORING_LOGIC_VERSION bumped. |
| **Step 4 — Rubric grader + Pillar 2/3 Python scorers** | **SHIPPED** (`6b5692d`). New `backend/rubric_grader.py` (the narrow Claude-in-Score slice for qualitative strength grading). New `backend/pillar_2_scorer.py` + `backend/pillar_3_scorer.py`. 27 unit tests. Wired into `intelligence.score()`. |
| **Step 5 — Soft cutover** | **SHIPPED** (`4d5e05e`). `fit_score` flipped to Python-authoritative for all three pillars. Legacy monolithic scoring output is OVERWRITTEN (not deleted — soft cutover). |
| **Trellix smoke test** | **PASSED** 2026-04-08. Pipeline runs end-to-end. |
| **Step 5b-lite — Stubbed monolithic scoring call** | **SHIPPED** (`1f7b2a6`). `scorer.score_selected_products` no longer makes a Claude call. Builds Product objects from discovery data directly + attaches fact drawer. Metadata fields (contacts, owning_org, lab_highlight, etc.) are empty during the rebuild window — restored at Step 5c via a dedicated lightweight metadata extractor. |
| **Pillar 1 refinements — all decisions locked 2026-04-08** | **SHIPPED** (`1f7b2a6`). See §0f for the full list. Simulation override (5/12/0/25), fabric priority + optionality + VM reframing + container disqualifiers + M365 as first-class fabric (Tenant 25, Admin 18), Custom Cloud strength badge, No GCP Path badge. |
| **Step 6-lite — Badge selector** | **SHIPPED** (`1f7b2a6`). `backend/badge_selector.py`. Deterministic Pillar 1 badge selection from facts + pass-through from GradedSignals for Pillars 2/3. Honors the naming rules locked 2026-04-08. |
| **Three Skillable capability docs filed** | **SHIPPED** (`1f7b2a6`). `backend/knowledge/skillable_capabilities.json` enriched with `m365_tenants`, `microsoft_office`, `byoc_custom_cloud_labs`, `software_licensing`. |
| **Step 5b — Pristine cleanup** | **SHIPPED (this commit).** Penalty-visibility fix ported into `pillar_2_scorer` + `pillar_3_scorer` + Trellix Org DNA regression test. New `backend/fit_score_composer.py` (compose_fit_score + Technical Fit Multiplier) with 11 unit tests. New `backend/acv_calculator.py` (absorbs ACV math). `scoring_math.py` + `badge_normalization.py` + `prompt_generator.py` + `prompts/scoring_template.md` DELETED. `_parse_*` dead code in `scorer.py` DELETED (~300 lines). `CEILING_FLAGS` dict + `CROSS_PILLAR_RULES` tuple DELETED. Comparison fields (`pillar_1/2/3_python_score`) DELETED from `models.py`. `intelligence.score()` cutover rewired to populate `fit_score` directly + call `compose_fit_score`. `intelligence.recompute_analysis` slimmed to ACV + verdict + sort (pillar scores trusted from save). Dead test files removed. app.py `PRODUCT_FAMILY_MIN_PRODUCTS` fix preserved. **115 tests passing, 0 failures.** |
| **Trellix verification** | Pending — HUDDLE POINT. Frank runs a forced-refresh Deep Dive on Trellix once this commit lands. |

### §0b — Architectural lock-ins (these are non-negotiable for the rebuild)

These lock-ins came out of multiple clarifying conversations during the rebuild. They override any prior guidance in any other doc. Platform-Foundation.md's Three Layers of Intelligence section is their home; this list is the working checklist.

| # | Lock-in | What it means operationally |
|---|---|---|
| **1** | **Score reads facts directly. Never badges.** | The Score layer takes typed primitives from the fact drawer as input and computes `DimensionScore` objects directly. It does NOT match against badge names or look up points by badge. The existing `scoring_math.compute_dimension_score()` is badge-keyed and will be deleted at Step 5. |
| **2** | **The math is right. Only the input format changes.** | Point values, caps, formulas, and rules in `scoring_config.py` stay exactly as they are: Hyper-V = +30, Sandbox API = +22, Grand Slam cap = 15, risk cap reduction (-3 amber, -8 red), Sandbox API red Pillar 1 cap (25/5), Technical Fit Multiplier, Ceiling Flags. What changes is HOW values get fed to the math. Old way: badge name → signal lookup. New way: `facts.provisioning.runs_as_installable` → direct signal credit. |
| **3** | **Badges are post-scoring display only.** | Badges are the Step 6 layer. They read facts + computed scores and pick 2–4 contextual storytellers per dimension to explain WHY the score is what it is. Badges never affect the math. Badges never feed scoring. A badge that tried to do both was the "badge-as-scoring" drift Platform-Foundation.md explicitly names as forbidden. |
| **4** | **Claude runs PRIMARILY in Research. Two open questions for Steps 4 and 6.** | Current direction: Score is pure Python. Badge is pure Python. Research is where Claude is called. **Not yet locked:** (a) Pillar 2 / Pillar 3 strength tiering at Step 4 may legitimately need a small Claude call because strength is qualitative judgment — candidate approaches in §0c Step 4. (b) Badge evidence phrasing at Step 6 may use a tiny Claude call per dimension. Both decisions happen at the step boundary, with Frank, before the code is written. This lock-in is **current direction, not locked**. |
| **5** | **Facts are truth-only. No `strength`, no Skillable judgment, no interpretation.** | `SignalEvidence` has `{present, observation, source_url, confidence}` — NO `strength` field. Strength is interpretation; the drawer holds facts. Define-Once spot tests in `tests/test_data_model.py` enforce this contract. Any future fact addition must go through the same spot-test gate. |
| **6** | **NO HARDCODING ANYWHERE. EVER.** | Every number, every threshold, every magic string, every point value, every cap, every weight, every rule parameter — all of it comes from a Define-Once source (`scoring_config.py`, `skillable_capabilities.json`, `competitors.json`, `contact_guidance.json`, `delivery_patterns.json`, etc.). If a rebuild scorer has a literal `15` or `+30` or `"rich"` or `"Hyper-V"` in it, that's a bug — lift the value to config. This rule is stronger than "Define-Once" as usually stated; it is the **hard zero-hardcoding standard** applied to every line of rebuild code. Pre-commit review will scan for literals that look like framework constants. |
| **7** | **The UX doesn't change during the rebuild.** | No new screens. No new buttons. No new progress modals. No new Product Chooser. The rebuild is internal — swap out the engine. Same entry points, same flows, same modal. |
| **8** | **Legacy paths stay alive until cutover.** | Each new step adds code alongside the old code, not in place of it. The monolithic scoring call keeps running as a safety net while Steps 3 and 4 build the new path in parallel. Step 5 is the cutover — delete the monolithic call, delete `compute_dimension_score()`, flip the Product model field from comparison to authoritative. |

### §0c — The rebuild plan (Steps 1 through 6)

| Step | What it does | Status |
|---|---|---|
| **1 — Fact drawer dataclasses** | Add typed-primitive dataclasses for all three pillars to `backend/models.py`. Attach to `Product` and `CompanyAnalysis`. Define-Once spot tests enforce canonical homes and truth-only contract. | **SHIPPED** (`14e0c44`) |
| **2 — Research → Store layer** | Three per-pillar Claude extractors in `backend/researcher.py`. Truth-only prompts. Wire into live Deep Dive path in `intelligence.score()`. Parallel per-product execution. Fact drawers attach to `Product` / `CompanyAnalysis` before the legacy monolithic call runs. | **SHIPPED** (`68ff479`, `eb44327`) |
| **3 — Pillar 1 Python scoring from facts** | `backend/pillar_1_scorer.py` shipped with full capability-store model, Define-Once everywhere, 25 unit tests. `score_provisioning` rewritten 2026-04-08 late with M365 fabric priority + preferred_fabric hint + multi-fabric optionality bonus + container disqualifier check + Simulation hard override + No GCP Path badge. | **SHIPPED** (`1dbe66f`) + refined in the upcoming bundled commit |
| **4a — scoring_config.py routing fix** | Lab infrastructure moved from Delivery Capacity to Build Capacity. Independent third-party course counts + cert body curricula confined to Market Demand only. ATP cross-credit between Delivery Capacity and Market Demand. New signal categories `lab_build_capability` and `vendor_published_on_third_party` added to Build Capacity. `SCORING_LOGIC_VERSION` bumped. | **SHIPPED** (`66c0b67` + `4f9f202`) |
| **4 — Pillars 2/3 rubric grader + Python scorers** | `backend/rubric_grader.py` shipped with 8 grader functions (4 per pillar), parallel orchestrators, prompts built at runtime from `scoring_config.py` rubrics. `backend/pillar_2_scorer.py` + `backend/pillar_3_scorer.py` shipped — pure Python scorers reading GradedSignal + baseline + penalties. 27 unit tests. | **SHIPPED** (`6b5692d`) |
| **5 — Soft cutover** | `intelligence.score()` overwrites the legacy monolithic path's `fit_score` output with the Python scorers' results. All three pillars flipped. Existing `scoring_math.py` math path unchanged (dead code for the Python flow but still present — full deletion deferred to Step 5b proper). | **SHIPPED** (`4d5e05e`) |
| **5b-lite — Stub the monolithic Claude call** | `scorer.score_selected_products` no longer fires the monolithic Claude scoring call. Products are built directly from discovery data + fact drawer. Metadata fields (contacts, owning_org, lab_highlight, lab_concepts, deployment_model, etc.) fall to empty during the rebuild window. | **ON DISK, UNCOMMITTED** (folded into upcoming bundled commit) |
| **5b — Full monolithic + dead math deletion** | Delete `_score_single_product`, `_parse_product`, `_parse_pillar`, `_parse_consumption`, `_parse_verdict`, `_parse_badges_for_dimension` from `scorer.py`. Delete `compute_dimension_score`, `_compute_rubric_dimension_score`, `compute_all`, `detect_sandbox_api_red_cap` from `scoring_math.py`. Delete related build-lookup helpers. Write a NEW lightweight metadata extractor to restore contacts / owning_org / deployment_model / etc. (small focused Claude call, metadata only, no scoring). Update tests that reference deleted functions. | **PENDING** (after Trellix verification of the Python path proves it's trustworthy) |
| **5.5 — Pillar 1 tuning pass** | Refinements that fell out of the 2026-04-08 walkthrough that are deferred as not-critical for Trellix verification: **(a)** Cosmetic renames — `Runs in Hyper-V` → `Runs in VM`, `Pre-Instancing` → `Pre-Instancing?`, `Requires GCP` → `No GCP Path` (the new badges for these already exist; the LEGACY badges with the old names still exist in `scoring_config.py` and `scoring_math.py` and need to be cleaned up). **(b)** Delete the `Large Lab` badge from `_provisioning_badges` (its fact field `is_large_lab` stays — it drives Pre-Instancing? logic). **(c)** Full GCP multi-badge nuance — the red `No GCP Path` + workaround-fabric-at-amber pattern when GCP is vendor-preferred. Currently No GCP Path only fires amber as a simple case; the red + workaround amber nuance needs `preferred_fabric == "gcp"` detection + tweaking the fabric credit to half-credit the workaround. **(d)** Training License universal amber-bias — currently applies only when M365 is set. Should generalize: Training License green is rare, reserved for truly-zero-friction cases (open source, unlimited free tier, no concurrent user model, no tier decisions). Most products should fire Training License amber. **(e)** `multi_fabric_flexibility` signal category added to Lab Versatility (Pillar 2) rubric so the grader can credit multi-fabric products. **(f)** `vendor_official_acronym` field captured at product level — wire the researcher to populate it and the badge selector to use it for long-product-name badges. | Pending |
| **6 — Badging layer (full)** | `backend/badge_selector.py` Step 6-lite is shipped in the upcoming bundled commit — it handles the deterministic Pillar 1 badge selection + pass-through from GradedSignals for Pillars 2/3. Step 6 FULL adds: (a) intelligent 2–4 badge selection logic per dimension (prioritize load-bearing signals, handle overflow, dedupe related findings), (b) badge evidence text polish for Pillar 1 (currently Step 6-lite uses canned evidence text — Step 6 full generates contextual evidence from the actual fact drawer content), (c) cross-pillar badge coordination (`Multi-VM Lab` firing in Pillar 1 AND Pillar 2 Product Complexity — decide which "owns" display), (d) vendor-product-name acronym rendering via `Product.vendor_official_acronym`. Also: cosmetic rename of `Pre-Instancing` → `Pre-Instancing?` (badge NAME, already shipped in new signals but needs to coexist with rename of the badge itself). | Pending |
| **7 — UX followups (post-rebuild)** | The two UX workstreams explicitly deferred until after the rebuild lands: **(a) ACV hero widget** — the 3-line structure defined in `docs/Platform-Foundation.md` lines 711–734 (company-level range, descriptor, scored subtotal with the word `ONLY`). **(b) Three-Box Bottom Row consistency pass** — same font, size, vertical spacing, column spacing, padding, and alignment across Scored Products / Competitive Products / ACV by Use Case, per `docs/Platform-Foundation.md` lines 766–800. Slate blue font on the middle box is the one intentional differentiator. Both plans are already well-written in Platform-Foundation — Step 7 is the implementation pass, not a re-design. | Pending |
| **8 — Docs major rewrite (rebuild capstone)** | After Steps 1–7 are in, **both `docs/Platform-Foundation.md` and `docs/Badging-and-Scoring-Reference.md` get a major refactor/rewrite pass** to be *best and most current thinking* — synthesized, not appended. The standard: (1) every section reflects exactly what the rebuilt code does, why, and how; (2) zero conflicts between the two docs, zero conflicts with the code, zero conflicts between sections of the same doc; (3) zero duplication — if a concept is defined in one place, the other references it rather than restating. This is load-bearing under GP3 (Explainably Trustworthy), GP4 (Self-Evident Design), GP5 (Intelligence Compounds — never resets), and the "Best Current Thinking, Always" rule in `docs/collaboration-with-frank.md`. The rebuild is not complete until both foundation docs read like they were written from scratch today with full knowledge of what the rebuilt code does. Stale references to "the AI emits badges that the math scores" must be gone. Stale badge-keyed scoring mechanics must be gone. Fact drawer architecture, per-pillar Python scorers, and the post-scoring badging layer must be first-class in both docs. | Pending |

### §0d — What NOT to touch during the rebuild

| Don't touch | Why |
|---|---|
| UX (templates, CSS, layouts, the progress modal, Product Chooser, the hero widget, the three-box bottom row) | The rebuild is backend-only. User-visible behavior should stay identical until Step 5 cutover, at which point scores may move because the math is now fed better evidence — but no layout or flow changes. |
| `scoring_config.py` | All point values, caps, thresholds, penalties, rubric definitions, baselines, canonical lists. Define-Once stays untouched. |
| Top-of-pillar math: `compute_pillar_score`, `apply_ceiling_flags`, `get_technical_fit_multiplier`, `compute_fit_score`, `compute_acv_potential`, `detect_sandbox_api_red_cap` in `scoring_math.py` | Those operate above the dimension-score level. They compose dimension scores into pillar scores and apply global caps. They stay. Only `compute_dimension_score()` and its rubric sibling get deleted at Step 5. |
| The fact extractors from Step 2 | They work. Don't retune them during Step 3/4 work. If a fact is missing, add a new typed field to the dataclass and a new line to the extractor prompt — don't refactor the extractors themselves. |
| Everything in §1 and below | Pre-rebuild backlog. Valid work, on hold. |

### §0f — Full Pillar 1 walkthrough decision log (2026-04-08)

This is the complete record of every decision Frank and Claude locked in during the Chunk 1 Pillar 1 walkthrough on 2026-04-08. Captured here durably so Step 5.5 tuning, Step 6 full badging, and Step 8 docs rewrite all have a single authoritative source.

**Chunk 1 Issue #1 — Simulation hard override:**
- When the scorer picks Simulation as the fabric, ALL FOUR Pillar 1 dimensions get hard override values (normal dimension scoring is bypassed)
- Provisioning: **5** pts (`SIMULATION_PROVISIONING_POINTS`) — "low but nonzero, it's a fallback"
- Lab Access: **12** pts (`SIMULATION_LAB_ACCESS_POINTS`) — "middle" of the 25 cap
- Scoring: **0** pts (`SIMULATION_SCORING_POINTS`) — "no scoring for sims today, feature request not a capability. Will change as the product evolves."
- Teardown: **25** pts (`SIMULATION_TEARDOWN_POINTS`) — "full credit — you can't penalize teardown when there's nothing to tear down. Structurally equivalent to Datacenter automatic cleanup."
- Total Simulation Pillar 1 = 42/100 (Light Amber territory — "viable fallback but not the happy path")
- Implementation: `simulation_chosen` flag on `_DimensionResult` triggers the composer (`score_product_labability`) to call `_build_simulation_override_dimensions()` instead of the normal per-dim scorers.

**Chunk 1 Issue #2 — Fabric priority + optionality + VM reframing + container context:**
- Multi-fabric products need a WINNER plus visible OPTIONALITY, not a rigid priority list that silently drops alternatives
- `preferred_fabric` field added to `ProvisioningFacts` — the extractor's multi-factor judgment of which fabric best fits this product: (1) default to VM for lab developer control, (2) lean cloud when VM is resource-intensive or premium-cost, (3) use container only when production-native + no disqualifiers, (4) use vendor marketing preference as tiebreaker only when technical analysis is neutral
- `preferred_fabric_rationale` field captures the extractor's reasoning in plain English (traceable, usable in badge evidence text)
- Multi-fabric optionality bonus: `MULTI_FABRIC_OPTIONALITY_BONUS_PER_EXTRA = 3`, `MULTI_FABRIC_OPTIONALITY_BONUS_CAP = 6`. Secondary viable fabrics beyond the primary add bonus credit. Simulation does NOT count. Partial-granularity Sandbox API does NOT count.
- VM framing corrected: "performance issue" was too loaded. Renamed fields to `vm_is_resource_intensive` (big VM needing 16+ vCPU, 32GB+ RAM, specialized hardware) and `vm_has_premium_cost_profile` (meaningfully more expensive than cloud alternative). Added `vm_footprint_notes` narrative. Normal VMs stay False for both.
- Container context: added four documented disqualifier fields — `container_is_production_native` (positive when true), `container_is_dev_only`, `container_needs_windows_gui`, `container_needs_multi_vm_network`. Container is only viable when production_native=True AND none of the three disqualifiers fire. Added `container_footprint_notes` narrative.
- ESX handling: added `requires_esx` + `requires_esx_reason` fields. ESX fires as a separate amber anomaly badge alongside the VM primary badge when the product has a specific ESX constraint (nested virtualization, socket licensing).
- Lab Versatility cross-pillar hook: multi-fabric products should get a `multi_fabric_flexibility` signal in Pillar 2 Lab Versatility because more fabrics enable more lab design patterns. **Deferred to Step 5.5** — signal category not yet added to `_lab_versatility_rubric.signal_categories`.

**Chunk 1 Issue #3 — Badge coloring + naming rules:**
- **Color semantics locked:** Green = works (confidence, no action). Amber = uneasy, needs validation, SE should verify (never "risk" in that wording — "uneasy" is more honest). Red = cannot do this, or this specific thing cannot be done.
- **Multi-badge per dimension is legitimate:** e.g., `Teardown API` green + `Orphan Risk` amber fires together because the green names the positive finding and the amber names the specific concern. Both badges render in the same dimension card.
- **Badges name findings, not fixes:** the badge is the NOUN / what IS. Never prescribes action. Never says "the SE should do X."
- **Evidence text can include exploratory suggestions** framed as "Something to explore:" / "Worth investigating:" / "One path worth trying:". NEVER "The SE should", "You'll need to", "Recommendation: do X", "Best practice is". The finding is the badge; the action is the SE's call.
- **M365 End User products fire two badges:** `M365 Tenant` green (in Provisioning) + `Training License` amber (in Lab Access). Both in Lab Access originally, but Frank reframed M365 as a Provisioning fabric so `M365 Tenant` moved to Provisioning.
- **M365 Administration products fire two badges:** `M365 Admin` amber (in Provisioning) + `Training License` amber (in Lab Access). Different friction profile from End User.
- **M365 scoring numbers locked:** `M365 Tenant` = **+25** (one below VM/Cloud peer full credit because M365 scope is narrower than a general-purpose fabric). `M365 Admin` = **+18** (lower because the path has friction — trial account or MOC-provided tenant, possible credit card/MFA identity verification by Microsoft).
- **BYOC surfacing locked — Option C (multi-badge):** The existing `Sandbox API` canonical stays as the vendor-side finding badge. A NEW `Custom Cloud` gray strength badge fires alongside when Sandbox API is green or amber — context that names Skillable's operational capability without conflating finding and feature. Zero scoring impact (+0). Evidence text references the 10-phase BYOC workflow from `backend/knowledge/skillable_capabilities.json → byoc_custom_cloud_labs`.
- **Training License amber-bias — universal default locked:** Green is reserved for truly-zero-friction cases (open source, unlimited free tier, no concurrent user model, no tier choices). Most products — including M365 End User — fire Training License amber because real SE conversations happen around almost every non-trivial licensing arrangement (tier, count, add-ons, regional restrictions, commercial vs training license terms, existing customer agreements). **Partially implemented in Step 6-lite; universalization across all products deferred to Step 5.5.**
- **GCP handling — multi-badge pattern locked:** `No GCP Path` red + workaround fabric at amber when GCP is vendor-preferred. Simple amber case (needs_gcp=True without preferred=gcp) just fires `No GCP Path` amber without altering the primary fabric. Risk cap reduction handles the math (-8 per red, -3 per amber) — no ceiling flag needed. **Simple amber case shipped in Step 6-lite; full red+workaround nuance deferred to Step 5.5** (requires `preferred_fabric == "gcp"` detection + half-credit the workaround fabric signal).
- **Badge naming rules locked (D1–D5):**
  - **Restricted list** (never abbreviated or varied): canonical framework vocabulary (`Runs in VM`, `Runs in Azure`, `Runs in AWS`, `Runs in Container`, `Sandbox API`, `Training License`, `Orphan Risk`, `Pre-Instancing?`, `Custom Cloud`, `M365 Tenant`, `M365 Admin`, `No GCP Path`), product/company names (`Microsoft`, `Cisco`, `Trellix`), industry-standard acronyms (`REST API`, `OpenAPI`, `SSO`, `SAML`, `MFA`, `NFR`, `ATP`, `ALP`, `GPU`, `CPU`). **Never** "Cloud Slice" in badges (internal jargon). **Never** "Labs" in badges (obvious, redundant given the platform).
  - **Everything else** can be abbreviated freely: `Tech`, `Pro`, `Reco`, `Admin`, `Config`, `Auth`, etc.
  - **Max length:** ~25 chars / ~4 words. **Concise is the goal.** Variable-data badges (counts, names) can run slightly longer.
  - **Vendor acronyms:** ONLY when the vendor themselves uses an acronym. The extractor captures `vendor_official_acronym` from vendor marketing/docs evidence. **Never invented.** If the vendor doesn't use an acronym, keep the full name.
  - **Acronym format:** ALL CAPS, no periods (`TIE` not `T.I.E.`, `SCCM` not `S.C.C.M.`).
  - **Capitalization:** Title Case for badge words. Acronyms stay ALL CAPS.
  - **Absence-finding convention:** `No X` prefix (`No Training Partners`, `No Classroom Delivery`, `No Deployment Method`, `No GCP Path`, `No Independent Training`).
  - **No periods anywhere** in badge text — no trailing periods, no internal periods.

**Chunk 1 Issue #4 — GCP handling:**
- `No GCP Path` badge replaces the old `Requires GCP` amber-only badge
- Amber when: `needs_gcp = True` AND another viable fabric exists AND vendor doesn't strongly prefer GCP
- Red when: `needs_gcp = True` AND (GCP is required OR vendor's preferred fabric is GCP)
- Multi-badge pattern when red + workaround exists: red `No GCP Path` + workaround fabric at AMBER (half-credit, evidence notes "vendor prefers GCP, this is a workaround")
- Risk cap reduction handles the math organically (-8 per red, -3 per amber). No ceiling flag needed.
- **Simple amber case shipped; full red+workaround nuance deferred to Step 5.5.**

**Chunk 1 Issues #5–7 — code duplication:** The `_apply_risk_cap_reduction` helper, `_DimensionResult` dataclass, and `_verify_canonical_names` pattern are duplicated across `pillar_1_scorer.py`, `pillar_2_scorer.py`, and `pillar_3_scorer.py`. Deferred to Step 8 cleanup — not urgent, each copy is ~15 lines.

**Knowledge file additions (filed during the walkthrough, included in the bundled commit):**
- `backend/knowledge/skillable_capabilities.json` — four blocks:
  - `m365_tenants` (enriched from thin stub): End User vs Administration scenarios, three tiers (Base/E3, Full/E5, Full+AI/E7), full app matrix with optional add-ons, billing model, concurrent user increments, scoring-layer mapping
  - `microsoft_office` (new): SPLA-based classic Office apps (Standard/Pro, Visio, Project, versions 2016/2019/2021)
  - `byoc_custom_cloud_labs` (new): the operational pattern behind Sandbox API — Lifecycle Actions, Automated Activities, Custom Start Page, 10-phase workflow with explicit mapping to each Pillar 1 dimension, Salesforce working example reference
  - `software_licensing` (new): responsibility model, minimization strategies, known solutions (Windows Client/Server, SQL Server, Tableau), potentially-supported Microsoft products list (SharePoint Server, SCCM, Visual Studio, BizTalk, Dynamics 365, Exchange Server, TFS)
- **Scoring implication of these knowledge file additions:** INFO ONLY for now. Pricing stays out of the scoring intelligence entirely. `software_licensing` is not wired into any scorer. The potentially-supported Microsoft products list does NOT give products a scoring boost yet — deferred to Step 5.5 tuning if it turns out to matter.

### §0g — Known concerns after tonight's bundled commit

These are the honest self-assessment concerns after the bundled commit lands. Surfaced durably so a fresh session or future Claude can see them.

| # | Concern |
|---|---|
| **1** | **The cutover is SOFT, not HARD.** The monolithic Claude scoring call in `scorer.py` was stubbed in Step 5b-lite, but `scoring_math.py` still has `compute_dimension_score`, `_compute_rubric_dimension_score`, `compute_all`, and `detect_sandbox_api_red_cap` as dead code reachable from nothing in the new path. Full deletion is Step 5b proper. |
| **2** | **Metadata loss during the rebuild window.** Products built via the Step 5b-lite stub have empty `contacts`, `owning_org`, `lab_highlight`, `lab_concepts`, `deployment_model`, `orchestration_method`, `user_personas`, `recommendation`, `poor_match_flags`, `description`, `subcategory`, `product_url` fields (when not present on the selected_products entry). A dedicated lightweight metadata extractor at Step 5b proper restores them. |
| **3** | **The rubric grader has zero live validation.** 27 unit tests for `pillar_2_scorer` and `pillar_3_scorer` use canned `GradedSignal` lists. The rubric grader itself is untested with mocked Claude responses. First Trellix Deep Dive is the real validation. Watch for empty `Product.rubric_grades` / `CompanyAnalysis.customer_fit_rubric_grades` dicts in the saved JSON — that signals grader failure. |
| **4** | **Badge selector Pillar 2/3 pass-through hasn't been tested on real grader output.** The `_graded_signals_to_badges` helper naively prettifies `signal_category` with Title Case and ALL CAPS for a handful of acronyms. Real grader output may surface signal_category values that need special-case renaming. Trellix will show this. |
| **5** | **Cross-pillar reads in the rubric grader are partially inert.** The `vendor_published_on_third_party` and `multi_fabric_flexibility` signal categories are wired but depend on fact drawer fields that don't exist yet (`MarketDemandFacts.vendor_published_course_counts`, `multi_fabric_flexibility` in Lab Versatility rubric). Defensively handled via `getattr` defaults — grader returns empty for these categories. Not breaking anything, just not firing. Deferred to Step 5.5. |
| **6** | **Step 5.5 Pillar 1 tune items** (see §0c Step 5.5 row): cosmetic renames, full GCP multi-badge nuance, Training License universal amber-bias generalization, multi_fabric_flexibility cross-pillar, vendor_official_acronym wiring — all deferred and captured. |
| **7** | **Step 6-lite evidence text uses canned strings for Pillar 1 badges.** Each canonical Pillar 1 badge has a fixed evidence text template in `badge_selector.py`. Step 6 full should generate evidence text from the actual fact drawer content for each specific product. |
| **8** | **Three old canonical badges from the pre-refinement era still exist in `scoring_config.py` and `scoring_math.py`:** `Runs in Hyper-V` (should become `Runs in VM`), `Pre-Instancing` (should become `Pre-Instancing?`), `Requires GCP` (replaced by `No GCP Path`). The NEW badges were added without deleting the old ones. Step 5.5 does the rename + delete cleanly. For now the scoring works because the extractor still uses the old names for inputs. |

---

## §1 — Search Modal Migration (demoted from §0 by the rebuild — still valid)

The Standard Search Modal unification is half-done. `discovering.html` was migrated in commit `e6784dc` (2026-04-07 late evening). `scoring.html` — the Deep Dive progress page — is still on its 417-line legacy custom implementation. Picks back up after the rebuild lands.

| Item | Description |
|---|---|
| **Migrate `scoring.html` to the shared `_search_modal.html`** | Deep Dive must render through the one shared modal like every other long-running flow. `scoring.html` currently has its own custom CSS, custom EventSource handler, rotating hint messages, three-stage "orchestration bars," and a research-to-Claude phase transition — all of which must move into a "deep dive" variant of the shared modal's middle section. Pattern to follow: the `discovering.html` migration in commit `e6784dc` (41-line shell that imports the shared modal, calls `openSearchModal()`, and wires the SSE stream). The SSE contract (`status:` / `done:` / `error:`) is already compatible — no backend changes should be needed, only template + frontend work. After migrating, delete the legacy `scoring.html` custom UI and add a regression test in `tests/test_ux_consistency.py` that scans Inspector templates for "custom progress" patterns (any `new EventSource(` outside `_search_modal.html`). Frank 2026-04-07: "We should not have multiple search. There should be one search modal, and the middle is the part that should be different." |

---

## §1 — Frank's QA-pass backlog (carry-over from 2026-04-06 + 2026-04-07)

These came out of Frank's review of dossiers across the 2026-04-06 and 2026-04-07 sessions. Concrete, ready to pick up. None blocked on SE clarifications.

| Item | Description |
|---|---|
| **M365 Provisioning canonical** | The M365 tenant provisioning capability (E3 / E5 / E7 — see `skillable_capabilities.json` `m365_tenants` block) is currently underrepresented in Provisioning scoring. M365-dependent products (Microsoft 365, Defender for Office 365, Purview, Copilot, etc.) should benefit from a clean canonical or scoring path that recognizes Skillable's automated M365 tenant provisioning via Azure Cloud Slice. **Today the AI doesn't know to credit M365-tenant-dependent products for this Skillable strength.** Investigate where to land it: a new Provisioning canonical badge (e.g., `M365 Tenant`) or a refinement of the existing `Runs in Azure` to recognize M365 as a first-class case. Frank §0.1. |
| **Company Description consistency** | The Company Description field renders differently on the Product Selection page vs the Full Analysis (Deep Dive) page — different font, different position, possibly different content. Should be consistent: same field, same source of truth, same rendering treatment, same prominence. Audit both pages and unify. Frank §0.3. |
| **Briefcase box size + alignment** | The three Sales Briefcase boxes (Key Technical Questions / Conversation Starters / Account Intelligence) don't render with consistent box sizes or alignment. They should match each other in width, height (or min-height), padding, and vertical alignment. Affects visual polish and seller credibility. Frank §0.4. |
| **Briefcase bolding + phrasing standard** | The three Sales Briefcase sections use inconsistent bolding patterns and phrasing styles. Need a documented standard for what gets bolded (entity names? action items? vendor terms?) and how each section's bullets are phrased (sentence length, tone, opening pattern). Land the standard in the prompt template for each of the three briefcase generators (Opus KTQ, Haiku Conv, Haiku Intel) so they produce consistent output. Frank §0.5. The 2026-04-07 commit `c91b819` already locked the routing rule (KTQ technical / Conv Starters strategic / Acct Intel leaders) — this item is the formatting half. |
| **Bottom three boxes consistency pass** | The three boxes in the bottom row of the Full Analysis page (Scored Products / Competitive / ACV by Use Case) need a consistency pass: font, font size, vertical spacing, column spacing, padding, alignment. They should feel like one designed row, not three independent components. Audit all three and unify. Frank §0.6. |
| **ACV Table polish** | The ACV by Use Case table needs three things landed together: (a) **Motion names below the row** instead of as the leftmost column, or as a clearer label treatment so the seller can scan the row easily; (b) **Logic for audience size** — better grounding for the AI's per-motion population estimates, anchored to vendor scale signals (links to §5.5 ACV review); (c) **Logic for lab rate per hour** — the rate selection logic should be transparent and auditable, with a clear mapping from orchestration method to rate tier. Frank §0.7. The five canonical motions: Customer training/enablement (direct), Training partner programs, Certification programs, Employee enablement, Events & Conference. (Worth reconciling against `CONSUMPTION_MOTIONS` in `scoring_config.py` — Frank's labels here may be the better naming.) |
| **Product Family Picker — cache awareness** | When a discovery has multiple product families and the family picker fires, the picker doesn't know what's in the cache. The user picks a family blind, without knowing which one would re-use cached scoring vs trigger fresh scoring. **Fix:** decorate each family chip with a `(N cached)` count so the user can pick the cache-leverage option. Frank flagged 2026-04-07 evening. |
| **Product Family Picker — interstitial position + threshold** | The picker currently renders ON the Product Selection page; the spec calls for a separate interstitial step BETWEEN discovery completion and Product Selection. Threshold is 30; should be 20 per Frank's 2026-04-06 directive. And: the "focused discovery" step (a second discovery pass scoped to the family) doesn't exist yet — today picking a family just filters the existing discovery. Decide: implement focused-discovery, or keep filter-only behavior and update the spec to match. Frank §0a. |

---

## §2 — Mid-priority deferred work (still relevant near-term)

| Item | Description |
|---|---|
| **Reusable doc-icon modal — per-product report** | The `?` icons next to each pillar are wired to the info modal for per-pillar WHY/WHAT/HOW. The doc icons next to each product are still decorative — they need to open the same modal but populated with a per-product report. Modal infra is ready (`openInfoModal(key)` accepts `{eyebrow, title, sections}`). **Open question:** what IS the per-product report content? Three options: (a) formatted summary of three pillars + verdict + ACV widget data; (b) Word doc export content rendered in HTML for preview; (c) new "executive briefing" view we haven't built yet. Design first, then build. |
| **Refresh button bug** | The Refresh button on Full Analysis (`tools/inspector/templates/full_analysis.html` ~L479) fires `POST /inspector/analysis/<id>/refresh`, gets back a `job_id`, then runs `window.location.href = '/inspector/score/progress/' + job_id`. That URL is the SSE endpoint — navigating to it renders the raw SSE event stream as text in the browser. Fix: redirect to the existing scoring waiting page (`scoring.html`) with the job_id, not the raw SSE endpoint. ~10 min. |
| **Move INFO_MODAL_CONTENT to scoring_config** | The per-pillar WHY/WHAT/HOW + ACV by Use Case explanation lives as a JS object literal at the top of `full_analysis.html` (`INFO_MODAL_CONTENT`). Should live in `scoring_config.py` (preferred — Define-Once) or a new `docs/explainability-content.md` consumed via a Jinja filter, so non-engineers can edit explainability text without touching the template. ~30 min. |

---

## §3 — Render deployment prep

Get the current build into a state Frank can share with a couple of people via the existing Render service.

| Item | Description |
|---|---|
| **Pre-flight audit** | Read-only audit of (a) how secrets are loaded today, (b) every place the cache writes to disk, (c) any other filesystem writes. Report back so we know exactly what changes need to land. |
| **Entry point** | Add `gunicorn` to `requirements.txt`. Render start command becomes `gunicorn backend.app:app`. Verify the Flask app object is importable as `app`. |
| **Persistent file storage decision** | Current cache writes to local disk; Render's filesystem is **ephemeral** and wipes on every deploy/restart. Three options: **Render Disk** (~$1/mo, 5-min setup, recommended for "share with a couple people"); **Postgres on Render free tier** (better long-term, more setup); **Accept ephemeral cache** (fine for pure demo, analyses regenerate on demand). |
| **Background threads** | Briefcase generation runs in a background thread. Survives normal operation but is lost if the worker restarts mid-generation. Acceptable for demo. Document the limitation. |
| **Secrets audit** | Confirm `ANTHROPIC_API_KEY` (and any other keys) are read from `os.environ` only. No hardcoded keys, no `.env` files committed. Quick grep before pushing. |
| **Auth gate** | The previous Render site's access posture is unknown. For sharing with a couple people: basic password gate (Flask middleware) / Render's built-in auth / IP allowlist. Decide before going live. |

---

## §4 — Standard Search Modal (designed; partially shipped via stale-cache modal)

The full design is in this doc's appendix. The 2026-04-07 stale-cache modal commit (`7c69eb1`) shipped the partial pattern (decision mode + transition to progress) — it's the right time to formalize the contract and use it everywhere.

| Item | Description |
|---|---|
| **Build the publisher** | `backend/progress.py` and a fake operation that emits events on a timer. Verify the contract works against the existing modal. |
| **Wire Discovery first** | Simplest operation, proves the integration pattern. |
| **Wire Deep Dive** | The operation that needs honest progress most. Pairs naturally with §5 Deep Dive performance work. |
| **Wire Prospector batch** | When batch scoring lands. |
| **Retire per-tool progress UIs** | Single cleanup pass once everything is on the standard modal. |

---

## §5 — Deep Dive performance rework

Frank observed during the 2026-04-06 Diligent test: Deep Dive zips through products 1, 2, 3, 4 in under a minute, then **sits on 4/4 for a long time** before the page is ready. The progress bar lies because per-product progress events fire as queries are dispatched, but the real bottleneck is at the tail.

| Item | Description |
|---|---|
| **Instrument the deep dive** | Add timing logs at each stage boundary so we know empirically where the 4/4 hang lives. Don't tune blind. |
| **Replace the products counter** | Stage-aware progress: `Searching → Fetching → Scoring → Ready` instead of "4/4". |
| **Per-fetch timeout** | 5–8 second hard cap in `_fetch_pages_parallel`. Fail fast and move on — missing one page is fine. |
| **Stream scored products** | Stream results to the page as each product finishes scoring. Don't wait for the slowest one. Show "Scoring 3/4 complete" instead of static "4/4". |
| **Sonnet vs Haiku for first-pass scoring** | Test on 2-3 known companies. Is per-product Sonnet necessary, or does Haiku get us 95% there for a fraction of the time? |

---

## §5.5 — ACV calculation review (HIGH PRIORITY)

The deterministic ACV math is **doing the math correctly** but the **inputs from the AI are coming out way too low** for global vendors with large user bases. Confirmed undersized cases: Cohesity ($34K–$167K total ACV across 2 of 15 products — should be hundreds of thousands to low millions), Epiq Discover (similar undersizing pattern).

| Item | Description |
|---|---|
| **Pull Cohesity raw scorer JSON** | Inspect each motion's `population_low/high` and `adoption_pct`. Are they realistic for a vendor of Cohesity's size? |
| **Compare to benchmarks** | `backend/benchmarks.json` lists Cohesity with relationship/scale signals. The AI should be using those signals to inform population sizing. |
| **Audit CONSUMPTION_MOTIONS prompt guidance** | The adoption ceiling rules and population guidance. Are we instructing the AI to "be conservative" in a way that produces unrealistically small numbers? |
| **Add anchor companies** | 3-5 known companies with hand-validated population/adoption estimates to test fixtures. Run scoring, compare AI output to anchors. Anything more than ~25% off is a flag. |
| **Hero display semantics decision** | The hero shows `$34K–$167K` with subtext "Across 2 scored of 15 discovered products" — the headline number represents 13% of the portfolio but visually presents as the answer. Either: extrapolate to full-company estimate; reword the label as clearly partial; or score all products by default. |

**Why HIGH:** ACV is the dollar number sellers and execs see first. If it's wrong by 5–10x, it undermines trust in the whole platform.

---

## §6 — Smaller carry-overs

Full descriptions live in `docs/roadmap.md`. Pull from there when starting.

| Item | Description |
|---|---|
| **Migrate Designer + Prospector off legacy templates** | Both still use `_nav.html` / `_theme.html` with hardcoded hex. Migration to the new shared theme. Deferred until the new Designer code push lands. Roadmap §D + §C. |
| **Update Foundation docs with new architecture** | Sync forward: PL floor, technical fit multiplier, ceiling flags, deterministic ACV math, locked rate variables, the Layer Discipline principle, the rubric model architecture, Phase F Customer Fit centralization. Most of it lives in the decision log — sync it forward. |
| **Comprehensive scoring framework alignment review** | Walk every scored field against `Badging-and-Scoring-Reference.md` and confirm no drift between docs / config / math / template / cached data. |
| **Audit other ceiling-flag-implied synthetic badges** | `bare_metal_required` and `no_api_automation` could follow the same pattern as the (now-removed) `No Learner Isolation` injection. Decide whether to reintroduce. |

---

## SE Clarification Queue — answers needed from a sales engineer

Three open SE questions remain from the 2026-04-06 session. SE-4 was resolved tonight when the Sandbox API red Pillar 1 cap shipped (Diligent five fixes commit `8b9d6be`).

| # | Question | Why it matters |
|---|---|---|
| **SE-1** | **Bare Metal Required** — when evaluating a vendor product, what specific signals in their docs or marketing tell us "this requires bare metal hardware orchestration that we can't virtualize"? Examples of products that hit this — what gave it away? | Today the AI guesses at this. We need detection signals for the canonical `Bare Metal Required` red Blocker badge so it fires reliably and doesn't fire spuriously. Lands in `prompts/scoring_template.md` Pillar 1 + possibly new research queries in `researcher.py`. |
| **SE-2** | **Container Disqualifiers** — we have four documented disqualifiers (dev-use-only image, Windows GUI required, multi-VM network, not container-native in production). Which is the most common practical reason to skip containers? When Windows is needed, is "Windows container" ever the right call, or do we always default to a Windows VM? | Pillar 1 has `Runs in Container` as a green/amber/don't-emit canonical, but the disqualifier list needs SE input to be sharp enough for the AI. Lands in `prompts/scoring_template.md` under the `Runs in Container` canonical. |
| **SE-3** | **Simulation Scorable** — when a lab is delivered via Simulation, when CAN we score it (via AI Vision) and when CAN'T we? Should `Simulation Scorable` ever be a red blocker, or is it always green/amber depending on what's visible on screen? | The `Simulation Scorable` canonical is currently amber-only. The answer determines whether we add a red state and what triggers it. Lands in `scoring_config.py` `_scoring_badges` + `prompts/scoring_template.md` Pillar 1 Scoring section. |

---

## Roadmap-only HIGH items (carry from `docs/roadmap.md`)

These live in the roadmap but should be in active rotation soon.

| Item | Description |
|---|---|
| **Variable-driven badge logic across all 3 pillars** | Extend the variable-badge rule pattern from Provisioning to every dimension across all three pillars. Test case: Epiq Discover — verify variable-driven badge names appear correctly in all three pillars, not just Provisioning/Lab Access. |
| **Discovery tier assignment refinement** | The Seems Promising / Likely / Uncertain / Unlikely assignment needs refinement. Test case: Epiq Discover — initial product search is putting products in the wrong tier in some cases. Revisit discovery scoring thresholds + prompt guidance + initial-pass signals. |
| **Finalize WHY/WHAT/HOW story for ? modal + doc modal** | The reusable info modal has placeholder content for Product Labability, Instructional Value, Customer Fit, and the ACV by Use Case widget. Each pillar's WHY/WHAT/HOW needs to be tight enough that a seller reads it in 30 seconds and walks away understanding the pillar. Pairs with the Skillable capabilities propagation work and the doc-icon report wiring. |
| **Skillable customer identification UX** | When the company being analyzed is already a Skillable customer, the UI should make that visually obvious — both on Product Selection and on Full Analysis. Drives different seller conversation (expansion vs acquisition). Source-of-truth question (decision needed): how do we know which companies are customers? CRM lookup? Static config? HubSpot integration? |
| **CTF in Lab Versatility** | Verify CTF (Capture The Flag) is one of the 12 lab types in `LAB_TYPE_MENU` with the right product category mappings (cybersecurity, security training, offensive security tooling). If it's there but named ambiguously, rename to "CTF / Capture The Flag". CTF is a primary lab format for cybersecurity training and needs to be a first-class option, not buried under "Cyber Range" or "Simulated Attack." |

---

## Deferred / shipped already (do not redo)

The historical record of what's been shipped is split: the 2026-04-06 session shipments are in this doc's "Shipped recently" section below; the 2026-04-07 evening shipments are listed in `docs/decision-log.md`.

Highlights from the 2026-04-07 evening session:

| Commit | What shipped |
|---|---|
| `00123cc` | Risk Cap Reduction — Pillar 1 dimensions can never be at full cap when amber/red risks present (-3 amber, -8 red as cap reduction, not deduction) |
| `a6f7b74` | Customer Fit unification across products (interim merge — Phase F was the proper fix below) |
| `8b9d6be` | Diligent Five Fixes: SE-4 Sandbox API cap (25/5), Datacenter excludes Simulation + new Simulation Reset gray badge, Scoring breadth Grand Slam rule, Fit Score floor drop, Pillar 2/3 prompt sharpening |
| `7c69eb1` | Stale-cache decision modal on Product Selection → Deep Dive |
| `7bb8d04` | Pillar 3 badge JUDGMENT rule — forbidden generic names (`Build vs Buy`, `DIY Labs`, etc.) + judgment-form alternatives (`Light Content Dev`, `Few Tech SMEs`, `Long RFP Process`, `Soft Skills Focus`) |
| `9e5d174` | Account Intelligence prompt — time-bounded events (Elevate-style) as TOP recommendations with concrete next-step actions and Skillable framework anchoring |
| `c91b819` | Briefcase routing rule — KTQ targets technical engineers only (Principal Engineers, API leads, SAs, SEs, customer onboarding); Conversation Starters target strategic VPs/Directors/CLOs; Account Intelligence targets named leaders + named events |
| `b5c981d` | Phase F — Customer Fit lives on the discovery (`discovery["_customer_fit"]`), `intelligence.score()` writes it at every save boundary, `intelligence.recompute_analysis()` reads from there first with per-product merge as fallback |
| `a414723` | Phase 4 creative test strategy — Category 11 with all 10 test classes (round-trip, idempotence, vocabulary closure, bold prefix, cache stamp, pillar isolation, polarity, adversarial, layer discipline AST, define-once string scan). 27 new tests, 115 total passing, pre-commit hook enforces. |

Decisions logged tonight (see `docs/decision-log.md` for details): Layer Discipline as a stated principle; Risk Cap Reduction calibration (-3/-8); Customer Fit unification with "best showing wins" merge rule; legacy quarantine of `_new` suffix files; Phase F as the canonical CF home; Diligent Five Fixes; the stale-cache modal trigger; the Pillar 3 judgment rule (badges as findings, not topics); the briefcase routing rule.

---

## Standard Search Modal — design plan (reference for §4)

A single, reusable progress modal used by **every** long-running operation in the platform: Discovery, Deep Dive, Prospector batch scoring, Designer research, future workflows. Today each tool reinvents its own progress UI; this consolidates to one component, one source of truth, one visual language.

### Why one modal

- **Consistency** — users learn it once
- **Define-Once** — one place to fix bugs, tune timings, change copy
- **Honest progress** — current bars lie because each tool implements progress differently. A standard modal forces a standard progress contract.
- **Real estate** — modal overlays the page being worked on, so users keep their context. No full-page route changes.

### Visual structure

```
┌────────────────────────────────────────────────────────────┐
│  ANALYZING DILIGENT                                    ×   │   ← title + close (close = cancel)
│  Deep Dive · 4 products                                    │   ← operation type + scope
├────────────────────────────────────────────────────────────┤
│   ●━━━━━━━●━━━━━━━●━━━━━━━○━━━━━━━○                       │   ← stage stepper (5 stages)
│   Discover  Search  Fetch  Score   Ready                   │
│   Currently: Scoring product 3 of 4                        │   ← live status line
│   Diligent Boards · Diligent One · HighBond · Galvanize    │   ← per-item live state (✓ ✓ ⏵ ○)
│   Elapsed: 1m 24s · Est. remaining: ~30s                   │   ← time signals
│   [────────────────────────────────] 78%                   │   ← optional fine-grained bar
│   ▸ Activity log (collapsed)                               │   ← optional verbose log
└────────────────────────────────────────────────────────────┘
```

### State contract — every operation publishes this shape

```json
{
  "operation_id": "uuid",
  "operation_type": "deep_dive | discovery | prospector_batch | designer_research",
  "title": "Analyzing Diligent",
  "subtitle": "Deep Dive · 4 products",
  "stages": ["Discover", "Search", "Fetch", "Score", "Ready"],
  "current_stage_index": 3,
  "current_status": "Scoring product 3 of 4",
  "items": [
    {"name": "Diligent Boards", "state": "done"},
    {"name": "Diligent One", "state": "done"},
    {"name": "HighBond", "state": "active"},
    {"name": "Galvanize", "state": "pending"}
  ],
  "elapsed_seconds": 84,
  "estimated_remaining_seconds": 30,
  "progress_pct": 78,
  "log_lines": ["..."],
  "terminal_state": null
}
```

`terminal_state` is `null` until done; then one of `success | partial | error | cancelled`.

### Where it lives in code

```
tools/shared/templates/
  _search_modal.html          ← markup + scoped styles (uses theme vars only) — already exists
  _search_modal.js            ← SSE subscription, DOM updates, lifecycle — already exists in macro form
backend/
  progress.py                 ← shared event publisher (operation_id → SSE channel) — TO BUILD
```

Each operation (`research_products`, `discover_products`, etc.) gets a `ProgressPublisher` injected. It calls `publisher.stage("Search")`, `publisher.item("Diligent Boards", "done")`, `publisher.status("Scoring 3 of 4")`. The publisher fans out to the right SSE channel by operation_id.

### Behavior rules

1. Modal overlays the current page — does not navigate away
2. Cancel kills the operation — backend honors cancellation tokens, no orphaned work
3. On success: dismiss + reload page (or call `on_complete`)
4. On error: stay open, show error in red, offer Retry
5. Stage stepper shows truth, not lies — stages only advance when the stage actually completes server-side
6. Time estimates use rolling history — measure last N runs, show median
7. Activity log is opt-in — collapsed by default
8. Mobile/narrow — stage stepper collapses to a single "Stage 3 of 5: Scoring" line

### Out of scope for first build

- Multi-operation queue (one operation at a time is fine)
- Operation history view (separate feature)
- WebSocket — SSE is sufficient

---

## Open questions (none blocking)

| Question | Notes |
|---|---|
| **Per-product report content for the doc-icon modal** | Three options in §2 — formatted three-pillar summary, Word doc preview, or new "executive briefing" view. Design first, then build. |
| **Other ceiling-flag-implied synthetic badges** | `bare_metal_required` and `no_api_automation` could follow the No Learner Isolation pattern (the latter has been removed). Reintroduce that pattern or skip? |
| **Designer + Prospector tools still on legacy `_nav.html` / `_theme.html`** | Migration is queued but timing depends on the new Designer code push. |
