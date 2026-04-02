# Skillable Lab Program — Instructional Design Guide

*Internal reference for Skillable Intelligence. Not for external distribution.*
*This guide informs Designer's program recommendations across all phases.*

---

## Philosophy: What Makes a Lab a Lab

A lab is not a tutorial. The distinction matters for every design decision.

A **tutorial** tells the learner what to do, step by step, and success means following instructions correctly. The learner can complete it without understanding what they're doing or why.

A **lab** places the learner in a realistic environment with a goal, and success means achieving that goal through their own judgment, decision-making, and skill. The learner can fail. The failure is informative. Recovery requires understanding.

Every design decision — scenario realism, task density, scaffolding level, assessment approach — should be evaluated against this distinction. If a learner can complete the lab by following instructions without engaging their judgment, it's a tutorial. Redesign it.

**The hands-on advantage is specific:** labs build the confidence that comes from having done the thing under realistic conditions. Not watched it. Not read about it. Done it. Program designs that lose sight of this produce content that could have been a video — and that is a failure.

---

## Part 1 — Learning Objectives

### Write objectives at the Apply/Analyze level or above

Bloom's Taxonomy for hands-on lab objectives:

| Level | Action verbs | Lab-appropriate? |
|---|---|---|
| **Remember** | Define, list, recall | No — a quiz handles this |
| **Understand** | Explain, describe, summarize | No — a short video handles this |
| **Apply** | Configure, deploy, execute, implement | ✓ Core lab target |
| **Analyze** | Diagnose, troubleshoot, compare, differentiate | ✓ Strong lab target |
| **Evaluate** | Assess, justify, recommend, validate | ✓ Advanced lab target |
| **Create** | Design, architect, build from requirements | ✓ Capstone lab target |

**The test:** can the learner satisfy this objective by watching someone else do it? If yes, rewrite the objective. A good lab objective begins with a verb that implies action in the environment: *configure*, *deploy*, *diagnose*, *validate*, *recover*, *migrate*, *implement*.

### Map objectives to activities, not to labs

Each activity in a lab should map to one learning objective. If an activity doesn't map to an objective, either the activity is filler (cut it) or the objective is missing (add it). This mapping is what makes performance-based scoring possible — you can only score what you can articulate.

### Right-size the scope

One lab, one job task domain. A lab that tries to cover Backup Policy Configuration AND Restore Operations AND Replication Setup is actually three labs compressed into one. Learner cognitive load collapses. Break it apart.

---

## Part 2 — Scenario Design

### The job task is the scenario

The best lab scenario is a realistic version of the task the learner will perform on the job. Not a simplified demo. Not an artificial exercise. A scenario that a practitioner would recognize as Tuesday morning.

Good scenario framing sources:
- Job postings and job descriptions for the target role
- Product documentation for administrator/operator workflows
- Common support tickets and incident patterns for this product
- Certification exam domains (they define what practitioners are tested on)

### Scenarios have context

A scenario without context is an instruction set. Effective scenarios include:
- **Who:** "You are the IT administrator responsible for protecting the finance department's data."
- **What happened:** "The backup job for the SQL Server cluster failed overnight."
- **What's needed:** "Restore to the last known-good state and determine why the job failed."

This framing activates prior knowledge, creates urgency, and makes the learning feel consequential — which drives engagement and retention.

### The scenario bank

Every lab program should be built around 3–5 scenarios that span the realistic range of what a practitioner encounters. These scenarios should:
1. Cover different difficulty levels (day-1 onboarding → incident response)
2. Cover different workflow phases (configure → validate → troubleshoot → upgrade)
3. Feel like they could be chapters in a practitioner's workday

---

## Part 3 — Lab Series Architecture

### The three-tier program model

Well-structured lab programs follow a consistent three-tier architecture:

**Tier 1 — Foundation Series (Onboarding & Core Concepts)**
- Target: New users, recently licensed, pre-deployment
- Goal: Confident with the product's core workflows; able to complete a basic implementation
- Labs per series: 4–6
- Seat time per lab: 45–60 min
- Scaffolding: High — guided activities, detailed step framing, knowledge blocks at critical decisions

**Tier 2 — Role-Specific Series (Practitioner Depth)**
- Target: Users who know the product; need depth in their specific domain
- Goal: Independently handle the full job task domain for their role
- Labs per series: 3–5 per role track
- Seat time per lab: 60–90 min
- Scaffolding: Moderate — task framing with less step-by-step guidance; learner makes configuration decisions

**Tier 3 — Advanced / Certification Prep Series**
- Target: Experienced users preparing for certification or advanced deployment
- Goal: Handle complex, multi-system scenarios; pass a cert exam; architect solutions
- Labs per series: 3–4
- Seat time per lab: 75–120 min
- Scaffolding: Low to none — scenario is given, outcome is defined, path is not

### Scaffolding progression within a series

Within each series, scaffolding should decrease lab by lab:
- Lab 1: Worked example — the procedure is shown step-by-step; learner follows
- Lab 2: Partially guided — key decision points flagged; specific steps not provided
- Lab 3+: Unguided — scenario is given; learner owns the path

This mirrors the research on deliberate practice: worked examples are efficient for novices; decreasing guidance forces the retrieval and application that builds durable skill.

### Role-based track design

When a product has multiple distinct user roles (Administrator, Developer, Analyst, Operator), design separate tracks per role rather than a single curriculum that switches between roles. Each track:
- Is cohesive — every lab builds on the previous within the same job domain
- Can be taken independently — no "you must do the Admin track before the Developer track" dependencies
- Has its own scaffold progression from guided to independent

Cross-role capstone labs (where two roles collaborate in a shared environment) are appropriate only in ILT/vILT contexts where learners are present simultaneously.

---

## Part 4 — Individual Lab Design

### Seat time guidance

| Lab type | Target seat time | Typical activity count |
|---|---|---|
| Quick-start / onboarding | 30–45 min | 4–6 activities |
| Standard admin workflow | 60 min | 6–8 activities |
| Complex configuration / deployment | 75–90 min | 7–10 activities |
| Break/fix / troubleshooting | 60–90 min | 5–8 activities (diagnostic steps are activities) |
| Capstone / multi-system | 90–120 min | 8–12 activities |

Keep seat time honest. A "60-minute lab" that consistently takes 90 minutes erodes trust in the program. If a workflow genuinely needs 90 minutes to be realistic, design it as 90 minutes.

### Task density and activity design

**Activities are discrete, scoreable actions** — not steps within an action. The difference:
- ❌ Step: "Click File > New > Backup Policy and name it 'Daily-Finance'"
- ✓ Activity: "Create a backup policy for the Finance file share with daily retention settings"

An activity should:
1. Have a clear, observable outcome (was it done or not?)
2. Require a deliberate decision or action (not just clicking through a wizard)
3. Be independently scoreable (can be validated without knowing the learner's approach)

### Starting state matters

The lab environment's starting state is a design decision, not a default. Good starting states:
- **Partially configured:** "The storage array is connected but the backup agent is not installed. Begin from here."
- **Broken state:** "The replication job is failing with Error 2305. Diagnose and resolve."
- **Realistic baseline:** "You are taking over an environment that a previous admin configured. Review the current backup policy and identify what needs to change."

A blank-slate starting state (fresh install, nothing done) is appropriate only for initial deployment labs. For anything beyond onboarding, learners should arrive in a realistic in-progress environment.

### The "what if they fail" design question

For every activity, ask: what happens if the learner does this wrong? If the answer is "nothing — the lab continues identically," the activity doesn't build real skill. Good lab activities have downstream consequences for mistakes — the next activity is harder, or the system doesn't behave as expected, or a later verification step fails.

This isn't cruelty. It's authenticity. Real environments respond to what you do to them.

---

## Part 5 — Assessment Design

### Performance-Based Testing (PBT) vs. Activity Based Assessment (ABA)

**Use ABA for learning labs:**
- Immediate per-activity feedback: "✓ Backup policy created successfully. The daily retention schedule is correctly configured."
- Learner can retry after failure
- Adaptive branching: correct answer can skip ahead; incorrect can redirect to a remediation resource
- Best for: onboarding, skill-building, practice labs where the goal is learning, not measurement

**Use PBT for validation/certification labs:**
- No interim feedback during the lab
- Learner completes everything, then submits for scoring
- Score is returned after submission — pass/fail or scaled
- Best for: certification exams, skill validation assessments, proctored testing

The choice between ABA and PBT should be explicit in the program design — not left to the lab author. A program designed for certification prep needs PBT. A program designed for onboarding needs ABA.

### Scoring surface mapping

Before designing a lab, identify the available scoring surface for this product:

| Product type | Scoring mechanism | Quality |
|---|---|---|
| VM-installable (Hyper-V/ESX) | PowerShell/Bash scripts against config state | High — precise, binary or percentage scoring |
| Cloud-native (Azure/AWS Cloud Slice) | PowerShell/Python against cloud resource state | High — full resource graph queryable |
| GUI-heavy with no CLI/API | AI Vision — screen evaluation against NL prompt | Moderate — less precise, needs careful prompt design |
| SaaS with API | REST API calls to validate learner state | High if API covers learner-accessible state |
| SaaS shared tenant / no isolation | MCQ knowledge checks only | Low — cannot score actions taken |

Design activities around what CAN be scored. An activity with no scoring path is either a navigation step (not an activity) or a design gap that needs resolution before authoring begins.

### Activity Group Scoring for certification

When a program includes certification-track labs, organize activities into scored groups that map to the certification's job task analysis:

- **Activity Group** = one JTA domain (e.g., "Backup Policy Management")
- **Activities within the group** = the observable tasks in that domain
- **Group result** = pass/fail threshold (e.g., 70% of activities in the group must pass)
- **Overall result** = weighted sum of group scores

This produces a score report that maps back to the JTA, which is what certification bodies need for score validity evidence.

### Scaled scoring for certification programs

If the vendor has an existing certification with a scaled score standard (e.g., 0–1000, passing = 700), design the lab scoring to produce a raw score that maps to that scale. Skillable's scaled scoring supports this. Document the scale in the program design so the lab author builds the rubric correctly.

---

## Part 6 — Break/Fix Lab Design

Break/fix labs are a distinct lab type that deserves explicit design treatment. They are the highest-difficulty format and the highest-value for senior practitioners.

### The anatomy of a break/fix lab

1. **Broken starting state** — the environment is delivered in a failed or degraded condition. The failure must be:
   - Realistic (a failure mode that actually occurs in production)
   - Diagnosable (enough information available in the environment to find the cause)
   - Specific enough to have a clear resolution (not "something is wrong" but a specific fault)

2. **Diagnostic phase** — the learner investigates. No hints. The tools available in the environment should be the same tools they'd use in production: logs, dashboards, CLI, event viewers.

3. **Resolution phase** — the learner fixes the fault. The fix should be specific enough to be scored (a service started, a config value corrected, a connection restored).

4. **Validation phase** — the learner confirms the fix worked. This is an explicit activity, not assumed. "Run the backup job and confirm it completes successfully" is the resolution; "verify the backup completed and the recovery point appears in the catalog" is the validation.

### Fault injection design

Common fault categories for break/fix labs (choose one per lab — not multiple concurrent faults):

- **Configuration fault:** a setting is wrong, missing, or misconfigured
- **Network fault:** a route is missing, a firewall rule is blocking, a DNS record is wrong
- **Service fault:** a required service is stopped or failed
- **Permission fault:** an account lacks a required permission or role
- **Resource fault:** a storage volume is full, a threshold is exceeded, a license is expired
- **Version/compatibility fault:** a mismatch between components

Multiple concurrent faults in a single lab are appropriate only for advanced/expert level labs, and only when learners have already practiced single-fault diagnosis.

---

## Part 7 — Collaborative Lab Design (ILT Only)

Collaborative labs run simultaneously for multiple learners in a shared environment. They are appropriate only for ILT/vILT delivery — not self-paced.

### Two collaborative patterns

**Pattern A — Parallel/Adversarial (Cyber Range)**
- Two teams operate simultaneously in the same network environment
- Red Team attacks; Blue Team defends
- Appropriate for: SOC operations, incident response, penetration testing, threat hunting
- Design note: the "attack" can be scripted (the environment generates attack traffic without a live Red Team) for solo self-paced labs — but the live adversarial version requires concurrent learners

**Pattern B — Sequential/Assembly Line**
- Each learner completes a phase, then the environment state passes to the next
- Developer configures the app → Ops engineer deploys it → Security engineer hardens it
- Appropriate for: DevSecOps pipelines, data engineering handoffs, multi-role deployment workflows
- Design note: this pattern requires explicit handoff state management — what one learner leaves must be what the next learner finds

### ILT-only constraint

Never design a collaborative lab as a substitute for a well-designed self-paced lab. Collaborative labs depend on simultaneous learner presence and a facilitator. Programs that require them for their core learning value are fragile — the value disappears in on-demand delivery. Design self-paced equivalents for every collaborative scenario.

---

## Part 8 — Program Sizing and Scope Estimation

### Program scope signals from product complexity

| Product complexity signal | Program scope implication |
|---|---|
| Deep documentation (10+ admin modules) | Multi-series curriculum; each module = potential series |
| Multiple distinct user roles | Separate role tracks; don't merge personas |
| High interoperability (4+ integrations) | Integration labs as separate series or appendix |
| Existing certification program | Add cert-prep track; use PBT for those labs |
| Break/fix content in product docs | Advanced series anchor; high-value differentiator |
| Cloud-native with full API | High scoring fidelity; full ABA recommended |

### Consumption estimate guidance

| Program tier | Typical total seat hours | Labs in program |
|---|---|---|
| Starter / single-product intro | 4–8 hours | 6–10 labs |
| Mid-depth curriculum | 10–20 hours | 15–25 labs |
| Full certification-level program | 20–40 hours | 25–50 labs |
| Enterprise multi-role curriculum | 40–80 hours | 50–100 labs |

These are gross estimates. The actual scope should be derived from the product's documented workflow depth, not from these defaults.

### Right-sizing the first program

For a customer building their first Skillable lab program, recommend starting with a single Foundation Series (4–6 labs, Tier 1 only). This produces a complete, valuable program quickly, without the scope and authoring burden of a full curriculum. Expansion to Tier 2 and Tier 3 follows after the customer has direct experience with what their learners need.

---

## Part 9 — Skillable Studio Integration Notes

*These technical specifics inform design decisions — not implementation details.*

- **Lab instructions** are written in Skillable Studio Markdown. Headings structure the content; activities are tracked via Studio's activity system, not markdown formatting alone.
- **Hints and knowledge blocks** are available in Studio and should be designed explicitly — not added by lab authors as an afterthought. Identify where learners are most likely to get stuck and place knowledge blocks there.
- **Scoring Bot (Hyper-V only):** a hidden Windows 10 VM that executes PowerShell against other VMs in the lab. Useful for external validation (checking a service on a target VM from an orchestrator VM). Note this in activity design when the scoring point is not the learner's own machine.
- **AI Vision:** uses a natural language prompt to evaluate what is on the learner's screen. Precision is moderate — supplement with MCQ knowledge checks for high-stakes activities.
- **Lab save/resume:** Hyper-V labs save as a snapshot and resume cleanly. Cloud Slice labs stop running services on save. Design activities that are naturally pause-able (not in the middle of a multi-step configuration that requires continuity).

---

## Part 10 — Quality Standards

### The program passes if a learner can say these things after completing it

1. "I could set this up in a real environment." (Foundation Series)
2. "I handled that incident without looking anything up." (Intermediate/Advanced)
3. "I know exactly what I'd do differently next time." (Break/Fix)
4. "I'm confident I'll pass the exam." (Certification Prep)

These are the real success criteria. Design decisions should be evaluated against them.

### Common design failures to avoid

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| **Click-through wizard labs** | No judgment required; no skill built | Design starts from a mid-point; learner must make configuration decisions |
| **Objectives that can be met by watching** | Not hands-on learning | Rewrite to Apply/Analyze level; add a scored validation step |
| **15+ activity labs** | Cognitive overload; seat time > 2 hours | Split into two labs; use a scenario connecting them |
| **Labs with no starting-state context** | Learner doesn't know why they're doing the task | Write a 2–3 sentence scenario framing before the first activity |
| **Activities scored by presence, not correctness** | "Did you create a policy?" vs. "Is the policy correctly configured?" | Score the state, not the action |
| **Generic skill framework mapping** | "Mapped to ITIL" without specific domain/practice | Map to the specific ITIL practice and activity level |
| **Same lab at every tier** | Beginner and Advanced learners get identical tasks, different labels | Each tier needs genuinely different scenarios, scaffolding, and scoring |
