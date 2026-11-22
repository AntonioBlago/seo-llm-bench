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
