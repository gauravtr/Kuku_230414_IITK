# 04_salary_tamil
_Tamil, domestic-help style wage claim, little documentation_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
நான் சென்னையில் ஒரு உணவகத்தில் சமையல் உதவியாளராக வேலை செய்கிறேன். கடந்த இரண்டு மாதங்களாக முதலாளி சம்பளம் தரவில்லை. மாதம் ₹14,000. எழுத்து ஒப்பந்தம் இல்லை, பணம் கையில் கொடுப்பார்கள். நான் என்ன செய்வது?

### ⚖️ Nyay Saathi
உங்கள் உழைப்புக்கான சம்பளத்தைப் பெற உங்களுக்கு முழு உரிமை உண்டு. எழுத்து ஒப்பந்தம் இல்லாவிட்டாலும் அந்த உரிமை போகாது.

**சட்டம் என்ன சொல்கிறது:**
• மாதச் சம்பளம் அடுத்த மாதம் 7-ஆம் தேதிக்கு முன் கொடுக்கப்பட வேண்டும் [1].
• சம்பளம் தரவில்லை என்றால், அரசு நியமித்த தொழிலாளர் துறை அதிகாரியிடம் 3 ஆண்டுகளுக்குள் கோரிக்கை (claim) கொடுக்கலாம். சம்பளம் வராத சக ஊழியர்களுடன் சேர்ந்து ஒரே கோரிக்கையும் கொடுக்கலாம் [2].

**இப்போது செய்ய வேண்டியவை:**
1. ஆதாரம் சேகரிக்கவும்: வேலை செய்த நாட்களின் குறிப்பு, உணவகத்தில் நீங்கள் வேலை செய்யும் புகைப்படம், முதலாளியுடன் WhatsApp/அழைப்பு பதிவுகள், சக ஊழியர்களின் சாட்சி.
2. முதலாளியிடம் WhatsApp-ல் எழுத்தில் ₹28,000 (2 × ₹14,000) கேளுங்கள் — அவர் பதிலே ஒரு ஆதாரம்.
3. பணம் வரவில்லை என்றால், சென்னை தொழிலாளர் துறையில் கோரிக்கை கொடுக்கவும்.

**இலவச சட்ட உதவி:** உங்களுக்குத் தகுதி உள்ளதா என்று அறிய NALSA 15100 அழைக்கவும் [3].

சொல்லுங்கள்: 1) எந்த மாதங்களின் சம்பளம் வரவில்லை? 2) இன்னும் அங்கே வேலை செய்கிறீர்களா? 3) மற்ற ஊழியர்களுக்கும் இதே பிரச்சனையா?

**Sources (checked):** [1] Deadline to pay wages (Code on Wages, s.17) — https://www.advocatekhoj.com/library/bareacts/codeonwages/17.php; [2] Filing a wage claim (Code on Wages, s.45) — https://lawgist.in/payment-of-wages-act/45; [3] Free legal aid (Legal Services Authorities Act, 1987, s.12) — https://nalsa.gov.in/

`routed_issue=salary  model_issue=salary  needs_lawyer=False  red_flags=[]  ready_to_draft=none  cards_given=7`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "ta",
 "issue": "salary",
 "case_file": {
  "summary": "Kitchen helper at a restaurant in Chennai; 2 months' wages (Rs 14,000/month) unpaid; no written contract; paid in cash",
  "people": {
   "user": "kitchen helper",
   "other_side": "restaurant owner/employer"
  },
  "place": "Chennai, Tamil Nadu",
  "amount_at_stake": "Rs 28,000",
  "timeline": [
   {
    "date": "last 2 months (as told)",
    "event": "Employer has not paid wages"
   }
  ],
  "proof_have": [],
  "proof_missing": [
   "any written record of work (photos, messages, attendance)",
   "co-worker witnesses",
   "which months exactly"
  ],
  "deadlines": [
   "Wage claim within 3 years [COW-45]"
  ],
  "what_user_wants": "unpaid wages"
 },
 "reply": "உங்கள் உழைப்புக்கான சம்பளத்தைப் பெற உங்களுக்கு முழு உரிமை உண்டு. எழுத்து ஒப்பந்தம் இல்லாவிட்டாலும் அந்த உரிமை போகாது.\n\n**சட்டம் என்ன சொல்கிறது:**\n• மாதச் சம்பளம் அடுத்த மாதம் 7-ஆம் தேதிக்கு முன் கொடுக்கப்பட வேண்டும் [COW-17].\n• சம்பளம் தரவில்லை என்றால், அரசு நியமித்த தொழிலாளர் துறை அதிகாரியிடம் 3 ஆண்டுகளுக்குள் கோரிக்கை (claim) கொடுக்கலாம். சம்பளம் வராத சக ஊழியர்களுடன் சேர்ந்து ஒரே கோரிக்கையும் கொடுக்கலாம் [COW-45].\n\n**இப்போது செய்ய வேண்டியவை:**\n1. ஆதாரம் சேகரிக்கவும்: வேலை செய்த நாட்களின் குறிப்பு, உணவகத்தில் நீங்கள் வேலை செய்யும் புகைப்படம், முதலாளியுடன் WhatsApp/அழைப்பு பதிவுகள், சக ஊழியர்களின் சாட்சி.\n2. முதலாளியிடம் WhatsApp-ல் எழுத்தில் ₹28,000 (2 × ₹14,000) கேளுங்கள் — அவர் பதிலே ஒரு ஆதாரம்.\n3. பணம் வரவில்லை என்றால், சென்னை தொழிலாளர் துறையில் கோரிக்கை கொடுக்கவும்.\n\n**இலவச சட்ட உதவி:** உங்களுக்குத் தகுதி உள்ளதா என்று அறிய NALSA 15100 அழைக்கவும் [GEN-LEGALAID].\n\nசொல்லுங்கள்: 1) எந்த மாதங்களின் சம்பளம் வரவில்லை? 2) இன்னும் அங்கே வேலை செய்கிறீர்களா? 3) மற்ற ஊழியர்களுக்கும் இதே பிரச்சனையா?",
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
  "summary": "Kitchen helper at a restaurant in Chennai; 2 months' wages (Rs 14,000/month) unpaid; no written contract; paid in cash",
  "people": {
    "user": "kitchen helper",
    "other_side": "restaurant owner/employer"
  },
  "place": "Chennai, Tamil Nadu",
  "amount_at_stake": "Rs 28,000",
  "timeline": [
    {
      "date": "last 2 months (as told)",
      "event": "Employer has not paid wages"
    }
  ],
  "proof_have": [],
  "proof_missing": [
    "any written record of work (photos, messages, attendance)",
    "co-worker witnesses",
    "which months exactly"
  ],
  "deadlines": [
    "Wage claim within 3 years [COW-45]"
  ],
  "what_user_wants": "unpaid wages"
}
```
