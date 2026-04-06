# Strategic Foundation Session Guide

This document captures how to conduct a strategic foundation session for any Skillable Intelligence tool. It was distilled from the Platform Foundation session (April 4-5, 2026) where Inspector's scoring framework, UX, and the entire platform architecture were rebuilt from scratch. The methodology produced Platform-Foundation.md, Badging-and-Scoring-Reference.md, and the Inspector dossier wireframe in a single extended session.

Use this guide to run the Designer session (and any future tool sessions) with the same rigor and results.

This document reflects best current thinking. As thinking evolves, this document evolves with it — fully synthesized, never appended.

---

## The Methodology: People, Purpose, Principles, Rubrics, UX

Every strategic foundation session follows five phases in strict sequence. Do not skip ahead. Each phase depends on the one before it.

| Phase | Core question | What it produces |
|---|---|---|
| **1. People** | Who uses this tool? What do they need? | Persona definitions, workflow descriptions, skill levels, win conditions |
| **2. Purpose** | Why does this tool exist? What problem does it uniquely solve? | Problem statement, value proposition, what the tool replaces |
| **3. Principles** | What rules govern every decision? | GP1-GP5 applied specifically to this tool, tool-specific design principles |
| **4. Rubrics** | What are the specific frameworks, categories, scoring models, or structures? | Detailed operational definitions — the "what exactly" |
| **5. UX** | What should the user see and experience? | Wireframes, layout decisions, interaction patterns, progressive disclosure design |

### Why This Sequence Matters

Starting with People forces every subsequent decision to be grounded in someone real. Purpose without People produces solutions looking for problems. Principles without Purpose produces rules without context. Rubrics without Principles produces frameworks nobody trusts. UX without Rubrics produces pretty interfaces that don't mean anything.

The Foundation session proved this: starting with "who are the people" immediately surfaced that sellers and SEs have different needs, which led to the 70/30 split, which led to the verdict grid, which led to the briefcase concept, which led to the dossier wireframe. Every decision traced back to a person and their need.

---

## Ground Rules

These rules govern how the session is conducted. They are non-negotiable.

### Go Deep, Not Fast

The goal is never to get through the agenda. The goal is to get every decision right. If a single topic takes two hours because the thinking needs to evolve, that is a successful two hours. Speed produces shallow decisions that have to be re-litigated later. Depth produces decisions that hold.

### Best Current Thinking, Always

Every statement, every document, every decision represents the best understanding at this moment. Nothing is sacred because it was said an hour ago. If new thinking supersedes old thinking, the old thinking is replaced — not preserved alongside it.

### Synthesize, Never Append

When a decision evolves, the document is rewritten to reflect the new state. Not annotated. Not appended with "UPDATE:" sections. The document always reads as if it were written in one pass with complete knowledge. A reader encountering the document for the first time should never have to mentally replay its edit history.

### Document as You Go

Decisions are captured in the moment, not reconstructed later. Every agreement is written into the working document immediately. The session produces its deliverable as a side effect of the conversation — not as a separate writing exercise afterward.

### No Legacy Conflicts Survive

If the current session's decisions conflict with any existing document, code, or prior decision, the conflict is flagged and resolved immediately. A conflict that survives the session will cause confusion in every future session. Legacy vocabulary, legacy structures, legacy assumptions — all are subject to replacement if the current thinking is better.

### Be Proactive

Claude leads the structure. The user leads the direction. Claude should surface conflicts, propose frameworks, offer options, and flag gaps — not wait to be asked. But Claude never acts on a proposal until the user confirms it.

---

## Phase 1: People

### What to Do

Start here. Always. Before discussing features, scoring models, UX layouts, or architecture — ask who the people are.

### Questions to Ask

- Who uses this tool today?
- Who will use this tool when it's fully realized?
- For each persona: What is their job? What do they need from this tool specifically? What does a win look like for them? What's their skill level? What's their workflow — where do they come from before using this tool, and where do they go after?
- Are there personas who should NOT use this tool? Where is the boundary?
- How do internal users differ from external users (if applicable)?
- Is there a progressive disclosure path — some personas see less, some see more?

### How to Structure the Conversation

List the personas in a table. For each one, capture: role title, what they need, where they start, what a win looks like. Read the table back. Let the user correct, add, remove. Do not proceed until the persona list feels complete and accurate.

### What Worked in the Foundation Session

The "Two Audiences, One Hard Wall" framing emerged from this phase — the realization that Skillable internal users (Prospector + Inspector) and customers (Designer) have fundamentally different needs and must never see each other's data. This architectural boundary came from talking about people, not from talking about architecture.

---

## Phase 2: Purpose

### What to Do

With the people defined, ask why this tool exists. Not what it does — why it needs to exist at all.

### Questions to Ask

- What problem does this tool solve that nothing else solves?
- What was the process before this tool existed? What was painful about it?
- What takes hours today that this tool should make take minutes?
- If this tool disappeared tomorrow, what would people do instead?
- How does this tool connect to the other tools in the platform? What intelligence flows in? What flows out?
- What is the one-sentence value proposition a user would say after using it?

### How to Structure the Conversation

Write a "Why [Tool] Exists" section. It should be two to three paragraphs maximum. Read it back. The user should feel it captures the core truth of the tool's purpose. If it reads like marketing copy, rewrite it until it reads like a conversation between two people who understand the problem.

### What Worked in the Foundation Session

The "Product-Up Model" — the insight that the product is the center of everything, not the customer — came from the Purpose phase. This single realization restructured the entire scoring framework.

---

## Phase 3: Principles

### What to Do

Apply the five Guiding Principles (GP1-GP5) plus the End-to-End Principle and the Define-Once Principle specifically to this tool. Not generically — specifically. What does "Right Information, Right Time, Right Person" mean for THIS tool's UX? What does "Explainably Trustworthy" mean for THIS tool's recommendations?

### Questions to Ask

For each Guiding Principle:
- How does this principle manifest in this tool?
- What specific design decisions does it drive?
- Where could this principle be violated if we're not careful?
- What's the test for whether we're honoring this principle?

Tool-specific principles:
- Are there principles unique to this tool that don't apply to others?
- What constraints does this tool operate under that shape its design?
- What should this tool NEVER do?

### How to Structure the Conversation

Create a "Principles Applied to [Tool]" section with a row per principle. Each row: the principle name, what it means specifically in this tool, and one concrete design implication. Keep it tight — principles are guardrails, not essays.

### What Worked in the Foundation Session

The variable-driven approach emerged as a principle — the insight that labels, categories, and messaging should derive from data, never be hard-coded. This became GP4 (Self-Evident Design) and the Define-Once Principle, and it reshaped every badge, every label, every piece of text in the entire platform.

---

## Phase 4: Rubrics

### What to Do

This is where the framework gets specific. Scoring models, category structures, pipeline phases, operational definitions — whatever the tool needs to function, define it here in detail.

### Questions to Ask

- What are the categories, levels, or stages?
- What are the inputs and outputs at each stage?
- Where does human judgment intervene vs. where does the AI decide?
- What scoring or assessment model applies (if any)?
- What vocabulary is locked — terms that must be used consistently?
- What canonical lists exist (lab types, frameworks, delivery patterns)?

### How to Structure the Conversation

This phase is the longest. Take each rubric area one at a time. For scoring models: define the hierarchy, then the weights, then the signals, then the badges. For pipelines: define the phases, then the inputs/outputs, then the intelligence requirements, then the human checkpoints. Do not move to the next area until the current one is settled.

Use tables. Tables force precision. If something can't be expressed in a table, it probably isn't specific enough yet.

### What Worked in the Foundation Session

The verdict grid exercise — building the Fit Score x ACV Potential matrix, naming each cell, defining what each verdict communicates — was the single most productive 30 minutes of the session. It forced every abstract concept into a concrete, testable label. The seller briefcase concept followed immediately from the verdicts, because once you know what a seller should do, you know what they need to know to do it.

---

## Phase 5: UX

### What to Do

Only now, with People + Purpose + Principles + Rubrics settled, design the interface.

### How to Approach UX Iteration

1. **Start with layout** — where do the major sections go? What's the information hierarchy?
2. **Quick mockups** — describe or sketch the layout. Do not worry about pixel-level detail yet. Focus on: what's above the fold? What's the first thing the user sees? What's the progressive disclosure path?
3. **Iterate based on feedback** — the user will react to layout, information hierarchy, and flow. Adjust. Re-describe. Repeat.
4. **Pixel-level refinement** — once the layout and information architecture are settled, get specific: font sizes, spacing, colors, alignment. These details matter for trust and usability.
5. **Name everything** — page names, section names, button labels. If it doesn't have a name, it doesn't have a clear purpose.

### Questions to Ask

- What's the first thing the user should see?
- What's the critical action on this page?
- What information can be hidden behind progressive disclosure?
- Does this layout reflect the scoring hierarchy / pipeline phases / rubric structure?
- If a non-technical person looked at this screen, would they understand what it's telling them?

### What Worked in the Foundation Session

The 70/30 visual split came directly from the 70/30 scoring split — the UX literally reflects the model. This is what happens when UX follows rubrics instead of preceding them.

The hero section design — product name left, Fit Score center (star of the show), ACV right — came from asking "what does the seller need to see first?" The answer was immediate because the People phase had already defined what sellers care about.

---

## Session Conduct Tips

### Listen First, Reflect Back

Before proposing anything, restate what the user said. Not as a parrot — as a synthesis. "So what you're describing is..." If the reflection is wrong, the user corrects it. If it's right, you've built alignment before proposing.

### Let the User Lead Direction, Structure Their Thinking

The user knows the domain. Claude knows how to organize thinking. The user says "I think sellers need something different from SEs." Claude says "Let me structure that — here's a table with what each persona needs. Does this capture it?"

### Flag Conflicts Immediately

If something the user says contradicts a prior decision, say so. "That would conflict with [specific prior decision]. Want to change it, or should we reconcile?" Never let a conflict slide and hope it resolves later.

### Make Decisions Explicit

After a discussion converges, state the decision: "So we're deciding that [specific thing]. Is that locked?" Wait for confirmation. Then write it down. Ambiguity is the enemy.

### Use the "Best Current Thinking" Frame

When the user is uncertain, remind them: "This doesn't have to be permanent. Let's capture our best current thinking and move on. We can revise it if better thinking emerges." This prevents analysis paralysis without sacrificing quality.

---

## What to Avoid

### Going Too Fast

The most common failure mode. It feels productive to race through topics. It is not. A session that covers everything shallowly produces documents that need to be rewritten. A session that covers half the topics deeply produces documents that hold.

### Appending Instead of Synthesizing

When a decision changes, rewrite the section. Do not add a note saying "Updated: now X instead of Y." The document should always read as a single coherent statement of current truth.

### Hard-Coding When Variables Are Possible

Every time a specific name, label, or category is written into a design decision, ask: could this be variable-driven instead? The Foundation session's biggest architectural insight was that nearly everything should be variable-driven — organization type, product category, motivation, badge text, ACV labels.

### Making UX Decisions Without Seeing Them

Do not finalize UX decisions in the abstract. Describe the layout. Build a wireframe if possible. Let the user react to something visual. The Foundation session's wireframe exercise caught several issues that the verbal description missed — the pillar card spacing, the hero section information hierarchy, the product selector dropdown design.

### Skipping the People Phase

The temptation is always to jump to "what should the tool do." Resist it. Start with who. Every time.

---

## Session Deliverables

A successful foundation session produces:

1. **A Foundation document** — the authoritative strategic reference for the tool. People, purpose, principles, rubrics, UX — all in one synthesized document.
2. **Updates to the Decision Log** — every decision captured with date and session context.
3. **Identified conflicts with existing documents** — listed explicitly, with resolution or flagged for follow-up.
4. **A clear "what's next" list** — implementation priorities that follow directly from the foundation decisions.

---

## Applying This to the Designer Session

The Designer session should follow this exact methodology:

1. **People** — Who uses Designer? Program owners, IDs, SMEs, ProServ, customers. What does each one need? How does the customer-facing future change the design?
2. **Purpose** — Why does Designer exist? The parallel workstream insight. The adoption problem. Building discipline.
3. **Principles** — GP1-GP5 applied to Designer specifically. How does "Explainably Trustworthy" work for program recommendations? How does "Right Person, Right Time" work when the same tool serves internal ProServ and external customers?
4. **Rubrics** — The 8-phase pipeline deep dive. Each phase: inputs, outputs, intelligence requirements, human checkpoints, scoring/assessment model.
5. **UX** — Designer's three-pane layout. Phase transitions. The checklist. The outline. Draft instructions. Export.

Read Designer-Session-Prep.md before starting. It contains the current state assessment, specific questions for each phase, and every open decision that needs resolution.
