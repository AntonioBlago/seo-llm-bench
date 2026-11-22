"""SEO-Aufgaben gegen lokale Modelle (Ollama) laufen lassen: Genauigkeit, Dauer, Tokens/s, Formattreue.

Nur Standardbibliothek, läuft auf jedem Rechner mit Python 3.9+ und Ollama.

    python bench.py --selbsttest
    python bench.py qwen2.5:0.5b qwen2.5:1.5b qwen2.5:3b qwen2.5:7b
    python bench.py qwen3:4b --think false --wdh 3 --temp 0.7      # Streuung bei wiederholten Läufen
    OLLAMA_URL=http://server:11434 python bench.py qwen2.5:3b

Vergleich mit Cloud-Modellen (nur am eigenen Rechner, Logins nie auf geteilten Maschinen):
    python bench.py claude/haiku claude/sonnet claude/opus          # Claude-Abo über die Claude-Code-CLI
    python bench.py codex/gpt-6-luna codex/gpt-6.2-sol              # ChatGPT-Abo über codex exec
    python bench.py tensorx/deepseek/deepseek-v4-pro-0813           # TensorX, Schlüssel in TENSORX_API_KEY oder ~/.config/tensorx/api.env

Ergebnis: ergebnisse/<Zeitstempel>.csv (je Lauf eine Zeile, Spalte 'manuell' für die eigene Bewertung)
und eine Zusammenfassung je Modell auf der Konsole und in ergebnisse/<Zeitstempel>.md.
"""
import argparse
import csv
import json
import os
import re
import statistics
import time
import urllib.request
from pathlib import Path

from aufgaben import AUFGABEN, IDEAL, pruefen

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")


LEER = None  # leerer Arbeitsordner für CLI-Aufrufe, damit kein CLAUDE.md/AGENTS.md mitgelesen wird


def _leer():
    global LEER
    import tempfile
    LEER = LEER or tempfile.mkdtemp(prefix="seo_bench_")
    return LEER


def _cli(befehl, prompt=None):
    import subprocess
    t = time.perf_counter()
    p = subprocess.run(befehl, input=prompt or "",  # leere Eingabe: codex exec wartet sonst auf stdin
                        capture_output=True, text=True, encoding="utf-8", cwd=_leer(), timeout=900)
    if p.returncode:
        raise RuntimeError(p.stderr[-300:] or p.stdout[-300:])
    return p.stdout, time.perf_counter() - t


def chat_claude(modell, prompt):
    import shutil
    out, sek = _cli([shutil.which("claude"), "-p", "--model", modell, "--system-prompt", "Du bist ein hilfreicher Assistent.",
                     "--tools", "", "--setting-sources", "", "--strict-mcp-config", "--no-session-persistence",
                     "--output-format", "json"], prompt)
    d = json.loads(out)
    tok = d.get("usage", {}).get("output_tokens", 0)
    return d.get("result", ""), sek, tok, tok / sek, 0.0


def chat_codex(modell, prompt):
    import glob
    import shutil
    exe = shutil.which("codex") or sorted(glob.glob(os.path.expanduser("~/.vscode/extensions/openai.chatgpt-*/bin/*/codex*")))[-1]
    ziel = Path(_leer()) / "codex_antwort.txt"
    # ponytail: effort low für alle Codex-Modelle, vergleichbar mit Antworten ohne Denkmodus; Tokens meldet exec nur gesamt
    _, sek = _cli([exe, "exec", "--skip-git-repo-check", "--ephemeral", "--ignore-user-config", "--ignore-rules",
                   "-s", "read-only", "-m", modell, "-c", "model_reasoning_effort=low", "-o", str(ziel), prompt])
    return ziel.read_text(encoding="utf-8").strip(), sek, 0, 0.0, 0.0


def chat_tensorx(modell, prompt):
    key = os.environ.get("TENSORX_API_KEY") or next(
        l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/.config/tensorx/api.env"))
        if l.startswith("TENSORX_API_KEY="))
    body = {"model": modell, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0}
    req = urllib.request.Request("https://api.tensorx.ai/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    sek = time.perf_counter() - t
    tok = d.get("usage", {}).get("completion_tokens", 0)
    return d["choices"][0]["message"]["content"].strip(), sek, tok, tok / sek, 0.0


CLOUD = {"claude": chat_claude, "codex": chat_codex, "tensorx": chat_tensorx}


def chat(modell, prompt, temp, think, ctx):
    anbieter, _, rest = modell.partition("/")
    if anbieter in CLOUD:
        return CLOUD[anbieter](rest, prompt)
    if think is False:
        prompt += " /no_think"  # Schalter im Prompt für qwen3, wirkt auch bei älterem Ollama ohne "think"-Feld
    # ponytail: 800 Tokens reichen je Antwort und bremsen Endlosschleifen; mit Denkmodus Platz fürs Nachdenken
    body = {"model": modell, "messages": [{"role": "user", "content": prompt}], "stream": False,
            "options": {"temperature": temp, "seed": 42, "num_ctx": ctx, "num_predict": 4096 if think else 800}}
    if think is not None:
        body["think"] = think
    req = urllib.request.Request(f"{URL}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    sek = time.perf_counter() - t
    text = re.sub(r"<think>.*?(</think>|$)", "", d["message"]["content"], flags=re.S).strip()  # auch abgebrochenes Denken
    tok = d.get("eval_count", 0)
    if d.get("done_reason") == "length":
        text = "ENDLOSSCHLEIFE abgebrochen: " + text
    return text, sek, tok, tok / (d.get("eval_duration") or 1) * 1e9, d.get("load_duration", 0) / 1e9


def selbsttest():
    fehler = []
    for a in AUFGABEN:
        score, hinweis = pruefen(a, IDEAL[a["id"]])
        if score is not None and score != 1.0:
            fehler.append(f"{a['id']}: {score} {hinweis}")
        # falsche Antwort darf nicht volle Punkte bekommen
        if score is not None and pruefen(a, "weiß ich nicht")[0] == 1.0:
            fehler.append(f"{a['id']}: Unsinn bekommt 1.0")
    assert not fehler, "\n".join(fehler)
    print(f"Selbsttest ok: {len(AUFGABEN)} Aufgaben, {sum(pruefen(a, IDEAL[a['id']])[0] is not None for a in AUFGABEN)} automatisch geprüft")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modelle", nargs="*")
    ap.add_argument("--selbsttest", action="store_true")
    ap.add_argument("--nur", help="nur diese Aufgaben, z. B. K01,X02 oder Präfix D")
    ap.add_argument("--wdh", type=int, default=1, help="Läufe je Aufgabe (Streuung)")
    ap.add_argument("--temp", type=float, default=0.0)
    ap.add_argument("--think", choices=["true", "false"], help="nur für Modelle mit Denkmodus (qwen3)")
    ap.add_argument("--ctx", type=int, default=4096)
    ap.add_argument("--bewerten", help="vorhandene Ergebnis-CSV neu bewerten")
    a = ap.parse_args()
    if a.bewerten:
        return neu_bewerten(a.bewerten)
    if a.selbsttest or not a.modelle:
        return selbsttest()

    think = None if a.think is None else a.think == "true"
    aufgaben = [x for x in AUFGABEN if not a.nur or any(x["id"].startswith(n.strip()) for n in a.nur.split(","))]
    stempel = time.strftime("%Y-%m-%d_%H%M%S")
    out = Path(__file__).parent / "ergebnisse"
    out.mkdir(exist_ok=True)
    zeilen, zusammen = [], []

    for modell in a.modelle:
        _, _, _, _, laden = chat(modell, "Antworte nur mit OK.", 0, think, a.ctx)  # Aufwärmen, Ladezeit separat
        print(f"\n== {modell}  (Laden {laden:.1f} s)")
        for x in aufgaben:
            for lauf in range(1, a.wdh + 1):
                try:
                    text, sek, tok, tps, _ = chat(modell, x["prompt"], a.temp, think, a.ctx)
                    score, hinweis = pruefen(x, text)
                    if text.startswith("ENDLOSSCHLEIFE"):
                        hinweis = "ENDLOSSCHLEIFE " + hinweis
                except Exception as e:  # Zeitüberschreitung, Modell fehlt: Lauf zählen, weitermachen
                    text, sek, tok, tps, score, hinweis = "", 0, 0, 0, 0.0, f"FEHLER {e}"
                zeilen.append(dict(modell=modell, aufgabe=x["id"], kategorie=x["kategorie"], lauf=lauf,
                                   score="" if score is None else score, hinweis=hinweis, sekunden=round(sek, 1),
                                   tokens=tok, tok_s=round(tps, 1), antwort=text, manuell=""))
                print(f"  {x['id']} {'  - ' if score is None else f'{score:4.2f}'}  {sek:5.1f} s  {hinweis[:70]}")

        zusammen.append(kennzahlen(zeilen, modell, laden))

    kopf = f"Server {URL}, temp {a.temp}, think {a.think}, Läufe {a.wdh}, ctx {a.ctx}"
    schreiben(out / stempel, zeilen, zusammen, kopf)


def kennzahlen(zeilen, modell, laden=""):
    eig = [z for z in zeilen if z["modell"] == modell]
    auto = [z["score"] for z in eig if z["score"] != ""]
    kats = [k for k in dict.fromkeys(z["kategorie"] for z in eig) if any(z["score"] != "" for z in eig if z["kategorie"] == k)]
    kat = {k: statistics.mean(z["score"] for z in eig if z["kategorie"] == k and z["score"] != "") for k in kats}
    return dict(modell=modell, genauigkeit=round(statistics.mean(auto), 2) if auto else 0,
                voll_richtig=sum(s == 1.0 for s in auto), auto_n=len(auto),
                formatfehler=sum("kein JSON" in z["hinweis"] or "Format" in z["hinweis"] for z in eig),
                verpackt=sum("VERPACKT" in z["hinweis"] for z in eig),
                endlos=sum("ENDLOS" in z["hinweis"] for z in eig),
                median_s=round(statistics.median(z["sekunden"] for z in eig), 1),
                summe_s=round(sum(z["sekunden"] for z in eig)), tok_s=round(statistics.median(z["tok_s"] for z in eig), 1),
                laden_s=laden if laden == "" else round(laden, 1), **{f"kat_{k}": round(v, 2) for k, v in kat.items()})


def schreiben(ziel, zeilen, zusammen, kopf):
    with open(f"{ziel}.csv", "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel zeigt Umlaute
        w = csv.DictWriter(f, fieldnames=list(zeilen[0]), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    spalten = list(dict.fromkeys(k for z in zusammen for k in z))
    md = ["| " + " | ".join(spalten) + " |", "|" + "---|" * len(spalten)]
    md += ["| " + " | ".join(str(z.get(k, "")) for k in spalten) + " |" for z in zusammen]
    tabelle = "\n".join(md)
    Path(f"{ziel}.md").write_text(f"# SEO-Bench {Path(ziel).name}\n\n{kopf}\n\n{tabelle}\n", encoding="utf-8")
    print(f"\n{tabelle}\n\nDetails: {ziel}.csv")


def neu_bewerten(pfad):
    """Vorhandene CSV mit den aktuellen Prüfungen neu bewerten, ohne die Modelle erneut zu fragen."""
    with open(pfad, encoding="utf-8-sig") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    nach_id = {x["id"]: x for x in AUFGABEN}
    for z in zeilen:
        score, hinweis = pruefen(nach_id[z["aufgabe"]], z["antwort"])
        if z["antwort"].startswith("ENDLOSSCHLEIFE"):
            hinweis = "ENDLOSSCHLEIFE " + hinweis
        z.update(score="" if score is None else score, hinweis=hinweis,
                 sekunden=float(z["sekunden"]), tok_s=float(z["tok_s"]))
    zusammen = [kennzahlen(zeilen, m) for m in dict.fromkeys(z["modell"] for z in zeilen)]
    schreiben(str(Path(pfad).with_suffix("")) + "_neu", zeilen, zusammen, f"Neu bewertet aus {Path(pfad).name}")


if __name__ == "__main__":
    main()
