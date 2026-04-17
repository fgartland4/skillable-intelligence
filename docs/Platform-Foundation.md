# Skillable Intelligence Platform — Foundation

This is the strategic authority for Skillable Intelligence. It owns the Guiding Principles, the architecture, the people the platform serves, the scoring framework at a glance, the ACV model, the Verdict Grid, and the UX structure. Operational detail — every dimension's math, every scoring signal, every strength tier, the penalty tables — lives in `Badging-and-Scoring-Reference.md`. Where the two docs touch, this document names what each thing *is* and the reference doc names *how* it's computed.

Best current thinking, always. Fully synthesized, never appended.

---

## Guiding Principles

**These are a thinking system, not a list.** Read them, then read the rest of this document, then come back and re-read them. The second pass is where they become operational — where you see how each GP shapes the architecture, the scoring, the UX, and how we work together. See `collaboration-with-frank.md` → "Re-reading Is the Point."

### GP1: Right Information, Right Time, Right Person, Right Context, Right Way

> Right information, at the right time, to the right person, with the right context, in the right way.

| Right... | Means... |
|---|---|
| **Right information** | The specific thing they need, not everything we know |
| **Right person** | Different roles get different slices of the same data |
| **Right time** | When they need it — not before it's relevant, not after it's useful |
| **Right context** | Framed so they understand why it matters *to them* |
| **Right way** | Concise first. Progressive disclosure. Fewer words. Invite depth, don't force it |

### GP2: Why → What → How

Every insight, every recommendation, every judgment starts with **why** it matters, then **what** to do about it, then **how** to do it.

| Level | Question | What it does |
|---|---|---|
| **Why** | Why does this matter? | Creates common ground between technical and non-technical people |
| **What** | What do we need to create or solve? | Defines the scope of work |
| **How** | How do we build or implement it? | Execution detail |

This sequence is how the platform builds **conversational competence**. When designing any screen, card, or recommendation, ask: Is the Why clear first? Can someone stop here and be conversationally competent? Can they keep going into What and How if they need to?

### GP3: Explainably Trustworthy

Every judgment the platform makes must be traceable, from conclusion back to evidence, so anyone can follow the reasoning and believe it.

- Scoring logic cannot be a black box
- Judgments distinguish fact from AI-informed assumption via the confidence levels (`confirmed` / `indicated` / `inferred`)
- Documents produced by the platform are evidence trails, not just summaries
- Progressive disclosure is the trust mechanism — give the conclusion, then let people pull on the thread until they believe it
- The documentation IS the in-app explainability layer. Users click into any Pillar card to see the framework documentation. One source of truth, one click, digestible.

### GP4: Self-Evident Design

The platform's intent, logic, and structure must be evident at every layer — from variable names to UX output. Anyone inspecting any layer should understand why it exists, what it does, and how it connects to the whole.

| Layer | What self-evidence looks like |
|---|---|
| Variable and field names | Named after the concepts they represent — `training_commitment`, `delivery_capacity`, `organizational_dna` — not generic labels |
| Module names | You can tell what a module does from its name — `pillar_1_scorer`, `fit_score_composer`, `acv_calculator`, `badge_selector` |
| Data models | Pillars, dimensions, and fact drawers are explicit in the schema, not buried in unstructured text |
| Prompts | Fact extractors carry typed field lists, not freeform instructions |
| UX output | Recommendations, badges, and rationale all trace back to code |
| Canonical lists | One source of truth for any shared list; referenced everywhere, never duplicated |

GP3 and GP4 are partners. Explainably Trustworthy is the standard. Self-Evident Design is how it's achieved at every layer. Together they mean: the platform explains itself — to users, to developers, to AI, to anyone who touches it.

### GP5: Intelligence Compounds — It Never Resets

Every interaction makes the data sharper. No update loses prior knowledge. The platform builds on what it already knows.

- Every analysis enriches what came before
- Deeper research (a full Deep Dive) automatically sharpens lighter data (a discovery-level record used by Prospector and the Inspector product chooser)
- Cache updates preserve and sharpen, not wipe and restart
- Prompt and logic changes trigger tiered cache invalidation via `SCORING_MATH_VERSION` / `RUBRIC_VERSION` / `RESEARCH_SCHEMA_VERSION`, never silent drift and never forced re-research on math-only changes (see Architecture Reality)
- **One persistent analysis per company.** Each company has a single stable URL. Every Deep Dive run accumulates products into the same analysis without breaking the URL. Re-running with the same products is instant (cached). Re-running with new products scores only the new ones and appends them.

### GP6: Slow Down to Go Faster

Truly understanding a problem and answering it once is dramatically faster than solving it quickly, bouncing off the wrong answer, and solving it again. This applies to people, to AI assistants, and to the platform itself.

| Slow down means... | Not... |
|---|---|
| Read before theorizing | Diagnosing from memory or summary |
| Verify the symptom against ground truth (the cache, the code, the actual output) | Inferring what must be happening |
| Present ONE grounded diagnosis, once | A branching decision tree of maybe-fixes |
| Distinguish root cause from symptom | Treating the first thing you see as the bug |
| Name structural questions when you spot them | Burying them inside a code change |
| Check for adjacent causes before declaring independence | Assuming two bugs are unrelated because they wear different masks |

**Why this is a Guiding Principle, not a work habit:** at a certain point, the cost of a fast-but-wrong answer isn't just the rework — it's the confidence tax on every future decision that depends on the flawed one. Working slowly where it matters is how the platform stays trustworthy as it grows. **GP6 and GP3 are partners.**

---

## Architecture Reality — Where the Code Deviates from the Ideal (and Why)

The rest of this document describes the architecture as a uniform system: research extracts raw facts, scoring applies Skillable capabilities to those facts, badges surface evidence. That framing is mostly true. But there are **intentional, bounded variations** between what the prose implies and what the code actually does. Without this section, every new reader (human or AI) hits those variations, reads them as drift, and launches into "fix everything" work that then gets reverted.

This section names every such variation we know about, with the reason each exists. If you're looking at the code and something reads like it contradicts a rule below, check here first.

### The three hard rules (Frank, 2026-04-16)

Everything in this section is scaffolding around three non-negotiable rules:

1. **Research is immutable.** The researcher extracts raw facts with evidence, source, and confidence. It never grades, never picks a Skillable fabric, never labels friction, never declares viability. Stored research can never be forced to refresh by a scoring logic change.
2. **Discovery must display trustworthy-yet-directional data.** Marketing and Prospector need real signals at discovery time — tier labels, rough ACV, rankings — good enough to prioritize ICP without overpromising.
3. **Each Deep Dive improves #2 without violating #1.** Deep Dive adds richer raw facts. The deterministic derivations layer reads the richer facts and sharpens the directional signals automatically. Free, instant, GP5.

These three rules are enforced structurally by the three-tier version stamps described under "Version invalidation" below.

### Three scoring models in the code, not one

The "Research → Store → Score → Badge" pipeline is uniform across all three Pillars, but **two scoring models** coexist inside the Score layer — by design, not drift.

| Pillar | Scoring model | What's in the fact drawer | Where grading happens |
|---|---|---|---|
| **Pillar 1 — Product Labability** | **Canonical** (fixed badge vocabulary, deterministic point lookup) | Raw fact primitives PLUS extractor-graded labels (`preferred_fabric`, `sandbox_api_granularity`, `credential_lifecycle`, `training_license`) — graded at extract time because the canonical model takes graded inputs directly | Inside the research prompt (Claude grades as part of fact extraction) |
| **Pillar 2 — Instructional Value** | **Rubric** (category baselines + strength tiers) | Raw `SignalEvidence` (truth-only: `present`, `observation`, `source_url`, `confidence` — no strength field) | Separate Claude call via `rubric_grader.py`; output stored as `GradedSignal` records on `Product.rubric_grades`, **separate from the fact drawer** |
| **Pillar 3 — Customer Fit** | **Rubric** (org-type baselines + strength tiers) | Same pattern as Pillar 2 | Same pattern as Pillar 2; grades live on `CompanyAnalysis.customer_fit_rubric_grades` |

**Why Pillar 1 is intentionally different.** Its dimension facts are binary or enumerable (does it run as installable? is the Sandbox API rich / partial / none?). Trying to rubric-grade them would be theater — the "grade" is a direct lookup, not a qualitative judgment. Keeping Pillar 1's canonical model simple and fast was a deliberate choice.

**What this means for the "no judgments in research" rule.** Pillar 2/3 honor the rule literally — their fact drawers store truth only; all grades live in a separate store. Pillar 1 stores graded labels in the drawer but only because those labels ARE the facts the canonical scorer needs. Rule #1 is still honored in substance — no re-research is ever required when scoring math changes, because the research prompt doesn't encode scoring math.

### Version invalidation is tiered, not binary

The code stamps three independent version fields on every saved discovery and analysis:

| Version | Bumps when... | Invalidation path | Cost |
|---|---|---|---|
| `SCORING_MATH_VERSION` | Point values, weights, multiplier tables, penalty values, ACV rates, Verdict thresholds change | Pure-Python rescore from saved facts + saved rubric grades | **Free** |
| `RUBRIC_VERSION` | Rubric tier definitions, signal categories, grading criteria, rubric grader prompts change | Re-run `rubric_grader` against saved raw facts; then pure-Python rescore | **~$0.30–0.50 per company** for grader calls. Zero re-research. |
| `RESEARCH_SCHEMA_VERSION` | Fact drawer shape itself changes — fields added, removed, or re-typed | Full re-research | **~$2.00–2.50 per product**. Deliberate human bump only — rare. |

Legacy `SCORING_LOGIC_VERSION` is preserved as a backwards-compat alias pointing at `SCORING_MATH_VERSION`. Records stamped before the split exist in the cache as "UNSTAMPED" records; the invalidation path treats them safely without forcing re-research.

**What this invalidates historically.** Before 2026-04-16 a `SCORING_LOGIC_VERSION` bump wiped the cached products and triggered full re-research. That was the Rule #1 violation we closed. The tiered model is the structural enforcement of Rule #1.

### Sharpening: Deep Dive writes back to Discovery

Intelligence compounds across layers, not just within a single analysis:

- **Customer Fit** — `aggregate_customer_fit_to_discovery()` writes the unified Pillar 3 back to the parent discovery so every tool (Inspector, Prospector, Designer) reads it from one canonical place.
- **Product Labability** — `aggregate_product_labability_to_discovery()` writes real Deep Dive PL scores back onto the parent discovery's per-product `rough_labability_score` so Prospector's tier columns (Promising / Potential / Uncertain / Unlikely) reflect real scoring, not the pre-Deep-Dive guess. Original rough guess preserved on `_rough_labability_score_initial` for diagnostics.
- **ACV** — `recompute_analysis()` recomputes `_company_acv` (scored + extrapolated + capped) on every page load in both Inspector and Prospector. Math retunes propagate instantly; rate-table changes apply to every view without re-research.

Pillar 2 Instructional Value discovery-level hints (`api_surface`, `complexity_signals`, `target_personas`, `cert_inclusion`) are **not** sharpened back to discovery today. This is a known gap, not a contradiction of the pattern — the row-level Fit Score IS sharpened; only the discovery-level lightweight hints lag.

### Skillable capabilities live in Python, in a dedicated Layer-2 module

Historical evolution:
  - Pre-2026-04-16: Two parallel sources — `scoring_config.SKILLABLE_CAPABILITIES` (Python tuple, claimed to be consumed by the scoring layer) and `backend/knowledge/skillable_capabilities.json` (a richer JSON that was loaded at startup but never read by any code path).
  - 2026-04-16: JSON file retired. Tuple kept in `scoring_config.py`.
  - 2026-04-17: Tuple extracted to `backend/skillable_knowledge.py` (Layer 2 — self-knowledge, distinct from Layer 3 scoring rules) and enriched with AWS supported/unsupported service lists, Azure orchestration detail (CSR/CSS, Bicep/ARM/Terraform, Resource Providers, Managed ACPs), and cross-fabric entries (Cloud Credential Pool, Cloud Security Review). The prior one-line entries became richly structured. An audit at that time found zero runtime consumers — the tuple was orphaned documentation. Wiring landed in the same commit: the discovery prompt in `backend/prompts/discovery.txt` now contains a `{SKILLABLE_CAPABILITY_CONTEXT}` marker that `backend.scorer.build_discovery_prompt()` substitutes at prompt-build time, and `backend.researcher.extract_product_labability_facts()` now concatenates the full capability context to the Pillar 1 system prompt. A product that depends on an AWS service in the "not supported" list (e.g. SageMaker, Bedrock, Lightsail) will have that surfaced in `ProductLababilityFacts.provisioning.description` so the Pillar 1 scorer and badge selector can reason about it as amber — not red.

Current state: `backend/skillable_knowledge.py` is the single source of truth. `scoring_config.py` re-exports `SkillableCapability` and `SKILLABLE_CAPABILITIES` for back-compat; new code imports directly from `skillable_knowledge`. Prompts render capability context at prompt-build time, so a single edit to the tuple (e.g. adding a new AWS service to the supported list, or a new fabric) flows to the next research call without a process restart.

### The Simulation hard override is intentional

When `preferred_fabric == "simulation"` in the Pillar 1 fact drawer, `pillar_1_scorer.score_product_labability()` returns four fixed dimension values (12 / 12 / 0 / 12 = **PL 36**) instead of scoring each dimension on its raw facts. This looks like a bug at first reading — two very different SaaS products both landing at identical PL 36 reads as flattening — but it's a deliberate design:

- Simulation is a genuinely different fabric with genuinely different economics
- Symmetric middle credit is the honest answer when the researcher has determined no real per-learner provisioning path exists
- The distinctness sellers care about shows up in badges and in the briefcase, not in the PL score

What Workday variability revealed separately was **researcher non-determinism** on Sandbox API detection — the same product detected as `has_sandbox_api: true, granularity: partial` on one run and `has_sandbox_api: false` on another. That's addressed by compound-research merge (fact convergence across runs), not by removing the Simulation override.

### Badge floor and evidence fidelity

The locked rule is 2–4 badges per dimension. Pillar 1's Simulation override and Pillar 2/3's thin-grade cases can legitimately produce 1 badge per dimension today — not because the 2–4 rule is wrong but because the badge selector has no synthesis fallback. When scoring produces fewer than 2 badges, the badge selector should emit specific fact-driven context badges ("Simulation Fabric Chosen", "SaaS-Only No Per-Learner API", "Category Baseline: Cybersecurity") that explain the score without inventing evidence. Teardown is the one dimension where 1 badge can be legitimate (it's more binary).

### Product archetype — the Skillable-labability shape (Frank, 2026-04-16)

Market category alone (Cybersecurity, Data & Analytics, Document Management) cannot discriminate between products that warrant hands-on lab training and products that don't. Inside one market category there's huge variance — SharePoint (enterprise admin, deep lab value) and Acrobat (individual-contributor doc tool, e-learning is the right delivery) are both "Document Management" but have nothing in common from a Skillable-labability perspective.

The **product archetype** is a second, orthogonal classification dimension that answers: *what kind of product is this from a Skillable-labability standpoint?* It lives as two fields on `Product`:

- `archetype` — the classification value (enum, see `backend/archetype_classifier.py`)
- `archetype_rationale` — short text explaining the inference, so downstream Claude calls (rubric grader, badge selector, briefcase generator) can reason about the classification

**10-archetype enum:**

| Archetype | IV ceiling | Examples |
|---|---|---|
| `enterprise_admin` | 100 | Azure, Workday, ServiceNow, Entra, Intune, SharePoint admin |
| `security_operations` | 100 | Defender, Sentinel, Splunk, CrowdStrike, Palo Alto, FortiGate |
| `developer_platform` | 100 | GitHub Actions/Enterprise/Codespaces, GitLab, Visual Studio, Azure DevOps, Terraform, Kubernetes |
| `data_platform` | 100 | Anaplan, Snowflake, Databricks, Power BI, SQL Server, GitHub Copilot (AI tooling) |
| `integration_middleware` | 100 | Marketo, AEM, Adobe Commerce, Mulesoft, SAP CPI |
| `deep_infrastructure` | 100 | NetApp, Quantum, Commvault, HPE Aruba/OneView/Alletra, Fortinet, VMware |
| `engineering_cad` | 100 | Autodesk AutoCAD/Revit, Bentley MicroStation, SolidWorks, Dassault CATIA, PTC Creo, Ansys |
| `creative_professional` | 65 | Photoshop, Illustrator, Premiere Pro, InDesign, After Effects |
| `ic_productivity` | 45 | Word, Excel, Outlook, Acrobat, Teams (IC workflows), PowerPoint |
| `consumer_app` | 25 | Pure end-user apps, no admin depth, no cert program |

**Inference:** `archetype_classifier.classify_archetype(product, discovery_data)` — deterministic Python, reads existing fact drawer signals (category, subcategory, deployment_model, personas, description). Zero Claude calls. Rule #1 honored — this is a scoring-layer classification, research is untouched.

**Short-acronym safety:** CAD-family acronyms (`bim`, `plm`, `fea`, `cfd`) use word-boundary matching to prevent false positives ('fea' matching 'feature'). Multi-word phrases ('3d modeling', 'finite element', 'civil engineering') use substring matching which is safe.

**What the archetype drives:**

1. **IV ceiling in Pillar 2.** `pillar_2_scorer.score_instructional_value(..., archetype=X)` caps the composed pillar score via `score_override` when the ceiling is below the natural score. Acrobat can't score above 45 IV no matter how generously the rubric grades signals, because hands-on Skillable labs aren't the right delivery for Acrobat.
2. **ACV labability gate** (see below) — composed with PL via the linear gate.
3. **Badge selector archetype-aware filters** — future work; today badges are archetype-agnostic.

### ACV × Product Labability — linear labability gate (Frank, 2026-04-16)

The ACV math today is `audience × adoption × hours × rate`. It did not know about Product Labability. That meant a product with PL 29 (Skillable can barely lab it) got the same ACV calculation as a product with PL 95 (Skillable delivers labs beautifully). Wrong — ACV should reflect what Skillable can actually deliver.

**The rule:** `gated_acv = raw_acv × (PL / 100)`. Applied uniformly across every motion (Customer Training, Partner Training, Employee Training, Certification, Events). If we can't produce a lab, we can't produce a lab — none of those motions ring up ACV.

**Why linear (not stepped or cliff):**
- Simplest — one formula, no threshold tuning, no arbitrary cutoffs
- Honest — every PL point translates proportionally to dollars
- Matches engagement economics — Skillable can usually figure out SOMETHING for hard-to-lab products, but the payoff must match the effort. PL 29 means proportionally reduced payoff; PL 95 means near-full payoff.
- Hard cliff would lie ("zero value at PL 39") — reality is we can still deliver partial value
- Stepped would add arbitrary discontinuities — a PL 79 vs PL 81 swing shouldn't cause a 15% ACV jump at a threshold

**Implementation:** both `compute_acv_on_product` (score-time, dataclass) and `compute_acv_potential` (cache-reload, dict) apply the multiplier at the final total dollar step. The `acv.labability_factor` field is stored for transparency.

**Example impacts from 6-company validation:**

| Product | PL | Pre-gate ACV | Gated ACV |
|---|---|---|---|
| Fortinet FortiGate | 97 | $162k | $157k (−3%) |
| Visual Studio | 95 | $23.4M | $22.3M (−5%) |
| Aruba Central (Sim override) | 36 | $430k | $155k (−64%) |
| Anaplan Platform (Sim override) | 36 | $100k | $36k (−64%) |
| GitHub Copilot | 36 | $7.4M | $2.7M (−64%) |
| Quantum Scalar Tape | 5 | $21k | $1k (−95%) |

Low-PL products with big audiences collapse to honest numbers. High-PL products with appropriate audiences barely move. The composition is self-consistent: the math says exactly what the rule says.

### Market Demand is per-product, not per-company (Frank, 2026-04-16)

Before 2026-04-16, `grade_market_demand` fed the rubric grader both product-specific and company-level facts (channel partners, ATPs, reference customers, geographic reach) as equal-weight evidence. That caused every product in a strong-company portfolio to inherit the same Market Demand score — HPE OneView, Aruba Central, SimpliVity all landed at 20/20 Market Demand because the grader read HPE's ATP program as evidence for each product.

**The fix:** the grader now receives two clearly-separated sections:
- **PRIMARY** — Market Demand facts for THIS product (install base for this product, cert mentions of this product, independent course counts for this product). Drives the tier directly.
- **COMPANY CONTEXT** — informational only. Cannot alone justify a 'strong' tier. Must be corroborated by product-specific evidence in PRIMARY.

The prompt explicitly instructs the grader that company-level signals can reinforce product-specific findings but cannot single-handedly drive a strong rating. Takes effect on the `RUBRIC_STALE` rescore path (`regrade=True`).

---

## How the GPs Show Up in the Platform

After reading the GPs, scan this table. It is the key that makes the rest of the document operational — every architectural choice below traces back to one or more of these principles.

| GP | Where it lives in the platform |
|---|---|
| **GP1** — right info, right time, right person | Progressive Disclosure Stack · HubSpot-first for sellers · Seller Briefcase · persona-specific entry points · concise-first, depth on hover |
| **GP2** — Why → What → How | Every Pillar card leads with the question · Seller Briefcase opens with Why · conversational competence starts with Why |
| **GP3** — Explainably Trustworthy | Confidence levels · evidence on hover · documentation is the in-app explainability layer · traceable from conclusion back to source |
| **GP4** — Self-Evident Design | Variable names carry meaning · Pillar / Dimension / fact drawer hierarchy is explicit · `scoring_config.py` is the Define-Once source · names you can read without a glossary |
| **GP5** — Intelligence Compounds | One persistent analysis per company · cache sharpens, never wipes · tiered version stamps (math / rubric / research schema) pick the cheapest invalidation path · Deep Dive writes back to parent discovery for PL + CF + ACV |
| **GP6** — Slow Down to Go Faster | Read ground truth before theorizing · one grounded diagnosis, not a branching maybe-list · trace signals end-to-end before editing · name structural questions when you see them |

---

## The Center of Everything: Products

**Why.** A product's fit with Skillable determines whether we can help a company at all. If the underlying technology cannot be labbed, nothing else — customer size, training maturity, budget — matters. Starting anywhere else produces answers that look right and don't hold up. And if the platform cannot distinguish a real product from a feature, a library, or a marketing term, every downstream score, badge, and ACV estimate is built on garbage. Getting the product definition right is the upstream fix for everything.

**What.** The platform is **product-up**. It does not start with "what kind of company is this?" and guess at their products. It starts with the products, and the products tell you everything else.

```
Products (the atomic unit)
  → roll up to → Product categories / verticals
    → roll up to → Company profile
      → map to → People (who builds training for THESE products)
```

### What IS a Product

A product is something a customer **licenses or deploys as a standalone thing**. It has its own installation or subscription, its own access model, its own identity, and it does meaningful work on its own. It has a real user population worth measuring.

| A product IS... | A product IS NOT... |
|---|---|
| Something you license or subscribe to as a standalone thing | A feature inside a product |
| Has its own deployment / installation | An add-on toggle within a parent product |
| Has its own identity and access model | A library or package you install from a repository |
| Does meaningful work on its own | A marketing umbrella or brand family name |
| Has a real user population worth measuring | A licensing tier of something else (Pro, Enterprise, Premium) |

**Examples.** RStudio IDE is a product. Posit Connect is a product. An R package installed via `install.packages()` is not. "RStudio Pro" is a licensing tier of RStudio — same product, different entitlement. The Trellix product portfolio has ~8 real products, not the 46 the old researcher returned — the rest were modules, integrations, and marketing labels.

### Product Relationships

**Why.** A flat list of products doesn't tell the seller which ones anchor the business and which ones orbit. Posit Connect makes no sense without RStudio — the seller needs to know RStudio is the flagship and Connect is a satellite. Without this distinction, the product chooser treats every product as equal, the ACV model weights them equally, and the seller walks into a conversation without knowing where to start. Product relationships tell the seller what matters most (GP1 — right information, right context).

| Relationship | What it means | Example |
|---|---|---|
| **Flagship** | The anchor product — largest user base, most recognizable, drives the ecosystem | RStudio IDE (Posit), Catalyst Switches (Cisco), Oracle Database (Oracle) |
| **Satellite** | Extends or depends on a flagship — meaningful on its own but smaller audience | Posit Connect (publishes what RStudio builds), Meraki (Cisco cloud networking) |
| **Standalone** | Independent product, no flagship dependency | Products at focused companies like Commvault |

A company can have multiple flagships across different categories — Cisco has flagships in Networking, Cybersecurity, and Collaboration. A focused company like Posit has one flagship and a few satellites. The relationship type, combined with estimated user base, drives product ranking.

### Product Popularity

**Why.** If the platform identifies 20 products for a company but cannot tell the seller which ones matter most, the seller wastes time on satellites while the flagship sits buried in the list. Worse: ACV estimates extrapolated from scored products to all discovered products are wildly inflated when the product count includes features and libraries that shouldn't be there. Popularity is the ranking signal that makes the product list commercially useful.

**What.** Every discovered product carries a rough estimated user base — not an exact number, but enough to separate a flagship with millions of users from a niche tool with thousands. The estimate is triangulated from vendor marketing claims ("trusted by 14M data scientists"), third-party signals (Stack Overflow tag counts, GitHub stars), analyst reports, and job posting volume.

**How.** The estimated user base feeds three things simultaneously:

| Where it lands | What it does |
|---|---|
| **Product chooser ranking** | Most popular products sort to the top — the seller sees what matters first |
| **ACV Motion 1 (Customer Training)** | Install base IS the audience for the biggest revenue motion |
| **Pillar 2 Market Demand** | A product with 2M users has a different training population than one with 5K |

This is a Define-Once fact: one estimate, used everywhere.

### How — Discovery and the Product Definition Filter

Every label, category, description, and piece of messaging derives from the product data. Organization type is a variable. Motivation is a variable. Product category is a variable. All flow from the data, and all shape how intelligence is presented.

The researcher's job during discovery is to be **selective, not exhaustive**. Identify all products that meet the product definition. Rank by estimated user base. There is no target count — the filter determines the count. A focused company like Posit yields 3–5 products. A broad company like Cisco or Oracle yields 20–30. Both are correct because both reflect the real portfolio.

**Product Labability applies to the underlying technology — always.** Regardless of organization type, the four Product Labability dimensions always apply to the *underlying technology*, never to a training wrapper or organizational structure. This applies at BOTH discovery time (the product definition filter extracts technologies from wrappers) AND Deep Dive time (the Pillar 1 fact extractors research the technology's provisioning, lab access, scoring, and teardown characteristics, not the wrapper program's). A "BS in Cybersecurity" is not the subject of a Pillar 1 assessment — Wireshark, Kali Linux, and Splunk are. *(Reinforced 2026-04-12)*

| Organization type | Intelligence path |
|---|---|
| Software company | Products → labability assessment → fit |
| Training / Certification org | Courses → extract underlying technologies → labability assessment → fit |
| University / School | Curriculum → extract underlying technologies → labability assessment → fit |
| GSI / Content firm | Client engagements → products involved → labability assessment → fit |
| LMS company | Their customers' products → labability assessment → fit |
| Distributor | Products they distribute → labability assessment → fit |

If a course or curriculum doesn't teach anything that involves hands-on interaction with technology — a leadership course, a compliance reading course, a soft-skills workshop — there's nothing to provision. No lab opportunity. Move on.

---

## Discovery Data Shape — What the Researcher Captures Before a Deep Dive

**Why.** Discovery is the first intelligence pass on a company. It has to be rich enough to rank products meaningfully — so the seller picks the right ones for a Deep Dive — without being so heavy that it costs as much as a Deep Dive itself. The discovery data also serves a dual purpose: it feeds the Inspector product chooser AND it feeds Prospector for marketing ICP targeting. One research pass, two consumers.

**What.** Discovery captures three tiers of data in a single research pass:

### Tier 1 — Per-product (light)

Captured for every product that passes the product definition filter.

| Field | What it captures |
|---|---|
| **name** | Product name |
| **vendor_official_acronym** | Official acronym only — never invented |
| **description** | 2–3 sentences with downstream-useful context: what the product does, what problem it solves, who uses it |
| **is_core_product** | True = standalone licensed product. False = feature / library / tier (filtered out) |
| **product_relationship** | flagship / satellite / standalone |
| **category** | One of the standard categories (Cybersecurity, Cloud Infrastructure, etc.) |
| **subcategory** | Industry-standard subcategory (2–3 words: Endpoint Protection, Statistical Computing IDE) |
| **deployment_model** | installable / cloud / hybrid / saas-only |
| **estimated_user_base** | Single estimated number — directionally right, not a range. "~14M" or "~50K" or "~2000". One number the seller can quote. For Software and Enterprise Software, this is the ACV audience directly. For wrapper org types (ILT, Academic, ELP, GSI/VAR/Distributor) this represents the underlying technology's market and is used for Labability context only — the ACV audience is `annual_enrollments_estimate` below. |
| **user_base_evidence** | What sources informed the estimate — vendor claims, Stack Overflow tag count, GitHub stars, analyst reports, job posting volume |
| **user_base_confidence** | confirmed / indicated / inferred |
| **annual_enrollments_estimate** | **Wrapper org types only.** Single estimated number — how many learners THIS organization serves in THIS program per year. For an ILT: classroom students per year in this course. For Academic: students enrolled in this program per year. For ELP: subscribers taking this technology slice per year. For GSI/VAR/Distributor: practitioners in this practice area per year. Distinct from `estimated_user_base` which is the underlying technology's global market. Empty / unset for Software and Enterprise Software org types. |
| **annual_enrollments_evidence** | What sources informed the enrollments estimate — published course catalog size, vendor case studies, Crunchbase / analyst reports, LinkedIn staff counts |
| **annual_enrollments_confidence** | confirmed / indicated / inferred |
| **rough_labability_score** | 0–100 directional estimate of lab promise. Clearly pre-Deep Dive — must be validated. See "Discovery Tier Labels" below |

### Tier 2 — Per-product (hints)

Lightweight signals that give a rough read on Pillar 1 and Pillar 2 potential without full extraction.

| Field | What it captures |
|---|---|
| **complexity_signals** | Is this a multi-component system with deep configuration? Or a simple single-purpose tool? Enough to rough-estimate Product Complexity |
| **target_personas** | Who uses it — admins, developers, analysts, end users. Tells us the training audience |
| **api_surface** | comprehensive / moderate / minimal / none + short description. Directly feeds Pillar 1 Lab Access and Scoring potential |
| **cert_inclusion** | Which certification programs include this product, if any. Feeds Market Demand and ACV Motion 4 |

### Tier 3 — Per-company (gathered once, applied to every product)

Company-level signals mapped to Customer Fit dimensions. Researched once during discovery and broadcast to every product — because Customer Fit measures the organization, not the product.

| Field | CF dimension | What it captures |
|---|---|---|
| **training_programs** | Training Commitment | What training does this company offer, and to whom? |
| **training_leadership** | Training Commitment | Named training/enablement org or leader |
| **training_breadth** | Training Commitment | How many audiences — customers, partners, employees |
| **sales_channel** | Market Demand / ACV | GSIs, VARs, distributors — who sells the product (channel = sales) |
| **atp_program** | Delivery Capacity | Authorized training partners, roughly how many |
| **delivery_partners** | Delivery Capacity | Who delivers training — vendor, third-party, ATPs (not "delivery channels") |
| **events** | Delivery Capacity | Flagship conferences, attendance estimates |
| **partnership_pattern** | Organizational DNA | Strategic partnerships or build-everything culture |
| **engagement_model** | Organizational DNA | Easy to engage or heavy procurement |
| **content_team_signals** | Build Capacity (thin) | Any evidence of internal authoring capability. Deliberately light — Build Capacity is inward-facing and hard to verify externally |
| **org_type** | Pillar 3 baseline lookup | Organization type for scoring baselines — ENTERPRISE SOFTWARE, SOFTWARE, TRAINING ORG, ACADEMIC, SYSTEMS INTEGRATOR, etc. Separate from `company_category` (the user-facing badge). See "Company Classification" below. |
| **lab_platform** | Delivery Capacity + Competitive | Already using a lab platform? Which one? |

**How.** The researcher makes a single Claude call during discovery. The product definition filter keeps the product count honest — no features, libraries, tiers, or marketing terms. Fewer products with richer context per product means the discovery call is actually **faster** than the old "find 40–60 everything" approach, not slower.

### Discovery Tier Labels

**Why.** The `rough_labability_score` is a pre-Deep Dive directional estimate. The seller and marketing need to know how much confidence to place in it — enough to prioritize, not enough to promise. The four tier labels communicate confidence level without overpromising (GP3 — Explainably Trustworthy at the discovery level).

**What.** The score maps to four tiers. Thresholds align with the scoring framework's existing color bands so the confidence language is consistent from discovery through Deep Dive:

| Tier | Label | Score range | Aligns with | What it communicates |
|---|---|---|---|---|
| 1 (highest) | **Promising** | ≥ 65 | Green band (≥ 65 in the Verdict Grid) | Strong signals — this looks good |
| 2 | **Potential** | ≥ 45 | Light Amber band (45–64) | Something here, needs validation |
| 3 | **Uncertain** | ≥ 25 | Amber band (25–44) | Could go either way |
| 4 (lowest) | **Unlikely** | < 25 | Red band (< 25) | Significant barriers visible |

**How.** Thresholds are sourced from `scoring_config.SCORE_THRESHOLDS` (Define-Once). The tier assignment is deterministic — `core.discovery_tier(score)` reads the thresholds and returns the tier key. No AI judgment in the tier assignment itself; the AI's judgment is in the score.

---

## Three Layers of Intelligence — Research, Store, Score, Badge

**Why.** The old monolithic Claude call collapsed research + scoring + badge selection into one step. Scoring logic changes forced re-research. Caching broke. A 4-minute Deep Dive replaced what should have been a millisecond recompute. Worse: badges became the *currency* of scoring, so changing a point value meant re-running Claude on every product. The fix is to separate the work by responsibility and never collapse the layers again.

**What.** The Intelligence layer has four internal sub-layers. Each has a different job, different rules about whether it can call Claude, and different modules. The framing is **Research → Store → Score → Badge.**

| Layer | Owns | Produces | Modules | Can call Claude? |
|---|---|---|---|---|
| **1. Research** | Going out to the world and extracting **structured facts** | Populated fact drawers | `researcher.py` + the three parallel fact extractors (Pillar 1 / 2 / 3) | **Yes** — the main place Claude runs |
| **2. Store** | Holding facts in a **single canonical location** per fact | `Product.product_labability_facts`, `Product.instructional_value_facts`, `CompanyAnalysis.customer_fit_facts` | `models.py` (typed dataclasses), `storage.py` (JSON persistence) | No — it's a location, not a process |
| **3. Score** | Applying **deterministic rules** to facts to produce scores | Per-dimension scores, per-pillar scores, composed Fit Score, ACV Potential | `pillar_1_scorer`, `pillar_2_scorer`, `pillar_3_scorer`, `rubric_grader`, `fit_score_composer`, `acv_calculator` | **Narrow slice only** — the rubric grader grades qualitative findings for Pillars 2 / 3. Everything else is pure Python. |
| **4. Badge** | Selecting **2–4 contextual badges per dimension** to explain the score | Canonical badge names + evidence text attached to each `DimensionScore` | `badge_selector.py` | Currently deterministic. Step 6 full may add a tiny per-dimension call for evidence phrasing. |

**How.** `intelligence.score()` wires them together:

```
researcher extracts facts → fact drawers stored on Product / CompanyAnalysis
  → rubric_grader tiers Pillar 2 + Pillar 3 findings (parallel Claude calls, one per dimension)
  → pillar_1_scorer produces Pillar 1 PillarScore from facts (zero Claude)
  → pillar_2_scorer produces Pillar 2 PillarScore from facts + grades
  → pillar_3_scorer produces Pillar 3 PillarScore from facts + grades
  → fit_score_composer applies the Technical Fit Multiplier, writes FitScore.total_override
  → acv_calculator recomputes ACV Potential from motion estimates + rate lookup
  → badge_selector attaches display badges
  → intelligence.score() persists and returns
```

Cache reloads go through `intelligence.recompute_analysis()`, which trusts saved pillar scores, recomputes ACV (so a rate-table retune propagates instantly), reassigns verdict, and sorts. No pillar scorer re-runs on cache reload. When scoring logic changes, the tiered versioning model (see Architecture Reality) picks the cheapest invalidation path — pure-Python rescore for math bumps, re-grade for rubric bumps, re-research only on schema bumps.

**The collapse rule.** No layer may collapse into another.

| Forbidden pattern | Why |
|---|---|
| Research + Score in one Claude call | Scoring changes force re-research. Caching breaks. Retired 2026-04-08 with the deletion of the monolithic scoring prompt. |
| Score + Badge in one step | Badges become the currency of scoring; facts get trapped inside badge labels. |
| Badge-as-scoring | A badge is *context on a score*, not the score itself. The score comes from facts via rules. |
| Score reads badges | The math layer must never look at badge names. Score reads the typed fact drawer directly. |

**The litmus test** before writing any Intelligence code: (1) which of the four layers does this belong to? (2) Am I about to collapse two layers? (3) Am I making a Claude call outside Research or the rubric grader? (4) Am I storing a fact in two places? (5) Am I reading a badge name to decide scoring math? If any of those stops fire, it's drift — find the right layer and write the code there instead.

---

## Layer Discipline — Shared Intelligence, Thin Tools

**Why.** The platform has three tools — Inspector, Prospector, Designer — that all need the same product intelligence, the same scoring, the same fact drawers, the same verdict logic. If each tool owned its own copy of that logic, they would drift. Drift means different fit scores for the same company in different tools. That destroys trust (GP3) and breaks the "intelligence compounds" promise (GP5).

**What.** One shared **Intelligence layer** sits below all three tools. Tools own only tool-specific work: URL patterns, request parsing, template selection, view orchestration. Everything that knows about products, companies, scoring, research, evidence, or the framework lives in the shared layer.

| Layer | What lives here | Modules |
|---|---|---|
| **Intelligence layer** (shared) | Research, discovery, per-pillar scoring, fit-score composition, ACV calculation, badge selection, rubric grading, cache versioning, validation, briefcase generation, model definitions, locked vocabulary, classification, verdicts | `intelligence.py`, `scorer.py`, `researcher.py`, `pillar_1_scorer.py`, `pillar_2_scorer.py`, `pillar_3_scorer.py`, `rubric_grader.py`, `fit_score_composer.py`, `acv_calculator.py`, `badge_selector.py`, `scoring_config.py`, `storage.py`, `models.py`, `core.py` |
| **Inspector** (tool) | Inspector-specific routes, request parsing, template selection, view orchestration | `app.py` Inspector route handlers, `tools/inspector/templates/*.html` |
| **Prospector** (tool) | Prospector-specific routes, batch discovery orchestration, results table, CSV export, HubSpot integration glue | `tools/prospector/` |
| **Designer** (tool) | Designer-specific routes, program-design pipeline, customer-facing views | (future) |

**How.** The litmus test for any new function is: "would Prospector or Designer also need this if they were calling it?" If yes, it's shared. If no, it's tool-specific. **When in doubt, default to shared.** Intelligence logic mistakenly placed in tool files is a **bug class**, not a style preference — it's graded with the same severity as cache-version lies and vocabulary drift.

---

## The Standard Search Modal — The One and Only

**Why.** Every time a drifted custom progress UI has been built, the platform has ended up with different timer behavior, different error handling, different cancel semantics, inconsistent status updates, and users who can't tell which Skillable tool they're in. Trust (GP3) requires consistency. Self-Evident Design (GP4) requires one way to do it.

**What.** There is **ONE** search / progress modal in this entire platform. It lives in `tools/shared/templates/_search_modal.html` and is used for every long-running operation across Inspector and Prospector today, and Designer when it comes online.

| Mode | Surface | Use |
|---|---|---|
| **Progress mode** — card overlay with eyebrow, title, animated status, progress bar, elapsed timer, cancel button, and SSE subscription | Dark progress chrome | Discovery research, Deep Dive scoring, cache refresh |
| **Decision mode** — same card, different middle section: message + two buttons (primary / secondary) | Dark progress chrome | Stale-cache prompts, any "confirm before running" flow |
| **Info mode** — rationale / drivers / caveats display triggered by clicking an ACV row | Dark progress chrome | Prospector ACV Potential click-through |
| **Docs mode** — full documentation surface with eyebrow, title, accent rule, WHY/WHAT/HOW section labels, tables, anchor-scroll support | **White — `--sk-modal-*` theme tokens**. 920px max width. Surface flips from dark to white for documentation readability. | Every `?` help icon across Inspector + Prospector (and Designer when it comes online) |
| **In-place transition** — decision → progress without flicker | Same card, no teardown | Refresh flows where the user confirms and then watches the work happen |

**The docs-mode white surface is the one design exception.** Progress / decision / info modes keep the dark progress chrome — those are action surfaces where a running operation is the context. Docs mode is a **reading surface** — 920px wide, white background, dark text, green accent rule under the header, WHY/WHAT/HOW eyebrow sections, scannable tables. It carries the original Deep Dive info-modal design, now unified inside the shared modal component. (Restored to white 2026-04-14 after an earlier consolidation flattened the design; the restoration uses `--sk-modal-*` theme tokens from `tools/shared/templates/_theme.html` — no hardcoded hex.)

**How — the enforcement rules, no exceptions:**

1. Every long-running operation across every tool uses this shared modal.
2. The ONLY `new EventSource(` in the entire codebase lives in `_search_modal.html`. Anywhere else is a bug.
3. The SSE contract is `status:<text>` / `done:<payload>` / `error:<message>`. Every backend route publishing progress uses this exact contract.
4. Routes that kick off long-running work return JSON `{ok, job_id}`. The caller opens the shared modal via `openSearchModal({sseUrl: '/.../progress/' + job_id, ...})`.
5. No forked markup. No per-flow "just this one modal." No inline loading states for long operations. If the modal's middle section needs a new variant, add it INSIDE `_search_modal.html` and document it in the file header.

**Shared API:**

- `openSearchModal({eyebrow, title, sseUrl, onComplete, onError})` — progress mode
- `openSearchModalDecision({eyebrow, title, message, onRefresh, onIgnore})` — decision mode
- `openSearchModalInfo({eyebrow, title, rationale, confidence, drivers, caveats})` — info mode (ACV rationale display)
- `openSearchModalDocs({eyebrow, title, sections: [{heading, body, id?, subtitle?}]})` — docs mode (white-surface documentation)
- `transitionSearchModalToProgress({...})` — decision → progress in place
- `scrollToSearchModalSection(id)` — anchor-nav helper for docs-mode cross-references

---

## The Define-Once Principle

**Why.** When a fact lives in two places, they drift. Install base in the ACV calculator drifts from install base in Pillar 2 Market Demand. Pillar weights in the code drift from pillar weights in the prompt. Drift destroys trust.

**What.** All Pillar names, dimension names, weights, thresholds, badge names, scoring signals, rate tables, verdict definitions, and locked vocabulary are defined **once** in `scoring_config.py` and referenced everywhere — code, UX, tests, in-app explainability. Nothing is hardcoded anywhere else. If a value changes, it changes in one place and propagates through the entire system.

**How.** Every scorer imports `scoring_config as cfg` and reads typed values directly. Pre-commit tests scan for magic-number literals in the Score layer files (`pillar_1_scorer`, `pillar_2_scorer`, `pillar_3_scorer`, `fit_score_composer`, `acv_calculator`). Anything that isn't `0`, `1`, `-1`, `100`, an HTTP status code, or a line carrying a `# magic-allowed: <reason>` annotation is a test failure and must come from config.

---

## The End-to-End Principle

The framework shapes how we **gather**, how we **store**, how we **judge**, and how we **present**. One model, end to end. The same Pillar / Dimension / Requirement structure runs through every layer — research, storage, scoring, display. No translation step. No reorganizing after the fact.

---

## Accessibility: WCAG AA Compliance

All UX elements must meet WCAG AA contrast standards (4.5:1 for normal text, 3.0:1 for large text). This is a build standard and a QA checkpoint — every color combination is validated before shipping. Accessibility is not optional.

---

## Organization Types

**Why.** Skillable serves a broad landscape. Software companies are the anchor — they create the products that everything else orbits around — but they are far from the only audience. The organization type determines how you find the products, what counts as the training population, and how the conversation with the seller is framed. The underlying intelligence logic — Pillars, dimensions, scoring, ACV — is the same for all.

### Software Companies — The Anchor

**Why.** Software companies are the baseline the entire framework is built on. The product definition, the scoring dimensions, the badge vocabulary, the ACV motions — all designed for software companies first. Every other org type is an adaptation of this baseline.

**What.** The product IS the product. No wrapper extraction needed. For universities we extract technologies from academic programs. For GSIs we extract from practice areas. For software companies, the product is already the thing we're scoring. RStudio is the product. Azure is the product. That directness is why software companies are the simplest path through the framework.

**The full framework applies without adaptation:**

| Element | Software company application |
|---|---|
| **Product definition** | Their products — directly. Licensed/deployed as standalone things. |
| **Product Labability** | How do we get this product into Skillable? |
| **Instructional Value** | Does this product warrant hands-on training? |
| **Customer Fit** | Is this organization a training buyer? |
| **ACV** | Users of the product (not customers — Bank of America is one customer, but 10,000 engineers using Azure are the learners) × adoption × lab hours × rate |
| **Deep Dive** | Full scoring — all three Pillars, all twelve dimensions |

**Software companies span a huge range.** Posit has one flagship product. Cisco has 25+. Both are software companies. The framework handles both because the product definition filter and popularity ranking adapt naturally — the number of products is an outcome of the filter, not an input.

**Company badge — derived from products, not generic labels:**

| Company | Badge | Why |
|---|---|---|
| Cisco | Networking | Clear primary category |
| Posit | Data Science & Engineering | One flagship, one category |
| Trellix | Cybersecurity | Focused portfolio |
| Commvault | Data Protection | Single-category company |
| Sage | ERP / Accounting | Primary ERP, secondary HR |

**Enterprise Software — earned by breadth.** A rare few companies are genuinely too broad to categorize with a single label. These earn the "Enterprise Software" badge — reserved for companies where no single category captures even half their product portfolio.

| Company | Badge | Why it earns Enterprise Software |
|---|---|---|
| **Microsoft** | Enterprise Software | Cloud + Productivity + Security + ERP + DevOps — 5+ major categories |
| **Oracle** | Enterprise Software | Database + Cloud Infrastructure + ERP + HCM + Healthcare IT — genuinely unrelated product lines |
| **SAP** | Enterprise Software | ERP + HCM + Supply Chain + Analytics + Cloud Platform |
| **IBM** | Enterprise Software | AI + Cloud + Security + Automation + Mainframe |
| **Broadcom** | Enterprise Software | Infrastructure/Virtualization (VMware) + Cybersecurity (Symantec) + Networking |

Companies that are expanding but still have a clear primary category keep the specific badge: Salesforce = CRM, ServiceNow = IT Service Management, Adobe = Creative / Digital Experience, Palo Alto Networks = Cybersecurity. The product chooser shows the category breakdown regardless of the badge.

**This is the primary Prospector audience.** Marketing is mostly targeting software companies — "find companies whose products are labable and whose organizations are training buyers." The ICP signal for marketing is the Fit Score + ACV combination. Every other org type has a modified Prospector story (partnership flags, distribution opportunities, cert prep volume), but software companies get the pure "should we pursue this deal" output.

### How the Framework Adapts to Other Organization Types

The scoring framework is universal — the same Pillars, dimensions, and math apply to every organization type. What changes is **how the researcher finds the products**, **what counts as the training population**, and in some cases **whether a full Deep Dive applies at all**. Most non-software org types follow a two-step extraction pattern: find the wrapper (program, practice area, course catalog), then extract the underlying technologies.

**The org-type summary:**

| Organization Type | Examples | Their relationship to products | How you find the products | Deep Dive? |
|---|---|---|---|---|
| **Software companies** | Cisco, Posit, Trellix, Commvault, Microsoft | They *create* the products | Product pages, documentation, API docs | Yes — full |
| **Universities & schools** | Arizona State, Rose-Hulman, WGU | Their *programs* teach technologies | Published curriculum — extract underlying technologies | Yes — on the technologies |
| **GSIs** | Deloitte, Accenture, Cognizant | They *deploy and implement* products | Practice areas — extract underlying technologies | Yes — on the technologies |
| **VARs** | Regional technology consultancies | They *implement and train on* products | Consulting practices — extract underlying technologies | Yes — on the technologies |
| **Technology Distributors** | CDW, Tech Data, Ingram, Arrow | They *sell and service* products | Service groups — extract underlying technologies | Yes — on the technologies |
| **Industry Authorities** | CompTIA, EC-Council, SANS, ISACA | They *certify professional competence* | Certification programs + cert prep — extract underlying technologies | Yes — on the technologies |
| **Enterprise Learning Platforms** | Skillsoft, Pluralsight, Coursera Business | They *sell massive course catalogs* | Technology portion of catalog — extract underlying technologies | Yes — on the technologies |
| **ILT Training Organizations** | New Horizons, QA | They *deliver instructor-led training* | Course offerings — extract underlying technologies | Yes — on the technologies |
| **LMS / Learning Platforms** | Cornerstone, Docebo, Degreed, Moodle | They *host and deliver* learning + they have a scorable product | Their LMS product + their distribution opportunity | Yes — hybrid (product + partnership) |
| **Content Development firms** | GP Strategies | They *build learning programs* for other companies | Technologies they cover + build capacity signals | **No** — partnership assessment only |

#### Universities & Schools

**Why this matters.** Universities are a significant Skillable audience. Their "products" are academic programs and courses. The labability question isn't about the course itself — it's about the **underlying technologies taught in that course**. A cybersecurity degree program that teaches Splunk, Wireshark, and Kali Linux is labable. An English literature program is not.

**Discovery — two-step extraction:**

| Step | What the researcher finds | Example |
|---|---|---|
| **1. Technology-facing departments and programs** | Degrees, certificates, focus areas that involve technology | BS Computer Science, MS Cybersecurity, Data Science certificate, Engineering school |
| **2. Underlying technologies taught** | The actual software products students use in those programs | AWS, Azure, Splunk, Wireshark, Cisco IOS, Python/Jupyter |

Programs are the "products" at the university level. The underlying technologies are what gets assessed for labability — which is no different from assessing those same technologies at a software company. Splunk is Splunk whether it's taught at Arizona State or deployed at Trellix.

**Product chooser display.** What appears on the product chooser depends on the university's scale:

- **Large university (Arizona State):** Show the 5–10 technology-facing programs/departments. The seller needs to know which department to talk to.
- **Small technical school (Rose-Hulman):** Show the underlying technologies directly — nearly every program is relevant.
- **Liberal arts college (Vassar):** May show only a small CS department, or nothing labable at all.

**Estimated user base = students in technology-facing programs, not total enrollment.**

| University | Total enrollment | Technology-facing students | What matters for Skillable |
|---|---|---|---|
| Arizona State | ~120,000 | ~15,000 | 15,000 — large engineering/CS/data science population |
| Rose-Hulman | ~2,200 | ~2,200 | 2,200 — nearly 100% relevant, small but concentrated |
| Vassar | ~2,400 | ~100 | 100 — small CS department, likely not a priority |

Same principle as the general rule: the training population is the relevant subset, not the headline number.

**Company badge for universities:**

| University type | Badge | What it signals |
|---|---|---|
| Engineering-focused | Engineering College | Nearly everything is relevant |
| Large research university | Research University | Big school — find the right departments |
| Liberal arts | Liberal Arts College | Probably not a fit — verify before investing time |

**How the Pillars apply:**

| Pillar / Dimension | University interpretation |
|---|---|
| **Product Labability** | Are the underlying technologies labable? Same assessment as any software product |
| **IV — Product Complexity** | Are these technologies complex enough for hands-on practice? |
| **IV — Market Demand** | How many students are in these programs? How many graduates enter the workforce needing these skills? |
| **CF — Training Commitment** | Do they invest in hands-on learning? Do they already have lab-based courses? |
| **CF — Build Capacity** | Does their CDD (content design and development) group build technology content? How many engineering/CS professors? Instructional designers focused on technical curriculum? One professor = weak. A full CDD team focused on technology = strong. |
| **CF — Delivery Capacity** | How many technology-facing courses? 3 courses vs 100 is a fundamentally different delivery footprint. Online, in-person, hybrid? |
| **CF — Org DNA** | Do they partner with technology vendors? AWS Academy, Microsoft Imagine Academy, Cisco Networking Academy memberships are direct Skillable signals — they already value external platform partnerships for hands-on learning. |

**For Prospector / marketing targeting:** Key filters are technology-facing student population, number of lab-relevant programs, and existing technology vendor partnerships (AWS Academy, Cisco Networking Academy, etc.). Marketing doesn't need the full Deep Dive — "15,000 engineering students, AWS Academy partner" is enough to prioritize outreach.

#### GSIs, VARs, and Distributors

**Why this matters.** GSIs (Deloitte, Accenture, Cognizant), VARs, and distributors (CDW, Tech Data) all consult on, deploy, sell, and train on other companies' products. Their "products" are practice areas and service lines built around underlying technologies — structurally similar to how universities wrap academic programs around technologies. The lines between these org types are blurring — distributors are adding consulting groups to compete on services — but the distinction still matters for Pillar 3 baselines because their organizational capabilities are different.

**Discovery — same two-step extraction pattern as universities:**

| Step | What the researcher finds | Example (Deloitte) |
|---|---|---|
| **1. Practice areas / service lines** | Disciplines the company consults on and deploys | SAP Practice, Cybersecurity Practice, AWS Practice, Azure Practice |
| **2. Underlying technologies** | The actual software products deployed within each practice | SAP S/4HANA, SAP SuccessFactors, Splunk, Palo Alto, CrowdStrike |

The granularity of practice areas adapts to the company. A GSI with a dedicated AWS practice and a separate Azure practice shows those separately. A smaller VAR with one general "Cloud Infrastructure" practice shows that as one line. The researcher determines the right level based on what the company actually has.

**Product Labability — same as universities.** The underlying technology is the technology. SAP S/4HANA has the same labability characteristics whether you're analyzing Deloitte or SAP directly. The practice area is the wrapper; the technology gets scored.

| Org type | Their "product" | What gets scored for labability |
|---|---|---|
| GSI | Practice area / service line | Underlying technologies deployed |
| VAR | Consulting practice | Underlying technologies implemented |
| Distributor | Service group | Underlying technologies trained on |

**Estimated user base — two distinct training populations:**

| Audience | Who they are | Example (Deloitte SAP) |
|---|---|---|
| **Internal practitioners** | The company's own consultants who deploy and configure the technology | ~15,000 SAP consultants who need deep hands-on skills |
| **Client end users** | Technical staff at client organizations who manage the technology after handoff | Technical teams at every client engagement (e.g., Bank of America's SAP administrators) |

Internal practitioners are a known, countable population. Client end users are harder to estimate — every new engagement creates a new batch. Conservative, believable estimates are better than inflated guesses. The seller understands this is rough.

**ACV motions map naturally to the standard five:**

| Standard motion | GSI interpretation |
|---|---|
| **Employee Training** | The company's own consultants/practitioners |
| **Customer Training** | Clients' end users — the handoff training population |
| **Partner Training** | Subcontractors, offshore teams, partner firms |
| **Certification** | Practice-specific certs (SAP certification, AWS certification) |
| **Events** | Internal summits, client training events |

**Company badges — keep the distinction:**

| Badge | Org behavior | Why separate |
|---|---|---|
| **Global Systems Integrator** | Deep consulting, large practice areas, strong build and delivery capacity | Different CF baselines — GSIs have mature build teams and global delivery |
| **Value Added Reseller** | Services growing but still secondary to resale | Moderate capabilities — services arm is meaningful but not primary |
| **Technology Distributor** | Services arm is new, primarily a sales channel | Lower build capacity, higher delivery volume — they move product at scale but consulting is emerging |

**How the Pillars apply:**

| Pillar / Dimension | GSI / VAR / Distributor interpretation |
|---|---|
| **Product Labability** | Underlying technologies scored identically to software companies. The practice area is the wrapper, not the subject of scoring. |
| **IV — Product Complexity** | Same as software — the technology's complexity doesn't change because a GSI deploys it |
| **IV — Market Demand** | Practitioner population + client end user population across all engagements |
| **CF — Training Commitment** | Do they invest in training their own consultants? Do they train client teams post-deployment? |
| **CF — Build Capacity** | Do they have a lab practice? Content development team? Instructional designers building technical training? GSIs often have strong build capacity; distributors are earlier in the journey. |
| **CF — Delivery Capacity** | How many consultants deliver training? How many client engagements per year? Global vs regional reach? |
| **CF — Org DNA** | Do they partner with technology vendors strategically? Are they already a Skillable partner? Do they value platform partnerships for hands-on learning? |

#### Industry Authorities (Certification Bodies)

**Why this matters.** Organizations like CompTIA, SANS Institute, EC-Council, ISACA, and the Swiss Cyber Security Institute are **Industry Authorities** — they define what professional competence looks like in their field, validate it through certifications, and maintain the standard. They are among Skillable's strongest existing customers. Their training programs and certification exams drive massive lab demand.

**Company badge:** Industry Authority.

**Discovery — same two-step extraction pattern:**

| Step | What the researcher finds | Example (CompTIA) |
|---|---|---|
| **1. Certification programs and training programs** | The wrapper — what they offer | CompTIA Security+, CompTIA Network+, CompTIA CySA+, CompTIA A+ |
| **2. Underlying technologies** | The labable products inside those programs | Wireshark, Splunk, pfSense, Linux CLI, Windows Server, Cisco IOS |

The certification program is the product. The technologies inside it are what gets scored for labability. CompTIA Security+ isn't labable by itself — it's the tools and environments that candidates need hands-on practice with that are labable.

**Estimated user base — two distinct populations, not one:**

| Population | Size | Why it matters |
|---|---|---|
| **Training participants** | Much larger | People taking courses to learn — this is the bigger lab opportunity for Skillable |
| **Certification candidates** | Smaller subset | People actually sitting for the exam — important but not the whole story |

The seller needs both numbers separately. "500,000 people take CompTIA Security+ training annually, 200,000 sit for the exam" tells a different story than just "200,000 certification candidates." The training population is the primary Skillable opportunity. The certification population is a subset with 100% adoption.

**Cert prep is where the lab volume lives.** Industry Authorities are known for their certifications — EC-Council's Certified Ethical Hacker, CompTIA's Security+, SANS GIAC. That's the marketing headline and why they're popular. But the lab opportunity is in the **certification preparation training**, not the exam itself. Cert prep courses, boot camps, and self-paced study programs generate far more lab hours than the exam does. The researcher should look for cert prep volume alongside exam candidate volume — "cert prep" is a keyword signal.

**ACV motions:**

| Motion | Population |
|---|---|
| **Training (the big one)** | All training participants across all delivery partners — the larger number |
| **Certification (PBT)** | Exam candidates only — smaller but 100% adoption per the standard model |
| **Partner Training** | ATPs and delivery partners who need to be trained to deliver the programs |

**Delivery partner network — Seller Briefcase context.** Industry Authorities typically have large partner networks delivering their programs. Pearson delivers certifications. ATPs deliver training. Knowing who delivers what helps the seller understand the ecosystem. "CompTIA has ~3,000 ATPs globally, Pearson handles exam delivery" is Seller Briefcase material — Account Intelligence, not Key Technical Questions.

**How the Pillars apply:**

| Pillar / Dimension | Industry Authority interpretation |
|---|---|
| **Product Labability** | Underlying technologies scored identically to software companies. The certification program is the wrapper. |
| **IV — Product Complexity** | Are the technologies covered by these certifications complex enough for hands-on practice? (Almost always yes — these certifications exist because the skills require practice.) |
| **IV — Market Demand** | Training participant volume + certification candidate volume. Industry Authorities often have the strongest Market Demand signals of any org type. |
| **CF — Training Commitment** | Definitionally strong — training IS their mission. Highest baseline tier. |
| **CF — Build Capacity** | Do they build labs themselves? Do they have content development teams? Many Industry Authorities partner with Skillable for lab building. |
| **CF — Delivery Capacity** | ATP network size, geographic reach, delivery modalities (ILT, self-paced, virtual). Often extremely strong. |
| **CF — Org DNA** | Typically strong partnership culture — they work through partners by design. Existing Skillable partnership is a direct signal. |

#### Enterprise Learning Platforms

**Why this matters.** Companies like Skillsoft, Pluralsight, Coursera (especially Coursera Business), and Udacity (acquired by Accenture) sell massive course catalogs to enterprises as all-you-can-eat training subscriptions. Their value proposition: "If you need training for anyone on anything, buy this catalog and all your needs are covered." The reality is that many organizations are realizing that checkbox training — watching videos and passing quizzes — doesn't ensure people actually develop skills or build confidence in doing things. As a result, these platforms are actively trying to embed hands-on labs within their learning journeys. Skillsoft is already one of Skillable's biggest customers for exactly this reason.

**Company badge:** Enterprise Learning Platform.

**Discovery — same two-step extraction, filtered to the technology catalog:**

| Step | What the researcher finds | Example (Skillsoft) |
|---|---|---|
| **1. Technology categories within the catalog** | The labable slice of their total course catalog | AWS Courses (450 courses), Cybersecurity Courses (300 courses), DevOps Courses (200 courses), Data Science Courses (150 courses) |
| **2. Underlying technologies** | The actual software products covered in those courses | AWS EC2/S3/Lambda, Splunk, Terraform, Kubernetes, Python/Jupyter |

The technology catalog is a subset of the total catalog. Leadership courses, soft skills, compliance — those aren't labable and should be filtered out. Only the technology portion matters for Skillable.

**Delivery modalities — context, not the product:**

| Modality | What it means | Scale | Examples |
|---|---|---|---|
| **On-demand / self-paced** | Labs embedded in the learning path — learner launches independently | Very high — millions of learners | Skillsoft catalog, Pluralsight, Coursera |
| **Instructor-led (ILT/VILT)** | Labs as part of a classroom experience — instructor guides learners | Lower per-session but high-value | Global Knowledge (now Skillsoft), New Horizons, QA |
| **Blended / hybrid** | Both — self-paced prep with instructor-led lab sessions | Growing model | Skillsoft post-merger, Pluralsight expanding into ILT |

The delivery modality is the HOW, not the WHAT. It affects Delivery Capacity scoring and how labs get embedded, but the technology categories are the products on the product chooser.

**Cert prep courses exist but are a subset.** Some catalog courses target specific certifications (CompTIA Security+ prep, AWS Solutions Architect prep). These are valuable but represent one slice of the total technology catalog. The broader opportunity is all technology courses that could benefit from labs, whether cert-aligned or not.

**Estimated user base — a learner funnel:**

| Step | What you're estimating |
|---|---|
| **1. Total learners on the platform** | Individual subscribers + enterprise client employees with access |
| **2. What % take technology courses** | Technology catalog is a slice of the total |
| **3. What % would consume labs** | Not every technology course has or needs labs — the labable subset |
| **4. Lab hours per learner** | Depends on learner type and course depth |

**Assigned vs self-directed learners — different consumption patterns:**

| Learner type | Behavior | Lab hours per learner |
|---|---|---|
| **Assigned (enterprise)** | Company assigns a course with 5 labs — they complete the full path | Higher consumption |
| **Self-directed (subscriber)** | Preparing on their own schedule, picks and chooses | Lower consumption — they take what they need |

The researcher can estimate which type dominates for each platform. Skillsoft is mostly enterprise-assigned (higher lab hours). Coursera skews more self-directed (lower lab hours). This distinction directly affects ACV without requiring impossible precision.

**ACV — lab hours consumed is the unit:**

The ACV opportunity is fundamentally about **lab hours consumed**. To estimate it:

- Number of learners likely to encounter a lab (the funnel above)
- Lab hours per learner (driven by assigned vs self-directed mix)
- Rate per lab hour (from the standard rate tier lookup)

The researcher won't get exact numbers. But it can get directional signals — total platform learner count (often published), relative size of the technology catalog, and the enterprise vs individual mix. That's enough for a believable range.

**How the Pillars apply:**

| Pillar / Dimension | Enterprise Learning Platform interpretation |
|---|---|
| **Product Labability** | Underlying technologies in the catalog scored identically to software companies. The course is the wrapper. |
| **IV — Product Complexity** | Are the technologies covered in the catalog complex enough for hands-on practice? |
| **IV — Market Demand** | Total learner volume on the platform taking technology courses. Often very large for major platforms. |
| **CF — Training Commitment** | Definitionally strong — training IS the entire business. Highest baseline tier. |
| **CF — Build Capacity** | Do they build labs? Do they have content development teams for technical courses? Post-merger companies (Skillsoft + Global Knowledge) may have strong ILT build capacity. |
| **CF — Delivery Capacity** | On-demand reach (millions of learners) + ILT capacity (classrooms, instructors, schedule). Both count. A platform that does both on-demand AND ILT has more paths to get labs in front of learners. |
| **CF — Org DNA** | Are they actively seeking to embed labs? Existing Skillable partnership is a direct signal. Platform openness to third-party integrations matters. |

#### ILT Training Organizations

**Why this matters.** Organizations like New Horizons, QA, and Global Knowledge (now part of Skillsoft) are primarily **instructor-led training** companies. Their business is classroom-based delivery — an instructor teaches a class, learners follow along in a lab environment, and the experience is guided and personalized. ILT organizations tend to be smaller than enterprise learning platforms but have high concentration: nearly every course is technology-focused and nearly every learner is hands-on.

**Company badge:** ILT Training Organization.

**Discovery — same two-step extraction:**

| Step | What the researcher finds | Example (QA) |
|---|---|---|
| **1. Technology categories in the course catalog** | What they teach | Microsoft Azure (45 classes), Cybersecurity (30 classes), AWS (25 classes), DevOps (20 classes) |
| **2. Underlying technologies** | The actual products used in those classes | Azure Portal, Azure CLI, Splunk, Terraform, Kubernetes, Cisco IOS |

**Key difference from enterprise learning platforms:** ILT organizations have much higher technology concentration. Most of their catalog IS technology training — there's less filtering needed. A company like QA may have some business skills courses, but the overwhelming majority are technical.

**Estimated user base = students per year in classrooms.**

| Signal | What it tells you |
|---|---|
| **Annual student count** | How many people literally sit in classes each year — often published or estimable from class schedule × class size |
| **Course schedule density** | How many classes run per week/month — a proxy for throughput |
| **Geographic reach** | One city vs national vs global — multiplier on student count |

These are countable, concrete numbers. An ILT org running 50 classes per week at 15 students each has ~39,000 student-seats per year. That's more precise than estimating enterprise learning platform funnels.

**Lab hours per learner — high by nature.** ILT courses are typically 3–5 day intensive classes where learners spend significant time in hands-on environments. An ILT student might consume 20–30 lab hours in a single week-long course. This is dramatically higher per-learner consumption than on-demand, where a learner might touch a lab for 30 minutes.

**ACV — same universal funnel:**

- Students per year in technology classes (the learner count)
- Lab hours per student (high — intensive classroom format)
- Rate per lab hour (standard rate tier from the technology's delivery path)

**How the Pillars apply:**

| Pillar / Dimension | ILT Training Organization interpretation |
|---|---|
| **Product Labability** | Underlying technologies scored identically — the class is the wrapper |
| **IV — Product Complexity** | ILT organizations naturally select for complex technologies — simple tools don't warrant a 5-day class |
| **IV — Market Demand** | Annual student volume, geographic reach, course schedule density |
| **CF — Training Commitment** | Definitionally strong — training IS the entire business. Highest baseline tier. |
| **CF — Build Capacity** | Do they author their own courseware and labs? Or do they deliver vendor-authored content? Authoring = strong build capacity. Delivery-only = lower. |
| **CF — Delivery Capacity** | Number of classrooms, instructors, locations. ILT delivery is inherently capacity-constrained (instructor + room + schedule), unlike on-demand which scales without friction. |
| **CF — Org DNA** | Partnership culture varies. Some ILT orgs are vendor-authorized (Microsoft CPLS, AWS Training Partner). Others are independent. Vendor authorization is a strong partnership signal. |

#### Content Development Firms

**Why this matters.** Companies like GP Strategies build learning programs on behalf of other companies. They don't own products, they don't typically deliver training, and they don't certify anyone. They are hired to create courseware, lab guides, and curriculum — built around their clients' products.

**Company badge:** Content Development Partner.

**Product Labability and Instructional Value do not apply.** Content development firms don't have their own labable products. They build for whatever technologies their clients need. Scoring Product Labability or Instructional Value for "GP Strategies" is meaningless — it would be scoring an empty wrapper.

**No Deep Dive.** There are no products to select and no scoring to do. The discovery pass gives you everything you need.

**How — the discovery workflow for content development firms.** The researcher runs the same discovery call but skips Tier 1 and Tier 2 (per-product fields) — there are no products to capture. It gathers Tier 3 (per-company signals) plus the technologies the firm covers and their build capacity indicators. The result is a partnership assessment stored in the same cache infrastructure as any other company — available to Prospector and Inspector.

**What discovery produces — a partnership assessment, not a product study:**

| What shows on the product chooser | What it means |
|---|---|
| **"Content Development Partner"** — no products listed, no Deep Dive button | This is a partner, not a prospect. The seller sees that immediately. |
| **Technologies they cover** | What kinds of programs they build — cybersecurity, cloud, data science, etc. |
| **Build capacity signals** | Team size, program volume, client portfolio |

**What marketing gets:** Partnership signal — build capacity, technologies they cover, potential Skillable content partner. Not ICP scoring, not product fit, not ACV. The conversation is different: "Can we partner with these people to help our mutual customers build labs?"

**Customer Fit dimensions still tell the partnership story:**

| Dimension | What it reveals |
|---|---|
| **Training Commitment** | How deep is their commitment to quality training content? |
| **Build Capacity** | This IS their core — team size, programs built, technologies covered |
| **Delivery Capacity** | Probably low — they build, they don't deliver. That's expected. |
| **Org DNA** | Platform partnership orientation? Do they work with technology vendors strategically? |

#### LMS / Learning Experience Platforms

**Why this matters.** Companies like Cornerstone, Docebo, Degreed, and Moodle sell learning management systems and learning experience platforms. They are a **hybrid** — they have a real, scorable software product AND they are a partnership opportunity. Their LMS is a deployed product with users, APIs, and identity management. But the bigger story is that their enterprise clients have thousands of technical courses in the LMS that could benefit from Skillable labs.

**Company badge:** LMS / Learning Platform.

**Two signals, one company:**

| Signal | What it does |
|---|---|
| **Product scoring** | Their LMS/LXP product gets scored normally — Product Labability, Instructional Value, Customer Fit. Can we embed Skillable labs inside their platform? |
| **Partnership flag** | Additionally flagged as a distribution partner — their customers' technical courses are lab opportunities for Skillable |

**Deep Dive: Yes — on their software product.** Unlike content development firms, LMS companies have a real product to score. Cornerstone's LMS has provisioning paths, identity management, APIs, scoring hooks. That's a legitimate Product Labability assessment.

**Discovery — two layers:**

| Layer | What the researcher finds |
|---|---|
| **Their product** | The LMS/LXP itself — deployment model, API surface, integration capabilities |
| **Their distribution opportunity** | How many enterprise clients, how many learners on the platform, what percentage of content is technical |

**ACV — two components:**

| Component | What it measures |
|---|---|
| **Product ACV** | Standard ACV for the LMS product — learners using the platform |
| **Distribution opportunity** | Downstream potential — if Skillable labs were embedded in their clients' technical courses, how many additional lab hours? This is the partnership upside. |

**How the Pillars apply:**

| Pillar / Dimension | LMS company interpretation |
|---|---|
| **Product Labability** | Their LMS software scored normally — can Skillable integrate with it? |
| **IV — Product Complexity** | LMS administration, configuration, integration — genuinely complex for admins |
| **IV — Market Demand** | Total learners on the platform + admin population |
| **CF — Training Commitment** | Definitionally strong — they exist to facilitate training |
| **CF — Build Capacity** | Do they build content or just host it? Hosting-only = lower build capacity |
| **CF — Delivery Capacity** | Platform reach — how many enterprise clients, how many learners |
| **CF — Org DNA** | Integration partnership culture? Open APIs? Marketplace for third-party content? These are direct Skillable integration signals |

### Company Classification

Company classification rules — badge derivation, the Enterprise Software threshold, specific company examples, and the `company_category` vs `org_type` two-field separation — are documented in **"Software Companies — The Anchor"** above. That section is the authoritative home for classification logic.

**Disambiguation — related but distinct companies.** Some company names resolve to multiple distinct organizations. The unified search field handles this:

| Search input | Disambiguation |
|---|---|
| "Siemens" | Siemens (Industrial / OT) vs Siemens Healthineers (Healthcare IT) — separate companies, separate products, separate scoring paths |
| "CSU" | Colorado State University vs California State University System — typeahead dropdown, user picks |

These are different companies with different badges, different products, and different scoring — not subdivisions of one analysis.

---

## Customer Motivation

**Why.** Every organization that invests in hands-on training does so for one or more reasons. Knowing the motivation lets the platform frame intelligence for the persona and surface the right conversation starters.

**What — three motivations:**

| Motivation | Core drive | The stakes | Signals |
|---|---|---|---|
| **Product adoption** | People use it, love it, don't churn | Revenue — if they don't adopt, they cancel | Customer enablement programs, adoption risk language, TTV concerns |
| **Skill development** | People are competent, certified, employable | Careers — if they can't do it, they can't get the job | Certification programs, university curricula, career-track training |
| **Compliance & risk reduction** | People don't make dangerous mistakes | Consequences — if they get it wrong, real harm happens | Regulatory requirements, healthcare / finance / cybersecurity contexts, audit readiness |

**How.** Motivations are **not mutually exclusive** — a single organization (even a single product) can have multiple. They are **contextual to the persona** — the same intelligence may be framed differently depending on who it's being served to (sellers see adoption, training-side personas see skill development, regulated industries surface compliance regardless). This connects directly to GP1.

All motivations lead to confidence. None are negative. All genuinely care about the learner: product adoption wants the learner confident *in the product*; skill development wants the learner confident *in themselves*; compliance wants the learner confident *under pressure*.

---

## The People

### Two Audiences, One Hard Wall

| Audience | Tools | Purpose |
|---|---|---|
| **Skillable internal** | Prospector + Inspector | Target the right companies, prepare for conversations, research products |
| **Customers (eventually) + Skillable ProServ** | Designer | Build lab programs based on product intelligence |

**Customers never see Prospector or Inspector data. Ever.** This boundary is architectural — not just a permissions layer. There is no path from Designer to company intelligence data. See "Data Architecture: Three Domains" below for how the hard wall is enforced.

### Personas by Tool

**Prospector (ICP Validation & Prioritization)** serves Marketing and RevOps. Its primary job is to take marketing's existing company lists — ICP targets and expansion targets — and return them **re-ranked by ACV potential with evidence-based rationale**. Marketing currently ranks by company size; Prospector ranks by labable products × real users × training buyer signals. That shift — from "big company = good target" to "labable products with real demand from a real training buyer = good target" — is the core value.

Prospector uses the **same discovery data** as Inspector. Every company Prospector researches is cached and immediately available for a Deep Dive in Inspector. Intelligence compounds (GP5) — the more companies Prospector processes, the richer the platform's data gets for everyone.

**What Prospector delivers today:**

| Capability | What it does |
|---|---|
| **ICP reprioritization** | Take marketing's target list, run discovery on each company, return the list re-ranked by ACV potential with product-level evidence |
| **Expansion targeting** | Same intelligence applied to existing Skillable customers — "here's what else this customer could be doing with us" |

**What Prospector delivers later (in priority order):**

| Capability | What it does |
|---|---|
| **HubSpot integration** | Authenticated write-back — discovery intelligence flows directly into HubSpot company and deal records, shown to the right person at the right time |
| **Product Lookalikes** | Companies marketing didn't know about, found because they use products that pass Product Labability — product-fit matching, not firmographic matching |
| **Contacts** | Specific humans responsible for training / enablement for products Skillable can serve |

Prospector's principle: deliver intelligence to marketing where they work (HubSpot), not where we work. The CSV/spreadsheet output is the interim step; HubSpot integration is the destination.

**Inspector (Evaluation & Research)** serves the spectrum from sellers to deep technical roles:

| Persona | What they need | Where they start |
|---|---|---|
| Sellers (AE, Account Directors) | Product-fit confirmation, buying signals, conversational competence | HubSpot — click deeper when needed |
| CSMs | Expansion opportunities, product fit for upsell | HubSpot — click deeper when needed |
| SEs | Deep product research, technical detail, orchestration specifics | Inspector directly |
| TSMs | Same as SEs — technical depth | Inspector directly |

**Designer (Program Design)** serves the builders — the people who have already decided to create labs:

| Persona | Role |
|---|---|
| Enablement / Training Program Owners | Strategy — which audiences, what outcomes, how many labs |
| Instructional Designers | Learning experience design — sequencing, objectives, assessment |
| SMEs | Product accuracy — what's worth teaching, what's realistic |
| Tech Writers | Lab content — instructions, steps, guidance |
| Product Engineers | Technical feasibility — what can be done, how it works |
| Skillable Professional Services | All of the above, on behalf of customers |

### Conversational Competence

**Why.** Sellers talking to technical buyers need to understand the product. SEs recommending programs need to understand the instructional case. Neither starts competent. The platform's job is to close both gaps.

**What.** Conversational competence is bidirectional:

| Who | Gap direction | What competence looks like |
|---|---|---|
| Sellers / CSMs | Toward product understanding | "I understand the purpose of your product, why hands-on training makes sense for it, and how Skillable fits. I'm not an architect, but I'm not wasting your time." |
| SEs / Technical folks | Toward instructional-design understanding | "I understand why specific lab types matter for specific learning outcomes. I can recommend the right labs, not just build the environment." |

**How.** Built through GP2 — every Pillar card leads with the Why. Starting with Why creates common ground between technical and non-technical people. It is the universal starting point.

### Progressive Disclosure Stack

**Why.** Different people need different depths. Nobody should be forced to see more than they need, and nobody should be locked out of going deeper.

**What.** The entire platform is one continuous progressive-disclosure path — one intelligence stream at increasing depth. Tool boundaries are entry points based on who you are.

| Layer | What you see | Who starts here |
|---|---|---|
| HubSpot card | Fit confirmation, key badges, "worth pursuing" confidence, ACV signal, HubSpot ICP Context | Marketing, Sellers, CSMs |
| Inspector Product Selection | All discovered products for a company — sorted by popularity, labability tier badges (Promising / Potential / Uncertain / Unlikely), subcategory, deployment model | SEs, TSMs (or anyone who clicked deeper) |
| Inspector Full Analysis (dossier) | Overall assessment, three Pillar cards, Seller Briefcase, bottom row | Anyone exploring a company |
| Pillar cards with evidence on hover | Technical detail — labability dimensions, features, orchestration specifics | SEs, TSMs digging into a specific product |
| Designer | Lab series, lab breakdown, activities, scoring, instructions, bill of materials | Program Owners, IDs, SMEs, Tech Writers, ProServ |

### Seller Briefcase

**Why.** Conversational competence (GP2) needs to be delivered in the most practical form possible. Sellers don't want to read a report — they want to know *what to say* and *who to say it to*.

**What.** Below the three Pillar cards in the dossier, each Pillar contributes a **briefcase section** — 2–3 sharp, actionable bullets that arm the seller for conversations.

| Section | Under which Pillar | What it gives the seller |
|---|---|---|
| **Key Technical Questions** | Product Labability | Who to find at the customer, what department, and the specific technical questions that unblock the lab build. Includes a verbatim question the champion can send. **These are questions TO ASK the customer** — action items for the seller, not evidence about the product. |
| **Conversation Starters** | Instructional Value | Product-specific talking points about why hands-on training matters for this product. Makes the seller credible without being technical. **Market Demand evidence** (Stack Overflow activity, install base size, cert ecosystem presence) belongs here as proof the training market exists — it is NOT a Key Technical Question. |
| **Account Intelligence** | Customer Fit | Organizational signals — training leadership, org complexity, LMS platform, competitive signals, news. Context that shows the seller has done their homework. |

**How.** Each section is a **separate Claude call with its own focused system prompt**, on the model best suited to its purpose. All three per product run in parallel:

| Section | Model | Why this model |
|---|---|---|
| **Key Technical Questions** | Opus 4.6 | Sales-critical synthesis — must be sharp, specific, answerable |
| **Conversation Starters** | Haiku 4.5 | Pattern-matched, fast — product-specific talking points |
| **Account Intelligence** | Haiku 4.5 | Pattern-matched, fast — surface organizational signals |

Briefcase scope: **Key Technical Questions and Conversation Starters are per-product** — they swap when the user picks a different product from the dropdown. **Account Intelligence is per-company** — it stays the same regardless of which product is selected because it's about the organization, not the product. Account Intelligence must never reference product-specific labability or product-specific capabilities. It covers company-level signals: leadership changes, funding rounds, new partnerships, events, competitive landscape, news. *(Clarified 2026-04-12)* Cached products keep their cached briefcase — only newly scored products get a fresh generation.

**Briefcase formatting:** Each bullet uses **Bold Label:** followed by the content. Use a colon after the bold label, not an em dash. Example: **Confirm NFR Path:** Solution Architect or Sales Engineering Lead... *(Locked 2026-04-12)*

---

## Scoring Framework at a Glance

**Why.** One composite Fit Score answers "should we pursue this?" It has to reflect both the product (can we lab it? is it worth labbing?) and the organization (will the opportunity actually happen?). 70% of the score is about the product because the product truth is the hard constraint — a great customer with an unlabbable product is not a Skillable opportunity. 30% is about the organization because even the most labbable product goes nowhere if the customer isn't a training buyer.

**What — the hierarchy:**

- **Fit Score** (composite, 0–100) — made up of three Pillars
  - **Pillars** (three) — the weighted components of the Fit Score
    - **Dimensions** (four per Pillar) — specific areas measured within each Pillar
      - **Requirements / facts** — the most granular level; what the researcher extracts into the fact drawer

**The 70/30 Split:**

| Level | Pillars | Combined weight |
|---|---|---|
| **Product** | Product Labability + Instructional Value | 70% |
| **Organization** | Customer Fit | 30% |

**The Three Pillars:**

| Pillar | Weight | Level | UX Question |
|---|---|---|---|
| **Product Labability** | 50% | Product | How labable is this product? |
| **Instructional Value** | 20% | Product | Does this product warrant hands-on training? |
| **Customer Fit** | 30% | Organization | Is this organization a good match for Skillable? |

Product Labability is weighted 50% because it is the gatekeeper — if Skillable cannot get the product into its platform, nothing else matters. Instructional Value and Customer Fit are important supporting signals, but they cannot compensate for an unlabable product. The 50/20/30 split makes the math match the philosophy. *(Rebalanced from 40/30/30 on 2026-04-12 after reviewing Workday, Trellix, Cohesity, and Diligent scored analyses.)*

**How.** Each Pillar scores out of 100 internally, then gets weighted. A Product Labability score of 85 contributes 85 × 0.50 = 42.5 points to the Fit Score. **Full operational detail — every dimension, every scoring signal, every baseline, every penalty, every strength tier — lives in `Badging-and-Scoring-Reference.md`.** This document does not duplicate that detail.

### Fit Score Composition

**Why.** A pure 70/30 weighted sum lets a product with weak Product Labability still score Solid Prospect when Instructional Value and Customer Fit are strong. That's not honest — if we cannot lab the product, the instructional case and organizational signals don't save us. The platform's value proposition is lab-based training.

**What.** The Technical Fit Multiplier scales **IV + CF contributions only** by a factor derived from the PL score and orchestration method, enforcing an asymmetric coupling rule:

> **Weak PL drags IV + CF contribution down. Weak IV or weak CF does NOT drag PL contribution down.**

**How.** `fit_score_composer.compose_fit_score` applies the math:

```
pl_contrib = pl_score × (pl_weight / 100)
iv_contrib = iv_score × (iv_weight / 100) × multiplier
cf_contrib = cf_score × (cf_weight / 100) × multiplier
fit_score  = clamp(round(pl_contrib + iv_contrib + cf_contrib), 0, 100)
```

The multiplier lookup lives in `scoring_config.TECHNICAL_FIT_MULTIPLIERS`. Full table with worked examples in `Badging-and-Scoring-Reference.md` → "Technical Fit Multiplier."

---

## Two Hero Metrics — Fit Score + ACV Potential

**Why.** Sellers and execs ask two questions about every opportunity: *should we pursue this?* and *how big is it if we win?* They are different questions with different answers, and forcing them into one number loses information.

**What — two separate outputs:**

| Metric | What it answers | Scope | Type |
|---|---|---|---|
| **Fit Score** | Should we pursue this? | **Per-product** — each product in the portfolio gets its own Fit Score | Qualitative composite of three Pillars (0–100) |
| **ACV Potential** | How big is this if we win? | **Per-company** — one ACV number for the whole company, broken out by use case | Calculated business metric — dollars per year. Five use-case motions × flat rates, sized by an AI audience judgment. See `ACV Potential Model` below. |

**How.** Both render in the hero section at the top of every company view and Prospector row. The Fit Score swaps as the user switches products in the dropdown. The ACV Potential hero is **company-level** and does not change across product selections — the five use-case breakdown below the hero is also company-level, not per-product. ACV values use lowercase `k` for thousands and uppercase `M` for millions (e.g., `$250k`, `$1.2M`).

---

## Verdict Grid

**Why.** "Score = 74" doesn't tell a seller what to *do*. The verdict combines Fit Score and ACV into an action label — *Prime Target*, *Worth Pursuing*, *Keep Watch*, *Poor Fit* — so sellers can prioritize without having to interpret the numbers.

**What — the score color spectrum:**

| Score range | Color |
|---|---|
| ≥80 | Dark Green |
| 65–79 | Green |
| 45–64 | Light Amber |
| 25–44 | Amber |
| <25 | Red |

**ACV tiers:** High, Medium, Low.

**The grid:**

| Score | High ACV | Medium ACV | Low ACV |
|:---:|:---:|:---:|:---:|
| **≥80** | Prime Target · Dark Green | Strong Prospect · Dark Green | Good Fit · Dark Green |
| **65–79** | High Potential · Green | Worth Pursuing · Green | Solid Prospect · Green |
| **45–64** | Assess First · Light Amber | Keep Watch · Light Amber | Deprioritize · Light Amber |
| **25–44** | Assess First · Amber | Keep Watch · Amber | Deprioritize · Amber |
| **<25** | Keep Watch · Red | Poor Fit · Red | Poor Fit · Red |

**Verdict definitions:**

| Verdict | What it communicates |
|---|---|
| **Prime Target** | Best possible combination. Build a strategy, align the team. |
| **Strong Prospect** | Great fit, meaningful opportunity. Pursue with confidence. |
| **Good Fit** | The fit is real. Worth your time. |
| **High Potential** | Gaps to work through but significant upside justifies the investment. |
| **Worth Pursuing** | Good fundamentals all around. Give it attention. |
| **Solid Prospect** | Decent fit, modest opportunity. Steady. |
| **Assess First** | Low fit today, but the opportunity is big. Do the homework before deciding. |
| **Keep Watch** | Not ready today. Opportunity is big enough to stay close and revisit when conditions change. |
| **Deprioritize** | Low fit, small opportunity. Focus elsewhere. |
| **Poor Fit** | Products don't align. Be honest about it. |

The grid and definitions are configured in `scoring_config.VERDICT_GRID`. This document is the Define-Once home for the verdict vocabulary. `Badging-and-Scoring-Reference.md` does not redefine these terms.

---

## ACV Potential Model

**Why.** Sellers and marketing ask two questions about every opportunity: *how big is this deal if we win?* and *where does the revenue actually come from?* ACV Potential answers both — a single company-level dollar figure, broken into five use-case motions. It's the sizing number that pairs with the Fit Score's "should we pursue this" question.

**What — company-level by construction.** ACV Potential is one number per company. Per-product ACV does not exist in this model. Five use-case motions × flat annual rates per human × a Product Labability harness equals the company total. This is the Define-Once home for the ACV model; `Badging-and-Scoring-Reference.md` references this section rather than restating it.

### The Five Use-Case Motions

Each motion counts a specific, countable human population for the coming year — not a percentage of something bigger. One flat rate per motion applies across all organization types. Define-Once source: `scoring_config.MOTION_METADATA`.

| Motion | Who that is | Rate |
|---|---|---|
| **Customer Training** | Humans being trained on the company's products this year — directly or through ATPs. The person consuming labs where someone pays Skillable for the lab hours. | ~$200/person/year |
| **Partner Training** | Partner employees — GSI / VAR / distributor consultants, SEs, solution architects being trained to sell, deploy, or support the products. | ~$200/person/year |
| **Employee Training** | Technical employees at this company, trained on their own products — product team, SEs, support engineers, trainers. Always a fraction of total headcount. | ~$200/person/year |
| **Certification** | Humans who sit the product's certification exam each year. Not training candidates — actual exam sitters. | ~$10/person/year |
| **Events** | Attendees at the company's flagship events (conferences, summits) with hands-on lab tracks. | ~$50/attendee/year |

The $200/person/year figure for Customer / Partner / Employee Training represents a blended training relationship — multiple lab hours across cert prep + enablement + ongoing skill development. The $10/person/year for Certification reflects the ~1 lab hour of a PBT exam delivery. The $50/attendee/year for Events reflects conference-scale lab tracks. Rates are grounded in Skillable economics, calibrated against known-customer revenue.

### How the Number Is Produced

**Step 1 — Judgment call (one narrow Claude turn per company).** A focused AI grader (sibling pattern to `rubric_grader.py`, living in `backend/audience_grader.py`) reads the discovery data and produces five audience integers plus per-motion rationale and confidence.

**Inputs** — entirely from the discovery data already captured:
- Per-product Tier 1/2 facts: name, category, deployment_model, `estimated_user_base`, target_personas, api_surface, cert_inclusion, complexity_signals, rough_labability_score
- Per-company Tier 3 facts: training_programs, training_leadership, atp_program, delivery_partners, events, partnership_pattern, engagement_model, lab_platform, org_type
- Anonymized calibration block: known-customer magnitudes grouped by stage, with customer names redacted

**Output:**

```python
{
  "audiences": {
    "customer_training":  int,
    "partner_training":   int,
    "employee_training":  int,
    "certification":      int,
    "events":             int,
  },
  "confidence": "low" | "medium" | "high",
  "rationale": str,
  "per_motion_rationale": dict[str, str],
  "per_motion_confidence": dict[str, str],
  "key_drivers": list[str],
  "caveats": list[str],
  "market_demand_story": str,
}
```

The call is narrow — one Claude turn, ~$0.05 on Sonnet. It never does dollar math; it outputs audience integers and reasoning only.

**Step 2 — Deterministic Python math.** For each motion: `motion_acv = audience × rate`. Sum: `raw_company_acv = Σ motion_acv`. Rates come from config; the math is trivial and fully inspectable.

**Step 3 — Product Labability harness.** Filters the total for what Skillable can actually deliver as labs. The judgment call estimates total training demand (which exists regardless of whether Skillable can deliver it); the harness filters that demand for Skillable addressability.

```
popularity_weighted_pl = Σ(product.rough_pl × product.user_base) / Σ(product.user_base)
harness = popularity_weighted_pl / 100
company_acv = raw_company_acv × harness
```

Popularity-weighted PL prevents broad portfolios from being punished by niche products: a company where the flagships are labable and the niche tools aren't keeps most of the harness credit. A company where the flagships aren't labable (Workday, ServiceNow) loses most of it regardless of niche-product breadth.

Pre-Deep-Dive uses `rough_labability_score` per product (researcher's directional estimate). Post-Deep-Dive uses the real PL score for products that have been scored, rough for the rest. The harness sharpens naturally as more products get Deep-Dived.

### When the Judgment Call Fires

| Event | Fires? |
|---|---|
| Fresh discovery | Always |
| Discovery refresh (default 45 days after last run) | Always |
| Deep Dive that merges new company-level signals (new ATP count, new event, changed partnership_pattern) | Yes — judgment re-fires with richer context |
| Deep Dive with no new company-level signals | No — existing audience estimates reused, harness updates with the new product's real PL |

Result: company ACV is stable between events, re-grounded when new company-level information arrives or on the refresh cadence. Deep Dives sharpen the per-product Fit Score and the harness without churning the audience estimates.

### Org-Type Framing

The judgment call prompt names what "audience" means for each organization type explicitly, so Claude interprets the same audience label correctly across very different business models:

| Organization type | Customer Training audience = |
|---|---|
| Software / Enterprise Software | Customers worldwide who pay for training on the company's products this year |
| Enterprise Learning Platform (Pluralsight, Skillsoft, CBT Nuggets) | Subscribers consuming the technology portion of the catalog this year — fraction of total platform learners |
| ILT Training Organization (New Horizons, LLPA, AXcademy) | Students in this org's classrooms and virtual ILT courses this year — bounded by the org's own delivery capacity |
| Academic Institution | Students enrolled in technology programs this year — not total enrollment |
| Systems Integrator / VAR / Technology Distributor | Consultants in the practice area this year — internal practitioners, not the underlying technology's global market |
| Industry Authority (CompTIA, SANS, EC-Council) | Annual training candidates — not lifetime cert holders |

The other four motions follow analogous per-org-type framing. Full prompt text lives in `backend/audience_grader.py`.

### Partnership-Only Org Types — Content Development Firms

**Why.** Content Development firms (GP Strategies, Waypoint Ventures, NetLogon-class partners) build learning programs for other companies' clients. They have no products to score, no audience that fits the motion model, and no direct Skillable revenue story. Their opportunity is downstream — if they partner with Skillable to power their client lab builds, revenue flows through those client engagements.

**What.** Content Development is a short-circuit org type. Before the judgment call fires, the pipeline checks `org_type`. For `CONTENT_DEVELOPMENT`, it returns a partnership result shape (audiences all zero, `acv_type = "partnership"`) without calling Claude.

| Surface | Display |
|---|---|
| Prospector row | Purple "Partnership" chip instead of a dollar range |
| Inspector | Partnership-focused dossier: Build Capacity signals, technologies covered, no Fit Score, no Deep Dive button |

### Calibration Anchors

**Why.** Without calibration, Claude can produce plausible-sounding but commercially off numbers — $50M for mid-market prospects, $100K for enterprises. The judgment needs a sense of "what real customers look like" to keep grounded.

**What.** `backend/known_customers.json` (gitignored — confidential revenue data) is the source of truth. It holds real Skillable customers with `current_acv`, `stage`, and optional `acv_potential_low/high`. A builder function assembles an **anonymized stage-grouped magnitude block** that the judgment call prompt includes:

```
Stage 'saturated' (N reference customers): current ACV $X–$Y, estimated Potential $A–$B
Stage 'mid' (N reference customers): ...
Stage 'first-year' (N reference customers): ...
```

Customer names never enter the prompt — the block shows only magnitudes and stage groupings. The committed `backend/known_customers.template.json` documents the schema; production deployments mount the real file.

**Commercial reality the prompt names explicitly:**
- Microsoft is the ceiling benchmark — ~15-year partnership, Skillable as their lab provider
- Most companies land in the $500K–$5M range
- A handful reach $5M–$20M
- Non-Microsoft numbers above $20M should trigger skepticism — only Accenture and Deloitte have realistic three-year paths to that tier, and only because those relationships are in motion

### Sharpening: Discovery → Deep Dive

Company ACV is set at discovery by the judgment call. Deep Dive doesn't churn it. Specifically:

| Deep Dive impact | Effect on company ACV |
|---|---|
| Real PL score replaces rough for one product | Harness shifts slightly (that product's weight × PL delta). Company ACV nudges. |
| Real IV rubric grades produced | Feeds per-product Fit Score on Inspector card. No direct ACV effect. |
| Real CF rubric grades produced | Feeds Fit Score. Company-unified (Phase F). No direct ACV effect. |
| Deep Dive surfaces new company-level signals | Judgment call re-fires with richer context. New company ACV. |
| Nothing company-level changed | Judgment cached. Company ACV stable. |

The "Deep Dive makes it skyrocket" pattern that plagued earlier architectures is structurally impossible here: ACV comes from the company total, not from per-product numbers summed upward. A Deep Dive can only reshape the harness or re-ground audiences via new company-level context.

### What Per-Product Still Tells You

Per-product cards on Inspector carry Product Labability, Instructional Value, Customer Fit (shared per company), the composite Fit Score, competitive product pairings, and badges + evidence per dimension. They do **not** carry a dollar ACV — ACV is company-level only. Marketing's Prospector row surfaces the per-product labability tier counts (Promising / Potential / Uncertain / Unlikely) for portfolio scannability alongside the company-level dollar ACV.

### Lineage — Mark Mangelson's CRO Framework

The five-motion model derives from Mark Mangelson's (CRO) labability estimation prompt, which identified nine audience/revenue categories with flat per-head annual rates. This framework consolidates Mark's nine into five:

| Mark's categories | Our motion |
|---|---|
| #3 — B2B customers being trained | Customer Training |
| #5 — Partners | Partner Training |
| #1 — Technical employees (also Mark's #6 sales personnel and #7 support personnel bundled in) | Employee Training |
| Subset of #3 (exam sitters) | Certification |
| #8 — Customer events | Events |

**Intentionally excluded:** Mark's #2 (total employees × $20) — counting all employees at a low rate inflates for non-technical workforces. Mark's #4 (technical SKUs × $25/customer) — our product-level PL harness filters what's actually labable. Mark's #9 (enterprise SKU flat $75K) — Skillable platform revenue, out of scope for lab-hour ACV.

**Intentionally simpler than Mark on rates:** Mark's flat rates without adoption or hours; ours is also flat (no per-product rate tiers, no adoption %, no hours multiplication) because flat rates across all orgs are consistent and trustworthy. Mark's own framework tested "close enough" on real customers. This framework should match or improve that calibration with richer signal input.

All ACV math is implemented in `acv_calculator.py`. Rate constants come from `scoring_config.MOTION_METADATA`. Tier thresholds come from `ACV_TIER_HIGH_THRESHOLD` and `ACV_TIER_MEDIUM_THRESHOLD`.

---

## Inspector UX

### Unified Search Field

**Why.** Users shouldn't have to know whether they're searching for a company or a product — the system figures it out. A single search field reduces friction and handles the common case where someone types a product name when they mean the company behind it.

**What.** One input field: "Search for a company or product." The system resolves the input before running discovery.

| Input | Resolution |
|---|---|
| Exact company match (e.g., "Cisco") | Straight to discovery |
| Ambiguous match (e.g., "CSU") | Typeahead dropdown with disambiguation: "Colorado State University," "California State University System," etc. User picks, then discovery runs |
| Product name (e.g., "Trellix Endpoint Security") | System resolves automatically — runs discovery on Trellix (the parent company) with Endpoint Security identified as a product. No confirmation needed. |
| Company and product are the same name (e.g., "Splunk") | Works directly — no disambiguation needed |
| Former name (e.g., "RStudio") | Resolves automatically to Posit. No confirmation needed. |

**How.** Resolution happens before discovery fires. Ambiguous matches (multiple companies with similar names) use a typeahead dropdown — the user must pick. Everything else resolves automatically: product-to-company mapping, former names, and exact matches just go. No unnecessary confirmation steps. The system makes the right call and moves.

### Product Family Interstitial

**Why.** When a company has a large product portfolio (Cisco, Oracle, Microsoft), showing all 20–30 products on one screen is overwhelming. The interstitial lets the seller narrow by category before seeing individual products.

**What.** The interstitial groups discovered products by **category** (not product family — categories are derived from the products themselves). Each category row shows the count of products in that category and the flagship products within it.

**When it appears.** Only when the discovered product count exceeds ~15–20 products. Below that threshold, the interstitial is skipped entirely and the seller goes straight to the product chooser. For Posit (3–5 products), Sage (5–8), Commvault (3–4) — no interstitial. For Cisco (25+), Oracle (30+) — the interstitial earns its place.

### Product Chooser

**Why.** The product chooser is where the seller decides which products to Deep Dive. It must answer two questions at a glance: **which products matter most** (popularity) and **which products can Skillable likely serve** (labability). The same discovery data that populates this page feeds the Prospector results table — one research pass, two consumers.

**What.** Products are sorted by **estimated user base** (most popular first), not by labability tier. Labability is shown as a badge on each product, not as the grouping mechanism. The layout has three columns:

| Left column | Middle column | Right column |
|---|---|---|
| **About the product** | **How it works** | **Labability judgment** |
| Product name | Deployment model (installable / cloud / hybrid / saas-only) | Promising / Potential / Uncertain / Unlikely |
| Subcategory | | |
| Popularity indicator | | |
| Flagship / Satellite tag | | |

The right column is **visually separated** from the other two — it is the one judgment call in the row. Everything else is factual. The labability tier is the researcher's rough pre-Deep Dive estimate and must read as directional, not definitive.

**How.** Ranking is derived from the discovery data — `estimated_user_base` drives sort order, `rough_labability_score` maps to the four tier labels, `subcategory` and `deployment_model` provide context. No separate ranking step needed.

### Hero Section

The hero section is the star of the show. Layout:

- **Left:** Product selector dropdown with verdict badge and "HIGH FIT · HIGH ACV" label
- **Center:** Fit Score — large and prominent
- **Right:** ACV Potential widget (three-line structure above)

No connector lines between hero and pillars. Pillar card padding balanced top/bottom.

### 70/30 Visual Split

The dossier body uses a 70/30 visual split reflecting the 70/30 product-vs-organization weighting:

- **Left (70%):** Two product Pillar cards — Product Labability and Instructional Value
- **Right (30%):** Customer Fit card, slightly different background to visually distinguish the organizational perspective

### Pillar Cards

Each Pillar card header has two icons at the same size, muted color, green on hover:

- **Info icon (?)** — opens the framework documentation section explaining how that Pillar works
- **Doc icon** — opens the full framework documentation

All dimension names display in ALL CAPS within the cards. Score bars use a **color gradient reflecting the score as a percentage of the dimension cap**: green for strong scores (≥70% of cap), transitioning through amber for moderate scores (40–69%), to red for weak scores (<40%). The gradient is continuous — a dimension at 60% of its cap shows a distinctly different hue than one at 90%. A green bar on a dimension at 4/30 is a trust failure (GP3). *(Locked 2026-04-12)*

### Badge System

**Why.** Badges carry the visible story of a dimension's score. They are immediately readable, evidence-backed, and never drive the math. A badge is *context on a score*, not the score itself.

Each dimension card renders 2–4 badges. Every badge carries an evidence payload on hover (1.5-second delay → modal with evidence bullets, source, confidence). Purple is for classification (product subcategory, company classification), not scoring.

**Full operational detail — the four scoring colors and their meanings, the confidence language (`confirmed` / `indicated` / `inferred`), the badge naming rules, canonical vocabulary, per-dimension badge catalogs, and penalty signals — lives in `Badging-and-Scoring-Reference.md`.** This document does not duplicate that content.

### Navigation and Controls

- **Two nav links:** "Back to Product Selection" and "Search Another Company"
- **Cache date:** hoverable link; tooltip reads "Refresh cache"
- **Export:** Word export (not PDF) — sellers customize the document for their conversations

### Three-Box Bottom Row — Shared Pattern

**Why.** The three boxes at the bottom of the company view — Scored Products (left), Competitive Products (middle), ACV by Use Case (right) — should read as **one designed row**, not three independent components. Visual coherence builds trust (GP3) and makes the dossier feel like one intelligent surface.

**What — one shared pattern across all three:**

| Element | Rule |
|---|---|
| Font family | Same across all three |
| Font size | Same across all three — section titles match, body rows match |
| Vertical spacing | Row padding, row gap, header-to-body spacing all identical |
| Section title style | Same font, size, treatment across all three titles |
| Link style | **Arrow links** (→) — de facto platform standard, locked |

**The one intentional differentiator — middle box only.** Competitor product names render in **slate blue**. That's it. Color is the one visual signal that earns its own treatment because "competitors vs us" is the one distinction worth calling out. Everything else about the middle box (typography, spacing, layout) matches the other two exactly.

**The right box is structurally unique because the content demands it** — four columns (Audience, Adoption, Hours, Annual Hours) plus footer rows (Annual Hours total, Annual Potential range, Rate + delivery path note). Tight column widths prevent line wrap. Right-aligned numeric columns. But the visual pattern (font, size, spacing) matches the other two boxes. The right box must **not** have a purple hairline (that's a middle-box treatment) and must **not** have a black background (should match the rest of the row).

This is GP4 (Self-Evident Design) applied at the UX layer — one typography pattern, one spacing pattern, one link style, defined once, used everywhere.

### Company Classification

Company classification badge uses purple — same color as product subcategory badges. Purple is for classification, not scoring.

---

## Prospector UX

**Why.** Marketing currently ranks their ICP by company size using firmographic data from tools like ZoomInfo. Prospector replaces that with product-level intelligence — which products are labable, how many people use them, and whether the organization is a training buyer. The shift from "big company" to "labable products with real demand" is how Skillable avoids wasting outreach on companies that look good on paper but can't use the platform.

**What — the workflow:**

| Step | What happens |
|---|---|
| **1. Input** | Marketing pastes company names OR uploads a CSV. One input area — same unified search field as Inspector. Optional checkbox: "Perform Deep Dive on top product" runs a full scoring pass on each company's flagship product automatically. |
| **1a. Estimator** | A live cost/time estimator in a right-side column next to the input area. Updates as companies are added. Shows estimated API cost (mid-to-mid-high) and wall time. Updates when Deep Dive checkbox is toggled. GP1: right information at the right time — the user knows the commitment before clicking Run. |
| **2. Discovery** | Prospector runs the standard discovery on each company — same research pass, same three-tier data shape, same caching. All discovered companies and their products are stored and available for Inspector Deep Dives immediately. Per-company timeout: 3 minutes for discovery, 5 minutes for Deep Dive. Failed companies show in results with an error flag — user can re-run. Companies process in parallel where possible. |
| **3. Results table** | All companies displayed in one view, sorted by ACV potential, with product-level evidence. Companies with Deep Dive data show sharpened Fit Score and ACV. This is the core of Prospector. |
| **4. Export** | CSV download with the same columns for import into HubSpot or other marketing tools. |

### Discovery-Level ACV Estimation (Option 2 — Holistic)

**Why.** Marketing needs a defensible per-company ACV Potential for 300+ companies in the Prospector list without running Deep Dives on every one. An early version of this used a Python heuristic stack — tiered caps × 4% adoption × hours × rate, summed across products and capped at $5M — but the heuristic produced systematically wrong answers. Nutanix undersold; LLPA over-shot by two orders of magnitude; school districts with real budget lines landed at $18k. The root cause was that per-product math cannot reason about the whole picture — the interaction between partner ecosystems, certification programs, existing DIY platforms, known customer relationships, and stage of maturity.

**What — Option 2: a single Claude call produces one holistic ACV estimate per company.** The researcher runs once at discovery time, sees the full picture (all products + company-level training signals + org type + calibration anchors + known-customer constraints), and returns one typed JSON object: `{acv_low, acv_high, confidence, rationale, key_drivers, caveats}`. The entire five-motion framework still applies — but it applies in Claude's reasoning, not as a Python formula. The output is anchored by deterministic guardrails (described below) and surfaces with full evidence in the Prospector table.

| Field | What it carries |
|---|---|
| **`acv_low` / `acv_high`** | Integer-dollar range, tight when signals are strong (high ≤ 2× low), wider when honest uncertainty exists |
| **`confidence`** | `low` / `medium` / `high` / `partnership` — guardrail-driven, downgrades automatically when range is too wide or sanity checks fail |
| **`rationale`** | 80–180 word paragraph explaining how the range was derived, with specific references to products, signals, and peer anchors |
| **`key_drivers`** | 3–5 short sentences, each tying the estimate to a specific signal — product user base, training infrastructure, partner ecosystem, event presence, cert program |
| **`caveats`** | 0–3 uncertainties the model wants the seller to see (e.g. "employee subset estimated, not researched") |

**How — guardrails are the trust layer.** The Claude call is anchored by deterministic Python rules that run before the output reaches the user. These are Define-Once in `scoring_config.py`:

| Guardrail | Behavior |
|---|---|
| **Company hard cap** | `HOLISTIC_ACV_COMPANY_HARD_CAP` — absolute ceiling. If exceeded, `acv_high` clamps to the cap and confidence drops to `low` (model was reasoning beyond supportable scale). |
| **Range-width ratio** | `HOLISTIC_ACV_MAX_RANGE_RATIO` — if `acv_high / acv_low` exceeds the ratio at `high` confidence, confidence drops to `medium`. If it exceeds `ratio × 1.5` at `medium`, drops to `low`. Wider range = less trust. |
| **Per-user ceiling sanity check** | Midpoint is compared against `total_users × HOLISTIC_ACV_PER_USER_CEILING`. If the midpoint implies a dollar-per-user value higher than the platform has ever seen, confidence drops to `low`. |
| **Known-customer floor / ceiling** | If the target is in `KNOWN_CUSTOMER_CURRENT_ACV`, Python enforces a floor (current ACV — cannot undersell an existing relationship) and a stage-derived ceiling. Floor informs the low bound without collapsing range-width; see "Known-Customer Calibration" below. |
| **Output scrubber** | Defense-in-depth. Redacts any dollar figure that matches a known-customer current ACV from rationale / drivers / caveats before it reaches the user. |

**Discovery now costs two Claude calls per company.** The discovery call (Tier 1/2/3 research) runs first, then the holistic ACV call runs once against that research. Discovery time budget expanded from ~1 min to ~3 min per company; per-company Claude cost roughly doubled but remains well under $1. Prospector batch estimator accounts for both calls.

### Known-Customer Calibration

**Why.** The platform has a known list of current Skillable customers and their real ACV. Using that list poorly would be worse than not using it. Two separate bugs showed up in earlier designs:

1. **Name leak risk** — if Claude sees a customer's name in the prompt, it can echo it back in the user-visible rationale and leak revenue data.
2. **Anchoring bug** — if we cap the ceiling at a multiple of current ACV for every customer, growing customers look small forever. Their current spend is not their potential; their portfolio size is.

The right design, locked 2026-04-14: the list **informs** the floor without ever **naming** customers, the ceiling cap only applies to genuinely saturated customers, and the calibration block anchors Claude on **ACV Potential** (not current revenue) for the "what could this be" question that prospects are being asked.

**What — five distinct contributions to an estimate:**

| Contribution | How it's used | What's protected |
|---|---|---|
| **Anonymized two-column anchor block** | Stage-grouped magnitudes shown to Claude: `current ACV $X–$Y, estimated ACV Potential $A–$B`. Customer names NEVER enter the prompt. For saturated customers current ≈ potential. For growing customers potential is materially higher — that's the right anchor for prospects. | Claude anchors prospects against **Potential**, not current. |
| **Hard floor (every stage)** | `acv_low = max(claude_low, current_acv)`. Cannot undersell an existing relationship. Applies to every known customer regardless of stage. | Floor protects against underselling. |
| **Ceiling cap — saturated only** | Saturated customers: `acv_high = min(claude_high, 1.3 × current_acv)`. Every other stage: **no cap** from current ACV — the high is Claude's holistic reasoning, subject only to the universal `HOLISTIC_ACV_COMPANY_HARD_CAP`. | Saturated customers cannot show runaway upside; growing customers are not artificially held down. |
| **`_raw_claude` preservation** | `_holistic_acv._raw_claude` stores Claude's original numeric output alongside the post-guardrail result. | Future guardrail tuning propagates across the cache via pure-Python re-application; zero additional Claude calls. |
| **Output scrubber** | Any dollar figure matching a known-customer `current_acv` is replaced with "<peer comparable>" in user-visible text before render. | Customer revenue data never surfaces even if the prompt directive is ignored. |

**Floor informs, does not collapse.** The floor rule preserves range-width: if Claude's original high is already above the floor, high keeps its value. If Claude's original high is below the floor, high expands (to the stage ceiling if one applies, else to 2× floor) so the range reflects genuine upside rather than pinning at a zero-width point.

**Why not multi-tier ceiling multipliers.** A previous design used a six-tier ceiling cap (saturated 1.3× / mature-small 1.5× / mid 3× / first-year 8× / early 15× / very-early uncapped) and an expected-low multiplier that pushed the low bound above current for growing stages. Both were abandoned 2026-04-14 as fake precision. A growing customer's ACV Potential is a function of their portfolio size, not a multiplier on their current Skillable contract. The simpler rule — **floor always, ceiling cap only for saturated** — is grounded in the actual asymmetry of the question. Stage labels for non-saturated customers remain in the data as descriptive context for the calibration block grouping, not as enforcement multipliers.

**ACV Potential computed once.** `scripts/compute_customer_potentials.py` runs the holistic prompt for each non-saturated known customer with `disable_known_customer_caps=True` to get their unclamped Potential. The result is stored as `acv_potential_low` / `acv_potential_high` on the customer's entry in `known_customers.json`. The calibration block reads both `current_acv` and `acv_potential` per customer and emits them per stage. This is a one-time pass (re-run after major prompt changes, not per retrofit).

**Customer data lives outside the repo.** `backend/known_customers.json` is gitignored. A committed `known_customers.template.json` documents the schema. The production deployment mounts the real file; no one can discover customer ACV figures by reading the repo.

### Partnership-Only ACV — Content Development Firms

**Why.** A subset of organizations — Content Development firms like GP Strategies — don't fit the direct ACV audience × adoption model. They don't have their own products; they build learning programs for other companies. Running the holistic ACV prompt on them produces meaningless numbers because the five-motion framework doesn't apply. Skillable's opportunity with them is a **partnership motion** (labs embedded in the programs they build for clients) that is fundamentally downstream-dependent.

**What.** For org types in `ACV_PARTNERSHIP_ONLY_ORG_TYPES` (currently: `CONTENT DEVELOPMENT`), the holistic ACV function short-circuits before calling Claude and returns a fixed-shape partnership result:

| Field | Value |
|---|---|
| `acv_type` | `"partnership"` |
| `acv_low` / `acv_high` | `0` |
| `confidence` | `"partnership"` |
| `rationale` | Explains why this is a partnership motion, not a direct ACV motion |
| `key_drivers` | Up to 5 partnership-relevant signals from the discovery data |

**How it surfaces.** Prospector displays "Partnership" in the ACV Potential column with a distinct purple chip (`--sk-classify-purple`) instead of a dollar range. CSV exports include an `acv_type` column so Marketing can filter partnership rows separately from direct-ACV rows. The company still gets ranked, scored, and researched — the partnership framing just replaces the dollar-range UX.

### Common Estimation Pitfalls — Built into the Prompt

**Why.** In early runs the model made the same mistakes repeatedly — not because the prompt was vague, but because the common pitfalls weren't named. After diagnosing the Parkway / Multiverse / Zero-Point / New Horizons low-estimate cluster against their rationales, five recurring anti-patterns were identified (A, B, D, E, F — G and C were deferred as structural) and explicitly called out in the prompt. Each pattern had been shaving estimates downward in ways that stacked on top of the calibrated adoption rates.

| Pattern | What Claude was doing wrong | What the prompt now tells it |
|---|---|---|
| **A — Fraction deflator** | Applying "minority subset actually consumes labs" on top of already-calibrated adoption rates | Adoption rates are already the realistic consumption view. Do not add a second discount. |
| **B — Cumulative vs. annual** | Silently substituting cumulative/lifetime user counts for annual enrollments (3–8× over-estimate in the wrong direction) | Prefer annual. If only cumulative is available, divide by program lifespan (2–3 yrs tech, 4 yrs academic). |
| **D — Known-customer floor collapse** | Clamping both low and high to the floor when Claude's original range was below it (zero-width ranges) | Floor informs the low bound. High preserves width via Claude's original high, stage ceiling, or 2× floor for very-early. Python-enforced, not prompt-dependent. |
| **E — DIY as discount** | Treating "they already run in-house labs" as a displacement discount ("partial before scaling") | In-house lab = POSITIVE ICP signal (existing demand, budget proven). Current DIY spend is a floor, not a ceiling. |
| **F — Rate tier by deployment label** | Defaulting "SaaS/cloud-delivered" programs to the $6-$8/hr cloud rate even when the content required VM-class labs | Rate tier is determined by workload complexity, not deployment label. Cybersecurity / networking / platform eng need VM rates even when delivered "via cloud." |

Pattern C (K-12 / district budget-signal audience) is deferred as a structural change — it needs a new researcher field and a routing rule, not a prompt tweak. Pattern G (parent-entity dedup — "Deloitte" vs. "Deloitte Consulting LLP" vs. "Grand Canyon University" vs. "Grand Canyon Education") is deferred as "probably has to stay separate" — organization-by-organization entity resolution is too fragile to automate at this scale.

### Sharpening: Discovery-Level → Deep Dive

**Intelligence sharpens automatically.** If a company in the Prospector list has had a Deep Dive in Inspector, Prospector shows the sharpened Deep Dive ACV instead of the discovery-level holistic estimate. GP5 in action.

| Company state | What Prospector shows |
|---|---|
| **Discovery only** | Option 2 holistic ACV — range, confidence, rationale, drivers, caveats |
| **Deep Dive cached** | Full five-motion ACV Potential — actual per-motion audience × adoption × hours × rate with product-level precision |
| **Partnership-only org type** | Partnership chip — no dollar range |

### Prospector Results Table

**Why.** Marketing needs to scan 100+ companies and immediately see which ones matter and why. The table must be scannable — glance and know.

**What — the columns:**

| Column | What it shows | Why marketing needs it |
|---|---|---|
| **Rank** | Auto-numbered by ACV midpoint | Where this company falls |
| **Company** | Name + classification badge (Cybersecurity, Enterprise Software, Industry Authority, etc.) | What kind of company — immediately sets context |
| **ACV Potential** | Range + confidence chip (`LOW` / `MEDIUM` / `HIGH` / `PARTNERSHIP`). Click opens docs-mode modal with full rationale + drivers + caveats. | The primary sort — how big is this opportunity, and how much to trust it |
| **Deep Dives** | `N/M` coverage pill — how many of M discovered products have been Deep-Dive'd. Colored: green if full, amber if partial, muted if none. | Signals Inspector investment at a glance — which rows already have rich data behind them |
| **Top Product** | Flagship product name + subcategory | The lead story — what's the biggest opportunity at this company |
| **Top Signal** | One line — "14M users, installable, strong API surface" | Why the top product is the lead. (Previously labeled "Why" — renamed 2026-04-14 to avoid the word-collision with "Rationale" in the ACV column's modal.) |
| **Prom.** / **Pot.** / **Unc.** / **Unl.** | Product tier counts (Promising / Potential / Uncertain / Unlikely) | Portfolio breadth at a glance. Tooltips read "Promising Products — strong pre-Deep-Dive labability signals," etc. |
| **Lab Platform** | Current lab platform or "None" | Competitive signal — expansion vs. displacement vs. greenfield |

**Every column header carries a tooltip.** Column labels are short for table scannability (Prom. / Pot. / Unc. / Unl.); tooltips carry the full meaning. GP1 applied to the table header row.

**Partnership rows.** Content Development firms show **"Partnership"** in the ACV Potential column with a purple chip (`--sk-classify-purple`) instead of a dollar range. CSV exports include an `acv_type` column (`direct` or `partnership`) so Marketing can filter. LMS companies show normally with a "Distribution Partner" flag in addition to their direct ACV. See ACV Potential Model → Partnership-Only ACV above.

**Running batch dot.** When a batch is processing, the Recent Batches panel shows a pulsing **amber** dot (`--sk-score-mid`). Completed batches show a green dot. The color difference is deliberate — running and complete should be visually distinguishable at a glance. (Amber-pulse locked 2026-04-14.)

**Retired column — "Key Signal."** Earlier versions had a "Key Signal" column that auto-picked from ATP / events / training_programs signals without a clear rule. Retired 2026-04-13 when the holistic ACV rationale replaced it — rationale explains WHY the company is ranked where it is, with full grounding, on the ACV column click-through instead.

### Prospector for Marketing Documentation

**Why.** When marketing reads the in-app documentation (the ? modal), they need to understand how Prospector works and why they should trust it. Key points the documentation must communicate:

| Point | What it says |
|---|---|
| **Products, not companies** | "We don't put companies into labs. We put products into labs. That's why we rank by product fit, not company size." |
| **ACV is product-driven** | "ACV potential is based on how many people use each product and how those products would be delivered as labs — not on company revenue or headcount." |
| **Intelligence compounds** | "The more companies we analyze, the better the data gets. Every Deep Dive sharpens the Prospector view. Every Prospector run caches data for future Deep Dives." |
| **Two lists, same intelligence** | "Whether it's a new target or an existing customer, the intelligence is the same. Expansion opportunities and new targets are scored identically." |

### Prospector → HubSpot Integration (Future)

**Why.** The CSV is the interim step. The destination is HubSpot — intelligence flows directly into company and deal records, shown to the right person at the right time with the right context (GP1).

**What.** Authenticated integration via HubSpot API. Discovery intelligence writes to custom properties on HubSpot company records. The field mapping is a RevOps conversation — which Skillable intelligence fields map to which HubSpot properties.

**How.** Two stages:

| Stage | What it does |
|---|---|
| **Stage 1 — Company Record** | ACV potential, top product, labability summary, key signals, lab platform → HubSpot company properties |
| **Stage 2 — Deal Records** | Per-product intelligence attached to deals — Fit Score, Pillar readings, Seller Briefcase content |

**Sequencing.** Stage 1 is the priority and stands alone as a complete solution — marketing gets company-level intelligence in HubSpot. Stage 2 layers on per-product deal intelligence and depends on how RevOps structures deals in HubSpot. The in-app Prospector results table and CSV export remain available regardless — HubSpot integration adds a delivery channel, it doesn't replace the in-app experience.

---

## Designer: The Complete Pipeline

**Why.** Designer turns product intelligence into an actionable build plan. It lives in the Intelligence Platform because every phase depends on deep product knowledge — what's possible, what's scorable, what infrastructure is required.

**What — eight phases:**

| Phase | What it does | Why it matters |
|---|---|---|
| **1. Intake** | Collects learning objectives, products, target audience, business objectives, job task analyses | Sets the scope — everything downstream derives from this |
| **2. Program outline** | Recommends lab series — names, descriptions, count | Structure based on product knowledge + objectives |
| **3. Lab breakdown** | Recommends individual labs per series — titles, descriptions, count | Granularity driven by product depth and learning goals |
| **4. Activity design** | Recommends 2–8 activities per lab, in sequence | Enables progress tracking — without activities, only completion data exists |
| **5. Scoring recommendations** | Recommends how to score each activity — AI Vision, PowerShell, API validation | Intelligence knows what's scorable and how |
| **6. Draft instructions** | Generates lab instructions — step-by-step or challenge-based | Tech writers edit instead of create from scratch |
| **7. Bill of materials** | Complete environment spec — VMs, cloud services, databases, dummy data, lifecycle actions | One pass, complete spec for the whole program |
| **8. Export package** | Lab series, lab profiles, instructions, build scripts — zipped for Studio import | Dev team's job becomes QA, finalize environments, publish |

**How.** Designer will eventually be a standalone application with its own authentication. For now, it lives in the platform and shares the intelligence brain. The architecture must support this separation — Designer's connection to product intelligence stays, but company intelligence is never accessible from Designer.

---

## Data Architecture: Three Domains

**Why.** Customers will eventually access Designer. They must never see the company intelligence that powers Prospector and Inspector. The separation is architectural, not just a permissions layer — when RBAC is implemented, it should be a configuration layer on top of an already-clean architecture, not a retrofit.

**What — three domains:**

| Domain | What it contains | Future access model |
|---|---|---|
| **Product data** | What products are, how they work, labability assessments, orchestration details | Open — anyone can see, including customers in Designer |
| **Program data** | Lab series, outlines, activities, instructions — created in Designer | Scoped — only your own programs |
| **Company intelligence** | Fit scores, badges, buying signals, customer fit data, contacts, ACV estimates | Internal-only — Skillable roles only |

**How.** No mixing these domains in the same database tables, API responses, or service calls in ways that would be hard to untangle later. The hard wall between Skillable and Customer roles is enforced at the data access layer.

---

## Authentication and Access Control

**Why.** The platform serves two fundamentally different audiences — Skillable internal users and customers — and the data they can see is not the same. Company intelligence (fit scores, ACV, badges, contacts) is commercially sensitive. Skillable's self-knowledge (capabilities, delivery patterns, competitive landscape) drives every analysis the platform produces. Lab programs may contain pre-release product information a customer doesn't want shared. These are three distinct protection problems that require explicit access boundaries.

**Current state (Prototype).** No authentication exists today. No login, no user sessions, no RBAC. API keys (`ANTHROPIC_API_KEY`, `SERPER_API_KEY`) are loaded from environment variables and never committed to the repo. The Flask secret key uses a dev fallback that must be replaced before deployment. The three-domain data architecture enforces structural separation, but there is no auth layer on top of it yet. Auth implementation is blocked on the deployment decision (Render vs Azure Web App).

### Roles — Seven Roles, Four Boundary Lines

**Why seven.** The original design had 11+ roles with fine-grained splits (Seller vs SE, Designer Admin vs Instructional Designer vs SME). In practice, the real access boundaries are coarser. A seller and an SE are both Skillable-internal users consuming the same intelligence — the difference is depth of interest, not access level. An Instructional Designer and an SME on the same team see the same programs — the difference is workflow, not permissions. Admin vs contributor distinctions within a role are configuration (can publish, can assign), not separate roles. Seven roles capture the four real boundary lines without creating friction.

| Role | What they need to do | What they must NOT do |
|---|---|---|
| **Skillable Admin** | Full platform access. Configure all tools, manage users, manage roles, view all data across all three domains. | No restrictions — superuser. |
| **Skillable Prospector Admin** | Run batch discovery, view/export results, configure HubSpot field mappings, view company intelligence + ACV + contacts. | Cannot modify scoring config, knowledge files, or Designer programs. |
| **Skillable CRM Integration Admin** | Configure HubSpot write-back, manage field mappings, control what intelligence flows to HubSpot and when. | Cannot run analyses, cannot modify scoring logic, cannot access Designer programs. |
| **Skillable User** (AE / CSM / SE / TSM) | View company intelligence, run Deep Dives, view full evidence detail, access Seller Briefcase, drill into dimension-level facts. | Cannot modify scoring config, knowledge files, or Designer programs. |
| **Skillable Capabilities Editor** | Edit Skillable's self-knowledge — `skillable_capabilities.json`, `delivery_patterns.json`, `competitors.json`. Define what Skillable can do and how it competes. Limited to Sales Engineering + Product. | Cannot modify scoring math (`scoring_config.py`). Cannot access company intelligence or customer Designer programs. Changes are high-impact — this role is deliberately restricted. |
| **Skillable Designer** | Create and manage lab programs across all Skillable-authored and customer Designer programs. ProServ builds on behalf of customers through this role. Admin vs contributor permissions are configuration within the role, not separate roles. | Cannot access company intelligence (Prospector/Inspector data). Cannot modify scoring config or knowledge files. |
| **Customer Designer** | Create and manage lab programs for THEIR organization only. Product visibility controlled by their org's admin — pre-release products can be restricted. Admin vs contributor permissions are configuration within the role. | **Never sees company intelligence — ever.** Cannot see other customers' programs. Cannot see Prospector or Inspector data. Cannot modify Skillable-authored programs. Cannot see products their admin has restricted. |

### Four Boundary Lines

These are the four real access boundaries an engineer needs to internalize. Every permission decision maps to one of these.

| Boundary | What it enforces |
|---|---|
| **Skillable ↔ Customer** | Customers never see company intelligence (fit scores, badges, ACV, contacts). Architectural — no code path from Designer to `company_intel/` domain. This is the hardest wall in the system. |
| **Skillable Capabilities ↔ everyone else** | Knowledge files that encode Skillable's platform self-knowledge are editable only by the Skillable Capabilities Editor role. These files drive how the Research layer understands what Skillable can do — fabrics, scoring methods, delivery patterns, competitive landscape. Uncontrolled edits here change every analysis the platform produces. |
| **Read ↔ Write on scoring** | Nobody outside Skillable Admin touches `scoring_config.py`. The Define-Once source of truth for all scoring parameters is not editable through the application — it is a code change with a version bump and a test run. |
| **Program scoping** | Skillable Designer sees all programs (theirs and customers'). Customer Designer sees only their own organization's programs. Pre-release product visibility is controlled at the customer org level — a customer building labs on unreleased products can restrict visibility so other customers don't see those products in Designer. |

### Auth Implementation Status

Authentication is deliberately deferred — it is blocked on the deployment decision (Render vs Azure Web App). The role table and boundary lines above are the design intent that deployment and auth implementation will enforce. When RBAC is built, it should be a configuration layer on top of the already-clean three-domain data architecture, not a retrofit.

---

## Estimated Platform Costs

Rough cost estimates per operation. These will be updated with actual measurements once the backend is stable on the rebuilt Score layer.

| Operation | What it does | AI Calls |
|---|---|---|
| **Discovery** (Inspector + Prospector) | Find products, build the product list, populate three-tier discovery data (call 1), then produce the holistic ACV estimate (call 2) | **2 Claude calls per company** — the discovery research call + the Option 2 holistic ACV call. Prospector runs both in batch across all input companies. Rough unit economics: ~$0.30–$0.45 per company, ~2–3 minutes wall time per company. |
| **Holistic ACV retrofit** (`scripts/retrofit_acv.py --mode holistic`) | Re-runs just the holistic ACV call against an already-cached discovery. No re-research, no rescore — cheap way to apply prompt / guardrail updates across the entire cache without throwing away per-product work. | 1 Claude call per company. ~$0.20–$0.50 per company at 5-way parallelism; ~10–12s per company wall-time at 5 concurrent. |
| **Deep Dive** (Inspector full analysis) | Three parallel fact extractors per product + rubric grader calls for Pillars 2 / 3 + three parallel briefcase calls per product (Opus KTQ + Haiku Conv + Haiku Intel) | ~3 extractors × N products + 8 grader calls × N products + 3 briefcase calls × N products |
| **Cache reload** (re-visit a saved analysis) | Recompute ACV, reassign verdict, sort | **Zero AI calls** — pure Python |
| **Re-score after logic change** — tiered | Depends on which version bumped. `SCORING_MATH_VERSION` → pure-Python rescore against saved facts + saved rubric grades, **zero Claude calls**. `RUBRIC_VERSION` → re-run rubric_grader against saved raw facts then rescore, **~$0.30-0.50 per company** for grader calls. `RESEARCH_SCHEMA_VERSION` → full re-research, **only on deliberate schema changes**. | Math bump free; rubric bump cheap; schema bump same as full Deep Dive |

Pillar 1 scoring is zero-Claude by design. Pillar 2 and Pillar 3 scoring is zero-Claude *after* the rubric grader runs — the scorers themselves are pure Python reading cached `GradedSignal` records. The rubric grader is the only Claude call the Score layer is allowed to make.

---

## Document Strategy

Two authoritative documents, clean boundary, zero duplication:

| Document | What it owns | Audience |
|---|---|---|
| **Platform-Foundation.md** (this doc) | Strategic authority — Guiding Principles, Three Layers of Intelligence, Layer Discipline, Define-Once, Search Modal rule, people and personas, motivation, scoring framework at a glance, Fit Score composition, Two Hero Metrics, Verdict Grid, **ACV Potential model**, Inspector UX, Designer pipeline, data architecture | Everyone — sellers, SEs, engineers, product, leadership |
| **Badging-and-Scoring-Reference.md** | Operational detail — every Pillar's dimensions, every scoring signal, every canonical badge, every strength tier, every penalty, every baseline, Technical Fit Multiplier table, risk cap reduction rules, penalty-visibility rule, Pillar 3 unification, badge naming rules, locked vocabulary | Developers, AI prompts, in-app help, anyone who needs to understand or modify the math |

Where the two docs touch (verdict grid, ACV model, pillar structure), **this document is the home** and the reference doc points back. Where the reference doc touches concepts (pillar questions, 70/30 split), it names them and refers back here. Neither doc duplicates what the other owns.

---

## Supporting Documents

| Document | Purpose |
|---|---|
| **`docs/collaboration-with-frank.md`** | How Frank thinks, how to work together, session startup sequence |
| **`docs/roadmap.md`** | Consolidated inventory of everything we want to do, are doing, or have done |
| **`docs/next-session-todo.md`** | What shipped last session, what's open, first thing to do next session |
| **`docs/decision-log.md`** | Write-only historical record of decisions made during sessions |
