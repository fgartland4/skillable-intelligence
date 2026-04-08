# Skillable Intelligence Platform — Foundation

This is the strategic authority for Skillable Intelligence. It owns the Guiding Principles, the architecture, the people the platform serves, the scoring framework at a glance, the ACV model, the Verdict Grid, and the UX structure. Operational detail — every dimension's math, every scoring signal, every strength tier, the penalty tables — lives in `Badging-and-Scoring-Reference.md`. Where the two docs touch, this document names what each thing *is* and the reference doc names *how* it's computed.

Best current thinking, always. Fully synthesized, never appended.

---

## Guiding Principles

**These are a thinking system, not a list.** Read them, then read the rest of this document, then come back and re-read them. The second pass is where they become operational — where you see how each GP shapes the architecture, the scoring, the UX, and how we work together. See `collaboration-with-frank.md` → "Re-reading Is the Point."

### GP1: Right Information, Right Time, Right Person, Right Context, Right Way

> Right information, at the right time, to the right person, with the right context, in the right way.

| Right... | Means... |
|---|---|
| **Right information** | The specific thing they need, not everything we know |
| **Right person** | Different roles get different slices of the same data |
| **Right time** | When they need it — not before it's relevant, not after it's useful |
| **Right context** | Framed so they understand why it matters *to them* |
| **Right way** | Concise first. Progressive disclosure. Fewer words. Invite depth, don't force it |

### GP2: Why → What → How

Every insight, every recommendation, every judgment starts with **why** it matters, then **what** to do about it, then **how** to do it.

| Level | Question | What it does |
|---|---|---|
| **Why** | Why does this matter? | Creates common ground between technical and non-technical people |
| **What** | What do we need to create or solve? | Defines the scope of work |
| **How** | How do we build or implement it? | Execution detail |

This sequence is how the platform builds **conversational competence**. When designing any screen, card, or recommendation, ask: Is the Why clear first? Can someone stop here and be conversationally competent? Can they keep going into What and How if they need to?

### GP3: Explainably Trustworthy

Every judgment the platform makes must be traceable, from conclusion back to evidence, so anyone can follow the reasoning and believe it.

- Scoring logic cannot be a black box
- Judgments distinguish fact from AI-informed assumption via the confidence levels (`confirmed` / `indicated` / `inferred`)
- Documents produced by the platform are evidence trails, not just summaries
- Progressive disclosure is the trust mechanism — give the conclusion, then let people pull on the thread until they believe it
- The documentation IS the in-app explainability layer. Users click into any Pillar card to see the framework documentation. One source of truth, one click, digestible.

### GP4: Self-Evident Design

The platform's intent, logic, and structure must be evident at every layer — from variable names to UX output. Anyone inspecting any layer should understand why it exists, what it does, and how it connects to the whole.

| Layer | What self-evidence looks like |
|---|---|
| Variable and field names | Named after the concepts they represent — `training_commitment`, `delivery_capacity`, `organizational_dna` — not generic labels |
| Module names | You can tell what a module does from its name — `pillar_1_scorer`, `fit_score_composer`, `acv_calculator`, `badge_selector` |
| Data models | Pillars, dimensions, and fact drawers are explicit in the schema, not buried in unstructured text |
| Prompts | Fact extractors carry typed field lists, not freeform instructions |
| UX output | Recommendations, badges, and rationale all trace back to code |
| Canonical lists | One source of truth for any shared list; referenced everywhere, never duplicated |

GP3 and GP4 are partners. Explainably Trustworthy is the standard. Self-Evident Design is how it's achieved at every layer. Together they mean: the platform explains itself — to users, to developers, to AI, to anyone who touches it.

### GP5: Intelligence Compounds — It Never Resets

Every interaction makes the data sharper. No update loses prior knowledge. The platform builds on what it already knows.

- Every analysis enriches what came before
- Deeper research (a full Deep Dive) automatically sharpens lighter data (a Prospector record)
- Cache updates preserve and sharpen, not wipe and restart
- Prompt and logic changes trigger smart cache invalidation via `SCORING_LOGIC_VERSION`, not silent drift
- **One persistent analysis per company.** Each company has a single stable URL. Every Deep Dive run accumulates products into the same analysis without breaking the URL. Re-running with the same products is instant (cached). Re-running with new products scores only the new ones and appends them.

### GP6: Slow Down to Go Faster

Truly understanding a problem and answering it once is dramatically faster than solving it quickly, bouncing off the wrong answer, and solving it again. This applies to people, to AI assistants, and to the platform itself.

| Slow down means... | Not... |
|---|---|
| Read before theorizing | Diagnosing from memory or summary |
| Verify the symptom against ground truth (the cache, the code, the actual output) | Inferring what must be happening |
| Present ONE grounded diagnosis, once | A branching decision tree of maybe-fixes |
| Distinguish root cause from symptom | Treating the first thing you see as the bug |
| Name structural questions when you spot them | Burying them inside a code change |
| Check for adjacent causes before declaring independence | Assuming two bugs are unrelated because they wear different masks |

**Why this is a Guiding Principle, not a work habit:** at a certain point, the cost of a fast-but-wrong answer isn't just the rework — it's the confidence tax on every future decision that depends on the flawed one. Working slowly where it matters is how the platform stays trustworthy as it grows. **GP6 and GP3 are partners.**

---

## How the GPs Show Up in the Platform

After reading the GPs, scan this table. It is the key that makes the rest of the document operational — every architectural choice below traces back to one or more of these principles.

| GP | Where it lives in the platform |
|---|---|
| **GP1** — right info, right time, right person | Progressive Disclosure Stack · HubSpot-first for sellers · Seller Briefcase · persona-specific entry points · concise-first, depth on hover |
| **GP2** — Why → What → How | Every Pillar card leads with the question · Seller Briefcase opens with Why · conversational competence starts with Why |
| **GP3** — Explainably Trustworthy | Confidence levels · evidence on hover · documentation is the in-app explainability layer · traceable from conclusion back to source |
| **GP4** — Self-Evident Design | Variable names carry meaning · Pillar / Dimension / fact drawer hierarchy is explicit · `scoring_config.py` is the Define-Once source · names you can read without a glossary |
| **GP5** — Intelligence Compounds | One persistent analysis per company · cache sharpens, never wipes · `SCORING_LOGIC_VERSION` triggers smart invalidation · every Deep Dive enriches what came before |
| **GP6** — Slow Down to Go Faster | Read ground truth before theorizing · one grounded diagnosis, not a branching maybe-list · trace signals end-to-end before editing · name structural questions when you see them |

---

## The Center of Everything: Products

**Why.** A product's fit with Skillable determines whether we can help a company at all. If the underlying technology cannot be labbed, nothing else — customer size, training maturity, budget — matters. Starting anywhere else produces answers that look right and don't hold up.

**What.** The platform is **product-up**. It does not start with "what kind of company is this?" and guess at their products. It starts with the products, and the products tell you everything else.

```
Products (the atomic unit)
  → roll up to → Product categories / verticals
    → roll up to → Company profile
      → map to → People (who builds training for THESE products)
```

**How.** Every label, category, description, and piece of messaging derives from the product data. Organization type is a variable. Motivation is a variable. Product category is a variable. All flow from the data, and all shape how intelligence is presented.

**Product Labability applies to the underlying technology — always.** Regardless of organization type, the four Product Labability dimensions always apply to the *underlying technology*, never to a training wrapper or organizational structure.

| Organization type | Intelligence path |
|---|---|
| Software company | Products → labability assessment → fit |
| Training / Certification org | Courses → extract underlying technologies → labability assessment → fit |
| University / School | Curriculum → extract underlying technologies → labability assessment → fit |
| GSI / Content firm | Client engagements → products involved → labability assessment → fit |
| LMS company | Their customers' products → labability assessment → fit |
| Distributor | Products they distribute → labability assessment → fit |

If a course or curriculum doesn't teach anything that involves hands-on interaction with technology — a leadership course, a compliance reading course, a soft-skills workshop — there's nothing to provision. No lab opportunity. Move on.

---

## Three Layers of Intelligence — Research, Store, Score, Badge

**Why.** The old monolithic Claude call collapsed research + scoring + badge selection into one step. Scoring logic changes forced re-research. Caching broke. A 4-minute Deep Dive replaced what should have been a millisecond recompute. Worse: badges became the *currency* of scoring, so changing a point value meant re-running Claude on every product. The fix is to separate the work by responsibility and never collapse the layers again.

**What.** The Intelligence layer has four internal sub-layers. Each has a different job, different rules about whether it can call Claude, and different modules. The framing is **Research → Store → Score → Badge.**

| Layer | Owns | Produces | Modules | Can call Claude? |
|---|---|---|---|---|
| **1. Research** | Going out to the world and extracting **structured facts** | Populated fact drawers | `researcher.py` + the three parallel fact extractors (Pillar 1 / 2 / 3) | **Yes** — the main place Claude runs |
| **2. Store** | Holding facts in a **single canonical location** per fact | `Product.product_labability_facts`, `Product.instructional_value_facts`, `CompanyAnalysis.customer_fit_facts` | `models.py` (typed dataclasses), `storage.py` (JSON persistence) | No — it's a location, not a process |
| **3. Score** | Applying **deterministic rules** to facts to produce scores | Per-dimension scores, per-pillar scores, composed Fit Score, ACV Potential | `pillar_1_scorer`, `pillar_2_scorer`, `pillar_3_scorer`, `rubric_grader`, `fit_score_composer`, `acv_calculator` | **Narrow slice only** — the rubric grader grades qualitative findings for Pillars 2 / 3. Everything else is pure Python. |
| **4. Badge** | Selecting **2–4 contextual badges per dimension** to explain the score | Canonical badge names + evidence text attached to each `DimensionScore` | `badge_selector.py` | Currently deterministic. Step 6 full may add a tiny per-dimension call for evidence phrasing. |

**How.** `intelligence.score()` wires them together:

```
researcher extracts facts → fact drawers stored on Product / CompanyAnalysis
  → rubric_grader tiers Pillar 2 + Pillar 3 findings (parallel Claude calls, one per dimension)
  → pillar_1_scorer produces Pillar 1 PillarScore from facts (zero Claude)
  → pillar_2_scorer produces Pillar 2 PillarScore from facts + grades
  → pillar_3_scorer produces Pillar 3 PillarScore from facts + grades
  → fit_score_composer applies the Technical Fit Multiplier, writes FitScore.total_override
  → acv_calculator recomputes ACV Potential from motion estimates + rate lookup
  → badge_selector attaches display badges
  → intelligence.score() persists and returns
```

Cache reloads go through `intelligence.recompute_analysis()`, which trusts saved pillar scores, recomputes ACV (so a rate-table retune propagates instantly), reassigns verdict, and sorts. No pillar scorer re-runs on cache reload — if scoring logic changed, `SCORING_LOGIC_VERSION` triggers a fresh Deep Dive instead.

**The collapse rule.** No layer may collapse into another.

| Forbidden pattern | Why |
|---|---|
| Research + Score in one Claude call | Scoring changes force re-research. Caching breaks. Retired 2026-04-08 with the deletion of the monolithic scoring prompt. |
| Score + Badge in one step | Badges become the currency of scoring; facts get trapped inside badge labels. |
| Badge-as-scoring | A badge is *context on a score*, not the score itself. The score comes from facts via rules. |
| Score reads badges | The math layer must never look at badge names. Score reads the typed fact drawer directly. |

**The litmus test** before writing any Intelligence code: (1) which of the four layers does this belong to? (2) Am I about to collapse two layers? (3) Am I making a Claude call outside Research or the rubric grader? (4) Am I storing a fact in two places? (5) Am I reading a badge name to decide scoring math? If any of those stops fire, it's drift — find the right layer and write the code there instead.

---

## Layer Discipline — Shared Intelligence, Thin Tools

**Why.** The platform has three tools — Inspector, Prospector, Designer — that all need the same product intelligence, the same scoring, the same fact drawers, the same verdict logic. If each tool owned its own copy of that logic, they would drift. Drift means different fit scores for the same company in different tools. That destroys trust (GP3) and breaks the "intelligence compounds" promise (GP5).

**What.** One shared **Intelligence layer** sits below all three tools. Tools own only tool-specific work: URL patterns, request parsing, template selection, view orchestration. Everything that knows about products, companies, scoring, research, evidence, or the framework lives in the shared layer.

| Layer | What lives here | Modules |
|---|---|---|
| **Intelligence layer** (shared) | Research, discovery, per-pillar scoring, fit-score composition, ACV calculation, badge selection, rubric grading, cache versioning, validation, briefcase generation, model definitions, locked vocabulary, classification, verdicts | `intelligence.py`, `scorer.py`, `researcher.py`, `pillar_1_scorer.py`, `pillar_2_scorer.py`, `pillar_3_scorer.py`, `rubric_grader.py`, `fit_score_composer.py`, `acv_calculator.py`, `badge_selector.py`, `scoring_config.py`, `storage.py`, `models.py`, `core.py` |
| **Inspector** (tool) | Inspector-specific routes, request parsing, template selection, view orchestration | `app.py` Inspector route handlers, `tools/inspector/templates/*.html` |
| **Prospector** (tool) | Prospector-specific routes, batch orchestration, lookalikes UI, HubSpot integration glue | (future) |
| **Designer** (tool) | Designer-specific routes, program-design pipeline, customer-facing views | (future) |

**How.** The litmus test for any new function is: "would Prospector or Designer also need this if they were calling it?" If yes, it's shared. If no, it's tool-specific. **When in doubt, default to shared.** Intelligence logic mistakenly placed in tool files is a **bug class**, not a style preference — it's graded with the same severity as cache-version lies and vocabulary drift.

---

## The Standard Search Modal — The One and Only

**Why.** Every time a drifted custom progress UI has been built, the platform has ended up with different timer behavior, different error handling, different cancel semantics, inconsistent status updates, and users who can't tell which Skillable tool they're in. Trust (GP3) requires consistency. Self-Evident Design (GP4) requires one way to do it.

**What.** There is **ONE** search / progress modal in this entire platform. It lives in `tools/inspector/templates/_search_modal.html` and is used for every long-running operation across Inspector today, and Prospector and Designer when they come online.

| Mode | Use |
|---|---|
| **Progress mode** — card overlay with eyebrow, title, animated status, progress bar, elapsed timer, cancel button, and SSE subscription | Discovery research, Deep Dive scoring, cache refresh |
| **Decision mode** — same card, different middle section: message + two buttons (primary / secondary) | Stale-cache prompts, any "confirm before running" flow |
| **In-place transition** — decision → progress without flicker | Refresh flows where the user confirms and then watches the work happen |

**How — the enforcement rules, no exceptions:**

1. Every long-running operation across every tool uses this shared modal.
2. The ONLY `new EventSource(` in the entire codebase lives in `_search_modal.html`. Anywhere else is a bug.
3. The SSE contract is `status:<text>` / `done:<payload>` / `error:<message>`. Every backend route publishing progress uses this exact contract.
4. Routes that kick off long-running work return JSON `{ok, job_id}`. The caller opens the shared modal via `openSearchModal({sseUrl: '/.../progress/' + job_id, ...})`.
5. No forked markup. No per-flow "just this one modal." No inline loading states for long operations. If the modal's middle section needs a new variant, add it INSIDE `_search_modal.html` and document it in the file header.

**Shared API:**

- `openSearchModal({eyebrow, title, sseUrl, onComplete, onError})` — progress mode
- `openSearchModalDecision({eyebrow, title, message, onRefresh, onIgnore})` — decision mode
- `transitionSearchModalToProgress({...})` — decision → progress in place

---

## The Define-Once Principle

**Why.** When a fact lives in two places, they drift. Install base in the ACV calculator drifts from install base in Pillar 2 Market Demand. Pillar weights in the code drift from pillar weights in the prompt. Drift destroys trust.

**What.** All Pillar names, dimension names, weights, thresholds, badge names, scoring signals, rate tables, verdict definitions, and locked vocabulary are defined **once** in `scoring_config.py` and referenced everywhere — code, UX, tests, in-app explainability. Nothing is hardcoded anywhere else. If a value changes, it changes in one place and propagates through the entire system.

**How.** Every scorer imports `scoring_config as cfg` and reads typed values directly. Pre-commit tests scan for magic-number literals in the Score layer files (`pillar_1_scorer`, `pillar_2_scorer`, `pillar_3_scorer`, `fit_score_composer`, `acv_calculator`). Anything that isn't `0`, `1`, `-1`, `100`, an HTTP status code, or a line carrying a `# magic-allowed: <reason>` annotation is a test failure and must come from config.

---

## The End-to-End Principle

The framework shapes how we **gather**, how we **store**, how we **judge**, and how we **present**. One model, end to end. The same Pillar / Dimension / Requirement structure runs through every layer — research, storage, scoring, display. No translation step. No reorganizing after the fact.

---

## Accessibility: WCAG AA Compliance

All UX elements must meet WCAG AA contrast standards (4.5:1 for normal text, 3.0:1 for large text). This is a build standard and a QA checkpoint — every color combination is validated before shipping. Accessibility is not optional.

---

## Organization Types

**Why.** Skillable serves a broad landscape. "Software companies" is the anchor — they create the products that everything else orbits around — but they are far from the only audience. The organization type determines how you find the products and how you approach the conversation, but the underlying intelligence logic is the same for all.

**What.**

| Organization Type | Examples | Their relationship to products | How you find the products |
|---|---|---|---|
| **Software companies** | Microsoft, Trellix, Dragos, Opswat, Hyland, UiPath, NICE, Tableau, Nutanix, NVIDIA, F5, Commvault, Cisco | They *create* the products | Product pages, documentation, API docs |
| **Training & certification organizations** | CompTIA, EC-Council, ISACA, SANS, Cybrary, Skillsoft, QA | Their *products are courses and certifications* | Course catalogs — extract the underlying technologies taught |
| **GSIs (Global System Integrators)** | Deloitte, Accenture, Cognizant | They *implement and deploy* other companies' products | Client engagements — what technologies are involved |
| **Content development firms** | GP Strategies | They *build learning programs* around other companies' products | Program portfolio |
| **LMS companies** | Cornerstone, Docebo | They *host and deliver* learning programs | Their customers' products |
| **Distributors** | Ingram, CDW, Arrow | They *sell and resell* products and build training | Training catalogs and distribution portfolio |
| **Universities & schools** | Saint Louis University, Grand Canyon University, WGU | Their *courses and degrees* cover technologies | Published curriculum |
| **Enterprise / multi-product** | Microsoft, Cisco, Siemens | Dozens of products across categories — each is a separate opportunity | Product portfolio — each assessed independently |

---

## Customer Motivation

**Why.** Every organization that invests in hands-on training does so for one or more reasons. Knowing the motivation lets the platform frame intelligence for the persona and surface the right conversation starters.

**What — three motivations:**

| Motivation | Core drive | The stakes | Signals |
|---|---|---|---|
| **Product adoption** | People use it, love it, don't churn | Revenue — if they don't adopt, they cancel | Customer enablement programs, adoption risk language, TTV concerns |
| **Skill development** | People are competent, certified, employable | Careers — if they can't do it, they can't get the job | Certification programs, university curricula, career-track training |
| **Compliance & risk reduction** | People don't make dangerous mistakes | Consequences — if they get it wrong, real harm happens | Regulatory requirements, healthcare / finance / cybersecurity contexts, audit readiness |

**How.** Motivations are **not mutually exclusive** — a single organization (even a single product) can have multiple. They are **contextual to the persona** — the same intelligence may be framed differently depending on who it's being served to (sellers see adoption, training-side personas see skill development, regulated industries surface compliance regardless). This connects directly to GP1.

All motivations lead to confidence. None are negative. All genuinely care about the learner: product adoption wants the learner confident *in the product*; skill development wants the learner confident *in themselves*; compliance wants the learner confident *under pressure*.

---

## The People

### Two Audiences, One Hard Wall

| Audience | Tools | Purpose |
|---|---|---|
| **Skillable internal** | Prospector + Inspector | Target the right companies, prepare for conversations, research products |
| **Customers (eventually) + Skillable ProServ** | Designer | Build lab programs based on product intelligence |

**Customers never see Prospector or Inspector data. Ever.** This boundary is architectural — not just a permissions layer. There is no path from Designer to company intelligence data. See "Data Architecture: Three Domains" below for how the hard wall is enforced.

### Personas by Tool

**Prospector (Targeting)** serves Marketing and RevOps. It delivers three things: **Enrichment** (deeper intelligence about companies you already know, scored against product fit), **Product Lookalikes** (companies you didn't know about, found because they use products that pass Product Labability — product-fit matching, not firmographic matching), and **Contacts** (specific humans responsible for training / enablement for products Skillable can serve). Prospector's principle: deliver intelligence to marketing where they work (HubSpot), not where we work.

**Inspector (Evaluation & Research)** serves the spectrum from sellers to deep technical roles:

| Persona | What they need | Where they start |
|---|---|---|
| Sellers (AE, Account Directors) | Product-fit confirmation, buying signals, conversational competence | HubSpot — click deeper when needed |
| CSMs | Expansion opportunities, product fit for upsell | HubSpot — click deeper when needed |
| SEs | Deep product research, technical detail, orchestration specifics | Inspector directly |
| TSMs | Same as SEs — technical depth | Inspector directly |

**Designer (Program Design)** serves the builders — the people who have already decided to create labs:

| Persona | Role |
|---|---|
| Enablement / Training Program Owners | Strategy — which audiences, what outcomes, how many labs |
| Instructional Designers | Learning experience design — sequencing, objectives, assessment |
| SMEs | Product accuracy — what's worth teaching, what's realistic |
| Tech Writers | Lab content — instructions, steps, guidance |
| Product Engineers | Technical feasibility — what can be done, how it works |
| Skillable Professional Services | All of the above, on behalf of customers |

### Conversational Competence

**Why.** Sellers talking to technical buyers need to understand the product. SEs recommending programs need to understand the instructional case. Neither starts competent. The platform's job is to close both gaps.

**What.** Conversational competence is bidirectional:

| Who | Gap direction | What competence looks like |
|---|---|---|
| Sellers / CSMs | Toward product understanding | "I understand the purpose of your product, why hands-on training makes sense for it, and how Skillable fits. I'm not an architect, but I'm not wasting your time." |
| SEs / Technical folks | Toward instructional-design understanding | "I understand why specific lab types matter for specific learning outcomes. I can recommend the right labs, not just build the environment." |

**How.** Built through GP2 — every Pillar card leads with the Why. Starting with Why creates common ground between technical and non-technical people. It is the universal starting point.

### Progressive Disclosure Stack

**Why.** Different people need different depths. Nobody should be forced to see more than they need, and nobody should be locked out of going deeper.

**What.** The entire platform is one continuous progressive-disclosure path — one intelligence stream at increasing depth. Tool boundaries are entry points based on who you are.

| Layer | What you see | Who starts here |
|---|---|---|
| HubSpot card | Fit confirmation, key badges, "worth pursuing" confidence, ACV signal, HubSpot ICP Context | Marketing, Sellers, CSMs |
| Inspector Product Selection | All discovered products for a company — early tiers (Seems Promising / Likely / Uncertain / Unlikely), subcategory badges | SEs, TSMs (or anyone who clicked deeper) |
| Inspector Full Analysis (dossier) | Overall assessment, three Pillar cards, Seller Briefcase, bottom row | Anyone exploring a company |
| Pillar cards with evidence on hover | Technical detail — labability dimensions, features, orchestration specifics | SEs, TSMs digging into a specific product |
| Designer | Lab series, lab breakdown, activities, scoring, instructions, bill of materials | Program Owners, IDs, SMEs, Tech Writers, ProServ |

### Seller Briefcase

**Why.** Conversational competence (GP2) needs to be delivered in the most practical form possible. Sellers don't want to read a report — they want to know *what to say* and *who to say it to*.

**What.** Below the three Pillar cards in the dossier, each Pillar contributes a **briefcase section** — 2–3 sharp, actionable bullets that arm the seller for conversations.

| Section | Under which Pillar | What it gives the seller |
|---|---|---|
| **Key Technical Questions** | Product Labability | Who to find at the customer, what department, and the specific technical questions that unblock the lab build. Includes a verbatim question the champion can send. |
| **Conversation Starters** | Instructional Value | Product-specific talking points about why hands-on training matters for this product. Makes the seller credible without being technical. |
| **Account Intelligence** | Customer Fit | Organizational signals — training leadership, org complexity, LMS platform, competitive signals, news. Context that shows the seller has done their homework. |

**How.** Each section is a **separate Claude call with its own focused system prompt**, on the model best suited to its purpose. All three per product run in parallel:

| Section | Model | Why this model |
|---|---|---|
| **Key Technical Questions** | Opus 4.6 | Sales-critical synthesis — must be sharp, specific, answerable |
| **Conversation Starters** | Haiku 4.5 | Pattern-matched, fast — product-specific talking points |
| **Account Intelligence** | Haiku 4.5 | Pattern-matched, fast — surface organizational signals |

Briefcase is **per-product**, not per-analysis. When the user picks a different product from the dropdown, the briefcase swaps. Cached products keep their cached briefcase — only newly scored products get a fresh generation.

---

## Scoring Framework at a Glance

**Why.** One composite Fit Score answers "should we pursue this?" It has to reflect both the product (can we lab it? is it worth labbing?) and the organization (will the opportunity actually happen?). 70% of the score is about the product because the product truth is the hard constraint — a great customer with an unlabbable product is not a Skillable opportunity. 30% is about the organization because even the most labbable product goes nowhere if the customer isn't a training buyer.

**What — the hierarchy:**

- **Fit Score** (composite, 0–100) — made up of three Pillars
  - **Pillars** (three) — the weighted components of the Fit Score
    - **Dimensions** (four per Pillar) — specific areas measured within each Pillar
      - **Requirements / facts** — the most granular level; what the researcher extracts into the fact drawer

**The 70/30 Split:**

| Level | Pillars | Combined weight |
|---|---|---|
| **Product** | Product Labability + Instructional Value | 70% |
| **Organization** | Customer Fit | 30% |

**The Three Pillars:**

| Pillar | Weight | Level | UX Question |
|---|---|---|---|
| **Product Labability** | 40% | Product | How labable is this product? |
| **Instructional Value** | 30% | Product | Does this product warrant hands-on training? |
| **Customer Fit** | 30% | Organization | Is this organization a good match for Skillable? |

**How.** Each Pillar scores out of 100 internally, then gets weighted. A Product Labability score of 85 contributes 85 × 0.40 = 34 points to the Fit Score. **Full operational detail — every dimension, every scoring signal, every baseline, every penalty, every strength tier — lives in `Badging-and-Scoring-Reference.md`.** This document does not duplicate that detail.

### Fit Score Composition

**Why.** A pure 70/30 weighted sum lets a product with weak Product Labability still score Solid Prospect when Instructional Value and Customer Fit are strong. That's not honest — if we cannot lab the product, the instructional case and organizational signals don't save us. The platform's value proposition is lab-based training.

**What.** The Technical Fit Multiplier scales **IV + CF contributions only** by a factor derived from the PL score and orchestration method, enforcing an asymmetric coupling rule:

> **Weak PL drags IV + CF contribution down. Weak IV or weak CF does NOT drag PL contribution down.**

**How.** `fit_score_composer.compose_fit_score` applies the math:

```
pl_contrib = pl_score × (pl_weight / 100)
iv_contrib = iv_score × (iv_weight / 100) × multiplier
cf_contrib = cf_score × (cf_weight / 100) × multiplier
fit_score  = clamp(round(pl_contrib + iv_contrib + cf_contrib), 0, 100)
```

The multiplier lookup lives in `scoring_config.TECHNICAL_FIT_MULTIPLIERS`. Full table with worked examples in `Badging-and-Scoring-Reference.md` → "Technical Fit Multiplier."

---

## Two Hero Metrics — Fit Score + ACV Potential

**Why.** Sellers and execs ask two questions about every opportunity: *should we pursue this?* and *how big is it if we win?* They are different questions with different answers, and forcing them into one number loses information.

**What — two separate outputs:**

| Metric | What it answers | Type |
|---|---|---|
| **Fit Score** | Should we pursue this? | Qualitative composite of three Pillars (0–100) |
| **ACV Potential** | How big is this if we win? | Calculated business metric — dollars per year |

**How.** Both render in the hero section at the top of every company view and caseboard entry. The Fit Score is per-product; the ACV Potential hero widget is **company-level** and does not change as the user switches products in the dropdown. ACV values use lowercase `k` for thousands and uppercase `M` for millions (e.g., `$250k`, `$1.2M`).

---

## Verdict Grid

**Why.** "Score = 74" doesn't tell a seller what to *do*. The verdict combines Fit Score and ACV into an action label — *Prime Target*, *Worth Pursuing*, *Keep Watch*, *Poor Fit* — so sellers can prioritize without having to interpret the numbers.

**What — the score color spectrum:**

| Score range | Color |
|---|---|
| ≥80 | Dark Green |
| 65–79 | Green |
| 45–64 | Light Amber |
| 25–44 | Amber |
| <25 | Red |

**ACV tiers:** High, Medium, Low.

**The grid:**

| Score | High ACV | Medium ACV | Low ACV |
|:---:|:---:|:---:|:---:|
| **≥80** | Prime Target · Dark Green | Strong Prospect · Dark Green | Good Fit · Dark Green |
| **65–79** | High Potential · Green | Worth Pursuing · Green | Solid Prospect · Green |
| **45–64** | High Potential · Light Amber | Worth Pursuing · Light Amber | Solid Prospect · Light Amber |
| **25–44** | Assess First · Amber | Keep Watch · Amber | Deprioritize · Amber |
| **<25** | Keep Watch · Red | Poor Fit · Red | Poor Fit · Red |

**Verdict definitions:**

| Verdict | What it communicates |
|---|---|
| **Prime Target** | Best possible combination. Build a strategy, align the team. |
| **Strong Prospect** | Great fit, meaningful opportunity. Pursue with confidence. |
| **Good Fit** | The fit is real. Worth your time. |
| **High Potential** | Gaps to work through but significant upside justifies the investment. |
| **Worth Pursuing** | Good fundamentals all around. Give it attention. |
| **Solid Prospect** | Decent fit, modest opportunity. Steady. |
| **Assess First** | Low fit today, but the opportunity is big. Do the homework before deciding. |
| **Keep Watch** | Not ready today. Opportunity is big enough to stay close and revisit when conditions change. |
| **Deprioritize** | Low fit, small opportunity. Focus elsewhere. |
| **Poor Fit** | Products don't align. Be honest about it. |

The grid and definitions are configured in `scoring_config.VERDICT_GRID`. This document is the Define-Once home for the verdict vocabulary. `Badging-and-Scoring-Reference.md` does not redefine these terms.

---

## ACV Potential Model

**Why.** A product sold through a global channel with a large certification ecosystem and a flagship event has fundamentally different annual revenue potential than a niche product with a regional footprint — even if both score identically on fit. ACV Potential answers "how big is this if we win?" — expressed as the estimated annual contract value if the customer standardized on Skillable across all training and enablement motions for the product. This is the Define-Once home for the ACV model; `Badging-and-Scoring-Reference.md` references this section rather than restating it.

**What — five consumption motions.** Each motion reflects both a reason people take labs AND a path for reaching them:

| # | Motion | Audience | Adoption | Hours | Zero when... |
|---|---|---|---:|---:|---|
| **1** | **Customer Training & Enablement** | Install base — total customers using the product this year | ~4% | 2 | Never (every product has customers) |
| **2** | **Partner Training & Enablement** | Global partner community — people reselling, deploying, supporting the product | ~15% | 5 | Company doesn't sell through a channel |
| **3** | **Employee Training & Enablement** | Relevant-employee subset — product team, support, SE, CS. **Not total headcount.** | ~30% | 8 | Never in practice |
| **4** | **Certification (PBT)** | People in the world who sit for the certification exam | **100%** | 1 | Product has no cert, or the cert has no lab component |
| **5** | **Events & Conferences** | Total attendees at the company's events (e.g., ~15,000 at Tableau Conference) | ~30% | 1 | Company doesn't run events. Events without labs today are the *opportunity*, not zero. |

**Motion 3 framing:** the audience must be narrowed to the relevant subset BEFORE the adoption % is applied. Applying ~30% to total headcount would massively overshoot. The researcher estimates the subset size per product.

**Motion 4 framing:** 100% is exact — if a lab is in the cert exam, everyone who sits for the cert takes the lab.

**How — per-motion calculation:**

```
Audience × Adoption × Hours = Annual Hours
Annual Hours × Rate = Annual Potential
```

Single values everywhere except audience. Audience is the only source of range in the final number — because that's where the real uncertainty lives. One source of range keeps the math clean and the final number defendable.

**Rate tier lookup — derived from Product Labability:**

| Delivery path (from Pillar 1) | Badges / facts that trigger this tier | Rate |
|---|---|---|
| **Cloud labs** | `Runs in Azure`, `Runs in AWS`, `Sandbox API` (green) | **~$6/hr** |
| **Small VM, Container, or Simulation** | `Runs in VM` alone (no Multi-VM / Complex Topology / is_large_lab), `Runs in Container`, `Simulation` | **~$9/hr** |
| **Typical VM** | `Runs in VM` with 1–3 VMs, standard footprint | **~$13/hr** |
| **Large or complex VM** | `Multi-VM Lab` OR `Complex Topology` fires on top of `Runs in VM` / `ESX Required`, OR `ProvisioningFacts.is_large_lab` is set | **~$45/hr** |

Rates use `~` to signal estimate. **One number per tier** — the final ACV range comes from audience variation, not from the rate. Rate ranges compound noise without adding precision and are forbidden here. Delivery path is determined once during Pillar 1 scoring — the ACV calculation looks it up, never redefines it. This is Define-Once: one source of truth for how a product gets delivered.

**Install base and partner community are Define-Once.** The same install base estimate feeds both Motion 1 audience AND Pillar 2 Market Demand. The researcher produces one install base number per product, and that number is used everywhere. Same rule applies to the global partner community size (feeds Motion 2 and Pillar 3 Delivery Capacity) and the delivery path (feeds the rate tier lookup and Pillar 1 badge display). Three Define-Once facts power the ACV model — all computed once, referenced everywhere.

**Range discipline.** Estimates must be **believable**. A range of 2,000–40,000 signals "we have no idea." The researcher produces tight, defendable ranges the seller can quote without caveats.

**The ACV Potential hero widget has three lines:**

| Line | Content |
|---|---|
| **1. `ACV POTENTIAL`** | Big range — company-level ACV across ALL discovered products (extrapolated from the scored sample) |
| **2. Descriptor** | `Estimated across all N discovered products` |
| **3. Scored subtotal** | `Estimate for ONLY the N scored products: $X – $Y` |

The word `ONLY` on line 3 is intentional and uppercase — it signals to the seller that line 3 is a subset, not a competing total. The two ranges together answer "how big is the full opportunity" AND "what can we defend with evidence today."

All ACV math is implemented in `acv_calculator.py`. Rate lookups come from `scoring_config.RATE_TABLES` + `ORCHESTRATION_TO_RATE_TIER`. Tier thresholds come from `ACV_TIER_HIGH_THRESHOLD` and `ACV_TIER_MEDIUM_THRESHOLD`.

---

## Inspector UX

### Hero Section

The hero section is the star of the show. Layout:

- **Left:** Product selector dropdown with verdict badge and "HIGH FIT · HIGH ACV" label
- **Center:** Fit Score — large and prominent
- **Right:** ACV Potential widget (three-line structure above)

No connector lines between hero and pillars. Pillar card padding balanced top/bottom.

### 70/30 Visual Split

The dossier body uses a 70/30 visual split reflecting the 70/30 product-vs-organization weighting:

- **Left (70%):** Two product Pillar cards — Product Labability and Instructional Value
- **Right (30%):** Customer Fit card, slightly different background to visually distinguish the organizational perspective

### Pillar Cards

Each Pillar card header has two icons at the same size, muted color, green on hover:

- **Info icon (?)** — opens the framework documentation section explaining how that Pillar works
- **Doc icon** — opens the full framework documentation

All dimension names display in ALL CAPS within the cards. Score bars use a gradient green/amber fill.

### Badge System

**Why.** Badges carry the visible story of a dimension's score. They are immediately readable, evidence-backed, and never drive the math. A badge is *context on a score*, not the score itself.

Each dimension card renders 2–4 badges. Every badge carries an evidence payload on hover (1.5-second delay → modal with evidence bullets, source, confidence). Purple is for classification (product subcategory, company classification), not scoring.

**Full operational detail — the four scoring colors and their meanings, the confidence language (`confirmed` / `indicated` / `inferred`), the badge naming rules, canonical vocabulary, per-dimension badge catalogs, and penalty signals — lives in `Badging-and-Scoring-Reference.md`.** This document does not duplicate that content.

### Navigation and Controls

- **Two nav links:** "Back to Product Selection" and "Search Another Company"
- **Cache date:** hoverable link; tooltip reads "Refresh cache"
- **Export:** Word export (not PDF) — sellers customize the document for their conversations

### Three-Box Bottom Row — Shared Pattern

**Why.** The three boxes at the bottom of the company view — Scored Products (left), Competitive Products (middle), ACV by Use Case (right) — should read as **one designed row**, not three independent components. Visual coherence builds trust (GP3) and makes the dossier feel like one intelligent surface.

**What — one shared pattern across all three:**

| Element | Rule |
|---|---|
| Font family | Same across all three |
| Font size | Same across all three — section titles match, body rows match |
| Vertical spacing | Row padding, row gap, header-to-body spacing all identical |
| Section title style | Same font, size, treatment across all three titles |
| Link style | **Arrow links** (→) — de facto platform standard, locked |

**The one intentional differentiator — middle box only.** Competitor product names render in **slate blue**. That's it. Color is the one visual signal that earns its own treatment because "competitors vs us" is the one distinction worth calling out. Everything else about the middle box (typography, spacing, layout) matches the other two exactly.

**The right box is structurally unique because the content demands it** — four columns (Audience, Adoption, Hours, Annual Hours) plus footer rows (Annual Hours total, Annual Potential range, Rate + delivery path note). Tight column widths prevent line wrap. Right-aligned numeric columns. But the visual pattern (font, size, spacing) matches the other two boxes. The right box must **not** have a purple hairline (that's a middle-box treatment) and must **not** have a black background (should match the rest of the row).

This is GP4 (Self-Evident Design) applied at the UX layer — one typography pattern, one spacing pattern, one link style, defined once, used everywhere.

### Company Classification

Company classification badge uses purple — same color as product subcategory badges. Purple is for classification, not scoring.

---

## Designer: The Complete Pipeline

**Why.** Designer turns product intelligence into an actionable build plan. It lives in the Intelligence Platform because every phase depends on deep product knowledge — what's possible, what's scorable, what infrastructure is required.

**What — eight phases:**

| Phase | What it does | Why it matters |
|---|---|---|
| **1. Intake** | Collects learning objectives, products, target audience, business objectives, job task analyses | Sets the scope — everything downstream derives from this |
| **2. Program outline** | Recommends lab series — names, descriptions, count | Structure based on product knowledge + objectives |
| **3. Lab breakdown** | Recommends individual labs per series — titles, descriptions, count | Granularity driven by product depth and learning goals |
| **4. Activity design** | Recommends 2–8 activities per lab, in sequence | Enables progress tracking — without activities, only completion data exists |
| **5. Scoring recommendations** | Recommends how to score each activity — AI Vision, PowerShell, API validation | Intelligence knows what's scorable and how |
| **6. Draft instructions** | Generates lab instructions — step-by-step or challenge-based | Tech writers edit instead of create from scratch |
| **7. Bill of materials** | Complete environment spec — VMs, cloud services, databases, dummy data, lifecycle actions | One pass, complete spec for the whole program |
| **8. Export package** | Lab series, lab profiles, instructions, build scripts — zipped for Studio import | Dev team's job becomes QA, finalize environments, publish |

**How.** Designer will eventually be a standalone application with its own authentication. For now, it lives in the platform and shares the intelligence brain. The architecture must support this separation — Designer's connection to product intelligence stays, but company intelligence is never accessible from Designer.

---

## Data Architecture: Three Domains

**Why.** Customers will eventually access Designer. They must never see the company intelligence that powers Prospector and Inspector. The separation is architectural, not just a permissions layer — when RBAC is implemented, it should be a configuration layer on top of an already-clean architecture, not a retrofit.

**What — three domains:**

| Domain | What it contains | Future access model |
|---|---|---|
| **Product data** | What products are, how they work, labability assessments, orchestration details | Open — anyone can see, including customers in Designer |
| **Program data** | Lab series, outlines, activities, instructions — created in Designer | Scoped — only your own programs |
| **Company intelligence** | Fit scores, badges, buying signals, customer fit data, contacts, ACV estimates | Internal-only — Skillable roles only |

**How.** No mixing these domains in the same database tables, API responses, or service calls in ways that would be hard to untangle later. The hard wall between Skillable and Customer roles is enforced at the data access layer.

### RBAC Roles (Tentative)

Every data field, API endpoint, and UX element must be permission-aware from the start. When RBAC is implemented, assigning and revoking access should be straightforward.

| Role | Tools | Data access |
|---|---|---|
| Skillable Admin | All | Full platform access |
| Skillable Prospector Admin | Prospector | Company intelligence, product data, contacts, ACV |
| Skillable CRM Integration Admin | HubSpot integration config | Company intelligence sent to HubSpot, field mappings |
| Skillable Seller (SAD / AE / CSM) | Inspector (via HubSpot + dossier) | Company intelligence (read), product data, seller briefcase |
| Skillable Solution Consultant (SE / TSM) | Inspector (full depth) | Company intelligence (read), product data, full evidence detail |
| Skillable Designer Admin | Designer (all programs) | Product data, all Skillable programs |
| Skillable Instructional Designer | Designer | Product data, assigned programs |
| Skillable SME | Designer | Product data, assigned programs |
| Customer Designer Admin | Designer (own programs only) | Product data (open), own programs only. **Never company intelligence.** |
| Customer Instructional Designer | Designer (own programs only) | Product data (open), assigned programs only |
| Customer SME | Designer (own programs only) | Product data (open), assigned programs only |

---

## Estimated Platform Costs

Rough cost estimates per operation. These will be updated with actual measurements once the backend is stable on the rebuilt Score layer.

| Operation | What it does | AI Calls |
|---|---|---|
| **Discovery** (Prospector / Caseboard) | Find products, build the product list | 1 discovery call + targeted product research calls |
| **Deep Dive** (Inspector full analysis) | Three parallel fact extractors per product + rubric grader calls for Pillars 2 / 3 + three parallel briefcase calls per product (Opus KTQ + Haiku Conv + Haiku Intel) | ~3 extractors × N products + 8 grader calls × N products + 3 briefcase calls × N products |
| **Cache reload** (re-visit a saved analysis) | Recompute ACV, reassign verdict, sort | **Zero AI calls** — pure Python |
| **Re-score after logic change** (`SCORING_LOGIC_VERSION` bump) | Fresh Deep Dive on next load | Same as Deep Dive |

Pillar 1 scoring is zero-Claude by design. Pillar 2 and Pillar 3 scoring is zero-Claude *after* the rubric grader runs — the scorers themselves are pure Python reading cached `GradedSignal` records. The rubric grader is the only Claude call the Score layer is allowed to make.

---

## Document Strategy

Two authoritative documents, clean boundary, zero duplication:

| Document | What it owns | Audience |
|---|---|---|
| **Platform-Foundation.md** (this doc) | Strategic authority — Guiding Principles, Three Layers of Intelligence, Layer Discipline, Define-Once, Search Modal rule, people and personas, motivation, scoring framework at a glance, Fit Score composition, Two Hero Metrics, Verdict Grid, **ACV Potential model**, Inspector UX, Designer pipeline, data architecture | Everyone — sellers, SEs, engineers, product, leadership |
| **Badging-and-Scoring-Reference.md** | Operational detail — every Pillar's dimensions, every scoring signal, every canonical badge, every strength tier, every penalty, every baseline, Technical Fit Multiplier table, risk cap reduction rules, penalty-visibility rule, Pillar 3 unification, badge naming rules, locked vocabulary | Developers, AI prompts, in-app help, anyone who needs to understand or modify the math |

Where the two docs touch (verdict grid, ACV model, pillar structure), **this document is the home** and the reference doc points back. Where the reference doc touches concepts (pillar questions, 70/30 split), it names them and refers back here. Neither doc duplicates what the other owns.

---

## Supporting Documents

| Document | Purpose |
|---|---|
| **`docs/collaboration-with-frank.md`** | How Frank thinks, how to work together, session startup sequence |
| **`docs/roadmap.md`** | Consolidated inventory of everything we want to do, are doing, or have done |
| **`docs/next-session-todo.md`** | What shipped last session, what's open, first thing to do next session |
| **`docs/decision-log.md`** | Write-only historical record of decisions made during sessions |
