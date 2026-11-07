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


class KB:
    def __init__(self, kb_dir: pathlib.Path = KB_DIR):
        laws = json.loads((kb_dir / "laws.json").read_text())
        pb = json.loads((kb_dir / "playbooks.json").read_text())
        self.acts: dict = laws["acts"]
        self.cards: dict = {c["id"]: c for c in laws["cards"]}
        self.issues: dict = pb["issues"]
        self.red_flags: list = pb["red_flags"]

    # ---- routing (code decides which law the model may see) -----------------
    def classify(self, text: str) -> dict[str, int]:
        t = text.lower()
        scores = {k: sum(_match(w, t) for w in v["keywords"]) for k, v in self.issues.items() if k != "other"}
        return {k: s for k, s in sorted(scores.items(), key=lambda x: -x[1]) if s > 0}

    def detect_red_flags(self, text: str) -> list[dict]:
        t = text.lower()
        return [rf for rf in self.red_flags if any(_match(k, t) for k in rf["keywords"])]

    def cards_for(self, issues: list[str]) -> list[dict]:
        wanted = set(issues) | {"*"}
        return [c for c in self.cards.values() if wanted & set(c["issues"])]

    # ---- whitelist used by the citation guard ------------------------------
    def allowed_sections(self) -> dict[str, set[str]]:
        allowed: dict[str, set[str]] = {k: set() for k in self.acts}
        for c in self.cards.values():
            allowed[c["act"]].update(c["sections"])
        return allowed
