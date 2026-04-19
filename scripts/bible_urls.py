#!/usr/bin/env python3
"""
HVV Sermon Kit — Bible URL & QR helper

Generates links to a bible passage in multiple translations, and optionally a QR code.

Usage:
  python3 bible_urls.py links <passage>
      Prints translation URLs as JSON for the given passage.
      Passage format: "MAT.9.18-26" (OSIS-like: BOOK.CHAPTER.VERSES)

  python3 bible_urls.py qr <url> <output.png>
      Generates a QR code PNG styled in the parchment palette.
"""

import json
import sys
import re


# -----------------------------------------------------------------------------
# BIBLE URL TEMPLATES
# -----------------------------------------------------------------------------
#
# bible.com passage URLs follow the pattern:
#     https://www.bible.com/bible/{version_id}/{BOOK}.{CHAPTER}.{VERSES}.{VERSION_CODE}
#
# For a verse range: use "18-26" (no spaces, hyphen).
# For a single verse: just "18".
#
# debijbel.nl uses a different pattern:
#     https://debijbel.nl/bijbel/NBV21/{BOOK}.{CHAPTER}.{START}-{BOOK}.{CHAPTER}.{END}
#
VERSIONS = {
    # Dutch uses debijbel.nl (not bible.com) per user preference
    "nl": {
        "label": "Nederlands (NBV21)",
        "provider": "debijbel.nl",
        "version_code": "NBV21",
    },
    "en": {
        "label": "English (NIV)",
        "provider": "bible.com",
        "version_id": 111,
        "version_code": "NIV",
    },
    "fr": {
        "label": "Français (BDS)",
        "provider": "bible.com",
        "version_id": 21,
        "version_code": "BDS",
    },
    "ar": {
        "label": "عربي (GNA2025)",
        "provider": "bible.com",
        "version_id": 67,
        "version_code": "GNA2025",
    },
    "fa": {
        "label": "فارسی (NMV)",
        "provider": "bible.com",
        "version_id": 118,
        "version_code": "nmv",
    },
    "tr": {
        "label": "Türkçe (TCL02)",
        "provider": "bible.com",
        "version_id": 170,
        "version_code": "TCL02",
    },
}


def parse_passage(passage):
    """
    Parses a passage string like "MAT.9.18-26" into parts.
    Returns dict: {book, chapter, verses (str), start, end}.
    """
    m = re.match(r"^([A-Z1-3]+)\.(\d+)\.(\d+)(?:-(\d+))?$", passage)
    if not m:
        raise ValueError(
            f"Invalid passage format: '{passage}'. "
            f"Expected: BOOK.CHAPTER.START[-END], e.g. 'MAT.9.18-26' or 'LUK.15.11-32'."
        )
    book, chapter, start, end = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
    end = int(end) if end else start
    verses = f"{start}-{end}" if start != end else str(start)
    return {"book": book, "chapter": chapter, "start": start, "end": end, "verses": verses}


def build_url(lang, passage):
    """Build a URL for the given language and passage."""
    v = VERSIONS.get(lang)
    if not v:
        raise ValueError(f"Unknown language code: {lang}")
    p = parse_passage(passage)

    if v["provider"] == "debijbel.nl":
        # debijbel.nl: https://debijbel.nl/bijbel/NBV21/MAT.9.18-MAT.9.26
        if p["start"] == p["end"]:
            return f"https://debijbel.nl/bijbel/{v['version_code']}/{p['book']}.{p['chapter']}.{p['start']}"
        return (
            f"https://debijbel.nl/bijbel/{v['version_code']}/"
            f"{p['book']}.{p['chapter']}.{p['start']}-{p['book']}.{p['chapter']}.{p['end']}"
        )

    # bible.com
    return (
        f"https://www.bible.com/bible/{v['version_id']}/"
        f"{p['book']}.{p['chapter']}.{p['verses']}.{v['version_code']}"
    )


def build_all_urls(passage, languages=None):
    """Return a dict of lang -> URL for the given passage."""
    if languages is None:
        languages = list(VERSIONS.keys())
    return {lang: build_url(lang, passage) for lang in languages}


# -----------------------------------------------------------------------------
# QR CODE GENERATION
# -----------------------------------------------------------------------------
def generate_qr(url, output_path, fg="#3D2B1F", bg="#F5F0E8"):
    """Generate a QR code PNG styled in the parchment palette."""
    try:
        import qrcode
    except ImportError:
        raise RuntimeError("qrcode package required. Install with: pip install qrcode[pil]")
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color=bg)
    img.save(output_path)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def _usage():
    print(__doc__, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        _usage()
    cmd = sys.argv[1]

    if cmd == "links":
        if len(sys.argv) != 3:
            _usage()
        passage = sys.argv[2]
        urls = build_all_urls(passage)
        # Pretty-print with labels
        out = {lang: {"label": VERSIONS[lang]["label"], "url": urls[lang]} for lang in urls}
        print(json.dumps(out, ensure_ascii=False, indent=2))

    elif cmd == "qr":
        if len(sys.argv) != 4:
            _usage()
        url = sys.argv[2]
        output = sys.argv[3]
        generate_qr(url, output)
        print(f"QR code written: {output}")

    else:
        _usage()


if __name__ == "__main__":
    main()
