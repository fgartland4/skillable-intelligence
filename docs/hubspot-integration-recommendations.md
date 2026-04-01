# Skillable Intelligence — HubSpot Integration
## Recommendations for RevOps & Marketing Leadership

---

### Why This Document Exists

Marketing and RevOps have built real infrastructure for identifying, prioritizing, and activating prospects and customers. That work is the foundation this document builds on — not a system we're replacing or second-guessing.

Skillable Intelligence is a purpose-built platform that adds one specific capability those systems structurally cannot provide: deep, product-level analysis of whether a company's products are technically compatible with Skillable's platform and complex enough to justify a lab program. It generates data that is highly actionable for Marketing and Sales — but only if it lands in HubSpot in the right places, in the right form, for the right people.

This document is a recommendation for **what data should flow from Intelligence to HubSpot, where it should live, and what it should enable**. It is not a technical specification. Our intent is to partner closely with RevOps to map these recommendations to existing HubSpot infrastructure, identify gaps, and build a write-back architecture that makes Intelligence's output immediately usable by the teams who need it.

---

## Section 1 — What Skillable Intelligence Is

Skillable Intelligence is a platform of three connected tools — Prospector, Inspector, and Designer — all powered by a shared research and scoring engine.

**Prospector** takes a list of companies and returns a ranked assessment of how well each one fits Skillable's ICP. It also surfaces expansion opportunities within existing customer accounts. Its output feeds HubSpot directly.

**Inspector** performs a deep product-level analysis of a specific company — researching their products, technical architecture, partner ecosystem, and organizational readiness for a lab program. It produces a full report with scoring, delivery path recommendations, consumption potential estimates, and key contacts.

**Designer** takes Inspector's output and generates a draft lab program architecture — lab titles, learning objectives, activity-level content, and environment requirements.

For the purposes of this document, the relevant tools are **Prospector** (primary data source for HubSpot write-back) and **Inspector** (deeper source for Company record enrichment and Deal context).

---

## Section 2 — Why Our Version of Fit Scoring Is Different

Marketing already uses a fit score to prioritize outreach. That score is capturing real and valuable signals — company size, industry category, training organization depth, partner program presence, market reach. These are the right first-order questions for identifying companies that *value* technical training and have the organizational infrastructure to build a program. Intelligence doesn't replace that score — it extends it into territory those signals cannot reach.

### Skillable Is a PaaS — Which Changes Everything About Qualification

Most B2B lead generation is looking for buyers of a product. Skillable's challenge is fundamentally different: **we are looking for builders of lab programs on a platform.**

A SaaS company asks: does this organization have the budget, the pain point, and the authority to buy our product?

Skillable has to ask three harder questions:

1. **Can we technically deliver a lab for what this company sells?** Does their product have the deployment model, API surface, and technical architecture that Skillable can orchestrate?

2. **Is their product complex enough that hands-on labs create genuine value?** A lab program only makes sense for products where practice accelerates skill development — where doing the thing in a realistic environment builds capability that reading about it doesn't. Simple, low-complexity products don't clear this bar.

3. **Does this company have the organizational maturity to actually adopt labs as a core training modality?** Building a lab program requires content teams with the right skills, technical resources to build and maintain environments, and program leadership committed to hands-on learning as a long-term strategy — not a one-time experiment.

All three gates have to clear. A company with a technically compatible product but a transactional training mindset will never build a sustainable program. A company with strong organizational commitment but a product that can't be orchestrated at scale will hit a wall before they start. A product that's technically feasible but too simple to justify a lab will produce one lab and stop.

Standard firmographic fit scoring — even good scoring — cannot evaluate any of these three things. They require deep product research, Skillable-specific technical knowledge, and an honest assessment of organizational readiness. That is what Intelligence is built to do.

### What Intelligence Actually Measures

**Product-level technical compatibility** — whether Skillable can orchestrate this company's products at all, and through which delivery path:

- **Deployment model** — Is the product installable in an isolated environment, or is it pure cloud SaaS with no tenant separation?
- **API surface** — Can Skillable provision and deprovision per-learner environments programmatically? Are there APIs for credential injection, configuration, and validation?
- **Marketplace and container presence** — Is the product available on Azure Marketplace, AWS Marketplace, or as a Docker image? These dramatically reduce build complexity and time to first lab.
- **Technical workflow depth** — Does using the product involve real infrastructure decisions and configuration tasks — or is it primarily a configuration UI?
- **Scoring feasibility** — Can learner actions be validated automatically, enabling Practice-Based Testing?

Each of these signals maps directly to one of Skillable's delivery paths: Azure Cloud Slice, AWS Cloud Slice, Standard VM, Simulation, Custom API. The right path determines build cost, time to first lab, and consumption potential.

**Organizational readiness for a lab program** — whether this company has the DNA to actually build and sustain one:

- Content team structure and skills — do they have the people to author, maintain, and iterate on lab content?
- Technical enablement maturity — is there evidence of existing hands-on training programs, technical certifications, or practice-based assessment?
- Partner and channel program depth — is there an ecosystem of builders who would benefit from and contribute to a lab program?
- Training org investment level — are training and enablement treated as strategic functions or cost centers?

### The Workday Problem

Workday is the clearest illustration of why product-level scoring matters — and why all three gates must be evaluated independently.

On organizational signals, Workday clears the bar easily:

- World-class training organization with a dedicated Workday Learning division and a substantial global partner program
- Deep content ecosystem, strong technical enablement culture, massive install base
- Gate 3 — organizational readiness — passes with distinction

And Gate 2 passes too. Configuring Workday HCM or Financials is genuinely complex. The skills involved are real. Workday's own content teams recognized this — they *wanted* to build labs. The motivation and organizational capability were both present.

Gate 1 is where the analysis ends. Workday is a pure multi-tenant cloud SaaS platform. There is no per-learner environment isolation, no deployment model Skillable can orchestrate, no API surface for provisioning individual lab instances. The platform architecture makes it technically impossible to deliver the labs that Workday's content teams were ready to build.

This is the most important version of the Workday story: it wasn't a bad lead with weak signals. It was motivated, capable people inside a well-run organization who invested significant time before hitting a wall that was always there — because Gate 1 was never evaluated before the pursuit began.

Intelligence surfaces this in the research phase, before the first conversation. The same analysis that flags Workday will surface a mid-market DevOps company with a Docker image, a Marketplace listing, and a clean API — a company that clears all three gates and can have a lab running in weeks.

### The Composite Score

Intelligence's composite score evaluates four dimensions — but they are not equal, and they are not averaged:

- **Technical Orchestrability** — can Skillable deliver a lab for this company's products? This is the primary gate. A low score here limits the composite regardless of everything else.
- **Lab Program Complexity** — is the product technically rich enough that hands-on practice creates genuine skill-building value?
- **Organizational DNA & Readiness** — does this company have the content team skills, technical enablement maturity, and program leadership to build and sustain a lab program?
- **Market & Strategic Fit** — install base, competitive positioning, partner ecosystem depth, strategic alignment with Skillable's growth areas

A company must clear a minimum threshold on Technical Orchestrability for the composite score to be meaningful. Exceptional organizational readiness does not overcome a product that cannot be orchestrated. Conversely, a technically compatible product paired with an immature training org is a slow, high-risk program — and Intelligence flags that too.

**The result is a score that reflects not just whether a company looks like a good prospect, but whether a successful lab program is actually achievable — and what it would take to get there.**

---

## Section 3 — ICP Outbound: How It Works & What Goes to HubSpot

### What It Does

Marketing inputs a list of company names. Intelligence researches each company — discovering their products, analyzing technical architecture, evaluating organizational readiness, and scoring against all three qualification gates — and returns a ranked table with fit scores, verdicts, delivery path recommendations, and key contacts.

The output is designed to answer three questions for every company on the list: *Can we deliver for them? Is the opportunity real? Are they ready to build?*

### Recommended Data for the HubSpot Company Record

The following data should write to the Company record upon analysis completion. We recommend partnering with RevOps to identify which of these map to existing custom properties and which are net-new.

| Data | Purpose |
|---|---|
| **Intelligence Fit Score** | Numeric score (0–100); enables list segmentation and prioritization in HubSpot |
| **Intelligence Verdict** | Labeled classification: Labable / Simulation Candidate / Do Not Pursue; enables filtered views and enrollment triggers |
| **Fit Rationale Summary** | 2–3 sentences written specifically for a seller: why this company scored well or poorly, which product drove the score, what the path looks like. This is synthesized by Intelligence at analysis time — not a data export |
| **Top Product Signal** | The product or product category that most drove the score |
| **Recommended Delivery Path** | Cloud Slice / Standard VM / Simulation / Custom API — the path Intelligence recommends based on product analysis |
| **Key Risk Flag** | If present: the single most important constraint a seller needs to know (e.g., "Pure SaaS — limited orchestrability") |
| **Date of Last Analysis** | Enables freshness filtering; analysis may be up to 45 days old |
| **Link to Full Intelligence Report** | One-click access to complete scoring breakdown, evidence, and solutioning guidance |

### Recommended Data for Contact Records

Intelligence surfaces up to two contacts per company for ABM targeting:

| Contact | Role | Data |
|---|---|---|
| **Primary Contact** | Decision maker — VP/Director of Training, Partner Enablement, or equivalent | Name, title, LinkedIn URL |
| **Secondary Contact** | Day-to-day champion — program manager, technical lead, or enablement manager | Name, title, LinkedIn URL |

Contacts are extracted from public sources during research. They should be treated as a starting point for verification — people change roles frequently and should be confirmed before outreach.

### How Marketing Activates from Here

Once data writes to HubSpot:
- **List segmentation**: filter by Verdict, Fit Score threshold, Delivery Path, or Key Risk Flag
- **Sequence enrollment**: trigger enrollment based on Verdict = "Labable" or Score ≥ threshold
- **ABM targeting**: use both contacts for multi-threaded outreach campaigns
- **AE assignment**: routed per existing HubSpot ownership rules — Intelligence does not assign

---

## Section 4 — Customer Expansion: How It Works & What Goes to HubSpot

### What It Does

For existing customer accounts, Intelligence maps the department landscape — identifying which departments have active lab programs, which could adopt labs already built by a colleague department, and which represent untapped greenfield opportunity.

The output answers: *Where is there more to sell within this account, and what kind of conversation does each opportunity require?*

### The Three Expansion Signal Types

All three are expansion opportunities. All three result in Deals. The signal type shapes the conversation.

**Use — Zero Build Cost Expansion**
A department that could adopt labs already built by another department within the same account. The content investment is done. The path to value is faster. The conversation is about adoption and utilization, not program design.

**Build — Greenfield Opportunity**
A department with a labable product and no existing lab program. Requires content development investment. The full Inspector and Designer motion applies — qualification, scoping, consumption estimate, program architecture.

**Existing Buyer Expanding**
A department already using Skillable that is ready to go further — a different product line, a new delivery path, a new audience, or additional lab types. They have already validated Skillable's value; the conversation is about what's next.

### The Buying Group Map

Intelligence's Expansion analysis produces a department-level map for each account: which departments exist, what products they work with, their lab status, and who the relevant contact is. This map is the foundation for the Buying Group Summary in HubSpot — enriching it with structured, Intelligence-derived data so AEs and CSMs have a clear picture of the account before any conversation.

### Recommended Data for the HubSpot Company Record

| Data | Purpose |
|---|---|
| **Expansion Signal Summary** | Brief narrative: how many departments analyzed, how many Use vs. Build vs. Expanding opportunities identified |
| **Buying Group Summary Enrichment** | Department nodes: department name, product, lab status, opportunity type, contact name + title |
| **Date of Last Expansion Analysis** | Freshness tracking |
| **Link to Full Expansion Report** | Complete department-by-department breakdown in Intelligence |

### Recommended Data for Deals

All identified expansion opportunities should result in either a new Deal or an update to an existing Deal. We recommend partnering with RevOps on the deduplication rule — what constitutes a match to an existing Deal — to avoid duplicate records.

**For each opportunity, the Deal should carry:**

| Data | Purpose |
|---|---|
| **Opportunity Type** | Use / Build / Existing Buyer Expanding — tells the AE immediately what conversation they're walking into |
| **Department** | The specific department or business unit this opportunity is for |
| **Product** | The product or product line driving the opportunity |
| **Delivery Path** | Recommended path for this specific product/department combination |
| **Opportunity Rationale** | 2–3 sentences: why Intelligence flagged this, what already exists, what the expansion looks like |
| **Key Contact** | Name, title, LinkedIn — the department-level contact Intelligence identified |
| **Cross-Reference** | If Use opportunity: which department built the labs that could be adopted |
| **Link to Intelligence Report** | Full context one click away |

**On Deal creation vs. appending:** Intelligence should check for an existing Deal before creating a new one. If a Deal already exists for the same Company + Department combination, the data above should append to that Deal as context — not create a duplicate. RevOps should define the matching criteria.

### Account Ownership and Routing

Intelligence does not assign Deals to individuals. All Deals write to the Company record; HubSpot's existing ownership rules and workflows handle routing to the Account Owner (SAD/AE). Where a CSM is assigned to the account, they should receive visibility into expansion signals — as the relationship owner, they are typically the first to validate an opportunity and bring it to the AE.

**Intelligence's role is to surface the signal. The commercial team decides how to act on it.**

### How Marketing Uses Expansion Data

As Marketing develops its expansion motion, Intelligence's department-level data enables account-based campaign targeting at scale:

- Segment by opportunity type across the customer base (e.g., all accounts with identified Build opportunities in a specific product category)
- Target department-level contacts from the Buying Group Summary with adoption or program-launch content
- Identify patterns across the customer base that inform ICP refinement (e.g., which department types consistently have untapped opportunities)

---

## Section 5 — Recommended Integration Model by Tool

The following describes our recommended integration model for how each Intelligence tool connects to HubSpot. This is a starting point for alignment with RevOps and Marketing — not a finalized architecture. The right touchpoints, trigger mechanisms, and data flows should be validated against the existing HubSpot setup before any build begins.

The three Intelligence tools have distinct integration models. Understanding the difference matters for RevOps configuration and for setting expectations with each user audience.

### Prospector ↔ HubSpot (Bidirectional — Marketing-driven)

Marketing triggers Prospector from inside HubSpot — selecting a list of ZoomInfo companies or defining ICP criteria and sending them to Prospector for analysis. Prospector runs the batch and writes enriched data sets back to HubSpot Company records, Contact records, and Deals as described in Sections 3 and 4.

**HubSpot is Prospector's primary output destination.** The Intelligence UI serves as the run interface and pre-commit review screen — Marketing confirms what will be written before the data lands in HubSpot. After that, all work happens in HubSpot using existing workflows, sequences, and pipeline views.

This integration requires the most RevOps configuration: trigger mechanism, field mapping, write-back rules, deduplication logic.

### HubSpot → Inspector (One-way trigger — Seller and SE-driven)

Company and Deal records in HubSpot surface a link: "Run Inspector." Clicking it opens Inspector in a new browser window at the Stage 1 Company Report — a broad scan that surfaces all company products, ranked by fit, with competitive pairings and company-level signals.

From there, the seller or SE selects 3–4 products for a deep dive (Stage 2), getting the full technical analysis, delivery path recommendation, scoring approach, and consumption potential estimate. The full Inspector experience runs in Intelligence — HubSpot is only the trigger.

Executives and SEs who are already regular Inspector users may go directly to Intelligence without using the HubSpot link. Both paths are valid.

This integration is lower-complexity on the RevOps side: a HubSpot Company/Deal property with the Inspector URL populated at the right time, or a workflow action that opens the link.

### Designer → HubSpot (Read-only visibility — no trigger from HubSpot)

Program owners, instructional designers, and SMEs go directly to Designer. HubSpot plays no role in triggering or driving Designer's workflow.

The integration runs the other direction: Designer-created Lab Programs should be visible in HubSpot as read-only links and summary data on the Company record. This gives sellers and CSMs visibility into what programs have been designed, what's in progress, and what has been delivered for their accounts — without needing to access Designer directly.

This surfaces high-value context for renewal and expansion conversations: "You have three completed lab programs for this product family and two more in design" is exactly what an AE needs before a QBR.

---

## Section 7 — What We Need From RevOps

To build this write-back architecture correctly, we need RevOps's expertise on the existing HubSpot setup. Specifically:

1. **Existing custom Company properties** — Which of the recommended Company record fields above already exist as custom properties? We want to write to existing infrastructure wherever possible and identify true gaps.

2. **Deal template review** — Walk through the standard expansion Deal template and identify where each recommended data element fits in the existing UX. Are there existing fields that map cleanly, or are new fields needed?

3. **Deduplication rules** — Define the matching criteria for "does an expansion Deal already exist for this Company + Department?" so Intelligence can append vs. create correctly.

4. **Buying Group Summary structure** — Understand the current state of Buying Group Summaries across the customer base (largely empty vs. partially populated) so we know what Intelligence would be adding vs. replacing.

5. **Pipeline confirmation** — Confirm that all three expansion signal types (Use, Build, Existing Buyer Expanding) belong in the same expansion pipeline, and that the Deal data above provides sufficient context to differentiate them within that pipeline.

6. **Ownership and notification rules** — Confirm how Deals created by Intelligence should trigger notifications or tasks for AEs and CSMs via existing HubSpot workflows.

---

## Section 8 — Open Questions

The following require input from RevOps and/or Marketing leadership before the write-back architecture can be finalized:

- Does a Use opportunity (adopt existing labs, typically CSM-facilitated) warrant immediate Deal creation, or should it start as a task or activity that converts to a Deal when it progresses?
- Should Intelligence read existing Deals before running Expansion analysis — so it does not surface opportunities already in active pipeline?
- What is the threshold for creating a Contact record vs. simply writing contact data to a Deal or Company note? (Avoiding duplicate Contact proliferation)
- How should Intelligence handle Contracted Expansion accounts where step-up growth is already locked in? Should those departments be excluded from Expansion analysis to avoid noise?
- Is there an existing HubSpot "Source" or "Lead Source" property that Intelligence-generated records should write to, for attribution tracking?
