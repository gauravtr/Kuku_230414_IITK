"""Nyay Saathi - Streamlit UI.   Run:  streamlit run app.py"""
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

from nyay.engine import NyaySaathi, new_state  # noqa: E402
from nyay.llm import LLM  # noqa: E402

st.set_page_config(page_title="Nyay Saathi · Free legal help for India", page_icon="⚖️", layout="wide",
                   menu_items={"About": "Nyay Saathi: free, multilingual help with everyday legal problems in India. "
                                        "Not a lawyer; it tells you when you need one. Free legal aid: NALSA 15100."})

st.markdown("""<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.6rem; max-width: 1100px;}
.ns-hero {background: linear-gradient(135deg,#1E3A8A 0%,#3B5BDB 100%); color:#fff; border-radius:16px;
          padding:22px 26px; margin-bottom:14px;}
.ns-hero h1 {color:#fff; font-size:1.9rem; margin:0 0 4px 0;}
.ns-hero p {color:#E0E7FF; margin:0; font-size:1.02rem;}
.ns-chips {margin-top:12px;}
.ns-chip {display:inline-block; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.28);
          color:#fff; border-radius:999px; padding:3px 11px; margin:3px 6px 0 0; font-size:.82rem;}
.ns-foot {color:#6B7280; font-size:.8rem; text-align:center; margin-top:28px; border-top:1px solid #E5E7EB; padding-top:10px;}
.ns-help {background:#F3F5FA; border-radius:10px; padding:10px 12px; font-size:.9rem;}
div[data-testid="stChatMessage"] {border-radius:12px;}
</style>""", unsafe_allow_html=True)

LANGS = {"Auto (reply in my language)": "auto", "English": "English", "हिंदी (Hindi)": "Hindi in Devanagari script",
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

# ------------------------------------------------------------------ state
if "state" not in st.session_state:
    st.session_state.state = new_state()
    st.session_state.chat = []
    st.session_state.practise = []
state = st.session_state.state

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("### ⚖️ Nyay Saathi")
    st.caption("Free help with everyday legal problems in India.")
    lang_label = st.selectbox("Reply language", list(LANGS))
    st.markdown("**How it works**")
    st.markdown("1. Tell your problem, in any language\n2. Get your rights, options and deadlines\n"
                "3. Download a ready legal notice or complaint\n4. Practise the hard conversation")
    st.markdown('<div class="ns-help"><b>Free helplines</b><br>⚖️ Free lawyer (NALSA): <b>15100</b><br>'
                '🛒 Consumer helpline: <b>1915</b><br>💳 Cyber fraud: <b>1930</b><br>🚨 Emergency: <b>112</b></div>',
                unsafe_allow_html=True)
    st.write("")
    if st.button("🗑️ Start a new case", width="stretch"):
        for k in ("state", "chat", "practise", "draft", "pending"):
            st.session_state.pop(k, None)
        st.rerun()
    available = [p for p, k in [("gemini", "GEMINI_API_KEY"), ("groq", "GROQ_API_KEY"), ("openai", "OPENAI_API_KEY"),
                                ("openrouter", "OPENROUTER_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")] if os.getenv(k)]
    default_p = os.getenv("NYAY_PROVIDER", available[0] if available else "gemini")
    options = sorted(set(available + [default_p]))
    with st.expander("⚙️ Advanced: AI model"):
        provider = st.selectbox("Provider", options, index=options.index(default_p))
        model = st.text_input("Model (blank = default)", os.getenv("NYAY_MODEL", ""))
        st.caption("Any provider works: Gemini, Groq, OpenAI, Anthropic or Ollama. Law checks stay the same.")

state["language"] = LANGS[lang_label]
if "llm" not in st.session_state or st.session_state.get("llm_cfg") != (provider, model):
    st.session_state.llm = LLM(provider, model or None)       # kept per session: remembers a working fallback model
    st.session_state.llm_cfg = (provider, model)
bot = NyaySaathi(st.session_state.llm)

# ------------------------------------------------------------------ hero
st.markdown("""<div class="ns-hero"><h1>⚖️ Nyay Saathi</h1>
<p>Your free legal companion for everyday problems. Explained simply, in your language.</p>
<div class="ns-chips"><span class="ns-chip">✅ Only verified Indian law</span><span class="ns-chip">🗣️ Hindi · English · Tamil · 10+ languages</span>
<span class="ns-chip">📝 Drafts notices &amp; complaints</span><span class="ns-chip">👩‍⚖️ Tells you when you need a lawyer</span></div></div>""",
            unsafe_allow_html=True)

if not available:
    st.error("The AI service isn't configured yet. The owner needs to add a free GEMINI_API_KEY in Settings → Secrets.")


def friendly_error(e: Exception) -> str:
    return ("Sorry, the AI service is busy or unavailable right now. Please try again in a minute. "
            "If it's urgent, call the free legal aid helpline **15100**.")


tab_talk, tab_case, tab_draft, tab_practise = st.tabs(["💬 Talk", "📁 My case file", "📝 Prepare a document", "🥊 Practise"])

# ---------------------------------------------------------------------- talk
with tab_talk:
    if not st.session_state.chat:
        st.markdown("##### What's the problem? Type or speak in your own words, or try an example:")
        cols = st.columns(len(EXAMPLES))
        for col, (label, text) in zip(cols, EXAMPLES):
            if col.button(label, width="stretch"):
                st.session_state.pending = text
        st.caption("🔒 Don't share Aadhaar, bank or card numbers. Nyay Saathi is not a lawyer and does not replace one.")
    for m in st.session_state.chat:
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "⚖️"):
            st.markdown(m["content"])
            for kind, note in m.get("notes", []):
                (st.warning if kind == "lawyer" else st.info)(note)

    voice_text = None
    if hasattr(st, "audio_input"):
        audio = st.audio_input("🎤 Or speak your problem (any Indian language)")
        if audio is not None and st.session_state.get("last_audio") != audio.getvalue()[:64]:
            st.session_state.last_audio = audio.getvalue()[:64]
            try:
                with st.spinner("Listening…"):
                    voice_text = bot.llm.transcribe(audio.getvalue(), audio.type or "audio/wav")
            except Exception:
                st.error("Sorry, I couldn't understand the recording. Please try again or type your problem.")
    typed = st.chat_input("Describe your problem… (e.g. landlord not returning deposit)")
    user_text = typed or voice_text or st.session_state.pop("pending", None)
    if user_text:
        st.session_state.chat.append({"role": "user", "content": user_text})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_text)
        notes = []
        with st.chat_message("assistant", avatar="⚖️"):
            with st.spinner("Checking the law for your situation…"):
                try:
                    r = bot.turn(state, user_text)
                    msg = r["reply"]
                    if r["needs_lawyer"]:
                        reason = f" ({r['lawyer_reason']})" if r["lawyer_reason"] else ""
                        notes.append(("lawyer", f"👩‍⚖️ **Talk to a lawyer about this{reason}.** Free legal aid: call **15100**."))
                    if r["ready_to_draft"] in ("legal_notice", "consumer_complaint"):
                        notes.append(("info", "📝 I can draft this document for you. Open the **Prepare a document** tab."))
                except Exception as e:
                    msg = friendly_error(e)
            st.markdown(msg)
            for kind, note in notes:
                (st.warning if kind == "lawyer" else st.info)(note)
        st.session_state.chat.append({"role": "assistant", "content": msg, "notes": notes})
        st.rerun()

# ----------------------------------------------------------------- case file
with tab_case:
    case = state.get("case") or {}
    if not case:
        st.info("Your case file builds up automatically as you talk: facts, timeline, proof and deadlines.")
    else:
        st.subheader(case.get("summary", "Your case"))
        m1, m2, m3 = st.columns(3)
        m1.metric("Problem type", (state.get("issue") or "-").title())
        m2.metric("Amount at stake", case.get("amount_at_stake") or "-")
        m3.metric("Place", case.get("place") or "-")
        for d in case.get("deadlines", []):
            st.warning(f"⏰ {d}")
        if case.get("timeline"):
            st.markdown("**Timeline**")
            st.dataframe(case["timeline"], width="stretch", hide_index=True)
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**✅ Proof you have**")
            st.markdown("\n".join(f"- {p}" for p in case.get("proof_have", [])) or "_Nothing yet_")
        with c4:
            st.markdown("**📌 Proof to collect**")
            st.markdown("\n".join(f"- {p}" for p in case.get("proof_missing", [])) or "_Nothing pending_")
        st.download_button("⬇️ Download case file", json.dumps(case, ensure_ascii=False, indent=2), "nyay_saathi_case.json")

# --------------------------------------------------------------------- draft
with tab_draft:
    if not state.get("case"):
        st.info("Tell me about your problem in the **Talk** tab first, so I can draft from your facts.")
    else:
        kind = st.radio("Which document?", ["legal_notice", "consumer_complaint"], horizontal=True,
                        format_func=lambda k: {"legal_notice": "Legal notice / demand notice",
                                               "consumer_complaint": "Consumer complaint (District Commission)"}[k])
        if st.button("✍️ Draft it for me", type="primary"):
            with st.spinner("Drafting from your case file…"):
                try:
                    st.session_state.draft = bot.draft(state, kind)
                except Exception as e:
                    st.error(friendly_error(e))
        d = st.session_state.get("draft")
        if d:
            if d["blanks"]:
                st.warning("Fill these blanks before sending: " + ", ".join(d["blanks"]))
            if d["user_note"]:
                st.info(d["user_note"])
            text = st.text_area("Your document (edit it here)", d["document"], height=480)
            b1, b2 = st.columns(2)
            b1.download_button("⬇️ Download .txt", text, "nyay_saathi_document.txt", width="stretch")
            try:
                from docx import Document
                doc = Document()
                for para in text.split("\n"):
                    doc.add_paragraph(para)
                buf = io.BytesIO()
                doc.save(buf)
                b2.download_button("⬇️ Download Word (.docx)", buf.getvalue(), "nyay_saathi_document.docx",
                                   width="stretch")
            except ImportError:
                pass
            st.caption("Drafted by AI from your facts. Read every line before sending. For amounts above ~₹5 lakh, or if "
                       "the other side has a lawyer, get it checked (free: 15100).")

# ------------------------------------------------------------------ practise
with tab_practise:
    opp = OPPONENTS.get(state.get("issue") or "other", "the other side")
    st.markdown(f"Practise the conversation with **{opp}**. I'll push back like they would and coach you after each turn. "
                "Type **feedback** to stop and get tips.")
    for m in st.session_state.practise:
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🎭"):
            st.markdown(m["content"])
    p = st.chat_input("What would you say to them?", key="practise_input")
    if p:
        try:
            bot.practise(state, st.session_state.practise, p, opp)
        except Exception as e:
            st.error(friendly_error(e))
        st.rerun()

st.markdown('<div class="ns-foot">Nyay Saathi gives legal information, not legal advice, and is not a substitute for a lawyer. '
            'Law verified as of 7 Nov 2026. Free legal aid: NALSA <b>15100</b> · '
            '<a href="https://github.com/gauravtr/Kuku_230414_IITK" target="_blank">Source code</a></div>',
            unsafe_allow_html=True)
