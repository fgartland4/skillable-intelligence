# Skillable Intelligence Platform
## Executive Leadership Team Brief

---

## Three problems worth solving

We recently agreed that Skillable is PaaS and not SaaS. Does this distinction simply change some positioning or does it signal our opportunity to shatter a few glass ceilings? As the category creator for hands-on experience platforms, we find ourselves staring at three unique challenges.

- Identifying companies in our ICP
- Proving labability and lab impact
- Enabling bought-in customers to adopt labs

### The PaaS Difference

Most B2B software companies sell products that run in a cloud, in a datacenter, on a computer, or on a phone. With a few customizations here and there, many of these products are roughly the same for every user. Qualifying a prospect means finding buyers who fit the profile: the right size, the right industry, the right pain point, the right budget.

Skillable is different. We do not deliver our own software. We orchestrate *other companies' software* into hands-on lab environments — real products, real interfaces, real consequence of error, accessible to a learner anywhere. What we sell is the platform that makes so many different things possible at scale.

This creates a fundamentally different go-to-market challenge. The buyer profile question (does this company value training?) is necessary but not sufficient. The deeper question is whether their products can be orchestrated into a Skillable environment at all. Whether those products are complex enough that hands-on practice creates real value. Whether the company can build and sustain a lab program once they are a customer.

These questions cannot be answered with the exhaustive-but-typical data provided by leading Marketing account intelligence software. They require a different kind of analysis entirely. That is what Intelligence provides.

---

## Three challenges. Three tools. One platform.

Each tool addresses one of the three challenges directly. All three share the same research and scoring engine — which means every analysis makes the entire platform smarter. A company Prospector evaluates is available to Inspector without re-running research. An Inspector analysis seeds Designer with the product context it needs from day one. The intelligence compounds with every use.

### Designer: Closing the adoption gap

A signed contract is not an adopted customer. The gap between "we want labs" and "we're building and delivering labs embedded in a variety of learning journeys" is wide. And it's crystal clear that most customers are not, and cannot, make the leap without significant and structured support.

Program design is a specialized skill. Embedding a new modality like hands-on experiences into your overall content strategy and content development operation is not a decision. It's a new discipline. They've built documentation, recorded videos, written certification exams. They have not mapped a product's administrative workflows to a sequence of learner activities, defined scoring logic for hands-on tasks, or produced a structured brief that a lab developer can build against without extensive back-and-forth.

Without a process that takes them from goals and audience to a complete, buildable program architecture, customers stall at the design phase. In a consumption model, a stalled customer is not just a missed upsell opportunity; it is a churn risk. A customer who has not built a program has not realized value. A customer who has not realized value does not renew.

Designer closes that gap.

Designer guides program owners, instructional designers, and subject matter experts through the full process — from learning objectives and intended audience through every decision a program requires. It doesn't require the customer to know how to design a lab program. Designer asks the right questions and sequences the decisions correctly. Every program produces:

- A structured program outline
- Draft lab instructions for every lab in the program
- Learner activities for progress tracking
- Scoring methodology recommendations

**Designer generates a complete Bill of Materials** from everything it knows about the program and the product: environment templates, PowerShell and Bash scripts, Bicep and CloudFormation templates, lifecycle action scripts, credential pool configuration, scoring validation stubs. What previously required hours of Solutions Engineering and lab developer work is produced in the same session where the program was designed.

**What it unlocks:** Every new customer engagement starts with Designer in the first week — while the technical folks are working to get the technical details sorted. Program design and environment build run in parallel. Day one is productive for the program owner. The adoption gap closes before it has a chance to form.

### Inspector: Proving labability and impact

Proving that a Skillable lab program will work for a specific customer's products requires deep technical analysis. Which is the best delivery path for each software environment? A set of virtual machines or containers, leveraging Azure or AWS subscriptions, a custom API orchestration, or a hybrid setup? What are the architectural constraints? What would a realistic program look like in terms of scope, seat time, and scoring approach? What is the estimated consumption potential?

This is the type of work that's required for virtually every new lab program with every new and existing customer and demands substantial commitment from our Solution Engineers and TSMs. It takes hours of conversation, researching API documents, and plain old trial and error.

The result is that qualification depth is rationed. It flows to deals already far enough along to justify the time. Early-stage prospects get a general conversation. The technical questions that would surface a Workday pattern early (before marketing dollars are spent, before SE time is committed) often go unasked until it is too late.

Inspector proves labability and impact.

Inspector performs a deep product-level analysis of a specific company. It runs in two stages.

- **The Case Board.** A broad scan that surfaces all of a company's products, ranked by labability, with competitive pairings, company-level signals, and an overall fit score. You walk in the room and get the picture at a glance.
- **The Dossier.** The seller or SE selects three to four products from the Case Board for exhaustive analysis — full technical orchestrability evidence, delivery path recommendation with rationale, scoring approach, consumption potential estimate, and program scope.

**Inspector turns every sales conversation into a solution conversation.** A seller walking into a meeting with a Dossier knows what the customer's products can and cannot do on the Skillable platform, which delivery path makes sense and why, and what the estimated consumption potential is. That is not discovery. That is a standing start.

Inspector also surfaces the competitive map for every analyzed company, which feeds directly into Prospector's lookalike targeting.

**What it unlocks:** Pre-call preparation that was previously impossible at scale is now standard. Every seller and SE enters every conversation with the technical depth that used to require hours of individual research, applied automatically to every product before the first meeting.

### Prospector: Finding the right companies

Platform companies cannot qualify prospects the way product companies do. The tools Marketing uses (ZoomInfo, 6sense, HubSpot, LinkedIn Sales Navigator) are built to identify buyers who match a profile. For Skillable, that is the wrong question. The right question is whether a company's products can be delivered as hands-on lab experiences. That is a technical assessment, not a firmographic one.

We evaluate every prospect across three dimensions:

- **Can we deliver a lab for this company's products?** This is the primary filter. If the answer is no, nothing else matters — not the size of their training organization, not the depth of their content team, not their enthusiasm for hands-on learning. A company whose products cannot be orchestrated into a Skillable environment is not a prospect.
- **Is the product complex enough for labs to create real value?** Simple products with shallow workflows don't benefit enough from hands-on practice to justify the investment. Products with deep administrative workflows, meaningful configuration decisions, and real consequence of error — those are where labs change what learners can actually do.
- **Does the organization have what it takes to build and sustain a program?** Content team skills, technical enablement maturity, program leadership. Some companies have it today. Others have the organizational DNA to build it. Either can become a strong customer. Companies with neither are high-risk regardless of product fit.

The Workday pattern illustrates what happens when this analysis doesn't happen early. On every traditional marketing signal, Workday is an ideal prospect: world-class training organization, dedicated learning division, deep technical enablement culture, massive install base. Two of the three dimensions are strong. The third ends the conversation.

- **Pure multi-tenant architecture:** Every customer shares the same cloud environment. There is no Workday instance to give a learner.
- **No provisioning API:** No mechanism to spin up an individual environment programmatically. Skillable's entire delivery model depends on this capability.
- **No deployment model:** Nothing to install, containerize, or slice.

These are specific technical facts findable in public documentation before a single sales conversation begins. Workday wasn't a bad lead. It was motivated, capable people who invested significant time before hitting a wall that was always there — because product-level technical fit was never evaluated before the pursuit began.

The same logic runs in the other direction. When Fortinet is a strong fit, it's not because Fortinet resembles other good customers as a company. It's because Fortinet's products have specific technical characteristics — multi-VM topology, deep administrative workflows, strong API surface, real consequence of misconfiguration — that make them ideal for hands-on labs. Every company selling products with those same characteristics is a strong fit for the same reasons. The competitive map of a strong-fit customer is a pre-qualified prospect list.

Prospector finds the right companies.

Prospector is the go-to-market tool for Marketing and RevOps. It takes a list of companies and returns a ranked assessment of ICP fit — with product-level evidence, composite scores, verdicts, delivery path signals, and key contacts for every company on the list.

**Prospector qualifies every company on product-level fit** before a sequence is written, a dollar is spent, or an SDR makes a call. Companies that clear all three dimensions go into outreach. Workday patterns come off the list — with specific, documented technical reasons on the Company record. Prospector also surfaces customer expansion opportunities, mapping the department landscape of existing accounts to identify adoption opportunities for existing labs, greenfield departments, and buyers ready to expand.

**What it unlocks:** The list that goes into outreach is the right list. Every company on it has been evaluated on the question that actually determines Skillable fit — not on firmographic proxies that have nothing to do with whether their products can be orchestrated into a lab.

Fit scores, product signals, delivery path recommendations, key contacts — all of it needs to reach the right people at the right moment. That is what the HubSpot integration is built to do.

---

## Surfacing the data. Right place. Right time. Right context.

The balance of this document outlines the decisions for RevOps to make with Marketing and Security. It includes more context, several recommendations, and a list of decisions to be made. If you're not in one of those groups, feel free to stop reading if you so choose.

### The Integration Principle

HubSpot is the seller and marketer's workspace. Intelligence is the specialist workspace. The integration surfaces the right intelligence, to the right people, in the right places, with the right context — without requiring sellers to live in another tool or RevOps to build a parallel system.

### Prospector ↔ HubSpot: Bidirectional, marketing-driven

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

### Inspector → HubSpot: Seller and SE-driven

Company and Deal records in HubSpot surface a "Run Inspector" link. Clicking it opens Inspector at the Case Board. The full Inspector experience runs in Intelligence — HubSpot is only the trigger.

**Case Board data → Company record:**

| Data | Purpose |
|---|---|
| Product list with labability scores | What this company sells and how labable each product is |
| Top delivery path signal per product | Quick read on delivery approach per product |
| Overall company fit score | Single number for segmentation and prioritization |
| Key risk flag | The most important constraint a seller needs to know |
| Date of last analysis + link to full report | Freshness tracking and one-click access |

**Dossier data → Deal record:**

| Data | Purpose |
|---|---|
| Delivery path recommendation + rationale | What path, and why |
| Scoring approach recommendation | How learner actions will be validated |
| Consumption potential / ACV estimate | Deal-level revenue context |
| Technical orchestrability evidence | Compressed analysis for the SE |
| Program scope estimate | Labs, seat time, curriculum depth |
| Link to full Inspector Dossier | Full context one click away |

### Designer → HubSpot: Read-only visibility

Program owners and IDs go directly to Designer. HubSpot plays no role in triggering Designer's workflow.

Designer-created Lab Programs surface in HubSpot as read-only links and summary data on the Company record — giving sellers and CSMs visibility into what programs have been designed, what is in progress, and what has been delivered. Critical context for renewal and expansion conversations before a QBR.

---

## Recommendations & open decisions

### What we are recommending

1. **Prospector as the primary Marketing data source for ICP outbound.** Replace or supplement the current ZoomInfo-only scoring motion with Intelligence-qualified lists. Companies that fail the technical orchestrability assessment come off the list before sequences are built. Companies that clear all three dimensions get prioritized outreach with seller-ready context already in HubSpot.

2. **The Inspector Case Board as the standard pre-call research tool for all sellers and SEs.** The "Run Inspector" link on every Company and Deal record makes it a one-click motion. The Case Board gives every seller account intelligence they currently don't have before the first conversation.

3. **Designer as a standard deliverable in every new customer engagement.** Skillable LC and PS should run every new customer through Designer in the first week — before the technical environment is ready. Program design and environment build run as parallel workstreams.

### Decisions required from RevOps and Marketing

| Decision | Context |
|---|---|
| Existing custom Company properties | Which recommended fields already exist vs. net-new? |
| Deal template review | Where does each data element fit in the existing deal UX? |
| Deduplication rules | What constitutes a match to an existing Deal for expansion opportunities? |
| Dossier multi-product question | Three products in one Inspector run — three Deals or one? |
| Buying Group Summary structure | Current state across the customer base? |
| Ownership and notification rules | How should Intelligence-generated Deals trigger notifications for AEs and CSMs? |
| ZoomInfo CSV column mapping | Minimum: Company Name + Domain. High value: Industry, LinkedIn URL, Employee Count, Technologies Used. |
| Score threshold for auto-create/update | At what fit score does a Company record get automatically enriched vs. queued for review? |
