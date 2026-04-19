# Handoff to Next Claude — Session Continuity + Rewrite Framework

> **Why this doc exists.** Recurring failure mode: new Claude sessions don't know what recent sessions decided, what subtle rules were hammered out in conversation, or the specific areas we've named as needing improvement in the upcoming rewrite. This doc bridges all of it. **Read immediately after `collaboration-with-frank.md` and before touching any work.**
>
> **Living doc.** Rewritten in place at the end of every session. Not append-only — stale context is actively pruned so this stays short, specific, and current.

---

## Part 1 — Last Session Status

### Session 1 (2026-04-19) accomplishments

1. **Finalized ACV framework v2.** Expanded from 5-motion flat-rate to per-org-type × motion × three-tier rate card with COG/Enablement framing. Documented in `Platform-Foundation.md` (in place) + new standalone `acv-framework-reference.md`. Primary metric renamed to **ACV Target** (go-get-it framing, vs "ACV Potential" which felt limiting to CRO).
2. **Named 5 Hard Rules** at top of `collaboration-with-frank.md` — Slow Down / Standards / Assumptions / Why-What-How / Fixes Align.
3. **Locked TypeScript rewrite decision.** Dev team spec captured in `rewrite-dev-team-spec.md`. Consolidated rewrite plan in `rewrite-plan.md`. Execution: Frank + Claude (not dev handoff) across Sessions 2 (audit + Requirements Doc) and 3+ (rewrite code).
4. **21-company ACV calibration** run honestly (no target-patching). Results preserved in `backend/_test_paying_audience_by_motion.py` + `_recompute_acv_with_big_tier.py`.
5. **Rule #5 self-catch.** I applied three audience overrides masquerading as "prompt refinements" — Frank caught it, all backed out.

### What's in good state entering Session 2

- ✓ ACV framework documented end-to-end
- ✓ 5 Hard Rules at top of collaboration doc
- ✓ Dev team specification in repo
- ✓ Consolidated rewrite plan
- ✓ Platform-wide "ACV Potential" → "ACV Target" rename directive (systematic pass happens during rewrite)
- ✓ 10 standard prompt-refinement approaches identified and documented
- ✓ Known outliers from calibration documented honestly

---

## Part 2 — Read Order for Session 2

1. **Project `CLAUDE.md`** (auto-loaded) — layer discipline, legacy boundary, search modal rule
2. **`docs/collaboration-with-frank.md`** — especially the **5 Hard Rules at the top** (new)
3. **This doc** (`docs/handoff-to-next-claude.md`) — right here
4. **`docs/rewrite-plan.md`** — consolidated rewrite plan, non-negotiable requirements R1–R10, sequencing
5. **`docs/rewrite-dev-team-spec.md`** — architectural contract (Node.js/TypeScript/React/Ant Design/Redis/Azure B2C)
6. **`docs/Platform-Foundation.md`** — current architecture (ACV Target Model section is v2)
7. **`docs/acv-framework-reference.md`** — standalone rate card + use case matrix
8. **`docs/decision-log.md`** — last entry (2026-04-19) covers today's decisions
9. **`docs/roadmap.md`** — inventory (some parts may be stale — audit will surface)

Then ask Frank what Session 2's first action is (likely: begin the codebase audit per `rewrite-plan.md#session-2`).

---

## Part 3 — The Rewrite Framework (the lion's share)

### The North Star (Frank, 2026-04-19)

> *"If we do this rewrite correctly, the entire platform should be more dependable/trustworthy, faster, and easier to maintain — and likely able to provide better insights at the same time."*

This is the success definition. The rewrite is successful if and only if we can defensibly claim all five: **dependable · trustworthy · faster · easier to maintain · better insights.** Any tradeoff that sacrifices one of these for convenience is worth pushing back on.

### Why We're Rewriting

**Why #1 — Shipping driver (immediate).** IT cannot support Python/Flask in production. Skillable is a .NET/Azure/TypeScript shop. Python is not a code problem; it is a launch blocker for IT ownership.

**Why #2 — Technical debt driver (deeper).** The Python codebase has accumulated real debt that the rewrite is the cleanest opportunity to address (see "Specific Areas That Need to Be Better" below for named pain points).

**Why #3 — Insight-quality driver (opportunity).** This isn't a 1:1 port. We apply improvements to the intelligence layer WHILE translating — specifically the 10 standard prompt-refinement approaches. The rewrite produces *better* audience estimates, *better* confidence signals, and *better* rate application out of the gate.

### What Success Looks Like

If we rewrite correctly, the platform becomes:
- **More dependable** — test coverage catches regressions before they ship
- **More trustworthy** — no accumulated caps/floors; every number grounded in principle
- **Faster** — Node.js + Redis out-performs Python + JSON file I/O
- **Easier to maintain** — TypeScript strict + enforced layer discipline + Ant Design + typed APIs + module headers
- **Better insights** — 10 standard approaches baked into prompts for the first time
- **IT-ownable** — Skillable's dev team maintains it

If we rewrite badly: silent behavior regressions, translated-but-still-monolithic files, lost ACV/scoring nuance, delayed launch, TypeScript version of the same drift problem.

**The difference is discipline:** 5 Hard Rules + 10 standard approaches + Why/What/How everywhere + structural tests + the right pair at the keyboard (Frank + Claude, not a cold dev handoff).

---

## Part 4 — Specific Areas That Need to Be Better

This is the concrete list of named pain points in the Python codebase that the rewrite addresses. Each one is a file / module / pattern that should be specifically improved, not just translated.

> **Session 2 validation required.** Items below are mostly surfaced from Session 1 conversation and my (Claude's) synthesis of pain points observed during the ACV framework work. Session 2's audit will validate each against the actual codebase AND Frank will gut-check the list before the Requirements Document treats any of them as locked. Treat this as a strong starting point, not a final contract.

### 4.1 Monolithic files that need decomposition

| Current (Python) | Problem | Target (TypeScript) |
|---|---|---|
| `backend/researcher.py` (~2000 lines) | All three per-pillar fact extractors + discovery + orchestration + prompt assembly in one file | `packages/intelligence/src/research/{product,pillar2,pillar3,discovery}.ts` — one concern per file |
| `backend/scoring_config.py` (~4000 lines) | Everything in one mega-file; hard to find specific constants | Split into `packages/intelligence/src/config/{rates,thresholds,vocabulary,motions,organizationTypes,verdictGrid}.ts` |
| `backend/intelligence.py` | Doing orchestration + some intelligence logic; name is misleading | Rename / split into `packages/intelligence/src/orchestration/{discover,score,recompute}.ts` — leave intelligence logic in dedicated modules |
| `backend/app.py` (Flask) | Routes + business logic mixed | `apps/inspector/src/routes/` (thin) + `apps/inspector/src/services/` + shared `packages/intelligence/` |

### 4.2 Prompts need a clean home

**Today:** Prompt strings are inline f-strings inside Python functions — scattered across `researcher.py`, `audience_grader.py`, `rubric_grader.py`, etc. Hard to iterate; hard to version; hard to review.

**Target:** `packages/intelligence/prompts/` directory with versioned text files. Prompts loaded at module init, composed via typed template functions. Each prompt file has a header with Why/What/How + its version + calibration data it depends on.

Motion-specific prompts that need extraction:
- `research/discovery.prompt.ts`
- `research/product-pillar1.prompt.ts`
- `research/product-pillar2.prompt.ts`
- `research/product-pillar3.prompt.ts`
- `scoring/rubric-grader.prompt.ts`
- `acv/audience-grader.prompt.ts`
- `acv/calibration-anchors.prompt.ts`

### 4.3 Claude SDK calls need a single abstraction

**Today:** Anthropic SDK calls happen in multiple places — `scorer.py:_call_claude`, various direct usages, sometimes bypassed for testing. Hard to mock; hard to swap endpoints; hard to add cross-cutting concerns like caching, telemetry, cost tracking.

**Target:** `packages/intelligence/src/services/claude.ts` — single `ILLMClient` interface with `AnthropicDirectClient` and `AzureFoundryClient` implementations. All intelligence code calls through this interface. Swap by config, not code. Built-in prompt caching, retry with exponential backoff, telemetry to App Insights, typed request/response shapes.

### 4.4 Configuration hierarchy needs to be formal

**Today:** `ANTHROPIC_API_KEY` via env vars. Other config via Python module constants. No runtime override mechanism.

**Target per dev team spec:** `.env` defaults → Redis overrides → UI settings panel. Formalize as `ConfigService` that resolves in precedence order. Typed config keys. UI settings panel is a first-class admin view (gated by RBAC role).

### 4.5 Data layer needs abstraction

**Today:** `backend/storage.py` reads/writes JSON files directly to disk. Mixed into business logic in places.

**Target:** `IStore` interface with `RedisStore` (production) and `InMemoryStore` (tests/dev). All read/write goes through the interface. Typed key patterns (`discovery:{hash}`, `analysis:{id}`, etc.). Encrypted at rest (AES-256-GCM). TTL-based expiration for caches.

### 4.6 Error handling is inconsistent

**Today:** Mix of try/except, sometimes silent failures, sometimes unchecked exceptions bubbling up. Confidence values returned differently across modules (string enum, sometimes numeric, sometimes null).

**Target:** `Result<T, E>` pattern (or similar) for operations that can fail. Typed error enums. Discriminated unions for variant outcomes. Confidence values standardized as string enum across all modules: `confirmed | indicated | inferred | thin_evidence | does_not_apply`.

### 4.7 Test coverage is zero

**Today:** No pytest suite. Silent regressions are common. Every change risks breaking something upstream.

**Target:** Jest (or Vitest — dev team confirms) with coverage thresholds. Structural equivalence tests FIRST (port from Python in Session 2 as snapshot): per-org-type motion applicability, rate math determinism, ATP exclusion rules, cert attribution rules, layer boundaries. Unit tests per module. Integration tests for API routes. E2E smoke tests for discovery → score → render flow. CI gate on every PR.

### 4.8 UI pattern inconsistency

**Today:** Jinja2 templates + vanilla JS + custom CSS + ad-hoc modal markup per flow. One "shared search modal" exists but has been violated in practice.

**Target:** Ant Design 6.x as the baseline. `ConfigProvider` theming. Dark/light mode via `ThemeContext`. Single `<ProgressModal />` component used platform-wide (long-running ops + decision prompts + errors all route through one component). `<DocsModal />` replacing `?` icon modals. `Statistic` for hero metrics. `Row/Col` grid with `gutter={16}`.

### 4.9 RBAC is missing entirely

**Today:** Single-user-single-machine assumption. No auth, no roles, no authorization checks.

**Target:** RBAC baked in from commit #1, even though prod auth (Azure B2C) is IT's deploy-time config. `useAuth()` hook for identity, `usePermissions()` hook for authorization, `<PermissionGuard />` for UI gating, middleware for API routes. Role model in Requirements Document (Session 2): mapping of Skillable personas (admin, seller, marketer, sales engineer, content author) to permission sets. Data-domain access (product / program / company intelligence) honored at every layer.

### 4.10 Legacy code still in the repo

**Today:** `legacy-reference/` directory exists but is documented as off-limits. Retrofit scripts accumulate in `scripts/`. `_test_*.py` temporary files appear and disappear. Decision log has entries referencing retired concepts.

**Target:** `legacy-reference/` deleted or moved to `docs/archive/` as part of the rewrite. `scripts/` cleaned up during Session 2 audit. No `_test_*.py` temp files in the Python codebase after Session 1; tests live in `backend/tests/` in Python, then port to `packages/*/tests/` in TypeScript. Decision log format standardized.

### 4.11 Cache invalidation is ad-hoc

**Today:** `SCORING_LOGIC_VERSION` as a string constant; mentioned in comments, checked in various places, bumped manually. Works but not typed, not enforced.

**Target:** Typed version constants in `scoringConfig.ts`. Three-tier invalidation (pure-Python rescore / re-grade / full re-research) formalized as discriminated union. Cache entries store their version stamp alongside the data.

### 4.12 Vocabulary drift across modules

**Today:** Mix of legacy and current vocabulary in different files. "catalog_subscribers" vs "on_demand_learners" in some decision log entries; "partner_training" + "partner_channel_engineers" as separate motions pre-merge; "ACV Potential" in most docs, "ACV Target" in latest.

**Target:** Vocabulary glossary locked in `packages/intelligence/src/config/vocabulary.ts`. All motion keys, org-type names, tier names, verdict labels Defined-Once. CI check for banned legacy vocabulary in code + docs (similar to the existing badge-vocabulary pre-commit hook). Legacy vocabulary in archival text (decision log, old docs) acceptable; active code and user-visible UI strings use the locked vocabulary only.

### 4.13 Confidence communication to users is thin

**Today:** Confidence values produced by research / scoring / ACV are sometimes surfaced, sometimes not. UI rarely exposes range/uncertainty.

**Target:** Confidence badges on every estimate. `thin_evidence` treatments are visually distinct. `<ConfidenceBadge />` component with consistent styling. Users see the spread, not spurious precision.

---

## Part 5 — The 10 Standard Prompt Approaches (Session 2+ Directives)

All principle-level ("teach Claude how to look at the market"), not per-company patches. Implementation happens in the TypeScript rewrite, not retrofitted to Python.

1. **Structural priors in the prompt.** Teach market facts: "free massive libraries → 10–20% of registered users are annual hands-on lab completers"
2. **Evidence-forcing discipline.** Cite public source or show triangulation reasoning
3. **Self-reflection / sanity-check pass.** Validate estimate against revenue ÷ unit price
4. **Multi-source triangulation for GSIs.** Sum published practice sizes (Azure + AWS + GCP + Salesforce + ServiceNow + SAP)
5. **Structural priors for GSI/VAR workforce composition.** Tier-1 GSIs have 8–15% of total workforce in tech consulting
6. **Disclosed-data prioritization.** Force the prompt to look for and cite specific disclosures (investor decks, careers pages, earnings transcripts)
7. **Motion-level triangulation from revenue for training partners.** Revenue ÷ avg bootcamp tuition × lab-bearing course share
8. **Training-partner-specific audience definition.** Exclude apprenticeships, short workshops, lecture-only
9. **Cert issuer PBT-only scope.** Count only PBT-format exam candidates (30–50% of total volume)
10. **Confidence-weighted estimates.** Wider ranges for thin evidence; midpoints reflect uncertainty

---

## Part 6 — Platform-Wide Rename Directive

**Locked 2026-04-19.** Primary ACV metric is **"ACV Target"** (go-get-it), not "ACV Potential" (felt limiting to CRO).

| Layer | Change |
|---|---|
| **Docs** | Section headings, prose, UI labels all use "ACV Target." Historical/archival references and schema field names (`acv_potential_low/high` in JSON) stay as-is until the schema migrates during the rewrite. |
| **UX** | Inspector hero widget, Prospector column, modals, tooltips, info-mode displays — all "ACV Target." 3-Year ACV is the parallel 3-year realistic metric. |
| **Code** | New TypeScript uses `acvTarget`, `acvTargetThreeYear`, `acvTargetVelocity`. Python legacy names stay until rewrite. |

Partial renames are drift. The systematic pass happens as part of the rewrite itself where field names / UI labels / prompts move together.

---

## Part 6a — Additional Locked Rules from Session 1 Conversation

Specific locked decisions that emerged during Session 1 discussion — each is already reflected somewhere in the framework, but grouped here so they don't get lost.

- **Industry Authority has no Channel Enablement motion.** Frank's statement: "ATPs really don't train their channel partners. They pretty much buy kits and train themselves. So there's not really any revenue or any labs or anything there." IA motion set = ILT + On-demand + Instructors + Cert Candidates + Exam Prep Labs. No Channel Enablement. No Employee Training as a separate line (their employees are instructors, already counted).
- **Training Partners have no Employee Training motion.** Frank: "they just really don't have hardly any employees. They got, you know, whoever owns it, they got some people, and then they've got... it's marketing people. It's instructional designers. It's not really... paying for labs." Training Partner motion set = ILT + On-demand + Instructors. Three motions only.
- **GSI "Customers" audience is flagged "unquantifiable", not estimated.** Frank: "I don't think we have ANY way of counting this." GSIs embed training in client engagements in ways that are fundamentally not triangulable from public data. The column shows as a flag, not a number.
- **Software Customer On-demand rate depends on catalog type.** `sw_paid` = $30/learner (Nutanix University, Hyland University paid content), `elp_paid` = $10/learner (CBT Nuggets, Pluralsight, Cloud Academy paid subscriptions), `free_big_library` = $5/learner (Microsoft Learn, AWS Skill Builder, Google Cloud Skills Boost — free to learner, vendor-subsidized).
- **Events are NOT a single-event motion.** "Paid registrants SUMMED across ALL the company's hands-on conferences and summits annually." Large vendors may have 10+ events — flagship + product summits + regional tours + partner events + developer conferences. Sum them all.
- **Faculty motion dropped from Software; kept only for Academic.** Context-only rate of $0 was considered, then dropped entirely for Software org type. Academic org type has Faculty at $30/person/yr (not context-only — real revenue motion for academic because faculty teaching on the institution's infrastructure is a real use case).
- **Hyperscaler tier applies by name (Microsoft / Google / AWS), not by audience threshold.** Cisco is explicitly NOT hyperscaler — it's at Big tier. Oracle and Salesforce would join the hyperscaler list IF they became Skillable customers. The list is intentionally tight — 3–4 truly hyperscale learning environments.
- **Velocity factor is NOT a growth multiplier.** Growth is already baked into honest current-state audience. Velocity reflects realistic 3-year capture GIVEN the relationship's starting point (current expand customer vs cold prospect). Applied only to compute 3-Year ACV from ACV Target, never to ACV Target itself.
- **Specific hyperscaler rates are tunable, not final.** Tested values ($30 ILT, $2 free big library, $5 SW-paid on-demand, $3 ELP-paid on-demand, etc.) are starting points. Session 2/3 tuning may adjust — particularly $3 cert rate and $15 events rate which Frank flagged as possibly too low.

---

## Part 7 — Known ACV Outliers from 2026-04-19 Calibration

10 of 21 test companies within ±30% of target. Remaining outliers, mapped to the standard approach that addresses each:

| Company | Delta | Root cause | Standard approach |
|---|---|---|---|
| Microsoft | +54% | on_demand audience counts registered users, not hands-on completers | #1 (completion-rate prior) |
| CompTIA | +35% | cert audience counts all exam sitters, not PBT-only | #9 (PBT-only scope) |
| Skillsoft | +18% | catalog audience counts broader Percipio base | close to range |
| EC-Council | +92% | ILT audience likely includes ATP-delivered | ATP exclusion + #9 |
| QA | +137% | ILT audience includes apprenticeships/workshops | #7 + #8 |
| Cisco | −5% | ✓ Big tier working correctly | — |
| Deloitte | −60% | practice-leads audience under-counts | #4 + #5 |
| NVIDIA | −70% | audience places at Big tier but list rates more appropriate | threshold calibration |
| Pluralsight | −60% | ELP Big rate too low for Pluralsight's positioning | rate-card refinement |
| Trellix / Eaton / Milestone / Calix | mixed | small cos, limited public disclosure | better triangulation or accept |

---

## Part 7a — Session 1 Calibration Artifacts (Reference Material)

Session 2 and 3 will use these Python files as reference for the calibration logic and as the basis for behavior tests:

- **`backend/_test_paying_audience_by_motion.py`** — the 21-company test script. Contains the canonical motion-by-motion prompt for `audience_grader`, the per-org-type routing (`MOTIONS_BY_ORG_TYPE`), motion definitions, and the JSON output schema. Re-runnable; safe to delete after Session 3 ports its logic to TypeScript.
- **`backend/_recompute_acv_with_big_tier.py`** — the three-tier rate-card logic (Mid < 100K / Big 100K–3M / Hyperscaler by name), applied as post-hoc math against the test output. This is the reference for `acvCalculator.ts` tier logic in the rewrite. Includes the audience data from the 2026-04-19 run for all 21 companies — useful as Session 2's baseline for structural tests.
- **`backend/_test_paying_audience.py`** — earlier single-total-ACV test (superseded by the per-motion test). Kept as reference; can be deleted in Session 2 cleanup.
- **`backend/_test_audience_grader.py`** — even earlier test script. Same — kept for reference, delete in Session 2 cleanup.

**No behavior tests exist yet in `backend/tests/`** specifically for the ACV v2 framework. Deferred to Session 2/3 as structural tests that port to TypeScript.

---

## Part 8 — Failure Modes to Catch Yourself Before Repeating

### Frank caught me doing X recently — don't repeat

**Session 1, 2026-04-19:** I applied three audience overrides (Microsoft on_demand 22M→5M, QA ILT 55K→25K, Deloitte practice_leads 30K→75K) labeled as "prompt refinement pending" — but the numbers were picked to land near target, not from evidence. Frank asked "we're still doing every fix with standard logic and no artificial floors or ceilings, correct?" **All three overrides were backed out.** If you feel the urge to "just tighten this number a bit to match expectation," STOP — that is a Rule #5 violation masquerading as a prompt refinement. The test is: *would you produce the same number if you didn't know the target?* If no, it's a patch.

### Prior-session patterns (captured in decision log)

- Adding "sanity-check ranges" to prompts to cap Microsoft — banned
- Using "saturated" vocabulary for non-current-customer ACV ceilings — CRO pushed back; replaced with "ACV Target"
- Inventing caps in `scoring_config` to fix outliers — banned
- Reconstructing deleted modules (`scoring_math.py`, `SCORING_PROMPT`) — route concept to new home, don't rebuild

### Non-grounded additions

Frank has flagged repeatedly: don't invent tiers, categories, or numbers that don't map to a real signal — then mask it as "research-informed." **Rule:** if you're about to add a tier / category / threshold / constant that didn't come from explicit user input or grounded research, flag it BEFORE writing it. "I'm considering adding X — is that right?"

### Search modal

One modal, platform-wide. `tools/shared/templates/_search_modal.html` (Python) → `<ProgressModal />` (TypeScript). Don't build a second one. Don't copy-paste markup to tweak.

---

## Part 9 — Active Todos Carrying Forward

1. Session 2: comprehensive codebase + docs audit (produces `docs/rewrite-codebase-audit.md`)
2. Session 2: draft Requirements Document (with Why/What/How at every level, incorporating the 10 standard approaches + Specific Areas from Part 4)
3. Session 2 or 3: write structural behavior tests (port cleanly to Jest/Vitest)
4. Session 2: resolve the 8 open questions with dev team (listed in `rewrite-dev-team-spec.md`)
5. Session 3+: begin the rewrite itself — intelligence layer first
6. Session 2 & 3: execute "ACV Potential" → "ACV Target" rename systematically across Docs > UX > Code (not piecemeal)

---

## Part 10 — Session Handoff Discipline

Before closing any future session, update this doc in place:
- What this session accomplished (replaces Part 1)
- What's in good state (replaces Part 1)
- New "Frank caught me doing X" warnings (add to Part 8)
- Updated read order if anything shifted (Part 2)
- Any shifts in the Rewrite Framework (Parts 3–7)
- Active todos carrying forward (Part 9)

Keep it short and specific. Stale context hurts more than it helps. When an improvement from Part 4 is fully implemented in the rewrite, move it to "done" or remove it.
