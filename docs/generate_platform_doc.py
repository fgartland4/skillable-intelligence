#!/usr/bin/env python3
"""
Generate Skillable Intelligence Platform briefing Word document.
Audience: Skillable executive leadership team.
WHY / WHAT / HOW structure. Follows Skillable document standards.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCS_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(DOCS_DIR, "Skillable-Intelligence-Platform.docx")
LOGO_PATH   = r"C:\Users\Frank.Gartland\OneDrive - Skillable\Sales Enablement\Keep\z-Skillable Logos\Skillable Logo\Default@4x.png"
ICON_PATH   = os.path.join(DOCS_DIR, "ai-moment-icon.png")

# ── Colors — Skillable brand palette (confirmed 2026-03-31) ──────────────────
DARK_GREEN     = RGBColor(0x13, 0x69, 0x45)   # #136945
DARK_GREEN_HEX = "136945"
PURPLE         = RGBColor(0x70, 0x00, 0xFF)   # #7000FF
PURPLE_HEX     = "7000FF"
PURPLE_LIGHT   = "F0E8FF"                     # very light purple tint for callout bg
DARK_TEXT      = RGBColor(0x1A, 0x1A, 0x1A)
WHITE          = RGBColor(0xFF, 0xFF, 0xFF)
GRAY           = RGBColor(0x60, 0x60, 0x60)
PAGE_GRAY      = RGBColor(0x88, 0x88, 0x88)
ROW_ALT        = "F0F5F2"
FONT_NAME      = "Calibri"


# ── Typographic quotes ────────────────────────────────────────────────────────

def smartify(text):
    """Convert straight quotes to typographic (curly) quotes."""
    import re
    # Double quotes: opening after space/start, closing before space/end/punctuation
    text = re.sub(r'(?<=[(\s\u2014])"(?=\S)', '\u201c', text)   # opening after space/dash/paren
    text = re.sub(r'^"(?=\S)', '\u201c', text)                   # opening at line start
    text = re.sub(r'"(?=[\s.,;:!?)\u2014]|$)', '\u201d', text)  # closing before space/punct/end
    text = re.sub(r'"', '\u201c', text)                          # remaining opens
    # Single quotes / apostrophes
    text = re.sub(r"(?<=\w)'(?=\w)", '\u2019', text)             # contractions (don't, it's)
    text = re.sub(r"(?<=\s)'(?=\S)", '\u2018', text)             # opening after space
    text = re.sub(r"'(?=[\s.,;:!?]|$)", '\u2019', text)         # closing
    return text


# ── XML helpers ───────────────────────────────────────────────────────────────

def set_cell_background(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_margins(cell, val=50):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side in ["top", "left", "bottom", "right"]:
        m = OxmlElement(f"w:{side}")
        m.set(qn("w:w"), str(val))
        m.set(qn("w:type"), "dxa")
        tcMar.append(m)
    tcPr.append(tcMar)


def set_paragraph_spacing(paragraph, before=0, after=0):
    pPr = paragraph._p.get_or_add_pPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), str(before))
    spacing.set(qn("w:after"), str(after))
    pPr.append(spacing)


def add_bottom_border(paragraph, color_hex=DARK_GREEN_HEX, size=8):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)


def make_run(paragraph, text, size_pt=10, bold=False, italic=False, color=None):
    run = paragraph.add_run(smartify(text))
    run.font.name = FONT_NAME
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    return run


def page_break(doc):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 0, 0)
    run = p.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._r.append(br)


# ── Document setup ─────────────────────────────────────────────────────────────

def setup_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width  = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin   = Inches(0.85)
    section.right_margin  = Inches(0.85)
    section.top_margin    = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.header_distance = Inches(0.35)
    section.footer_distance = Inches(0.35)
    return doc, section


# ── Header ────────────────────────────────────────────────────────────────────

def add_header(section):
    header = section.header
    header.is_linked_to_previous = False
    for p in header.paragraphs:
        p._element.getparent().remove(p._element)

    p = header.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_spacing(p, 0, 0)
    add_bottom_border(p)
    run = p.add_run()
    run.add_picture(LOGO_PATH, width=Inches(1.1))


# ── Footer ────────────────────────────────────────────────────────────────────

def page_num_fld(paragraph, instrText):
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    r1 = OxmlElement("w:r")
    rPr1 = OxmlElement("w:rPr")
    rFonts1 = OxmlElement("w:rFonts"); rFonts1.set(qn("w:ascii"), FONT_NAME); rFonts1.set(qn("w:hAnsi"), FONT_NAME)
    sz1 = OxmlElement("w:sz"); sz1.set(qn("w:val"), "16")
    color1 = OxmlElement("w:color"); color1.set(qn("w:val"), "888888")
    rPr1.extend([rFonts1, sz1, color1])
    r1.extend([rPr1, fldChar_begin])

    r2 = OxmlElement("w:r")
    rPr2 = OxmlElement("w:rPr")
    rFonts2 = OxmlElement("w:rFonts"); rFonts2.set(qn("w:ascii"), FONT_NAME); rFonts2.set(qn("w:hAnsi"), FONT_NAME)
    sz2 = OxmlElement("w:sz"); sz2.set(qn("w:val"), "16")
    color2 = OxmlElement("w:color"); color2.set(qn("w:val"), "888888")
    rPr2.extend([rFonts2, sz2, color2])
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = instrText
    r2.extend([rPr2, instr])

    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    r3 = OxmlElement("w:r")
    rPr3 = OxmlElement("w:rPr")
    rFonts3 = OxmlElement("w:rFonts"); rFonts3.set(qn("w:ascii"), FONT_NAME); rFonts3.set(qn("w:hAnsi"), FONT_NAME)
    sz3 = OxmlElement("w:sz"); sz3.set(qn("w:val"), "16")
    color3 = OxmlElement("w:color"); color3.set(qn("w:val"), "888888")
    rPr3.extend([rFonts3, sz3, color3])
    r3.extend([rPr3, fldChar_end])

    paragraph._p.extend([r1, r2, r3])


def gray_run(paragraph, text):
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts"); rFonts.set(qn("w:ascii"), FONT_NAME); rFonts.set(qn("w:hAnsi"), FONT_NAME)
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "16")
    color = OxmlElement("w:color"); color.set(qn("w:val"), "888888")
    rPr.extend([rFonts, sz, color])
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    r.extend([rPr, t])
    paragraph._p.append(r)


def add_footer(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    for p in footer.paragraphs:
        p._element.getparent().remove(p._element)
    p = footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_spacing(p, 0, 0)
    gray_run(p, "Page ")
    page_num_fld(p, " PAGE ")
    gray_run(p, " of ")
    page_num_fld(p, " NUMPAGES ")


# ── Content helpers ───────────────────────────────────────────────────────────

def add_title(doc, title, subtitle):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 0, 40)
    make_run(p, title, size_pt=18, bold=True, color=DARK_GREEN)
    p2 = doc.add_paragraph()
    set_paragraph_spacing(p2, 0, 80)
    add_bottom_border(p2)
    make_run(p2, subtitle, size_pt=11, italic=True, color=GRAY)


def h1(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 120, 40)
    make_run(p, text, size_pt=13, bold=True, color=DARK_GREEN)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 100, 30)
    make_run(p, text, size_pt=11, bold=True, color=DARK_GREEN)
    return p


def body(doc, text, after=60):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 0, after)
    make_run(p, text, color=DARK_TEXT)
    return p


def body_bold(doc, text_parts, after=60):
    """text_parts: list of (text, bold) tuples"""
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 0, after)
    for text, bold in text_parts:
        make_run(p, text, bold=bold, color=DARK_TEXT)
    return p


def bullet(doc, text, after=40):
    p = doc.add_paragraph(style="List Bullet")
    set_paragraph_spacing(p, 0, after)
    # Clear default run and add styled one
    for run in p.runs:
        run.text = ""
    make_run(p, text, color=DARK_TEXT)
    return p


def bullet_bold(doc, label, rest, after=40):
    p = doc.add_paragraph(style="List Bullet")
    set_paragraph_spacing(p, 0, after)
    for run in p.runs:
        run.text = ""
    make_run(p, label, bold=True, color=DARK_TEXT)
    make_run(p, rest, color=DARK_TEXT)
    return p


def section_note(doc, text, after=60):
    """Italic note paragraph."""
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 40, after)
    make_run(p, text, italic=True, color=GRAY)
    return p


def add_table(doc, headers, rows):
    """Full-width table: dark green header, alternating rows."""
    col_count = len(headers)
    table = doc.add_table(rows=1 + len(rows), cols=col_count)
    table.style = "Table Grid"

    # Total width 9792 DXA (~6.8")
    total_dxa = 9792
    col_width = total_dxa // col_count

    # Header row
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        set_cell_background(cell, DARK_GREEN_HEX)
        set_cell_margins(cell, 50)
        for p in cell.paragraphs:
            p._element.getparent().remove(p._element)
        p = cell.add_paragraph()
        set_paragraph_spacing(p, 0, 0)
        make_run(p, h, bold=True, color=WHITE)
        cell._tc.get_or_add_tcPr()
        # Set column width
        tcW = OxmlElement("w:tcW")
        tcW.set(qn("w:w"), str(col_width))
        tcW.set(qn("w:type"), "dxa")
        cell._tc.get_or_add_tcPr().append(tcW)

    # Data rows
    for r_idx, row_data in enumerate(rows):
        row = table.rows[r_idx + 1]
        bg = ROW_ALT if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell_text in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 50)
            for p in cell.paragraphs:
                p._element.getparent().remove(p._element)
            p = cell.add_paragraph()
            set_paragraph_spacing(p, 0, 0)
            make_run(p, smartify(cell_text), color=DARK_TEXT)

    # Spacing after table
    p_after = doc.add_paragraph()
    set_paragraph_spacing(p_after, 0, 60)


def remove_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    tblBorders = OxmlElement("w:tblBorders")
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "none")
        tblBorders.append(b)
    tblPr.append(tblBorders)


def set_cell_width(cell, dxa):
    tcPr = cell._tc.get_or_add_tcPr()
    tcW = OxmlElement("w:tcW")
    tcW.set(qn("w:w"), str(dxa))
    tcW.set(qn("w:type"), "dxa")
    tcPr.append(tcW)


def set_cell_left_border(cell, color_hex, size=18):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), str(size))
    left.set(qn("w:space"), "0")
    left.set(qn("w:color"), color_hex)
    tcBorders.append(left)
    tcPr.append(tcBorders)


def ai_moment(doc, text):
    """AI Moment callout: purple icon left, label + italic text right, light purple tint."""
    p_pre = doc.add_paragraph()
    set_paragraph_spacing(p_pre, 50, 0)

    table = doc.add_table(rows=1, cols=2)
    remove_table_borders(table)

    # ── Icon cell ──
    icon_cell = table.rows[0].cells[0]
    set_cell_background(icon_cell, PURPLE_LIGHT)
    set_cell_width(icon_cell, 504)          # ~0.35"
    set_cell_left_border(icon_cell, PURPLE_HEX, size=18)
    set_cell_margins(icon_cell, 60)
    for p in icon_cell.paragraphs:
        p._element.getparent().remove(p._element)
    p_icon = icon_cell.add_paragraph()
    p_icon.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p_icon, 20, 0)
    run = p_icon.add_run()
    run.add_picture(ICON_PATH, width=Inches(0.26))  # noticeable but subtle

    # ── Content cell ──
    content_cell = table.rows[0].cells[1]
    set_cell_background(content_cell, PURPLE_LIGHT)
    set_cell_width(content_cell, 9288)      # remainder of 9792
    set_cell_margins(content_cell, 80)
    for p in content_cell.paragraphs:
        p._element.getparent().remove(p._element)

    p_label = content_cell.add_paragraph()
    set_paragraph_spacing(p_label, 10, 8)
    make_run(p_label, "AI Moment", size_pt=8, bold=True, color=PURPLE)

    p_text = content_cell.add_paragraph()
    set_paragraph_spacing(p_text, 0, 10)
    make_run(p_text, smartify(text), size_pt=9.5, italic=True, color=PURPLE)

    p_post = doc.add_paragraph()
    set_paragraph_spacing(p_post, 0, 60)


# ── Content sections ──────────────────────────────────────────────────────────

def write_why(doc):
    h1(doc, "WHY — The Problem No Other Tool Solves")

    h2(doc, "We Are a Platform, Not a Product")
    body(doc, "Most B2B companies sell a product. Their go-to-market challenge is identifying organizations that have the budget, the pain point, and the authority to buy. Firmographic signals — company size, industry, growth stage, technology stack — are meaningful proxies. A company that fits the profile is a prospect.")
    body(doc, "Skillable sells a platform. That changes the qualification question entirely.")
    body(doc, "We are not asking whether a company values training. We are asking whether a company's products can be orchestrated into hands-on labs — whether Skillable can technically deliver for them, whether their products are complex enough that labs create genuine skill-building value, and whether their organization has the maturity to build and sustain a lab program.")
    body(doc, "These are not questions about the company. They are questions about the product. And they cannot be answered with firmographic data.")
    body_bold(doc, [
        ("This is the gap Intelligence fills. Every other tool in our stack — ZoomInfo, 6sense, HubSpot, LinkedIn Sales Navigator — evaluates companies. ", False),
        ("Intelligence evaluates products.", True),
        (" It is the only platform in our stack capable of answering the question that actually determines whether a prospect can become a Skillable customer.", False),
    ])
    ai_moment(doc, "Assessing whether a company's products have the deployment model, API surface, marketplace presence, and technical architecture that Skillable can orchestrate takes an experienced SE hours per company. Intelligence does it in minutes, across a list of hundreds — researching marketplace listings, API documentation, GitHub repositories, Docker images, and partner ecosystem signals automatically. Every company on a ZoomInfo list gets a real technical evaluation, not just a firmographic score.")

    h2(doc, "The Three Gates")
    body(doc, "Intelligence evaluates every company and product against three qualification gates. All three must clear for a prospect to be genuinely purseable.")
    bullet_bold(doc, "Gate 1 — Technical Orchestrability: ", "Can Skillable deliver a lab for this company's products? This is the primary gate. If the answer is no, the composite score is limited regardless of everything else. Gate 1 failure means the company is not a Skillable prospect — period.")
    bullet_bold(doc, "Gate 2 — Product Complexity: ", "Is the product technically rich enough that hands-on labs create genuine skill-building value? Simple products with shallow workflows don't benefit enough from labs to justify the investment. High Gate 2 scores mean learners get dramatically better at something that matters — and they can prove it.")
    bullet_bold(doc, "Gate 3 — Organizational Readiness: ", "Does the company have the content team skills, technical enablement maturity, and program leadership to build and sustain a lab program? Gate 3 uses a two-question model: does the organization have this capability today, and do they have the organizational DNA to build it if absent?")
    body(doc, "A company must clear all three gates for a successful lab program to be achievable. Intelligence flags what's missing — and surfaces what it would take to get there.")
    ai_moment(doc, "Skillable has deep, specific knowledge about how its platform works — delivery paths, technical blockers, feature availability, Gate 1 disqualifiers, scoring feasibility signals. A human SE applies that knowledge to one company at a time, in a live conversation. Intelligence applies it to every product it researches, automatically — reasoning through the specific technical characteristics of a product against the specific capabilities and constraints of the Skillable platform, and producing a judgment that reflects reality rather than optimism. Intelligence knows Skillable as well as your best SE, and applies that knowledge to every company it touches.")

    h2(doc, "The Workday Pattern — Knowing When to Stop Before We Start")
    body_bold(doc, [("The goal of Intelligence is to surface the specific technical reasons a company cannot be a Skillable customer — before we spend a single dollar marketing to them.", True)])
    body(doc, "Workday is the clearest illustration. On every traditional marketing signal, Workday looks like an ideal prospect: world-class training organization, deep content ecosystem, strong technical enablement culture, massive install base. Gate 3 passes with distinction. Gate 2 passes too — configuring Workday HCM or Financials is genuinely complex. Workday's own content teams wanted to build labs.")
    body(doc, "Gate 1 is where the analysis ends. The specific technical reasons are articulable and discoverable from public documentation:")
    bullet_bold(doc, "Pure multi-tenant architecture — ", "every Workday customer shares the same cloud environment. There is no Workday instance to give a learner. The product is architecturally incapable of per-learner isolation.")
    bullet_bold(doc, "No provisioning API — ", "no mechanism to spin up an individual environment programmatically. Skillable's entire delivery model depends on this capability.")
    bullet_bold(doc, "No deployment model — ", "nothing to install, nothing to containerize, nothing to slice. The product lives entirely in Workday's cloud and cannot be replicated outside it.")
    body(doc, "These are not hunches. They are specific, technical facts — findable in public documentation before a single sales conversation begins.")
    body(doc, "The most important version of this story: Workday wasn't a bad lead. It was motivated, capable people inside a well-run organization who invested significant time before hitting a wall that was always there — because Gate 1 was never evaluated before the pursuit began.")
    body_bold(doc, [
        ("Products that work like Workday are not a fit — and Intelligence surfaces that before any marketing motion begins. ", True),
        ("The HubSpot verdict is Do Not Pursue — with the specific technical reasons documented on the Company record so any seller or marketer who asks gets a clear, defensible answer.", False),
    ])
    ai_moment(doc, "Identifying that a product has no provisioning API, no deployment model, and pure multi-tenant architecture — from public documentation, before any human conversation — is not a filter. It is a research and reasoning task. The technical reasons a company cannot be a Skillable customer are documented before the first marketing dollar is spent.")

    h2(doc, "Lookalike Is Causation, Not Correlation")
    body(doc, "Standard lookalike analysis finds companies that resemble existing customers — same size, same industry, same growth profile. That is firmographic correlation. It is useful, and it has limits.")
    body(doc, "For Skillable, lookalike analysis works differently — and more powerfully.")
    body(doc, "When Fortinet is a strong fit, it is not because Fortinet resembles other good customers as a company. It is because Fortinet's products have specific technical characteristics — multi-VM topology, deep admin workflows, real consequence of error, strong API surface — that make them labable. Those characteristics are determined by what Fortinet sells, not by how large they are.")
    body_bold(doc, [("Every company selling products with those same technical characteristics is labable for the same reasons.", True), (" The fit is not approximate. It transfers directly.", False)])
    bullet(doc, "A company selling network security products will almost always clear Gates 1 and 2 — for the same reasons Fortinet, Palo Alto, and Cisco do.")
    bullet(doc, "A company selling SIEM, EDR, or identity management will almost always clear Gates 1 and 2 — for the same reasons CrowdStrike, Splunk, and SentinelOne do.")
    bullet(doc, "A company selling data pipeline or ML infrastructure will almost always clear Gates 1 and 2 — for the same reasons Databricks, dbt Labs, and Snowflake do.")
    body_bold(doc, [("The competitive map is the lookalike list. ", True), ("Every time Intelligence analyzes a strong-fit customer, it surfaces that company's direct competitors — pre-qualified lookalike candidates, identified automatically, without additional research. And it compounds: every new Skillable customer proves another product category.", False)])
    body_bold(doc, [
        ("We are not looking for companies that look like our customers. ", False),
        ("We are looking for companies whose products behave like our customers' products.", True),
        (" That is a fundamentally more defensible, more precise, and more scalable approach to ICP targeting.", False),
    ])
    ai_moment(doc, "Finding companies whose products behave like known strong-fit customers requires understanding what makes a product technically orchestrable and applying that reasoning across the internet. The competitive map of every analyzed customer becomes an automatically updated list of pre-qualified lookalike candidates — identified without additional research, compounding with every new customer.")


def write_what(doc):
    h1(doc, "WHAT — The Intelligence Platform")

    h2(doc, "Three Tools, One Intelligence Layer")
    body(doc, "Skillable Intelligence is a platform of three connected tools — Prospector, Inspector, and Designer — all powered by a shared research and scoring engine. The intelligence layer accumulates, stores, and maintains company and product knowledge. Each tool contextualizes that intelligence for a specific person doing a specific job.")
    body_bold(doc, [("Improving the intelligence layer improves all three tools simultaneously. ", True), ("Every research improvement makes Prospector rankings more accurate, Inspector analyses more complete, and Designer recommendations more specific — at the same time. The platform gets smarter with every analysis, and every tool benefits.", False)])

    h2(doc, "Prospector — ICP Outbound at Scale")
    body(doc, "Prospector is the go-to-market tool for Marketing and RevOps. It takes a list of companies and returns a ranked assessment of how well each one fits Skillable's ICP — with product-level evidence, composite scores, verdicts, delivery path signals, and key contacts for every company on the list.")
    body_bold(doc, [("What it unlocks: ", True), ("Marketing has never had access to product-level qualification data at the point of list building. Prospector makes it possible to screen a ZoomInfo export of 500 companies for Gate 1/2/3 compatibility before a sequence is written, a dollar is spent, or an SDR makes a call. Companies that clear all three gates go into outreach. The Workday patterns come off the list — with documented reasons.", False)])
    body(doc, "Prospector also surfaces customer expansion opportunities — mapping the department landscape of existing accounts to identify adoption opportunities for existing labs, greenfield departments, and existing buyers ready to expand.")

    h2(doc, "Inspector — Deep Analysis for Sellers and SEs")
    body(doc, "Inspector performs a deep product-level analysis of a specific company. It runs in two stages.")
    bullet_bold(doc, "Stage 1 — Company Report: ", "A broad scan that surfaces all of the company's products, ranked by labability, with competitive pairings, company-level signals, and an overall fit score. The foundation document for any seller or SE entering a conversation with this account. Also the output of Prospector's Customer Expansion pass — the same research, stored once per company, shared across both tools.")
    bullet_bold(doc, "Stage 2 — Deep Dive: ", "The seller or SE selects three to four products from Stage 1 for exhaustive analysis — full Gate 1/2/3 evidence, delivery path recommendation with rationale, scoring approach, consumption potential estimate, and program scope. This is the document that goes into a deal conversation.")
    ai_moment(doc, "A seller walking into a conversation with a Stage 2 Inspector report knows what the customer's products can and cannot do on the Skillable platform, which delivery path makes sense and why, and what the estimated consumption potential is. That is not a discovery conversation — it is a solution conversation. A level of pre-call preparation that was previously impossible at scale is now standard.")

    h2(doc, "Designer — From Analysis to Program")
    body(doc, "Designer takes Inspector's output and guides program owners, instructional designers, and subject matter experts through the full process of designing a lab program — from goals and audience through a complete approved outline, draft instructions, and a Skillable Studio-ready export package.")
    body_bold(doc, [("What it unlocks: ", True), ("Customers who don't know how to design a lab program won't build one. And if they don't build one, they don't adopt Skillable. Designer is the adoption engine — the tool that gives a new customer something concrete to do on day one, before the technical environment is ready, and produces a complete program architecture that a contracted lab developer can build against immediately.", False)])
    ai_moment(doc, "Designer generates a complete Bill of Materials — PowerShell scripts, Bicep templates, CloudFormation templates, lifecycle action scripts, credential pool configuration, scoring validation stubs — from everything it knows about the program. Hours of SE and lab developer work, generated in the same session where the program was designed.")


def write_how(doc):
    h1(doc, "HOW — Integration with HubSpot and Revenue Operations")
    section_note(doc, "This section is written for RevOps and Marketing leadership. Executive readers who do not own HubSpot infrastructure may stop here.")

    h2(doc, "The Integration Principle")
    body(doc, "HubSpot is the seller and marketer's workspace. Intelligence is the specialist workspace. The integration surfaces the right intelligence in the right place — without requiring sellers to live in another tool or RevOps to build a parallel system.")
    body(doc, "The three Intelligence tools have distinct integration models. Understanding the difference matters for RevOps configuration and for setting expectations with each user audience.")

    h2(doc, "Prospector ↔ HubSpot — Bidirectional, Marketing-Driven")
    body(doc, "Marketing triggers Prospector from inside HubSpot — selecting a ZoomInfo list or defining ICP criteria and sending them to Prospector for analysis. Prospector writes enriched data back to HubSpot Company records, Contact records, and Deals. HubSpot is Prospector's primary output destination.")
    body(doc, "Data written to the Company record:")
    add_table(doc,
        ["Data", "Purpose"],
        [
            ["Intelligence Fit Score", "Numeric score (0–100); enables list segmentation and prioritization"],
            ["Intelligence Verdict", "Labable / Simulation Candidate / Do Not Pursue; enables filtered views and enrollment triggers"],
            ["Fit Rationale Summary", "2–3 sentences for a seller: why this company scored well or poorly, which product drove the score, what the path looks like"],
            ["Top Product Signal", "The product or product category that most drove the score"],
            ["Recommended Delivery Path", "Cloud Slice / Standard VM / Simulation / Custom API"],
            ["Key Risk Flag", "The single most important constraint a seller needs to know"],
            ["Date of Last Analysis", "Enables freshness filtering"],
            ["Link to Full Intelligence Report", "One-click access to complete scoring and evidence"],
        ]
    )
    body(doc, "Intelligence also surfaces up to two contacts per company — a decision maker and a day-to-day champion — extracted from public sources for ABM targeting.")

    h2(doc, "HubSpot → Inspector — One-Way Trigger, Seller and SE-Driven")
    body(doc, "Company and Deal records in HubSpot surface a 'Run Inspector' link. Clicking it opens Inspector in a new browser window at the Stage 1 Company Report. The full Inspector experience runs in Intelligence — HubSpot is only the trigger.")
    body(doc, "Stage 1 data → Company Record (persistent account intelligence):")
    add_table(doc,
        ["Data", "Purpose"],
        [
            ["Product list with labability scores", "Account-level intelligence on what this company sells and how labable each product is"],
            ["Top delivery path signal per product", "Quick read on how each product would be delivered"],
            ["Overall company fit score", "Single number for segmentation and prioritization"],
            ["Key risk flag", "The most important constraint a seller needs to know"],
            ["Date of last analysis + link to full report", "Freshness tracking and one-click access"],
        ]
    )
    body(doc, "Stage 2 data → Deal Record (opportunity-specific):")
    add_table(doc,
        ["Data", "Purpose"],
        [
            ["Delivery path recommendation + rationale", "What path, and why — the SE's talking point"],
            ["Scoring approach recommendation", "How learner actions will be validated"],
            ["Consumption potential / ACV estimate", "Deal-level revenue context"],
            ["Gate scores summary", "Compressed evidence for the SE"],
            ["Program scope estimate", "Labs, seat time, curriculum depth"],
            ["Link to full Inspector Stage 2 report", "Full context one click away"],
        ]
    )

    h2(doc, "Designer → HubSpot — Read-Only Visibility")
    body(doc, "Program owners, IDs, and SMEs go directly to Designer. HubSpot plays no role in triggering Designer's workflow.")
    body(doc, "Designer-created Lab Programs surface in HubSpot as read-only links and summary data on the Company record — giving sellers and CSMs visibility into what programs have been designed, what's in progress, and what has been delivered. Critical context for renewal and expansion conversations before a QBR.")


def write_recommendations(doc):
    h1(doc, "Recommendations and Open Decisions")

    h2(doc, "What We Are Recommending")
    bullet_bold(doc, "Prospector as the primary Marketing data source for ICP outbound. ", "Replace or supplement the current ZoomInfo-only scoring motion with Intelligence-qualified lists. Companies that fail Gate 1 come off the list before sequences are built. Companies that clear all three gates get prioritized outreach with seller-ready context already in HubSpot.")
    bullet_bold(doc, "Inspector Stage 1 as the standard pre-call research tool for all sellers and SEs. ", "The 'Run Inspector' link on every Company and Deal record makes it a one-click motion. Stage 1 output on the Company record gives every seller account intelligence they currently don't have.")
    bullet_bold(doc, "Designer as a standard deliverable in every new customer engagement. ", "Skillable LC and PS should run every new customer through Designer in the first week — before the technical environment is ready. Designer makes day one productive for the program owner.")

    h2(doc, "Decisions Required from RevOps and Marketing")
    body(doc, "The following require RevOps and Marketing input before the HubSpot integration can be built:")
    add_table(doc,
        ["Decision", "Context"],
        [
            ["Existing custom Company properties", "Which recommended fields already exist vs. net-new?"],
            ["Deal template review", "Where does each recommended data element fit in the existing deal UX?"],
            ["Deduplication rules", "What constitutes a match to an existing Deal for expansion opportunities?"],
            ["Stage 2 multi-product question", "If Inspector covers three products, do they generate three Deals or append to one?"],
            ["Buying Group Summary structure", "Current state across the customer base?"],
            ["Ownership and notification rules", "How should Intelligence-generated Deals trigger notifications for AEs and CSMs?"],
            ["ZoomInfo CSV column mapping", "Which columns are in Marketing's standard export? Minimum: Company Name + Domain. High value: Industry, LinkedIn URL, Employee Count, Technologies Used."],
            ["Score threshold for auto-create/update", "At what Intelligence Fit Score does a Company record automatically get enriched vs. queued for review?"],
        ]
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    doc, section = setup_document()
    add_header(section)
    add_footer(section)

    add_title(doc, "Skillable Intelligence Platform", "Briefing for Skillable Executive Leadership")

    write_why(doc)
    page_break(doc)
    write_what(doc)
    page_break(doc)
    write_how(doc)
    write_recommendations(doc)

    doc.save(OUTPUT_PATH)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
