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
    def draft(self, state: dict, doc_type: str = "legal_notice", details: dict | None = None) -> dict:
        """Draft a document from the case file. Code picks the law and the judgments the model may use, then
        checks the draft (lint_draft) and, if it falls short, asks the model once to fix exactly those points."""
        kb, t = self.kb, prompts.TEMPLATES[doc_type]
        issue = state.get("issue") or "other"
        cards = kb.cards_for([issue])
        details = {k: str(v).strip() for k, v in (details or {}).items() if str(v or "").strip()}
        sender = details.pop("sender", "self") if details.get("sender") in ("self", "advocate") else "self"
        details.pop("sender", None)
        last_user = next((m["content"] for m in reversed(state["history"]) if m["role"] == "user"), "")
        lang = detect_language(last_user) if state["language"] == "auto" else state["language"]
        j = state.get("judgments") or pick_judgments(kb, issue, None, {}, lambda x: str(x or ""))
        jfor, jagainst = (j or {}).get("for", []), (j or {}).get("against", [])
        def jline(c):
            return (f"[{c['id']}] {c['name']} ({c['date'][:4]}), {c['citation']}: {c['holding']}"
                    + (f" Caution: {c['caution']}" if c.get("caution") else ""))
        d = dt.date.fromisoformat(today())
        system = prompts.DRAFT_SYSTEM.format(
            doc_label=t["label"], language=lang, today=today(), today_long=f"{d.day} {d.strftime('%B %Y')}",
            sender_rule=prompts.SENDER_RULES[sender] if doc_type == "legal_notice" else
            "The client signs it personally, in the first person.",
            template=t["structure"],
            cards="\n".join(f"[{c['id']}] {c['title']}: {c['text']}" for c in cards),
            judgments_for="\n".join(jline(c) for c in jfor) or "(none - cite no case law)",
            judgments_against="\n".join(jline(c) for c in jagainst) or "(none)",
            details=json.dumps(details, ensure_ascii=False) if details else "(none given - use specific blanks)",
            case_file=json.dumps(state["case"], ensure_ascii=False))
        convo = "\n".join(f"{m['role']}: {m['content']}" for m in state["history"][-10:])
        ask = [{"role": "user", "content": f"Conversation so far:\n{convo}\n\nDraft the {t['label']} now."}]
        raw = self.llm.chat(system, ask, json_mode=True, max_tokens=8192)
        out = parse_json(raw) or {"document": raw, "blanks": [], "user_note": ""}
        doc = MARKER_STRIP_KEEP(out.get("document", ""))
        problems = lint_draft(doc, doc_type, sender, kb)
        repaired = False
        if problems:   # one repair pass: the model fixes exactly what code found, nothing else
            fix = ask + [{"role": "assistant", "content": json.dumps({"document": doc}, ensure_ascii=False)},
                         {"role": "user", "content": "A legal reviewer checked this draft and found these problems:\n- "
                          + "\n- ".join(problems) + "\nReturn the corrected full document in the same JSON format. "
                          "Fix exactly these points; keep everything else as it is."}]
            raw2 = self.llm.chat(system, fix, json_mode=True, max_tokens=8192)
            out2 = parse_json(raw2)
            if out2 and out2.get("document"):
                doc2 = MARKER_STRIP_KEEP(out2["document"])
                p2 = lint_draft(doc2, doc_type, sender, kb)
                if len(p2) < len(problems):
                    doc, problems, repaired = doc2, p2, True
                    out["user_note"] = out2.get("user_note") or out.get("user_note", "")
        g = check(doc, kb)
        blanks = sorted(set(re.findall(r"\[[A-Z][A-Z0-9 /&',.()?:\-]{2,90}\]", g.text)))
        res = {"document": g.text, "blanks": blanks, "user_note": out.get("user_note", ""), "sender": sender,
               "checks": draft_checks(g.text, doc_type, sender), "problems": problems, "repaired": repaired,
               "guard_flags": g.flags, "model": self.llm.name, "raw": raw}
        state["log"].append({"draft": doc_type, "guard_flags": g.flags, "blanks": blanks, "problems": problems})
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


# ------------------------------------------------------------------ draft quality checks (code, not model)
BANNED_PHRASES = ["incontrovertible", "irrefutable", "conclusively prove", "conclusively establish", "beyond any doubt",
                  "sole cost", "own peril", "at your risk and cost", "risks and consequences", "risk and consequences",
                  "dire consequences", "strictest action", "without any further notice"]
VERDICT_RE = re.compile(r"\byou (?:have|had) (?:committed|extorted|blackmailed|defamed|cheated|stalked)\b|\byou are guilty\b"
                        r"|\boffences? (?:is|are|has been|have been) (?:clearly )?(?:made out|committed)\b", re.I)
NOTICE_HEADINGS = [("FACTS", "a 'FACTS IN ORDER OF DATE' section"), ("EVIDENCE", "an evidence schedule"),
                   ("LEGAL POSITION", "a 'LEGAL POSITION' section"), ("DEMANDS", "a numbered 'DEMANDS' section"),
                   ("MANNER OF REPLY", "a 'TIME FOR COMPLIANCE AND MANNER OF REPLY' section"),
                   ("CONSEQUENCES", "one 'CONSEQUENCES OF NON-COMPLIANCE' paragraph"),
                   ("RESERVATION OF RIGHTS", "a 'RESERVATION OF RIGHTS' section"), ("ENCLOSURES", "an 'ENCLOSURES' list"),
                   ("SERVICE RECORD", "the 'SERVICE RECORD' office-copy block")]
VAGUE_BLANK_RE = re.compile(r"\[(?:DATE|DETAILS|NAME|ADDRESS|AMOUNT|PLACE|X|XX|___+)\]")


def MARKER_STRIP_KEEP(text: str) -> str:
    """Drafts never carry [CARD-ID] markers; strip them and any markdown the model added."""
    text = MARKER_RE.sub("", str(text or ""))
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return re.sub(r"(?m)^#{1,6}\s*", "", text).replace(" .", ".").strip()


def has_heading(doc: str, key: str) -> bool:
    """A section heading: the key in capitals at the start of a line (after an optional number like '4.' or 'B.')."""
    return re.search(rf"(?m)^\s*(?:[0-9A-H]{{1,2}}[.)]\s*)?[A-Z ,&/-]*{re.escape(key)}", doc) is not None


def lint_draft(doc: str, doc_type: str, sender: str, kb) -> list[str]:
    """Problems a careful senior advocate would mark on the draft. Empty list = passes."""
    low, probs = doc.lower(), []
    for ph in BANNED_PHRASES:
        if ph in low:
            probs.append(f'Remove "{ph}": overstated or aggressive; use measured language ("records", "shows", "costs as the court may allow").')
    for m in VERDICT_RE.finditer(doc):
        probs.append(f'"{m.group(0)}" states guilt as settled; rephrase as an allegation ("the conduct described, if established, would constitute ...").')
    for b in sorted(set(VAGUE_BLANK_RE.findall(doc))):
        probs.append(f"{b} is too vague; name exactly what to fill, e.g. [DATE OF THE FIRST THREAT MESSAGE].")
    bad = [f["mention"] for f in check(doc, kb).flags if f["severity"] == "block"]
    if bad:
        probs.append("These legal references are not on the law or judgment cards; remove them or use only card law: " + ", ".join(bad[:6]))
    if doc_type == "legal_notice":
        for key, what in NOTICE_HEADINGS:
            if not has_heading(doc, key):
                probs.append(f"Add {what}.")
        if sender == "self" and re.search(r"\b(?:my|our) client\b", low):
            probs.append("The client sends this personally: write 'I' throughout, never 'my client'/'our client'.")
        if sender == "advocate":
            if not re.search(r"\bmy client\b", low):
                probs.append("An advocate sends this: refer to the client as 'my client' throughout.")
            if "enrol" not in low:
                probs.append("Add the advocate's enrolment number and Bar Council in the letterhead and signature.")
            if re.search(r"\bour client\b", low):
                probs.append("Use 'my client' consistently, not 'our client'.")
        if not re.search(r"\b\d{1,3}\s*(?:days?|hours?)\b", low):
            probs.append("State a clear time for compliance (in days) and its basis.")
        elif not re.search(r"reasonable|statutory|prescribed|required by|under section|as provided", low):
            probs.append("Explain the basis of the compliance period (statutory, or a reasonable period for a considered reply).")
        if not re.search(r"without prejudice", low):
            probs.append("The reservation of rights must say the notice is without prejudice to all other civil and criminal remedies.")
        annex = set(re.findall(r"annexure\s+([a-z]-?\d+)", low))
        if not annex:
            probs.append("Number the evidence as Annexure A-1, A-2 ... and refer to it in the facts.")
        else:
            orphan = [a.upper() for a in annex if low.count(f"annexure {a}") < 2]
            if orphan:
                probs.append("Annexures mentioned only once (must appear in the facts/schedule AND the enclosures): " + ", ".join(sorted(orphan)))
        dm = re.search(r"DEMANDS(.*?)(?:TIME FOR COMPLIANCE|MANNER OF REPLY|CONSEQUENCES|$)", doc, re.S)
        items = re.findall(r"(?m)^\s*\(?(?:[ivx]{1,4}|[a-h]|\d{1,2}(?:\.\d{1,2})?)[).]\s", dm.group(1)) if dm else []
        if len(items) < 2:
            probs.append("Number the demands (i), (ii), (iii) - each a specific action with a time limit and how compliance is shown.")
    return probs


def draft_checks(doc: str, doc_type: str, sender: str) -> list[tuple[str, bool]]:
    """Plain-language checklist shown to the user beside the draft."""
    low = doc.lower()
    if doc_type != "legal_notice":
        return [("Only verified law cited", "⚠️[unverified]" not in doc),
                ("No vague blanks", not VAGUE_BLANK_RE.search(doc))]
    h = lambda k: has_heading(doc, k)   # noqa: E731
    return [("Facts in date order, each with its channel and annexure", h("FACTS") and "annexure" in low),
            ("Exact sections, with ingredients mapped to the facts", h("LEGAL POSITION") and "⚠️[unverified]" not in doc),
            ("Written as allegations, not a verdict", not VERDICT_RE.search(doc)),
            ("Evidence schedule, with BSA s.63 certificate note", h("EVIDENCE") and ("63" in doc or "certificate" in low)),
            ("Specific, numbered demands with time limits", h("DEMANDS")),
            ("Deadline explained, and how to reply", h("TIME FOR COMPLIANCE") or h("MANNER OF REPLY")),
            ("Measured language, one consequences paragraph", not any(p in low for p in BANNED_PHRASES)),
            ("Rights reserved", "without prejudice" in low),
            ("One consistent sender: " + ("you personally" if sender == "self" else "your advocate"),
             not (sender == "self" and re.search(r"\b(?:my|our) client\b", low))),
            ("Service record for your office copy", h("SERVICE RECORD"))]
