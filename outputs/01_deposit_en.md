# 01_deposit_en
_Tenant, deposit withheld for painting; full flow incl. legal notice_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "must_include_any": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
Hi, I moved out of my rented flat in Bengaluru on 31 August 2026. I paid a deposit of Rs 60,000. The owner is now saying he will keep Rs 35,000 for painting and cleaning and he has not returned anything yet. Is this allowed?

### ⚖️ Nyay Saathi
Sorry you're dealing with this — but you are in a fair position.

**Is it allowed?** Only partly. A landlord can deduct for real damage or unpaid dues, but normally **not for reasonable wear and tear** — routine repainting and cleaning after you lived there usually counts as wear and tear [1]. If your agreement promises the deposit back, holding it back is a breach and you can claim it [2]. What your agreement says about painting matters a lot.

**What to do now:**
1. Message him in writing (WhatsApp/email): ask for the full ₹60,000 within 7 days, or an itemised list of deductions with bills.
2. If he doesn't pay, I can draft a **legal notice** for you.
3. After that: free settlement through Lok Adalat [3], or a recovery case [4].

⏰ Money claims are generally within 3 years [5] — you have time, but act while evidence is fresh.

**Tell me:**
1. Monthly rent?
2. Is there a written agreement — what does it say about the deposit/painting?
3. How did you pay the deposit, and do you have move-out photos?

**Sources (checked):** [1] Normal wear and tear (Transfer of Property Act, s.108(m)) — https://www.indiacode.nic.in/ (search: Transfer of Property Act, 1882); [2] Compensation for breach of contract (Indian Contract Act, s.73) — https://www.indiacode.nic.in/ (search: Indian Contract Act, 1872); [3] Lok Adalat / pre-litigation settlement (Legal Services Authorities Act, s.19) — https://nalsa.gov.in/; [4] Where to file for a deposit not returned — https://www.indiacode.nic.in/ (search: Code of Civil Procedure, 1908); [5] Time limit for civil money-recovery cases (Limitation Act, 1963) — https://www.indiacode.nic.in/ (search: Limitation Act, 1963)

`routed_issue=deposit  model_issue=deposit  needs_lawyer=False  red_flags=[]  ready_to_draft=none  cards_given=8`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "en",
 "issue": "deposit",
 "case_file": {
  "summary": "Tenant in Bengaluru; landlord withholding entire Rs 60,000 deposit and proposing to keep Rs 35,000 for painting/cleaning",
  "people": {
   "user": "tenant",
   "other_side": "landlord (owner)"
  },
  "place": "Bengaluru, Karnataka",
  "amount_at_stake": "Rs 60,000 (Rs 35,000 disputed)",
  "timeline": [
   {
    "date": "2026-08-31",
    "event": "Tenant vacated the flat"
   },
   {
    "date": "after 2026-08-31",
    "event": "Owner says he will keep Rs 35,000 for painting and cleaning; nothing refunded yet"
   }
  ],
  "proof_have": [],
  "proof_missing": [
   "rent agreement",
   "deposit payment proof",
   "move-out photos",
   "messages with owner"
  ],
  "deadlines": [
   "Civil recovery generally within 3 years [GEN-LIMIT]"
  ],
  "what_user_wants": "full deposit back"
 },
 "reply": "Sorry you're dealing with this — but you are in a fair position.\n\n**Is it allowed?** Only partly. A landlord can deduct for real damage or unpaid dues, but normally **not for reasonable wear and tear** — routine repainting and cleaning after you lived there usually counts as wear and tear [TEN-WEAR]. If your agreement promises the deposit back, holding it back is a breach and you can claim it [TEN-CONTRACT]. What your agreement says about painting matters a lot.\n\n**What to do now:**\n1. Message him in writing (WhatsApp/email): ask for the full ₹60,000 within 7 days, or an itemised list of deductions with bills.\n2. If he doesn't pay, I can draft a **legal notice** for you.\n3. After that: free settlement through Lok Adalat [GEN-LOKADALAT], or a recovery case [TEN-FORUM].\n\n⏰ Money claims are generally within 3 years [GEN-LIMIT] — you have time, but act while evidence is fresh.\n\n**Tell me:**\n1. Monthly rent?\n2. Is there a written agreement — what does it say about the deposit/painting?\n3. How did you pay the deposit, and do you have move-out photos?",
 "needs_lawyer": false,
 "lawyer_reason": "",
 "ready_to_draft": "none"
}
```
</details>

---
### 🧑 User
Rent was 20,000 per month. We have an 11 month rent agreement, it just says deposit is refundable at the end. I paid the deposit by bank transfer. I have WhatsApp chats where he says 'will return after painting'. I didn't damage anything, it was normal use for 2 years. I have some photos from when I left.

### ⚖️ Nyay Saathi
Thanks — this helps a lot, and your case looks good.

**Why you're in a strong position:**
• Your agreement says the deposit is **refundable at the end** — keeping it is a breach, and you can claim it [1].
• After 2 years of normal use, repainting and cleaning are usually **reasonable wear and tear**, which can't normally be charged to you [2]. Your agreement doesn't say painting can be deducted.
• His WhatsApp ("will return after painting") shows he accepts the money is yours.

Note: the Model Tenancy Act's 2-month cap applies only in states that adopted it [3], so in Karnataka rely on your agreement, not that cap.

**Plan:**
1. **Today:** one final WhatsApp/email asking for ₹60,000 within 7 days.
2. **Then:** a legal notice by Speed Post — I can draft it now.
3. **If no reply in 15 days:** free settlement via DLSA/Lok Adalat [4], or a recovery case; with a written agreement a lawyer may use the faster summary-suit route [5].

You don't need a lawyer for the notice; for a court case, yes (free if eligible: 15100) [6].

**Keep safe:** agreement, bank statement, exported WhatsApp chat, photos.

**Sources (checked):** [1] Compensation for breach of contract (Indian Contract Act, s.73) — https://www.indiacode.nic.in/ (search: Indian Contract Act, 1872); [2] Normal wear and tear (Transfer of Property Act, s.108(m)) — https://www.indiacode.nic.in/ (search: Transfer of Property Act, 1882); [3] Security deposit under the Model Tenancy Act, 2021 (s.11) — https://mohua.gov.in/ (Model Tenancy Act, 2021); [4] Lok Adalat / pre-litigation settlement (Legal Services Authorities Act, s.19) — https://nalsa.gov.in/; [5] Where to file for a deposit not returned — https://www.indiacode.nic.in/ (search: Code of Civil Procedure, 1908); [6] Free legal aid (Legal Services Authorities Act, 1987, s.12) — https://nalsa.gov.in/

`routed_issue=deposit  model_issue=deposit  needs_lawyer=False  red_flags=[]  ready_to_draft=legal_notice  cards_given=15`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "en",
 "issue": "deposit",
 "case_file": {
  "summary": "Tenant in Bengaluru vacated 31 Aug 2026 after ~2 years; landlord withholding entire Rs 60,000 deposit and proposing to keep Rs 35,000 for painting/cleaning",
  "people": {
   "user": "tenant",
   "other_side": "landlord (owner)"
  },
  "place": "Bengaluru, Karnataka",
  "amount_at_stake": "Rs 60,000 (Rs 35,000 disputed)",
  "timeline": [
   {
    "date": "~2024-08",
    "event": "Tenancy began; 11-month rent agreement; rent Rs 20,000/month; deposit Rs 60,000 paid by bank transfer"
   },
   {
    "date": "2026-08-31",
    "event": "Tenant vacated after ~2 years of normal use; took photos"
   },
   {
    "date": "after 2026-08-31",
    "event": "Landlord says he will keep Rs 35,000 for painting/cleaning; WhatsApp: 'will return after painting'; nothing refunded"
   }
  ],
  "proof_have": [
   "rent agreement (deposit refundable at the end)",
   "bank transfer proof of deposit",
   "WhatsApp chats with landlord",
   "move-out photos"
  ],
  "proof_missing": [
   "key handover proof (if any)",
   "move-in photos/condition (if any)",
   "itemised deduction list from landlord"
  ],
  "deadlines": [
   "Civil recovery generally within 3 years (~Aug 2029) [GEN-LIMIT]"
  ],
  "what_user_wants": "full Rs 60,000 deposit back"
 },
 "reply": "Thanks — this helps a lot, and your case looks good.\n\n**Why you're in a strong position:**\n• Your agreement says the deposit is **refundable at the end** — keeping it is a breach, and you can claim it [TEN-CONTRACT].\n• After 2 years of normal use, repainting and cleaning are usually **reasonable wear and tear**, which can't normally be charged to you [TEN-WEAR]. Your agreement doesn't say painting can be deducted.\n• His WhatsApp (\"will return after painting\") shows he accepts the money is yours.\n\nNote: the Model Tenancy Act's 2-month cap applies only in states that adopted it [TEN-MTA], so in Karnataka rely on your agreement, not that cap.\n\n**Plan:**\n1. **Today:** one final WhatsApp/email asking for ₹60,000 within 7 days.\n2. **Then:** a legal notice by Speed Post — I can draft it now.\n3. **If no reply in 15 days:** free settlement via DLSA/Lok Adalat [GEN-LOKADALAT], or a recovery case; with a written agreement a lawyer may use the faster summary-suit route [TEN-FORUM].\n\nYou don't need a lawyer for the notice; for a court case, yes (free if eligible: 15100) [GEN-LEGALAID].\n\n**Keep safe:** agreement, bank statement, exported WhatsApp chat, photos.",
 "needs_lawyer": false,
 "lawyer_reason": "",
 "ready_to_draft": "legal_notice"
}
```
</details>

---
### 📝 Draft: legal_notice

```
LEGAL NOTICE / DEMAND NOTICE FOR REFUND OF SECURITY DEPOSIT

Date: [DATE]
Sent by: Speed Post / Registered Post AD (copy also sent by WhatsApp and email, if available)

From:
[YOUR FULL NAME]
[YOUR CURRENT ADDRESS]
Phone: [YOUR PHONE NUMBER]

To:
[LANDLORD'S FULL NAME]
[LANDLORD'S ADDRESS]

Subject: Demand for refund of security deposit of Rs 60,000 for the premises at [ADDRESS OF RENTED FLAT], Bengaluru

Sir/Madam,

1. I was your tenant at [ADDRESS OF RENTED FLAT], Bengaluru, under a rent agreement dated [DATE OF RENT AGREEMENT] (11 months, renewed/continued thereafter), at a monthly rent of Rs 20,000.

2. At the start of the tenancy I paid you a security deposit of Rs 60,000 by bank transfer on [DATE OF DEPOSIT PAYMENT] (transaction reference [UTR/REFERENCE NUMBER]). The rent agreement states that the deposit is refundable at the end of the tenancy.

3. I occupied the premises for about two years with normal, careful use and vacated on 31 August 2026, handing back possession to you. I have photographs of the condition of the premises at the time of leaving. No rent or other dues are pending from my side.

4. Despite my requests, you have not refunded any part of the deposit. You have informed me that you intend to keep Rs 35,000 towards painting and cleaning, and in WhatsApp messages you stated that you "will return after painting".

5. Repainting and cleaning after two years of normal occupation are reasonable wear and tear. Under Section 108(m) of the Transfer of Property Act, 1882, a tenant is bound to return the property in the condition received, subject to changes caused by reasonable wear and tear. The rent agreement does not permit any deduction for painting. Withholding the deposit is a breach of the rent agreement, and I am entitled to compensation for the loss caused by that breach under Section 73 of the Indian Contract Act, 1872.

6. I therefore call upon you to pay me the full security deposit of Rs 60,000 within 15 days of receipt of this notice, by bank transfer to:
   Account name: [YOUR NAME AS IN BANK]
   Account number / UPI ID: [ACCOUNT NUMBER OR UPI ID]
   IFSC: [IFSC CODE]
If you claim any deduction for actual damage (not wear and tear), please send an itemised list with bills within the same period.

7. If you fail to do so, I shall be constrained to approach the appropriate forum, including pre-litigation settlement through the Legal Services Authority / Lok Adalat and a suit for recovery of money before the competent civil court, at your cost and risk, without further notice.

Yours faithfully,

[SIGNATURE]
[YOUR FULL NAME]

Enclosures (copies):
1. Rent agreement dated [DATE OF RENT AGREEMENT]
2. Bank statement showing payment of the deposit
3. WhatsApp messages with you about the deposit
4. Photographs of the premises at the time of vacating

```

**Blanks to fill:** [ACCOUNT NUMBER OR UPI ID], [ADDRESS OF RENTED FLAT], [DATE OF DEPOSIT PAYMENT], [DATE OF RENT AGREEMENT], [DATE], [IFSC CODE], [LANDLORD'S ADDRESS], [LANDLORD'S FULL NAME], [SIGNATURE], [UTR/REFERENCE NUMBER], [YOUR CURRENT ADDRESS], [YOUR FULL NAME], [YOUR NAME AS IN BANK], [YOUR PHONE NUMBER]

**Note to user:** Fill every [BRACKET] and check the dates against your bank statement and agreement. Print, sign, and send it by Speed Post or Registered Post AD; keep the postal receipt and tracking printout — that is your proof of sending. Also send a photo of the signed notice on WhatsApp. Keep a signed copy for yourself.

Guard flags: []

---
## Final case file
```json
{
  "summary": "Tenant in Bengaluru vacated 31 Aug 2026 after ~2 years; landlord withholding entire Rs 60,000 deposit and proposing to keep Rs 35,000 for painting/cleaning",
  "people": {
    "user": "tenant",
    "other_side": "landlord (owner)"
  },
  "place": "Bengaluru, Karnataka",
  "amount_at_stake": "Rs 60,000 (Rs 35,000 disputed)",
  "timeline": [
    {
      "date": "~2024-08",
      "event": "Tenancy began; 11-month rent agreement; rent Rs 20,000/month; deposit Rs 60,000 paid by bank transfer"
    },
    {
      "date": "2026-08-31",
      "event": "Tenant vacated after ~2 years of normal use; took photos"
    },
    {
      "date": "after 2026-08-31",
      "event": "Landlord says he will keep Rs 35,000 for painting/cleaning; WhatsApp: 'will return after painting'; nothing refunded"
    }
  ],
  "proof_have": [
    "rent agreement (deposit refundable at the end)",
    "bank transfer proof of deposit",
    "WhatsApp chats with landlord",
    "move-out photos"
  ],
  "proof_missing": [
    "key handover proof (if any)",
    "move-in photos/condition (if any)",
    "itemised deduction list from landlord"
  ],
  "deadlines": [
    "Civil recovery generally within 3 years (~Aug 2029) [GEN-LIMIT]"
  ],
  "what_user_wants": "full Rs 60,000 deposit back"
}
```
