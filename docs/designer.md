# Skillable Intelligence — Designer

> Designer takes a confirmed lab program opportunity and produces a complete draft program architecture — lab titles, learning objectives, activity-level content, environment requirements, and a delivery package ready for SMEs and instructional designers to build from.
>
> For shared research, evidence, and scoring infrastructure, see [intelligence-platform.md](intelligence-platform.md). Designer is typically seeded from an Inspector analysis — see [inspector.md](inspector.md) for the handoff flow.

---

## Why Designer Exists

Designer is the execution contextualization layer of Skillable Intelligence. Where Inspector answers *whether* a lab program is worth building and *what it would cost*, Designer answers *how* to build it — translating Intelligence's qualification signals into a concrete program architecture that a content team can act on.

The three qualification gates don't disappear in Designer — they inform it. Gate 1 determines the delivery path and environment architecture. Gate 2 shapes the program scope, lab complexity, and scenario types. Gate 3 signals whether the customer's team needs prescriptive scaffolding or just a framework to run with. Every design decision Designer makes is traceable back to the Intelligence signals that justified it.

Before Designer, a Learning Consultant or PS team member arriving at a scoping conversation had to reconstruct the technical context from scratch — re-reading Inspector output, translating delivery path recommendations into environment specs, manually drafting lab titles and objectives based on product documentation they may or may not have read. That work was inconsistently done, time-consuming, and often duplicated across similar engagements.

Designer closes that gap. When Inspector analysis completes, a "Design Lab Program →" button carries the full analysis into Designer Phase 1 — company context, scored products, delivery path, consumption estimates, and scenario type flags all pre-filled. What would take hours of scoping prep arrives in seconds, already grounded in the technical reality of what can be built and how.

Designer's output is draft scaffolding — not finished lab content. The program architecture, lab titles, learning objectives, and activity outlines it produces are starting points for SMEs and instructional designers working in Skillable Studio, not a replacement for their expertise. The goal is to give content teams a defensible, intelligence-grounded foundation rather than a blank page.

---

## Who Uses Designer

**Learning Consultants and Professional Services** are Designer's primary users. They use it to accelerate the scoping and program design phase of a new customer engagement — arriving at the first content conversation with a draft program architecture already grounded in the customer's product set, delivery constraints, and organizational readiness signals. Typical trigger: Inspector analysis complete, opportunity qualified, PS engagement beginning.

**Instructional Designers** use Designer to get a structured starting point for lab content development. The activity-level outlines Designer produces give them the right level of scaffolding — enough to understand the program intent and lab scope without over-prescribing the authoring decisions that are rightfully theirs. Typical trigger: program architecture approved, moving into content build.

**Subject Matter Experts (SMEs)** engage with Designer output during content review — validating that the lab scenarios, activities, and objectives reflect accurate and realistic product workflows. Designer's scenario type flags (break/fix, simulated attack, collaborative lab patterns) give SMEs an early signal of which lab types are in scope and what technical complexity to prepare for.

**Program Owners and Customer Stakeholders** use Designer to review and approve the program architecture before build begins. The Phase 2 program structure output — lab titles, sequencing, learning objectives, role-based paths — is the artifact that gets reviewed and signed off before any content development starts.

---

## What Designer Delivers

Designer produces output across four phases. Each phase builds on the last and produces a discrete, reviewable artifact.

**Phase 1 — Requirements & Intent**
Company context, training goals, target audience, success criteria, and delivery constraints. Pre-filled from Inspector when an `analysis_id` is provided. The human reviews and confirms before proceeding.

**Phase 2 — Program Architecture**
AI-generated program structure: recommended lab titles, sequencing, learning objectives, and role-based paths. Reflects Gate 2 complexity signals — a high-complexity product with multiple modules and strong interoperability generates a multi-series curriculum, not a single lab. Includes scenario type recommendations (break/fix, simulated attack, collaborative lab) where research signals support them. The human reviews, edits, and approves before proceeding to content.

**Phase 3 — Lab Content**
Activity-level content for each approved lab: activities, task descriptions, and outcome statements at the right granularity for a content team to build from. Not individual step-by-step instructions — those are authored in Skillable Studio by SMEs and tech writers. The right level is: what the learner does, in what sequence, and what they should be able to demonstrate at the end.

**Phase 4 — Package & Export**
Environment Template (Bill of Materials, launch scripts, dummy data file manifest), delivery path specification, and a Skillable Studio-ready export package. All references to lab authoring tools use "Skillable Studio" — never "LOD."

---

## How Designer Works

*[Full workflow detail pending requirements document. The section below reflects confirmed architecture decisions.]*

**Seeding from Inspector**
The primary entry point is `GET /designer?analysis_id={inspector_analysis_id}`. Designer loads company name, scored products, delivery path recommendation, Gate scores, consumption estimates, scenario type flags, and key contacts from the Inspector analysis. Phase 1 fields pre-fill automatically. The user confirms and proceeds.

Designer also accepts manual entry when no Inspector analysis exists — useful for PS engagements where Inspector hasn't been run or where the customer's product is already known.

**Delivery Path Respect**
Designer builds entirely for the confirmed delivery path. If Hyper-V is recommended but the customer prefers VMware, Designer proceeds with VMware — and surfaces a clear, non-intrusive note: *"Hyper-V delivers equivalent capability at lower cost due to Broadcom's pricing changes. You can switch at any time."* Designer is an advisor, not a gatekeeper.

**Scenario Type Integration**
Scenario type flags from Inspector (break/fix, simulated attack, collaborative lab — parallel/adversarial or sequential/assembly line) carry into Designer's program architecture recommendations. A cybersecurity product with Red/Blue Team signals gets a program architecture that includes both self-paced guided labs and an ILT cyber range track. A data pipeline product with multi-role handoff signals gets an assembly line collaborative lab scenario alongside role-specific tracks.

**Gate 2 → Program Scope**
Designer uses Inspector's Gate 2 complexity map directly. High module count, deep feature depth, and strong interoperability generate multi-series curriculum recommendations. Low complexity generates a focused single-series recommendation. Complexity and program scope are positively correlated — Designer reflects this explicitly rather than defaulting to conservative single-lab recommendations.

**Save / Load / Export**
Program state saves at each phase. A DesignerProgram record stores phase outputs against the Company and InspectorAnalysis records. Export produces a Skillable Studio-ready package. If the source Inspector analysis is updated after a Designer program is created, the program surface a "⚠ Source analysis updated" badge.

---

## Relationship to the Intelligence Platform

Designer is downstream of Inspector in the primary handoff chain. It does not re-run research or re-score products — it consumes the Intelligence signals that Inspector already produced and translates them into program design decisions.

The three qualification gates are present throughout Designer's output, though they manifest differently than in Inspector:
- **Gate 1** determines environment architecture, delivery path, and provisioning pattern
- **Gate 2** determines program scope, lab complexity, scenario types, and seat time
- **Gate 3** determines how prescriptive Designer's scaffolding needs to be — a customer with a mature content team needs a framework; a customer with an early-stage team needs more detailed scaffolding and may benefit from Skillable PS involvement

Designer program records link back to their source Inspector analysis. If no Inspector analysis exists, that provenance is absent — but the Gate signals should still inform every design decision manually entered in Phase 1.

---

*This document is a stub. Full HOW detail — phase UI, save/load behavior, export format, BOM structure, and activity content granularity — will be added after the Designer requirements document is complete.*
