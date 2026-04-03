"""Claude API calls for the Designer tool — Lab Program Designer.

This module is a stub. Implementation is Phase 3 of the platform plan.

---

## SA Build Notes — IMPORTANT: Include in Designer prompts

The SA build notes below were intentionally removed from the Inspector scoring
prompt (scorer.py) to reduce token cost — they don't affect labability scoring.

BUT they are exactly the platform knowledge a Solution Engineer needs when
building a Proof of Concept. When implementing the Phase 2 (Program Architecture)
and Phase 3 (Lab Content) Designer prompts, inject the relevant notes from this
list so Claude can produce accurate, buildable lab architecture guidance.

The notes:

### Skillable Datacenter / VM fabric (Hyper-V / ESX / Docker)
- Hyper-V/ESX Integration Services or VMware Tools must be installed in the VM
  for Skillable automation and scoring to work (LCA/ABA activities, screen
  commands, heartbeat detection).
- Recommended max 4 vCPUs per VM (diminishing returns beyond that); RAM is the
  primary cost driver — size to actual need.
- Multi-VM labs: configure startup delays between VMs to prevent resource
  conflicts at launch; set a default VM for display order.
- Nested virtualization (running a hypervisor inside the lab VM) requires the
  Nested Virtualization option enabled in the lab profile; use ESX as the host
  fabric when the nested software is not Hyper-V.
- Hardware-ID licensing: some on-prem software activates against a machine BIOS
  GUID/UUID (hardware-locked activation). Skillable lab profiles can pin the BIOS
  GUID so the same activation key works across all learner VMs — removes what
  looks like a blocker.
- Custom VM Endpoints: Skillable can expose multiple protocol endpoints per VM
  (RDP, SSH, HTTP, HTTPS) as separate buttons in the lab interface. For products
  with both a web console and a CLI, configure each as its own endpoint.
- Web page override: for hybrid products where the VM runs backend services but
  the learner interacts via a web app, Skillable can hide the VM and display the
  URL directly in the lab interface — cleaner learner experience.

### Docker / Container fabric
- Container Volumes: Skillable supports shared file storage mounted into one or
  more containers. Two patterns: (1) Code assessment — learner works in Container
  A, hidden assessment scripts run in Container B against the same volume.
  (2) Content separation — one base image used across multiple courses by swapping
  the attached volume (different starter files/datasets per course).
- Container image authoring: lab authors build images iteratively — launch the
  lab, configure interactively, save and tag from the running session. No
  Dockerfile required.
- Container Web Display: Docker containers can expose a port and display the web
  app directly in a browser tab within the lab — Skillable proxies it with SSL
  automatically (e.g., VS Code in browser via codercom/code-server).

### Azure Cloud Slice
- Azure Resource Providers: non-default services need their provider pre-registered
  via PowerShell before the lab can deploy them.
- Cloud Security Risk Levels: Low Risk required for free/public labs; Medium Risk
  acceptable for paid/ILT; High Risk only approved temporarily. A lab achieves Low
  Risk when compute is denied or limited by name AND instance count.
- Azure quota scaling for events: quota increase requests must be submitted to
  Microsoft in advance — can take days to weeks for large/specialized resources.
- Azure lab instance ID tag: automatically added to the resource group
  (resourcegroup().tags.LabInstance) — lab authors can name resources dynamically
  for deterministic per-learner scoring.
- Azure concurrent template deployment: multiple resource templates deploy
  simultaneously (no sequencing). Foreground deployment: ACPs not enforced until
  all templates finish. Background deployment: ACPs active during deployment —
  use for long-running provisioning where learners can start working early.
- Azure-hosted VMs (Compute Gallery): right path for GPU instances or
  Azure-specific hardware. Images must be Specialized state. VMs auto-geo-locate
  to nearest supported region.
- Lab Webhooks: POST lab instance JSON to an external endpoint at any lifecycle
  event (Pre-Build, Post-Build, Scoring, Torn Down, etc.) — use for score
  passback to LMS/LRS or unlocking downstream content in the vendor's platform.
- User-input variables: @lab.TextBox(name), @lab.MaskedTextBox(name),
  @lab.EssayTextBox(name) — learner-entered values stored as lab variables,
  recalled anywhere via @lab.Variable(name) or used in scoring scripts.

### AWS Cloud Slice
- AWS-hosted VMs (EC2 AMIs): uses AWS AMIs; AMIs are region-specific (no
  auto-geo-replication). EC2 save behavior: instances suspended on save (billing
  stops) and reboot on resume — note if product workflow depends on persistent
  EC2 state.
- AWS permission boundaries: Skillable caps max permissions via IAM policy;
  learner-created IAM users are forced onto LabSecureAccess policy — verify
  product's required IAM actions fall within the boundary.

---

## Inspector → Designer handoff

When a Designer session is seeded from an Inspector analysis (`analysis_id`
provided), load the following from the InspectorAnalysis record and pre-fill
Phase 1:
- company_name, company_description, organization_type
- top_products (sorted by labability_score.total)
- orchestration_method, fabric, skillable_mechanism per product
- consumption_potential per product (for program sizing context)
- contacts (decision makers and influencers — for stakeholder context)

Phase 2 (Program Architecture) should use the product's `fabric` and
`orchestration_method` to select the correct SA build notes above and include them
in the Claude prompt for that phase.
"""


# ---------------------------------------------------------------------------
# Phase 1 — Requirements & Intent
# ---------------------------------------------------------------------------

# TODO: implement


# ---------------------------------------------------------------------------
# Phase 2 — Program Architecture
# ---------------------------------------------------------------------------

# TODO: implement
# Inject SA build notes relevant to product.fabric when generating architecture


# ---------------------------------------------------------------------------
# Phase 3 — Lab Content
# ---------------------------------------------------------------------------

# TODO: implement


# ---------------------------------------------------------------------------
# Phase 4 — Package & Export
# ---------------------------------------------------------------------------

# TODO: implement
