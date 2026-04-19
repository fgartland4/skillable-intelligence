# Rewrite — Bugs and Improvements in Detail

> **Purpose.** The rewrite is not a translation of Python-as-is. Every bug and architectural weakness below is **actively known and must be proactively fixed during the port** — not carried forward. Each entry gives Session 3+ Claude the Why / What / How plus verification criteria so nothing slips through by being "translated faithfully."
>
> **Rule #5 framing.** Every item here is an architectural decision, not a throwaway. If during the port you feel the pull to "just translate it and fix later," that's the signal to stop and fix it now. Now IS the later.
>
> **Referenced from:** `next-session-todo.md` §10 (Bugs) + `handoff-to-next-claude.md` Part 4 (Specific Areas). This is the deep-dive where both meet.

---

## Category A — Structural / Architectural

### A1. `researcher.py` is ~2000 lines (monolithic)

**Current state.** Single file in `backend/researcher.py` contains: discovery-time research, three per-pillar fact extractors (PL / IV / CF), prompt assembly, post-filter logic, Claude call orchestration, JSON parsing, retry logic, cost tracking. ~2000 lines.

**Why it's a problem.**
- Hard to navigate. Sessions miss that helpers already exist and rebuild them.
- Hard to test. A single file with 30+ functions is hard to unit-test.
- Hard to evolve. Changing IV prompt requires opening a 2000-line file.
- Violates "one file, one job" implied by the Score layer's decomposition pattern.
- Prompts are tangled with orchestration code, making prompt iteration painful.

**Proactive fix in rewrite.**
```
packages/intelligence/src/research/
  ├── discovery.ts          // discovery-time research (product inventory + org type)
  ├── pillar1-pl.ts          // per-product Product Labability fact extraction
  ├── pillar2-iv.ts          // per-product Instructional Value fact extraction
  ├── pillar3-cf.ts          // per-company Customer Fit fact extraction
  ├── orchestration.ts       // parallel dispatching, retry, cost aggregation
  ├── post-filters.ts        // deterministic guardrails applied to AI output
  └── types.ts               // typed request/response shapes
```
Each file under ~400 lines. One concern per file.

Prompts extracted separately — see B1 (Prompts).

**Verification.** No file in `packages/intelligence/src/research/` exceeds 500 lines. Each file has a single clear responsibility named in its header Why/What/How block. No cross-cutting logic embedded in prompt strings.

---

### A2. `scoring_config.py` is ~4000 lines (single mega-file)

**Current state.** One file holds: pillar weights, dimension weights, rubric tiers, category baselines, penalty tables, risk-cap reductions, Technical Fit Multiplier table, rate tables, ACV tier thresholds, Verdict Grid, locked vocabulary, motion metadata, discovery-level ACV rules, tier-aware caps, rate-by-deployment lookup, calibration text, modal copy, and more.

**Why it's a problem.**
- Finding the right constant requires grepping within the 4000-line file.
- Loose coupling between constants and their consumers — hard to know which rates map to which pillar.
- Review is hard — a PR that touches 3 unrelated constants is indistinguishable from one that touches 3 related ones.
- Define-Once is a SEMANTIC principle (single source of truth), not a FILE principle (one-file-contains-all). The mega-file implementation is an accidental side-effect.

**Proactive fix in rewrite.**
```
packages/intelligence/src/config/
  ├── motions.ts             // motion keys, metadata, rate card (3-tier)
  ├── organizationTypes.ts   // 5 org-type rows + motion applicability matrix
  ├── pillars.ts             // pillar weights + dimension weights + category baselines
  ├── rubric.ts              // rubric tiers + penalty tables
  ├── technicalFitMultiplier.ts  // Tech Fit Multiplier table
  ├── rateTiers.ts           // lab-hour rates by deployment / complexity
  ├── verdicts.ts            // Verdict Grid
  ├── vocabulary.ts          // locked nouns, badge names, enum labels
  ├── caches.ts              // version stamps (typed enum)
  └── index.ts               // re-exports; imports point to `@intelligence/config`
```
Each file typed, each export a typed constant. Imports read clean: `import { MOTION_RATES } from '@intelligence/config/motions'`.

**Verification.** No file exceeds 500 lines. Each file can be understood independently. Any hardcoded constant found outside `src/config/` via CI check. Test: `grep -r '[0-9]+' packages/intelligence/src/` surfaces nothing outside config files (except annotations like `/* magic-allowed: display-precision */`).

---

### A3. `intelligence.py` name is misleading — it's orchestration

**Current state.** `backend/intelligence.py` does: `discover()`, `score()`, `recompute_analysis()`, briefcase generation, some glue logic. Not the intelligence *layer* — more like the orchestration layer that calls intelligence.

**Why it's a problem.** Misleading names lead to misplaced code. Sessions put intelligence logic in this file because "intelligence" is in the name, when it belongs in the actual scorer / calculator / researcher modules.

**Proactive fix in rewrite.**
```
packages/intelligence/src/orchestration/
  ├── discover.ts            // one discovery pass
  ├── score.ts               // Deep Dive — per-product scoring
  ├── recompute.ts           // cache-reload rescore with latest config
  └── briefcase.ts           // Seller Briefcase assembly
```
Intelligence logic lives in its own modules (`src/scoring/`, `src/acv/`, `src/badges/`, `src/research/`). Orchestration calls them.

**Verification.** No scoring/ACV/rubric/badge logic in `src/orchestration/`. Orchestration functions are thin compositions.

---

### A4. `app.py` is ~1300 lines — routes + business logic mixed

**Current state.** `backend/app.py` holds Flask routes AND business logic AND template rendering AND some orchestration.

**Why it's a problem.** Violates layer discipline. Changing a route requires understanding business logic; changing business logic requires understanding routes.

**Proactive fix in rewrite.**
```
apps/inspector/src/
  ├── routes/
  │   ├── discover.ts        // POST /api/inspector/discover
  │   ├── score.ts           // POST /api/inspector/score
  │   ├── briefcase.ts       // GET /api/inspector/briefcase/:id
  │   └── ...
  ├── services/              // tool-specific glue (Inspector-only)
  ├── components/            // React UI
  └── main.ts
```
Routes are thin — request validation, service call, response shape. Services orchestrate `@intelligence/*` calls. Components render.

**Verification.** No route handler exceeds 40 lines. Each route calls exactly one service function. All intelligence calls go through `@intelligence/*` imports.

---

## Category B — Code Organization

### B1. Prompts scattered inline across code

**Current state.** Prompt strings are Python f-strings inside function bodies in `researcher.py`, `audience_grader.py`, `rubric_grader.py`. Prompt assembly (adding calibration blocks, motion tables, org-type framing) happens inline mixed with orchestration logic.

**Why it's a problem.**
- Hard to iterate on a prompt — you have to edit code inside a function instead of a text file.
- Hard to version prompts — no clean way to diff prompt changes separately from code changes.
- Hard to review prompt changes — git diff mixes prompt text with surrounding code edits.
- Prompts are intellectual property; they should be readable as text.
- Token-count-sensitive operations (like prompt caching) become harder to reason about.

**Proactive fix in rewrite.**
```
packages/intelligence/prompts/
  ├── research/
  │   ├── discovery.prompt.ts         // exports typed PromptTemplate
  │   ├── pillar1.prompt.ts
  │   ├── pillar2.prompt.ts
  │   └── pillar3.prompt.ts
  ├── scoring/
  │   └── rubric-grader.prompt.ts
  ├── acv/
  │   ├── audience-grader.prompt.ts   // includes 10 standard approaches baked in
  │   └── calibration-anchors.prompt.ts
  └── types.ts                         // PromptTemplate, PromptArguments, TypedPromptBuilder
```
Each `.prompt.ts` exports a typed template with named template variables. A typed builder function composes the template + arguments. Git diff on a prompt change is clean text diff. Version stamps per prompt file for cache invalidation.

**Verification.** No prompt string literal over 10 lines inline in any `.ts` file outside `prompts/`. CI check: grep for multi-line template literals outside `prompts/` flags violations.

---

### B2. Claude SDK calls in multiple files — no single abstraction

**Current state.** `backend/scorer.py:_call_claude` is the main abstraction, but:
- Direct `anthropic.Anthropic()` invocations exist in some places.
- Retry logic is hand-rolled per call site.
- Cost tracking is scattered.
- No way to swap to Azure Foundry / Bedrock / other without touching every call site.

**Why it's a problem.**
- Can't swap LLM providers without code churn.
- Can't mock centrally for tests.
- Can't add cross-cutting concerns (caching, telemetry, safety filters) without touching every call site.

**Proactive fix in rewrite.**
```typescript
// packages/intelligence/src/services/claude.ts
export interface ILLMClient {
  complete(request: LLMRequest): Promise<LLMResponse>;
  stream(request: LLMRequest): AsyncIterable<LLMStreamChunk>;
}

export class AnthropicDirectClient implements ILLMClient { ... }
export class AzureFoundryClient implements ILLMClient { ... }

// Factory picks based on config:
export function createLLMClient(config: LLMConfig): ILLMClient { ... }
```
All intelligence code calls `client.complete()` / `client.stream()`. Never imports the Anthropic SDK directly. Retry + telemetry + cost tracking + prompt caching sit inside the client implementation.

**Verification.** `grep -r '@anthropic-ai/sdk' packages/intelligence/src/` returns exactly one file (`services/claude.ts`). All other modules import `ILLMClient` from the service.

---

### B3. Data layer — JSON file I/O mixed into business logic

**Current state.** `backend/storage.py` reads/writes JSON files to `backend/data/company_intel/`. File paths are hardcoded. Some business logic calls file operations directly. No connection pooling, no encryption at rest, no TTL-based expiry for cache entries.

**Why it's a problem.**
- Blocker for production deployment (Redis/Azure Cache expected per dev team spec).
- No way to mock storage for tests.
- Confidential data (known customers, company intelligence) sits in files without encryption.
- Concurrent-access issues possible with file-based persistence.

**Proactive fix in rewrite.**
```typescript
// packages/intelligence/src/services/store.ts
export interface IStore {
  get<T>(key: StoreKey): Promise<T | null>;
  set<T>(key: StoreKey, value: T, ttl?: Duration): Promise<void>;
  delete(key: StoreKey): Promise<void>;
  // encryption handled by the implementation
}

export class RedisStore implements IStore { ... }      // production
export class InMemoryStore implements IStore { ... }   // tests/dev
```
Typed key patterns: `discovery:{hash}`, `analysis:{id}`, `cache:rubric:{hash}`, `settings:*`. Encrypted at rest (AES-256-GCM in Redis Enterprise / Azure Cache for Redis). TTLs per key pattern.

**Verification.** No file I/O in intelligence layer code (`fs` not imported outside `services/store.ts`). All persistence goes through `IStore`.

---

### B4. Dimension name constants duplicated across pillar scorers + rubric_grader

**Current state.** Strings like `"training_commitment"`, `"delivery_capacity"`, `"build_capacity"`, `"organizational_dna"`, `"market_demand"`, `"product_complexity"`, `"mastery_stakes"`, `"lab_versatility"` appear in multiple files — `scoring_config.py`, `pillar_2_scorer.py`, `pillar_3_scorer.py`, `rubric_grader.py`, badge code.

**Why it's a problem.**
- Typos silently break behavior.
- Rename a dimension = multi-file coordinated change.
- No autocomplete support.

**Proactive fix in rewrite.**
```typescript
// packages/intelligence/src/config/dimensions.ts
export enum PillarOneDimension { Provisioning = 'provisioning', ... }
export enum PillarTwoDimension { MarketDemand = 'market_demand', ... }
export enum PillarThreeDimension { TrainingCommitment = 'training_commitment', ... }
```
Every reference uses the enum. IDE autocompletes; typos become compile errors.

**Verification.** No string literal matching a dimension name appears outside `config/dimensions.ts`. CI check.

---

## Category C — Testing and Validation

### C1. Zero test coverage — no regression safety net

**Current state.** Nothing in `backend/tests/` covers the scoring pipeline, ACV calculator, rubric grader, audience grader, badge selector, or research layer. A handful of unrelated checks (no-hardcoding, badge vocab) run as pre-commit hooks but don't validate behavior.

**Why it's a problem.**
- Every change to scoring logic risks silent regression.
- Sessions catch their own bugs only when Frank notices unusual output.
- Refactoring is high-risk because there's no behavior baseline.
- Confidence in numbers is purely reviewer-based.

**Proactive fix in rewrite.** Three-tier test strategy:

```
packages/intelligence/tests/
  ├── unit/
  │   ├── motions.test.ts          // motion applicability per org type
  │   ├── rateTiers.test.ts         // Mid/Big/Hyperscaler routing
  │   ├── rubric.test.ts            // tier assignment logic
  │   ├── atpExclusion.test.ts      // ATP exclusion rule fires correctly
  │   └── certAttribution.test.ts   // issuer-only cert counting
  ├── integration/
  │   ├── discovery.test.ts         // full discovery pipeline with mocked LLM
  │   ├── scoring.test.ts           // full scoring pipeline
  │   └── acvCalculation.test.ts    // full ACV pipeline
  └── structural/
      └── rewriteEquivalence.test.ts // structural tests from Python snapshot
```

Unit tests cover pure-function logic. Integration tests cover module boundaries with mocked LLM client (`InMemoryLLMClient`). Structural tests verify rewrite-time behavior equivalence.

**Verification.** Coverage threshold enforced at 80%+ for intelligence layer. CI gate on every PR. New intelligence-layer code requires tests.

---

### C2. Behavior-test-blocking Python state (Session 2 discovery)

**Current state.** Session 1 created `_test_paying_audience_by_motion.py` and `_recompute_acv_with_big_tier.py` as temp test scripts that implement the v2 ACV framework. The *live* `audience_grader.py` and `acv_calculator.py` still reflect a v1-ish state.

**Why it's a problem (for testing).** If Session 2 writes structural tests against live Python code paths, the tests would verify v1 behavior — not what we want. Tests against the temp scripts are fine, but it means the temp scripts become the reference implementation that Session 3 ports to TypeScript.

**Proactive fix in rewrite.**
- Session 2 writes structural tests in Python against the temp test scripts (treated as reference impl).
- Session 3 ports to TypeScript — implements v2 framework natively in `packages/intelligence/src/acv/` and `.../research/audienceGrader.ts`.
- Structural tests port to Jest; new tests can optionally be written against the live TS code paths.

**Verification.** Test equivalence — the same structural tests pass on the Python temp-script implementation and the TypeScript production implementation.

---

## Category D — Model Quality

### D1. Audience estimation outliers (2026-04-19 calibration)

**Current state.** 21-company calibration produced 10 within ±30% of targets; 11 outliers. The 11 outliers trace to specific audience-definition weaknesses in the `audience_grader` prompt.

**Why it's a problem.** Downstream ACV Target numbers are wrong by ~50%-140% for specific companies. Microsoft over by 54%, QA over by 137%, Deloitte under by 60%.

**Proactive fix in rewrite.** Implement **10 standard approaches** in the TypeScript `audienceGrader.prompt.ts`:
1. Structural priors (free-library completion rate 10-20%)
2. Evidence-forcing (cite source or show triangulation)
3. Self-sanity-check (validate vs revenue ÷ unit price)
4. Multi-source triangulation for GSIs
5. Workforce composition priors for GSI/VAR
6. Disclosed-data prioritization
7. Motion-level revenue triangulation for training partners
8. Training-partner-specific audience definition
9. Cert issuer PBT-only scope
10. Confidence-weighted estimates

See `handoff-to-next-claude.md` Part 5 for each approach in detail.

**Verification.** Re-run the 21-company calibration against the new TypeScript audience grader. Target: 15+ of 21 within ±30%. No outliers above +100% or below -70%.

---

### D2. Pillar 2 fact extractor intermittent empty drawers

**Current state.** The IV fact extractor (`researcher.py` → Pillar 2 extraction) sometimes returns empty `mastery_stakes`, `lab_versatility`, or `market_demand` drawers. Rubric grader has a safety net that keeps scoring flowing but the root cause is upstream.

**Why it's a problem.** Downstream badge emission and scoring quality suffer when drawers are empty. Silent quality degradation.

**Proactive fix in rewrite.** Apply standard approach #2 (evidence-forcing) to the Pillar 2 prompt: "If a signal category produces no finding, explicitly return `{ category: 'mastery_stakes', findings: [], confidence: 'does_not_apply', reason: '...' }` — never silently omit. The grader must account for presence + substance separately."

**Verification.** Structural test that runs P2 extraction on known companies and asserts the drawer field is always present (even if empty with confidence=does_not_apply). No silent empties.

---

### D3. Badge-to-score consistency across 12 dimensions

**Current state.** Products scoring similarly on a dimension sometimes show 1 badge, sometimes 4. Root cause is unknown — could be researcher not extracting, scorer not crediting, or badge selector not emitting.

**Why it's a problem.** Badges are supposed to *defend* the score — if a product scores well, badges should explain why. When they don't, the seller can't use the page.

**Proactive fix in rewrite.** During intelligence layer port:
1. Trace the evidence chain per dimension: researcher → fact drawer → scorer → dimension score → badge selector → rendered badge.
2. Identify which of three stages is the consistency failure:
   - **Researcher not extracting**: fact drawer has low variance (always 1-2 findings regardless of product).
   - **Scorer not crediting**: drawer has findings but dimension score doesn't reflect them.
   - **Badge selector not emitting**: score is high but badge count is low.
3. Apply structural fix at the identified stage. Write a structural test that asserts badge count correlates with dimension score.

**Verification.** Structural test: for any product where `dimension.score >= 70`, `badges.length >= 3`. For any product where `dimension.score <= 30`, `badges.length <= 2`. Assertions hold across 10+ sample products.

---

### D4. PL Provisioning badge sparsity (30/35 score → only 2 badges)

**Current state.** Products scoring 30/35 on Provisioning sometimes show only 2 badges. Specific observed cases: Sage 50, Sage 100.

**Why it's a problem.** Same as D3 — badges don't defend the score.

**Proactive fix in rewrite.** Part of the D3 work. Specifically for PL Provisioning: the badge selector's emission rules for this dimension need auditing. If the Python code checks specific fact-drawer fields, the TypeScript port should generalize the emission logic to respect the 12-dimension coherence rule from D3.

**Verification.** Sage 50 scores 30 on Provisioning and shows ≥3 badges. Spot-check across 5 more PL-scoring-high products.

---

## Category E — UX / UI

### E1. No UI component library — custom CSS everywhere

**Current state.** Jinja2 templates with custom CSS. Custom modals, custom progress bars, custom tables, custom status pills. Shared templates exist but aren't uniformly used.

**Why it's a problem.**
- Visual inconsistency across views.
- Accessibility is manual (no baseline a11y from a component library).
- Theming is hard — no dark mode support; brand colors hardcoded.
- Custom modal pattern has been violated repeatedly despite the "one search modal" rule.

**Proactive fix in rewrite.** Ant Design 6.x as the baseline. `ConfigProvider` for theming (Skillable green palette per dev team spec). `ThemeContext` for dark/light mode. `<ProgressModal />` as the ONE progress modal. All tables use `Table` with typed columns. All metrics use `Statistic`.

**Verification.** No custom modal markup in any `apps/*/` file. All progress UI uses `<ProgressModal />`. No hardcoded hex colors outside `packages/ui-kit/theme/`.

---

### E2. Refresh button bug — navigates to SSE endpoint

**Current state.** The refresh button (somewhere in Prospector UI) sometimes navigates to the SSE endpoint URL instead of the HTML waiting page. Raw event-stream text renders.

**Why it's a problem.** Confusing user experience. Browsers see `text/event-stream` and render as plain text.

**Proactive fix in rewrite.** React routing with proper route guards. SSE endpoints are API routes (`/api/...`), never navigable URLs. UI buttons fire `fetch` against API, not `window.location =`.

**Verification.** Refresh button in React implementation navigates to a React route, not an API endpoint. Test: click refresh, URL should be a client route, not `/api/*`.

---

## Category F — Observability and Auth

### F1. No RBAC — single-user-single-machine assumption

**Current state.** No auth, no roles, no authorization checks. Anyone with access to the running instance can do anything.

**Why it's a problem.** Blocker for launch. Retrofitting auth after launch is how authorization bugs ship.

**Proactive fix in rewrite.** RBAC baked in from commit #1. `useAuth()` hook returns identity. `usePermissions()` hook returns role + permission matrix. `<PermissionGuard permission="...">` component gates UI. API routes have middleware: `requirePermission('...')`. Role model defined in Requirements Document (Session 2), roles include: admin, seller, marketer, sales_engineer, content_author (specific names TBD with dev team). Mock auth for local dev via `useAuth()` dev variant (returns a seeded user with configurable role).

**Verification.** Every API route has a `requirePermission(...)` middleware. Every UI action checks `usePermissions()`. No route handler lacks authorization.

---

### F2. No observability / Claude call tracking

**Current state.** Claude calls are made and responses returned. No structured logs, no cost tracking, no latency tracking, no prompt-hash tracking. Debugging a bad call means re-running and hoping to catch it.

**Why it's a problem.** Can't debug production issues. Can't attribute costs. Can't diagnose prompt regressions.

**Proactive fix in rewrite.** `ILLMClient` implementation includes:
- Prompt-text hash (for cache analysis)
- Response-text hash
- Token counts (input + output)
- Latency
- Cost estimate
- Model ID

All emitted to Application Insights via `winston` or `pino`. Queryable. Per-user / per-tool / per-motion cost attribution possible.

**Verification.** Every Claude call appears in App Insights with the full metadata envelope. Latency p95, cost per tool, error rate by prompt are dashboarded.

---

## Category G — Drift and Cleanup

### G1. `legacy-reference/` directory still exists

**Current state.** `legacy-reference/` contains pre-Platform-Foundation proof-of-concept code. Documented as off-limits (CLAUDE.md "Legacy Boundary" section) but physically present.

**Why it's a problem.** Sessions sometimes reference it by accident. Being in the repo makes it searchable and potentially copy-paste-able. The "off-limits" label is weaker than actual absence.

**Proactive fix in rewrite.** Delete or move to `docs/archive/` during the Session 2 audit. Any still-relevant snippets migrated to current docs. Directory removed from the main repo tree.

**Verification.** `legacy-reference/` does not exist in the main tree. Either deleted or archived with a README explaining the history.

---

### G2. Cache invalidation via string constants

**Current state.** `SCORING_MATH_VERSION`, `RUBRIC_VERSION`, `RESEARCH_SCHEMA_VERSION` are module-level Python strings. Incrementing them triggers different levels of cache invalidation (pure-Python rescore / re-grade / full re-research).

**Why it's a problem.** Stringly-typed. No type safety. Easy to forget which one to bump. No enforced structure.

**Proactive fix in rewrite.**
```typescript
// packages/intelligence/src/config/caches.ts
export const enum CacheTier {
  ScoringMath = 'scoring-math',
  Rubric = 'rubric',
  ResearchSchema = 'research-schema',
}
export const CACHE_VERSIONS: Record<CacheTier, string> = {
  [CacheTier.ScoringMath]: '2026-04-19.v2',
  [CacheTier.Rubric]: '2026-04-19.v2',
  [CacheTier.ResearchSchema]: '2026-04-19.v2',
};
```
Every cache entry stores its tier + version stamp. Invalidation routines take `CacheTier` parameter. IDE autocompletes the three tiers; typos are compile errors.

**Verification.** No cache-version string literal outside `config/caches.ts`. All invalidation calls use `CacheTier` enum.

---

### G3. Vocabulary drift across modules

**Current state.** Some modules use `catalog_subscribers`; newer work uses `on_demand_learners`. `partner_training` + `partner_channel_engineers` superseded by `channel_enablement`. `ACV Potential` superseded by `ACV Target`. Old decision-log entries use retired terms (appropriate — archival).

**Why it's a problem.** In active code + user-visible UI, mixed vocabulary leads to confusion and sessions silently regressing to legacy names.

**Proactive fix in rewrite.** `packages/intelligence/src/config/vocabulary.ts` exports the locked vocabulary as typed constants. CI check enforces no use of retired terms in active code (similar to the existing badge-vocabulary pre-commit hook). Archive text (decision log, old docs) freely uses legacy terms.

**Verification.** `grep -r 'catalog_subscribers\|partner_training\|partner_channel_engineers\|ACV Potential' packages/` returns zero results in active code. Pre-commit hook catches regressions.

---

### G4. Confidence values inconsistent across modules

**Current state.** Some modules return confidence as string enum (`"confirmed" | "indicated" | ...`); some numeric 1-5; some boolean; some null-as-thin-evidence.

**Why it's a problem.** Downstream consumers (UI, ACV calculator, badge selector) can't consume uniformly. Some places treat null as "does not apply"; others as "unknown."

**Proactive fix in rewrite.**
```typescript
// packages/intelligence/src/config/confidence.ts
export enum ConfidenceLevel {
  Confirmed = 'confirmed',
  Indicated = 'indicated',
  Inferred = 'inferred',
  ThinEvidence = 'thin_evidence',
  DoesNotApply = 'does_not_apply',
}
```
Every module returns typed `ConfidenceLevel`. UI renders consistent badge styling. ACV calculator consumes consistently. No null, no numeric, no boolean.

**Verification.** All module boundaries return `ConfidenceLevel`. Grep for `"confirmed"` / `"indicated"` string literals outside `config/confidence.ts` flags violations.

---

## Category H — Performance

### H1. Sequential product scoring in Deep Dive

**Current state.** When a Deep Dive scores multiple products, `score()` iterates serially. Each product's three per-pillar fact extractions + rubric grading runs one at a time.

**Why it's a problem.** A 5-product Deep Dive takes ~5x the time of a 1-product Deep Dive, linearly. With 15-20 products common for large companies, cold-path Deep Dive can take minutes.

**Proactive fix in rewrite.**
```typescript
// apps/inspector/src/services/scoring.ts
const results = await Promise.all(
  products.map(product => scoreOneProduct(product, companyContext))
);
```
Parallel by default. Back-pressure via `p-limit` if hitting rate limits. Still returns in dependency order.

**Verification.** 5-product Deep Dive completes in approximately 1-2x single-product time, not 5x. Integration test measures.

---

### H2. Prompt caching not fully exploited

**Current state.** Anthropic's prompt caching feature is partially used. The large system-prompt prefix is cached in some call paths but not consistently — specifically rubric grader and audience grader make calls that could share a prefix but re-send it.

**Why it's a problem.** 90% cost reduction on repeat prompts is available and being left on the table.

**Proactive fix in rewrite.** `ILLMClient` implementation owns prompt cache behavior. System prompts are marked `{ type: 'ephemeral' }` per Anthropic's cache API. Rubric grader and audience grader are structured so their shared prefix (calibration anchors, standard approaches, org-type framing) is cached once per session.

**Verification.** Anthropic cache hit rate metric in App Insights exceeds 70% on rubric-grader and audience-grader calls after warmup.

---

## How Session 3+ Uses This Doc

When porting a module, the rewrite Claude:
1. Reads this doc's category for that module.
2. Identifies every applicable bug / improvement by item ID.
3. Implements the "Proactive fix in rewrite" portion, not the Python behavior.
4. Writes the verification test.
5. Confirms the item is closed before moving to the next module.

Items marked as closed during the rewrite get removed from this doc in the corresponding commit (so this doc shrinks as the rewrite progresses). When the rewrite is done, this doc should be empty or near-empty — everything has been fixed.
