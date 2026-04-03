# Skillable Company Reference
## Step 1.5 — All Skillable-specific context organized for platform use

---

## 1. Company Identity and History

**Current name:** Skillable

**Former names:**
- Learn on Demand Systems (LOD) — the predecessor brand
- Referenced internally as "LOD" in some platform contexts (the Skillable tenant is `LOD` in some M365 references; the vocabulary table in `reference_scoring_model.md` explicitly maps "LOD" → internal platform reference, "Skillable" → external brand name)

**Historical domains:**
- `learnondemandsystems.com` — former primary domain under the LOD brand
- `labondemandsystems.com` — former domain (referenced in memory as a known historical URL)

**Current domain:** `skillable.com`

**Positioning statement (from product_scoring.txt):**
"Skillable orchestrates software in cloud VMs and datacenters so learners practice real workflows in safe, instrumented environments."

**Core differentiation (from product_scoring.txt):**
- Purpose-built for ephemeral learning and skill validation — datacenters optimized for fast, consistent, isolated lab launches, not long-running production workloads
- Performance-Based Testing (PBT) and scoring — no competitor has a native, orchestrated scoring engine
- Complex multi-VM environments and flexible networking — private VLANs, isolated network segments, multi-VM topologies with real routing protocols
- Scale for events — proven delivery at Cisco Live (~30k attendees), Tableau Conference (14,000+ labs), Microsoft events
- Complex enterprise software depth — any software that installs on Windows or Linux
- Exam delivery (EDP) integration — Pearson VUE confirmed partner; Certiport, PSI (ISACA), Certiverse (NVIDIA) also confirmed

---

## 2. Skillable's Own Products and Capabilities

### 2.1 Lab Delivery Infrastructure

**Skillable Datacenter (Hyper-V / ESX / Docker)**
- Purpose-built for ephemeral learning
- Hyper-V: default fabric; lower cost than ESX due to Broadcom's post-acquisition pricing
- VMware ESX: use only when nested virtualization requires non-Hyper-V hypervisor, or when socket-based licensing and VM >24 vCPUs (which splits to 2 sockets, doubling cost)
- Docker: for genuinely container-native products; supports private registries (Docker Hub private repos, Azure Container Registry); ACR explicitly supported with admin account mode; no nested virtualization support; large images must be pre-baked
- No GPU in Skillable datacenters — Azure Compute Gallery / EC2 AMI is the current GPU workaround

**Cloud Slice — Azure**
- Isolated Azure environment per learner
- CSR mode: resource group level (lower privilege)
- CSS mode: subscription level (required for subscription-wide settings, Global Admin tasks)
- ALL Azure services supported after Skillable Security Review — no fixed whitelist
- Entra ID tenant included with every subscription — clean per-learner isolation for Entra-authenticated products
- Bicep templates (compiles to ARM at launch) and ARM JSON templates both supported
- Access Control Policies (ACPs) restrict services/SKUs/regions even on CSS
- M365 End User sub-pattern: Skillable-owned tenants, concurrent licensing (15/50 increments), tiers: Base E3 / Full E5 / Full+AI (coming); no credit card, no MFA

**Cloud Slice — AWS**
- Dedicated, isolated AWS account per learner (stronger isolation than Azure shared subscription)
- Known unsupported services (notable gaps): SageMaker, Comprehend, Rekognition, Lex, Polly, Transcribe, ElastiCache/OpenSearch, GuardDuty, Neptune, EMR, CodeBuild/Pipeline/Commit/Deploy, AWS SSO, SES, ACM, Direct Connect
- EC2 save behavior: instances suspend on save (billing stops); reboot on resume

**ADO and GitHub Cloud Slice**
- Native integrations for Azure DevOps and GitHub
- ADO: ~85% instant, 15% slow (5-15 min) — Pre-Instancing recommended
- GitHub: ~85% slow (5-15+ min) — Pre-Instancing strongly recommended

**Skillable Simulations**
- Realistic front-end UI mimicry for scenarios where real provisioning is not practical
- Score 8-16 on Product Labability

### 2.2 Scoring and Assessment Capabilities

**Performance-Based Testing (PBT)**
- Learner completes all tasks and submits at end for grade
- No interim verbose feedback
- Best for certification, skill validation, proctored exams
- No competitor has native PBT — Skillable exclusive

**Activity Based Assessment (ABA)**
- Learner gets immediate per-activity feedback, can retry
- Adaptive outcomes: correct → skip ahead; incorrect → redirect to resources
- Best for learning and practice labs

**Activity Group Scoring**
- Groups activities into Tasks/Learning Objectives with pass/fail thresholds
- Maps to job task analyses and skill frameworks
- Recommended for formal skills validation and certification programs

**Scaled Scoring**
- Maps raw scores to standardized scale (e.g., 0-1000 with passing score of 700)
- Critical for certification vendors needing score consistency across exam versions

**AI Vision scoring**
- Computer vision evaluates learner screen via natural language prompt
- Best for GUI-heavy products with no CLI/API surface
- No scripting required

**Scoring Bot**
- Hidden Windows 10 VM executing PowerShell against other VMs in a Hyper-V lab
- Useful for external vantage-point scoring (checking service on target VM from orchestrator VM)
- Hyper-V only, not ESX

**Skillable Copilot**
- Lab authoring tool: generates scoring scripts from natural language descriptions
- AI Practice Generator: learner-driven practice scenarios
- These are Designer/authoring-phase tools, not Inspector-phase tools

### 2.3 Special Delivery Patterns

**Pre-Instancing**
- Pre-builds environments before the learner arrives
- Support-only feature (not self-service)
- Required for: ADO, GitHub, Salesforce (10-hour provisioning), and any other product with provisioning latency >5 min

**Collaborative Labs**
- Multiple learners in a shared environment
- Minimum two lab profiles: Shared Environment (one) + Participant (one or more)
- Instructor must launch Shared Environment first from Monitor Labs view
- ILT/vILT only — self-paced not viable
- Two patterns: Parallel/Adversarial (cyber range, red/blue team) and Sequential/Assembly Line

**Credential Pool**
- Skillable-managed pool of pre-loaded credentials distributed to learners
- Reuse policies: always new / reuse within class / reuse per lab profile / reuse per series / always reuse
- Blocks launches when no credentials available

**Custom API (BYOC — Bring Your Own Cloud)**
- Life Cycle Actions (LCAs) handle provision, configure, score, teardown via vendor's own API
- Salesforce sandboxes are the canonical example
- Pre-Instancing required for long provisioning (Salesforce can take up to 10 hours)

**OVA Import**
- Customer provides virtual appliance (.ova/.ovf); Skillable imports to ESX fabric
- Constraints: hardware version ≤19, single VM only, ESX export format required
- Large appliances (>~50GB) require FTP upload coordinated with Cloud Infra team

**Security Add-ons**
- Conditional Access Policy (CAP): requires Entra ID P1; VM-only (NAT/PubIP); NOT compatible with Cloud Slice VMs (dynamic IPs)
- Custom UUID: pins BIOS GUID to satisfy hardware-fingerprinted license checks; concurrency capped at 1 if product also requires Public IP
- Keyboard Selector (LangSwap): language-specific keyboard input for non-English delivery

### 2.4 Platform Capabilities (Status)

| Capability | Status |
|---|---|
| PBT | Live |
| AI Vision scoring | Live |
| Scoring Bot | Live (Hyper-V only) |
| Geolocation | Live |
| Edge AI Translation (100+ languages) | Live |
| LTI 1.3 | Live (preferred LMS integration) |
| SCORM | Live (geolocation-aware since Oct 2024; legacy use only) |
| xAPI / Tin Can API | Not supported — Blocker if vendor requires LRS |
| FedRAMP | Not certified — hard ceiling for government |
| GPU in datacenter | Not available — Azure/AWS VM workaround |
| Pre-Instancing | Live (support-only) |
| Custom UUID | Live |
| Conditional Access Policy | Live (VM-only) |
| AI Content Assistant | Live (authoring/Designer phase) |
| AI Practice Generator | Live (authoring/Designer phase) |

---

## 3. Known Customers and Use Cases

**Tanium:** Pre-sales POC motion — 7x higher expansion revenue from customers who completed hands-on lab POC vs. churned without one. Primary data point for POC motion ROI argument.

**Cisco:** Cisco Live ~30,000 attendees with hands-on labs at event scale.

**Tableau:** Tableau Conference — 14,000+ labs over 3-4 days. Seasonal/burst model. (Note: now reduced; relationship special case — AWS VMs for the burst event model.)

**Hyland:** CommunityLIVE event + ongoing OnBase/Nuxeo training.

**Microsoft:** Multiple programs — Ignite, Build, TechConnect, AI Tour. Also M365 tenant infrastructure partnership (LODSPRODMCA, MSLEARNMCA tenants).

**CompTIA, ISACA, SANS, EC-Council, CREST:** Certification body use cases with PBT at core.

**NVIDIA:** Active engagement; uses Certiverse as EDP.

**Siemens:** 6,000 HR professionals completing skills assessments — confirms non-technical lab demand.

**National Instruments, Emerson, Cohesity, Commvault, Salesforce, Tableau, SAIT:** Listed in `_SKILLABLE_CUSTOMER_NAMES` in researcher.py.

**LMS Partners (tight integrations):** Cornerstone OnDemand, Docebo — pre-built connectors, proven path, faster time to delivery. When research surfaces either, flag explicitly.

**EDP Partners (confirmed integrations):**
- Pearson VUE: Microsoft all exams, CompTIA, SANS/GIAC, EC-Council, CREST — major Skillable partner
- Certiport: Pearson company; entry-level IT certifications (MOS, IC3, Adobe, Autodesk)
- PSI: ISACA
- Certiverse: NVIDIA; fast-growing EDP

**Discontinued:**
- AWS: business/relationship decision, not technical capability
- Benchling: business/relationship reasons

---

## 4. M365 Tenant Infrastructure

**Skillable-operated tenants:**
- LODSPRODMCA (primary M365 tenant)
- MSLEARNMCA (Microsoft Learn partnership)

**License groups available:**
- `_Skillable-E3` (core M365 + Entra P1)
- `_Skillable-E5` (adds Power BI Pro + Entra P2)
- `_Skillable-TeamsEnt`, `_Skillable-M365Copilot`, `_Skillable-CopilotStudio`
- `_Skillable-PowerAutomatePro`, `_Skillable-E3+PBIPro`, `_Skillable-E5+PBIPremium`

**GitHub groups available:**
- Events (Skillable-owned), Applied Skills (Microsoft-sponsored)
- Variants for Copilot and Org Owner permissions

---

## 5. Organizational Context

**Positioning in the market:** Skillable is a PaaS (Platform-as-a-Service) provider for hands-on lab delivery. The critical distinction from SaaS competitors is that Skillable's customers build on top of the platform — it is not a pre-built content library. Customers bring their own content or use Skillable PS to build it.

**Scoring platform is Skillable-exclusive:** Performance-Based Testing with native orchestrated scoring is the defining competitive differentiator. No other lab delivery platform has an equivalent native capability.

**Organizational areas the platform serves:**
- Sales / SE / TSM / CSM (Inspector — pre-sales qualification and account expansion)
- Marketing / AEs / SDRs (Prospector — batch ABM and outbound qualification)
- Learning Consultants / PS / Customers (Designer — lab program architecture)

---

## 6. Impact on Logic and Research

### 6.1 What Should Be Embedded as Reference Knowledge (not fetched dynamically)

The following Skillable-specific knowledge is stable, proprietary, and should be embedded directly in prompts and code — not researched:

- The nine orchestration methods, their tier names, and scoring ranges
- The 40/30/20/10 composite scoring model
- Multiplier logic thresholds
- Penalty deductions (GPU -5, MFA -3, etc.)
- The four technical gates (Provision, Accounts, Scoring, Teardown)
- CEILING_FLAGS set (bare_metal_required, no_api_automation, saas_only, multi_tenant_only)
- AWS supported/unsupported service lists
- Collaborative lab delivery constraints (ILT-only, two-profile minimum)
- Pre-Instancing requirement triggers (ADO, GitHub, Salesforce)
- OVA import constraints (hardware version ≤19, single VM, etc.)
- Known EDP partner list (Pearson VUE, Certiport, PSI, Certiverse)
- Known LMS partner list (Cornerstone, Docebo)
- Skillable's M365 tenant tiers and concurrent licensing model
- Hyper-V vs. ESX decision rules (including Broadcom pricing context)
- GPU workaround (Azure VM / AWS VM path)
- xAPI / FedRAMP gaps as known blockers

**These are already in product_scoring.txt.** They should stay there and be kept synchronized.

### 6.2 What Should Affect Research Query Logic

The following Skillable knowledge affects how `researcher.py` should target queries:

- **Known competitor names** (Skytap, CloudShare, Instruqt, GoDeploy, ReadyTech, etc.) should be included in the `lab_platform` query in `discover_products()` and in the `compete_/{labplatform_}` query in `research_products()`. The current query includes CloudShare, Instruqt, Skytap — add GoDeploy and ReadyTech.
- **Known EDP partner names** should be included in certification training queries to surface integration-confirmed signals.
- **Known LMS partners** (Cornerstone, Docebo) should be explicitly mentioned in LMS queries so Claude flags them as strong signals when they appear.
- **Former Skillable names** (LOD, Learn on Demand Systems, LODS) — if a prospect's research surfaces "LODS" or "Learn on Demand" as their existing lab platform, this is an active/former Skillable engagement signal. Add to the `lab_platform` competitor detection query.

### 6.3 What Should Affect Scoring Logic

- The **Hyper-V preference rationale** (Broadcom pricing) should be made more explicit in scoring: whenever ESX is recommended over Hyper-V, require specific justification (nested virtualization OR socket-based licensing with >24 vCPUs). This is already in the prompt but could be tightened.
- **LOD/LODS as existing lab platform signal**: if research shows "LOD labs" or "LODS" already in use, this is a current Skillable customer (expansion opportunity), not a competitor displacement. This distinction needs to be handled in the competitor detection logic.
- **The 7x Tanium POC stat** should be embedded in the scoring prompt's pre-sales POC motion section as a concrete reference point for ACV framing.
