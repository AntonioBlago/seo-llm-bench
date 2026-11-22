"""Builds METHODOLOGY.md from aufgaben.py: every prompt, reference answer and the exact check code.

    python methodology.py
"""
import inspect
from pathlib import Path

from aufgaben import AUFGABEN, CHECKS, IDEAL

HEAD = Path(__file__).with_name("methodology_head.md").read_text(encoding="utf-8")


def regel(a):
    if a["id"] in CHECKS:
        return "```python\n" + inspect.getsource(CHECKS[a["id"]]).strip() + "\n```"
    gold = a.get("gold")
    if isinstance(gold, dict):
        return f"Share of correctly assigned keys (`_dict_score`). Expected: `{gold}`"
    if isinstance(gold, list):
        opt = f", ignored if present: `{a['optional']}`" if a.get("optional") else ""
        return f"F1 between answer list and expected list (`_mengen_score`). Expected: `{gold}`{opt}"
    return "Manual only."


teile = [HEAD]
for kat in dict.fromkeys(a["kategorie"] for a in AUFGABEN):
    teile.append(f"\n## {kat}\n")
    for a in (x for x in AUFGABEN if x["kategorie"] == kat):
        teile.append(f"### {a['id']}\n\n**Prompt**\n\n```text\n{a['prompt']}\n```\n\n"
                     f"**Reference answer** (scores 1.0 in the self-test)\n\n```text\n{IDEAL[a['id']]}\n```\n\n"
                     f"**Scoring**\n\n{regel(a)}\n")
Path(__file__).with_name("METHODOLOGY.md").write_text("\n".join(teile), encoding="utf-8")
print(f"METHODOLOGY.md: {len(AUFGABEN)} tasks")
