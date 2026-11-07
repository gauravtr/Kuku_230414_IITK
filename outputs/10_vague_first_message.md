# 10_vague_first_message
_Very little information; should ask the few key questions, not lecture_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"must_include_any": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
company not giving my money back. what to do

### ⚖️ Nyay Saathi
I can help. To point you the right way, I need a little more:

1. **What is the money for?** A refund for something you bought or booked, salary they owe you, a deposit, or something else?
2. **How much, and since when?**
3. **Which company, and which city/state are you in?**
4. **What proof do you have?** (bill/order ID, offer letter, emails, chats)

Meanwhile, one thing helps in every route: ask the company **in writing** (email or chat) for the money, with a date, and save their reply.

If it turns out to be unpaid salary, employers must pay monthly wages before the 7th of the next month [1]. If you can't afford help, free legal aid is available through NALSA 15100 [2].

**Sources (checked):** [1] Deadline to pay wages (Code on Wages, s.17) — https://www.advocatekhoj.com/library/bareacts/codeonwages/17.php; [2] Free legal aid (Legal Services Authorities Act, 1987, s.12) — https://nalsa.gov.in/

`routed_issue=salary  model_issue=other  needs_lawyer=False  red_flags=[]  ready_to_draft=none  cards_given=7`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "en",
 "issue": "other",
 "case_file": {
  "summary": "User says a company is not giving their money back; no details yet",
  "people": {
   "user": "unknown",
   "other_side": "a company"
  },
  "place": "unknown",
  "amount_at_stake": "unknown",
  "timeline": [],
  "proof_have": [],
  "proof_missing": [
   "what the money is for",
   "amount and date",
   "company name",
   "documents"
  ],
  "deadlines": [],
  "what_user_wants": "money back"
 },
 "reply": "I can help. To point you the right way, I need a little more:\n\n1. **What is the money for?** A refund for something you bought or booked, salary they owe you, a deposit, or something else?\n2. **How much, and since when?**\n3. **Which company, and which city/state are you in?**\n4. **What proof do you have?** (bill/order ID, offer letter, emails, chats)\n\nMeanwhile, one thing helps in every route: ask the company **in writing** (email or chat) for the money, with a date, and save their reply.\n\nIf it turns out to be unpaid salary, employers must pay monthly wages before the 7th of the next month [COW-17]. If you can't afford help, free legal aid is available through NALSA 15100 [GEN-LEGALAID].",
 "needs_lawyer": false,
 "lawyer_reason": "",
 "ready_to_draft": "none"
}
```
</details>

---
## Final case file
```json
{
  "summary": "User says a company is not giving their money back; no details yet",
  "people": {
    "user": "unknown",
    "other_side": "a company"
  },
  "place": "unknown",
  "amount_at_stake": "unknown",
  "timeline": [],
  "proof_have": [],
  "proof_missing": [
    "what the money is for",
    "amount and date",
    "company name",
    "documents"
  ],
  "deadlines": [],
  "what_user_wants": "money back"
}
```
