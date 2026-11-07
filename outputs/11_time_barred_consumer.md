# 11_time_barred_consumer
_Purchase and refusal in 2023 (past the 2-year consumer limit)_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "must_include_any": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
In June 2023 I bought a washing machine for Rs 32,000 from a showroom in Jaipur. It stopped working in August 2023 and the company refused to repair it under warranty in September 2023. I never complained anywhere after that. Can I file a consumer case now?

### ⚖️ Nyay Saathi
Short answer: it is late, but not necessarily impossible.

• A consumer complaint must be filed within **2 years** from when the problem arose [1]. The warranty repair was refused in September 2023, so the 2 years most likely ended around **September 2025**.
• A late complaint can still be accepted **only if** the Commission is satisfied there was sufficient cause for the delay [1]. You would need a genuine reason, and it's the Commission's decision.

**What I'd suggest:**
1. Think honestly: was there a real reason you couldn't file earlier? Collect proof of it.
2. Check whether the company wrote to you or promised anything after September 2023 — a lawyer should judge if that changes when the problem 'arose'.
3. Try the free National Consumer Helpline **1915** [2] — it can't order them, but companies sometimes still settle.
4. Get advice before filing a delayed complaint — free legal aid: 15100 [3].

If you do file: District Commission, Jaipur (value under ₹50 lakh) [4], no fee up to ₹5 lakh [5].

Do you have the invoice, the warranty card, and the refusal in writing? And was there any reason for the delay?

**Sources (checked):** [1] 2-year time limit for consumer complaints (s.69) — https://www.advocatekhoj.com/library/bareacts/consumerprotection2019/69.php; [2] National Consumer Helpline 1915 (free, before going to court) — https://consumerhelpline.gov.in/; [3] Free legal aid (Legal Services Authorities Act, 1987, s.12) — https://nalsa.gov.in/; [4] Which Consumer Commission and where (s.34, s.35 + 2021 Jurisdiction Rules) — https://pib.gov.in/PressReleasePage.aspx?PRID=1847881; [5] Online filing on e-Jagriti and fees — https://e-jagriti.gov.in/

`routed_issue=consumer  model_issue=consumer  needs_lawyer=True  red_flags=[]  ready_to_draft=none  cards_given=14`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "en",
 "issue": "consumer",
 "case_file": {
  "summary": "Washing machine (Rs 32,000) bought June 2023 in Jaipur; failed Aug 2023; warranty repair refused Sep 2023; no complaint filed since",
  "people": {
   "user": "buyer",
   "other_side": "manufacturer and showroom (names not given)"
  },
  "place": "Jaipur, Rajasthan",
  "amount_at_stake": "Rs 32,000 + compensation",
  "timeline": [
   {
    "date": "2023-06",
    "event": "Bought washing machine for Rs 32,000 from a showroom"
   },
   {
    "date": "2023-08",
    "event": "Machine stopped working"
   },
   {
    "date": "2023-09",
    "event": "Company refused warranty repair"
   }
  ],
  "proof_have": [],
  "proof_missing": [
   "invoice",
   "warranty card",
   "refusal in writing",
   "any reason for the delay"
  ],
  "deadlines": [
   "2-year consumer limit likely ended ~Sep 2025; late filing needs sufficient cause [CPA-LIMIT]"
  ],
  "what_user_wants": "file a consumer case"
 },
 "reply": "Short answer: it is late, but not necessarily impossible.\n\n• A consumer complaint must be filed within **2 years** from when the problem arose [CPA-LIMIT]. The warranty repair was refused in September 2023, so the 2 years most likely ended around **September 2025**.\n• A late complaint can still be accepted **only if** the Commission is satisfied there was sufficient cause for the delay [CPA-LIMIT]. You would need a genuine reason, and it's the Commission's decision.\n\n**What I'd suggest:**\n1. Think honestly: was there a real reason you couldn't file earlier? Collect proof of it.\n2. Check whether the company wrote to you or promised anything after September 2023 — a lawyer should judge if that changes when the problem 'arose'.\n3. Try the free National Consumer Helpline **1915** [CPA-NCH] — it can't order them, but companies sometimes still settle.\n4. Get advice before filing a delayed complaint — free legal aid: 15100 [GEN-LEGALAID].\n\nIf you do file: District Commission, Jaipur (value under ₹50 lakh) [CPA-FORUM], no fee up to ₹5 lakh [CPA-EFILE].\n\nDo you have the invoice, the warranty card, and the refusal in writing? And was there any reason for the delay?",
 "needs_lawyer": true,
 "lawyer_reason": "Complaint is likely past the 2-year limit; a delay (condonation) application needs proper advice",
 "ready_to_draft": "none"
}
```
</details>

---
## Final case file
```json
{
  "summary": "Washing machine (Rs 32,000) bought June 2023 in Jaipur; failed Aug 2023; warranty repair refused Sep 2023; no complaint filed since",
  "people": {
    "user": "buyer",
    "other_side": "manufacturer and showroom (names not given)"
  },
  "place": "Jaipur, Rajasthan",
  "amount_at_stake": "Rs 32,000 + compensation",
  "timeline": [
    {
      "date": "2023-06",
      "event": "Bought washing machine for Rs 32,000 from a showroom"
    },
    {
      "date": "2023-08",
      "event": "Machine stopped working"
    },
    {
      "date": "2023-09",
      "event": "Company refused warranty repair"
    }
  ],
  "proof_have": [],
  "proof_missing": [
    "invoice",
    "warranty card",
    "refusal in writing",
    "any reason for the delay"
  ],
  "deadlines": [
    "2-year consumer limit likely ended ~Sep 2025; late filing needs sufficient cause [CPA-LIMIT]"
  ],
  "what_user_wants": "file a consumer case"
}
```
