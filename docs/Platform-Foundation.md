# Skillable Intelligence Platform — Foundation

This is the authoritative source for the strategic foundation of the Skillable Intelligence Platform. All code, UX, documentation, and communication should align to what is defined here. Where conflicts exist with other documents, this document wins.

This document reflects best current thinking. As thinking evolves, this document evolves with it — fully synthesized, never appended. Best current thinking, always.

---

## Guiding Principles

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

### GP4: Self-Evident Design

The platform's intent, logic, and structure must be evident at every layer — from variable names to UX output. Anyone inspecting any layer should understand why it exists, what it does, and how it connects to the whole.

| Layer | What self-evidence looks like |
|---|---|
| **Variable and field names** | Named after the concepts they represent — `customer_motivation`, `delivery_capacity`, `orchestration_method` — not generic labels |
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

### The End-to-End Principle

The framework shapes how we **gather**, how we **store**, how we **judge**, and how we **present**. One model, end to end. The same Pillar/Dimension/Requirement structure runs through every layer — research, storage, scoring, display. No translation step. No reorganizing after the fact.

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

Product Labability determines product-market fit. It asks one fundamental question: **can Skillable deliver a complete lab lifecycle for this product?** The answer is measured across four dimensions: Orchestration Method, Lab Access, Scoring, and Teardown (detailed in Pillar 1 of the Scoring Framework).

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
| **HubSpot card** | Fit confirmation, key badges, "worth pursuing" confidence, ACV signal | Marketing, Sellers, CSMs |
| **Inspector Caseboard** | All products for a company — scores, badges at a glance, Fit Score + ACV Potential | SEs, TSMs (or anyone who clicked deeper) |
| **Dossier top sections** | Overall assessment, key findings, organizational context | Anyone exploring a company |
| **Product cards (Dossier)** | Technical detail — labability dimensions, features, orchestration specifics | SEs, TSMs digging into a specific product |
| **Designer** | Lab series, lab breakdown, activities, scoring, instructions, bill of materials | Program Owners, IDs, SMEs, Tech Writers, ProServ |

Nobody is forced to see more than they need. Nobody is locked out of going deeper. The design is intentional about where each persona *should* start — but the platform doesn't gatekeep.

---

## Scoring Framework

### Hierarchy

The scoring framework follows a clear hierarchy:

- **Fit Score** — the composite, made up of four Pillars
  - **Pillars** — the four weighted components of the Fit Score
    - **Dimensions** — the specific areas measured within each Pillar
      - **Requirements** — the most granular level; what the AI researches and evaluates. These surface as badges in the UX.

### Badge System

Badges are variable-driven visual indicators that surface requirements in the UX. Each badge has a name and a color.

**Four badge colors:**

| Color | Meaning | When to use |
|---|---|---|
| **Green** | Strength / Opportunity | This is good — go forward |
| **Gray** | Neutral / Context | Worth knowing, not good or bad — just information |
| **Amber** | Risk / Caution | Dig deeper — there's something to figure out |
| **Red** | Blocker | This is a problem that must be solved |

**Evidence confidence language:**

Confidence is communicated through language in the evidence text, not through additional visual indicators. Three levels:

| Level | Phrasing | What it means |
|---|---|---|
| **Confirmed** | "REST API **confirmed** — OpenAPI spec at docs.trellix.com" | Direct evidence from a primary source |
| **Indicated** | "VM deployment **indicated** — installation guide references Windows Server" | Strong indirect evidence, multiple signals |
| **Inferred** | "Troubleshooting lab potential **inferred** from category norms" | AI-informed assumption based on patterns or limited signals |

For high-risk areas (contacts, consumption estimates), rationale must be explicit: "Estimated based on..." or "Contact identified from LinkedIn search results — may be out of date."

The badge color and the evidence language work together. The badge tells you the assessment. The evidence tells you the basis for that assessment. Together they give the reader everything they need to decide how much weight to put on a finding.

**Badge naming principles:**

- When the recommendation is clear, the badge should name the **solution**, not the problem — show the answer, not the question (e.g., "NFR Accounts Available" rather than "Account Creation")
- When the finding is a spectrum, a single badge name with variable color works (e.g., "Learner Isolation" — green, amber, or red)
- Some badges are variable-driven: the badge text itself changes based on what's found (e.g., the specific LMS name, the specific competitor platform)
- If something is green and unremarkable, it doesn't need to surface at all — only show what matters
- All four colors should be available for most badges — let the AI assess based on research

**Evidence bullet standard:** Clear, concise, and complete. Every bullet must be all three. No filler. No vague language. Specific details, specific sources, specific reasoning. The AI assesses the finding, recommends the solution, judges its own confidence, and shows its work.

### Two Hero Metrics

The platform presents two primary metrics that together tell the full story:

| Metric | What it answers | How it's determined |
|---|---|---|
| **Fit Score** | Should we pursue this? How strong is the opportunity? | Composite of four Pillars |
| **ACV Potential** | How big is this if we win? | Calculated from consumption motions: population x adoption x hours x rate |

These are the two hero elements in the UX — visible at the top of every dossier and caseboard entry. They are separate outputs, not one composite. The Fit Score is a qualitative assessment. ACV Potential is a calculated business metric. Together they drive prioritization:

| Fit Score | ACV Potential | What it means |
|---|---|---|
| **High** | **High** | Best opportunity — strong fit, big prize. Prioritize aggressively. |
| **High** | **Low** | Great fit but small opportunity. Worth pursuing, don't over-invest. |
| **Medium** | **High** | Gaps exist but massive potential. Worth solving the gaps. |
| **Medium** | **Low** | Moderate fit, small opportunity. Lower priority. |
| **Low** | **High** | Can't deliver today, but opportunity is huge. Watch list. |
| **Low** | **Low** | Not a fit, not worth it. Move on. |

### Four Pillars

The Fit Score is a composite of four Pillars — two product-level, two organization-level:

| Pillar | Weight | Level | UX Question |
|---|---|---|---|
| **Product Labability** | 40% | Product | How labable is this product? |
| **Product Demand** | 25% | Product | Does this product need hands-on training? |
| **Customer Motivation** | 20% | Organization | Why would they invest in hands-on training? |
| **Organizational Readiness** | 15% | Organization | Can they build and deliver labs? |

---

### Pillar 1: Product Labability (40%)
*How labable is this product?*

The gatekeeper. If this fails, nothing else matters. Measures whether Skillable can deliver a complete lab lifecycle for this product.

**Orchestration Method determines difficulty for everything else.** When a product runs in Skillable's infrastructure (VM, container, Cloud Slice), the other dimensions are largely within Skillable's control. When a product runs in the vendor's own cloud, every dimension depends on the vendor's APIs and policies — significantly more risk.

| Dimension | Question | Key badges |
|---|---|---|
| **Orchestration Method** | How do we get this product into Skillable? | Azure Cloud Slice, AWS Cloud Slice, Hyper-V, Container, Custom API / BYOC, Simulation |
| **Lab Access** | Can we get people in with their own identity, reliably, at scale? | Variable badges that name the solution (NFR Accounts Available, Account Recycling, Credential Pool, etc.), Learner Isolation, Anti-Automation Controls |
| **Scoring** | Can we assess what they did, and how granularly? | API Scorable, Script Scorable, Simulation Scorable, AI Vision Scorable, MCQ Scorable |
| **Teardown** | Can we clean it up when it's over? | Teardown APIs, Orphan Risk. For VM/container labs, teardown is automatic — badges only surface when there's a finding. |

---

### Pillar 2: Product Demand (25%)
*Does this product need hands-on training?*

The commercial case. Measures whether this product genuinely warrants hands-on lab experiences.

| Dimension | Question | Key badges |
|---|---|---|
| **Product Complexity** | Is this product hard enough to require hands-on practice? | Product Breadth & Depth, Workflow Complexity, Configuration Complexity, Hands-On AI Features, Not Lab Appropriate (disqualifier) |
| **Mastery Stakes** | How much does competence matter? | High-Stakes Skills, Adoption & TTV Risks, Certification Program |
| **Lab Versatility** | What kinds of hands-on experiences can we build? | Collaborative Lab Opportunity, Break/Fix Opportunity, Simulated Attack Opportunity |
| **Market Demand** | Does the broader market validate the need? | Growth Trajectory, Geographic Reach, Annual Users, Key Customers |

**Market Demand includes strong category-level priors.** Certain product categories inherently carry high market demand:

- **Highest demand:** Cybersecurity, Cloud Infrastructure, Networking/SDN, Data Science & Engineering, Data & Analytics, DevOps
- **Moderate demand:** Data Protection, Infrastructure/Virtualization, App Development, ERP/CRM, Healthcare IT, FinTech, Collaboration, Content Management, Legal Tech, Industrial/OT
- **Low demand:** Simple SaaS, Consumer

**AI as a market demand signal has two distinct forms:**

| Signal | What it means | Example |
|---|---|---|
| **Learning AI-embedded features** | The product has AI features users need to learn — hands-on practice with AI-powered capabilities | Learning Trellix's GenAI-powered threat investigation |
| **Creating AI** | The product IS an AI platform — labs teach people to build, train, deploy AI models | Building models in SageMaker or Azure ML |

Both are strong demand signals. Learning AI features is about using a tool. Creating AI is about building the tool.

---

### Pillar 3: Customer Motivation (20%)
*Why would they invest in hands-on training?*

Why the organization would invest. Scored based on the presence and strength of three motivations. Multiple motivations present = stronger score. Motivation also serves as a **framing variable** that shapes how all recommendations and rationale are communicated — it's not just a number, it's a conversation shaper.

**Key distinction from Pillar 2:** Product Demand measures the **product** (is it complex? are the stakes high?). Customer Motivation measures the **organization's response** (have they invested because of that complexity and those stakes?). The badges in Pillar 3 are observable evidence of organizational commitment, not product-level signals.

| Dimension | Question | Key badges (evidence of commitment) |
|---|---|---|
| **Product Adoption** | Are they investing to drive usage, reduce churn, accelerate time-to-value? | Customer Enablement, Customer Success, Channel Enablement |
| **Skill Development** | Are they investing to build competence, certify people, advance careers? | Certification Program, Training Catalog, ATP / Learning Partner Program |
| **Compliance & Risk** | Are they investing because the cost of incompetence is unacceptable? | Regulated Industry, Compliance Training Program, Audit Requirements |

The underlying business problems — adoption & TTV risk, churn & retention risk, regulatory exposure — are the **rationale** that explains why these programs exist. They surface in the evidence detail when someone drills deeper, not as badges themselves.

---

### Pillar 4: Organizational Readiness (15%)
*Can they build and deliver labs?*

Whether the organization can execute. Weighted lower because Skillable Professional Services or partners can fill the build gap. Two dimensions, with delivery weighted higher.

**Delivery Capacity** (higher weight) — can they get labs to learners at scale?

| Badge | What it tells us |
|---|---|
| **ATP / Learning Partner Program** | Scaled delivery through partners — broad reach |
| **{LMS Platform Name}** (variable) | Delivery infrastructure confirmed — badge shows the specific platform (Docebo, Cornerstone, Moodle, etc.). Skillable partners (Docebo, Cornerstone) are green. |
| **ILT / vILT Offerings** | Instructor-led delivery channel established |
| **On-Demand Catalog** | Self-paced delivery — scales without instructors |
| **Certification Delivery** | Proctored exam infrastructure — high-stakes delivery channel |
| **Events & Conferences** | Direct delivery channel — labs at events |
| **Customer Onboarding Infrastructure** | Structured path to deliver labs to new customers |

**Lab Platform Detection** — a special signal within Delivery Capacity. Confirms they already have lab delivery infrastructure and identifies migration or expansion opportunities:

| Badge | Color | What it tells us |
|---|---|---|
| **Skillable** | Green | Existing customer — expansion opportunity |
| **{Competitor Name}** (variable) | Amber | Competitor in use — migration opportunity (Instruqt, CloudShare, Kyndryl/Skytap, GoDeploy, Vocareum, Appsembler, ReadyTech, Immersive Labs, Hack The Box, TryHackMe, ACI Learning) |
| **DIY Labs** | Amber | Home-built — they've invested in labs but likely hitting limitations |

**Build Capacity** (lower weight) — can they create the labs?

| Badge | What it tells us |
|---|---|
| **Content Dev Team** | They have the people — Lab Authors, IDs, Tech Writers |
| **Existing Labs** | They've built hands-on experiences before |
| **Content Outsourcing** | They use third parties — ProServ opportunity for Skillable |

When Build Capacity is low but Delivery Capacity is strong, the platform surfaces: **Professional Services Opportunity** — they need help building but they'll deliver at scale.

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

## Data Architecture: Three Domains

The codebase must cleanly separate three data domains. Architect for authorization now, implement it later. When roles and permissions are added, it should be a configuration layer on top of an already-clean architecture, not a retrofit.

| Domain | What it contains | Future access model |
|---|---|---|
| **Product data** | What products are, how they work, labability assessments, orchestration details | Open — anyone can see, including customers in Designer |
| **Program data** | Lab series, outlines, activities, instructions — created in Designer | Scoped — only your own programs |
| **Company intelligence** | Fit scores, badges, buying signals, organizational readiness, contacts, ACV estimates | Internal-only — Skillable roles only |

No mixing these domains in the same database tables, API responses, or service calls in ways that would be hard to untangle later. The separation must be architectural, not just a permissions layer.

---

## Open Decisions

Items not yet fully resolved. These will be addressed as the foundation matures.

| Item | Status |
|---|---|
| **Motivation and Org Readiness relationship** | Keep separate, present together. Revisit during rubric development. |
| **Product Labability as UX structure** | The model must be right first. Display will follow. |
| **Legacy variable names** | Principle set (GP4) — addressed during code refactor. |
| **Cache versioning** | Principle set (GP5) — implementation TBD. |
| **Product Lookalikes** | Confirmed as core Prospector concept — implementation TBD. |
| **UX interpretation tags** | Concept agreed — tag taxonomy TBD. |
| **Lab Access dimension naming** | Working name — will be refined as requirements are finalized. |

---

## Document Strategy

Two authoritative documents, not four:

| Document | What it owns | Audience |
|---|---|---|
| **Platform-Foundation.md** | Strategic authority — Guiding Principles, Pillars, Dimensions, people, motivation, architecture, ACV model | Everyone |
| **Badging-and-Scoring-Reference.md** | Operational detail — specific badge names, color criteria, point values, weights, signals, penalties, thresholds | Developers, AI prompts |

The Badging and Scoring Reference references the Foundation for structure and vocabulary. It never redefines what the Foundation owns. The AI scoring prompt (product_scoring.txt) will be generated fresh from these two documents.

Define once, reference everywhere.
