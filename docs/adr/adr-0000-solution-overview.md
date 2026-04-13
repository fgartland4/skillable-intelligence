---
title: "ADR-0000: Skillable Intelligence Platform — Solution Overview"
status: "Prototype"
date: "2026-04-13"
authors: "Frank Gartland, Claude"
stakeholders: "Engineering Team, Sales Engineering, Product"
tags: ["architecture", "overview", "orientation"]
supersedes: ""
superseded_by: ""
---

## Status

Prototype — Inspector and Prospector are functional with real scoring, running on localhost. Pre-deployment, pre-auth. Designer has design documents but no implementation yet.

---

## Business Problem

Skillable sells a platform that lets companies deliver hands-on lab experiences for their software products. Before a seller can have a credible conversation with a prospect, they need to answer two questions: **can we actually lab this company's products?** and **how big is the opportunity if we win?** Today, answering those questions requires an SE to manually research each product's technical architecture, licensing model, API surface, and teardown characteristics — work that takes hours per product and doesn't scale.

The second problem is on the marketing side. Marketing ranks target companies by firmographic data — company size, industry, headcount. But company size doesn't predict whether a company's products are labbable. A 50,000-person company whose products are all SaaS-only with no provisioning API is a worse target than a 500-person company with three installable cybersecurity products. Marketing needs product-level intelligence, not company-level guesswork.

The Skillable Intelligence Platform solves both problems with a product-up intelligence system. It researches a company's products, scores each product's fit with Skillable's platform across three Pillars (Product Labability, Instructional Value, Customer Fit), computes an ACV Potential estimate, and delivers the results through three tools — Inspector (evaluation and research), Prospector (ICP validation and prioritization), and Designer (lab program design). The platform's intelligence compounds over time: every analysis enriches what came before, and the same data serves all three tools.

---

## Design Principles

These are the decision-making principles that drive every architecture, UX, and code choice in this platform. They are not aspirational — they are operational. Every module, every variable name, every scoring rule traces back to one or more of these.

| Principle | What it means for engineering |
|---|---|
| **GP1: Right Info, Right Time, Right Person** | Progressive disclosure everywhere. Different personas get different depths of the same data. Don't dump everything — surface what matters for the audience. |
| **GP2: Why → What → How** | Every insight leads with WHY it matters. This drives Pillar card structure, Seller Briefcase format, and how we present scoring rationale. Code should be readable in the same order. |
| **GP3: Explainably Trustworthy** | Every judgment is traceable from conclusion back to evidence. No black boxes. Confidence levels (`confirmed` / `indicated` / `inferred`) distinguish fact from assumption. The documentation IS the in-app explainability layer. |
| **GP4: Self-Evident Design** | Variable names carry meaning (`training_commitment`, not `dim_3_1`). Module names tell you what they do (`pillar_1_scorer`, not `scorer_a`). The codebase reads like the docs because the docs drove the code. |
| **GP5: Intelligence Compounds** | Every analysis enriches what came before. Cache sharpens, never wipes. One persistent analysis per company. `SCORING_LOGIC_VERSION` triggers smart invalidation — not silent drift. |
| **GP6: Slow Down to Go Faster** | Read ground truth before theorizing. Verify against the actual cache, the actual code, the actual output. One grounded diagnosis beats a branching maybe-list. |

Two additional structural principles:

| Principle | What it means for engineering |
|---|---|
| **Define-Once** | Every scoring parameter, badge name, threshold, weight, and vocabulary term is defined once in `scoring_config.py` and referenced everywhere. If a value lives in two places, one of them is wrong. Pre-commit tests enforce this. |
| **End-to-End** | The same Pillar → Dimension → Signal hierarchy runs through research, storage, scoring, and display. No translation step. No reorganization after the fact. |

The full Guiding Principles are documented in `docs/Platform-Foundation.md` → Guiding Principles section.

---

## Solution Architecture

```
                         ┌─────────────────────────────────────────────────────┐
                         │                   TOOL LAYER                        │
                         │         (view orchestration, routing only)          │
                         │                                                     │
                         │  ┌─────────────┐ ┌──────────────┐ ┌─────────────┐  │
                         │  │  Inspector   │ │  Prospector   │ │  Designer   │  │
                         │  │  (eval +     │ │  (ICP batch   │ │  (lab       │  │
                         │  │   research)  │ │   scoring)    │ │   design)   │  │
                         │  └──────┬───────┘ └──────┬────────┘ └──────┬──────┘  │
                         └─────────┼────────────────┼─────────────────┼─────────┘
                                   │                │                 │
                         ══════════╪════════════════╪═════════════════╪═════════
                                   │                │                 │
                         ┌─────────▼────────────────▼─────────────────▼─────────┐
                         │              INTELLIGENCE LAYER (shared)              │
                         │                                                      │
                         │  ┌────────────────────────────────────────────────┐  │
                         │  │  1. RESEARCH — extract structured facts        │  │
                         │  │     researcher.py + 3 parallel fact extractors │  │
                         │  │     (Claude calls live here)                   │  │
                         │  └───────────────────┬────────────────────────────┘  │
                         │                      ▼                               │
                         │  ┌────────────────────────────────────────────────┐  │
                         │  │  2. STORE — typed fact drawers                 │  │
                         │  │     models.py (dataclasses) + storage.py       │  │
                         │  │     (JSON persistence, three data domains)     │  │
                         │  └───────────────────┬────────────────────────────┘  │
                         │                      ▼                               │
                         │  ┌────────────────────────────────────────────────┐  │
                         │  │  3. SCORE — deterministic rules on facts       │  │
                         │  │     pillar_1_scorer  (pure Python, zero AI)    │  │
                         │  │     pillar_2_scorer  (pure Python)             │  │
                         │  │     pillar_3_scorer  (pure Python)             │  │
                         │  │     rubric_grader    (narrow Claude slice:     │  │
                         │  │                       Pillar 2/3 qualitative)  │  │
                         │  │     fit_score_composer (Technical Fit Mult.)   │  │
                         │  │     acv_calculator   (pure Python)             │  │
                         │  └───────────────────┬────────────────────────────┘  │
                         │                      ▼                               │
                         │  ┌────────────────────────────────────────────────┐  │
                         │  │  4. BADGE — display layer on top of scores     │  │
                         │  │     badge_selector.py (zero scoring impact)    │  │
                         │  └────────────────────────────────────────────────┘  │
                         │                                                      │
                         │  Orchestration: intelligence.py + scorer.py          │
                         │  Guardrails:    post_filters.py                      │
                         │  Config:        scoring_config.py (Define-Once)      │
                         └──────────────────────────────────────────────────────┘
                                            │
                         ┌──────────────────┼──────────────────────────┐
                         │                  ▼                          │
                         │        THREE DATA DOMAINS                  │
                         │                                            │
                         │  ┌──────────────┐ ┌─────────┐ ┌────────┐  │
                         │  │ product_data │ │ company │ │program │  │
                         │  │  (open)      │ │ _intel  │ │ _data  │  │
                         │  │              │ │(internal│ │(scoped)│  │
                         │  │              │ │  only)  │ │        │  │
                         │  └──────────────┘ └─────────┘ └────────┘  │
                         └────────────────────────────────────────────┘

EXTERNAL DEPENDENCIES:
  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐
  │ Anthropic API│  │ Serper API   │  │ Skillable Knowledge│
  │ (Claude)     │  │ (web search) │  │ Files (JSON)       │
  └──────────────┘  └──────────────┘  └───────────────────┘
```

### Module Map

| Module | Responsibility | Layer |
|---|---|---|
| `intelligence.py` | Orchestration — `discover()`, `score()`, `recompute_analysis()`, `refresh()` | Intelligence (orchestration) |
| `researcher.py` | Web research, parallel Claude calls, three per-pillar fact extractors | Intelligence (Research) |
| `scorer.py` | Claude API wrappers, product discovery, briefcase generation | Intelligence (Research) |
| `models.py` | Typed dataclasses — `CompanyAnalysis`, `Product`, `FitScore`, `PillarScore`, `DimensionScore` | Intelligence (Store) |
| `storage.py` | JSON persistence, three-domain separation, atomic writes, thread-safe | Intelligence (Store) |
| `pillar_1_scorer.py` | Product Labability — pure Python, zero Claude. Canonical model, fabric priority. | Intelligence (Score) |
| `pillar_2_scorer.py` | Instructional Value — pure Python. Rubric model, category-aware baselines. | Intelligence (Score) |
| `pillar_3_scorer.py` | Customer Fit — pure Python. Rubric model, org-type baselines, per-company. | Intelligence (Score) |
| `rubric_grader.py` | Narrow Claude slice — one call per Pillar 2/3 dimension, grades qualitative findings | Intelligence (Score) |
| `fit_score_composer.py` | Composes three pillar scores into Fit Score. Applies Technical Fit Multiplier. | Intelligence (Score) |
| `acv_calculator.py` | ACV Potential — five consumption motions × rate tier lookup. Pure Python. | Intelligence (Score) |
| `badge_selector.py` | Post-scoring display badges. 2–4 per dimension with evidence. Zero scoring impact. | Intelligence (Badge) |
| `post_filters.py` | Deterministic guardrails — delivery platform removal, audience sanity, ACV caps | Intelligence (guardrails) |
| `scoring_config.py` | Define-Once source of truth for ALL scoring parameters | Intelligence (config) |
| `core.py` | Verdict assignment, SSE progress streaming, classification helpers | Intelligence (shared) |
| `config.py` | Environment validation, startup checks, operational constants | Infrastructure |
| `app.py` | Flask routes — Inspector, Prospector, Designer. View orchestration only. | Tool Layer |

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.11 + Flask | Application server, route handling, SSE streaming |
| **AI** | Anthropic Claude API (claude-sonnet-4-6 default) | Research fact extraction, rubric grading, briefcase generation |
| **Web Search** | Serper API (primary), DuckDuckGo (fallback) | Product and company research during discovery |
| **Templating** | Jinja2 | Server-side HTML rendering for all three tools |
| **Frontend** | Vanilla JavaScript + CSS | No framework — plain JS with SSE for real-time progress |
| **Storage** | JSON files on disk (three-domain separation) | Atomic writes via temp-file + `os.replace`, thread-safe |
| **Export** | openpyxl | Excel export for Prospector batch results |
| **Web Scraping** | BeautifulSoup4 + requests | Evidence gathering during research phase |
| **Testing** | pytest (118 tests) | Scoring math, data model, config integrity, no-hardcoding audit |
| **Pre-commit** | Custom git hook + `validate-badge-names.py` | Badge naming discipline, magic-number detection |
| **Deployment** | Render (configured, not yet deployed) | `render.yaml` — gunicorn, Python 3.11, env vars |
| **Version Control** | Git (GitHub) | OneDrive sync for working directory |

---

## Key Capabilities

### Implemented

| Capability | What it does |
|---|---|
| **Inspector — Discovery** | Single search field resolves company or product name → parallel web research → three-tier discovery data (per-product, per-product hints, per-company signals) → product chooser sorted by popularity |
| **Inspector — Deep Dive** | User selects products → three parallel fact extractors per product → rubric grading → three deterministic pillar scorers → Fit Score composition with Technical Fit Multiplier → ACV calculation → badge selection → Seller Briefcase (three parallel Claude calls per product) |
| **Inspector — Full Analysis view** | Hero section (Fit Score + ACV Potential), 70/30 Pillar card layout, badge evidence on hover, Seller Briefcase (Key Technical Questions, Conversation Starters, Account Intelligence), scored products table, competitive products, ACV by use case |
| **Inspector — Cache intelligence** | One persistent analysis per company. Stale cache detection via `SCORING_LOGIC_VERSION`. Decision modal (refresh vs use cached). Re-running with new products scores only the new ones. |
| **Inspector — Word export** | Full analysis exported as Word document for seller customization |
| **Prospector — Batch discovery** | Paste company names or upload CSV → parallel discovery (3 concurrent) → results table sorted by ACV potential → Excel export |
| **Prospector — Deep Dive checkbox** | Optional: score the top product per company during batch run |
| **Prospector — Cost/time estimator** | Live estimate of API cost and wall time before running |
| **Prospector — History** | View and revisit previous batch runs |
| **Scoring framework** | Three Pillars (50/20/30 weighting), 12 dimensions, canonical model (Pillar 1) + rubric model (Pillars 2/3), Technical Fit Multiplier, risk cap reduction, penalty-visibility rule, cross-pillar compounding |
| **ACV Potential** | Five consumption motions, org-type adoption overrides, technology-specific rate tiers ($6–$45/hr), single-number estimation discipline |
| **Organization type support** | Software companies, universities, GSIs, VARs, distributors, Industry Authorities, enterprise learning platforms, ILT training orgs, content development firms, LMS providers — each with adapted discovery and scoring paths |
| **In-app documentation** | Framework documentation modals sourced from `scoring_config.py`. Per-pillar, per-dimension explainability. Verdict Grid. ACV explainer. Wired to ? icons throughout. |
| **Shared Search Modal** | One progress/decision modal used by all tools — progress mode, decision mode, in-place transition. Single `EventSource` in the entire codebase. |
| **Post-filters** | Deterministic guardrails — delivery platform removal from product lists, category validation, audience sanity checks, ACV caps. Millisecond execution. |
| **Test suite** | 118 tests — scoring math, data model, config integrity, no-hardcoding audit, UX consistency |

### In Progress

| Capability | State |
|---|---|
| **Validation round** | All scoring fixes shipped. Fresh validation needed across 7–10 company types to confirm demo-readiness. |
| **Provisioning badge sparsity** | Products scoring 30/35 on Provisioning sometimes show only 2 badges. Badge selector needs to emit more when facts support them. |
| **ACV audience transparency** | Large companies with small training populations need badges explaining why ACV is modest relative to company size. |

### Planned

| Capability | Design state |
|---|---|
| **Designer** | Eight-phase lab program design pipeline. Design docs exist (`Designer-Session-Prep.md`, `Designer-Session-Guide.md`). Zero code beyond a stub in `designer_engine.py`. Serves builders: Enablement Owners, Instructional Designers, SMEs, Tech Writers, ProServ. |
| **HubSpot integration** | Stage 1: company-level intelligence → HubSpot company properties. Stage 2: per-product intelligence → deal records. Needs RevOps conversation for field mapping. |
| **Product Lookalikes** | Companies marketing didn't know about, found because they use products that pass Product Labability. Product-fit matching, not firmographic matching. |
| **Contacts** | Specific humans responsible for training/enablement for products Skillable can serve. |
| **Parallel product scoring** | Run all products' extractors simultaneously instead of sequential per-product rounds. |
| **Deployment** | Render or Azure Web App. Decision pending. Blocks auth implementation. |
| **Authentication and RBAC** | See Security Model below. |

---

## Glossary

| Term | Definition |
|---|---|
| **Fit Score** | Composite 0–100 score answering "should we pursue this?" Weighted sum of three Pillar scores with Technical Fit Multiplier applied. |
| **Pillar** | One of three top-level scoring components: Product Labability (50%), Instructional Value (20%), Customer Fit (30%). |
| **Dimension** | One of four scored sub-components within each Pillar. Twelve dimensions total. Each has a weight, cap, and scoring model. |
| **Product Labability** | Pillar 1 — can Skillable run a hands-on lab on this product at scale? Four dimensions: Provisioning, Lab Access, Scoring, Teardown. |
| **Instructional Value** | Pillar 2 — does this product warrant hands-on training? Four dimensions: Product Complexity, Mastery Stakes, Lab Versatility, Market Demand. |
| **Customer Fit** | Pillar 3 — is this organization a training buyer? Four dimensions: Training Commitment, Build Capacity, Delivery Capacity, Organizational DNA. Per-company, not per-product. |
| **Technical Fit Multiplier** | Asymmetric coupling rule: weak Product Labability drags Instructional Value + Customer Fit contributions down. Weak IV or CF does NOT drag PL down. Lookup table keyed on PL score band × orchestration method class. |
| **ACV Potential** | Estimated annual contract value if the customer standardized on Skillable. Computed from five consumption motions × technology-specific rate tiers. |
| **Verdict** | Action label combining Fit Score + ACV tier — Prime Target, Strong Prospect, Good Fit, High Potential, Worth Pursuing, Solid Prospect, Assess First, Keep Watch, Deprioritize, Poor Fit. |
| **Discovery** | Light research pass on a company. Identifies products, captures three-tier data, assigns rough labability tiers (Promising / Potential / Uncertain / Unlikely). Feeds both Inspector product chooser and Prospector results table. |
| **Deep Dive** | Full scoring run on selected products. Three parallel fact extractors → rubric grading → three pillar scorers → Fit Score composition → ACV → badge selection → Seller Briefcase. |
| **Canonical model** | Scoring model for Pillar 1. Fixed badge vocabulary, deterministic signal lookup from `scoring_config.py`. Binary — Hyper-V supports it or it doesn't. |
| **Rubric model** | Scoring model for Pillars 2 and 3. Variable badge names, strength tiers (strong/moderate/weak/informational), category-aware or org-type baselines. Contextual — cybersecurity is different from CRM. |
| **Seller Briefcase** | Three sections below the Pillar cards: Key Technical Questions (PL), Conversation Starters (IV), Account Intelligence (CF). Arms the seller for conversations. |
| **Define-Once** | Architectural rule: every scoring parameter defined once in `scoring_config.py`, referenced everywhere. No hardcoded values in scorer modules. Pre-commit tests enforce this. |
| **Layer Discipline** | Architectural rule: Intelligence logic lives in the shared Intelligence layer. Tool-specific logic (routes, templates) stays in the Tool layer. Intelligence logic in a tool file is a bug-class violation. |
| **Skillable Capabilities** | The knowledge files (`skillable_capabilities.json`, `delivery_patterns.json`, `competitors.json`) that encode what Skillable's platform can do — fabrics, scoring methods, delivery patterns, competitive landscape. These are the platform's self-knowledge. |
| **SCORING_LOGIC_VERSION** | Version string stamped on every cached analysis. When scoring logic changes, the version bumps, and stale caches trigger a fresh Deep Dive on next load. |

---

## Security Model

### Current State (Prototype)

| Area | Implementation |
|---|---|
| **Authentication** | None. No login, no user sessions. Anyone with the URL has full access. |
| **API keys** | `ANTHROPIC_API_KEY` (required) and `SERPER_API_KEY` (optional) loaded from environment variables. Not committed to the repo. Startup validation fails fast if the Anthropic key is missing. |
| **Flask secret key** | `FLASK_SECRET_KEY` env var with a hardcoded dev fallback (`"dev-key-change-in-production"`). Must be replaced before deployment. |
| **Data isolation** | Three-domain storage architecture (`product_data/`, `company_intel/`, `program_data/`) enforced at the storage layer. The hard wall between domains is structural today but not enforced by auth. |
| **Transport** | HTTP on localhost. HTTPS required at deployment. |
| **Secrets in code** | None. All secrets in env vars. `.env` is gitignored. |

### Planned RBAC Model

Seven roles, four boundary lines. The full role table — what each role needs to do and what it must NOT do — plus the four boundary lines and implementation status are documented in `docs/Platform-Foundation.md` → **Authentication and Access Control**. That section is the single source of truth for auth design. This ADR summarizes the boundary model; Platform-Foundation.md owns the detail.

**The four boundary lines (summary):**

| Boundary | What it enforces |
|---|---|
| **Skillable ↔ Customer** | Customers never see company intelligence. Hardest wall in the system. |
| **Skillable Capabilities ↔ everyone else** | Knowledge files editable only by Skillable Capabilities Editor (Sales Engineering + Product). |
| **Read ↔ Write on scoring** | `scoring_config.py` is a code change, not an application edit. |
| **Program scoping** | Skillable Designer sees all programs. Customer Designer sees only their own. Pre-release product visibility controlled at the customer org level. |

Auth implementation is blocked on the deployment decision (Render vs Azure Web App).

---

## Suggested ADR Reading Order

This is the first ADR. Future decisions will be listed here as they are documented:

| ADR | Topic | Status |
|---|---|---|
| **ADR-0000** | Solution Overview (this document) | Active |
| ADR-0001 | Deployment Platform Decision (Render vs Azure Web App) | Pending |
| ADR-0002 | Authentication and RBAC Implementation | Pending — blocked on ADR-0001 |
| ADR-0003 | HubSpot Integration Field Mapping | Pending — needs RevOps conversation |

---

## Scale

### Current Usage

| Metric | Value |
|---|---|
| **Concurrent users** | Single user (prototype, localhost) |
| **Cached analyses** | ~12 full analyses, ~76 discoveries |
| **Prospector batches** | ~4 batch runs to date |

### Per-Operation Characteristics

| Operation | AI calls | Wall time | Estimated API cost |
|---|---|---|---|
| **Discovery** | 1 Claude call per company | ~30–60 seconds | ~$0.10–$0.30 |
| **Deep Dive** (per product) | ~3 extractors + ~8 grader calls + 3 briefcase calls | ~2–4 minutes | ~$1.00–$2.00 |
| **Cache reload** | Zero AI calls (pure Python) | Milliseconds | $0 |
| **Prospector batch** (10 companies, discovery only) | ~10 Claude calls | ~3–5 minutes (parallel) | ~$1.00–$3.00 |
| **Prospector batch** (10 companies + Deep Dive top product) | ~10 discovery + ~140 scoring calls | ~15–25 minutes | ~$10–$20 |

### What Would Need to Be Measured at Scale

| Question | Why it matters |
|---|---|
| **Concurrent Deep Dive throughput** | Multiple users scoring simultaneously — Anthropic API rate limits and thread pool sizing |
| **Storage performance at volume** | JSON-on-disk works for prototype. At thousands of analyses, query patterns may require a database. |
| **Prospector batch ceiling** | How many companies can run in a single batch before SSE timeout or memory pressure |
| **Claude API cost at production volume** | Cost per company analyzed × expected monthly volume = monthly API spend |

---

## Related Documents

### Primary Documents (read in this order)

| Document | What it owns |
|---|---|
| `docs/collaboration-with-frank.md` | How the team works together. Session rhythm, non-negotiables, partnership model, the three-pass startup sequence. |
| `docs/Platform-Foundation.md` | Strategic authority. Guiding Principles, Three Layers of Intelligence, Layer Discipline, Define-Once, organization types, personas, scoring framework, Fit Score composition, Verdict Grid, ACV Potential model, Inspector UX, Prospector UX, Designer pipeline, data architecture. |
| `docs/Badging-and-Scoring-Reference.md` | Operational detail. Every Pillar, every dimension, every scoring signal, every baseline, every penalty, Technical Fit Multiplier table, risk cap reduction, badge naming rules, locked vocabulary, worked examples. Also serves as the in-app explainability layer. |

### Working Documents

| Document | What it owns |
|---|---|
| `docs/next-session-todo.md` | Current priorities. §1 names the first action of the next session. |
| `docs/roadmap.md` | Long-arc inventory of everything planned, in progress, and completed. |
| `docs/decision-log.md` | Write-only log of decisions made during sessions. Not authoritative for current state — the Foundation docs are best current thinking. |
| `CLAUDE.md` | Auto-loaded working context. Layer Discipline rules, module map, project rules, deleted-module routing table. |

### Designer Planning

| Document | What it owns |
|---|---|
| `docs/Designer-Session-Prep.md` | Design preparation for the Designer tool |
| `docs/Designer-Session-Guide.md` | Eight-phase pipeline design guide |

### In-App Documentation

The platform includes a built-in explainability layer. Every Pillar card has a `?` icon that opens a modal with WHY-WHAT-HOW documentation sourced dynamically from `scoring_config.py`. The Verdict Grid, ACV model, and dimension-level scoring logic are all accessible from within the application — one click, one source of truth.
