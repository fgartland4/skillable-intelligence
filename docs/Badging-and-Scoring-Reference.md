# Badging and Scoring Reference

This is the operational reference for how the Skillable Intelligence scoring framework actually works — every Pillar, every dimension, every signal, every rule. It is the authoritative source for the math layer and it serves as the **in-app explainability layer** (GP3): each section below can be linked from the UX so any user can see exactly how any part of the framework is computed, in plain English, with one click.

For strategic context — Guiding Principles, the Three Layers of Intelligence, the people the platform serves, the Verdict Grid, and the ACV Potential model — see `Platform-Foundation.md`. Where this document touches a concept Platform-Foundation owns (pillar weights, 70/30 split, verdict labels, ACV motions, rate tiers), it names the concept and refers back. **No duplication.**

Best current thinking, always. Fully synthesized, never appended.

---

## How to Read This Document

Every Pillar section below is **self-contained** and follows the same shape so you can read any one of them in isolation and understand it completely — which is also what lets the in-app modal pull a single Pillar section as stand-alone explainability content.

| Section | What it answers |
|---|---|
| **Why** | Why this Pillar exists in the framework |
| **What it measures** | The four dimensions and the question each one answers |
| **Scoring model** | Canonical (Pillar 1) or rubric (Pillars 2 + 3) — and what that implies |
| **How each dimension is scored** | Per-dimension detail — signals, baselines, caps, penalties, evidence |
| **Cross-pillar compounding** | Where a signal in this Pillar also credits a signal in another Pillar |
| **Worked examples** | Real products — Trellix, Diligent, CompTIA, IBM — stepping through the math |

Pillars 1, 2, and 3 use this same structure. Find your bearings in one, and you can navigate the others.

---

## The Scoring Hierarchy

**Why.** Readers need one consistent mental model for the whole framework. Everything else in this document hangs off this hierarchy.

**What.** Five levels, coarsest to finest:

```
Fit Score (0–100)
  └─ Pillar (three of them, weighted 50 / 20 / 30)
       └─ Dimension (four per Pillar, weights sum to 100 within a Pillar)
            └─ Signal or graded finding (facts extracted by the researcher)
                 └─ Badge (the 2–4 display items per dimension that tell the story)
```

The Fit Score, 70/30 split, pillar weights, and verdict grid are defined in `Platform-Foundation.md → Scoring Framework at a Glance` and `→ Verdict Grid`. This document does not re-state them — it picks up where those sections end, at the dimension level.

**How.** Two scoring models live below the dimension level. Pillar 1 uses the **canonical model** (fixed badge vocabulary, named scoring signals, deterministic point lookup). Pillars 2 and 3 use the **rubric model** (variable-data badge names, strength tiers, category / org-type baselines). Both models produce the same shape of output — a `DimensionScore` with a numeric value and a list of display badges — but they get there differently because they measure different kinds of things. The two-model architecture is intentional, not accidental, and it should not be collapsed.

| Pillar | Scoring model | Scope | What it measures |
|---|---|---|---|
| **1 — Product Labability** | **Canonical** — fixed badge vocabulary, deterministic scoring signal lookup from `scoring_config.py`, color-aware credit (green = full, amber = 1/2 except Scoring dimension which uses 1/3, red = color fallback) | **Per-product** — each product has its own Pillar 1 reading because each product has its own technical fabric | Technical fact-finding. Hyper-V either supports the install or it doesn't. APIs exist or they don't. **Concrete and binary.** |
| **2 — Instructional Value** | **Rubric** — AI-synthesized variable badge names, strength tiers (strong / moderate / weak / informational), category-aware baselines, per-dimension signal_category tags | **Per-product** — product complexity, mastery stakes, lab versatility, and market demand are all properties of THIS product | Domain-specific judgment. Cybersecurity, legal, healthcare, banking are genuinely different. **Subjective and contextual.** |
| **3 — Customer Fit** | **Rubric** — same architecture as Pillar 2 with organization-type baselines | **Per-COMPANY** — Customer Fit measures the ORGANIZATION, not the product. Every product from the same company gets the same Pillar 3 reading | Organizational pattern recognition. Training maturity, build capacity, delivery partners, partner culture — properties of the COMPANY, not any single product. |

---

## Four Badge Colors

**Why.** Every badge on every Pillar carries a color. One color vocabulary across the whole platform means readers can scan any card and know immediately what they're looking at.

**What.**

| Color | Meaning | Qualifier label | When to use |
|---|---|---|---|
| **Green** | Works — confident, no action needed | `| Strength:` or `| Opportunity:` | Skillable can do this cleanly, OR a positive finding worth celebrating |
| **Gray** | Context — informational, no scoring impact | `| Context:` | Facts the seller should know that don't move the score |
| **Amber** | Uneasy — needs SE validation | `| Risk:` | The path exists but there's friction, a decision, or a detail an SE should verify before promising |
| **Red** | Cannot do this, or this specific thing is blocked | `| Blocker:` | A hard constraint. Something about the product or customer makes this specific approach unavailable |

**How.** Amber is **"uneasy, needs validation"** — not "risk" in the hedge-everything sense. The word "uneasy" is the locked vocabulary (Frank 2026-04-08). An amber badge means an SE should dig one level deeper before the seller commits. Red is harder: the thing named in the badge is not available. Multi-badge per dimension is legitimate — a dimension can carry a green strength badge next to an amber concern next to a gray context note. The dimension card renders all of them.

**Purple** is used for **classification**, not scoring — product subcategory badges and company classification badges. Purple signals categorization, not assessment. It is never one of the four scoring colors above.

**Evidence on hover.** Every badge MUST carry an evidence payload — no badge renders without evidence. Hovering for 1.5 seconds triggers a modal displaying evidence bullets, source, and confidence level. This is how GP3 (Explainably Trustworthy) is realized at the badge level.

**Confidence language:**

| Level | Meaning | Example |
|---|---|---|
| **Confirmed** | Direct evidence from primary source | "REST API **confirmed** — OpenAPI spec at docs.vendor.com" |
| **Indicated** | Strong indirect evidence | "VM deployment **indicated** — installation guide references Windows Server" |
| **Inferred** | AI assumption from patterns or limited signals | "Troubleshooting lab potential **inferred** from category norms" |

---

## Badge Naming Rules — The Locked Discipline

**Why.** Badge drift destroys trust. When `Build vs Buy` carries three different findings by color (Platform Buyer / Mixed / Builds Everything), the label teaches the reader nothing without a color legend — and the seller can't scan the card. Every badge name must be a finding the seller can read out loud and understand without context.

**What — the rules, all locked 2026-04-08:**

| Rule | What it means |
|---|---|
| **The badge IS the finding** | The name is the answer, not the topic. `Platform Buyer` is an answer. `Build vs Buy` is a topic. |
| **Restricted canonical vocabulary** | Framework vocabulary is fixed — `Runs in VM`, `Runs in Azure`, `Runs in AWS`, `Runs in Container`, `Sandbox API`, `Training License`, `Low Orphan Risk`, `Orphan Risk`, `High Orphan Risk`, `Pre-Instancing?`, `Custom Cloud`, `M365 Tenant`, `M365 Admin`, `No GCP Path`. These never abbreviate and never vary. |
| **Everything else is free** | Variable badges (Pillar 2 and Pillar 3 rubric findings) can use any domain-specific wording — `Breach Exposure`, `~500 ATPs`, `Multi-Correlation Engine`. Abbreviate freely: Config, Admin, Auth, Dev, Ops. |
| **Max length** | ~25 characters / ~4 words. Concise is the goal. Variable-data badges (counts, platform names) can run slightly longer. |
| **Vendor acronyms — only when real** | Use a vendor's own acronym (Trellix `TIE`, Microsoft `SCCM`, Cisco `ISE`) only when the vendor themselves uses it in their own marketing or docs. **Never invented.** The `vendor_official_acronym` field on `Product` captures this; the researcher populates it from evidence. |
| **Acronym format** | ALL CAPS, no periods — `TIE` not `T.I.E.`, `SCCM` not `S.C.C.M.` Industry standard acronyms (API, CLI, GUI, AI, MFA, SSO, SIEM, EDR, SOC, REST API, OpenAPI, SAML, ATP, ALP, GPU, CPU, NFR) are always ALL CAPS and never spelled out. |
| **Capitalization** | Title Case for badge words. Acronyms stay ALL CAPS. |
| **Absence-finding convention** | Use a `No X` prefix when naming a finding about absence — `No Training Partners`, `No Classroom Delivery`, `No Deployment Method`, `No GCP Path`, `No Independent Training`. Absence is a finding, not a blank. |
| **No periods anywhere** | Badge text has no trailing periods and no internal periods. |
| **No product names of the company being scored** | The dossier header has the company name — don't repeat it in badges. |
| **No topic labels as names** | `Partner Ecosystem`, `Training Catalog`, `Integration Maturity` are topics, not answers. The badge must name the *finding*. |
| **No signal_category names as badge names** | `deep_configuration` is the internal category, not the label. The badge is the finding that belongs in that category — `180+ Detection Rules`, `Multi-Phase Workflow`. |
| **Name the specific provider, not the category** | `Pearson VUE` not `Cert Delivery Infra`. `iLabs` not `Has Lab Platform`. `ILT Calendar` not `Published Course`. The badge names the thing, not the type of thing. *(Locked 2026-04-12)* |
| **Absence badges are mandatory, not optional** | When a dimension scores but has no positive badges, emit specific absence findings — `No Scoring API`, `No Script Access`, `SaaS-Only`. A dimension with a score and zero badges is a UX failure. Absence is a finding, not an empty space. *(Reinforced 2026-04-12)* |
| **Coexistence of nuanced findings** | A dimension can carry both a strength and a concern about the same topic when both are evidence-specific. `~12 Pluralsight Courses` (green) alongside `Thin Training Market` (amber) — both true, no contradiction because the names are specific enough that the reader understands both. Avoid generic labels that would clash — use count-based findings (`~12 Pluralsight Courses`) and assessment findings (`Thin Training Market`, `Niche Audience`). *(Locked 2026-04-12)* |
| **Standard badge name fixes** | `Content Team` not `Content Team Named`. `IDs on Staff` not `ID IDs`. `Niche Audience` (amber) for products with small training populations. *(Locked 2026-04-12)* |

### Organization-Type Badge Language Overrides

**Why.** A university has a curriculum, not a training catalog. A professor is faculty, not a training leader. Using software-company vocabulary for academic institutions produces badges that don't make sense to the reader. Badge language must match the organization type.

**What — vocabulary overrides by org type:**

| Standard (Software) | Academic Override | Why |
|---|---|---|
| Training Catalog | Curriculum | Universities publish curricula, not training catalogs |
| Training Leadership | Faculty / Academic Leadership | Professors and deans, not VPs of Enablement |
| Training Programs | Degree Programs | Degrees and certificates, not training programs |
| Training Commitment | Academic Commitment | Teaching IS the mission |
| Training Catalog Present | Strong Curriculum | More specific and natural |
| Hands On | Lab-Based Courses | Academic framing |
| Multi Audience Commit | Multi-Program Breadth | Undergrad + graduate + certificate + online |

**How.** The rubric grader applies these overrides when the org_type is ACADEMIC. The scorer and badge selector are org-type-agnostic — they process whatever badge names the grader emits. The vocabulary shift happens at grading time, not scoring time.

**How.** Pillar 1 enforces the canonical vocabulary via `_verify_canonical_names` in `pillar_1_scorer.py` — the scorer verifies at module load that every signal name it references matches a signal in `scoring_config.py`. Drift throws an immediate error. Pillars 2 and 3 enforce the rubric model by requiring every graded finding to carry a `signal_category` that matches the dimension's fixed category list; unknown categories are silently dropped by the scorer. The badge selector (`badge_selector.py`) then turns graded signals + canonical facts into display badges that honor the naming rules above.

---

## Pillar 1 — Product Labability (50%)

### Why this Pillar exists

**Product Labability is the gatekeeper.** If Skillable cannot deliver a complete lab lifecycle for this product, nothing else matters — not the instructional case, not the customer maturity, not the deal size. The four dimensions below collectively answer one question: **can we run a hands-on lab on this product, at scale, for learners we've never met?** A failure in any one dimension is a signal. A failure in multiple dimensions is a wall.

Pillar 1 is weighted 50% — the heaviest single Pillar — because Product Labability is the gatekeeper. If Skillable cannot get the product into its platform, nothing else matters. When Pillar 1 is weak, the `fit_score_composer` Technical Fit Multiplier drags the downstream pillars' contribution down — weak PL means strong instructional signals can't fully compensate. See `Platform-Foundation.md → Fit Score Composition` for the asymmetric coupling rule. *(Rebalanced from 40% on 2026-04-12.)*

### What it measures — four dimensions

| Dimension | Weight | Question |
|---|---|---|
| **Provisioning** | 35 | How do we get this product into Skillable? |
| **Lab Access** | 25 | Can we get people in with their own identity, reliably, at scale? |
| **Scoring** | 15 | Can we assess what they did, and how granularly? |
| **Teardown** | 25 | Can we clean it up when it's over? |

Weights sum to 100 within the Pillar. Each dimension scores out of its weight (Provisioning 0–35, Lab Access 0–25, etc.); the Pillar total is the sum.

### Scoring model — canonical

**Why canonical.** Technical fact-finding is concrete. Hyper-V supports the install or it doesn't. The Sandbox API exposes per-learner provisioning or it doesn't. Facts this binary don't benefit from qualitative rubric tiering — they benefit from a named vocabulary of canonical findings and a lookup table of points per finding.

**What the canonical model means operationally:**

- The AI extracts typed fact primitives into `ProductLababilityFacts` (`runs_as_installable`, `has_sandbox_api`, `sandbox_api_granularity`, `auth_model`, etc.) — this is the Research layer's job.
- `pillar_1_scorer.py` reads those facts directly — zero Claude, pure Python — and produces a `DimensionScore` per dimension by walking a priority order and crediting named scoring signals from `scoring_config.py`.
- Each canonical badge has a fixed name, fixed color criteria, and a fixed point value when emitted green.
- **Color-aware credit**: green = full points, amber = half points (except the Scoring dimension which uses 1/3 credit — `cfg.SCORING_AMBER_CREDIT_FRACTION = 3` — because "can't really tell" on scoring methods should not produce near-full marks), red = falls back to the color contribution table (negative points for red blockers).
- The math layer never reads badge names from Claude output. It reads the fact drawer, produces the dimension scores, and then `badge_selector.py` separately emits display badges based on the same facts.

### 1.1 Provisioning (35 points)

#### Why

Provisioning determines difficulty for everything else. When a product runs in Skillable's own infrastructure (VM, container, Cloud Slice), Lab Access / Scoring / Teardown are largely within Skillable's control. When a product runs in the vendor's own cloud via Sandbox API, every downstream dimension depends on the vendor's APIs and policies. That's why Provisioning is the heaviest dimension in Pillar 1 (35 / 100).

#### What

**Path priority order.** The scorer walks the fabrics in sequence and picks the FIRST viable path — the priority IS the score order.

| Priority | Path | When it fires | Canonical badge |
|---|---|---|---|
| 1 | **M365 Tenant / Admin fabric** | Product is a Microsoft 365 scenario | `M365 Tenant` (End User) or `M365 Admin` (Administration) |
| 2 | **VM fabric** | Installable on Windows / Linux | `Runs in VM` (default), `Runs in Container` (singular), `ESX Required` (amber anomaly) |
| 3 | **Cloud Slice fabric** | Product IS an Azure or AWS native managed service | `Runs in Azure` or `Runs in AWS` |
| 4 | **Sandbox API** (BYOC) | SaaS but vendor exposes a provisioning API for per-learner environments | `Sandbox API` (green) + `Custom Cloud` (gray strength context) |
| 5 | **Simulation** | Nothing else viable — NOT a fallback, a real fabric | `Simulation` (gray Context) → triggers Simulation hard override (see below) |

**Cloud disambiguation.** `Runs in Azure` / `Runs in AWS` mean the product IS the cloud's native managed service, NOT "hostable on a VM in that cloud." For installable products that happen to run on cloud VMs, the badge is `Runs in VM`.

**Native fabric beats manual API wiring.** A SaaS product native to Azure or AWS uses Cloud Slice (Path 3), not Sandbox API (Path 4) — even if both are technically viable. The platform prefers the path with less SE work per lab build.

**Canonical badges:**

| Badge | Green | Amber | Red |
|---|---|---|---|
| **Runs in VM** | Clean VM install confirmed | Installs with complexity | — |
| **Runs in Azure** | Azure-native managed service | Azure path with friction | — |
| **Runs in AWS** | AWS-native managed service | AWS path with friction | — |
| **Runs in Container** | Container-native confirmed, no disqualifiers | Image exists but disqualifiers OR research uncertain | — |
| **ESX Required** | — | Nested virt or socket licensing forces ESX (details in evidence) | — |
| **Simulation** | — (gray Context when chosen path) | — | — |
| **Sandbox API** (gatekeeper) | Vendor has rich provisioning / sandbox / management API | API exists but coverage uncertain | No provisioning API confirmed |
| **M365 Tenant** | Microsoft 365 End User scenario — automated tenant lane | — | — |
| **M365 Admin** | — | Microsoft 365 Admin scenario — trial tenant or MOC-provided tenant (identity verification friction) | — |
| **Custom Cloud** | — (gray Strength context alongside Sandbox API) | — | — |
| **Pre-Instancing?** | Slow first-launch or large-footprint cold starts mitigated by Skillable Pre-Instancing — feature suggestion | — | — |
| **Multi-VM Lab** | Multiple VMs working together — Skillable competitive strength | — | — |
| **Complex Topology** | Real network complexity (routers / switches / firewalls / segmentation) — networking AND cybersecurity | — | — |
| **GPU Required** | — | Forces cloud VM with GPU instance — slower, more expensive | — |
| **Bare Metal Required** | — | — | Physical hardware required — no virtualization path |
| **No Deployment Method** | — | — | Ultimate dead end — no real provisioning AND no Simulation viable |
| **No GCP Path** | — | Product runs on GCP but another viable fabric exists — workaround path | GCP is required or preferred by the vendor AND no native Skillable GCP path |

**Sandbox API + GCP path contradiction.** When a product has `needs_gcp=true` AND the primary fabric is Sandbox API, the Sandbox API badge downgrades from green to amber (half credit). A GCP-native product using Sandbox API (BYOC) inherits the GCP limitation — Skillable has no native GCP fabric, so the BYOC path has known friction. Green Sandbox API alongside No GCP Path amber was a scoring contradiction: the framework was saying "clean BYOC path" and "no GCP path" simultaneously. The amber downgrade resolves it — the BYOC path exists but carries the same GCP friction that No GCP Path names. *(Locked 2026-04-13.)*

**Container disqualifiers.** `Runs in Container` fires green only when the container is **production-native** AND none of the three disqualifiers apply: production_native = True AND NOT dev_only AND NOT needs_windows_gui AND NOT needs_multi_vm_network. If any disqualifier fires, the container path is not viable and the scorer falls through to the next priority.

**Simulation hard override.** When the scorer picks Simulation as the fabric (nothing else viable), all four Pillar 1 dimensions get hard override values that bypass normal dimension scoring:

| Dimension | Simulation override value | Source |
|---|---|---|
| Provisioning | 5 | `cfg.SIMULATION_PROVISIONING_POINTS` |
| Lab Access | 12 | `cfg.SIMULATION_LAB_ACCESS_POINTS` |
| Scoring | 0 | `cfg.SIMULATION_SCORING_POINTS` |
| Teardown | 25 | `cfg.SIMULATION_TEARDOWN_POINTS` |
| **Pillar 1 total** | **42 / 100** | Light Amber — viable fallback, not the happy path |

Teardown is full credit under Simulation because there is nothing to tear down — structurally equivalent to Datacenter automatic cleanup. Scoring is 0 because Skillable doesn't score simulations today (feature request, not a capability).

**Multi-fabric optionality bonus.** When a product has a primary fabric plus one or more secondary viable fabrics (e.g., installable AND container-native AND Sandbox API), the scorer adds `cfg.MULTI_FABRIC_OPTIONALITY_BONUS_PER_EXTRA` (3 pts) per extra fabric, capped at `cfg.MULTI_FABRIC_OPTIONALITY_BONUS_CAP` (6 pts). Simulation does NOT count as a secondary fabric for the bonus. Partial-granularity Sandbox API does NOT count either. This rewards products that give SEs real choices at lab-build time.

#### How — scoring signals

Each canonical badge has a fixed green base credit. The math layer looks up the point value from `scoring_config.py` — no hardcoded numbers in the scorer.

| Canonical | Green base credit | Source |
|---|---|---|
| `Runs in VM`, `Runs in Azure`, `Runs in AWS`, `Runs in Container` | +30 | `cfg` scoring signals |
| `ESX Required` | +26 | -4 vs VM for Broadcom licensing operational cost |
| `M365 Tenant` | +25 | `cfg.M365_TENANT_POINTS` — one below a general-purpose fabric because M365 scope is narrower |
| `Sandbox API` | +22 | BYOC path — viable per-learner provisioning, scored below native fabrics |
| `M365 Admin` | +18 | `cfg.M365_ADMIN_POINTS` — lower because identity verification adds friction |
| `Multi-VM Lab`, `Complex Topology`, `Pre-Instancing?`, `Custom Cloud` | 0 | Strength context — drives ACV rate tier upward, does NOT score points in Provisioning |

**Provisioning friction penalties:**

| Penalty | Deduction |
|---|---|
| `GPU Required` | -5 |
| `Socket licensing (ESX) >24 vCPUs` | -2 (surfaces as evidence on the `ESX Required` badge) |

**Ceiling caps (handled in `pillar_1_scorer` via `score_override`, not via a separate ceiling-flag dict):**

| Condition | Pillar 1 cap | Source |
|---|---|---|
| Bare metal required | 5 | `cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE` (shared constant) |
| Sandbox API red + Simulation viable | 25 | `cfg.SANDBOX_API_RED_CAP_SIM_VIABLE` |
| Sandbox API red + nothing viable | 5 | `cfg.SANDBOX_API_RED_CAP_NOTHING_VIABLE` |

These caps are applied directly by `pillar_1_scorer` as a `score_override` on the final `PillarScore`. The old `CEILING_FLAGS` dict has been retired — `saas_only`, `no_api_automation`, and `multi_tenant_only` are structurally replaced by the red-badge risk cap reduction described in "Risk Cap Reduction" below.

### 1.2 Lab Access (25 points)

#### Why

Provisioning gets the environment. Lab Access gets the *learner* into the environment — with their own identity, reliably, without SE hand-wringing at every onboard. This is where identity lifecycle, credential management, training licenses, and learner isolation live. A product can provision perfectly and still fail Lab Access if there's no way to give 500 learners their own credential path.

#### What

**Canonical badges:**

| Badge | Green | Amber | Red |
|---|---|---|---|
| **Full Lifecycle API** | Complete API for user provisioning and management | — | — |
| **Identity API** | Vendor API can create users and assign roles per learner | API exists but coverage uncertain | — |
| **Entra ID SSO** | App pre-configured to use Entra ID tenant — zero credential management. **Azure-native applications only.** Preempts `Identity API` for Azure products. | — | — |
| **Cred Recycling** | Customer credentials can be reset and recycled between learners — low operational overhead | Recycling exists but coverage uncertain | — |
| **Credential Pool** | Pre-provisioned consumable credential pool — operationally painful but works | — | — |
| **Training License** (consolidated) | **Universal amber default** (Frank 2026-04-08) — every product fires Training License amber unless the license is explicitly blocked. Green is reserved for truly zero-friction cases (OSS with no concurrent-user model, no tier choices). | Amber Risk — license design conversation needed with customer | Red — license blocked (credit card + high cost + no negotiation path) |
| **Learner Isolation** (gatekeeper, always emit) | Per-user or per-tenant isolation confirmed via API evidence | Research can't confirm either way | Explicitly absent — confirmed shared multi-tenant with no isolation mechanism |
| **Manual SSO** | — | Azure SSO but requires manual learner login | — |
| **MFA Required** | — | — | MFA blocks automated provisioning |
| **Anti-Automation Controls** | — | — | Platform actively blocks automated account creation (CAPTCHA, bot detection) |
| **Rate Limits** | — | — | API rate limits constrain concurrent learner provisioning |

**Training License universal amber default.** Real SE conversations happen around almost every non-trivial licensing arrangement — tier choice (Base / Full / Full+AI for M365), concurrent user count, optional add-ons, regional restrictions, commercial-vs-training license terms, existing customer agreements. Green is rare enough that the badge defaults to amber until an SE confirms otherwise. Red fires only when the fact drawer reports the license is blocked.

**Cred Recycling vs Credential Pool — two distinct canonicals:**

- **Credential Pool** — Customer hands over a batch of credentials; we deplete the pool; when we run low we ask for more. Operationally painful.
- **Cred Recycling** — Customer hands over one set; we clean up after each learner and return it to the pool. Self-sustaining.

#### How — scoring signals

| Canonical | Green base credit |
|---|---|
| `Full Lifecycle API` | +23 |
| `Entra ID SSO` | +20 |
| `Identity API` | +19 |
| `Cred Recycling` | +18 |
| `Credential Pool`, `Training License` | +16 |
| `Manual SSO` | +12 |

**Penalties:**

| Penalty | Deduction |
|---|---|
| `MFA Required` | -15 |
| `Rate Limits` | -5 |
| `Anti-Automation Controls` | -5 |

Floor: 0. The dimension never scores negative.

### 1.3 Scoring (15 points)

#### Why

A lab that can't be scored isn't a lab — it's a guided tour. The Scoring dimension asks whether Skillable can assess what the learner actually did, with what granularity, and through what mechanism (API, script, AI Vision, simulation, MCQ). **Scoring is about OPTIONS** — full marks require more than one viable assessment path, because no single method covers every lab scenario.

#### What — the Grand Slam rule

Per Frank 2026-04-07: full marks (15 / 15) require **AI Vision PLUS at least one programmatic method** — Script Scoring for VM context OR Scoring API for cloud context. Single-method-alone caps below 15.

The dichotomy:

- **Script Scoring** — what you write when you have shell access to a VM (Bash / PowerShell running INSIDE the VM). Direct state validation with zero API involvement.
- **Scoring API** — what cloud products require. Cloud services don't give you shell access, so you need an API to invoke validation work remotely.
- **AI Vision** — peer to API/Script, not a fallback. GUI-driven product where state is visually evident. Real Skillable differentiator — rare in the lab platform space.

**Canonical badges:**

| Badge | Green | Amber | Notes |
|---|---|---|---|
| **Scoring API** | Vendor REST API for state validation — rich coverage | API exists but coverage uncertain or partial | Cloud products use this |
| **Script Scoring** | Bash / PowerShell scripts can validate config state comprehensively | Scriptable surface exists but with gaps | VM products use this |
| **AI Vision** | GUI-driven product where state is visually evident — AI Vision is the right tool | AI Vision usable but visual state ambiguous | Peer to API / Script, not a fallback |
| **Simulation Scorable** | — | Simulation environment supports scoring via guided interaction | (Pending SE clarification — see "Open Questions" at the end) |
| **MCQ Scoring** | — (gray Context only) | No programmatic surface — knowledge-check questions only | **0 points.** Anyone can build MCQs; it isn't lab work. Display so the seller sees the option, earns nothing. |

#### How — the Grand Slam cap table

| Methods present (excluding MCQ) | Effective cap |
|---|---|
| AI Vision + Script Scoring | **15** (Grand Slam, VM) |
| AI Vision + Scoring API | **15** (Grand Slam, cloud) |
| Script Scoring alone | **15** (VM context — anything goes with shell access) |
| Scoring API alone | **12** (`cfg.SCORING_API_ALONE_CAP`) |
| AI Vision alone | **10** (`cfg.SCORING_AI_VISION_ALONE_CAP`) |
| Nothing (only MCQ or zero methods) | **0** |

**Routing rule.** The Scoring dimension is about HOW we assess, not what's being taught. Subject matter complexity (governance topics, security concepts, eDiscovery workflows) belongs in Pillar 2 Instructional Value, not here.

### 1.4 Teardown (25 points)

#### Why

Every lab has to end cleanly. Environment left behind = cost left behind, orphaned credentials left behind, data left behind, and the next learner contaminating the previous learner's session. Teardown failure is a Day 2 operational cost that outweighs Day 1 convenience.

#### What

**Canonical badges:**

| Badge | Green | Amber | Red |
|---|---|---|---|
| **Datacenter** | Skillable hosts a REAL environment (VM, ESX, OR Container) — teardown is automatic via snapshot revert or container destroy. **Does NOT apply to Simulation.** | — | — |
| **Simulation Reset** | (gray Context only) Simulation session ends with the user session. No teardown work. **Earns ZERO Teardown points** (Frank 2026-04-07). | — | — |
| **Teardown API** | Vendor API covers environment cleanup and deprovisioning | Some teardown API coverage but gaps remain | — |
| **Manual Teardown** | — | — | No teardown mechanism — manual cleanup required between learners |
| **Low Orphan Risk** | Rich teardown API with minor gaps — low residue risk | — | — |
| **Orphan Risk** | — | Partial API, gaps remain — moderate residue risk | — |
| **High Orphan Risk** | — | — | No API or major cleanup gaps — high residue risk |

**The Simulation Reset rule (Frank 2026-04-07).** A Simulation lab for a SaaS web app doesn't have anything to "tear down" in the operational sense, so the historical "Datacenter green for Simulation" rule was misleading — it earned 25 / 25 for Teardown work that didn't happen. Simulation now uses its own `Simulation Reset` gray badge worth zero points. The seller sees Teardown was considered, but credit is not awarded for work that isn't real.

**Orphan Risk is a three-tier spectrum.** `Low Orphan Risk` (green, 0 points) fires when the teardown API is rich but has minor gaps. `Orphan Risk` (amber, -5) fires when there's partial API coverage with meaningful gaps. `High Orphan Risk` (red, -15) fires when there is no API or major cleanup gaps remain. Orphan Risk badges fire alongside `Teardown API` when there's API coverage but with gaps that could leave residue. All three tiers render in the same dimension.

#### How — scoring signals

| Canonical | Green base credit |
|---|---|
| `Datacenter` | +25 (full marks — VM / ESX / Container only) |
| `Simulation Reset` | **0** — display only |
| `Teardown API` | +22 |

**Penalties:**

| Penalty | Deduction |
|---|---|
| `Manual Teardown` | -10 |
| `Low Orphan Risk` | 0 |
| `Orphan Risk` | -5 |
| `High Orphan Risk` | -15 |

Floor: 0.

### Risk Cap Reduction — applies to all Pillar 1 dimensions

#### Why

A dimension can be at full raw credit and still have a real risk attached to it — Trellix Endpoint Security Lab Access was 25 / 25 with a Training License Risk badge, and the perfect score hid the concern. A dimension should never be at full cap when there's a known risk badge. Amber risks shave the effective cap down visibly. Red blockers shave it down harder.

#### What

| Risk type | Cap reduction per badge | Rationale |
|---|---|---|
| **Amber Risk** | **-3** from cap | "Strong with friction to manage." A dimension with one amber risk still reads well above 50%. |
| **Red Blocker** | **-8** from cap | "Must be resolved before we can ship." A dimension with one red lands in mid-amber verdict territory. |

Sourced from `cfg.AMBER_RISK_CAP_REDUCTION` and `cfg.RED_RISK_CAP_REDUCTION`.

#### How

1. Count visible risk badges in the dimension: `amber_count`, `red_count`.
2. Compute the knockdown: `(amber_count × 3) + (red_count × 8)`.
3. `effective_cap = max(dim.weight - knockdown, dim.floor or 0)`.
4. Clamp the raw dimension credit to `effective_cap`.

Linear compounding. Two ambers = -6. Three reds = -24. Hard floor at the dimension's floor (0 for most) prevents pathological negatives. Risk cap reduction is a **cap reduction**, not a deduction — if the raw credit is already below the lowered cap, the knockdown has no further effect.

**Risk cap reduction replaces most old ceiling flags.** `saas_only`, `no_api_automation`, and similar flags are retired — a red Sandbox API badge knocks the Provisioning cap down -8 on its own, and red badges across multiple dimensions compound the effect organically. The old `CEILING_FLAGS` dict is deleted. The only hard caps still enforced by `pillar_1_scorer` via `score_override` are `bare_metal_required` and the Sandbox API red Pillar 1 cap, both documented above in the Provisioning section.

---

## Pillar 2 — Instructional Value (20%)

### Why this Pillar exists

**Instructional Value is the commercial case.** Product Labability tells us *can* we lab this product. Instructional Value tells us *should* we — does this product genuinely warrant hands-on lab experiences, or is it a read-the-manual product whose learners don't need to practice? Combined with Product Labability, Instructional Value makes up the 70% of the Fit Score that's about the product.

### What it measures — four dimensions

| Dimension | Weight | Question |
|---|---|---|
| **Product Complexity** | 40 | Is this product hard enough that someone needs hands-on practice to become competent? |
| **Mastery Stakes** | 25 | What are the consequences of getting it wrong? |
| **Lab Versatility** | 15 | What kinds of high-value hands-on experiences could we build for this product? |
| **Market Demand** | 20 | How big is the worldwide population of people who need to learn this product at hands-on depth? |

Weights sum to 100 within the Pillar.

### Scoring model — rubric, default-positive

**Why rubric.** Domain-specific judgment is not binary. Cybersecurity products are almost always hands-on-appropriate. Social media products almost never are. Between those extremes, the realistic starting point is different for cybersecurity than for CRM than for content management. A canonical badge model can't capture that — the framework needs **category-aware baselines** so the score starts in a realistic place and sculpts up or down from evidence.

**Why default-positive.** The old framework started at zero and demanded the AI *earn* Instructional Value from findings. That produced absurd results — multi-VM cybersecurity platforms scoring 41 / 100 because positive signals couldn't overcome a pessimistic default. The new posture is realistic by default: **most real software has instructional value for the right audience**, and the question shifts from "is there evidence of instructional value?" to "is there any reason this product would NOT have instructional value?"

**What the rubric model means operationally:**

- Every dimension has a **category-aware baseline** drawn from the product's top-level category (Cybersecurity, Cloud Infrastructure, Networking / SDN, etc.). Baselines live in `cfg.IV_CATEGORY_BASELINES`.
- The researcher extracts qualitative `SignalEvidence` records into `InstructionalValueFacts` — truth-only, no strength grading at extract time.
- `rubric_grader.py` — the **narrow Claude-in-Score slice** — makes one focused Claude call per dimension and returns a list of `GradedSignal` records. Each `GradedSignal` carries a `signal_category` (from a fixed per-dimension list), a `strength` tier (`strong` / `moderate` / `weak` / `informational`), a `color`, an `evidence_text`, and a `confidence`.
- `pillar_2_scorer.py` — pure Python — reads the grades + the baseline, adds tier points for positive findings, subtracts named penalty points, applies risk cap reduction from the color counts, and honors the **penalty-visibility rule** (see below).

**Strength tier points (sourced from the rubric definition in `scoring_config.py`):**

- **strong**: the full tier value — typically +6 on a cap-40 dimension, +9 on Mastery Stakes, +5 on Lab Versatility and Market Demand.
- **moderate**: about half of strong — typically +3.
- **weak**: don't emit — too thin to carry its own badge.
- **informational**: 0 points — context-only, renders as gray Context badge.

**Strong signal cap per dimension.** Each dimension caps strong-tier signals at `MAX_STRONG_SIGNALS_PER_DIMENSION = 2` (from `scoring_config.py`). When a dimension receives more than 2 strong-tier graded signals, the 3rd and beyond are downgraded to moderate credit (+3 instead of +6 for Product Complexity, +3 instead of +9 for Mastery Stakes, etc.). This creates differentiation within high-baseline categories (Cybersecurity, Cloud Infrastructure) where every product would otherwise hit the dimension cap. A product with 2 strong + 1 moderate scores differently than one with 3+ strong. Applies to both Pillar 2 and Pillar 3 rubric dimensions. *(Locked 2026-04-13.)*

**Signal categories are fixed per dimension.** The grader picks ONE `signal_category` per finding from the dimension's locked list. Categories outside the list are silently dropped. The AI gets freedom in naming the badge itself (variable, domain-specific, finding-as-name) but not in what the category *means*.

**The penalty-visibility rule — locked 2026-04-07, ported into `pillar_2_scorer` and `pillar_3_scorer` 2026-04-08.**

Named penalties must ALWAYS be visible in the final score, even when positive contributions overflow the dimension cap.

| Math | Formula |
|---|---|
| **Positive total** | `baseline + sum(positive tier credits)` |
| **Penalty total** | `sum(negative penalty deductions)` (already signed negative) |
| **Effective cap** | `max(dim.cap - (amber_count × 3 + red_count × 8), floor)` |
| **Capped positive** | `min(positive_total, effective_cap)` |
| **Final score** | `max(capped_positive + penalty_total, floor)` |

The cap clamps positives **only**. Penalties are subtracted AFTER the clamp so they are always visible in the final score. Under the old buggy math, a -4 penalty on a dimension where positives would have been 30 vs a cap of 25 silently became 25 / 25 — the penalty absorbed into the overflow. Under the correct math, the same dimension scores 25 - 4 = 21. The Trellix Org DNA regression test in `test_pillar_3_scorer.py` gates this against regression.

### 2.1 Product Complexity (cap 40)

**Why it measures hands-on appropriateness, not abstract difficulty.** Complexity here is not "sophisticated" — it's whether hands-on repetition, experimentation, and real-environment interaction are the difference between someone who can use the product and someone who can't. A product is complex in the sense this dimension measures when any of these are true: it requires configuring interrelated components; it has multi-phase workflows; it involves multiple distinct personas; it requires troubleshooting real failure scenarios; it has AI features requiring iterative practice; it has networking topology learned through manipulation; or integration with external systems IS the primary workflow.

**What it does NOT measure.** Not provisioning difficulty (Pillar 1 Provisioning). Not scoring difficulty (Pillar 1 Scoring). Not the cost of failure (Pillar 2 Mastery Stakes). Not whether a market exists (Pillar 2 Market Demand). Not company training infrastructure (Pillar 3).

**Category-aware baseline (sourced from `cfg.IV_CATEGORY_BASELINES`):**

| Category | Baseline | Rationale |
|---|---|---|
| **Cybersecurity** | **28 / 40 (70%)** | Multi-system, cross-role, deep configuration |
| **Cloud Infrastructure** | **28 / 40 (70%)** | Inherently multi-component |
| **Networking / SDN** | **28 / 40 (70%)** | Topology learned by manipulation |
| **Data Science & Engineering** | **28 / 40 (70%)** | Pipelines, tuning, iteration |
| **Data & Analytics** | **26 / 40 (65%)** | Modeling, query tuning |
| **DevOps** | **28 / 40 (70%)** | CI/CD, IaC, config management |
| **AI Platforms & Tooling** | **28 / 40 (70%)** | Prompt / tune / verify cycles |
| **Data Protection** | **26 / 40 (65%)** | Complex multi-layer systems |
| **ERP** | **24 / 40 (60%)** | Deep configuration, financial workflow depth |
| **CRM** | **22 / 40 (55%)** | Workflow depth, but typically shallower configuration |
| **Healthcare IT** | **24 / 40 (60%)** | Regulated workflows, clinical configuration |
| **FinTech** | **24 / 40 (60%)** | Regulated workflows, transaction complexity |
| **Legal Tech** | **22 / 40 (55%)** | Workflow depth, compliance configuration |
| **Industrial / OT** | **24 / 40 (60%)** | Control systems, safety-critical configuration |
| **Infrastructure / Virtualization** | **24 / 40 (60%)** | Multi-component, hypervisor-level depth |
| **App Development** | **22 / 40 (55%)** | IDE / framework depth varies widely |
| **Collaboration** | **18 / 40 (45%)** | SharePoint, Microsoft 365, Teams — administrative depth |
| **Content Management** | **18 / 40 (45%)** | Documentum, Alfresco — workflow depth |
| **Unknown / uncategorized** | **18 / 40 (45%)** | Neutral fallback — triggers the classification review flag |
| **Social / Entertainment** (Facebook, Instagram, TikTok, Netflix, Spotify) | **4 / 40 (10%)** | No professional training market |

**Signal categories (positive):** `multi_vm_architecture`, `deep_configuration`, `multi_phase_workflow`, `role_diversity`, `troubleshooting_depth`, `complex_networking`, `integration_complexity`, `ai_practice_required`, `state_persistence`, `compliance_depth`.

**Signal categories (negative):** `consumer_grade` (red), `simple_ux` (red), `wizard_driven` (amber / red).

### 2.2 Mastery Stakes (cap 25)

**Why it's separate from Product Complexity.** A product can be simple with high stakes (don't press the big red button) or complex with low stakes (a CI/CD pipeline where mistakes cost time but not money). Mastery Stakes asks: **what are the consequences of failing to use this product correctly?** — breach, data loss, compliance failure, malpractice, downtime, reputation damage, regulatory sanction, physical harm. High stakes turn "it's hard to learn" into "they MUST be competent before they touch production."

**Category-aware baseline:**

| Category | Baseline | Rationale |
|---|---|---|
| **Cybersecurity** | **16 / 25 (64%)** | Breach exposure, incident response — definitional stakes |
| **Healthcare IT** | **16 / 25 (64%)** | Patient safety, regulated clinical workflows |
| **FinTech** | **16 / 25 (64%)** | Financial loss, regulatory compliance |
| **Legal Tech** | **16 / 25 (64%)** | Malpractice, compliance consequences |
| **Data Science & Engineering** | **16 / 25 (64%)** | Garbage-in-garbage-out, model integrity |
| **AI Platforms & Tooling** | **16 / 25 (64%)** | Model safety, hallucination risk, deployment stakes |
| **Cloud Infrastructure** | **15 / 25 (60%)** | Data loss, downtime, configuration errors at scale |
| **Networking / SDN** | **15 / 25 (60%)** | Outage impact, topology misconfiguration |
| **DevOps** | **15 / 25 (60%)** | Pipeline failures, deployment risk |
| **Data Protection** | **15 / 25 (60%)** | Data loss, compliance failure |
| **ERP** | **15 / 25 (60%)** | Financial records, business continuity |
| **Industrial / OT** | **15 / 25 (60%)** | Safety-critical systems, physical harm potential |
| **Infrastructure / Virtualization** | **15 / 25 (60%)** | Downtime, resource misconfiguration |
| **Data & Analytics** | **13 / 25 (52%)** | Business-skills layer — dashboards drive decisions |
| **CRM** | **12 / 25 (48%)** | Real consequences, but usually recoverable |
| **Collaboration** | **10 / 25 (40%)** | Low stakes, typically recoverable |
| **Content Management** | **10 / 25 (40%)** | Low stakes, typically recoverable |
| **App Development** | **10 / 25 (40%)** | Stakes depend on what's being built — neutral-moderate |
| **Unknown / uncategorized** | **10 / 25 (40%)** | Neutral fallback |
| **Social / Entertainment** | **2 / 25 (8%)** | No professional stakes |

**Signal categories:** `breach_exposure`, `compliance_consequences`, `data_integrity`, `business_continuity`, `safety_regulated`, `legal_liability`, `reputation_damage`, `financial_impact`.

Strong-tier credit on Mastery Stakes is **+9** (higher than Product Complexity's +6) because a single high-stakes finding can carry more weight in this dimension.

### 2.3 Lab Versatility (cap 15)

**Why it's here.** Lab Versatility is the bridge from Inspector to Designer. It asks: **what lab types could be designed and delivered on Skillable for this product?** This is about the *platform's capability*, regardless of who actually builds the labs (Skillable ProServ, the customer's team, a content partner). The lab-type signals identified here feed Designer as starting points for program recommendations, and they give sellers specific conversational competence points.

**What it measures against — the Lab Type Menu** (from `cfg.LAB_TYPE_MENU`):

Red vs Blue · Simulated Attack · Incident Response · Break/Fix · Team Handoff · Bug Bounty · Cyber Range · Performance Tuning · Migration Lab · Architecture Challenge · Compliance Audit · Disaster Recovery · CTF / Capture The Flag.

A product with Lab Versatility doesn't need to support ALL lab types — it needs to support *some lab type naturally*, where "naturally" means without shoehorning.

**Category-aware baseline:**

| Category | Baseline | Natural lab types |
|---|---|---|
| **Cybersecurity** | **10 / 15 (67%)** | Red vs Blue, Simulated Attack, Incident Response, Cyber Range, CTF |
| **Cloud Infrastructure** | **10 / 15 (67%)** | Migration, Architecture Challenge, DR, Performance Tuning |
| **Networking / SDN** | **10 / 15 (67%)** | Break/Fix, Topology, Performance Tuning, DR |
| **DevOps** | **10 / 15 (67%)** | CI/CD Pipeline, Migration, Break/Fix, Performance Tuning |
| **AI Platforms & Tooling** | **10 / 15 (67%)** | Model Tuning, Pipeline, Architecture Challenge |
| **Data Science & Engineering** | **9 / 15 (60%)** | Pipeline building, Performance Tuning, Break/Fix |
| **Data & Analytics** | **8 / 15 (53%)** | Break/Fix, Compliance Audit, Configuration |
| **Data Protection** | **8 / 15 (53%)** | DR, Compliance Audit, Break/Fix |
| **ERP** | **8 / 15 (53%)** | Workflow, Configuration, Compliance Audit |
| **Healthcare IT** | **8 / 15 (53%)** | Compliance Audit, Workflow, Configuration |
| **FinTech** | **8 / 15 (53%)** | Compliance Audit, Workflow, Configuration |
| **Industrial / OT** | **8 / 15 (53%)** | DR, Break/Fix, Safety Scenario |
| **Infrastructure / Virtualization** | **8 / 15 (53%)** | DR, Migration, Break/Fix, Configuration |
| **App Development** | **8 / 15 (53%)** | Break/Fix, Architecture Challenge, Performance Tuning |
| **CRM** | **7 / 15 (47%)** | Workflow, Compliance Audit, Permission Modeling |
| **Legal Tech** | **7 / 15 (47%)** | Workflow, Compliance Audit, Permission Modeling |
| **Collaboration** | **7 / 15 (47%)** | Workflow, Permission Modeling |
| **Content Management** | **7 / 15 (47%)** | Workflow, Permission Modeling |
| **Unknown / uncategorized** | **7 / 15 (47%)** | Neutral fallback |
| **Social / Entertainment** | **1 / 15 (7%)** | Rarely fits any lab type |

**Signal categories** map directly to `LAB_TYPE_MENU` entries: `adversarial_scenario`, `simulated_attack`, `incident_response`, `break_fix`, `team_handoff`, `bug_bounty`, `cyber_range`, `performance_tuning`, `migration_lab`, `architecture_challenge`, `compliance_audit`, `disaster_recovery`, `ctf`.

Strong = +5. Moderate = +3.

### 2.4 Market Demand (cap 20)

**Why it's derivative.** Market Demand is naturally Product Complexity × Mastery Stakes × Specialist Population Size. Complex, high-stakes products with a large specialist population (cybersecurity professionals, cloud engineers, AI developers) score at the top. Popular consumer products with no specialist training population score near zero. The same number of users doesn't mean the same number of learners — Salesforce has millions of users but thousands of admins, which is who takes the labs.

**Important distinction — user population is not training population.** A product with 2 billion casual users and 200 administrators has a small Market Demand. A product with 5 million specialist professionals who all need deep skills has a massive Market Demand.

**What it measures — the legitimacy check.** Does the outside world validate that training on this product is worth delivering? ATP networks, active cert exams, conference presence, and independent training market (Coursera, Pluralsight, LinkedIn Learning) are strong Market Demand signals. Absence of any of those for a scaled product is a real negative.

**Category-aware baseline:**

| Category | Baseline |
|---|---|
| **Cybersecurity** | **12 / 20 (60%)** |
| **Cloud Infrastructure** | **12 / 20 (60%)** |
| **AI Platforms & Tooling** | **12 / 20 (60%)** |
| **Networking / SDN** | **11 / 20 (55%)** |
| **DevOps** | **11 / 20 (55%)** |
| **Data Science & Engineering** | **10 / 20 (50%)** |
| **Data & Analytics** | **9 / 20 (45%)** |
| **App Development** | **9 / 20 (45%)** |
| **ERP** | **8 / 20 (40%)** |
| **Data Protection** | **8 / 20 (40%)** |
| **Healthcare IT** | **8 / 20 (40%)** |
| **FinTech** | **8 / 20 (40%)** |
| **Industrial / OT** | **8 / 20 (40%)** |
| **Infrastructure / Virtualization** | **8 / 20 (40%)** |
| **CRM** | **7 / 20 (35%)** |
| **Legal Tech** | **7 / 20 (35%)** |
| **Unknown / uncategorized** | **7 / 20 (35%)** |
| **Collaboration** | **6 / 20 (30%)** |
| **Content Management** | **6 / 20 (30%)** |
| **Social / Entertainment** | **0 / 20 (0%)** |

**Why baselines are lower than for Complexity and Stakes.** Market Demand baselines leave room for product-specific differentiation. Microsoft-scale cybersecurity products land at 18–19. Trellix-scale products land at 15–16. Niche products at 12–13. The baseline gives the category ceiling; the product-specific evidence determines where THIS product lands within it.

**Signal categories (positive):** `install_base_scale` (variable data — `~2M Users`), `enterprise_validation`, `geographic_reach`, `cert_body_mentions` (CompTIA / EC-Council / SANS / ISC2 curriculum mentions), `independent_training_market` (Coursera / Pluralsight / LinkedIn Learning counts), `cert_ecosystem`, `competitor_labs`, `funding_growth`, `category_demand`, `ai_signal`.

**Signal categories (negative):**

| Signal | Color | Hit | When it fires |
|---|---|---|---|
| `no_independent_training_market` | Amber Risk | -4 | Fewer than 3 courses on the open market. Cross-pillar with Delivery Capacity. |
| `niche_training_population` | Amber | -2 | Small addressable training market relative to install base. Badge: `Niche Audience`. The product is real but the training population is limited. *(Added 2026-04-12)* |

Strong = +5. Moderate = +3.

**Market Demand must differentiate product-level dominance.** A cybersecurity product from a category leader (CrowdStrike, Palo Alto) should score higher than a similar product from a mid-tier vendor (Trellix, Tanium). The category baseline provides the starting point; the grader must use product-specific evidence (install base scale, independent training market size, cert ecosystem breadth) to differentiate within the category. A perfect 20/20 should be rare — reserved for products with demonstrably massive training demand. *(Locked 2026-04-12)*

---

## Pillar 3 — Customer Fit (30%)

### Why this Pillar exists

**Customer Fit is the organization check.** Even the most labable product with the highest instructional value goes nowhere if the customer isn't a training buyer. Pillar 3 asks whether THIS organization is actually the kind of place Skillable can help — do they invest in training, can they build labs, can they deliver them at scale, and do they partner strategically with outside platforms? Customer Fit is weighted 30% — meaningful but never overriding the product truth.

### What it measures — four dimensions

| Order | Dimension | Weight | Question |
|---|---|---|---|
| **1** | **Training Commitment** | 25 | Have they invested in training? Do they have a heart for teaching? |
| **2** | **Build Capacity** | 20 | Can they create the labs? |
| **3** | **Delivery Capacity** | 30 | Can they get labs to learners at scale? |
| **4** | **Organizational DNA** | 25 | Are they the kind of company that partners strategically? |

Presented in chronological reading order — how a seller naturally thinks about a customer's training maturity. Delivery Capacity is weighted highest (30) because of a share-of-wallet reality: having labs = cost, delivering labs to learners = value. Without delivery infrastructure, labs are a cost center that never reaches the audience.

### Scoring model — rubric with organization-type baselines

Same architectural pattern as Pillar 2, with two adaptations:

1. **Baselines are keyed on organization type**, not product category. Sourced from `cfg.CF_ORG_BASELINES`. Org types used for baseline lookup: ENTERPRISE SOFTWARE, SOFTWARE (category-specific), TRAINING ORG, ACADEMIC, SYSTEMS INTEGRATOR, PROFESSIONAL SERVICES, CONTENT DEVELOPMENT, LMS PROVIDER, TECH DISTRIBUTOR, Unknown. **Note:** these org-type categories are internal scoring labels for baseline selection, not the user-facing company classification badge. The company classification badge shown in the UI is derived from discovered product categories (see `Platform-Foundation.md → Company Classification`). Both coexist — one drives scoring math, the other drives the display.

2. **Customer Fit is per-COMPANY, not per-product.** Every product from the same company must show the same Pillar 3 reading. Enforced by two helpers in `intelligence.py` — `_build_unified_customer_fit(products)` and `_apply_customer_fit_to_products(products, cf)` — that merge per-product Customer Fit blocks using a "best showing wins" rule and broadcast the unified result onto every product before the Pillar 3 scorer runs. See "Pillar 3 Unification" below for the merge rule.

**Research asymmetry — critical for CF dimensions.** Not all Customer Fit dimensions are equally easy to research from outside the firewall. This asymmetry is baked into the penalty philosophy for each dimension:

| Dimension | Research difficulty | Penalty philosophy |
|---|---|---|
| **Training Commitment** | Moderate — customer-facing training is public, employee training is harder to see | Penalize when external training evidence is missing; be cautious about employee-only training |
| **Build Capacity** | **Hard** — internal authoring roles and content-team structures are inward-facing | **Cautious penalties only.** Absence of public evidence is NOT evidence of absence. Only penalize when research finds direct positive evidence of outsourcing or explicit absence of authoring roles. |
| **Delivery Capacity** | **Easy** — ATPs, events, course calendars, cert infrastructure are all public | **Penalize aggressively.** Absence of public evidence IS strong evidence of absence for outward-facing dimensions. |
| **Organizational DNA** | Moderate — partnerships are public, RFP processes and internal culture take more inference | Penalize confidently on well-documented signals; cautiously on inferred signals |

### 3.1 Training Commitment (cap 25)

**Why philosophical, not operational.** Training Commitment asks one question: **does this organization have a heart for teaching?** It's not about lab infrastructure (Build Capacity) or delivery mechanisms (Delivery Capacity). A training catalog that exists is a start. A named customer enablement team, senior training leadership, and programs across multiple audiences (employees + customers + partners) show deeper commitment.

**Breadth of audiences served:**

- **Employees** — do they invest in their own people's skills? Pluralsight / Udemy / LinkedIn Learning contracts + internal programs
- **Customers** — do they invest in their customers' success?
- **Partners** — do they enable the channel, the ATPs, the resellers?
- **End-users at scale** — learner-facing programs that reach millions

An organization that trains ONE audience is making some commitment. An organization that trains customers AND partners AND employees is operating at the highest level. Breadth is as important as depth within any one audience.

**Organization-type baseline:**

| Org type | Baseline |
|---|---|
| **TRAINING ORG** (CompTIA, SANS, EC-Council, Cybrary) | **17 / 25 (68%)** — training IS their business; baseline lowered to leave room for positive signal differentiation |
| **ACADEMIC** (WGU, SLU, community colleges) | **16 / 25 (64%)** — teaching is the mission; calibrated to let breadth-of-audience signals lift the score |
| **CONTENT DEVELOPMENT** (GP Strategies) | **16 / 25 (64%)** — content creation implies training commitment but not always multi-audience breadth |
| **ENTERPRISE SOFTWARE** (Microsoft, SAP, Oracle, Salesforce) | **14 / 25 (56%)** — invest in training but depth varies; positive findings do the differentiating |
| **PROFESSIONAL SERVICES** | **14 / 25 (56%)** — training built into offerings but not always formalized |
| **SOFTWARE** (category-specific — Trellix, Cohesity, Nutanix) | **12 / 25 (48%)** — varies widely; baseline centered to let evidence drive |
| **SYSTEMS INTEGRATOR** (Deloitte, Accenture, Cognizant) | **12 / 25 (48%)** — training in delivery motion but not always customer-facing |
| **LMS PROVIDER** (Cornerstone, Docebo) | **9 / 25 (36%)** — host others' training, rarely train themselves deeply |
| **TECH DISTRIBUTOR** (Ingram, CDW, Arrow) | **7 / 25 (28%)** — distribution-first, training is not core |
| **Unknown / uncategorized** | **10 / 25 (40%)** — conservative default; positive evidence lifts |

**Signal categories (positive):** `customer_enablement_team`, `partner_enablement_program`, `employee_learning_investment`, `multi_audience_commitment` (breadth signal), `cert_exam_active`, `onboarding_program`, `customer_success_investment`, `training_leadership_level`, `training_events_at_scale`, `hands_on_learning_language`, `compliance_training_program`, `training_catalog_present`.

**Signal categories (negative — penalties):**

| Signal | Color | Hit |
|---|---|---|
| `no_customer_training` | Amber Risk | -4 |
| `thin_cert_program` | Amber Risk | -3 |
| `no_customer_success_team` | Amber Risk | -3 |
| `minimal_training_language` | Amber Context | -2 |

Strong = +6. Moderate = +3.

### 3.2 Build Capacity (cap 20)

**Why centered baselines.** Build Capacity is **inward-facing** and genuinely hard to verify from outside research. The AI can find partial evidence (job postings, conference talks, Trailblazer Community posts, vendor university branding) but absence of public evidence doesn't mean internal capacity isn't there. Baselines cluster in the middle so **positive findings do most of the differentiation**, and penalties fire only with direct positive evidence of the negative.

**Why the lowest weight in Pillar 3 (20).** Skillable Professional Services can fill a Build Capacity gap. A company with low Build Capacity but strong Delivery Capacity and Training Commitment is a **ProServ opportunity** — Skillable can build for them. Build Capacity is important but not as structurally blocking as Delivery Capacity.

**What it measures — CREATE roles, not delivery roles.** An instructor who teaches is not Build Capacity; an instructor who also authors labs is. An SME who reviews content for accuracy is not Build Capacity; an SME who writes content is. The strongest signal is `DIY Labs` — the organization is already building hands-on labs today, meaning they understand the value of hands-on training and are investing in it.

**Organization-type baseline:**

| Org type | Baseline |
|---|---|
| **CONTENT DEVELOPMENT** (GP Strategies) | **13 / 20 (65%)** — content creation is the core competency |
| **TRAINING ORG** (CompTIA, SANS, EC-Council, Cybrary) | **12 / 20 (60%)** — training orgs build their own material |
| **ACADEMIC** (WGU, SLU, community colleges) | **11 / 20 (55%)** — faculty create course material but lab authoring varies |
| **PROFESSIONAL SERVICES** | **11 / 20 (55%)** — client-facing delivery often requires custom content |
| **ENTERPRISE SOFTWARE** (Microsoft, SAP, Oracle, Salesforce) | **10 / 20 (50%)** — large vendors have content teams but evidence is inward-facing |
| **SYSTEMS INTEGRATOR** (Deloitte, Accenture, Cognizant) | **10 / 20 (50%)** — build capacity exists but is project-scoped |
| **SOFTWARE** (category-specific — Trellix, Cohesity, Nutanix) | **9 / 20 (45%)** — varies; positive findings differentiate |
| **LMS PROVIDER** (Cornerstone, Docebo) | **8 / 20 (40%)** — platform providers, not content creators |
| **TECH DISTRIBUTOR** (Ingram, CDW, Arrow) | **8 / 20 (40%)** — distribution-first, limited authoring |
| **Unknown / uncategorized** | **9 / 20 (45%)** — conservative default; evidence drives |

**Signal categories (positive):** `diy_labs` (the strongest signal), `content_team_named`, `instructional_designers`, `lab_authors`, `tech_writers`, `product_training_partnership`, `content_partnership`, `instructor_authors_dual_role`, `sme_content_authoring`.

**DIY lab platform — strength AND amber risk.** When the company operates its own lab platform (Qwiklabs for Google, CML for Cisco, iLabs for EC-Council), it is a Build Capacity strength — they CAN build and they understand hands-on value. But it is also an amber Risk signal: the seller is pitching Skillable against an internal solution the company already invested in. Emitted as `diy_labs` amber Risk with evidence naming the specific platform (e.g., "Operates Qwiklabs internally"). The positive `diy_labs` signal and the amber risk coexist — same `signal_category`, different color badges on the same dimension card. *(Locked 2026-04-13.)*

**Signal categories (negative — cautious penalties):**

| Signal | Color | Hit | When it fires |
|---|---|---|---|
| `confirmed_outsourcing` | Amber Risk | -3 | Explicit case studies or press documenting off-the-shelf consumption |
| `no_authoring_roles_found` | Amber Risk | -3 | Zero evidence of ID / lab author / tech writer roles combined with explicit "we use Pluralsight" language |
| `review_only_smes` | Amber Context | -2 | SMEs mentioned only in review / accuracy-validation roles |

Strong = +5. Moderate = +3.

### 3.3 Delivery Capacity (cap 30)

**Why the highest weight in Pillar 3.** Having labs = cost, delivering labs to learners = value. A customer can have perfect Training Commitment and excellent Build Capacity, but if they have no channel to reach learners, the commercial case collapses. Delivery Capacity is where commercial value lives.

**What it measures — three delivery layers that stack (Frank 2026-04-07).** Each layer is a separate fact. A vendor can have any subset or all three. Each deeper layer ADDS bonus points on top of the previous:

| Layer | What it is | How to detect | Example badges |
|---|---|---|---|
| **1. Vendor-Delivered** (base) | Vendor runs training directly. Official ILT, self-paced portal, vendor-run hands-on labs. **One badge** whose evidence text names the modes found. | Search the vendor's training / academy pages for "instructor-led training," "self-paced courses," "on-demand," "lab exercises." | `Vendor-Delivered Training` (single badge; evidence names modes) |
| **2. Third-Party-Delivered** (bonus) | Independent training in the open market AND cert body curricula. **Cross-pillar with Market Demand.** | Search Coursera, Pluralsight, LinkedIn Learning, Udemy for counts. Search CompTIA, EC-Council, SANS, ISC2 curricula for product mentions. | `~15 Pluralsight Courses`, `CompTIA Curriculum`, `No Independent Training` (penalty) |
| **3. Auth-Partner-Delivered** (TOP bonus) | Formal ATP / ALP program. Certified partners delivering vendor training at scale. | Search for "ATP," "Authorized Training Partner," "ALP," "training partner directory." | `Global Partner Network`, `~500 ATPs`, `No Training Partners` (penalty) |

**One fact, one badge.** Layer 1 is always a single `Vendor-Delivered Training` badge whose evidence text names the specific modes (ILT, self-paced, labs, bootcamps, published course calendar). Splitting Layer 1 into three badges for ILT/self-paced/labs is three labels for one fact — a discipline violation.

**Organization-type baseline:**

| Org type | Baseline |
|---|---|
| **TRAINING ORG** (CompTIA, SANS, EC-Council, Cybrary) | **18 / 30 (60%)** — delivery is core but evidence-based signals do the differentiating |
| **LMS PROVIDER** (Cornerstone, Docebo) | **18 / 30 (60%)** — delivery infrastructure is the product |
| **ENTERPRISE SOFTWARE** (Microsoft, SAP, Oracle, Salesforce) | **17 / 30 (57%)** — large vendor delivery channels but depth varies |
| **TECH DISTRIBUTOR** (Ingram, CDW, Arrow) | **17 / 30 (57%)** — wide distribution reach, delivery breadth |
| **SYSTEMS INTEGRATOR** (Deloitte, Accenture, Cognizant) | **16 / 30 (53%)** — delivery through client engagements |
| **PROFESSIONAL SERVICES** | **15 / 30 (50%)** — project-based delivery, not always at scale |
| **SOFTWARE** (category-specific — Trellix, Cohesity, Nutanix) | **14 / 30 (47%)** — varies widely; evidence drives |
| **ACADEMIC** (WGU, SLU, community colleges) | **14 / 30 (47%)** — deliver to enrolled students, limited external reach |
| **CONTENT DEVELOPMENT** (GP Strategies) | **12 / 30 (40%)** — create content, less often deliver at scale |
| **Unknown / uncategorized** | **14 / 30 (47%)** — conservative default; positive evidence lifts |

**Signal categories (positive):** `lab_platform` (variable — Skillable expansion, competitor displacement, `No Lab Platform` greenfield, `DIY Lab Platform` replacement), `atp_network`, `lms_partner`, `lms_other`, `instructor_delivery_network`, `training_events_scale`, `cert_delivery_infrastructure`, `geographic_reach`, `published_course_calendar`, `gray_market`, `lab_build_capability`, `vendor_published_on_third_party`.

**Signal categories (negative — aggressive penalties):**

| Signal | Color | Hit |
|---|---|---|
| `no_training_partners` | Red Blocker | -10 |
| `no_classroom_delivery` | Red Blocker | -10 |
| `no_independent_training_market` | Amber Risk | -4 (cross-pillar with Market Demand) |
| `single_region_only` | Amber Risk | -3 |
| `gray_market_only` | Amber Context | -2 |

**Lab platform naming convention.** The badge IS the platform name — no `Lab Platform:` prefix. `Skillable` (green, customer expansion), `CloudShare` / `Instruqt` / `Skytap` / `Kyndryl` / `ReadyTech` (amber, competitor displacement), `No Lab Platform` (gray Context moderate — greenfield, not weak), `DIY Lab Platform` (gray Context moderate — replacement opportunity).

Strong = +8. Moderate = +4.

### 3.4 Organizational DNA (cap 25)

**Why the most consequential partnership question.** Organizational DNA asks: **if Skillable proposes a strategic relationship to power your hands-on training, will you see it as a strategic partnership or as a procurement line item to squeeze?** Some companies see outside platforms as strategic assets (Salesforce for CRM, Workday for HR, Okta for identity). Other companies see every outside vendor as a cost to control and every engagement as an RFP to run. The first kind of company makes a great Skillable customer. The second kind makes a painful one. Organizational DNA is the cultural version of this question.

**What this dimension does NOT measure:**

| Not this | That belongs to... |
|---|---|
| Technical architecture of their PRODUCT (API openness, modularity) | **Pillar 1** — a routing failure we caught on Trellix |
| "Open Platform Architecture" as a technical claim about the product | Pillar 1 — not DNA |
| Whether their software is cloud-native vs on-prem | Classification metadata (not scoring) |
| "They have partners" | Too shallow — DNA is about the *cultural pattern*, not presence of any one partnership |

**Organization-type baseline (centered because most real organizations have some partnership culture):**

| Org type | Baseline |
|---|---|
| **TRAINING ORG** (CompTIA, SANS, EC-Council, Cybrary) | **15 / 25 (60%)** — partnership culture exists but evidence differentiates |
| **CONTENT DEVELOPMENT** (GP Strategies) | **15 / 25 (60%)** — content partnerships are core to the model |
| **ENTERPRISE SOFTWARE** (Microsoft, SAP, Oracle, Salesforce) | **14 / 25 (56%)** — large vendor ecosystems with established partner programs |
| **PROFESSIONAL SERVICES** | **14 / 25 (56%)** — partnership-oriented by nature of delivery model |
| **SYSTEMS INTEGRATOR** (Deloitte, Accenture, Cognizant) | **14 / 25 (56%)** — multi-vendor partnerships are the business |
| **SOFTWARE** (category-specific — Trellix, Cohesity, Nutanix) | **13 / 25 (52%)** — varies; positive findings differentiate |
| **LMS PROVIDER** (Cornerstone, Docebo) | **13 / 25 (52%)** — platform integration partnerships |
| **ACADEMIC** (WGU, SLU, community colleges) | **13 / 25 (52%)** — academic partnerships exist but are less commercially oriented |
| **TECH DISTRIBUTOR** (Ingram, CDW, Arrow) | **13 / 25 (52%)** — distribution partnerships are transactional, not always strategic |
| **Unknown / uncategorized** | **12 / 25 (48%)** — conservative default; evidence drives |

**Signal categories (positive):** `many_partnership_types`, `strategic_asset_partnerships`, `platform_buyer_behavior`, `formal_channel_program`, `nimble_engagement`, `named_alliance_leadership`.

**Signal categories (negative — penalties):**

| Signal | Color | Hit |
|---|---|---|
| `long_rfp_process` | Amber Risk | -4 |
| `heavy_procurement` | Amber Risk | -3 |
| `build_everything_culture` | Amber Risk | -4 |
| `diy_labs` | Amber Risk | -3 — company operates its own lab platform (Qwiklabs, CML, iLabs); indicates build-everything posture |
| `closed_platform_culture` | Amber Risk | -3 |
| `hard_to_engage` | Red Blocker | -6 |

**Why `Build vs Buy` is retired as a badge.** Historically, `Build vs Buy` was a single badge whose color carried three different findings (Platform Buyer / Mixed / Builds Everything). That violated the finding-as-name discipline — the label communicated nothing without a color legend. The new canonicals are finding-named: `Platform Buyer` (positive via `platform_buyer_behavior`), `Builds Everything` (negative via `build_everything_culture`). Mixed buyer-builder posture doesn't emit — absence of a strong signal is the absence of a badge.

Strong = +6. Moderate = +3.

### Pillar 3 Unification — enforcing per-company consistency

**Why.** Customer Fit measures the organization, not the product. Every product from the same company must show the same Pillar 3 reading. Before this rule landed, Trellix Threat Intelligence Exchange and Trellix Endpoint Security showed different Customer Fit data — Partner Ecosystem amber on one, green on the other — because each product's research surfaced different signals. The organization is the organization. One source of truth.

**What — the merge rule.** Per `signal_category`, pick the best finding across all products using "best showing wins":

1. **Strongest strength tier wins.** `strong` > `moderate` > `weak`.
2. **Within the same strength tier, prefer the most-positive color.** Sourced from `cfg.BADGE_COLOR_POINTS` — higher numeric value means more positive (`green` > `gray` > `amber` > `red`). Define-Once: no hardcoded color order anywhere in the merge logic.
3. **Tiebreak by evidence length.** More grounding wins.

**How.** Enforced in `intelligence.py` by two helpers called at the start of `recompute_analysis` and at the start of `score` for cached-product reloads:

- `_build_unified_customer_fit(products)` — pure function, returns the unified Customer Fit dict from a list of per-product CF blocks
- `_apply_customer_fit_to_products(products, customer_fit)` — broadcasts the unified block onto every product (deep-copied so the per-product math loop has independent refs)

**Phase F — the canonical home is the discovery.** The unified CF is written to `discovery["_customer_fit"]` at every save boundary via `aggregate_customer_fit_to_discovery`, so Inspector, Prospector, and Designer all read it from a single source. `recompute_analysis` reads the Phase F home first and falls back to the merge helper only for legacy analyses whose parent discovery hasn't been stamped yet.

**Pillars 1 and 2 stay per-product.** Product Labability is genuinely about the product. Most of Instructional Value (Product Complexity, Mastery Stakes, Lab Versatility) is also per-product. Only Pillar 3 is fully organizational.

---

## Cross-Pillar Compounding

**Why.** The same fact can legitimately credit more than one Pillar when it answers more than one question. `Multi-VM Lab` in Provisioning (Pillar 1) is *also* strong evidence of `multi_vm_architecture` in Product Complexity (Pillar 2) — it's one fact, two legitimate credits. `~500 ATPs` in Delivery Capacity (Pillar 3) is *also* strong evidence of real Market Demand (Pillar 2) — partners don't exist without skill demand. Cross-pillar compounding honors the fact that evidence from one Pillar sometimes proves something about another.

**What — the locked cross-pillar rules:**

| Fact in one Pillar | Also credits |
|---|---|
| `Multi-VM Lab` (P1 Provisioning) | `multi_vm_architecture` (P2 Product Complexity) |
| `Complex Topology` (P1 Provisioning) | `complex_networking` (P2 Product Complexity) |
| `is_large_lab` (P1 fact) | `deep_configuration` or `state_persistence` (P2 Product Complexity) |
| `atp_alp_program` (P3 Delivery Capacity) | Positive Market Demand (P2) — partners don't exist without skill demand |
| `cert_body_mentions` (P2 Market Demand) | `vendor_published_on_third_party` (P3 Delivery Capacity Layer 2) |
| `independent_training_market` count (P2 Market Demand) | `vendor_published_on_third_party` (P3 Delivery Capacity Layer 2) |
| `training_events_at_scale` (P3 Delivery Capacity) | Positive Market Demand (P2) — events at scale signal real appetite |
| **Negative: fewer than 3 courses on Coursera / Pluralsight / LinkedIn Learning** | `no_independent_training_market` amber in BOTH P2 Market Demand AND P3 Delivery Capacity |
| `multi_fabric_flexibility` (multi-fabric product) | P2 Lab Versatility — more fabrics enable more lab design patterns (deferred to Step 5.5) |

**How.** Cross-pillar compounding is a **rubric grader instruction**, not a math rule. The grader is told to cross-reference facts between pillars at grading time, so the same underlying evidence can produce `GradedSignal` records in multiple dimensions. The per-pillar scorers don't know anything about cross-pillar — they just score whatever grades they're handed. The old `CROSS_PILLAR_RULES` config tuple has been retired; cross-pillar logic now lives in grader prompts, not a data structure.

---

## Fit Score Composition — Technical Fit Multiplier

### Why

A pure 70/30 weighted sum lets a product with weak Product Labability (PL ≈ 20) still score Solid Prospect when Instructional Value and Customer Fit are strong. That's not honest — if we fundamentally cannot lab the product, great instructional signals and a training-mature customer don't recover the situation. Skillable's value proposition is lab-based training. The Technical Fit Multiplier enforces an **asymmetric coupling rule**: weak PL drags IV + CF contribution down. Weak IV or weak CF does NOT drag PL contribution down. A perfectly labable product with weak organizational signals is still a viable deal; a perfectly committed customer with an unlabable product is not.

### What — the multiplier table

From `cfg.TECHNICAL_FIT_MULTIPLIERS`:

| Product Labability score | Orchestration method class | Multiplier | Effect |
|---|---|---|---|
| ≥60 | Any | **1.0** | Full credit — strong product |
| 32–59 | Datacenter (Hyper-V, ESX, Container, Azure VM, AWS VM) | **1.0** | Datacenter protected — VM/ESX/Container products keep full credit |
| 32–59 | Non-datacenter | **0.65** | Meaningful drag — SaaS/cloud with uncertain provisioning |
| 19–31 | Datacenter | **0.75** | Moderate drag even for datacenter |
| 19–31 | Non-datacenter | **0.60** | Significant drag — weak SaaS labability |
| 10–18 | Any | **0.50** | Heavy drag — very weak labability |
| 0–9 | Any | **0.35** | Near-total drag — product is nearly unlabable |

*(Retuned 2026-04-12 from the original 5-row table after Workday validation showed PL 45 non-datacenter was producing Fit 66 instead of ~49.)*

The table is keyed on PL score band × method class. Method class comes from `cfg.DATACENTER_METHODS` — anything in that tuple is "datacenter," anything else (empty string, unknown) is "any." Walk order: method-specific match first, then "any" fallback.

### How

`fit_score_composer.compose_fit_score(fit_score: FitScore, orchestration_method: str) -> None`:

```
multiplier = get_technical_fit_multiplier(pl_score, orchestration_method)

pl_contrib = pl_score × (pl_weight / 100)
iv_contrib = iv_score × (iv_weight / 100) × multiplier
cf_contrib = cf_score × (cf_weight / 100) × multiplier

fit_score.total_override = clamp(round(pl_contrib + iv_contrib + cf_contrib), 0, 100)
fit_score.technical_fit_multiplier = multiplier
```

The multiplier applies ONLY to IV + CF contributions (the "downstream" pillars). PL always contributes at full weight. `FitScore.total` reads `total_override` when set, so the composed value becomes the authoritative Fit Score. Historical note: an earlier version used `max(weighted_sum, pl_score)` as a PL floor — PL could only LIFT the score, never drag it below. Removed 2026-04-07 after the Diligent Boards review (PL=66, IV=33, CF=23 was being pinned at 66 / Solid Prospect instead of 43 / Keep Watch). The 70/30 weighting is the right formula; the floor was fighting the framework. The multiplier restored the asymmetric coupling intent without re-introducing the floor.

---

## ACV Calculation — Rate Tier Lookup

### Why this section is here

The full ACV Potential model — the five consumption motions, the per-motion math, the three-line hero widget, the Define-Once install base rule, and estimation discipline (single numbers, not ranges) — lives in `Platform-Foundation.md → ACV Potential Model`. This document does not duplicate that content. What DOES live here is the operational detail of how the **rate tier** is computed from Pillar 1 facts, because the rate lookup is Pillar-aware and belongs with the scoring math.

### What — the rate tier table

| Delivery path | Triggered by | Rate |
|---|---|---|
| **Cloud labs** | `Runs in Azure`, `Runs in AWS`, `Sandbox API` green | **~$6/hr** (`cfg.CLOUD_LABS_RATE`) |
| **Small VM / Container / Simulation** | `Runs in VM` alone (no Multi-VM / Complex Topology / is_large_lab), `Runs in Container`, `Simulation` | **~$8/hr** (`cfg.VM_LOW_RATE`) |
| **Typical VM** | `Runs in VM` with 1–3 VMs, standard footprint | **~$14/hr** (`cfg.VM_MID_RATE`) |
| **Large or complex VM** | `Multi-VM Lab` OR `Complex Topology` fires on top of `Runs in VM` / `ESX Required`, OR `ProvisioningFacts.is_large_lab` is set | **~$45/hr** (`cfg.VM_HIGH_RATE`) |

Simulation rate is pinned to `VM_LOW_RATE` — Sims are priced the same as VM Low ($8/hr per Frank).

### How

`acv_calculator.py`:

1. Reads `product.orchestration_method`.
2. Looks up the tier name via `cfg.ORCHESTRATION_TO_RATE_TIER` (a dict keyed on lowercase orchestration method → delivery path name).
3. Falls back to `cfg.DEFAULT_RATE_TIER_NAME` when the method is empty or unknown (the everyday admin-lab default — conservatively neither cheap nor pricey).
4. Reads the rate from the matched entry in `cfg.RATE_TABLES`.
5. Computes per-motion annual hours × rate, sums to total ACV, assigns the ACV tier from `cfg.ACV_TIER_HIGH_THRESHOLD` ($250k) and `cfg.ACV_TIER_MEDIUM_THRESHOLD` ($50k).

Rates use `~` to signal estimate. **One number per tier.** Audience is also a single estimated number — not a range. Every input is one number, one number out. Rate ranges and audience ranges both compound noise without adding precision and are forbidden.

### Customer Training adoption by category tier — locked 2026-04-13

For Software and Enterprise Software org types only, Motion 1 adoption is tier-driven rather than a flat 4%. Tiers derive from `CATEGORY_PRIORS` in `scoring_config.py` — the same tiering that feeds Market Demand ACV rate hints, now consolidated to also drive Motion 1 adoption deterministically (no longer just an AI prompt hint).

| Tier | Adoption | Categories |
|---|---:|---|
| **High** | **8%** (`cfg.CUSTOMER_TRAINING_ADOPTION_HIGH`) | Cybersecurity, Cloud Infrastructure, Networking/SDN, Data Science & Engineering, Data & Analytics, DevOps, AI Platforms & Tooling |
| **Moderate** | **4%** (`cfg.CUSTOMER_TRAINING_ADOPTION_MODERATE`) | Data Protection, Infrastructure/Virtualization, App Development, ERP, CRM, Healthcare IT, FinTech, Collaboration, Content Management, Legal Tech, Industrial/OT |
| **Low** | **1%** (`cfg.CUSTOMER_TRAINING_ADOPTION_LOW`) | Social / Entertainment |
| **Unknown** | 4% | Fallback to Moderate |

**Why tier rather than flat 4%:** specialist categories with career-gated training (a Nutanix infrastructure admin, a Splunk analyst, a Kubernetes operator) have roughly 2× the formal-training uptake of general-purpose categories (a Salesforce end user, a SharePoint contributor). Flat 4% was the average across the whole portfolio and systematically undercounted the categories that matter most for Skillable's pipeline. Source: `cfg.CATEGORY_PRIORS` + `cfg.CUSTOMER_TRAINING_ADOPTION_BY_TIER`.

**Scope:** applies to Software and Enterprise Software org types. Wrapper org types (Academic, ILT Training Org, Enterprise Learning Platform, GSI/VAR/Distributor) use their existing org-level overrides in `ACV_ORG_ADOPTION_OVERRIDES` because their adoption dynamics come from delivery model, not product category.

### Audience source by org type — locked 2026-04-13

Software and Enterprise Software org types use `estimated_user_base` as the Motion 1 audience. Wrapper org types use `annual_enrollments_estimate` — a distinct per-program field populated by the researcher specifically for wrapper orgs, representing how many learners the organization actually serves in that program per year.

| Org type | Motion 1 audience field | Source constant |
|---|---|---|
| Software, Enterprise Software | `estimated_user_base` | `cfg.ACV_AUDIENCE_SOURCE_USER_BASE` |
| Industry Authority | `estimated_user_base` with deflation | `cfg.ACV_AUDIENCE_SOURCE_USER_BASE_DEFLATED` |
| Academic, ILT Training Org, Enterprise Learning Platform, GSI, VAR, Tech Distributor | `annual_enrollments_estimate` | `cfg.ACV_AUDIENCE_SOURCE_ANNUAL_ENROLLMENTS` |

Full rationale in `Platform-Foundation.md → Wrapper organizations — product vs. audience`. This document does not duplicate that content.

### Training maturity multipliers — locked 2026-04-13

Researcher-captured signals nudge the baseline adoption rate up or down. Apply to all org types. Multipliers stack multiplicatively, capped at 35% adoption ceiling (`cfg.ACV_TRAINING_MATURITY_ADOPTION_CAP`).

| Condition | Multiplier | Source signal |
|---|---|---|
| ATP program with 50+ partners | 1.5× | `atp_program` |
| Active cert exams for this product | 1.25× | `cert_inclusion` |
| No training programs, no ATPs, no certs | 0.75× | Absence of signals |
| Training license blocked | 0.5× | `training_license = "blocked"` |

Source: `cfg.ACV_TRAINING_MATURITY_MULTIPLIERS`.

### Three-tier open source classification — locked 2026-04-13

Replaces the old binary open source discount. Detection keys off `training_license` plus the presence or absence of training programs, certs, and ATPs.

| Tier | Effective adoption | Multiplier | Detection |
|---|---|---|---|
| Commercial | 4% (baseline) | 1.0× | `training_license` is not `"none"` |
| Open source with commercial training (e.g. MongoDB, Red Hat) | 3% | 0.75× (`cfg.OPEN_SOURCE_WITH_TRAINING_MULTIPLIER`) | `training_license = "none"` AND training programs / certs / ATPs exist |
| Pure open source (no organized training) | 1% | 0.25× (`cfg.OPEN_SOURCE_PURE_MULTIPLIER`) | `training_license = "none"` AND no training programs, certs, or ATPs |

### Industry Authority user base deflation — locked 2026-04-13

Researcher-reported user base numbers for Industry Authorities are inflated — they represent lifetime cert holders, not annual training candidates. Tiered deflation is applied before adoption math.

| Researcher `user_base` | Deflation factor | Rationale |
|---|---|---|
| > 500K | ÷ 10 | Almost certainly lifetime holders |
| 100K – 500K | ÷ 5 | Mix of lifetime and annual |
| < 100K | ÷ 2 | Probably closer to reality for niche certs |

When annual exam volume IS available from the researcher, use that × 3 instead of deflation. Source: `cfg.INDUSTRY_AUTHORITY_DEFLATION_TIERS`.

---

## Cache Versioning — SCORING_LOGIC_VERSION

### Why

Scoring logic evolves. When a Pillar weight changes, a penalty is retuned, a baseline shifts, or a new canonical badge ships, cached analyses scored under the old logic need to be re-scored under the new logic. Leaving old cache in place produces silent score drift — the dossier shows 74 but a fresh run would produce 68, and nobody knows which one to trust.

### What

`cfg.SCORING_LOGIC_VERSION` is a string stamped on every saved analysis and every saved discovery at write time. Format: `"YYYY-MM-DD.short-description"`. Current value: `"2026-04-13.iv-badges-penalties-orphan-mfa"`.

### How

On every cache read:

1. `cfg.is_cached_logic_current(saved_data)` compares the cached version string to the live `SCORING_LOGIC_VERSION`.
2. If they match, the cache is honored — `recompute_analysis` runs its slim ACV-and-verdict pass and the saved pillar scores are trusted.
3. If they differ, the cache is treated as stale — `intelligence.score` forces a fresh Deep Dive on the next load, scoring every product through the current Python path.

**Bump policy.** Any commit that touches `scoring_config.py` (badges, signals, rubrics, baselines, penalties), the per-pillar scorers, `fit_score_composer`, or `rubric_grader` should bump `SCORING_LOGIC_VERSION`. Comment-only changes don't require a bump.

---

## Worked Examples

All examples assume `SCORING_LOGIC_VERSION = "2026-04-13.iv-badges-penalties-orphan-mfa"`. Values come from `scoring_config.py` — nothing is hardcoded in this doc.

### Trellix Endpoint Security (SOFTWARE, Cybersecurity)

**Pillar 1 — Product Labability**

| Dimension | Detail | Score |
|---|---|---|
| Provisioning | `Runs in VM` green + `Multi-VM Lab` strength badge | 30 / 35 (no friction, strength badge is 0-point context) |
| Lab Access | `Identity API` green + `Cred Recycling` green + `Training License` amber | Raw 19+18+8 = 45, cap 25, amber risk reduces cap to 22 → **22 / 25** |
| Scoring | `Script Scoring` green + `AI Vision` green | Grand Slam → **15 / 15** |
| Teardown | `Datacenter` green | **25 / 25** |
| **PL total** | | **92 / 100** |

**Pillar 2 — Instructional Value**

| Dimension | Detail | Score |
|---|---|---|
| Product Complexity | Cybersecurity baseline 28 + Multi-Correlation Engine strong (+6) + Analyst+Automation role_diversity strong (+6) = 40, capped at 40 | **40 / 40** |
| Mastery Stakes | Cybersecurity baseline 16 + Breach Detection Gap strong (+9) = 25, capped at 25 | **25 / 25** |
| Lab Versatility | Cybersecurity baseline 10 + SOC Alert Triage strong (+5) = 15, capped at 15 | **15 / 15** |
| Market Demand | Cybersecurity baseline 12 + Top 5 EDR install base scale (+5) + Active Cert Track (+5) = 22, capped at 20 | **20 / 20** |
| **IV total** | | **100 / 100** |

**Pillar 3 — Customer Fit** (Trellix at the COMPANY level, shared by every Trellix product)

| Dimension | Detail | Score |
|---|---|---|
| Training Commitment | SOFTWARE baseline 12 + Partner Academy strong (+6) + Customer Enablement Team strong (+6) + Multi-Audience Programs strong (+6) = 30, capped at 25 | **25 / 25** |
| Build Capacity | SOFTWARE baseline 9 + Trellix Education Team content_team_named strong (+5) + DIY Labs strong (+5) = 19, capped at 20 | **19 / 20** |
| Delivery Capacity | SOFTWARE baseline 14 + No Lab Platform moderate (+4) + Global Channel Network strong (+8) = 26, capped at 30 + No Training Partners red (-10) risk cap reduction = 20 effective cap, clamp 26 → **20 / 30** |
| Organizational DNA | SOFTWARE baseline 13 + Multi-Type Partnerships strong (+6) + Strategic Alliance Program strong (+6) = 25, capped at 25 | **25 / 25** |
| **CF total** | | **89 / 100** |

**Fit Score composition**

PL 92, IV 100, CF 89, orchestration = Hyper-V (datacenter method class).

- Technical Fit Multiplier lookup: PL 92 is ≥ 60 → multiplier = **1.0**
- PL contrib = 92 × 0.50 = 46.0
- IV contrib = 100 × 0.20 × 1.0 = 20.0
- CF contrib = 89 × 0.30 × 1.0 = 26.7
- **Fit Score = round(92.7) = 93 → Dark Green → Prime Target**

### Diligent Boards (SOFTWARE, Content Management / Governance, SaaS-only)

**Pillar 1 — Product Labability**

| Dimension | Detail | Score |
|---|---|---|
| Provisioning | `Sandbox API` red (no per-learner provisioning API) + `Simulation` gray Context (fallback) → Sandbox API red + Simulation viable cap | Pillar 1 caps at **25** |
| Lab Access | (normally scored, but Pillar 1 is capped at 25 via `score_override`) | (clamped) |
| Scoring | (clamped) | (clamped) |
| Teardown | (clamped) | (clamped) |
| **PL total** | Capped via `score_override` | **25 / 100** |

**Pillar 2** (Content Management category)

| Dimension | Detail | Score |
|---|---|---|
| Product Complexity | CM baseline 18 + Agenda+Voting Workflow moderate (+3) + Committee Role Separation moderate (+3) + Document Permission Tree moderate (+3) = 27 | **27 / 40** |
| Mastery Stakes | CM baseline 10 + Board Privilege Exposure strong (+9) = 19 | **19 / 25** |
| Lab Versatility | CM baseline 7 + Workflow strong (+5) = 12 | **12 / 15** |
| Market Demand | CM baseline 6 + Specialist admin population moderate (+3) = 9 | **9 / 20** |
| **IV total** | | **67 / 100** |

**Pillar 3** Customer Fit — Diligent as a company — assume moderate Training Commitment, moderate Delivery (Layer 1 vendor-delivered, no ATP), Organizational DNA strong. Rough **CF total ≈ 68**.

**Fit Score composition**

PL 25, IV 67, CF 68, orchestration = SaaS (non-datacenter).

- Technical Fit Multiplier lookup: PL 25 is in 19–31, method = non-datacenter → multiplier = **0.60**
- PL contrib = 25 × 0.50 = 12.5
- IV contrib = 67 × 0.20 × 0.60 = 8.0
- CF contrib = 68 × 0.30 × 0.60 = 12.2
- **Fit Score = round(32.7) = 33 → Amber → Keep Watch**

Honest outcome: strong instructional case and decent customer, but the Sandbox API red cap honestly reflects that Skillable can't run per-learner labs on Diligent Boards today.

### IBM (ENTERPRISE SOFTWARE, closed-culture pattern)

**Pillar 3 — Organizational DNA** (one dimension, demonstrating penalty-visibility on a rubric penalty)

| Step | Value |
|---|---|
| ENTERPRISE SOFTWARE baseline | 17 |
| Mix of positive findings | +10 (capped at 25) |
| `Builds Everything` amber (-4) | -4 |
| `Closed Platform` amber (-3) | -3 |
| **Correct math** | positive_total 27, capped at 25, then + (-4) + (-3) = **18 / 25** |
| Old buggy math (pre-2026-04-07) | `min(27 + -4 + -3, 25)` = `min(20, 25)` = 20 → hides one of the penalties |

The 2026-04-07 fix: cap clamps positives only, penalties always visible. Both penalties count toward the final score.

---

## Locked Vocabulary

**Why.** A framework that lets every reader invent their own words ceases to be a framework. The locked vocabulary is the shared language Skillable uses when talking about the platform — internally, in prompts, in docs, in the UI.

**What — the terms and their retired alternatives:**

| Use this | Not this |
|---|---|
| Fit Score | Composite Score / Lab Score |
| Pillar | Dimension (as top-level component) |
| Product Labability | Technical Orchestrability |
| Instructional Value | Product Demand / Workflow Complexity |
| Customer Fit | Customer Motivation / Organizational Readiness |
| Provisioning | Orchestration Method / Gate 1 |
| Lab Access | Licensing & Accounts / Gate 2 / Configure |
| Scoring | Gate 3 |
| Teardown | Gate 4 |
| Product Complexity | Difficult to Master |
| Mastery Stakes | Mastery Matters / Consequence of Failure |
| Lab Versatility | Lab Format Opportunities |
| Market Demand | Market Fit / Market Readiness / Strategic Fit |
| Training Commitment | Training Motivation |
| Organizational DNA | (no prior term) |
| Delivery Capacity | Content Delivery Ecosystem |
| Build Capacity | Content Development Capabilities |
| Content Dev Team | Dedicated Content Dept |
| Content Outsourcing | Outsourced Content Creation |
| DIY Labs | DIY |
| Runs in VM | Runs in Hyper-V *(renamed 2026-04-08)* |
| Pre-Instancing? | Pre-Instancing *(renamed 2026-04-08 to signal it's a suggestion)* |
| No GCP Path | Requires GCP *(replaced 2026-04-08)* |
| Green / Gray / Amber / Red | Pass / Partial / Fail / Yellow |
| Blocker | Red (in badge context) |
| Uneasy | Risk *(color-meaning vocabulary locked 2026-04-08 — "uneasy, needs validation" replaces "risk")* |
| HubSpot ICP Context | Notes / Generic notes field |
| Delivery partners | Delivery channels *(locked 2026-04-12 — "channel" always means sales channel; training delivery uses "delivery partners")* |
| Channel / Sales channel | Delivery channels (when referring to GSIs, VARs, distributors who sell the product) |
| Promising / Potential / Uncertain / Unlikely | Seems Promising / Likely / Uncertain / Unlikely *(discovery tier labels locked 2026-04-12)* |
| Company classification (derived from products) | Enterprise Software / generic single-label classification *(locked 2026-04-12 — classification derived from discovered product categories, not a separate AI judgment)* |
| Flagship / Satellite / Standalone | (no prior term) *(product relationship vocabulary locked 2026-04-12)* |
| Industry Authority | Certification Body / Industry Association / Training & Certification Organization *(locked 2026-04-12 — organizations that define and certify professional competence)* |
| Enterprise Learning Platform | Training Company / E-Learning Company *(locked 2026-04-12 — companies selling massive course catalogs to enterprises)* |
| ILT Training Organization | Instructor-Led Training Company / Training Delivery Company *(locked 2026-04-12 — organizations that deliver instructor-led training on other companies' products)* |

---

## Open Questions — SE Clarification Needed

These are framework questions that need sales-engineer input to finalize. Nothing blocks scoring — the current defaults are honest — but these would sharpen the framework further.

| # | Question | Why it matters |
|---|---|---|
| **SE-1** | **Bare Metal Required** — when evaluating a vendor product, what specific signals tell us "this requires bare-metal hardware orchestration that we can't virtualize"? Examples of products that hit this — what gave it away? | The canonical `Bare Metal Required` red Blocker needs detection signals to fire reliably and not fire spuriously. |
| **SE-2** | **Container Disqualifiers** — we have four documented disqualifiers (dev-use-only image, Windows GUI required, multi-VM network, not container-native in production). Which is the most common practical reason to skip containers? When Windows is needed, is a Windows container ever the right call, or do we always default to a Windows VM? | Pillar 1 has `Runs in Container` as a green / amber / don't-emit canonical; the disqualifier list needs SE input to be sharp. |
| **SE-3** | **Simulation Scorable** — when CAN we score a Simulation lab via AI Vision, and when can't we? Should `Simulation Scorable` ever be a red blocker, or is it always green / amber depending on what's visible on screen? | The `Simulation Scorable` canonical is currently amber-only. The answer determines whether we add a red state and what triggers it. |

---

## Items Requiring Calibration

These need validation against real company data. Current values are best current thinking; Trellix + CompTIA + Microsoft + Diligent Deep Dive runs will tell us whether they're correct.

| Item | Question |
|---|---|
| **Pillar weights (50 / 20 / 30)** | Do these produce the right Fit Scores for known companies? Rebalanced 2026-04-12 from 40/30/30 after Workday/Trellix/Cohesity/Diligent review. |
| **Dimension weights within Pillars** | Do the internal weights rank dimensions correctly? |
| **Score thresholds (80 / 65 / 45 / 25)** | Do these produce the right verdict distribution? |
| **Technical Fit Multiplier ranges** | After seeing a handful of real Trellix-class scores, do the PL score bands and multiplier values need retuning? |
| **Category-aware baselines** (`IV_CATEGORY_BASELINES`) | Do the per-category starting points land where they should for real products? |
| **Org-type baselines** (`CF_ORG_BASELINES`) | Same question at the organization level. |
| **Penalty hit values** | Are the -3 / -4 / -6 / -8 / -10 values proportional to the real harm each signal represents? |
| **ACV rate tiers** ($6 / $8 / $14 / $45) | Do these map to real Skillable rate economics once real analyses land? |
