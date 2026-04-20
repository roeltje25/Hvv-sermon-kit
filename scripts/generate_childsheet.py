#!/usr/bin/env python3
"""
HVV Sermon Kit — Child Sheet Generator

Generates an A4 PDF "Kinderblad" (children's sheet) in the parchment style from a config.
Usage:  python3 generate_childsheet.py <config.json> <output.pdf>

The config can include any combination of:
  - wordsearch:   {words: [...]}
  - story_order:  {images: [...]}  (2–8 images)
  - fruit_tree:   {good_fruits: [...], bad_fruits: [...]}
  - questions:    {items: [...]}

Sections that are absent from the config are simply not rendered.
"""

import json
import random
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader


# -----------------------------------------------------------------------------
# PALETTE (parchment)
# -----------------------------------------------------------------------------
PALETTE = {
    "bg":       HexColor("#EDE8DC"),
    "card_bg":  HexColor("#F5F0E8"),
    "border":   HexColor("#C8B99A"),
    "header":   HexColor("#3D2B1F"),
    "label":    HexColor("#6B4C35"),
    "text":     HexColor("#2C1F13"),
    "band":     HexColor("#D9CEB8"),
}

# Wordsearch directions: only forward (right, down, diagonal down-right)
# This makes the puzzle more suitable for children.
DIRECTIONS = [(0, 1), (1, 0), (1, 1)]


# -----------------------------------------------------------------------------
# WORDSEARCH GENERATION
# -----------------------------------------------------------------------------
def _can_place(grid, word, row, col, dr, dc, gs):
    for i, ch in enumerate(word):
        r, c = row + i * dr, col + i * dc
        if r < 0 or r >= gs or c < 0 or c >= gs:
            return False
        if grid[r][c] != "" and grid[r][c] != ch:
            return False
    return True


def _place_word(grid, word, gs):
    for _ in range(400):
        dr, dc = random.choice(DIRECTIONS)
        row = random.randint(0, gs - 1)
        col = random.randint(0, gs - 1)
        if _can_place(grid, word, row, col, dr, dc, gs):
            for i, ch in enumerate(word):
                grid[row + i * dr][col + i * dc] = ch
            return True
    return False


def build_wordsearch_grid(words, grid_size=14):
    """Build a wordsearch grid that contains all words. Retries with different seeds."""
    sorted_words = sorted([w.upper().replace(" ", "") for w in words], key=len, reverse=True)
    longest = len(sorted_words[0]) if sorted_words else 0
    if grid_size < longest:
        grid_size = longest + 2

    for attempt in range(600):
        random.seed(attempt)
        grid = [["" for _ in range(grid_size)] for _ in range(grid_size)]
        ok = True
        for w in sorted_words:
            if not _place_word(grid, w, grid_size):
                ok = False
                break
        if ok:
            for r in range(grid_size):
                for c in range(grid_size):
                    if grid[r][c] == "":
                        grid[r][c] = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            return grid
    raise RuntimeError(
        f"Could not place all {len(sorted_words)} words in a {grid_size}x{grid_size} grid. "
        f"Try a larger grid_size or fewer/shorter words."
    )


# -----------------------------------------------------------------------------
# PDF DRAWING
# -----------------------------------------------------------------------------
def draw_header(c, W, H, title, subtitle):
    P = PALETTE
    # Top ornamental band
    c.setFillColor(P["band"])
    c.rect(0, H - 1.5 * cm, W, 1.5 * cm, fill=1, stroke=0)
    c.setStrokeColor(P["border"])
    c.setLineWidth(0.7)
    c.line(1.5 * cm, H - 1.5 * cm, W - 1.5 * cm, H - 1.5 * cm)

    # Title
    c.setFillColor(P["header"])
    c.setFont("Times-Bold", 22)
    c.drawCentredString(W / 2, H - 1.05 * cm, title)

    # Subtitle
    if subtitle:
        c.setFillColor(P["label"])
        c.setFont("Times-Italic", 11)
        c.drawCentredString(W / 2, H - 1.95 * cm, subtitle)

    # Decorative line + diamond
    c.setStrokeColor(P["border"])
    c.setLineWidth(0.5)
    c.line(W / 2 - 3.5 * cm, H - 2.3 * cm, W / 2 - 0.25 * cm, H - 2.3 * cm)
    c.line(W / 2 + 0.25 * cm, H - 2.3 * cm, W / 2 + 3.5 * cm, H - 2.3 * cm)
    c.setFillColor(P["border"])
    cx, cy, s = W / 2, H - 2.3 * cm, 0.1 * cm
    c.saveState()
    c.translate(cx, cy)
    c.rotate(45)
    c.rect(-s / 2, -s / 2, s, s, fill=1, stroke=0)
    c.restoreState()


def draw_wordsearch(c, W, top_y, config):
    """Draw wordsearch section. Returns the y-coordinate of the bottom."""
    P = PALETTE
    words = config.get("words", [])
    display_words = config.get("display_words") or words
    section_title = config.get("section_title", "Zoek deze woorden")
    section_num = config.get("section_num", 1)
    grid_size = config.get("grid_size", 14)

    # Section header
    c.setFillColor(P["label"])
    c.setFont("Times-BoldItalic", 12)
    c.drawCentredString(W / 2, top_y, f"{section_num}. {section_title}")

    # Generate grid
    grid = build_wordsearch_grid(words, grid_size)
    gs = len(grid)

    # Grid layout
    grid_size_cm = 9.5
    cell = grid_size_cm / gs * cm
    grid_x = 1.5 * cm
    grid_y_top = top_y - 0.4 * cm

    # Grid card background
    pad = 0.2 * cm
    c.setFillColor(P["card_bg"])
    c.setStrokeColor(P["border"])
    c.setLineWidth(0.6)
    c.rect(
        grid_x - pad, grid_y_top - gs * cell - pad,
        gs * cell + 2 * pad, gs * cell + 2 * pad,
        fill=1, stroke=1,
    )

    # Letters
    c.setFillColor(P["text"])
    c.setFont("Times-Roman", 10.5)
    for r in range(gs):
        for ccol in range(gs):
            x = grid_x + ccol * cell + cell / 2
            y = grid_y_top - r * cell - cell / 2 - 0.09 * cm
            c.drawCentredString(x, y, grid[r][ccol])

    # Word list (2 columns to the right of grid)
    words_x = grid_x + gs * cell + 0.8 * cm
    words_y_top = grid_y_top - 0.1 * cm
    col_w = 2.8 * cm
    c.setFillColor(P["text"])
    c.setFont("Times-Roman", 10)
    for i, w in enumerate(display_words):
        col = i % 2
        row = i // 2
        x = words_x + col * col_w
        y = words_y_top - row * 0.55 * cm
        # Diamond bullet
        c.setFillColor(P["border"])
        c.saveState()
        c.translate(x - 0.2 * cm, y + 0.11 * cm)
        c.rotate(45)
        c.rect(-0.055 * cm, -0.055 * cm, 0.11 * cm, 0.11 * cm, fill=1, stroke=0)
        c.restoreState()
        c.setFillColor(P["text"])
        c.drawString(x, y, w)

    return grid_y_top - gs * cell - pad


def draw_story_order(c, W, top_y, config):
    """Draw story-order section. Returns y-coordinate of bottom."""
    P = PALETTE
    images = config.get("images", [])
    if not images:
        return top_y

    section_title = config.get("section_title", "Zet de plaatjes in de juiste volgorde")
    instruction = config.get("instruction", f"Schrijf het cijfer (1 tot {len(images)}) in het vakje onder elk plaatje")
    section_num = config.get("section_num", 2)

    # Section header
    c.setFillColor(P["label"])
    c.setFont("Times-BoldItalic", 12)
    c.drawCentredString(W / 2, top_y, f"{section_num}. {section_title}")

    c.setFillColor(P["label"])
    c.setFont("Times-Italic", 9)
    c.drawCentredString(W / 2, top_y - 0.4 * cm, instruction)

    # Layout: 3 cols for 6 images, 3 cols for 3, 2 cols for 4, etc.
    n = len(images)
    if n <= 3:
        img_cols = n
    elif n == 4:
        img_cols = 2
    else:
        img_cols = 3
    img_rows = (n + img_cols - 1) // img_cols

    img_total_w = W - 2 * (1.5 * cm)
    img_gap_x = 0.5 * cm
    img_w = (img_total_w - (img_cols - 1) * img_gap_x) / img_cols
    img_h = 3.3 * cm  # fixed height

    img_grid_top = top_y - 0.85 * cm
    img_gap_y = 0.65 * cm

    # Deterministic shuffle (based on length so it's reproducible)
    indices = list(range(n))
    rng = random.Random(42 + n)
    shuffled = indices[:]
    for _ in range(10):
        rng.shuffle(shuffled)
        if shuffled != indices:
            break
    # As fallback, force a rotation if still in order
    if shuffled == indices and n > 1:
        shuffled = indices[1:] + indices[:1]

    for display_idx, story_idx in enumerate(shuffled):
        col = display_idx % img_cols
        row = display_idx // img_cols
        x = 1.5 * cm + col * (img_w + img_gap_x)
        y = img_grid_top - row * (img_h + img_gap_y) - img_h

        # Image with frame
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(P["border"])
        c.setLineWidth(0.7)
        c.rect(x - 0.05 * cm, y - 0.05 * cm, img_w + 0.1 * cm, img_h + 0.1 * cm, fill=1, stroke=1)

        img_path = images[story_idx]
        if Path(img_path).exists():
            img = ImageReader(img_path)
            c.drawImage(img, x, y, width=img_w, height=img_h, preserveAspectRatio=True, anchor="c")
        else:
            c.setFillColor(P["label"])
            c.setFont("Times-Italic", 8)
            c.drawCentredString(x + img_w / 2, y + img_h / 2, "[afbeelding ontbreekt]")

        # Number box below
        box_size = 0.55 * cm
        box_x = x + (img_w - box_size) / 2
        box_y = y - 0.15 * cm - box_size
        c.setFillColor(P["card_bg"])
        c.setStrokeColor(P["border"])
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_size, box_size, fill=1, stroke=1)

    # Return bottom
    last_row_img_y = img_grid_top - (img_rows - 1) * (img_h + img_gap_y) - img_h
    return last_row_img_y - 0.15 * cm - 0.55 * cm


def _draw_bare_tree(c, cx, bottom_y, height):
    """Detailed coloring-book tree: thick outlines, white fill, bark + leaf texture."""
    brown = HexColor("#2C1F13")
    lw_main = 2.2
    lw_detail = 0.9

    trunk_h = height * 0.34
    canopy_base = bottom_y + trunk_h
    bh = height - trunk_h

    # --- Grass tufts at base ---
    c.setStrokeColor(brown)
    c.setLineWidth(1.3)
    for dx in [-1.4, -1.0, -0.6, -0.2, 0.2, 0.6, 1.0, 1.4]:
        gx = cx + dx * cm
        c.line(gx, bottom_y, gx - 0.07 * cm, bottom_y + 0.22 * cm)
        c.line(gx, bottom_y, gx + 0.07 * cm, bottom_y + 0.22 * cm)

    # --- Canopy (drawn first so trunk paints over its base) ---
    # Large rounded shape with small leaf-bumps along the edge
    cn = c.beginPath()
    # Bottom entry points
    cn.moveTo(cx - 0.65 * cm, canopy_base + 0.05 * cm)
    # Lower-left curve
    cn.curveTo(cx - 2.0 * cm, canopy_base - 0.1 * cm,
               cx - 3.2 * cm, canopy_base + 0.5 * cm,
               cx - 3.0 * cm, canopy_base + bh * 0.30)
    # Left leaf bump
    cn.curveTo(cx - 3.6 * cm, canopy_base + bh * 0.38,
               cx - 3.7 * cm, canopy_base + bh * 0.58,
               cx - 3.2 * cm, canopy_base + bh * 0.63)
    # Upper-left bump
    cn.curveTo(cx - 3.1 * cm, canopy_base + bh * 0.80,
               cx - 2.4 * cm, canopy_base + bh * 0.95,
               cx - 1.6 * cm, canopy_base + bh * 0.88)
    # Top-left bump
    cn.curveTo(cx - 1.4 * cm, canopy_base + bh * 1.08,
               cx - 0.5 * cm, canopy_base + bh * 1.18,
               cx,             canopy_base + bh * 1.12)
    # Top-right bump
    cn.curveTo(cx + 0.5 * cm, canopy_base + bh * 1.18,
               cx + 1.4 * cm, canopy_base + bh * 1.08,
               cx + 1.6 * cm, canopy_base + bh * 0.88)
    # Upper-right bump
    cn.curveTo(cx + 2.4 * cm, canopy_base + bh * 0.95,
               cx + 3.1 * cm, canopy_base + bh * 0.80,
               cx + 3.2 * cm, canopy_base + bh * 0.63)
    # Right leaf bump
    cn.curveTo(cx + 3.7 * cm, canopy_base + bh * 0.58,
               cx + 3.6 * cm, canopy_base + bh * 0.38,
               cx + 3.0 * cm, canopy_base + bh * 0.30)
    # Lower-right curve
    cn.curveTo(cx + 3.2 * cm, canopy_base + 0.5 * cm,
               cx + 2.0 * cm, canopy_base - 0.1 * cm,
               cx + 0.65 * cm, canopy_base + 0.05 * cm)
    cn.close()
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(brown)
    c.setLineWidth(lw_main)
    c.drawPath(cn, fill=1, stroke=1)

    # Interior leaf detail lines (simple curved strokes inside canopy)
    c.setStrokeColor(brown)
    c.setLineWidth(lw_detail)
    leaf_hints = [
        (cx - 1.6 * cm, canopy_base + bh * 0.28, cx - 0.9 * cm, canopy_base + bh * 0.45),
        (cx + 0.5 * cm, canopy_base + bh * 0.22, cx + 1.3 * cm, canopy_base + bh * 0.40),
        (cx - 0.4 * cm, canopy_base + bh * 0.55, cx + 0.5 * cm, canopy_base + bh * 0.70),
        (cx - 2.0 * cm, canopy_base + bh * 0.55, cx - 1.1 * cm, canopy_base + bh * 0.68),
        (cx + 1.4 * cm, canopy_base + bh * 0.52, cx + 2.2 * cm, canopy_base + bh * 0.65),
        (cx - 0.8 * cm, canopy_base + bh * 0.78, cx + 0.2 * cm, canopy_base + bh * 0.92),
        (cx + 0.8 * cm, canopy_base + bh * 0.35, cx + 1.5 * cm, canopy_base + bh * 0.50),
    ]
    for x1, y1, x2, y2 in leaf_hints:
        lp = c.beginPath()
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        lp.moveTo(x1, y1)
        lp.curveTo(mx - 0.1 * cm, my + 0.15 * cm, mx + 0.1 * cm, my + 0.15 * cm, x2, y2)
        c.drawPath(lp, fill=0, stroke=1)

    # --- Trunk (on top of canopy) ---
    tw_bot = 0.60 * cm
    tw_top = 0.35 * cm
    tp = c.beginPath()
    tp.moveTo(cx - tw_bot, bottom_y)
    tp.curveTo(cx - tw_bot - 0.08 * cm, bottom_y + trunk_h * 0.4,
               cx - tw_top - 0.04 * cm, bottom_y + trunk_h * 0.75,
               cx - tw_top, canopy_base)
    tp.lineTo(cx + tw_top, canopy_base)
    tp.curveTo(cx + tw_top + 0.04 * cm, bottom_y + trunk_h * 0.75,
               cx + tw_bot + 0.08 * cm, bottom_y + trunk_h * 0.4,
               cx + tw_bot, bottom_y)
    tp.close()
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(brown)
    c.setLineWidth(lw_main)
    c.drawPath(tp, fill=1, stroke=1)

    # Bark texture on trunk
    c.setLineWidth(lw_detail)
    for frac, x_off in [(0.22, 0.3), (0.48, -0.2), (0.72, 0.15)]:
        y_b = bottom_y + trunk_h * frac
        w_b = tw_bot + (tw_top - tw_bot) * frac
        c.line(cx - w_b * 0.65 + x_off * cm, y_b,
               cx + w_b * 0.50 + x_off * cm, y_b + 0.07 * cm)
    # Knot
    kx, ky = cx + 0.05 * cm, bottom_y + trunk_h * 0.58
    kp = c.beginPath()
    kp.moveTo(kx, ky)
    kp.curveTo(kx + 0.18 * cm, ky + 0.10 * cm,
               kx + 0.18 * cm, ky - 0.10 * cm, kx, ky)
    c.drawPath(kp, fill=0, stroke=1)


def _draw_fruit_shape(c, cx, cy, r, label, fill_color, brown):
    """Detailed coloring-book apple: heart-top body, highlight, curved stem, leafed, label below."""
    lw = 1.8

    # Apple body — slight indentation at top for heart shape
    body = c.beginPath()
    body.moveTo(cx, cy + r * 0.88)
    body.curveTo(cx + r * 0.28, cy + r * 1.02,
                 cx + r,        cy + r * 0.55,
                 cx + r,        cy)
    body.curveTo(cx + r,        cy - r,
                 cx - r,        cy - r,
                 cx - r,        cy)
    body.curveTo(cx - r,        cy + r * 0.55,
                 cx - r * 0.28, cy + r * 1.02,
                 cx,            cy + r * 0.88)
    body.close()
    c.setFillColor(fill_color)
    c.setStrokeColor(brown)
    c.setLineWidth(lw)
    c.drawPath(body, fill=1, stroke=1)

    # Highlight (small oval, upper-right)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(brown)
    c.setLineWidth(0.5)
    hx, hy = cx + r * 0.30, cy + r * 0.30
    c.ellipse(hx - r * 0.22, hy - r * 0.14,
              hx + r * 0.22, hy + r * 0.14, fill=1, stroke=1)

    # Curved stem
    stem = c.beginPath()
    stem.moveTo(cx, cy + r * 0.88)
    stem.curveTo(cx + r * 0.25, cy + r + 0.12 * cm,
                 cx + r * 0.20, cy + r + 0.28 * cm,
                 cx + r * 0.10, cy + r + 0.38 * cm)
    c.setStrokeColor(brown)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setLineWidth(1.2)
    c.drawPath(stem, fill=0, stroke=1)

    # Leaf
    lbx = cx + r * 0.10
    lby = cy + r + 0.22 * cm
    leaf = c.beginPath()
    leaf.moveTo(lbx, lby)
    leaf.curveTo(lbx + 0.42 * cm, lby + 0.30 * cm,
                 lbx + 0.55 * cm, lby + 0.00 * cm,
                 lbx + 0.18 * cm, lby - 0.12 * cm)
    leaf.close()
    c.setFillColor(HexColor("#D4EDB8"))
    c.setStrokeColor(brown)
    c.setLineWidth(0.8)
    c.drawPath(leaf, fill=1, stroke=1)
    # Leaf vein
    c.setLineWidth(0.5)
    c.line(lbx, lby, lbx + 0.28 * cm, lby + 0.10 * cm)

    # Label below apple
    c.setFillColor(HexColor("#2C1F13"))
    c.setFont("Times-Roman", 7.5)
    c.drawCentredString(cx, cy - r - 0.22 * cm, label)


def draw_fruit_tree(c, W, top_y, config):
    """Draw fruit-tree matching activity. Returns y-coordinate of bottom."""
    P = PALETTE
    good_fruits = config.get("good_fruits", [])
    bad_fruits = config.get("bad_fruits", [])
    section_title = config.get("section_title", "Welke vruchten horen bij de boom?")
    instruction = config.get("instruction", "Trek een lijn van de goede vruchten naar de boom")
    section_num = config.get("section_num", 2)

    c.setFillColor(P["label"])
    c.setFont("Times-BoldItalic", 12)
    c.drawCentredString(W / 2, top_y, f"{section_num}. {section_title}")

    c.setFillColor(P["label"])
    c.setFont("Times-Italic", 9)
    c.drawCentredString(W / 2, top_y - 0.4 * cm, instruction)

    content_top = top_y - 1.0 * cm
    brown = HexColor("#2C1F13")

    # Layout: 4 columns of apples on the right half
    all_fruits = [(w, True) for w in good_fruits] + [(w, False) for w in bad_fruits]
    rng = random.Random(77)
    rng.shuffle(all_fruits)

    r = 0.40 * cm
    stem_leaf_h = 0.50 * cm   # height above circle center for stem+leaf
    label_h = 0.28 * cm       # text below circle
    row_h = 2 * r + stem_leaf_h + label_h + 0.30 * cm  # gap between rows
    cols = 4
    col_w = 1.50 * cm
    n = len(all_fruits)
    rows = (n + cols - 1) // cols

    fruits_x0 = W / 2 + 0.3 * cm
    first_cy = content_top - stem_leaf_h - r

    for i, (word, is_good) in enumerate(all_fruits):
        col = i % cols
        row = i // cols
        cx_f = fruits_x0 + col * col_w + r
        cy_f = first_cy - row * row_h
        fill_color = HexColor("#D4EDBC") if is_good else HexColor("#F0C8C4")
        _draw_fruit_shape(c, cx_f, cy_f, r, word, fill_color, brown)

    section_h = stem_leaf_h + rows * row_h + 0.1 * cm

    # Tree fills the left half at the same height
    tree_cx = 4.5 * cm
    tree_bottom = content_top - section_h + 0.4 * cm
    _draw_bare_tree(c, tree_cx, tree_bottom, section_h - 0.4 * cm)

    return content_top - section_h


def draw_questions(c, W, top_y, config):
    P = PALETTE
    items = config.get("items", [])
    if not items:
        return top_y
    section_title = config.get("section_title", "Vragen om over na te denken")
    section_num = config.get("section_num", 3)

    # Header
    c.setFillColor(P["label"])
    c.setFont("Times-BoldItalic", 12)
    c.drawCentredString(W / 2, top_y, f"{section_num}. {section_title}")

    q_y = top_y - 0.7 * cm
    q_spacing = 1.4 * cm

    for i, q in enumerate(items):
        y = q_y - i * q_spacing
        c.setFillColor(P["text"])
        c.setFont("Times-Italic", 10.5)
        c.drawString(1.5 * cm, y, f"{i+1}.  {q}")
        c.setStrokeColor(P["border"])
        c.setLineWidth(0.5)
        c.line(1.5 * cm, y - 0.6 * cm, W - 1.5 * cm, y - 0.6 * cm)

    return q_y - len(items) * q_spacing


def draw_footer(c, W):
    P = PALETTE
    c.setStrokeColor(P["border"])
    c.setLineWidth(0.7)
    c.line(1.5 * cm, 0.9 * cm, W - 1.5 * cm, 0.9 * cm)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate_childsheet.py <config.json> <output.pdf>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    title = config.get("title", "Kinderblad")
    subtitle = config.get("subtitle", "")

    c = canvas.Canvas(output_path, pagesize=A4)
    W, H = A4

    # Background
    c.setFillColor(PALETTE["bg"])
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Header
    draw_header(c, W, H, title, subtitle)

    # Sections — auto-numbered based on what's present
    cursor_y = H - 2.9 * cm
    section_num = 1

    if "wordsearch" in config and config["wordsearch"].get("words"):
        ws_conf = dict(config["wordsearch"])
        ws_conf["section_num"] = section_num
        cursor_y = draw_wordsearch(c, W, cursor_y, ws_conf)
        section_num += 1
        cursor_y -= 0.9 * cm  # gap to next section

    if "story_order" in config and config["story_order"].get("images"):
        so_conf = dict(config["story_order"])
        so_conf["section_num"] = section_num
        cursor_y = draw_story_order(c, W, cursor_y, so_conf)
        section_num += 1
        cursor_y -= 0.5 * cm

    if "fruit_tree" in config:
        ft_conf = dict(config["fruit_tree"])
        ft_conf["section_num"] = section_num
        cursor_y = draw_fruit_tree(c, W, cursor_y, ft_conf)
        section_num += 1
        cursor_y -= 0.7 * cm

    if "questions" in config and config["questions"].get("items"):
        q_conf = dict(config["questions"])
        q_conf["section_num"] = section_num
        cursor_y = draw_questions(c, W, cursor_y, q_conf)

    # Overlap check: warn if content reached the footer zone
    footer_limit = 1.2 * cm
    if cursor_y < footer_limit:
        print(
            f"WARNING: Content bottom ({cursor_y / cm:.1f}cm from page bottom) is below "
            f"the safe zone ({footer_limit / cm:.1f}cm). Sections may overlap the footer. "
            "Consider removing a section or reducing grid_size.",
            file=sys.stderr,
        )

    # Footer
    draw_footer(c, W)

    c.showPage()
    c.save()
    print(f"Child sheet written: {output_path}")


if __name__ == "__main__":
    main()
