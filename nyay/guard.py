"""Citation guard: the model's answer is checked by plain code before the user sees it.

Rule: the bot may only state a section / act that exists in kb/laws.json.
Anything else (a section number not on a card, an act we don't hold, a judgment that is
not on a verified judgment card, any old IPC/CrPC number) is marked inline as unverified
and explained in a footer. Judgments are allowed only from kb/judgments.json, because
invented judgments are the most common legal hallucination.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .kb import KB

SECTION_RE = re.compile(
    r"(?:(?<![A-Za-z])(?:sections?|sec\.|u/s\.?|s\.)\s*|धारा\s*|பிரிவு\s*)(\d{1,3}[A-Z]?)(?:\s*\([0-9a-z]+\))*",
    re.IGNORECASE)
CODE_NUM_RE = re.compile(r"\b(IPC|BNS|BNSS|CrPC|Cr\.P\.C\.?|NI Act)\s*(?:section\s*)?(\d{1,3}[A-Z]?)\b", re.IGNORECASE)
ARTICLE_RE = re.compile(r"\bArticle\s+(\d{1,3}[A-Z]?)", re.IGNORECASE)
CASE_RE = re.compile(
    r"\b[A-Z][\w.&']+(?:\s+(?:[A-Z][\w.&']+|of|and|&))*\s+(?:v\.|vs\.?|versus)\s+[A-Z][\w.&']+(?:\s+[A-Z][\w.&']+)*"
    r"|\bAIR\s*\d{4}\s*\w+\s*\d+|\(\d{4}\)\s*\d+\s*SCC\s*\d+|\b\d{4}\s+SCC\s+(?:OnLine\s+)?\w*\s*\d+")
ACT_NAME_RE = re.compile(r"\b((?:[A-Z][a-z]+\s+(?:(?:of|on|and|the)\s+)?){1,6}(?:Act|Code|Rules|Sanhita|Adhiniyam)),?\s*(\d{4})")
MARKER_RE = re.compile(r"\[([A-Z]{2,6}-[A-Z0-9]{1,12})\]")
# "I cannot confirm 'Sharma v. Kapoor' ...": an unverified case named only to refuse it is not a citation
REFUSAL_RE = re.compile(r"\b(?:cannot|can't|can not|could not|couldn't|unable to|won't|will not)\s+(?:confirm|verify|cite|find|use|rely)"
                        r"|\bnot (?:in|on) (?:my|our|the) (?:verified|checked)|\bnot verified\b|\bno such (?:judgment|case|ruling)"
                        r"|\b(?:does not|doesn't) exist|\bnot a real\b|\bfake\b|\bmade[- ]up\b|\binvented\b"
                        r"|पुष्टि नहीं|सत्यापित नहीं|उपलब्ध नहीं", re.I)


# "IPC 420 was replaced on 1 July 2024 by the BNS": the old law named as history, right after the citation
HISTORY_AFTER_RE = re.compile(r"^\W*(?:\([^)]{0,30}\)\W*)?(?:was|has been|have been|got|stands?|is now|were)\s+(?:\w+\s+){0,2}"
                              r"(?:replaced|repealed|substituted|superseded)|^[^.\n]{0,40}\b(?:replaced by|repealed|no longer (?:in force|applies|the law))", re.I)


def _sentence(text: str, a: int, b: int) -> str:
    s = max(text.rfind(". ", 0, a), text.rfind("\n", 0, a)) + 1
    ends = [x for x in (text.find(". ", b), text.find("\n", b)) if x >= 0]
    return text[s: min(ends) if ends else len(text)]


@dataclass
class GuardResult:
    text: str
    flags: list = field(default_factory=list)
    sources: list = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not any(f["severity"] == "block" for f in self.flags)


def _find_act(kb: KB, window: str, nearest_end: bool = False):
    """Return the act whose name/alias appears in the window (closest to the mention)."""
    w = window.lower()
    best, best_pos = None, None
    for key, act in kb.acts.items():
        for a in [x.lower() for x in act["aliases"] + [act["name"]]]:
            if a.isascii():
                hits = [m.start() for m in re.finditer(rf"(?<![a-z]){re.escape(a)}(?![a-z])", w)]
            else:
                hits = [m.start() for m in re.finditer(re.escape(a), w)]
            if not hits:
                continue
            i = max(hits) if nearest_end else min(hits)
            if best_pos is None or (i > best_pos if nearest_end else i < best_pos):
                best, best_pos = key, i
    if best is None:
        return None, 10 ** 9
    return best, (len(w) - best_pos if nearest_end else best_pos)


MULTI_MARKER_RE = re.compile(r"\[([A-Z]{2,6}-[A-Z0-9]{1,12}(?:\s*[,;]\s*(?:[A-Z]{2,6}-[A-Z0-9]{1,12}|[A-Z][A-Z0-9]{2,11}))+)\]")
# "Police vs Court", "Notice vs Case": headings that look like "X v. Y" but name no party
GENERIC_SIDES = {"police", "court", "courts", "civil", "criminal", "consumer", "commission", "notice", "case", "fir", "complaint",
                 "landlord", "tenant", "employer", "employee", "option", "route", "path", "mediation", "settlement", "suit",
                 "online", "offline", "family", "state", "law", "rights", "money", "time", "cost", "costs", "risk", "you", "them"}


def _party(name: str) -> str:
    first = re.split(r"\s+(?:v\.|vs\.?|versus)\s+", name, maxsplit=1, flags=re.I)[0].lower()
    first = re.sub(r"\b(m/s\.?|pvt|private|ltd|limited|\(p\)|\(i\)|and others|& ors|ors)\b", " ", first)
    return re.sub(r"[^a-z ]", " ", first).split() and " ".join(re.sub(r"[^a-z ]", " ", first).split())


def _known_judgment(mention: str, kb: KB) -> bool:
    """True if a case name / citation the model wrote is one of the verified judgment cards."""
    cards = getattr(kb, "judgments", {}).values()
    m = mention.lower()
    if any(c["citation"].lower().find(m.strip(" ;,")) >= 0 for c in cards if re.search(r"\d", m)):
        return True
    mp = _party(mention)
    if not mp:
        return False
    for c in cards:
        cp = _party(c["name"])
        if mp == cp or (len(mp) >= 8 and (mp in cp or cp in mp)):
            return True
    return False


def fix_act_years(text: str, kb: KB) -> str:
    """'Bharatiya Nagarik Suraksha Sanhita, 2024' -> '..., 2023'. A known act with a year off by one or two is a slip,
    corrected in code. A year further off (e.g. 'Consumer Protection Act, 1986') may name the older law, so it is left."""
    years = {}
    for a in kb.acts.values():
        mm = re.match(r"(.+?),\s*(\d{4})", a["name"])
        if mm:
            years[mm.group(1).strip().lower()] = mm.group(2)

    def repl(m):
        name = m.group(1).strip().lower()   # may carry a leading capitalised word: "Under Bharatiya ... Sanhita"
        right = next((y for k, y in years.items() if name == k or name.endswith(" " + k)), None)
        if right and right != m.group(2) and abs(int(right) - int(m.group(2))) <= 2:
            return m.group(0)[: m.start(2) - m.start(0)] + right
        return m.group(0)
    return ACT_NAME_RE.sub(repl, text)


def fix_case_citations(text: str, kb: KB) -> str:
    """'Balaji Traders v. State of U.P. (2025), 2005 INSC 806' -> '2025 INSC 806': a verified judgment named with its own
    INSC number but a mistyped year gets the card's exact citation, in code."""
    for j in getattr(kb, "judgments", {}).values():
        cm = re.match(r"(\d{4}) INSC (\d+)", j["citation"])
        if not cm:
            continue
        first = j["name"].split(" v.")[0].replace("M/s ", "").strip()
        for nm in list(re.finditer(re.escape(first), text)):
            window = text[nm.end(): nm.end() + 160]
            bad = re.search(rf"\(?(\d{{4}})\)?\s*INSC\s+{cm.group(2)}\b", window)
            if bad and bad.group(1) != cm.group(1):
                s0 = nm.end() + bad.start()
                text = text[:s0] + f"{cm.group(1)} INSC {cm.group(2)}" + text[nm.end() + bad.end():]
    return text


def check(text: str, kb: KB) -> GuardResult:
    text = fix_case_citations(fix_act_years(text, kb), kb)
    # "[COW-45, GEN-LIMIT]" -> "[COW-45][GEN-LIMIT]" so each card becomes its own numbered source
    def _one(x):   # "[BNSS-MAINT, RAJNESH]": a bare short name of a judgment card means that card
        x = x.strip()
        return x if "-" in x else ("JUD-" + x if "JUD-" + x in getattr(kb, "judgments", {}) else "")
    text = MULTI_MARKER_RE.sub(lambda m: "".join(f"[{y}]" for y in map(_one, re.split(r"[,;]", m.group(1))) if y), text)
    flags, marks = [], []  # marks: (end_index, label)
    allowed = kb.allowed_sections()

    cited_ids = [m.group(1) for m in MARKER_RE.finditer(text)]
    cited_acts = {kb.cards[i]["act"] for i in cited_ids if i in kb.cards}
    low = text.lower()   # acts named anywhere in this text, e.g. a notice that names the BNS in its legal-position section
    named_acts = {k for k, a in kb.acts.items() if not a.get("outdated") and any(
        (re.search(rf"(?<![a-z]){re.escape(x.lower())}(?![a-z])", low) if x.isascii() else x in text)
        for x in a["aliases"] + [a["name"]] if len(x) > 2)}

    def add(span, mention, severity, why):
        flags.append({"mention": mention, "severity": severity, "why": why})
        if severity == "block":
            marks.append((span[1], " ⚠️[unverified]"))

    # 1) "Section 17 of the Code on Wages", "धारा 45", "s.69"
    for m in SECTION_RE.finditer(text):
        sec = m.group(1).upper()
        after = re.split(r"\.(?=\s)|\n", text[m.end(): m.end() + 90], maxsplit=1)[0]   # this sentence only
        before = text[max(0, m.start() - 50): m.start()]
        (a1, d1), (a2, d2) = _find_act(kb, after), _find_act(kb, before, nearest_end=True)
        act = a1 if d1 <= d2 else a2
        if act is None:   # "4.3 IT Act - Section 66E ... (a) ... (Section 67)": the act was named a line or two above
            act, _ = _find_act(kb, text[max(0, m.start() - 400): m.start()], nearest_end=True)
            if act is not None and sec not in allowed[act] and any(sec in allowed[a] for a in cited_acts | named_acts):
                continue   # the nearest act above lacks it, but an act named in this text has it (BNS 308 after an IT Act para)
        if act is None:   # no act nearby: fine if a verified act named (or card-cited) elsewhere in this text has the section
            ok = any(sec in allowed[a] for a in cited_acts | named_acts)
            if not ok:
                add(m.span(), m.group(0), "block", "section number with no act we can verify")
            continue
        if kb.acts[act].get("outdated"):
            if re.search(r"^[^.\n]{0,25}\(?\s*(?:now|since replaced|replaced by|corresponding to)\b", text[m.end(): m.end() + 60], re.I) \
                    or HISTORY_AFTER_RE.search(text[m.end(): m.end() + 80]):
                continue   # "Section 387 IPC (now BNS s.308(4))": the old law named as history, with today's section
            add(m.span(), m.group(0), "block", f"{kb.acts[act]['name']}: old law, use BNS/BNSS")
        elif sec not in allowed[act]:
            add(m.span(), m.group(0), "block", f"section {sec} of {kb.acts[act]['name']} is not on a verified card")

    # 2) "IPC 420", "BNS 318", "NI Act 138"
    for m in CODE_NUM_RE.finditer(text):
        code, sec = m.group(1).lower().replace(".", ""), m.group(2).upper()
        act = {"ipc": "IPC", "bns": "BNS", "bnss": "BNSS", "crpc": "CRPC", "ni act": "NI"}.get(code)
        if act and kb.acts.get(act, {}).get("outdated") and re.search(
                r"(earlier|old|formerly|former|previously|replaced|was|पहले|पुरान|purana|pehle)\W*(\w+\W+){0,3}$",
                text[max(0, m.start() - 40): m.start()], re.I):
            continue   # "earlier IPC 498A" names the old law as history, not as the law to apply
        if act and kb.acts.get(act, {}).get("outdated") and HISTORY_AFTER_RE.search(text[m.end(): m.end() + 80]):
            continue   # "IPC 420 was replaced on 1 July 2024 by the BNS"
        if act is None or kb.acts.get(act, {}).get("outdated") or sec not in allowed.get(act, set()):
            add(m.span(), m.group(0), "block", "criminal/statute section not on a verified card")

    # 3) Constitution articles, case law and unknown acts
    for m in ARTICLE_RE.finditer(text):
        add(m.span(), m.group(0), "block", "constitutional article not on a verified card")
    for m in CASE_RE.finditer(text):
        words = re.findall(r"[A-Za-z]+", m.group(0).lower())
        if words and all(w in GENERIC_SIDES or w in ("v", "vs", "versus", "the", "and", "of") for w in words):
            continue   # "Police vs Court": a comparison heading, not a case name
        if _known_judgment(m.group(0), kb):
            continue   # a verified Supreme Court judgment card
        if REFUSAL_RE.search(_sentence(text, m.start(), m.end())):
            flags.append({"mention": m.group(0), "severity": "note", "why": "unverified case named only to say it can't be relied on"})
            continue
        add(m.span(), m.group(0), "block", "case-law citation not on a verified judgment card")
    known = [a["name"].lower() for a in kb.acts.values()] + [al for a in kb.acts.values() for al in a["aliases"]]
    for m in ACT_NAME_RE.finditer(text):
        name = m.group(1).lower()
        if not any(k in name or name in k for k in known if len(k) > 3):
            add(m.span(), m.group(0), "block", "act not in the verified knowledge base")

    # 4) [CARD-ID] markers -> numbered sources; unknown IDs are dropped
    order: list[str] = []
    judgments = getattr(kb, "judgments", {})
    def to_num(m):
        cid = m.group(1)
        if cid not in kb.cards and cid not in judgments:
            flags.append({"mention": m.group(0), "severity": "block", "why": "model cited a card ID that does not exist"})
            return ""
        if cid not in order:
            order.append(cid)
        return f"[{order.index(cid) + 1}]"

    # apply inline marks (from the end so spans stay valid), then markers
    seen = set()
    for end, label in sorted(marks, reverse=True):
        if end in seen:
            continue
        seen.add(end)
        text = text[:end] + label + text[end:]
    text = MARKER_RE.sub(to_num, text)
    def src(i, cid):
        if cid in kb.cards:
            return {"n": i + 1, "id": cid, "title": kb.cards[cid]["title"], "url": kb.cards[cid]["source"],
                    "verified": kb.cards[cid]["verified"]}
        j = judgments[cid]   # a verified Supreme Court judgment card
        return {"n": i + 1, "id": cid, "title": f"Supreme Court: {j['name']}, {j['citation']}", "url": j["url"],
                "verified": True}
    sources = [src(i, cid) for i, cid in enumerate(order)]
    return GuardResult(text=text, flags=_dedupe(flags), sources=sources)


def _dedupe(flags):
    out, seen = [], set()
    for f in flags:
        k = (f["mention"], f["why"])
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def footer(result: GuardResult, lang: str = "en") -> str:
    lines = []
    if result.sources:
        lines.append("**Sources (checked):** " + "; ".join(f"[{s['n']}] {s['title']} — {s['url']}" for s in result.sources))
    bad = [f for f in result.flags if f["severity"] == "block"]
    if bad:
        lines.append("⚠️ **Please double-check:** I mentioned " + ", ".join(f"“{f['mention']}”" for f in bad[:5]) +
                     ", which I could not verify against my checked law list. Don't rely on it without asking a lawyer "
                     "or legal aid (15100).")
    return "\n\n".join(lines)
