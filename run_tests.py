"""Run every test case end to end and save UNEDITED outputs + an automatic scorecard.

    python run_tests.py                       # uses NYAY_PROVIDER / NYAY_MODEL (default gemini)
    python run_tests.py --provider groq --model llama-3.3-70b-versatile
    python run_tests.py --provider manual     # cache-only: replays outputs/cache, writes prompts for misses

Outputs: outputs/<case>.md (transcript as the user sees it + case file + guard flags + raw model JSON),
         outputs/summary.md and outputs/summary.json (pass/fail per automatic check).
"""
import argparse
import json
import pathlib
import re
import sys

from nyay.engine import NyaySaathi, new_state
from nyay.llm import LLM, PendingResponse

ROOT = pathlib.Path(__file__).resolve().parent
SCRIPTS = {"devanagari": r"[ऀ-ॿ]", "tamil": r"[஀-௿]", "latin": r"[A-Za-z]"}


def script_ok(text, script):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    share = sum(bool(re.match(SCRIPTS[script], c)) for c in letters) / len(letters)
    return share > 0.5


def run_case(bot, case):
    state = new_state()
    practise_hist, blocks, transcript, results = [], 0, [], []
    for t in case["turns"]:
        if t["type"] == "chat":
            r = bot.turn(state, t["text"])
            transcript.append(f"### 🧑 User\n{t['text']}\n\n### ⚖️ Nyay Saathi\n{r['reply']}\n\n"
                              f"`routed_issue={r['routed_issue']}  model_issue={r['issue']}  needs_lawyer={r['needs_lawyer']}  "
                              f"red_flags={r['red_flags']}  ready_to_draft={r['ready_to_draft']}  cards_given={len(r['cards_given'])}`\n\n"
                              f"Guard flags: {json.dumps(r['guard_flags'], ensure_ascii=False) or 'none'}\n\n"
                              f"<details><summary>Raw model output</summary>\n\n```json\n{r['raw']}\n```\n</details>\n")
        elif t["type"] == "draft":
            r = bot.draft(state, t["doc_type"])
            transcript.append(f"### 📝 Draft: {t['doc_type']}\n\n```\n{r['document']}\n```\n\n**Blanks to fill:** "
                              f"{', '.join(r['blanks']) or 'none'}\n\n**Note to user:** {r['user_note']}\n\n"
                              f"Guard flags: {json.dumps(r['guard_flags'], ensure_ascii=False) or 'none'}\n")
        elif t["type"] == "practise":
            r = bot.practise(state, practise_hist, t["text"], t["opponent"])
            transcript.append(f"### 🥊 Practise — user\n{t['text']}\n\n### 🥊 {t['opponent']} (AI)\n{r['reply']}\n")
        blocks += sum(f["severity"] == "block" for f in r["guard_flags"])
        results.append(r)
    return state, results, transcript, blocks


def score(case, state, results, blocks):
    e, chats = case.get("expect", {}), [r for r in results if "routed_issue" in r]
    text = "\n".join(r["reply"] for r in chats)
    checks = {}
    if "issue" in e:
        checks["issue"] = state["issue"] == e["issue"]
    if "needs_lawyer" in e:
        checks["needs_lawyer"] = any(r["needs_lawyer"] for r in chats) == e["needs_lawyer"]
    if "must_include_any" in e:
        checks["must_include_any"] = any(s.lower() in text.lower() for s in e["must_include_any"])
    if "must_not_include" in e:
        checks["must_not_include"] = not any(s in text for s in e["must_not_include"])
    if "max_guard_blocks" in e:
        checks["guard_clean"] = blocks <= e["max_guard_blocks"]
    if "script" in e:
        checks["language"] = script_ok(chats[0]["reply"].split("**Sources")[0], e["script"])
    checks["json_parsed"] = not any(r.get("parse_error") for r in chats)
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider"), ap.add_argument("--model")
    ap.add_argument("--cases", default=str(ROOT / "tests/cases.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs"))
    ap.add_argument("--only", help="run one case id")
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(exist_ok=True)
    bot = NyaySaathi(LLM(a.provider, a.model, cache_dir=str(out / "cache")))
    cases = [c for c in json.loads(pathlib.Path(a.cases).read_text()) if not a.only or c["id"] == a.only]
    summary, pending = [], 0
    for case in cases:
        try:
            state, results, transcript, blocks = run_case(bot, case)
        except PendingResponse:
            pending += 1
            print(f"… {case['id']}: waiting for a response (manual provider)")
            continue
        checks = score(case, state, results, blocks)
        passed = all(checks.values())
        summary.append({"id": case["id"], "about": case["about"], "passed": passed, "checks": checks, "guard_blocks": blocks,
                        "model": bot.llm.name})
        md = (f"# {case['id']}\n_{case['about']}_\n\nModel: `{bot.llm.name}`  |  Auto-checks: "
              f"{'✅ PASS' if passed else '❌ FAIL'} {json.dumps(checks)}\n\n" + "\n---\n".join(transcript) +
              f"\n---\n## Final case file\n```json\n{json.dumps(state['case'], ensure_ascii=False, indent=2)}\n```\n")
        (out / f"{case['id']}.md").write_text(md)
        print(f"{'PASS' if passed else 'FAIL'} {case['id']} {checks}")
    if summary:
        n = sum(s["passed"] for s in summary)
        lines = [f"# Test summary — {n}/{len(summary)} cases pass all automatic checks", "",
                 "| case | about | result | checks | guard blocks |", "|---|---|---|---|---|"]
        lines += [f"| {s['id']} | {s['about']} | {'✅' if s['passed'] else '❌'} | "
                  f"{', '.join(k + ('✓' if v else '✗') for k, v in s['checks'].items())} | {s['guard_blocks']} |" for s in summary]
        (out / "summary.md").write_text("\n".join(lines) + "\n")
        (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
        print(f"\n{n}/{len(summary)} cases pass. {pending} pending.")
    return 0 if not pending else 2


if __name__ == "__main__":
    sys.exit(main())
