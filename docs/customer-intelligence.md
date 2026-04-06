# Customer Intelligence — Reference

Empirically-grounded data from EMERALD Customer Spotlights, internal benchmarks, and customer conversations.
Use to calibrate Inspector scoring, validate assumptions, and ground consumption estimates.

---

## Lab Volume Leaders (EMERALD)

| Vertical | Annual Lab Volume | Notes |
|---|---|---|
| Cybersecurity | 5.4M | Largest; VM-heavy; POC motion dominant |
| Systems Administration | 5.0M | AD/identity heavy; Quest/Entra patterns |
| Cloud / DevOps | 3.6M | Cloud Slice dominant; IaC-native |
| AI / ML | Exploding (no ceiling data) | GPU compute demand rising fast |
| Non-Technical | Emerging | Siemens: 6,000 HR professionals on Skillable |

---

## Proven Customer Use Cases

**Pre-sales POC / Proof of Concept:**
- **Tanium:** 7x higher expansion revenue from customers who completed a hands-on lab POC vs. churned without one — strongest available data point for the pre-sales motion ROI argument
- **Trellix, Dragos:** Security platforms using labs for prospect evaluation before purchase
- **Commvault:** Data protection labs for customer evaluation and onboarding

**Training at Scale:**
- **Microsoft:** Multiple programs (Ignite, Build, TechConnect, AI Tour) — event + ongoing training
- **Cisco:** Cisco Live ~30,000 attendees with hands-on labs at event scale
- **Tableau:** Tableau Conference — 14,000+ labs over 3–4 days; canonical high-density event example
- **Hyland:** CommunityLIVE event + ongoing OnBase/Nuxeo training
- **CompTIA, ISACA, SANS, EC-Council:** Certification body use cases with PBT at the core

**Customer Expansion / Retention:**
- **Cornerstone OnDemand, Docebo:** LMS partnerships creating indirect training pipeline

**Non-Technical / HR:**
- **Siemens:** 6,000 HR professionals completing skills assessments on Skillable — confirms non-technical lab demand is real, not theoretical

**Government / Education:**
- **SAIT:** Government-adjacent; DOE relationship confirmed
- FedRAMP gap is the hard ceiling for government procurement — addressable only when Skillable pursues certification
- Section 508 (accessibility) is addressable at the content/instruction layer, not a platform gap

---

## Discontinued / Paused Customers (and Reason)

Understanding why customers left helps calibrate risk:

| Customer | Status | Reason |
|---|---|---|
| AWS | Discontinued | Business/relationship decision — not technical capability |
| Tableau | Special case | 3-day burst event model (AWS VMs); then reduced; seasonal relationship |
| Benchling | Discontinued | Business/relationship reasons — not technical |

---

## Active Prospects (from EMERALD era)

| Prospect | Signal |
|---|---|
| Google | Active engagement |
| HashiCorp | Active engagement (now IBM/HCP) |
| NVIDIA | Active; uses Certiverse as EDP |

---

## Competitive Displacement Benchmarks

Priority order for lab platform competitive signals (ranked by frequency/importance):

**#1 — DIY**
- Most common competitor; many companies have built internal lab portals or custom VM environments
- Pain: engineering maintenance burden, no scoring, no LMS integration, hard to scale
- Indicator phrases: "we built it ourselves," "internal lab environment," "custom training infrastructure"
- Treatment: strong displacement opportunity — they're already spending money on something Skillable does better

**#2 — Skytap**
- Legacy platform; many customers actively looking to modernize
- Pain: billing unpredictability (usage spikes = surprise invoices), no Cloud Slice capability, scaling limits at events, IBM ownership adds sales cycle friction
- Indicator phrases: "we use Skytap," "Skytap labs," "migrating from Skytap"
- Treatment: immediate high-priority flag; warmest possible lab platform conversations

**#3 — CloudShare**
- Common in pre-sales demo and POC environments
- Cannot support complex multi-VM private networking — that's Skillable's clearest technical win against them
- When found: note as migration opportunity in Inspector output

**#4 — Instruqt**
- Common in developer relations and DevOps communities
- Docker/browser-native only; cannot support Windows enterprise software or VM-depth workflows
- When found: note as migration opportunity if product requires traditional software depth

---

## POC Motion ROI Framework

When a product is complex, expensive, or configuration-heavy, the pre-sales POC motion deserves explicit framing:

**The argument for the seller:**
"Before your prospect signs, they need to see it work. Today that means a PS-delivered or SE-guided evaluation that takes weeks and costs us delivery hours. A Skillable lab delivers the same experience in 2 hours, on demand, at any stage of the deal."

**Supporting data point:** Tanium's analysis shows 7x higher expansion revenue from customers who completed a hands-on POC vs. those who churned. This stat is publicly referenceable in Skillable conversations.

**Products most likely to benefit:**
- Cybersecurity (endpoint, SIEM, SOC tools)
- Data protection / backup / recovery
- Network security appliances
- Enterprise infrastructure management (monitoring, observability)
- Identity and access management

---

## Event Scale Reference Points

Use these to calibrate Events & Conferences consumption motion estimates:

| Event | Scale | Lab Volume |
|---|---|---|
| Cisco Live | ~30,000 attendees | Large |
| Tableau Conference | 14,000+ | 14,000+ labs / 3–4 days |
| Microsoft Ignite / Build | Large | Multiple tracks |
| Tanium Converge | Moderate | Confirmed hands-on |
| Hyland CommunityLIVE | Moderate | Confirmed hands-on |

Rule of thumb: A 3-day conference event with 500 lab-track attendees at 50% adoption and 2 hours per lab = 500 hours of lab consumption. That equals roughly 2 months of ongoing self-paced training at typical adoption rates.

---

## License Management Process Reference

When a product requires a non-standard license for lab delivery:

**New license process:**
1. Initial Discovery (SE/TSM) — identify what license is needed and surface to Solution Architecture / P&T
2. Initial Solutioning (Solution Architecture / P&T) — determine if an existing Skillable-held license covers it, or if a new license is required
3. Policies & Procedures — establish how the license is maintained and scaled

**Existing license process:**
1. License Request — submitted via internal process
2. Acquisition — obtained from vendor
3. Maintenance — ongoing renewal and compliance tracking

**Critical questions for any non-standard license:**
- Is it per lab instance or per real human?
- Can the license be reused across multiple VMs or is it single-use?
- How does activation/deactivation scale with lab volume?
- Must the license pool be customer-dedicated, or can it be Skillable-shared?

---

## M365 Tenant Infrastructure Reference

For reference when discussing M365 or Entra ID lab scenarios:

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

## Platform Capability Flags

Quick reference for capabilities that affect scoring or recommendations:

| Capability | Status | Notes |
|---|---|---|
| Performance-Based Testing (PBT) | ✅ Live | No competitor has native PBT — Skillable exclusive |
| AI Vision scoring | ✅ Live | GUI-heavy products with no CLI/API surface |
| Scoring Bot | ✅ Live | Hyper-V only; hidden Windows 10 VM for cross-VM scoring |
| Geolocation | ✅ Live | Auto-routes to nearest datacenter; VPN disrupts |
| Edge AI Translation | ✅ Live | 100+ languages via Edge browser; no extension needed |
| LTI 1.3 | ✅ Live | Preferred LMS integration method |
| SCORM | ✅ Live | Geolocation-aware since Oct 2024; use for legacy LMS only |
| xAPI / Tin Can API | ❌ Not supported | Flag as Blocker if vendor requires LRS |
| FedRAMP | ❌ Not certified | Hard ceiling for government procurement |
| GPU in datacenter | ❌ Not available | Azure Compute Gallery / EC2 AMI workaround (slower, pricier) |
| Pre-Instancing | ✅ Live (support-only) | Required for ADO, GitHub, Salesforce — mitigates provisioning latency |
| Custom UUID | ✅ Live | Hardware-fingerprinted license support; concurrency capped with Public IP |
| Conditional Access Policy | ✅ Live | VM-only (NAT/PubIP); not compatible with Cloud Slice dynamic IPs |
| AI Content Assistant | ✅ Live | Lab authoring tool — Designer phase, not Inspector |
| AI Practice Generator | ✅ Live | Learner-driven practice scenarios — Designer phase, not Inspector |
