# 03_salary_hindi
_Hindi (Devanagari), 3 months salary unpaid after resignation_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "must_include_any": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
मैं इंदौर की एक प्राइवेट कंपनी में अकाउंटेंट था। जुलाई, अगस्त और सितंबर 2026 की सैलरी नहीं मिली, हर महीने ₹25,000। मैंने 30 सितंबर को इस्तीफा दे दिया। HR बस कहता है 'अगले महीने'। मेरे पास ऑफर लेटर और पुरानी सैलरी स्लिप हैं। मैं क्या करूँ?

### ⚖️ Nyay Saathi
आपको अपनी तनख्वाह पाने का पूरा हक है, और कानून आपके साथ है।

**कानून क्या कहता है:**
• महीने की सैलरी अगले महीने की 7 तारीख से पहले देनी होती है [1]।
• इस्तीफा देने पर बकाया वेतन 2 कामकाजी दिनों के अंदर देना होता है [1] — आपके मामले में यह समय कब का निकल चुका है।
• आप श्रम विभाग (Labour Department) के अधिकारी के पास वेतन संहिता (Code on Wages) की धारा 45 के तहत दावा कर सकते हैं, 3 साल के अंदर [2]। जिन साथियों की सैलरी रुकी है, वे साथ मिलकर एक दावा कर सकते हैं।

**अभी क्या करें:**
1. HR को ईमेल करें: ₹75,000 (3 × ₹25,000) 7 दिन में देने की लिखित माँग।
2. जवाब न आए तो लीगल नोटिस — मैं ड्राफ्ट कर सकता हूँ।
3. फिर इंदौर के श्रम विभाग में दावा दायर करें [2]।

**संभालकर रखें:** ऑफर लेटर, सैलरी स्लिप, बैंक स्टेटमेंट (जिसमें जुलाई से सैलरी बंद दिखे), इस्तीफे का ईमेल, HR के मैसेज।

बताइए: 1) कंपनी का नाम? 2) इस्तीफा ईमेल से दिया था, क्या कंपनी ने स्वीकार किया? 3) क्या दूसरे कर्मचारियों की सैलरी भी रुकी है?

**Sources (checked):** [1] Deadline to pay wages (Code on Wages, s.17) — https://www.advocatekhoj.com/library/bareacts/codeonwages/17.php; [2] Filing a wage claim (Code on Wages, s.45) — https://lawgist.in/payment-of-wages-act/45

`routed_issue=salary  model_issue=salary  needs_lawyer=False  red_flags=[]  ready_to_draft=legal_notice  cards_given=7`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "hi",
 "issue": "salary",
 "case_file": {
  "summary": "Accountant at private company in Indore; salary for Jul-Sep 2026 (Rs 25,000/month) unpaid; resigned 30 Sep 2026",
  "people": {
   "user": "former accountant",
   "other_side": "private company (name not given), HR"
  },
  "place": "Indore, Madhya Pradesh",
  "amount_at_stake": "Rs 75,000",
  "timeline": [
   {
    "date": "2026-07 to 2026-09",
    "event": "Salary not paid for July, August, September (Rs 25,000 each)"
   },
   {
    "date": "2026-09-30",
    "event": "User resigned"
   },
   {
    "date": "after 2026-09-30",
    "event": "HR keeps saying 'next month'"
   }
  ],
  "proof_have": [
   "offer letter",
   "old salary slips"
  ],
  "proof_missing": [
   "bank statement showing salary stopped",
   "resignation email/acknowledgement",
   "written messages from HR",
   "attendance proof for Jul-Sep"
  ],
  "deadlines": [
   "Dues should have been paid within 2 working days of resignation [COW-17]",
   "Wage claim within 3 years (~Sep 2029) [COW-45]"
  ],
  "what_user_wants": "Rs 75,000 unpaid salary"
 },
 "reply": "आपको अपनी तनख्वाह पाने का पूरा हक है, और कानून आपके साथ है।\n\n**कानून क्या कहता है:**\n• महीने की सैलरी अगले महीने की 7 तारीख से पहले देनी होती है [COW-17]।\n• इस्तीफा देने पर बकाया वेतन 2 कामकाजी दिनों के अंदर देना होता है [COW-17] — आपके मामले में यह समय कब का निकल चुका है।\n• आप श्रम विभाग (Labour Department) के अधिकारी के पास वेतन संहिता (Code on Wages) की धारा 45 के तहत दावा कर सकते हैं, 3 साल के अंदर [COW-45]। जिन साथियों की सैलरी रुकी है, वे साथ मिलकर एक दावा कर सकते हैं।\n\n**अभी क्या करें:**\n1. HR को ईमेल करें: ₹75,000 (3 × ₹25,000) 7 दिन में देने की लिखित माँग।\n2. जवाब न आए तो लीगल नोटिस — मैं ड्राफ्ट कर सकता हूँ।\n3. फिर इंदौर के श्रम विभाग में दावा दायर करें [COW-45]।\n\n**संभालकर रखें:** ऑफर लेटर, सैलरी स्लिप, बैंक स्टेटमेंट (जिसमें जुलाई से सैलरी बंद दिखे), इस्तीफे का ईमेल, HR के मैसेज।\n\nबताइए: 1) कंपनी का नाम? 2) इस्तीफा ईमेल से दिया था, क्या कंपनी ने स्वीकार किया? 3) क्या दूसरे कर्मचारियों की सैलरी भी रुकी है?",
 "needs_lawyer": false,
 "lawyer_reason": "",
 "ready_to_draft": "legal_notice"
}
```
</details>

---
## Final case file
```json
{
  "summary": "Accountant at private company in Indore; salary for Jul-Sep 2026 (Rs 25,000/month) unpaid; resigned 30 Sep 2026",
  "people": {
    "user": "former accountant",
    "other_side": "private company (name not given), HR"
  },
  "place": "Indore, Madhya Pradesh",
  "amount_at_stake": "Rs 75,000",
  "timeline": [
    {
      "date": "2026-07 to 2026-09",
      "event": "Salary not paid for July, August, September (Rs 25,000 each)"
    },
    {
      "date": "2026-09-30",
      "event": "User resigned"
    },
    {
      "date": "after 2026-09-30",
      "event": "HR keeps saying 'next month'"
    }
  ],
  "proof_have": [
    "offer letter",
    "old salary slips"
  ],
  "proof_missing": [
    "bank statement showing salary stopped",
    "resignation email/acknowledgement",
    "written messages from HR",
    "attendance proof for Jul-Sep"
  ],
  "deadlines": [
    "Dues should have been paid within 2 working days of resignation [COW-17]",
    "Wage claim within 3 years (~Sep 2029) [COW-45]"
  ],
  "what_user_wants": "Rs 75,000 unpaid salary"
}
```
