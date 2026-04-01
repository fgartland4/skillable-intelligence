# Skillable Intelligence Platform
## Briefing for Skillable Executive Leadership

---

## Three Problems Worth Solving

Skillable is a platform company. Not a software product — an orchestration platform that enables software companies to deliver hands-on learning experiences at scale. That distinction is more than positioning. It is the root cause of three hard problems that no standard sales or marketing tool was ever designed to solve.

- **Marketing:** Identifying companies in our ICP
- **Revenue:** Proving labability and lab impact
- **ProServ & Product:** Enabling bought-in customers to adopt labs

Each problem is structural — a natural consequence of the sophistication of what we do, not a gap in any team's execution. And each one requires a different kind of intelligence than any existing tool provides.

### The Platform Difference

Most B2B software companies sell a product that runs in their cloud. Their buyers interact with it through a browser. The product is the same for every customer. Qualifying a prospect means finding buyers who fit the profile: the right size, the right industry, the right pain point, the right budget.

Skillable is different. We do not deliver our own software. We orchestrate *other companies' software* into hands-on lab environments — real products, real interfaces, real consequence of error, accessible to a learner anywhere. What we sell is the infrastructure that makes that possible.

This creates a fundamentally different go-to-market challenge. The buyer profile question — does this company value training? — is necessary but not sufficient. The deeper question is whether their products can be orchestrated into a Skillable environment at all. Whether those products are technically complex enough that hands-on practice creates real value. Whether the company can build and sustain a lab program once they are a customer.

These questions cannot be answered with firmographic data. They require a different kind of analysis entirely. That is what Intelligence provides.

### Marketing Challenge: Identifying Companies in Our ICP

Platform companies cannot qualify prospects the way product companies do. The tools Marketing uses — ZoomInfo, 6sense, HubSpot, LinkedIn Sales Navigator — are built to identify buyers who match a profile. For Skillable, that is the wrong question. The right question is whether a company's products can be delivered as hands-on lab experiences. That is a technical assessment, not a firmographic one.

We evaluate every prospect across three dimensions:

**Can we deliver a lab for this company's products?** This is the primary filter. If the answer is no, nothing else matters — not the size of their training organization, not the depth of their content team, not their enthusiasm for hands-on learning. A company whose products cannot be orchestrated into a Skillable environment is not a prospect.

**Is the product technically complex enough for labs to create real value?** Simple products with shallow workflows do not benefit enough from hands-on practice to justify the investment. Products with deep administrative workflows, meaningful configuration decisions, and real consequence of error — those are where labs change what learners can actually do.

**Does the organization have what it takes to build and sustain a program?** Content team skills, technical enablement maturity, program leadership. Some companies have it today. Others have the organizational DNA to build it. Either can become a strong customer. Companies with neither are high-risk programs regardless of product fit.

The Workday pattern illustrates what happens when this analysis does not happen early. On every traditional marketing signal, Workday is an ideal prospect: world-class training organization, dedicated learning division, deep technical enablement culture, massive install base. Two of the three dimensions are strong. The third ends the conversation.

Workday's architecture is pure multi-tenant — every customer shares the same cloud environment. There is no Workday instance to give a learner. There is no provisioning API to spin one up. There is nothing to install, containerize, or slice. Skillable cannot deliver a lab for Workday's products. That fact is findable in public documentation before a single sales conversation begins.

Workday was not a bad lead. It was motivated, capable people who invested significant time before hitting a wall that was always there. The Workday pattern repeats whenever product-level technical fit is evaluated late — or not at all.

The same logic runs in the other direction. When Fortinet is a strong fit, it is not because Fortinet resembles other good customers as a company. It is because Fortinet's products have specific technical characteristics — multi-VM topology, deep administrative workflows, strong API surface, real consequence of misconfiguration — that make them ideal for hands-on labs. Every company selling products with those same characteristics is a strong fit for the same reasons. The competitive map of a strong-fit customer is a pre-qualified prospect list.

### Revenue Challenge: Proving Labability and Lab Impact

Proving that a Skillable lab program will work for a specific customer's products requires deep technical analysis. Which delivery path is right for this product — standard virtual machine, cloud environment slice, containerized workload, custom integration? What are the architectural constraints? What would a realistic program look like in terms of scope, seat time, and scoring approach? What is the estimated consumption potential?

This is exactly the kind of work a skilled Solutions Engineer does well. It requires knowing Skillable's platform deeply — delivery paths, technical constraints, feature availability, scoring feasibility — and applying that knowledge to a specific product's architecture and deployment model. That synthesis takes hours per company, in a live conversation, with access to documentation and a customer contact who can fill in the gaps.

The result is that qualification depth is rationed. It flows to deals already far enough along to justify the time. Early-stage prospects get a general conversation. The technical questions that would surface a Workday pattern early — before marketing dollars are spent, before SE time is committed — often go unasked until it is too late.

### ProServ & Product Challenge: Enabling Bought-In Customers to Adopt Labs

A signed contract is not an adopted customer. The gap between "we want to build labs" and "we have a running program" is wide, and most customers cannot cross it without structured guidance.

Program design is a specialized skill. Most buyers — even technically sophisticated ones with strong content teams — have never designed a hands-on lab curriculum. They have built documentation, recorded videos, written certification exams. They have not mapped a product's administrative workflows to a sequence of learner activities, defined scoring logic for hands-on tasks, or produced a structured brief that a lab developer can build against without extensive back-and-forth.

Without a process that takes them from goals and audience to a complete, buildable program architecture, customers stall at the design phase. In a consumption model, a stalled customer is not just a missed upsell opportunity — it is a churn risk. A customer who has not built a program has not realized value. A customer who has not realized value does not renew.

---

## Three Tools. One Platform.

Each tool in Skillable Intelligence addresses one of the three challenges directly. All three share the same research and scoring engine — which means every analysis makes the entire platform smarter. A company Prospector evaluates is available to Inspector without re-running research. An Inspector analysis seeds Designer with the product context it needs from day one. The intelligence compounds with every use.

### Designer — Closing the Adoption Gap

Designer takes an Inspector analysis and guides program owners, instructional designers, and subject matter experts through the full process of designing a lab program. From goals and audience definition through a complete approved outline, activity-level content, and a Skillable Studio-ready export package.

The process is structured. It does not require the customer to know how to design a lab program — that is the point. Designer asks the right questions, sequences the decisions correctly, and generates a complete program architecture that a contracted lab developer can build against immediately.

The output is not just a plan. Designer generates a complete Bill of Materials from everything it knows about the program and the product: environment templates, PowerShell and Bash scripts, Bicep and CloudFormation templates, lifecycle action scripts, credential pool configuration, scoring validation stubs. What previously required hours of Solutions Engineering and lab developer work is produced in the same session where the program was designed.

**What it unlocks:** Every new customer engagement starts with Designer in the first week — before the technical environment is ready. Program design and environment build run as parallel workstreams. Day one is productive for the program owner. The adoption gap closes before it has a chance to form.

### Inspector — Proving Labability and Impact

Inspector performs a deep product-level analysis of a specific company. It runs in two stages.

**Stage 1 — Company Report:** A broad scan that surfaces all of a company's products, ranked by labability, with competitive pairings, company-level signals, and an overall fit score. The foundation document for any seller or SE entering a conversation with this account.

**Stage 2 — Deep Dive:** The seller or SE selects three to four products from Stage 1 for exhaustive analysis — full technical orchestrability evidence, delivery path recommendation with rationale, scoring approach, consumption potential estimate, and program scope.

A seller walking into a conversation with a Stage 2 Inspector report knows what the customer's products can and cannot do on the Skillable platform, which delivery path makes sense and why, and what the estimated consumption potential is. That is not a discovery conversation. It is a solution conversation.

Inspector also surfaces the competitive map for every analyzed company — which feeds directly into Prospector's lookalike targeting.

**What it unlocks:** Pre-call preparation that was previously impossible at scale is now standard. Every seller and SE enters every conversation with the technical depth that used to require hours of individual research — applied automatically, to every product, before the first meeting.

### Prospector — Finding the Right Companies

Prospector is the go-to-market tool for Marketing and RevOps. It takes a list of companies and returns a ranked assessment of ICP fit — with product-level evidence, composite scores, verdicts, delivery path signals, and key contacts for every company on the list.

Marketing has never had access to product-level qualification data at the point of list building. Prospector makes it possible to screen a ZoomInfo export of 500 companies for technical orchestrability, product complexity, and organizational readiness before a sequence is written, a dollar is spent, or an SDR makes a call. Companies that clear all three dimensions go into outreach. Workday patterns come off the list — with specific, documented technical reasons on the Company record.

Prospector also surfaces customer expansion opportunities — mapping the department landscape of existing accounts to identify adoption opportunities for existing labs, greenfield departments, and buyers ready to expand.

**What it unlocks:** The list that goes into outreach is the right list. Every company on it has been evaluated on the question that actually determines Skillable fit — not on firmographic proxies that have nothing to do with whether their products can be orchestrated into a lab.

---

## HubSpot and Revenue Operations

*This section is written for RevOps and Marketing leadership. Executive readers who do not own HubSpot infrastructure may stop here.*

### The Integration Principle

HubSpot is the seller and marketer's workspace. Intelligence is the specialist workspace. The integration surfaces the right intelligence in the right place — without requiring sellers to live in another tool or RevOps to build a parallel system.

### Prospector ↔ HubSpot — Bidirectional, Marketing-Driven

Marketing triggers Prospector from inside HubSpot — selecting a ZoomInfo list or defining criteria and sending them to Prospector for analysis. Prospector writes enriched data back to HubSpot Company records, Contact records, and Deals. HubSpot is Prospector's primary output destination.

**Data written to the Company record:**

| Data | Purpose |
|---|---|
| Intelligence Fit Score | Numeric score (0–100); enables list segmentation and prioritization |
| Intelligence Verdict | Labable / Simulation Candidate / Do Not Pursue; enables filtered views and enrollment triggers |
| Fit Rationale Summary | 2–3 sentences: why this company scored well or poorly, which product drove the score, what the path looks like |
| Top Product Signal | The product or product category that most drove the score |
| Recommended Delivery Path | Cloud Slice / Standard VM / Simulation / Custom API |
| Key Risk Flag | The single most important constraint a seller needs to know |
| Date of Last Analysis | Enables freshness filtering |
| Link to Full Intelligence Report | One-click access to complete scoring and evidence |

Intelligence surfaces up to two contacts per company — a decision maker and a day-to-day champion — extracted from public sources for ABM targeting.

### Inspector → HubSpot — Seller and SE-Driven

Company and Deal records in HubSpot surface a "Run Inspector" link. Clicking it opens Inspector at the Stage 1 Company Report. The full Inspector experience runs in Intelligence — HubSpot is only the trigger.

**Stage 1 data → Company Record:**

| Data | Purpose |
|---|---|
| Product list with labability scores | What this company sells and how labable each product is |
| Top delivery path signal per product | Quick read on delivery approach per product |
| Overall company fit score | Single number for segmentation and prioritization |
| Key risk flag | The most important constraint a seller needs to know |
| Date of last analysis + link to full report | Freshness tracking and one-click access |

**Stage 2 data → Deal Record:**

| Data | Purpose |
|---|---|
| Delivery path recommendation + rationale | What path, and why |
| Scoring approach recommendation | How learner actions will be validated |
| Consumption potential / ACV estimate | Deal-level revenue context |
| Technical orchestrability evidence | Compressed analysis for the SE |
| Program scope estimate | Labs, seat time, curriculum depth |
| Link to full Inspector Stage 2 report | Full context one click away |

### Designer → HubSpot — Read-Only Visibility

Program owners and IDs go directly to Designer. HubSpot plays no role in triggering Designer's workflow.

Designer-created Lab Programs surface in HubSpot as read-only links and summary data on the Company record — giving sellers and CSMs visibility into what programs have been designed, what is in progress, and what has been delivered. Critical context for renewal and expansion conversations before a QBR.

---

## Recommendations and Open Decisions

### What We Are Recommending

1. **Prospector as the primary Marketing data source for ICP outbound.** Replace or supplement the current ZoomInfo-only scoring motion with Intelligence-qualified lists. Companies that fail the technical orchestrability assessment come off the list before sequences are built. Companies that clear all three dimensions get prioritized outreach with seller-ready context already in HubSpot.

2. **Inspector Stage 1 as the standard pre-call research tool for all sellers and SEs.** The "Run Inspector" link on every Company and Deal record makes it a one-click motion. Stage 1 output gives every seller account intelligence they currently do not have before the first conversation.

3. **Designer as a standard deliverable in every new customer engagement.** Skillable LC and PS should run every new customer through Designer in the first week — before the technical environment is ready. Program design and environment build run as parallel workstreams.

### Decisions Required from RevOps and Marketing

| Decision | Context |
|---|---|
| Existing custom Company properties | Which recommended fields already exist vs. net-new? |
| Deal template review | Where does each data element fit in the existing deal UX? |
| Deduplication rules | What constitutes a match to an existing Deal for expansion opportunities? |
| Stage 2 multi-product question | Three products in one Inspector run — three Deals or one? |
| Buying Group Summary structure | Current state across the customer base? |
| Ownership and notification rules | How should Intelligence-generated Deals trigger notifications for AEs and CSMs? |
| ZoomInfo CSV column mapping | Minimum: Company Name + Domain. High value: Industry, LinkedIn URL, Employee Count, Technologies Used. |
| Score threshold for auto-create/update | At what fit score does a Company record get automatically enriched vs. queued for review? |
