# Labability Signals — Reference

This document maps research signals to delivery patterns, WHY use cases, and scoring priors.
Use this when reviewing Inspector output, answering questions, or identifying gaps in analysis.

---

## Technology → Delivery Pattern Quick Lookup

| Signal in Research | Most Likely Pattern | Key Risk to Surface |
|---|---|---|
| Azure DevOps (ADO) | ADO Cloud Slice (Pattern 4) | 15% slow provisioning — Pre-Instancing needed |
| GitHub, GitHub Actions, GHAS | GitHub Cloud Slice (Pattern 5) | 85% slow provisioning — Pre-Instancing required |
| Microsoft 365 end-user apps | M365 End User (Pattern 2) | Clean path; contrast with M365 Admin (higher friction) |
| Entra ID / Azure AD admin | Credential Pool + Recycling (Pattern 6) | Recycling completeness risk; P1/E5 license cost |
| Azure PaaS/IaaS service | Azure Cloud Slice (Pattern 2) | Check ACP restrictions needed |
| AWS service | AWS Cloud Slice (Pattern 3) | Check against supported service list |
| Windows Server / Linux installer | Standard VM / Hyper-V (Pattern 1) | Default path; no provisioning API needed |
| Docker Hub image | Standard VM / Docker (Pattern 1) | Container-native only; no nested virt |
| VMware vSphere administration | Shared VM Infrastructure (Pattern 8) | Broadcom license risk; collaborative-only |
| OVA / virtual appliance | OVA Import to ESX (Pattern 9) | HW v≤19; single VM; FTP for large files |
| Hardware-fingerprinted license | Custom UUID add-on (Pattern 9) | +Public IP = 1 concurrent launch |
| Salesforce, vendor-hosted SaaS | Custom API / BYOC (Pattern 10) | MFA risk; provisioning latency |
| Anthropic, SSO-dependent SaaS | SSO Bridge (Pattern 7) | Account ban risk; no recourse |
| Quest, One Identity | Credential Pool + Recycling (Pattern 6) | Recycling completeness; P1/E5 cost |
| SaaS-only, no sandbox | Simulation (Pattern 11) | Lower fidelity; UI training only |
| Conditional Access / Zero Trust | CAP Security Add-on | VM-only (not Cloud Slice); P1 required |
| Non-English markets | Keyboard Selector Add-on | Language-switch for input |
| GPU compute (NVIDIA, AI training) | Hybrid: Cloud + External Trial | Not in datacenter; flag cost/launch speed |

---

## Priority Research Questions by Product Type

Use these to identify which delivery pattern applies before scoring begins:

**For any product:**
- Is this SaaS-only, installable, or hybrid? (determines VM vs. Cloud Slice vs. Simulation)
- Is there a free trial, developer tier, or NFR program? (determines whether a lab can be built at all)
- Does it use Entra ID / Azure AD for authentication? (major advantage for Azure Cloud Slice)
- Is there a Docker Hub image or Azure/AWS Marketplace listing? (confirms cloud/container viability)
- Are Bicep, ARM, or CloudFormation templates available? (reduces lab build effort)

**For VM-path candidates:**
- Is there a silent install mechanism? (critical for automated provisioning)
- What does license activation look like in a network-isolated environment?
- Is licensing hardware-fingerprinted (BIOS UUID, node-locked)?
- Is there a Public IP requirement for license validation?

**For cloud-path candidates:**
- Which Azure/AWS services are core to the product? (check against supported list)
- Does the product require subscription-level admin access (CSS) or resource group level (CSR)?
- Does it require real Entra tenant admin permissions? (flags credential pool pattern)

**For identity/IAM products:**
- Does training require Global Admin or tenant-level Entra permissions?
- Is there a sandbox or isolated tenant option?
- How long does tenant provisioning take?

**For security/compliance products:**
- Are there restrictions on environment provisioning for compliance reasons?
- Does training involve Conditional Access Policy configuration?
- Is the product used in FedRAMP or government contexts? (ceiling: FedRAMP gap exists)

**For appliance-based products:**
- Is an OVA/OVF download available?
- What hardware version is the appliance exported from?
- Is licensing tied to hardware UUID or MAC address?

---

## WHY Use Case Taxonomy

These are the business problems that labs solve — the framing SADs, AEs, and CSMs use:

**Pre-sales POC / Proof of Concept Acceleration**
- Prospect can evaluate the product hands-on before buying
- Removes "show me it works in my environment" friction from deal cycle
- Best for: complex, expensive, or configuration-heavy products (security, data protection, infrastructure, monitoring)
- Supporting data: Tanium internal analysis shows 7x higher expansion revenue from customers who completed a hands-on lab POC vs. those who churned without one
- Products most likely to benefit: cybersecurity, data protection, backup/recovery, network security, enterprise infrastructure management

**Partner / Channel Enablement**
- Partners can sell what they can demonstrate and configure
- ATP programs, reseller technical certifications, SE bootcamps
- Reduces deal cycles, shortens time to partner revenue contribution
- Signal: ATP/Learning Partner program exists or is being built

**Customer Onboarding / Time-to-Value**
- New customers reach first value milestone faster
- Guided setup labs replace or augment PS engagement
- Reduces churn from customers who never fully adopt the product
- Signal: long onboarding process, complex initial configuration, PS-heavy first 90 days

**Certification / Skills Validation**
- Formal credential programs with performance-based testing
- Tamper-resistant scoring (Skillable's decisive competitive advantage — no competitor has native PBT)
- Enables exam delivery via Pearson VUE, Certiport, PSI, Certiverse
- Signal: existing certification program, exam delivery partner, skills framework

**Field Events / Conference Hands-On Labs**
- Annual user conferences, product launches, trade show tracks
- Highest-density consumption: a 3-day event can exceed months of ongoing training volume
- Known scale: Tableau Conference (14,000+ labs), Microsoft Ignite/Build, Cisco Live (~30k attendees)
- Signal: any annual conference, user summit, or "hands-on lab" in event marketing

**Competitive Differentiation**
- Hands-on labs exist for competing products; prospect has no labs (demand gap)
- Or: existing labs on CloudShare/Instruqt that Skillable can displace with deeper capability
- Signal: competitor labs found in research; Skytap/CloudShare/Instruqt references

**Non-Technical / Procedural Skills**
- HR assessments, compliance training, software process workflows
- Often simulation-appropriate (Siemens HR skills example: 6,000 HR professionals)
- Lower technical depth; value is in consistent process execution, not configuration

---

## Delivery Model Rules

| Delivery Mode | Allowed Patterns | Blocked Patterns |
|---|---|---|
| Self-paced | All except Shared VM Infra (Pattern 8) | Pattern 8 (vSphere) — timing dependencies |
| ILT / vILT | All | None |
| Collaborative (shared environment) | Pattern 8 (vSphere) ONLY | All per-user-account patterns (ADO, GitHub, Quest, Anthropic) and security-monitored patterns |
| Events | All except Pattern 8 | Pattern 8 — scaling incompatible with shared ESX |

---

## Vertical Priors (from EMERALD Customer Data)

Use these as scoring priors — a strong labability signal in these verticals is more credible because market evidence confirms demand:

| Vertical | Lab Volume | Primary Patterns | Key Signal |
|---|---|---|---|
| Cybersecurity | 5.4M labs (largest) | VM/Hyper-V, multi-VM networking | POC motion dominant (Trellix, Dragos, Tanium) |
| Systems Administration | 5.0M labs | VM, Credential Pool, vSphere | AD/identity heavy |
| Cloud / DevOps | 3.6M labs | Cloud Slice (Azure/AWS), ADO, GitHub | IaC templates common |
| AI / ML | Exploding | GPU (cloud VM), Simulation | Hands-on vs. watch growing fast |
| HR / Non-Technical | Emerging | Simulation | Siemens: 6,000 HR professionals |
| Government | Niche | VM | FedRAMP gap is ceiling; Section 508 addressable at content layer |

---

## Competitive Displacement Signals

**Skytap** (highest priority signal):
- "We currently use Skytap for labs" = high-value migration target
- Pain points: billing unpredictability, no Cloud Slice, scaling limits at events, IBM ownership friction
- Skillable advantages: PBT (Skytap has none), Cloud Slice, event scale, lower cost predictability

**CloudShare:**
- Demo/POC platform, not built for training at scale
- Critical gap: cannot support complex multi-VM environments connected by private networks
- Migration opportunity: any multi-VM topology, networking product, or training-at-scale need

**Instruqt:**
- Developer-focused, browser-native, Docker/cloud-native only
- Cannot support Windows enterprise software, complex application stacks, VM-depth workflows
- Migration opportunity: any product that needs Windows VMs or traditional enterprise software depth

**Active Skillable customers (from benchmarks):**
- When research shows a product from a company that already has Skillable labs, note explicitly in "Similar Products Already in Skillable" bullet

---

## Connectivity and Deployment Considerations

For enterprise accounts with strict network security (relevant for POC conversations):

- Skillable domains to whitelist: `*.skillable.com`, `*.labondemand.com`, `*.learnondemandsystems.com`
- Protocols: Secure WebSocket over port 443; RDP over port 21xxx or 443
- Minimum bandwidth: 200kbps consistent / 1mbps burst per learner; Azure/AWS portal: 512kbps
- Events: 5mbps per concurrent user, separate network from conference, WiFi 6 required
- VPN conflicts with geolocation: labs route to nearest datacenter by IP; VPN disrupts this
- Corporate proxy: websocket upgrade headers must not be altered; certificates must not be repackaged
- FedRAMP: not yet certified — ceiling for government procurement requirements

---

## LMS Integration Priority Order

When a vendor has an existing LMS/LXP:
1. **LTI 1.3** — best when LMS is LTI 1.3 compliant; SSO, real-time score passback, minimal maintenance
2. **API integration** — best when vendor has dev resources; maximum flexibility
3. **Skillable TMS** — when vendor has no existing platform
4. **SCORM** — legacy standard; use only when speed of LMS deployment is the sole constraint and data richness is not a priority

**Tight LMS partners (flag explicitly when found):** Cornerstone OnDemand · Docebo — pre-built connectors, proven path

**Exam delivery partners (flag when EDP found in research):** Pearson VUE (major Skillable partner) · Certiport (Pearson company) · PSI (ISACA) · Certiverse (NVIDIA, fast-growing)
