# Prospector Background Batch Processing — Design Spec

**Status:** Spec complete, ready to build
**Aligned:** 2026-04-13

---

## The Problem

Running a Prospector batch takes over the entire app. The user can't use Inspector, can't view researched companies, can't do anything until the batch finishes. For large batches (50–100 companies), this means 15–45 minutes of dead time.

## The Solution

Batches run in the background. The user stays on the Prospector home page (or navigates anywhere). A compact Batch Status Panel on the Prospector home page shows all active and recent batches with live progress updates.

---

## UX — Batch Status Panel

Lives below the input form on the Prospector home page. Always visible when there are batches to show.

| Column | Content | Behavior |
|---|---|---|
| **Status** | Colored dot + label: Running / Complete / Failed | Animated pulse on running dot |
| **Description** | "12 companies · discovery only" or "8 companies · discovery + Deep Dive" | Set at batch creation, never changes |
| **Started** | Relative time — "2 min ago", "1 hr ago" | Updates on page load, not live |
| **Progress** | "7 of 12" when running, "12 of 12" when complete | Live update via SSE |
| **Est. remaining** | "~4 min left" when running, blank when complete | Computed from progress + estimated per-company time |
| **Actions** | "View Results →" when complete. "Cancel" when running. | View links to `/prospector/results/<batch_id>`. Cancel kills the thread. |

---

## Behavioral Rules

| Rule | Detail |
|---|---|
| **No redirect on submit** | Clicking "Run Prospector →" adds a row to the panel and stays on the same page. No modal, no page change. |
| **Navigate freely** | User can go to Inspector, come back, panel shows current state. Panel reads from batch metadata on page load + picks up SSE for running batches. |
| **Multiple concurrent batches** | Each batch is an independent row. Backend already supports this (each batch has its own `job_id` and thread). |
| **Panel shows last 10 batches** | Complete batches stay visible until displaced. Gives the user a history without navigating away. |
| **SSE per running batch** | Each running row opens its own SSE connection to `/prospector/progress/<job_id>`. Updates the progress count and est. remaining in real time. |
| **Page reload resilience** | Batch metadata (status, description, started, progress, batch_id) is persisted to the batch JSON file. On page load, the panel reads all recent batches and renders their current state. Running batches reconnect SSE. |

---

## Backend Changes

| Change | Detail |
|---|---|
| **Batch metadata** | Extend `_save_prospector_batch` to include `status`, `description`, `started_at`, `company_count`, `deep_dive`, `progress` alongside results. Write metadata at batch start (status=running), update progress during, write final state (status=complete/failed) at end. |
| **List recent batches** | New helper `_list_recent_batches(limit=10)` — reads batch files, returns metadata sorted by `started_at` descending. |
| **Progress endpoint stays the same** | `/prospector/progress/<job_id>` still publishes SSE. The front-end consumer changes (row update instead of modal), but the backend contract is identical. |
| **Cancel endpoint** | New route `/prospector/cancel/<job_id>` — sets a cancellation flag the batch thread checks between companies. |
| **Submit returns JSON** | POST to `/prospector/run` returns `{ok: true, job_id: "...", batch_id: "..."}` instead of rendering `prospector_running.html`. The front-end JS handles adding the row and connecting SSE. |

---

## Front-End Changes

| Change | Detail |
|---|---|
| **Remove `prospector_running.html`** | No longer needed — no full-screen progress page. |
| **Prospector home gains Batch Status Panel** | Rendered from `_list_recent_batches()` on page load. JS connects SSE for any running batches. |
| **Submit handler changes** | Form submit intercepted by JS. POST via fetch, get JSON back. Add row to panel, connect SSE. No page navigation. |
| **Panel row JS** | Each running row: connect SSE, update progress count, compute est. remaining, swap to "Complete" + "View Results →" on `done:` event. |

---

## What Doesn't Change

- SSE contract (`status:` / `done:` / `error:`)
- Batch processing logic in `run_batch` thread
- Results page (`/prospector/results/<batch_id>`)
- Export routes
- The Standard Search Modal — still used by Inspector discovery and Deep Dive. Only Prospector batch moves to background processing.
