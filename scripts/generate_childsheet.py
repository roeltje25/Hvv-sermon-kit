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
    """Coloring-book style tree: outlined trunk + cloud canopy, white fill."""
    brown = HexColor("#6B4C35")
    trunk_h = height * 0.36
    canopy_base = bottom_y + trunk_h

    # Trunk as outlined trapezoid (white fill so it covers the canopy bottom)
    tw_bot = 0.55 * cm
    tw_top = 0.32 * cm
    trunk_path = c.beginPath()
    trunk_path.moveTo(cx - tw_bot, bottom_y)
    trunk_path.lineTo(cx + tw_bot, bottom_y)
    trunk_path.lineTo(cx + tw_top, canopy_base)
    trunk_path.lineTo(cx - tw_top, canopy_base)
    trunk_path.close()
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(brown)
    c.setLineWidth(1.4)
    c.drawPath(trunk_path, fill=1, stroke=1)

    # Bark texture lines
    c.setLineWidth(0.5)
    c.setStrokeColor(brown)
    c.line(cx - tw_bot * 0.4, bottom_y + trunk_h * 0.18,
           cx + tw_bot * 0.6, bottom_y + trunk_h * 0.32)
    c.line(cx - tw_bot * 0.6, bottom_y + trunk_h * 0.52,
           cx + tw_bot * 0.3, bottom_y + trunk_h * 0.65)

    # Cloud-like canopy using bezier curves
    bh = height - trunk_h
    cy = canopy_base  # base of canopy
    # Control points tuned for a round, bumpy cloud crown
    canopy = c.beginPath()
    canopy.moveTo(cx - 0.6 * cm, cy)
    canopy.curveTo(cx - 2.8 * cm, cy + 0.3 * cm,
                   cx - 3.2 * cm, cy + bh * 0.45,
                   cx - 2.4 * cm, cy + bh * 0.62)
    canopy.curveTo(cx - 3.0 * cm, cy + bh * 0.80,
                   cx - 2.2 * cm, cy + bh * 1.05,
                   cx - 1.0 * cm, cy + bh * 0.90)
    canopy.curveTo(cx - 0.8 * cm, cy + bh * 1.15,
                   cx + 0.8 * cm, cy + bh * 1.15,
                   cx + 1.0 * cm, cy + bh * 0.90)
    canopy.curveTo(cx + 2.2 * cm, cy + bh * 1.05,
                   cx + 3.0 * cm, cy + bh * 0.80,
                   cx + 2.4 * cm, cy + bh * 0.62)
    canopy.curveTo(cx + 3.2 * cm, cy + bh * 0.45,
                   cx + 2.8 * cm, cy + 0.3 * cm,
                   cx + 0.6 * cm, cy)
    canopy.close()
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(brown)
    c.setLineWidth(1.6)
    c.drawPath(canopy, fill=1, stroke=1)

    # Redraw trunk on top so canopy doesn't cover it
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(brown)
    c.setLineWidth(1.4)
    c.drawPath(trunk_path, fill=1, stroke=1)
    c.setLineWidth(0.5)
    c.line(cx - tw_bot * 0.4, bottom_y + trunk_h * 0.18,
           cx + tw_bot * 0.6, bottom_y + trunk_h * 0.32)
    c.line(cx - tw_bot * 0.6, bottom_y + trunk_h * 0.52,
           cx + tw_bot * 0.3, bottom_y + trunk_h * 0.65)


def _draw_fruit_shape(c, cx, cy, r, label, fill_color, brown):
    """Coloring-book apple: circle + stem + leaf + label."""
    # Apple body
    c.setFillColor(fill_color)
    c.setStrokeColor(brown)
    c.setLineWidth(1.2)
    c.circle(cx, cy, r, fill=1, stroke=1)

    # Stem
    c.setLineWidth(1.0)
    c.line(cx, cy + r, cx + 0.1 * cm, cy + r + 0.35 * cm)

    # Leaf (small bezier teardrop)
    lx, ly = cx + 0.1 * cm, cy + r + 0.2 * cm
    leaf = c.beginPath()
    leaf.moveTo(lx, ly)
    leaf.curveTo(lx + 0.45 * cm, ly + 0.35 * cm,
                 lx + 0.55 * cm, ly - 0.1 * cm,
                 lx, ly)
    c.setFillColor(HexColor("#B8D4A0"))
    c.setStrokeColor(brown)
    c.setLineWidth(0.7)
    c.drawPath(leaf, fill=1, stroke=1)

    # Label
    c.setFillColor(HexColor("#2C1F13"))
    c.setFont("Times-Roman", 7.5)
    c.drawCentredString(cx, cy - 0.13 * cm, label)


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
    section_h = 9.0 * cm
    brown = HexColor("#6B4C35")

    # Tree on left side
    tree_cx = 4.5 * cm
    tree_bottom = content_top - section_h + 0.5 * cm
    _draw_bare_tree(c, tree_cx, tree_bottom, section_h - 0.5 * cm)

    # Fruits: apple shapes in 3 columns on the right
    all_fruits = [(w, True) for w in good_fruits] + [(w, False) for w in bad_fruits]
    rng = random.Random(77)
    rng.shuffle(all_fruits)

    r = 0.62 * cm          # apple radius
    gap_x = 0.35 * cm
    gap_y = 0.45 * cm
    fruits_x0 = W / 2 + 0.3 * cm
    cols = 3
    col_w = 2 * r + gap_x
    n = len(all_fruits)
    rows = (n + cols - 1) // cols

    for i, (word, is_good) in enumerate(all_fruits):
        col = i % cols
        row = i // cols
        cx_f = fruits_x0 + col * col_w + r
        # +0.4cm to leave room for stem+leaf above
        cy_f = content_top - 0.4 * cm - row * (2 * r + gap_y + 0.4 * cm) - r

        fill_color = HexColor("#D4EDBC") if is_good else HexColor("#F0C8C4")
        _draw_fruit_shape(c, cx_f, cy_f, r, word, fill_color, brown)

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

    # Footer
    draw_footer(c, W)

    c.showPage()
    c.save()
    print(f"Child sheet written: {output_path}")


if __name__ == "__main__":
    main()
