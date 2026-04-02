# Skillable Intelligence — Standards Library

Platform-level reference material shared across all Intelligence tools
(Inspector, Designer, Prospector). Not tool-specific assets.

---

## Style Guides

| File | Guide | Source | Format |
|---|---|---|---|
| `style_guides/microsoft-writing-style-guide.md` | Microsoft Writing Style Guide | learn.microsoft.com/style-guide | MD (key principles) |
| `style_guides/apple-style-guide.pdf` | Apple Style Guide | support.apple.com/guide/applestyleguide | PDF (full guide, 3.6 MB) |
| `style_guides/red-hat-documentation-guide.md` | Red Hat Documentation Guide (closely aligned with IBM Style Guide) | redhat-documentation.github.io | MD (key principles) |
| `style_guides/digitalocean-technical-writing-guidelines.md` | DigitalOcean Technical Writing Guidelines | digitalocean.com/community/tutorials | MD (full guide, CC BY-NC-SA 4.0) |

**IBM Style Guide** — commercial book, not freely available. Red Hat guide covers this territory and is noted as such in the UI.

---

## Skill Frameworks

| File | Framework | Status |
|---|---|---|
| *(pending)* | NICE Cybersecurity Workforce Framework (NICE NCWF) | Not yet captured — NIST source |
| *(pending)* | DoD Cybersecurity Workforce Framework (DoD DCWF) | Not yet captured |
| *(pending)* | DoD 8570 / 8140 | Not yet captured |
| *(pending)* | Skills Framework for the Information Age (SFIA) | Not yet captured |
| *(pending)* | Information Technology Infrastructure Library (ITIL 4) | Not yet captured |
| *(pending)* | LinkedIn Skill Framework | Not yet captured |

---

## How Standards Drive Phase 3 Generation (Designer)

Standards are injected into the Phase 3 system prompt context when the user has selected them in Preferences.

### Style Guides — injection logic (in `designer.html`, buildContext for Phase 3)

1. **Named guides** (Microsoft, Apple, Red Hat, DigitalOcean) — injected by name:
   ```
   Style guide(s) to follow strictly:
   - Microsoft Writing Style Guide
   - DigitalOcean Technical Writing Guidelines
   ```
   Claude's training data includes all four guides, so it applies their voice, terminology,
   capitalization, formatting rules, and admonitions without requiring the file content re-sent.
   Apple is the least reliably indexed; wiring file content is recommended (see Roadmap below).

2. **Custom style guide** — user uploads a file; text content (up to 6,000 chars) is injected
   verbatim into context as the primary writing authority:
   ```
   Custom style guide content (follow these rules when writing instructions):
   [file content]
   ```

### Skill Frameworks — injection logic (in `designer.html`, buildContext for Phase 3)

1. **Primary framework** — single selection stored as `p.primary_framework` (string). Injected first
   with the highest-priority label:
   ```
   Primary skill framework (align ALL activity skill tags to this taxonomy first):
   - NICE Cybersecurity Workforce Framework (NICE NCWF)
   ```

2. **Additional frameworks** — multi-selection stored as `p.skill_frameworks` (array). Injected after
   primary with a secondary label:
   ```
   Additional skill frameworks (use for secondary tagging and cross-mapping):
   - Skills Framework for the Information Age (SFIA)
   - ITIL 4
   ```

3. **Custom framework** — user uploads a file; text content (up to 4,000 chars) is injected verbatim.
   Role-labelled based on whether it was selected as primary or additional:
   ```
   Primary custom framework taxonomy (align all activities to this):
   [file content]
   ```

### Reliability by framework

| Framework | Training data reliability | File content available |
|---|---|---|
| Microsoft Writing Style Guide | High | Yes (MD) |
| DigitalOcean Technical Writing Guidelines | High | Yes (MD) |
| Red Hat Documentation Guide | High | Yes (MD) |
| Apple Style Guide | Moderate | Yes (PDF — not yet served to context) |
| NICE NCWF | High | No — pending |
| SFIA | High | No — pending |
| ITIL 4 | High | No — pending |
| DoD DCWF | Moderate | No — pending |
| DoD 8570 / 8140 | Moderate | No — pending |
| LinkedIn Skill Framework | Moderate | No — pending |

---

## Roadmap — Standards as a Platform Service

### [ ] Serve file content into context (closes the "name only" gap)
Build `GET /standards/style-guides/<slug>` and `GET /standards/skill-frameworks/<slug>` routes
that read the local markdown/PDF files and return their text content. Wire Designer's Phase 3
context builder to fetch and inline the content alongside the name for every selected standard.

Priority order:
1. Apple Style Guide (PDF) — moderate training reliability; file is on disk, just not being served
2. DoD DCWF + DoD 8570/8140 — lower training reliability; need files captured first
3. All others — lower priority (high training reliability already)

### [ ] Capture skill framework content files
Source and store taxonomy content for each framework in `skill_frameworks/`:
- NICE NCWF — NIST publishes a spreadsheet of Work Roles, Task IDs, and KSAs (freely available)
- DoD DCWF — DoD publishes a similar role/KSA spreadsheet
- DoD 8570/8140 — baseline qualification tables (freely available)
- SFIA — summary taxonomy available; full guide requires license
- ITIL 4 — practice summaries available; full guide requires license
- LinkedIn Skill Framework — publicly queryable via API (requires app registration)

### [ ] `/standards/catalog` API route
`GET /standards/catalog` — returns JSON catalog of all available standards with slug, display name,
type (style_guide / skill_framework), and whether file content is available. Enables any tool
(Inspector, Designer, Prospector) to query available standards without hardcoding lists.

---

## Usage

Designer Phase 3 reads selected style guides and frameworks from `state.preferences` and injects
them into the generation context so Neo follows them when writing lab instructions.

Future: `/standards/catalog` API route to serve available standards to any tool.
