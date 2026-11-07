"""Nyay Saathi - Streamlit UI.   Run:  streamlit run app.py"""
import io
import json
import os

import streamlit as st

# Streamlit Cloud / HF Spaces secrets -> env (so nyay/llm.py stays framework-free)
try:
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ.setdefault(k, v)
except Exception:
    pass

from nyay.engine import NyaySaathi, new_state  # noqa: E402
from nyay.llm import LLM  # noqa: E402

st.set_page_config(page_title="Nyay Saathi - free legal helper", page_icon="⚖️", layout="wide")

LANGS = {"Auto (reply in my language)": "auto", "English": "English", "हिंदी (Hindi)": "Hindi in Devanagari script",
         "Hinglish": "Hinglish (Hindi in Latin script)", "தமிழ் (Tamil)": "Tamil", "বাংলা (Bengali)": "Bengali",
         "मराठी (Marathi)": "Marathi", "తెలుగు (Telugu)": "Telugu", "ಕನ್ನಡ (Kannada)": "Kannada"}
OPPONENTS = {"deposit": "the landlord", "consumer": "the company's customer-care manager",
             "salary": "the employer's HR manager", "cheque": "the person who gave the cheque", "other": "the other side"}

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("⚖️ Nyay Saathi")
    st.caption("Free help with everyday legal problems in India. Not a lawyer — it tells you when you need one.")
    lang_label = st.selectbox("Language", list(LANGS))
    available = [p for p, k in [("gemini", "GEMINI_API_KEY"), ("groq", "GROQ_API_KEY"), ("openai", "OPENAI_API_KEY"),
                                ("openrouter", "OPENROUTER_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")] if os.getenv(k)]
    default_p = os.getenv("NYAY_PROVIDER", available[0] if available else "gemini")
    with st.expander("Model (swap any time)"):
        provider = st.selectbox("Provider", sorted(set(available + [default_p, "ollama"])),
                                index=sorted(set(available + [default_p, "ollama"])).index(default_p))
        model = st.text_input("Model name (blank = default)", os.getenv("NYAY_MODEL", ""))
    st.markdown("**Covers in depth:** deposit not returned · refund / defective product · unpaid salary · cheque bounce.  \n"
                "**Anything else:** honest pointer to free legal aid.")
    st.markdown("**Free lawyer:** NALSA **15100** · Consumer helpline **1915** · Cyber fraud **1930** · Emergency **112**")
    if st.button("🗑️ Start a new case"):
        for k in ("state", "chat", "practise", "draft"):
            st.session_state.pop(k, None)
        st.rerun()

if "state" not in st.session_state:
    st.session_state.state = new_state()
    st.session_state.chat = []          # what the UI shows
    st.session_state.practise = []
state = st.session_state.state
state["language"] = LANGS[lang_label]
bot = NyaySaathi(LLM(provider, model or None))

if not available and provider != "ollama":
    st.warning("No API key found. Add a free GEMINI_API_KEY (aistudio.google.com) or GROQ_API_KEY in Settings → Secrets.")

tab_talk, tab_case, tab_draft, tab_practise = st.tabs(["💬 Talk", "📁 My case file", "📝 Prepare a document", "🥊 Practise"])

# ---------------------------------------------------------------------- talk
with tab_talk:
    if not st.session_state.chat:
        st.info("Tell me what happened, in your own words and language. Example: *“Landlord ne 2 mahine se ₹40,000 deposit "
                "wapas nahi kiya, painting ka paisa kaat raha hai.”*  Don't share Aadhaar/bank numbers.")
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    voice_text = None
    if hasattr(st, "audio_input"):
        audio = st.audio_input("🎤 Or speak (any Indian language)")
        if audio is not None and st.session_state.get("last_audio") != audio.getvalue()[:64]:
            st.session_state.last_audio = audio.getvalue()[:64]
            try:
                voice_text = bot.llm.transcribe(audio.getvalue(), audio.type or "audio/wav")
                st.caption(f"Heard: {voice_text}")
            except Exception as e:
                st.error(f"Voice failed: {e}")
    typed = st.chat_input("Type your problem…")
    user_text = typed or voice_text
    if user_text:
        st.session_state.chat.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    r = bot.turn(state, user_text)
                    msg = r["reply"]
                    if r["needs_lawyer"]:
                        msg += f"\n\n👩‍⚖️ **You should talk to a lawyer** {('— ' + r['lawyer_reason']) if r['lawyer_reason'] else ''}. Free legal aid: **15100**."
                    if r["ready_to_draft"] in ("legal_notice", "consumer_complaint"):
                        msg += "\n\n📝 I can draft this for you — open the **Prepare a document** tab."
                except Exception as e:
                    msg = f"Sorry, something went wrong talking to the model ({e}). Please try again."
            st.markdown(msg)
        st.session_state.chat.append({"role": "assistant", "content": msg})

# ----------------------------------------------------------------- case file
with tab_case:
    case = state.get("case") or {}
    if not case:
        st.write("Your case file will build up here as you talk.")
    else:
        st.subheader(case.get("summary", "Your case"))
        c1, c2 = st.columns(2)
        c1.markdown(f"**Problem type:** {state.get('issue')}  \n**Place:** {case.get('place', '?')}  \n"
                    f"**Amount at stake:** {case.get('amount_at_stake', '?')}  \n**You want:** {case.get('what_user_wants', '?')}")
        c2.markdown("**Deadlines**\n" + "\n".join(f"- ⏰ {d}" for d in case.get("deadlines", [])) or "-")
        st.markdown("**Timeline**")
        st.table(case.get("timeline", []))
        c3, c4 = st.columns(2)
        c3.markdown("**✅ Proof you have**\n" + "\n".join(f"- {p}" for p in case.get("proof_have", [])))
        c4.markdown("**❗ Proof to collect**\n" + "\n".join(f"- {p}" for p in case.get("proof_missing", [])))
        st.download_button("Download case file (JSON)", json.dumps(case, ensure_ascii=False, indent=2), "case_file.json")

# --------------------------------------------------------------------- draft
with tab_draft:
    if not state.get("case"):
        st.write("Talk to me first so I know the facts.")
    else:
        kind = st.radio("Document", ["legal_notice", "consumer_complaint"],
                        format_func=lambda k: {"legal_notice": "Legal notice / demand notice",
                                               "consumer_complaint": "Consumer complaint (District Commission)"}[k])
        if st.button("Draft it"):
            with st.spinner("Drafting…"):
                st.session_state.draft = bot.draft(state, kind)
        d = st.session_state.get("draft")
        if d:
            if d["blanks"]:
                st.warning("Fill these blanks before sending: " + ", ".join(d["blanks"]))
            if d["user_note"]:
                st.info(d["user_note"])
            text = st.text_area("Your document (you can edit it here)", d["document"], height=480)
            st.download_button("Download .txt", text, "nyay_saathi_document.txt")
            try:
                from docx import Document
                doc = Document()
                for para in text.split("\n"):
                    doc.add_paragraph(para)
                buf = io.BytesIO()
                doc.save(buf)
                st.download_button("Download Word (.docx)", buf.getvalue(), "nyay_saathi_document.docx")
            except ImportError:
                pass
            st.caption("Drafted by AI from your facts. Read every line. For amounts above ~₹5 lakh or if the other side "
                       "has a lawyer, get it checked (free: 15100).")

# ------------------------------------------------------------------ practise
with tab_practise:
    opp = OPPONENTS.get(state.get("issue") or "other", "the other side")
    st.write(f"Practise the conversation with **{opp}**. I'll push back like they would, and coach you after each turn. "
             "Type *feedback* to stop and get tips.")
    for m in st.session_state.practise:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    p = st.chat_input("Say what you'd say to them…", key="practise_input")
    if p:
        r = bot.practise(state, st.session_state.practise, p, opp)
        st.rerun()
