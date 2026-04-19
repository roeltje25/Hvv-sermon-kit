/**
 * HVV Sermon Kit — Presentation Generator
 *
 * Generates a PowerPoint presentation in the parchment style from a config.
 * Usage:  node generate_presentation.js <config.json> <bible_texts.json> <output.pptx>
 *
 * IMPORTANT:
 *  - Arabic font is FIXED to "Traditional Arabic" (not configurable).
 *  - Farsi font is FIXED to "Arabic Typesetting" (not configurable).
 *  - RTL direction for Arabic and Farsi is FIXED (not configurable).
 *  - All other styling follows the parchment palette by default.
 *
 * The bible_texts.json MUST contain translations supplied by the user.
 * The script does NOT and MUST NOT fabricate verses.
 */

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// -----------------------------------------------------------------------------
// FIXED FONT & DIRECTION CONSTANTS — NOT CONFIGURABLE
// -----------------------------------------------------------------------------
const ARABIC_FONT = "Traditional Arabic";
const FARSI_FONT = "Arabic Typesetting";
const RTL_LANGS = new Set(["ar", "fa"]);

// Native numeral systems for verse numbers
const ARABIC_INDIC_DIGITS = ["٠","١","٢","٣","٤","٥","٦","٧","٨","٩"];
const PERSIAN_DIGITS      = ["۰","۱","۲","۳","۴","۵","۶","۷","۸","۹"];
const RLM = "\u200F"; // Right-to-Left Mark

function toNativeNum(n, digitSet) {
  return String(n).split("").map(d => digitSet[parseInt(d)]).join("");
}

// -----------------------------------------------------------------------------
// DEFAULT PALETTE (can be overridden by config.style)
// -----------------------------------------------------------------------------
const DEFAULT_PALETTE = {
  parchmentBg:  "EDE8DC",
  cardBg:       "F5F0E8",
  cardBorder:   "C8B99A",
  headerBand:   "D9CEB8",
  headerColor:  "3D2B1F",
  labelColor:   "6B4C35",
  textColor:    "2C1F13",
  dividerColor: "C8B99A"
};

// -----------------------------------------------------------------------------
// LANGUAGE METADATA
// -----------------------------------------------------------------------------
const LANG_META = {
  nl: { label: "Nederlands (NBV)",   font: "Georgia",           size: 10,   numSize: 8  },
  en: { label: "English (NIV)",      font: "Georgia",           size: 10,   numSize: 8  },
  fr: { label: "Français (BDS)",     font: "Georgia",           size: 10,   numSize: 8  },
  ar: { label: "عربي (GNA2025)",     font: ARABIC_FONT,         size: 14,   numSize: 12 },
  fa: { label: "فارسی (NMV)",        font: FARSI_FONT,          size: 14,   numSize: 12 },
  tr: { label: "Türkçe (TCL02)",     font: "Georgia",           size: 10,   numSize: 8  }
};

// -----------------------------------------------------------------------------
// MAIN
// -----------------------------------------------------------------------------
async function main() {
  const [configPath, bibleTextsPath, outputPath] = process.argv.slice(2);
  if (!configPath || !bibleTextsPath || !outputPath) {
    console.error("Usage: node generate_presentation.js <config.json> <bible_texts.json> <output.pptx>");
    process.exit(1);
  }

  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const bibleTexts = JSON.parse(fs.readFileSync(bibleTextsPath, "utf8"));

  const palette = Object.assign({}, DEFAULT_PALETTE, config.style && config.style.palette || {});
  const languages = config.languages || ["nl", "en", "fr", "ar", "fa", "tr"];
  if (languages.length > 6) {
    throw new Error("Maximum 6 languages supported (3x2 grid).");
  }

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.title = config.passage_label || "Preek";

  buildTitleSlide(pres, config, palette);
  buildBibleTextSlides(pres, config, bibleTexts, languages, palette);
  buildOutlineSlide(pres, config, palette);
  buildPointSlides(pres, config, palette);

  await pres.writeFile({ fileName: outputPath });
  console.log(`Presentation written: ${outputPath}`);
}

// -----------------------------------------------------------------------------
// SLIDE: TITLE
// -----------------------------------------------------------------------------
function buildTitleSlide(pres, config, P) {
  const SW = 10, SH = 5.625;
  const slide = pres.addSlide();
  slide.background = { color: P.parchmentBg };

  // Top ornament
  slide.addShape(pres.shapes.LINE, {
    x: 2.5, y: 0.45, w: 5, h: 0,
    line: { color: P.cardBorder, width: 1 }
  });
  slide.addShape(pres.shapes.DIAMOND, {
    x: 4.9, y: 0.37, w: 0.2, h: 0.15,
    fill: { color: P.cardBorder }, line: { color: P.cardBorder }
  });

  // Main title (Dutch / primary)
  slide.addText(config.title.nl, {
    x: 0.5, y: 0.8, w: SW - 1, h: 0.9,
    fontSize: 44, fontFace: "Georgia", italic: true,
    color: P.headerColor, align: "center", valign: "middle", margin: 0
  });

  // Translations of the title
  if (config.title.en) {
    slide.addText(config.title.en, {
      x: 0.5, y: 1.75, w: SW - 1, h: 0.45,
      fontSize: 20, fontFace: "Georgia", italic: true,
      color: P.labelColor, align: "center", valign: "middle", margin: 0
    });
  }
  if (config.title.ar) {
    slide.addText(config.title.ar, {
      x: 0.5, y: 2.25, w: SW - 1, h: 0.5,
      fontSize: 26, fontFace: ARABIC_FONT,
      color: P.labelColor, align: "center", valign: "middle", margin: 0,
      rtlMode: true
    });
  }
  if (config.title.fa) {
    slide.addText(config.title.fa, {
      x: 0.5, y: 2.80, w: SW - 1, h: 0.5,
      fontSize: 26, fontFace: FARSI_FONT,
      color: P.labelColor, align: "center", valign: "middle", margin: 0,
      rtlMode: true
    });
  }

  // Passage label
  slide.addText(config.passage_label, {
    x: 0.5, y: 3.4, w: SW - 1, h: 0.4,
    fontSize: 16, fontFace: "Georgia", italic: true,
    color: P.labelColor, align: "center", valign: "middle", margin: 0
  });

  slide.addShape(pres.shapes.LINE, {
    x: 3.5, y: 3.95, w: 3, h: 0,
    line: { color: P.cardBorder, width: 0.75 }
  });

  // QR code (optional)
  if (config.qr_image) {
    const qrSize = 1.15;
    slide.addImage({
      path: config.qr_image,
      x: (SW - qrSize) / 2, y: 4.10, w: qrSize, h: qrSize
    });
    slide.addText(config.qr_caption || "Scan voor de bijbelpassage", {
      x: 0.5, y: 5.28, w: SW - 1, h: 0.25,
      fontSize: 10, fontFace: "Georgia", italic: true,
      color: P.labelColor, align: "center", valign: "middle", margin: 0
    });
  }

  slide.addShape(pres.shapes.LINE, {
    x: 2.5, y: 5.55, w: 5, h: 0,
    line: { color: P.cardBorder, width: 1 }
  });
}

// -----------------------------------------------------------------------------
// BIBLE TEXT SLIDES
// -----------------------------------------------------------------------------
function buildBibleTextSlides(pres, config, bibleTexts, languages, P) {
  const SW = 10, SH = 5.625;
  const MARGIN = 0.20;
  const HDR_H = 0.55;
  const GRID_TOP = HDR_H + 0.15;
  const GRID_H = SH - GRID_TOP - 0.15;
  const CARD_W = (SW - MARGIN * 2 - 0.10 * (languages.length > 3 ? 2 : languages.length - 1)) / Math.min(3, languages.length);
  const COL_GAP = 0.10;

  // verse_groups: array of arrays of verse numbers, e.g. [[18,19],[20,21,22],[23,24,25,26]]
  for (const group of config.verse_groups) {
    const slide = pres.addSlide();
    slide.background = { color: P.parchmentBg };

    const first = group[0], last = group[group.length - 1];
    const shortLabel = config.passage_label_short || config.passage_label;
    const slideLabel = group.length > 1
      ? `${shortLabel}:${first}–${last}`
      : `${shortLabel}:${first}`;

    // Header bar
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: SW, h: HDR_H,
      fill: { color: P.headerBand }, line: { color: P.headerBand }
    });
    slide.addShape(pres.shapes.LINE, {
      x: MARGIN, y: HDR_H - 0.01, w: SW - MARGIN * 2, h: 0,
      line: { color: P.cardBorder, width: 0.75 }
    });
    slide.addText(slideLabel, {
      x: MARGIN, y: 0, w: 5, h: HDR_H,
      fontSize: 19, fontFace: "Georgia", bold: true,
      color: P.headerColor, valign: "middle", align: "left", margin: 0
    });
    slide.addText(config.passage_label, {
      x: 5.5, y: 0, w: SW - 5.5 - MARGIN, h: HDR_H,
      fontSize: 10.5, fontFace: "Georgia", italic: true,
      color: P.labelColor, valign: "middle", align: "right", margin: 0
    });

    // Card grid
    const nCols = Math.min(3, languages.length);
    const nRows = Math.ceil(languages.length / nCols);
    const ROW_GAP = 0.08;
    const CARD_H_ACTUAL = (GRID_H - ROW_GAP * (nRows - 1)) / nRows;

    languages.forEach((lang, i) => {
      const col = i % nCols;
      const row = Math.floor(i / nCols);
      const cx = MARGIN + col * (CARD_W + COL_GAP);
      const cy = GRID_TOP + row * (CARD_H_ACTUAL + ROW_GAP);
      drawLangCard(pres, slide, lang, group, bibleTexts, cx, cy, CARD_W, CARD_H_ACTUAL, P);
    });
  }
}

function drawLangCard(pres, slide, lang, group, bibleTexts, cx, cy, cardW, cardH, P) {
  const meta = LANG_META[lang];
  if (!meta) throw new Error(`Unknown language: ${lang}`);
  const isRTL = RTL_LANGS.has(lang);

  // Card background
  slide.addShape(pres.shapes.RECTANGLE, {
    x: cx, y: cy, w: cardW, h: cardH,
    fill: { color: P.cardBg },
    line: { color: P.cardBorder, width: 0.75 },
    shadow: { type: "outer", color: "000000", blur: 3, offset: 1, angle: 135, opacity: 0.10 }
  });

  // Language label
  const LABEL_H = 0.22;
  slide.addText(meta.label, {
    x: cx + 0.10, y: cy + 0.06,
    w: cardW - 0.20, h: LABEL_H,
    fontSize: 8, fontFace: "Georgia", bold: true, italic: true,
    color: P.labelColor,
    align: isRTL ? "right" : "left",
    margin: 0
  });

  // Divider
  slide.addShape(pres.shapes.LINE, {
    x: cx + 0.10, y: cy + 0.06 + LABEL_H,
    w: cardW - 0.20, h: 0,
    line: { color: P.dividerColor, width: 0.5 }
  });

  // Verse content
  const TEXT_TOP = cy + 0.06 + LABEL_H + 0.07;
  const TEXT_H = cardH - (TEXT_TOP - cy) - 0.06;

  const textRuns = [];
  group.forEach((verseNum, vi) => {
    const verseText = bibleTexts[lang] && bibleTexts[lang][verseNum];
    if (!verseText) {
      throw new Error(
        `Missing bible text for language "${lang}", verse ${verseNum}. ` +
        `All verses must be provided in bible_texts.json — Claude is NOT allowed to fabricate them.`
      );
    }
    let numStr;
    if (lang === "ar") {
      numStr = RLM + toNativeNum(verseNum, ARABIC_INDIC_DIGITS) + "\u00A0";
    } else if (lang === "fa") {
      numStr = RLM + toNativeNum(verseNum, PERSIAN_DIGITS) + "\u00A0";
    } else {
      numStr = `${verseNum}\u00A0`;
    }
    textRuns.push({
      text: numStr,
      options: { bold: true, fontSize: meta.numSize, color: P.labelColor, fontFace: meta.font }
    });
    const isLast = vi === group.length - 1;
    const trailing = isLast ? "" : (isRTL ? RLM + "\u00A0" : "\u00A0");
    textRuns.push({
      text: verseText + trailing,
      options: { bold: false, fontSize: meta.size, color: P.textColor, fontFace: meta.font }
    });
  });

  slide.addText(textRuns, {
    x: cx + 0.10, y: TEXT_TOP,
    w: cardW - 0.20, h: TEXT_H,
    align: isRTL ? "right" : "left",
    valign: "top",
    wrap: true,
    margin: 0,
    rtlMode: isRTL
  });
}

// -----------------------------------------------------------------------------
// OUTLINE SLIDE
// -----------------------------------------------------------------------------
function buildOutlineSlide(pres, config, P) {
  if (!config.points || config.points.length === 0) return;

  const SW = 10, SH = 5.625;
  const MARGIN = 0.20;
  const HDR_H = 0.55;

  const slide = pres.addSlide();
  slide.background = { color: P.parchmentBg };

  // Header bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: SW, h: HDR_H,
    fill: { color: P.headerBand }, line: { color: P.headerBand }
  });
  slide.addShape(pres.shapes.LINE, {
    x: MARGIN, y: HDR_H - 0.01, w: SW - MARGIN * 2, h: 0,
    line: { color: P.cardBorder, width: 0.75 }
  });
  slide.addText(config.passage_label, {
    x: 5.5, y: 0, w: SW - 5.5 - MARGIN, h: HDR_H,
    fontSize: 10.5, fontFace: "Georgia", italic: true,
    color: P.labelColor, valign: "middle", align: "right", margin: 0
  });

  // Adaptive item height based on number of points
  const n = config.points.length;
  const itemH = Math.min(1.05, (SH - HDR_H - 0.3) / n);
  const totalH = n * itemH;
  const startY = HDR_H + (SH - HDR_H - totalH) / 2;

  config.points.forEach((pt, i) => {
    const y = startY + i * itemH;

    // Big number
    slide.addText(String(i + 1), {
      x: 1.5, y: y, w: 0.8, h: itemH,
      fontSize: 48, fontFace: "Georgia", italic: true,
      color: P.labelColor, align: "center", valign: "middle", margin: 0
    });

    // Vertical divider
    slide.addShape(pres.shapes.LINE, {
      x: 2.5, y: y + 0.15, w: 0, h: itemH - 0.3,
      line: { color: P.cardBorder, width: 0.75 }
    });

    // Dutch title
    slide.addText(pt.title.nl, {
      x: 2.75, y: y + 0.05, w: 6, h: 0.45,
      fontSize: 22, fontFace: "Georgia", bold: true,
      color: P.headerColor, align: "left", valign: "middle", margin: 0
    });

    // Translations row (only if space allows — at least 4 points still fits)
    if (itemH >= 0.85) {
      if (pt.title.en) {
        slide.addText(pt.title.en, {
          x: 2.75, y: y + 0.55, w: 2.3, h: 0.4,
          fontSize: 12, fontFace: "Georgia", italic: true,
          color: P.labelColor, align: "left", valign: "middle", margin: 0
        });
      }
      if (pt.title.ar) {
        slide.addText(pt.title.ar, {
          x: 5.2, y: y + 0.55, w: 2.3, h: 0.4,
          fontSize: 16, fontFace: ARABIC_FONT,
          color: P.labelColor, align: "center", valign: "middle", margin: 0,
          rtlMode: true
        });
      }
      if (pt.title.fa) {
        slide.addText(pt.title.fa, {
          x: 7.6, y: y + 0.55, w: 2.0, h: 0.4,
          fontSize: 16, fontFace: FARSI_FONT,
          color: P.labelColor, align: "right", valign: "middle", margin: 0,
          rtlMode: true
        });
      }
    }
  });
}

// -----------------------------------------------------------------------------
// POINT SLIDES
// -----------------------------------------------------------------------------
function buildPointSlides(pres, config, P) {
  if (!config.points) return;

  const SW = 10, SH = 5.625;
  const MARGIN = 0.20;
  const HDR_H = 0.55;

  config.points.forEach((pt, idx) => {
    const slide = pres.addSlide();
    slide.background = { color: P.parchmentBg };
    const num = idx + 1;

    // Header
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: SW, h: HDR_H,
      fill: { color: P.headerBand }, line: { color: P.headerBand }
    });
    slide.addShape(pres.shapes.LINE, {
      x: MARGIN, y: HDR_H - 0.01, w: SW - MARGIN * 2, h: 0,
      line: { color: P.cardBorder, width: 0.75 }
    });
    slide.addText(`${num}. ${pt.title.nl}`, {
      x: MARGIN, y: 0, w: 7, h: HDR_H,
      fontSize: 19, fontFace: "Georgia", bold: true,
      color: P.headerColor, valign: "middle", align: "left", margin: 0
    });
    slide.addText(config.passage_label, {
      x: 7, y: 0, w: SW - 7 - MARGIN, h: HDR_H,
      fontSize: 10.5, fontFace: "Georgia", italic: true,
      color: P.labelColor, valign: "middle", align: "right", margin: 0
    });

    // Image area (square frame, cover sizing)
    const imgAreaX = MARGIN;
    const imgAreaY = HDR_H + 0.3;
    const imgAreaW = 5.0;
    const imgAreaH = SH - imgAreaY - 0.3;

    slide.addShape(pres.shapes.RECTANGLE, {
      x: imgAreaX, y: imgAreaY, w: imgAreaW, h: imgAreaH,
      fill: { color: "FFFFFF" },
      line: { color: P.cardBorder, width: 1 },
      shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 }
    });

    if (pt.image && fs.existsSync(pt.image)) {
      slide.addImage({
        path: pt.image,
        x: imgAreaX + 0.05, y: imgAreaY + 0.05,
        w: imgAreaW - 0.10, h: imgAreaH - 0.10,
        sizing: { type: "cover", w: imgAreaW - 0.10, h: imgAreaH - 0.10 }
      });
    } else {
      slide.addText("[ afbeelding volgt ]", {
        x: imgAreaX, y: imgAreaY, w: imgAreaW, h: imgAreaH,
        fontSize: 14, fontFace: "Georgia", italic: true,
        color: P.cardBorder, align: "center", valign: "middle", margin: 0
      });
    }

    // Right text column
    const txtX = imgAreaX + imgAreaW + 0.4;
    const txtW = SW - txtX - MARGIN;
    const txtY = HDR_H + 0.5;

    slide.addText(String(num), {
      x: txtX, y: txtY, w: txtW, h: 1.4,
      fontSize: 110, fontFace: "Georgia", italic: true,
      color: P.cardBorder, align: "left", valign: "top", margin: 0
    });
    slide.addShape(pres.shapes.LINE, {
      x: txtX, y: txtY + 1.55, w: 1.8, h: 0,
      line: { color: P.cardBorder, width: 1.25 }
    });
    slide.addText(pt.title.nl, {
      x: txtX, y: txtY + 1.75, w: txtW, h: 0.9,
      fontSize: 26, fontFace: "Georgia", bold: true,
      color: P.headerColor, align: "left", valign: "top", margin: 0, wrap: true
    });

    if (pt.title.en) {
      slide.addText(pt.title.en, {
        x: txtX, y: txtY + 2.75, w: txtW, h: 0.4,
        fontSize: 15, fontFace: "Georgia", italic: true,
        color: P.labelColor, align: "left", valign: "top", margin: 0
      });
    }
    if (pt.title.ar) {
      slide.addText(pt.title.ar, {
        x: txtX, y: txtY + 3.2, w: txtW, h: 0.5,
        fontSize: 20, fontFace: ARABIC_FONT,
        color: P.labelColor, align: "left", valign: "top", margin: 0,
        rtlMode: true
      });
    }
    if (pt.title.fa) {
      slide.addText(pt.title.fa, {
        x: txtX, y: txtY + 3.75, w: txtW, h: 0.5,
        fontSize: 20, fontFace: FARSI_FONT,
        color: P.labelColor, align: "left", valign: "top", margin: 0,
        rtlMode: true
      });
    }
  });
}

main().catch(err => {
  console.error("ERROR:", err.message);
  process.exit(1);
});
