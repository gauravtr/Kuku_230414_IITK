"""Conversation engine. Code decides routing, safety and verification; the model only
does the language work (understanding the story, explaining, drafting).

  user text -> [code] red-flag check + issue routing -> pick law cards
            -> [model] case file + reply as JSON
            -> [code] citation guard + safety enforcement -> user
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

from . import prompts
from .guard import check, footer
from .kb import KB
from .llm import LLM


def today() -> str:
    return os.getenv("NYAY_TODAY") or dt.date.today().isoformat()


def new_state(language: str = "auto") -> dict:
    return {"history": [], "case": {}, "issue": None, "language": language, "red_flags": [], "log": []}


def parse_json(raw: str) -> dict | None:
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", s, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


class NyaySaathi:
    def __init__(self, llm: LLM | None = None, kb: KB | None = None):
        self.llm = llm or LLM()
        self.kb = kb or KB()

    # ----------------------------------------------------------------- chat
    def turn(self, state: dict, user_text: str) -> dict:
        kb = self.kb
        # 1. code: routing. Sticky once known; re-scored on every message.
        all_user_text = " ".join([m["content"] for m in state["history"] if m["role"] == "user"] + [user_text])
        scores = kb.classify(all_user_text)
        issue = state["issue"] or (next(iter(scores)) if scores else "other")
        if state["issue"] and scores and next(iter(scores)) != state["issue"] and scores[next(iter(scores))] >= 3 + scores.get(state["issue"], 0):
            issue = next(iter(scores))  # user clearly moved to another problem
        issues = [issue] + [k for k in scores if k != issue][:1]   # main issue + runner-up
        cards = kb.cards_for(issues)

        # 2. code: safety
        flags = kb.detect_red_flags(user_text)
        for f in flags:
            if f["id"] not in state["red_flags"]:
                state["red_flags"].append(f["id"])
        active = [f for f in kb.red_flags if f["id"] in state["red_flags"]]
        redflag_rule = prompts.REDFLAG_RULE.format(
            flags=", ".join(f["id"] for f in active), messages=" | ".join(f["message"] for f in active)) if active else ""

        system = prompts.TURN_SYSTEM.format(
            today=today(),
            language_rule=prompts.LANG_AUTO if state["language"] == "auto" else state["language"],
            redflag_rule=redflag_rule,
            issue_label=kb.issues[issue]["label"],
            playbook=json.dumps({k: v for k, v in kb.issues[issue].items() if k != "keywords"}, ensure_ascii=False),
            cards="\n".join(f"[{c['id']}] {c['title']}: {c['text']}" for c in cards),
            case_file=json.dumps(state["case"], ensure_ascii=False) if state["case"] else "{} (empty - first message)",
        )
        messages = state["history"] + [{"role": "user", "content": user_text}]

        # 3. model
        raw = self.llm.chat(system, messages, json_mode=True)
        out = parse_json(raw)
        if out is None:
            out = {"reply": raw, "case_file": state["case"], "needs_lawyer": bool(active),
                   "lawyer_reason": "", "ready_to_draft": "none", "issue": issue, "_parse_error": True}

        # 4. code: verify + enforce
        g = check(out.get("reply", ""), kb)
        reply = g.text
        if active and not any(n in reply for f in active for n in re.findall(r"\b1\d{2,4}\b", f["message"])):
            reply = "⚠️ " + " ".join(f["message"] for f in active) + "\n\n" + reply   # model forgot -> code adds it
        needs_lawyer = bool(out.get("needs_lawyer")) or bool(active) or issue == "other"
        foot = footer(g)
        final = reply + (f"\n\n{foot}" if foot else "")

        state["history"] += [{"role": "user", "content": user_text}, {"role": "assistant", "content": out.get("reply", "")}]
        state["case"] = out.get("case_file") or state["case"]
        state["issue"] = out.get("issue") if out.get("issue") in kb.issues else issue
        result = {"reply": final, "issue": state["issue"], "routed_issue": issue, "cards_given": [c["id"] for c in cards],
                  "needs_lawyer": needs_lawyer, "lawyer_reason": out.get("lawyer_reason", ""),
                  "ready_to_draft": out.get("ready_to_draft", "none"), "red_flags": [f["id"] for f in active],
                  "guard_flags": g.flags, "sources": g.sources, "case_file": state["case"],
                  "parse_error": out.get("_parse_error", False), "model": self.llm.name, "raw": raw}
        state["log"].append({k: v for k, v in result.items() if k != "raw"})
        return result

    # --------------------------------------------------------------- drafting
    def draft(self, state: dict, doc_type: str = "legal_notice") -> dict:
        t = prompts.TEMPLATES[doc_type]
        cards = self.kb.cards_for([state["issue"] or "other"])
        lang = "the user's language" if state["language"] == "auto" else state["language"]
        system = prompts.DRAFT_SYSTEM.format(
            doc_label=t["label"], language=lang, today=today(), template=t["structure"],
            cards="\n".join(f"[{c['id']}] {c['title']}: {c['text']}" for c in cards),
            case_file=json.dumps(state["case"], ensure_ascii=False))
        convo = "\n".join(f"{m['role']}: {m['content']}" for m in state["history"][-8:])
        raw = self.llm.chat(system, [{"role": "user", "content": f"Conversation so far:\n{convo}\n\nDraft the {t['label']} now."}],
                            json_mode=True, max_tokens=8192)
        out = parse_json(raw) or {"document": raw, "blanks": [], "user_note": ""}
        g = check(out.get("document", ""), self.kb)
        blanks = sorted(set(re.findall(r"\[[A-Z][A-Z0-9 /&',.\-]{2,60}\]", g.text)))
        res = {"document": g.text, "blanks": blanks, "user_note": out.get("user_note", ""),
               "guard_flags": g.flags, "model": self.llm.name, "raw": raw}
        state["log"].append({"draft": doc_type, "guard_flags": g.flags, "blanks": blanks})
        return res

    # --------------------------------------------------------------- practise
    def practise(self, state: dict, practise_history: list[dict], user_text: str, opponent: str) -> dict:
        cards = self.kb.cards_for([state["issue"] or "other"])
        lang = "the same language the user writes in" if state["language"] == "auto" else state["language"]
        system = prompts.PRACTISE_SYSTEM.format(opponent=opponent, case_file=json.dumps(state["case"], ensure_ascii=False),
                                                language=lang, card_ids=", ".join(c["id"] for c in cards))
        msgs = practise_history + [{"role": "user", "content": user_text}]
        raw = self.llm.chat(system, msgs, temperature=0.7, max_tokens=2048)
        g = check(raw, self.kb)
        shown = g.text + (f"\n\n{footer(g)}" if g.flags else "")
        practise_history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": shown}]
        return {"reply": shown, "guard_flags": g.flags, "model": self.llm.name, "raw": raw}
