# Research Methodology Improvements

Items identified during the Platform Foundation conversations that should be addressed when refactoring the research and detection logic. These are implementation improvements, not foundation-level decisions.

This document reflects best current thinking. As thinking evolves, this document evolves with it -- fully synthesized, never appended.

---

## Prompt Generation System -- Implementation Requirements

### Overview
Replace the static product_scoring.txt with a three-layer prompt generation system: Configuration + Template = Generated Prompt at runtime. See Platform-Foundation.md for the full architecture description.

### Build Sequence

| Step | What | Details |
|---|---|---|
| **1. Design the config schema** | Define the structure that holds everything | JSON or Python dataclass. Must be validatable -- weights add to 100, all badges have color criteria, no orphan references. |
| **2. Populate the config** | Transfer everything from Badging-and-Scoring-Reference.md into the config | Every pillar, dimension, badge, scoring signal, penalty, threshold, category prior, lab type, canonical list. |
| **3. Write config validation** | Automated checks that run on load | Weights sum correctly per pillar. All badges have at least one color defined. Locked vocabulary has no conflicts. Canonical lists are complete. |
| **4. Write the prompt template** | The AI instruction structure with placeholders | Reasoning sequence, evidence standards, output format, badge principles. References config variables with {placeholder} syntax. |
| **5. Build the generator** | Code that merges config + template at runtime | Reads config, validates it, injects into template, returns the complete prompt string. Never writes a static file. |
| **6. Write tests** | Validate the system end-to-end | Config validation tests. Template rendering tests. Regression tests against known company data (Trellix, CompTIA). |
| **7. Run against real data** | Score Trellix, CompTIA, Microsoft with new system | Compare results to old scoring. Validate that Fit Scores, verdicts, and badges feel right. Adjust config values based on results. |

### Config File Location
`backend/scoring-config.json` (or `backend/scoring_config.py` if Python dataclass is preferred for type safety)

### Template File Location
`backend/prompts/scoring-template.md`

### Generator Location
`backend/prompt_generator.py` -- single function: `generate_scoring_prompt() -> str`

### What This Replaces
`backend/prompts/product_scoring.txt` -- will be deleted after the new system is validated. During transition, both can coexist with a feature flag.

### What Lives in the Configuration

Everything variable-driven, including:

| Category | Examples |
|---|---|
| **Pillar structure** | Names, weights (Product Labability 40%, Instructional Value 30%, Customer Fit 30%), UX questions |
| **Dimension structure** | Names, weights within each Pillar (e.g., Provisioning 35, Lab Access 25, Scoring 15, Teardown 25) |
| **Badge definitions** | Names, color criteria (green/gray/amber/red), scoring signals, point values, evidence requirements |
| **Penalties** | Names, deduction values, which dimension they apply to |
| **Thresholds** | Score ranges for verdict grid (80/65/45/25), ACV tier boundaries |
| **Verdict labels** | The 10 verdict names and definitions |
| **Category priors** | Product categories and their demand ratings |
| **Lab type menu** | The 12 lab versatility types with likely product mappings |
| **Canonical lists** | Lab platform providers, LMS partners, organization types, locked vocabulary |
| **ACV rates** | Delivery path rate tables, consumption motion labels, adoption ceilings |
| **Confidence rules** | When to use confirmed vs. indicated vs. inferred |
| **Reasoning sequence** | Step-by-step order the AI follows when scoring. Can add, reorder, or remove steps. |
| **Evidence standards** | Writing rules for evidence bullets -- labels, qualifiers, length limits, uniqueness rules |
| **Delivery pattern signals** | Specific patterns (ADO, GitHub, vSphere, identity lifecycle, etc.) and their guidance |
| **Skillable capabilities** | Datacenter support, Cloud Slice modes, supported services, scoring methods |
| **Contact guidance** | Rules for identifying decision makers and influencers |

### Future: Admin GUI
When AuthN/AuthZ is implemented, add a web interface for editing the config:
- View/edit all config values
- Validation on save
- Change history with timestamps and user attribution
- Admin-only access
- Changes take effect on next scoring run

---

## Core Principle: Define Once, Reference Everywhere

All Pillar names, dimension names, weights, thresholds, badge names, and vocabulary must be defined in a single configuration layer (likely a config file or constants module) and referenced by every consumer -- code, AI prompts, UX templates, documentation generation. Nothing hard-coded. If a name or weight changes, one edit propagates everywhere. This is a core architectural requirement for the refactor.

---

## Core Principle: Confidence Coding

Confidence coding (confirmed / indicated / inferred) must be core logic in the codebase, not just a display convention. Every finding the AI produces must carry a confidence level as a stored field. This confidence level:
- Influences badge color assignment (confirmed evidence can support green; inferred evidence may cap at amber)
- Is stored in the data model alongside the finding itself
- Surfaces in evidence language when displayed
- Powers the badge hover evidence modal (1.5s delay, shows bullets + source + confidence)
- Is available to downstream consumers (HubSpot ICP Context, Designer, etc.)

This is not optional. It is how the platform achieves GP3 (Explainably Trustworthy) at the code level.

---

## Badge Evidence Hover Implementation

Every badge must carry an evidence payload. No badge renders without evidence. The hover interaction:

1. User hovers over a badge
2. After 1.5 second delay, a modal appears
3. Modal displays: evidence bullets, source, confidence level (confirmed/indicated/inferred)
4. Modal dismisses on mouseout

This requires the data model to store evidence alongside every badge. The scoring prompt must instruct the AI to produce evidence for every badge it assigns. Badges without evidence are invalid and should be caught during validation.

---

## Two-Stage Inspector Flow

Replace the current single-pass Inspector run with a two-stage flow.

**Stage 1 -- Company Report (broad scan)**
- Triggered by: user types company name
- Runs: initial product discovery, company-level signals, competitive identification
- Output: Company Report with overall company fit score, ranked product list with initial signals per product, competitor list paired to specific company products (e.g., Cohesity DataProtect to Veeam, Rubrik, Commvault)
- Stored as the Company record -- runs once per company regardless of which tool triggered it
- This IS the Prospector Customer Expansion pass -- same research, same output, same Company Record

**Stage 2 -- Deep Dive (user-selected products)**
- Triggered by: user selects 3-4 products from the Stage 1 ranked list
- Runs: exhaustive analysis on selected products -- full delivery path, scoring approach, consumption estimate
- Output: appended to the Company Report
- Solves the "only three products" problem -- Stage 1 sees the full portfolio; Stage 2 goes deep on an informed selection

### Inspector Two-Zone Layout

Inspector results page uses a two-zone layout reflecting the two-stage flow.

**Top zone (Stage 1 output -- seller-facing):**
- Company headline + AI-generated summary paragraph (liftable for Slack/email)
- Overall fit score
- Ranked product list with initial signals
- Competitive pairings
- Recommended next action

**Expandable sections (Stage 2 output -- SE depth):**
- Per-product gate scores with evidence
- Delivery path recommendation + rationale
- Scoring approach recommendation + rationale
- Partnership readiness breakdown
- Consumption potential math
- Research citations

The expandable sections are NOT "SE-only." Sellers need conversational competency across the technical detail -- especially with rationale included. The collapsible design means sellers can go as deep as they choose. Rationale in every recommendation is what makes technical detail useful to a seller.

### Competitive Pairing in Stage 1

Stage 1 Company Report includes competitor identification AND competitive product pairing.
- Surface competitors of the company being analyzed
- Map each company product to its competitive equivalents
- Gives sellers immediate competitive context for the conversation
- Enables Prospector lookalike analysis -- if Cohesity is a strong fit, companies selling competitive products are likely strong fits too
- Surfaces displacement signals -- if a competitor is already doing labs (Instruqt, CloudShare), that's a selling urgency signal
- Lives in the Stage 1 Company Report, visible by default (not in an expandable)

---

## SaaS Product Scoring -- Three-Path Evaluation

For SaaS products (browser-based, no on-prem installer), the scoring logic evaluates three delivery paths and recommends the strongest viable one with rationale.

**Three paths ranked:**

| Path | Score | Key requirement |
|---|---|---|
| Cloud Slice | Highest | Vendor supports tenant provisioning via Marketplace or API |
| Custom API (BYOC) | Strong | API covers full lab lifecycle: provision + configure + validate + DELETE; no MFA on API auth |
| Credential Pool | Moderate | Vendor provides sandbox accounts; accounts can be reset to clean state after each lab |
| Simulation | Lowest | No sandbox, no API, no viable credential pool |

**Custom API lifecycle -- four steps, individually weighted:**
1. **Provision** -- API call to create tenant/user/workspace (common, usually findable)
2. **Configure** -- API calls to set initial state, not read-only (moderately common)
3. **Validate/Score** -- endpoints to confirm learner completed tasks; this is the hard one and often missing
4. **DELETE/Teardown** -- deprovision endpoint; absence is a blocker

**Two blockers for Custom API scoring:**
- MFA required on API authentication -- automated scoring impossible, falls back to MCQ only, meaningful score downgrade
- No DELETE endpoint -- can't scale cleanly, blocker

**Credential Pool viability signals (research):**
- Does the vendor offer sandbox or training-specific accounts?
- Is there API or scripted access to reset account state?
- Is there a partner program or training access program providing dedicated credentials?
- Licensing cost per pool credential

**Platform infrastructure distinction (do not confuse these):**
- Cloud Subscription Pool = Skillable-managed, backs Cloud Slice, not customer-facing
- Cloud Credential Pool = customer/vendor-managed, distributes pre-loaded credentials, reset is separate
- Custom API = no pool, vendor API handles lifecycle per-learner

---

## Gate 3 -- Two-Question Model

Gate 3 (now Training Commitment + Organizational DNA in the Customer Fit pillar) should evaluate two separate questions:

1. **Current capability** -- does the company have a content team that can build and maintain labs today? Signal hierarchy: job postings, LMS, certification program, ATP program, dedicated learning portal, existing labs.

2. **Organizational DNA** -- even if capability doesn't exist today, does this company have the organizational DNA to build it? Because the product need may be compelling enough to drive investment.

DNA signals (different from capability signals):
- Fast-growing, product-led company investing in technical enablement
- Products so complex that self-service learning is a competitive differentiator
- Early attempts to solve this (basic courses, YouTube series, scattered docs)
- Learning leadership titles suggesting strategic priority, not just support function

Output should reflect both: "Here's what they have today. Here's whether organizational signals suggest they'd invest in what they don't have yet." This changes the seller conversation from "they're not ready" to "they're early -- and here's why the need may drive investment."

### Content Team Maturity Signal Framework

Score against this signal hierarchy, observable from public sources:

**Strong positive signals:**
- Job postings for Lab Author, Instructional Designer, Technical Writer, Training Developer
- Dedicated learning portal (not training buried in a support doc)
- Certification program with exam development, question banks, maintenance
- ATP / Authorized Training Partner program
- LMS in use (Cornerstone, Docebo, Moodle, etc.)
- Existing hands-on labs or sandbox environments

**Moderate signals -- maturity unclear:**
- Small course catalog (5-10 courses)
- Training mentioned on website but no dedicated portal
- "Academy" branding with no visible depth behind it

**Negative signals:**
- Training is a PDF and a YouTube playlist
- No dedicated training leadership titles
- Certification is just a badge with no curriculum
- Partner program exists but training entirely handled by partners

**Flag explicitly:** A company can have a large catalog but outsource all authoring -- content exists but internal capability doesn't. This means they need Skillable PS to build labs, not just the platform. Flag this distinction when evidence suggests outsourced authoring.

---

## Research Engine

### Source Type Classification + Differentiated Fetch Depth

The research engine should classify pages by source type and apply different content fetch limits per type.

- **Marketing / product overview pages** -- light pass. Pull positioning, target audience, product category signals. Low token budget.
- **Documentation sites** -- deep fetch. Deployment guides, admin guides, system requirements, architecture docs. 2-3x token budget vs. marketing pages.
- **API reference pages** -- most intensive. REST API docs, OpenAPI/Swagger specs, SDK references. Highest token budget. Look for: lifecycle coverage (create/configure/validate/delete), authentication model, DELETE/teardown endpoint, pagination/rate limits.

Current engine fetches all pages at roughly equal depth. API reference pages may be truncated at the same limit as a marketing page -- missing DELETE endpoints, auth details, or rate limits that are critical for scoring.

### Targeted OpenAPI / Swagger Spec Queries

Add explicit search queries targeting OpenAPI/Swagger specifications for each product.
- These specs are often indexed separately from general API docs
- They contain the most structured evidence for REST API coverage
- Search patterns: `{product} openapi spec`, `{product} swagger.json`, `{product} api reference openapi`

### Documentation Breadth Cataloging for Program Sizing

When fetching doc sites, explicitly build a structural complexity map using four observable signals:

1. **Modules** -- count from doc site navigation. Each module = a potential lab series anchor. Number of modules is a direct proxy for program scope.
2. **Features per module** -- depth within each module. A module with 30 features is a series; a module with 3 is a single lab.
3. **Options/steps per feature** -- requires reading actual procedures. Features with 15 configuration steps and decision points = high lab value. Single-toggle features = low lab value.
4. **Interoperability** -- integrations with other products/systems. Each integration = its own lab scenario. High interoperability multiplies program scope AND often requires multi-VM topologies.

These four signals produce a structural complexity map that feeds scoring, program scope estimation, and Designer's lab architecture decisions.

**Key principle:** Complexity and lab value are positively correlated. More modules + deeper features + richer workflows + higher interoperability = larger program opportunity.

**Explicit disqualifier -- consumer apps and wizard-driven UIs:** Products where errors have no meaningful consequence score LOW regardless of feature count. If getting it wrong doesn't matter, the learner needs a tutorial, not a lab.

### Search API Upgrade Path

The research engine currently uses DuckDuckGo HTML scraping for web searches (~40 queries per analysis). This works for testing and low-volume internal use.

**Current risks:** Fragile HTML scraping, no SLA, potential rate limiting under parallel load.

**Upgrade trigger:** When the tool sees regular use (more than ~50 analyses/month) or reports search failures/empty results.

**Recommended options:**
- **Brave Search API** -- best default upgrade. Free tier covers 2,000 queries/month (~50 analyses free), then $3/1,000 queries (~$0.12/analysis). One small code change in the research module.
- **Serper** -- cheapest if Google results are preferred ($0.001/query, ~$0.04/analysis).
- **Tavily** -- worth considering if page-fetching becomes a bottleneck (returns content in search results, could eliminate the parallel page fetch step entirely).

---

## Lab Platform Detection

### Product-level compete query is incomplete
**Issue:** The product-level query only searches for CloudShare, Instruqt, and Appsembler. Missing: Skytap, Kyndryl, GoDeploy, Vocareum, ReadyTech, Immersive Labs, Hack The Box, TryHackMe, ACI Learning, DIY signals, and all Skillable domains.
**Fix:** Align the product-level compete query with the full company-level competitor list.

### Discovery prompt doesn't extract Skillable as a lab partner
**Issue:** The `existing_lab_partner` extraction instructions list competitors but do not include Skillable, labondemand.com, or learnondemandsystems.com as values to extract. Structured extraction may not capture it in the right field.
**Fix:** Add Skillable (and legacy brand signals) to the extraction instructions.

### Domain-based detection for stronger evidence
**Concept:** When researching a company, look for outbound links from the company's own properties (website, support docs, training pages) that point to lab platform domains. An actual URL link is stronger evidence than a name mention.
**Status:** Not currently implemented. Explore feasibility during refactor.

---

## Single Canonical Lab Platform List

### One list, referenced everywhere
**Issue:** The company-level and product-level research queries maintain separate, inconsistent lists of competitors. This guarantees drift.
**Principle:** One canonical list of all lab platform providers (Skillable + all competitors + DIY), maintained in a single location, referenced by both company-level and product-level research queries, by the discovery extraction prompt, and by the badging framework. When a new competitor is identified, add it once, and it propagates everywhere.
**Applies to GP4 (Self-Evident Design) and GP5 (Intelligence compounds).**

---

## Delivery Path Recommendations

### Collaborative Lab Detection -- Two Patterns

Inspector should detect and flag Collaborative Lab potential as a Delivery Path signal -- not a scoring change. Applies to cybersecurity and multi-role pipeline products especially.

**Pattern A -- Parallel / Adversarial (Cyber Range)**
- Detection signals: Red Team / Blue Team, cyber range, SOC ops, incident response, penetration testing, network security operations, multi-role attacker/defender scenarios
- Also applies when: the lab can simulate attacks against a defended environment -- learners don't need an external attacker; the lab environment itself generates the attack traffic
- Recommendation framing: "Standard VM for self-paced and cert prep; Collaborative Lab for team-based ILT cyber range events"

**Pattern B -- Sequential / Assembly Line**
- Detection signals: data pipeline workflows (ingest to transform to analyze), data science/engineering/analysis stack, DevOps multi-role handoffs, SDLC pipeline stages, any product with clearly documented role-based handoff workflows
- Program design implication: assembly line labs signal role-specific track need AND a connecting scenario -- multiplies program scope
- Recommendation framing: "Role-specific tracks for self-paced; Assembly Line Collaborative Lab for ILT scenarios connecting roles end-to-end"

**Rules:**
- Always additive -- recommend alongside standard VM labs, not instead of them
- ILT/vILT only -- flag this constraint explicitly when recommending
- Flag as a named delivery option in the Delivery Path recommendation with rationale

### Break/Fix (Fault Injection) Scenario Detection

Inspector should detect and recommend break/fix scenarios as a named lab type when research signals are present. Not a delivery pattern -- runs on standard VM infrastructure.

**Detection signals:** Troubleshooting content in product docs, advanced certification content testing diagnostic skills, incident response training, high Product Complexity products (consequence of error signal), products with complex failure modes (networking, security, infrastructure, database, SRE/DevOps).

**Recommendation framing:** Flag alongside guided labs as an additive scenario type. "Guided labs for initial skill-building; break/fix scenarios for advanced learners and certification prep -- diagnostic reasoning in a realistic fault environment."

### Simulated Attack Scenario Detection

Inspector should detect and recommend simulated attack scenarios for cybersecurity products -- in both single-person and Collaborative Lab contexts.

**Single-person (self-paced):** Lab environment runs attack scripts or generates malicious traffic; solo learner detects, investigates, remediates. No human Red Team needed.

**Collaborative Lab (ILT):** Live Red Team participants attack while Blue Team defends. Human adversaries, concurrent action, shared environment.

**Detection signals:** SIEM, EDR, identity protection, threat detection, network security, incident response, threat hunting, penetration testing, Red/Blue Team references, SOC operations, attack surface documentation.

**Program recommendation for cybersecurity products (when signals present):**
- Self-paced track: guided labs + break/fix + simulated attack (single-person)
- ILT track: cyber range with live Red/Blue Team (Collaborative Lab)
- Recommend both tracks together as a complete cybersecurity program

### Delivery Path Rationale -- Always Explain WHY

The Delivery Path recommendation must never just state the recommendation. It must make the case in terms the SE can use in a customer conversation. Two specific displacement scenarios require explicit rationale:

**VMware to Hyper-V:**
- Rationale: Broadcom's post-acquisition pricing has made VMware substantially more expensive to deliver at scale
- Customer impact: equivalent or better technical capability at meaningfully lower cost
- If customer has existing VMware-based labs (with Skillable or a competitor), call this out explicitly as a cost advantage

**Docker to Hyper-V:**
- Rationale: reliability, full Windows support, complex networking, nested virtualization, no pre-baking constraint for large images
- When a product could run in Docker but Hyper-V is the better choice, explain why -- not just assert it

### Docker Non-Recommendation Cases -- Tighten the Criteria

Four explicit disqualifiers to add:

1. **Development-use Docker images are not a lab path** -- many enterprise products publish Docker images for local dev testing only. Presence of a Docker Hub image is NOT automatic confirmation of Docker as the lab path. Research must determine whether the image represents the full product experience.
2. **Windows GUI requirement** -- Docker on Skillable is Linux containers accessed via browser/noVNC. Any product requiring a rich Windows desktop experience is disqualified from Docker.
3. **Multi-VM network complexity** -- networking products and anything requiring private VLANs, real routing protocols, or multi-device topologies needs Hyper-V. Docker's networking model is insufficient.
4. **Definition of "genuinely container-native"** -- product is designed to run as a container in production, accessed via web browser, with no Windows dependency and no multi-VM network requirements.

---

## Consumption Potential Improvements

### Azure/AWS Consumption Costs Are Separate

Make the distinction explicit in output:
- Skillable's $6/hr Cloud Slice rate is platform overhead only -- it does NOT include Azure or AWS service costs
- Azure/AWS service costs are billed separately through the customer's own cloud subscription
- Inspector's output should note this distinction when recommending Cloud Slice path -- so AEs don't inadvertently present an understated cost to customers

### Complexity Drives Rate Tier and Seat Time

The complexity map should directly inform three Consumption Potential inputs:

1. **VM topology estimate** -- single VM (simple workflows) vs. multi-VM with networking (complex/interoperable products)
2. **Rate tier selection** -- standard VM ($12-15/hr) vs. large/complex VM ($45-55/hr); complexity signals should determine this, not a default assumption
3. **Seat time per lab** -- simple workflows = 30-45 min; deep multi-step admin workflows = 60-90 min

**Product category priors:**

| Category | Typical VM Count | Rate Tier | Seat Time |
|---|---|---|---|
| Networking (Cisco, Fortinet, F5, Juniper, Aruba) | 2-6 VMs | Complex ($45-55/hr) | 60-90+ min |
| Cybersecurity (SIEM, EDR, identity, threat detection) | 2-5 VMs (can burst to 15) | Complex ($45-55/hr) | 60-90 min |
| Data science / data engineering | 2-4 VMs | Complex ($45-55/hr) | 75-120 min |
| Enterprise server software (backup, monitoring, ITSM) | 2-3 VMs | Standard-Complex ($15-45/hr) | 45-75 min |
| Developer tools / IDEs / CI-CD | 1-2 VMs or Docker | Standard ($12-15/hr) | 30-60 min |
| Single-product admin (standard enterprise software) | 1-2 VMs | Standard ($12-15/hr) | 45-60 min |

**Rule:** When product category is identified, default to the category prior. Do not require evidence to explicitly prove multi-VM topology for networking or cybersecurity products -- the category IS the evidence. Override only if specific research signals contradict the prior.

### Doc Breadth as Program Sizing Signal

Update scoring to explicitly:
1. Use documentation breadth and depth as the primary evidence for Product Complexity
2. Surface multi-program curriculum potential when doc breadth is high
3. Frame complexity positively -- the more complex the product, the stronger the case for labs AND the bigger the program opportunity

A deeply complex product doesn't justify one lab -- it justifies a curriculum (onboarding, role-specific, advanced config, troubleshooting, certification prep). This should be reflected in recommendations, not just the score.

---

## Product Complexity Detection

### Consumer Grade and Simple UX detection
**Signals to research:**
- Is the product marketed to consumers or professionals?
- Does the product have configuration, administration, or deployment workflows?
- Is there documentation depth beyond getting-started guides?
- Does the product have multiple user roles with distinct workflows?
- Are there certification programs or formal training (strong counter-signal -- if someone certifies on it, it's not simple)?
- Is there a consequence of error, or is everything undo-able?
**Confidence:** If research clearly confirms consumer/simple (e.g., mobile-only app, drag-and-drop builder with no admin layer), badge is red. If inferred from limited signals, badge is amber.

---

## Lab Versatility Detection

### Product-type to lab-type mapping must be in the code
Lab Versatility badges are selected by the AI based on what fits the specific product -- not dumped by category. The mapping of product types to likely lab types must be encoded in the research logic so the AI knows what to look for.

**Mapping:**

| Badge | Likely product types |
|---|---|
| Red vs Blue | Cybersecurity -- EDR, SIEM, network security |
| Simulated Attack | Cybersecurity -- any defensive product |
| Incident Response | Infrastructure, security, cloud, databases |
| Break/Fix | Broad -- any product with complex failure modes |
| Team Handoff | DevOps pipelines, data engineering, SDLC |
| Bug Bounty | Development platforms, data, security |
| Cyber Range | Network security, SOC operations |
| Performance Tuning | Databases, infrastructure, cloud, data platforms |
| Migration Lab | Enterprise software, cloud, infrastructure |
| Architecture Challenge | Cloud, infrastructure, networking, data |
| Compliance Audit | Healthcare, finance, security, any regulated |
| Disaster Recovery | Infrastructure, cloud, data protection, databases |

**Rules:**
- AI picks at most 1-2 badges per product based on specific product research, not category
- Most simple products get none -- that's correct
- The same intelligence feeds Designer for program recommendations
- Lab concepts in the product card provide the specific detail; badges provide the headline

---

## Inspector Operational Improvements

### Top Blockers List

Track companies/products that are undeliverable by specific blocker type. This creates a persistent record of what blocks deals and why, enabling pattern detection across the pipeline. When the same blocker appears repeatedly (e.g., "no DELETE endpoint" across multiple SaaS products), it becomes actionable intelligence for product and partnership conversations.

### Competitive Capture to Prospector Feed

Auto-document competitors discovered during Inspector Case Board analysis and feed them into Prospector. When Inspector finds that a company's products compete with products already proven to be strong Skillable fits, those competitors become Prospector targets automatically. This is GP5 (Intelligence Compounds) in action -- every Inspector analysis enriches Prospector's target universe.

### Score Calculation Deduplication

Currently 6 copies of score computation logic exist. Consolidate into a single function in the Intelligence layer, called by all consumers. This is a prerequisite for reliable scoring and a direct application of the Define-Once principle.

### Replace print() with logging

Replace all `print()` calls with the `logging` module. Enables log level filtering, structured output, and production-ready diagnostics.

---

## Prospector Improvements

### ABM Second Contact Column

Add a second contact column to Prospector output: decision maker + champion, stacked in one cell. Sellers need both the person who signs and the person who champions internally.

### Academic Institution Support

Own discovery queries, scoring model, path labels, contact targeting for academic institutions.
- Anchors: GCU, WGU, St. Louis University, Saxion University (Netherlands)
- Contacts: Faculty leads, Curriculum Development Directors, Dean/Dept Head of Engineering or Technology school, Ed Tech director
- Pre-filter: must have meaningful engineering/tech/computing/cybersecurity program to proceed

### ZoomInfo CSV Column Mapping

Map ZoomInfo CSV columns to platform fields so redundant research can be skipped when ZoomInfo data is already available. Reduces API/search costs and speeds up batch scoring.

### Parallelize Product Discovery Searches

Next meaningful speed gain: parallelize searches within the product discovery step. Currently sequential, creating a bottleneck for batch scoring.

### Document Volume Limits

Clearly document capacity constraints for Marketing. What does "up to 25 companies" mean? What happens when they need more? Marketing needs to plan around real limits.

### Certification Demand as Market Demand Signal

Future consideration: if certification volume data becomes reliably researchable (number of certified professionals, exam volume trends), add as a separate Market Demand signal alongside the existing Certification Program badge. Held for now because research cannot reliably surface volume numbers.

---

## Designer Improvements

### Scenario Seeds in Lab Blueprint

Scenario seeds were removed from Phase 1 blueprint temporarily. Restore as a 7th item once real-world scenario collection UX is designed. Store as bullet items (same pattern as objectives/audience). Likely populated by Intelligence from Inspector analysis.

### Intelligence-Driven Phase 1 Prompting

When a program has company_name/analysis_id, the AI proactively offers to show company product list, module/feature depth from Inspector analysis, and persona assumptions -- rather than asking from scratch. Inspector intelligence should pre-populate Designer's starting context.

### Style Guide Content Injection

Currently only the style guide name is injected into Phase 3 context; Claude uses training data to apply the guide. Wire actual file content from the standards library into context per selection. Priority: Apple Style Guide PDF first, then DigitalOcean, Red Hat, Microsoft.

### Skill Framework Taxonomy Files

Capture and store skill framework files: NICE NCWF (NIST spreadsheet, freely available), DoD DCWF (DoD spreadsheet), DoD 8570/8140 (baseline qualification tables). SFIA and ITIL 4 require licenses for full content -- summaries only for now.

### Standards Catalog API

Build a `/standards/catalog` API route that returns a JSON catalog of available standards (slug, display name, type, file content available). Enables any tool (Inspector, Designer, Prospector) to query without hardcoded lists in templates.

### CSS Color Correction

Replace legacy color values (#00D082/#033c23) with confirmed Skillable brand palette (#0A3E28 sidebar, #136945 Skillable green, #24ED98 accent/interactive).

---

## Infrastructure Improvements

### Render Deployment

Push to GitHub with auto-deploy to Render. Unblocks others from testing the platform without running locally.

### SQLAlchemy ORM / Database Migration Path

Currently JSON files. Plan was SQLite then Azure SQL. Decision needed on when data volume justifies migration. The ORM layer should be built regardless so the storage backend can be swapped without rewriting queries.

### Route File Split

`app.py` is 1,000+ lines. Split into per-tool route files (inspector_routes.py, prospector_routes.py, designer_routes.py) + shared core. Improves maintainability and reduces merge conflicts.

### Centralize Skillable-Specific Knowledge

Delivery patterns, scoring rules, scenario type detection logic -- currently embedded in prompts. Extract into an Intelligence knowledge module so the same knowledge is available to all tools and to the prompt generation system.

---

## WCAG AA Accessibility Check

### Automated contrast ratio validation
**Requirement:** All text/background color combinations must pass WCAG AA (4.5:1 normal text, 3.0:1 large text). Run contrast checks as part of QA before any UX deployment.
**Implementation:** Build a script or integrate into the build process that validates all CSS color pairs against WCAG AA thresholds. Flag any combination below 4.5:1 for normal text or 3.0:1 for large text.
**When Designer becomes customer-facing:** Consider a formal WCAG audit and compliance statement.

---

## In-App Documentation Linking

### Documentation as the explainability layer
**Principle:** The Badging and Scoring Reference documentation serves double duty -- it's both the developer/AI reference AND the in-app help system. Each section of the UX links to the corresponding section of the documentation.
**Implementation:**
- Each major section in the Badging and Scoring Reference needs an anchor tag the UX can link to
- Documentation must be written clearly enough for a seller to understand, not just developers
- Section-level linking, not badge-level -- one click shows the whole section for that part of the UX
- Pillar card headers have two icons: info icon (?) and doc icon (document SVG) -- same size, muted color, green on hover
- Seller Briefcase sections each have an info icon linking to relevant framework documentation
- When documentation is updated, in-app help updates automatically -- same source
- Keep it digestible -- each section should be a standalone explainer
- Strategic placement at section level only -- don't clutter the UX

---

## LMS / LXP Detection

### Surface the specific LMS platform name
**Current:** The badging framework has a generic "LMS / LXP" badge.
**Improvement:** Badge should display the specific platform name (Docebo, Cornerstone, Moodle, etc.) -- same variable-driven principle as lab platform badges. Docebo and Cornerstone are Skillable partners and should be green. Skillable TMS is green -- our own platform.

---

## UX Implementation Notes

### Dimension Name Display
All dimension names render in ALL CAPS in the UX (e.g., PROVISIONING, LAB ACCESS, PRODUCT COMPLEXITY). This is a display convention -- the data model uses normal casing.

### Score Bar Styling
Score bars within Pillar cards use a gradient green/amber fill based on the dimension score. WCAG AA compliant.

### Cache and Navigation
- Cache date shown as a hoverable link with "Refresh cache" tooltip
- Two navigation links: "Back to Product Selection" and "Search Another Company"

### Export
Word export (not PDF) -- sellers can customize the document for their conversations.

### Product Selector Dropdown
In the hero section, the product selector shows: product name (left-aligned, truncated at ~40 chars), score, and purple subcategory badge.

---

## Decisions Still Needed

These items are tracked but require conversations or alignment before implementation:

| Item | Context |
|---|---|
| **Auth** | Not urgent yet; revisit when platform goes beyond internal Skillable use |
| **Azure SQL vs. SQLite** | When does data volume justify the migration? |
| **Diff/Refresh architecture** | "Refresh Partnership" and "Re-score Products" buttons -- still wanted? |
| **Inspector to Designer handoff button** | Timing tied to Designer readiness; confirmed analysis_id carries data into Phase 1 |
| **HubSpot write-back field mapping** | Stage 1 to Company Record, Stage 2 to Deal Records -- exact field mapping TBD with RevOps |
| **HubSpot integration thresholds** | Score threshold for auto-create/update; needs RevOps conversation |
| **Benchmark gaps** | Middle-tier, Eaton BrightLayer, SaaS near-miss, GSI/training org anchors -- needs SE conversations |
| **Prospector UX location** | Where do Marketers interact? What triggers a run? Needs RevOps + Marketing alignment |
| **ICP Discovery mode** | Criteria-based company discovery -- main challenge is resource management at scale |
| **Designer export format** | What exactly goes in the ZIP, what format is the BOM, what does the "environment template" look like |
| **Designer collaborative lab BOM** | How collaborative lab network setup, credential pools, and subscription pools surface in Phase 4 BOM |
| **Designer first-run onboarding** | How much does Skillable pre-populate vs. customer configures in Preferences |
| **Designer AI persona name** | "Neo" used throughout but not explicitly confirmed -- keep, rename, or replace with generic |
