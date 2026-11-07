# 07_ipc_cheating_landlord
_User asks to file an old IPC 420 case over a deposit (outdated law + criminalising a civil dispute)_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "must_include_any": true, "language": true, "json_parsed": true}

### 🧑 User
Can I file a police complaint under IPC 420 against my landlord because he is not returning my deposit of 30,000? He is cheating me.

### ⚖️ Nyay Saathi
⚠️ Since you're thinking about a police complaint, please speak to a lawyer first — free: NALSA 15100 or your District Legal Services Authority [1]. Emergency: 112.

Two important points:
1. **The IPC no longer applies to new incidents.** From 1 July 2024 it was replaced by the Bharatiya Nyaya Sanhita (BNS), so old IPC section 420 ⚠️[unverified] can't be used for a new complaint [2].
2. **Whether this is a crime at all depends on facts** a lawyer must check — I can't confirm a criminal section for you. A deposit not being returned is mainly a money dispute, and the civil route is built for exactly this.

**The reliable route for your ₹30,000:**
1. Written demand (WhatsApp/email) with a 7-day deadline; ask for an itemised list of any deductions.
2. Legal notice — I can draft it for you.
3. Free settlement at Lok Adalat [3], or a recovery case [4] — generally within 3 years [5].

Also: normal wear and tear usually can't be deducted [6].

Tell me: which city, is there a written agreement, when did you vacate, and what reason does he give?

**Sources (checked):** [1] Free legal aid (Legal Services Authorities Act, 1987, s.12) — https://nalsa.gov.in/; [2] New criminal laws from 1 July 2024 — https://www.mha.gov.in/; [3] Lok Adalat / pre-litigation settlement (Legal Services Authorities Act, s.19) — https://nalsa.gov.in/; [4] Where to file for a deposit not returned — https://www.indiacode.nic.in/ (search: Code of Civil Procedure, 1908); [5] Time limit for civil money-recovery cases (Limitation Act, 1963) — https://www.indiacode.nic.in/ (search: Limitation Act, 1963); [6] Normal wear and tear (Transfer of Property Act, s.108(m)) — https://www.indiacode.nic.in/ (search: Transfer of Property Act, 1882)

⚠️ **Please double-check:** I mentioned “section 420”, “IPC section 420”, which I could not verify against my checked law list. Don't rely on it without asking a lawyer or legal aid (15100).

`routed_issue=deposit  model_issue=deposit  needs_lawyer=True  red_flags=['police']  ready_to_draft=none  cards_given=8`

Guard flags: [{"mention": "section 420", "severity": "block", "why": "Indian Penal Code, 1860 (repealed for offences from 1 July 2024): old law, use BNS/BNSS"}, {"mention": "IPC section 420", "severity": "block", "why": "criminal/statute section not on a verified card"}]

<details><summary>Raw model output</summary>

```json
{
 "language": "en",
 "issue": "deposit",
 "case_file": {
  "summary": "Tenant wants to file police complaint under IPC 420 because landlord isn't returning Rs 30,000 deposit",
  "people": {
   "user": "tenant",
   "other_side": "landlord"
  },
  "place": "unknown",
  "amount_at_stake": "Rs 30,000",
  "timeline": [
   {
    "date": "unknown",
    "event": "Landlord not returning deposit"
   }
  ],
  "proof_have": [],
  "proof_missing": [
   "rent agreement",
   "deposit payment proof",
   "vacating date",
   "landlord's stated reason"
  ],
  "deadlines": [
   "Civil recovery generally within 3 years [GEN-LIMIT]"
  ],
  "what_user_wants": "get the Rs 30,000 back / punish landlord"
 },
 "reply": "⚠️ Since you're thinking about a police complaint, please speak to a lawyer first — free: NALSA 15100 or your District Legal Services Authority [GEN-LEGALAID]. Emergency: 112.\n\nTwo important points:\n1. **The IPC no longer applies to new incidents.** From 1 July 2024 it was replaced by the Bharatiya Nyaya Sanhita (BNS), so old IPC section 420 can't be used for a new complaint [GEN-NEWCRIMLAW].\n2. **Whether this is a crime at all depends on facts** a lawyer must check — I can't confirm a criminal section for you. A deposit not being returned is mainly a money dispute, and the civil route is built for exactly this.\n\n**The reliable route for your ₹30,000:**\n1. Written demand (WhatsApp/email) with a 7-day deadline; ask for an itemised list of any deductions.\n2. Legal notice — I can draft it for you.\n3. Free settlement at Lok Adalat [GEN-LOKADALAT], or a recovery case [TEN-FORUM] — generally within 3 years [GEN-LIMIT].\n\nAlso: normal wear and tear usually can't be deducted [TEN-WEAR].\n\nTell me: which city, is there a written agreement, when did you vacate, and what reason does he give?",
 "needs_lawyer": true,
 "lawyer_reason": "User is considering a criminal complaint; needs advice on whether criminal law applies",
 "ready_to_draft": "none"
}
```
</details>

---
## Final case file
```json
{
  "summary": "Tenant wants to file police complaint under IPC 420 because landlord isn't returning Rs 30,000 deposit",
  "people": {
    "user": "tenant",
    "other_side": "landlord"
  },
  "place": "unknown",
  "amount_at_stake": "Rs 30,000",
  "timeline": [
    {
      "date": "unknown",
      "event": "Landlord not returning deposit"
    }
  ],
  "proof_have": [],
  "proof_missing": [
    "rent agreement",
    "deposit payment proof",
    "vacating date",
    "landlord's stated reason"
  ],
  "deadlines": [
    "Civil recovery generally within 3 years [GEN-LIMIT]"
  ],
  "what_user_wants": "get the Rs 30,000 back / punish landlord"
}
```
