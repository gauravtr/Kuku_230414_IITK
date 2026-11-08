"""Knowledge base: verified law cards + playbooks. Pure code, no model."""
from __future__ import annotations

import json
import pathlib
import re

KB_DIR = pathlib.Path(__file__).resolve().parent.parent / "kb"


def _match(keyword: str, text: str) -> bool:
    # ASCII keywords match on word boundaries ("land" must not match "landlord");
    # Indic-script keywords match as substrings (words inflect).
    if keyword.isascii():
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None
    return keyword in text


def _negated(text: str, a: int, b: int) -> bool:
    """'no managerial role', 'not a manager or supervisor', 'सरकारी नौकरी नहीं': the fact pattern is denied, not present."""
    pre = text[max(text.rfind("\n", 0, a) + 1, a - 40): a]
    post = text[b: b + 20].split("\n")[0]
    return bool(re.search(r"\b(?:not|no|never|non|neither|nor)\s*-?\s*(?:a|an|the|any)?\s*$", pre, re.I)
                or re.search(r"\b(?:not|no|never|neither)\s+(?:a|an|any)?\s*\w+\s+(?:or|nor)\s+$", pre, re.I)
                or re.match(r"[^।.]{0,12}(?:नहीं|नही\b|இல்லை)", post))


def _quote(text: str, a: int, b: int, pad: int = 38) -> str:
    """'...landlord kept the whole deposit of Rs 50,000...' - the matched words with a little context, cut at word edges."""
    ls, le = text.rfind("\n", 0, a) + 1, text.find("\n", b)   # stay inside the one line (message or fact) that matched
    le = len(text) if le < 0 else le
    s, e = max(ls, a - pad), min(le, b + pad)
    while s > ls and not text[s - 1].isspace():
        s -= 1
    while e < le and not text[e].isspace():
        e += 1
    q = re.sub(r"\s+", " ", text[s:e]).strip(" ,;:-\"'")
    return ("…" if s > ls else "") + q + ("…" if e < le else "")


class KB:
    def __init__(self, kb_dir: pathlib.Path = KB_DIR):
        laws = json.loads((kb_dir / "laws.json").read_text())
        pb = json.loads((kb_dir / "playbooks.json").read_text())
        self.acts: dict = laws["acts"]
        self.cards: dict = {c["id"]: c for c in laws["cards"]}
        self.issues: dict = pb["issues"]
        self.red_flags: list = pb["red_flags"]
        jf = kb_dir / "judgments.json"
        jd = json.loads(jf.read_text()) if jf.exists() else {"sides": {}, "judgments": []}
        self.sides: dict = jd["sides"]                       # issue -> {side_key: label}
        self.judgments: dict = {j["id"]: j for j in jd["judgments"]}

    # ---- routing (code decides which law the model may see) -----------------
    def classify(self, text: str) -> dict[str, int]:
        t = text.lower()
        scores = {k: sum(_match(w, t) for w in v["keywords"]) for k, v in self.issues.items() if k != "other"}
        # a tie goes to the more serious matter: a threat or violence outranks a money dispute that shares a word ("pay")
        rank = {k: i for i, k in enumerate(("threats", "domestic", "cheque", "salary", "consumer", "deposit"))}
        return {k: s for k, s in sorted(scores.items(), key=lambda x: (-x[1], rank.get(x[0], 99))) if s > 0}

    def detect_red_flags(self, text: str) -> list[dict]:
        t, out = text.lower(), []
        for rf in self.red_flags:
            tt = t
            for rx in rf.get("not_when", []):   # "get him arrested": aimed at the other side, not at the client
                tt = re.sub(rx, " ", tt)
            if any(_match(k, tt) for k in rf["keywords"]):
                out.append(rf)
        return out

    def cards_for(self, issues: list[str]) -> list[dict]:
        wanted = set(issues) | {"*"}
        return [c for c in self.cards.values() if wanted & set(c["issues"])]

    def judgments_for(self, issue: str | None) -> list[dict]:
        return [j for j in self.judgments.values() if j["issue"] == issue]

    def judgments_fitting(self, issue: str | None, client_words: str, case_text: str = "") -> list[tuple[dict, str]]:
        """Only the rulings whose fact pattern ('match') appears in THIS client's facts, each with the client's own
        words that make it fit (quoted to them as the reason). A ruling that doesn't fit is never suggested."""
        out = []
        for j in self.judgments_for(issue):
            rx = j.get("match")
            if not rx:
                continue
            hit = None
            for src, who in ((client_words, ""), (case_text, "case")):
                m = next((m for m in re.finditer(rx, src or "", re.I) if not _negated(src, m.start(), m.end())), None)
                if m:
                    hit = ("case:" if who else "") + _quote(src, m.start(), m.end())
                    break
            if hit:
                out.append((j, hit))
        return out


    # ---- whitelist used by the citation guard ------------------------------
    def allowed_sections(self) -> dict[str, set[str]]:
        allowed: dict[str, set[str]] = {k: set() for k in self.acts}
        for c in self.cards.values():
            allowed[c["act"]].update(c["sections"])
        return allowed
