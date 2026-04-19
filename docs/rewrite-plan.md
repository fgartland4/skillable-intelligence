# Rewrite Plan — Skillable Intelligence Platform

> **The one doc that tells you what we're rewriting, why, and the non-negotiable constraints.**
> Read this AFTER `collaboration-with-frank.md` (5 Hard Rules) and `handoff-to-next-claude.md`, BEFORE touching any rewrite code.

---

## Why We're Rewriting

Sales and marketing want this platform live. The IT team cannot support a Python/Flask application — Skillable is a Microsoft/.NET shop and the IT team supports Azure web services built on the Skillable standard stack. The rewrite is a **shipping prerequisite**, not a language preference. Every week of additional Python iteration adds translation surface to the eventual rewrite.

This is the **best possible moment** to do the rewrite:
- Platform is not yet launched externally
- Business logic is fresh in the pair (Frank + Claude) who just specified the ACV framework
- No external users means zero migration pressure
- Designer tool has not started — rewrite lands before that work begins

---

## Execution Model — Frank + Claude (NOT a Dev Handoff)

The rewrite is done by **Frank + Claude together across focused sessions** — not handed to Skillable's .NET developers who don't carry the business-logic nuance.

**Why:**
- Business-logic nuance (ACV framework, scoring math, rubric logic, badge selection, layer discipline) was specified between Frank and Claude; the same pair executes so nothing is lost in translation
- No knowledge-transfer overhead — Claude holds the full context
- Dev team is the landing pad: they own production Azure provisioning, CI/CD pipelines, B2C configuration, deployment once the application is complete

**What the dev team owns (post-handoff):**
- Azure App Service provisioning
- Azure Cache for Redis (production Redis)
- Azure B2C tenant + app registration + sign-in flows
- Production secrets via Azure Key Vault
- CI/CD pipeline
- DNS + SSL + domain configuration
- Application Insights / monitoring

**What Frank + Claude own (the entire application):**
- Everything else — backend TypeScript, frontend React, prompts, data layer, tests, documentation

---

## Target Architecture — see `docs/rewrite-dev-team-spec.md`

The dev team's specification is **the architectural contract**. Captured verbatim in `docs/rewrite-dev-team-spec.md`. Summary:

| Layer | Stack |
|---|---|
| Backend | Node.js + Express + TypeScript |
| Frontend | React + TypeScript + Vite 7.x + Ant Design 6.x |
| Persistence | Redis (encrypted AES-256-GCM) |
| Auth | Azure B2C (prod) + mock auth (dev) via `useAuth()` hook |
| Config | `.env` defaults → Redis overrides → UI settings panel |
| LLM | `@anthropic-ai/sdk` via Claude client abstraction (Anthropic direct or Azure AI Foundry — swappable) |
| Web search | Serper API (as today) |
| Excel export | `exceljs` (replaces `openpyxl`) |
| Testing | Jest or Vitest (dev team to confirm) |

---

## Top-Line Requirements — Non-Negotiable

These are the architectural-level requirements the rewrite must satisfy. Violating any of these is NOT a refactor — it's a new decision that warrants an explicit conversation with Frank.

### R1. RBAC baked in from day one

**Why.** Even though IT owns the auth system, the application must be architected around roles from the first commit. Retrofitting RBAC after launch is how authorization bugs ship.

**What.** Roles defined in code. Every API route has a permission guard. Every UI action checks `usePermissions()`. Data-domain access honors role boundaries (product data: open; program data: scoped; company intelligence: internal-only).

**How.** `useAuth()` hook for identity, `usePermissions()` hook for authorization, `PermissionGuard` wrapper for UI gating, middleware for API routes. Role model documented in Requirements Document (Session 2 deliverable); specific roles mapped to Skillable's identity system.

### R2. AI model swap-ability

**Why.** Skillable may choose to route through Azure AI Foundry, Bedrock, OpenAI, or an in-house SLM. Code that hardcodes the Anthropic endpoint is legacy on day one.

**What.** A thin `ILLMClient` abstraction wrapping the Claude SDK. Implementations: `AnthropicDirectClient`, `AzureFoundryClient`, eventually others. Swap via config, not code. Prompt structure kept model-neutral. Model-specific features (caching, tools) degrade gracefully when not supported.

**How.** `services/claude.ts` defines the interface. Intelligence-layer code calls the interface, never the SDK directly. Test mocks implement the same interface.

### R3. Intelligence Layer logic preserved

**Why.** The Python intelligence layer has been carefully specified and calibrated. The rewrite ports it — it does not redesign it.

**What.** Same layer architecture (Research / Score / Badge), same pillar structure (Product Labability / Instructional Value / Customer Fit), same ACV framework v2 (per-org-type × motion × three-tier rate card), same rubric grader pattern, same badge selector pattern. `scoringConfig.ts` mirrors `scoring_config.py` as single source of truth.

**How.** Each Python module maps to a TypeScript module. Prompts port as text. Config constants port as typed exports. Business logic is translated faithfully, then the 10 standard approaches (see `handoff-to-next-claude.md`) are applied to the prompts during translation.

### R4. Layer Discipline — Intelligence layer shared across tools

**Why.** Three tools (Inspector, Prospector, Designer) sit on top of one Intelligence layer. Drift across tools is how bugs compound.

**What.** Intelligence logic lives in a shared package/module, consumed by all three tools. Tool-level code handles only routing, request parsing, template rendering. No intelligence decisions happen in a tool-level route.

**How.** Monorepo structure or shared package. Tool-specific code imports from the shared intelligence package. Any intelligence-layer change lands in one place and propagates.

### R5. Why/What/How at every level

**Why.** Frank's #4 Hard Rule. Every module, function, decision, doc section carries Why/What/How reasoning so future Claude sessions don't have to infer intent.

**What.** Every TypeScript module header has a Why/What/How block. Every exported function has a JSDoc with purpose + inputs + outputs. Every React component has a Why/What/How header comment. Requirements Document has Why/What/How at every section and subsection.

**How.** ESLint rule or pre-commit check to enforce module headers (Session 2 decides the enforcement mechanism).

### R6. One search modal (platform-wide)

**Why.** Recurring violation in the Python codebase was rebuilding the search/progress modal for each new flow. The Ant Design rewrite adopts the Modal/Drawer pattern platform-wide.

**What.** A single `<ProgressModal />` React component used across Inspector, Prospector, Designer for all long-running operations. All progress SSE and decision prompts route through it.

**How.** Reusable component with variants for progress / decision / error states. Built early in the rewrite so it becomes the established pattern.

### R7. Define-Once discipline

**Why.** Magic numbers and duplicated constants are how the Python codebase accumulated 17 caps/floors/multipliers that Frank banned.

**What.** Every scoring constant, rate, tier threshold, category baseline, and vocabulary label lives in `scoringConfig.ts`. Nothing else hardcodes those values. Tests verify no-hardcoding at CI time.

**How.** Port the existing `test_no_hardcoding.py` check to Jest/Vitest. `magic-allowed: <reason>` annotation pattern preserved.

### R8. "ACV Target" naming (not "ACV Potential")

**Why.** CRO feedback — "Potential" implies a ceiling; "Target" is the go-get-it framing. Locked 2026-04-19.

**What.** All UI labels, field names, prompt text, documentation, and code variables use "ACV Target" / `acvTarget` / `acvTargetThreeYear` / `acvTargetVelocity`. Historical docs referencing "ACV Potential" stay as archival; new code uses the new vocabulary.

**How.** Rename happens as a natural part of rewriting each file. No grep-and-replace on the Python codebase — Python is legacy.

### R9. No artificial floors, ceilings, or multipliers

**Why.** Frank's banned pattern. Every cap/floor/multiplier in the Python codebase existed to paper over a place the underlying logic wasn't producing the right answer. The rewrite starts without them.

**What.** Zero caps, floors, or multipliers in any scoring or ACV code path. Edge cases handled via principle-level logic, not clamping. Confidence levels communicate uncertainty; clamping values does not.

**How.** Code reviewed against this principle. Any caps/floors/multipliers from the Python codebase are deliberately NOT ported — they were drift artifacts, not architectural features.

### R10. Structural tests as equivalence spec

**Why.** The Python codebase has no test coverage. The rewrite is the opportunity to establish a testing culture from commit #1.

**What.** Behavior tests verify **structural correctness** (motion applicability per org type, rate math determinism, attribution rules, layer boundaries) — NOT number snapshots (which would lock in current imperfect audience estimates). Tests port to Jest/Vitest as equivalence gate.

**How.** Test file structure mirrors code structure. CI runs tests on every PR. Test coverage required for new intelligence-layer code.

---

## What's in the Repo vs. What Session 2 Produces vs. What Session 3+ Builds

| Artifact | Location | Status |
|---|---|---|
| 5 Hard Rules | `docs/collaboration-with-frank.md` (top) | ✓ Done |
| ACV Framework v2 | `docs/Platform-Foundation.md` + `docs/acv-framework-reference.md` | ✓ Done |
| Session handoff | `docs/handoff-to-next-claude.md` | ✓ Done (living doc) |
| Decision log | `docs/decision-log.md` | ✓ Done |
| Dev team spec | `docs/rewrite-dev-team-spec.md` | ✓ Done |
| Rewrite plan (this doc) | `docs/rewrite-plan.md` | ✓ Done |
| **Codebase audit** | `docs/rewrite-codebase-audit.md` | ◇ Session 2 |
| **Requirements Document** | `docs/rewrite-requirements.md` | ◇ Session 2 |
| **Behavior tests** (Python equivalence snapshot) | `backend/tests/test_rewrite_equivalence.py` | ◇ Session 2 |
| **TypeScript monorepo structure** | New directory tree | ◇ Session 3 |
| **Intelligence layer ports** | `packages/intelligence/` | ◇ Session 3 |
| **Tool layer ports** (Inspector first) | `apps/inspector/` | ◇ Session 3+ |
| **Prospector, Designer** | `apps/prospector/`, `apps/designer/` | ◇ Session 3+ |

---

## Session Sequencing

### Session 1 (complete) — Closeout and prep artifacts

- ACV Framework v2 finalized and documented
- 5 Hard Rules named and added to collaboration doc
- Session handoff doc created (living)
- Decision log entry for today
- Dev team spec captured in repo
- Rewrite plan (this doc) created
- Known outliers from 21-company calibration documented honestly
- Commits: `18eb26d`, `d50a342`, and this session

### Session 2 — Audit + Requirements Document

- **Comprehensive codebase audit** — inventory every file, every tool, every script, every prompt in `backend/`. Surface drift, dead code, undocumented tools, `legacy-reference/` contents, test coverage gaps. Produces `docs/rewrite-codebase-audit.md`.
- **Draft Requirements Document** — Why/What/How at every section/subsection. Captures:
  - Architectural overview + target stack (references rewrite-dev-team-spec)
  - Non-functional requirements (R1-R10 above, fleshed out)
  - API contract (REST endpoints, auth header, error shape, SSE contract)
  - Data model (Redis key patterns, blob shapes, migration path from JSON)
  - Component architecture (React + Ant Design conventions)
  - Intelligence layer specs (what each module in `packages/intelligence/` does)
  - RBAC role model + permission matrix
  - Prompt structure (including the 10 standard approaches for audience estimation)
  - Testing strategy
  - Deployment topology (dev / staging / prod)
- **Behavior tests (Python)** — snapshot structural tests; port to Jest in Session 3
- **Resolve open questions with dev team** (list in `rewrite-dev-team-spec.md`)
- Commits expected: codebase audit, requirements document, initial test scaffolding

### Session 3+ — The rewrite itself

- Fresh Claude reads: CLAUDE.md → collaboration-with-frank (5 Hard Rules) → handoff → rewrite-plan (this doc) → rewrite-dev-team-spec → rewrite-codebase-audit → rewrite-requirements → behavior tests → sample cached data
- Asks clarifying questions; validates understanding with Frank
- Rewrite begins with intelligence layer (where the nuance lives)
- Works through plan across multiple sessions if needed
- Behavior tests port Python → Jest as equivalence gate
- 10 standard approaches implemented in TypeScript prompts for the first time
- "ACV Potential" → "ACV Target" rename happens natively in new code
- Final deliverable: running TypeScript/Node/React application that Frank + Claude hand to dev team for production deployment

---

## Open Questions for Dev Team (Session 2 Surface)

These questions live in `docs/rewrite-dev-team-spec.md` and need resolution before Session 3 starts:

1. Azure AI Foundry — Claude model availability today
2. Redis vs. Azure SQL — is Redis the full persistence layer
3. Auth role model — what roles Skillable's identity system supports
4. Integration surfaces — calls into existing Skillable systems
5. Ant Design version alignment — internal custom extensions
6. Testing framework — Jest vs. Vitest
7. Deployment pipeline — GitHub Actions vs. Azure DevOps
8. Observability — App Insights schema

---

## What Success Looks Like

At the end of Session 3+, Frank has:

- A TypeScript/Node/React application matching the dev team's spec
- Intelligence layer logic faithfully ported from Python with improvements (10 standard approaches)
- All 5 org types' ACV use cases rendering correctly in the Ant Design UI
- Structural test suite running green in Jest
- RBAC baked in throughout (even though prod auth is IT's deploy-time config)
- Clear handoff to Skillable dev team for Azure provisioning and deployment
- No "ACV Potential" references remaining; all "ACV Target"
- Why/What/How headers on every module
- Decision log entries for every major architectural choice made during the rewrite

The framework is in the right shop (TypeScript, Skillable's stack). The business logic is the one Frank and Claude specified. IT can support it. Launch is unblocked.
