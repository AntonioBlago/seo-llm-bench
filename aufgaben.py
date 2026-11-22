"""SEO-Aufgaben für den Modellvergleich (fiktive Daten, keine Kundendaten).

Jede Aufgabe: id, kategorie, prompt, ideal (Musterantwort für den Selbsttest), check(antwort) -> (score 0..1 | None, hinweis).
score None = nur manuell bewerten. Neue Aufgabe: Dict an AUFGABEN anhängen, `python bench.py --selbsttest` muss grün bleiben.
"""
import json
import re

# ---------- Hilfen ----------

def _json(text):
    """Erstes JSON-Objekt/-Array aus der Antwort ziehen (Code-Zäune und Vortext tolerieren)."""
    text = re.sub(r"```(?:json)?", "", text)
    paare = sorted((("{", "}"), ("[", "]")), key=lambda p: text.find(p[0]) % (len(text) + 1))  # was zuerst kommt
    for start, ende in paare:
        a, b = text.find(start), text.rfind(ende)
        if a != -1 and b > a:
            try:
                return json.loads(text[a:b + 1])
            except ValueError:
                pass
    return None


def _norm(s):
    return re.sub(r"\s+", " ", str(s).strip().lower().strip(".\"'"))


def _menge(antwort):
    """JSON-Liste als Menge normalisierter Strings, None bei Formatfehler."""
    d = _json(antwort)
    if not isinstance(d, list):
        return None
    # Objekte wie {"entität": "ADAC", "typ": "Organisation"}: erster Textwert zählt
    return {_norm(next((v for v in x.values() if isinstance(v, str)), "") if isinstance(x, dict) else x) for x in d}


def _mengen_score(antwort, gold, optional=()):
    """F1 zwischen Antwortliste und Goldliste: bestraft Fehlende und Überflüssige; optionale Werte zählen nie."""
    m = _menge(antwort)
    if m is None:
        return 0.0, "kein JSON-Array"
    m -= {_norm(o) for o in optional}
    gold = {_norm(g) for g in gold}
    treffer = len(m & gold)
    if not treffer:
        return 0.0, f"0 Treffer, Antwort {sorted(m)}"
    p, r = treffer / len(m), treffer / len(gold)
    return round(2 * p * r / (p + r), 2), f"fehlt {sorted(gold - m)}, zu viel {sorted(m - gold)}"


SYNONYME = {"transactional": "transaktional", "commercial": "kommerziell", "kommerzielle": "kommerziell",
            "informativ": "informational", "informationell": "informational", "navigation": "navigational"}


def _dict_score(antwort, gold):
    """Anteil richtig zugeordneter Schlüssel in einem JSON-Objekt."""
    d = _json(antwort)
    if not isinstance(d, dict):
        return 0.0, "kein JSON-Objekt"
    d = {_norm(k): SYNONYME.get(_norm(v), _norm(v)) for k, v in d.items()}
    # Sollwert als Tupel = mehrere vertretbare Antworten
    falsch = [k for k, v in gold.items() if d.get(_norm(k)) not in {_norm(x) for x in (v if isinstance(v, tuple) else (v,))}]
    return round(1 - len(falsch) / len(gold), 2), f"falsch: {falsch}" if falsch else "alles richtig"


def _zahl(antwort):
    zahlen = re.findall(r"-?\d[\d.,]*", antwort.replace(" ", "").replace(" ", ""))
    if not zahlen:
        return None
    z = zahlen[-1].rstrip(".,")  # letzte Zahl: Modelle rechnen oft erst vor, Ergebnis steht am Ende
    z = z.replace(".", "").replace(",", ".") if re.search(r"\d\.\d{3}(\D|$)", z) or "," in z else z
    try:
        return float(z)
    except ValueError:
        return None


def _laenge(text, lo, hi, muss=()):
    t = text.strip().strip('"').strip()
    n = len(t)
    fehlt = [m for m in muss if m.lower().replace("-", " ") not in t.lower().replace("-", " ")]
    score = (lo <= n <= hi) * 0.5 + (not fehlt) * 0.5
    return score, f"{n} Zeichen (Soll {lo} bis {hi}), fehlt {fehlt}" if fehlt else f"{n} Zeichen (Soll {lo} bis {hi})"


NUR_JSON = "Antworte ausschließlich mit gültigem JSON, ohne Erklärung."

# ---------- Aufgaben ----------

AUFGABEN = [
    # --- Keywords ---
    dict(id="K01", kategorie="Keywords",
         prompt="Ordne jedem Keyword genau einen Suchintent zu: informational, kommerziell, transaktional, navigational.\n"
                "Keywords: fahrrad kaufen | wie pumpe ich einen fahrradreifen auf | e-bike test 2026 | rose bikes login | "
                "bester fahrradhelm | fahrradkette ölen | decathlon öffnungszeiten koblenz | trekkingrad günstig bestellen\n"
                + NUR_JSON + ' Format: {"keyword": "intent", ...}',
         gold={"fahrrad kaufen": ("transaktional", "kommerziell"), "wie pumpe ich einen fahrradreifen auf": "informational",
               "e-bike test 2026": ("kommerziell", "informational"), "rose bikes login": "navigational", "bester fahrradhelm": "kommerziell",
               "fahrradkette ölen": "informational", "decathlon öffnungszeiten koblenz": "navigational",
               "trekkingrad günstig bestellen": "transaktional"}),
    dict(id="K02", kategorie="Keywords",
         prompt="Unsere Marke heißt Velora (E-Bikes). Welche Keywords sind Brand-Keywords (inklusive Tippfehler der Marke)?\n"
                "Keywords: velora e-bike | velora erfahrungen | e-bike damen | velra ebike | trekkingrad 28 zoll | "
                "velora händler koblenz | e-bike mit mittelmotor\n" + NUR_JSON + " Format: Liste der Brand-Keywords.",
         gold=["velora e-bike", "velora erfahrungen", "velra ebike", "velora händler koblenz"]),
    dict(id="K03", kategorie="Keywords",
         prompt="Teile die Keywords in genau 3 thematische Cluster.\n"
                "Keywords: wärmepumpe kosten | wärmepumpe förderung 2026 | wärmepumpe altbau | photovoltaik speicher | "
                "pv anlage einfamilienhaus | solaranlage balkon | dachdämmung kosten | dämmung zwischensparren | "
                "fassadendämmung förderung\n" + NUR_JSON + ' Format: {"Clustername": ["keyword", ...], ...}',
         gruppen=[["wärmepumpe kosten", "wärmepumpe förderung 2026", "wärmepumpe altbau"],
                  ["photovoltaik speicher", "pv anlage einfamilienhaus", "solaranlage balkon"],
                  ["dachdämmung kosten", "dämmung zwischensparren", "fassadendämmung förderung"]]),
    dict(id="K04", kategorie="Keywords",
         prompt="Schreibe einen regulären Ausdruck (RE2, für den Search-Console-Filter), der Suchanfragen findet, die mit "
                "einem dieser Fragewörter beginnen: wer, was, wie, warum, wo, welche. Groß/Kleinschreibung egal, "
                "'werkzeug' oder 'wohnung' dürfen nicht passen.\nAntworte nur mit dem Regex, ohne Erklärung, ohne Anführungszeichen.",
         treffer=["wie funktioniert seo", "Was kostet ein e-bike", "warum rankt meine seite nicht", "wo kaufe ich",
                  "welche wärmepumpe", "wer erfand das rad"],
         kein=["werkzeug kaufen", "wohnung mieten", "seo wie geht das", "wiesbaden hotel", "waschmaschine test"]),
    dict(id="K05", kategorie="Keywords",
         prompt="Ein Nutzer sucht nach 'wärmepumpe altbau'. Nenne 8 unterschiedliche Folgesuchanfragen, die er "
                "wahrscheinlich als Nächstes stellt (Query Fan-out).\n" + NUR_JSON + " Format: Liste mit 8 Strings."),

    # --- Snippets und Texte ---
    dict(id="T01", kategorie="Snippets",
         prompt="Schreibe einen Title-Tag für eine Ratgeberseite zum Keyword 'e-bike leasing für arbeitnehmer'. "
                "Maximal 60 Zeichen, Keyword am Anfang.\nAntworte nur mit dem Title, ohne Anführungszeichen."),
    dict(id="T02", kategorie="Snippets",
         prompt="Schreibe eine Meta-Description für eine Kategorieseite zum Keyword 'trekkingrad kaufen'. "
                "140 bis 160 Zeichen, mit Handlungsaufforderung.\nAntworte nur mit der Description."),
    dict(id="T03", kategorie="Snippets",
         prompt="Erstelle 3 Title-Varianten (je maximal 60 Zeichen) für eine Produktseite 'Velora Tour 5 Trekking-E-Bike'. "
                "Jede Variante mit anderem Nutzenversprechen.\n" + NUR_JSON + " Format: Liste mit 3 Strings."),
    dict(id="T04", kategorie="Snippets",
         prompt="Schreibe einen Alt-Text für dieses Bild: Eine Frau fährt mit einem grauen Trekking-E-Bike auf einem "
                "Schotterweg an der Mosel, im Hintergrund Weinberge. Maximal 125 Zeichen, nicht mit 'Bild von' beginnen.\n"
                "Antworte nur mit dem Alt-Text."),
    dict(id="T05", kategorie="Texte",
         prompt="Erstelle eine H2-Gliederung (5 bis 8 Überschriften) für einen Ratgeber zum Keyword 'wärmepumpe altbau'.\n"
                + NUR_JSON + " Format: Liste der H2-Überschriften."),
    dict(id="T06", kategorie="Texte",
         prompt="Fasse den Text in höchstens 2 Sätzen und höchstens 220 Zeichen zusammen:\n"
                "Eine Wärmepumpe kann auch im Altbau effizient arbeiten, wenn die Vorlauftemperatur unter 55 Grad bleibt. "
                "Entscheidend sind ausreichend große Heizkörper oder eine Flächenheizung sowie ein hydraulischer Abgleich. "
                "Eine Komplettsanierung ist nicht immer nötig; oft reichen der Austausch einzelner Heizkörper und eine "
                "bessere Dämmung des Dachs. Vor der Entscheidung sollte eine Heizlastberechnung stehen.\n"
                "Antworte nur mit der Zusammenfassung."),
    dict(id="T07", kategorie="Texte",
         prompt="Ist der folgende Produkttext Keyword-Stuffing? Text: 'Unser E-Bike kaufen lohnt sich. Wer ein E-Bike kaufen "
                "will, sollte bei uns E-Bike kaufen, denn E-Bike kaufen war nie leichter. E-Bike kaufen online oder E-Bike "
                "kaufen im Laden: E-Bike kaufen bei Velora.'\n" + NUR_JSON + ' Format: {"stuffing": true/false, "keyword": "..."}'),
    dict(id="T08", kategorie="Texte",
         prompt="Schreibe das Snippet so um, dass es mehr Klicks bekommt (Title max. 60, Description max. 155 Zeichen). "
                "Alt: Title 'Wärmepumpe | Firma Müller GmbH', Description 'Wir bieten Wärmepumpen an. Kontaktieren Sie uns.'\n"
                + NUR_JSON + ' Format: {"title": "...", "description": "..."}'),
    dict(id="T09", kategorie="Texte",
         prompt="Extrahiere aus dem Text alle Fragen und Antworten als FAQ (genau 3).\nText: Wie lange hält ein E-Bike-Akku? "
                "Meist 800 bis 1000 Ladezyklen, also 3 bis 5 Jahre. Darf ich den Akku im Winter draußen lassen? Nein, lagern "
                "Sie ihn bei 10 bis 20 Grad. Muss ich den Akku vor dem ersten Laden leer fahren? Nein, Lithium-Akkus haben "
                "keinen Memory-Effekt.\n" + NUR_JSON + ' Format: [{"frage": "...", "antwort": "..."}, ...]'),
    dict(id="T10", kategorie="Texte",
         prompt="Extrahiere alle benannten Entitäten (Marken, Orte, Organisationen, Produkte) aus dem Text: "
                "'Velora stellt das Tour 5 auf der Eurobike in Frankfurt vor. Der Motor kommt von Bosch, der Akku wird in "
                "Koblenz montiert, der ADAC hat das Rad bereits getestet.'\n" + NUR_JSON + " Format: Liste der Entitäten.",
         gold=["Velora", "Tour 5", "Eurobike", "Frankfurt", "Bosch", "Koblenz", "ADAC"]),

    # --- Technik ---
    dict(id="X01", kategorie="Technik",
         prompt="robots.txt:\nUser-agent: *\nDisallow: /warenkorb/\nDisallow: /*?sort=\nDisallow: /intern/\nAllow: /intern/presse/\n\n"
                "Welche URLs darf Googlebot NICHT crawlen?\n/warenkorb/schritt-1 | /e-bikes?sort=preis | /e-bikes?farbe=rot | "
                "/intern/presse/mitteilung-1 | /intern/team | /blog/warenkorb-tipps\n" + NUR_JSON + " Format: Liste der gesperrten Pfade.",
         gold=["/warenkorb/schritt-1", "/e-bikes?sort=preis", "/intern/team"]),
    dict(id="X02", kategorie="Technik",
         prompt="Welche dieser hreflang-Werte sind ungültig? de | de-AT | en-UK | ch-de | fr-FR | x-default | es-419 | pt-br\n"
                + NUR_JSON + " Format: Liste der ungültigen Werte.",
         gold=["en-UK", "es-419"], optional=["ch-de"]),  # es-419: Google nimmt nur ISO-3166-1-Alpha-2-Regionen; ch-de formal gültig (Chamorro), aber vermutlich Dreher
    dict(id="X03", kategorie="Technik",
         prompt="Weiterleitung: /alt -> 301 -> /zwischen -> 302 -> /neu -> 200. Wie viele Weiterleitungen hat die Kette, "
                "und welcher Statuscode sollte ersetzt werden?\n" + NUR_JSON + ' Format: {"hops": Zahl, "ersetzen": Statuscode}',
         gold={"hops": "2", "ersetzen": "302"}),
    dict(id="X04", kategorie="Technik",
         prompt="Eine Produktseite wurde dauerhaft entfernt, es gibt kein Ersatzprodukt. Welchen HTTP-Statuscode sollte "
                "die URL liefern, damit Google sie am schnellsten entfernt? Antworte nur mit der Zahl."),
    dict(id="X05", kategorie="Technik",
         prompt="Welche URLs gehören NICHT in die XML-Sitemap?\n"
                "/e-bikes (200, indexierbar) | /e-bikes/alt (301 auf /e-bikes) | /suche?q=akku (200, noindex) | "
                "/ratgeber/akku (200, Canonical auf /ratgeber/akku-pflege) | /ratgeber/akku-pflege (200, indexierbar) | "
                "/aktion-2024 (404)\n" + NUR_JSON + " Format: Liste der Pfade.",
         gold=["/e-bikes/alt", "/suche?q=akku", "/ratgeber/akku", "/aktion-2024"]),
    dict(id="X06", kategorie="Technik",
         prompt="Welche Canonical-Tags sind fehlerhaft?\nA: /e-bikes?farbe=rot -> canonical /e-bikes\n"
                "B: /blog/akku -> canonical /blog/akku\nC: /tour-5 -> canonical /tour-5-alt (liefert 404)\n"
                "D: /kontakt -> canonical /impressum (noindex)\nE: /e-bikes?page=2 -> canonical /e-bikes?page=2\n"
                + NUR_JSON + " Format: Liste der Buchstaben.",
         gold=["C", "D"]),
    dict(id="X07", kategorie="Technik",
         prompt="Erzeuge JSON-LD (schema.org FAQPage) für diese zwei Fragen:\n1. Wie lange hält ein E-Bike-Akku? 3 bis 5 Jahre.\n"
                "2. Kann man den Akku nachrüsten? Ja, beim Fachhändler.\n" + NUR_JSON),
    dict(id="X08", kategorie="Technik",
         prompt="Erzeuge JSON-LD (schema.org BreadcrumbList) für den Pfad Startseite (https://velora.example/) > "
                "E-Bikes (https://velora.example/e-bikes/) > Trekking (https://velora.example/e-bikes/trekking/).\n" + NUR_JSON),

    # --- Daten und Analyse ---
    dict(id="D01", kategorie="Analyse",
         prompt="CTR-Modell: Position 3 = 2,37 %, Position 8 = 0,61 %. Eine Seite rankt auf Position 8 mit 40.000 "
                "Impressionen pro Monat. Wie viele zusätzliche Klicks pro Monat bringt Position 3? Antworte nur mit der Zahl.",
         zahl=704),
    dict(id="D02", kategorie="Analyse",
         prompt="Search-Console-Daten (Suchanfrage; Impressionen; CTR; Position):\n"
                "e-bike leasing; 8200; 1,1 %; 7,4\ntrekkingrad; 15000; 0,4 %; 18,2\nvelora; 3000; 38 %; 1,0\n"
                "e-bike akku laden; 900; 2,0 %; 6,1\nfahrradhelm test; 5400; 6,2 %; 4,8\ne-bike versicherung; 2600; 0,9 %; 24,0\n"
                "pedelec gebraucht; 1200; 3,1 %; 11,3\n"
                "Quick Win = Position 4 bis 20, mindestens 1000 Impressionen, CTR unter 5 %. Welche Suchanfragen sind Quick Wins?\n"
                + NUR_JSON + " Format: Liste der Suchanfragen.",
         gold=["e-bike leasing", "trekkingrad", "pedelec gebraucht"]),
    dict(id="D03", kategorie="Analyse",
         prompt="Ranking-Daten (Suchanfrage; URL; Klicks):\ne-bike akku; /ratgeber/akku; 120\ne-bike akku; /shop/akkus; 95\n"
                "trekkingrad; /e-bikes/trekking; 300\nakku laden; /ratgeber/akku-laden; 40\nakku laden; /ratgeber/akku; 38\n"
                "fahrradhelm; /zubehoer/helme; 210\n"
                "Bei welchen Suchanfragen konkurrieren mehrere eigene URLs (Kannibalisierung)?\n" + NUR_JSON + " Format: Liste der Suchanfragen.",
         gold=["e-bike akku", "akku laden"]),
    dict(id="D04", kategorie="Analyse",
         prompt="Welche URLs haben doppelte Title-Tags? Gib jede betroffene URL an.\n"
                "/e-bikes: E-Bikes kaufen | Velora\n/e-bikes?page=2: E-Bikes kaufen | Velora\n/trekking: Trekking-E-Bikes | Velora\n"
                "/kontakt: Kontakt | Velora\n/impressum: Velora\n/datenschutz: Velora\n/blog: Ratgeber | Velora\n"
                + NUR_JSON + " Format: Liste der URLs.",
         gold=["/e-bikes", "/e-bikes?page=2", "/impressum", "/datenschutz"]),
    dict(id="D05", kategorie="Analyse",
         prompt="Ein neuer Artikel heißt 'E-Bike-Akku richtig pflegen'. Wähle die 3 passendsten Seiten für interne Links:\n"
                "/ratgeber/akku-laden | /ratgeber/winterlagerung | /zubehoer/helme | /ratgeber/akku-reichweite | "
                "/ueber-uns | /blog/radtouren-mosel\n" + NUR_JSON + " Format: Liste mit 3 Pfaden.",
         gold=["/ratgeber/akku-laden", "/ratgeber/winterlagerung", "/ratgeber/akku-reichweite"]),
    dict(id="D06", kategorie="Analyse",
         prompt="Eigene H2: Was kostet eine Wärmepumpe? | Förderung 2026 | Wärmepumpe im Altbau\n"
                "Wettbewerber-H2: Kosten im Überblick | Förderung und Zuschüsse | Lautstärke und Abstand zum Nachbarn | "
                "Stromtarif für Wärmepumpen | Altbau: geht das? | Wartung und Lebensdauer\n"
                "Welche Themen fehlen bei uns? " + NUR_JSON + " Format: Liste kurzer Themenbegriffe.",
         stichworte=["laut", "strom", "wartung"]),
]


# ---------- Prüfungen je Aufgabe ----------

def _k03(a, t):
    d = _json(a)
    if not isinstance(d, dict) or len(d) != 3:
        return 0.0, "kein Objekt mit 3 Clustern"
    wo = {_norm(k): i for i, ks in enumerate(d.values()) if isinstance(ks, list) for k in ks}
    paare = [(x, y, gi == gj) for gi, g in enumerate(t["gruppen"]) for gj, h in enumerate(t["gruppen"])
             for x in g for y in h if x < y]
    ok = sum((wo.get(x) is not None and wo.get(x) == wo.get(y)) == gleich for x, y, gleich in paare)
    return round(ok / len(paare), 2), f"{ok}/{len(paare)} Paare richtig"


def _k04(a, t):
    rx = a.strip().strip("`").strip().splitlines()[0].strip().strip('"').strip("/") if a.strip() else ""
    try:
        r = re.compile(rx, re.I)
    except re.error as e:
        return 0.0, f"Regex ungültig: {e}"
    falsch = [s for s in t["treffer"] if not r.search(s)] + [s for s in t["kein"] if r.search(s)]
    n = len(t["treffer"]) + len(t["kein"])
    return round(1 - len(falsch) / n, 2), f"falsch: {falsch}" if falsch else "alle Beispiele richtig"


def _k05(a, t):
    m = _menge(a)
    if m is None:
        return 0.0, "kein JSON-Array"
    return (len(m) == 8) * 1.0, f"{len(m)} eindeutige Anfragen; Qualität manuell prüfen"


def _t03(a, t):
    d = _json(a)
    if not isinstance(d, list) or len(d) != 3:
        return 0.0, "keine Liste mit 3 Titles"
    zu_lang = [len(x) for x in d if len(str(x)) > 60]
    return (0 if zu_lang else 1.0), f"zu lang: {zu_lang}" if zu_lang else "alle bis 60 Zeichen"


def _t04(a, t):
    n = len(a.strip().strip('"'))
    if a.strip().lower().startswith(("bild von", "foto von")):
        return 0.0, "beginnt mit 'Bild von'"
    return (20 <= n <= 125) * 1.0, f"{n} Zeichen (Soll 20 bis 125)"


def _t05(a, t):
    d = _json(a)
    if not isinstance(d, list):
        return 0.0, "kein JSON-Array"
    return (5 <= len(d) <= 8) * 1.0, f"{len(d)} Überschriften; Qualität manuell prüfen"


def _t06(a, t):
    saetze = len(re.findall(r"[.!?](\s|$)", a.strip()))
    n = len(a.strip())
    inhalt = "55" in a and "wärmepumpe" in a.lower()
    return round(((n <= 220) + (saetze <= 2) + inhalt) / 3, 2), f"{n} Zeichen, {saetze} Sätze, Kernaussage 55 Grad {inhalt}"


def _t07(a, t):
    d = _json(a)
    if not isinstance(d, dict):
        return 0.0, "kein JSON-Objekt"
    ok = (d.get("stuffing") is True) + ("e-bike kaufen" in _norm(d.get("keyword", "")))
    return ok / 2, f"Antwort {d}"


def _t08(a, t):
    d = _json(a)
    if not isinstance(d, dict) or not {"title", "description"} <= set(d):
        return 0.0, "Format falsch"
    lt, ld = len(str(d["title"])), len(str(d["description"]))
    return ((lt <= 60) + (ld <= 155)) / 2, f"Title {lt}, Description {ld} Zeichen; Wirkung manuell prüfen"


def _t09(a, t):
    d = _json(a)
    if not isinstance(d, list):
        return 0.0, "kein JSON-Array"
    ok = len(d) == 3 and all(isinstance(x, dict) and x.get("frage") and x.get("antwort") for x in d)
    return ok * 1.0, f"{len(d)} Einträge"


def _x04(a, t):
    z = _zahl(a)
    return (1.0 if z == 410 else 0.5 if z == 404 else 0.0), f"Antwort {z} (410 richtig, 404 halb)"


def _x07(a, t):
    d = _json(a)
    if not isinstance(d, dict):
        return 0.0, "kein JSON-Objekt"
    fragen = d.get("mainEntity") or []
    ok = [d.get("@type") == "FAQPage", "schema.org" in str(d.get("@context", "")), len(fragen) == 2,
          all(f.get("@type") == "Question" and isinstance(f.get("acceptedAnswer"), dict)
              and f["acceptedAnswer"].get("@type") == "Answer" for f in fragen if isinstance(f, dict))]
    return round(sum(ok) / 4, 2), f"Prüfpunkte {ok}"


def _x08(a, t):
    d = _json(a)
    if not isinstance(d, dict):
        return 0.0, "kein JSON-Objekt"
    el = d.get("itemListElement") or []
    ok = [d.get("@type") == "BreadcrumbList", len(el) == 3,
          [e.get("position") for e in el if isinstance(e, dict)] in ([1, 2, 3], ["1", "2", "3"]),
          all("velora.example" in str(e.get("item", "")) for e in el if isinstance(e, dict))]
    return round(sum(ok) / 4, 2), f"Prüfpunkte {ok}"


def _d01(a, t):
    z = _zahl(a)
    return (1.0 if z is not None and abs(z - t["zahl"]) <= t["zahl"] * 0.01 else 0.0), f"Antwort {z}, Soll {t['zahl']}"


def _d06(a, t):
    m = _menge(a)
    if m is None:
        return 0.0, "kein JSON-Array"
    text = " ".join(m)
    fehlt = [s for s in t["stichworte"] if s not in text]
    zu_viel = [x for x in m if any(w in x for w in ("kosten", "förder", "altbau"))]
    score = (len(t["stichworte"]) - len(fehlt)) / len(t["stichworte"]) - 0.2 * len(zu_viel)
    return round(max(score, 0), 2), f"fehlt {fehlt}, schon vorhanden genannt {zu_viel}"


CHECKS = {
    "K03": _k03, "K04": _k04, "K05": _k05,
    "T01": lambda a, t: _laenge(a, 30, 60, ["e-bike leasing"]),
    "T02": lambda a, t: _laenge(a, 140, 160, ["trekkingrad"]),
    "T03": _t03, "T04": _t04, "T05": _t05, "T06": _t06, "T07": _t07, "T08": _t08, "T09": _t09,
    "X03": lambda a, t: _dict_score(a, t["gold"]), "X04": _x04, "X07": _x07, "X08": _x08,
    "D01": _d01, "D06": _d06,
}


def pruefen(aufgabe, antwort):
    """Wie _pruefen; eine Liste, die das Modell in ein Objekt packt ({"x": [...]}) wird ausgepackt und mit VERPACKT markiert."""
    if IDEAL[aufgabe["id"]].lstrip().startswith("["):
        d = _json(antwort)
        if isinstance(d, dict) and len(d) == 1 and isinstance(next(iter(d.values())), list):
            score, hinweis = _pruefen(aufgabe, json.dumps(next(iter(d.values())), ensure_ascii=False))
            return score, "VERPACKT " + hinweis
    return _pruefen(aufgabe, antwort)


def _pruefen(aufgabe, antwort):
    if aufgabe["id"] in CHECKS:
        return CHECKS[aufgabe["id"]](antwort, aufgabe)
    gold = aufgabe.get("gold")
    if isinstance(gold, dict):
        return _dict_score(antwort, gold)
    if isinstance(gold, list):
        return _mengen_score(antwort, gold, aufgabe.get("optional", ()))
    return None, "manuell"


# Musterantworten für den Selbsttest (müssen Score 1.0 ergeben)
IDEAL = {
    "K01": json.dumps({k: v if isinstance(v, str) else v[0] for k, v in AUFGABEN[0]["gold"].items()}, ensure_ascii=False),
    "K02": '["velora e-bike", "velora erfahrungen", "velra ebike", "velora händler koblenz"]',
    "K03": '{"Wärmepumpe": ["wärmepumpe kosten", "wärmepumpe förderung 2026", "wärmepumpe altbau"], '
           '"Solar": ["photovoltaik speicher", "pv anlage einfamilienhaus", "solaranlage balkon"], '
           '"Dämmung": ["dachdämmung kosten", "dämmung zwischensparren", "fassadendämmung förderung"]}',
    "K04": r"^(wer|was|wie|warum|wo|welche)\b",
    "K05": '["wärmepumpe altbau kosten", "wärmepumpe altbau förderung", "wärmepumpe altbau heizkörper", '
           '"wärmepumpe altbau erfahrungen", "wärmepumpe altbau vorlauftemperatur", "wärmepumpe altbau dämmung", '
           '"wärmepumpe altbau sinnvoll", "wärmepumpe altbau fußbodenheizung"]',
    "T01": "E-Bike Leasing für Arbeitnehmer: So sparen Sie bis 40 %",
    "T02": "Trekkingrad kaufen beim Fachhändler: über 80 Modelle, Beratung vor Ort, Probefahrt und schnelle "
           "Lieferung. Jetzt Ihr passendes Trekkingrad finden!",
    "T03": '["Velora Tour 5: Trekking-E-Bike mit 120 km Reichweite", "Velora Tour 5 kaufen: Gratis Probefahrt", '
           '"Velora Tour 5: Leichtes E-Bike für jede Tour"]',
    "T04": "Frau fährt mit grauem Trekking-E-Bike auf Schotterweg an der Mosel, dahinter Weinberge",
    "T05": '["Funktioniert eine Wärmepumpe im Altbau?", "Vorlauftemperatur prüfen", "Heizkörper oder Fußbodenheizung", '
           '"Kosten und Förderung", "Heizlastberechnung als erster Schritt"]',
    "T06": "Eine Wärmepumpe läuft im Altbau effizient, wenn die Vorlauftemperatur unter 55 Grad bleibt. Oft reichen "
           "größere Heizkörper, Dachdämmung und eine Heizlastberechnung.",
    "T07": '{"stuffing": true, "keyword": "E-Bike kaufen"}',
    "T08": '{"title": "Wärmepumpe vom Fachbetrieb: Beratung und Förderung", '
           '"description": "Planung, Einbau und Förderantrag aus einer Hand. Jetzt kostenlose Heizlastberechnung anfragen!"}',
    "T09": '[{"frage": "Wie lange hält ein E-Bike-Akku?", "antwort": "3 bis 5 Jahre"}, '
           '{"frage": "Darf der Akku im Winter draußen bleiben?", "antwort": "Nein"}, '
           '{"frage": "Muss ich ihn vorher leer fahren?", "antwort": "Nein"}]',
    "T10": '["Velora", "Tour 5", "Eurobike", "Frankfurt", "Bosch", "Koblenz", "ADAC"]',
    "X01": '["/warenkorb/schritt-1", "/e-bikes?sort=preis", "/intern/team"]',
    "X02": '["en-UK", "es-419"]',
    "X03": '{"hops": 2, "ersetzen": 302}',
    "X04": "410",
    "X05": '["/e-bikes/alt", "/suche?q=akku", "/ratgeber/akku", "/aktion-2024"]',
    "X06": '["C", "D"]',
    "X07": '{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": ['
           '{"@type": "Question", "name": "Wie lange hält ein E-Bike-Akku?", "acceptedAnswer": {"@type": "Answer", "text": "3 bis 5 Jahre."}}, '
           '{"@type": "Question", "name": "Kann man den Akku nachrüsten?", "acceptedAnswer": {"@type": "Answer", "text": "Ja, beim Fachhändler."}}]}',
    "X08": '{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ['
           '{"@type": "ListItem", "position": 1, "name": "Startseite", "item": "https://velora.example/"}, '
           '{"@type": "ListItem", "position": 2, "name": "E-Bikes", "item": "https://velora.example/e-bikes/"}, '
           '{"@type": "ListItem", "position": 3, "name": "Trekking", "item": "https://velora.example/e-bikes/trekking/"}]}',
    "D01": "704",
    "D02": '["e-bike leasing", "trekkingrad", "pedelec gebraucht"]',
    "D03": '["e-bike akku", "akku laden"]',
    "D04": '["/e-bikes", "/e-bikes?page=2", "/impressum", "/datenschutz"]',
    "D05": '["/ratgeber/akku-laden", "/ratgeber/winterlagerung", "/ratgeber/akku-reichweite"]',
    "D06": '["Lautstärke", "Stromtarif", "Wartung"]',
}
