"""One-page case brief a person can hand to a human lawyer or legal-aid clinic.

Built by code from the case file and the AI's latest opinion (no model call), so it never
adds facts or law that are not already in the case. Sources are the verified law cards cited.
"""
from __future__ import annotations

import io

from .guard import MARKER_RE

STRENGTH_LABEL = {"strong": "Strong", "moderate": "Moderate", "weak": "Weak", "unclear": "Unclear - more facts needed"}
REASON_LABEL = {
    "safety": "Possible risk to safety or liberty (police, violence, self-harm, fraud or family matter).",
    "out_of_scope": "The problem is outside the areas the AI lawyer has verified law for.",
    "large_amount": "A large amount is at stake (over about Rs 5 lakh).",
    "ambiguous": "Key facts are still unclear, and they change the legal answer.",
}


def _c(x) -> str:
    return MARKER_RE.sub("", str(x or "")).replace("  ", " ").strip()


def sections(state: dict, sources: list[dict] | None = None) -> list[tuple[str, list[str]]]:
    case = state.get("case") or {}
    a = state.get("assessment") or {}
    esc = state.get("escalation") or {}
    people = case.get("people") or {}
    out = [("Matter", [_c(case.get("summary")) or "-",
                       f"Client: {_c(people.get('user')) or '-'}   |   Other side: {_c(people.get('other_side')) or '-'}",
                       f"Place: {_c(case.get('place')) or '-'}   |   Amount at stake: {_c(case.get('amount_at_stake')) or '-'}",
                       f"What the client wants: {_c(case.get('what_user_wants')) or '-'}"])]
    if case.get("timeline"):
        out.append(("Timeline", [f"{_c(t.get('date'))}: {_c(t.get('event'))}" for t in case["timeline"] if isinstance(t, dict)]))
    out.append(("Proof the client has", [_c(p) for p in case.get("proof_have", [])] or ["None listed yet"]))
    out.append(("Proof still to collect", [_c(p) for p in case.get("proof_missing", [])] or ["None listed"]))
    if case.get("deadlines"):
        out.append(("Deadlines", [_c(d) for d in case["deadlines"]]))
    if a:
        out.append(("AI lawyer's preliminary view", [f"Strength of position: {STRENGTH_LABEL.get(a.get('strength'), '-')}"]
                    + ([f"Why: {_c(a.get('why'))}"] if a.get("why") else [])))
    if state.get("plan"):
        out.append(("Steps suggested so far", [f"{_c(s['step'])}" + (f" ({_c(s['by_when'])})" if s.get("by_when") else "")
                                               for s in state["plan"]]))
    qs = [REASON_LABEL.get(r, _c(r)) for r in esc.get("reasons", [])] + [_c(q) for q in state.get("open_questions", [])]
    if qs:
        out.append(("Why a lawyer should look at this / open questions", qs))
    if sources:
        out.append(("Law relied on (verified sources)", [f"{s['title']} - {s['url']}" for s in sources]))
    out.append(("Note", ["Prepared by Nyay Saathi, an AI lawyer (not an enrolled advocate), from what the client said. "
                         "Facts are unverified. Free legal aid: NALSA helpline 15100."]))
    return out


def markdown(state: dict, sources=None) -> str:
    lines = ["# Case brief for a lawyer", ""]
    for head, items in sections(state, sources):
        lines += [f"## {head}"] + [f"- {i}" for i in items] + [""]
    return "\n".join(lines)


def docx_bytes(state: dict, sources=None) -> bytes | None:
    try:
        from docx import Document
    except ImportError:
        return None
    doc = Document()
    doc.add_heading("Case brief for a lawyer", level=1)
    for head, items in sections(state, sources):
        doc.add_heading(head, level=2)
        for i in items:
            doc.add_paragraph(i, style="List Bullet")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
