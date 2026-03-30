# Skillable Intelligence — Inspector

> Inspector takes a single company name and produces a fully scored, evidence-backed assessment of which products could become Skillable lab programs — and what it would actually take to build them.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md). For guidance on how to interpret findings, confidence levels, and where hallucination risk is highest, see [Before You Read the Scores](intelligence-platform.md#before-you-read-the-scores).

---

## Why Inspector Exists

Before a discovery call, a Solution Engineer typically spends one to three hours doing pre-call research. They're reading product documentation, scanning training portals, checking Azure Marketplace listings, poking around Docker Hub, and generally trying to answer one question: *is this company actually a good candidate for a lab program?* That research lives in a browser history and a few bullet points in a notes app. When the next SE picks up the same account six months later, or when the AE wants to qualify the logo before asking for SE time at all, the process starts from zero.

The problem isn't just the wasted hours. It's the inconsistency. Manual research is only as good as the person doing it and the time they had. One SE knows to check for a Docker image as a fast proxy for deployment automability. Another doesn't. One knows that MFA on the API is a soft constraint that caps the Skillable path at A2. Another calls it a blocker. These judgment calls compound across the team and produce analysis that doesn't travel well — from SE to AE, from this quarter to next quarter, from one territory to another.

Inspector automates the same research a strong SE would do, but with consistency, depth, and speed that manual research can't match. It runs 12 parallel web searches during discovery, fetches and reads company pages, and passes all of that evidence through calibrated scoring prompts anchored against real Skillable customer deployments. The output is a structured `CompanyAnalysis`: a composite score, per-product labability scores broken down by dimension, a recommended Skillable delivery path, a consumption potential model, evidence claims with source URLs, and a prioritized list of contacts. Because results are cached for 45 days, the next person who opens the same company sees the full analysis instantly rather than triggering another research pass.

Inspector is also the starting point for the Designer tool. When scoring completes, a "Design Lab Program →" button appears in the results dashboard. Clicking it carries the `analysis_id`, company name, product scores, and recommended contacts directly into Designer Phase 1. The two tools are designed to flow sequentially: Inspector answers *whether* a lab program is worth building. Designer answers *how* to build it.

---

## Who Uses Inspector

**Solution Engineers** are Inspector's primary users, and the tool was built around their workflow. Before a discovery call or pilot proposal, an SE opens Inspector, enters the company name, selects the products most likely to become lab programs, and runs a full scoring pass. What they need from the output is specific and technical: per-product scores broken down by dimension, the Skillable Path determination (A1, A2, B, or C), the Essential Technical Resource flag that identifies the single highest-priority open question before a pilot can start, and consumption estimates they can use to anchor a business case. Inspector replaces the hours of pre-call research an SE would otherwise do manually and surfaces the technical proof points — API surface, provisioning model, Marketplace presence, competitive lab signals — in a format that maps directly to Skillable's delivery architecture. Typical trigger: an AE brings in a new logo and the SE needs to get up to speed before the first technical conversation.

**Account Executives** use Inspector to qualify a logo before committing SE time to it. The signals they need are high-level: composite score, the pursuit recommendation, and the names of the decision makers most likely to own a training or enablement initiative. They are not reading the evidence section or interpreting dimension breakdowns — they want to know whether this account is worth a deeper investment and who to call. Typical trigger: an SDR passes a warm account, or the AE is preparing for a QBR and needs to identify expansion logos in their territory.

**Technical Sales Managers and Customer Success Managers** use Inspector on existing accounts, looking for expansion opportunities. They want to know which products haven't been incorporated into a lab program yet, what the Lab Maturity signals look like, and who the relevant contacts are for an expansion conversation. Inspector's Lab Maturity Score is particularly useful here — it surfaces organizational readiness signals like training org structure, partner program depth, and LMS usage that indicate whether a customer has the infrastructure to absorb an expanded program. Typical trigger: renewal prep, QBR preparation, or an active expansion motion where the CSM needs to identify the next program to propose.

---

## What Inspector Delivers

At the end of a full Inspector run, you have a `CompanyAnalysis` that contains everything an SE needs to walk into a discovery call prepared. For each scored product: a 0–100 labability score with dimension-level breakdowns, a Skillable Path determination (A1/A2/B/C), evidence claims sourced to specific URLs and organized by the lab lifecycle (Provision → Configure → Score → Teardown), and a set of recommendations that includes the single most important open technical question blocking a pilot. At the company level: an org type classification, a Lab Maturity score that gauges organizational readiness independently of any specific product, a Consumption Potential table projecting lab volume across six business motions, and a contact list with role types and inferred ownership of a lab program conversation.

That output serves two conversations simultaneously. The SE gets the technical depth they need to run an informed discovery call. The AE gets the composite score and pursuit recommendation they need to decide whether to invest.

---

## How Inspector Works

Inspector executes in four sequential phases, and understanding the flow explains why the tool produces what it produces.

**Discovery** is the phase where Inspector figures out what the company makes. The user enters a company name — optionally with specific products they already know about — and the Research Engine immediately fires 12 parallel web searches across six query categories: product portfolio, training and certification catalog, authorized training partner signals, customer success and onboarding motion, organizational and contact signals, and targeted queries for any named products. While searches run, the company homepage and up to five additional high-value pages are fetched and read in parallel. Inspector-specific discovery queries include searches for Marketplace listings (Azure, AWS, Google Cloud), Docker Hub and container availability, NFR and developer license programs, AI and Copilot feature announcements, and hands-on labs offered by competitive platforms (CloudShare, Instruqt, Appsembler). From all of this, Claude produces a structured discovery output: organization type (one of six values), a product list with labability tiers assigned to each product, deployment models, candidate Skillable paths, a company description, and partnership signals. If a 45-day discovery cache entry exists for the company, all of this Phase 1 research is skipped entirely.

**Product Selection** is where the user decides where to invest the full scoring pass. Discovery tiers products as `highly_likely`, `likely`, `less_likely`, or `not_likely` based on lightweight signals — deployment model, product category, Marketplace presence. These are directionally accurate estimates, not final judgments. The selection interface surfaces them transparently so the user can make an informed choice about which three products to score. Deep research and scoring per product involves meaningful API call volume and token cost; running the full pipeline on every product a company makes would be slow and expensive for candidates that discovery has already flagged as poor fits.

**Deep Research and Scoring** is where the real work happens. For each selected product, the Research Engine runs 9 additional web searches and fetches up to 3 high-value pages, targeting specific evidence categories: deployment architecture, training catalog, REST API / CLI / PowerShell surface, AI features, Marketplace listings, Docker images, NFR license programs, system requirements, and competitive lab offerings. Once research completes for all selected products, every scoring call runs fully in parallel — one call per product for the four labability dimensions, one for Lab Maturity, one for Consumption Potential, one for Contacts, and one for Recommendations. Each individual call has a 5-minute timeout; the full scoring pass has a 10-minute total timeout enforced via the SSE stream. Progress is streamed in real time through six descriptive steps so the user has a clear signal of what's happening rather than watching a spinner.

**Results** is when the full analysis renders. The dashboard surfaces everything — scores, evidence, paths, consumption table, contacts, recommendations — in a format designed to support both a technical discovery conversation and an executive qualification conversation. A "Design Lab Program →" button appears at the top when scoring is complete, ready to carry the analysis into Designer.

---

## The Research Layer

**Why:** Before a single dimension can be scored, Inspector needs to know what the company makes, how it deploys, and what kind of training ecosystem surrounds its products. The Research Layer is what produces that raw material — systematically, in parallel, and with enough depth to support evidence-backed scoring rather than inference from product category alone.

**What:** Structured web research across two phases — a company-level discovery pass that maps the product landscape and assigns labability tiers, followed by a product-level deep research pass that generates the specific evidence needed for scoring. All research is cached to avoid redundant work on repeat analyses.

**How:** Discovery fires first, producing a product list with labability tiers. The user selects up to three products. Product-level research runs on those selections, generating the evidence corpus that flows directly into the parallel scoring calls.

---

### Discovery Engine

**Why it exists:** Running full per-product research on every product a company makes before the user has indicated which products matter is expensive and slow. Discovery solves this by producing a low-cost preliminary map — enough to tier the products, orient the user, and target the deeper research pass.

**What it does:** Produces a structured company-level output: organization type (one of six values: `software_company`, `academic_institution`, `training_organization`, `systems_integrator`, `technology_distributor`, `professional_services`), a complete product list with a labability tier per product (`highly_likely`, `likely`, `less_likely`, `not_likely`), deployment model signals, candidate Skillable paths, a company description, and partnership signals. This classification is not cosmetic — the org type drives the composite score formula and the Lab Maturity rubric adjustments used in Phase 3.

**How it works:** 12 parallel web searches fire across six query categories: product portfolio, training and certification catalog, authorized training partner signals, customer success and onboarding motion, organizational and contact signals, and targeted queries for any named products the user supplied. Simultaneously, the company homepage and up to five additional high-value pages are fetched and read in parallel. Inspector-specific discovery queries target the signals that most directly proxy for technical orchestrability before committing to per-product research: Azure/AWS/Google Cloud Marketplace listings, Docker Hub and container image availability, NFR or developer license programs, AI and Copilot feature announcements, and competitive lab platform presence (CloudShare, Instruqt, Appsembler). A product on the Azure Marketplace or with a public Docker image has almost certainly cleared the bare-metal dependency hurdle before a single scoring prompt runs. Discovery results are cached for 45 days keyed by company name. A cache hit skips all Phase 1 web research entirely and jumps directly to product selection.

One constraint that applies to everything the Discovery Engine produces: it reads only what's publicly accessible. Vendor documentation behind a login, internal roadmaps, private API references, and paywalled partner portals are invisible to it. Labability tiers assigned at this stage should be read as "best estimate from public signals" — not as a confirmed assessment.

---

### Product-Level Research Engine

**Why it exists:** Company-level discovery can identify that a product exists and estimate its labability tier from category signals and Marketplace presence. It cannot score Technical Orchestrability or flag a provisioning time risk. That requires dedicated, product-specific research that reads the actual technical documentation, API reference, and system requirements for each candidate.

**What it does:** Produces a product-specific evidence corpus — search results plus fetched page content — covering every dimension needed for scoring. This corpus is what the scoring calls receive as their evidence input. Without it, scoring would be inference from product names. With it, scoring is inference from actual technical documentation.

**How it works:** For each selected product, 9 web searches run in parallel, each targeting a specific evidence category:

1. Deployment and technical architecture documentation
2. Training and certification catalog
3. REST API / CLI / PowerShell surface area
4. AI and Copilot feature availability
5. Azure and AWS Marketplace listings
6. Docker Hub images
7. NFR or developer trial license programs
8. System requirements and hardware dependencies
9. Competitive hands-on lab offerings (CloudShare, Instruqt, Appsembler)

Up to three high-value pages are fetched per product and read alongside search snippets. Sources include technical documentation sites, API reference pages, deployment and admin guides, training catalogs, Marketplace listing pages, Docker Hub, GitHub repositories, and competitive lab platform catalogs.

Two limitations apply to everything this engine produces. First, it reads public sources only — API references behind authentication walls, private deployment guides, and vendor-internal documentation are not accessible. Second, technical documentation is often aspirational: vendor docs describe what the product *can* do in ideal conditions, not what's typical in the field deployments Skillable's SE team will encounter. Both of these mean that Technical Orchestrability evidence in particular should be treated as a well-researched hypothesis, with the Essential Technical Resource in the recommendations being the explicit flag for what couldn't be confirmed.

Research results are stored per product within the discovery cache file. If a product was researched in a previous Inspector session for the same company, those results are reused — only products being scored for the first time trigger new web queries.

---

### Caching

**Why it exists:** A full Inspector run — 12 discovery searches, up to 9 product searches each for three products, multiple page fetches, and eight parallel scoring calls — takes real time and incurs real cost. Running the whole pipeline every time someone opens a company that was analyzed last week would be wasteful and would erode trust in the tool. Caching makes repeat access instant and makes incremental analysis (scoring a new product for a company that's already been discovered) fast and cheap.

**What it does:** Three independent cache levels allow Inspector to skip work at whatever granularity is appropriate for the request, from returning a full analysis instantly to skipping only the web searches for a specific product that was already researched.

**How it works:**

| Level | TTL | Key | What It Stores | When It Triggers |
|---|---|---|---|---|
| Full analysis cache | 45 days | `company_name` | Complete `CompanyAnalysis` including all product scores, Lab Maturity, contacts, recommendations, consumption potential | Inspector has been fully run for this company before |
| Discovery cache | 45 days | `company_name` | Discovery output: product list with labability tiers, org type, deployment models, partnership signals | Company was discovered but some products may not have been scored |
| Research cache | Per-discovery | `company_name` + `product_name` | Web search results and fetched page contents for a specific product | Product was researched in a previous Inspector session for this company |

Cache hit behavior is layered: a full analysis hit skips everything and returns the stored results instantly. A discovery hit skips all Phase 1 web research, loads the cached product list and org type, and goes directly to product selection — per-product research and scoring still run for products that haven't been scored before. A research hit skips product-level web searches for that product but still runs the Claude scoring calls on the cached research content; the API calls execute, but no new web queries are issued.

A force-refresh checkbox on the Inspector home page bypasses all three cache levels. Checking it before submitting a company name triggers a full re-run: new discovery searches, new product research, new scoring calls, and an overwrite of all cached data for that company.

---

## The Scoring Layer

**Why:** Raw research evidence — search snippets, fetched page content, Docker Hub hits — doesn't directly answer "should we pursue this account?" That answer requires structured judgment: calibrated, consistent, and traceable back to specific evidence. The Scoring Layer is where evidence becomes scores, and scores become a recommendation.

**What:** Four parallel scoring components produce the full output: a product labability score across four dimensions, a Lab Maturity score across five dimensions, a Composite Score that combines the two into a single pursuit signal, and a Consumption Potential estimate that quantifies what "pursuing" would actually mean in volume and revenue terms.

**How:** All scoring calls run fully in parallel after research completes. Each call receives the evidence corpus gathered during the Research Layer and returns structured scores, evidence citations, and flags. Parallel execution is load-bearing — waiting for each call sequentially on a three-product analysis would add significant latency to an already long operation.

---

### Scoring Engine

**Why it exists:** Translating product research into a consistent 0–100 labability score requires calibrated judgment calls — calls that need to produce the same result whether the analyst is an experienced SE who's built a hundred lab programs or someone running their first Inspector analysis. The Scoring Engine embeds that calibration into the prompts.

**What it does:** Produces a 0–100 labability score for each selected product, broken down across four dimensions. Also determines the Skillable Path (A1/A2/B/C/Unknown) and identifies any constraint flags that affect delivery viability or path assignment.

**How it works:** One Claude call per product covers all four labability dimensions simultaneously:

| Dimension | Max Score | What It Measures |
|---|---|---|
| Technical Orchestrability | 40 | Can the product be provisioned, configured, and torn down programmatically? API surface, deployment model, containerization, Marketplace presence |
| Workflow Complexity | 30 | How complex is the lab workflow? Multi-step configurations, dependency chains, realistic exercise design |
| Training Ecosystem Maturity | 20 | How developed is the training infrastructure around this product? Catalog depth, certification programs, partner training |
| Market & Strategic Fit | 10 | Is the market moving in a direction that makes labs strategically relevant? |
| **Total** | **100** | — |

Scoring prompts contain embedded calibration benchmarks derived from real Skillable customer deployments. These anchors ensure that a 70 in Inspector reflects a consistent standard across different analyses and different people running the tool — not just a Claude judgment call on that day's evidence.

That said: a calibrated AI interpretation is still an interpretation. Every score reflects what the research found and how Claude weighed it against the rubric — not an SE's direct hands-on assessment of the product. The right posture is to treat dimension scores as well-grounded hypotheses about where a product stands, and to use the Essential Technical Resource recommendation as the explicit signal for where that hypothesis needs field validation.

The scoring engine also enforces specific constraint logic based on detected signals:

| Constraint Signal | Scoring Behavior |
|---|---|
| Bare metal hardware requirement | Automatic disqualifier — scored at floor |
| MFA on API authentication | Risk flag on Technical Orchestrability; Path A2 ceiling applied |
| Provisioning time > 30 minutes | Pre-Instancing flag added to recommendations |
| No DELETE endpoint detected | Resource leak risk flag on Technical Orchestrability |
| Hardware-locked licensing (BIOS GUID) | Not a blocker — Skillable pins BIOS GUIDs; flag noted, not penalized |

---

### Lab Maturity Scorer

**Why it exists:** A product that scores 85 for Technical Orchestrability is still a poor investment if the company has no training function, no partner program, and no internal capacity to build or maintain lab content. Lab Maturity captures the organizational side of the equation — independently of any specific product's technical characteristics.

**What it does:** Produces a 0–100 Lab Maturity score that reflects the company's organizational readiness to build, deliver, and scale a lab program. This score runs in parallel with the product scoring calls — it's a company-level judgment, not a per-product one.

**How it works:** One dedicated Claude call evaluates the company across five dimensions based on evidence gathered during discovery and product research:

| Dimension | Max Raw Score | What It Measures |
|---|---|---|
| Training Org Maturity | 35 | Formal training function, content team, and catalog depth |
| Partner Program | 27 | Structured ATP or learning partner ecosystem |
| Customer Success | 35 | Active customer education motion: onboarding labs, CS-driven training |
| Organizational DNA | 10 | Is training a strategic investment or an afterthought? Hiring signals, exec sponsorship |
| Tech & Integration Readiness | 10 | LMS in use, xAPI/SCORM/LTI history, integration readiness signals |
| **Raw Maximum** | **117** | — |

The five dimensions are not equally weighted by design, and their raw totals intentionally exceed 100. The normalized score is computed as: `raw_score ÷ 1.17 = normalized 0–100`. Scoring rubrics are adjusted by organization type — a training organization without its own certification program is penalized less heavily than a software company with no training function, because the organizational models and expectations genuinely differ.

---

### Composite Score Engine

**Why it exists:** Product labability and Lab Maturity measure different things, and the right way to combine them depends on what kind of company you're looking at. A software company with a great product but no training function is a different conversation than a training organization with a mature delivery infrastructure but a technically challenging product. The Composite Score Engine handles that distinction explicitly rather than pretending a single fixed formula works for everyone.

**What it does:** Produces a single 0–100 composite score that drives the "pursue / pilot / monitor / do not pursue" recommendation. The formula weights and gating rules differ by org type.

**How it works:**

| Org Type | Product Labability Weight | Lab Maturity Weight |
|---|---|---|
| Software company | 65% | 35% |
| Channel org (training org, SI, distributor, academic) | 35% | 65% |

**Gating rules:**

| Condition | Composite Cap |
|---|---|
| Software company with Product score < 30 | Composite capped at 25 |
| Channel org with Product score < 20 | Composite capped at 30 |

The asymmetry is intentional. For a software company, the product *is* the program — if it can't be provisioned, scored, and torn down automatically, no amount of organizational readiness makes a scalable lab program viable. A high Lab Maturity score sitting on top of a failing product score should not produce a composite that implies viability. For a channel organization — training orgs, SIs, distributors, academic institutions — the primary investment signal is the delivery machine. These organizations can build effective programs even with products that score lower technically, provided their delivery infrastructure and distribution capabilities are strong. The gating rules protect against composite scores that would mislead a pursuit recommendation in either direction.

---

### Consumption Potential Model

**Why it exists:** A composite score of 72 is useful for prioritization. It does not answer the question an AE or TSM needs answered before building a business case: *what would this actually be worth?* Consumption Potential translates product fit signals into volume and revenue estimates that can anchor the business conversation.

**What it does:** Projects lab consumption across six business motions, producing a per-motion estimate of population, hours, adoption, and annual lab hours. Combined with a VM rate estimate, this produces the revenue range that goes into a business case.

**How it works:** One Claude call generates estimates for all six motions simultaneously:

| Motion | What It Represents |
|---|---|
| Customer Onboarding | Lab-based onboarding delivered at or shortly after point of sale |
| ATP/Channel | Partner certification, enablement, and authorized training programs |
| General Practice | Ongoing technical skill development for customers and partners |
| Certification/PBT | Performance-based testing and formal certification programs |
| Employee Enablement | Internal training for SE, CSM, TSM, and support staff |
| Events | Conference labs, tech days, POC demos, and hosted hands-on experiences |

For each motion, the model estimates population range (low and high), hours of hands-on lab time per user per year, and an adoption percentage — the fraction of that population who would realistically complete structured lab training in a given year.

**These are directional estimates, not market research.** The population figures are Claude's inference from public signals like partner directory sizes, published install bases, and company headcount data. The right way to use them is to answer the order-of-magnitude question — is this a 100-hour-per-year opportunity or a 100,000-hour-per-year opportunity — not to present them as projections in a business case without further validation.

To keep estimates defensible, the scoring prompt enforces hard adoption ceilings for each motion type:

| Motion | Adoption % Ceiling | Rationale |
|---|---|---|
| Customer Onboarding | 2–5% | Most onboarding is rep-led or self-service, not structured lab-based |
| ATP/Channel | 5–10% | Partner reps who actively complete labs, not total partner headcount |
| General Practice | 2–5% | Self-directed lab usage is a small minority of practitioners |
| Certification/PBT | 2–4% | Only the most dedicated pursue certification each year |
| Employee Enablement | 8–15% | Internal technical staff are the highest adopters |
| Events | 30–70% | People attend specifically to do labs; adoption is much higher than ongoing training |

Population ranges are also required to stay tight — the high end should be no more than 1.5× the low (e.g., 500–750, not 500–5,000). Wide ranges signal uncertainty; the prompt instructs the model to narrow the population rather than widen the range.

**Lab cost estimates use specific rate tiers.** These are the exact values used in the scoring prompt and in the results dashboard revenue calculation:

| Delivery Path | Environment | $/hr |
|---|---|---|
| Cloud Slice (Path A1/A2) | Any Azure or AWS lab | $10.50 |
| Standard VM (Path B) | 1–3 VMs, typical complexity | $12–15 |
| Large/Complex VM (Path B) | Many VMs, multiple networks, GPU, large clusters | $45–55 |
| Simulation (Path C) | AI Vision compute + platform overhead, no live environment | $5 |

The Cloud Slice rate ($10.50) is a Skillable platform overhead rate — it applies regardless of which Azure or AWS services are used in the lab, and is separate from any Azure/AWS consumption costs the customer pays through their cloud subscription. Simulation ($5) reflects AI Vision compute and platform overhead even though no live environment is provisioned. The VM rate reflects environment complexity: a clean single-VM install gets $12, 2–3 VMs get $15, and demanding topologies (multi-VM with networking, GPU) reach $45–55. Claude defaults to the standard VM tier unless the product genuinely requires a large environment — the $45–55 range should be rare.

**Inspector does not trust Claude's arithmetic.** After the scoring call returns, the server recomputes every annual hours total from the parsed motion fields — population midpoint × hours per user per year × adoption % — and replaces whatever figures Claude produced. Claude reasons well about the inputs; it is not a reliable calculator at the motion-summation level.

Every result includes a `methodology_note` field generated by the scoring call, shown directly on the results page. This note is required to acknowledge the estimate basis and name the 1–2 primary signals used (install base, ATP count, company headcount, conference attendance). If you see a methodology note that sounds vague or doesn't cite a specific signal, treat the numbers with extra skepticism.

---

## The Results Layer

**Why:** Research and scoring produce a lot of structured data. The Results Layer is what makes that data useful — surfacing it in a format that supports a technical discovery conversation, an executive qualification conversation, and a handoff to the next tool in the workflow, all from the same output.

**What:** A results dashboard that renders the full `CompanyAnalysis` — scores, evidence, paths, consumption table, contacts, and recommendations — plus a handoff button that carries the analysis into Designer, and an API endpoint that makes the full pipeline available programmatically for batch use cases like Prospector.

**How:** The dashboard renders when all parallel scoring calls complete. The handoff button navigates to Designer pre-populated with everything Inspector already knows. The API endpoint runs the full pipeline synchronously and returns the `CompanyAnalysis` as a single JSON payload, bypassing the streaming interface for callers that don't need it.

---

### Results Dashboard

**Why it exists:** A structured JSON payload full of scores and evidence is not a discovery call prep tool. The dashboard is what turns the `CompanyAnalysis` into something an SE can open the morning of a call and walk into the room ready.

**What it does:** Renders the full analysis in a format that supports both technical depth and executive-level qualification. Every score is traceable to specific evidence, and every recommendation is grounded in what the research actually found.

**How it works:** The results page surfaces the following:

- **Company overview:** Organization name, description, org type, composite score, pursuit recommendation, and analysis date.
- **Per-product labability scores:** Dimension breakdown (Technical Orchestrability, Workflow Complexity, Training Ecosystem Maturity, Market and Strategic Fit), total score, Skillable Path determination (A1 / A2 / B / C / Unknown), and any risk or qualification flags.
- **Evidence:** Every score is backed by evidence claims organized by the lab lifecycle — Provision → Configure → Score → Teardown. Each claim is labeled by the aspect it supports and includes the source URL and page title so the SE can verify or follow up directly.
- **Lab Maturity score:** Company-level score with dimension breakdown and supporting evidence.
- **Consumption Potential table:** All six motions with population range, hours per user per year, adoption %, annual hours total, and VM rate estimate.
- **Contacts:** Decision makers and influencers for each product and the company overall, with title, inferred role in a lab program conversation, and source. **Important:** Contact names and titles are extracted from LinkedIn snippets returned in search results — not from direct LinkedIn profile scrapes. These snippets may be months out of date. People change roles frequently. Treat every contact as a starting point for verification, not a confirmed outreach target. If a contact is flagged as a Skillable alumni (previously at a known customer in a training or enablement role), that's a warm outreach signal worth prioritizing — but still verify their current role before reaching out.
- **Recommendations:** Per product — Delivery Path, Scoring Approach, Essential Technical Resource (the single highest-priority open question blocking a pilot), and Next Step. These are grounded in the evidence, not generated from a template.
- **"Design Lab Program →" handoff button:** Appears when scoring is complete. See below.

A CSV export of all scored products is available from the results page. Columns include company name, product name, composite score, product labability score, Lab Maturity score, Skillable Path, and org type.

---

### Inspector → Designer Handoff

**Why it exists:** When an SE finishes an Inspector analysis and decides a lab program is worth building, the last thing they should have to do is manually re-enter everything Inspector already knows into the first screen of Designer. The handoff eliminates that gap entirely.

**What it does:** Carries the full context of an Inspector analysis into Designer Phase 1 — company name, scored products with labability scores and recommended Skillable paths, and the top contacts identified for each product. The SE arrives in Designer already oriented, refining and approving a pre-populated program structure rather than starting from a blank form.

**How it works:** When scoring completes, the results page displays a "Design Lab Program →" button. Clicking it navigates to `/designer?analysis_id={id}`. Designer reads the Inspector analysis and pre-fills Phase 1 with everything it found. The `inspector_analysis_id` is stored on the Designer program record for provenance tracking — if Inspector is subsequently re-run on the same company (after a 45-day cache expiry or a force-refresh), Designer displays a "⚠ Source analysis updated" badge on the program, prompting the SE to review whether any scores or contacts have changed materially.

---

### API Access

**Why it exists:** Inspector's streaming interface and product selection step are designed for an SE sitting at a browser. Prospector, which runs Inspector-quality analyses across an entire target account list in batch, doesn't need either of those things. The API endpoint exposes the full pipeline in a form that programmatic callers can use directly.

**What it does:** Accepts a company name and an optional list of known products, runs the complete Inspector pipeline, and returns the full `CompanyAnalysis` JSON as a single synchronous response. No streaming, no product selection step, no browser required.

**How it works:**

**`POST /inspector/api/analyze`**

Request body:

```json
{
  "company_name": "string",
  "known_products": ["string"]   // optional
}
```

Returns the full `CompanyAnalysis` JSON, including all discovered products with labability tiers, all scored products with dimension scores and evidence, Lab Maturity score, contacts, consumption potential, and recommendations.

This endpoint bypasses the discovery and research caches and runs the full pipeline synchronously. The `known_products` field, if supplied, seeds the product list and adds targeted discovery queries for each named product. Prospector calls this endpoint when it needs Inspector-quality analysis as part of a batch run — rather than duplicating the research and scoring pipeline, Prospector delegates to Inspector and stores the returned `CompanyAnalysis` under the Prospector account record.

---

*Last updated: 2026-03-30*
*Maintained by: Skillable Intelligence platform team*
