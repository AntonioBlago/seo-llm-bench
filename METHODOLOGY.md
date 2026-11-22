# Methodology

This file documents every task of the benchmark: the exact prompt, a reference answer and the code that scores an answer. The task sections below are generated from [`aufgaben.py`](aufgaben.py) with `python methodology.py`, so they always match the code.

## Setup

| | |
|---|---|
| Tasks | 29, in five categories, fictional data (an e-bike brand "Velora", a heat pump topic) |
| Runs | one run per task and model, temperature 0, seed 42 (local) |
| Local models | Ollama on a cloud VM with one Nvidia Tesla T4 (16 GB VRAM) and 32 GB RAM, context 4096 tokens, max. 800 output tokens (4096 with thinking mode) |
| Claude | Claude Code CLI with a subscription (`claude -p`, no tools, neutral system prompt) |
| Codex / GPT | `codex exec` with a ChatGPT subscription, reasoning effort low |
| DeepSeek | TensorX API, temperature 0, max. 4096 output tokens |
| Dates | 21 November 2026, qwen3:30b-a3b on 22 November 2026 |

Models larger than the VRAM (qwen3:30b-a3b, 19 GB) run with Ollama's automatic offloading: the layers that do not fit are computed on the CPU.

## Scoring principles

Every answer gets a score between 0 and 1. The accuracy of a model is the mean over all 29 tasks.

- **Lists** (e.g. brand keywords, invalid hreflang codes): F1 between the answer and the expected list. Missing and superfluous entries both cost points.
- **Assignments** (e.g. search intent per keyword): share of correctly assigned keys. Where two answers are defensible (e.g. "fahrrad kaufen" as transactional or commercial), both count.
- **Lengths** (titles, meta descriptions, summaries): half the points for the character range, half for the required keyword. Hyphens and spaces count as equal when looking for the keyword.
- **Numbers** (CTR and click calculations): the last number in the answer counts, because models often show their working first. Tolerance 1 percent.
- **JSON-LD, regex, redirect chains:** checked structurally (valid JSON, correct `@type`, regex tested against matching and non-matching queries).

Formatting problems are counted separately and do not cost the content points twice:

- **Format error:** no valid JSON where JSON was required. Score 0 for that task.
- **Wrapped list:** the model returns `{"keywords": [...]}` instead of `[...]`. The list is unpacked, scored normally and flagged `VERPACKT`.
- **Endless loop:** the answer hits the output limit without finishing. Flagged `ENDLOSSCHLEIFE`.

## Decisions I had to make

Some expected answers were not obvious. These are the calls I made, with sources:

- **hreflang (X02):** `es-419` counts as invalid, because Google only supports ISO 3166-1 alpha-2 region codes and names `es-419` explicitly as not supported. `en-UK` is invalid (the code is `GB`). `ch-de` is formally valid (Chamorro, Germany) but most likely a typo, so it is optional: naming it or not costs nothing. Source: [Google Search Central, localized versions](https://developers.google.com/search/docs/specialty/international/localized-versions?hl=en)
- **Removed product (X04):** 410 is the semantically correct answer and gets full points. 404 gets half points, because Google treats all 4xx codes except 429 the same. Source: [Google, HTTP status codes](https://developers.google.com/search/docs/crawling-indexing/http-network-errors?hl=en)
- **CTR model (D01):** the prompt gives the CTR values (position 3 = 2.37 %, position 8 = 0.61 %, from my [Keyword Study 2026](https://www.antonioblago.com/keyword-study-2026-organic-search-ctr)), so the task tests arithmetic, not knowledge.
- **Query fan-out (K05) and outlines (T05):** only the format and the number of entries are checked automatically (8 queries, 5 to 8 headings). Quality is a matter of judgement, the CSV has an empty `manuell` column for your own grading.

## Limitations

- One run per task. With temperature 0 the answers are mostly stable, but small differences between models (0.01 to 0.02) are within noise. Use `--wdh 3 --temp 0.7` to measure variance.
- The expected answers are mine. I documented every call above, but you may disagree, and you can change them in `aufgaben.py`.
- Prompts are in German. Results for English SEO work may differ.
- Cloud times include network latency, subscription CLIs add start-up time per call.
- Codex does not report output tokens per answer, so tokens per second are missing for Codex.

## Reproduce it

1. Install [Ollama](https://ollama.com) and Python 3.9 or newer. No pip packages needed.
2. Pull the models, e.g. `ollama pull qwen3:4b-instruct`. Note: `qwen3:4b` and `qwen3:30b` point to thinking variants.
3. Run `python bench.py --selbsttest`, then `python bench.py <model> [<model> ...]`.
4. Compare your `ergebnisse/<timestamp>.md` with [`ergebnisse/gesamt_2026-11-22_neu.md`](ergebnisse/gesamt_2026-11-22_neu.md).
5. Re-score any result file after changing a check: `python bench.py --bewerten ergebnisse/<file>.csv`.

If you run it on other hardware or with other models, I'd be happy to hear about your results. Open an issue with your summary table.

# Tasks


## Keywords

### K01

**Prompt**

```text
Ordne jedem Keyword genau einen Suchintent zu: informational, kommerziell, transaktional, navigational.
Keywords: fahrrad kaufen | wie pumpe ich einen fahrradreifen auf | e-bike test 2026 | rose bikes login | bester fahrradhelm | fahrradkette ölen | decathlon öffnungszeiten koblenz | trekkingrad günstig bestellen
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: {"keyword": "intent", ...}
```

**Reference answer** (scores 1.0 in the self-test)

```text
{"fahrrad kaufen": "transaktional", "wie pumpe ich einen fahrradreifen auf": "informational", "e-bike test 2026": "kommerziell", "rose bikes login": "navigational", "bester fahrradhelm": "kommerziell", "fahrradkette ölen": "informational", "decathlon öffnungszeiten koblenz": "navigational", "trekkingrad günstig bestellen": "transaktional"}
```

**Scoring**

Share of correctly assigned keys (`_dict_score`). Expected: `{'fahrrad kaufen': ('transaktional', 'kommerziell'), 'wie pumpe ich einen fahrradreifen auf': 'informational', 'e-bike test 2026': ('kommerziell', 'informational'), 'rose bikes login': 'navigational', 'bester fahrradhelm': 'kommerziell', 'fahrradkette ölen': 'informational', 'decathlon öffnungszeiten koblenz': 'navigational', 'trekkingrad günstig bestellen': 'transaktional'}`

### K02

**Prompt**

```text
Unsere Marke heißt Velora (E-Bikes). Welche Keywords sind Brand-Keywords (inklusive Tippfehler der Marke)?
Keywords: velora e-bike | velora erfahrungen | e-bike damen | velra ebike | trekkingrad 28 zoll | velora händler koblenz | e-bike mit mittelmotor
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der Brand-Keywords.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["velora e-bike", "velora erfahrungen", "velra ebike", "velora händler koblenz"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['velora e-bike', 'velora erfahrungen', 'velra ebike', 'velora händler koblenz']`

### K03

**Prompt**

```text
Teile die Keywords in genau 3 thematische Cluster.
Keywords: wärmepumpe kosten | wärmepumpe förderung 2026 | wärmepumpe altbau | photovoltaik speicher | pv anlage einfamilienhaus | solaranlage balkon | dachdämmung kosten | dämmung zwischensparren | fassadendämmung förderung
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: {"Clustername": ["keyword", ...], ...}
```

**Reference answer** (scores 1.0 in the self-test)

```text
{"Wärmepumpe": ["wärmepumpe kosten", "wärmepumpe förderung 2026", "wärmepumpe altbau"], "Solar": ["photovoltaik speicher", "pv anlage einfamilienhaus", "solaranlage balkon"], "Dämmung": ["dachdämmung kosten", "dämmung zwischensparren", "fassadendämmung förderung"]}
```

**Scoring**

```python
def _k03(a, t):
    d = _json(a)
    if not isinstance(d, dict) or len(d) != 3:
        return 0.0, "kein Objekt mit 3 Clustern"
    wo = {_norm(k): i for i, ks in enumerate(d.values()) if isinstance(ks, list) for k in ks}
    paare = [(x, y, gi == gj) for gi, g in enumerate(t["gruppen"]) for gj, h in enumerate(t["gruppen"])
             for x in g for y in h if x < y]
    ok = sum((wo.get(x) is not None and wo.get(x) == wo.get(y)) == gleich for x, y, gleich in paare)
    return round(ok / len(paare), 2), f"{ok}/{len(paare)} Paare richtig"
```

### K04

**Prompt**

```text
Schreibe einen regulären Ausdruck (RE2, für den Search-Console-Filter), der Suchanfragen findet, die mit einem dieser Fragewörter beginnen: wer, was, wie, warum, wo, welche. Groß/Kleinschreibung egal, 'werkzeug' oder 'wohnung' dürfen nicht passen.
Antworte nur mit dem Regex, ohne Erklärung, ohne Anführungszeichen.
```

**Reference answer** (scores 1.0 in the self-test)

```text
^(wer|was|wie|warum|wo|welche)\b
```

**Scoring**

```python
def _k04(a, t):
    rx = a.strip().strip("`").strip().splitlines()[0].strip().strip('"').strip("/") if a.strip() else ""
    try:
        r = re.compile(rx, re.I)
    except re.error as e:
        return 0.0, f"Regex ungültig: {e}"
    falsch = [s for s in t["treffer"] if not r.search(s)] + [s for s in t["kein"] if r.search(s)]
    n = len(t["treffer"]) + len(t["kein"])
    return round(1 - len(falsch) / n, 2), f"falsch: {falsch}" if falsch else "alle Beispiele richtig"
```

### K05

**Prompt**

```text
Ein Nutzer sucht nach 'wärmepumpe altbau'. Nenne 8 unterschiedliche Folgesuchanfragen, die er wahrscheinlich als Nächstes stellt (Query Fan-out).
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste mit 8 Strings.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["wärmepumpe altbau kosten", "wärmepumpe altbau förderung", "wärmepumpe altbau heizkörper", "wärmepumpe altbau erfahrungen", "wärmepumpe altbau vorlauftemperatur", "wärmepumpe altbau dämmung", "wärmepumpe altbau sinnvoll", "wärmepumpe altbau fußbodenheizung"]
```

**Scoring**

```python
def _k05(a, t):
    m = _menge(a)
    if m is None:
        return 0.0, "kein JSON-Array"
    return (len(m) == 8) * 1.0, f"{len(m)} eindeutige Anfragen; Qualität manuell prüfen"
```


## Snippets

### T01

**Prompt**

```text
Schreibe einen Title-Tag für eine Ratgeberseite zum Keyword 'e-bike leasing für arbeitnehmer'. Maximal 60 Zeichen, Keyword am Anfang.
Antworte nur mit dem Title, ohne Anführungszeichen.
```

**Reference answer** (scores 1.0 in the self-test)

```text
E-Bike Leasing für Arbeitnehmer: So sparen Sie bis 40 %
```

**Scoring**

```python
"T01": lambda a, t: _laenge(a, 30, 60, ["e-bike leasing"]),
```

### T02

**Prompt**

```text
Schreibe eine Meta-Description für eine Kategorieseite zum Keyword 'trekkingrad kaufen'. 140 bis 160 Zeichen, mit Handlungsaufforderung.
Antworte nur mit der Description.
```

**Reference answer** (scores 1.0 in the self-test)

```text
Trekkingrad kaufen beim Fachhändler: über 80 Modelle, Beratung vor Ort, Probefahrt und schnelle Lieferung. Jetzt Ihr passendes Trekkingrad finden!
```

**Scoring**

```python
"T02": lambda a, t: _laenge(a, 140, 160, ["trekkingrad"]),
```

### T03

**Prompt**

```text
Erstelle 3 Title-Varianten (je maximal 60 Zeichen) für eine Produktseite 'Velora Tour 5 Trekking-E-Bike'. Jede Variante mit anderem Nutzenversprechen.
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste mit 3 Strings.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["Velora Tour 5: Trekking-E-Bike mit 120 km Reichweite", "Velora Tour 5 kaufen: Gratis Probefahrt", "Velora Tour 5: Leichtes E-Bike für jede Tour"]
```

**Scoring**

```python
def _t03(a, t):
    d = _json(a)
    if not isinstance(d, list) or len(d) != 3:
        return 0.0, "keine Liste mit 3 Titles"
    zu_lang = [len(x) for x in d if len(str(x)) > 60]
    return (0 if zu_lang else 1.0), f"zu lang: {zu_lang}" if zu_lang else "alle bis 60 Zeichen"
```

### T04

**Prompt**

```text
Schreibe einen Alt-Text für dieses Bild: Eine Frau fährt mit einem grauen Trekking-E-Bike auf einem Schotterweg an der Mosel, im Hintergrund Weinberge. Maximal 125 Zeichen, nicht mit 'Bild von' beginnen.
Antworte nur mit dem Alt-Text.
```

**Reference answer** (scores 1.0 in the self-test)

```text
Frau fährt mit grauem Trekking-E-Bike auf Schotterweg an der Mosel, dahinter Weinberge
```

**Scoring**

```python
def _t04(a, t):
    n = len(a.strip().strip('"'))
    if a.strip().lower().startswith(("bild von", "foto von")):
        return 0.0, "beginnt mit 'Bild von'"
    return (20 <= n <= 125) * 1.0, f"{n} Zeichen (Soll 20 bis 125)"
```


## Texte

### T05

**Prompt**

```text
Erstelle eine H2-Gliederung (5 bis 8 Überschriften) für einen Ratgeber zum Keyword 'wärmepumpe altbau'.
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der H2-Überschriften.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["Funktioniert eine Wärmepumpe im Altbau?", "Vorlauftemperatur prüfen", "Heizkörper oder Fußbodenheizung", "Kosten und Förderung", "Heizlastberechnung als erster Schritt"]
```

**Scoring**

```python
def _t05(a, t):
    d = _json(a)
    if not isinstance(d, list):
        return 0.0, "kein JSON-Array"
    return (5 <= len(d) <= 8) * 1.0, f"{len(d)} Überschriften; Qualität manuell prüfen"
```

### T06

**Prompt**

```text
Fasse den Text in höchstens 2 Sätzen und höchstens 220 Zeichen zusammen:
Eine Wärmepumpe kann auch im Altbau effizient arbeiten, wenn die Vorlauftemperatur unter 55 Grad bleibt. Entscheidend sind ausreichend große Heizkörper oder eine Flächenheizung sowie ein hydraulischer Abgleich. Eine Komplettsanierung ist nicht immer nötig; oft reichen der Austausch einzelner Heizkörper und eine bessere Dämmung des Dachs. Vor der Entscheidung sollte eine Heizlastberechnung stehen.
Antworte nur mit der Zusammenfassung.
```

**Reference answer** (scores 1.0 in the self-test)

```text
Eine Wärmepumpe läuft im Altbau effizient, wenn die Vorlauftemperatur unter 55 Grad bleibt. Oft reichen größere Heizkörper, Dachdämmung und eine Heizlastberechnung.
```

**Scoring**

```python
def _t06(a, t):
    saetze = len(re.findall(r"[.!?](\s|$)", a.strip()))
    n = len(a.strip())
    inhalt = "55" in a and "wärmepumpe" in a.lower()
    return round(((n <= 220) + (saetze <= 2) + inhalt) / 3, 2), f"{n} Zeichen, {saetze} Sätze, Kernaussage 55 Grad {inhalt}"
```

### T07

**Prompt**

```text
Ist der folgende Produkttext Keyword-Stuffing? Text: 'Unser E-Bike kaufen lohnt sich. Wer ein E-Bike kaufen will, sollte bei uns E-Bike kaufen, denn E-Bike kaufen war nie leichter. E-Bike kaufen online oder E-Bike kaufen im Laden: E-Bike kaufen bei Velora.'
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: {"stuffing": true/false, "keyword": "..."}
```

**Reference answer** (scores 1.0 in the self-test)

```text
{"stuffing": true, "keyword": "E-Bike kaufen"}
```

**Scoring**

```python
def _t07(a, t):
    d = _json(a)
    if not isinstance(d, dict):
        return 0.0, "kein JSON-Objekt"
    ok = (d.get("stuffing") is True) + ("e-bike kaufen" in _norm(d.get("keyword", "")))
    return ok / 2, f"Antwort {d}"
```

### T08

**Prompt**

```text
Schreibe das Snippet so um, dass es mehr Klicks bekommt (Title max. 60, Description max. 155 Zeichen). Alt: Title 'Wärmepumpe | Firma Müller GmbH', Description 'Wir bieten Wärmepumpen an. Kontaktieren Sie uns.'
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: {"title": "...", "description": "..."}
```

**Reference answer** (scores 1.0 in the self-test)

```text
{"title": "Wärmepumpe vom Fachbetrieb: Beratung und Förderung", "description": "Planung, Einbau und Förderantrag aus einer Hand. Jetzt kostenlose Heizlastberechnung anfragen!"}
```

**Scoring**

```python
def _t08(a, t):
    d = _json(a)
    if not isinstance(d, dict) or not {"title", "description"} <= set(d):
        return 0.0, "Format falsch"
    lt, ld = len(str(d["title"])), len(str(d["description"]))
    return ((lt <= 60) + (ld <= 155)) / 2, f"Title {lt}, Description {ld} Zeichen; Wirkung manuell prüfen"
```

### T09

**Prompt**

```text
Extrahiere aus dem Text alle Fragen und Antworten als FAQ (genau 3).
Text: Wie lange hält ein E-Bike-Akku? Meist 800 bis 1000 Ladezyklen, also 3 bis 5 Jahre. Darf ich den Akku im Winter draußen lassen? Nein, lagern Sie ihn bei 10 bis 20 Grad. Muss ich den Akku vor dem ersten Laden leer fahren? Nein, Lithium-Akkus haben keinen Memory-Effekt.
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: [{"frage": "...", "antwort": "..."}, ...]
```

**Reference answer** (scores 1.0 in the self-test)

```text
[{"frage": "Wie lange hält ein E-Bike-Akku?", "antwort": "3 bis 5 Jahre"}, {"frage": "Darf der Akku im Winter draußen bleiben?", "antwort": "Nein"}, {"frage": "Muss ich ihn vorher leer fahren?", "antwort": "Nein"}]
```

**Scoring**

```python
def _t09(a, t):
    d = _json(a)
    if not isinstance(d, list):
        return 0.0, "kein JSON-Array"
    ok = len(d) == 3 and all(isinstance(x, dict) and x.get("frage") and x.get("antwort") for x in d)
    return ok * 1.0, f"{len(d)} Einträge"
```

### T10

**Prompt**

```text
Extrahiere alle benannten Entitäten (Marken, Orte, Organisationen, Produkte) aus dem Text: 'Velora stellt das Tour 5 auf der Eurobike in Frankfurt vor. Der Motor kommt von Bosch, der Akku wird in Koblenz montiert, der ADAC hat das Rad bereits getestet.'
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der Entitäten.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["Velora", "Tour 5", "Eurobike", "Frankfurt", "Bosch", "Koblenz", "ADAC"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['Velora', 'Tour 5', 'Eurobike', 'Frankfurt', 'Bosch', 'Koblenz', 'ADAC']`


## Technik

### X01

**Prompt**

```text
robots.txt:
User-agent: *
Disallow: /warenkorb/
Disallow: /*?sort=
Disallow: /intern/
Allow: /intern/presse/

Welche URLs darf Googlebot NICHT crawlen?
/warenkorb/schritt-1 | /e-bikes?sort=preis | /e-bikes?farbe=rot | /intern/presse/mitteilung-1 | /intern/team | /blog/warenkorb-tipps
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der gesperrten Pfade.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["/warenkorb/schritt-1", "/e-bikes?sort=preis", "/intern/team"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['/warenkorb/schritt-1', '/e-bikes?sort=preis', '/intern/team']`

### X02

**Prompt**

```text
Welche dieser hreflang-Werte sind ungültig? de | de-AT | en-UK | ch-de | fr-FR | x-default | es-419 | pt-br
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der ungültigen Werte.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["en-UK", "es-419"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['en-UK', 'es-419']`, ignored if present: `['ch-de']`

### X03

**Prompt**

```text
Weiterleitung: /alt -> 301 -> /zwischen -> 302 -> /neu -> 200. Wie viele Weiterleitungen hat die Kette, und welcher Statuscode sollte ersetzt werden?
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: {"hops": Zahl, "ersetzen": Statuscode}
```

**Reference answer** (scores 1.0 in the self-test)

```text
{"hops": 2, "ersetzen": 302}
```

**Scoring**

```python
"X03": lambda a, t: _dict_score(a, t["gold"]), "X04": _x04, "X07": _x07, "X08": _x08,
```

### X04

**Prompt**

```text
Eine Produktseite wurde dauerhaft entfernt, es gibt kein Ersatzprodukt. Welchen HTTP-Statuscode sollte die URL liefern, damit Google sie am schnellsten entfernt? Antworte nur mit der Zahl.
```

**Reference answer** (scores 1.0 in the self-test)

```text
410
```

**Scoring**

```python
def _x04(a, t):
    z = _zahl(a)
    return (1.0 if z == 410 else 0.5 if z == 404 else 0.0), f"Antwort {z} (410 richtig, 404 halb)"
```

### X05

**Prompt**

```text
Welche URLs gehören NICHT in die XML-Sitemap?
/e-bikes (200, indexierbar) | /e-bikes/alt (301 auf /e-bikes) | /suche?q=akku (200, noindex) | /ratgeber/akku (200, Canonical auf /ratgeber/akku-pflege) | /ratgeber/akku-pflege (200, indexierbar) | /aktion-2024 (404)
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der Pfade.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["/e-bikes/alt", "/suche?q=akku", "/ratgeber/akku", "/aktion-2024"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['/e-bikes/alt', '/suche?q=akku', '/ratgeber/akku', '/aktion-2024']`

### X06

**Prompt**

```text
Welche Canonical-Tags sind fehlerhaft?
A: /e-bikes?farbe=rot -> canonical /e-bikes
B: /blog/akku -> canonical /blog/akku
C: /tour-5 -> canonical /tour-5-alt (liefert 404)
D: /kontakt -> canonical /impressum (noindex)
E: /e-bikes?page=2 -> canonical /e-bikes?page=2
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der Buchstaben.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["C", "D"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['C', 'D']`

### X07

**Prompt**

```text
Erzeuge JSON-LD (schema.org FAQPage) für diese zwei Fragen:
1. Wie lange hält ein E-Bike-Akku? 3 bis 5 Jahre.
2. Kann man den Akku nachrüsten? Ja, beim Fachhändler.
Antworte ausschließlich mit gültigem JSON, ohne Erklärung.
```

**Reference answer** (scores 1.0 in the self-test)

```text
{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Wie lange hält ein E-Bike-Akku?", "acceptedAnswer": {"@type": "Answer", "text": "3 bis 5 Jahre."}}, {"@type": "Question", "name": "Kann man den Akku nachrüsten?", "acceptedAnswer": {"@type": "Answer", "text": "Ja, beim Fachhändler."}}]}
```

**Scoring**

```python
def _x07(a, t):
    d = _json(a)
    if not isinstance(d, dict):
        return 0.0, "kein JSON-Objekt"
    fragen = d.get("mainEntity") or []
    ok = [d.get("@type") == "FAQPage", "schema.org" in str(d.get("@context", "")), len(fragen) == 2,
          all(f.get("@type") == "Question" and isinstance(f.get("acceptedAnswer"), dict)
              and f["acceptedAnswer"].get("@type") == "Answer" for f in fragen if isinstance(f, dict))]
    return round(sum(ok) / 4, 2), f"Prüfpunkte {ok}"
```

### X08

**Prompt**

```text
Erzeuge JSON-LD (schema.org BreadcrumbList) für den Pfad Startseite (https://velora.example/) > E-Bikes (https://velora.example/e-bikes/) > Trekking (https://velora.example/e-bikes/trekking/).
Antworte ausschließlich mit gültigem JSON, ohne Erklärung.
```

**Reference answer** (scores 1.0 in the self-test)

```text
{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Startseite", "item": "https://velora.example/"}, {"@type": "ListItem", "position": 2, "name": "E-Bikes", "item": "https://velora.example/e-bikes/"}, {"@type": "ListItem", "position": 3, "name": "Trekking", "item": "https://velora.example/e-bikes/trekking/"}]}
```

**Scoring**

```python
def _x08(a, t):
    d = _json(a)
    if not isinstance(d, dict):
        return 0.0, "kein JSON-Objekt"
    el = d.get("itemListElement") or []
    ok = [d.get("@type") == "BreadcrumbList", len(el) == 3,
          [e.get("position") for e in el if isinstance(e, dict)] in ([1, 2, 3], ["1", "2", "3"]),
          all("velora.example" in str(e.get("item", "")) for e in el if isinstance(e, dict))]
    return round(sum(ok) / 4, 2), f"Prüfpunkte {ok}"
```


## Analyse

### D01

**Prompt**

```text
CTR-Modell: Position 3 = 2,37 %, Position 8 = 0,61 %. Eine Seite rankt auf Position 8 mit 40.000 Impressionen pro Monat. Wie viele zusätzliche Klicks pro Monat bringt Position 3? Antworte nur mit der Zahl.
```

**Reference answer** (scores 1.0 in the self-test)

```text
704
```

**Scoring**

```python
def _d01(a, t):
    z = _zahl(a)
    return (1.0 if z is not None and abs(z - t["zahl"]) <= t["zahl"] * 0.01 else 0.0), f"Antwort {z}, Soll {t['zahl']}"
```

### D02

**Prompt**

```text
Search-Console-Daten (Suchanfrage; Impressionen; CTR; Position):
e-bike leasing; 8200; 1,1 %; 7,4
trekkingrad; 15000; 0,4 %; 18,2
velora; 3000; 38 %; 1,0
e-bike akku laden; 900; 2,0 %; 6,1
fahrradhelm test; 5400; 6,2 %; 4,8
e-bike versicherung; 2600; 0,9 %; 24,0
pedelec gebraucht; 1200; 3,1 %; 11,3
Quick Win = Position 4 bis 20, mindestens 1000 Impressionen, CTR unter 5 %. Welche Suchanfragen sind Quick Wins?
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der Suchanfragen.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["e-bike leasing", "trekkingrad", "pedelec gebraucht"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['e-bike leasing', 'trekkingrad', 'pedelec gebraucht']`

### D03

**Prompt**

```text
Ranking-Daten (Suchanfrage; URL; Klicks):
e-bike akku; /ratgeber/akku; 120
e-bike akku; /shop/akkus; 95
trekkingrad; /e-bikes/trekking; 300
akku laden; /ratgeber/akku-laden; 40
akku laden; /ratgeber/akku; 38
fahrradhelm; /zubehoer/helme; 210
Bei welchen Suchanfragen konkurrieren mehrere eigene URLs (Kannibalisierung)?
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der Suchanfragen.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["e-bike akku", "akku laden"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['e-bike akku', 'akku laden']`

### D04

**Prompt**

```text
Welche URLs haben doppelte Title-Tags? Gib jede betroffene URL an.
/e-bikes: E-Bikes kaufen | Velora
/e-bikes?page=2: E-Bikes kaufen | Velora
/trekking: Trekking-E-Bikes | Velora
/kontakt: Kontakt | Velora
/impressum: Velora
/datenschutz: Velora
/blog: Ratgeber | Velora
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste der URLs.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["/e-bikes", "/e-bikes?page=2", "/impressum", "/datenschutz"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['/e-bikes', '/e-bikes?page=2', '/impressum', '/datenschutz']`

### D05

**Prompt**

```text
Ein neuer Artikel heißt 'E-Bike-Akku richtig pflegen'. Wähle die 3 passendsten Seiten für interne Links:
/ratgeber/akku-laden | /ratgeber/winterlagerung | /zubehoer/helme | /ratgeber/akku-reichweite | /ueber-uns | /blog/radtouren-mosel
Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste mit 3 Pfaden.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["/ratgeber/akku-laden", "/ratgeber/winterlagerung", "/ratgeber/akku-reichweite"]
```

**Scoring**

F1 between answer list and expected list (`_mengen_score`). Expected: `['/ratgeber/akku-laden', '/ratgeber/winterlagerung', '/ratgeber/akku-reichweite']`

### D06

**Prompt**

```text
Eigene H2: Was kostet eine Wärmepumpe? | Förderung 2026 | Wärmepumpe im Altbau
Wettbewerber-H2: Kosten im Überblick | Förderung und Zuschüsse | Lautstärke und Abstand zum Nachbarn | Stromtarif für Wärmepumpen | Altbau: geht das? | Wartung und Lebensdauer
Welche Themen fehlen bei uns? Antworte ausschließlich mit gültigem JSON, ohne Erklärung. Format: Liste kurzer Themenbegriffe.
```

**Reference answer** (scores 1.0 in the self-test)

```text
["Lautstärke", "Stromtarif", "Wartung"]
```

**Scoring**

```python
def _d06(a, t):
    m = _menge(a)
    if m is None:
        return 0.0, "kein JSON-Array"
    text = " ".join(m)
    fehlt = [s for s in t["stichworte"] if s not in text]
    zu_viel = [x for x in m if any(w in x for w in ("kosten", "förder", "altbau"))]
    score = (len(t["stichworte"]) - len(fehlt)) / len(t["stichworte"]) - 0.2 * len(zu_viel)
    return round(max(score, 0), 2), f"fehlt {fehlt}, schon vorhanden genannt {zu_viel}"
```
