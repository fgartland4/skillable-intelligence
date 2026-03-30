# Skillable Intelligence — Inspector

> Inspector is the deep-analysis tool in the Skillable Intelligence platform. It takes a single company and produces a fully scored, evidence-backed assessment of every product that could become a Skillable lab program.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md).

---

## 1. What Problem Does Inspector Solve?

Before a discovery call, a Solution Engineer typically spends one to three hours manually researching a company — reading product documentation, scanning training portals, checking Marketplace listings, and piecing together a picture of whether a lab program is even viable. That research lives in a browser history and a handful of notes. When the next SE picks up the same account, or when the first SE circles back after six months, the process starts over from zero.

Inspector automates the same research an SE would do, but with consistency, depth, and speed that manual research can't match. It runs 12 parallel web searches during discovery, fetches and reads multiple source pages, and passes all of that evidence through calibrated scoring prompts that have been anchored against real Skillable customer deployments. The output is a structured CompanyAnalysis: a composite score, per-product labability scores broken down by dimension, a recommended Skillable delivery path, a consumption potential model, evidence claims with source URLs, and a prioritized list of contacts. Because results are cached for 45 days, the next person who opens the same company sees the full analysis instantly rather than triggering another research pass.

That output serves two distinct conversations. For a Solution Engineer preparing for a technical discovery call, Inspector surfaces the specific product-level signals that matter: Technical Orchestrability score, Skillable Path determination, provisioning risk flags, and the Essential Technical Resource — the one open question that must be resolved before a pilot can start. For an Account Executive qualifying a logo before investing SE time, Inspector surfaces the composite score and the "pursue / pilot / monitor / do not pursue" recommendation alongside the names of the decision makers most likely to own a lab initiative.

Inspector is also the starting point for the Designer tool. When scoring completes, a "Design Lab Program →" button appears in the results dashboard. Clicking it carries the `analysis_id`, company name, product scores, and recommended contacts directly into Designer Phase 1, eliminating manual re-entry of everything Inspector already discovered. The two tools are designed to flow sequentially: Inspector answers whether a lab program is worth building; Designer answers how to build it.

---

## 2. Personas

### Solution Engineer (Primary)

The SE is Inspector's primary user. Before a discovery call or pilot proposal, the SE opens Inspector, enters the company name, selects the products most likely to become lab programs, and runs a full scoring pass. What they need from the output is specific and technical: per-product scores broken down by dimension, the Skillable Path determination (A1, A2, B, C), the Essential Technical Resource flag that identifies the single highest-priority open question, and the consumption estimates they can use to anchor a business case. Inspector replaces the hours of pre-call research an SE would otherwise do manually, and it surfaces the technical proof points — API surface, provisioning model, Marketplace presence, competitive lab signals — in a format that maps directly to Skillable's delivery architecture.

Typical trigger: An AE brings in a new logo and the SE needs to get up to speed before the first technical conversation.

### Account Executive

The AE uses Inspector to qualify a logo before asking for SE time. The signals they need are high-level: composite score, the pursuit recommendation, and the names of the decision makers and influencers most likely to own a training or enablement initiative. They are not reading the evidence section or interpreting dimension scores; they want to know whether this account is worth a deeper investment and who to call.

Typical trigger: An SDR passes a warm account, or the AE is preparing for a QBR and needs to identify expansion logos in their territory.

### Technical Sales Manager / Customer Success Manager

The TSM or CSM uses Inspector on accounts that are already customers, looking for expansion opportunities. They want to know which products the customer has that haven't been incorporated into a lab program yet, what the lab maturity signals look like for the organization, and who the relevant contacts are for an expansion conversation. Inspector's Lab Maturity Score is particularly useful here because it surfaces organizational readiness signals — training org structure, partner program depth, LMS usage — that indicate whether the customer has the infrastructure to absorb an expanded program.

Typical trigger: Renewal prep, QBR preparation, or an active expansion motion where the CSM needs to identify the next program to propose.

---

## 3. The Inspector Workflow

Inspector executes in four sequential phases: Discovery, Product Selection, Deep Research + Scoring, and Results.

### Phase 1: Discovery

The user enters a company name on the Inspector home page. If they know specific products they want to evaluate, they can enter those as well — Inspector will resolve the parent company automatically and include those products in the discovery output. The Research Engine immediately fires 12 parallel web searches across six query categories: product portfolio, training and certification catalog, authorized training partner (ATP) signals, customer success and onboarding motion, organizational and contact signals, and (if known products were supplied) targeted queries for each named product. While searches run, the company homepage and up to five additional high-value pages are fetched in parallel and read by Claude.

Inspector-specific discovery queries include searches for Marketplace listings (Azure, AWS, or Google Cloud), Docker Hub and container availability, NFR or developer license programs, AI and Copilot feature announcements, and hands-on labs offered by competitive platforms (CloudShare, Instruqt, Appsembler). These signals are lightweight proxies for Technical Orchestrability — if a product is on the Azure Marketplace or has a public Docker image, its deployment model is almost certainly automatable without bare-metal dependencies.

Claude reads all fetched content and produces a structured discovery output: organization type, a product list with labability tiers assigned to each product (`highly_likely`, `likely`, `less_likely`, `not_likely`), identified deployment models, candidate Skillable paths, a company description, and partnership signals. The organization type is also resolved at this stage — one of six values: `software_company`, `academic_institution`, `training_organization`, `systems_integrator`, `technology_distributor`, or `professional_services`. This classification drives the scoring weights and the composite formula used in Phase 3.

Discovery results are cached for 45 days, keyed by company name. If a fresh cache entry exists for the company, all Phase 1 web research is skipped entirely and the system moves directly to product selection using the cached output.

### Phase 2: Product Selection

Products returned from discovery are organized into four grouped sections by labability tier: Highly Likely, Likely, Less Likely, and Not Likely. This grouping is the user's signal about where to focus scoring resources. Deep research and Claude scoring per product involves multiple API calls and meaningful token volume; running the full pipeline on every product the company makes would be slow and expensive for products that discovery has already flagged as poor candidates.

The user selects up to three products to score. A "Select All Likely Labable" shortcut pre-checks all products in the Highly Likely and Likely tiers, which is the right default for most analyses. Products that Inspector identified as belonging to other companies — competitive products that appeared in the research — are shown in a separate section and excluded from scoring; they provide context but are not candidates for a Skillable program. If a product was scored in a previous Inspector run, it shows a badge indicating that cached research is available, meaning scoring will be faster.

### Phase 3: Deep Research + Scoring

For each selected product, the Research Engine runs 9 additional product-specific web searches targeting: deployment and technical architecture documentation, training and certification catalog, REST API / CLI / PowerShell surface area, AI and Copilot feature availability, Azure and AWS Marketplace listings, Docker Hub images, NFR or developer trial license programs, system requirements and hardware dependencies, and competitive hands-on lab offerings. Up to three high-value pages are fetched per product and read alongside the search results. Research results are stored per product within the discovery cache file — if a product was previously researched in an earlier session, its cached results are used directly and no web queries are re-run.

Once research is complete for all selected products, the scoring pass runs fully in parallel: one Claude call per product covering all four labability dimensions (Technical Orchestrability, Workflow Complexity, Training Ecosystem Maturity, Market and Strategic Fit), one Claude call for the Lab Maturity score, one Claude call for Consumption Potential, one for Contacts, and one for Recommendations. All of these calls execute concurrently. Each individual call has a 5-minute timeout; the full scoring pass has a 10-minute timeout enforced via the SSE stream.

Progress is streamed to the user in real time via Server-Sent Events (SSE). Six descriptive steps are shown during the scoring pass, updating as each stage completes, so the user has a clear signal of what's happening rather than watching a spinner.

### Phase 4: Results

When all scoring calls complete, the results dashboard renders the full analysis. See Section 4.8 for a detailed description of what the results page surfaces and how it is structured.

---

## 4. Components

### 4.1 Discovery Engine

**Purpose:** Resolve what the company makes and which products are candidates for lab programs, without committing to expensive per-product research.

**Research approach:** 12 parallel web searches across six query categories — product portfolio, training and certification, ATP and partner program, customer success, organizational and contact signals, and targeted product queries if known products were supplied. The company homepage and up to five additional high-value pages are fetched in parallel. Inspector-specific discovery queries cover Marketplace listings, Docker/container availability, NFR or developer license programs, AI feature announcements, and competitive lab platform presence.

**Sources:** Official product and company pages, training portals, partner program landing pages, LinkedIn snippets (via search snippet results, not direct scrape), press releases, and Marketplace catalog pages.

**Output:** Organization type (one of six values), product list with labability tier per product, deployment models, Skillable path candidates, company description, and partnership signals.

**Cache:** 45-day discovery cache keyed by company name. A cache hit skips all Phase 1 web research entirely.

### 4.2 Product Selection Interface

**Purpose:** Let the user focus scoring resources on the products most likely to be worth the investment.

**Why it matters:** Discovery assigns labability tiers using lightweight signals — deployment model, product category, platform type, Marketplace presence — without running expensive per-product research. Those tiers are directionally accurate and give the user an informed starting point, but they are estimates. The selection interface surfaces them transparently so the user can make an informed choice about where to invest the full scoring pass.

**Behavior:** Products are grouped by tier (Highly Likely, Likely, Less Likely, Not Likely). Up to three products can be selected for scoring. The "Select All Likely Labable" shortcut pre-checks all Highly Likely and Likely products. Competitive products (products belonging to other companies that appeared in research) are shown separately and excluded from the selection. Previously-scored products display a badge indicating cached research is available.

### 4.3 Research Engine (Product-Level)

**Purpose:** Gather product-specific evidence to support scoring across all four labability dimensions.

**Research approach:** 9 web searches per product, each targeting a specific evidence category: deployment and technical architecture, training and certification catalog, REST API / CLI / PowerShell surface area, AI and Copilot features, Azure and AWS Marketplace listings, Docker Hub images, NFR or developer trial license programs, system requirements and hardware dependencies, and competitive hands-on lab offerings (CloudShare, Instruqt, Appsembler). Up to three high-value pages are fetched per product and read alongside search snippets.

**Sources:** Technical documentation sites, API reference pages, deployment and admin guides, training catalogs, Azure and AWS Marketplace, Docker Hub, GitHub repositories, competitive lab platform catalogs.

**Cache:** Research results are stored per product within the discovery cache file. If a product was researched in a previous session for the same company, those results are reused — only products being scored for the first time trigger new web queries.

### 4.4 Scoring Engine

**Purpose:** Translate product-level research evidence into structured, calibrated scores across all four labability dimensions.

**How it works:** The full scoring model is described in [intelligence-platform.md](intelligence-platform.md) §5. Inspector runs the complete scoring pass: all four product labability dimensions, the Lab Maturity score, Consumption Potential, Contacts, and Recommendations — all in parallel Claude calls. The four product dimensions and their weights are:

| Dimension | Max Score |
|---|---|
| Technical Orchestrability | 40 |
| Workflow Complexity | 30 |
| Training Ecosystem Maturity | 20 |
| Market & Strategic Fit | 10 |
| **Total** | **100** |

**Calibration:** Scoring prompts contain embedded benchmarks derived from real Skillable customer deployments. These calibration anchors ensure that a score of 70 in Inspector reflects a consistent standard of product fit across different analyses and different analysts running the tool.

**Key constraints enforced by the scoring engine:**

| Constraint Signal | Scoring Behavior |
|---|---|
| Bare metal hardware requirement | Automatic disqualifier — scored at floor |
| MFA on API authentication | Risk flag on Technical Orchestrability; Path A2 ceiling applied |
| Provisioning time > 30 minutes | Pre-Instancing flag added to recommendations |
| No DELETE endpoint detected | Resource leak risk flag on Technical Orchestrability |
| Hardware-locked licensing (BIOS GUID) | Not a blocker — Skillable pins BIOS GUIDs; flag noted but not penalized |

### 4.5 Lab Maturity Scorer

**Purpose:** Score the company's organizational readiness to build, deliver, and scale a lab program — independently of any specific product's technical characteristics.

**How it works:** The Lab Maturity score is produced by a dedicated Claude call that runs in parallel with the product scoring calls. It evaluates the company across five dimensions based on evidence gathered during discovery and product research.

**Five dimensions:**

| Dimension | Max Raw Score | What It Measures |
|---|---|---|
| Training Org Maturity | 35 | Formal training function, content team, and catalog depth |
| Partner Program | 27 | Structured ATP or learning partner ecosystem |
| Customer Success | 35 | Active customer education motion: onboarding labs, CS-driven training |
| Organizational DNA | 10 | Is training a strategic investment or an afterthought? Hiring signals, exec sponsorship |
| Tech & Integration Readiness | 10 | LMS in use, xAPI/SCORM/LTI history, integration readiness signals |
| **Raw Maximum** | **117** | — |

**Normalization:** The five dimensions are not equally weighted by design, and their raw totals intentionally exceed 100. The normalized score is computed as: `raw_score ÷ 1.17 = normalized 0–100`.

**Org-type adjustment:** Scoring rubrics are adjusted by organization type. A training organization that lacks its own certification program is penalized less heavily than a software company with no training function — the expectations differ because the organizational models differ.

### 4.6 Composite Score Engine

**Purpose:** Produce a single number that combines product fit and organizational readiness into a score that drives the pursuit recommendation.

**Formula:** The composite weights differ based on the organization type resolved during discovery.

| Org Type | Product Labability Weight | Lab Maturity Weight |
|---|---|---|
| Software company | 65% | 35% |
| Channel org (training org, SI, distributor, academic) | 35% | 65% |

**Gating rules:**

| Condition | Composite Cap |
|---|---|
| Software company with Product score < 30 | Composite capped at 25 |
| Channel org with Product score < 20 | Composite capped at 30 |

**Why the asymmetry exists:** For a software company, the product is the program — if the product cannot be provisioned, scored, and torn down automatically, no amount of organizational readiness makes a scalable lab program viable. A high Lab Maturity score with a failing product score should not produce a composite that suggests viability. For a channel organization (training orgs, SIs, distributors, academic institutions), the primary investment signal is the delivery machine — their organizational infrastructure, partner network, and training catalog. These organizations can build effective programs even with products that score lower technically, provided their delivery and distribution capabilities are strong. The gating rules protect against composite scores that would mislead a pursuit recommendation in either direction.

### 4.7 Consumption Potential Model

**Purpose:** Translate product labability signals into a volume and revenue estimate that can anchor the business case portion of a discovery conversation.

**Six consumption motions:**

| Motion | What It Represents |
|---|---|
| Customer Onboarding | Lab-based onboarding delivered at or shortly after point of sale |
| ATP/Channel | Partner certification, enablement, and authorized training programs |
| General Practice | Ongoing technical skill development for customers and partners |
| Certification/PBT | Performance-based testing and formal certification programs |
| Employee Enablement | Internal training for SE, CSM, TSM, and support staff |
| Events | Conference labs, tech days, POC demos, and hosted hands-on experiences |

**Per-motion estimate fields:** Population range (low and high), hours per user per year, adoption percentage, and annual hours total.

**VM rate estimate:** A $/hr range for VM-based lab delivery (range: $12–$55/hr). A value of 0 indicates the product follows a SaaS or cloud-slice path where VM rate is not applicable.

**Arithmetic integrity:** Inspector does not trust Claude's arithmetic on the annual hours totals. The totals are recomputed server-side from the parsed motion fields (population midpoint × hours/user/year × adoption %) after the scoring call returns, and the recomputed values replace any figures Claude produced directly.

### 4.8 Results Dashboard

**Purpose:** Surface the full analysis in a format that supports both a technical discovery conversation and an executive qualification conversation.

**What the results page shows:**

- **Company overview:** Organization name, description, org type, composite score, pursuit recommendation, and analysis date.
- **Per-product labability scores:** Dimension breakdown (Technical Orchestrability, Workflow Complexity, Training Ecosystem Maturity, Market and Strategic Fit), total score, Skillable Path determination, and any risk or qualification flags.
- **Evidence:** Every score is backed by evidence claims that follow the lab lifecycle — Provision → Configure → Score → Teardown. Each claim is labeled in bold by the aspect it supports, and includes the source URL and page title so the SE can verify or follow up directly.
- **Skillable Path:** One of A1 (Azure Cloud Slice), A2 (Custom API/BYOC), B (VM Lab), C (Simulation), or Unknown — determined by the scoring engine based on deployment model, API surface, and Marketplace signals.
- **Consumption Potential table:** All six motions with population range, hours/user/year, adoption %, annual hours total, and VM rate estimate.
- **Lab Maturity score:** Company-level score with dimension breakdown and supporting evidence.
- **Contacts:** Decision makers and influencers for each product and for the company overall, with title, inferred role in a lab program conversation, and source.
- **Recommendations:** Per product — Delivery Path, Scoring Approach, Essential Technical Resource (the single highest-priority open question blocking a pilot), and Next Step. Recommendations are grounded in the evidence gathered during research, not generated from a template.
- **"Design Lab Program →" handoff button:** Appears when scoring is complete. See Section 4.9.

**Export:** A CSV export of all scored products is available from the results page. Columns include company name, product name, composite score, product labability score, Lab Maturity score, Skillable Path, and org type.

### 4.9 Inspector → Designer Handoff

**Purpose:** Eliminate manual re-entry of everything Inspector already knows when the SE is ready to build a lab program.

**How it works:** When scoring completes, the results page displays a "Design Lab Program →" button. Clicking it navigates to `/designer?analysis_id={id}`. Designer reads the Inspector analysis and pre-fills Phase 1: company name, the scored products with their labability scores, recommended Skillable path, and the top contacts identified for each product. The SE arrives in Designer already oriented — they are refining and approving a pre-populated program structure rather than starting from a blank form.

**Provenance tracking:** The `inspector_analysis_id` is stored on the Designer program record. If Inspector is subsequently re-run on the same company — for example after a 45-day cache expiry or a force-refresh — Designer displays a "⚠ Source analysis updated" badge on the program, prompting the SE to review whether any scores or contacts have changed materially.

---

## 5. Caching Architecture

Inspector uses three cache levels. All are keyed by company name and stored in the analysis file system. They operate independently, meaning a hit at a higher level does not require hits at lower levels.

| Level | TTL | Key | What It Stores | When It Triggers |
|---|---|---|---|---|
| Full analysis cache | 45 days | `company_name` | Complete `CompanyAnalysis` including all product scores, Lab Maturity, contacts, recommendations, consumption potential | Inspector has been fully run for this company before |
| Discovery cache | 45 days | `company_name` | Discovery output: product list with labability tiers, org type, deployment models, partnership signals | Company was discovered but some products may not have been scored |
| Research cache | Per-discovery | `company_name` + `product_name` | Web search results and fetched page contents for a specific product | Product was researched in a previous Inspector session for this company |

**Cache hit behavior:**

- **Full analysis hit:** Skip everything. Return the stored results instantly to the results dashboard.
- **Discovery hit:** Skip all Phase 1 web research. Load the cached product list and org type, go directly to product selection. Per-product research and scoring still run for any products that haven't been scored before.
- **Research hit:** Skip product-level web searches for that product. Run Claude scoring on the cached research content — the API calls and scoring logic still execute, but no new web queries are issued.

**Force refresh:** A force-refresh checkbox on the Inspector home page bypasses all three cache levels. Checking it before submitting a company name triggers a full re-run: new discovery searches, new product research, new scoring calls, and an overwrite of all cached data for that company.

---

## 6. API Access

Inspector exposes a headless endpoint for batch or programmatic use cases where streaming and the product selection interface are not needed.

**`POST /inspector/api/analyze`**

**Request body:**

```json
{
  "company_name": "string",
  "known_products": ["string"]   // optional
}
```

**Returns:** Full `CompanyAnalysis` JSON, including all discovered products with labability tiers, all scored products with dimension scores and evidence, Lab Maturity score, contacts, consumption potential, and recommendations.

**Behavior:** This endpoint bypasses the discovery and research caches and runs the full pipeline synchronously. There is no streaming — the response is returned as a single JSON payload when the complete pipeline finishes. The `known_products` field, if supplied, seeds the product list and adds targeted discovery queries for each named product.

**Usage:** This endpoint is called by Prospector when it needs a full Inspector-quality analysis as part of a batch run. Rather than duplicating the research and scoring pipeline, Prospector delegates to Inspector's API and stores the returned `CompanyAnalysis` under the Prospector account record.

---

*Last updated: 2026-03-30*
*Maintained by: Skillable Intelligence platform team*
