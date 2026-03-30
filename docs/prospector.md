# Skillable Intelligence — Prospector

> Prospector is the batch-analysis tool in the Skillable Intelligence platform. It takes a list of companies and produces a ranked table of labability fit, surfacing the highest-potential accounts for outreach or deeper Inspector analysis.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md).

---

## 1. What Problem Does Prospector Solve?

Marketing and field teams typically work from large TAM lists — databases of hundreds or thousands of companies within a target vertical or segment. Without a systematic way to prioritize these, there is no mechanism for distinguishing companies whose products are genuinely good candidates for Skillable's lab platform from those that are a poor fit. The result is wasted outreach cycles and campaigns built on undifferentiated lists.

Without qualification, every company on a list receives the same pitch regardless of whether their product is technically labable, whether they already have a training ecosystem in place, or whether they have any organizational readiness to adopt a lab-based learning motion. This is inefficient for field teams and creates noise in pipeline metrics — high-activity, low-conversion outreach that obscures where real demand exists.

Prospector addresses this by running a lightweight version of Inspector's research pipeline across a batch of companies in parallel. Each company is analyzed using the same discovery-phase searches that Inspector uses — surfacing deployment model, training ecosystem, partner program, certification structure, and existing labs — then scored on both product labability and organizational readiness. The output is a ranked table of composite scores that sales and marketing can use immediately to prioritize outreach, build ABM target lists, identify accounts ready for a full Inspector analysis, and eliminate known poor-fit companies from future runs.

The Prospector → Inspector handoff is a first-class workflow. Every row in Prospector's results table links directly to a full Inspector report if one exists, and if it doesn't, clicking the link pre-fills the Inspector home screen for a one-click deep-dive. The intended flow is: Prospector surfaces the top 3–5 accounts from a batch, then Inspector goes deep on those.

---

## 2. Personas

### Marketing / Demand Generation

Marketing and demand generation teams use Prospector to build a prioritized target list for a campaign or ABM motion. They typically start with a large unqualified list — purchased from ZoomInfo, pulled from a vertical database, or assembled from event registrations — and need to reduce it to a set of high-confidence targets before investing in campaign spend or content personalization.

**Needs:** Ranked composite score table, top contact name and LinkedIn URL, CSV or Excel export for upload into Salesforce or HubSpot.

**Typical triggers:** New vertical initiative, event list qualification, quarterly pipeline build.

### Account Executive / SDR

AEs and SDRs use Prospector to qualify a cold list before investing outreach time. Rather than working through a list sequentially and discovering poor-fit companies through failed conversations, they run the list through Prospector first and direct their energy at accounts with strong labability and organizational readiness signals.

**Needs:** Composite score, "Labable / Simulations / Do Not Pursue" Skillable Path signal, top contact title to confirm they're reaching the right person.

**Typical triggers:** Post-conference attendee list, SDR prospect list from ZoomInfo or LinkedIn Sales Navigator.

### Solution Engineer (light use)

SEs use Prospector for lightweight account scanning ahead of team planning sessions. Rather than pulling full Inspector reports on a large set of accounts, they run a batch scan to see which accounts already have high scores (and therefore existing Inspector reports) and which need deeper attention.

**Needs:** Composite signal per account, direct link to full Inspector analysis for high-scoring accounts.

**Typical triggers:** Territory planning, partner QBR prep, pre-sales team review.

---

## 3. The Prospector Workflow

### Input

Prospector accepts companies in two modes:

- **Paste mode:** Comma-separated or newline-separated company names pasted directly into the input box.
- **CSV upload:** First column is used as the company name list; a header row containing the word "company" is automatically skipped.

The batch limit is **25 companies per run**. A **"Force refresh"** checkbox bypasses both the full analysis cache and discovery cache, forcing fresh web research for every company in the batch regardless of cached results.

### Analysis Pipeline (per company)

Each company goes through a lightweight research-and-score pass:

1. **Discovery phase** — Runs the same 12 parallel web searches as Inspector Phase 1, covering company overview, product overview, deployment model, training programs, certification structure, partner programs, API and developer ecosystem, pricing model, existing hands-on labs, gray market labs, technical documentation, and market context.
2. **Product selection** — Automatically selects the single highest-labability product from discovery output. No selection interface is presented. If multiple products are in the `highly_likely` tier, the first one returned by the model is used.
3. **Lightweight scoring** — Scores the selected product from discovery context only, without Phase 2 deep research. Produces the same `ProductLababilityScore` data model as Inspector, but from shallower evidence.
4. **Lab Maturity scoring** — Runs the same organizational readiness model as Inspector, from discovery context.
5. **Composite scoring** — Applies the same formula and gating rules as Inspector (see [intelligence-platform.md](intelligence-platform.md) §5.4).
6. **Contact extraction** — Surfaces the top 2 contacts for outreach.

**What Prospector skips compared to Inspector:**

- No interactive product selection step (always takes the top product automatically)
- No Phase 2 deep research (9-query product-specific search batch)
- No per-product page fetches (technical docs, API references, Docker Hub, Marketplace listings)
- No Consumption Potential model
- No per-product recommendations (Delivery Path, Scoring Approach, Essential Technical Resource)

**Why the lighter pass is still valid:** Discovery searches surface the most important signals — deployment model, training ecosystem, partner program, and existing labs. These are sufficient to rank companies by relative fit. The score will be less precise than a full Inspector score, and Technical Orchestrability scores in particular tend to be conservative because that dimension benefits most from Phase 2 deep research. But the composite score is directionally accurate enough for prioritization.

### Concurrency and Throughput

- Up to **6 companies** are analyzed in parallel, controlled by a semaphore.
- **Per-company timeout: 3 minutes (180 seconds).** Companies that exceed this are marked as skipped and processing continues with the rest of the batch.
- A 25-company batch typically completes in **5–8 minutes** depending on API response times.
- Progress is streamed live via SSE. Each company progresses through states: `waiting → analyzing → done / cache / timeout`. Cache hits display a date stamp ("From cache — 3/15/2026"). Timeouts display a skipped indicator with the company name.

### Caching

Prospector participates in the shared platform cache (see [intelligence-platform.md](intelligence-platform.md) §4 for cache infrastructure details):

- **Full analysis cache (45 days):** If Inspector has already scored a company, Prospector uses that cached result instantly — no web research is performed for that company.
- **Discovery cache (45 days):** If a discovery pass has been run recently (by Prospector or Inspector), the product list and discovery context are reused, skipping Phase 1 searches.
- Cache hits are shown with a date stamp in the progress view so analysts know how fresh the data is.

### Results Table

Results are sorted by composite score descending. The table columns are:

| Column | Description |
|---|---|
| **Rank** | Position in composite score order (1 = highest) |
| **Company** | Company name, linked to company URL |
| **Product Counts** | Counts of products by labability tier: Highly Labable / Likely / Not Labable |
| **Top Product** | Name of the highest-scoring product analyzed |
| **Lab Score** | Labability score of the top product (0–100), color-coded green / amber / red |
| **Skillable Path** | For software: "Labable", "Simulations", or "Do Not Pursue". For academic: school name or "Academic — High Potential" / "Academic — Emerging" / "Not a Fit" |
| **Lab Maturity** | Organizational readiness score (0–100) |
| **Composite** | Weighted combination of Lab Score and Lab Maturity (0–100) |
| **Partnership Signals** | Checkmarks or counts for: ATP Program, Channel Program, Existing Lab Partner, ILT/vILT, On-Demand, Certifications, Gray Market |
| **Contact 1** | Name, title, LinkedIn URL |
| **Contact 2** | Name, title, LinkedIn URL |
| **Score Report** | Link to full Inspector analysis (if cached), or pre-filled Inspector link for a one-click deep-dive |

### Path Labels

**Software companies:**

- Lab Score ≥ 50 → **"Labable"** (with delivery sublabel: Cloud Slice / Custom API / VM Lab based on Skillable Path)
- Lab Score ≥ 20 → **"Simulations"**
- Lab Score < 20 → **"Do Not Pursue"**

**Academic institutions:**

- No technology programs found → **"Not a Fit"**
- Has technology programs, school is a known Skillable anchor → **School name displayed**
- Has technology programs, high score → **"Academic — High Potential"**
- Has technology programs, lower score → **"Academic — Emerging"**

### Flagging Poor-Fit Companies

Any row in the results table can be flagged as a poor fit with a brief reason. Flagged companies are excluded from all future Prospector runs — they are filtered out before analysis begins so no API calls are wasted on known non-candidates.

Flagged companies appear in a **"Skipped"** section at the bottom of the results page with their reason and the date flagged. The flag record includes: company name, reason text, UTC timestamp, and the job ID where the flag was created.

---

## 4. Components

### 4.1 Batch Job Manager

**Purpose:** Coordinate parallel analysis across a list of companies without overwhelming the API or blocking the UI.

**Implementation:** Each company in the batch is submitted as a background thread. A semaphore limits concurrency to 6 simultaneous analyses. Per-company timeout enforcement uses `concurrent.futures.wait()` with a 180-second timeout parameter. Companies that exceed the timeout are marked as `skipped` with a timeout reason, and the batch loop continues with remaining companies.

**Cancellation:** A cancel endpoint (`POST /prospector/cancel/<job_id>`) sets a cancellation flag on the job. The batch loop checks this flag before initiating analysis on each new company. Companies already in-flight at cancellation time are allowed to complete or timeout normally.

**Progress tracking:** Uses the same SSE infrastructure as Inspector (see [intelligence-platform.md](intelligence-platform.md) §4). SSE messages distinguish between cache hits (with date), active analyses, timeouts, and errors, so the UI can render appropriate per-company state indicators.

### 4.2 Discovery Engine (shared with Inspector)

**Purpose:** Resolve the company's products and partnership signals from public sources.

See [intelligence-platform.md](intelligence-platform.md) §3 for the full Research Engine description. Prospector runs the same 12-query discovery pass as Inspector Phase 1, covering the same search intents and using the same evidence extraction model.

**Prospector-specific behavior:** After discovery completes, Prospector takes the single top product — the one ranked highest by labability tier — rather than presenting a product selection interface to the user. If multiple products share the `highly_likely` tier, the first one returned by the model is used. This selection is logged in the job record so analysts can see which product drove the score.

### 4.3 Lightweight Scorer

**Purpose:** Produce a calibrated labability and maturity score from discovery-level context only, without the deep per-product research that Inspector's Phase 2 provides.

**Input:** Discovery output — search result summaries, fetched content from the company homepage, top product pages, training and partner program pages.

**Output:** The same `ProductLababilityScore` and `LabMaturityScore` data models as Inspector, but derived from shallower evidence. The scoring prompt is identical to Inspector's; the difference is in the evidence fed into it.

**Why scores may differ from Inspector:** Inspector's Phase 2 adds 9 product-specific searches plus fetched content from technical documentation, API reference pages, and Docker Hub. These sources frequently unlock Technical Orchestrability evidence — containerization signals, REST API coverage, SDK availability — that discovery-level searches do not reliably surface. Expect Prospector's Technical Orchestrability dimension to be conservative relative to a full Inspector score. The other dimensions (Content Richness, Training Ecosystem, Market Reach) are less affected by the lighter pass.

### 4.4 Composite Score Engine (shared with Inspector)

**Purpose:** Combine Product Labability and Lab Maturity into a single ranking signal for the results table.

See [intelligence-platform.md](intelligence-platform.md) §5.4 for the full formula, weight definitions, and gating rules. Prospector uses the same weights and gating rules as Inspector with no modifications.

### 4.5 Contact Extractor

**Purpose:** Surface the two most relevant contacts per company so the results table is immediately actionable for outreach.

**Selection logic:**

- **Academic institutions:** Prefers contacts with titles containing faculty, curriculum, dean, or registrar.
- **Software companies:** Prefers `decision_maker` role type first (VP Training, Director of Learning, Head of Technical Education), then `influencer` or `champion` roles.

**Output:** Name, title, and LinkedIn URL for the top 2 contacts. If fewer than 2 contacts are found, available fields are populated and missing fields are left blank rather than substituting lower-quality contacts.

### 4.6 Results Table and Export

**Purpose:** Deliver a ranked, actionable table that can be used directly in the platform or exported into a CRM or marketing automation tool.

**Export formats:**

- **CSV:** 26 columns, filename pattern: `Prospector-{YYYY-MM-DD}-{count}-{job_id[:6]}.csv`
- **Excel (.xlsx):** Same 26 columns, professionally styled for direct delivery to stakeholders:
  - Header row: dark background (`#06100C`), centered text, frozen pane
  - Data rows: dark background (`#0D1A14`)
  - Score column coloring: Green (`#24ED9B`) for scores ≥ 70, Amber (`#F59E0B`) for scores ≥ 40, Red (`#F87171`) for scores < 40

### 4.7 Poor-Fit Registry

**Purpose:** Prevent known poor-fit companies from re-entering future Prospector runs, keeping batches focused on genuinely qualified targets.

**Implementation:** Flagged company names are stored in a persistent poor-fit list. On each new Prospector run, the input list is filtered against this registry before analysis begins, using a case-insensitive match. Filtered companies never consume API calls or semaphore slots.

**Flag data stored per entry:** Company name, reason text (free-form, entered by the analyst), UTC timestamp of flag creation, and the job ID where the flag was created. This record is available for audit and can be reviewed or cleared by platform administrators.

**Results presentation:** A collapsible "Skipped" section at the bottom of the results page lists all companies filtered by the poor-fit registry, along with their flag reason and date, so analysts can confirm the right companies were excluded.

---

## 5. Prospector vs. Inspector — When to Use Which

| Signal | Use Prospector | Use Inspector |
|---|---|---|
| You have a list of 5–25 companies to prioritize | ✓ | |
| You're building an ABM target list | ✓ | |
| You want a fast directional signal on an account | ✓ | |
| You've already Prospected and want to go deeper | | ✓ |
| You need a Delivery Path recommendation | | ✓ |
| You need consumption or revenue estimates | | ✓ |
| You're preparing for a discovery call | | ✓ |
| You need an Essential Technical Resource question | | ✓ |
| You want to seed Designer with scoring context | | ✓ |

---

## 6. Prospector → Inspector Handoff

Every row in Prospector's results table includes a **Score Report** link in the final column. If Inspector has already scored the company (cache hit), this link opens the full Inspector results page directly. If no Inspector analysis exists for the company, clicking the link pre-fills the Inspector home screen with the company name for a one-click deep-dive — no manual entry required.

This handoff is the intended flow. Prospector is not meant to replace Inspector; it is meant to focus it. Run a 25-company batch, identify the top 3–5 accounts by composite score and Skillable Path signal, then use Inspector to build the full evidence-backed analysis on those accounts before investing SE time or crafting a tailored pitch.

---

*Last updated: 2026-03-30*
*Maintained by: Skillable Intelligence platform team*
