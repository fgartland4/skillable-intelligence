# Skillable Intelligence Platform — Foundation

This is the authoritative source for the strategic foundation of the Skillable Intelligence Platform. All code, UX, documentation, and communication should align to what is defined here. Where conflicts exist with other documents, this document wins.

This document reflects best current thinking. As thinking evolves, this document evolves with it — fully synthesized, never appended. Best current thinking, always.

---

## Guiding Principles

**These are a thinking system, not a list.** Read them, then read the rest of this document, then come back and re-read them. The second pass is where they become operational — where you see how each GP shapes the architecture, the scoring, the UX, and how we work together. See `collaboration-with-frank.md` → "Re-reading Is the Point."

These are the capital-G, capital-P Guiding Principles of the platform. Every feature, every screen, every piece of content, every line of code should be testable against these.

### GP1: Right Information, Right Time, Right Person, Right Context, Right Way

> Right information, at the right time, to the right person, with the right context, in the right way.

| Right... | Means... |
|---|---|
| **Right information** | The specific thing they need, not everything we know |
| **Right person** | Different roles get different slices of the same data |
| **Right time** | When they need it — not before it's relevant, not after it's useful |
| **Right context** | Framed so they understand why it matters *to them* |
| **Right way** | Concise first. Progressive disclosure. Fewer words. Invite depth, don't force it |

### GP2: Why -> What -> How

Every insight, every recommendation, every judgment starts with **why** it matters, then **what** to do about it, then **how** to do it.

| Level | Question | What it does |
|---|---|---|
| **Why** | Why does this matter? | Creates common ground between technical and non-technical people |
| **What** | What do we need to create or solve? | Defines the scope of work |
| **How** | How do we build or implement it? | Execution detail |

This sequence is how the platform builds **conversational competence**. When designing any screen, card, or recommendation, ask:

1. Is the Why clear first?
2. Can someone stop here and be conversationally competent?
3. Can they keep going into What and How if they need to?

### GP3: Explainably Trustworthy

Every judgment the platform makes must be traceable, from conclusion back to evidence, so anyone can follow the reasoning and believe it.

- The scoring logic cannot be a black box
- Judgments must distinguish between fact and AI-informed assumption
- Documents produced by the platform are evidence trails, not just summaries
- Progressive disclosure is the trust mechanism — give the conclusion, then let people pull on the thread until they believe it
- The documentation IS the in-app explainability layer. At each section of the UX, users can click to see the actual framework documentation that explains how that section works. One source of truth, one click, digestible. When the documentation updates, the in-app help updates automatically — because it's the same content.

### GP4: Self-Evident Design

The platform's intent, logic, and structure must be evident at every layer — from variable names to UX output. Anyone inspecting any layer should understand why it exists, what it does, and how it connects to the whole.

| Layer | What self-evidence looks like |
|---|---|
| **Variable and field names** | Named after the concepts they represent — `training_commitment`, `delivery_capacity`, `organizational_dna` — not generic labels |
| **Component and module names** | You can tell what a module does and why it exists from its name |
| **Data models** | Pillars, dimensions, and requirements are explicit in the schema, not buried in unstructured text |
| **API surface** | Naming is clear and intentional |
| **AI prompts** | Variables flow in as named parameters that carry meaning, not hard-coded strings |
| **UX output** | Recommendations, badges, and rationale are all shaped by variables that trace back to the code |
| **Canonical lists** | One source of truth for any shared list (e.g., lab platform providers), referenced everywhere — never duplicated |

GP3 and GP4 are partners. Explainably Trustworthy is the standard. Self-Evident Design is how it's achieved at every layer. Together they mean: the platform explains itself — to users, to developers, to AI, to anyone who touches it.

### GP5: Intelligence Compounds — It Never Resets

Every interaction makes the data sharper. No update loses prior knowledge. The platform builds on what it already knows.

- Every analysis enriches what came before
- Deeper research (e.g., a full dossier) should automatically sharpen lighter data (e.g., Prospector records)
- Cache updates should preserve and sharpen, not wipe and restart
- Prompt changes should trigger smart invalidation, not silent drift
- **One persistent analysis per company.** Each company has a single stable URL. Every Deep Dive run accumulates products into the same analysis without breaking the URL. Re-running with the same products is instant (cached). Re-running with new products scores only the new ones and appends them. The seller can bookmark the URL — it always reflects best current thinking.

### GP6: Slow Down to Go Faster

Truly understanding a problem and answering it once is dramatically faster than solving it quickly, bouncing off the wrong answer, and solving it again. This applies to people, to AI assistants, and to the platform itself.

| Slow down means... | Not... |
|---|---|
| **Read before theorizing** | Diagnosing from memory or summary |
| **Verify the symptom against ground truth** (the cache, the code, the actual output) | Inferring what must be happening |
| **Present ONE grounded diagnosis, once** | A branching decision tree of maybe-fixes |
| **Distinguish root cause from symptom** | Treating the first thing you see as the bug |
| **Name structural questions when you spot them** | Burying them inside a code change |
| **Check for adjacent causes before declaring independence** | Assuming two bugs are unrelated because they wear different masks |

**Why this is a Guiding Principle, not a work habit:** the platform is maturing. Complexity compounds. At a certain point, the cost of a fast-but-wrong answer isn't just the rework — it's the confidence tax on every future decision that depends on the flawed one. Working slowly where it matters is how the platform stays trustworthy as it grows.

**Where it shows up operationally:**

- **In research:** read the cached JSON, read the code, read the docs — in that order — before proposing a fix.
- **In scoring changes:** trace the same signal through config -> math -> prompt -> docs -> tests before touching anything. Don't stop at the first file.
- **In UX changes:** check the shared components first. If there's already a pattern, use it; don't rebuild.
- **In AI prompts:** verify what the AI is actually emitting from the cached output before changing the prompt. The fix may be in the data the prompt reads, not the prompt itself.
- **In conversations:** when the right answer takes three more minutes of reading, take three more minutes of reading. A confident "I don't know yet, let me verify" is faster than two wrong answers.

**GP6 and GP3 are partners.** Explainably Trustworthy (GP3) is the standard the platform must meet; Slow Down to Go Faster (GP6) is the discipline that lets it meet the standard as the platform grows.

### The End-to-End Principle

The framework shapes how we **gather**, how we **store**, how we **judge**, and how we **present**. One model, end to end. The same Pillar/Dimension/Requirement structure runs through every layer — research, storage, scoring, display. No translation step. No reorganizing after the fact.

### Accessibility: WCAG AA Compliance

All UX elements must meet WCAG AA contrast standards (4.5:1 for normal text, 3.0:1 for large text). This is a build standard and a QA checkpoint — every color combination is validated before shipping. Accessibility is not optional.

### The Define-Once Principle

All Pillar names, dimension names, weights, thresholds, badge names, and vocabulary are defined **once** in a configuration layer and referenced everywhere — code, prompts, UX templates, documentation. Nothing is hard-coded. If a name or weight changes, it changes in one place and propagates through the entire system. No find-and-replace across files. No drift. This is how Self-Evident Design (GP4) works at the code level.

### The Layer Discipline Principle

The platform is built on a clear architectural separation: **three thin tools sit on top of one shared Intelligence layer.** The tools are Inspector, Prospector, and Designer. The Intelligence layer is everything that knows about products, companies, scoring, research, evidence, and the framework.

| Layer | What lives here | Examples |
|---|---|---|
| **Intelligence layer** (shared) | Research, discovery, scoring math, badge normalization, cache versioning, validation, briefcase generation, model definitions, prompt assembly, locked vocabulary, classification, verdicts, ACV computation | `intelligence.py`, `scorer.py`, `scoring_math.py`, `scoring_config.py`, `storage.py`, `models.py`, `prompt_generator.py`, `researcher.py`, `core.py`, `badge_normalization.py` |
| **Inspector** (tool) | Inspector-specific routes, request parsing, template selection, view orchestration | `app.py` Inspector route handlers, `tools/inspector/templates/*.html` |
| **Prospector** (tool) | Prospector-specific routes, batch orchestration, lookalikes UI, HubSpot integration glue | (future) Prospector routes + templates |
| **Designer** (tool) | Designer-specific routes, program design pipeline UX, customer-facing views | (future) Designer routes + templates |

**The discipline rule:** if a function does intelligence work — scoring, normalizing, validating, computing, classifying, recomputing, deciding what color a badge should be, deciding how to combine evidence — it belongs in the **Intelligence layer** where ALL three tools can call it. If it does view work — rendering a template, parsing a query string, redirecting, picking a default product index — it stays in the **tool layer**.

**The litmus test:** "would Prospector or Designer also need this if they were calling it?" If yes, shared. If no, tool. **When in doubt, default to shared.** Prospector batch scoring + lookalikes are real work coming next, and Designer needs product intelligence (with the hard wall against company intelligence). Three tools cannot have three drifted copies of the same scoring logic. The shared layer is the only way GP5 (Intelligence Compounds) actually compounds — drift across tools means each tool's intelligence is its own silo.

**Architectural enforcement:** intelligence functions in tool files are a **bug class**, not a stylistic choice. They are graded with the same severity as cache version lies and vocabulary drift. When the platform finds them, they get moved to the Intelligence layer or explicitly justified as tool-private with a comment.

---

## How the GPs Show Up in the Platform

*After reading the GPs, scan this table. It is the key that makes the rest of the document operational — every architectural choice below traces back to one or more of these principles. When re-reading, use this as the lens.*

| GP | Where it lives in the platform |
|---|---|
| **GP1** — right info, right time, right person, right way | Progressive Disclosure Stack · HubSpot-first for sellers · Seller Briefcase · persona-specific entry points · concise-first, depth on hover |
| **GP2** — Why → What → How | Every Pillar card leads with the question · Seller Briefcase opens with Why · conversational competence for both sellers and SEs starts with Why |
| **GP3** — Explainably Trustworthy | Confidence levels (confirmed / indicated / inferred) · evidence on hover · documentation is the in-app explainability layer · traceable from conclusion back to source |
| **GP4** — Self-Evident Design | Variable names carry meaning · Pillar / Dimension / Requirement hierarchy is explicit · `scoring_config.py` is the Define-Once source · names you can read without a glossary |
| **GP5** — Intelligence Compounds | One persistent analysis per company · cache sharpens, never wipes · prompt changes trigger smart invalidation · every analysis enriches what came before |
| **GP6** — Slow Down to Go Faster | Read ground truth before theorizing · one grounded diagnosis, not a branching maybe-list · trace signals end-to-end before editing · name structural questions when you see them · the platform's trust comes from doing the right thing once, not the wrong thing fast |
| **End-to-End** | Same Pillar / Dimension / Requirement model shapes research, storage, scoring, display — no translation step |
| **Define-Once** | All framework variables in one config · referenced everywhere · change once, propagate everywhere |
| **Layer Discipline** | Intelligence logic lives in the shared Intelligence layer (`intelligence`, `scorer`, `scoring_math`, `scoring_config`, `storage`, `models`, `prompt_generator`, `researcher`, `core`, `badge_normalization`). Tools (Inspector, Prospector, Designer) own URL handlers, request parsing, template selection — nothing more. When in doubt, default to shared. |

---

## The Center of Everything: Products

The product is the center of the entire platform. Not the customer, not the persona — the **product**. A product's fit with Skillable determines whether we can help a company at all.

### The Product-Up Model

The platform does not start with "what kind of company is this?" and guess at their products. It starts with the products, and the products tell you everything else. Labels, categories, messaging, and contacts all derive from the product data.

```
Products (the atomic unit)
  -> roll up to -> Product categories / verticals
    -> roll up to -> Company profile
      -> map to -> People (who builds training for THESE products)
```

This model is **variable-driven, not hard-coded**. Every label, category, description, and piece of messaging derives from the product data. Organization type is a variable. Motivation is a variable. Product category is a variable. All flow from the data, and all shape how intelligence is presented and communicated.

### Product-Market Fit = Product Labability

Product Labability determines product-market fit. It asks one fundamental question: **can Skillable deliver a complete lab lifecycle for this product?** The answer is measured across four dimensions: Provisioning, Lab Access, Scoring, and Teardown (detailed in Pillar 1 of the Scoring Framework).

If a product cannot pass these dimensions, it does not matter how big the company is, how much they spend on training, or how many employees they have. Skillable cannot help them.

These four dimensions should be surfaced visibly and early in the UX — not buried in technical detail. They help marketers, sellers, and SEs alike understand at a glance what's possible and where the gaps are. They shape conversations, inform questions, and guide where to focus.

### Product Labability Applies to the Underlying Technology — Always

Regardless of organization type, the four Product Labability dimensions always apply to the **underlying technology**, never to the training wrapper or organizational structure.

| Organization type | Intelligence path |
|---|---|
| **Software company** | Products -> labability assessment -> fit |
| **Training / Certification org** | Courses -> extract underlying technologies -> labability assessment -> fit |
| **University / School** | Curriculum -> extract underlying technologies -> labability assessment -> fit |
| **GSI / Content firm** | Client engagements -> products involved -> labability assessment -> fit |
| **LMS company** | Their customers' products -> labability assessment -> fit |
| **Distributor** | Products they distribute -> labability assessment -> fit |

If a course or curriculum doesn't teach anything that involves hands-on interaction with technology — a leadership course, a compliance reading course, a soft skills workshop — there's nothing to provision. No lab opportunity. Move on.

---

## Organization Types

Skillable serves a broad landscape. "Software companies" is the anchor — they create the products that everything else orbits around — but they are far from the only audience. The organization type determines how you find the products and how you approach the conversation, but the underlying intelligence logic is the same for all.

| Organization Type | Examples | Their relationship to products | How you find the products |
|---|---|---|---|
| **Software companies** | Microsoft, Trellix, Dragos, Opswat, Hyland, Majesco, UiPath, NICE, Tableau, Nutanix, NVIDIA, F5, Commvault, Cisco, Eaton, Trumpf | They *create* the software products | Product pages, documentation, API docs |
| **Training & certification organizations** | CompTIA, EC-Council, ISACA, SANS Institute, Cybrary, CREST, ZeroPoint Security, Swiss Cyber Institute, Skillsoft, QA | Their *products are training courses and certifications* | Course catalogs — extract the underlying technologies taught |
| **GSIs (Global System Integrators)** | Deloitte, Accenture, Cognizant | They *implement and deploy* other companies' products | Client engagements — what technologies are involved |
| **Content development firms** | GP Strategies | They *build learning programs* around other companies' products | Their program portfolio |
| **LMS companies** | Cornerstone, Docebo | They *host and deliver* learning programs | Their customers' products |
| **Distributors** | Ingram, CDW, Arrow | They *sell and resell* products and build training | Training catalogs and distribution portfolio |
| **Universities & schools** | Saint Louis University, Grand Canyon University, WGU, Academy of Learning (Launch Life) | Their *courses and degrees* cover technologies | Published curriculum |
| **Enterprise / multi-product** | Microsoft, Cisco, Siemens | Dozens of products across categories — each is a separate opportunity | Product portfolio — each assessed independently |

---

## Customer Motivation

### Three Motivations

Every organization that invests in hands-on training does so for one or more of these reasons:

| Motivation | Core drive | The stakes | Example signals |
|---|---|---|---|
| **Product adoption** | People use it, love it, don't churn | Revenue — if they don't adopt, they cancel | Customer enablement programs, adoption risk language, TTV concerns |
| **Skill development** | People are competent, certified, employable | Careers — if they can't do it, they can't get the job | Certification programs, university curricula, career-track training |
| **Compliance & risk reduction** | People don't make dangerous mistakes | Consequences — if they get it wrong, real harm happens | Regulatory requirements, healthcare/finance/cybersecurity contexts, audit readiness |

### How Motivations Work in the Platform

**Not mutually exclusive.** A single organization — even a single product — can have multiple motivations. A cybersecurity software company may have all three: product adoption (don't churn), skill development (train the channel), and compliance (one mistake = a breach).

**Contextual to the persona.** The same company's intelligence may be framed differently depending on who it's being served to. Sales-side personas see the product adoption angle. Training-side personas see skill development. Regulated industries surface compliance regardless of persona. This connects directly to GP1 — right person, right context.

**All motivations lead to confidence.** Neither is negative. All genuinely care about the learner:

| Motivation | They want the learner to be... | So that... |
|---|---|---|
| **Product adoption** | Confident *in the product* | They love it, adopt it, grow with it, don't leave |
| **Skill development** | Confident *in themselves* | They have the skills, get the job, come back to learn more |
| **Compliance & risk** | Confident *under pressure* | They perform correctly when the stakes are real |

---

## The People

### Two Audiences, One Hard Wall

| Audience | Tools | Purpose |
|---|---|---|
| **Skillable internal** | Prospector + Inspector | Target the right companies, prepare for conversations, research products |
| **Customers** (eventually) + Skillable ProServ | Designer | Build lab programs based on product intelligence |

Customers never see Prospector or Inspector data. Ever. This boundary is architectural — not just a permissions layer. There should be no path from Designer to company intelligence data.

### Personas by Tool

**Prospector (Targeting)** serves Marketing and RevOps. It delivers three things:

1. **Enrichment** — deeper intelligence about companies you already know, scored against product fit
2. **Product Lookalikes** — companies you didn't know about, found because they use products that pass Product Labability (product-fit matching, not firmographic matching)
3. **Contacts** — specific humans responsible for training/enablement for products Skillable can serve

Prospector's principle: deliver intelligence to marketing where they work (HubSpot), not where we work. Design for integration from the start.

**Inspector (Evaluation & Research)** serves the spectrum from sellers to deep technical roles:

| Persona | What they need | Where they start |
|---|---|---|
| **Sellers (AE, Account Directors)** | Product-fit confirmation, buying signals, conversational competence points | HubSpot — click deeper when needed |
| **CSMs** | Expansion opportunities, product fit for upsell | HubSpot — click deeper when needed |
| **SEs** | Deep product research, technical detail, orchestration specifics | Inspector directly (or from HubSpot) |
| **TSMs** | Same as SEs — technical depth | Inspector directly (or from HubSpot) |

Executives are not a separate persona — they have the same needs as above with broader range.

**Designer (Program Design)** serves the builders — the people who have already decided to create labs:

| Persona | Role |
|---|---|
| **Enablement / Training Program Owners** | Strategy — which audiences, what outcomes, how many labs |
| **Instructional Designers** | Learning experience design — sequencing, objectives, assessment |
| **SMEs (Subject Matter Experts)** | Product accuracy — what's worth teaching, what's realistic |
| **Tech Writers** | Lab content — instructions, steps, guidance |
| **Product Engineers** | Technical feasibility — what can be done, how it works |
| **Skillable Professional Services** | All of the above, on behalf of customers |

### Conversational Competence

Conversational competence is a core platform concept: **the platform makes every Skillable persona credible in the conversations they need to have, by closing their knowledge gap in the direction it runs.**

It is bidirectional:

| Who | Gap direction | What competence looks like |
|---|---|---|
| **Sellers / CSMs** | Toward product understanding | "I understand the purpose of your product, why hands-on training makes sense for it, and how Skillable fits. I'm not an architect, but I'm not wasting your time." |
| **SEs / Technical folks** | Toward instructional design understanding | "I understand why specific lab types matter for specific learning outcomes. I can recommend the right labs, not just build the environment." |

Conversational competence is built through GP2 (Why -> What -> How). Starting with Why creates common ground between technical and non-technical people. It is the universal starting point.

### The Progressive Disclosure Stack

The entire platform is one continuous progressive disclosure path — one intelligence stream at increasing depth. The tool boundaries are entry points based on who you are and what you need.

| Layer | What you see | Who starts here |
|---|---|---|
| **HubSpot card** | Fit confirmation, key badges, "worth pursuing" confidence, ACV signal, HubSpot ICP Context | Marketing, Sellers, CSMs |
| **Inspector Caseboard** | All products for a company — scores, badges at a glance, Fit Score + ACV Potential | SEs, TSMs (or anyone who clicked deeper) |
| **Dossier top sections** | Overall assessment, key findings, organizational context | Anyone exploring a company |
| **Product cards (Dossier)** | Technical detail — labability dimensions, features, orchestration specifics | SEs, TSMs digging into a specific product |
| **Designer** | Lab series, lab breakdown, activities, scoring, instructions, bill of materials | Program Owners, IDs, SMEs, Tech Writers, ProServ |

Nobody is forced to see more than they need. Nobody is locked out of going deeper. The design is intentional about where each persona *should* start — but the platform doesn't gatekeep.

### Seller Briefcase

Below the three Pillar cards in the dossier, each Pillar has a **briefcase section** — 2-3 sharp, actionable bullets that arm the seller for conversations. This is conversational competence (GP2) delivered in the most practical form possible.

| Section | Under which Pillar | What it gives the seller |
|---|---|---|
| **Key Technical Questions** | Product Labability | Who to find at the customer, what department they're in, and the specific technical questions that unblock the lab build. Includes a verbatim question the champion can send. |
| **Conversation Starters** | Instructional Value | Product-specific talking points about why hands-on training matters for this product. Makes the seller credible without being technical. |
| **Account Intelligence** | Customer Fit | Organizational signals — training leadership, org complexity, LMS platform, competitive signals, news. Context that shows the seller has done their homework. |

Each section has an info icon that links to the documentation section explaining how that part of the framework works (GP3). The briefcase is generated by the AI from the same research that produces the scores and badges. Each bullet is specific to the company and product — never generic. The briefcase is the bridge between "this is a good opportunity" and "here's exactly what to do next."

**Briefcase is per-product, not per-analysis.** Each scored product has its own Seller Briefcase. When the user picks a different product from the dropdown, the briefcase swaps to that product's briefcase. Cached products keep their cached briefcase — only newly scored products get a fresh briefcase generation.

**Each section uses the right brain for its job.** The three sections are generated by three separate AI calls per product, not one. Each section has its own focused system prompt and runs on the model best suited to its purpose:

| Section | Model | Why |
|---|---|---|
| **Key Technical Questions** | Opus 4.6 | Sales-critical. Drives the conversation with the technical champion. The bullets must be sharp, specific, and answerable — quality over speed. |
| **Conversation Starters** | Haiku 4.5 | Pattern-matched, fast. Product-specific talking points the seller can use without sounding scripted. |
| **Account Intelligence** | Haiku 4.5 | Pattern-matched, fast. Surface organizational signals from existing scoring data. |

All three sections per product run in parallel, and across N products that's 3N parallel calls — total time gated by the slowest call (Opus KTQ ~20 seconds). Each call receives the full scoring context for that product (all pillar scores, dimensions, badges, evidence) so it synthesizes from what's already known instead of doing fresh research.

---

## Scoring Framework

### Hierarchy

The scoring framework follows a clear hierarchy:

- **Fit Score** — the composite, made up of three Pillars
  - **Pillars** — the three weighted components of the Fit Score
    - **Dimensions** — the specific areas measured within each Pillar (four per Pillar)
      - **Requirements** — the most granular level; what the AI researches and evaluates. These surface as badges in the UX.

### The 70/30 Split

The Fit Score is 70% about the product and 30% about the organization. The product is the center of everything — it dominates the score. The organization matters because it determines whether the opportunity will actually happen — but the product truth comes first.

| Level | Pillars | Combined weight |
|---|---|---|
| **Product** | Product Labability + Instructional Value | 70% |
| **Organization** | Customer Fit | 30% |

### Three Pillars

| Pillar | Weight | Level | UX Question |
|---|---|---|---|
| **Product Labability** | 40% | Product | How labable is this product? |
| **Instructional Value** | 30% | Product | Does this product have instructional value for hands-on training? |
| **Customer Fit** | 30% | Organization | Is this organization a good match for Skillable? |

Each Pillar scores out of 100 internally, then gets weighted. A Product Labability score of 85/100 contributes 85 x 0.40 = 34 points to the Fit Score. This makes scores intuitive — 85 out of 100 is clearly strong.

### Badge System

Badges are variable-driven visual indicators that surface requirements in the UX. Each badge has a name and a color. Fewer badges with more context is better than many badges with less context. The detail lives in the evidence bullets when you drill deeper.

**Four badge colors:**

| Color | Meaning | Qualifier label |
|---|---|---|
| **Green** | Strength / Opportunity | `| Strength:` or `| Opportunity:` |
| **Gray** | Neutral / Context | `| Context:` |
| **Amber** | Risk / Caution | `| Risk:` |
| **Red** | Blocker | `| Blocker:` |

**Purple badges** are used for classification — product subcategory and company classification. Purple is not a scoring color; it signals categorization, not assessment. Consistent color across all classification badges.

**Evidence on hover:** Every badge carries an evidence payload. Hovering over a badge for 1.5 seconds triggers a modal with evidence bullets, source, and confidence level. No badge renders without evidence. This is how GP3 (Explainably Trustworthy) works at the badge level.

**Evidence confidence coding:**

Confidence is core logic in the codebase — every finding carries a confidence level as a stored field. It influences badge color assignment, surfaces in evidence language, and is available to downstream consumers. Three levels:

| Level | Phrasing | What it means |
|---|---|---|
| **Confirmed** | "REST API **confirmed** — OpenAPI spec at docs.trellix.com" | Direct evidence from a primary source |
| **Indicated** | "VM deployment **indicated** — installation guide references Windows Server" | Strong indirect evidence, multiple signals |
| **Inferred** | "Troubleshooting lab potential **inferred** from category norms" | AI-informed assumption based on patterns or limited signals |

The badge color tells you the assessment. The evidence language tells you the basis. Together they're complete.

**Badge naming principles:**

- Name the **solution**, not the problem, when the recommendation is clear
- Use variable-driven badge text when the specific finding IS the answer (e.g., LMS name, competitor name, user count, region)
- If something is green and unremarkable, don't surface — only show what matters
- No dimension should need more than three to five badges to tell its story — if more are needed, detail belongs in evidence bullets

**Evidence bullet standard:** Clear, concise, and complete. Every bullet must be all three. No filler. No vague language. Specific details, specific sources, specific reasoning.

### Badge Display by Tool

| Tool | What appears |
|---|---|
| **Prospector** | Color + HubSpot ICP Context (synthesis note — 1-2 sentences, why this score) |
| **Inspector Caseboard** | Color + badge name (no rationale) |
| **Inspector Dossier hero** | Color + badge name; click-through to evidence |
| **Inspector Dossier drill-down** | Full evidence bullet with source and rationale |
| **Designer** | Green signals become program design inputs; badges not shown |

**HubSpot Integration** (data sent, not UX controlled): Fields sent from Prospector and Inspector — Fit Score, ACV Potential, HubSpot ICP Context, key badges, product list, contacts. HubSpot ICP Context is regenerated from best current intelligence every time data is sent (GP5).

### Two Hero Metrics

| Metric | What it answers | How it's determined |
|---|---|---|
| **Fit Score** | Should we pursue this? | Composite of three Pillars |
| **ACV Potential** | How big is this if we win? | Calculated: population x adoption x hours x rate |

These are the two hero elements in the UX — visible at the top of every dossier and caseboard entry. Separate outputs, not one composite. The Fit Score is a qualitative assessment. ACV Potential is a calculated business metric. ACV values use lowercase k for thousands and uppercase M for millions (e.g., 250k, 1.2M).

### Verdict Grid

The verdict combines Fit Score and ACV Potential into a single action-oriented label. It tells the seller what the opportunity looks like and what action makes sense — without predicting customer behavior or dictating effort.

**Score color spectrum:**

| Score range | Color |
|---|---|
| >=80 | Dark Green |
| 65-79 | Green |
| 45-64 | Light Amber |
| 25-44 | Amber |
| <25 | Red |

**ACV tiers:** High, Medium, Low. ACV values use lowercase k for thousands and uppercase M for millions.

**Verdict grid:**

| Score | High ACV | Medium ACV | Low ACV |
|:---:|:---:|:---:|:---:|
| **>=80** | Prime Target | Strong Prospect | Good Fit |
| | Dark Green | Dark Green | Dark Green |
| **65-79** | High Potential | Worth Pursuing | Solid Prospect |
| | Green | Green | Green |
| **45-64** | High Potential | Worth Pursuing | Solid Prospect |
| | Light Amber | Light Amber | Light Amber |
| **25-44** | Assess First | Keep Watch | Deprioritize |
| | Amber | Amber | Amber |
| **<25** | Keep Watch | Poor Fit | Poor Fit |
| | Red | Red | Red |

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

---

### Pillar 1: Product Labability (40%)
*How labable is this product?*

The gatekeeper. If this fails, nothing else matters. Measures whether Skillable can deliver a complete lab lifecycle for this product. 70% of the Fit Score is about the product — and this Pillar is the foundation of that.

| Dimension | Weight | Question |
|---|---|---|
| **Provisioning** | 35 | How do we get this product into Skillable? |
| **Lab Access** | 25 | Can we get people in with their own identity, reliably, at scale? |
| **Scoring** | 15 | Can we assess what they did, and how granularly? |
| **Teardown** | 25 | Can we clean it up when it's over? |

**Provisioning determines difficulty for everything else.** When a product runs in Skillable's infrastructure (VM, container, Cloud Slice), the other dimensions are largely within Skillable's control. When a product runs in the vendor's own cloud, every dimension depends on the vendor's APIs and policies — significantly more risk.

---

### Pillar 2: Instructional Value (30%)
*Does this product have instructional value for hands-on training?*

The commercial case. Measures whether this product genuinely warrants hands-on lab experiences. For operational detail on tier values, signal categories, badge naming, baselines, and penalty signals, see `Badging-and-Scoring-Reference.md` → Pillar 2.

| Dimension | Weight | Question |
|---|---|---|
| **Product Complexity** | 40 | Is this product hard enough that someone needs repeated hands-on practice to become competent? |
| **Mastery Stakes** | 25 | What are the consequences of getting it wrong? |
| **Lab Versatility** | 15 | What kinds of high-value hands-on skill development and skill validation experiences could be designed and delivered on Skillable for this product? |
| **Market Demand** | 20 | How big is the worldwide population of people who need to learn this product at hands-on depth? |

**Posture — default-positive, category-aware baselines.** Every Pillar 2 dimension starts from a baseline derived from the product's top-level category. The baseline is the realistic starting point for a typical product in that category; findings move the score up (specific positive evidence) or down (explicit negative evidence like `Consumer Grade` or `Simple UX`). Missing evidence means baseline, not zero. The question shifts from *"is there evidence of instructional value?"* to *"is there any reason this product would NOT have instructional value?"*

**Category master list** (shared across all four Pillar 2 dimensions and with Pillar 3 for cross-pillar compounding): Cybersecurity · Cloud Infrastructure · Networking/SDN · Data Science & Engineering · Data & Analytics · DevOps · AI Platforms & Tooling · Data Protection · ERP · CRM · Healthcare IT · FinTech · Legal Tech · Industrial/OT · Infrastructure/Virtualization · App Development · Collaboration · Content Management · Social/Entertainment · Unknown (fallback with classification review flag). Social/Entertainment replaces the old ambiguous "Consumer" bucket and captures only true no-training-market cases (Facebook, Instagram, TikTok, Netflix, Spotify).

**Market Demand is derivative.** Market Demand approximates Product Complexity × Mastery Stakes × Specialist Population Size. Complex products with high stakes AND a large specialist population (cybersecurity professionals, cloud engineers, AI developers) score at the top. Popular consumer products with no specialist training population score near zero. Salesforce admins are a real population but smaller per company than cyber pros, so CRM trails cybersecurity in Market Demand.

**Cross-pillar evidence compounding.** Certain facts legitimately fire in multiple pillars. `Multi-VM Lab` in Pillar 1 Provisioning also fires `multi_vm_architecture` in Pillar 2 Product Complexity. `~500 ATPs globally` in Pillar 3 Delivery Capacity also fires as positive Market Demand evidence (partners don't exist without skill demand). `Active cert exam` fires in both Delivery Capacity and Market Demand. The prompt template instructs the AI to cross-reference evidence between pillars at badge-emission time.

**Lab Versatility** connects directly to Designer. The lab type signals identified here (Red vs Blue, Break/Fix, Simulated Attack, Team Handoff, Incident Response, CTF, etc.) feed into Designer as starting points for program recommendations. In Inspector, they provide conversational competence for sellers — specific, product-relevant talking points about what kinds of hands-on experiences could be designed and delivered on Skillable.

---

### Pillar 3: Customer Fit (30%)
*Is this organization a good match for Skillable?*

Everything about the organization in one Pillar. Combines training commitment, build capacity, delivery capacity, and organizational DNA. 30% of the Fit Score — meaningful but never overriding the product truth. For operational detail on tier values, signal categories, badge naming, baselines, and penalty signals, see `Badging-and-Scoring-Reference.md` → Pillar 3.

| Dimension | Weight | Question |
|---|---|---|
| **Training Commitment** | 25 | Are you committed to helping your people become genuinely competent — not just checking a training box? |
| **Build Capacity** | 20 | Are you tailoring what you need, or just buying generic training? Are you actually building the hands-on content for your audience? |
| **Delivery Capacity** | 30 | Once labs exist — whether you built them or Skillable ProServ did — does your organization have the infrastructure and network to get them to learners at scale? |
| **Organizational DNA** | 25 | Are you the kind of company that partners strategically with outside platforms to build strategic assets — or are you a "we build everything here" culture? |

**Posture — default-realistic, organization-type baselines.** Every Pillar 3 dimension starts from a baseline derived from the organization's type (identified during discovery via the company classification: ENTERPRISE SOFTWARE, SOFTWARE category-specific, TRAINING ORG, ACADEMIC, SYSTEMS INTEGRATOR, PROFESSIONAL SERVICES, CONTENT DEVELOPMENT, LMS PROVIDER, TECH DISTRIBUTOR, Unknown). The baseline reflects the realistic starting point for a typical organization of that type; findings move the score up (positive evidence) or down (penalty signals on explicit absence).

**Research asymmetry is baked into the penalty design.** Not all CF dimensions are equally verifiable from outside the firewall:

| Dimension | Verifiability | Penalty philosophy |
|---|---|---|
| **Delivery Capacity** | Easy (outward-facing — ATPs, events, course calendars, cert infrastructure are public) | **Penalize aggressively** when signals are absent |
| **Build Capacity** | Hard (inward-facing — internal authoring roles, content teams are mostly invisible) | **Penalize cautiously** — only when research finds direct positive evidence of outsourcing, not for absence of evidence |
| **Training Commitment** | Moderate | Penalize on missing customer-facing signals, be cautious about employee-only evidence |
| **Organizational DNA** | Moderate | Penalize confidently on well-documented signals (RFP processes, build-everything culture), cautiously on inferred signals |

**Training Commitment** is about *philosophical investment* — does the organization have a heart for teaching? It's not about lab infrastructure (Build Capacity) or delivery mechanisms (Delivery Capacity). Strong signals include customer enablement teams, active certification programs, and breadth across audiences (employees + customers + partners). The multi-audience signal is particularly important — an organization that trains all three audiences shows the deepest commitment.

**Build Capacity** is about whether the organization tailors its own training or buys generic off-the-shelf content. The strongest signal is `DIY Labs` — already building hands-on labs today. ProServ can fill a Build Capacity gap, which is why Build Capacity is weighted lowest (20). Baselines cluster centrally because internal capacity is hard to verify from outside.

**Delivery Capacity** is weighted highest (30) because of a share-of-wallet reality — having labs = cost, delivering labs to learners = value. Without delivery infrastructure, labs are a cost center that never reaches learners. Geographic reach matters (Indiana < US < Western Hemisphere < Global), as do ATP networks, flagship events, and certification delivery infrastructure. **Low Build Capacity + strong Delivery Capacity + strong Training Commitment = Professional Services Opportunity** — Skillable can build for them.

**Organizational DNA** measures the cultural pattern around partnerships — **does this organization see outside platforms as strategic assets or as procurement line items to squeeze?** The old `Build vs Buy` badge is retired (it was a topic label whose color carried the finding — a GP4 violation). The new canonicals are `Platform Buyer`, `Builds Everything`, `Multi-Type Partnerships`, `Strategic Alliance Program`, `Long RFP Process`, `Heavy Procurement`, `Hard to Engage`, and similar finding-named badges. IBM-style "we build everything here" culture is a real penalty. Companies that use Salesforce, Workday, and Okta rather than building their own are signaling platform-buyer DNA.

---

### ACV Potential

ACV Potential is calculated, not scored. It is the estimated annual contract value if a customer standardized on Skillable for all training and enablement motions.

**ACV = Population x Adoption Rate x Hours per Learner x Rate**

The rate depends on the delivery path determined by Product Labability:
- VM labs (Hyper-V/ESX): $12-55/hr depending on complexity
- Cloud labs (Azure/AWS Cloud Slice): $6/hr platform rate (cloud consumption billed separately)
- Container labs: $6-12/hr
- Simulation: $5/hr

Six consumption motions feed the calculation:
1. Customer Onboarding & Enablement
2. Authorized Training Partners & Channel Enablement
3. General Practice & Skilling Experiences
4. Certification / PBT
5. Employee Technical Enablement
6. Events & Conferences

Each motion reflects both motivation (why people would take labs) and delivery reach (how many people could). The consumption motions are where motivation and delivery capacity converge into revenue.

Delivery reach directly drives ACV. CompTIA with millions of global certification candidates has a fundamentally different ACV potential than a niche content management company — even if both score identically on fit.

---

## Inspector Dossier UX

### Hero Section

The hero section is the star of the show. Layout:

- **Left:** Product name with dropdown selector (products listed with name left-aligned truncated at ~40 chars, score, purple subcategory badge)
- **Center:** Fit Score — the star of the show, large and prominent
- **Right:** ACV Potential

Below the product name: verdict badge, then "HIGH FIT · HIGH ACV" label (all caps).

### 70/30 Visual Split

The dossier body uses a 70/30 visual split reflecting the 70/30 product vs organization weighting:

- **Left (70%):** Two product Pillar cards — Product Labability and Instructional Value
- **Right (30%):** Customer Fit card, slightly different background to visually distinguish the organizational perspective

No connector lines between hero and pillars. Pillar card padding balanced top/bottom.

### Pillar Cards

Each Pillar card header has two icons at the same size, muted color, green on hover:
- **Info icon (?)** — links to the documentation section explaining how that Pillar works
- **Doc icon (document SVG)** — links to the full framework documentation

All dimension names display in ALL CAPS within the cards. Score bars use a gradient green/amber fill.

### Navigation and Controls

- **Two nav links:** "Back to Product Selection" and "Search Another Company"
- **Cache date:** Shown as a hoverable link; tooltip reads "Refresh cache"
- **Export:** Word export (not PDF) — sellers can customize the document for their conversations

### Product List

Below the Pillar cards and briefcase sections, a product list table shows all discovered products: product name, purple subcategory badge, score, and a doc icon link.

### Company Classification

Company classification badge uses purple — same color as product subcategory badges. Purple is for classification, not scoring.

---

## Designer: The Complete Pipeline

Designer is a program design tool that turns product intelligence into an actionable build plan. It lives in the Intelligence Platform because every phase depends on deep product knowledge — what's possible, what's scorable, what infrastructure is required.

| Phase | What it does | Why it matters |
|---|---|---|
| **1. Intake** | Collects learning objectives, products, target audience, business objectives, job task analyses | Sets the scope — everything downstream derives from this |
| **2. Program outline** | Recommends lab series — names, descriptions, count | Structure based on product knowledge + objectives |
| **3. Lab breakdown** | Recommends individual labs per series — titles, descriptions, count | Granularity driven by product depth and learning goals |
| **4. Activity design** | Recommends 2-8 activities per lab, in sequence | Enables progress tracking — without activities, only completion data exists |
| **5. Scoring recommendations** | Recommends how to score each activity — AI vision, PowerShell, API validation | Intelligence knows what's scorable and how |
| **6. Draft instructions** | Generates lab instructions — step-by-step or challenge-based | Tech writers edit instead of create from scratch |
| **7. Bill of materials** | Complete environment spec — VMs, cloud services, databases, dummy data, lifecycle actions | One pass, complete spec for the whole program — eliminates iterative environment rebuilds |
| **8. Export package** | Lab series, lab profiles, instructions, build scripts — zipped for Studio import | Dev team's job becomes QA, finalize environments, publish |

Designer will eventually be a standalone application with its own authentication. For now, it lives in the platform and shares the intelligence brain. The architecture must support this separation — Designer's connection to product intelligence stays, but company intelligence is never accessible from Designer.

---

## Prompt Generation System

The AI scoring prompt is not a static text file. It is **generated at runtime** by combining three distinct inputs: what we know about the company (research), what Skillable can do (platform knowledge), and how to evaluate the fit (scoring framework). This eliminates fragility, prevents drift, and ensures every scoring run reflects the current state of all three.

### The Three Inputs to Every Scoring Run

| Input | What it is | Where it lives | Who updates it |
|---|---|---|---|
| **Company Research** | What we know about THEM — products, training programs, partner ecosystem, delivery infrastructure, org structure, contacts | `data/company_intel/` — gathered by the researcher, stored per company, organized by dimension | Updated automatically every time research runs |
| **Skillable Knowledge** | What WE can do — platform capabilities, delivery patterns, supported services, competitor positioning, contact guidance | `backend/knowledge/` — JSON files, human-readable, updatable without code changes | Product team, SEs, sales leadership — as the platform evolves |
| **Scoring Framework** | The RULES — how to evaluate, what to score, what weights to apply, what badges to assign, what evidence standards to enforce | `backend/scoring_config.py` — the single source of truth for all framework variables | Platform architects — when the framework itself changes |

**Research is about them. Knowledge is about us. The framework is how we evaluate the fit between the two.** The Prompt Generation System brings all three together at runtime.

### The Three Layers of Prompt Generation

| Layer | What it is | How it works |
|---|---|---|
| **Configuration** | All variables that define the scoring model — pillar names, dimension names, weights, badge definitions, scoring signals, penalties, thresholds, vocabulary | A single structured file (Python dataclasses). The one place framework rules change. Validated on load — missing or invalid data throws errors before the AI ever sees it. |
| **Template** | The prompt structure — instructions for the AI with placeholders that pull from the configuration, knowledge, and research | A template file that defines how to instruct the AI. Rarely changes unless the fundamental approach changes. Contains the reasoning framework, the evidence standards, the output format — with {variable} references. |
| **Generated Prompt** | Configuration + Skillable Knowledge + Company Research assembled into the template at runtime — this is what the AI actually receives | Built in memory at the moment of scoring. Never saved as a static file. Always current. Always consistent. |

### What Lives in the Scoring Configuration

The scoring framework — everything about HOW to evaluate:

| Category | Examples |
|---|---|
| **Pillar structure** | Names, weights, UX questions (Product Labability 40%, Instructional Value 30%, Customer Fit 30%) |
| **Dimension structure** | Names, weights within each Pillar, questions |
| **Badge definitions** | Names, color criteria (green/gray/amber/red), scoring signals, point values |
| **Penalties** | Names, deduction values, which dimension they apply to |
| **Thresholds** | Score ranges for verdict grid (80/65/45/25), ACV tier boundaries |
| **Verdict labels** | The 10 verdict names and their definitions |
| **Category priors** | Product categories and their demand ratings |
| **Lab type menu** | The 12 lab versatility types with likely product mappings |
| **Canonical lists** | Lab platform providers, LMS partners, organization types, locked vocabulary |
| **ACV rates** | Delivery path rate tables, consumption motion labels, adoption ceilings |
| **Confidence rules** | When to use confirmed vs. indicated vs. inferred |
| **Reasoning sequence** | The step-by-step order the AI follows when scoring |
| **Evidence standards** | Writing rules for evidence bullets — labels, qualifiers, length limits, uniqueness rules |

### What Lives in Skillable Knowledge

What Skillable can do — stored as structured JSON data files in `backend/knowledge/`, updatable without code changes:

| File | What it contains | Who updates it |
|---|---|---|
| **skillable_capabilities.json** | Platform capabilities — datacenter fabrics, Cloud Slice modes (CSR/CSS), supported Azure/AWS services, scoring methods, container support, M365 tenant provisioning, BIOS GUID pinning | Product team as features ship |
| **delivery_patterns.json** | The delivery patterns with guidance — ADO, GitHub, vSphere, identity lifecycle, OVA import, Custom API, Simulation, and all variations | Product team + SEs |
| **competitors.json** | Competitor profiles — detection domains, positioning, Skillable advantages | Sales/marketing as landscape changes |
| **contact_guidance.json** | Decision maker and influencer title rules, exclusions, fallback behavior | Sales leadership |

This separation matters: when Skillable ships a new Cloud Slice feature or adds support for a new Azure service, someone updates the knowledge file. The next scoring run picks it up automatically. No code changes. No redeployment. No risk of breaking the scoring framework.

### What Lives in the Template

The template is a structural skeleton — it arranges configuration, knowledge, and research sections into a complete prompt. It contains almost no hard-coded content. The only thing hard-coded is the assembly structure itself: put section A here, then section B here.

### What the Researcher Gathers and Stores

Company research is gathered by the researcher and stored in the company intelligence domain, organized by dimension so the AI receives evidence that's already structured for evaluation:

**Product-level research (per product):**
- Provisioning signals — installers, marketplace listings, Docker images, API documentation
- Lab Access signals — auth APIs, SSO, credential management, NFR programs, MFA requirements
- Scoring signals — API endpoints for state validation, CLI tools, scriptable surfaces
- Teardown signals — DELETE endpoints, cleanup APIs, resource group scope vs tenant scope
- Product Complexity signals — documentation breadth, configuration depth, role diversity
- Mastery Stakes signals — high-stakes scenarios, learning curve evidence, adoption risk
- Lab Versatility signals — product-type to lab-type mapping
- Market Demand signals — install base, growth, certification, competitor labs

**Company-level research (per company):**
- Training Commitment — enablement programs, certification programs, training catalogs, compliance training, training leadership
- Organizational DNA — partner ecosystem, build-vs-buy signals, API/marketplace maturity, org complexity
- Delivery Capacity — ATP network, LMS platforms (by name), lab platforms (domain detection), gray market training
- Build Capacity — content dev team evidence, technical build roles, DIY labs, outsourcing signals

**Domain-based lab platform detection** scans fetched pages for outbound links to known platform domains. A URL link is stronger evidence than a name mention.

### Why This Architecture Matters

| Problem with static prompts | How the generation system solves it |
|---|---|
| Changing a weight means editing a 700-line text file | Change one number in the config |
| Adding a badge means updating multiple sections | Add it once in the config, template picks it up |
| Badge names in the prompt can drift from badge names in the code | Both read from the same config — impossible to drift |
| No validation — a typo silently breaks scoring | Config validates on load — errors caught before the AI runs |
| Testing requires reading the whole prompt | Test the config independently — do weights add to 100? Are all badges defined? |
| Updating vocabulary means find-and-replace | Vocabulary is in the config — one change propagates everywhere |
| Skillable ships a new feature | Update a knowledge JSON file — no code changes needed |
| Research misses a signal | Improve the researcher — scoring framework stays untouched |

### Config and Knowledge Administration (Future)

When AuthN/AuthZ is implemented, both the scoring configuration and the Skillable knowledge files will have admin-only GUI access:

- View and edit all configuration values and knowledge data through a clean interface
- Validation runs automatically on save — prevents invalid configurations
- Change history with timestamps and user attribution — full auditability
- Role-restricted — only platform administrators can access
- Changes take effect on the next scoring run — no deployment needed

This means a product leader can update Skillable capabilities, a scoring analyst can adjust weights, and a sales leader can update contact guidance — all without touching code, prompts, or templates.

---

## Data Architecture: Three Domains

The codebase must cleanly separate three data domains. Architect for authorization now, implement it later. When roles and permissions are added, it should be a configuration layer on top of an already-clean architecture, not a retrofit.

| Domain | What it contains | Future access model |
|---|---|---|
| **Product data** | What products are, how they work, labability assessments, orchestration details | Open — anyone can see, including customers in Designer |
| **Program data** | Lab series, outlines, activities, instructions — created in Designer | Scoped — only your own programs |
| **Company intelligence** | Fit scores, badges, buying signals, customer fit data, contacts, ACV estimates | Internal-only — Skillable roles only |

No mixing these domains in the same database tables, API responses, or service calls in ways that would be hard to untangle later. The separation must be architectural, not just a permissions layer.

### RBAC Roles (Tentative)

Every data field, API endpoint, and UX element must be permission-aware from the start. When RBAC is implemented, assigning and revoking access should be straightforward — flipping switches, not retrofitting. This is GP1 (right data to the right people) applied to security.

| Role | Tools | Data access |
|---|---|---|
| **Skillable Admin** | All | Full platform access |
| **Skillable Prospector Admin** | Prospector | Company intelligence, product data, contacts, ACV |
| **Skillable CRM Integration Admin** | HubSpot integration config | Company intelligence sent to HubSpot, field mappings |
| **Skillable Seller (SAD/AE/CSM)** | Inspector (via HubSpot + dossier) | Company intelligence (read), product data, seller briefcase |
| **Skillable Solution Consultant (SE/TSM)** | Inspector (full depth) | Company intelligence (read), product data, full evidence detail |
| **Skillable Designer Admin** | Designer (all programs) | Product data, all Skillable programs |
| **Skillable Instructional Designer** | Designer | Product data, assigned programs |
| **Skillable SME** | Designer | Product data, assigned programs |
| **Customer Designer Admin** | Designer (own programs only) | Product data (open), own programs only. Never company intelligence. |
| **Customer Instructional Designer** | Designer (own programs only) | Product data (open), assigned programs only |
| **Customer SME** | Designer (own programs only) | Product data (open), assigned programs only |

The hard wall between Skillable and Customer roles: customers see product data and their own programs. They never see company intelligence, other customers' programs, or any Prospector/Inspector data. This is enforced architecturally, not just by permission checks.

---

## Estimated Platform Costs

Rough cost estimates per operation. These are approximations based on current API pricing and will be updated with actual measurements once the backend is built and tested against real companies.

| Operation | What it does | AI Calls | Estimated Cost (Sonnet) | Estimated Cost (Opus) |
|---|---|---|---|---|
| **Discovery + Scoring** (Prospector / Caseboard) | Find products, score at caseboard depth | 1 discovery + 1 per product | TBD after build | TBD after build |
| **Full Dossier** (Inspector deep dive) | Deep per-product research + scoring | 1 per product (scoring) + 1 per product (Seller Briefcase) | TBD after build | TBD after build |
| **Prospector Batch** (e.g., 25 companies) | Discovery + scoring for each company | ~25 discovery + scoring calls | TBD after build | TBD after build |

*To be updated with actual token counts and costs once the backend rebuild is complete and validated against real data.*

---

## Cost-Saving Levers

Operational levers to revisit if platform scale creates cost or performance pressure. None of these are active today — they are options to pull when needed, without compromising the architecture.

| Lever | What it would do | When to consider |
|---|---|---|
| **Lighter Prospector research** | Reduce per-company research depth below caseboard level for batch scoring | If Prospector batch sizes regularly exceed 50+ companies and cost or speed becomes a constraint |

---

## Open Decisions

| Item | Status |
|---|---|
| **Product Labability as UX structure** | The model must be right first. Display will follow. |
| **Legacy variable names** | Principle set (GP4) — addressed during code refactor. |
| **Cache versioning** | Principle set (GP5) — implementation TBD. |
| **Product Lookalikes** | Confirmed as core Prospector concept — implementation TBD. |
| **UX interpretation tags** | Concept agreed — tag taxonomy TBD. |
| **Lab Access dimension naming** | Working name — will be refined as requirements are finalized. |
| **Scoring point values** | Dimension weights set. Detailed point values for badges need calibration against real data. |
| **ACV tier dollar boundaries** | High/Medium/Low tiers confirmed — specific dollar thresholds TBD. |

---

## Document Strategy

Two authoritative documents:

| Document | What it owns | Audience |
|---|---|---|
| **Platform-Foundation.md** | Strategic authority — Guiding Principles, Pillars, Dimensions, people, motivation, architecture, ACV model, UX structure | Everyone |
| **Badging-and-Scoring-Reference.md** | Operational detail — specific badge names, color criteria, point values, weights, signals, penalties, thresholds. Also serves as the in-app explainability layer (GP3). | Developers, AI prompts, in-app help |

The Badging and Scoring Reference references the Foundation for structure and vocabulary. It never redefines what the Foundation owns.

The AI scoring prompt is no longer a static document. It is generated at runtime by the Prompt Generation System from the scoring configuration and template. The configuration is populated from the Badging and Scoring Reference. Define once, reference everywhere.

---

## Supporting Documents

| Document | Purpose |
|---|---|
| **roadmap.md** | Consolidated inventory of every item we know we want to do, are doing, have done, or need to decide. For active session work, see `next-session-todo.md`. |
