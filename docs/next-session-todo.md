# Next Session — Todo List

**Last updated:** 2026-04-15 (environment cleanup session)

**What happened this session (2026-04-15):**

| Item | Status |
|---|---|
| Worktree cleanup | **Done.** Deleted `claude/elated-mccarthy` branch (local + remote). `claude/competent-feistel` worktree exited and cleaned. |
| A11y branch assessed | **Done.** `elated-mccarthy` had untested a11y work (never merged, never run against live app). Deleted branch; wrote detailed redo instructions in §1a below. |
| Worktree default | **Known issue.** Claude Code desktop defaults worktree checkbox to ON. No setting to change the default (open issue anthropics/claude-code#27616). Uncheck manually each session. |

**What happened prior session (2026-04-14):**

| Item | Status |
|---|---|
| `~/.claude/CLAUDE.md` rewritten | **Done.** Small pointer + hard rules only. No duplicated content. |
| Repo `CLAUDE.md` cleaned | **Done.** Project-specific rules only. Points to `docs/collaboration-with-frank.md` as single source of truth. |
| Memory files deleted | **Done.** All 5 memory files removed from local `~/.claude/projects/`. |
| Settings fixed | **Done.** `bypassPermissions` set in both global and project settings. |
| Dead files removed | **Done.** `storage/`, `wireframe.html`, `discovery_v1_backup.txt`. |

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

---

## §1a — Accessibility Pass (redo from scratch)

**Context:** A previous worktree session (`elated-mccarthy`) attempted a11y work but was never merged or tested against the running app. That branch was deleted 2026-04-15. The concepts were sound but the implementation was untested. Below are the exact gaps to fix, fresh, with the Flask app running and verified in-browser.

**Important:** Do the full startup sequence first. Run the app. Test each change in the browser as you go — do not batch untested changes.

### Known bugs (fix first — these are broken right now)

| Bug | File | What's wrong | Fix |
|---|---|---|---|
| `--sk-accent-pale` self-reference | `tools/shared/templates/_theme.html:78` | Value is `var(--sk-accent-pale)` — references itself. Breaks `.t-po` (Potential tier badge) and `.badge-deploy-green`. | Set to `#5fe5b0` (10.4:1 contrast on dark bg). Verify both badge types render in the browser. |
| `--sk-text-dim` fails AA | `_theme.html:31` | Current `#4a7060` is ~3.0:1 on dark bg. Needs 4.5:1 for AA normal text. | Change to `#6b9585` (4.97:1). Check muted labels across Inspector and Prospector pages. |
| `--sk-text-faint` fails AA | `_theme.html:62` | Current `#4a5550` is ~2.15:1. | Change to `#868f8a` (5.01:1). Check any "faint" text elements. |

### Accessibility infrastructure to add (after bugs are fixed)

| Item | WCAG ref | Where | What to do |
|---|---|---|---|
| `--sk-modal-accent` | 1.4.3 Contrast | `_theme.html` | Add `--sk-modal-accent: #136945` (6.7:1 on white). In `_search_modal.html`, anywhere `--sk-accent` is used on the white `.is-docs` modal surface, swap to `--sk-modal-accent`. There are ~6 usages (eyebrow, section headings, hover borders, back-to-top link). |
| `:focus-visible` outlines | 2.4.7 Focus Visible | `_theme.html` | Add universal `:focus-visible { outline: 2px solid var(--sk-accent); outline-offset: 2px; }` and suppress plain `:focus` outlines. Inside `.is-docs` modals, override outline color to `--sk-modal-accent`. |
| `prefers-reduced-motion` | 2.3.3 | `_theme.html` | Add `@media (prefers-reduced-motion: reduce)` that sets `animation-duration: 0.01ms`, `transition-duration: 0.01ms`, `scroll-behavior: auto` on `*, *::before, *::after`. |
| `.sr-only` utility | 1.3.1 | `_theme.html` | Standard visually-hidden class (1px clip rect pattern). Needed by skip link and heading hierarchy items below. |
| Skip-to-main link | 2.4.1 Bypass Blocks | `_nav.html` | Add `<a href="#main-content" class="skip-to-main">Skip to main content</a>` as first child. Style: visible only on `:focus-visible`, positioned absolute. Add `id="main-content" tabindex="-1"` to the main content container on every page template (Inspector: 4 pages, Prospector: 6 pages). |
| Modal ARIA | 4.1.3 Status Messages | `_search_modal.html` | Add `aria-live="polite"` to `#searchModalStatus`, `#searchModalCounter`, `#searchModalStages`. Add `role="progressbar"` + `aria-valuemin/max/now` to progress track (keep `aria-valuenow` in sync at open/creep/done in JS). Add `role="alert" aria-live="assertive"` to `#searchModalError`. |
| Modal focus trap | 2.4.3 + 2.1.2 | `_search_modal.html` | On modal open: capture `document.activeElement`, move focus to cancel button. While open: Tab cycles within modal only. On close: restore focus to captured element. Use a MutationObserver on the backdrop's `is-open` class to handle all open/close paths. |
| Heading hierarchy | 1.3.1 + 2.4.6 | Various templates | Company name in `_company_header.html` should be `<h1>` not `<span>`. Pages without visible h1 get a `.sr-only` h1. |
| Form labels | 1.3.1 + 3.3.2 | Prospector templates | Every `<input>` needs an associated `<label>`. Add `sr-only` labels where the visual design already communicates purpose. Add `aria-describedby` for hint text. |
| Expand/collapse keyboard access | 2.1.1 + 4.1.2 | Prospector templates | Any `onclick` expand/collapse `<div>` needs `role="button" tabindex="0" aria-expanded="false"` + `onkeydown` for Enter/Space + toggle `aria-expanded` on click. |

### After implementing — verify live

- Tab through every page with keyboard only. Every interactive element should have a visible focus ring.
- Open and close the search modal with keyboard. Focus should trap inside and restore on close.
- Check the Potential tier badge and deploy-green badge render correctly (the `--sk-accent-pale` fix).
- Resize browser to check no contrast regressions on dark surfaces.

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
