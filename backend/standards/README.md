# Skillable Intelligence — Standards Library

Platform-level reference material shared across all Intelligence tools
(Inspector, Designer, Prospector). Not tool-specific assets.

## Style Guides

| File | Guide | Source | Format |
|---|---|---|---|
| `style_guides/microsoft-writing-style-guide.md` | Microsoft Writing Style Guide | learn.microsoft.com/style-guide | MD (key principles) |
| `style_guides/apple-style-guide.pdf` | Apple Style Guide | support.apple.com/guide/applestyleguide | PDF (full guide, 3.6 MB) |
| `style_guides/red-hat-documentation-guide.md` | Red Hat Documentation Guide (closely aligned with IBM Style Guide) | redhat-documentation.github.io | MD (key principles) |

**DigitalOcean Technical Writing Guidelines** — not yet captured (JS-rendered page).
**IBM Style Guide** — commercial book, not freely available. Red Hat guide covers this territory.

## Skill Frameworks

*(Pending — see project_tool_checklists.md)*

Planned frameworks:
- NICE Cybersecurity Workforce Framework (NICE NCWF) — NIST
- DoD Cybersecurity Workforce Framework (DoD DCWF)
- DoD 8570 / 8140
- Skills Framework for the Information Age (SFIA)
- Information Technology Infrastructure Library (ITIL 4)
- LinkedIn Skill Framework

## Usage

Designer Phase 3 reads selected style guides and injects content into the
generation context so Neo follows them when writing lab instructions.

Future: `/standards/catalog` API route to serve available standards to any tool.
