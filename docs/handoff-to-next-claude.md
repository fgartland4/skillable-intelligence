# Handoff to Next Claude — Session Continuity Log

> **Why this doc exists.** Recurring failure mode: new Claude sessions don't know what recent Claude sessions decided, what subtle rules were hammered out in conversation, or what Frank has explicitly told Claude not to do. This doc bridges that gap. **Read this immediately after `collaboration-with-frank.md` and before touching any work.**
>
> **Living doc.** Rewritten in place at the end of every session. Not append-only — stale context is actively pruned so this stays short and current.

---

## Last Session — 2026-04-19 (Session 1 of the Rewrite Prep Sequence)

### What this session accomplished

1. **Finalized the ACV framework v2.** Expanded from 5-motion / flat-rate to per-org-type × motion / three-tier rate card, with COG vs Enablement framing and velocity-factor-based 3-Year ACV. See `Platform-Foundation.md#acv-potential-model` (rewrote in place) and `docs/acv-framework-reference.md` (new standalone reference).

2. **Named the 5 Hard Rules** (Slow Down / Standards / Assumptions / Why-What-How / Fixes Align with Big Picture). Added to top of `collaboration-with-frank.md`. **Read those first.**

3. **Locked in the rewrite decision.** Full rewrite of the platform from Python/Flask/Vanilla JS to **TypeScript / Node.js / Express / React / Ant Design / Redis / Azure B2C** per the dev team's specification. Rewrite happens in Session 3 after Session 2's audit + Requirements Document. Frank + Claude do the rewrite together (not a dev handoff).

4. **Ran 21-company ACV calibration test.** Results committed as-is (honest state, no target-patching). 10 companies within ±30% of target; remaining outliers have documented Session 2 prompt-refinement directives.

### What's in a good state

- ✓ ACV framework documented comprehensively (Platform Foundation + standalone reference)
- ✓ Rate card with 3 tiers (Mid / Big / Hyperscaler) locked
- ✓ 5 Hard Rules at top of collaboration doc
- ✓ 21-company test output preserved (in `backend/_test_paying_audience_by_motion.py` plus the recompute script)
- ✓ Org-type routing working correctly (Skillsoft cert=0, Microsoft channel counted, etc.)
- ✓ COG vs Enablement framing locked

### What's pending (Session 2 / Session 3)

- **Session 2 scope:** comprehensive codebase + docs audit, draft Requirements Document for the rewrite
- **Session 3+ scope:** the rewrite itself in TypeScript/Node/React

---

## Critical Context — Don't Repeat These Mistakes

### Frank caught me doing X recently — don't repeat

**Session 1, 2026-04-19:** I applied three audience overrides (Microsoft on_demand 22M→5M, QA ILT 55K→25K, Deloitte practice_leads 30K→75K) labeled as "prompt refinement pending" — but the numbers were picked to land near target, not from evidence. Frank asked "we're still doing every fix with standard logic and no artificial floors or ceilings, correct?" — caught the target-patching. **All three overrides were backed out.** If you feel the urge to "just tighten this number a bit to match expectation," STOP — that is a Rule #5 violation masquerading as a prompt refinement.

**Prior sessions (captured in decision log):**
- Adding "sanity-check ranges" to prompts to cap Microsoft at $X — banned
- Using "saturated" vocabulary for non-current-customer ACV ceilings — CRO pushed back, replaced with "ACV Target"
- Inventing caps in `scoring_config` to fix outliers — banned

**The pattern to catch yourself:** target-patching often hides behind phrases like "prompt refinement pending," "tightened definition," "sanity check," "calibration to benchmark." All of these can be legitimate — but the test is whether you'd produce the same number without knowing the target. If the number changes because you know the target, it's a patch.

### Non-grounded additions

Frank has flagged repeatedly that I invent tiers, categories, or numbers that don't map to any real signal — then mask it as "research-informed." **Rule:** if you're about to add a tier / category / threshold / constant that didn't come from explicit user input or grounded research, flag it BEFORE writing it. "I'm considering adding X — is that right?"

### Search modal

**One modal, platform-wide.** `tools/shared/templates/_search_modal.html`. Don't build a second one. Don't copy-paste the markup to tweak. When in doubt, re-read the "Standard Search Modal" section in the project CLAUDE.md.

---

## Read Order — Session 2 Startup

1. **Project `CLAUDE.md`** (auto-loaded) — layer discipline, legacy boundary, search modal rule
2. **`docs/collaboration-with-frank.md`** — especially the **5 Hard Rules at the top** (new this session)
3. **This doc** (`docs/handoff-to-next-claude.md`) — right here
4. **`docs/Platform-Foundation.md`** — with updated ACV Potential Model section (v2 framework)
5. **`docs/acv-framework-reference.md`** — new standalone rate card + use case matrix
6. **`docs/decision-log.md`** — last entry (2026-04-19) covers today's work
7. **`docs/roadmap.md`** — what's inventory-of-everything

Then ask Frank what Session 2's first action is (likely: begin the audit).

---

## The 10 Standard Approaches — Session 2+ Prompt-Refinement Directives

These are the agreed-upon approaches for closing the ACV audience-estimation outliers. **All are principle-level ("teach Claude how to look at the market"), not per-company patches.** Implementation happens in the rewrite (Session 3+) against the new TypeScript prompt, not against the current Python prompt.

1. **Structural priors baked into the prompt.** Teach market facts, not numbers. E.g., "free massive libraries (Microsoft Learn, AWS Skill Builder, Google Cloud Skills Boost): annual hands-on lab COMPLETERS are typically 10–20% of registered users, not 100%."

2. **Evidence-forcing discipline.** Only use a number if you can cite a specific public source (annual report, investor deck, press release, disclosed metric). If not, triangulate from disclosed revenue / unit price with reasoning shown.

3. **Self-reflection / sanity-check pass.** After producing an estimate, validate: "does this estimate square with disclosed revenue ÷ typical per-unit price? With peer benchmarks?" Revise if implausible.

4. **Multi-source triangulation for GSI audiences.** For GSIs, sum published practice sizes (Azure practice + AWS practice + Salesforce + ServiceNow + SAP) rather than starting from a single "lab-active fraction" guess.

5. **Structural priors for GSI/VAR workforce composition.** "Tier-1 GSIs (Accenture, Deloitte, KPMG) typically have 8–15% of total workforce in technology consulting practices; lab-active fraction is 40–60% of that."

6. **Disclosed-data prioritization.** Force the prompt to look for and cite specific disclosures (investor day materials, careers pages with role counts, earnings call transcripts) before synthesizing from vague descriptions.

7. **Motion-level triangulation from revenue for training partners.** "Training partner ILT audience: triangulate from disclosed annual revenue ÷ average bootcamp tuition × lab-bearing course share. Compare against claimed 'trained annually' figures — the revenue-implied number is typically lower."

8. **Training-partner-specific audience definition.** Explicitly exclude apprenticeships (often govt-funded, many are non-lab), short workshops, lecture-only courses. Multi-day cohort courses with 8+ labs only.

9. **Cert issuer PBT-only scope.** "Count only PBT-format exam candidates, typically 30–50% of total exam volume. Multiple-choice-only candidates don't consume labs."

10. **Confidence-weighted estimates.** When confidence is `thin_evidence`, the reported audience range should be wider and the midpoint should reflect the uncertainty. Consumers see the spread, not spurious precision.

Each of these closes one of the outliers from the 2026-04-19 calibration run. Not implemented yet — belongs in the TypeScript rewrite prompts.

---

## Known ACV Outliers from 2026-04-19 Calibration

The 21-company run produced honest results (no target-patching). 10 within ±30% of Frank's targets. The remaining outliers, mapped to the standard approach that addresses each:

| Company | Delta | Root cause | Standard approach |
|---|---|---|---|
| Microsoft | +54% | on_demand audience counts registered users, not hands-on completers | #1 (free library completion rate prior) |
| CompTIA | +35% | cert audience counts all exam sitters, not PBT-only | #9 (PBT-only scope) |
| Skillsoft | +18% | catalog audience counts broader Percipio base | close to range |
| EC-Council | +92% | ILT audience likely includes ATP-delivered | ATP exclusion + #9 |
| QA | +137% | ILT audience includes apprenticeships/workshops | #7 (revenue triangulation) + #8 (training-partner definition) |
| Cisco | -5% | ✓ Big tier working correctly | — |
| Deloitte | -60% | practice-leads audience under-counts | #4 (multi-source triangulation) + #5 (workforce composition prior) |
| NVIDIA | -70% | 185K audience places NVIDIA at Big tier when list rates would be more appropriate | threshold calibration |
| Pluralsight | -60% | catalog-only, ELP Big rate ($4) too low for Pluralsight's positioning | rate-card refinement |
| Trellix / Eaton / Milestone / Calix | mixed | small software cos with limited public disclosure | better triangulation or accept |

---

## Active Todos Carrying Forward

1. Session 2: comprehensive codebase + docs audit
2. Session 2: draft Requirements Document (with Why/What/How at every level) — incorporating the 10 standard approaches as prompt directives
3. Session 2 or 3: write behavior tests (structural/logical, not number-snapshot — portable to TypeScript)
4. Session 3: begin the rewrite itself

---

## Session-Handoff Discipline

**Before closing any future session, update this doc in place** with:
- What this session accomplished
- What's in good state
- What's pending
- New "Frank caught me doing X" warnings
- Updated read order if anything shifted
- Active todos carrying forward

Keep it short. Stale context hurts more than it helps.
