# Next Session — Todo List

**Last updated:** 2026-04-14 late evening (project organization session)

**What happened this session:**

| Item | Status |
|---|---|
| `~/.claude/CLAUDE.md` rewritten | **Done.** Small pointer + hard rules only. No duplicated content. |
| Repo `CLAUDE.md` cleaned | **Done.** Removed duplicated startup sequence and collaboration rules. Project-specific rules only. Points to `docs/collaboration-with-frank.md` as single source of truth. |
| Memory files deleted | **Done.** All 5 memory files removed from local `~/.claude/projects/` — content was redundant with repo docs. |
| Settings fixed | **Done.** `bypassPermissions` set in both global and project settings. `settings.local.json` cleared of junk rules. |
| Dead files removed | **Done.** `storage/` (empty dir), `wireframe.html` (orphaned prototype), `backend/prompts/discovery_v1_backup.txt` (backup — git handles this). |
| Orphaned worktree | **Not done.** `git worktree prune` failed — OneDrive lock. Try again next session. |

---

## §1 — START HERE NEXT SESSION

**Architecture cleanup: move tool code out of the intelligence layer.**

`backend/` currently mixes intelligence layer code with tool-layer code. Two files need to move:

| File | What it is | Move to |
|---|---|---|
| `backend/app.py` | Flask routes for Inspector, Prospector, Designer | `tools/` (tool-layer code) |
| `backend/designer_engine.py` | Designer-specific logic | `tools/designer/` (tool-layer code) |

After this move, `backend/` becomes purely the intelligence layer. This enforces layer discipline physically — if it's in `backend/`, any tool can call it; if it's in `tools/`, it's tool-specific.

**Before moving anything:**
1. Do the full three-pass startup sequence from `docs/collaboration-with-frank.md`
2. Review all import paths in `app.py` and `designer_engine.py` to understand the blast radius
3. Confirm the plan with Frank before touching any files
4. Run all 118 tests before AND after to verify nothing breaks

**Also try again:** `git worktree prune` to clean the orphaned `elated-mccarthy` worktree.

---

## §2 — Then resume prior work

### Force-refresh Commvault and Trellix

- **Commvault** — force-refresh discovery. Current cache only has 2 products; should have more.
- **Trellix** — confirm merge resolution fix works correctly in the UI after restart.

### Validate 10 diverse ACV numbers with Frank

The full 549-record ACV retrofit (shipped 2026-04-14) completed cleanly, but Frank has not yet done a human pass. This is the gate before Marketing gets a CSV export.

**Suggested 10-company spot-check (mix of org types + sizes):**

| Company | Org type | Expect |
|---|---|---|
| CompTIA | Industry Authority (saturated) | ~$5M (current) — 1.3x cap binding |
| SANS Institute | Industry Authority (saturated) | ~$624k-$810k |
| Skillsoft | Enterprise Learning Platform (saturated) | ~$5.5M-$7.2M |
| Microsoft | Software (mid) | ~$22M-$30M — hard cap binding |
| Cisco (known customer view) | Software (first-year) | Sharp up from $255k |
| Deloitte | Systems Integrator (very-early) | ~$12M-$22M |
| Multiverse | ILT Training Org (early) | ~$350k-$950k (finally above floor) |
| Parkway School District | K-12 (Pattern C deferred) | ~$18k-$55k — EXPECTED low |
| Nutanix | Software prospect | ~$6M-$12M |
| GP Strategies | Content Development (partnership) | "Partnership" chip, no dollar range |

**After validation:** CSV export to Marketing.

### Prospector UX fixes (identified 2026-04-14)

| # | Issue | Expected behavior |
|---|---|---|
| **UX-1** | View Results — no loading indicator | Visual spinner or progress indicator |
| **UX-2** | Export CSV — no visual feedback | Button changes state during export |
| **UX-3** | Batch results tab — no column sorting | Click column header to sort |
| **UX-4** | Batch results tab — no search/filter | Search filter for company names |
| **UX-5** | Sticky header | Pin tab bar and action buttons to top of page |

### Badge-to-Score Consistency Investigation

Badges are not consistently defending the scores they accompany. This is a pipeline investigation, not a badge selector problem. See `docs/roadmap.md` for full detail.

---

## Backlog

| Item | Why deferred |
|---|---|
| **Pattern C — K-12 district budget-signal audience** | Structural work (~1 day). Parkway has a ~$750k CTE/PD budget line that never enters the math. |
| **Pattern G — parent/subsidiary entity dedup** | Manual merge via `scripts/merge_companies.py` when needed. |
| **LLPA-class federating associations** | Rare pattern. Punted. |
| **Lightweight Pillar rescore for rubric-text changes** | `rescore_pillars.py` handles weight/tier/baseline/penalty changes. Text changes still need Claude calls. |

---

## Full Priority List

**See `docs/roadmap.md`** — the single consolidated inventory of everything active, backlog, decisions needed, and done.
