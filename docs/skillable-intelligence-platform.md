# Skillable Intelligence Platform
## Briefing for Skillable Executive Leadership

---

## WHY — The Problem No Other Tool Solves

### We Are a Platform, Not a Product

Most B2B companies sell a product. Their go-to-market challenge is identifying organizations that have the budget, the pain point, and the authority to buy. Firmographic signals — company size, industry, growth stage, technology stack — are meaningful proxies. A company that fits the profile is a prospect.

Skillable sells a platform. That changes the qualification question entirely.

We are not asking whether a company values training. We are asking whether a company's products can be orchestrated into hands-on labs — whether Skillable can technically deliver for them, whether their products are complex enough that labs create genuine skill-building value, and whether their organization has the maturity to build and sustain a lab program.

These are not questions about the company. They are questions about the product. And they cannot be answered with firmographic data.

This is the gap Intelligence fills. Every other tool in our stack — ZoomInfo, 6sense, HubSpot, LinkedIn Sales Navigator — evaluates companies. **Intelligence evaluates products.** It is the only platform in our stack capable of answering the question that actually determines whether a prospect can become a Skillable customer.

### The Three Gates

Intelligence evaluates every company and product against three qualification gates. All three must clear for a prospect to be genuinely purseable.

**Gate 1 — Technical Orchestrability**
Can Skillable deliver a lab for this company's products? This is the primary gate. If the answer is no, the composite score is limited regardless of everything else. Gate 1 failure means the company is not a Skillable prospect — period — regardless of how strong their training organization is or how much they value hands-on learning.

**Gate 2 — Product Complexity**
Is the product technically rich enough that hands-on labs create genuine skill-building value? Simple products with shallow workflows don't benefit enough from labs to justify the investment. Complexity drives the value of practice. High Gate 2 scores mean learners get dramatically better at something that matters — and they can prove it.

**Gate 3 — Organizational Readiness**
Does the company have the content team skills, technical enablement maturity, and program leadership to build and sustain a lab program? Gate 3 uses a two-question model: does the organization have this capability today, and do they have the organizational DNA to build it if absent? A company can clear Gate 3 on potential alone — if the signals suggest they're building toward it.

A company must clear all three gates for a successful lab program to be achievable. Exceptional organizational readiness does not overcome a product that cannot be orchestrated. Strong Gate 1 compatibility paired with an immature training organization is a slow, high-risk program. Intelligence flags both — and surfaces what it would take to get there.

### The Workday Pattern — Knowing When to Stop Before We Start

**The goal of Intelligence is to surface the specific technical reasons a company cannot be a Skillable customer — before we spend a single dollar marketing to them.**

Workday is the clearest illustration of why this matters.

On every traditional marketing signal, Workday looks like an ideal prospect. World-class training organization. Dedicated learning division. Deep content ecosystem. Strong technical enablement culture. Massive install base. Gate 3 passes with distinction — their organizational capability to build a lab program is unquestioned.

Gate 2 passes too. Configuring Workday HCM or Financials is genuinely complex. The skills involved are real. Workday's own content teams recognized this — they wanted to build labs.

Gate 1 is where the analysis ends. The specific technical reasons are articulable and discoverable from public documentation:

- **Pure multi-tenant architecture** — every Workday customer shares the same cloud environment. There is no "Workday instance" to give a learner. The product is architecturally incapable of per-learner isolation.
- **No provisioning API** — no mechanism to spin up an individual environment programmatically. Skillable's entire delivery model depends on this capability.
- **No deployment model** — nothing to install, nothing to containerize, nothing to slice. The product lives entirely in Workday's cloud and cannot be replicated outside it.

These are not hunches or soft signals. They are specific, technical facts — findable in Workday's architecture documentation before a single sales conversation begins.

The most important version of this story: Workday wasn't a bad lead. It was motivated, capable people inside a well-run organization who invested significant time before hitting a wall that was always there — because Gate 1 was never evaluated before the pursuit began.

**Products that work like Workday are not a fit — and Intelligence surfaces that before any marketing motion begins.** The Workday pattern generalizes: any product with pure multi-tenant architecture, no provisioning API, and no deployment model fails Gate 1. Intelligence identifies this pattern from research signals automatically. The HubSpot verdict is "Do Not Pursue" — with the specific technical reasons documented on the Company record so any seller or marketer who asks gets a clear, defensible answer.

### Lookalike Is Causation, Not Correlation

Standard lookalike analysis finds companies that resemble existing customers — same size, same industry, same growth profile. That is firmographic correlation. It is useful, and it has limits.

For Skillable, lookalike analysis works differently — and more powerfully.

When Fortinet is a strong fit, it is not because Fortinet resembles other good customers as a company. It is because Fortinet's products have specific technical characteristics — multi-VM topology, deep admin workflows, real consequence of error, strong API surface — that make them labable. Those characteristics are determined by what Fortinet *sells*, not by how large they are or what industry they're in.

**Every company selling products with those same technical characteristics is labable for the same reasons.** The fit is not approximate. It transfers directly.

This means Skillable's most powerful prospecting signal is product category — not firmographics:

- A company selling network security products will almost always clear Gates 1 and 2 — for the same reasons Fortinet, Palo Alto, and Cisco do.
- A company selling SIEM, EDR, or identity management will almost always clear Gates 1 and 2 — for the same reasons CrowdStrike, Splunk, and SentinelOne do.
- A company selling data pipeline or ML infrastructure will almost always clear Gates 1 and 2 — for the same reasons Databricks, dbt Labs, and Snowflake do.

**The competitive map is the lookalike list.** Every time Intelligence analyzes a strong-fit customer, it surfaces that company's direct competitors. Those competitors sell products in the same category, with the same technical profile. They are pre-qualified lookalike candidates — identified automatically, without additional research.

**We are not looking for companies that look like our customers. We are looking for companies whose products behave like our customers' products.** That is a fundamentally more defensible, more precise, and more scalable approach to ICP targeting.

### AI Moments — Capability Unlocks, Not Efficiency Gains

Intelligence uses AI to do things that were not previously possible — not faster versions of existing work, but work that simply did not happen before because the human cost made it impractical.

**Evaluating product-level technical compatibility at scale.** Assessing whether a company's products have the deployment model, API surface, marketplace presence, and technical architecture that Skillable can orchestrate is work that takes an experienced SE hours per company. Intelligence does it in minutes, across a list of hundreds — researching marketplace listings, API documentation, GitHub repositories, Docker images, and partner ecosystem signals automatically. The AI moment: every company on a ZoomInfo list gets a real technical evaluation, not just a firmographic score.

**Applying Skillable's platform knowledge to every product it touches.** Skillable has deep, specific knowledge about how its platform works — delivery paths, technical blockers, feature availability, Gate 1 disqualifiers, scoring feasibility signals. That knowledge lives in documentation, in SE expertise built over years of customer engagements. A human SE applies it to one company at a time, in a live conversation. Intelligence applies that entire body of Skillable-specific knowledge to every product it researches, automatically — matching the specific technical characteristics of a product against the specific capabilities and constraints of the Skillable platform, and producing a judgment that reflects reality rather than optimism. The AI moment: Intelligence knows Skillable as well as your best SE, and applies that knowledge to every company it touches — not just the ones that make it into a conversation.

**Surfacing the Workday pattern before the pursuit begins.** Identifying that a product has no provisioning API, no deployment model, and pure multi-tenant architecture — from public documentation, before any human conversation — is not a filter. It is a research and reasoning task. The AI moment: the technical reasons a company cannot be a Skillable customer are documented before the first marketing dollar is spent.

**Lookalike by product behavior, not firmographic resemblance.** Finding companies whose products behave like known strong-fit customers requires understanding what makes a product technically orchestrable and applying that understanding across the internet. The AI moment: the competitive map of every analyzed customer becomes an automatically updated list of pre-qualified lookalike candidates.

---

## WHAT — The Intelligence Platform

### Three Tools, One Intelligence Layer

Skillable Intelligence is a platform of three connected tools — Prospector, Inspector, and Designer — all powered by a shared research and scoring engine. The intelligence layer accumulates, stores, and maintains company and product knowledge. Each tool contextualizes that intelligence for a specific person doing a specific job.

**Improving the intelligence layer improves all three tools simultaneously.** Every research improvement makes Prospector rankings more accurate, Inspector analyses more complete, and Designer recommendations more specific — at the same time. Every new Gate signal improves qualification across the entire platform. Every company analyzed by Prospector is available to Inspector without re-running research. This is the compounding effect: the platform gets smarter with every analysis, and every tool benefits.

### Prospector — ICP Outbound at Scale

Prospector is the go-to-market tool for Marketing and RevOps. It takes a list of companies and returns a ranked assessment of how well each one fits Skillable's ICP — with product-level evidence, composite scores, verdicts, delivery path signals, and key contacts for every company on the list.

**What it unlocks:** Marketing has never had access to product-level qualification data at the point of list building. Prospector makes it possible to screen a ZoomInfo export of 500 companies for Gate 1/2/3 compatibility before a sequence is written, a dollar is spent, or an SDR makes a call. The companies that clear all three gates go into outreach. The Workday patterns come off the list — with documented reasons.

Prospector also surfaces **customer expansion opportunities** — mapping the department landscape of existing accounts to identify which departments have active lab programs, which could adopt labs already built elsewhere in the organization, and which represent untapped greenfield opportunity.

### Inspector — Deep Analysis for Sellers and SEs

Inspector performs a deep product-level analysis of a specific company. It runs in two stages.

**Stage 1 — Company Report:** A broad scan that surfaces all of the company's products, ranked by labability, with competitive pairings, company-level signals, and an overall fit score. This is the foundation document for any seller or SE entering a conversation with this account. It is also the output of Prospector's Customer Expansion pass — the same research, stored once per company, shared across both tools.

**Stage 2 — Deep Dive:** The seller or SE selects three to four products from Stage 1 for exhaustive analysis — full Gate 1/2/3 evidence, delivery path recommendation with rationale, scoring approach recommendation, consumption potential estimate, and program scope. This is the document that goes into a deal conversation.

**What it unlocks:** A seller walking into a conversation with a Stage 2 Inspector report knows what the customer's products can and cannot do on the Skillable platform, which delivery path makes sense and why, what a lab program would realistically look like, and what the estimated consumption potential is. That is not a discovery conversation — it is a solution conversation. The AI moment: a level of pre-call preparation that was previously impossible at scale is now standard.

### Designer — From Analysis to Program

Designer takes Inspector's output and guides program owners, instructional designers, and subject matter experts through the full process of designing a lab program — from goals and audience through a complete approved outline, draft instructions, and a Skillable Studio-ready export package.

**What it unlocks:** Customers who don't know how to design a lab program won't build one. And if they don't build one, they don't adopt Skillable. Designer breaks that pattern. It is the adoption engine — the tool that gives a new customer something concrete to do on day one, before the technical environment is ready, and produces a complete program architecture that a contracted lab developer can build against immediately.

The AI moment: Designer generates a complete Bill of Materials — PowerShell scripts, Bicep templates, CloudFormation templates, lifecycle action scripts, credential pool configuration, scoring validation stubs — from everything it knows about the program. Hours of SE and lab developer work, generated in the same session where the program was designed.

---

## HOW — Integration with HubSpot and Revenue Operations

*This section is written for RevOps and Marketing leadership. Executive readers who do not own HubSpot infrastructure may stop here.*

---

### The Integration Principle

HubSpot is the seller and marketer's workspace. Intelligence is the specialist workspace. The integration surfaces the right intelligence in the right place — without requiring sellers to live in another tool or RevOps to build a parallel system.

The three Intelligence tools have distinct integration models. Understanding the difference matters for RevOps configuration and for setting expectations with each user audience.

### Prospector ↔ HubSpot — Bidirectional, Marketing-Driven

Marketing triggers Prospector from inside HubSpot — selecting a ZoomInfo list or defining ICP criteria and sending them to Prospector for analysis. Prospector runs the batch and writes enriched data back to HubSpot Company records, Contact records, and Deals.

**HubSpot is Prospector's primary output destination.** The Intelligence UI serves as the run interface and pre-commit review screen. After that, all work happens in HubSpot.

**Data written to the Company record:**

| Data | Purpose |
|---|---|
| Intelligence Fit Score | Numeric score (0–100); enables list segmentation and prioritization |
| Intelligence Verdict | Labable / Simulation Candidate / Do Not Pursue; enables filtered views and enrollment triggers |
| Fit Rationale Summary | 2–3 sentences for a seller: why this company scored well or poorly, which product drove the score, what the path looks like |
| Top Product Signal | The product or product category that most drove the score |
| Recommended Delivery Path | Cloud Slice / Standard VM / Simulation / Custom API |
| Key Risk Flag | The single most important constraint a seller needs to know |
| Date of Last Analysis | Enables freshness filtering |
| Link to Full Intelligence Report | One-click access to complete scoring and evidence |

**Data written to Contact records:**
Intelligence surfaces up to two contacts per company — a decision maker (VP/Director of Training, Partner Enablement, or equivalent) and a day-to-day champion (program manager, technical lead, or enablement manager). Contacts are extracted from public sources and should be verified before outreach.

### HubSpot → Inspector — One-Way Trigger, Seller and SE-Driven

Company and Deal records in HubSpot surface a "Run Inspector" link. Clicking it opens Inspector in a new browser window at the Stage 1 Company Report. The full Inspector experience runs in Intelligence — HubSpot is only the trigger.

**Data written back to HubSpot from Inspector:**

*Stage 1 → Company Record (persistent account intelligence — relevant to every seller and CSM on the account):*

| Data | Purpose |
|---|---|
| Product list with labability scores | Account-level intelligence on what this company sells and how labable each product is |
| Top delivery path signal per product | Quick read on how each product would be delivered |
| Overall company fit score | Single number for segmentation and prioritization |
| Key risk flag | The most important constraint a seller needs to know |
| Date of last analysis + link to full report | Freshness tracking and one-click access |

*Stage 2 → Deal Record (opportunity-specific — tied to a specific product, audience, and scope):*

| Data | Purpose |
|---|---|
| Delivery path recommendation + rationale | What path, and why — the SE's talking point |
| Scoring approach recommendation | How learner actions will be validated |
| Consumption potential / ACV estimate | Deal-level revenue context |
| Gate scores summary | Compressed evidence for the SE |
| Program scope estimate | Labs, seat time, curriculum depth |
| Link to full Inspector Stage 2 report | Full context one click away |

### Designer → HubSpot — Read-Only Visibility

Program owners, instructional designers, and SMEs go directly to Designer. HubSpot plays no role in triggering or driving Designer's workflow.

Designer-created Lab Programs surface in HubSpot as read-only links and summary data on the Company record — giving sellers and CSMs visibility into what programs have been designed, what's in progress, and what has been delivered. This surfaces high-value context for renewal and expansion conversations before a QBR or renewal call.

---

## Recommendations and Open Decisions

### What We Are Recommending

1. **Prospector as the primary Marketing data source for ICP outbound.** Replace or supplement the current ZoomInfo-only scoring motion with Intelligence-qualified lists. Companies that fail Gate 1 come off the list before sequences are built. Companies that clear all three gates get prioritized outreach with seller-ready context already in HubSpot.

2. **Inspector Stage 1 as the standard pre-call research tool for all sellers and SEs.** The "Run Inspector" link on every Company and Deal record makes it a one-click motion. Stage 1 output on the Company record gives every seller account intelligence they currently don't have.

3. **Designer as a standard deliverable in every new customer engagement.** Skillable LC and PS should run every new customer through Designer in the first week — before the technical environment is ready. Program design and environment build are parallel workstreams. Designer makes day one productive for the program owner.

### Decisions Required from RevOps and Marketing

The following require RevOps and Marketing input before the HubSpot integration can be built:

1. **Existing custom Company properties** — which recommended fields already exist as custom properties vs. net-new?
2. **Deal template review** — where does each recommended data element fit in the existing deal UX?
3. **Deduplication rules** — what constitutes a match to an existing Deal for expansion opportunities?
4. **Stage 2 multi-product question** — if a single Inspector run covers three products, do they generate three separate Deals or does all Stage 2 data append to one Deal?
5. **Buying Group Summary structure** — current state of Buying Group Summaries across the customer base?
6. **Ownership and notification rules** — how should Intelligence-generated Deals trigger notifications for AEs and CSMs?
7. **ZoomInfo CSV column mapping** — which columns are in Marketing's standard export and how do they map to Prospector's input requirements? Minimum viable: Company Name + Domain. High value: Industry, LinkedIn URL, Employee Count, Technologies Used.
8. **Score threshold for auto-create/update** — at what Intelligence Fit Score does a Company record automatically get enriched vs. queued for review?
