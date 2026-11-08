"""Run every test case end to end and save UNEDITED outputs + an automatic scorecard.

    python run_tests.py                       # uses NYAY_PROVIDER / NYAY_MODEL (default gemini)
    python run_tests.py --provider groq --model llama-3.3-70b-versatile
    python run_tests.py --provider manual     # cache-only: replays outputs/cache, writes prompts for misses

Each case is a full consultation: the client's story, their answers to the AI lawyer's questions over several
turns, then the drafts (and, in one case, a rehearsal). The transcript shows everything the client sees on each
turn - bottom line, case strength, reasoning, action plan, deadlines, proof, questions, the Supreme Court rulings
that fit (with the client's words that make them fit), the lawyer card, the law relied on - plus the engine trace
(routing, guard flags, raw model JSON). Drafts show the code checks and any review notes.

Outputs: outputs/<case>.md, outputs/summary.md and outputs/summary.json (pass/fail per automatic check).
The live app can run the same cases with its own model (see app.py, run page), so outputs come from the deployed app.
"""
import argparse
import json
import pathlib
import re
import sys

from nyay.engine import NyaySaathi, new_state
from nyay.guard import MARKER_RE
from nyay.llm import LLM, PendingResponse

ROOT = pathlib.Path(__file__).resolve().parent
SCRIPTS = {"devanagari": r"[ऀ-ॿ]", "tamil": r"[஀-௿]", "latin": r"[A-Za-z]"}
DOC_LABEL = {"legal_notice": "Legal notice", "consumer_complaint": "Consumer complaint (District Commission)",
             "dv_application": "Application under the DV Act, 2005", "police_complaint": "Police complaint (FIR request)"}
STRENGTH = {"strong": "Strong case", "moderate": "Moderate case", "weak": "Weak case", "unclear": "Needs more facts"}
REASONS = {"safety": "your safety may be at risk", "liberty": "an arrest, summons or case against you",
           "court_matter": "this is usually settled in court", "out_of_scope": "outside the verified law areas",
           "large_amount": "a large amount is at stake", "ambiguous": "key facts are still unclear"}


def script_ok(text, script):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    share = sum(bool(re.match(SCRIPTS[script], c)) for c in letters) / len(letters)
    return share > 0.5


def plain(x) -> str:
    return re.sub(r"\s+([.,;:!?])", r"\1", MARKER_RE.sub("", str(x or ""))).strip()


def quote_block(text: str) -> str:
    return "\n".join("> " + ln if ln.strip() else ">" for ln in str(text).strip().splitlines())


# ------------------------------------------------------------------ rendering: what the client sees, turn by turn
def render_chat(n: int, user: str, r: dict) -> str:
    out = [f"## Turn {n}\n\n### 🧑 Client\n{quote_block(user)}\n\n### ⚖️ Nyay Saathi — legal opinion\n"]
    if r.get("headline"):
        out.append(f"**Bottom line:** {plain(r['headline'])}\n")
    a = r.get("assessment") or {}
    if a.get("strength"):
        conf = f" (confidence: {a['confidence']})" if a.get("confidence") else ""
        out.append(f"**Case strength:** {STRENGTH.get(a['strength'], a['strength'])}{conf}"
                   + (f" — {plain(a['why'])}" if a.get("why") else "") + "\n")
    out.append("#### My reasoning\n" + (r.get("reply_body") or r["reply"]).strip() + "\n")
    esc = r.get("escalation") or {}
    if esc.get("level") in ("consult", "urgent"):
        why = "; ".join(REASONS.get(x, plain(x)) for x in esc.get("reasons", []))
        out.append(f"#### {'🚨 Speak to a human lawyer now' if esc['level'] == 'urgent' else '⚖️ I recommend a human lawyer'}\n"
                   f"{why or '-'}. Free legal aid: NALSA 15100 / District Legal Services Authority.\n")
    if esc.get("safety"):
        out.append("#### 🛟 Safety card shown\nHelplines: 112 (emergency), 181 (women), 14416 (Tele-MANAS), as applicable.\n")
    if r.get("next_steps"):
        out.append("#### Action plan\n" + "\n".join(
            f"{k}. {plain(s['step'])}" + (f" — _{plain(s['by_when'])}_" if plain(s.get("by_when")) not in ("", "-") else "")
            for k, s in enumerate(r["next_steps"], 1)) + "\n")
    if r.get("deadlines"):
        out.append("#### ⏰ Deadlines you must not miss\n" + "\n".join(f"- {plain(d)}" for d in r["deadlines"]) + "\n")
    if r.get("proof_have") or r.get("proof_missing"):
        out.append("#### Your proof\n" + "".join(f"- ✅ have: {plain(x)}\n" for x in r.get("proof_have", []))
                   + "".join(f"- ⏳ get / keep safe: {plain(x)}\n" for x in r.get("proof_missing", [])))
    if r.get("question_form"):
        out.append("#### Questions I need answered\n" + "\n".join(
            f"{k}. {plain(q['q'])}" + (f"  _(choices: {' / '.join(q['options'])})_" if q.get("options") else "")
            for k, q in enumerate(r["question_form"], 1)) + "\n")
    j = r.get("judgments")
    if j and j.get("none_fit"):
        out.append(f"#### Supreme Court rulings\nNone of the {j.get('considered', 0)} verified rulings on this kind of problem fits "
                   "these facts, so none is cited.\n")
    elif j:
        out.append(f"#### Supreme Court rulings that fit your facts (you: {j.get('side_label', '')})\n")
        for grp, title in (("for", "In your favour"), ("against", "Against you — what the other side may cite")):
            for c in j.get(grp, []):
                q = str(c.get("quote") or "")
                said = (f'from your case file: "{q[5:]}"' if q.startswith("case:") else f'you said: "{q}"') if q else ""
                out.append(f"- **{title}: {c['name']}** — Supreme Court, {c['date'][:4]}, {c['citation']}\n"
                           f"  - Why it fits: applies when {c.get('when', '')}; {said}\n"
                           f"  - Held: {c['holding']}\n"
                           + (f"  - What it means for you: {plain(c['why'])}\n" if c.get("why") else "")
                           + (f"  - Caution: {c['caution']}\n" if c.get("caution") else ""))
    if r.get("sources"):
        out.append("#### Law relied on (verified sources)\n" + "\n".join(
            f"{k}. {s['title']} — {s['url']}" for k, s in enumerate(r["sources"], 1)) + "\n")
    out.append(f"<details><summary>Engine trace</summary>\n\n"
               f"`routed_issue={r['routed_issue']}  model_issue={r['issue']}  needs_lawyer={r['needs_lawyer']}  "
               f"red_flags={r['red_flags']}  ready_to_draft={r['ready_to_draft']}  law_cards_given={len(r['cards_given'])}`\n\n"
               f"Guard flags: {json.dumps(r['guard_flags'], ensure_ascii=False) or 'none'}\n\n"
               f"Raw model output:\n\n```json\n{r['raw']}\n```\n</details>\n")
    return "\n".join(out)


def render_draft(t: dict, r: dict) -> str:
    who = "through an advocate" if r.get("sender") == "advocate" else "sent by the client personally"
    checks = "\n".join(f"- {'✅' if ok else '⚠️'} {name}" for name, ok in r.get("checks", []))
    notes = ("\n**Review notes still open after the automatic repair pass:**\n" + "\n".join(f"- {p}" for p in r["problems"])
             if r.get("problems") else "\n**Review notes:** none - every drafting check passed.")
    return (f"## 📝 Draft: {DOC_LABEL.get(t['doc_type'], t['doc_type'])} ({who})\n\n"
            f"**Checked before the client sees it (code):**\n{checks}\n"
            f"{notes}\n\n_Automatic repair pass used: {'yes' if r.get('repaired') else 'no'}_\n\n"
            f"```text\n{r['document']}\n```\n\n**Blanks to fill:** {', '.join(r['blanks']) or 'none'}\n\n"
            f"**Note to the client:**\n{quote_block(r.get('user_note') or '-')}\n\n"
            f"Guard flags: {json.dumps(r['guard_flags'], ensure_ascii=False) or 'none'}\n")


def run_case(bot, case):
    state = new_state()
    practise_hist, blocks, transcript, results, n = [], 0, [], [], 0
    for t in case["turns"]:
        if t["type"] == "chat":
            n += 1
            r = bot.turn(state, t["text"])
            transcript.append(render_chat(n, t["text"], r))
        elif t["type"] == "draft":
            r = bot.draft(state, t["doc_type"], t.get("details"))
            transcript.append(render_draft(t, r))
        elif t["type"] == "practise":
            r = bot.practise(state, practise_hist, t["text"], t["opponent"])
            transcript.append(f"## 🥊 Rehearsal\n\n**Client:** {t['text']}\n\n**{t['opponent'].capitalize()} (played by the AI):**\n\n"
                              f"{r['reply'].strip()}\n")
        blocks += sum(f["severity"] == "block" for f in r["guard_flags"])
        results.append((t, r))
    return state, results, transcript, blocks


def score(case, state, results, blocks):
    e = case.get("expect", {})
    chats = [r for t, r in results if t["type"] == "chat"]
    drafts = [r for t, r in results if t["type"] == "draft"]
    text = "\n".join(r["reply"] for r in chats)
    shown = {c["id"] for r in chats for g in ("for", "against") for c in ((r.get("judgments") or {}).get(g) or [])}
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
    if "judgments_shown_any" in e:
        checks["fitting_rulings_shown"] = bool(shown & set(e["judgments_shown_any"]))
    if "judgments_never" in e:
        checks["unfitting_rulings_left_out"] = not (shown & set(e["judgments_never"]))
    if "draft_must_not_include" in e:
        checks["draft_clean"] = not any(s in r["document"] for r in drafts for s in e["draft_must_not_include"])
    if drafts:
        checks["drafts_verified_law_only"] = not any("⚠️[unverified]" in r["document"] for r in drafts)
    checks["json_parsed"] = not any(r.get("parse_error") for r in chats)
    stats = {"turns": len(chats), "questions_asked": sum(len(r.get("question_form") or []) for r in chats),
             "rulings_shown": sorted(shown), "drafts": len(drafts),
             "draft_review_notes": sum(len(r.get("problems") or []) for r in drafts)}
    return checks, stats


def run_one(bot, case, when: str = "") -> tuple[str, dict]:
    """One case end to end -> (markdown transcript, summary row). Used by this script and by the app's run page."""
    state, results, transcript, blocks = run_case(bot, case)
    checks, stats = score(case, state, results, blocks)
    passed = all(checks.values())
    row = {"id": case["id"], "about": case["about"], "passed": passed, "checks": checks, "guard_blocks": blocks,
           "model": bot.llm.name, **stats}
    head = (f"# {case['id']}\n\n_{case['about']}_\n\n"
            f"| | |\n|---|---|\n| Model | `{bot.llm.name}`{' (the live app, ' + when + ')' if when else ''} |\n"
            f"| Auto-checks | {'✅ PASS' if passed else '❌ FAIL'} — "
            + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items()) + " |\n"
            f"| Consultation | {stats['turns']} client turns · {stats['questions_asked']} questions asked by the AI · "
            f"{len(stats['rulings_shown'])} Supreme Court rulings shown · {stats['drafts']} draft(s) |\n\n"
            "Unedited output: every reply below is exactly what the app produced.\n\n---\n\n")
    md = head + "\n---\n\n".join(transcript) + (
        f"\n---\n\n## Final case file (built by the AI over the conversation)\n\n```json\n"
        f"{json.dumps(state['case'], ensure_ascii=False, indent=2)}\n```\n")
    return md, row


def summary_md(rows: list[dict]) -> str:
    n = sum(r["passed"] for r in rows)
    lines = [f"# Test summary — {n}/{len(rows)} cases pass all automatic checks", "",
             "Each case is a full multi-turn consultation (story → the AI's questions → answers → opinion and plan → drafts).", "",
             "| case | about | result | turns | questions asked | rulings shown | drafts | checks |", "|---|---|---|---|---|---|---|---|"]
    lines += [f"| [{r['id']}]({r['id']}.md) | {r['about']} | {'✅' if r['passed'] else '❌'} | {r['turns']} | {r['questions_asked']} | "
              f"{', '.join(x.replace('JUD-', '') for x in r['rulings_shown']) or '-'} | {r['drafts']} | "
              f"{', '.join(k + ('✓' if v else '✗') for k, v in r['checks'].items())} |" for r in rows]
    return "\n".join(lines) + "\n"


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
    rows, pending = [], 0
    for case in cases:
        try:
            md, row = run_one(bot, case)
        except PendingResponse:
            pending += 1
            print(f"… {case['id']}: waiting for a response (manual provider)")
            continue
        (out / f"{case['id']}.md").write_text(md)
        rows.append(row)
        print(f"{'PASS' if row['passed'] else 'FAIL'} {case['id']} {row['checks']}")
    if rows:
        (out / "summary.md").write_text(summary_md(rows))
        (out / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n{sum(r['passed'] for r in rows)}/{len(rows)} cases pass. {pending} pending.")
    return 0 if not pending else 2


if __name__ == "__main__":
    sys.exit(main())
