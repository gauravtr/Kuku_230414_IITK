# ⚖️ Nyay Saathi: an AI lawyer for everyday problems in India

**Live app:** https://nyay-saathi-kuku.streamlit.app

Talk to it by text or voice, in Hindi, Hinglish, Tamil, English or any Indian language, about:

| Covered in depth | What it does |
|---|---|
| Security deposit not returned | builds the case file, explains wear-and-tear vs damage, drafts a legal notice |
| Refund / defective product (online or offline) | grievance officer → 1915 → e-Jagriti route, drafts a District Commission complaint |
| Salary / wages not paid | Code on Wages deadlines (in force since 21 Nov 2025), Labour Department claim |
| Cheque bounce (either side) | explains the 15-day / 1-month clocks, urgent lawyer referral |

For anything else (criminal, family, property) it says honestly that it doesn't cover it and points to **free legal aid (NALSA 15100)**.

## How it works like a lawyer, and when it hands you to a human one
Each answer is laid out like a lawyer's written opinion: **bottom line** and case strength, the reasoning, an **action plan** with timing, deadlines, the proof you have and still need, the rulings that fit, and the law relied on. Behind it: the facts, a **legal opinion** (case strength: strong / moderate / weak / unclear, and why),
a **step-by-step plan** with deadlines, and the **paperwork** (legal notice, consumer complaint). The plan becomes a tickable
checklist in the case file.

It says **"get a human lawyer"** clearly, and code (`decide_escalation` in `nyay/engine.py`) has the final say, not only the model:
- **urgent:** police, violence, self-harm, fraud or family-property keywords, or the model marks it urgent (deadline very close);
- **consult:** the facts are still ambiguous after it has asked; the amount is over ~Rs 5 lakh; the problem is outside the
  verified law cards; or the model finds the other side has a lawyer, a case was filed, or a court filing is needed.

When that happens, the case file offers a one-page **case brief for a lawyer** (Word/text, built by code from the case file, with
no model call) to take to free legal aid (NALSA 15100). It never claims to be an enrolled advocate.

## How it avoids made-up law
1. **The model only sees verified law cards** (`kb/laws.json`, 38 cards, each with a source and a verified date), picked by code from keywords, and must tag every legal claim with a card ID.
2. **A code guard (`nyay/guard.py`) checks every answer before the user sees it**: any section, act, constitutional article or court case that isn't on a card is marked `⚠️[unverified]` with a warning. Old IPC/CrPC numbers are flagged. Offline tests: `python -m pytest tests`. The same guard also checks the opinion line and plan steps; any with unverified law are dropped.
3. **Supreme Court rulings only when they fit.** `kb/judgments.json` holds 26 verified rulings, each with the fact pattern it fits. Code shows a ruling (and lets the model or a draft cite it) only when that pattern appears in the client's own facts, and shows the client's words as the reason. Rulings against the client that fit are always shown; if none fits, none is shown.
4. **Safety is code, not prompt**: police/violence/self-harm/fraud keywords force a "talk to a lawyer / call 112, 15100, 1930, 14416" block even if the model forgets.

## Run it
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...        # free key: https://aistudio.google.com  (or GROQ_API_KEY)
streamlit run app.py
```
**Deploy free:** push this folder to GitHub → share.streamlit.io → New app → `app.py` → Settings → Secrets: paste `.streamlit/secrets.toml.example` with your key.

## Swap the model (one line)
```bash
NYAY_PROVIDER=groq      NYAY_MODEL=llama-3.3-70b-versatile   streamlit run app.py
NYAY_PROVIDER=anthropic NYAY_MODEL=claude-sonnet-5-5         streamlit run app.py
NYAY_PROVIDER=openai    NYAY_MODEL=gpt-4o-mini               streamlit run app.py
NYAY_PROVIDER=ollama    NYAY_MODEL=llama3.1                   streamlit run app.py   # fully local
NYAY_BASE_URL=https://your-gateway/v1 NYAY_PROVIDER=openai NYAY_MODEL=<model>     # any OpenAI-compatible API
```
No SDKs: every provider is a plain HTTP call in `nyay/llm.py`.

## Test cases and their outputs
**[`outputs/`](outputs/summary.md) holds 14 full consultations recorded from the live app** (Gemini, 8 November 2026) through
its normal chat and Documents screens, unedited: the client's story, the AI lawyer's questions and the answers, the opinion and
plan on every turn, the Supreme Court rulings that fit, then the drafts with their code checks. 58 client turns, 14 drafts.
They cover Hindi, Hinglish and Tamil; deposit, consumer, salary, cheque, threats and domestic-violence matters; a request for a
made-up judgment, a request to forge receipts, an outdated IPC 420 question, a husband named in a dowry FIR, a one-line vague
start, a time-barred complaint, and a rehearsed phone call with a coach.
[`outputs/REVIEW.md`](outputs/REVIEW.md) is a human review of those transcripts: what works, what is still wrong, and the
bugs these runs found that were then fixed in code (each with a regression test).

To replay the same scripts (`tests/cases.json`) with your own key:
```bash
python run_tests.py --provider gemini        # writes outputs/<case>.md, summary.md, summary.json
```

## Layout
```
app.py              Streamlit UI: Consultation · Case file · Documents · Practise
nyay/engine.py      routing → model (JSON) → guard → safety
nyay/guard.py       citation guard (pure code)         nyay/brief.py  case brief for a human lawyer (pure code)
nyay/kb.py          loads cards/playbooks, keyword routing, red flags
nyay/llm.py         provider-agnostic model layer + cache + voice transcription
nyay/prompts.py     all prompts and document templates
kb/laws.json        verified law cards       kb/playbooks.json  facts to collect, proof, escalation ladder, red flags
run_tests.py        end-to-end runner + auto-checks          tests/  cases + guard unit tests
```

*An AI lawyer, not an enrolled advocate. Law verified as of 7 Nov 2026; check `kb/laws.json` sources before relying on it.*
