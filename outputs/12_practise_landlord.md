# 12_practise_landlord
_Practise mode: user rehearses asking the landlord for the deposit_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
My landlord in Delhi is holding my Rs 40,000 deposit since I vacated on 15 September 2026. He says the walls need repainting. I want to practise talking to him before I call.

### ⚖️ Nyay Saathi
Practising first is a smart move. Here's what to keep in your pocket for the call:

**Your strongest points:**
1. Repainting after normal use is usually **reasonable wear and tear**, which a tenant generally doesn't have to pay for [1] — unless your agreement clearly says otherwise.
2. If the agreement says the deposit is refundable, holding it back is a breach and you can claim it [2].
3. Your next steps are real: a legal notice, then free settlement at Lok Adalat [3] or a recovery case [4].

**Tips for the call:** stay polite, name the exact amount (₹40,000) and a date, ask him to list any deductions with bills, and follow up the call with a WhatsApp summary — that becomes your record.

Open the **🥊 Practise** tab — I'll play your landlord and push back the way landlords often do, and coach you after each turn.

Quick check: how long did you live there, and does your agreement say anything about painting?

**Sources (checked):** [1] Normal wear and tear (Transfer of Property Act, s.108(m)) — https://www.indiacode.nic.in/ (search: Transfer of Property Act, 1882); [2] Compensation for breach of contract (Indian Contract Act, s.73) — https://www.indiacode.nic.in/ (search: Indian Contract Act, 1872); [3] Lok Adalat / pre-litigation settlement (Legal Services Authorities Act, s.19) — https://nalsa.gov.in/; [4] Where to file for a deposit not returned — https://www.indiacode.nic.in/ (search: Code of Civil Procedure, 1908)

`routed_issue=deposit  model_issue=deposit  needs_lawyer=False  red_flags=[]  ready_to_draft=none  cards_given=8`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "en",
 "issue": "deposit",
 "case_file": {
  "summary": "Tenant in Delhi; landlord holding Rs 40,000 deposit since 15 Sep 2026 vacating, citing repainting; user wants to practise the conversation",
  "people": {
   "user": "tenant",
   "other_side": "landlord"
  },
  "place": "Delhi",
  "amount_at_stake": "Rs 40,000",
  "timeline": [
   {
    "date": "2026-09-15",
    "event": "Tenant vacated"
   },
   {
    "date": "after 2026-09-15",
    "event": "Landlord holding deposit, says walls need repainting"
   }
  ],
  "proof_have": [],
  "proof_missing": [
   "rent agreement",
   "deposit payment proof",
   "move-out photos",
   "how long the tenancy lasted"
  ],
  "deadlines": [
   "Civil recovery generally within 3 years [GEN-LIMIT]"
  ],
  "what_user_wants": "deposit back; practise the call first"
 },
 "reply": "Practising first is a smart move. Here's what to keep in your pocket for the call:\n\n**Your strongest points:**\n1. Repainting after normal use is usually **reasonable wear and tear**, which a tenant generally doesn't have to pay for [TEN-WEAR] — unless your agreement clearly says otherwise.\n2. If the agreement says the deposit is refundable, holding it back is a breach and you can claim it [TEN-CONTRACT].\n3. Your next steps are real: a legal notice, then free settlement at Lok Adalat [GEN-LOKADALAT] or a recovery case [TEN-FORUM].\n\n**Tips for the call:** stay polite, name the exact amount (₹40,000) and a date, ask him to list any deductions with bills, and follow up the call with a WhatsApp summary — that becomes your record.\n\nOpen the **🥊 Practise** tab — I'll play your landlord and push back the way landlords often do, and coach you after each turn.\n\nQuick check: how long did you live there, and does your agreement say anything about painting?",
 "needs_lawyer": false,
 "lawyer_reason": "",
 "ready_to_draft": "none"
}
```
</details>

---
### 🥊 Practise — user
Hello uncle, I vacated on 15 September. Please return my deposit of 40,000 this week.

### 🥊 the landlord (AI)
Arre beta, I know, I know. But the walls are in a bad state — there are marks everywhere and the new tenant won't take it like this. Painting will cost me at least 30-35 thousand. Let me get the work done first, then whatever is left I'll send you.

COACH: Good start — you gave the exact date and amount and a clear deadline. Next, ask him what *damage* there is beyond normal use: routine repainting after a long stay is usually reasonable wear and tear, which a tenant doesn't pay for [1]. Ask for an itemised list with bills.

---
### 🥊 Practise — user
Uncle, painting after 2 years is normal wear and tear, the tenant doesn't have to pay for it. If it's not returned by Friday I'll send a legal notice.

### 🥊 the landlord (AI)
Wear and tear, wear and tear... everyone says this now. Two years you stayed, the walls are dirty, nail holes everywhere. And don't threaten me with notices, beta — I have known your family's broker for years. Okay, I'll give you 20,000 now, the rest after painting, final.

COACH: You stayed calm and gave a deadline — good. Don't accept a part payment as 'final' on the phone. Ask him to put any deduction in writing with bills; nail holes and dirt from normal living are usually reasonable wear and tear [1], and if your agreement says the deposit is refundable, holding it is a breach [2]. You can take ₹20,000 now *without* giving up the rest — say that clearly, then send a WhatsApp summary.

---
## Final case file
```json
{
  "summary": "Tenant in Delhi; landlord holding Rs 40,000 deposit since 15 Sep 2026 vacating, citing repainting; user wants to practise the conversation",
  "people": {
    "user": "tenant",
    "other_side": "landlord"
  },
  "place": "Delhi",
  "amount_at_stake": "Rs 40,000",
  "timeline": [
    {
      "date": "2026-09-15",
      "event": "Tenant vacated"
    },
    {
      "date": "after 2026-09-15",
      "event": "Landlord holding deposit, says walls need repainting"
    }
  ],
  "proof_have": [],
  "proof_missing": [
    "rent agreement",
    "deposit payment proof",
    "move-out photos",
    "how long the tenancy lasted"
  ],
  "deadlines": [
    "Civil recovery generally within 3 years [GEN-LIMIT]"
  ],
  "what_user_wants": "deposit back; practise the call first"
}
```
