# Designer Foundation Session — Preparation Document

This document is the pre-read for the Designer strategic foundation session. It captures Designer's current state, identifies what has already been decided, surfaces conflicts with the Platform Foundation, and structures the questions that need answers.

Read this document fully before starting the session. Read Designer-Session-Guide.md for the methodology.

This document reflects best current thinking. As thinking evolves, this document evolves with it — fully synthesized, never appended.

---

## Section 1: Current State Assessment

### What Designer Does Today

Designer is a lab program design tool that guides users from goals and audience through a complete program architecture, draft instructions, and a Skillable Studio export package. It lives in the Intelligence Platform because every phase depends on deep product knowledge.

The Platform Foundation describes an 8-phase pipeline:

| Phase | What it does | Current implementation status |
|---|---|---|
| **1. Intake** | Collects objectives, products, audience, business goals, job task analyses | Implemented — AI conversation + checklist in right pane |
| **2. Program outline** | Recommends lab series — names, descriptions, count | Implemented — AI generates JSON outline |
| **3. Lab breakdown** | Recommends individual labs per series | Implemented — part of Phase 2 outline generation |
| **4. Activity design** | Recommends 2-8 activities per lab, in sequence | Implemented — part of Phase 2 outline generation |
| **5. Scoring recommendations** | Recommends how to score each activity | Implemented — embedded in Phase 3 draft instructions |
| **6. Draft instructions** | Generates lab instructions per lab | Implemented — Phase 3 parallel generation |
| **7. Bill of materials** | Complete environment spec | Stub only — designer_engine.py is a placeholder |
| **8. Export package** | Lab series, profiles, instructions, scripts — zipped for Studio | Not implemented |

The pre-Foundation requirements document describes a 4-phase model (not 8) that consolidates the pipeline:

| Phase | Name | What it covers |
|---|---|---|
| **Phase 1** | Requirements & Intent | Lab Blueprint checklist, AI conversation, document upload |
| **Phase 2** | Program Architecture | Outline generation, series/labs/activities, skill mapping |
| **Phase 3** | Draft Instructions & Scoring Recommendations | Parallel draft generation, editable instructions |
| **Phase 4** | Package & Export | BOM generation, Studio export ZIP |

**Key observation:** The 8-phase pipeline in Platform-Foundation.md is a logical breakdown. The 4-phase UX model is the user-facing breakdown. These are not in conflict — Phases 2-4 of the logical model (outline, labs, activities) are all executed within Phase 2 of the UX model. Phase 5 (scoring) is embedded in Phase 3. Phases 7-8 map to Phase 4. The mapping is now documented in the "Phase Structure and Transitions" section above.

### Current UX Layout and Flow

The current designer.html implements a three-pane layout:

**Left pane — Sidebar (280px, dark green #0A3E28):**
- Skillable logo (120px wide, left-aligned)
- "LAB PROGRAM DESIGNER" label (11.5px uppercase, muted)
- Program name (17px, bold white, click-to-edit)
- Phase navigation with numbered rounded-square icons
- Bottom: "All Programs" and "Preferences" ghost buttons
- Footer: copyright link

**Main content — Two-pane split:**
- Middle pane (flex, light background): Chat area in Phase 1, outline in Phase 2-3
- Right pane (fixed 420px, white): Checklist in Phase 1, AI conversation in Phase 2, draft instructions in Phase 3

**Phase 1 specific:**
- Middle pane: chat conversation with AI (bubbles, typing indicator)
- Chat input: textarea with file attachment popup (supports file upload, URL input)
- Right pane: Lab Blueprint checklist with 6 items (program_objectives, target_audience, primary_product, difficulty_seat_time, success_criteria, skill_framework)
- Generate Outline button at bottom of checklist with readiness status messages

**Preferences:**
- Full takeover layout — replaces both middle and right panes
- Left nav (220px) with five groups, right panel (max 640px) scrollable
- Five groups: AI Connection, Organization Identity, Style Guides & Standards, Skill Frameworks, Lab Defaults

### Current Backend Architecture

**designer_routes.py** — Flask Blueprint with routes:
- `GET /designer/` — program list (designer_home.html)
- `GET /designer/new` — creates new program, redirects
- `GET /designer/<program_id>` — loads program into designer.html
- `POST /designer/<program_id>/save` — merge-save program state
- `POST /designer/<program_id>/delete` — delete program
- `POST /designer/<program_id>/chat` — SSE streaming chat with phase-specific system prompts
- `GET/POST /designer/<program_id>/checklist` — read/update checklist
- `GET /designer/<program_id>/vocabulary` — VocabularyPack loading states
- `POST /designer/<program_id>/product-intel` — lightweight product intelligence lookup
- `POST /designer/<program_id>/outline` — save outline

**Phase-specific system prompts (PHASE_PROMPTS):**
- Phase 1: Detailed persona instructions — warm but not eager, max 3 sentences, one question per turn, checklist JSON updates appended
- Phase 2: Outline generation — "Neo" reference, JSON outline format
- Phase 3: Draft instructions — Markdown format, scoring recommendations per activity

**designer_engine.py** — Stub file. No implementation. Contains SA Build Notes (detailed Skillable platform knowledge for Hyper-V, Docker, Azure Cloud Slice, AWS Cloud Slice) and Inspector-to-Designer handoff specification. All four phase sections are TODO.

**Data model (_default_program):**
- program_id, program_name, company_name, current_phase
- checklist (6 items with state/items/value)
- outline (series array)
- phase1/2/3_messages
- draft_instructions
- preferences (counts, defaults, toggles, export format)

### Decisions Already Made About Designer

From reference_designer_decisions.md, the decision log, and the pre-Foundation requirements document.

#### Phase Structure and Transitions

4 UX phases, mapping to the 8-phase logical pipeline in Platform-Foundation.md:

| UX Phase | Name | Logical Phases Covered |
|---|---|---|
| **Phase 1** | Requirements & Intent | 1. Intake |
| **Phase 2** | Program Architecture | 2. Program Outline, 3. Lab Breakdown, 4. Activity Design |
| **Phase 3** | Draft Instructions & Scoring Recommendations | 5. Scoring Recommendations, 6. Draft Instructions |
| **Phase 4** | Package & Export | 7. Bill of Materials, 8. Export Package |

Phase transition buttons: Generate Outline (1->2), Generate Draft Instructions (2->3), Generate Lab Package (3->4), Export Lab Package (4->done), Build Another Program (done->new).

Phase fluidity: no hard walls between phases. Users move freely. The Phase 2 AI conversation handles Phase 1 refinements directly without requiring navigation back.

#### AI Persona

No confirmed name. Four character references define personality: R2D2 (technically brilliant), Jeeves (anticipates needs), Sergeant Hulka (decisive, organized), Neo (cool under pressure). "Neo" is a tone reference, not a name — remove "You are Neo" from Phase 2 prompt.

The AI speaks first always. When seeded from Inspector, it opens by naming what it knows and stating an assumption. When cold-starting, it opens with a short direct question. The tone is confident, measured, present — a trusted advisor who earns trust by knowing things, not performing eagerness.

#### Phase 1 — Requirements & Intent (Detailed Spec)

**Three-pane layout:** Left = navigation + Preferences access. Middle = content upload, URL input, AI conversation. Right = Lab Blueprint checklist (live progress tracker and thought provoker).

**Content input — zero friction:** Drag-and-drop files (PDF, DOCX, PPTX, XLSX, CSV), URL input (any web page, Google Docs/Sheets parsed as documents), direct text input, image upload (whiteboards, napkin drawings, network diagrams). For every upload, the AI immediately shows a card: what it extracted, which checklist items it updated, and a clarifying question.

**The Lab Blueprint checklist tracks seven requirements:**

1. Program Objectives — business outcome + hands-on skill outcomes
2. Target Audience — role, experience level, technical background
3. Primary Product(s) & Topic(s) — software/platform/subject
4. Difficulty & Duration — difficulty level + target seat time per lab (defaults from Preferences)
5. Success Criteria — completion rate, cert pass rate, demonstrated performance
6. Scenario Seeds — real-world situations labs should simulate
7. Skill Framework & Competency Mapping — optional, appears lower in checklist, AI surfaces conversationally at the right moment

**Checklist item states:** Gray (nothing captured), yellow (partially filled — AI found or inferred something, confidence still building), green (confirmed — enough to proceed). Progression is continuous, not a single pass. Every upload, question, and URL processed adds context. Items shift in real time.

**In-place checklist editing:** Click any value, type correction, click away or Enter to save. Edits update AI context immediately.

**Generate Outline readiness progression:**

| Checklist state | Status message | Button |
|---|---|---|
| Early — major gaps | "I need more to work with." | Disabled |
| Building — some gaps remain | "More context sharpens this." | Disabled |
| Sufficient — usable but improvable | "I can build something. More context improves it." | **Active** |
| Strong — ready | "Ready when you are." | **Active** |

Button becomes active at the "sufficient" stage. Permanent note below: "You can return to refine this anytime."

**Intelligence informs but never restricts direction.** Even when seeded from Inspector, the actual subject is confirmed through Phase 1 conversation. A Tanium customer might build networking fundamentals. The AI follows the program owner's direction completely.

**When the program owner is stuck, the AI suggests** — based on product modules/workflows, complexity signals, common patterns for the product category, or natural prerequisite topics. Suggestions are starting points the owner can take, modify, or reject.

**The checklist is a thought provoker, not just a progress tracker.** Each item signals a dimension of program design that matters — many of which first-time program owners have never considered. Items carry enough context to explain why they matter.

**Code conflict:** Code has 6 checklist items (Scenario Seeds removed). Docs say 7. Scenario Seeds should be re-added per spec.

#### Phase 2 — Program Architecture (Detailed Spec)

**Three-pane layout:** Left = navigation. Middle = outline (fully live-editable inline). Right = AI conversation driving outline changes.

Middle and right panes work together: direct inline editing in middle (rename, reorder, add/delete) OR AI-directed structural changes in right ("merge labs 4 and 5," "make this two series"). Both change the same outline. A "Refactor Outline" button triggers significant AI restructuring.

**Outline structure:** Series > Labs > Activities. Labs are 45-75 minutes, 3-8 activities each. Activities are discrete tasks — the unit of progress tracking and scoring. Activities are not optional. Well-formed names and short descriptions at every level.

**Default expand/collapse on arrival:** Single series = open showing all labs, activities collapsed. Multiple series = first expanded, others collapsed. Expand All / Collapse All controls available.

**Edit retention on Phase 1 return:** If user navigates back to Phase 1 and makes changes, outline regenerates on return to Phase 2. AI-aware regeneration passes the current edited outline as a scaffold the AI must respect, alongside updated Phase 1 context. User's structural choices (renamed labs, added activities, reordered items) are preserved. No versioning, no merge UI, no lock icons.

**Skill Mapping Mode — a distinct focus within Phase 2:**

- Outlining and skill mapping run in parallel, not in strict sequence. While the outline is being built, the AI quietly proposes skill tags in the background.
- The outline stays clean — mapping doesn't clutter the outlining experience. Progress visible in checklist: "Skill Mapping — 14 of 22 activities tagged."
- User can flip into Skill Mapping Mode at any point to review AI proposals. Proposed mappings are waiting — not starting from scratch.
- Review is structured for an instructional designer: full framework visible alongside outline, mappings editable individually, ability to approve the complete map as a whole.
- **Skill mapping review prompt on outline approval:** If framework is configured and AI has proposed tags but user hasn't opened Skill Mapping Mode, clicking to approve triggers: "The AI has proposed skill tags for 22 activities — want to review them before moving to Phase 3?" Not a blocker — a reminder. Suppressed if user has opened the mode even briefly.
- **Tagging granularity:** Activity-level is the recommendation, not the rule. Some frameworks or content teams need lab-level tagging. Designer recommends activity-level but doesn't enforce.
- **Multiple frameworks simultaneously:** A program can map to more than one framework at once (e.g., NICE and DCWF in parallel). AI handles dual-framework mapping automatically.
- **Gap detection both directions:** Activities that map to no framework skill (scope gaps) and framework skills with no activity coverage (curriculum gaps). Surfaces as reviewable findings without forcing changes.
- **Governance split:** Executives/program owners own the decision (which framework, whether mapping is required). Instructional designers own the approach (which activity maps to which skill, how to handle gaps). AI bridges both.
- Mappings travel with the program — stored on program record, included in Phase 3 context, exported in Phase 4 package.

#### Phase 3 — Draft Instructions & Scoring Recommendations (Detailed Spec)

**Three-pane layout:** Left = navigation. Middle = outline (same series/lab structure as Phase 2, click a lab to load instructions). Right = draft instructions for selected lab, rendered at actual Skillable Studio instruction width.

**Parallel progressive generation:** All lab generation calls kick off in parallel when user clicks Generate Draft Instructions. Phase 3 opens immediately. Labs populate as they complete. Typical: 15-30 seconds for a full program.

**Pulsing dot while generating:** Small pulsing dot (Skillable green) appears left of lab name in outline. Lab name muted and not clickable until done. When ready, dot resolves and name becomes fully active.

**First lab auto-selects** — its draft instructions appear in right pane automatically. User is already reading before clicking anything. Can then click any ready lab in any order.

**Middle pane outline editing:** Click any lab or series name to edit in place. Drag handle on left of each lab row for reorder within a series.

**Right pane — fully editable:** Click anywhere and type. No edit mode toggle, no separate form. Edits auto-saved.

**Three draft reminders:**
1. Persistent pill above right pane instructions: "Draft - Finalized in Skillable Studio" (muted, always visible)
2. AI's opening message when Phase 3 loads: acknowledges what it built and where work goes next
3. Brief note at Phase 4 export moment before package downloads

**Phase 3 output is draft scaffolding** — not finished content. A head start for the SME or tech writer doing final authoring in Skillable Studio.

**Open question:** Phase 3 AI conversation capability (refinement) vs. direct-edit only — TBD.

#### Phase 4 — Package & Export (Detailed Spec)

Phase 4 is a review-and-export experience — not a design or conversation experience. The hard work is done.

**Three-pane layout:** Left = navigation. Middle = program summary + environment template BOMs (one per template, collapsible if multiple). Right = export actions and status.

**BOM is AI-generated** from full program context: every lab, activity, scoring recommendation, and delivery path decision from Phases 1-3, combined with Skillable platform documentation (provisioning patterns, lifecycle actions, credential pools, cloud slice config, OVA import, scripting conventions). Goal is an enormous head start, not perfection.

**BOM categories per environment template:**

| Category | Contents |
|---|---|
| **Cloud Slice / API Package** *(listed first — all other decisions depend on this)* | Subscription type (Azure/AWS/Custom), API endpoints, auth mechanism, OAuth scopes, permissions, provisioning sequence, pre-instancing, ownership model |
| Virtual Machines | OS, version, CPU/RAM, disk, snapshot strategy |
| Containers & IDEs | Container images, IDE config, port mappings |
| Software & Tools | Applications, versions, licenses, installation order, config notes |
| Accounts & Credentials | User/service accounts, credential pool setup, permissions |
| Data & Files | Dummy data files, placement paths, seeding scripts |
| Networking & Permissions | VNet/subnet, firewall, DNS, inter-VM connectivity, collaborative lab network |
| **Lifecycle Action (LCA) Scripts** *(Lab Profile > Lifecycle Actions in Studio)* | Environment automation — startup, teardown, reset, fault injection. Run without learner interaction. |
| **Scoring Scripts** *(attached to Activities in Studio)* | Per-activity validation scripts. Stubs from Phase 3 scoring recommendations. Pass threshold and scoring format (ABA/PBT/Activity Group) per activity. |
| Studio Configuration | Variables, replacement tokens, credential pool IDs, subscription pool IDs, collaborative lab settings |

**LCAs vs. Scoring Scripts distinction:** Both are PowerShell/Bash scripts but serve entirely different purposes and live in different places in Studio. LCAs automate the environment (Lab Profile). Scoring Scripts validate learner work (Activities). This distinction is critical for lab developers.

**Environment templates — one per VM/cloud configuration type:** A single program can span multiple templates. Single template = flat comprehensive list. Multiple templates = each collapsible independently.

**Program summary panel (above BOM):** Total series / labs / activities, skill framework coverage summary, delivery path confirmed, environment template count and names, export readiness status.

**Cloud Slice ownership question:** Prompted before BOM generation: "Will you use Skillable-managed or customer-provided subscriptions?" Affects BOM, lifecycle scripts, and Studio configuration. The one design decision that cannot be resolved before Phase 4.

**Loading language:** BOM generation is the heaviest AI lift. Loading states use invented words from the VocabularyPack — a deliberate UX decision, not placeholders.

**Export package (ZIP):** data.json (imports into Studio creating series, profiles, instructions, activities), bom.pdf (or structured format TBD), generated script files organized by environment template, skill mapping export at activity level.

**Phase 4 actions:** Export Lab Package (downloads ZIP), Build Another Program (returns to fresh Phase 1).

**Delivery path respect:** Designer builds for the confirmed delivery path. If recommended path differs from customer preference, Designer proceeds with customer's choice and surfaces a clear, non-intrusive note about the alternative. Designer is an advisor, not a gatekeeper.

**Export format pending SE validation.** Exact data.json structure, BOM document format, and script packaging conventions need validation with SEs before Phase 4 build.

#### Preferences (Detailed Spec)

**Two-level hierarchy:** Global defaults (organization level, apply to every new program) + per-program overrides (override any global default for a specific program without changing the global standard).

**Setup vs. Preferences distinction:** System Setup (AI provider, API key, model config) is Admin-configured once during onboarding, lives in separate Admin section. Preferences (program standards) are used regularly, organized into five groups.

**First-run onboarding:** AI connection configured by Skillable before customer logs in. First thing new user sees is Preferences guided setup — walk-through of five groups establishing the organization's content DNA. If Inspector analysis exists, Preferences can be pre-populated with smart defaults.

**The five preference groups:**

**1. Content Standards** (Program owner) — structural and naming defaults:
- Target Lab Duration (15-30 / 30-45 / **45-75** / 75-90 / 90-120 / 120+ min)
- Activities per Lab (1-2 / **3-5** / 6-10 / Unlimited)
- Default Difficulty (Beginner / **Intermediate** / Advanced / Expert)
- Lab Naming Formula (text field with variables)
- Activity Naming Convention (text field with variables)
- Lab Series Naming Convention (text field)
- Lab Pass Threshold (% of activities required)

**2. Learning Design Standards** (ID / Program owner) — pedagogical defaults:
- Writing Style Guide (Microsoft / Google / Apple / Red Hat / Custom URL)
- Certification Alignment (free text / None)
- Default Skill Framework(s) (picklist + custom upload)
- Hint Usage Policy (Always / On request / Never)
- Knowledge Block Usage (Yes / No)
- SME Handoff Format (Inline AI comments / Clean draft only)

**3. Scenario & Lab Type Defaults** (PS / Program owner) — advanced scenario types:
- Break/Fix Scenarios (Yes / No / AI-recommended)
- Collaborative Lab Scenarios (Yes / No / AI-recommended)
- Simulated Attack Scenarios (Yes / No / AI-recommended)

**4. Brand & Identity** (Program owner / Marketing):
- Logo upload, Brand URL, Brand colors + fonts

**5. Reference Materials** (Anyone) — always-on AI context:
- Documentation Site URL, Knowledge Base URL, Reference file uploads

**Environment and software do not belong in Preferences.** Delivery path, VM configuration, software requirements, and scoring approach are program-specific decisions that emerge from the design process and are captured in the Phase 4 BOM.

**Conflict note:** reference_designer_decisions.md lists 5 groups (Organization Identity, Learning Design Standards, Scenario & Lab Type Defaults, Environment & Delivery Defaults, Contacts & Roles). The detailed spec above lists 5 different groups (Content Standards, Learning Design Standards, Scenario & Lab Type Defaults, Brand & Identity, Reference Materials). The Foundation session needs to reconcile and lock the definitive 5.

**Skill framework catalog detail:** Curated catalog grouped by domain (Cybersecurity, Cloud & DevOps, Networking, Software Engineering, IT Operations, Data & AI, Cross-Domain). Includes public frameworks and vendor certification catalogs (Microsoft, CompTIA, AWS, Cisco). Custom uploads (JSON, CSV, plain text) appear under "Your Frameworks." LinkedIn Skill Framework included for HR/L&D teams with LinkedIn Learning-anchored strategies. Soft skills and power skills frameworks explicitly excluded — only hands-on technical skills that map to keyboard-level tasks. Certification frameworks use hyper-simplified UX: user picks the cert name, AI maps to domain objectives behind the scenes.

#### VocabularyPack

When Designer starts a new program, Intelligence generates a VocabularyPack for the customer — approximately 60% Skillable domain vocabulary blended with 40% of the company's specific product and domain language from Intelligence.

**Contents:**
- **Manufactured Words** — invented portmanteaus, gerunds, suffixes blending Skillable and product vocabulary (not real words). Appear in program name suggestions and personality moments.
- **Program Name Seeds** — 4-6 program name concepts using manufactured vocabulary and real product terms.
- **Lab Series Labels** — 4-6 series naming patterns the program owner can adopt or adapt.
- **Skill Level Labels** — replaces generic Beginner/Intermediate/Advanced with invented alternatives (e.g., "Pre-Skillified / Getting Skillified / Fully Skillified"; a security product might produce "Threat-Curious / Actively Securifying / Fully Threat-Hardened").
- **Action Verb Palette** — strong domain-specific verbs for titles drawn from what the product actually does.
- **Loading States** — the most visible expression in the UI. Instead of "Thinking...", Designer shows randomly selected invented gerunds from the pack.

Generated once at program creation, saved with the program, consistent throughout the design session.

**Open question for Foundation session:** The loading language is charming internally. Is it appropriate for the customer-facing version?

#### Intelligence Flow Into Designer

Intelligence is the fuel that powers everything Designer produces — not a starting point it builds from. Without Intelligence, Designer produces generic scaffolding. With it, Designer produces architecture specific to this product, this audience, and this delivery path.

The three Pillars inform Designer throughout:
- **Product Labability** — determines environment architecture, delivery path, provisioning pattern. Surfaces in Preferences defaults and BOM.
- **Instructional Value** — determines program scope, lab complexity, scenario types, seat time. High complexity generates multi-series curricula; low complexity generates focused single-series programs.
- **Customer Fit** — determines how prescriptive Designer's scaffolding needs to be. Mature teams get a framework; early-stage teams get detailed guidance.

Lab scenario type flags from Inspector (break/fix, simulated attack, collaborative lab patterns) carry into Phase 2 outline recommendations.

Designer program records link back to source Inspector analysis via inspector_analysis_id. If the analysis is updated after a program is created, a "Source analysis updated" indicator appears.

**General principles:** Designer is self-service by design — no Skillable involvement required. Phase 3 output is draft scaffolding. Activities are first-class. Topic emerges in Phase 1 even when seeded. Organizational readiness calibrates scaffolding prescriptiveness. The parallel workstream insight (program design and environment build happen simultaneously) is the critical design rationale.

### What the Instructional Design Guide Covers

`backend/prompts/instructional_design_guide.md` is a 10-part reference:

1. **Philosophy** — Labs vs tutorials distinction. Labs require judgment, decision-making, skill. If a learner can complete it by following instructions without engaging judgment, it's a tutorial.
2. **Learning Objectives** — Apply/Analyze level or above (Bloom's). Map objectives to activities, not labs. Right-size scope to one job task domain.
3. **Scenario Design** — Job task is the scenario. Scenarios have context (who, what happened, what's needed). Scenario bank of 3-5 per program.
4. **Lab Series Architecture** — Three-tier model: Foundation (Tier 1, guided), Role-Specific (Tier 2, moderate scaffolding), Advanced/Cert Prep (Tier 3, low scaffolding). Scaffolding decreases within each series. Role-based tracks for multi-role products.
5. **Individual Lab Design** — Seat time guidance (30-120 min by type). Activities are discrete scoreable actions. Starting state is a design decision. "What if they fail" design question.
6. **Assessment Design** — ABA for learning labs (per-activity feedback, retry). PBT for validation/certification (no interim feedback, scored after submission). Scoring surface mapping by product type. Activity Group Scoring for certification.
7. **Break/Fix Lab Design** — Broken starting state, diagnostic phase, resolution phase, validation phase. Fault injection categories. Single fault per lab except advanced.
8. **Collaborative Lab Design** — ILT only. Two patterns: Parallel/Adversarial (Cyber Range) and Sequential/Assembly Line. Never substitute for self-paced.
9. **Program Sizing** — Starter (4-8 hours, 6-10 labs) through Enterprise (40-80 hours, 50-100 labs). First program recommendation: single Foundation Series.
10. **Quality Standards** — Four learner success statements. Anti-pattern catalog (click-through wizards, objectives met by watching, 15+ activity labs, etc.).

**Key observation:** This guide is comprehensive but not yet injected into Designer's Phase 1/2/3 system prompts. The CLAUDE.md notes this as a next step. The Foundation session should decide how and when this guide informs the AI's behavior — it should not be dumped wholesale into prompts; it should be selectively injected based on phase and context.

### What's Working Well

- The three-pane layout is clean and functional
- Phase 1 AI conversation with progressive checklist is a strong interaction pattern
- The concept of parallel outline generation in Phase 2 is sound
- The instructional design guide is thorough and well-structured
- The skill mapping design (AI proposes, human validates) is well thought out
- The SA Build Notes in designer_engine.py are exactly the platform knowledge Designer needs
- The VocabularyPack / AI Processing Messages concept adds personality without compromising function
- Product intelligence lookup (product-intel route) enables Designer to pull Inspector data without exposing company intelligence

### What Conflicts with Foundation Decisions

| Area | Current Designer State | Foundation Decision | Conflict |
|---|---|---|---|
| **Checklist items** | Code has 6 items (Scenario Seeds removed) | Spec says 7 items including Scenario Seeds | Scenario Seeds should be re-added per spec |
| **Phase prompt — "Neo" name** | Phase 2 prompt starts with "You are Neo" | AI persona has no confirmed name; "Neo" is a tone reference only | Remove "Neo" as a name from the Phase 2 prompt |
| **Pillar vocabulary** | designer_engine.py references "Gate scores" and "labability_score.total" | Foundation uses Pillar/Dimension vocabulary, not Gates | Needs vocabulary alignment |
| **Pipeline naming** | Foundation doc uses 8-phase pipeline; UX uses 4-phase model | Both are valid — mapping now documented in Decisions Already Made section | Resolved in this document |
| **Preferences groups** | reference_designer_decisions.md lists 5 groups; detailed spec lists 5 different groups | The two lists don't match exactly | Need to reconcile and lock the definitive 5 |
| **User bubble color** | designer.html uses `#00D082` gradient for user chat bubbles | Brand palette has `#24ED98` as accent green | Should use brand palette color |
| **Data domain enforcement** | product-intel route queries Inspector analysis cache | Foundation says "no path from Designer to company intelligence data" | Need to verify product-intel doesn't leak company intelligence fields |

---

## Section 2: People — Who Uses Designer?

### Personas from the Foundation Doc

| Persona | Role | Phase engagement | Current in Designer? |
|---|---|---|---|
| **Program Owners** | Strategy — goals, audience, scope, program decisions | Primary Phase 1-2 user; reviews Phase 3-4 | Yes — primary audience |
| **Instructional Designers** | Learning experience — sequencing, objectives, assessment, skill mapping | Phases 1-3: contribute JTA, audience defs, competency frameworks in P1; refine outline in P2; review drafts + scoring in P3 | Yes |
| **SMEs (Subject Matter Experts)** | Product accuracy — realistic workflows, technical validation | Phases 2-3: validate lab scenarios and activities in P2; review and tech-edit draft instructions in P3 | Yes |
| **Tech Writers** | Lab content — instructions, steps, guidance | Phase 3 consumers | Implied |
| **Product Engineers** | Technical feasibility — what can be done, how it works | Not addressed | Not addressed |
| **Skillable Learning Consultants / Professional Services** | All of the above, on behalf of customers. Arrive with Inspector analysis, deep product knowledge, platform expertise | All phases — use Designer to accelerate scoping engagements | Yes — primary internal user |
| **Contracted Lab Developers** | Downstream consumers — build from Designer's output in Studio. Import package, receive BOM and scripts, begin technical build | Not a Designer user — consumer of Phase 4 output | Consumer only |

### Questions to Explore

**For each persona:**
- What does their workflow look like end to end? Where does Designer fit in their day?
- What's their technical skill level? How much do they know about Skillable Studio, lab design, instructional design?
- What information do they need at each phase? What would overwhelm them?
- What's a win for them — what output from Designer makes them say "this saved me a week"?

**Customer-facing future:**
- How does the customer-facing version of Designer change the persona mix? Program owners at customer organizations are the primary audience — but they know less about Skillable than internal ProServ users.
- What should a first-time customer program owner see vs. what an experienced ProServ consultant sees?
- Should scaffolding prescriptiveness adapt based on user experience level? (The Foundation doc hints at this: "an early-stage team gets more detailed guidance; a mature team gets a framework.")
- How does onboarding work for a customer's first time in Designer?

**ProServ vs Customer differences:**
- ProServ arrives with an Inspector analysis, deep product knowledge, and Skillable platform expertise. They use Designer to structure and accelerate what they'd otherwise do manually.
- Customers arrive with business goals and product knowledge but often no mental model for lab program design. They use Designer to learn what a program is while building one.
- Is the difference handled entirely by the AI's adaptive scaffolding, or do the two audiences need different UX paths?

---

## Section 3: Purpose — Why Does Designer Exist?

### Current Purpose Statement

Designer exists to solve the adoption problem: customers who don't know how to design a lab program won't build one. Without a guided design process, the default pattern is predictable — everyone waits for the technical team to get software working in the platform, timelines compress, energy dissipates, and a few labs get built to justify the contract without the structure that makes scoring, progression, or growth possible.

The parallel workstream insight is that program design and environment build are independent workstreams that should happen simultaneously. While the technical team gets software working in Skillable, the program owner and ID can be in Designer defining objectives, building the outline, and approving program structure. When the environment is ready, the program design is already done.

Designer also builds discipline — making good decisions the default. The checklist surfaces what's missing. The outline enforces the series-lab-activity hierarchy that makes scoring possible. Draft instructions include guidance on validating each activity. The BOM surfaces platform features at exactly the moment they're relevant. A content team that goes through Designer once comes out with a better mental model for labs.

### Questions to Explore

- Is the adoption problem statement still the right framing after the Foundation session? The Foundation established that the product is the center of everything. Does Designer's purpose need to be reframed around products rather than programs?
- What's the relationship between Designer and the three customer motivations (product adoption, skill development, compliance/risk)? Does the motivation shape what Designer recommends?
- What was the process before Designer? What specific steps took hours that Designer should make take minutes?
- For ProServ: How does Designer change a scoping engagement? What do they walk into a customer conversation with that they didn't have before?
- What's the one thing Designer does that no other tool, competitor, or manual process can do?
- How does Designer connect to Inspector's intelligence? The Foundation says "Green signals become program design inputs; badges not shown." What does that mean concretely for each phase?
- How does Designer connect to Prospector? (Currently: it doesn't. Should it?)

---

## Section 4: Principles — What Should Guide Designer?

### GP1: Right Information, Right Time, Right Person, Right Context, Right Way

**Applied to Designer:**
- Different personas at different phases need different information. A program owner in Phase 1 needs business goal alignment. An SME in Phase 2 needs technical accuracy validation. A lab developer receiving the Phase 4 export needs build specifications.
- Progressive disclosure within each phase — the checklist shows what matters now, not everything.
- The customer-facing version must hide Skillable-internal context (company intelligence, competitive signals) while still leveraging product intelligence.

**Questions:**
- How does GP1 apply to the Phase 1 AI conversation? What does the AI surface vs. hold back?
- How does the checklist's three-state progression (gray/yellow/green) embody GP1?
- When the same tool serves both internal ProServ and external customers, how does "Right Person" work?

### GP2: Why, What, How

**Applied to Designer:**
- Phase 1 is Why (why this program, why this audience, why these goals)
- Phase 2 is What (what labs, what activities, what structure)
- Phases 3-4 are How (how to teach it, how to build it)

**Questions:**
- Does the current Phase 1 conversation lead with Why strongly enough?
- Should the Phase 2 outline communicate Why for each series and lab (not just What)?
- How does the BOM connect Why to How — does it explain why specific environment choices were made?

### GP3: Explainably Trustworthy

**Applied to Designer:**
- Every program recommendation should be traceable to evidence. When Designer recommends a break/fix lab, the user should be able to understand why.
- The checklist is a transparency mechanism — it shows the AI's confidence and basis.
- Draft instructions should reflect the scoring surface mapping — if an activity can't be scored by scripts, the scoring recommendation should say so and explain the alternative.

**Questions:**
- How does Designer make its recommendations explainable? Inspector has badge evidence on hover. What's Designer's equivalent?
- When the AI recommends a program structure, can the user ask "why this structure?" and get a meaningful answer?
- Should the instructional design guide be linkable from Designer's UX (the same way the Badging and Scoring Reference is linkable from Inspector)?

### GP4: Self-Evident Design

**Applied to Designer:**
- Variable names in the data model should reflect the concepts (they largely do: program_objectives, target_audience, etc.)
- Phase names should be self-evident to non-Skillable users
- The outline structure (Series > Labs > Activities) should be immediately clear to someone who has never used Skillable Studio

**Questions:**
- Are the current phase names (Collaborate & Design, Generate Outline, Draft Instructions, Package & Export) self-evident to a customer program owner?
- Does the data model need restructuring to align with the Foundation's vocabulary?

### GP5: Intelligence Compounds

**Applied to Designer:**
- Every program designed in Designer enriches the platform's understanding of what works for specific product types
- A program designed for a Trellix product should inform recommendations for the next cybersecurity program
- Preferences represent organizational learning that compounds across programs

**Questions:**
- How does intelligence flow back from Designer into the platform? Currently it flows in (from Inspector) but not out.
- Should Designer programs be searchable/referenceable — "show me programs designed for products like this one"?
- How do Preferences compound over time — does the AI learn what this organization prefers?

### End-to-End Principle

**Applied to Designer:**
- The same Pillar/Dimension/Requirement structure that drives Inspector scoring should inform Designer recommendations. Product Labability dimensions tell Designer what delivery path to use. Instructional Value dimensions tell Designer what lab types to recommend. Customer Fit dimensions tell Designer how prescriptive to be.
- The same intelligence that produces badges in Inspector should produce program recommendations in Designer — same source, different presentation.

**Questions:**
- How exactly does each Pillar feed into Designer's recommendations? This needs to be specified at the dimension level.
- Is there a formal mapping: "Provisioning dimension -> BOM delivery path section," "Lab Versatility dimension -> Phase 2 scenario type suggestions"?

### Define-Once Principle

**Applied to Designer:**
- Lab type names (Break/Fix, Simulated Attack, etc.) should come from the same canonical list used in Inspector's Lab Versatility badges
- Skill framework names should be defined once and referenced in Preferences and Phase 2
- Delivery pattern names should match between Inspector badges and Designer BOM

**Questions:**
- Where do Designer's canonical lists currently live? Are they defined once or duplicated?
- How does Designer's vocabulary stay in sync with Inspector's vocabulary as the platform evolves?

---

## Section 5: The 8-Phase Pipeline — Deep Dive

### Phase 1 — Intake / Requirements & Intent

**Current input:** AI conversation, document upload, URL input, checklist
**Current output:** Populated Lab Blueprint with program_objectives, target_audience, primary_product, difficulty_seat_time, success_criteria, skill_framework (and Scenario Seeds when re-added)

**Questions:**
- How does the instructional design guide's philosophy section ("what makes a lab a lab") inform Phase 1? Should the AI actively steer program owners away from tutorial-style programs?
- How should the AI handle a program owner who doesn't know what they want? The guide says "when the program owner is stuck, the AI suggests" — but what's the boundary between suggesting and leading?
- How do the three customer motivations (product adoption, skill development, compliance) shape Phase 1 questions and recommendations?
- Should Phase 1 capture delivery context (ILT vs self-paced vs blended)? This affects Phase 2 activity design significantly (collaborative labs are ILT-only).
- How does document quality assessment work? The Phase 1 prompt says to call out thin documents — but what's the standard for "thin"?

### Phase 2 — Program Architecture (Outline + Labs + Activities)

**Current input:** Phase 1 checklist, AI conversation
**Current output:** Outline JSON with series, labs (titles, seat times), activities (titles, skill tags)

**Questions:**
- How does the instructional design guide's three-tier model (Foundation, Role-Specific, Advanced) map to Phase 2 series generation? Should the AI explicitly recommend a tier structure?
- How should scaffolding progression (decreasing guidance lab-by-lab within a series) be represented in the outline?
- How do Lab Versatility signals from Inspector feed into Phase 2? If Inspector identified "Break/Fix" and "Incident Response" as lab versatility badges, how do those become specific labs in the outline?
- How does the BOM connect to Phase 2? The Foundation says "The BOM is generated after all labs are designed — which makes it dramatically more complete." But some BOM decisions (delivery path, VM count) affect activity design. Is there a feedback loop?
- Activity design standards from the guide (discrete, scoreable, not steps within an action) — how are these enforced or encouraged by the AI during outline generation?
- Role-based tracks: when a product has multiple distinct user roles, should Phase 2 automatically generate separate tracks? How does this interact with the program owner's intent?

### Phase 3 — Draft Instructions & Scoring Recommendations

**Current input:** Approved outline, Phase 1 context
**Current output:** Markdown draft instructions per lab with scoring recommendation blocks

**Questions:**
- How does the instructional design guide's assessment design section inform Phase 3? The guide distinguishes ABA (learning labs) vs PBT (certification labs) — should Phase 3 instructions differ based on which assessment approach the program uses?
- How does the scoring surface mapping (from the guide) get injected into Phase 3? If the product is GUI-heavy with no CLI/API, the scoring recommendations should recommend AI Vision — not PowerShell scripts.
- The Phase 3 prompt currently says to format instructions in Markdown with scoring recommendations. Should it also generate hints and knowledge blocks (per the instructional design guide) based on Preferences settings?
- How should style guides affect Phase 3 generation? The prompt mentions it but the injection mechanism isn't specified.
- Should Phase 3 have AI conversation capability (for refinement) or is it direct-edit only? reference_designer_decisions.md flags this as TBD.

### Phase 4 — Package & Export (BOM + Studio Export)

**Current input:** All prior phases, delivery path, cloud ownership decision
**Current output:** ZIP with data.json, bom.pdf, generated scripts, skill mapping export

**Questions:**
- The BOM specification is extremely detailed (Cloud Slice packages, PowerShell scripts, Bicep templates, CloudFormation templates, LCA scripts, scoring scripts, credential pool config — see Phase 4 Detailed Spec above). How much of this can the AI realistically generate? What's the quality bar — accurate stubs or production-ready scripts?
- How does the SA Build Notes content from designer_engine.py get injected into Phase 4? These notes are critical for accurate BOM generation.
- What's the Studio import format? The legacy Designer export code is noted as the current best reference. Has this been located and analyzed?
- Environment templates — one per VM/cloud configuration type. How does the AI determine how many templates a program needs? What signals from Phases 1-2 inform this?
- The data.json format needs SE validation before Phase 4 is built. Is this validation a prerequisite for the Foundation session, or can the Foundation session define what the format should contain and leave the exact structure for later?

---

## Section 6: UX — What Should Designer Look Like?

### Current UX Issues and Opportunities

**Layout:**
- The three-pane layout works but the middle/right pane split swaps purpose between phases (middle = chat in Phase 1, middle = outline in Phase 2-3). Is this intuitive or confusing?
- The right pane is fixed at 420px. Is this the right size for all phases? Phase 3 right pane shows draft instructions at "actual Skillable Studio instruction width" — is 420px that width?
- designer.html is a single monolithic file with all CSS inline. As the Foundation session adds complexity, should this be refactored?

**Progressive disclosure:**
- The checklist's gray/yellow/green progression is a good start. How does progressive disclosure work in Phase 2 (the outline)? In Phase 4 (the BOM)?
- Should completed phases show a summary rather than the full interface when revisited?

**Navigation:**
- Phase fluidity ("no hard walls") means users can move between phases freely. How does the UI communicate where the user is and what's available?
- The sidebar phase nav has progress dots (hollow, partial, complete). Are these sufficient to communicate phase state?

### Customer-Facing Version

- The Foundation says Designer will eventually be a standalone application with its own authentication. How should the customer-facing UX differ from the internal version?
- Customers should never see company intelligence. The product-intel route currently queries Inspector analysis cache — does it filter out company intelligence fields?
- Should the customer version have a simpler Preferences experience? Customers don't need AI Connection setup (Skillable configures it).
- How does branding work? Can customers apply their own brand to Designer's output?

### Export Formats and Studio Integration

- The data.json import format is unvalidated
- Should Designer also export a Word document (program design document) for stakeholder review?
- Should Designer export to other formats (PDF summary, slide deck)?
- How does the skill mapping export format work — is there a standard?

---

## Section 7: Data Architecture

### How Designer Consumes Product Intelligence Without Exposing Company Intelligence

The Foundation defines three data domains:

| Domain | What it contains | Designer access |
|---|---|---|
| **Product data** | What products are, how they work, labability assessments | Open — Designer should use this freely |
| **Program data** | Lab series, outlines, activities, instructions | Scoped — Designer creates and owns this |
| **Company intelligence** | Fit scores, badges, buying signals, contacts, ACV | Internal-only — Designer must never access |

**Current implementation:**
- The product-intel route queries Inspector analysis cache and returns delivery method and labability score. It does not return company intelligence fields (fit scores, badges, ACV, contacts).
- When seeded from Inspector, Designer loads: company_name, company_description, organization_type, top_products (with labability scores), orchestration_method, fabric, consumption_potential, contacts.

**Questions:**
- The seeding data includes contacts (decision makers and influencers). Are contacts "company intelligence" or "product data"? The Foundation says contacts are internal-only, but the pre-Foundation spec says contacts are loaded for "stakeholder context."
- consumption_potential is derived from ACV calculation — is this company intelligence?
- How does tenant awareness work for customer programs? When a customer uses Designer, they should see only their own programs — not other customers' programs or Skillable's internal programs.
- Should Designer have its own data store separate from Inspector's analysis cache, or does it read from the shared Intelligence layer?

---

## Section 8: Open Questions

### From the Decision Log and Memory Files

| Question | Source | Status |
|---|---|---|
| Export ZIP format — exact structure and validation with SEs | reference_designer_decisions.md | Unresolved |
| AI persona name — "Neo" not confirmed, no name confirmed | reference_designer_decisions.md | Unresolved — decide: named or unnamed? |
| Inspector-to-Designer handoff pre-fill level — how much data flows over | reference_designer_decisions.md | Partially specified in designer_engine.py |
| Standards Library API route | reference_designer_decisions.md | Not implemented |
| Phase 3 AI conversation — refinement capability or direct-edit only | reference_designer_decisions.md | TBD |
| Scenario Seeds — removed from code, specified in docs | Code vs docs conflict | Needs decision |
| Instructional design guide injection into Phase 1/2/3 prompts | CLAUDE.md next steps | Not implemented |
| CSS color correction to confirmed brand palette | CLAUDE.md next steps | Partially done — user bubble gradient still uses #00D082 |
| Skill framework taxonomy files | reference_designer_decisions.md | backend/standards/skill_frameworks/ is empty |
| Phase 4 BOM generation quality bar | Pre-Foundation spec | Not specified — stubs vs production-ready |
| Cloud Slice ownership question timing | Pre-Foundation spec | Phase 4 only, but affects BOM significantly |

### New Questions Raised by Foundation Decisions

| Question | Why it matters |
|---|---|
| How do the three Pillars map to Designer's four phases? | The Foundation established Product Labability (40%), Instructional Value (30%), Customer Fit (30%). Each Pillar contains intelligence that Designer should use. The mapping needs to be explicit. |
| Should Designer have its own scoring/assessment model? | Inspector has the Fit Score. Prospector has the qualifying score. Should Designer have a "program readiness" score or a "program quality" score? |
| How does the 70/30 product-vs-organization split affect Designer? | 70% of intelligence is about the product. Designer is product-focused. But Customer Fit (30%) shapes scaffolding prescriptiveness and ProServ opportunity identification. |
| How does the variable-driven approach apply to Designer? | The Foundation says everything should be variable-driven — organization type, motivation, product category all shape output. How do these variables shape Designer's recommendations? |
| How does Conversational Competence apply to Designer? | Inspector builds conversational competence for sellers. Does Designer build conversational competence for program owners? If so, in what direction? |
| How does the verdict grid connect to Designer? | A "Prime Target" verdict in Inspector means something for a seller. What does it mean for a program designer? |
| How does the Seller Briefcase connect to Designer? | The briefcase has "Key Technical Questions" (Product Labability), "Conversation Starters" (Instructional Value), "Account Intelligence" (Customer Fit). Should Designer have its own equivalent — a "Builder Briefcase"? |
| How do confidence levels (confirmed/indicated/inferred) apply to Designer? | Inspector badges carry confidence levels. When Designer makes a recommendation based on Inspector data, should it communicate confidence? |
| How does the 12-item Lab Versatility menu flow into Designer? | Inspector identifies 1-2 lab versatility badges per product. How do these become specific labs, activities, and scenarios in Designer? |
| What happens when Designer is used without Inspector? | Cold start — no intelligence, no product data. How much can Designer deliver on its own? What's the quality difference? |
| Multi-product programs — how does Designer handle programs that span multiple products? | A customer may want a program that covers Product A and Product B. Each product has its own labability assessment, delivery path, and scoring surface. |
| How does Designer handle non-software programs? | The Foundation says labs for leadership, compliance reading, or soft skills have nothing to provision. But a customer using Designer might want to build those. Does Designer refuse, redirect, or accommodate? |
| How does the loading language ("Skillifying, smartating") work in the customer-facing version? | These are charming internally. Are they appropriate for a customer-facing tool? |

---

## Session Agenda — Suggested Sequence

Based on the Designer-Session-Guide.md methodology:

**Phase 1: People (est. 45-60 min)**
- Review each Designer persona from the Foundation doc
- Define customer persona profiles (new to labs, experienced, ProServ-assisted)
- Establish the adaptive scaffolding model (who gets what level of guidance)
- Decide on internal vs customer UX differences

**Phase 2: Purpose (est. 30 min)**
- Validate or reframe the adoption problem statement
- Clarify how Designer connects to each customer motivation
- Define the parallel workstream value proposition for customers vs ProServ
- Establish what Designer uniquely delivers that no other tool provides

**Phase 3: Principles (est. 45 min)**
- Apply GP1-GP5 to Designer specifically (one principle at a time)
- Define any Designer-specific principles
- Resolve the data domain boundary questions (what's product data vs company intelligence in Designer's context)
- Establish the explainability model for Designer recommendations

**Phase 4: Rubrics (est. 90-120 min)**
- Walk through each of the 4 UX phases (8 logical phases)
- For each: define inputs, outputs, intelligence requirements, human checkpoints
- Decide on the instructional design guide injection strategy
- Resolve the Lab Versatility-to-program-design flow
- Define the BOM specification and quality bar
- Lock the Preferences groups and settings

**Phase 5: UX (est. 60-90 min)**
- Review the current three-pane layout against Foundation decisions
- Iterate on Phase 1 (checklist, conversation, upload)
- Iterate on Phase 2 (outline, skill mapping, conversation)
- Iterate on Phase 3 (draft instructions, scoring recommendations)
- Iterate on Phase 4 (BOM, export, review)
- Decide customer-facing UX differences
- Name everything — pages, sections, buttons, states

**Total estimated time: 4.5-6 hours** (comparable to the Foundation session)
