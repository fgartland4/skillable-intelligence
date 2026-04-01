# Skillable Intelligence — Designer

> Designer guides program owners, instructional designers, and subject matter experts through the full process of designing a lab program — from goals and audience through a complete, approved outline, draft instructions, and a Skillable Studio-ready export package.
>
> Designer's AI conversations, recommendations, program structure, and Bill of Materials are all fueled by the deep product and company understanding stored in Intelligence. Without Intelligence, Designer produces generic scaffolding. With it, Designer produces program architecture specific to this product, this audience, and this delivery path — before the program owner has made a single decision.
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

### Designer Is Self-Service by Design

Designer does not depend on Skillable. Any customer — regardless of whether they have an active PS engagement or LC support — can open Designer and produce a meaningful program architecture independently. The tool guides the process. No Skillable involvement is required.

Skillable Learning Consultants and Professional Services are avid Designer users, and they use it to do better work faster. But their involvement is always additive — never a prerequisite. A program owner at a new customer account should be able to complete all four phases, export a Studio package, and hand it to a contracted SME without ever speaking to a Skillable employee.

### Intelligence Flowing Into Phase 1

When a program is seeded from an Inspector analysis, Intelligence doesn't just pre-fill fields — it actively shapes the AI's recommendations throughout Phase 1 and into Phase 2. What Inspector knows about the customer's products is present from the first interaction:

- Gate 2 complexity signals inform program scope recommendations — a deeply complex product with high module count and strong interoperability generates multi-series curriculum suggestions before the program owner has said anything
- Gate 1 delivery path feeds Preferences defaults and BOM recommendations
- Scenario type flags (break/fix, simulated attack, collaborative lab) surface in scenario seed suggestions and Phase 2 outline generation
- Gate 3 organizational readiness signals calibrate how prescriptive the scaffolding is — an early-stage team gets more detailed guidance; a mature team gets a framework

The program owner doesn't need to re-explain the product. Designer already knows it.

### Seeding from Inspector

The primary entry point is `GET /designer?analysis_id={inspector_analysis_id}`. Designer loads company name, scored products, delivery path recommendation, Gate scores, consumption estimates, scenario type flags, and key contacts from the Inspector analysis. Phase 1 fields pre-fill automatically. The user reviews and confirms before the AI asks follow-up questions.

Designer also accepts manual entry when no Inspector analysis exists — the program owner describes the product, audience, and goals, and Designer works from that context alone.

### Phase 1 — Requirements & Intent

**Three-pane layout:**
- **Left pane** — navigation and Preferences access
- **Middle pane** — primary work area: content upload, URL input, and AI conversation
- **Right pane** — Lab Blueprint checklist: live progress tracker and thought provoker

The middle pane accepts content in as many ways as possible — the goal is zero friction for whatever the program owner has available:
- Drag and drop files (job task analysis, existing course outlines, product documentation, audience profiles, any prior training materials)
- URL input (documentation sites, knowledge bases, existing course pages)
- Direct text input
- Image upload — including photos of whiteboards, napkin drawings, and network diagrams. If a program owner sketched a curriculum structure on a whiteboard, they should be able to photograph it and upload it directly

The AI reads all uploaded content, extracts relevant signals, and asks follow-up questions to fill gaps. The conversation happens in the middle pane — questions appear inline as the AI processes content and identifies what's missing.

**Phase 1 → Phase 2 transition:**
A "Generate Outline" button lives at the bottom of the right pane checklist — visible once the AI has enough to produce a meaningful program structure. The AI may proactively signal readiness ("I have enough to generate an outline — want to proceed?") but the program owner decides when to commit. Both the AI prompt and the button trigger Phase 2.

**Phase fluidity — no hard walls:**
The program owner can move between phases freely. There is no lock-out. Additionally, the Phase 2 AI conversation (right pane) can handle Phase 1 refinements directly — "we need to refine success criteria" doesn't require returning to Phase 1. The AI should proactively surface gaps it notices: *"Your success criteria are still general — want to refine those before we finalize the outline?"*

**The Lab Blueprint checklist tracks nine requirements:**
1. Business / Learning Objectives — what the program needs to achieve
2. Target Audience(s) — roles, experience levels, prerequisites
3. Primary Product / Platform — the product being trained on
4. Recommended Difficulty — Beginner / Intermediate / Advanced / Expert
5. Target Lab Duration — seat time per lab (default 45–75 min; adjustable in Preferences)
6. Success Criteria — how program success will be measured
7. Scenario Seeds — initial ideas for lab scenarios and use cases
8. Skill Framework — optional alignment to a skills or certification framework; AI recommends based on product category
9. Competency Mapping — whether activity-level framework mapping will be applied; set here, executed in Phase 2

Items 1–7 are standard for every program. Items 8 and 9 are optional — they appear lower in the checklist and the AI surfaces them conversationally at the right moment, not at the start. The AI does not wait for the program owner to know that skill frameworks exist: *"This looks like a cybersecurity program — I'd recommend mapping to the NICE Workforce Framework. Want me to do that?"* If the answer is no, the items stay gray and the program proceeds without mapping. If yes, the AI carries the framework selection forward into Phase 2 where the actual mapping work happens.

Each item shows a filled green indicator when confirmed, a gray indicator when empty, and a summary of what's been captured when expanded. The AI prompts for missing items conversationally — it doesn't wait for the user to realize something is missing.

**The topic emerges in Phase 1 — it is not pre-determined.** Even when a program is seeded from an Inspector analysis, the actual subject of the labs is confirmed through the Phase 1 conversation. A customer seeded from a Tanium Inspector analysis might decide their first program is networking fundamentals — a primer for Tanium learners that has nothing to do with Tanium products. Phase 1 is where that gets established.

**Intelligence informs the AI's prompts — it never restricts the direction.** If Inspector knows this is a Tanium customer with endpoint security products, the AI might ask: "Is this program for Tanium product skills, or for foundational skills that support your Tanium curriculum?" But the moment the program owner says "networking fundamentals," the AI follows completely — no steering back, no resistance. Intelligence context makes Phase 1 feel smarter and more relevant. It does not constrain what the program can be about.

**When the program owner is stuck, the AI suggests.** If a program owner doesn't know what topics to cover, what labs to build, or how to structure the curriculum, the AI doesn't wait. It offers suggestions based on what it knows — documented product modules and workflows, Gate 2 complexity signals, common patterns for the product category, or natural prerequisite topics for the product being trained on. The program owner can take any suggestion, modify it, reject it, or use it as a starting point. The AI is a thinking partner, not a passive recorder.

**The checklist is a thought provoker, not just a progress tracker.** Each checklist item signals a dimension of program design that matters for building a strong learning or skill validation program — many of which a first-time program owner may never have considered. Seeing "Competency Framework — not defined" prompts the question: *should I align this to a framework?* Seeing "Scenario Seeds — none yet" prompts: *what real-world situations should these labs simulate?* Each checklist item carries enough context to explain why it matters — not just what it is — so the program owner understands what they're being asked to think about, not just what field to fill in. The checklist is one of the primary ways Designer builds the discipline of thinking well about lab programs.

Phase 1 is complete when the program owner and AI have enough shared understanding of goals, audience, scope, and topic to generate a meaningful program outline.

### Phase 2 — Program Architecture

**Three-pane layout:**
- **Left pane** — navigation
- **Middle pane** — the outline itself, fully live-editable inline
- **Right pane** — AI conversation that drives outline changes

The middle and right panes work together: the program owner edits the outline directly in the middle (rename a lab, reorder activities, add or delete items inline) OR directs the AI in the right pane to make structural changes ("merge labs 4 and 5," "make this two series," "suggest more activities for this section"). Both inputs change the same outline. A "Refactor Outline" button in the right pane triggers a more significant AI restructuring when the program owner wants the AI to re-examine the overall structure rather than make targeted edits.

Once Phase 1 is approved, the AI generates a complete program outline structured as:

**Series → Labs → Activities**

- **Series** are the top-level groupings (e.g., Administration Fundamentals, Advanced Configuration, Troubleshooting)
- **Labs** are the individual practice units within each series — 45–75 minutes, three to eight activities each
- **Activities** are the discrete tasks within each lab — the unit of progress tracking and scoring in Skillable Studio

The outline includes well-formed names and short descriptions at every level. Scenario type recommendations (break/fix, simulated attack, collaborative lab) appear where Inspector signals or program context supports them.

Every level of the outline is expandable and collapsible. The program owner refines through conversation: "merge labs 4 and 5," "make this two series instead of three," "I only have budget for 12 labs — which ones should I keep?" The AI responds with a revised outline. This continues until the outline is approved.

**Activities are not optional.** They are how Skillable tracks learner progress and the only level at which scoring is possible. Designer treats activity design as a first-class part of program architecture — not an afterthought for the lab developer.

Once the outline is approved, it's saved. Collaborators (SMEs, IDs, additional program owners) can review and engage with the AI to evolve the framework before moving to Phase 3.

**Skill Mapping Mode — a distinct focus within Phase 2:**

Outlining and skill mapping are separate modes of focus. When designing the program, skill mapping stays in the background. When the outline is ready, the program owner or ID shifts into Skill Mapping Mode — the outline is still visible for reference, but the focus moves to framework alignment.

If a skill framework was selected in Phase 1, the AI enters Skill Mapping Mode automatically after outline approval. It proposes activity-level mappings for every activity in the approved outline — *"Configure Network Policies → NICE Work Role: Cyber Defense Analyst (KS0001, KS0002)"* — and presents them for review. The program owner or ID reviews, confirms, or adjusts. This is not a quick confirm dialog. The review is structured and designed for an instructional designer: full framework visible alongside the outline, mappings editable individually, and the ability to approve the complete map as a whole before it's locked.

**Multiple frameworks simultaneously.** A program can be mapped to more than one framework at the same time. A cybersecurity program will commonly run NICE and DCWF in parallel — the work roles overlap, so the same activity maps to both. The AI handles dual-framework mapping automatically; the ID reviews both mappings in the same review step.

**Gap detection.** Once mapping is complete, the AI checks coverage in both directions: activities that map to no framework skill (potential scope gaps), and framework skills with no activity coverage (curriculum gaps). It surfaces both as reviewable findings — *"No activities cover Incident Response (NICE PR-IR) — want to add a lab or activity?"* — without forcing any changes.

**Skill mapping is always optional and always AI-led.** The AI does most of the work. The ID validates and governs. Organizations that don't want mapping skip it entirely with no friction. Organizations that need rigorous framework alignment — government contractors, EC-Council, organizations with custom consulting-built frameworks — get a structured, complete mapping process that would otherwise require weeks of manual work.

**Governance split — executives own the decision, instructional designers own the approach.** Whether to use a skill framework, which framework(s) to align to, and whether mapping is required for program completion — those are executive or program owner decisions. They reflect organizational strategy: compliance obligations, certification goals, workforce development commitments. How the mapping is actually done — which activity maps to which skill, how to handle gaps, how to handle overlapping frameworks — that is the instructional designer's domain. Designer is built around this split: the program owner makes the framework selection in Preferences and Phase 1; the ID does the review, adjustment, and approval work in Skill Mapping Mode. The AI bridges both by proposing mappings that the ID can accept or change without requiring the program owner to understand the mechanics.

**The mapping travels with the program.** Framework selections and activity-level mappings are stored on the program record, included in Phase 3 draft instruction context, and exported in the Phase 4 Studio package.

### Phase 3 — Draft Instructions & Scoring Recommendations

**Three-pane layout — the panes flip from Phase 2:**
- **Left pane** — navigation
- **Middle pane** — AI conversation: generating and refining draft instructions lab by lab
- **Right pane** — learner preview: live rendering of draft instructions at Skillable Studio width

When the outline is approved, the UI shifts: the right pane narrows to approximately the width of actual Skillable Studio lab instructions. This previews what learners will see.

For each lab, the AI generates:
- Draft lab instructions organized by activity
- Recommendations for how each activity should be validated — the logic and approach for scoring, surfaced as guidance for the lab developer who will configure validation in Studio

The program owner or ID reviews each lab's draft with the AI — refining language, adjusting task descriptions, clarifying validation approaches. SMEs can be brought in at this stage to tech-edit for accuracy.

Phase 3 output is draft scaffolding — not finished content. The draft instructions are a head start for the SME or tech writer who will do final authoring in Skillable Studio.

### Phase 4 — Package & Export

Phase 4 is a review-and-export experience — not a design or conversation experience. The hard work is done. Phase 4 assembles everything into a complete, exportable package and gives the program owner a final review before it goes to the lab developer.

**Three-pane layout:**
- **Left pane** — navigation
- **Middle pane** — program summary and environment template BOMs (one per template, collapsible if multiple)
- **Right pane** — export actions and status

**What the AI generates in Phase 4:**

The BOM is not a blank checklist the program owner fills in — it is AI-generated from the full context of the program: every lab, every activity, every scoring recommendation, every delivery path decision made in Phases 1–3, combined with Skillable platform documentation covering provisioning patterns, lifecycle action structures, credential pool setup, cloud slice configuration, OVA import process, and scripting conventions.

The goal of the generated BOM is not perfection — it is an enormous head start. Lab developers adjust a few variables rather than starting from scratch.

Generated artifacts included in the BOM and export package:
- **PowerShell and Bash scripts** — environment setup, teardown, and reset automation based on the delivery path and software requirements
- **Bicep templates** (Azure Cloud Slice programs) — resource group definitions, role assignments, service configurations
- **CloudFormation templates** (AWS Cloud Slice programs) — stack definitions for the specific services the program uses
- **Lifecycle Action (LCA) scripts** — startup, teardown, and scoring automation; break/fix fault injection scripts where applicable
- **Credential pool configuration** — connection string format, reset procedure, pool size guidance
- **Scoring validation stubs** — starting points for the validation scripts the lab developer will configure in Studio, based on Phase 3 scoring recommendations

None of these are expected to be production-ready out of the box. They are authoritative starting points — structured, specific, and informed by everything Designer knows about the program.

**Cloud Slice ownership question:**
If the program uses Cloud Slice, Phase 4 prompts before generating the BOM: *"Will you use Skillable-managed cloud subscriptions or customer-provided subscriptions?"* The answer affects the BOM, the lifecycle scripts, and the Studio configuration. This is the one design decision that cannot be resolved before Phase 4.

**Environment templates — one per VM/cloud configuration type:**

A single lab program can span multiple environment templates — a 50-lab program across three series might use three or four distinct environment templates (different VM configurations, different cloud resource sets, different software stacks). Each environment template gets its own BOM section.

- **Single template** — displayed as a flat, comprehensive list
- **Multiple templates** — each template is collapsible; the program owner can expand or collapse independently

Each BOM section is comprehensive. Everything the lab developer needs to build and configure the environment:

| Category | Contents |
|---|---|
| Cloud & Subscriptions | Subscription type, resource groups, IAM roles, supported services, ownership (Skillable vs. customer) |
| Virtual Machines | OS, version, CPU/RAM, disk size, snapshot strategy |
| Containers & IDEs | Container images, IDE configuration, port mappings |
| Software & Tools | Applications, versions, licenses, installation order, configuration notes |
| Accounts & Credentials | User accounts, service accounts, credential pool setup, permission assignments |
| Data & Files | Dummy data files (CRM records, log files, datasets), placement paths, seeding scripts |
| Networking & Permissions | VNet/subnet config, firewall rules, DNS, inter-VM connectivity, collaborative lab network setup |
| Lifecycle Scripts | Startup, teardown, reset, fault injection (break/fix), generated script files attached |
| Scoring & Assessment | Validation approach per activity, scoring script stubs, pass threshold, Studio configuration notes |
| Studio Configuration | Variables, replacement tokens, credential pool IDs, subscription pool IDs, collaborative lab settings |

**Program summary panel:**

Above the BOM, Phase 4 shows the complete program at a glance:
- Total series / Total labs / Total activities
- Skill framework mappings (if applicable) — frameworks selected, coverage summary
- Delivery path confirmed
- Environment templates: count and names
- Export readiness status

**Loading language:**
BOM generation is the heaviest AI lift in Designer. The loading state uses Designer's signature invented words — *Skillifying... smartating... intelligentifing... job-ready-makin'...* — the same personality established throughout the tool. These are not placeholders; they are a deliberate UX decision.

**The Skillable Studio Export Package:**

A downloadable ZIP containing:
- `data.json` — imports directly into Skillable Studio, creating all lab series, lab profiles, draft instructions, and activities
- `bom.pdf` (or structured format TBD) — the complete Bill of Materials for the lab developer
- Generated script files — all PowerShell, Bash, Bicep, and CloudFormation files, organized by environment template
- Skill mapping export — framework mappings at the activity level, in a format suitable for import or reference

The contracted SME or lab developer imports the Studio package, receives the BOM and generated scripts, and begins the technical build. The structural and environmental scaffolding is done. Their job is to make it work — not figure out what to build or how to start.

> **Export format — pending SE validation.** The exact structure of `data.json`, the BOM document format, and the script packaging conventions are to be validated with Skillable Solution Engineers before Phase 4 is built. The legacy Designer export code is the current best reference and is likely close to the correct format. A separate **Designer Export Specification** document will capture the draft format for SE review.

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
The defaults that shape every program Designer generates. Organized into five groups, each with a distinct owner and purpose. This is where the first-run onboarding guided setup focuses.

### First-Run Onboarding

When a new customer account is provisioned, the AI connection is configured by Skillable before the customer logs in. The first thing a new user sees is the Preferences guided setup — a walk-through of the five groups that explains why each section matters and establishes the organization's content DNA before any program is started.

If the customer has an Inspector analysis, Preferences can be pre-populated with smart defaults — a cybersecurity product triggers break/fix and collaborative lab recommendations; a networking product triggers Hyper-V default and multi-VM environment suggestions. The PS team or LC confirms before handing off to the program owner.

### The Five Preference Groups

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
| Default Skill Framework(s) | Picklist + custom upload | Organization-wide default framework(s); every new program inherits these unless overridden |
| Hint Usage Policy | Always / On request / Never | Whether draft instructions include hint structures for learners |
| Knowledge Block Usage | Yes / No | Whether draft instructions use knowledge blocks for background context |
| SME Handoff Format | Inline AI comments / Clean draft only | Whether draft instructions include AI guidance notes for the SME |

**Skill framework selection — how it works in Preferences:**

The Default Skill Framework(s) picker presents a curated catalog grouped by domain — Cybersecurity, Cloud & DevOps, Networking, Software Engineering, IT Operations, Data & AI, Cross-Domain. Organizations select one or more frameworks as their organization-wide default. Every new program inherits these defaults; program owners can override for a specific program without changing the global standard.

The catalog includes public frameworks (NICE NCWF, DoD DCWF, LinkedIn Skill Framework, CompTIA certification domains, AWS/Azure certification frameworks, SFIA, Cisco CCNA/CCNP/CCIE, ITIL 4, and others) and supports custom framework uploads in JSON, CSV, or plain text format. Custom frameworks — consulting-built company frameworks, vendor-proprietary frameworks like Microsoft's internal skill model — appear at the top of the picker under "Your Frameworks."

**LinkedIn Skill Framework.** LinkedIn's skill taxonomy is a large, flat framework covering thousands of skills grouped into domains. It is widely used by HR and L&D teams because LinkedIn Learning content is already tagged to it — making it easy to connect lab programs to broader L&D catalogs. For customers whose learning strategy is LinkedIn Learning-anchored, Designer can map activities to LinkedIn skill tags, enabling direct linkage between lab completion and LinkedIn Learning skill credits.

**Soft skills and power skills frameworks are explicitly excluded.** The catalog contains only frameworks relevant to hands-on technical skills — the kind that map to keyboard-level tasks in a lab environment. Frameworks built around communication, leadership, or behavioral competencies have no meaningful relationship to lab activities and are not included.

**Certification frameworks are included and treated as skill frameworks.** Certifications are built from job task analysis — the resulting skill domains are a structured competency framework. CompTIA Security+, AWS Solutions Architect, Cisco CCNA, and similar certifications belong in the catalog. A customer building labs to prepare learners for a certification exam is doing skill framework mapping whether they call it that or not.

**Per-program override.** Program owners can select a different framework — or add a second framework — for any specific program without changing the organization default. Multiple frameworks can be active simultaneously on the same program. The instructional design team creates the mapping rules and governs approval; the program owner selects the framework; the AI does the mapping work.

**3. Scenario & Lab Type Defaults** *(PS / Program owner)*
Controls which advanced scenario types Designer recommends during outline generation. Can be pre-populated from Inspector signals.

| Setting | Options | Purpose |
|---|---|---|
| Break/Fix Scenarios | Yes / No / AI-recommended | Whether to suggest fault injection scenarios during outline generation |
| Collaborative Lab Scenarios | Yes / No / AI-recommended | Whether to suggest ILT collaborative scenarios (cyber range, assembly line) |
| Simulated Attack Scenarios | Yes / No / AI-recommended | Whether to suggest simulated attack scenarios for cybersecurity products |

**4. Brand & Identity** *(Program owner / Marketing)*
Applied to all exports and program artifacts.

| Setting | Purpose |
|---|---|
| Logo upload | Applied to export packages and program artifacts |
| Brand URL | Source for brand color and font extraction |
| Brand colors + fonts | Applied to generated content for visual consistency |

**5. Reference Materials** *(Anyone)*
Always-on context the AI uses in every generation call across all phases. The more complete these are, the more product-specific and accurate the AI's output.

| Setting | Purpose |
|---|---|
| Documentation Site URL | Primary product documentation — highest AI context value |
| Knowledge Base URL | Support knowledge base, FAQs, troubleshooting guides |
| Reference file uploads | Job task analysis, existing course outlines, internal standards docs |

> **Environment and software do not belong in Preferences.** Delivery path, VM configuration, software requirements, and scoring approach are program-specific decisions that emerge from the design process. They cannot be meaningfully defaulted because they depend entirely on what the program is teaching. These decisions are captured in the Phase 4 BOM — after the program is fully designed, which is the only point at which they can be complete and accurate.

---

## Relationship to the Intelligence Platform

Intelligence is not a starting point that Designer builds from. It is the fuel that powers everything Designer produces.

The AI conversations in Designer, the recommendations Designer makes, the program structure it generates, and especially the Bill of Materials — none of these are generic outputs shaped by instructional design principles alone. They are specific, grounded outputs that are only possible because Intelligence knows the product deeply: how it is deployed, who uses it, what the workflows look like, what the delivery path requires, what the organizational context signals, and what a realistic lab program for this product looks like in scope and complexity.

Without Intelligence, Designer produces generic scaffolding. With Intelligence, Designer produces program architecture, draft instructions, and a BOM that reflect this specific product — before the program owner has made a single decision.

**The BOM is the clearest example.** A Bill of Materials is not a template. It is a precise artifact that reflects this product's delivery path, VM topology, provisioning pattern, software requirements, and orchestration constraints. Intelligence holds all of that. Designer synthesizes it into something a lab developer can build from directly. The human's job is to confirm and refine — not to generate the technical specification from scratch.

The same principle applies throughout the design process:
- **Number of labs and series** — derived from Gate 2 complexity signals, not from a default program structure
- **Intended audience** — derived from product user personas and organizational context, not from a generic audience prompt
- **Lab titles and activities** — derived from what the product actually does and how administrators, engineers, and operators interact with it
- **Scenario types** — derived from scenario type flags surfaced by Intelligence (break/fix, simulated attack, collaborative lab patterns)
- **Seat time estimates** — derived from workflow depth and activity count, grounded in the product's actual complexity

The three qualification gates inform Designer throughout:
- **Gate 1** determines environment architecture, delivery path, and provisioning pattern — surfaced in Preferences defaults and BOM
- **Gate 2** determines program scope, lab complexity, scenario types, and seat time — high complexity generates multi-series curricula; low complexity generates focused single-series programs
- **Gate 3** determines how prescriptive Designer's scaffolding needs to be — a mature content team needs a framework; an early-stage team benefits from more detailed scaffolding and may need Skillable PS support

Lab scenario type flags from Inspector (break/fix, simulated attack, collaborative lab — parallel/adversarial or sequential/assembly line) carry into Designer's Phase 2 outline recommendations. A cybersecurity product with Red/Blue Team signals gets a program architecture that includes both self-paced guided labs and an ILT cyber range track. A data pipeline product with multi-role handoff signals gets assembly line collaborative lab scenarios alongside role-specific tracks.

Designer program records link back to their source Inspector analysis via `inspector_analysis_id`. If the Inspector analysis is updated after a Designer program is created, the program displays a "⚠ Source analysis updated" badge — because the foundation the program was built on has changed.

### VocabularyPack — Language That Belongs to This Customer

When Designer starts a new program, Intelligence generates a **VocabularyPack** for the customer. The pack blends approximately 60% Skillable's own domain vocabulary with approximately 40% of the company's specific product and domain language — pulled directly from the product names, categories, deployment models, and domain signals Intelligence has already collected.

The VocabularyPack is used throughout Designer — not just for naming, but for personality. Its contents:

- **Manufactured Words** — invented portmanteaus, gerunds, and suffixes that blend Skillable and product vocabulary. These are intentionally not real words. Examples: *Skillifying*, *Job-Readyifyin'*, *Fortification* (Fortinet + fortification — the double meaning is the point), *CohesiFication*, *TaniumOlogizing*, *The Configuratorinator*. These appear in program name suggestions and wherever Designer wants to inject personality.
- **Program Name Seeds** — 4–6 program name concepts using the manufactured vocabulary and real product terms.
- **Lab Series Labels** — 4–6 series naming patterns the program owner can adopt or adapt.
- **Skill Level Labels** — Designer replaces generic Beginner/Intermediate/Advanced with invented alternatives derived from the pack. A typical default: *Pre-Skillified → Getting Skillified → Fully Skillified*. A security product might produce: *Threat-Curious → Actively Securifying → Fully Threat-Hardened*.
- **Action Verb Palette** — strong domain-specific verbs for lab and activity titles. Drawn from what the product actually does: *Provision*, *Orchestrate*, *Segment*, *Enforce* — or invented: *Skillify*, *Fortinate*, *Cohesify*.
- **Loading States** — the most visible expression of the VocabularyPack in the UI. Instead of "Thinking..." appearing while the AI works, Designer shows a randomly selected invented gerund from the pack. Each one has a recognizable root and an absurd *-ing* form: *Threatologizing...*, *Firewallificating...*, *Data-fabricating...*, *Masterificating...*, *Program-architecturifying...*. The root is the joke setup; the gerund is the punchline.

The VocabularyPack is generated once at program creation and saved with the Designer program. It does not change between phases — the vocabulary is consistent throughout the design session. Program owners will notice that the language feels like their product, not like generic training scaffolding. That is the intent.

---

