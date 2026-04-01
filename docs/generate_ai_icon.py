#!/usr/bin/env python3
"""
Generate the AI Moment icon for Skillable Intelligence Platform Word doc.
Renders at 4x resolution then downscales with LANCZOS for smooth anti-aliasing.
Output: ai-moment-icon.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
PNG_PATH  = os.path.join(DOCS_DIR, "ai-moment-icon.png")

# ── Brand colors ──────────────────────────────────────────────────────────────
PURPLE = (112, 0, 255)    # #7000FF
BG     = (0, 0, 0, 0)     # transparent

# ── Render at 4x, output at 1x ───────────────────────────────────────────────
SCALE    = 4
OUT_SIZE = 220
RENDER   = OUT_SIZE * SCALE   # 880px

# All coordinates are in 1x space, multiplied by SCALE when drawing
def px(n): return int(n * SCALE)

img  = Image.new("RGBA", (RENDER, RENDER), BG)
draw = ImageDraw.Draw(img)

SW  = px(8)    # stroke width
CR  = px(8)    # circle radius (hollow)
CW  = px(3)    # circle stroke width

CX  = OUT_SIZE / 2   # 110
CY  = OUT_SIZE / 2   # 110
CHL = 75              # half chip width/height
RR  = px(8)           # chip corner radius (in render pixels)


def rr_rect(x0, y0, x1, y1, radius, stroke, width):
    """Draw a rounded rectangle outline."""
    draw.rounded_rectangle(
        [px(x0), px(y0), px(x1), px(y1)],
        radius=radius, outline=stroke, width=width
    )


def wire(pts):
    """Draw a polyline through a list of (x, y) 1x-space points."""
    scaled = [(px(x), px(y)) for x, y in pts]
    draw.line(scaled, fill=PURPLE, width=SW, joint="curve")


def node(cx, cy):
    """Draw a hollow circle (node) at 1x-space coords."""
    draw.ellipse(
        [px(cx) - CR, px(cy) - CR, px(cx) + CR, px(cy) + CR],
        outline=PURPLE, width=CW
    )


# ── Chip rectangle ────────────────────────────────────────────────────────────
chip_x0 = CX - CHL
chip_y0 = CY - CHL
chip_x1 = CX + CHL
chip_y1 = CY + CHL
rr_rect(chip_x0, chip_y0, chip_x1, chip_y1, radius=RR, stroke=PURPLE, width=SW)

# ── "AI" label ────────────────────────────────────────────────────────────────
font_size = px(46)
font = None
for fp in ["C:/Windows/Fonts/calibrib.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
    if os.path.exists(fp):
        font = ImageFont.truetype(fp, font_size)
        break
if font is None:
    font = ImageFont.load_default()

bbox = draw.textbbox((0, 0), "AI", font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
draw.text((px(CX) - tw // 2, px(CY) - th // 2 - px(2)), "AI", fill=PURPLE, font=font)

# ── Wire pin offsets from chip center ────────────────────────────────────────
# Two pins per side, symmetric about center
PIN = 28   # distance from center to pin along the edge

# ── Top wires ─────────────────────────────────────────────────────────────────
# Left pin: up from chip top, jog left, terminate
wire([(CX - PIN, chip_y0), (CX - PIN, chip_y0 - 22), (CX - PIN - 20, chip_y0 - 22), (CX - PIN - 20, 12)])
node(CX - PIN - 20, 12)

# Right pin: up from chip top, jog right, terminate
wire([(CX + PIN, chip_y0), (CX + PIN, chip_y0 - 22), (CX + PIN + 20, chip_y0 - 22), (CX + PIN + 20, 12)])
node(CX + PIN + 20, 12)

# ── Bottom wires ──────────────────────────────────────────────────────────────
wire([(CX - PIN, chip_y1), (CX - PIN, chip_y1 + 22), (CX - PIN - 20, chip_y1 + 22), (CX - PIN - 20, OUT_SIZE - 12)])
node(CX - PIN - 20, OUT_SIZE - 12)

wire([(CX + PIN, chip_y1), (CX + PIN, chip_y1 + 22), (CX + PIN + 20, chip_y1 + 22), (CX + PIN + 20, OUT_SIZE - 12)])
node(CX + PIN + 20, OUT_SIZE - 12)

# ── Left wires ────────────────────────────────────────────────────────────────
wire([(chip_x0, CY - PIN), (chip_x0 - 22, CY - PIN), (chip_x0 - 22, CY - PIN - 20), (12, CY - PIN - 20)])
node(12, CY - PIN - 20)

wire([(chip_x0, CY + PIN), (chip_x0 - 22, CY + PIN), (chip_x0 - 22, CY + PIN + 20), (12, CY + PIN + 20)])
node(12, CY + PIN + 20)

# ── Right wires ───────────────────────────────────────────────────────────────
wire([(chip_x1, CY - PIN), (chip_x1 + 22, CY - PIN), (chip_x1 + 22, CY - PIN - 20), (OUT_SIZE - 12, CY - PIN - 20)])
node(OUT_SIZE - 12, CY - PIN - 20)

wire([(chip_x1, CY + PIN), (chip_x1 + 22, CY + PIN), (chip_x1 + 22, CY + PIN + 20), (OUT_SIZE - 12, CY + PIN + 20)])
node(OUT_SIZE - 12, CY + PIN + 20)

# ── Downscale with LANCZOS for smooth anti-aliasing ───────────────────────────
img = img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
img.save(PNG_PATH, "PNG")
print(f"Saved: {PNG_PATH}")
