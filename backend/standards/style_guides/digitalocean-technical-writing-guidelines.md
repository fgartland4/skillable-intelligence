# DigitalOcean Technical Writing Guidelines
# Source: https://www.digitalocean.com/community/tutorials/digitalocean-s-technical-writing-guidelines
# Authors: Hazel Virdó, Brian Hogan — Editor: Caitlin Postal
# License: Creative Commons BY-NC-SA 4.0 — Published 2016, last modified 2022

---

## Style

DigitalOcean articles are written to be:

- **Comprehensive and written for all experience levels** — as clear and detailed as possible without assuming background knowledge. Include every command a reader needs from first SSH connection to final working setup.
- **Technically detailed and correct** — technically accurate, following industry best-practices. Every command gets a detailed explanation including options and flags. Every code block gets a prose explanation of what it does and why.
- **Practical, useful, and self-contained** — at the end, the reader has installed, built, or set up something from start to finish. Cover the topic thoroughly.
- **Friendly but formal** — no jargon, memes, excessive slang, emoji, or jokes. Written for a global audience across language and cultural boundaries.

**Avoid:** "simple," "straightforward," "easy," "simply," "obviously," "just" — these make assumptions about the reader's knowledge and frustrate readers who encounter difficulty.

**Voice:**
- Use second person: "you will configure" not "we will learn" or "I will explain"
- Use first person plural sparingly: "we will examine"
- Use motivational language focused on outcomes: "you will install Apache" not "you will learn how to install Apache"
- No first person singular ("I think…")

**Inclusivity:** Language honors diverse human experiences. Avoid offensive language related to age, disability, ethnicity, gender identity, level of experience, nationality, neurodiversity, race, religion, political affiliation, sexual orientation, socioeconomic status, or technology choices.

---

## Structure

### Procedural tutorial structure:
1. Title (H1)
2. Introduction (H3)
3. Prerequisites (H2)
4. Step 1 — Doing the First Thing (H2)
5. Step 2 — Doing the Next Thing (H2)
6. …
7. Step n — Doing the Last Thing (H2)
8. Conclusion (H2)

### Conceptual article structure:
1. Title (H1)
2. Introduction (H3)
3. Prerequisites (optional) (H2)
4. Subtopic sections (H2)
5. Conclusion (H2)

### Title
- Include the goal of the tutorial, not just the tool used
- Ideal format: `How To <Accomplish a Task> with <Software> on <Distro>`
- Under 60 characters

### Introduction (1–3 paragraphs)
Answer: What is the tutorial about? Why should the reader care? What will the reader do? What will they have accomplished when done? Keep focus on the reader and what they will accomplish.

### Prerequisites
- Exact checklist of what the reader must have or do before starting
- Each point links to an existing tutorial or official documentation
- Be specific — "Familiarity with JavaScript" without a link is insufficient

### Steps
- Each step begins with a level 2 heading
- Procedural step titles: `Step N — Gerund Phrase` (use -ing words)
- Each step has an introductory sentence describing what the reader will do and why
- Each step ends with a transition sentence summarizing what was accomplished and where they're going next
- All commands on their own line in their own code block, preceded by an explanation
- Command output shown in a separate code block labeled "Output"
- Files: introduce with purpose, explain every change before making it, show full context

### Conclusion
- Summarize what the reader accomplished ("you configured" not "we learned how to")
- Describe what the reader can do next: use cases, additional tutorials, external docs

---

## Formatting (Markdown)

### Headers
- H1: Title
- H3: Introduction
- H2: Prerequisites, Steps, Conclusion
- H3 used sparingly; avoid H4
- Step headers use numbers and em-dash: `Step 1 — Installing Nginx`
- Step headers use gerunds (-ing words)

### Inline formatting
- **Bold**: visible GUI text, hostnames/usernames, term lists, emphasis when switching context
- *Italics*: introducing technical terms only
- `Code`: command names, package names, optional commands, file names/paths, example URLs, ports, key presses

### Code blocks
Used for: commands to execute, files/scripts, terminal output, interactive dialogues

- **Do not** include the command prompt (`$` or `#`) in the code block
- Use custom prefix Markdown to distinguish user types:
  - ` ```command ` — non-root user commands
  - ` ```super_user ` — root user commands
  - ` ```custom_prefix(mysql>) ` — custom prompt
- Label code blocks with filenames: `[label filename.js]`
- Label output blocks: `[secondary_label Output]`
- Use `...` (ellipsis with spaces) to indicate omitted sections in file excerpts
- Highlight variables and lines readers must change with `<^>highlighted text<^>`

### Variables
- Default username: `sammy`
- Default hostname: `your_server`
- Default domain: `your_domain`
- Default IP: `your_server_ip`
- For documentation IPs: use `203.0.113.0/24` (public) or `198.51.100.0/24` (private) per RFC-5737

### Admonitions
- `Note:` — additional information, not critical
- `Warning:` — important caution the reader must heed

### Images
- Only for screenshots of GUIs, interactive dialogue, diagrams
- Never for screenshots of code, config files, or copyable output
- Include descriptive alt text
- Include a brief caption
- Use .png format

---

## Terminology

- **Software names:** use the official website's capitalization
- **Multi-server terminology:** use the project's own terms; for abstract discussion use "primary/replica" or "manager/worker"
- **Example URLs:** use `your_domain` not `example.com` to make clear the reader must change it
- **Links:** link to software's home page on first mention
