"""Nyay Saathi - your AI lawyer. Streamlit UI.   Run:  streamlit run app.py

Product notes (who this is for and why the screen looks like this):
- The user is stressed, often on a phone, often not comfortable in English, and has never met a lawyer.
  So: one obvious place to type, their language, short answers, and always a clear "what do I do next".
- A lawyer's first consultation gives three things: where you stand, what to do, and the paperwork.
  The flow mirrors that: Consultation -> Case file (opinion + plan) -> Documents -> Practise.
- Trust is earned by showing the law relied on (verified sources) and by being blunt about when a
  human lawyer is needed. That escalation is decided by code, not left to the model.
"""
import hashlib
import io
import json
import os

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

st.set_page_config(page_title="Nyay Saathi · AI Lawyer for India", page_icon="⚖️", layout="wide",
                   menu_items={"About": "Nyay Saathi: an AI lawyer for everyday legal problems in India, in your language. "
                                        "It tells you plainly when you need a human lawyer. Free legal aid: NALSA 15100."})

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea {font-family: 'Inter', 'Noto Sans', sans-serif;}
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.2rem; padding-bottom: 6rem; max-width: 960px;}
.ns-hero {background: radial-gradient(1200px 300px at 0% 0%, #2B4C9B 0%, #0B2545 60%); color:#fff; border-radius:18px;
          padding:26px 28px 22px; margin-bottom:14px;}
.ns-hero .tag {display:inline-block; background:#C9A227; color:#0B2545; font-weight:700; font-size:.75rem;
               letter-spacing:.06em; border-radius:6px; padding:2px 8px; margin-bottom:8px;}
.ns-hero h1 {color:#fff; font-size:2rem; margin:0 0 6px 0; font-weight:700;}
.ns-hero p {color:#DCE4F5; margin:0; font-size:1.02rem; line-height:1.5;}
.ns-bar {display:flex; align-items:center; gap:10px; background:#0B2545; color:#fff; border-radius:14px;
         padding:10px 16px; margin-bottom:10px;}
.ns-bar b {font-size:1.1rem;} .ns-bar span.t {color:#C9D6F2; font-size:.88rem;}
.ns-bar .tag {background:#C9A227; color:#0B2545; font-weight:700; font-size:.7rem; border-radius:5px; padding:1px 6px;}
.ns-values {display:grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap:10px; margin:6px 0 14px;}
.ns-value {border:1px solid #E5E7EB; border-radius:14px; padding:12px 14px; background:#fff;}
.ns-value b {display:block; margin-bottom:2px;} .ns-value span {color:#4B5563; font-size:.9rem;}
.ns-steps {display:flex; gap:6px; margin:4px 0 12px; flex-wrap:wrap;}
.ns-step {flex:1; min-width:120px; border-radius:10px; padding:6px 10px; font-size:.82rem; background:#F3F4F6; color:#6B7280;}
.ns-step.done {background:#E7F6EE; color:#166534;} .ns-step.now {background:#E8EEFB; color:#1E3A8A; font-weight:600;}
.ns-pill {display:inline-block; border-radius:999px; padding:3px 12px; font-size:.85rem; font-weight:600; margin:4px 0 2px;}
.ns-strong {background:#DCFCE7; color:#166534;} .ns-moderate {background:#FEF3C7; color:#92400E;}
.ns-weak {background:#FEE2E2; color:#991B1B;} .ns-unclear {background:#F3F4F6; color:#374151;}
.ns-why {color:#4B5563; font-size:.88rem;}
.ns-help {background:#F3F5FA; border-radius:12px; padding:10px 12px; font-size:.9rem; line-height:1.7;}
.ns-foot {color:#6B7280; font-size:.78rem; text-align:center; margin-top:28px; border-top:1px solid #E5E7EB; padding-top:10px;}
div[data-testid="stChatMessage"] {border-radius:14px;}
</style>""", unsafe_allow_html=True)

LANGS = {"🌐 Auto (my language)": "auto", "English": "English", "हिंदी (Hindi)": "Hindi in Devanagari script",
         "Hinglish": "Hinglish (Hindi in Latin script)", "தமிழ் (Tamil)": "Tamil", "বাংলা (Bengali)": "Bengali",
         "मराठी (Marathi)": "Marathi", "తెలుగు (Telugu)": "Telugu", "ಕನ್ನಡ (Kannada)": "Kannada",
         "ગુજરાતી (Gujarati)": "Gujarati", "മലയാളം (Malayalam)": "Malayalam"}
OPPONENTS = {"deposit": "the landlord", "consumer": "the company's customer-care manager",
             "salary": "the employer's HR manager", "cheque": "the person who gave the cheque", "other": "the other side"}
EXAMPLES = [
    ("🏠 Deposit not returned", "I vacated my rented flat in Pune on 30 September. The landlord is not returning my ₹50,000 "
                               "deposit and says he will cut money for painting. What can I do?"),
    ("📦 Refund / faulty product", "Maine 10 din pehle online ₹15,999 ka phone liya, screen kharab nikli. Return reject kar diya. "
                                   "Paisa wapas kaise milega?"),
    ("💼 Salary not paid", "मेरी कंपनी ने पिछले 2 महीने की सैलरी (₹30,000 प्रति माह) नहीं दी है और मैंने इस्तीफा दे दिया है। क्या करूँ?"),
    ("🧾 Cheque bounce notice", "I received a legal notice saying my ₹80,000 cheque bounced and I must pay in 15 days. "
                                "What does this mean for me?"),
]
VIEWS = ["💬 Consultation", "📁 Case file", "📝 Documents", "🥊 Practise"]
DOCS = {"legal_notice": ("Legal notice", "A formal demand to the other side. Usually the first step."),
        "consumer_complaint": ("Consumer complaint", "For the District Consumer Commission, if a notice didn't work.")}
STRENGTH = {"strong": ("🟢 Strong case", "ns-strong"), "moderate": ("🟡 Moderate case", "ns-moderate"),
            "weak": ("🔴 Weak case", "ns-weak"), "unclear": ("⚪ Need a few more facts", "ns-unclear")}
REASONS = {"safety": "This may involve your safety or liberty.",
           "out_of_scope": "This is outside the areas where I have verified Indian law.",
           "large_amount": "A large amount is at stake (over about ₹5 lakh).",
           "ambiguous": "Key facts are still unclear, and they change the legal answer."}

# ------------------------------------------------------------------ state
ss = st.session_state
if "state" not in ss:
    ss.state, ss.chat, ss.practise, ss.sources, ss.done_steps = new_state(), [], [], {}, set()
    ss.blank_values, ss.doc_edits = {}, {}
ss.setdefault("view", VIEWS[0])
ss.setdefault("last_view", VIEWS[0])
state = ss.state


def go(view: str, doc_kind: str | None = None):
    ss.view = ss.last_view = view
    if doc_kind in DOCS:
        ss.doc_kind = doc_kind


def keep_view():   # segmented control: clicking the active option would deselect it; keep it selected
    if ss.view is None:
        ss.view = ss.last_view
    ss.last_view = ss.view


def clean(x) -> str:
    """Display text: drop internal law-card tags like [GEN-LIMIT]."""
    return MARKER_RE.sub("", str(x or "")).replace("  ", " ").strip()


def friendly_error(e: Exception) -> str:
    print("Nyay Saathi model error:", type(e).__name__, _safe(e), flush=True)   # shows in the app logs
    return ("Sorry, I couldn't reach the AI service just now. Please send your message again in a minute. "
            "If it's urgent, call the free legal aid helpline **15100**.\n\n"
            f"`Technical detail: {type(e).__name__}: {_safe(e)[:160]}`")


def new_case():
    for k in ("state", "chat", "practise", "sources", "done_steps", "draft", "pending", "doc_kind", "blank_values",
              "doc_edits"):
        ss.pop(k, None)
    ss.view = ss.last_view = VIEWS[0]


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("### ⚖️ Nyay Saathi")
    st.caption("Your AI lawyer for everyday legal problems in India.")
    st.button("➕ New consultation", width="stretch", on_click=new_case)
    st.markdown('<div class="ns-help"><b>Free help, any time</b><br>⚖️ Free lawyer (NALSA): <b>15100</b><br>'
                '🛒 Consumer helpline: <b>1915</b><br>💳 Cyber fraud: <b>1930</b><br>👩 Women helpline: <b>181</b><br>'
                '🚨 Emergency: <b>112</b></div>', unsafe_allow_html=True)
    st.write("")
    with st.expander("🛡️ How Nyay stays accurate"):
        st.markdown("- It may only state law from **verified law cards**, and every claim is linked to its source.\n"
                    "- Code checks each answer: any section, act or court case not on a card is flagged.\n"
                    "- It tells you when you need a human lawyer: code decides this too, not just the AI.\n"
                    "- Law verified as of 7 Nov 2026.")
    available = [p for p, k in [("gemini", "GEMINI_API_KEY"), ("groq", "GROQ_API_KEY"), ("openai", "OPENAI_API_KEY"),
                                ("openrouter", "OPENROUTER_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")] if os.getenv(k)]
    default_p = os.getenv("NYAY_PROVIDER", available[0] if available else "gemini")
    options = sorted(set(available + [default_p]))
    with st.expander("⚙️ Advanced: AI model"):
        provider = st.selectbox("Provider", options, index=options.index(default_p))
        model = st.text_input("Model (blank = default)", os.getenv("NYAY_MODEL", ""))
        st.caption("Any provider works: Gemini, Groq, OpenAI, Anthropic or Ollama. The law checks stay the same.")

if "llm" not in ss or ss.get("llm_cfg") != (provider, model):
    ss.llm = LLM(provider, model or None)       # kept per session: remembers a working fallback model
    ss.llm_cfg = (provider, model)
bot = NyaySaathi(ss.llm)

# ------------------------------------------------------------------ header
if not ss.chat:
    st.markdown("""<div class="ns-hero"><span class="tag">AI LAWYER · INDIA</span><h1>⚖️ Nyay Saathi</h1>
<p>Tell me your legal problem in your own words and language. I'll tell you where you stand, what to do next,
draft your legal notice or complaint, and tell you straight when you need a human lawyer.</p></div>
<div class="ns-values">
<div class="ns-value"><b>🧭 Know where you stand</b><span>A clear legal opinion on your case, its strength and your deadlines.</span></div>
<div class="ns-value"><b>📝 Get the paperwork</b><span>Legal notices and consumer complaints, ready to send.</span></div>
<div class="ns-value"><b>✅ Only verified law</b><span>Every legal point links to its source. No made-up sections.</span></div>
</div>""", unsafe_allow_html=True)
else:
    st.markdown('<div class="ns-bar">⚖️ <b>Nyay Saathi</b> <span class="tag">AI LAWYER</span>'
                '<span class="t">Verified Indian law · your language · free legal aid 15100</span></div>',
                unsafe_allow_html=True)

nav_col, lang_col = st.columns([3, 1])
with nav_col:
    st.segmented_control("Section", VIEWS, key="view", on_change=keep_view, label_visibility="collapsed")
with lang_col:
    lang_label = st.selectbox("Reply language", list(LANGS), label_visibility="collapsed",
                              help="I reply in the language you write in. Pick one to always use it.")
state["language"] = LANGS[lang_label]
view = ss.view or ss.last_view

if not available:
    st.error("The AI service isn't configured yet. The owner needs to add a free GEMINI_API_KEY in Settings → Secrets.")

# progress: tell -> opinion -> document -> act
if ss.chat:
    steps = [("1 · Tell your story", bool(ss.chat)), ("2 · Legal opinion", bool(state.get("assessment"))),
             ("3 · Prepare document", bool(ss.get("draft"))), ("4 · Take action", bool(ss.done_steps))]
    first_open = next((i for i, (_, d) in enumerate(steps) if not d), None)
    st.markdown('<div class="ns-steps">' + "".join(
        f'<div class="ns-step {"done" if d else ("now" if i == first_open else "")}">{"✓ " if d else ""}{t}</div>'
        for i, (t, d) in enumerate(steps)) + "</div>", unsafe_allow_html=True)


def opinion_block(m: dict):
    a = m.get("assessment") or {}
    if a.get("strength") in STRENGTH and (a.get("strength") != "unclear" or m.get("open_questions")):
        label, css = STRENGTH[a["strength"]]
        why = f' <span class="ns-why">{clean(a.get("why"))}</span>' if a.get("why") else ""
        st.markdown(f'<span class="ns-pill {css}">{label}</span>{why}', unsafe_allow_html=True)
    esc = m.get("escalation") or {}
    reasons = [REASONS.get(r, clean(r)) for r in esc.get("reasons", [])]
    if esc.get("level") == "urgent":
        st.error("🚨 **Speak to a human lawyer now.** " + " ".join(reasons) +
                 "\n\nFree legal aid: call **15100** (NALSA). In an emergency, call **112**.")
    elif esc.get("level") == "consult":
        st.warning("👩‍⚖️ **I recommend a human lawyer for this.** " + " ".join(reasons) +
                   "\n\nFree legal aid: call **15100** (NALSA). Take your **case brief** from the Case file tab.")
    if m.get("sources"):
        with st.expander(f"📚 Law I relied on ({len(m['sources'])} verified sources)"):
            for s in m["sources"]:
                st.markdown(f"**[{s['n']}]** {s['title']}: {s['url']}")


# ---------------------------------------------------------------------- consultation
if view == VIEWS[0]:
    if not ss.chat:
        st.markdown("##### What's your legal problem? Type it, speak it, or start from an example:")
        cols = st.columns(2)
        for i, (label, text) in enumerate(EXAMPLES):
            if cols[i % 2].button(label, width="stretch", key=f"ex{i}"):
                ss.pending = text
        st.caption("🔒 Don't share Aadhaar, bank or card numbers. Nyay Saathi is an AI lawyer, not an enrolled advocate; "
                   "for anything that goes to court, it will tell you to get a human lawyer.")
    for i, m in enumerate(ss.chat):
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "⚖️"):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                opinion_block(m)

    # next-best actions after the latest answer (no hunting through tabs)
    if ss.chat and ss.chat[-1]["role"] == "assistant" and not ss.chat[-1].get("error") and state.get("case"):
        ready = ss.chat[-1].get("ready", "none")
        c1, c2, c3 = st.columns(3)
        c1.button(f"📝 Draft {DOCS.get(ready, DOCS['legal_notice'])[0].lower()}", width="stretch",
                  type="primary" if ready in DOCS else "secondary", on_click=go, args=(VIEWS[2], ready))
        c2.button("📁 My case file & plan", width="stretch", on_click=go, args=(VIEWS[1],))
        c3.button("🥊 Practise the conversation", width="stretch", on_click=go, args=(VIEWS[3],))

    voice_text = None
    if hasattr(st, "audio_input"):
        with st.expander("🎤 Speak instead of typing (any Indian language)", expanded=not ss.chat):
            audio = st.audio_input("Record your problem", label_visibility="collapsed")
        if audio is not None and ss.get("last_audio") != audio.getvalue()[:64]:
            ss.last_audio = audio.getvalue()[:64]
            try:
                with st.spinner("Listening…"):
                    voice_text = bot.llm.transcribe(audio.getvalue(), audio.type or "audio/wav")
            except Exception:
                st.error("Sorry, I couldn't understand the recording. Please try again or type your problem.")
    typed = st.chat_input("Describe your problem, or answer my questions…")
    user_text = typed or voice_text or ss.pop("pending", None)
    if user_text:
        ss.chat.append({"role": "user", "content": user_text})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_text)
        with st.chat_message("assistant", avatar="⚖️"):
            with st.spinner("Reviewing your case like a lawyer would… (usually 20–50 seconds)"):
                try:
                    r = bot.turn(state, user_text)
                    for s in r["sources"]:
                        ss.sources[s["title"]] = s
                    msg = {"role": "assistant", "content": r["reply_body"], "assessment": r["assessment"],
                           "escalation": r["escalation"], "sources": r["sources"], "ready": r["ready_to_draft"],
                           "open_questions": r["open_questions"]}
                except Exception as e:
                    msg = {"role": "assistant", "content": friendly_error(e), "error": True}
        ss.chat.append(msg)
        st.rerun()

# ---------------------------------------------------------------------- case file
elif view == VIEWS[1]:
    case = state.get("case") or {}
    if not case:
        st.info("Your case file builds itself as we talk: the facts, my legal opinion, your action plan and deadlines.")
        st.button("💬 Start the consultation", on_click=go, args=(VIEWS[0],), type="primary")
    else:
        st.markdown(f"#### {clean(case.get('summary', 'Your case'))}")
        facts = [("Problem type", (state.get("issue") or "").title()), ("Amount at stake", case.get("amount_at_stake")),
                 ("Place", case.get("place"))]
        st.markdown(" · ".join(f"**{k}:** {clean(v)}" for k, v in facts
                               if v and str(v).strip().lower() not in ("unknown", "-", "none", "n/a")))
        last = next((m for m in reversed(ss.chat) if m["role"] == "assistant" and not m.get("error")), None)
        with st.container(border=True):
            st.markdown("**🧭 My legal opinion**")
            if last:
                opinion_block({k: v for k, v in last.items() if k != "sources"})
            for d in case.get("deadlines", []):
                st.markdown(f"⏰ **Deadline:** {clean(d)}")

        plan = state.get("plan") or []
        if plan:
            st.markdown(f"**✅ Your action plan** ({sum(clean(p['step']) in ss.done_steps for p in plan)} of {len(plan)} done)")
            for i, p in enumerate(plan):
                step = clean(p["step"])
                when = f" — _{clean(p['by_when'])}_" if p.get("by_when") else ""
                checked = st.checkbox(step + when, value=step in ss.done_steps, key=f"plan_{hashlib.md5(step.encode()).hexdigest()[:8]}")
                (ss.done_steps.add if checked else ss.done_steps.discard)(step)
        if state.get("open_questions"):
            st.markdown("**❓ What I still need from you**")
            st.markdown("\n".join(f"- {clean(q)}" for q in state["open_questions"]))
            st.button("💬 Answer in the consultation", on_click=go, args=(VIEWS[0],))
        if case.get("timeline"):
            st.markdown("**🗓️ Timeline**")
            st.dataframe([{k: clean(v) for k, v in t.items()} for t in case["timeline"] if isinstance(t, dict)],
                         width="stretch", hide_index=True)
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**📎 Proof you have**")
            st.markdown("\n".join(f"- {clean(p)}" for p in case.get("proof_have", [])) or "_Nothing yet_")
        with c4:
            st.markdown("**📌 Proof to collect**")
            st.markdown("\n".join(f"- {clean(p)}" for p in case.get("proof_missing", [])) or "_Nothing pending_")

        st.markdown("**👩‍⚖️ Taking this to a human lawyer?** Download a one-page brief so they understand your case in minutes.")
        srcs = list(ss.sources.values())
        b1, b2, b3 = st.columns(3)
        data = brief.docx_bytes(state, srcs)
        if data:
            b1.download_button("📄 Case brief (Word)", data, "nyay_case_brief.docx", width="stretch", type="primary")
        b2.download_button("📝 Case brief (text)", brief.markdown(state, srcs), "nyay_case_brief.md", width="stretch")
        b3.download_button("💾 Case data (JSON)", json.dumps(case, ensure_ascii=False, indent=2), "nyay_case.json",
                           width="stretch")

# ---------------------------------------------------------------------- documents
elif view == VIEWS[2]:
    if not state.get("case"):
        st.info("Tell me about your problem in the **Consultation** first, so I can draft from your facts.")
        st.button("💬 Start the consultation", on_click=go, args=(VIEWS[0],), type="primary")
    else:
        ss.setdefault("doc_kind", "legal_notice")
        kind = st.radio("Which document do you need?", list(DOCS), key="doc_kind", horizontal=True,
                        format_func=lambda k: DOCS[k][0])
        st.caption(DOCS[kind][1])
        if st.button(f"✍️ Draft my {DOCS[kind][0].lower()}", type="primary"):
            with st.spinner("Drafting from your case file… (usually 15–40 seconds)"):
                try:
                    ss.draft = dict(bot.draft(state, kind), kind=kind)
                except Exception as e:
                    st.error(friendly_error(e))
        d = ss.get("draft")
        if d:
            if d.get("user_note"):
                st.info(d["user_note"])
            text = d["document"]
            if d["blanks"]:
                with st.container(border=True):
                    st.markdown("**🖊️ Fill in your details** (they go straight into the document)")
                    cols = st.columns(2)
                    for i, b in enumerate(d["blanks"]):
                        val = cols[i % 2].text_input(b.strip("[]").capitalize(), value=ss.blank_values.get(b, ""),
                                                     key=f"blank_{d.get('kind')}_{b}")
                        ss.blank_values[b] = val          # kept outside the widget, so it survives switching sections
                        if val.strip():
                            text = text.replace(b, val.strip())
                left = [b for b in d["blanks"] if b in text]
                if left:
                    st.caption(f"Still to fill: {len(left)} of {len(d['blanks'])}. You can also edit the text directly below.")
                else:
                    st.success("All details filled in. Read it once, then download.")
            key = "doc_" + hashlib.md5(text.encode()).hexdigest()[:10]   # refresh the editor when details change
            text = st.text_area("Your document (you can edit it)", ss.doc_edits.get(key, text), height=460, key=key)
            ss.doc_edits[key] = text
            b1, b2 = st.columns(2)
            try:
                from docx import Document
                doc = Document()
                for para in text.split("\n"):
                    doc.add_paragraph(para)
                buf = io.BytesIO()
                doc.save(buf)
                b1.download_button("📄 Download Word (.docx)", buf.getvalue(), f"nyay_{d.get('kind', 'document')}.docx",
                                   width="stretch", type="primary")
            except ImportError:
                pass
            b2.download_button("📝 Download text (.txt)", text, f"nyay_{d.get('kind', 'document')}.txt", width="stretch")
            how = ("Print it, sign it, and send it by **Registered Post AD or Speed Post**. Keep the postal receipt and a "
                   "copy. Also send a scan by email or WhatsApp if you can." if d.get("kind") == "legal_notice" else
                   "File it online at **e-Jagriti (e-jagriti.gov.in)** with an affidavit and copies of your proof. Keep "
                   "your complaint number safe.")
            st.markdown(f"**📮 How to send it:** {how}")
            st.caption("Drafted by an AI lawyer from your facts. Read every line before sending. If the other side has a "
                       "lawyer, or the amount is above ~₹5 lakh, get it checked by a human lawyer (free: 15100).")

# ---------------------------------------------------------------------- practise
elif view == VIEWS[3]:
    opp = OPPONENTS.get(state.get("issue") or "other", "the other side")
    st.markdown(f"**Rehearse the conversation with {opp}.** I'll argue back the way they usually do, and coach you "
                "after each reply, like your lawyer would.")
    for m in ss.practise:
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🎭"):
            st.markdown(m["content"])
    c1, c2 = st.columns(2)
    want_feedback = c1.button("🧑‍🏫 Stop and give me feedback", width="stretch", disabled=not ss.practise)
    if c2.button("🔄 Restart practice", width="stretch", disabled=not ss.practise):
        ss.practise = []
        st.rerun()
    p = st.chat_input("What would you say to them?", key="practise_input")
    p = p or ("feedback" if want_feedback else None)
    if p:
        with st.spinner("They're thinking…"):
            try:
                bot.practise(state, ss.practise, p, opp)
            except Exception as e:
                st.error(friendly_error(e))
        st.rerun()

st.markdown('<div class="ns-foot">Nyay Saathi is an AI lawyer, not an enrolled advocate. It gives legal guidance based '
            'on verified Indian law (as of 7 Nov 2026) and tells you when you need a human lawyer. Free legal aid: NALSA '
            '<b>15100</b> · <a href="https://github.com/gauravtr/Kuku_230414_IITK" target="_blank">Source code</a></div>',
            unsafe_allow_html=True)
