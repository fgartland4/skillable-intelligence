# Ops Scripts — Index

Operational tools for maintaining cached data, applying scoring/rubric/ACV
retunes, dedup, and validation. **Every script worth knowing about lives
either in this directory or in `backend/scripts/`.**

If you're searching the repo wondering "is there already a tool for X?" —
start here. If it's not in this table, build it and add it to this table
in the same commit.

---

## How to run

Every script runs from the repo root. Environment is loaded from
`backend/.env` automatically. Most scripts follow the same pattern:

- **Dry run by default** — call without flags to see what would happen
- **`--execute`** (or `--dry-run`) — actually make changes
- **Targeted filters** — most scripts accept `--company NAME` or
  a list of names to scope the run

Read the script's top-of-file docstring for the exact flags.

---

## The scripts

### Scoring / ACV retune

| Script | What it does | Cost | When to use |
|---|---|---|---|
| `scripts/rescore.py` | Re-runs Pillar 1 (pure Python) + Pillar 2/3 rubric graders (Claude) + ACV calculator + Fit Score composer + badge selector on cached analyses. Does NOT re-run researcher — uses cached facts. | Claude calls per rubric dimension (~$0.30–0.50 per company) | After scoring logic OR rubric prompt changes |
| `scripts/rescore_pillars.py` | Lightweight Python-only rescore — reruns pure-Python pillar scorers + fit-score composer against cached facts + rubric grades. **Zero Claude.** Milliseconds per product. | Free | After pillar weights / tier point values / baselines / penalties / Technical Fit Multiplier changes. NOT after rubric text changes. |
| `scripts/stamp_version.py` | Stamps all cached analyses with the current `SCORING_LOGIC_VERSION` so Inspector's cache-versioning check doesn't trigger unnecessary re-research. | Free | After ACV config changes (rates, adoption, hours, deflation) that don't affect pillar math. The ACV is recomputed on page load anyway — this just prevents the version check from over-triggering. |

### Research / discovery refresh

| Script | What it does | Cost | When to use |
|---|---|---|---|
| `scripts/retrofit_discovery_acv.py` | Walks every cached `discovery_*.json` and recomputes `_company_acv` via `acv_calculator.compute_company_acv()`. Flags: `--dry-run`, `--only <company>`, `--include-org-types`, `--exclude-org-types`. Used after ACV logic changes to refresh the corpus without re-research. | ~$0.05 per company (one `audience_grader` call) | After ACV architecture / prompt / rate / harness changes land. Spot-check 5-10 companies with `--only` before running the full sweep. |
| `backend/scripts/run_flagship_deep_dives.py` | Runs a full Deep Dive on each company's flagship product for companies that have no Deep Dive yet. Picks the best-labability-tier + most-popular product per company (Promising preferred; falls through to Potential / Uncertain / Unlikely if no Promising exists). Leaves companies with existing Deep Dives untouched. | ~$2.40 per company | When you want to give every company in the cache at least one real scored product (anchors Prospector in real data, not rough discovery guesses). |

### Dedup / data hygiene

| Script | What it does | Cost | When to use |
|---|---|---|---|
| `scripts/dedup_discoveries.py` | Scans all cached discovery records, groups by normalized company name, auto-merges obvious duplicates (Cisco / Cisco Systems, VMware variants), flags ambiguous cases (different badges or org_types) for human review. The merge rule is locked: cleanest name wins, data union across records, canonical discovery_id preserved, older records archived with `.archived-<ts>.json` suffix. | Free | Periodically, after a big research push or when duplicate clusters become visible. |
| `scripts/merge_companies.py` | Force-merge a specific set of duplicates that the auto-dedup rule can't catch (different normalized names). Typical use: parent/service-line pairs like "Deloitte" / "Deloitte Consulting" / "Deloitte Consulting LLP" or "Grand Canyon University" / "Grand Canyon Education". | Free | When you know two or more records are the same entity but they don't normalize to the same key. The "I know these are the same" escape hatch. |
| `scripts/identify_thin_research.py` | No Claude — pure Python analysis over cached holistic ACV + product list + signals. Surfaces records that look thin (tiny holistic midpoint relative to org-type cohort, low confidence + below-floor midpoint, product count < 2, telltale rationale phrases like "limited research"). Ranked list of candidates for re-research. | Free | Before deciding which companies to re-research. Non-destructive; caller chooses what to do. |

### Hooks / CI

| Script | What it does | When |
|---|---|---|
| `scripts/validate-badge-names.py` | Pre-commit hook that blocks commits introducing legacy badge vocabulary (the "Not this" column from the locked vocabulary in `docs/Badging-and-Scoring-Reference.md`). | Automatic on `git commit` |
| `scripts/session-stop-reminder.py` | Claude Code stop hook — reminds Claude to update `decision-log.md` before the session ends. | Automatic on session close |

---

## Adding a new script

When you build a new operational tool, **add it to this table in the same
commit.** Otherwise future-you and future-Claude will rebuild it three
more times before remembering it exists. That's the whole reason this
file exists.

Docstring at the top of the script should cover:

1. What it does in one sentence
2. When to use it (the triggering situation)
3. Cost (free / per-Claude-call range / per-record range)
4. Usage examples with common flags

Once those are in the docstring, updating this README is a one-minute
copy-paste.
