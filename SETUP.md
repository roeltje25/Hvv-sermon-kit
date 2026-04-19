# Setup (technisch)

Deze instructies zijn voor wie de scripts lokaal wil draaien, bijvoorbeeld voor ontwikkeling van het kit zelf.

**Voor gewone gebruikers (oudsten) is dit niet nodig** — zie de [README.md](README.md) voor hoe je het kit via een Claude-gesprek gebruikt.

## Vereisten

- Node.js 18 of hoger
- Python 3.10 of hoger
- `npm` (komt met Node) en `pip`

## Installatie

```bash
git clone https://github.com/<jouw-org>/hvv-sermon-kit.git
cd hvv-sermon-kit

# Node dependencies
npm install

# Python dependencies
pip install -r requirements.txt
```

## Lokaal genereren

### Presentatie

```bash
node scripts/generate_presentation.js example/config.json example/bible_texts.json output.pptx
```

### Kinderblad

```bash
python3 scripts/generate_childsheet.py example/childsheet_config.json output.pdf
```

### Bible URLs genereren

```bash
# Alle 6 talen voor een passage
python3 scripts/bible_urls.py links MAT.9.18-26

# QR code voor een URL
python3 scripts/bible_urls.py qr "https://debijbel.nl/bijbel/NBV21/MAT.9.18-MAT.9.26" qr.png
```

## Repo-structuur

```
hvv-sermon-kit/
├── README.md              Gebruikershandleiding (voor oudsten)
├── CLAUDE.md              Instructies voor Claude
├── SETUP.md               Dit bestand
├── STYLE.md               Stijl-aanpassingen
├── scripts/
│   ├── generate_presentation.js   Config → PPTX
│   ├── generate_childsheet.py     Config → PDF kinderblad
│   └── bible_urls.py              URL + QR helpers
├── example/                Werkende voorbeeldpreek (Matteüs 9:18-26)
│   ├── config.json
│   ├── bible_texts.json
│   ├── childsheet_config.json
│   ├── qr.png
│   ├── point_images/
│   └── story_images/
└── templates/              Lege sjablonen
    ├── config.template.json
    ├── bible_texts.template.json
    └── childsheet_config.template.json
```

## Een nieuwe preek toevoegen

1. Maak een nieuwe map aan, bijvoorbeeld `sermons/lukas-15/`.
2. Kopieer de templates uit `templates/` naar die map.
3. Vul `config.json` in met je preek-specifieke inhoud.
4. Vul `bible_texts.json` met de verzen uit een officiële bron — **nooit uit geheugen**.
5. Voeg afbeeldingen toe in een `point_images/` submap.
6. Genereer:
   ```bash
   node scripts/generate_presentation.js sermons/lukas-15/config.json sermons/lukas-15/bible_texts.json sermons/lukas-15/output.pptx
   ```

## Troubleshooting

### "Missing bible text for language X, verse N"

Je `bible_texts.json` mist een vers. Voeg het toe — het script mag geen verzen zelf invullen.

### "Could not place all words" (woordzoeker)

Teveel woorden voor de rastergrootte. Verhoog `grid_size` in `childsheet_config.json` van 14 naar 16 of 18, óf reduceer het aantal woorden.

### Fonts renderen niet correct

- Voor Arabisch heb je *Traditional Arabic* nodig (ingebouwd in Microsoft Office).
- Voor Farsi heb je *Arabic Typesetting* nodig (ingebouwd in Microsoft Office).
- Op Linux/headless systemen zonder deze fonts worden ze door LibreOffice gesubstitueerd; dit is cosmetisch en beïnvloedt PowerPoint-output op Windows/Mac niet.

### Afbeelding ontbreekt

De presentatie toont automatisch een `[ afbeelding volgt ]` placeholder. Vervang de afbeelding later handmatig in PowerPoint.
