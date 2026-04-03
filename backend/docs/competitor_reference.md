# Competitor Reference
## Step 1.7 — All competitor information found in memory, organized for platform use

---

## 1. Direct Competitors — Lab Delivery Platforms

These platforms directly compete with Skillable for lab delivery contracts.

### 1.1 Skytap (Kyndryl)

**What it is:** Legacy cloud lab delivery platform. Now owned by IBM / Kyndryl after IBM's acquisition.

**Known strengths:**
- Windows workloads, legacy enterprise software
- IBM enterprise credibility / existing IBM relationships

**Known weaknesses vs. Skillable:**
- No Performance-Based Testing (PBT) or scoring engine
- No certified exam delivery
- Weaker events infrastructure
- IBM ownership adds sales cycle friction and procurement complexity
- Billing unpredictability — usage spikes create surprise invoices
- No Cloud Slice capability
- Scaling limits at events

**Displacement signals:**
- "We use Skytap"
- "Skytap labs"
- "Migrating from Skytap"
- Customer mentions billing surprises or unpredictable costs
- IBM/Kyndryl in the sales process

**Displacement opportunity:** Skytap customers are often actively looking to modernize. This is described as "the warmest possible lab platform conversations" when found. Billing unpredictability and the Kyndryl transition create real switching motivation.

**Priority in lab platform detection:** #2 (after DIY). Most frequently encountered displacement opportunity.

**References found in:** `reference_customer_intelligence.md`, `product_scoring.txt`

---

### 1.2 CloudShare

**What it is:** Cloud lab platform focused on pre-sales demo and POC environments, SE demo environments.

**Known strengths:**
- Polished sharing and invite flows
- SE demo environments
- Prospect engagement analytics (time spent in demo)

**Known weaknesses vs. Skillable:**
- Cannot support complex multi-VM environments connected by private networks — this is Skillable's clearest technical win
- Thin on complex enterprise applications requiring deep configuration
- No PBT
- Not built for training programs at scale — built for sales demos and POCs
- Limited networking support

**Displacement signals:**
- Research shows existing CloudShare labs for a product
- Company uses CloudShare for SE demos or customer POCs
- "CloudShare environment" in training/sales materials

**When found:** Note as migration opportunity in Inspector output. Flag Skillable's deeper networking and multi-VM capability as the technical win.

**Priority in lab platform detection:** #3. Common in pre-sales demo environments.

**References found in:** `reference_customer_intelligence.md`, `product_scoring.txt`

---

### 1.3 Instruqt

**What it is:** Developer-focused lab platform. Browser-native labs (no RDP/client), strong for CLI and cloud-native developer workflows.

**Known strengths:**
- Browser-native labs (no RDP/client dependency)
- Excellent for CLI and cloud-native developer workflows
- Strong developer relations and community integrations (HashiCorp, DevRel use cases)

**Known weaknesses vs. Skillable:**
- Primarily Docker/cloud-native only — cannot support Windows enterprise software, complex application stacks, or anything requiring traditional VM depth
- No PBT
- No networking depth for multi-device topologies
- Weak on Windows enterprise software

**Displacement signals:**
- Product has existing Instruqt labs
- Company uses Instruqt for developer community training
- "Try it in browser" lab experiences (often Instruqt)

**When found:** Note as migration opportunity if the product requires traditional software depth or VM-depth workflows. Strong selling point: Skillable can do everything Instruqt does PLUS Windows enterprise, VM depth, and PBT.

**Priority in lab platform detection:** #4. Common in developer relations and DevOps communities.

**References found in:** `reference_customer_intelligence.md`, `product_scoring.txt`, `reference_scoring_model.md`

---

### 1.4 GoDeploy

**What it is:** Lab delivery platform. Listed in `reference_scoring_model.md` as a platform to flag in Organizational Readiness scoring.

**Known information:** Limited. Listed alongside Skytap, CloudShare, Instruqt in the lab platform detection list in the scoring model reference. No detailed competitive intelligence available in current memory files.

**Detection signals:** "GoDeploy" in research results for a prospect.

**References found in:** `reference_scoring_model.md` (competitor list only)

---

### 1.5 ReadyTech

**What it is:** Lab delivery platform. Listed in `reference_scoring_model.md`.

**Known information:** Limited. Listed in the organizational readiness scoring context as a recognized lab platform. No detailed competitive intelligence in current memory files.

**Detection signals:** "ReadyTech" in research results.

**References found in:** `reference_scoring_model.md` (competitor list only)

---

### 1.6 Appsembler (also spelled "Appsembler" in some sources, "AppSimpler" in some contexts)

**What it is:** Open-source community focused lab platform built on open edX / Tahoe-LMS.

**Known information:**
- Focused on open source communities
- Niche player — not a meaningful competitor for enterprise prospects Skillable targets
- The research query in `researcher.py` (`research_products()`) uses "Appsembler" as the canonical spelling in the `compete_` query

**Known strengths:** None noted for enterprise context.

**Known weaknesses vs. Skillable:** Niche open-source focus; no enterprise capability.

**When encountered:** Flag as a displacement opportunity but note low-priority — this prospect profile is unlikely to be the primary Skillable ICP.

**References found in:** `product_scoring.txt`, `researcher.py`

---

### 1.7 DIY (Internal Build)

**What it is:** Not a vendor — the category of companies that built their own internal lab portal or custom VM environment. This is the most common "competitor."

**Known characteristics:**
- Engineering maintenance burden
- No scoring
- No LMS integration
- Hard to scale
- Indicator phrases: "we built it ourselves," "internal lab environment," "custom training infrastructure"

**Displacement opportunity:** Strong. They are already spending money on something Skillable does better. The pain points (maintenance burden, no scoring, no scale) map directly to Skillable's advantages.

**Priority in lab platform detection:** #1. Most common scenario encountered.

**References found in:** `reference_customer_intelligence.md`

---

### 1.8 ACI Learning

**What it is:** Training content company that sells labs but cannot author custom labs.

**Known information:** Listed in `reference_scoring_model.md` as a recognized lab delivery entity under Organizational Readiness. The key distinction: sells labs but cannot build custom ones. This means a prospect using ACI Learning has lab demand but may need Skillable for custom lab authoring.

**References found in:** `reference_scoring_model.md`

---

### 1.9 Vocareum

**What it is:** Cloud lab delivery platform. Listed in `reference_scoring_model.md`.

**Known information:** Limited. No detailed competitive intelligence in current memory files.

**References found in:** `reference_scoring_model.md`

---

## 2. Indirect Competitors — Cybersecurity-Specific

These platforms compete in specific cybersecurity use cases but are not general-purpose lab platforms.

### 2.1 Immersive Labs

**What it is:** Cybersecurity skills platform. Immersive learning focused on security teams.

**Scope:** Cybersecurity only. Not a general lab delivery platform.

**References found in:** `reference_scoring_model.md`

---

### 2.2 Hack The Box

**What it is:** Cybersecurity training platform with challenge-based labs and CTF (Capture the Flag) scenarios.

**Scope:** Cybersecurity only. Community-oriented.

**References found in:** `reference_scoring_model.md`

---

### 2.3 TryHackMe

**What it is:** Beginner-to-intermediate cybersecurity training platform with browser-based labs.

**Scope:** Cybersecurity only. Community-oriented, entry-level to intermediate.

**References found in:** `reference_scoring_model.md`

---

## 3. Adjacent / Special Cases

### 3.1 Microsoft (as a training platform competitor)

Microsoft operates MOC (Microsoft Official Curriculum) and Applied Skills learning paths. For Microsoft-specific training, Microsoft provides dedicated tenant access to authorized learning partners (MOC/Learning Partners only) for M365 Administration scenarios. This is NOT available to general training providers — only Microsoft's own authorized partner network.

**Impact on Skillable:** For M365 End User scenarios, Skillable's M365 tenant provisioning (LODSPRODMCA) is the correct path. For M365 Administration (Global Admin, managing the tenant itself), Microsoft's own tenant provision for MOC is the only clean path — Skillable has to use trial accounts with MFA/credit card friction for custom labs.

**Reference:** `product_scoring.txt` (M365 section)

---

## 4. What Queries Inspector Should Fire to Detect Competitor Usage

### 4.1 Company-Level Query (in discover_products())
Currently implemented as:
```python
("lab_platform", f"{company_name} hands-on lab CloudShare OR Instruqt OR Skytap OR \"virtual lab\" OR \"lab environment\" OR \"we built\" training infrastructure")
```

**Recommended expansion:**
- Add GoDeploy, ReadyTech, Appsembler, Vocareum to this query
- Add "LODS" and "Learn on Demand" as signals for existing Skillable customers (expansion vs. new sale)
- Add "ACI Learning" as a signal for third-party lab consumption without custom authoring capability

**Improved query:**
```python
("lab_platform", f"{company_name} hands-on lab (CloudShare OR Instruqt OR Skytap OR GoDeploy OR ReadyTech OR Appsembler OR Vocareum OR \"virtual lab\" OR \"lab environment\" OR \"we built\" OR \"LODS\" OR \"Learn on Demand Systems\" OR \"Immersive Labs\" OR \"Hack The Box\" OR \"TryHackMe\") training")
```

### 4.2 Product-Level Query (in research_products())
Currently implemented as:
```python
(f"compete_{name}", f"{name} hands-on lab CloudShare Instruqt Appsembler")
```

**Recommended expansion and rename:**
```python
(f"labplatform_{name}", f"{company_name} {name} hands-on lab (CloudShare OR Instruqt OR Skytap OR GoDeploy OR ReadyTech OR Appsembler OR Vocareum OR \"virtual lab\" OR \"sandbox environment\")")
```

Note: Rename from `compete_` to `labplatform_` for clarity. "Compete" is ambiguous — it could mean competitive product analysis. The intent is specifically to detect existing lab platform usage.

### 4.3 Cybersecurity-Specific Competitor Detection
For cybersecurity products (detected via category signals in discovery), add:
```python
(f"cybersec_labs_{name}", f"{company_name} {name} \"Immersive Labs\" OR \"Hack The Box\" OR \"TryHackMe\" OR \"cyber range\" hands-on lab")
```

### 4.4 DIY Signal Detection
The DIY signal is the hardest to detect automatically. The current `lab_platform` query includes "we built" as a signal. Add:
```python
# In discover_products(), add to lab_platform query or create separate query:
("diy_signal", f"{company_name} \"internal lab\" OR \"built our own\" OR \"custom lab environment\" OR \"lab portal\" training infrastructure")
```

---

## 5. Competitive Pairing Logic (Stage 1 Company Report)

Per the Stage 1 competitive pairing decision, Inspector should pair each company product to its market competitors. This is separate from detecting which lab platform the company uses — it's about identifying which competing SOFTWARE PRODUCTS exist in the same market.

**Purpose:** Enables lookalike analysis (if Cohesity DataProtect is a strong Skillable fit, Rubrik, Veeam, and Commvault are likely strong fits too) and surfaces displacement signals (if a competitor already has Skillable labs, that's urgency for this prospect).

**What the research query should do:**
```python
(f"competitors_{name}", f"{company_name} {name} competitors alternatives versus comparison {category}")
```

This query feeds the competitive pairing field in the Stage 1 Company Report, which is a separate output from the lab platform detection.

---

## 6. Known Gaps in Competitor Intelligence

1. **GoDeploy:** No detailed competitive analysis available. Need: pricing model, feature set, typical customer profile, displacement signals.
2. **ReadyTech:** Same as GoDeploy. Limited information.
3. **Vocareum:** Limited information. Need: whether this is primarily academic/MOOC-focused or enterprise.
4. **AppSimpler vs. Appsembler:** Task description uses "AppSimpler" — this may be a variant spelling or a different company. Current code uses "Appsembler." Verify whether these are the same entity and standardize.
5. **AWS as a former customer:** AWS was a discontinued Skillable customer (business/relationship reasons, not technical). This means Inspector should NOT flag AWS itself as a competitor — it's a former customer that departed for non-technical reasons.
