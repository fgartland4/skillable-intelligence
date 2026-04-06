# Skillable Delivery Patterns — Reference

All lab delivery at Skillable falls into one of three HOW categories (as shown in the internal sales slide):
- **Cloud Slice** — real cloud subscriptions (Azure, AWS, ADO, GitHub, M365)
- **Virtualization** — real VMs and containers (Hyper-V, ESX, Docker)
- **Simulation** — realistic front-end UI mimicry when real provisioning is not practical

The WHAT is always the same: hands-on labs. The WHY (business problem) drives which HOW is right.

---

## Pattern 1 — Standard VM (Hyper-V / ESX / Docker)

**What it is:** The default pattern for any software that installs on Windows or Linux. The VM image IS the lab — no runtime provisioning API needed.

**Detection signals in research:** Windows Server, Linux installer, .msi/.rpm/.deb deployment guide, Docker Hub image, ESXi/VMware deployment option, desktop application, enterprise server software, data protection, backup, monitoring, security agent, networking appliance (when virtualized).

**Hyper-V vs. ESX decision:**
- Default to Hyper-V — standardized, lower cost, faster
- ESX required only when: (a) nested virtualization runs a non-Hyper-V hypervisor inside the lab, or (b) socket-based licensing applies and VMs >24 vCPUs would double socket cost
- Docker: only for genuinely container-native products; no nested virtualization; large images must be pre-baked

**Known risks:**
- Linux VMs: second NIC at 172.20.0.0/16 (Skillable management plane, separate from data plane); SSH config tuning needed (UseDNS no saves ~10s, disable NetworkManager-wait saves ~20s); VMTools or open-vm-tools required for LCA/activities
- Windows 11 VMs: TPM/secure boot bypass via removable media + PowerShell; hardware-dependent features (Hello, BitLocker, attestation) may still fail
- No GPU in Skillable datacenter — if product requires GPU, flag as Blocker; cloud VM (Azure Compute Gallery / EC2 AMI) is the workaround at higher cost and slower launch

**Delivery models:** Self-paced ✅ · ILT/vILT ✅ · Collaborative ✅ · Events ✅

**Save/restore:** Differencing disk — automatic snapshot revert; no teardown script needed

**Scoring surface:** PowerShell/Bash scripts validate config state inside VM (file creation, service status, registry values, running processes, config files, database state). Richest automated scoring surface of all patterns.

---

## Pattern 2 — Azure Cloud Slice

**What it is:** Isolated Azure environment per learner. Two modes: CSR (resource group level, lower privilege) or CSS (subscription level, required for subscription-wide settings).

**Detection signals:** Azure-native product, Azure PaaS/IaaS service, Entra ID/Azure AD integration, M365 ecosystem, Bicep/ARM deployment templates, Azure Marketplace listing.

**Key advantages:**
- ALL Azure services supported after Skillable security review (no fixed whitelist — unlike AWS)
- Entra ID tenant included with every subscription — if product authenticates via Entra ID/Azure SSO, it can be pre-configured automatically (zero credential management, clean per-learner isolation)
- Bicep/ARM templates from vendor can be reused directly
- Access Control Policies (ACPs) restrict services/SKUs/regions even on full CSS labs

**M365 End User sub-pattern:** Skillable-owned M365 tenants, concurrent licensing model (sold in increments of 15/50). Three tiers:
- Base (E3): core apps + Entra ID P1
- Full (E5): adds Power BI Pro + Entra ID P2
- Full+AI (coming): adds Copilot + Agent 365
- Add-ons: Teams Enterprise, Power BI Premium, Power Automate Pro
- No credit card, no MFA required — cleanest automated path for M365 end-user labs
- ⚠️ Contrast with M365 Administration (managing tenant, Global Admin) — those require real tenant trial accounts with potential MFA/credit card friction

**Delivery models:** Self-paced ✅ · ILT/vILT ✅ · Events ✅ · Collaborative ❌ (per-learner subscriptions)

**Scoring surface:** PowerShell/Python/JavaScript validate cloud resource state (storage accounts, policies, role assignments, VNets, security groups, resource existence).

---

## Pattern 3 — AWS Cloud Slice

**What it is:** Dedicated isolated AWS account per learner (stronger isolation than Azure's shared subscription model).

**Detection signals:** AWS-native product, EC2/RDS/S3/Lambda dependency, CloudFormation templates, AWS Marketplace listing.

**Supported services (notable):** EC2, RDS, S3, Lambda, DynamoDB, CloudFormation, ECS, EKS, API Gateway, Kinesis, SNS, SQS, Step Functions, Glue, CloudWatch, VPC, IAM, Route 53, Secrets Manager, SSM.

**Not yet supported (flag as gaps):** SageMaker, Comprehend, Rekognition, Lex, Polly, Transcribe, ElastiCache/OpenSearch, GuardDuty, Neptune, EMR, CodeBuild/Pipeline/Commit/Deploy, AWS SSO, SES, ACM, Direct Connect, Directory Service.

**EC2 save behavior:** EC2 instances suspend on save (billing stops); reboot on resume. If product workflow depends on persistent EC2 state across save/resume, flag this.

**Delivery models:** Self-paced ✅ · ILT/vILT ✅ · Events ✅ · Collaborative ❌

---

## Pattern 4 — ADO (Azure DevOps) Cloud Slice

**What it is:** Real Azure DevOps organization provisioned per learner via Skillable's native ADO integration.

**Detection signals:** Azure DevOps training, ADO pipelines, boards, repos, artifacts, test plans.

**Known provisioning latency (empirically measured):**
- ~85% of launches: under 2 minutes (instant)
- ~15% of launches: 5–15 minutes (Microsoft org provisioning queue)
- Mitigation: Pre-Instancing (Skillable support-only feature — pre-builds environments before learner arrives)

**Delivery models:** Self-paced ✅ · Collaborative ❌ (per-user orgs)

---

## Pattern 5 — GitHub Cloud Slice

**What it is:** Real GitHub organization provisioned per learner via Skillable's native GitHub integration.

**Detection signals:** GitHub training, Actions, Copilot, repo management, GHAS, GitHub Enterprise.

**Known provisioning latency — INVERSE of ADO:**
- ~15% of launches: instant
- ~85% of launches: 5–15+ minutes (GitHub org provisioning is consistently slow)
- Pre-Instancing is strongly recommended, not optional, for reliable delivery

**Delivery models:** Self-paced ✅ · Collaborative ❌ (per-user accounts)

---

## Pattern 6 — Pre-provisioned Credential Pool + Recycling

**What it is:** Real Entra ID tenants maintained in a credential pool and recycled via teardown scripts between learners. Used when the product requires real tenant admin permissions that cannot be provisioned fresh per learner.

**Detection signals:** Quest Active Roles, One Identity, identity lifecycle management, Entra ID administration (Global Admin, Hybrid Join, tenant-level config), any product requiring real Entra tenant admin that can't use Cloud Slice.

**Known risks:**
- **Recycling completeness risk:** Teardown scripts must enumerate and reverse every possible action a learner could have taken. Any missed action leaves the tenant dirty for the next learner. This is an ongoing maintenance obligation as product features evolve.
- **License cost:** Each tenant in the pool requires an Entra ID P1 or E5 license — ongoing recurring cost.
- Customer-dedicated pool possible (tenant pool owned/funded by customer).

**Variants:** Quest Entra Tenant Recycling blueprint, Generic Entra Tenant Recycling blueprint, M365 Admin/Identity sub-pattern.

**Delivery models:** Self-paced ✅ · Collaborative ❌

---

## Pattern 7 — SSO Bridge (Anthropic-model)

**What it is:** NOT a native cloud fabric. Azure Cloud Slice provisions mailboxes; Entra ID federates into vendor's organization via SCIM. Used when a vendor requires SSO into their managed SaaS environment.

**Detection signals:** Anthropic Claude, products requiring SSO into vendor-controlled org, no per-learner isolated instance available, vendor requires organizational account membership.

**Known risks:**
- **Account ban risk:** Vendors like Anthropic actively monitor for unusual patterns and can ban accounts with no recourse or appeal process. Rate of false positives is non-trivial. This is the primary risk of this pattern.
- **Complex setup:** Requires vendor relationship and SCIM configuration; not a self-service build.
- No per-learner isolation beyond the SSO account.

**Delivery models:** Self-paced ✅ · Collaborative ❌

---

## Pattern 8 — Shared VM Infrastructure (vSphere Management)

**What it is:** A physically licensed ESX server shared by multiple concurrent learners, with user isolation at the application layer. Used specifically when the PRODUCT BEING TRAINED is vSphere itself.

**Detection signals:** VMware vSphere administration training, ESXi management, vCenter, vSAN, NSX training (where the learner is managing the hypervisor, not just running software on VMs).

**Known risks:**
- **Broadcom licensing compliance:** ESX server licenses cost ~$5,000 each under Broadcom's post-acquisition pricing. Third-party lab delivery exists in a gray area. Loop in Cloud Infra team before committing; may require direct Broadcom engagement or customer-provided licensing.
- **Self-paced not viable:** Shared infrastructure creates timing dependencies between learners. Instructor coordination required.

**Delivery models:** Collaborative/ILT ✅ ONLY · Self-paced ❌

---

## Pattern 9 — OVA Import

**What it is:** Customer provides a virtual appliance (.ova/.ovf); Skillable imports it to the ESX fabric for lab delivery.

**Detection signals:** Virtual appliance download, OVA/OVF format mentioned in product docs, hardware-bundled software, network security appliances, storage appliances, purpose-built software requiring specific hardware simulation.

**Import constraints:**
- Hardware version ≤19 (ESXi 7.0 max)
- Single VM only (multi-VM OVA sets must be restructured)
- ESX export format required (Hyper-V .vhd/.vhdx not supported via OVA path)
- VMware Workstation 12–16.2: full support · VirtualBox → ESX: full · Hyper-V ≤v10.0: full · Hyper-V >10.0: not guaranteed
- Large appliances (>~50GB): require FTP upload coordinated with Cloud Infra team (web interface = disk-only limitation)

**Hardware-fingerprinted licensing:** If the appliance uses Custom UUID licensing, Skillable can pin the BIOS UUID in the VM profile. However, if the product ALSO requires a Public IP for license validation, Custom UUID + Public IP = only 1 concurrent launch (license tied to both hardware ID and network identity).

**Delivery models:** Self-paced ✅ · ILT ✅ · Collaborative context-dependent

---

## Pattern 10 — Custom API Provisioning (BYOC)

**What it is:** Skillable calls the vendor's own cloud API at launch; Life Cycle Actions (LCAs) handle provision, configure, score, and teardown. For vendors with their own cloud platform that is not Azure or AWS.

**Detection signals:** Salesforce sandboxes (canonical example), vendor-hosted SaaS with partner/sandbox API, products with their own provisioning API for partner integrations.

**Known risks:**
- **MFA on API:** If vendor's API requires MFA for authentication, automated task scoring is not possible. Falls back to MCQ/fill-in-blank only.
- **Long provisioning times:** Salesforce sandbox can take up to 10 hours — Pre-Instancing required.
- **Teardown dependency:** Vendor API must have a DELETE/deprovision endpoint; absence is a Blocker.
- **No isolation mechanism:** If vendor cannot provide per-learner isolated instances, score 1–6 (not viable without workaround).

**Delivery models:** Self-paced ✅ · ILT ✅

---

## Pattern 11 — Simulation

**What it is:** Realistic front-end UI that mimics the product environment when real provisioning is not practical.

**When to use:**
- SaaS-only product with no sandbox/trial tier
- Security/compliance restrictions prevent real environment provisioning
- Per-instance cost is prohibitive at training scale
- Workflows take too long for a lab session (>2–4 hours in real environment)

**Detection signals:** SaaS-only deployment, no sandbox API documented, strict compliance controls on environment access, expensive per-seat licensing with no NFR tier, workflows that are inherently long-running.

**Key limitation:** Lower fidelity than real environment. Best for procedural/UI training (navigate this interface, follow this workflow). Not appropriate for deep technical validation (configure this system, troubleshoot this failure) where real system behavior matters.

**Delivery models:** Self-paced ✅ · ILT (demo-style) ✅

---

## Pattern 12 — Collaborative Labs (Multi-User / Shared Environment)

**What it is:** Multiple learners connected into a single shared environment via a common network. One learner's actions can affect others — simulating real-world team scenarios. Also called: multi-user labs, cyber range labs, shared labs.

**Two distinct use patterns (same infrastructure, different scenarios):**

**Pattern A — Parallel / Adversarial (Cyber Range)**
All learners active simultaneously. Actions are concurrent and interdependent. One learner's move affects others in real time.
- Red Team vs. Blue Team: Blue Team defends/secures network; Red Team infiltrates
- SOC team operations, incident response drills, penetration testing scenarios
- Detection signals: cybersecurity, Red/Blue Team, SOC ops, incident response, pen testing, network security operations

**Pattern B — Sequential / Assembly Line**
Learner A completes their stage and hands off a configured environment to Learner B, who builds on it and passes to Learner C. Output of one role becomes the input of the next.
- Data pipelines: data engineering (ingest/transform) → data science (model) → data analysis (insights)
- DevOps: developer builds → ops deploys → security reviews
- SDLC multi-role workflows, CI/CD pipelines
- Any scenario where real-world handoffs between roles are core to the skill being learned
- Detection signals: pipeline workflows, multi-role handoffs, data science/engineering/analysis stack, DevOps/SDLC, products with clearly defined role-based stages documented in training materials

**Why assembly line labs matter for program design:** They teach the *workflow between roles*, not just the tool itself. High-value scenario that can't be replicated in isolated single-learner environments. Strong signal for role-specific lab tracks AND assembly line connecting scenarios — multiplies program scope.

**Other use cases:**
- **Collaborative Software** — project management or SDLC tools where isolated environments don't reflect real workplace behavior
- **Enterprise Infrastructure** — shared access across all learners; realistic team-based environment

**Architecture — minimum two lab profiles:**
- **Shared Environment** (one) — provides the shared class network(s) and any shared VMs. Networks must be flagged as "Shared Class Network." Instructor launches this first from the Monitor Labs view.
- **Participant** (one or more) — each learner's lab profile. Connects to the shared network(s) and has its own VMs.
- More complex topologies: shared servers on the shared network PLUS multiple VMs per learner environment

**Delivery models:** ILT/vILT ✅ ONLY · Self-paced ❌ · Requires instructor to launch Shared Environment first

**Key constraints:**
- Instructor canceling the Shared Environment lab cancels ALL participant labs
- Requires Skillable Course Requests Team for course and class setup
- Participant can reset their own machines without affecting others

**Detection signals in research:** Red Team / Blue Team content, cyber range, SOC team training, incident response scenarios, penetration testing, network security operations, multi-role scenarios (attacker/defender), collaborative software training (SDLC tools, project management platforms used in team settings), enterprise infrastructure where team interaction is core to the workflow.

**Scoring note:** Flag Collaborative Lab as a delivery option when research surfaces any of the above signals — especially for cybersecurity products. Mention it in the Delivery Path recommendation with rationale. It is NOT a replacement for standard VM labs — it is an additive capability for team-based scenarios within a larger lab program.

---

## Lab Scenario Types (Apply Across Delivery Patterns)

These are not separate delivery patterns — they are scenario architectures that run on top of standard VM or Collaborative Lab infrastructure. Inspector should detect and recommend them when the right signals are present.

### Break/Fix (Fault Injection / Chaos)
The lab introduces a fault at launch or mid-lab via LCAs — broken service, misconfigured setting, downed network link, crashed process, corrupted config. The learner diagnoses and fixes it. No steps to follow; diagnostic reasoning is the skill being tested.

**Random variant:** Multiple faults pre-programmed; system selects which to introduce at launch so the scenario varies between learners or retakes.

**Why high-value:**
- Tests diagnostic reasoning, not procedural compliance
- Hard to complete by following steps without understanding
- Closely mirrors real-world production incidents
- High consequence of error — system stays broken if learner fails to find and fix it
- Strong for advanced/experienced audiences and certification prep

**Use cases:** Network troubleshooting, SRE/DevOps incident diagnosis, database administration, infrastructure administration, cybersecurity incident response, any product with complex failure modes.

**Detection signals:** Troubleshooting guides in product docs, advanced certification content testing diagnostic skills, incident response training, products where misconfiguration has real operational consequences, high Gate 2 products (consequence of error signal).

**Connection to Gate 2:** Products scoring high on consequence of error are prime candidates for break/fix scenarios. The Gate 2 signal that qualifies a product for labs also qualifies it for this scenario type.

---

### Simulated Attack (Solo and Collaborative)
The lab environment runs attack scripts, generates malicious traffic, or introduces a compromise — the learner responds as the defender. The lab itself is the attacker.

**Two delivery contexts — same capability, different model:**

- **Single-person lab (standard VM):** Solo Blue Team scenario. Simulated attack runs in the background; learner detects, investigates, and remediates alone. No human Red Team needed. Strong for self-paced security training.
- **Collaborative Lab:** Live Red Team participants attack while Blue Team defends in real time. Human adversaries, concurrent action, shared environment. ILT/vILT only.

**Use cases:** SIEM, EDR, identity protection, threat detection, network security, incident response — any product where the learner's job is to find and stop something bad.

**Detection signals:** Cybersecurity products, SOC operations, incident response, threat hunting, SIEM/EDR training content, penetration testing, Red/Blue Team references, products with attack surface documentation.

**Program recommendation for cybersecurity products (when signals present):**
- Self-paced: guided labs + break/fix + simulated attack (single-person)
- ILT: cyber range with live Red/Blue Team (Collaborative Lab)
- Both tracks recommended together for a complete cybersecurity program

---

## Infrastructure Pools (Supporting Mechanisms — Not Standalone Patterns)

### Cloud Subscription Pool
Skillable-managed pool of Azure/AWS subscriptions backing Cloud Slice labs. Load-balances learners across subscriptions at launch. Skillable manages this infrastructure — customers do not interact with it directly.
- Azure: Shared subscriptions, Manual pool type
- AWS: Dedicated per-learner accounts, Automated pool type

### Cloud Credential Pool
Customer/vendor-managed pool of pre-loaded credentials distributed to learners via lab instructions. The pool handles distribution only — provisioning and reset of the actual accounts happen outside the pool via LCAs, teardown scripts, or vendor-managed reset.
- Reuse policies: always new, reuse within class/event, reuse per lab profile, reuse per series, always reuse
- Blocks lab launches when no credentials are available (configurable)
- Low availability notifications configurable
- Credentials can have custom properties beyond username/password

**SaaS product scoring — three paths evaluated separately:**

| Path | Who manages environment | Pool type |
|---|---|---|
| Cloud Slice (Azure/AWS) | Skillable | Subscription Pool — Skillable-owned |
| Custom API (BYOC) | Vendor's cloud | No pool — API provisions per-learner |
| Credential Pool | Vendor/customer | Credential Pool — customer loads credentials |

For Credential Pool viability on SaaS products, research must surface: (1) does the vendor offer sandbox/training accounts? (2) can accounts be reset to clean state after each lab via API or script?

---

## Security Layer Add-ons (Layer on Top of Base Pattern)

These are not standalone patterns — they add constraints or capabilities to a base VM pattern:

**Conditional Access Policy (CAP):**
- Requires Entra ID P1 license
- Only compatible with Skillable VM labs (stable NAT or Public IP)
- NOT compatible with Cloud Slice VMs (dynamic IPs cannot be added to Entra Trusted Locations)
- Use when: training demonstrates or configures Zero Trust / MFA enforcement scenarios

**Keyboard Selector (LangSwap):**
- Adds language-specific keyboard input switching for non-English lab delivery
- Relevant for: international training programs, APAC/EMEA delivery

**Custom UUID:**
- Pins BIOS GUID in VM profile to satisfy hardware-fingerprinted license checks
- Standard add-on for appliance-based or node-locked products
- Concurrency capped at 1 if product also requires Public IP for license validation

---

## VM Import Compatibility Matrix

| Source Format | Import Support |
|---|---|
| VMware ESX 5.0–7.0 (HW ≤v19) | ✅ Full |
| VMware Workstation 12–16.2 | ✅ Full |
| VirtualBox → ESX export | ✅ Full |
| Hyper-V ≤v10.0 | ✅ Full |
| Hyper-V >v10.0 | ⚠️ Not guaranteed |
| Web interface upload | Disk-only (no OVA metadata) |
| FTP/prep server | Required for large VMs |
