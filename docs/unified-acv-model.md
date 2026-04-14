# Unified ACV Model — All Organization Types

**Status:** In progress — aligned with Frank 2026-04-13
**Applies to:** Both discovery-level AND Deep Dive ACV. Same constants, two depths of input.

---

## Principle

One formula: `Audience × Adoption × Hours × Rate`

Same constants in `scoring_config.py` drive both discovery and Deep Dive. The Deep Dive is sharper because the audience numbers are per-product and the rate comes from orchestration method. But adoption and hours are identical at both levels. Define-Once.

Training maturity multipliers from researcher data nudge adoption up or down from the baseline — same pattern applies to all org types.

---

## 1. Software Companies (the baseline) — LOCKED

| Motion | Audience | Adoption | Hours | Rate |
|---|---|---|---|---|
| Customer Training | Product users (training pop) | 4% | 2 | From deployment model |
| Partner Training | Channel partner SEs | 15% | 5 | From deployment model |
| Employee Training | Company's product-facing employees | 30% | 8 | From deployment model |
| Certification (PBT) | Annual exam sitters | 100% | 1 | From deployment model |
| Events | Event attendees | 30% | 1 | From deployment model |

**Three-tier open source classification:**

| Tier | Effective adoption | Detection |
|---|---|---|
| Commercial | 4% (baseline) | training_license is not "none" |
| Open source with commercial training | 3% | training_license = "none" AND (training programs OR certs OR ATPs exist) |
| Pure open source | 1% | training_license = "none" AND no training programs, certs, or ATPs |

**Training maturity multipliers (apply to all org types):**

| Condition | Multiplier | Source signal |
|---|---|---|
| ATP program with 50+ partners | 1.5× | atp_program |
| Active cert exams for this product | 1.25× | cert_inclusion |
| No training programs, no ATPs, no certs | 0.75× | absence of signals |
| Training license blocked | 0.5× | training_license = "blocked" |

---

## 2. Academic (Universities / Schools) — LOCKED

| Motion | Label | Audience | Adoption | Hours |
|---|---|---|---|---|
| Student Training | Students in tech programs | install_base | **25%** | **15** |
| Faculty & Staff Development | Faculty + staff in tech depts | employee_subset | 30% | 8 |
| Campus Events | If applicable | events | 30% | 1 |

**Key decisions:**
- Course Exams removed — bundled into Student Training (exams are part of tuition, not separate)
- 25% adoption = ~half of enrolled students are in a lab course in any given year, ~90% of those complete labs → ~45% effective, but 25% accounts for the fact that not all courses have labs yet
- 15 hours = realistic semester lab consumption including practice labs outside class
- Training maturity multipliers apply (same as software)

**Benchmarks:** WGU ~$4.7M (90K students), GCU ~$1.7M (32.5K students). Both validated against real Skillable revenue.

---

## 3a. Industry Authorities (CompTIA, EC-Council, SANS, ISACA) — LOCKED

**User base deflation (researcher numbers are inflated — lifetime holders, not annual candidates):**

| Researcher user_base | Deflation factor | Rationale |
|---|---|---|
| > 500K | ÷ 10 | Almost certainly lifetime holders |
| 100K – 500K | ÷ 5 | Mix of lifetime and annual |
| < 100K | ÷ 2 | Probably closer to reality for niche certs |

When annual exam volume IS available from researcher, use that × 3 instead of deflation.

| Motion | Label | Audience | Adoption | Hours |
|---|---|---|---|---|
| Training Participants | Cert prep students | Deflated user_base | **5%** | **10** |
| Certification (PBT) | Exam sitters | Deflated training pop ÷ 3 | **100%** | **1** |
| Events | If applicable | Event attendees | 30% | 1 |

**Key decisions:**
- Partner Training removed — ATPs are delivery channels, not a separate audience. Training participants are already counted regardless of delivery channel.
- Employee Training removed — the org's own employees aren't a meaningful lab audience.
- 5% adoption (slightly above software baseline) because cert seekers are motivated.
- 10 hours — cert prep is intensive, structured lab time.

**Benchmarks:** CompTIA ~$5.8M, EC-Council ~$2.2M. Both validated against real Skillable revenue (~$5M and ~$2M).

---

## 3b. Enterprise Learning Platforms (Pluralsight, Skillsoft, Coursera Business) — LOCKED

**Benchmark:** Skillsoft (includes Global Knowledge acquisition — ~60/40 on-demand/ILT split) ~$5.5M/year. Pluralsight — no benchmark available, estimated ~$2.5M.

| Motion | Label | Audience | Adoption | Hours |
|---|---|---|---|---|
| Platform & ILT Learners | Technology subscribers + classroom students | install_base | **3%** | **3** |
| Events | If applicable | events | 30% | 1 |

**Key decisions:**
- One blended motion instead of splitting on-demand vs ILT — the researcher can't reliably report these separately
- Label "Platform & ILT Learners" tells the seller both audiences are included
- 3% adoption — most platform learners are video-only, the small fraction who engage with labs drives revenue
- 3 hours — average across on-demand (1-2 hrs) and ILT (15+ hrs) weighted toward the larger on-demand population
- Training maturity multipliers apply — platforms with strong ILT (Skillsoft/Global Knowledge) get nudged up via signals
- Companies where ILT IS the whole business → classified as ILT Training Org, not Enterprise Learning Platform

**Benchmarks:** Skillsoft ~$5.0M (4M learners × 3% × 3hrs × $14), Pluralsight ~$2.5M (2M × 3% × 3hrs × $14). ✓

---

## 3c. ILT Training Organizations (New Horizons, QA) — LOCKED

**Benchmark:** QA ~$350K current revenue, ~$700K ACV potential.

| Motion | Label | Audience | Adoption | Hours |
|---|---|---|---|---|
| Classroom Students | Students per year in tech classes | install_base | **25%** | **18** |
| Instructor Training | Instructors who need product skills | employee_subset | 30% | 8 |
| Events | If applicable | events | 30% | 1 |

**Key decisions:**
- 25% adoption = percentage of courses that currently have Skillable labs (not all courses have labs yet)
- 18 hours = intensive multi-day classroom format (4-5 day courses with heavy lab time)
- Instructor Training separate motion — instructors need product skills too
- Highest per-learner consumption of any org type

**Benchmark:** QA at ~12K students: 12K × 25% × 18hrs × $14 = $756K — right at ~2x current revenue (growth potential). ✓

---

## 4. GSIs / VARs / Distributors — LOCKED

**Benchmark:** Accenture — early relationship, ~$2.8M estimated ACV potential for internal consultant training. Client-side opportunity (Phase 2 — Accenture becomes a lab builder for their clients) is the bigger long-term play but too variable to model reliably. Noted as upside in the Seller Briefcase, not in the ACV number.

### 4a. GSIs (Accenture, Deloitte, Cognizant)

| Motion | Label | Audience | Adoption | Hours |
|---|---|---|---|---|
| Internal Consultants | Practitioners in practice areas | install_base (practice headcount) | **5%** | **8** |
| Events | Internal summits, client events | events | 30% | 1 |

### 4b. VARs (regional technology consultancies)

| Motion | Label | Audience | Adoption | Hours |
|---|---|---|---|---|
| Internal Practitioners | Practice area headcount | install_base | **5%** | **8** |
| Events | If applicable | events | 30% | 1 |

Same model as GSIs — same business structure at smaller scale.

### 4c. Technology Distributors (CDW, Ingram, Arrow)

| Motion | Label | Audience | Adoption | Hours |
|---|---|---|---|---|
| Internal Practitioners | Services arm headcount | install_base | **3%** | **5** |
| Events | If applicable | events | 30% | 1 |

Lower adoption and hours — training is emerging for distributors, not core.

**Key decisions across all three:**
- Partner Training and Employee Training removed as separate motions — the internal practitioners ARE the audience, one motion covers it
- Client-side opportunity acknowledged but not modeled (too variable, noted as Seller Briefcase content)
- Training maturity multipliers apply (same as software)
- The researcher reports practice area headcount for GSIs (Accenture AWS Practice ~60K consultants), total technical staff for VARs, services arm headcount for distributors

**Benchmark:** Accenture: ~500K total consultants across practices × 5% × 8hrs × $14 = $2.8M. ✓

---

## Implementation Plan

Once all org types are locked:

1. Update `scoring_config.py` with unified constants (adoption overrides, hours overrides, deflation tiers)
2. Update `_build_prospector_row` in `app.py` (discovery-level ACV) to use all org-type overrides
3. Update `acv_calculator.py` (Deep Dive ACV) to match — should already align via shared constants
4. Update researcher prompts if needed (especially for Industry Authority annual numbers)
5. Update Platform-Foundation.md with the unified model
6. Update Badging-and-Scoring-Reference.md with the operational detail
7. Run validation: CompTIA, EC-Council, WGU, GCU, Pluralsight, Skillsoft, Accenture — verify all land in range
