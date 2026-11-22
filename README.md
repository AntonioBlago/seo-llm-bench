# seo-llm-bench

A small, reproducible benchmark that checks how well language models handle everyday SEO work.
It runs 29 SEO tasks, scores every answer automatically, and puts local models (Qwen via Ollama) next to cloud models (Claude, Codex/GPT, DeepSeek).

Python standard library only. No dependencies, no API key needed for local models.

> The prompts are in German, because the test targets German-language SEO work. The scoring is language-independent (JSON structure, counts, lengths, expected values).

Full write-up: [Local AI Models for SEO](https://www.antonioblago.com/blog/local-ai-models-seo-test) (EN) · [Lokale KI-Modelle im SEO-Test](https://www.antonioblago.com/de/blog/lokale-ki-modelle-seo-test) (DE)

## What it tests

| Category | Tasks | Examples |
|---|---|---|
| Keywords | K01 to K05 | search intent, brand keywords incl. typos, clustering, regex for Search Console, follow-up queries |
| Snippets | T01 to T04 | title tags (max. 60 characters), meta descriptions (140 to 160), title variants, alt text |
| Texte | T05 to T10 | outlines, summaries with length limits, keyword stuffing, snippet rewrites, FAQ and entity extraction |
| Technik | X01 to X08 | robots.txt, hreflang codes, redirect chains, status codes, sitemaps, canonicals, JSON-LD |
| Analyse | D01 to D06 | CTR calculation, Search Console prioritisation, cannibalisation, duplicate titles, internal links, content gaps |

All data is fictional (an e-bike brand, a heat pump site). Expected values for technical tasks follow Google's documentation, e.g. `es-419` is not a valid hreflang code for Google, and all 4xx codes except 429 are treated the same.

Each answer gets a score from 0 to 1. Formatting problems (no valid JSON, list wrapped in an object, endless loops) are counted separately, so a model is not punished twice.

## Results (21 and 22 November 2026)

One run per task, temperature 0. Local models on a cloud VM with one Nvidia Tesla T4 (16 GB VRAM). Every prompt, reference answer and check: [METHODOLOGY.md](METHODOLOGY.md).

| Model | Accuracy | Fully correct (of 29) | Median per task | Total |
|---|---|---|---|---|
| codex/gpt-6.2-sol | 1.00 | 29 | 5.3 s | 179 s |
| claude/opus | 0.99 | 28 | 4.1 s | 131 s |
| codex/gpt-6.1-terra | 0.99 | 28 | 4.7 s | 149 s |
| claude/haiku | 0.98 | 27 | 3.3 s | 109 s |
| claude/sonnet | 0.97 | 26 | 3.5 s | 100 s |
| codex/gpt-6-luna | 0.94 | 26 | 5.2 s | 145 s |
| deepseek-v4.1-flash (TensorX) | 0.93 | 24 | 0.6 s | 18 s |
| deepseek-v4-pro (TensorX) | 0.90 | 23 | 0.7 s | 26 s |
| qwen3:4b-instruct (local) | 0.77 | 14 | 2.7 s | 88 s |
| qwen3:4b, thinking (local) | 0.77 | 19 | 41.9 s | 1300 s |
| qwen2.5:14b (local) | 0.76 | 17 | 3.9 s | 138 s |
| qwen3:8b (local) | 0.76 | 15 | 3.3 s | 110 s |
| qwen3:8b, thinking (local) | 0.76 | 20 | 14.8 s | 667 s |
| qwen3:30b-a3b-instruct, partly offloaded (local) | 0.75 | 15 | 3.7 s | 120 s |
| qwen2.5:7b (local) | 0.72 | 15 | 2.8 s | 95 s |
| qwen2.5:1.5b (local) | 0.58 | 9 | 2.5 s | 79 s |
| qwen2.5:3b (local) | 0.51 | 8 | 2.6 s | 91 s |
| qwen2.5:0.5b (local) | 0.33 | 3 | 2.3 s | 83 s |

Full numbers incl. per-category scores: [`ergebnisse/gesamt_2026-11-22_neu.md`](ergebnisse/gesamt_2026-11-22_neu.md).
Every single answer: [`ergebnisse/gesamt_2026-11-22_neu.csv`](ergebnisse/gesamt_2026-11-22_neu.csv) (semicolon-separated).

Takeaways:
- The best local model reaches 0.77, the smallest Claude model 0.98.
- Locally, size stops helping above 7b: qwen2.5:14b is barely better than 7b and half as fast, the newer qwen3:4b beats both. Even the 30b mixture-of-experts model reaches only 0.75 (best local model for keywords at 0.96, weaker on snippets and technical SEO).
- Thinking mode raises the number of fully correct answers, but is up to 15 times slower and caused 8 endless loops with qwen3:4b.
- Local models fail most often at arithmetic (CTR and click deltas), character limits and hreflang edge cases.

Caveats: one run per task, automated scoring with my own expected values, cloud times include network latency. Treat it as a practical comparison, not a scientific leaderboard. All scoring decisions and limitations: [METHODOLOGY.md](METHODOLOGY.md).

## Run it

```bash
python bench.py --selbsttest                         # checks the scoring itself
python bench.py qwen2.5:7b qwen3:4b-instruct         # local models via Ollama
python bench.py qwen3:8b --think true                # with thinking mode
python bench.py qwen3:4b-instruct --wdh 3 --temp 0.7 # repeated runs for variance
OLLAMA_URL=http://server:11434 python bench.py qwen2.5:7b
python bench.py --bewerten ergebnisse/<file>.csv     # re-score an existing result file
```

Cloud models (optional, on your own machine):

```bash
python bench.py claude/haiku claude/opus             # via the Claude Code CLI (subscription)
python bench.py codex/gpt-6.2-sol                    # via `codex exec` (ChatGPT subscription)
TENSORX_API_KEY=... python bench.py tensorx/deepseek/deepseek-v4.1-flash-1017
```

Each run writes `ergebnisse/<timestamp>.csv` (one row per answer, plus an empty `manuell` column for your own grading) and a summary per model in `ergebnisse/<timestamp>.md`.

Pitfall with Ollama: the tag `qwen3:4b` points to the thinking variant. For answers without thinking use `qwen3:4b-instruct`.

## Reproduce it

Step by step in [METHODOLOGY.md, section "Reproduce it"](METHODOLOGY.md#reproduce-it). Results on other hardware are welcome as an issue.

## Add your own tasks

Tasks live in [`aufgaben.py`](aufgaben.py): a prompt, a category and a check function that returns a score from 0 to 1. Add a reference answer to `IDEAL` and run `python bench.py --selbsttest`. It makes sure a perfect answer scores 1.0 and nonsense does not. Then run `python methodology.py` to update METHODOLOGY.md.

## Deutsch

Kleiner Benchmark für SEO-Aufgaben mit lokalen und Cloud-Sprachmodellen: 29 Aufgaben in fünf Kategorien, automatisch bewertet, nur Python-Standardbibliothek. Aufruf und Ergebnisse siehe oben.

## Author

Antonio Blago, SEO freelancer, [antonioblago.com](https://www.antonioblago.com)

## License

MIT
