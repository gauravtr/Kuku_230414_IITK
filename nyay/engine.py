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
from .guard import MARKER_RE, check, footer
from .kb import KB
from .llm import LLM


def MARKER_STRIP(text: str) -> str:
    return MARKER_RE.sub("", text).replace("  ", " ").strip()


def today() -> str:
    return os.getenv("NYAY_TODAY") or dt.date.today().isoformat()


SCRIPTS = [("\u0900", "\u097f", None), ("\u0b80", "\u0bff", "Tamil"), ("\u0980", "\u09ff", "Bengali"),
           ("\u0c00", "\u0c7f", "Telugu"), ("\u0c80", "\u0cff", "Kannada"), ("\u0a80", "\u0aff", "Gujarati"),
           ("\u0d00", "\u0d7f", "Malayalam"), ("\u0a00", "\u0a7f", "Punjabi in Gurmukhi script")]
HINGLISH = re.compile(r"\b(hai|hain|nahi|nahin|kya|kaise|kyun|mera|meri|mujhe|maine|paisa|wapas|karo|kar|diya|liya|"
                      r"raha|rahi|tha|thi|aur|lekin|abhi|bhi|ka|ki|ke)\b", re.I)


def detect_language(text: str) -> str:
    """The user's language, decided in code from their own words, so drafts never drift into another language."""
    for lo, hi, name in SCRIPTS:
        if any(lo <= ch <= hi for ch in text):
            return name or f'the same language as this message, in Devanagari script: "{text[:150]}"'
    return "Hinglish (Hindi in Latin script)" if len(HINGLISH.findall(text)) >= 3 else "English"


def new_state(language: str = "auto") -> dict:
    return {"history": [], "case": {}, "issue": None, "language": language, "red_flags": [], "log": [],
            "assessment": {}, "escalation": {"level": "none", "reasons": []}, "plan": [], "open_questions": []}


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


STRENGTHS = ("strong", "moderate", "weak", "unclear")
ESC_CODES = ("safety", "liberty", "court_matter", "out_of_scope", "large_amount", "ambiguous")
INTAKE_TURNS = 3   # while still asking questions in the first 3 turns, no "consult a lawyer" card
LARGE_AMOUNT = 500_000   # Rs 5 lakh: above this, a human lawyer should look at it (playbooks agree)


def parse_amount(text) -> int | None:
    """'Rs 60,000' -> 60000, '1.5 lakh' -> 150000, '2 crore' -> 20000000. None if no number."""
    if not text:
        return None
    t = str(text).lower().replace(",", "")
    unit = {"lakh": 1e5, "lac": 1e5, "crore": 1e7, "cr": 1e7, "k": 1e3}
    nums = [float(n) * unit.get(u or "", 1) for n, u in re.findall(r"(\d+(?:\.\d+)?)\s*(lakh|lac|crore|cr|k)?\b", t)]
    return int(max(nums)) if nums else None   # "Rs 50,000 deposit / Rs 6 lakh claim" -> the larger stake counts


def decide_escalation(out: dict, active_flags: list, issue: str, case: dict, turn_no: int) -> dict:
    """Code, not the model, has the final say on 'you need a real lawyer'. Returns {level, reasons, safety}.
    level: none | consult | urgent. Reasons are short English codes the UI turns into plain words.
    safety: red-flag ids that need a safety card (helplines), which is NOT the same as 'get a lawyer'.

    Intake first: a client doesn't know which facts matter, so while the AI lawyer is still asking
    questions (first 3 turns), a 'consult a lawyer' card is held back. Only urgent matters
    (arrest, summons, a case against the client, a deadline within days) skip the wait."""
    level, reasons = "none", []
    order = ["none", "consult", "urgent"]

    def bump(new, why):
        nonlocal level
        level = max(level, new, key=order.index)
        if why and why not in reasons:
            reasons.append(why)

    esc = out.get("escalate") if isinstance(out.get("escalate"), dict) else {}
    if esc.get("needed"):
        bump("urgent" if esc.get("level") == "urgent" else "consult", esc.get("reason") or "")
    safety = []
    for f in active_flags:
        kind = f.get("escalate", "urgent")
        if kind == "safety":
            safety.append(f["id"])
        elif kind in ("consult", "urgent"):
            bump(kind, "liberty" if kind == "urgent" else "court_matter")
    if issue == "other":
        bump("consult", "out_of_scope")
    amt = parse_amount((case or {}).get("amount_at_stake"))
    if amt and amt > LARGE_AMOUNT:
        bump("consult", "large_amount")
    a = out.get("assessment") if isinstance(out.get("assessment"), dict) else {}
    if turn_no >= 4 and (a.get("confidence") == "low" or a.get("strength") == "unclear") and out.get("open_questions"):
        bump("consult", "ambiguous")   # still unclear after several rounds of questions
    still_asking = bool(out.get("open_questions")) and turn_no <= INTAKE_TURNS
    if level == "consult" and still_asking:
        level, reasons = "none", []    # take the facts first; the card can come once they are in
    return {"level": level, "reasons": reasons, "safety": safety}


def pick_judgments(kb, issue: str, side, notes, verify) -> dict | None:
    """Split the verified judgment cards for this issue into 'for you' / 'against you' from the client's
    side. The model's picks come first; code tops each group up so the client always sees at least two
    rulings against them (what the other side will argue) whenever the cards exist. Max 3 per group."""
    sides = kb.sides.get(issue) or {}
    if not sides:
        return None
    side = side if side in sides else next(iter(sides))
    notes = notes if isinstance(notes, dict) else {}
    cards = sorted(kb.judgments_for(issue), key=lambda c: c["date"], reverse=True)   # latest first
    picked = [c for c in cards if c["id"] in notes]
    groups = {"for": [], "against": []}
    for c in picked + [c for c in cards if c not in picked]:
        g = "for" if c["favours"] == side else "against"
        if len(groups[g]) < (3 if c in picked else 2):
            groups[g].append({k: c[k] for k in ("id", "name", "date", "citation", "holding", "applies", "caution", "url")}
                             | {"why": verify(notes.get(c["id"]))})
    for g in groups.values():
        g.sort(key=lambda c: c["date"], reverse=True)
    return {"side": side, "side_label": sides[side], **groups} if groups["for"] or groups["against"] else None


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
        redflag_rule = "".join(prompts.REDFLAG_RULE[f.get("escalate", "urgent")].format(message=f["message"]) for f in active)

        system = prompts.TURN_SYSTEM.format(
            today=today(),
            language_rule=prompts.LANG_AUTO if state["language"] == "auto" else state["language"],
            redflag_rule=redflag_rule,
            issue_label=kb.issues[issue]["label"],
            playbook=json.dumps({k: v for k, v in kb.issues[issue].items() if k != "keywords"}, ensure_ascii=False),
            cards="\n".join(f"[{c['id']}] {c['title']}: {c['text']}" for c in cards),
            judgments="\n".join(f"[{j['id']}] {j['name']} ({j['date'][:4]}, {j['citation']}) - favours {j['favours']}: {j['holding']}"
                                + (f" Caution: {j['caution']}" if j.get("caution") else "")
                                for j in kb.judgments_for(issue)) or "(none for this problem type)",
            sides=", ".join(f"{k} = {v}" for k, v in kb.sides.get(issue, {}).items()) or "-",
            case_file=json.dumps(state["case"], ensure_ascii=False) if state["case"] else "{} (empty - first message)",
        )
        messages = state["history"] + [{"role": "user", "content": user_text}]

        # 3. model
        raw = self.llm.chat(system, messages, json_mode=True)
        out = parse_json(raw)
        if out is None:
            out = {"reply": raw, "case_file": state["case"], "ready_to_draft": "none", "issue": issue, "_parse_error": True}
        if "escalate" not in out and "needs_lawyer" in out:   # older output shape
            out["escalate"] = {"needed": bool(out["needs_lawyer"]), "level": "consult", "reason": out.get("lawyer_reason", "")}

        # 4. code: verify + enforce
        g = check(out.get("reply", ""), kb)
        reply = g.text
        missed = [f["message"] for f in active if f.get("escalate") != "consult"
                  and (nums := re.findall(r"\b1\d{2,4}\b", f["message"])) and not any(n in reply for n in nums)]
        if missed:
            reply = "⚠️ " + " ".join(missed) + "\n\n" + reply   # model forgot a helpline -> code adds it
        case = out.get("case_file") or state["case"]
        turn_no = 1 + sum(m["role"] == "user" for m in state["history"])
        esc = decide_escalation(out, active, issue, case, turn_no)
        a = out.get("assessment") if isinstance(out.get("assessment"), dict) else {}
        def verified(text) -> str:   # side texts get the same guard; anything with unverified law is dropped
            text = str(text or "").strip()
            return MARKER_STRIP(text) if text and check(text, kb).clean else ""
        assessment = {"strength": a.get("strength") if a.get("strength") in STRENGTHS else "unclear",
                      "why": verified(a.get("why")), "confidence": a.get("confidence", "")}
        next_steps = [{"step": verified(x.get("step")), "by_when": str(x.get("by_when") or "").strip(" -")}
                      for x in (out.get("next_steps") or []) if isinstance(x, dict)]
        next_steps = [x for x in next_steps if x["step"]][:6]
        def question(q):   # {"q": text, "options": [..]} or a bare string -> verified dict, or None
            text, opts = (q.get("q") or q.get("question"), q.get("options")) if isinstance(q, dict) else (q, [])
            text = verified(text)
            opts = [o for o in (verified(o) for o in (opts or []) if isinstance(o, (str, int, float))) if o and len(o) <= 60]
            return {"q": text, "options": list(dict.fromkeys(opts))[:6]} if text else None
        qform = [x for x in (question(q) for q in (out.get("open_questions") or [])) if x][:5]
        open_q = [x["q"] for x in qform]
        # Supreme Court judgments: picked by code from verified cards; the model only says whose side the
        # client is on and why each ruling matters. Shown once the facts are in (or when the client asks).
        asked = bool(re.search(r"judg|case ?law|precedent|ruling|supreme court|फैसल|निर्णय|नज़ीर|नजीर", user_text, re.I))
        jout = out.get("judgments") if isinstance(out.get("judgments"), dict) else {}
        judgments = None
        model_ready = isinstance(jout.get("notes"), dict) and len(jout["notes"]) >= 2   # model judged the facts sufficient
        if kb.judgments_for(issue) and (model_ready or not open_q or turn_no >= INTAKE_TURNS or asked):
            judgments = pick_judgments(kb, issue, jout.get("client_side"), jout.get("notes"), verified)
        if esc["reasons"]:
            esc["reasons"] = [r if r in ESC_CODES else verified(r) for r in esc["reasons"]]
            esc["reasons"] = [r for r in esc["reasons"] if r]
        foot = footer(g)
        final = reply + (f"\n\n{foot}" if foot else "")

        state["history"] += [{"role": "user", "content": user_text}, {"role": "assistant", "content": out.get("reply", "")}]
        state["case"] = case
        state["issue"] = out.get("issue") if out.get("issue") in kb.issues else issue
        state["assessment"], state["escalation"] = assessment, esc
        if next_steps:
            state["plan"] = next_steps
        state["open_questions"] = open_q
        if judgments:
            state["judgments"] = judgments
        result = {"reply": final, "reply_body": reply, "issue": state["issue"], "routed_issue": issue,
                  "cards_given": [c["id"] for c in cards],
                  "needs_lawyer": esc["level"] != "none", "lawyer_reason": "; ".join(esc["reasons"]),
                  "escalation": esc, "assessment": assessment, "next_steps": next_steps, "open_questions": open_q,
                  "question_form": qform, "judgments": judgments,
                  "ready_to_draft": out.get("ready_to_draft", "none"), "red_flags": [f["id"] for f in active],
                  "guard_flags": g.flags, "sources": g.sources, "case_file": state["case"],
                  "parse_error": out.get("_parse_error", False), "model": self.llm.name, "raw": raw}
        state["log"].append({k: v for k, v in result.items() if k != "raw"})
        return result

    # --------------------------------------------------------------- drafting
    def draft(self, state: dict, doc_type: str = "legal_notice") -> dict:
        t = prompts.TEMPLATES[doc_type]
        cards = self.kb.cards_for([state["issue"] or "other"])
        last_user = next((m["content"] for m in reversed(state["history"]) if m["role"] == "user"), "")
        lang = detect_language(last_user) if state["language"] == "auto" else state["language"]
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
        for c in cards:   # coach tips may cite a bare card ID; bracket it so it becomes a numbered, linked source
            raw = re.sub(rf"(?<!\[){re.escape(c['id'])}(?!\])", f"[{c['id']}]", raw)
        g = check(raw, self.kb)
        shown = g.text + (f"\n\n{footer(g)}" if g.flags or g.sources else "")
        practise_history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": shown}]
        return {"reply": shown, "guard_flags": g.flags, "model": self.llm.name, "raw": raw}
