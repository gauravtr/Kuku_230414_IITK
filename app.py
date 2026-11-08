"""Nyay Saathi - your AI lawyer. Streamlit UI.   Run:  streamlit run app.py

Product notes (who this is for and why the screen looks like this):
- The user is stressed, often on a phone, often not comfortable in English, and has never met a lawyer.
  So: one obvious place to type, their language, plain words, and always a clear "what do I do next".
- A lawyer's first consultation gives three things: where you stand, what to do, and the paperwork.
  The flow mirrors that: Consultation -> Case file (opinion + plan) -> Documents -> Rehearse.
- Trust is earned by showing the law relied on (verified sources) and by being blunt about when a
  human lawyer is needed. That escalation is decided by code, not left to the model.
- Visual language: ink, paper and brass; serif for what a lawyer hands you (opinions, documents),
  sans for what you operate. The design system lives in nyay/style.css.
"""
import hashlib
import html
import io
import json
import os
import re
from pathlib import Path

import streamlit as st

# Streamlit Cloud secrets -> env (so nyay/llm.py stays framework-free)
try:
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ.setdefault(k, v)
except Exception:
    pass

from nyay import brief  # noqa: E402
from nyay.engine import NyaySaathi, new_state  # noqa: E402
from nyay.guard import MARKER_RE  # noqa: E402
from nyay.llm import LLM, _safe  # noqa: E402


def favicon():
    """The brand mark drawn in code (ink tile, brass scales), so no binary asset is needed."""
    try:
        from PIL import Image, ImageDraw
        s, g = 128, "#D9B26A"
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=30, fill="#0E1A2B")
        d.line([(64, 30), (64, 98)], fill=g, width=7)
        d.line([(34, 42), (94, 42)], fill=g, width=7)
        d.line([(48, 101), (80, 101)], fill=g, width=7)
        for cx in (34, 94):
            d.line([(cx, 42), (cx - 13, 70)], fill=g, width=4)
            d.line([(cx, 42), (cx + 13, 70)], fill=g, width=4)
            d.pieslice([cx - 17, 56, cx + 17, 86], 0, 180, fill=g)
        d.ellipse([57, 23, 71, 37], fill=g)
        return im
    except Exception:
        return "⚖️"


st.set_page_config(page_title="Nyay Saathi — AI lawyer for India", page_icon=favicon(), layout="wide",
                   initial_sidebar_state="collapsed",
                   menu_items={"About": "Nyay Saathi: an AI lawyer for everyday legal problems in India, in your language. "
                                        "It tells you plainly when you need a human lawyer. Free legal aid: NALSA 15100."})

CSS = Path(__file__).with_name("nyay").joinpath("style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ------------------------------------------------------------------ content & vocabulary
MARK = ('<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#0E1A2B"/>'
        '<g stroke="#D9B26A" stroke-width="1.6" stroke-linecap="round" fill="none"><path d="M16 7.5v16.5M8.5 10.5h15M12.5 25h7"/>'
        '<path d="M8.5 10.5l-3 6.6M8.5 10.5l3 6.6M23.5 10.5l-3 6.6M23.5 10.5l3 6.6"/></g><g fill="#D9B26A">'
        '<path d="M5 17h7a3.5 2.7 0 0 1-7 0z"/><path d="M20 17h7a3.5 2.7 0 0 1-7 0z"/><circle cx="16" cy="7.3" r="1.6"/></g></svg>')

LANGS = {"Auto-detect": "auto", "English": "English", "हिंदी · Hindi": "Hindi in Devanagari script",
         "Hinglish": "Hinglish (Hindi in Latin script)", "தமிழ் · Tamil": "Tamil", "বাংলা · Bengali": "Bengali",
         "मराठी · Marathi": "Marathi", "తెలుగు · Telugu": "Telugu", "ಕನ್ನಡ · Kannada": "Kannada",
         "ગુજરાતી · Gujarati": "Gujarati", "മലയാളം · Malayalam": "Malayalam"}
ISSUES = {"deposit": "Security deposit", "consumer": "Consumer · refund", "salary": "Unpaid salary",
          "cheque": "Cheque bounce", "domestic": "Domestic violence", "other": "General matter"}
OPPONENTS = {"deposit": ("the landlord", "Landlord"), "consumer": ("the company's customer-care manager", "Customer care"),
             "salary": ("the employer's HR manager", "HR manager"), "cheque": ("the person who gave the cheque", "Cheque issuer"),
             "domestic": ("the duty officer at the police station, who is reluctant to register your FIR", "Police officer"),
             "other": ("the other side", "Other side")}
EXAMPLES = [
    ("home", "Deposit not returned", "Landlord holding back your security deposit", "English",
     "I vacated my rented flat in Pune on 30 September. The landlord is not returning my ₹50,000 "
     "deposit and says he will cut money for painting. What can I do?"),
    ("inventory_2", "Refund or faulty product", "Defective item, rejected return, or no refund", "Hinglish",
     "Maine 10 din pehle online ₹15,999 ka phone liya, screen kharab nikli. Return reject kar diya. "
     "Paisa wapas kaise milega?"),
    ("payments", "Salary not paid", "Employer delaying or withholding your wages", "हिंदी",
     "मेरी कंपनी ने पिछले 2 महीने की सैलरी (₹30,000 प्रति माह) नहीं दी है और मैंने इस्तीफा दे दिया है। क्या करूँ?"),
    ("receipt_long", "Cheque bounce notice", "You received a notice, or need to send one", "English",
     "I received a legal notice saying my ₹80,000 cheque bounced and I must pay in 15 days. "
     "What does this mean for me?"),
]
VIEWS = {"consult": ":material/forum: Consult", "case": ":material/folder_open: Case file",
         "docs": ":material/description: Documents", "rehearse": ":material/record_voice_over: Rehearse"}
DOCS = {"legal_notice": ("Legal notice", "A formal written demand to the other side. Usually the first step."),
        "consumer_complaint": ("Consumer complaint", "For the District Consumer Commission, if a notice didn't work."),
        "dv_application": ("DV Act application", "Asks the Magistrate for urgent protection, the right to stay in the home, "
                           "maintenance, medical costs and compensation."),
        "police_complaint": ("Police complaint (FIR)", "A written complaint to the police station. If they refuse, the same "
                             "copy goes to the Superintendent of Police.")}


def docs_for(issue) -> list[str]:
    return ["dv_application", "police_complaint"] if issue == "domestic" else ["legal_notice", "consumer_complaint"]
STRENGTH = {"strong": ("Strong case", 3), "moderate": ("Moderate case", 2), "weak": ("Weak case", 1),
            "unclear": ("Needs a few more facts", 0)}
REASONS = {"safety": "This may involve your safety or liberty.",
           "liberty": "An arrest, a summons or a case against you: your liberty may be at stake.",
           "court_matter": "This kind of matter is usually settled in court, where you'll need a lawyer to file.",
           "out_of_scope": "This is outside the areas where I have verified Indian law.",
           "large_amount": "A large amount is at stake (over about ₹5 lakh).",
           "ambiguous": "Key facts are still unclear, and they change the legal answer."}
HELPLINES = [("Free legal aid (NALSA)", "15100"), ("Consumer helpline", "1915"), ("Cyber fraud", "1930"),
             ("Women helpline", "181"), ("Emergency", "112")]
UNKNOWN = {"", "unknown", "-", "none", "n/a", "na", "not known", "not specified", "null"}


def ic(name: str, cls: str = "") -> str:
    return f'<span class="ms {cls}" aria-hidden="true">{name}</span>'


def esc(x) -> str:
    """Model or user text -> safe inline HTML (keeps **bold**, drops law-card tags, no blank lines)."""
    t = html.escape(clean(x))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


def clean(x) -> str:
    """Display text: drop internal law-card tags like [GEN-LIMIT]."""
    return re.sub(r"\s+([.,;:!?])", r"\1", MARKER_RE.sub("", str(x or ""))).replace("  ", " ").strip()


def known(x) -> str:
    v = clean(x)
    return "" if v.lower().strip(" .") in UNKNOWN else v


def html_block(s: str):
    st.markdown(s, unsafe_allow_html=True)


# ------------------------------------------------------------------ state
ss = st.session_state
if "state" not in ss:
    ss.state, ss.chat, ss.practise, ss.sources, ss.done_steps = new_state(), [], [], {}, set()
    ss.blank_values, ss.doc_edits = {}, {}
ss.setdefault("view", "consult")
ss.setdefault("last_view", "consult")
ss.setdefault("lang", "Auto-detect")
state = ss.state
state["language"] = LANGS.get(ss.lang, "auto")


def go(view: str, doc_kind: str | None = None):
    ss.view = ss.last_view = view
    if doc_kind in DOCS:
        ss.doc_kind = doc_kind


def keep_view():   # segmented control: clicking the active option would deselect it; keep it selected
    if ss.view is None:
        ss.view = ss.last_view
    ss.last_view = ss.view


def queue(text: str):
    ss.queued = text
    go("consult")


def toggle_step(step: str, key: str):   # runs before the page redraws, so counters update instantly
    (ss.done_steps.add if ss.get(key) else ss.done_steps.discard)(step)


def friendly_error(e: Exception) -> str:
    print("Nyay Saathi model error:", type(e).__name__, _safe(e), flush=True)   # shows in the app logs
    return ("I couldn't reach the AI service just now. Please send your message again in a minute. "
            "If it's urgent, call the free legal aid helpline **15100**.\n\n"
            f"`{type(e).__name__}: {_safe(e)[:140]}`")


def new_case():
    for k in ("state", "chat", "practise", "sources", "done_steps", "draft", "queued", "doc_kind", "blank_values",
              "doc_edits"):
        ss.pop(k, None)
    ss.view = ss.last_view = "consult"


available = [p for p, k in [("gemini", "GEMINI_API_KEY"), ("groq", "GROQ_API_KEY"), ("openai", "OPENAI_API_KEY"),
                            ("openrouter", "OPENROUTER_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")] if os.getenv(k)]
default_p = os.getenv("NYAY_PROVIDER", available[0] if available else "gemini")
provider_options = sorted(set(available + [default_p]))
has_case = bool(ss.chat or ss.get("queued"))

# ------------------------------------------------------------------ top bar
with st.container(key="topbar"):
    cols = st.columns([6, 1, 1, 1] if has_case else [6, 1, 1], vertical_alignment="center")
    cols[0].markdown(f'<div class="brand">{MARK}<div><div class="name">Nyay Saathi</div>'
                     f'<div class="sub"><b>your AI lawyer</b></div></div>'
                     f'<span class="chip-verified">{ic("verified", "fill")}Verified Indian law</span></div>',
                     unsafe_allow_html=True)
    short = ss.lang.split(" · ")[0] if ss.lang != "Auto-detect" else "Auto"
    with cols[1].popover(f":material/translate: {short}", help="Reply language"):
        st.radio("I'll reply in", list(LANGS), key="lang",
                 captions=None, help="Auto-detect replies in whatever language you write in.")
    if has_case:
        cols[2].button(":material/add: New", on_click=new_case, help="Start a new consultation")
    with cols[-1].popover(":material/more_horiz:", help="Help, accuracy and settings"):
        st.markdown(f'<div class="card-t">{ic("support_agent")}Free help, any time</div>', unsafe_allow_html=True)
        html_block('<div class="helplist">' + "".join(f'<a href="tel:{n}">{l}<b>{n}</b></a>' for l, n in HELPLINES) + "</div>")
        st.markdown(f'<div class="card-t" style="margin-top:14px">{ic("verified_user")}How Nyay stays accurate</div>',
                    unsafe_allow_html=True)
        st.markdown("- States law only from **verified law cards**, each linked to its source.\n"
                    "- Code checks every answer; any section or case not on a card is flagged.\n"
                    "- Code, not just the AI, decides when you need a human lawyer.\n"
                    "- Law verified as of **7 Nov 2026**.")
        st.markdown(f'<div class="card-t" style="margin-top:14px">{ic("tune")}AI model</div>', unsafe_allow_html=True)
        provider = st.selectbox("Provider", provider_options, index=provider_options.index(default_p))
        model = st.text_input("Model (blank = default)", os.getenv("NYAY_MODEL", ""))
        st.caption("Works with Gemini, Groq, OpenAI, Anthropic or Ollama. The law checks stay the same.")

if "llm" not in ss or ss.get("llm_cfg") != (provider, model):
    ss.llm = LLM(provider, model or None)       # kept per session: remembers a working fallback model
    ss.llm_cfg = (provider, model)
bot = NyaySaathi(ss.llm)

if not available:
    st.error("The AI service isn't configured yet. The owner needs to add a free GEMINI_API_KEY in Settings → Secrets.")


# ------------------------------------------------------------------ shared pieces
def verdict_html(a: dict, show_unclear: bool = False) -> str:
    s = (a or {}).get("strength")
    if s not in STRENGTH or (s == "unclear" and not show_unclear):
        return ""
    label, n = STRENGTH[s]
    meter = "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(3))
    why = f'<p>{esc(a.get("why"))}</p>' if clean(a.get("why")) else ""
    return (f'<div class="verdict v-{s}"><div class="top"><span class="lbl">Case strength</span>'
            f'<span class="meter">{meter}</span><span class="val">{label}</span></div>{why}</div>')


def badge_html(a: dict) -> str:
    s = (a or {}).get("strength")
    if s not in STRENGTH:
        return ""
    label, n = STRENGTH[s]
    meter = "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(3))
    return f'<span class="badge b-{s}"><span class="meter">{meter}</span>{label}</span>'


SAFETY_LINES = {"violence": ("Your safety comes first", "If you are in danger now, call 112. Women Helpline 181 (free, 24x7) "
                             "connects you to the One Stop Centre: medical help, police help, a lawyer and shelter.",
                             [("181", "181 Women Helpline"), ("112", "112 Emergency")]),
                "self_harm": ("You don't have to go through this alone", "Please talk to someone now, it's free and confidential.",
                              [("14416", "14416 Tele-MANAS"), ("112", "112 Emergency")])}


def safety_html(ids: list) -> str:
    out = ""
    for i in ids or []:
        if i not in SAFETY_LINES:
            continue
        title, text, calls = SAFETY_LINES[i]
        cta = " · ".join(f'<a href="tel:{n}">{html.escape(lbl)}</a>' for n, lbl in calls)
        out += (f'<div class="esc esc-urgent"><div class="ic">{ic("health_and_safety", "fill")}</div><div>'
                f'<b>{title}</b><p>{html.escape(text)}</p><div class="cta">{cta}</div></div></div>')
    return out


def esc_html(e: dict) -> str:
    level = (e or {}).get("level")
    if level not in ("consult", "urgent"):
        return safety_html((e or {}).get("safety"))
    reasons = " ".join(html.escape(REASONS.get(r, clean(r))) for r in e.get("reasons", []))
    if level == "urgent":
        return safety_html(e.get("safety")) + (f'<div class="esc esc-urgent"><div class="ic">{ic("emergency_home", "fill")}</div><div>'
                f'<b>Speak to a human lawyer now</b><p>{reasons}</p><div class="cta">Free legal aid: '
                f'<a href="tel:15100">call 15100</a> (NALSA) · Emergency: <a href="tel:112">112</a></div></div></div>')
    return safety_html(e.get("safety")) + (f'<div class="esc esc-consult"><div class="ic">{ic("gavel")}</div><div>'
            f'<b>I recommend a human lawyer for this</b><p>{reasons}</p><div class="cta">Free legal aid: '
            f'<a href="tel:15100">call 15100</a> (NALSA) · Your <b style="display:inline;font-size:inherit">case brief</b> '
            f'for them is ready in the Case file.</div></div></div>')


def question_form(i: int, qs: list):
    """The AI lawyer's questions as a short form under its reply: a dropdown where it gave answer choices,
    a text box otherwise. Answers go back as the client's next message."""
    with st.container(key=f"qform_{i}"):
        html_block(f'<div class="card-t">{ic("edit_note")}Answer here so I can advise you precisely</div>')
        with st.form(key=f"qf_{i}", border=False, clear_on_submit=True):
            answers = []
            for j, x in enumerate(qs):
                label = f"{j + 1}. {clean(x['q'])}"
                if x.get("options"):
                    a = st.selectbox(label, x["options"], index=None, placeholder="Choose an answer", key=f"qa_{i}_{j}")
                else:
                    a = st.text_input(label, key=f"qa_{i}_{j}", placeholder="Type your answer")
                answers.append((clean(x["q"]), a))
            more = st.text_area("Anything else I should know? (optional)", key=f"qa_{i}_more", height=70)
            sent = st.form_submit_button(":material/send: Send answers", type="primary")
    if sent:
        lines = [f"{j}. {q} — {str(a).strip()}" for j, (q, a) in enumerate(answers, 1) if a and str(a).strip()]
        if more and more.strip():
            lines.append(more.strip())
        if lines:
            ss.queued = "\n".join(lines)
            st.rerun()
        st.warning("Answer at least one question, or type in the box at the bottom.")


def judgments_html(j: dict) -> str:
    """Supreme Court rulings for and against the client, rendered from verified judgment cards only."""
    if not j or not (j.get("for") or j.get("against")):
        return ""

    def item(c, cls):
        year = html.escape(str(c.get("date", ""))[:4])
        why = f'<p class="why"><b>What it means for you:</b> {esc(c["why"])}</p>' if clean(c.get("why")) else ""
        note = f'<p class="cau">{ic("info")}{html.escape(c["caution"])}</p>' if c.get("caution") else ""
        how = ' · <span class="tag">same principle</span>' if c.get("applies") == "principle" else ""
        return (f'<li class="{cls}"><div class="jn">{html.escape(c["name"])}</div>'
                f'<div class="jm">Supreme Court · {year} · {html.escape(c["citation"])}{how}</div>'
                f'<p>{html.escape(c["holding"])}</p>{why}{note}'
                f'<a href="{html.escape(c["url"])}" target="_blank" rel="noopener">Read the judgment summary{ic("open_in_new")}</a></li>')

    parts = []
    if j.get("for"):
        parts.append(f'<div class="jg jg-for"><div class="jh">{ic("thumb_up", "fill")}In your favour</div><ul>'
                     + "".join(item(c, "for") for c in j["for"]) + "</ul></div>")
    if j.get("against"):
        parts.append(f'<div class="jg jg-against"><div class="jh">{ic("warning", "fill")}Against you: '
                     f'what the other side may cite</div><ul>' + "".join(item(c, "against") for c in j["against"]) + "</ul></div>")
    side = f'<span class="right">You: {html.escape(j.get("side_label", ""))}</span>' if j.get("side_label") else ""
    return (f'<details class="juds" open><summary>{ic("account_balance")}Supreme Court judgments{side}{ic("expand_more", "chev")}</summary>'
            + "".join(parts) + '<p class="jfoot">Verified summaries from published sources. Read the full judgment, '
            'or ask a lawyer (free: 15100), before relying on one in court.</p></details>')


def sources_html(sources: list) -> str:
    if not sources:
        return ""
    items = "".join(f'<li><a href="{html.escape(s["url"])}" target="_blank" rel="noopener">{html.escape(s["title"])}</a></li>'
                    for s in sources)
    n = len(sources)
    return (f'<details class="srcs"><summary>{ic("menu_book")}Law relied on · {n} verified source{"s" if n > 1 else ""}'
            f'{ic("expand_more", "chev")}</summary><ol>{items}</ol></details>')


def matter_header():
    case = state.get("case") or {}
    issue = state.get("issue") or ("other" if case else None)
    title = known(case.get("summary")) or "New consultation"
    chips = []
    if issue:
        chips.append(ic("category") + html.escape(ISSUES.get(issue, "General matter")))
    if known(case.get("amount_at_stake")):
        chips.append(ic("currency_rupee") + esc(case["amount_at_stake"]))
    if known(case.get("place")):
        chips.append(ic("location_on") + esc(case["place"]))
    steps = [("Your story", bool(ss.chat)), ("Legal opinion", (state.get("assessment") or {}).get("strength") in ("strong", "moderate", "weak")),
             ("Document", bool(ss.get("draft"))), ("Action", bool(ss.done_steps))]
    first_open = next((i for i, (_, d) in enumerate(steps) if not d), None)
    lis = "".join(
        f'<li class="{"done" if d else ("now" if i == first_open else "")}"><span class="dot">'
        f'{ic("check") if d else i + 1}</span><span class="l">{t}</span></li>' for i, (t, d) in enumerate(steps))
    html_block(f'<div class="matter"><div class="row"><div><div class="eyebrow">Your matter</div><h2>{esc(title)}</h2>'
               f'<div class="meta">{"".join(f"<span>{c}</span>" for c in chips)}</div></div>'
               f'<div>{badge_html(state.get("assessment"))}</div></div><ol class="stepper">{lis}</ol></div>')


def nav():
    with st.container(key="nav"):
        st.segmented_control("Section", list(VIEWS), key="view", on_change=keep_view, format_func=VIEWS.get,
                             label_visibility="collapsed")


def thinking(title: str, stages: list[str]) -> str:
    return (f'<div class="thinking">{MARK}<div><b>{title}</b><div class="stages"><div>'
            + "".join(f"<span>{s}</span>" for s in stages) + '</div></div><div class="bar"><i></i></div></div></div>')


def voice_popover(label: str = ":material/mic: Speak instead"):
    if not hasattr(st, "audio_input"):
        return
    with st.popover(label):
        st.caption("Speak in any Indian language. I'll write it down and reply.")
        audio = st.audio_input("Record your problem", label_visibility="collapsed")
    if audio is not None and ss.get("last_audio") != audio.getvalue()[:64]:
        ss.last_audio = audio.getvalue()[:64]
        try:
            with st.spinner("Listening…"):
                text = bot.llm.transcribe(audio.getvalue(), audio.type or "audio/wav")
            if text and text.strip():
                queue(text.strip())
                st.rerun()
        except Exception:
            st.error("Sorry, I couldn't understand the recording. Please try again, or type your problem.")


def footer(slim: bool = False):
    if slim:
        html_block('<div class="foot slim"><p>Nyay Saathi is an AI lawyer, not an enrolled advocate. It relies only on '
                   'verified Indian law (as of 7 Nov 2026) and tells you when you need a human lawyer. '
                   'Free legal aid: <a href="tel:15100">15100</a></p></div>')
        return
    html_block(f'<div class="foot"><div class="b">{MARK}Nyay Saathi</div><p>An AI lawyer, not an enrolled advocate. '
               'Guidance is based on verified Indian law (as of 7 Nov 2026); anything headed to court, or above about '
               '₹5 lakh, should be checked by a human lawyer. Free legal aid: <a href="tel:15100">15100</a> · '
               '<a href="https://github.com/gauravtr/Kuku_230414_IITK" target="_blank" rel="noopener">Source code</a></p></div>')


view = ss.view or ss.last_view
WIDTH = {"consult": 820, "case": 1120, "docs": 1160, "rehearse": 820}

# ====================================================================== landing
if not has_case:
    html_block("<style>:root{--w:1120px}</style>")
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        html_block('<div class="hero"><div class="eyebrow">AI lawyer · built for India</div>'
                   '<h1>Tell me what happened.<br>I\'ll tell you <em>where you stand.</em></h1>'
                   '<p class="lede">Describe your problem the way you\'d tell a friend. You get a clear legal opinion, '
                   'a step-by-step plan with deadlines, and a legal notice ready to send — in your language.</p></div>')
        with st.container(key="hero_composer"):
            first = st.chat_input("e.g. My landlord won't return my ₹50,000 deposit…", key="hero_input")
        if first and first.strip():
            queue(first.strip())
            st.rerun()
        html_block(f'<div class="hint"><span>{ic("lock")}Private — nothing is kept after you close this tab</span>'
                   f'<span>{ic("schedule")}Opinion in about a minute</span><span>{ic("money_off")}Free</span></div>')
        voice_popover()
    with right:
        html_block(
            '<div class="sample"><span class="tag">What you get</span>'
            '<div class="head"><span>Security deposit · Pune</span><b class="num">₹50,000 at stake</b></div>'
            + verdict_html({"strength": "strong", "why": "Repainting after an ordinary tenancy is normal wear and tear. "
                                                         "The landlord can't deduct it from your deposit."})
            + '<h4>Your plan</h4><ol class="plan-mini">'
              '<li><div>Send a written demand on WhatsApp<em>This week</em></div></li>'
              '<li><div>Send a legal notice by Speed Post<em>If there\'s no reply in 15 days</em></div></li>'
              '<li><div>File a civil claim if they still refuse<em>Within 3 years</em></div></li></ol>'
            f'<div class="docline">{ic("description")}<b>Legal notice</b><span class="ok">Ready to send</span></div></div>')

    html_block('<div class="section-h"><div class="sh">Start with a common problem</div>'
               '<span>Or describe anything else above — tenancy, consumer, salary, cheques and more.</span></div>')
    cols = st.columns(2, gap="small")
    for i, (icon, title, sub, lang, text) in enumerate(EXAMPLES):
        with cols[i % 2]:
            with st.container(key=f"ex_{i}"):
                html_block(f'<div class="ex-card"><div class="ic">{ic(icon)}</div><div><b>{title}</b><p>{sub}</p>'
                           f'<span class="lang">Example in {lang}</span></div>{ic("arrow_forward", "go")}</div>')
                st.button(title, key=f"exb_{i}", on_click=queue, args=(text,), width="stretch")

    html_block('<div class="section-h"><div class="sh">How a consultation works</div><span>The same three things a good lawyer gives you '
               'in a first meeting.</span></div><div class="how">'
               '<div><span class="n">01</span><b>Tell your story</b><p>In your own words and language — type it or speak '
               'it. I\'ll ask the questions a lawyer would.</p></div>'
               '<div><span class="n">02</span><b>Get a legal opinion</b><p>How strong your case is, the law that applies, '
               'and the deadlines you must not miss.</p></div>'
               '<div><span class="n">03</span><b>Act on it</b><p>A ready legal notice or complaint, a step-by-step plan, '
               'and a brief for a human lawyer if you need one.</p></div></div>')
    html_block(f'<div class="trust"><h3>Built to be <em>trusted</em> with something that matters.</h3>'
               f'<div>{ic("verified", "ic")}<b>Only verified law</b><p>Every legal point comes from a checked set of '
               f'Indian laws and links to its source. Anything unverified is flagged, never passed off.</p></div>'
               f'<div>{ic("gavel", "ic")}<b>Asks before it refers</b><p>It asks the questions a lawyer would, then advises. A human lawyer is '
               f'suggested only for a clear reason, like an arrest or a court case — a rule enforced in code.</p></div>'
               f'<div>{ic("lock", "ic")}<b>Your case stays yours</b><p>No sign-up. Nothing is kept after you close the '
               f'tab. Never share Aadhaar, bank or card numbers.</p></div></div>')
    html_block('<div class="helplines"><span>Free help, any time:</span>' + "".join(
        f'<a href="tel:{n}">{l} <b>{n}</b></a>' for l, n in HELPLINES) + "</div>")
    footer()
    st.stop()

# ====================================================================== working views
html_block(f"<style>:root{{--w:{WIDTH.get(view, 1080)}px}}</style>")
nav()
matter_header()

# ---------------------------------------------------------------------- consultation
if view == "consult":
    typed = st.chat_input("Reply, or add more details…", key="chat_input")   # pinned to the bottom wherever it's called
    if typed and typed.strip():
        ss.queued = typed.strip()
    for i, m in enumerate(ss.chat):
        if m["role"] == "user":
            html_block(f'<div class="u-row"><div class="u-bubble">{html.escape(m["content"]).replace(chr(10), "<br>")}</div></div>')
            continue
        html_block(f'<div class="a-head">{MARK}<b>Nyay Saathi</b><span>· {"Couldn’t reply" if m.get("error") else "Legal opinion"}</span></div>')
        with st.container(key=f"amsg_{i}"):
            if m.get("error"):
                st.markdown(m["content"])
                continue
            st.markdown(m["content"])
            extra = verdict_html(m.get("assessment"), show_unclear=bool(m.get("open_questions"))) + esc_html(m.get("escalation"))
            extra += judgments_html(m.get("judgments")) + sources_html(m.get("sources"))
            if m.get("unverified"):
                extra += (f'<div class="caution">{ic("warning")}<div>I mentioned '
                          + ", ".join(f"“{html.escape(x)}”" for x in m["unverified"][:4])
                          + ", which I couldn't verify against my checked law. Don't rely on it without asking a lawyer "
                            "(free: 15100).</div></div>")
            if extra:
                html_block(extra)
            qs = m.get("questions") or [{"q": x, "options": []} for x in m.get("open_questions", [])]
            if qs and i == len(ss.chat) - 1:
                question_form(i, qs)
            elif qs:
                html_block(f'<div class="qs-asked"><div class="card-t">{ic("help")}I asked</div><ol>'
                           + "".join(f"<li>{esc(x['q'])}</li>" for x in qs) + "</ol></div>")

    q = ss.pop("queued", None)
    # Guard against double-submit: if the last message in chat is already this user text, skip
    last_role = ss.chat[-1]["role"] if ss.chat else None
    last_content = ss.chat[-1].get("content", "") if ss.chat else ""
    if q and last_role == "user" and last_content == q:
        q = None  # already appended (e.g. form double-submit), don't process again
    if q:
        ss.chat.append({"role": "user", "content": q})
        html_block(f'<div class="u-row"><div class="u-bubble">{html.escape(q).replace(chr(10), "<br>")}</div></div>')
        slot = st.empty()
        slot.markdown(thinking("Reviewing your case", ["Reading your facts…", "Checking the law that applies…",
                                                        "Writing your opinion…"]), unsafe_allow_html=True)
        try:
            r = bot.turn(state, q)
            for s in r["sources"]:
                ss.sources[s["title"]] = s
            msg = {"role": "assistant", "content": r.get("reply_body", r["reply"]),
                   "assessment": r.get("assessment", {}), "escalation": r.get("escalation", {}),
                   "sources": r.get("sources", []), "ready": r.get("ready_to_draft", "none"),
                   "open_questions": r.get("open_questions", []), "questions": r.get("question_form", []), "judgments": r.get("judgments"),
                   "unverified": [f.get("mention") for f in r.get("guard_flags", [])
                                  if f.get("severity") == "block" and f.get("mention")]}
        except Exception as e:
            msg = {"role": "assistant", "content": friendly_error(e), "error": True}
        ss.chat.append(msg)
        st.rerun()

    # next-best actions after the latest answer (no hunting through sections)
    last = ss.chat[-1] if ss.chat else {}
    if last.get("role") == "assistant" and not last.get("error") and state.get("case"):
        ready = last.get("ready", "none")
        opp = OPPONENTS.get(state.get("issue") or "other", OPPONENTS["other"])
        st.write("")
        with st.container(key="actions"):
            c1, c2, c3 = st.columns(3)
            kinds = docs_for(state.get("issue"))
            pick = ready if ready in kinds else kinds[0]
            c1.button(":material/edit_document: Draft " + {"legal_notice": "legal notice", "consumer_complaint": "complaint",
                      "dv_application": "DV application", "police_complaint": "police complaint"}[pick],
                      width="stretch", type="primary" if ready in kinds else "secondary",
                      on_click=go, args=("docs", pick))
            c2.button(":material/folder_open: Case file & plan", width="stretch", on_click=go, args=("case",))
            c3.button(f":material/record_voice_over: Rehearse with {opp[1].lower()}", width="stretch",
                      on_click=go, args=("rehearse",))
    c_hint, c_voice = st.columns([3, 1], vertical_alignment="center")
    c_hint.markdown(f'<div class="hint"><span>{ic("tips_and_updates")}Answer my questions in the chat, or add anything I missed. '
                    'Don\'t share Aadhaar, bank or card numbers.</span></div>', unsafe_allow_html=True)
    with c_voice:
        voice_popover(":material/mic: Speak")
    footer(slim=True)

# ---------------------------------------------------------------------- case file
elif view == "case":
    case = state.get("case") or {}
    if not case:
        html_block('<div class="paper-empty" style="min-height:0"><div class="msg">' + ic("folder_open") +
                   '<b>Your case file is being prepared</b><p>It fills itself in as we talk: the facts, my opinion, '
                   'your action plan and every deadline.</p></div></div>')
        st.button(":material/forum: Back to the consultation", on_click=go, args=("consult",), type="primary")
    else:
        main, side = st.columns([1.7, 1], gap="large")
        last = next((m for m in reversed(ss.chat) if m["role"] == "assistant" and not m.get("error")), {})
        with main:
            with st.container(key="card_opinion"):
                html_block(f'<div class="card-t">{ic("balance")}My legal opinion</div>'
                           + (verdict_html(state.get("assessment"), show_unclear=True) or
                              '<p class="note">I\'ll give you my view once I have the key facts.</p>')
                           + esc_html(state.get("escalation"))
                           + "".join(f'<div class="deadline">{ic("event")}<div><b>Deadline</b> · {esc(d)}</div></div>'
                                     for d in case.get("deadlines", []) if known(d)))
            plan = state.get("plan") or []
            if plan:
                with st.container(key="card_plan"):
                    done = sum(clean(p["step"]) in ss.done_steps for p in plan)
                    html_block(f'<div class="card-t">{ic("checklist")}Your action plan<span class="right">'
                               f'{done} of {len(plan)} done</span></div><div class="progress">'
                               f'<i style="width:{100 * done / len(plan):.0f}%"></i></div>')
                    for p in plan:
                        step = clean(p["step"])
                        when = known(p.get("by_when"))
                        k = f"plan_{hashlib.md5(step.encode()).hexdigest()[:8]}"
                        st.checkbox(step + (f" — _{when}_" if when else ""), value=step in ss.done_steps, key=k,
                                    on_change=toggle_step, args=(step, k))
            if state.get("open_questions"):
                with st.container(key="card_questions"):
                    html_block(f'<div class="card-t">{ic("help")}What I still need from you</div><ul class="qs">'
                               + "".join(f"<li>{esc(q)}</li>" for q in state["open_questions"]) + "</ul>")
                    st.button(":material/forum: Answer in the consultation", on_click=go, args=("consult",))
            tl = [t for t in case.get("timeline", []) if isinstance(t, dict)]
            if tl:
                with st.container(key="card_timeline"):
                    items = "".join(
                        f'<li><span class="d">{esc(t.get("date", ""))}</span>'
                        f'{esc(t.get("event") or " · ".join(str(v) for k, v in t.items() if k != "date"))}</li>' for t in tl)
                    html_block(f'<div class="card-t">{ic("timeline")}Timeline</div><ul class="tl">{items}</ul>')
            with st.container(key="card_evidence"):
                have = [esc(p) for p in case.get("proof_have", []) if known(p)]
                need = [esc(p) for p in case.get("proof_missing", []) if known(p)]
                e1, e2 = st.columns(2)
                e1.markdown(f'<div class="card-t">{ic("inventory")}Proof you have</div>' + (
                    '<ul class="ev have">' + "".join(f"<li>{ic('check_circle', 'fill')}{p}</li>" for p in have) + "</ul>"
                    if have else '<p class="empty-line">Nothing noted yet</p>'), unsafe_allow_html=True)
                e2.markdown(f'<div class="card-t">{ic("search")}Proof to collect</div>' + (
                    '<ul class="ev need">' + "".join(f"<li>{ic('radio_button_unchecked')}{p}</li>" for p in need) + "</ul>"
                    if need else '<p class="empty-line">Nothing pending</p>'), unsafe_allow_html=True)
        with side:
            people = case.get("people") if isinstance(case.get("people"), dict) else {}
            rows = [("Matter", ISSUES.get(state.get("issue") or "other")), ("Amount at stake", known(case.get("amount_at_stake"))),
                    ("Place", known(case.get("place"))), ("You are", known(people.get("user"))),
                    ("Other side", known(people.get("other_side"))), ("You want", known(case.get("what_user_wants")))]
            with st.container(key="card_glance"):
                html_block(f'<div class="card-t">{ic("info")}At a glance</div><dl class="kv">'
                           + "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in rows if v) + "</dl>")
            with st.container(key="card_brief"):
                html_block(f'<div class="card-t">{ic("work")}Seeing a human lawyer?</div><p class="note">Hand them a '
                           'one-page brief with your facts, timeline, proof and the law I relied on. They\'ll understand '
                           'your case in minutes.</p>')
                srcs = list(ss.sources.values())
                data = brief.docx_bytes(state, srcs)
                if data:
                    st.download_button(":material/download: Case brief (Word)", data, "nyay_case_brief.docx",
                                       width="stretch", type="primary")
                st.download_button(":material/article: Case brief (text)", brief.markdown(state, srcs), "nyay_case_brief.md",
                                   width="stretch")
                st.download_button(":material/data_object: Case data (JSON)", json.dumps(case, ensure_ascii=False, indent=2),
                                   "nyay_case.json", width="stretch", type="tertiary")
            with st.container(key="card_help"):
                html_block(f'<div class="card-t">{ic("support_agent")}Free help</div><div class="helplist">'
                           + "".join(f'<a href="tel:{n}">{l}<b>{n}</b></a>' for l, n in HELPLINES) + "</div>")
    footer(slim=True)

# ---------------------------------------------------------------------- documents
elif view == "docs":
    if not state.get("case"):
        html_block('<div class="paper-empty" style="min-height:0"><div class="msg">' + ic("description") +
                   '<b>Tell me about your problem first</b><p>I draft from your facts — names, dates and amounts — so '
                   'the consultation comes first.</p></div></div>')
        st.button(":material/forum: Start the consultation", on_click=go, args=("consult",), type="primary")
    else:
        kinds = docs_for(state.get("issue"))
        if ss.get("doc_kind") not in kinds:
            ss.doc_kind = kinds[0]
        left, right = st.columns([1, 1.45], gap="large")
        d = ss.get("draft")
        with left:
            with st.container(key="card_doctype"):
                html_block(f'<div class="card-t">{ic("description")}Choose a document</div>')
                kind = st.radio("Document", kinds, key="doc_kind", format_func=lambda k: DOCS[k][0],
                                label_visibility="collapsed")
                html_block(f'<div class="note">{DOCS[kind][1]}</div>')
                again = d and d.get("kind") == kind
                go_draft = st.button((":material/refresh: Redraft " if again else ":material/edit: Draft my ")
                                     + DOCS[kind][0].lower(), type="secondary" if again else "primary", width="stretch")
                st.caption("Written from your case file in about 10–40 seconds.")
            if d and d.get("blanks"):
                with st.container(key="card_blanks"):
                    filled = sum(bool(ss.blank_values.get(b, "").strip()) for b in d["blanks"])
                    html_block(f'<div class="card-t">{ic("edit_note")}Fill in your details<span class="right">'
                               f'{filled} of {len(d["blanks"])}</span></div>'
                               '<p class="note">They go straight into the document.</p>')
                    for b in d["blanks"]:
                        val = st.text_input(b.strip("[]").capitalize(), value=ss.blank_values.get(b, ""),
                                            key=f"blank_{d.get('kind')}_{b}")
                        ss.blank_values[b] = val          # kept outside the widget, so it survives switching sections
            if d:
                with st.container(key="card_send"):
                    if d.get("kind") == "legal_notice":
                        steps = ["Read it once, fill any gaps, then print and sign it.",
                                 "Send it by <b>Registered Post AD</b> or <b>Speed Post</b>. Keep the receipt.",
                                 "Also send a scan by email or WhatsApp, if you have their contact.",
                                 "Note the date. If there's no reply by the deadline in the notice, come back for next steps."]
                    elif d.get("kind") == "dv_application":
                        steps = ["Call <b>181</b> or <b>15100</b> and ask for the district <b>Protection Officer</b> or a free "
                                 "DLSA lawyer. Women get free legal aid, whatever their income.",
                                 "Take this draft, your medical (MLC) papers, photos and messages to them. They file it with the "
                                 "Magistrate along with your affidavit.",
                                 "Ask for an <b>urgent ex parte protection order</b> on the first day if you are at risk.",
                                 "Keep copies of everything, and the case number, for every hearing."]
                    elif d.get("kind") == "police_complaint":
                        steps = ["Print two copies and sign both. Go to <b>any</b> police station; it doesn't have to be where it "
                                 "happened. Take someone you trust if you can.",
                                 "Hand it to the duty officer and get the second copy stamped as received (date and stamp).",
                                 "Ask to be sent for a <b>medical examination</b>, and ask for your <b>free copy of the FIR</b>.",
                                 "If they refuse, send the stamped copy to the <b>Superintendent of Police</b> by Registered Post "
                                 "the same day, and keep the receipt."]
                    else:
                        steps = ["File it online at <b>e-Jagriti</b> (e-jagriti.gov.in).",
                                 "Attach an affidavit and copies of your proof: bills, chats, photos, your notice.",
                                 "Pay the small filing fee shown on the portal.",
                                 "Keep your complaint number safe for hearings and follow-ups."]
                    html_block(f'<div class="card-t">{ic("local_post_office")}How to send it</div><ol class="steps-n">'
                               + "".join(f"<li><span>{s}</span></li>" for s in steps) + "</ol>")
        with right:
            slot = st.empty()
            if go_draft:
                slot.markdown(f'<div class="paper-empty loading"><div class="ln" style="width:38%"></div>'
                              f'<div class="ln" style="width:62%"></div><div class="msg">{ic("edit_document")}'
                              f'<b>Drafting your {DOCS[kind][0].lower()}…</b><p>Using your facts and only verified law.</p>'
                              '</div>' + "".join(f'<div class="ln" style="width:{w}%"></div>' for w in (96, 88, 92, 70, 84)) +
                              "</div>", unsafe_allow_html=True)
                try:
                    ss.draft = dict(bot.draft(state, kind), kind=kind)
                except Exception as e:
                    ss.draft_error = friendly_error(e)
                st.rerun()
            if ss.get("draft_error"):
                st.error(ss.pop("draft_error"))
            if not d:
                slot.markdown('<div class="paper-empty"><div class="ln" style="width:38%"></div><div class="ln" style="width:62%">'
                              f'</div><div class="msg">{ic("history_edu")}<b>Your draft appears here</b><p>Written like a '
                              'lawyer would, from your case file — with your names, dates and amounts. You can edit every '
                              'line before you send it.</p></div>'
                              + "".join(f'<div class="ln" style="width:{w}%"></div>' for w in (96, 88, 92, 70)) + "</div>",
                              unsafe_allow_html=True)
            else:
                text = d["document"]
                for b in d.get("blanks", []):
                    if ss.blank_values.get(b, "").strip():
                        text = text.replace(b, ss.blank_values[b].strip())
                left_blanks = [b for b in d.get("blanks", []) if b in text]
                status = (f'<span class="st st-todo">{len(left_blanks)} detail{"s" if len(left_blanks) > 1 else ""} to fill</span>'
                          if left_blanks else '<span class="st st-ok">Ready to send</span>')
                if d.get("user_note"):
                    html_block(f'<div class="usernote">{ic("lightbulb")}<div>{esc(d["user_note"])}</div></div>')
                html_block(f'<div class="paper-bar"><span class="t">{ic("description")}<b>{DOCS.get(d.get("kind"), ("Document",))[0]}</b>'
                           f'· editable</span>{status}</div>')
                key = "doc_" + hashlib.md5(text.encode()).hexdigest()[:10]   # refresh the editor when details change
                with st.container(key="paper"):
                    text = st.text_area("Your document", ss.doc_edits.get(key, text), height=620, key=key,
                                        label_visibility="collapsed")
                ss.doc_edits[key] = text
                b1, b2 = st.columns(2)
                try:
                    from docx import Document
                    from docx.shared import Pt
                    doc = Document()
                    doc.styles["Normal"].font.name, doc.styles["Normal"].font.size = "Georgia", Pt(11.5)
                    for para in text.split("\n"):
                        doc.add_paragraph(para)
                    buf = io.BytesIO()
                    doc.save(buf)
                    b1.download_button(":material/download: Word (.docx)", buf.getvalue(), f"nyay_{d.get('kind', 'document')}.docx",
                                       width="stretch", type="primary")
                except ImportError:
                    pass
                b2.download_button(":material/article: Plain text", text, f"nyay_{d.get('kind', 'document')}.txt", width="stretch")
                st.caption("Drafted by an AI lawyer from your facts. Read every line before sending. If the other side has a "
                           "lawyer, or more than about ₹5 lakh is at stake, have a human lawyer check it (free: 15100).")
    footer(slim=True)

# ---------------------------------------------------------------------- rehearse
elif view == "rehearse":
    opp_long, opp_short = OPPONENTS.get(state.get("issue") or "other", OPPONENTS["other"])
    with st.container(key="card_room"):
        html_block(f'<div class="room"><div class="av">{ic("person")}</div><div><b>Rehearsal room</b>'
                   f'<p>You\'re talking to <b style="display:inline;font-family:inherit;font-size:inherit">{opp_long}</b>. '
                   'They\'ll push back the way they usually do. After each reply, your coach tells you what worked and '
                   'what to say next.</p></div></div>')
        c1, c2 = st.columns(2)
        want_feedback = c1.button(":material/rate_review: End & get feedback", width="stretch", disabled=not ss.practise)
        if c2.button(":material/restart_alt: Start over", width="stretch", disabled=not ss.practise):
            ss.practise = []
            st.rerun()

    coach_re = re.compile(r"\n?\s*\**\s*COACH\s*\**\s*:\s*\**", re.I)
    for i, m in enumerate(ss.practise):
        if m["role"] == "user":
            if m["content"].strip().lower() not in ("feedback", "stop"):
                html_block(f'<div class="u-row"><div class="u-bubble">{html.escape(m["content"]).replace(chr(10), "<br>")}</div></div>')
            continue
        body = m["content"]
        src = ""
        if "**Sources (checked):**" in body:
            body, src = body.split("**Sources (checked):**", 1)
            src = re.sub(r"\s—\s.*?(?=;\s*\[\d|$)", "", src, flags=re.S)   # titles only; links live in the consultation
        is_feedback = i > 0 and ss.practise[i - 1]["content"].strip().lower() in ("feedback", "stop")
        if is_feedback:
            with st.container(key=f"card_feedback_{i}"):
                html_block(f'<div class="card-t">{ic("school")}Coach\'s feedback</div>')
                st.markdown(clean(body))
            continue
        parts = coach_re.split(body, maxsplit=1)
        html_block(f'<div class="o-head">{ic("person")}{opp_short}</div><div class="o-bubble">{esc(parts[0].strip())}</div>'
                   + (f'<div class="coach">{ic("lightbulb", "fill")}<div><b>Coach</b>{esc(parts[1].strip())}'
                      + (f'<span class="src">Based on: {html.escape(clean(src)).strip(" .")}</span>' if src.strip() else "")
                      + "</div></div>" if len(parts) > 1 else ""))
    p = st.chat_input(f"Say it the way you would to {opp_long}…", key="practise_input")
    p = p or ("feedback" if want_feedback else None)
    if p:
        if p != "feedback":
            html_block(f'<div class="u-row"><div class="u-bubble">{html.escape(p)}</div></div>')
        html_block(thinking("Your coach is reviewing" if p == "feedback" else f"{opp_short} is replying",
                            ["Thinking it over…", "Choosing their words…", "Almost there…"]))
        try:
            bot.practise(state, ss.practise, p, opp_long)
        except Exception as e:
            st.error(friendly_error(e))
        st.rerun()
    if not ss.practise:
        html_block(f'<div class="hint" style="margin-top:14px"><span>{ic("tips_and_updates")}Open the way you would in real '
                   'life: say what you want, by when, and why you\'re entitled to it.</span></div>')
    footer(slim=True)
