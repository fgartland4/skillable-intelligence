# Skillable Intelligence — Designer

> Designer guides program owners, instructional designers, and subject matter experts through the full process of designing a lab program — from goals and audience through a complete, approved outline, draft instructions, and a Skillable Studio-ready export package.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md). Designer is typically seeded from an Inspector analysis — see [inspector.md](inspector.md) for the handoff flow.

---

## Why Designer Exists

### The Adoption Problem

Customers who don't know how to design a lab program won't build one. And if they don't build one, they don't adopt Skillable.

This is not a hypothetical. Most new customers — and many program owners who are new to labs even at experienced companies — arrive without a mental model for what a lab program is, how it's structured, or how to make decisions about scope, sequencing, and activity design. Skillable Studio is built for lab developers: the contracted SMEs and borrowed SEs who do the technical building work. It is not built for the program owner, instructional designer, or champion who needs to figure out *what to build* before anyone starts building.

Without a tool to guide that design process, the default pattern is predictable: everyone waits for the technical team to get the software working in the platform. By the time the environment is ready, the program timeline is compressed, the energy has dissipated, and a few labs get built to justify the contract. Those labs rarely have a clear structure, almost never have activities, and produce too little learner engagement to demonstrate value. The customer isn't churning — but they're not growing either. They can't grow, because they never built the foundation that growth requires.

Designer exists to break that pattern.

### The Parallel Workstream

The critical insight behind Designer's design is that program design and environment build are independent workstreams that can — and should — happen simultaneously.

While the technical team is getting the software working in Skillable, the program owner and instructional designer can be in Designer: defining objectives, designing the curriculum, building the outline, and approving the program structure. When the technical team has the environment ready, the program design is already done. The contracted SME or SE can start building immediately against a clear, approved blueprint — instead of making structural decisions that were never the technical team's job to make.

Designer is what gives the program owner something concrete to do on day one. That changes the entire trajectory of a new customer engagement.

### Building the Discipline

Even well-resourced, experienced customers don't consistently produce great labs. Common problems: no activities (which means no progress tracking and no scoring), seat times that are too long or too short, lab titles that don't reflect what the learner actually does, programs that don't align to a competency framework, and environments that require ongoing rework because nobody thought through all the software requirements before the first lab was built.

These aren't failures of effort — they're failures of process. And they affect even the most capable content teams, because the contracted SMEs and SEs who do the technical building work often have no idea that features like activities, scoring, collaborative scenarios, or credential pools exist — let alone when and why to use them.

Designer builds the discipline by making good decisions the default. The checklist surfaces what's missing. The outline enforces the series → lab → activity hierarchy that makes scoring possible. The draft instructions include guidance on how to validate each activity. The BOM surfaces features like credential pools, variables, and replacement tokens at exactly the moment when they're relevant to the program being designed.

A content team that goes through Designer once comes out with a better mental model for labs. The second time, they bring that model with them. Over time, Designer doesn't just produce better programs — it produces better teams.

---

## Who Uses Designer

**Program Owners** are Designer's primary audience for Phases 1 and 2. They define the goals, the audience, the learning objectives, and the program scope. Designer guides them through that definition process — asking the right questions, reading uploaded materials, and helping them think through decisions they may never have made before. Typical trigger: new customer engagement beginning, or an existing customer starting a new program area.

**Instructional Designers** use Designer throughout Phases 1–3. In Phase 1, they contribute job task analysis, audience definitions, and competency frameworks. In Phase 2, they refine the outline — adjusting series structure, lab count, and activity design in collaboration with the AI. In Phase 3, they review and refine draft instructions and scoring recommendations before handing off to SMEs.

**Subject Matter Experts (SMEs)** engage primarily in Phases 2 and 3. In Phase 2, they validate that the lab scenarios and activities reflect accurate, realistic product workflows. In Phase 3, they review and tech-edit draft instructions. Designer gives SMEs a structured starting point — a concrete outline to react to — rather than asking them to generate program structure from scratch.

**Skillable Learning Consultants and Professional Services** use Designer to accelerate scoping engagements. Instead of arriving at a customer conversation with a blank page, they arrive with a draft program architecture seeded from Inspector — already grounded in the customer's products, delivery constraints, and organizational readiness signals.

**Contracted Lab Developers** are the downstream consumers of Designer's output. They don't use Designer directly — they work in Skillable Studio. But the Studio import package Designer produces creates all the lab series, lab profiles, draft instructions, and activities the developer needs to build against. Their job becomes: make this work technically. Not: figure out what to build.

---

## What Designer Delivers

Designer produces output across four phases, each building on the last and producing a discrete, reviewable artifact.

**Phase 1 — Requirements & Intent**
A fully populated Lab Blueprint: objectives (business and learning), target audiences, primary product, difficulty level, seat time, success criteria, scenario seeds, and competency framework. The AI reads uploaded materials and asks questions to fill gaps. The checklist panel shows exactly what's confirmed, what's partial, and what's still missing — in real time, as uploads are processed and questions are answered.

**Phase 2 — Program Architecture**
A complete, approved program outline: lab series with names and descriptions, labs within each series with titles and descriptions, and activities within each lab. The outline reflects the product's complexity, the defined roles, the approved seat time, and any scenario type signals (break/fix, simulated attack, collaborative lab) surfaced from Inspector. Conversational refinement allows the program owner to merge labs, split series, cut scope, or reorganize structure before approving.

**Phase 3 — Draft Instructions & Scoring Recommendations**
Draft lab instructions for every lab in the approved outline, formatted in a preview pane that matches actual Skillable Studio instruction width. Each set of draft instructions includes AI-generated recommendations for how to validate each activity — not the scoring scripts themselves, but the logic and approach that guides the lab developer building the validation in Studio. SMEs review, refine, and approve before Phase 4.

**Phase 4 — Package & Export**
Two deliverables:

1. **Bill of Materials** — a complete, structured list of everything needed to build the lab environments: VMs and OS configurations, software and tools, accounts and credentials, data files (including dummy data for CRM, ERP, or other data-dependent products), networking and permission requirements, lifecycle scripts, scoring and assessment requirements, and notes on Skillable Studio features to configure (credential pools, subscription pools, variables, replacement tokens, collaborative lab setup). The BOM is generated after all labs are designed — which makes it dramatically more complete and accurate than any BOM built before the program was defined.

2. **Skillable Studio Export Package** — a downloadable ZIP containing a `data.json` file that imports directly into Skillable Studio, creating all lab series, lab profiles, draft instructions, and activities. The contracted lab developer imports the package and builds from there — the structural decisions are already made.

---

## How Designer Works

### Seeding from Inspector

The primary entry point is `GET /designer?analysis_id={inspector_analysis_id}`. Designer loads company name, scored products, delivery path recommendation, Gate scores, consumption estimates, scenario type flags, and key contacts from the Inspector analysis. Phase 1 fields pre-fill automatically. The user reviews and confirms before the AI asks follow-up questions.

Designer also accepts manual entry when no Inspector analysis exists — for PS engagements where Inspector hasn't run, or where the customer's product is already known.

### Phase 1 — Requirements & Intent

The Phase 1 interface has two panels. The left panel is the main conversation area: the user uploads documents (job task analysis, existing course outlines, product documentation, audience profiles, any prior training materials), provides URLs to documentation sites, and responds to AI questions. The right panel is the Lab Blueprint checklist — a live progress tracker that updates as the AI processes uploads and confirms information.

**The Lab Blueprint checklist tracks eight requirements:**
1. Business / Learning Objectives — what the program needs to achieve
2. Target Audience(s) — roles, experience levels, prerequisites
3. Primary Product / Platform — the product being trained on
4. Recommended Difficulty — Beginner / Intermediate / Advanced / Expert
5. Target Lab Duration — seat time per lab (default 45–75 min; adjustable in Preferences)
6. Success Criteria — how program success will be measured
7. Scenario Seeds — initial ideas for lab scenarios and use cases
8. Competency Framework — alignment to a skills or certification framework, if applicable

Each item shows a filled green indicator when confirmed, a gray indicator when empty, and a summary of what's been captured when expanded. The AI prompts for missing items conversationally — it doesn't wait for the user to realize something is missing.

Phase 1 is complete when the program owner and AI have enough shared understanding of goals, audience, and scope to generate a meaningful program outline.

### Phase 2 — Program Architecture

Once Phase 1 is approved, the AI generates a complete program outline structured as:

**Series → Labs → Activities**

- **Series** are the top-level groupings (e.g., Administration Fundamentals, Advanced Configuration, Troubleshooting)
- **Labs** are the individual practice units within each series — 45–75 minutes, three to eight activities each
- **Activities** are the discrete tasks within each lab — the unit of progress tracking and scoring in Skillable Studio

The outline includes well-formed names and short descriptions at every level. Scenario type recommendations (break/fix, simulated attack, collaborative lab) appear where Inspector signals or program context supports them.

Every level of the outline is expandable and collapsible. The program owner refines through conversation: "merge labs 4 and 5," "make this two series instead of three," "I only have budget for 12 labs — which ones should I keep?" The AI responds with a revised outline. This continues until the outline is approved.

**Activities are not optional.** They are how Skillable tracks learner progress and the only level at which scoring is possible. Designer treats activity design as a first-class part of program architecture — not an afterthought for the lab developer.

Once the outline is approved, it's saved. Collaborators (SMEs, IDs, additional program owners) can review and engage with the AI to evolve the framework before moving to Phase 3.

### Phase 3 — Draft Instructions & Scoring Recommendations

When the outline is approved, the UI shifts: the main pane becomes a lab-by-lab instructions workspace, and the right panel narrows to approximately the width of actual Skillable Studio lab instructions. This previews what learners will see.

For each lab, the AI generates:
- Draft lab instructions organized by activity
- Recommendations for how each activity should be validated — the logic and approach for scoring, surfaced as guidance for the lab developer who will configure validation in Studio

The program owner or ID reviews each lab's draft with the AI — refining language, adjusting task descriptions, clarifying validation approaches. SMEs can be brought in at this stage to tech-edit for accuracy.

Phase 3 output is draft scaffolding — not finished content. The draft instructions are a head start for the SME or tech writer who will do final authoring in Skillable Studio.

### Phase 4 — Package & Export

Phase 4 packages everything into two deliverables for export.

The **Bill of Materials** is organized into categories: Cloud & Subscriptions, Virtual Machines, Containers & IDEs, Software & Tools, Accounts & Credentials, Data & Files, Networking & Permissions, Lifecycle Scripts, Scoring & Assessment. Each item specifies what's needed, relevant details, and whether it's required or optional. The BOM also surfaces relevant Skillable Studio features the builder needs to configure — credential pools, subscription pools, variables, replacement tokens, collaborative lab network setup — at the point where they're relevant to this specific program.

The **Skillable Studio Export Package** is a ZIP containing `data.json` — importable directly into Skillable Studio. The import creates:
- All lab series
- All lab profiles with draft instructions
- All activities, pre-created and attached to the correct labs

The contracted SME or lab developer imports the package and begins the technical build. The structural scaffolding is done.

### Delivery Path Respect

Designer builds entirely for the confirmed delivery path. If Hyper-V is recommended but the customer prefers VMware, Designer proceeds with VMware — and surfaces a clear, non-intrusive note: *"Hyper-V delivers equivalent capability at lower cost due to Broadcom's pricing changes. You can switch at any time."* Designer is an advisor, not a gatekeeper.

---

## Preferences

### Settings Hierarchy

Preferences operates on a two-level hierarchy:

- **Global defaults** — set once at the organization level, apply to every new program automatically
- **Per-program overrides** — program owners can override any global default for a specific program without changing the global standard

This means a content team sets their standards once and every program inherits them. A program that needs different defaults (different audience level, different delivery path, different seat time) overrides only what's different — everything else flows down from the global standard.

### Setup vs. Preferences

Two categories of configuration exist in Designer, and they belong in separate places:

**System Setup (Admin — configured once):**
AI provider connection, API key, model configuration. Configured once during customer onboarding — typically by Skillable or the customer's technical admin. Lives in a separate Admin section, not in Preferences. Most users never see it after initial setup.

**Preferences (Program Standards — used regularly):**
The defaults that shape every program Designer generates. Organized into six groups, each with a distinct owner and purpose. This is where the first-run onboarding guided setup focuses.

### First-Run Onboarding

When a new customer account is provisioned, the AI connection is configured by Skillable before the customer logs in. The first thing a new user sees is the Preferences guided setup — a walk-through of the six groups that explains why each section matters and establishes the organization's content DNA before any program is started.

If the customer has an Inspector analysis, Preferences can be pre-populated with smart defaults — a cybersecurity product triggers break/fix and collaborative lab recommendations; a networking product triggers Hyper-V default and multi-VM environment suggestions. The PS team or LC confirms before handing off to the program owner.

### The Six Preference Groups

**1. Content Standards** *(Program owner)*
The structural and naming defaults that make every lab feel like it belongs to the same program.

| Setting | Options | Purpose |
|---|---|---|
| Target Lab Duration | 15–30 / 30–45 / **45–75** / 75–90 / 90–120 / 120+ min | Default seat time per lab; 45–75 min recommended for most complex products |
| Activities per Lab | 1–2 / **3–5** / 6–10 / Unlimited | Default activity count; 3–5 recommended for 45–75 min labs |
| Default Difficulty | Beginner / **Intermediate** / Advanced / Expert | Baseline difficulty for generated outlines |
| Lab Naming Formula | Text field: `{Verb} {Specific Action} {Product Name}` | Consistent, well-formed lab titles across every program |
| Activity Naming Convention | Text field with variables | Consistent activity titles; mirrors lab naming logic |
| Lab Series Naming Convention | Text field | Consistent series titles at the program level |
| Lab Pass Threshold | % of activities required | Default completion standard for scoring configuration |

**2. Learning Design Standards** *(Instructional Designer / Program owner)*
The pedagogical defaults that align labs to recognized frameworks and ensure consistent instructional quality.

| Setting | Options | Purpose |
|---|---|---|
| Writing Style Guide | Microsoft / Google / Apple / Red Hat / Custom URL | Applies a consistent writing voice to all draft instructions |
| Certification Alignment | Free text / None | Aligns objectives and activity structure to a specific certification or exam |
| Standards Framework | Bloom's Taxonomy / NICE NCWF / CompTIA / SFIA / None | Informs objective framing and competency mapping in Phase 1 |
| Hint Usage Policy | Always / On request / Never | Whether draft instructions include hint structures for learners |
| Knowledge Block Usage | Yes / No | Whether draft instructions use knowledge blocks for background context |
| SME Handoff Format | Inline AI comments / Clean draft only | Whether draft instructions include AI guidance notes for the SME |

**3. Scenario & Lab Type Defaults** *(PS / Program owner)*
Controls which advanced scenario types Designer recommends during outline generation. Can be pre-populated from Inspector signals.

| Setting | Options | Purpose |
|---|---|---|
| Break/Fix Scenarios | Yes / No / AI-recommended | Whether to suggest fault injection scenarios during outline generation |
| Collaborative Lab Scenarios | Yes / No / AI-recommended | Whether to suggest ILT collaborative scenarios (cyber range, assembly line) |
| Simulated Attack Scenarios | Yes / No / AI-recommended | Whether to suggest simulated attack scenarios for cybersecurity products |

**4. Environment & Delivery Defaults** *(PS / Technical lead)*
The technical defaults that shape BOM generation and environment template recommendations. Typically set during PS onboarding and rarely changed.

| Setting | Options | Purpose |
|---|---|---|
| Default Delivery Path | Hyper-V / Azure Cloud Slice / AWS / Docker / Custom API | Environment baseline for BOM and template recommendations |
| Default VM OS | Windows Server 2022 / Windows 11 / Ubuntu 22.04 / RHEL 9 / Other | Pre-fills VM config in BOM; reduces manual entry for the lab developer |
| Scoring Approach | REST API / PowerShell·Bash / AI Vision / MCQ / Mixed | Informs Phase 3 scoring recommendations — generates guidance aligned to this approach |

**5. Brand & Identity** *(Program owner / Marketing)*
Applied to all exports and program artifacts.

| Setting | Purpose |
|---|---|
| Logo upload | Applied to export packages and program artifacts |
| Brand URL | Source for brand color and font extraction |
| Brand colors + fonts | Applied to generated content for visual consistency |

**6. Reference Materials** *(Anyone)*
Always-on context the AI uses in every generation call across all phases. The more complete these are, the more product-specific and accurate the AI's output.

| Setting | Purpose |
|---|---|
| Documentation Site URL | Primary product documentation — highest AI context value |
| Knowledge Base URL | Support knowledge base, FAQs, troubleshooting guides |
| Reference file uploads | Job task analysis, existing course outlines, internal standards docs |

---

## Relationship to the Intelligence Platform

Designer is downstream of Inspector in the primary handoff chain. It does not re-run research or re-score products — it consumes the Intelligence signals that Inspector already produced and translates them into program design decisions.

The three qualification gates inform Designer throughout:
- **Gate 1** determines environment architecture, delivery path, and provisioning pattern — surfaced in Preferences defaults and BOM
- **Gate 2** determines program scope, lab complexity, scenario types, and seat time — high complexity generates multi-series curricula; low complexity generates focused single-series programs
- **Gate 3** determines how prescriptive Designer's scaffolding needs to be — a mature content team needs a framework; an early-stage team benefits from more detailed scaffolding and may need Skillable PS support

Lab scenario type flags from Inspector (break/fix, simulated attack, collaborative lab — parallel/adversarial or sequential/assembly line) carry into Designer's Phase 2 outline recommendations. A cybersecurity product with Red/Blue Team signals gets a program architecture that includes both self-paced guided labs and an ILT cyber range track. A data pipeline product with multi-role handoff signals gets assembly line collaborative lab scenarios alongside role-specific tracks.

Designer program records link back to their source Inspector analysis via `inspector_analysis_id`. If the Inspector analysis is updated after a Designer program is created, the program displays a "⚠ Source analysis updated" badge.

---

*Phase 4 BOM categories, Studio export format details, and full activity validation guidance will be expanded after the Designer requirements document is complete.*
