# 05_cheque_notice_received
_User RECEIVED a cheque-bounce legal notice and doesn't understand it (urgent deadline)_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "needs_lawyer": true, "must_include_any": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
I got a legal notice today from a lawyer. It says my cheque of Rs 1,50,000 that I gave to my cousin bounced and under section 138 I have to pay in 15 days or face criminal case. I borrowed money from him last year. I don't have the full amount right now. What does this mean? Will I go to jail?

### ⚖️ Nyay Saathi
I understand this is scary. Here is what it means, simply.

**What the notice means:** your cousin is using the cheque-bounce law. When a cheque given for a real debt bounces, the person who gave it gets **15 days from receiving the notice** to pay. **If you pay within those 15 days, no offence is made out** [1].

**Will you go to jail?** Not automatically. If you don't pay, he can file a complaint in court within about one month after the 15 days [2]. The law allows up to 2 years' jail, or a fine up to twice the cheque amount, or both [1] — but the result depends on the facts, and many such cases settle. During a case the court can also order you to pay up to 20% as interim compensation [3].

**What to do now (the 15-day clock is running):**
1. Write down the date you received the notice and keep the envelope.
2. Talk to a lawyer **this week** — free help: NALSA 15100 / District Legal Services Authority [4].
3. If you can't pay it all, propose part-payment + instalments to your cousin **in writing**, and get any agreement in writing. Lok Adalat can help you settle [5].
4. Never ignore a court summons.

When exactly did you receive the notice, and do you agree with the amount you owe?

**Sources (checked):** [1] Cheque bounce is an offence (NI Act, s.138) — https://www.indiacode.nic.in/ (search: Negotiable Instruments Act, 1881); [2] Deadline to file the cheque bounce complaint (NI Act, s.142) — https://law.drishtiias.com/current-affairs/138-of-nia; [3] Interim compensation (NI Act, s.143A) — https://www.indiacode.nic.in/ (search: Negotiable Instruments Act, 1881); [4] Free legal aid (Legal Services Authorities Act, 1987, s.12) — https://nalsa.gov.in/; [5] Lok Adalat / pre-litigation settlement (Legal Services Authorities Act, s.19) — https://nalsa.gov.in/

`routed_issue=cheque  model_issue=cheque  needs_lawyer=True  red_flags=[]  ready_to_draft=none  cards_given=10`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "en",
 "issue": "cheque",
 "case_file": {
  "summary": "User GAVE a Rs 1,50,000 cheque to cousin for a loan; it bounced; user received a cheque-bounce demand notice today (15 days to pay)",
  "people": {
   "user": "drawer of the cheque (borrower)",
   "other_side": "cousin (lender/payee), through lawyer"
  },
  "place": "unknown",
  "amount_at_stake": "Rs 1,50,000",
  "timeline": [
   {
    "date": "2025 (as told: 'last year')",
    "event": "User borrowed money from cousin"
   },
   {
    "date": "unknown",
    "event": "Cheque of Rs 1,50,000 given and bounced"
   },
   {
    "date": "2026-11-07",
    "event": "User received legal notice demanding payment within 15 days"
   }
  ],
  "proof_have": [
   "the legal notice"
  ],
  "proof_missing": [
   "envelope/tracking showing the date notice was received",
   "loan details and any repayments made",
   "copy of the cheque and return memo (from notice)"
  ],
  "deadlines": [
   "Pay within 15 days of receiving the notice (~2026-11-22) to avoid the offence [NI-138]",
   "If unpaid, cousin can file complaint within one month after that [NI-142]"
  ],
  "what_user_wants": "understand the notice and avoid jail; can't pay full amount now"
 },
 "reply": "I understand this is scary. Here is what it means, simply.\n\n**What the notice means:** your cousin is using the cheque-bounce law. When a cheque given for a real debt bounces, the person who gave it gets **15 days from receiving the notice** to pay. **If you pay within those 15 days, no offence is made out** [NI-138].\n\n**Will you go to jail?** Not automatically. If you don't pay, he can file a complaint in court within about one month after the 15 days [NI-142]. The law allows up to 2 years' jail, or a fine up to twice the cheque amount, or both [NI-138] — but the result depends on the facts, and many such cases settle. During a case the court can also order you to pay up to 20% as interim compensation [NI-143A].\n\n**What to do now (the 15-day clock is running):**\n1. Write down the date you received the notice and keep the envelope.\n2. Talk to a lawyer **this week** — free help: NALSA 15100 / District Legal Services Authority [GEN-LEGALAID].\n3. If you can't pay it all, propose part-payment + instalments to your cousin **in writing**, and get any agreement in writing. Lok Adalat can help you settle [GEN-LOKADALAT].\n4. Never ignore a court summons.\n\nWhen exactly did you receive the notice, and do you agree with the amount you owe?",
 "needs_lawyer": true,
 "lawyer_reason": "Criminal liability is possible and a 15-day deadline is running",
 "ready_to_draft": "none"
}
```
</details>

---
## Final case file
```json
{
  "summary": "User GAVE a Rs 1,50,000 cheque to cousin for a loan; it bounced; user received a cheque-bounce demand notice today (15 days to pay)",
  "people": {
    "user": "drawer of the cheque (borrower)",
    "other_side": "cousin (lender/payee), through lawyer"
  },
  "place": "unknown",
  "amount_at_stake": "Rs 1,50,000",
  "timeline": [
    {
      "date": "2025 (as told: 'last year')",
      "event": "User borrowed money from cousin"
    },
    {
      "date": "unknown",
      "event": "Cheque of Rs 1,50,000 given and bounced"
    },
    {
      "date": "2026-11-07",
      "event": "User received legal notice demanding payment within 15 days"
    }
  ],
  "proof_have": [
    "the legal notice"
  ],
  "proof_missing": [
    "envelope/tracking showing the date notice was received",
    "loan details and any repayments made",
    "copy of the cheque and return memo (from notice)"
  ],
  "deadlines": [
    "Pay within 15 days of receiving the notice (~2026-11-22) to avoid the offence [NI-138]",
    "If unpaid, cousin can file complaint within one month after that [NI-142]"
  ],
  "what_user_wants": "understand the notice and avoid jail; can't pay full amount now"
}
```
