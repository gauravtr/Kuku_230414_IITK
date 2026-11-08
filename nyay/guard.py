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


MULTI_MARKER_RE = re.compile(r"\[([A-Z]{2,6}-[A-Z0-9]{1,12}(?:\s*[,;]\s*[A-Z]{2,6}-[A-Z0-9]{1,12})+)\]")


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


def check(text: str, kb: KB) -> GuardResult:
    # "[COW-45, GEN-LIMIT]" -> "[COW-45][GEN-LIMIT]" so each card becomes its own numbered source
    text = MULTI_MARKER_RE.sub(lambda m: "".join(f"[{x.strip()}]" for x in re.split(r"[,;]", m.group(1))), text)
    flags, marks = [], []  # marks: (end_index, label)
    allowed = kb.allowed_sections()

    cited_ids = [m.group(1) for m in MARKER_RE.finditer(text)]
    cited_acts = {kb.cards[i]["act"] for i in cited_ids if i in kb.cards}

    def add(span, mention, severity, why):
        flags.append({"mention": mention, "severity": severity, "why": why})
        if severity == "block":
            marks.append((span[1], " ⚠️[unverified]"))

    # 1) "Section 17 of the Code on Wages", "धारा 45", "s.69"
    for m in SECTION_RE.finditer(text):
        sec = m.group(1).upper()
        after = text[m.end(): m.end() + 90]
        before = text[max(0, m.start() - 50): m.start()]
        (a1, d1), (a2, d2) = _find_act(kb, after), _find_act(kb, before, nearest_end=True)
        act = a1 if d1 <= d2 else a2
        if act is None:
            ok = any(sec in allowed[a] for a in cited_acts)
            if not ok:
                add(m.span(), m.group(0), "block", "section number with no act we can verify")
            continue
        if kb.acts[act].get("outdated"):
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
        if act is None or kb.acts.get(act, {}).get("outdated") or sec not in allowed.get(act, set()):
            add(m.span(), m.group(0), "block", "criminal/statute section not on a verified card")

    # 3) Constitution articles, case law and unknown acts
    for m in ARTICLE_RE.finditer(text):
        add(m.span(), m.group(0), "block", "constitutional article not on a verified card")
    for m in CASE_RE.finditer(text):
        if _known_judgment(m.group(0), kb):
            continue   # a verified Supreme Court judgment card
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
