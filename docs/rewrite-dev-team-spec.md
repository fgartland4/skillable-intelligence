# Rewrite — Skillable Dev Team Specification (As-Provided)

> **Source.** This document captures the development team's proposed architecture and technology stack for the rewrite of the Skillable Intelligence Platform, as shared with Frank on 2026-04-19. It is the **input specification** the rewrite is built against. Session 2's Requirements Document turns this spec into the implementation-level plan.
>
> **Status.** Locked as the target architecture. The execution model is: Frank + Claude rewrite the application to this specification in Session 3+; the dev team handles production Azure provisioning, CI/CD, B2C configuration, and deployment once the app is ready.

---

## Changes Required to Conform to the Design Framework & Tech Stack

### Backend — Python/Flask → Node.js/Express/TypeScript

| Current | Target | Impact |
|---|---|---|
| Python 3.11 + Flask | Node.js + Express + TypeScript | Full backend rewrite |
| Jinja2 server-side rendering | React SPA with API backend | Routes become REST endpoints (`/api/` prefix) |
| JSON files on disk (`storage.py`) | Redis for settings/cache, encrypted at rest (AES-256-GCM) | New persistence layer |
| `ANTHROPIC_API_KEY` via env vars | `.env` defaults → Redis overrides → UI settings panel | Config management rearchitecture |
| No auth | Azure B2C (prod) + mock login (dev) via `useAuth()` hook | Auth layer added |
| SSE streaming (single EventSource) | Express SSE or WebSocket equivalent | Streaming reimplementation |

### Frontend — Vanilla JS → React/TypeScript/Ant Design

| Current | Target | Impact |
|---|---|---|
| Vanilla JS + CSS | React + TypeScript + Vite 7.x | Full frontend rewrite |
| No component library | Ant Design 6.x + `@ant-design/icons` | All UI components replaced |
| Custom modals (Shared Search Modal) | Ant Design Modal, Drawer, Popconfirm patterns | Modal system redesign |
| Custom progress/decision UI | Ant Design Progress, Steps, Spin components | UX pattern alignment |
| No theming | Dark/light mode via `ThemeContext` + `getThemeColors(isDark)` + `ConfigProvider` | Full theme system |
| Custom layout | Header (64px) / Sidebar (220px) / Content Area pattern with Ant Design `Menu` | Layout restructuring |
| Custom tables for Prospector results | Ant Design `Table` with typed columns, sort, filter, pagination | Table standardization |

### Visual Identity Changes

- **Colors:** Adopt the Skillable green palette (`#1a6b45` dark / `#0a3e28` light primary)
- **Status colors:** Map Verdicts and scoring tiers to `#52c41a` / `#faad14` / `#ff4d4f` / `#d9d9d9`
- **Typography:** `system-ui` font stack, Ant Design `Typography` components for all text
- **Spacing:** 24px content padding, 16px gutters, 8px inline spacing via `Space`
- **Cards:** All Pillar cards, Seller Briefcase sections, and metric displays wrapped in Ant Design `Card`
- **Metric boxes:** Fit Score, ACV Target, Pillar scores use `Statistic` component with color-coded values

### Structural Changes

| Area | Change |
|---|---|
| Inspector Hero section | Fit Score + ACV as `Statistic` in `Row/Col` grid with `Card` containers |
| Pillar cards (70/30 layout) | `Row gutter={16}` with `Col` spans, badges as Ant Design `Tag` components |
| Prospector batch table | Ant Design `Table` with sortable columns, `Tag` for verdicts, built-in pagination |
| In-app documentation modals | Ant Design `Modal` (720px width) replacing custom `?` icon modals |
| Excel export | Keep `openpyxl` equivalent on Node.js (e.g., `exceljs`) |
| Charts (if any scoring visualizations added) | Chart.js + `react-chartjs-2` with `chartjs-plugin-annotation` |
| RBAC UI | `usePermissions()` hook, role `Tag` in user dropdown, disabled states with `Alert` banners |

### What Stays Conceptually the Same

- **Intelligence Layer logic** (scoring, research, badges) — rewritten in TypeScript but same architecture
- **Three-tool structure** (Inspector, Prospector, Designer)
- **`scoring_config.py` → `scoringConfig.ts`** as single source of truth
- **Pillar → Dimension → Signal hierarchy**
- **Claude API integration** (swap `anthropic` Python SDK for `@anthropic-ai/sdk`)
- **Serper API** for web search

### Summary

This is a full-stack rewrite from Python/Flask/Vanilla JS to **Node.js/Express/React/TypeScript/Ant Design**, preserving the Intelligence Layer's scoring logic and architecture while adopting the Skillable standard UI framework, auth model, config management, and visual identity.

---

## Open Questions to Resolve with Dev Team (Session 2)

1. **Azure AI Foundry.** Dev team mentioned Foundry as the hosting path for Claude API calls. Does Foundry support Anthropic Claude models natively today, or do we route direct to `api.anthropic.com` for now? If Foundry, auth becomes Azure Managed Identity / service principal instead of an API key in env.

2. **Redis vs SQL.** Spec says Redis for settings/cache. Frank's earlier recollection was Azure SQL. Is Redis the full persistence layer (including discovery/analysis JSON documents), or is there a secondary data store planned for entity data?

3. **Auth roles model.** Spec mentions `usePermissions()` and role `Tag`s — what roles does Skillable's identity system support? What maps to "admin / seller / marketer / sales engineer / content author"?

4. **Integration with existing Skillable systems.** Does the rewrite need to call into existing Skillable APIs (product catalog, customer CRM, HubSpot, etc.)? If so, those integration surfaces need to be identified for the Requirements Document.

5. **Ant Design 6.x specifically.** That's a specific version — confirm it's what Skillable's internal apps are on, or whether we should match a different version if their component library has custom extensions.

6. **Testing framework.** Jest or Vitest? Which does the dev team standardize on for Node.js + React code at Skillable?

7. **Deployment pipeline.** What CI/CD pattern does Skillable use for Node.js apps on Azure App Service? GitHub Actions? Azure DevOps Pipelines?

8. **Logging / observability.** App Insights for logging? What log schema does the dev team expect?

---

## What's in the Repo vs. What's in Session 1's Chat vs. What Session 2 Produces

| Artifact | Where it lives |
|---|---|
| Dev team spec | **This doc** (`docs/rewrite-dev-team-spec.md`) |
| Rewrite plan index | `docs/rewrite-plan.md` (Session 1 — if not yet, Session 2 creates) |
| Platform Foundation (current architecture) | `docs/Platform-Foundation.md` |
| ACV framework v2 | `docs/Platform-Foundation.md` + `docs/acv-framework-reference.md` |
| 5 Hard Rules | `docs/collaboration-with-frank.md` (top section) |
| Session handoff | `docs/handoff-to-next-claude.md` |
| Decision log | `docs/decision-log.md` |
| Codebase audit (current state inventory) | Session 2 deliverable: `docs/rewrite-codebase-audit.md` (doesn't exist yet) |
| Requirements Document (forward-looking spec) | Session 2 deliverable: `docs/rewrite-requirements.md` (doesn't exist yet) |
| Behavior tests (structural equivalence) | Session 2 or 3 deliverable: `backend/tests/test_rewrite_equivalence.py` (doesn't exist yet) |
| TypeScript codebase | Session 3+ deliverable |
