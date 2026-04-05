# Research Methodology Improvements

Items identified during the Platform Foundation conversations that should be addressed when refactoring the research and detection logic. These are implementation improvements, not foundation-level decisions.

---

## Prompt Generation System — Implementation Requirements

### Overview
Replace the static product_scoring.txt with a three-layer prompt generation system: Configuration + Template = Generated Prompt at runtime. See Platform-Foundation.md for the full architecture description.

### Build Sequence

| Step | What | Details |
|---|---|---|
| **1. Design the config schema** | Define the structure that holds everything | JSON or Python dataclass. Must be validatable — weights add to 100, all badges have color criteria, no orphan references. |
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
`backend/prompt_generator.py` — single function: `generate_scoring_prompt() -> str`

### What This Replaces
`backend/prompts/product_scoring.txt` — will be deleted after the new system is validated. During transition, both can coexist with a feature flag.

### Future: Admin GUI
When AuthN/AuthZ is implemented, add a web interface for editing the config:
- View/edit all config values
- Validation on save
- Change history with timestamps and user attribution
- Admin-only access
- Changes take effect on next scoring run

---

## Core Principle: Define Once, Reference Everywhere

All Pillar names, dimension names, weights, thresholds, badge names, and vocabulary must be defined in a single configuration layer (likely a config file or constants module) and referenced by every consumer — code, AI prompts, UX templates, documentation generation. Nothing hard-coded. If a name or weight changes, one edit propagates everywhere. This is a core architectural requirement for the refactor.

**What lives in the config layer:**
- Pillar names and weights (Product Labability 40%, Instructional Value 30%, Customer Fit 30%)
- Dimension names and weights within each Pillar
- Badge names and color criteria
- Score thresholds (80/65/45/25) and verdict labels
- Canonical lists (lab platforms, LMS partners, organization types)
- Locked vocabulary (use this, not that)
- ACV rate tables
- Consumption motion labels and adoption ceilings

---

## Core Principle: Confidence Coding

Confidence coding (confirmed / indicated / inferred) must be core logic in the codebase, not just a display convention. Every finding the AI produces must carry a confidence level as a stored field. This confidence level:
- Influences badge color assignment (confirmed evidence can support green; inferred evidence may cap at amber)
- Is stored in the data model alongside the finding itself
- Surfaces in evidence language when displayed
- Is available to downstream consumers (HubSpot ICP Context, Designer, etc.)

This is not optional. It is how the platform achieves GP3 (Explainably Trustworthy) at the code level.

---

## Lab Platform Detection

### Product-level compete query is incomplete
**File:** `backend/researcher.py` line 431
**Issue:** The product-level query only searches for CloudShare, Instruqt, and Appsembler. Missing: Skytap, Kyndryl, GoDeploy, Vocareum, ReadyTech, Immersive Labs, Hack The Box, TryHackMe, ACI Learning, DIY signals, and all Skillable domains.
**Fix:** Align the product-level compete query with the full company-level competitor list.

### Discovery prompt doesn't extract Skillable as a lab partner
**File:** `backend/prompts/discovery.txt` line 98
**Issue:** The `existing_lab_partner` extraction instructions list competitors (CloudShare, Instruqt, Skytap, Appsembler, DIY) but do not include Skillable, labondemand.com, or learnondemandsystems.com as values to extract. Even though Phase 1 research queries look for Skillable signals, the structured extraction in Phase 2 may not capture it in the right field.
**Fix:** Add Skillable (and legacy brand signals) to the `existing_lab_partner` extraction instructions.

### Domain-based detection for stronger evidence
**Concept:** When researching a company, look for outbound links from the company's own properties (website, support docs, training pages) that point to lab platform domains — labondemand.com, learnondemandsystems.com, instruqt.com, cloudshare.com, etc. An actual URL link is stronger evidence than a name mention.
**Status:** Not currently implemented. Explore feasibility during refactor.

---

## Single Canonical Lab Platform List

### One list, referenced everywhere
**Issue:** The company-level and product-level research queries maintain separate, inconsistent lists of competitors. The company-level query has the full set; the product-level query has only three. This guarantees drift.
**Principle:** One canonical list of all lab platform providers (Skillable + all competitors + DIY), maintained in a single location (likely constants.py or a config file), referenced by both company-level and product-level research queries, by the discovery extraction prompt, and by the badging framework. When a new competitor is identified, add it once, and it propagates everywhere.
**Applies to GP4 (Self-Evident Design) and GP5 (Intelligence compounds).**

---

## Product Complexity Detection

### Consumer Grade and Simple UX detection
**Context:** Consumer Grade and Simple UX are red/amber badges within the Product Complexity dimension (Instructional Value pillar). The AI needs strong detection logic to determine when a product is too simple for labs.
**Signals to research:**
- Is the product marketed to consumers or professionals?
- Does the product have configuration, administration, or deployment workflows?
- Is there documentation depth beyond getting-started guides?
- Does the product have multiple user roles with distinct workflows?
- Are there certification programs or formal training (strong counter-signal — if someone certifies on it, it's not simple)?
- Is there a consequence of error, or is everything undo-able?
**Confidence:** If research clearly confirms consumer/simple (e.g., mobile-only app, drag-and-drop builder with no admin layer), badge is red. If inferred from limited signals, badge is amber. The evidence confidence language (confirmed/indicated/inferred) applies here.

---

## Lab Versatility Detection

### Product-type to lab-type mapping must be in the code
**Context:** Lab Versatility badges are selected by the AI based on what fits the specific product — not dumped by category. The mapping of product types to likely lab types must be encoded in the research logic so the AI knows what to look for.
**Mapping (encode in research prompts and/or constants):**

| Badge | Likely product types |
|---|---|
| Red vs Blue | Cybersecurity — EDR, SIEM, network security |
| Simulated Attack | Cybersecurity — any defensive product |
| Incident Response | Infrastructure, security, cloud, databases |
| Break/Fix | Broad — any product with complex failure modes |
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
- Most simple products get none — that's correct
- The same intelligence feeds Designer for program recommendations
- Lab concepts in the product card provide the specific detail; badges provide the headline

---

## In-App Documentation Linking

### Documentation as the explainability layer
**Principle:** The Badging and Scoring Reference documentation serves double duty — it's both the developer/AI reference AND the in-app help system. Each section of the UX links to the corresponding section of the documentation.
**Implementation:**
- Each major section in the Badging and Scoring Reference needs an anchor tag the UX can link to
- Documentation must be written clearly enough for a seller to understand, not just developers
- Section-level linking, not badge-level — one click shows the whole section for that part of the UX
- Examples: clicking "how does this work?" on Product Labability shows the full Product Labability section. Clicking on ACV shows the ACV calculation section.
- When documentation is updated, in-app help updates automatically — same source
- Keep it digestible — each section should be a standalone explainer
- Don't clutter the UX with icons everywhere — strategic placement at section level only

---

## LMS / LXP Detection

### Surface the specific LMS platform name
**Current:** The badging framework has a generic "LMS / LXP" badge.
**Improvement:** Badge should display the specific platform name (Docebo, Cornerstone, Moodle, etc.) — same variable-driven principle as lab platform badges. Docebo and Cornerstone are Skillable partners and should be green.
