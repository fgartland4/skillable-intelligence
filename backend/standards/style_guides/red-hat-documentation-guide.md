# Red Hat Supplementary Style Guide for Product Documentation
# (Closely aligned with IBM Style Guide)
# Source: https://redhat-documentation.github.io/supplementary-style-guide/
# Open source — contributions welcome via GitHub pull request

## Purpose

Establishes consistent, clear, and cohesive writing standards for Red Hat product documentation.
Supplements the IBM Style Guide. Where this guide conflicts with IBM Style, this guide takes precedence.
Hierarchy: IBM Style Guide → Red Hat Supplementary Guide → product-specific guidelines.

## Voice and Tone

- Clear, direct, and professional — not conversational
- Contractions generally discouraged except in specifically conversational contexts
- Second person ("you") for the reader; avoid "the user" or "one"
- Active voice preferred; passive acceptable when the actor is unknown or irrelevant

## Conscious Language

Avoid terms with historical or social bias. Use these replacements:

| Avoid | Use instead |
|---|---|
| blacklist / whitelist | blocklist / allowlist |
| master / slave | primary / secondary, leader / follower, source / replica |
| sanity check | confidence check, coherence check |
| native feature | built-in feature, core feature |

## Capitalization

- Sentence-style capitalization for headings and titles (first word + proper nouns only)
- Optimal heading length: 3–11 words
- Non-breaking space between "Red" and "Hat" in all instances

## Structure

- Lead-in sentence required before every list, table, or code block
- Prerequisites section required where applicable
- Short description (1–3 sentences) required for every topic module
- Sections should be scannable: short paragraphs, clear headings

## Admonitions

Use sparingly. Each type has a specific purpose:

- **Note** — additional information that isn't critical
- **Tip** — helpful but optional suggestion
- **Important** — information the reader must understand to proceed correctly
- **Caution** — potential for data loss or unintended consequence
- **Warning** — potential for system damage or irreversible action

## Code and Technical Content

- Separate command input and output into distinct code blocks — never combine
- Do not use callouts on code blocks; use surrounding text or a definition list to explain
- Specify the language for syntax highlighting on every code block
- Show root privilege with `#` prompt; non-root with `$` prompt
- IP address formatting: use `192.0.2.0/24` range for examples (IANA documentation range)
- YAML: use `...` (ellipsis) only when explicitly required by the YAML spec

## Formatting

- Bold for UI elements the user interacts with
- Code font for commands, file names, paths, values, options, placeholders
- Use product name attributes/variables — never hardcode version numbers in body text
- Numbered lists for sequential procedures; bulleted lists for non-sequential items

## Accessibility

- Do not rely on color alone to convey information
- All images require descriptive alt text
- Heading hierarchy must be logical (H1 → H2 → H3; no skipping levels)
- Tables require header rows; avoid merged cells where possible

## Pronouns

- Use "they/their" as singular neutral third person
- Animate objects (users, administrators): "who" / "they"
- Inanimate objects (servers, systems): "that" / "it"
