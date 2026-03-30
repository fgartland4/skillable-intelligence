"""Claude API-powered scoring engine for labability analysis."""

import json
import time
import traceback
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import (
    CompanyAnalysis, Product, ProductLababilityScore, PartnershipReadinessScore,
    DimensionScore, Evidence, Contact, OrgUnit,
    ConsumptionMotion, ConsumptionPotential,
)
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

# ---------------------------------------------------------------------------
# Calibration benchmarks — known Skillable customers used to anchor scoring
# ---------------------------------------------------------------------------

CUSTOMER_BENCHMARKS = [
    {
        "company": "Microsoft",
        "relationship": "Skillable's largest and most strategic customer — the ceiling benchmark",
        "org_type": "software_company",
        "products_and_paths": [
            "Azure services (Azure Cloud Slice — Best Case) — native Cloud Slice fabric, rich APIs across all lifecycle stages",
            "Microsoft 365 / Copilot (Azure Cloud Slice — Best Case) — M365 tenant provisioning with programmatic license application including Copilot",
            "Windows Server / Active Directory / SQL Server (Hyper-V fabric) — installs on Hyper-V VMs, rich PowerShell/CLI automation",
            "Microsoft Dynamics 365 (Azure Cloud Slice / Custom API provisioning) — complex ERP/CRM workflows, large implementation partner ecosystem",
            "Microsoft Security suite: Defender, Sentinel, Purview, Entra ID (Azure Cloud Slice + Hyper-V fabric) — cybersecurity hands-on essential",
            "Power BI / Microsoft Fabric (Hyper-V fabric + Azure Cloud Slice) — Power BI Desktop installs on Windows, highest lab volume product",
            "Azure AI Studio / Azure OpenAI (Azure Cloud Slice — Best Case) — CREATE AI platform, native Azure provisioning, programmatic model deployment",
        ],
        "use_cases": [
            "Partner training channel: Microsoft Official Courseware delivered through Authorized Training Partners (Skillsoft, Global Knowledge, New Horizons, QA, Firebrand, etc.)",
            "Events: hands-on labs at Ignite, Build, Microsoft AI Tour, TechConnect — thousands of concurrent labs",
            "Certification PBT: performance-based testing in official Microsoft exams (AZ-104, SC-300, etc.)",
            "Applied Skills: free scenario-based credentialing program at scale for customers and partners",
            "AI Roadshow: hands-on AI labs at touring events where learners practice Copilot and Azure AI in context",
        ],
        "key_signals": {
            "technical": "Native Skillable integrations for Azure (Cloud Slice fabric), M365 tenants, and Hyper-V. Every major product family has a viable lab path.",
            "workflow": "Every product requires DTDS activities. Multiple product lines have embedded AI features (Copilot) requiring hands-on iterative practice.",
            "training_ecosystem": "ATP/Learning Partner network is massive and global. Gray market training ecosystem enormous. Annual flagship events plus global AI Tour. Formal certification with PBT.",
            "market_fit": "Dominant in cloud, security, data, developer tools, and AI infrastructure — all core Skillable categories. CREATE AI platform (Azure AI Studio) adds +5.",
            "partnership_readiness": "Dedicated training organizations per product group. Platform adoption (build + deliver) not project adoption. Training is a strategic revenue driver across the org.",
        },
        "score_guidance": "CEILING benchmark — total product labability 88-100, partnership readiness 90-100.",
    },
    {
        "company": "Cohesity",
        "relationship": "Active Skillable customer — Hyper-V fabric benchmark",
        "org_type": "software_company",
        "products_and_paths": ["DataProtect, DataManagement (Hyper-V fabric — Skillable Datacenter, rich REST APIs)"],
        "key_signals": {
            "technical": "Self-hosted/hybrid, installs in VMs. Rich REST APIs covering all 4 lifecycle stages including scoring/validation of backup and recovery outcomes.",
            "workflow": "Deep admin console. Multi-step workflows for backup policy, recovery orchestration, data management. Role-based (admin/operator/viewer). Strong troubleshooting scenarios. AI-powered data management features requiring hands-on practice.",
            "training_ecosystem": "Cohesity University with certification tracks. Partner enablement with lab requirements. Formal training catalog.",
            "market_fit": "Data protection is Skillable core strength. Large enterprise install base. Fast-growing category.",
            "partnership_readiness": "Dedicated training org. Formal tiered partner program with technical certification. Customer success team.",
        },
        "score_guidance": "HIGH benchmark — product labability 82-92, partnership readiness 75-88.",
    },
    {
        "company": "Tanium",
        "relationship": "Active Skillable customer — cybersecurity Hyper-V fabric benchmark",
        "org_type": "software_company",
        "products_and_paths": ["Tanium Platform (Hyper-V fabric — Skillable Datacenter, agent-based, rich module API)"],
        "key_signals": {
            "technical": "Agent-based, installs in VMs. Rich API covering endpoint detection, patch management, compliance validation.",
            "workflow": "Complex admin workflows: threat hunting, patch management, asset discovery, compliance reporting. Multiple operator roles.",
            "training_ecosystem": "Tanium Training with role-based certification. Partner technical certification requirements.",
            "market_fit": "Cybersecurity/endpoint management is Skillable core. Enterprise-only. Limited hands-on lab alternatives.",
            "partnership_readiness": "Strong training org. Tiered partner program. Professional services. Enterprise LMS.",
        },
        "score_guidance": "HIGH benchmark — comparable to Cohesity. Strong on all dimensions.",
    },
    {
        "company": "UiPath",
        "relationship": "Active Skillable customer — AI-embedded enterprise software benchmark",
        "org_type": "software_company",
        "products_and_paths": ["UiPath Platform (Azure Cloud Slice / Hyper-V fabric) — RPA with embedded AI requiring hands-on practice"],
        "key_signals": {
            "technical": "Installable automation platform with cloud components. Rich APIs for provisioning environments and validating automation workflows.",
            "workflow": "Complex design, build, deploy, monitor, troubleshoot cycle for automation. Embedded AI features (AI-powered document processing, AI Center) require iterative hands-on practice — cannot be learned by watching.",
            "training_ecosystem": "UiPath Academy with role-based certification. Large ATP network. Annual events with hands-on workshops.",
            "market_fit": "Enterprise automation and AI is fast-growing, high-value category.",
            "partnership_readiness": "Strong training org. Robust partner program. AI-powered product features drive urgent hands-on training demand.",
        },
        "score_guidance": "HIGH benchmark — AI-embedded workflow boosts workflow complexity score significantly.",
    },
    {
        "company": "Tableau (Salesforce)",
        "relationship": "Active Skillable customer — events use case benchmark",
        "org_type": "software_company",
        "products_and_paths": ["Tableau Desktop (Hyper-V fabric — installs on Windows), Tableau Cloud (Custom API provisioning)"],
        "key_signals": {
            "technical": "Tableau Desktop installs on Windows — clean Hyper-V path. Complex data modeling, visualization workflows.",
            "workflow": "Complex BI workflows: data connection, modeling, calculated fields, dashboard design, publication. AI-powered analytics features requiring hands-on practice. Role-based.",
            "training_ecosystem": "Tableau Conference delivers 14,000+ labs to 10,000+ attendees in 3-4 days. Tableau certifications. Large user community and gray market training.",
            "market_fit": "Data & Analytics is a core Skillable strength. Massive install base.",
            "partnership_readiness": "Dedicated training org. Salesforce (parent) has enormous partner ecosystem and ATP network.",
        },
        "score_guidance": "HIGH benchmark, especially for events use case. AI-powered analytics features add workflow complexity signal.",
    },
    {
        "company": "Commvault",
        "relationship": "Active Skillable customer — data protection with AI features benchmark",
        "org_type": "software_company",
        "products_and_paths": ["Commvault Cloud (Azure Cloud Slice / Hyper-V fabric) — data protection with embedded AI"],
        "key_signals": {
            "technical": "Hybrid deployment. APIs for provisioning, recovery validation, and scoring lab outcomes.",
            "workflow": "Complex data management workflows. AI-powered recovery and threat detection features that partners and customers practice hands-on in labs.",
            "training_ecosystem": "Commvault training programs. Partner enablement. Labs for AI feature adoption.",
            "market_fit": "Data protection/cyber resilience is core Skillable territory.",
            "partnership_readiness": "Dedicated training org. Partner program. AI features driving new training demand.",
        },
        "score_guidance": "HIGH benchmark — AI-embedded workflows drive hands-on lab demand even for existing customers who need to learn new AI features.",
    },
    {
        "company": "CompTIA",
        "relationship": "Active Skillable customer — certification body benchmark",
        "org_type": "training_organization",
        "products_and_paths": ["CompTIA certifications (Hyper-V fabric for underlying tools — Windows Server, Linux, network devices, cloud platforms)"],
        "key_signals": {
            "technical": "Labs run on industry-standard tools (Windows Server, Linux, Cisco, cloud) via Hyper-V and Cloud Slice. CompTIA CertMaster Labs confirms commitment to hands-on.",
            "workflow": "Performance-based exam scenarios. Multi-tool environments. Troubleshooting workflows across networking, security, sysadmin.",
            "training_ecosystem": "CompTIA IS the certification ecosystem. Massive global catalog.",
            "market_fit": "IT certification is Skillable's home market.",
            "partnership_readiness": "Very mature training and certification org. Deep global partner network. Existing LMS and delivery infrastructure.",
        },
        "score_guidance": "HIGH benchmark for certification bodies and training organizations.",
    },
    {
        "company": "Hyland",
        "relationship": "Active Skillable customer — VM-installable enterprise software benchmark",
        "org_type": "software_company",
        "products_and_paths": [
            "Hyland OnBase (Hyper-V fabric — Skillable Datacenter, installs on Windows Server VM)",
            "Hyland Nuxeo (Docker container / Hyper-V fabric — Docker/VM-deployable)",
            "Hyland Alfresco (Hyper-V fabric — installable on Linux/Windows VMs)",
        ],
        "key_signals": {
            "technical": "OnBase installs on Windows Server in a Hyper-V VM — the VM image IS the lab environment. Lab authors build the pre-configured image once; Skillable spins up copies per learner. No runtime provisioning APIs needed. Workflow Designer, Unity Client, and admin console are script-accessible. High viability on Hyper-V fabric; API richness is a bonus for scoring, not a requirement.",
            "workflow": "Deep admin console. Complex multi-step content management, case management, workflow automation, and AP/AR automation workflows. Admin/operator/end-user role distinction. Troubleshooting, integration configuration, and workflow design are all hands-on activities that cannot be learned by watching.",
            "training_ecosystem": "Hyland University with formal certification tracks. Hyland Community conferences with hands-on workshops. Growing ATP network. Large gray market training ecosystem (Udemy, consultancy courses).",
            "market_fit": "Content management / ECM is a growing Skillable category. Large enterprise install base. Complex product with training demand from implementation partners.",
            "partnership_readiness": "Dedicated training org (Hyland University). Partner enablement program. Annual conferences. Professional services arm.",
        },
        "score_guidance": "HIGH benchmark for VM-installable enterprise software. Technical score 18-22 — 'installable in VM + complex admin workflows' is the right tier, NOT 'minimal automation'. Workflow score 18-22 due to deep admin console and DTDS activities. Do not penalize for lacking cloud-native APIs — the Hyper-V fabric is designed exactly for this class of software.",
    },
    {
        "company": "Workday",
        "relationship": "POOR MATCH — canonical poor match benchmark despite enterprise complexity",
        "org_type": "software_company",
        "products_and_paths": ["Workday HCM, Workday Finance (Custom API provisioning — Not Viable, proprietary cloud, locked APIs)"],
        "key_signals": {
            "technical": "SaaS on Workday's proprietary cloud. APIs locked down. No self-hosted option. No Azure/AWS path. No free developer tier. Tenant provisioning takes months and costs thousands. FAILS API Automation Gate.",
            "workflow": "End users (HR/finance employees) have business_user persona. Implementation consultants have complexity but cannot be served without provisioning.",
            "training_ecosystem": "Training programs exist. Training leadership is engaged but cannot influence product team API decisions.",
            "market_fit": "Large install base, but technical fit failure overrides everything.",
            "partnership_readiness": "Training org is mature and engaged. Partnership readiness can score 60-75 independently of low product labability.",
        },
        "warning": "WILLING BUYER / UNWILLING PRODUCT TEAM pattern. Skillable invested over a year with engaged training leadership but product team will not open APIs. Maintain relationship at low cost. Do not invest significant solution engineering time until vendor commits to API openness.",
        "score_guidance": "LOW product labability (8-15 total after multiplier). Partnership readiness may score 60-75 independently. The composite gate (Lab < 30 → composite capped at 25) applies here — do not let high partnership readiness inflate pursuit priority.",
    },
    {
        "company": "Facebook / Meta consumer products",
        "relationship": "POOR MATCH — canonical consumer product poor match",
        "org_type": "software_company",
        "products_and_paths": ["Facebook, Instagram (consumer apps — no viable path)"],
        "key_signals": {
            "technical": "Consumer products. No enterprise deployment. No APIs for per-learner provisioning. Nothing to install.",
            "workflow": "Learned in minutes by using it. No DTDS activities. Consumer persona.",
            "training_ecosystem": "No certification. No gray market training. No partner ATP.",
            "market_fit": "Consumer category. No Skillable relevance.",
        },
        "score_guidance": "FLOOR benchmark — total product labability 0-10. Note: Meta's developer products (React, PyTorch) score very differently — always score at product level, not company level.",
    },
]

# ---------------------------------------------------------------------------
# Phase 1: Fast product discovery
# ---------------------------------------------------------------------------

DISCOVERY_PROMPT = """You are helping Skillable — a platform that provisions hands-on cloud/VM lab environments for software training and certification — identify what an organization offers that could be used in hands-on labs.

The organization may be a SOFTWARE COMPANY, an ACADEMIC INSTITUTION, a TRAINING ORGANIZATION, a SYSTEMS INTEGRATOR or PROFESSIONAL SERVICES FIRM, or a TECHNOLOGY DISTRIBUTOR or VAR. Handle each differently:

--- IF IT IS A SOFTWARE COMPANY ---
List their software products or product families. Group related products into families where appropriate (e.g., don't list 20 individual Microsoft products — group into "Azure", "Cybersecurity", "Application Development", etc.).

⚠️ CONSISTENCY RULE: Only list products you are CONFIDENT exist based on clear evidence in the research. Do not include products based on thin, ambiguous, or uncertain signals. If you are unsure whether something is a distinct product or just a feature of another product, group it under the parent. A product that shows up in one search snippet but has no other corroboration should be omitted. The goal is a stable, reliable list — not an exhaustive one.

If the company has a named training or certification program (e.g., "Hyland University", "Cisco Learning Network"), list it ONCE as a single entry with category "Training & Certification" and likely_labable = "not_likely". It is a partnership signal and lab opportunity, not a software product — but including it reminds the user that this channel exists. Do NOT list multiple training sub-programs or courses — one entry only.

Pay special attention to AI signals — note if any products:
- Are platforms used to BUILD, TRAIN, or DEPLOY AI (Azure AI Studio, SageMaker, NVIDIA AI Enterprise, Databricks ML) — mark these as "CREATE AI"
- Have embedded AI features requiring hands-on iterative practice (Copilot integration, AI-powered workflows, generative AI capabilities) — mark these as "INCORPORATE AI"

--- IF IT IS AN ACADEMIC INSTITUTION ---
Academic institutions use Skillable labs to give students job-ready skills in technology and engineering. List:
- Their key Technology & Engineering programs (e.g., "BS Computer Science", "Cybersecurity Certificate", "Cloud Computing Program")
- Technology platforms or tools they use to deliver these programs
- Any existing lab or simulation tools they use
Treat each program or platform as a candidate for Skillable lab integration.

--- IF IT IS A TRAINING ORGANIZATION (company whose primary business is training/certification) ---
Training organizations use Skillable as their lab delivery infrastructure for the SOFTWARE PRODUCTS THEY TEACH (not their own platform). List:
- The software platforms and technology areas their curriculum covers (e.g., "Microsoft Azure curriculum", "Cisco Networking programs", "Cybersecurity tools and platforms")
- Their certification programs and what technology each tests
- Existing lab or simulation infrastructure they operate
Treat each major curriculum area or technology platform they teach as a "product" to score — the labability is about the SOFTWARE THEY TEACH, not their own LMS or delivery platform.

--- IF IT IS A SYSTEMS INTEGRATOR OR PROFESSIONAL SERVICES FIRM ---
GSIs and professional services firms need Skillable to build and deliver labs for their clients and internal staff. List:
- Their major technology practice areas (e.g., "SAP Practice", "Salesforce Implementation", "Azure Cloud Practice")
- Their learning services or enablement arm if it exists
- Technology platforms they implement and train on for clients
Treat each major practice area as a "product" to score.

--- IF IT IS A TECHNOLOGY DISTRIBUTOR OR VAR ---
Technology distributors need Skillable to enable their internal technical staff and reseller partners. List:
- Their major vendor lines and technology portfolios they sell and support
- Technical enablement or training programs they run for partners and internal staff
- Key vendor ATP/Learning Partner certifications they hold
Treat each major vendor line or technology area as a "product" to score.

--- FOR ALL ORGANIZATIONS ---
For each item, identify:
- name: Product, program, or platform name
- category: One of: Cloud Infrastructure, Cybersecurity, Data Protection, Networking, DevOps, Application Development, Data & Analytics, Data Science & Engineering, Collaboration, ERP/CRM, Healthcare IT, Industrial/OT, Content Management, Legal Tech, FinTech, AI/ML Platform, Academic Program, Training & Certification, Technology Platform, Other
- description: One sentence describing what it does or covers
- deployment_model: "self-hosted", "cloud", "hybrid", or "saas-only"
- likely_labable: one of "highly_likely" | "likely" | "less_likely" | "not_likely"
  - "highly_likely": Installs in VM/container (any Windows or Linux software), OR native Azure/AWS IaaS/PaaS service — AND has meaningful admin workflows or technical depth. This is the default for any installable enterprise software.
  - "likely": Technically viable but with caveats — e.g., cloud-hosted with some API access, hybrid deployment, or installable but very limited interaction surface. Worth scoring.
  - "less_likely": SaaS-only on vendor's own cloud with limited API access, OR unclear deployment model, OR technically viable but weak training ecosystem or consumer-leaning.
  - "not_likely": Pure SaaS-only with no self-hosted option and no Azure/AWS native path, consumer app, locked APIs, or non-technical program. Training & Certification entries for software companies are always "not_likely".
- priority: integer starting at 1. Rank ALL products across the entire list by their value as a hands-on lab opportunity — weighting two factors equally: (1) market reach and install base (how many people use or need to learn this product), and (2) technical labability signals (installable, has APIs, complex workflows, strong training demand). The ideal priority 1 product is both widely deployed AND highly amenable to labs. Do not rank within tiers — rank across the entire portfolio. No two products should share the same priority number.

⚠️ OWNERSHIP CHECK — Before adding any product to the products list, confirm it is currently owned and sold by the TARGET COMPANY. If it is owned by a different company — even if it competes in the same space, was historically related, or is commonly mentioned alongside the target's products — it belongs in competitive_products, NOT in products. Examples: Documentum is owned by OpenText, not Hyland. SharePoint is owned by Microsoft. Do not add products to the products list if you are not certain the target company owns them today.

Return ONLY valid JSON:
{
  "company_name": "Organization Name",
  "company_description": "Brief description",
  "company_url": "main website URL",
  "organization_type": "software_company|academic_institution|training_organization|systems_integrator|technology_distributor|professional_services|other",
  "products": [
    {
      "name": "Product or Program Name",
      "category": "Category",
      "description": "One sentence",
      "deployment_model": "self-hosted|cloud|hybrid|saas-only",
      "likely_labable": "highly_likely",
      "priority": 1
    }
  ],
  "competitive_products": [
    {
      "competitor_name": "Competitor Company Name",
      "product_name": "Their Product Name",
      "category": "Category",
      "competitive_context": "One sentence on how this competes with the target company's products"
    }
  ]
}
"""

# (Legacy SCORING_PROMPT removed — superseded by PRODUCT_SCORING_PROMPT + PARTNERSHIP_PROMPT)


# ---------------------------------------------------------------------------
# Focused prompts for parallel scoring (product + partnership run simultaneously)
# ---------------------------------------------------------------------------

PRODUCT_SCORING_PROMPT = """You are an expert analyst helping Skillable evaluate whether a specific software product is a good candidate for hands-on labs ("labability").

## About Skillable
Skillable orchestrates software in cloud VMs and datacenters so learners practice real workflows in safe, instrumented environments.
- **Skillable Datacenter**: **Purpose-built for ephemeral learning and skill validation** — Skillable's datacenters are tuned to provision complete, production-grade software environments to individual learners on demand, over and over, rather than to run production workloads for long periods at scale. Cloud providers (AWS, Azure) optimize for long-running, always-on production workloads. Skillable optimizes for fast, consistent, isolated lab launches. This is the fundamental performance and cost advantage: cloud VMs are slow to start when usage is sporadic (cold-start problem); Skillable datacenter VMs launch predictably every time regardless of usage frequency. No idle storage costs, no egress bandwidth charges, no throttling — and high-cost activities like lab authoring run on the same infrastructure at no extra cost. **Always prefer datacenter over cloud VMs when the product doesn't specifically require cloud infrastructure.** Fabrics: **Hyper-V** (default — Skillable standardizes on Hyper-V due to Broadcom's extreme VMware cost increases; note Hyper-V specifically in recommendations), **VMware ESX** (use only when nested virtualization requires a non-Hyper-V hypervisor, or when socket-based licensing is a factor — on ESX, VMs with ≤24 vCPUs use 1 socket; >24 vCPUs split to 2 sockets, doubling socket license cost), **Docker** (for genuinely container-native products only; not supported: nested virtualization; large images must be pre-baked; prefer Hyper-V if the product runs on either). ANY software that installs on Windows or Linux runs in this datacenter. Custom network topologies: full support for private networks, NAT, VPNs, dedicated IP addressing, and network traffic monitoring — enables simulation of physical network configurations impossible to replicate in cloud, directly relevant for networking/SDN products (Cisco, Fortinet, F5), cybersecurity tools, and multi-VM architectures with specific inter-VM routing.
- **Cloud Slice - Azure**: Provisions isolated Azure environments per learner. Two modes: **CSR (Cloud Slice Resource Group)** restricts the learner to specific resource groups — lower privilege, appropriate for most product labs. **CSS (Cloud Slice Subscription)** gives subscription-level access including admin settings and the ability to create resource groups — required for products that need learners to configure subscription-wide settings. Supports ALL Azure services — no fixed whitelist; any service can be used after a Skillable Security Review. Also supports M365 tenant provisioning, Bicep templates (compiles to ARM at launch), and ARM JSON templates. **Access Control Policies (ACPs)** can restrict which services, SKUs, and regions a learner can provision — even on full CSS labs, the environment is locked down to exactly what the lab needs. This is Skillable's broadest cloud fabric — contrast with AWS, which has a specific supported services list.
- **Cloud Slice - AWS**: Provisions a **dedicated, isolated AWS account** per learner (stronger isolation than Azure's shared subscription model). Supported services include: EC2, RDS, S3, Lambda, DynamoDB, DynamoDB DAX, CloudFormation, ECS, EKS, ECR, API Gateway, Kinesis (standard, Analytics, Firehose, Video Streams), SNS, SQS, Step Functions, Glue, CloudWatch (metrics, events, logs), CloudFront, CloudTrail, CloudShell, Cloud9, Config, Cognito User Pools, AppSync, Athena, Redshift, EFS, Elastic Beanstalk, ELB/ALB, EventBridge, IAM, VPC, Route 53, Secrets Manager, SSM, WAF (Classic/v2/Regional), AWS Backup, IoT Analytics, OpsWorks, Auto Scaling Plans, Machine Learning (basic). **Not yet supported** (notable gaps): SageMaker, Comprehend, Rekognition, Lex, Polly, Transcribe, ElastiCache, ElasticSearch/OpenSearch, GuardDuty, Neptune, EMR, CodeBuild, CodePipeline, CodeCommit, CodeDeploy, AWS SSO, SES, ACM, Direct Connect, Directory Service, Auto Scaling (standard autoscaling), Database Migration Service, CloudHSM, Shield, XRay. **EC2 save behavior**: when a learner saves a lab, EC2 instances are suspended (billing stops); on resume, the instance reboots. ECS task counts are reduced on save and restored on resume. If a product workflow depends on persistent EC2 state across save/resume, note this in the Configure bullet. **AWS-specific lab structure**: resources are organized into Stack Deployments (equivalent to Azure resource groups) — each stack has its own ACP, resource templates, and user permissions; a lab can have multiple stacks. Automatic login to the AWS portal is available. "Deploy Default VPC" option pre-deploys default networking at launch (adds to launch time). Labs geo-locate to the nearest AWS region.
- **Skillable Simulations**: For scenarios where real labs are impractical.
- Labs include automated scoring via API, PowerShell, CLI, Azure Resource Graph queries, and AI Vision.

You will receive research for ONE product. Score it and output a single product JSON object.

Follow Steps 1-5 and Step 7 from the scoring rubric below.

## STEP 1 — API Automation Gate
Can provisioning, user account creation, license application, and environment configuration be done programmatically without learner action?
If NONE feasible → Score technical_orchestrability 0-5, add "no_api_automation" to poor_match_flags.
If requires credit card/PII → add "credit_card_required" and "broken_learner_experience".

## STEP 2 — User Persona Filter
List 2-4 from: Architect · Administrator · Security Engineer / Analyst · Infrastructure Engineer · Networking Engineer · Data Scientist · Data Engineer · Data Analyst · Business Analyst · Business User · Developer · Software Engineer · Consumer
All except Consumer are highly labable. Consumer → Score 0-3, add "consumer_product".

## STEP 3 — Determine Skillable Path

**Product category quick-reference** (orient your path recommendation before diving into scoring tiers):
→ **Skillable Datacenter (Hyper-V/ESX/Docker)**: Enterprise server software (backup, data protection, virtualization, security, monitoring); hardware-dependent tools requiring custom network topologies (SDN/networking: Cisco, Fortinet, F5, HP); traditional desktop and productivity apps complex enough to require training; data science platforms, IDEs, dev tools; any software that installs on Windows or Linux
→ **Skillable Cloud Slice (Azure/AWS)**: Enterprise SaaS platforms (Microsoft 365, Salesforce, Workday, SAP, Dynamics); cloud-native IaaS/PaaS services (Azure, AWS, Google Cloud native); multi-tenant apps requiring subscription-level admin access or cloud identity (Entra ID)
→ **Typically not labable**: Simple browser-based consumer or business apps designed for ease-of-use with no meaningful admin or technical workflows — products where the value is content consumption, not configuration or skill building

**Hyper-V / VMware / Docker fabric — Check FIRST:** Does it run in VMs (Hyper-V/VMware) or Docker containers? → skillable_path: "B"
⚠️ The VM/container image IS the lab. No runtime provisioning APIs needed. Any software that installs on Windows or Linux scores 18-25.
⚠️ Default to Hyper-V. Both Hyper-V and VMware ESX are exceptionally mature; Skillable standardizes on Hyper-V due to Broadcom's extreme VMware cost increases. Note this explicitly in Technical Orchestrability evidence.
⚠️ ESX recommendation policy: Only recommend ESX as the primary fabric when it is clearly and unambiguously the better choice — specifically: (1) the product requires nested virtualization (running a hypervisor inside the lab, e.g. VMware Player, VirtualBox, ESXi itself) AND the nested software is not Hyper-V, or (2) socket-based software licensing is a hard constraint and VM size will exceed 24 vCPUs (splitting to 2 sockets doubles per-socket license cost). If the advantage of ESX is marginal, equal, or uncertain — recommend Hyper-V and note in the Delivery Path bullet that "ESX is also available if the customer prefers it, at higher cost." ESX costs more than Hyper-V; default to Hyper-V whenever the decision is even close.
⚠️ GPU or specialist hardware (e.g. NVIDIA A100/H100) is NOT available in Skillable datacenters — can use Azure or AWS cloud VMs (via Compute Gallery / EC2 AMI), but cloud VMs are significantly slower to launch and more expensive than datacenter VMs. Flag GPU as a Blocker for cost/performance unless the product genuinely requires it.
⚠️ Note: Azure and AWS fabrics CAN run VMs (Azure Compute Gallery, AWS EC2 AMIs). Recommend cloud VMs only when one of these conditions applies: (1) the product requires cloud-native infrastructure (Entra ID, Azure PaaS services, AWS services) that can't be replicated in Skillable's datacenter; (2) GPU or specialized hardware is required; (3) the customer runs large-scale burst events requiring temporary capacity beyond what Skillable datacenters maintain — e.g., a vendor running ~10,000+ concurrent labs over a 2-3 day conference window (Tableau Conference is the canonical example: AWS VMs for a three-day spike, then scale-down). For standard ongoing training, always recommend Hyper-V for performance and cost.
⚠️ Docker is appropriate only for genuinely container-native products. Note that nested virtualization is not supported, and large images must be pre-baked into the lab at build time. If a product can run on either Hyper-V or Docker, recommend Hyper-V.
- VM + rich APIs for outcome validation: 22-25, tier: "VM - Best Case"
- VM + admin console + scripting/CLI: 20-22, tier: "VM - Best Case"
- VM + meaningful admin workflows: 18-20, tier: "VM - Standard"
- VM + limited interaction: 15-18, tier: "VM - Standard"
- Impractical (GPU farm, 100GB+, mainframe): 10-15, tier: "VM - Complex Install"

**Azure Cloud Slice:** Runs natively on Azure (IaaS/PaaS) and the service is supported by Skillable? → skillable_path: "A1"
ALL Azure services are supported (after security review). Bicep and ARM JSON templates both work. This is Skillable's broadest cloud fabric.
⚠️ Entra ID / Azure SSO is a major advantage: every Azure Cloud Slice subscription includes an Entra ID tenant. If the product authenticates via Entra ID or Azure SSO, Skillable can pre-configure the app to use that tenant automatically — clean per-learner isolation with no separate credential pool, no manual login, no credential management overhead. This elevates the path significantly compared to products that require separate identity systems.
- Rich APIs + full resource lifecycle: 20-24, tier: "Best - Rich APIs"
- Entra ID / Azure SSO authentication (app pre-configured to use tenant): 18-22, tier: "Best - Rich APIs" (note the Entra ID advantage explicitly in evidence)
- Credential pool recyclable: 15-19, tier: "Next Best - Credential Pool"
- Azure SSO but requires manual learner login steps: 11-15, tier: "Manual - Azure SSO"
- Trial accounts: 7-11, tier: "Manual - Trial Accounts" (credit card → 4-7, add flags)

**AWS Cloud Slice:** Runs natively on AWS (IaaS/PaaS) and the service is on Skillable's supported list? → skillable_path: "A1"
Supported: EC2, RDS, S3, Lambda, DynamoDB, CloudFormation, ECS, EKS, API Gateway, Kinesis, SNS, SQS, Step Functions, Glue, CloudWatch, VPC, IAM, Route 53, Secrets Manager, and more.
Not yet supported: SageMaker, Comprehend, Rekognition, Lex, Polly, Transcribe, ElastiCache, GuardDuty, CodeBuild/Pipeline — if a product relies primarily on these, note the gap.
- Rich APIs + full resource lifecycle: 20-24, tier: "Best - Rich APIs"
- Credential pool recyclable: 15-19, tier: "Next Best - Credential Pool"
- Trial accounts: 7-11, tier: "Manual - Trial Accounts" (credit card → 4-7, add flags)

**Custom API Provisioning (BYOC):** Vendor's own cloud (not Azure/AWS)? → skillable_path: "A2"
Skillable calls this Bring Your Own Cloud (BYOC). Life Cycle Actions (LCAs) handle provisioning, waiting, and teardown via the vendor's API. Salesforce sandboxes are the canonical example.
⚠️ If the vendor's platform requires MFA for API authentication → automated task scoring is NOT possible. Falls back to MCQ/fill-in-blank only. Score accordingly — this is a meaningful capability gap.
⚠️ Long provisioning times (e.g., Salesforce sandbox = up to 10 hours) require Pre-Instancing (Skillable support-only feature) to pre-build environments before the learner arrives.
- Rich APIs for all lifecycle phases (provision, configure, score, teardown), isolated instance per learner: 14-18
- Credential pool recyclable (no per-learner isolation but usable): 10-14
- SSO only (no per-learner instance): 7-11
- Trial accounts: 4-8 (credit card → 2-5, add flags)
- No isolation mechanism: 1-4

**Skillable Simulation:** When real labs not practical (too long, too costly, data sensitivity) → skillable_path: "C", score 5-10

## STEP 4 — Score All Dimensions

**Technical Orchestrability (0-25)** — from Steps 1-3.

The `technical_orchestrability` evidence bullets are SA handoff notes — written for a Skillable Solution Architect who needs to understand how to actually build this lab. Do NOT write research citations here. Write 3–4 concise, actionable bullets using these bold labels:

All automation in Skillable is delivered via **Life Cycle Actions (LCAs)** — scripts and actions triggered at specific lab events. Key events for SA design: **Pre-Build** (cloud resources deploying, run provisioning LCAs here), **Post-Build** (environment built, VMs may still be starting — run configuration LCAs here), **First Displayable** (all components running, user enters — run final-state LCAs here), **Scoring** (runs before platform scoring, use for pre-scoring validation), **Tearing Down** (run cleanup/teardown LCAs here). LCA actions: Execute Script in VM (PowerShell, Bash, Shell), Execute Script in Container (Bash), Execute Script in Cloud Platform (PowerShell, Python, C#, JavaScript — Azure and AWS both supported), Execute Custom Script (targets external APIs — PowerShell, Python, JavaScript, C#), Send Web Request (GET/POST/DELETE/PUT with @lab tokens — primary BYOC provisioning mechanism). LCAs support Blocking (hold lifecycle until complete), Delay, Repeat (poll until true — use for async provisioning wait loops), and Retry. LCA scripts can set lab variables that surface as @lab replacement tokens in instructions — use this to pass generated credentials, URLs, or resource IDs to the learner.

- **Provision:** How Skillable provisions the environment (triggered via Pre-Build LCA). For VM/Hyper-V: describe the VM image, OS, and installed software. For Cloud Slice: describe how the Azure/AWS subscription is provisioned and what gets deployed into it. For Custom API/BYOC: describe the vendor API call (web request or custom script LCA) that spins up the learner environment.
- **Configure:** What automation sets up the lab starting state (Post-Build or First Displayable LCA) — PowerShell, Python, CLI, REST API calls, seed data, user accounts, license application. For cloud platforms: runs as Execute Script in Cloud Platform (PowerShell, Python, or C# for Azure; PowerShell, Python, or JavaScript for AWS).
- **Score:** How Skillable validates that the learner completed each task (Scoring-event LCA or Automated Activity) — REST API checks, PowerShell/Python assertions, CLI output, Azure Resource Graph queries, AI Vision. Be specific about what is being checked.
- **Reset / Teardown:** How the environment is cleaned up (Tearing Down LCA) — VM snapshot revert is automatic on Hyper-V; cloud subscriptions/accounts are deleted automatically; BYOC requires an explicit teardown API call or script.
- **License / Access Note:** (include only if relevant) NFR license, dev tier, trial, or Marketplace image available — or flag if licensing is a blocker that needs vendor engagement. For socket-licensed software on ESX: note whether the expected VM size stays under 24 vCPUs (1 socket) or requires more (2 sockets, doubled license cost).

Keep each bullet to 1–2 sentences. These should be directional enough for an SA to start solutioning, not a full technical spec.

SA build notes (reference when relevant — do not include all of these, only what applies):
- Hyper-V/ESX Integration Services or VMware Tools must be installed in the VM for Skillable automation and scoring to work (LCA/ABA activities, screen commands, heartbeat detection)
- Recommended max 4 vCPUs per VM (diminishing returns beyond that); RAM is the primary cost driver — size to actual need
- Multi-VM labs: configure startup delays to prevent resource conflicts at launch; set a default VM for display order
- Nested virtualization (running a hypervisor inside the VM) requires the Nested Virtualization option enabled in the lab profile; use ESX as the host fabric when the nested software is not Hyper-V
- For cloud VMs (Azure/AWS): start from an AWS AMI or Azure Gallery image; install Skillable VM Cloud Integration Services for automation to function
- Container Volumes: Skillable supports shared file storage (Container Volumes) mounted into one or more containers in a lab. Two patterns worth noting when a product is Docker-based: (1) Code assessment pattern — learner works in Container A, hidden assessment scripts run in Container B against the same volume; cleaner than in-line scoring and preserves assessment integrity. (2) Content separation pattern — one base image used across multiple courses by swapping the attached volume (different starter files/datasets per course without rebuilding or retagging the image). Flag these patterns in the Provision bullet when the product involves coding, data science, or IDE environments.
- Custom VM Endpoints: Skillable can expose multiple protocol endpoints per VM (RDP, SSH, HTTP, HTTPS) as separate buttons in the lab interface. For products with both a web console and a CLI, configure each as its own endpoint — cleaner than switching within a single session. Flag this in the Provision bullet when the product has multiple interaction surfaces.
- Web page override: For hybrid products where the VM runs backend services but the learner interacts via a web app, Skillable can hide the VM and display a URL directly in the lab interface. Note this in the Provision bullet when it applies — it's a better learner experience than exposing the raw VM.
- Container image authoring: Lab authors build container images iteratively — launch the lab, configure the product interactively, then save and tag from the running session. No Dockerfile required. Saves create a new tagged image in the connected registry (or update existing); use version-specific tags so lab profiles always reference the right image. Note: updating an existing image affects ALL lab profiles that reference it.
- Container Web Display: Docker containers can expose a port (e.g., port 8080) and display the web app output directly in a browser tab within the lab — Skillable proxies it with SSL automatically. Canonical example: VS Code in a browser (codercom/code-server). The container author must enable port output support. Requires a network with Web Access enabled on the lab profile. Note this in the Provision bullet when the product has a web UI and runs in a container — the learner experience is clean without any separate browser setup.
- Hardware-ID licensing: Some on-prem software activates against a machine BIOS GUID/UUID (hardware-locked activation). Skillable lab profiles can pin the BIOS GUID so the same activation key works across all learner VMs. Note this in the License/Access Note bullet when a product uses this licensing model — it removes what looks like a blocker.
- Azure Resource Providers: Azure subscriptions come with a default set of registered resource providers. Non-default services (e.g. specialized compute, networking, AI services) need their provider pre-registered via PowerShell before the lab can deploy them. For any Azure-native product that uses non-standard services, note in the Configure bullet that the resource provider must be pre-registered on the subscription.
- Cloud Security Risk Levels: All cloud labs are rated Low / Medium / High risk. **Low Risk** is required for free, publicly accessible labs (open events, marketing labs). **Medium Risk** is acceptable for paid/ILT courses with unique user accounts. **High Risk** is only approved temporarily (short-term events or explicit sign-off). A lab achieves Low Risk when: compute is either denied entirely OR limited by name AND instance count (not just SKU), LCAs don't modify permissions, and durations are reasonable. Products requiring large/expensive compute or unlimited scaling are harder to get to Low Risk — note this in Blockers when recommending cloud labs for public/free consumption contexts.
- Azure quota scaling for events: Azure subscriptions have per-region resource quotas (vCPU cores, IP addresses, etc.). For training events with many concurrent learners, a quota increase request must be submitted to Microsoft in advance — typical fulfillment is a few hours but can take days to weeks for large or specialized resource types. Flag this in the Provision bullet when a product is likely to be used in high-concurrency event scenarios.
- AWS permission boundaries: Skillable defines a permission boundary (AWS IAM policy) that caps the maximum permissions any lab user can have. Learners can create IAM users within a lab, but those created users are forced onto Skillable's `LabSecureAccess` policy — preventing privilege escalation. For products where AWS IAM management is a core workflow (identity platforms, security tools, DevOps pipelines that create service accounts), note in the Configure bullet that created IAM users will have restricted permissions and the SA needs to verify the product's required IAM actions fall within the permission boundary. The `@lab.CloudSubscription.Id` replacement token provides the AWS account ID dynamically — usable in lab instructions, scripts, and CloudFormation templates for unique resource naming (AWS equivalent of Azure's `@lab.LabInstance.Id`).
- Azure lab instance ID tag: The Skillable lab instance ID is automatically added as a tag on the Azure resource group (`resourcegroup().tags.LabInstance`). ARM templates and ACPs can reference this tag — lab authors can name resources dynamically (e.g., `vmweb[labInstanceId]`) so each learner gets uniquely named resources that can be validated by exact name in scoring activity scripts. Replacement tokens (`@lab.LabInstance.Id`, `@lab.CloudPortalCredential().Password`) can also be embedded directly inside ARM template JSON for unique naming and credential injection. Note this in the Score bullet when Azure-native products benefit from deterministic, per-learner resource naming.
- Azure concurrent template deployment: Multiple resource templates in a lab deploy simultaneously — there is no sequencing. If a product deploys Azure resources with dependencies on each other (e.g., a VM that depends on a database being ready first), all dependent resources must be consolidated into a single template. **Foreground deployment (default)**: ACPs are NOT enforced until after all templates finish deploying — the template can deploy any resources regardless of ACP restrictions. **Background deployment** ("Deploy in Background" flag): ACPs are active during deployment, so the ACP must explicitly allow every resource the template deploys. Use Deploy in Background for long-running provisioning (AI model loading, large DB restore) where learners can start working before resources finish. Use Foreground when template resources should not be visible in the learner's ACP. Note this tradeoff in the Configure bullet for products with multi-service Azure architectures.
- Azure-hosted VMs (Compute Gallery): Skillable can run VMs hosted in Azure (not in Skillable's datacenter) using Azure VM images from the Compute Gallery. This is the right path for products requiring GPU instances or Azure-specific hardware (e.g., Azure N-series GPU VMs for AI model training). Images must be Specialized state — Generalized/Sysprepped images are not supported. Skillable Integration Services must be installed in the image for scoring/LCAs to work. VMs auto-geo-locate to the nearest supported region (US, Europe, Asia/Pacific) — better connectivity for global audiences. Existing Hyper-V VMs can migrate to Compute Gallery via VHD upload, but starting from an Azure Marketplace image is preferred. Note this path in the Provision bullet when a product needs GPU or hardware not available in Skillable's Hyper-V datacenter.
- AWS-hosted VMs (EC2 AMIs): Skillable can run VMs hosted in AWS via EC2. Uses existing AWS AMIs (AWS-supplied or custom) or imports from Hyper-V, Azure, VMware, or Citrix via the AWS VM Import/Export service (free). Unlike Azure Compute Gallery, AMIs are region-specific — no automatic geo-replication. Skillable Integration Services must be installed in the AMI for scoring/LCAs to work. EC2 save behavior: instances are suspended (stop billing) when a lab is saved and reboot when resumed — note this in Configure if a product's workflow depends on persistent EC2 state. Note this path in the Provision bullet when a product needs AWS-specific hardware or when migrating an existing AWS-based training environment.
- Lab Webhooks (external integration): If the vendor product requires real-time notification when lab events occur — score passback to an LMS/LRS, unlocking downstream content in the vendor's platform, or triggering external automation when a learner completes — configure Skillable webhooks. Webhooks POST lab instance JSON (user ID, score, completion status, lab profile ID) to a specified external endpoint at any lifecycle event: Pre-Build, Post-Build, First Displayable, Scoring, Scored, Torn Down, Lab Assignment Created, and others. Support the same Blocking/Delay/Retry/Error Action options as LCAs. Note in Configure when the vendor's architecture requires integration with an external tracking or content delivery system — webhooks are a cleaner pattern than having scoring scripts make outbound API calls.
- User-input variables in instructions: Lab instructions can embed `@lab.TextBox(name)`, `@lab.MaskedTextBox(name)` (passwords), or `@lab.EssayTextBox(name)` input fields — the learner types a value, which is stored as a lab variable and recalled anywhere later via `@lab.Variable(name)` or used in scoring scripts. Useful when a product's workflow requires a learner-entered value (external IP, tenant URL, license key) that downstream instructions or scoring scripts need to reference. Note this in Configure when the product involves user-provided inputs that feed into automated validation.

**Workflow Complexity (0-25):**
- AI-embedded features requiring iterative practice: +6
- DTDS: Design (+5), Tailor (+5), Deploy (+5), Support (+5), Troubleshoot (+5)
- Role-based workflows (+2), multi-VM scenarios (+2), integration complexity (+1). Cap 25.

**Training & Enablement Maturity (0-25):**
Programs where labs drive business impact — score the highest applicable combination:
- ATP/Learning Partner program (channel credentials, technical seller enablement): +10
- Certification program (customer training, skill validation): +6
- Events/conferences (product launches, adoption drives, partner events): +5
- Channel demos & tailored PoCs (reducing deal cycles, shortening time to revenue): +4
- Gray market / community training: +4
- Formal employee enablement / internal L&D programs: +3
- Existing labs/sandboxes: +2
Cap 25.

**Market & Strategic Fit (0-25):**
Category prior (highest applicable): Cybersecurity: +9 | Cloud Infrastructure: +9 | Networking/SDN: +9 | DevOps: +8 | Data Protection: +8 | Infrastructure/Virtualization: +8 | Data & Analytics: +8 | Data Science & Engineering: +7 | Application Development: +7 | Collaboration: +5 | ERP/CRM: +5 | Healthcare IT: +5 | Legal Tech: +5 | FinTech: +5 | Content Management: +5 | Industrial/OT: +4 | Simple SaaS: +1 | Consumer: +0
AI additive: Builds/Trains/Deploys AI: +5 | AI-embedded features with market demand: +2
Other: Large/growing install base: +5 | ATP pipeline: +4 | Growing category: +3 | Limited competitor labs: +2 | Skillable adjacency: +1. Cap 25.

## STEP 5 — Technical Fit Multiplier (for your awareness — system applies it)
VM/Datacenter (Hyper-V/Docker) ≥15: 1.0x | Any path ≥20: 1.0x | Tech 12-19 non-VM: 0.75x | Tech 6-11: 0.40x | Tech 0-5: 0.15x

## STEP 6 — Labability Intelligence Signals (use these to enrich technical evidence)

When you see any of these signals in the research, note them explicitly in evidence or summary:
- **Microsoft 365 End User apps (Word, Excel, SharePoint, Teams, Copilot, OneDrive, etc.)**: Skillable provides automated M365 tenant provisioning via Azure Cloud Slice using Skillable-owned tenants — no credit card or MFA required. Three tiers: Base (E3 — core apps + Entra ID P1), Full (E5 — adds Power BI Pro + Entra ID P2), Full+AI (E7, coming soon — adds Copilot + Agent 365). Teams, Power BI Premium, Power Automate Premium available as add-ons. Concurrent user licensing model (sold in increments of 15/50, annual). Note this explicitly for any product in the M365 End User space — clean automated path. Contrast with M365 Administration scenarios (managing tenant, Global Admin tasks) which require trial accounts with potential credit card/MFA for custom labs (or Microsoft-provided tenant for MOC/Learning Partners only) — score Admin scenarios lower due to trial account friction.
- **Entra ID / Azure SSO support**: Major advantage for Azure Cloud Slice — Skillable provisions an Entra ID tenant with every Azure subscription. If the product authenticates via Entra ID or Azure SSO, the app can be pre-configured to use that tenant automatically. Zero credential management, clean per-learner isolation, no manual login. Note this explicitly and score Technical Orchestrability toward the high end of the Azure Cloud Slice tier.
- **Azure Marketplace / AWS Marketplace listing**: Strong signal — confirms cloud-native deployment or partner-published image; directly compatible with Skillable Cloud Slice or Azure/AWS fabric.
- **Bicep or ARM templates available**: If the product deploys via Bicep or ARM JSON, lab authors can reuse those templates directly in Skillable Azure Cloud Slice. Note explicitly — this dramatically reduces lab build effort.
- **Docker Hub image or public container registry**: VM/container fabric ready; lab authors can pull and configure without building from scratch. Note: Skillable also supports private registries (Docker Hub private repos, Azure Container Registry, and others) — proprietary or enterprise container images are not a blocker. ACR is explicitly supported with admin account mode.
- **Bicep or ARM templates, or CloudFormation**: Native deployment format — most efficient path. Bicep compiles to ARM at launch. Note explicitly if found.
- **Terraform files**: Skillable supports Terraform via a custom solution (Terraform runs in a Docker container via a Life Cycle Action, reads .tf files from a Container Volume). Valid path for customers with existing Terraform investment, but slower to deploy than native ARM. Note as a viable path, not a native one.
- **Ansible, Helm, Kubernetes manifests**: Confirms container/cloud-native architecture — investigate whether Azure/AWS Cloud Slice or Docker fabric is the right match.
- **NFR / Developer / Trial license**: Confirms Skillable can obtain a license for lab authoring without a commercial agreement.
- **Existing LMS / LXP / delivery infrastructure**: If the vendor has an existing LMS, LXP, or learning delivery platform, note it — this determines how Skillable labs get embedded in their learner experience. Recommended integration paths in priority order: (1) **LTI 1.3** — best choice when the LMS is LTI 1.3 compliant; provides SSO, secure data exchange, real-time score passback, and scalable deployment with minimal ongoing maintenance; (2) **API integration** — best choice when the vendor has dev/IT resources; maximum flexibility, real-time learner tracking and data exchange, works regardless of LMS capabilities; (3) **Skillable TMS** — Skillable's native LMS, best when the vendor has no existing delivery platform and wants a unified solution; (4) **Custom Connector** — for vendors who need tight system coupling but lack LTI or API development capacity; (5) **SCORM** — Skillable supports SCORM well, but SCORM is a legacy standard not designed to handle the richer data that labs generate (detailed scores, activity-level completion, learner behavior, custom lab variables); recommend LTI 1.3 or API when the vendor wants to capture and act on that data. Reserve SCORM for customers where speed of deployment into an existing LMS is the only constraint and data richness is not a priority. Note the inferred best integration path in the Next Step or Program Fit bullet.
- **Existing CloudShare / Appsembler / Instruqt labs**: Confirms hands-on training demand exists; potential Skillable migration opportunity — note explicitly.
- **Existing Skillable labs found**: Note directly — this is an active or past Skillable engagement signal.
- **Deployment guide, system requirements, installation docs**: Confirms VM install viability; mention specific doc URL if found.
- **xAPI / Tin Can API requirement**: Skillable does not currently support xAPI (Experience API). If research surfaces the vendor mentioning xAPI, LRS (Learning Record Store), or Tin Can API as a requirement for their learning data infrastructure, flag it in Blockers — the SE needs to verify whether this is a hard requirement before committing. Note: this signal rarely appears in automated research; it more often surfaces in technical conversations. Flag it when found so it doesn't become a surprise late in the deal.
- **AWS service dependency check**: If the product runs on AWS, verify its core services are on Skillable's supported list. Flag explicitly if key dependencies (SageMaker, AI/ML services, ElastiCache, GuardDuty, CodePipeline) are not yet supported.

## STEP 7 — Generate Product Recommendation (2-5 crisp bullets)
Never use "Path A", "Path B", or "Path C" in the output — use the actual fabric/mechanism names instead.

Each bullet MUST start with a bold label in the format "**Label:** rest of sentence." Use ONLY these labels:

- **Delivery Path:** [fabric and delivery mechanism — state plainly. When recommending ESX, always state the specific reason explicitly: either (a) "ESX required — product runs a nested hypervisor (e.g. VMware Player/ESXi/VirtualBox) inside the lab VM that is not Hyper-V" or (b) "ESX preferred — socket-based licensing applies; VMs over 24 vCPUs would span 2 sockets on Hyper-V, doubling per-socket license cost." When recommending Hyper-V where ESX would also work, add: "ESX is also available at higher cost if the customer prefers it."]
  Examples: "**Delivery Path:** Hyper-V fabric — installs clean on Windows Server."
            "**Delivery Path:** Azure Cloud Slice — isolated Azure subscription per learner."
            "**Delivery Path:** Custom API provisioning — Skillable calls vendor APIs per learner."
            "**Delivery Path:** VMware ESX fabric — required because the lab runs a nested ESXi hypervisor inside the VM, which is not supported on Hyper-V."
            "**Delivery Path:** Hyper-V fabric — installs on Windows Server VM; ESX also available at higher cost if customer prefers VMware."

- **Scoring Rationale:** [1-2 strongest signals that drove the score — be specific. Do NOT mention existing Skillable customer status here — that belongs in the Similar Products bullet, not here.]
  Example: "**Scoring Rationale:** Deep admin workflows (workflow designer, case config, role-based access) plus a formal partner ATP program drive the high score."

- **Similar Products Already in Skillable:** [one short factual sentence naming an active Skillable customer with same delivery model — include ONLY when the parallel is genuinely strong]
  Examples: "**Similar Products Already in Skillable:** Hyland OnBase and Microsoft Windows Server both run on Skillable's Hyper-V fabric today."
            "**Similar Products Already in Skillable:** Cohesity and Commvault are both active Skillable customers in data protection."
            "**Similar Products Already in Skillable:** Tanium is an active Skillable customer in endpoint security."

- **Essential Technical Resource:** [ALWAYS include — who the Skillable rep should ask their champion to connect them with, and why. If a specific API or developer docs URL is known, embed it as a markdown link: [API Docs](https://url)]
  - VM-installable (Hyper-V/Docker): "**Essential Technical Resource:** Ask your champion to connect you with their Professional Services or Implementation Engineering team — they build customer environments and know exactly what automation is available."
  - Cloud/SaaS (Azure Cloud Slice or Custom API): "**Essential Technical Resource:** Ask your champion to connect you with their Solutions Engineering or Sales Engineering team — they own the provisioning APIs and can confirm per-learner isolation in 15 minutes."
  - Developer platforms/DevOps: "**Essential Technical Resource:** Ask your champion to connect you with their Developer Advocate or Platform Engineering team — they own the CLI and API docs."

- **Program Fit:** [which of the standard program types these labs serve, and the business outcome. Include when 2+ program types apply — this is the reusability/ROI case. Format: "**Program Fit:** Customer Training & Enablement (ILT, on-demand catalog) + Channel Enablement (technical demos, SE credentials) — a single lab investment drives adoption, reduces churn, and shortens deal cycles." Standard program types: Customer Training & Enablement (ILT/vILT, on-demand catalog, certification — drives adoption & reduces churn), Channel & Technical Seller Enablement (bootcamps, demos, tailored PoCs, SE credentials — reduces deal cycles, shortens time to revenue), Employee Training & Enablement (internal bootcamps, on-demand courses, assessments — reduces time to resolution, increases efficiency), Customer & Partner Events (adoption campaigns, product launches, exam launches — drives loyalty, generates qualified leads). Omit this bullet if only one program type applies and it's already obvious from context.]

- **Next Step:** [what the rep should do — pursue aggressively / pilot with X / monitor API roadmap / do not pursue until Y]
  Example: "**Next Step:** Pursue — strong technical fit and active partner ecosystem. Start with their Professional Services team."

- **Blockers:** [include whenever Skillable has a current platform gap that meaningfully limits what we can deliver for this product — 1-2 specific, honest items. This is about Skillable's limitations, not the product's. Examples of blockers:
  - An AWS product whose core workflow depends on a service Skillable doesn't yet support (e.g. SageMaker, GuardDuty, ElastiCache)
  - A product that requires a GPU or specialized hardware environment Skillable can't provision
  - A licensing model where no NFR/dev tier exists and vendor engagement is required before any lab can be built
  - A cloud product that has no per-tenant isolation mechanism, making clean learner separation impossible today
  Be specific — name the service, license type, or capability gap. One sentence per blocker. Omit this bullet entirely if there are no meaningful Skillable-side gaps.]
  Examples: "**Blockers:** AWS SageMaker (core to this product's ML pipeline) is not yet supported in Skillable's AWS Cloud Slice fabric — limits hands-on ML workflow coverage until Skillable adds support."
            "**Blockers:** No NFR or developer license program found — Skillable would need direct vendor engagement to obtain lab environments before authoring can begin."
            "**Blockers:** Product requires GPU instances (A100/H100) — not currently available in Skillable's VM fabric; limits AI model training scenarios."

- **Note:** [for other critical flags — credit card required, locked APIs, willing buyer/unwilling product team]
  Example: "**Note:** Trial accounts require credit card — breaks the learner experience. Do not pursue until vendor opens programmatic provisioning."

REQUIRED bullets: Delivery Path, Scoring Rationale, Essential Technical Resource, Next Step.
OPTIONAL (include when applicable): Similar Products Already in Skillable, Program Fit, Blockers, Note.
Do NOT include a "Sample Tasks" bullet — sample lab concepts are captured separately in the `lab_concepts` field and displayed at the bottom of the product card, not here.
Total: 4-7 bullets. Never use "Path A", "Path B", or "Path C".
Include Blockers whenever a real Skillable platform gap exists — this is important intelligence for the product team, not just the seller.

**Embed training URLs as markdown links wherever relevant.** The research contains URLs for training catalogs, on-demand course pages, certification programs, ILT/vILT calendars, and partner portals. When a URL is available and relevant, embed it as a markdown link directly in the bullet text — do not list URLs separately. Examples of where to embed:
- Program Fit bullet: link the training catalog or on-demand page (e.g. "Customer Training & Enablement ([Training Academy](https://...))")
- Program Fit or Scoring Rationale: link the certification page if found (e.g. "[Certified Administrator exam](https://...)")
- Next Step: link the partner portal or ATP program page if relevant
Only embed URLs that appeared in the research — do not fabricate or guess URLs.

Output `recommendation` as a JSON array of strings, one string per bullet (including the **bold label**). 4-6 items.

## STEP 8 — Consumption Potential

Estimate annual lab consumption potential for this product if the customer standardized on Skillable for all training and enablement motions. Break into 5 motions:

- **Customer Onboarding & Enablement** — new customers getting started with the product; onboarding programs, guided setup labs
- **Authorized Training Partners & Channel Enablement** — ATP network, resellers, and channel partners who deliver or sell training on this product
- **General Practice & Skilling Experiences** — ongoing skills development for existing users, admins, and practitioners; self-paced and instructor-led upskilling
- **Certification / PBT** — performance-based testing and proctored certification exams
- **Employee Technical Enablement** — internal SEs, presales, professional services, and support staff who need hands-on product skills

Estimate each motion independently based on research signals. Population sizes will vary significantly — let the data drive the estimates, not the order above.

⚠️ CONSERVATIVE BY DEFAULT. These estimates will be seen by sellers, executives, and customers. An estimate that proves accurate builds trust. An estimate that proves inflated destroys it. When any input is uncertain, use the lower end. Do not optimize for impressiveness — optimize for defensibility.

For each motion estimate:
- `population_low` / `population_high`: the actively engaged subset who would realistically participate in structured lab training — NOT the total addressable market or full install base. Use install base, ATP network size, team sizes as anchors, then apply hard realism: what fraction of that population is actively engaged in formal training programs today? Start from that subset, not the total. Keep ranges tight — high should be no more than 1.5× low (e.g. 500–750, not 500–5,000). Wide ranges signal uncertainty. When in doubt, narrow the population further and use the low end.
- `hours_low` / `hours_high`: hands-on lab hours only — not total learning time. Typical ratio is 20–40% of total course time (not 50%). A 10-hour course → 2–4 lab hours. Do not count lectures, videos, reading, or assessments. Keep the ratio ≤1.5× (e.g. 2–3 hrs, not 2–8 hrs).
- `adoption_pct`: the realistic fraction of the population who would actually complete a structured lab in a given year. These are HARD CEILINGS — do not exceed them, and default to the low end unless you have strong evidence of high lab engagement:
  - Certification / PBT: 0.02–0.04 (2–4%) — only the most dedicated pursue certification each year; most people who could certify don't
  - Customer Onboarding: 0.02–0.05 (2–5%) — most onboarding is rep-led or self-service, not structured lab-based
  - ATP / Channel Enablement: 0.05–0.10 (5–10%) — partner reps who actively complete labs, not total partner headcount
  - General Practice & Skilling: 0.02–0.05 (2–5%) — self-directed lab usage is a small minority; most practitioners learn by doing in production
  - Employee Technical Enablement: 0.08–0.15 (8–15%) — internal technical staff are highest adopters, but most employees never touch a formal lab
  Never exceed 0.20 under any circumstances. If you're near the ceiling, your population is too broad — narrow it first.
- `rationale`: 1-sentence explanation citing the specific signal that anchors your estimate (e.g. "Based on ~200 active ATPs per public partner directory and 10% completion rate for structured lab programs")

Then provide:
- `annual_hours_low`: sum of (population_low × hours_low × adoption_pct) across all motions, rounded to integer. This is the "realistic today" figure — what a reasonable first-year engagement might look like.
- `annual_hours_high`: sum of (population_high × hours_high × adoption_pct) across all motions, rounded to integer. This is the "mature engagement" ceiling — what a well-established program at good adoption looks like. It should not feel like a stretch goal.
- `vm_rate_estimate`: for VM/Datacenter (Path B) products only — estimate the lab environment complexity and set an appropriate $/hr between $12 and $55. Use $12 for simple single-VM labs, $20–25 for moderate (a few VMs or services), $30–40 for complex multi-VM with networking, $55 for exotic large environments (GPU, large clusters, specialized hardware). Set to 0 for Cloud Slice (Path A) and Simulation (Path C) products.
- `methodology_note`: 2-3 sentences shown directly to the user. Acknowledge that estimates are based on publicly available signals and are intentionally conservative — they reflect realistic engagement, not theoretical maximums. Name the 1-2 primary signals used (install base, ATP count, company headcount, etc.).

⚠️ A seller seeing these numbers will use them in conversations with customers and executives. If the numbers can't be defended with publicly available evidence, they should be lower. Directional and defensible beats impressive and wrong every time.

## Output Format
⚠️ MAXIMUM 3 evidence items per dimension. Fewer is better — one strong, specific bullet is preferable to three vague or redundant ones. Do not pad.
⚠️ EVIDENCE MUST BE UNIQUE ACROSS ALL DIMENSIONS. Do not reword or repeat the same fact in multiple dimensions. Each evidence item should cite a distinct signal — if a finding already appears under one dimension, do not include it (even reworded) under another. If you cannot find genuinely distinct signals for a dimension, use one item or a summary instead of filling the quota.

## Contact Selection Guidance

Target contacts who own external technical training, partner enablement, or certification — people a Skillable rep would call to discuss building or expanding hands-on labs.

**Good targets (decision_maker) — VP level or "Head of" equivalent ONLY:**
These titles own the budget, strategy, and vendor relationships for external technical training:
- VP of Training / VP of Partner Enablement / VP of Technical Enablement / VP of Customer Education
- Head of Customer Education / Head of Global Enablement / Head of Partner Enablement / Head of Certification
- Chief Training Officer / Chief Learning Officer (only if scope is clearly external)
- SVP or GM of [Company] Academy or University
- Senior Director of Training or Enablement (only if they clearly run the function end-to-end with no VP above them)

The key test: does this person OWN the training function and have authority to sign a vendor agreement? If yes → decision_maker. If no → influencer or exclude.

If no qualifying person can be identified from the research, use "Unknown - search for [title]" — do NOT name a lower-level person as a decision maker just to fill the slot.

**❌ NOT decision makers — these are influencers at best:**
- Directors and Managers of Training, Enablement, or Certification (unless they clearly run the whole function)
- Instructors, Trainers, Technical Training Professionals, Enablement Specialists, Enablement Managers
- Individual contributors in any enablement or training role
- Anyone whose title suggests they deliver or create content rather than own the budget and strategy
- Solutions Engineers, Sales Engineers, Field Enablement (these are influencers, not buyers)

**Good targets (influencer) — Director level or above ONLY:**
- Director of Training / Director of Partner Enablement / Director of Customer Education / Director of Certification
- Senior Director of Training or Enablement (when a VP exists above them)
- Partner Program Director / Certification Program Director
- Solutions Engineering Director or Sr. Manager (when they own SE/presales enablement)

**❌ NOT influencers — exclude these entirely:**
- Managers, Specialists, Coordinators, or individual contributors in any training or enablement role
- Instructional Designers, Instructional Design Managers, Training Professionals, Enablement Managers
- Anyone whose title suggests they create or deliver content rather than own a program budget
- Any title below Director level

If no qualifying Director-level or above person can be identified, leave the influencers list empty — do NOT name a lower-level person just to fill the slot.

**❌ EXCLUDE Learning & Development (L&D) roles entirely** — both as named contacts and as "Unknown - search for [title]" suggestions. L&D owns internal employee training: compliance courses, onboarding, corporate LMS. They do not build or buy external technical lab content for software products or partner programs. Titles to exclude: Learning & Development Manager/Director/VP, Chief Learning Officer (CLO) unless scope is clearly external, Employee Development, HR Training, Talent Development.

Return ONLY valid JSON — a single product object:
{
  "company_description": "Brief company description",
  "company_url": "URL",
  "organization_type": "software_company|academic_institution|training_organization|systems_integrator|technology_distributor|professional_services|other",
  "product": {
    "name": "Product Name",
    "product_url": "https://vendor.com/product-page — canonical product page URL, not the homepage",
    "category": "Category",
    "description": "1-2 sentence description written for a Skillable seller or SE who has never heard of this product. State what the product does, who uses it, and what problem it solves — no assumed knowledge. Example: 'Tanium Asset is an IT asset management module that gives security and operations teams real-time visibility into hardware and software inventory across every endpoint in the environment, regardless of location or connectivity.'",
    "deployment_model": "self-hosted|cloud|hybrid|saas-only",
    "skillable_path": "A1|A2|B|C|Unknown",
    "path_tier": "VM - Best Case|VM - Standard|VM - Complex Install|Best - Rich APIs|Next Best - Credential Pool|Manual - Azure SSO|Manual - Trial Accounts|Simulation|Not Viable|Unknown",
    "skillable_mechanism": "Skillable Datacenter|Cloud Slice - Azure/AWS|Cloud Slice - Vendor Cloud|Skillable Simulation|Unclear",
    "fabric": "Hyper-V|ESX|Docker|Azure Cloud Slice|AWS Cloud Slice|Custom API|Simulation|Unclear",
    "user_personas": ["Administrator", "Developer"],
    "lab_highlight": "3–5 word badge phrase answering: WHY is this product a great Skillable lab candidate? NOT a product description — the SE already knows what the product does. The badge must capture what makes it inherently hands-on or uniquely suited to lab delivery. Ask: 'What would be lost if a learner just watched a demo instead of doing it?' Good: 'Misconfigure it, something breaks', 'Every action is API-scoreable', 'Multi-VM topology required', 'Real API orchestration required', 'Config decisions have real consequences', 'Hands-on or nothing sticks', 'Build the pipeline yourself'. Bad (product descriptions — do NOT use): 'Endpoint security platform', 'Real-time asset inventory', 'Data protection solution', 'Cloud-native monitoring'. Only include if genuinely compelling. Leave empty string if nothing stands out.",
    "poor_match_flags": [],
    "api_scoring_potential": "Full|Partial|Minimal|None",
    "recommendation": ["Bullet 1", "Bullet 2", "Bullet 3"],
    "scores": {
      "technical_orchestrability": {"score": 0, "summary": "...", "evidence": [{"claim": "...", "source_url": "...", "source_title": "..."}]},
      "workflow_complexity": {"score": 0, "summary": "...", "evidence": []},
      "training_ecosystem": {"score": 0, "summary": "...", "evidence": []},
      "market_fit": {"score": 0, "summary": "...", "evidence": []}
    },
    "owning_org": {"name": "Specific org name", "type": "department|subsidiary|business_unit", "description": "..."},
    "contacts": [{"name": "Name or 'Unknown - search for [title]'", "title": "...", "role_type": "decision_maker|influencer", "linkedin_url": "...", "relevance": "..."}],
    "lab_concepts": ["Specific lab idea 1", "Specific lab idea 2"],
    "consumption_potential": {
      "motions": [
        {"label": "Customer Onboarding & Enablement", "population_low": 0, "population_high": 0, "hours_low": 0, "hours_high": 0, "adoption_pct": 0.0, "rationale": "..."},
        {"label": "Authorized Training Partners & Channel Enablement", "population_low": 0, "population_high": 0, "hours_low": 0, "hours_high": 0, "adoption_pct": 0.0, "rationale": "..."},
        {"label": "General Practice & Skilling Experiences", "population_low": 0, "population_high": 0, "hours_low": 0, "hours_high": 0, "adoption_pct": 0.0, "rationale": "..."},
        {"label": "Certification / PBT", "population_low": 0, "population_high": 0, "hours_low": 0, "hours_high": 0, "adoption_pct": 0.0, "rationale": "..."},
        {"label": "Employee Technical Enablement", "population_low": 0, "population_high": 0, "hours_low": 0, "hours_high": 0, "adoption_pct": 0.0, "rationale": "..."}
      ],
      "annual_hours_low": 0,
      "annual_hours_high": 0,
      "vm_rate_estimate": 0,
      "methodology_note": "These estimates are directional and based on publicly available signals. Treat as order-of-magnitude guidance."
    }
  }
}
"""

PARTNERSHIP_PROMPT = """You are evaluating an organization's partnership readiness for Skillable — a platform that provisions hands-on cloud/VM lab environments for software training and certification.

Score the organization's partnership readiness based on the research provided. Output ONLY the partnership_readiness JSON object.

## Evidence Format

Each evidence item's `claim` field MUST use bold-label format: **Label:** finding text.
Choose concise, specific labels that describe the signal type. Examples:
- **Dedicated Training Academy:** Cohesity University offers 150+ courses with ILT and self-paced paths
- **ATP Program:** Authorized Training Partner network with 200+ certified delivery partners globally
- **Formal Certification:** Two active certifications — CDCP and CDCA — with exam vouchers for partners
- **LMS Platform:** Uses Cornerstone OnDemand for internal and partner training delivery
- **Active Hiring:** 12 open roles for Enablement Manager and Instructional Designer on LinkedIn
- **Partner Portal:** Password-protected portal with technical enablement content and co-marketing resources

⚠️ SCORE/EVIDENCE ALIGNMENT: If a dimension scores below 80% of its maximum, at least one evidence item MUST explain what is absent or underdeveloped — not just what exists. Use a label like **Gap:** or **Missing:** or **Limited:** to flag it. A reader looking only at the evidence should be able to understand why the score is not higher. Do not show only positive signals when the score reflects meaningful gaps.

## Partnership Readiness Scoring

Determine organization type and apply the appropriate rubric.

**FOR SOFTWARE COMPANIES** (raw max = 117, system normalizes ÷1.17):

Training Org Maturity (0-35): dedicated team (+8), training owns P&L (+7), published catalog (+6), professional services (+6), technical enablement function (+4), active hiring signals (+4)

Partner Program (0-27): ATP/Learning Partner program (+12), tiered partner program with tech certs (+6), partner enablement resources (+4), ISV ecosystem (+3), channel enablement function (+2)

Customer Success (0-35): customer education content (+8), dedicated CS/onboarding team (+6), community forums (+6), advisory board (+5), active training consumption (+4), expansion revenue tied to training (+3), customer enablement function (+3)

Organizational DNA (0-10) — write 2-3 sentence narrative in summary field: training as strategic revenue driver (+4), partnership culture (+3), VP-level training leadership (+2), build-first orientation (+1)

Tech & Integration Readiness (0-10): LMS/LXP in use (+4), existing hands-on labs (+3), API-first architecture (+2), cloud-native content delivery (+1)

**FOR TRAINING ORGANIZATIONS**: Training Org Maturity: instructional design team (+10), large curriculum (+8), SME staff (+8), delivery infrastructure (+9) | Partner Program: ATP status multiple vendors (+12), own certification (+8), vendor-sponsored (+4), industry recognition (+3) | Customer Success: learner scale (+10), employer recognition (+9), outcome tracking (+8), community (+8) | Tech: LMS (+4), lab infrastructure (+4), online delivery (+2) | DNA: hands-on mission (+4), vendor partnerships (+3), lab investment (+2), build vs buy (+1)

**FOR SYSTEMS INTEGRATORS**: Training Org Maturity: L&D practice (+12), content development (+10), workforce scale (+8), lab infra (+5) | Partner Program: multi-vendor ATP (+12), practice areas (+8), vendor tiers (+7) | Customer Success: training as service (+12), enterprise client scale (+12), track record (+11) | Tech: LMS/LXP (+4), learning platform (+4), API integrations (+2) | DNA: L&D as differentiator (+4), ecosystem orientation (+3), technical enablement (+2), build-first (+1)

**FOR TECHNOLOGY DISTRIBUTORS**: Training Org Maturity: channel enablement team (+12), internal training (+10), content dev (+8), scale (+5) | Partner Program: reseller network (+12), tech cert requirements (+9), enablement programs (+6) | Customer Success: PS for clients (+12), client training (+12), vendor breadth (+11) | Tech: multi-vendor LMS (+4), lab delivery (+4), catalog (+2) | DNA: channel-first (+4), ecosystem (+3), technical training (+2), vendor breadth (+1)

**FOR ACADEMIC INSTITUTIONS**: Training Org Maturity: instructional design team (+10), tech/engineering curriculum (+9), advisory board (+8), faculty dev (+8) | Partner Program: industry partnerships (+10), vendor-sponsored programs (+9), articulation agreements (+8) | Customer Success: student success org (+10), faculty PD (+9), IT student support (+9), access programs (+7) | Tech: LMS (+4), virtual labs (+3), cloud access (+2), hybrid delivery (+1) | DNA: workforce alignment (+4), partnership-driven curriculum (+3), hands-on investment (+2), delivery innovation (+1)

## Output Format
Return ONLY valid JSON:
{
  "partnership_readiness": {
    "training_org_maturity": {"score": 0, "summary": "...", "evidence": [{"claim": "**Label:** finding text", "source_url": "...", "source_title": "..."}]},
    "partner_program": {"score": 0, "summary": "...", "evidence": [{"claim": "**Label:** finding text", "source_url": "...", "source_title": "..."}]},
    "customer_success": {"score": 0, "summary": "...", "evidence": [{"claim": "**Label:** finding text", "source_url": "...", "source_title": "..."}]},
    "organizational_dna": {"score": 0, "summary": "2-3 sentence narrative about organizational DNA", "evidence": []},
    "tech_readiness": {"score": 0, "summary": "...", "evidence": [{"claim": "**Label:** finding text", "source_url": "...", "source_title": "..."}]}
  }
}
"""


def _call_claude(system_prompt: str, user_content: str, max_tokens: int = 4000) -> dict:
    """Call Claude and parse JSON response. Retries on rate limit errors with exponential backoff."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    last_exc = None
    for attempt in range(4):
        if attempt > 0:
            wait = 15 * (2 ** (attempt - 1))  # 15s, 30s, 60s
            print(f"[scorer] Rate limit hit — retrying in {wait}s (attempt {attempt + 1}/4)")
            time.sleep(wait)
        try:
            with client.messages.stream(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            ) as stream:
                message = stream.get_final_message()
            text = message.content[0].text
            stop_reason = message.stop_reason
            if "```json" in text:
                # Use the LAST ```json block in case Claude prefaces with explanation
                text = text.rsplit("```json", 1)[1].split("```")[0]
            elif "```" in text:
                text = text.rsplit("```", 2)[-2] if text.count("```") >= 2 else text
            text = text.strip()
            if stop_reason == "max_tokens":
                raise ValueError(
                    "The analysis was too large to complete in one pass. "
                    "Please go back and select fewer products (3-5 recommended), then try again."
                )
            return json.loads(text)
        except anthropic.RateLimitError as e:
            last_exc = e
            continue
        except anthropic.APIStatusError as e:
            if e.status_code == 529:  # Anthropic overloaded
                last_exc = e
                continue
            if e.status_code == 400 and "credit balance" in str(e).lower():
                raise ValueError(
                    "You guys are using this tool a ton! Looks like your admin needs to refresh "
                    "your Anthropic API credits — please let them know."
                )
            raise
    raise last_exc


def discover_products_with_claude(findings: dict) -> dict:
    """Phase 1: Product discovery — passes all research signals to Claude for accurate product identification."""
    def _good(results: list) -> list:
        return [r for r in results if r.get("title", "") not in ("Search error", "Error")
                and not r.get("snippet", "").startswith("[Error")]

    lines = [f"# Company: {findings['company_name']}\n"]

    lines.append("## Product Search Results")
    for r in _good(findings.get("product_discovery", [])):
        lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    lines.append("\n## Training & Certification Programs")
    for r in _good(findings.get("training_programs", []) + findings.get("atp_signals", []) + findings.get("training_catalog", []))[:8]:
        lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    lines.append("\n## Partner Program & Ecosystem")
    for r in _good(findings.get("partner_ecosystem", []) + findings.get("partner_portal", []))[:5]:
        lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    if findings.get("known_products"):
        lines.append(f"\n## Known Products (user-provided): {', '.join(findings['known_products'])}")

    page_contents = findings.get("page_contents", {})
    if page_contents:
        lines.append("\n## Fetched Page Content")
        for key, content in page_contents.items():
            lines.append(f"\n### {key}:")
            lines.append(content[:2000])

    return _call_claude(DISCOVERY_PROMPT, "\n".join(lines), max_tokens=3000)


def _build_benchmarks_text() -> str:
    """Build calibration benchmarks text for product scoring calls."""
    key_companies = {"Microsoft", "Hyland", "Cohesity", "Workday", "Facebook / Meta consumer products"}
    lines = ["\n## Scoring Calibration: Known Skillable Customers",
             "Use these benchmarks to calibrate scores. Do not copy — use to ensure consistency."]
    for b in CUSTOMER_BENCHMARKS:
        if b["company"] not in key_companies:
            continue
        lines.append(f"\n### {b['company']} ({b['relationship']})")
        if "products_and_paths" in b:
            lines.append(f"Products and paths: {'; '.join(b['products_and_paths'])}")
        for dim, desc in b.get("key_signals", {}).items():
            lines.append(f"- **{dim}**: {desc}")
        if b.get("warning"):
            lines.append(f"⚠️ WARNING: {b['warning']}")
        lines.append(f"**Scoring guidance**: {b['score_guidance']}")
    return "\n".join(lines)


def _build_company_context(company_name: str, discovery_data: dict | None = None) -> str:
    """Build company-level context for partnership scoring.

    Discovery data is the PRIMARY source — it's reliably fetched in a small focused batch.
    Phase-2 product research results are not included here (they're product-specific).
    """
    def _good(results: list) -> list:
        return [r for r in results if r.get("title", "") not in ("Search error", "Error")
                and r.get("snippet", "").strip()
                and not r.get("snippet", "").startswith("[Error")]

    lines = [f"# Company: {company_name}\n"]

    if not discovery_data:
        return "\n".join(lines)

    disc = discovery_data
    disc_pages = disc.get("page_contents", {})

    # Company description (from Claude discovery response)
    if disc.get("company_description"):
        lines.append(f"**Company description:** {disc['company_description']}")
    if disc.get("company_url"):
        lines.append(f"**Company URL:** {disc['company_url']}")

    # Company homepage (fetched during discovery)
    if "company_homepage" in disc_pages:
        lines.append("\n## Company Homepage")
        lines.append(disc_pages["company_homepage"])

    # Product pages from discovery (give partnership scorer product context)
    for key in ["product_page_0", "product_page_1"]:
        if key in disc_pages:
            lines.append(f"\n## {key.replace('_', ' ').title()} (from product discovery)")
            lines.append(disc_pages[key])

    # Training & certification (ATP, catalog, programs)
    training = _good(disc.get("training_programs", []) + disc.get("atp_signals", []) + disc.get("training_catalog", []))
    if training:
        lines.append("## Training & Certification Programs")
        for r in training:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    for key in ["training_page", "atp_page"]:
        if key in disc_pages:
            lines.append(f"\n## {key.replace('_page','').title()} Page")
            lines.append(disc_pages[key])

    # Partner program & ecosystem
    partners = _good(disc.get("partner_ecosystem", []) + disc.get("partner_portal", []))
    if partners:
        lines.append("\n## Partner Program & Ecosystem")
        for r in partners:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    if "partner_portal_page" in disc_pages:
        lines.append("\n## Partner Portal Page")
        lines.append(disc_pages["partner_portal_page"])

    # Customer success & LMS
    cs_lms = _good(disc.get("cs_signals", []) + disc.get("lms_signals", []))
    if cs_lms:
        lines.append("\n## Customer Success & LMS Signals")
        for r in cs_lms:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    # Org & contacts
    org = _good(disc.get("org_contacts", []))
    if org:
        lines.append("\n## Training & Enablement Leadership Contacts")
        for r in org:
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")

    return "\n".join(lines)


def _build_product_context(name: str, all_results: dict, page_contents: dict) -> str:
    """Build per-product research context string."""
    lines = [f"## Research: {name}"]
    search_keys = [
        f"tech_{name}", f"train_{name}", f"api_{name}", f"ai_{name}", f"contact_{name}",
        f"marketplace_{name}", f"docker_{name}", f"nfr_{name}", f"deploy_{name}", f"compete_{name}",
    ]
    for key in search_keys:
        for r in all_results.get(key, []):
            lines.append(f"- **{r.get('title', '')}** ({r.get('url', '')}): {r.get('snippet', '')}")
    for key in [name, f"train_{name}", f"api_{name}"]:
        if key in page_contents:
            label = "Documentation" if key == name else key.replace(f"_{name}", "").replace("_", " ").title()
            lines.append(f"\n### {label} page for {name}:")
            lines.append(page_contents[key])
    return "\n".join(lines)


def _score_single_product(company_name: str, product: dict, product_context: str,
                           company_context: str, benchmarks_text: str) -> dict:
    """Score one product via Claude. Returns the raw product dict."""
    user_content = "\n".join([
        f"# Score this product for: {company_name}",
        f"Product: {product.get('name', '')}",
        product_context,
        company_context,
        benchmarks_text,
    ])
    data = _call_claude(PRODUCT_SCORING_PROMPT, user_content, max_tokens=7500)
    return data


def _score_partnership(company_name: str, company_context: str) -> dict:
    """Score partnership readiness via Claude. Returns the raw partnership_readiness dict."""
    user_content = f"# Partnership Readiness Assessment for: {company_name}\n\n{company_context}"
    data = _call_claude(PARTNERSHIP_PROMPT, user_content, max_tokens=4500)
    if "partnership_readiness" in data:
        return data["partnership_readiness"]
    pr_keys = {"training_org_maturity", "partner_program", "customer_success", "organizational_dna", "tech_readiness"}
    if any(k in data for k in pr_keys):
        return data
    return {}


def score_selected_products(research: dict) -> CompanyAnalysis:
    """Phase 2: Parallel scoring — one Claude call per product + one for partnership readiness."""
    company_name = research["company_name"]
    selected = research["selected_products"]
    all_results = research.get("search_results", {})
    page_contents = research.get("page_contents", {})

    discovery_data = research.get("discovery_data")
    company_context = _build_company_context(company_name, discovery_data)
    benchmarks_text = _build_benchmarks_text()

    # Fire all calls in parallel
    with ThreadPoolExecutor(max_workers=len(selected) + 1) as executor:
        product_futures = {
            executor.submit(
                _score_single_product,
                company_name, p,
                _build_product_context(p["name"], all_results, page_contents),
                company_context, benchmarks_text
            ): p["name"]
            for p in selected
        }
        partnership_future = executor.submit(_score_partnership, company_name, company_context)

        # Collect product results — 5-minute per-call timeout so a hung Claude call can't block forever
        product_results = {}
        for future in as_completed(product_futures, timeout=300):
            name = product_futures[future]
            try:
                product_results[name] = future.result()
            except Exception as e:
                product_results[name] = {"_error": str(e)}

        try:
            partnership_data = partnership_future.result()
        except Exception as pe:
            traceback.print_exc()
            partnership_data = {}

    # Log any product scoring failures and skip them — don't let errors produce "Unknown" products
    failed = {name: r for name, r in product_results.items() if "_error" in r}
    successful = {name: r for name, r in product_results.items() if "_error" not in r}
    for name, r in failed.items():
        print(f"[scorer] Product scoring failed for '{name}': {r['_error']}")

    if not successful:
        raise ValueError(
            "Scoring failed for all selected products — this is usually a temporary API issue. "
            "Please try again in a moment. If the problem persists, try selecting fewer products."
        )

    # Use first successful result for company-level metadata
    first = next(iter(successful.values()))
    products_list = []
    for p in selected:
        result = product_results.get(p["name"], {})
        if "_error" in result:
            continue  # skip failed products rather than emitting an "Unknown" entry
        product_obj = result.get("product") or result
        products_list.append(product_obj)

    data = {
        "company_description": first.get("company_description", ""),
        "company_url": first.get("company_url", ""),
        "organization_type": first.get("organization_type", "software_company"),
        "products": products_list,
        "partnership_readiness": partnership_data,
    }
    return _parse_response_to_models(company_name, data)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_consumption(d: dict) -> ConsumptionPotential:
    motions = [
        ConsumptionMotion(
            label=m.get("label", ""),
            population_low=int(m.get("population_low", 0)),
            population_high=int(m.get("population_high", 0)),
            hours_low=float(m.get("hours_low", 0)),
            hours_high=float(m.get("hours_high", 0)),
            adoption_pct=float(m.get("adoption_pct", 0.5)),
            rationale=m.get("rationale", ""),
        )
        for m in d.get("motions", [])
    ]
    return ConsumptionPotential(
        motions=motions,
        annual_hours_low=int(d.get("annual_hours_low", 0)),
        annual_hours_high=int(d.get("annual_hours_high", 0)),
        vm_rate_estimate=int(d.get("vm_rate_estimate", 0)),
        methodology_note=d.get("methodology_note", ""),
    )


def _parse_dimension(d: dict) -> DimensionScore:
    return DimensionScore(
        score=d.get("score", 0),
        summary=d.get("summary", ""),
        evidence=[
            Evidence(
                claim=e.get("claim", ""),
                source_url=e.get("source_url"),
                source_title=e.get("source_title"),
            )
            for e in d.get("evidence", [])
        ],
    )


def _parse_response_to_models(company_name: str, data: dict) -> CompanyAnalysis:
    products = []
    for p in data.get("products", []):
        scores = p.get("scores", {})
        owning_org = None
        if p.get("owning_org"):
            o = p["owning_org"]
            owning_org = OrgUnit(
                name=o.get("name", "Unknown"),
                type=o.get("type", "department"),
                description=o.get("description", ""),
            )
        contacts = [
            Contact(
                name=c.get("name", ""),
                title=c.get("title", ""),
                role_type=c.get("role_type", "influencer"),
                linkedin_url=c.get("linkedin_url"),
                relevance=c.get("relevance", ""),
            )
            for c in p.get("contacts", [])
        ]
        cp_raw = p.get("consumption_potential", {})
        product = Product(
            name=p.get("name", "Unknown"),
            product_url=p.get("product_url", ""),
            category=p.get("category", ""),
            description=p.get("description", ""),
            deployment_model=p.get("deployment_model", "unknown"),
            skillable_path={"A": "A1"}.get(p.get("skillable_path", ""), p.get("skillable_path", "Unknown")),
            path_tier=p.get("path_tier", "Unknown"),
            skillable_mechanism=p.get("skillable_mechanism", ""),
            user_personas=p.get("user_personas", []),
            lab_highlight=p.get("lab_highlight", ""),
            poor_match_flags=p.get("poor_match_flags", []),
            api_scoring_potential=p.get("api_scoring_potential", ""),
            recommendation=p.get("recommendation") if isinstance(p.get("recommendation"), list) else ([p["recommendation"]] if p.get("recommendation") else []),
            labability_score=ProductLababilityScore(
                technical_orchestrability=_parse_dimension(scores.get("technical_orchestrability", {})),
                workflow_complexity=_parse_dimension(scores.get("workflow_complexity", {})),
                training_ecosystem=_parse_dimension(scores.get("training_ecosystem", {})),
                market_fit=_parse_dimension(scores.get("market_fit", {})),
            ),
            owning_org=owning_org,
            contacts=contacts,
            lab_concepts=p.get("lab_concepts", []),
            consumption_potential=_parse_consumption(cp_raw) if cp_raw else ConsumptionPotential(),
        )
        products.append(product)

    pr = data.get("partnership_readiness", {})
    return CompanyAnalysis(
        company_name=company_name,
        company_url=data.get("company_url"),
        company_description=data.get("company_description", ""),
        organization_type=data.get("organization_type", "software_company"),
        products=products,
        partnership_readiness=PartnershipReadinessScore(
            training_org_maturity=_parse_dimension(pr.get("training_org_maturity", {})),
            partner_program=_parse_dimension(pr.get("partner_program", {})),
            customer_success=_parse_dimension(pr.get("customer_success", {})),
            organizational_dna=_parse_dimension(pr.get("organizational_dna", {})),
            tech_readiness=_parse_dimension(pr.get("tech_readiness", {})),
        ),
    )
