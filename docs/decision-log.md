# Decision Log — Skillable Intelligence Platform

Each entry captures decisions made during a working session. Newest entries first.

---

## Session: 2026-04-07 evening — Pillar 1 risk caps, CF unification, prompt sharpening, Phase F, Phase 4 tests

A long late-night session covering scoring math refinements, prompt sharpening for Pillars 2/3 + the Sales Briefcase, the Customer Fit centralization (Phase F), and the creative test strategy (Category 11). Commits referenced inline.

### Risk Cap Reduction — Pillar 1 dimensions can never be at full cap when amber/red risks present
- **DECIDED:** When a Pillar 1 dimension surfaces amber or red risk badges, the dimension's effective cap is reduced (not the score deducted, the cap itself lowered): -3 points per amber risk badge, -8 points per red risk badge.
- **Why a cap reduction, not a deduction:** the existing color-aware math already deducts color points for amber/red badges. Doing a second deduction would double-count. Lowering the cap means the dimension can still earn green credits but can never reach its full theoretical max while risks are present — which is what "risk" actually means in business terms.
- **Calibration source:** Frank, after reviewing Trellix and Diligent dossiers — the dimensions that should "never feel clean" with red present were still showing high scores via green offsets. Capping forces the visible score to honor the worst-case finding.
- **Constants:** `cfg.AMBER_RISK_CAP_REDUCTION = 3`, `cfg.RED_RISK_CAP_REDUCTION = 8` in `scoring_config.py`.
- **Commit:** `00123cc`.

### Customer Fit unification — best-showing wins, broadcast across all products
- **DECIDED:** Customer Fit is a property of the **organization**, not the product. Every product from the same company must show **identical** Pillar 3 dimensions, scores, and badges. The merge rule is **"best showing wins"** (Option B): when two products surface different evidence for the same CF signal_category, the stronger color + stronger strength wins, and that single best version broadcasts to every product.
- **Why best-showing wins:** the alternative (worst-of-group) made every product look as bad as the worst-researched product, which punished CF for incomplete evidence. Best-showing aligns with how a seller actually frames the conversation — "what we know about this company at its best."
- **Frank's framing:** "Customer Fit measures the organization, not the product. Every product from the same company must show identical Pillar 3."
- **Initial implementation (commit `a6f7b74`):** an interim merge inside `recompute_analysis()` that built the unified CF from the analysis's products and broadcast it onto every product. This worked but Frank flagged it as the wrong architectural home — see Phase F below.

### Phase F — Customer Fit lives on the discovery, owned by the Intelligence layer
- **DECIDED:** The canonical home for the unified Customer Fit is `discovery["_customer_fit"]`, written by `intelligence.score()` at every save boundary, read by `intelligence.recompute_analysis()` at every page load. Inspector / Prospector / Designer all read from this one place. The interim per-analysis merge becomes a fallback for legacy data.
- **Why move it from analysis to discovery:** discovery is the company-level concept; analysis is the per-Deep-Dive concept. Customer Fit is a company-level property. Every Deep Dive on the same discovery (even months apart, across Inspector + Prospector + Designer) should see the same CF — and it should be computed once, not re-merged on every page load.
- **Lookup order in `recompute_analysis()`:**
  1. `discovery["_customer_fit"]` — canonical Phase F home
  2. `_build_unified_customer_fit(products)` — fallback for legacy analyses whose discovery hasn't been stamped, or for the pre-save window inside `score()` before aggregate has run
- **Layer Discipline note:** `aggregate_customer_fit_to_discovery()` lives in `intelligence.py`, not `app.py` — it's intelligence work that all three tools need, not Inspector-specific orchestration.
- **Commit:** `b5c981d`.

### Diligent Five Fixes — five distinct scoring + badging refinements shipped together
- **DECIDED (1):** Sandbox API red caps Pillar 1 hard. When the Sandbox API canonical fires red on a SaaS product, Pillar 1 is capped at **25** if Simulation is viable (the next-best path) and at **5** if nothing is viable. Constants: `cfg.SANDBOX_API_RED_CAP_SIM_VIABLE` and `cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE`. This is the SE-4 answer Frank approved by inspection of Diligent's earlier 66-point Pillar 1.
- **DECIDED (2):** Datacenter excludes Simulation. The Datacenter badge previously fired even on Simulation-only products; now Simulation is excluded from the Datacenter set. A new gray `Simulation Reset` badge with 0 points is emitted in Teardown for Simulation products to surface the teardown story without crediting it.
- **DECIDED (3):** Scoring breadth rule (the "Grand Slam" rule). MCQ alone = 0 points. AI Vision alone caps at 10 (`cfg.SCORING_AI_VISION_ALONE_CAP`). Script alone = full marks (VM context). Scoring API alone caps at 12 (`cfg.SCORING_API_ALONE_CAP`). **Grand Slam (AI Vision + Script OR API) = full marks** — the breadth bonus credits the combined scoring surface, not the individual methods.
- **DECIDED (4):** Drop the Fit Score floor. The previous formula was `fit_score = max(weighted_sum, pl_score)`, which let strong PL pull the Fit Score above its weighted-sum value. Now the formula is the pure weighted sum. Frank's framing: "if Customer Fit is bad, the Fit Score should be allowed to reflect that — even on a great product."
- **DECIDED (5):** Pillar 2/3 prompt sharpening — three new rules in `prompts/scoring_template.md`: strength grading discipline (don't hedge to moderate; force STRONG for high-stakes domains like governance/cybersecurity/healthcare); subject-matter-specific badge names (not generic templates); emit gap badges (red) when grading low to make judgment visible.
- **Commit:** `8b9d6be`.

### Pillar 3 badges must convey JUDGMENT, not describe categories
- **DECIDED:** Customer Fit badges must read as findings about the customer, not as category labels. "Build vs Buy" is not a finding — it's a topic. "Platform Buyer" or "In-House Builder" are findings. The prompt now carries an explicit FORBIDDEN list of generic structural names (`Build vs Buy`, `DIY Labs`, `Content Dev Team`, `Partner Ecosystem`, `Integration Maturity`, `Ease of Engagement`, `Lab Platform` as a label, `Training Culture`, `Certification Program`, `Training Catalog`) with required judgment-form alternatives for each.
- **The three permitted shapes** for every Pillar 3 badge:
  1. **A counted/named specific** (`~500 ATPs`, `Elevate 2026`, `Skillable`, `Series D $200M`)
  2. **A judgment phrase** (`Light Content Dev`, `Few Tech SMEs`, `Long RFP Process`, `Soft Skills Focus`, `Slide-Deck Culture`, `Compliance-Only Training`)
  3. **An explicit gap** (`No Lab Authors`, `No Documented ATPs`, `No Tech Writer Team`)
- **Forcing function:** if the AI cannot produce one of those three shapes for a dimension's evidence, it must re-read the dossier — it doesn't understand the evidence well enough to emit a badge.
- **Frank's framing:** "Customer Fit badges need to show judgement. Light Content Dev, Soft Skills, Long RFP Process, Few Tech SMEs... Something like that."
- **Commit:** `7bb8d04`.

### Account Intelligence — time-bounded events as TOP recommendations with concrete actions
- **DECIDED:** When the scoring evidence mentions a specific conference, flagship event, certification launch, product release, or other time-bounded signal, that bullet should be FIRST in Account Intelligence and must include three things: (1) the named event with date if known; (2) a concrete person/role to find ("the head of Elevate 2026"); (3) WHY it matters as a specific Skillable opportunity, anchored to the framework: "Events are Skillable's lowest-friction consumption motion — defined audience, defined timeline, no incumbent platform to displace."
- **Worked example for Diligent's Elevate 2026** is in the prompt as the WEAK vs STRONG side-by-side.
- **Frank's framing:** "If you go down to account intelligence — find out who's running that event. Like, who's the Elevate 2026 conference. It's phenomenal place for us to start by having hands-on experiences at events."
- **Commit:** `9e5d174`.

### Briefcase routing rule — KTQ technical / Conv Starters strategic / Acct Intel leaders
- **DECIDED:** The three Sales Briefcase sections target three non-overlapping audiences:
  - **Key Technical Questions** target TECHNICAL ROLES ONLY: Principal/Staff Engineer, API Team Lead, Solution Architect, Sales/Solution Engineer, Customer Onboarding Engineer, DevRel, SRE, product team technical lead. **NEVER target VPs, Directors, CLOs, or any pure-management role** — forwarding "does the REST API support DELETE on user records?" to a VP wastes the seller's credibility.
  - **Conversation Starters** target STRATEGIC LEADERS: VPs of Customer Education / Training / Customer Success, Directors of Enablement, CLOs, VPs of Product. Talking points must be VP-respondable ("yeah, that's exactly why we're doing X"), framed around business outcomes (retention, time-to-productivity, certification pass rates, NRR, churn risk). Never technical.
  - **Account Intelligence** targets named leaders + named events.
- **Why explicit role lists:** the previous prompts said "technical champion" without naming roles, and the AI was emitting "ask the VP of Customer Education..." for technical API questions. Explicit ✅/❌ lists in the prompt force compliance.
- **Frank's framing:** "If you want a technical question, that's how are we gonna get your labs into Skillable? You don't wanna be talking to director-level people and VPs of customer education... principal engineers, API team leads... solution architects, solution engineers, sales engineers... people that help with customer onboarding... VPs and things, that's in conversation starters. And account intelligence — that's where you wanna know the leaders."
- **Commit:** `c91b819`.

### Stale-cache decision modal on Product Selection → Deep Dive
- **DECIDED:** When a user clicks Deep Dive on a Product Selection page whose existing cached analysis was scored with an older `SCORING_LOGIC_VERSION`, intercept the form submit and show a confirmation modal: **Refresh first** / **Use cached** / Cancel. Once the user has made a choice on a given page load, a second click of Deep Dive goes through without re-prompting.
- **Why:** Frank reported clicking Deep Dive on cached Diligent and the system silently re-scored without giving him a choice. The cache versioning gate was right (the data WAS stale) but the user lost agency over the decision. The modal preserves the gate's correctness while restoring the choice.
- **Implementation note:** the same modal partial (`_search_modal.html`) that powers the Full Analysis stale-cache modal is now imported on Product Selection. Buttons relabeled from the default "Refresh / Ignore for now" to "Refresh first / Use cached" because "Ignore for now" reads ambiguously in a submit-intercept context.
- **Commit:** `7c69eb1`.

### Phase 4 — creative test strategy (Category 11) — 27 tests across 10 classes
- **DECIDED:** Implement all 10 test classes from `docs/code-review-2026-04-07.md §"Phase 4 — creative test strategy"`. The 88 existing structural tests would not have caught any of the CRITICAL findings from the deep code review — they assert config shape, not the integration paths between layers. Category 11 walks every saved analysis on disk plus a battery of synthetic in-memory fixtures and asserts runtime invariants that span layers.
- **The 10 test classes** (full descriptions in `docs/Test-Plan.md` Category 11): round-trip badge identity (Pillar 3 exempt for Phase F unification), recompute idempotence, vocabulary closure, bold prefix doesn't leak (against the recomputed view, not raw JSON), cache stamp truth, pillar isolation, polarity invariants, adversarial fixtures, layer discipline (AST), define-once enforcement (string constants only).
- **Auto-skip stale fixtures:** `_load_saved_analyses(current_only=True)` skips any saved analysis whose `_scoring_logic_version` doesn't match the current — those are queued for re-score by the cache versioning gate, so it isn't fair to enforce current architectural rules against them.
- **Render-time normalization:** tests check the **recomputed view** (what the user actually sees), not the raw saved JSON, because Phase 1 normalization runs at render time by design.
- **Frank's framing:** "would love you to finish all these tests... they're so important for keeping us from making architecture mistakes."
- **Commit:** `a414723`. 27 new tests, 115 total passing (was 88).

### Legacy quarantine — drop the `_new` suffix from the entire active code path
- **DECIDED:** The `_new` suffix (`app_new.py`, `intelligence_new.py`, `scorer_new.py`, `data_new/`) was a transitional convention while the rebuild was in flight. With the rebuild complete and the legacy POC code moved to `legacy-reference/`, the suffix is now a documentation-rot risk — every file that references "the new code" goes stale the moment "new" stops being new. Drop the suffix everywhere and reference the canonical names (`app.py`, `intelligence.py`, etc.).
- **Commits:** `e2620b0` (rename), `9f44222` (sync session-opening docs).

---

## Session: 2026-04-06 — Universal variable-badge rule

### One rule, two vocabularies, applied universally
- **DECIDED:** When a finding warrants multiple badges in the same dimension, every badge gets a unique name. Never emit the same canonical badge twice.
  - **First occurrence:** keep the canonical badge name (e.g., `Runs in Hyper-V`).
  - **Subsequent occurrences:** rename using a more specific variable, in priority order:
    1. **PREFERRED** — pick the matching scoring signal name from the dimension's `scoring_signals` list (e.g., `Hyper-V: Standard`, `Hyper-V: CLI Scripting`, `Azure Cloud Slice: Entra ID SSO`). These names carry real point values via `signal_lookup` in the scoring math layer.
    2. **FALLBACK** — derive a qualifier-specific label from the evidence (e.g., `Install Complexity`, `Multi-VM Topology`). These don't lift the score but they prevent visual duplicates and make the evidence specific.
- **Why this is universal:** It solves two problems at once with one architectural rule.
  - **Visual problem:** No more duplicate badge names rendering twice with different colors. Each row shows distinct, specific labels.
  - **Scoring problem:** Closes the badge-vocabulary-vs-scoring-signal disconnect. The math layer credits scoring-signal names with their real point values (e.g., `Hyper-V: Standard` = +30) instead of falling back to color points (+6 for green). Affected products: every installable VM/cloud product that previously underscored.
- **Architectural shape:**
  - **Prompt** is the source of truth (`backend/prompts/scoring_template.md` + `prompt_generator._format_badge_naming_principles()` + `_format_canonical_badge_names()`).
  - **Math layer** needs zero changes — it already credits any name that matches `signal_lookup` and falls back to color points otherwise.
  - **Display normalizer** (`_normalize_badges_for_display`) keeps the same-name merge logic as a defensive safety net for legacy cached analyses + occasional AI non-compliance, but the AI is now responsible for disambiguating at the source.
- **Test plan:** Re-run a fresh discovery + score on SOTI ONE Platform after the prompt change lands. Expect Provisioning to jump from ~6 to ~30+ (Hyper-V: Standard signal credit). Then validate against Cohesity, Tanium, Diligent for regressions. None of those should drop in score — only installable products with a viable scoring signal should gain.
- **Frank's framing (verbatim):** "Wouldn't this be a better idea? If there's two for any badge... instead of showing it twice, you show it once. And then you do a nice variable driven badge for the second one that really kinda points out the good thing or the bad thing... it's really the visual is the problem. Let's just for the second one, if there's more than one, then do a variable on the problem."

---

## Session: 2026-04-06 — ACV tier thresholds locked

### ACV tier dollar thresholds
- **DECIDED:** ACV tier labels are computed deterministically in Python from the **high end** of the per-product ACV range (a deal is sized at its upside, not its floor):
  - `acv_high >= $250,000` → **HIGH ACV**
  - `acv_high >= $50,000`  → **MEDIUM ACV**
  - `acv_high <  $50,000`  → **LOW ACV**
- **Where:** `scoring_config.ACV_TIER_HIGH_THRESHOLD` and `ACV_TIER_MEDIUM_THRESHOLD`. One-line edits with zero rescore needed — `_prepare_analysis_for_render` recomputes on every page render via `scoring_math.compute_acv_potential()`.
- **Why:** Visible label needs *some* threshold to flip between low/medium/high. Frank picked deliberately conservative numbers — anything under $50K is correctly Low, $50K–$250K is real but bounded, $250K+ is the point where a deal warrants serious investment. The verdict grid combines this tier with Fit Score to choose the verdict label and color.
- **Architectural note:** This finishes the move of ACV math from the AI prompt into deterministic Python. The AI's only ACV job now is per-motion population, adoption %, and hours/learner — population × adoption × hours, the rate lookup, the dollar conversion, and the tier label all happen in Python.

### Verdict ACV labels — keep them
- **DECIDED:** Keep the LOW ACV / MEDIUM ACV / HIGH ACV labels under the verdict badge. They give immediate context next to the verdict text without forcing the reader to compute "is $63K low or medium" in their head. The labels are now driven by the Python tier computation above, not AI guesswork.

---

## Session: 2026-04-06 — Score color buckets

### Three visible color buckets, five logical thresholds — intentional
- **DECIDED:** The score color system has **five logical thresholds** (`dark_green`, `green`, `light_amber`, `amber`, `red` at 80 / 65 / 45 / 25 / 0) defined in `scoring_config.SCORE_THRESHOLDS`. All four score displays — Fit Score, the three Pillar Scores, and the Verdict — read from this single dict via `score_color` filter or `get_verdict()`. They are aligned by construction.
- **DECIDED:** The **visible color palette is intentionally only three buckets** (high green / mid amber / low red). `dark_green` and `green` both render `var(--sk-score-high)`. `light_amber` and `amber` both render `var(--sk-score-mid)`. This is a deliberate design choice, not a bug. The finer-grained nuance lives in the **verdict label text** ("Prime Target" vs "Worth Pursuing" vs "Solid Prospect"), not in color saturation.
- **Why:** Five distinct color shades on the same page becomes visual noise. Three clean buckets give an immediate gut read; the verdict label gives the precision when you want it. Future self: do not "fix" this by adding two more colors unless this decision is explicitly revisited.

---

## Session: 2026-04-06 — Roadmap consolidation

### Single consolidated roadmap doc
- **DECIDED:** `docs/build-roadmap.md` and `docs/Research-Methodology-Improvements.md` consolidated into a single new doc at `docs/roadmap.md`. Both source docs deleted in the same commit. The new doc is the complete inventory of every item we know we want to do, are doing, have done, or need to decide.
- **Why:** Frank flagged that we'd been developing 2-3 different places listing next steps. The two source docs had real overlap (Render deployment prep was in both), stale items (Score Calc Dedup, Replace print() with logging, Prompt Generation System were marked as TODO but actually done), and unclear ownership ("where do I add this?" had multiple answers). One inventory eliminates the fragmentation.
- **Format:** Each section has a 2-column table (Item | Description) with status icons inline in the item name (✓ Done · 📝 Partial · 🟢 Active · 🔵 Backlog · ❓ Decision Needed) plus HIGH/MED/LOW priority tags on items not yet done. Sections organized by area: Macro Build Sequence, Architecture & Foundation, Inspector, Prospector, Designer, Research Engine, Infrastructure, Cross-Cutting, Decisions Needed.
- **`next-session-todo.md` stays separate.** It serves a different time horizon: focused near-term action driver, refreshed every session, part of the CLAUDE.md startup sequence (step 4). The roadmap is the long-term inventory; next-session-todo is "what to do this session." Items flow: idea → roadmap as 🔵 Backlog → moved to next-session-todo when prioritized → marked ✓ Done in roadmap when shipped.
- **Cross-references updated:** `CLAUDE.md` build roadmap reference now points at `docs/roadmap.md`. `Platform-Foundation.md` Supporting Documents table updated. New "complete inventory" pointer added to CLAUDE.md startup section so future Claude knows the roadmap exists as a reference (but doesn't need to read it as part of the startup sequence — that would be too much).

---

## Session: 2026-04-06 — Principles surfaced from Bug Hunting

### Visual changes must NEVER affect scoring
- **DECIDED (principle):** Any change made for display purposes — badge merging, splitting, deduplication, color promotion, name normalization, sorting, grouping — must NEVER alter the inputs the scoring math sees. Scoring math reads the AI's evidence as faithfully as possible. Display transforms run on a separate path so the user sees a clean UI without the math being silently distorted.
- **Origin:** Caught during the badge merger fix on SOTI ONE Platform. The merger collapsed two same-named "Runs in Hyper-V" badges into one and promoted the color from green to amber for clarity. The math layer reads `BADGE_COLOR_POINTS` for badges that don't match a named signal — green = +6, amber = 0. The color promotion silently dropped 6 points per dimension where this happened, ~10 points across SOTI's pillars.
- **Architectural enforcement:** `_normalize_product_badges` should be split into two functions — one that runs before the math (deterministic injections like Bug 2's No Learner Isolation badge, plus the badge splitter) and one that runs AFTER the math (display-only merging and color promotion). The math sees the unmerged list; the user sees the merged list.
- **Generalization:** The same principle applies to any future display work — sorting badges by severity, hiding low-confidence badges, collapsing badge groups, renaming badges for clarity. None of these may touch what the math sees.

---

## Session: 2026-04-05 (late night) — Inspector Cache, Stable URL, Per-Product Briefcase, In-Place Swap

### Stable URL Per Company
- **DECIDED:** One persistent analysis per company (per discovery_id), forever. The analysis URL is bookmarkable and stable. Captured in Platform-Foundation.md under GP5.

### Cache + Append Logic
- **DECIDED:** Deep Dive checks for an existing analysis on the discovery. For each selected product: cached → leave alone, new → score it. Newly scored products are APPENDED to the existing analysis (same analysis_id, same URL).
- **DECIDED:** If all selected products are cached, the route returns instantly with zero Claude calls.
- **DECIDED:** Default product shown on the page = highest-scoring product from the CURRENT selection. The dropdown shows ALL products ever scored for the company.

### Briefcase Is Per-Product
- **DECIDED:** The Seller Briefcase moves from analysis-level to product-level. Each scored product has its own briefcase. Switching products in the dropdown swaps to that product's briefcase. Captured in Platform-Foundation.md and Badging-and-Scoring-Reference.md.
- **DECIDED:** Briefcase generation runs only for NEWLY scored products. Cached products keep their cached briefcase.
- **DECIDED:** Briefcase generation is its own background phase that runs after scoring. The Full Analysis page renders immediately with "preparing" placeholders, then swaps in the briefcase content as it becomes available — no page reload, no scroll loss.

### In-Place Product Swap
- **DECIDED:** When the user picks a different product from the dropdown, the page updates IN PLACE (no URL change, no reload, no lost scroll position). Three sections swap together: hero, pillars, and briefcase. URL stays bound to the company.
- **DECIDED:** The endpoint that returns rendered fragments lives at `/inspector/analysis/<id>/product/<index>` and returns JSON with `hero_html`, `pillars_html`, `briefcase_html`.

### Briefcase Loading UX
- **DECIDED:** The "loading" state for each briefcase section shows the real card title (Key Technical Questions, Conversation Starters, Account Intelligence) with three subtle pulsing dots in the body. No generic "Preparing Seller Briefcase..." text. Consistent with the search-loading dot pattern.
- **DECIDED:** Polling frequency is 5 seconds — invisible to the user (no jumpiness possible since nothing visible animates per poll). Will increase to 60s once tonight's debugging is done.

### Logging Infrastructure
- **DECIDED:** Logging is configured directly in `app_new.py` (not just `run_new.py`) so that the Flask reloader child process inherits it. Werkzeug request logs and backend `log.info` calls now show in real time.
- **DECIDED:** Claude API calls in `_call_claude` emit a heartbeat log every 15 seconds during streaming so we can see calls are alive. Will tune to 60-90s after tonight.

### Doc Reorganization
- **DECIDED:** All four memory files for Frank's collaboration preferences (commit/push, grid uniformity, writing standard, etc.) consolidated into `docs/collaboration-with-frank.md`. CLAUDE.md and MEMORY.md both point to it. Project-specific rules live in CLAUDE.md only.
- **DECIDED:** Mandatory file storage rule added to both CLAUDE.md and MEMORY.md: never save anything persistent to the local hard drive. All docs go in the repo (OneDrive + GitHub).
- **DECIDED:** Old docs moved to `docs/archive/`: Badging-Framework-Core.md, Scoring-Framework-Core.md, inspector.md, intelligence-platform.md, skillable-intelligence-platform.md, Skillable-Intelligence-Executive-Briefing.docx, Skillable-Intelligence-Platform.docx. designer.md was merged into Designer-Session-Prep.md and deleted.

### Build Roadmap
- **DECIDED:** `docs/build-roadmap.md` created from the memory file. Status: steps 1-4 complete, currently in step 5 (testing).

---

## Session: 2026-04-05 (evening) — Designer Document Consolidation

### designer.md Merged and Deleted
- **DECIDED:** All content from `designer.md` (the pre-Foundation requirements document) merged into `Designer-Session-Prep.md`. No content lost — full Phase 1-4 detailed specs, Preferences specification, VocabularyPack, and intelligence flow details now live in the Prep doc's "Decisions Already Made" section. `designer.md` deleted. The two session docs (`Designer-Session-Guide.md` + `Designer-Session-Prep.md`) are now the complete authority for Designer.
- **DECIDED:** References to `designer.md` cleaned from all memory files (conversation_agenda.md, project_document_inventory.md, project_tool_checklists.md).

---

## Session: 2026-04-05 (afternoon) — Backend Rebuild Alignment

### Prospector Page — Fresh Redesign
- **DECIDED:** Prospector input page is NOT ported from proof-of-concept. It will be redesigned fresh on the new framework once the backend is building. Simple page — will go quickly using our standard process.

### Page Names — Simplified
- **DECIDED:** Inspector pages named for what the user is doing, not persona-specific language:
  - Home → **Inspector** (starting a search)
  - Caseboard → **Product Selection** (choosing products for deep dive)
  - Dossier → **Full Analysis** (reviewing deep research)
- **DECIDED:** "Seller Action Plan" and "Seller & SE Action Plan and Solution Recommendations" are retired. Content serves both personas through progressive disclosure — page names stay simple.
- **DECIDED:** "Deep Dive →" button on Product Selection leads to Full Analysis.

### Remaining Build Items
- **DECIDED:** "Back to Company Search" link text — fine as-is.
- **DECIDED:** "Product families" in family picker — fine, capitalize the F.
- **DECIDED:** 6 product selection limit — fine for now, should be configurable.
- **DECIDED:** All CSS must use theme variables — no hardcoded hex values. Complete rewrite to new standard. Visual output must be identical to proof-of-concept pages.

### Designer Page — Fresh Redesign
- **DECIDED:** Designer page is NOT ported from proof-of-concept. Will be redesigned fresh after the Designer Foundation Session.

### Button Label — "Run Dossier" renamed
- **DECIDED:** "Run Dossier →" button on Caseboard renamed to **"Deep Dive →"**

### Org Type Badge Colors — Three Groups
- **DECIDED:** Org type badges use three colors by group, NOT all purple. Colors are classification, not assessment — must not overlap with scoring colors (green/amber/red).
  - **Purple** — Product creators: Software companies, Enterprise/multi-product
  - **Teal** — Learning-focused: Training & certification orgs, Academic institutions
  - **Warm blue / Slate blue** — Channel/partners: GSIs, Distributors, Professional services, LMS companies, Content development firms
- **DECIDED:** Exact hex values for teal and warm blue TBD during build — must complement the platform palette and pass WCAG AA.

### Caseboard Tier Labels — Renamed
- **DECIDED:** Discovery tier labels renamed to be honest about confidence level at discovery depth:
  - Highly Likely → **Seems Promising**
  - Likely → **Likely**
  - Less Likely → **Uncertain**
  - Not Likely → **Unlikely**
- **DECIDED:** These communicate "early read, not conclusion" — GP3 trustworthiness. No false confidence.

### Deployment Model Data Value
- **DECIDED:** Rename `self-hosted` data value to `installable` — display and data should match (GP4).

### Inspector UX Pages
- **DECIDED:** Home page, Inspector search page, Prospector search/upload page, and Caseboard are all close to final from the proof-of-concept. UX design carries forward — no redesign needed.
- **DECIDED:** The header from those pages is also the header for the Dossier page — consistent navigation across the entire Inspector experience.
- **DECIDED:** All four pages plus the dossier are rewritten from scratch as part of the rebuild — not carried forward from old templates. Same UX design, clean new code on the new backend/vocabulary/data model. Avoids legacy template risk.

### Test Plan Created
- **DECIDED:** Test plan document created at `docs/Test-Plan.md` — 8 categories, all traced to Guiding Principles.
- **DECIDED:** Tests implemented in pytest, stored in `backend/tests/`, one file per category.
- **DECIDED:** Test plan document is the strategy (for humans). Test code files are the enforcement (for the machine). No duplication — code references the plan.

### Badge Layout — Responsive, No Hard Cap
- **DECIDED:** No hard cap on badge count per dimension. Show as much context as possible (GP1).
- **DECIDED:** Badges wrap responsively — if they flow to the next row, everything below moves down. Nothing overlaps, clips, or breaks.
- **DECIDED:** Backend uses a soft warning if a dimension produces more than 5 badges — logged for review, not rejected.
- **DECIDED:** UX validation at standard breakpoints (desktop, laptop, tablet) to ensure layout integrity.

### Confidence Field — Level + Explanation
- **DECIDED:** Every evidence finding carries two confidence fields: the level (confirmed/indicated/inferred) AND a short AI-generated explanation of why that level was assigned.
- **DECIDED:** Explanation is one sentence, maybe two at most — specific enough to understand the basis, brief enough to fit in a badge hover modal.
- **DECIDED:** Both fields are required — tests validate that evidence without confidence level AND explanation is invalid.
- **DECIDED:** UX must respect the explanation text — word wrapping, layout in the hover modal must look good.

### Seller Briefcase — Separate AI Call
- **DECIDED:** Seller Briefcase (Key Technical Questions, Conversation Starters, Account Intelligence) is generated in a separate AI call AFTER scoring is complete — not combined into the scoring call.
- **DECIDED:** The briefcase call receives complete scoring output as context — all scores, badges, and evidence. This produces sharper, more pointed seller guidance because the AI is synthesizing, not multitasking.
- **DECIDED:** Key Technical Questions are the highest priority — who to talk to, what department, what to ask, why it matters. Must be tight, clear, concise, and complete.
- **DECIDED:** Extra cost is ~$0.03-0.05/product (Sonnet) or ~$0.15-0.25/product (Opus). Worth it for the quality improvement.
- **DECIDED:** Briefcase only applies to full dossiers (Inspector deep dive), not Prospector batch scoring.

### Scoring — Product Labability Floor Protection
- **DECIDED:** The 40% weight alone is not sufficient to prevent undeliverable products from scoring too high. A product at 5/100 Product Labability still produces a ~50 Fit Score with a strong company — that's misleading.
- **DECIDED:** The old multiplier thresholds (32, 24, 19, 10) are from the proof-of-concept and do not carry forward. Fresh mechanism needed.
- **DECIDED:** The Fit Score stays mathematically honest. When Product Labability is below a threshold, a UX badge/flag communicates the delivery risk so sellers aren't misled by the overall number. Math is one thing, communication is another — both need to be right.
- **OPEN:** Exact threshold and UX language TBD — decide after backend scoring is working so we can see real numbers.

### Scoring — AI Flexibility Within Ranges
- **DECIDED:** The AI determines the exact score within defined ranges (e.g., +21 to +25 for Full Lifecycle API) based on evidence quality. Not fixed values.
- **DECIDED:** Evidence quality drives score placement — comprehensive, well-documented findings earn the top of the range; limited or inferred findings earn the bottom.
- **DECIDED:** GP3 makes this trustworthy — the AI must explain its reasoning in the evidence bullet. Confidence coding (confirmed/indicated/inferred) reinforces accountability. Range = flexibility. Evidence = accountability.

### Data Storage — Three Domains Separated from Day One
- **DECIDED:** Product data, program data, and company intelligence stored in separate locations from day one — not field-level separation within shared files.
- **DECIDED:** This is architectural separation as the Foundation requires — "the separation must be architectural, not just a permissions layer." When auth comes, it's access control on clean boundaries, not a retrofit.
- **DECIDED:** Old cached data from the proof-of-concept is not migrated. Clean slate — everything scores fresh on the new framework.
- **DECIDED:** Cache TTL remains 45 days with manual refresh button available.

### Architecture — Three Inputs to Every Scoring Run
- **DECIDED:** The Prompt Generation System combines three distinct inputs: Company Research (them) + Skillable Knowledge (us) + Scoring Framework (the rules). This is now explicit in Platform Foundation.
- **DECIDED:** Skillable Knowledge stored as JSON files in `backend/knowledge/` — updatable without code changes. Separate from scoring config. Four files: skillable_capabilities.json, delivery_patterns.json, competitors.json, contact_guidance.json.
- **DECIDED:** Company research gathered by the researcher, stored organized by dimension in `data_new/company_intel/` — not raw snippets, structured evidence.
- **DECIDED:** No old code used anywhere. Storage, researcher, and all modules rebuilt from scratch. Old `storage.py` and `researcher.py` are proof-of-concept.

### Domain-Based Lab Platform Detection
- **DECIDED:** Domain-based detection (scanning fetched pages for outbound links to known lab platform domains) is included in the first build, not deferred.
- **DECIDED:** This is critical for trustworthiness — if we can't detect our own customers, that's a trust problem. Also detects competitors.
- **DECIDED:** Uses the canonical lab platform list from scoring_config.py. Scans page content we're already fetching — not a separate research pass. Link evidence is stronger than name mentions.

### Research Depth
- **DECIDED:** Two research depths, not three. Discovery-depth research serves both Prospector and Caseboard. Full scoring is for the Inspector dossier deep dive.
- **DECIDED:** Deeper dossier research sharpens lighter discovery data over time (GP5 — Intelligence Compounds). The lighter research is never wasted.
- **DECIDED:** If Prospector scale (100+ companies) creates speed or cost concerns, revisit with operational constraints (throttling, batching) — not by reducing research depth. Best current thinking.

---

## Session: 2026-04-05 — UX Wireframe, Badge System, and Document Synthesis

### UX Wireframe — Inspector Dossier
- **DECIDED:** 70/30 visual split — two product pillar cards on left (70%), customer fit card on right (30%, slightly different background)
- **DECIDED:** Hero section: product name with dropdown selector (left), Fit Score centered (star of the show), ACV Potential (right)
- **DECIDED:** Product selector dropdown: product name (left-aligned, truncated at ~40 chars), score, purple subcategory badge
- **DECIDED:** Verdict badge below product name, "HIGH FIT · HIGH ACV" below that (all caps)
- **DECIDED:** All dimension names in ALL CAPS in the UX
- **DECIDED:** No connector lines between hero and pillars
- **DECIDED:** Pillar card padding balanced top/bottom
- **DECIDED:** Score bars with gradient green/amber fill

### UX Icons and Navigation
- **DECIDED:** Info icons (?) and doc icons (document SVG) on pillar headers — same size, muted color, green on hover
- **DECIDED:** Two nav links: "Back to Product Selection" and "Search Another Company"
- **DECIDED:** Cache date shown as hoverable link with "Refresh cache" tooltip
- **DECIDED:** Word export (not PDF) — sellers can customize

### Badge System Refinements
- **DECIDED:** Purple subcategory badges for product categories — consistent color for classification badges
- **DECIDED:** Company classification badge uses purple (same as subcategory)
- **DECIDED:** Every badge MUST carry evidence — no badge renders without evidence payload
- **DECIDED:** Badge evidence on hover: 1.5 second delay, modal with bullets, source, confidence
- **DECIDED:** Confidence coding: confirmed, indicated, inferred — core logic, stored as field on every finding

### Seller Briefcase
- **DECIDED:** Three sections below pillar cards: Key Technical Questions (Product Labability), Conversation Starters (Instructional Value), Account Intelligence (Customer Fit)
- **DECIDED:** Each section has info icon for documentation link

### Verdict Grid and ACV
- **DECIDED:** ACV tiers: High, Medium, Low
- **DECIDED:** ACV values use lowercase k (thousands) and uppercase M (millions)

### HubSpot
- **DECIDED:** HubSpot ICP Context field (not generic "notes")

### Standards
- **DECIDED:** WCAG AA compliance on all colors — build standard
- **DECIDED:** No spaces in file names
- **DECIDED:** Fewer badges with more context
- **DECIDED:** Documentation IS the in-app explainability layer

### Document Synthesis
- **DECIDED:** All three core documents (Platform-Foundation.md, Badging-and-Scoring-Reference.md, Research-Methodology-Improvements.md) synthesized to best current thinking
- **DECIDED:** Wireframe HTML committed separately — not part of doc synthesis

---

## Session: 2026-04-04 — Platform Foundation Strategic Session

### Strategic Foundation Established
- **DECIDED:** Platform-Foundation.md is now the authoritative source of truth for all strategic decisions. Where it conflicts with other documents, it wins.
- **DECIDED:** Best current thinking, always. Documents are fully synthesized, never appended. When thinking evolves, the document evolves with it.

### Guiding Principles (5 + End-to-End Principle)
- **DECIDED:** GP1: Right Information, Right Time, Right Person, Right Context, Right Way
- **DECIDED:** GP2: Why -> What -> How (the thinking model and conversational competence builder)
- **DECIDED:** GP3: Explainably Trustworthy (every judgment traceable from conclusion to evidence)
- **DECIDED:** GP4: Self-Evident Design (intent evident at every layer — variable names to UX)
- **DECIDED:** GP5: Intelligence Compounds — It Never Resets
- **DECIDED:** End-to-End Principle: The framework shapes how we gather, store, judge, and present. One model, end to end.

### Scoring Framework — Final Structure (Three Pillars)
- **DECIDED:** Hierarchy is Fit Score -> Pillars -> Dimensions -> Requirements (Requirements = badges)
- **DECIDED:** Three Pillars (not four). Old Customer Motivation and Organizational Readiness merged into Customer Fit.
- **DECIDED:** 70/30 product vs organization split. Product dominates the score.
- **DECIDED:** ACV Potential = separate calculated metric, not part of Fit Score
- **DECIDED:** Two hero metrics in UX: Fit Score + ACV Potential (separate, side by side)
- **DECIDED:** Each Pillar scores out of 100 internally, then weighted. Makes scores intuitive.
- **DECIDED:** Final weights:
  - Product Labability 40% (How labable is this product?)
  - Instructional Value 30% (Does this product have instructional value for hands-on training?) — was "Product Demand"
  - Customer Fit 30% (Is this organization a good match for Skillable?) — combines old Customer Motivation + Organizational Readiness

### Pillar 1: Product Labability (40%) — Dimensions
- **DECIDED:** Four dimensions: Provisioning (35), Lab Access (25), Scoring (15), Teardown (25)
- **DECIDED:** "Provisioning" restored (was briefly "Orchestration Method" — too long)
- **DECIDED:** "Lab Access" replaces "Licensing & Accounts" (working name, may refine)
- **DECIDED:** No more "gates" — use "dimensions" within Product Labability
- **DECIDED:** Old scoring tables split — Lab Access columns (Entra ID SSO, Credential Pool, etc.) moved out of Provisioning into Lab Access as separate scoring items
- **DECIDED:** Lab Access uses base score + penalties model (Credit Card -10, MFA -10, Anti-Automation -5, Rate Limits -5, Provisioning Lag -5, High License Cost -5)
- **DECIDED:** Scoring dimension: API Scorable, Script Scorable, Simulation Scorable, AI Vision Scorable, MCQ Scorable — always has a fallback
- **DECIDED:** Teardown at 25 (elevated from 10) — orphaned cloud resources are real financial risk

### Pillar 2: Instructional Value (30%) — Dimensions
- **DECIDED:** Pillar renamed from "Product Demand" to "Instructional Value" — better name, was the original
- **DECIDED:** Four dimensions: Product Complexity (40), Mastery Stakes (25), Lab Versatility (15), Market Demand (20)
- **DECIDED:** Product Complexity badges: Deep Configuration, Multi-Phase Workflow, Role Diversity, Troubleshooting, Complex Networking, Integration Complexity, AI Practice Required, Consumer Grade (red), Simple UX (red)
- **DECIDED:** Mastery Stakes badges: High-Stakes Skills, Steep Learning Curve, Adoption Risk (Certification Program moved to Market Demand)
- **DECIDED:** Lab Versatility: menu of 12 lab types, AI picks 1-2 per product (Red vs Blue, Simulated Attack, Incident Response, Break/Fix, Team Handoff, Bug Bounty, Cyber Range, Performance Tuning, Migration Lab, Architecture Challenge, Compliance Audit, Disaster Recovery)
- **DECIDED:** Market Demand badges are variable-driven: specific regions (Global, NAMER & EMEA, US Only), specific user counts (~2M Users), specific growth signals (Series D $200M, IPO 2024), Active Certification, Competitor Labs Confirmed
- **DECIDED:** AI market demand has two distinct forms: Learning AI-embedded features vs. Creating AI

### Pillar 3: Customer Fit (30%) — NEW Combined Pillar
- **DECIDED:** Combines old Customer Motivation (20%) and Organizational Readiness (15%) into one Pillar
- **DECIDED:** Four dimensions: Training Commitment (25), Organizational DNA (25), Delivery Capacity (30), Build Capacity (20)
- **DECIDED:** Training Commitment replaces "Training Motivation" — commitment is evidence, motivation is intent
- **DECIDED:** Training Commitment badges across three motivation categories: Customer Enablement, Customer Success, Channel Enablement (adoption); Certification Program, Training Catalog (skill development); Regulated Industry, Compliance Training Program, Audit Requirements (compliance); Training Leadership, Training Culture (cross-cutting)
- **DECIDED:** Organizational DNA is NEW — partner ecosystem, build vs buy, integration maturity, ease of engagement. All variable-driven.
- **DECIDED:** Delivery Capacity: ATP/Learning Partners, {LMS Name (Public/Internal)}, {Lab Platform Name}, Gray Market Offering. Consolidated from old 11 badges to 4.
- **DECIDED:** Skillable TMS is a valid LMS badge (green — our own platform)
- **DECIDED:** Build Capacity: Content Dev Team, Technical Build Team, DIY Labs, Content Outsourcing
- **DECIDED:** DIY Labs can appear in both Delivery Capacity and Build Capacity — means two different things in each

### Verdict Grid
- **DECIDED:** 10 verdicts across Fit Score x ACV Potential matrix
- **DECIDED:** Five score color bands: Dark Green (>=80), Green (65-79), Light Amber (45-64), Amber (25-44), Red (<25)
- **DECIDED:** Verdicts: Prime Target, Strong Prospect, Good Fit, High Potential, Worth Pursuing, Solid Prospect, Assess First, Keep Watch, Deprioritize, Poor Fit
- **DECIDED:** Same verdict can appear in two color bands — verdict = action, color = confidence

### HubSpot Integration
- **DECIDED:** HubSpot is a data destination, not a tool in the display table
- **DECIDED:** HubSpot ICP Context = synthesis note (1-2 sentences), regenerated from best current intelligence every time (GP5)
- **DECIDED:** Variable name: `hubspot_icp_context`

### Prompt Generation System
- **DECIDED:** Static product_scoring.txt replaced by three-layer Prompt Generation System
- **DECIDED:** Layer 1: Configuration — single structured file, all variables defined once
- **DECIDED:** Layer 2: Template — AI instruction structure with {placeholder} references to config
- **DECIDED:** Layer 3: Generated Prompt — assembled at runtime, never a static file
- **DECIDED:** Future admin GUI for config editing with validation, change history, admin-only access

### Define-Once Principle
- **DECIDED:** All pillar names, dimension names, weights, thresholds, badges, vocabulary defined once in config, referenced everywhere
- **DECIDED:** Nothing hard-coded. One change propagates through code, prompts, UX, documentation.
- **DECIDED:** Added as a named principle in the Foundation document

### Confidence Coding
- **DECIDED:** Confidence (confirmed/indicated/inferred) is core logic in the codebase, not just display
- **DECIDED:** Every finding carries confidence level as a stored field
- **DECIDED:** Confidence influences badge color assignment (inferred may cap at amber)

### In-App Documentation
- **DECIDED:** Documentation IS the in-app explainability layer (GP3)
- **DECIDED:** Section-level linking, not badge-level — one click shows the whole section
- **DECIDED:** Written clearly enough for sellers to understand
- **DECIDED:** When docs update, in-app help updates automatically — same source

### Standards
- **DECIDED:** No spaces in file names — ever
- **DECIDED:** Fewer badges with more context, not many badges with less
- **DECIDED:** No dimension should need more than 3-5 badges to tell its story

### Badge System Updated
- **DECIDED:** Four colors: Green (strength), Gray (neutral/context — NEW), Amber (risk), Red (blocker)
- **DECIDED:** Badge names should show the solution, not the problem, when recommendation is clear
- **DECIDED:** Variable-driven badges: text itself changes based on findings (LMS name, competitor name)
- **DECIDED:** If green and unremarkable, don't surface — only show what matters

### Evidence Confidence Language
- **DECIDED:** Three levels: Confirmed (direct primary source), Indicated (strong indirect), Inferred (AI assumption)
- **DECIDED:** Confidence communicated through language in evidence text, not visual indicators
- **DECIDED:** Badge color = the assessment. Evidence language = the basis. Together they're complete.
- **DECIDED:** Evidence bullets must be clear, concise, and complete. No filler. Specific details, sources, reasoning.

### Organization Types — Variable-Driven
- **DECIDED:** Platform cannot be built around "software companies" as sole organizing concept
- **DECIDED:** Eight organization types: Software companies, Training & certification orgs, GSIs, Content development firms, LMS companies, Distributors, Universities & schools, Enterprise/multi-product
- **DECIDED:** Product Labability always applies to underlying technology, not training wrapper
- **DECIDED:** All labels, categories, messaging derive from product data — variable-driven, not hard-coded

### Lab Platform Detection
- **DECIDED:** One canonical list of all lab platform providers, maintained in one place, referenced everywhere
- **DECIDED:** Lab platform badges include Skillable (green) + all competitors (amber) + DIY Labs (amber)
- **DECIDED:** Research Methodology Improvements doc created for detection logic improvements

### Data Architecture
- **DECIDED:** Three domains: Product data (open), Program data (scoped), Company intelligence (internal-only)
- **DECIDED:** Architect for authorization now, implement later
- **DECIDED:** Customers in Designer see product data, never company intelligence

### Document Strategy
- **DECIDED:** Two authoritative documents replace four:
  - Platform-Foundation.md (strategic authority)
  - Badging-and-Scoring-Reference.md (operational detail — to be created)
- **DECIDED:** Old Badging-Framework-Core.md and Scoring-Framework-Core.md will be replaced
- **DECIDED:** product_scoring.txt will be regenerated fresh from the two new docs
- **DECIDED:** Define once, reference everywhere

### Standards
- **DECIDED:** No spaces in file names — ever
- **DECIDED:** Pre-commit vocabulary hook will be updated when new docs are finalized

### Next Steps Agreed
1. Finalize Platform Foundation (done)
2. Create Badging-and-Scoring-Reference.md (new, from scratch)
3. Go through Badging and Scoring doc section by section together
4. Generate new product_scoring.txt from the two docs
5. Write automated tests before code refactor
6. Major code refactor — rename fields, reorganize models, align everything

---

## Session: 2026-04-03 (evening) — Render Deployment & Dossier UX Overhaul

### Render Deployment
- **DECIDED:** App deployed to Render at `https://skillable-intelligence.onrender.com`
- **DECIDED:** Gunicorn timeout set to 300s in Render dashboard (not render.yaml — dashboard overrides yaml after initial setup)
- **DECIDED:** Render filesystem is ephemeral — every redeploy wipes the analysis cache. Persistent storage deferred; acceptable for internal testing
- **DECIDED:** Auto-deploy on commit enabled

### Vocabulary Change: Market Fit
- **DECIDED:** Rename "Market Readiness" to "Market Fit" everywhere — UI, docs, prompts, CLAUDE.md, locked vocabulary, pre-commit validator
- **NOTE:** Market Fit has now been superseded — absorbed into Product Demand pillar's Market Demand dimension (see 2026-04-04 session)
- **DECIDED:** Internal data key stays as `market_readiness` — will be renamed during code refactor

### Dossier Hero Section
- **DECIDED:** Remove boxes around score and ACV — clean horizontal row, no cards
- **DECIDED:** ACV: large green text (1.9rem, 900 weight, #24ED9B), right-aligned
- **DECIDED:** ACV subtitle: "Estimate based on X of Y products" in amber (#f59e0b), where Y = total discovered products (not just scored)
- **DECIDED:** Remove vertical hairline between score and ACV
- **DECIDED:** Remove horizontal hairline below hero
- **DECIDED:** Remove Next Steps section entirely — information distributed into product detail sections
- **DECIDED:** "Back to Caseboard" renamed to "Back to Product Selection"

### Dossier Four Dimension Boxes
- **NOTE:** These will be restructured to reflect the new four Pillars (see 2026-04-04 session)
- **DECIDED:** Subsection-grouped badges per Badging Framework (not flat badge lists)
- **DECIDED:** Subsection labels in purple (#a78bfa) — structural framework element, distinct from evidence badges
- **DECIDED:** Badges left-aligned to consistent column right of purple labels
- **DECIDED:** Max 2 badges per subsection row for layout consistency
- **DECIDED:** Default amber badge shown when no evidence found for a subsection (risk = unknown)
- **DECIDED:** Lab Format Opportunities has no default badge (additive, not a risk)
- **DECIDED:** Dimension scores: larger (1.4rem), bold green (#24ED9B), right-aligned, with visible max values
- **DECIDED:** Emojis removed from all badges in dimension boxes

### Dossier Product Detail Panels
- **DECIDED:** "Help your champion find" recommendation pulled to top as amber callout box ("Essential Technical Resource")
- **DECIDED:** "Delivery Path" recommendation merged into Provisioning subsection
- **DECIDED:** "Scoring Approach" recommendation merged into Scoring subsection
- **DECIDED:** Summary paragraphs removed from all four dimension sections (redundant with evidence bullets)
- **DECIDED:** Orchestration method removed from product bar and detail — redundant with Provisioning badges
- **DECIDED:** Category badge removed from product bar; subcategory badge added (matches Caseboard)
- **DECIDED:** Highlight badge (green, "why labs matter") moved next to product name
- **DECIDED:** Product score moved to right side, larger (1.4rem)
- **DECIDED:** Three badges (subcategory, highlight, verdict) normalized to same height
- **DECIDED:** Stronger section dividers between dimensions (2px solid)
- **DECIDED:** Dimension definitions added to section headers
- **DECIDED:** Potential Labs card names in purple (#a78bfa)

### Backend Infrastructure
- **DECIDED:** Subsection mappings added to `core.py` for all four dimensions
- **NOTE:** These mappings will be restructured during the code refactor to reflect new Pillars/Dimensions
- **DECIDED:** `dedup_evidence` filter added — keeps first occurrence of each badge name per subsection

### Lab Format Pattern — Core Platform Concept
- **DECIDED:** `{Product-Specific-Item} {LabFormat}` is a core platform principle
- **DECIDED:** The LabFormat is always ONE word from a fixed vocabulary: Attack, Defense, Simulation, Collaboration, Fault, Recovery, Troubleshoot, Challenge, Incident, Build, Optimization
- **DECIDED:** This pattern flows across all three tools

---

## Session: 2026-04-03 — Platform Hardening & Code Review

### Shared CSS Theme
- **DECIDED:** `tools/shared/templates/_theme.html` wired into dossier, caseboard, product_detail, and prospector_results
- **DECIDED:** CSS class `yellow` renamed to `amber` everywhere — aligns with locked vocabulary

### Error Handling
- **DECIDED:** `_error_response()` added to `core.py` — returns JSON for API/XHR, styled HTML for browser

### Storage Layer Hardening
- **DECIDED:** All JSON file writes use atomic temp-file + `os.replace()` pattern
- **DECIDED:** Read-modify-write operations protected by `threading.Lock()`
- **DECIDED:** In-memory company-name index added to `storage.py`

### Shared Constants
- **DECIDED:** `backend/constants.py` created — single source of truth for all hardcoded values
- **NOTE:** Will be updated during refactor to reflect new Pillar/Dimension vocabulary

### Startup Validation
- **DECIDED:** `config.validate_startup()` runs at app init

### Thread Pool Caps
- **DECIDED:** `scorer.py` ThreadPoolExecutor capped at 6

---

## Session: 2026-04-03 — Code Review, Cleanup & Session Infrastructure

### CLAUDE.md
- **DECIDED:** `CLAUDE.md` created in project root — loads automatically every session
- **NOTE:** Will need to be updated to reflect new vocabulary and Pillar structure

### Repository Cleanup
- **DECIDED:** `backend/docs/` deleted — Claude session artifacts
- **DECIDED:** `tools/designer/legacy_ref/` deleted — superseded old code
- **DECIDED:** Word docs restored after accidental deletion — never delete Word docs without asking

### Framework Standardization
- **NOTE:** The vocabulary locked in this session has been superseded by the 2026-04-04 Platform Foundation session. New vocabulary is authoritative. Old locked terms (Instructional Value, Market Fit, Difficult to Master, Mastery Matters, Licensing & Accounts, etc.) are now legacy.
