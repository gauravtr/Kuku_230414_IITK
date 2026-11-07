# 02_refund_hinglish
_Hinglish, defective phone from an online marketplace; consumer complaint draft_

Model: `manual:claude-opus-5-5`  |  Auto-checks: ✅ PASS {"issue": true, "must_include_any": true, "guard_clean": true, "language": true, "json_parsed": true}

### 🧑 User
bhai maine 12 Oct 2026 ko ek online app se 18,999 ka phone order kiya tha, 2 din me screen pe green line aa gayi. Return request daala to reject kar diya bol rahe 'physical damage'. Maine kuch nahi kiya. Customer care pe 3 baar complaint ki, koi reply nahi. Main Lucknow me rehta hu. Paisa wapas chahiye.

### ⚖️ Nyay Saathi
Bhai, tension mat lo — ye clear consumer case lagta hai. 2 din me screen kharab hona product ka **defect** hai, aur bina sahi jaanch ke return reject karna **deficiency in service** ho sakta hai [1].

**Abhi kya karo (free se shuru):**
1. App ke Help/Legal page pe **Grievance Officer** ka contact dhoondo aur unko likhit complaint bhejo — unhe 48 ghante me acknowledge aur 1 mahine me solve karna hota hai [2].
2. Saath me **1915** pe call karo ya consumerhelpline.gov.in pe complaint daalo — free hai, docket number sambhal ke rakhna [3].
3. Phir bhi na sune to **District Consumer Commission, Lucknow** me case — ghar baithe e-Jagriti pe, ₹5 lakh tak koi fee nahi [4] [5]. Lawyer zaroori nahi. Refund + pareshani ka compensation maang sakte ho [6].

⏰ Deadline: problem se 2 saal ke andar [7] — time hai, par der mat karo.

**Sambhal ke rakho:** invoice, payment proof, green line ka photo/video, reject message ka screenshot, teeno complaints ke ticket number.

Batao: 1) app aur seller ka naam, 2) delivery kis din hui, 3) return kab reject hua? Phir main complaint draft kar deta hu.

**Sources (checked):** [1] Who is a consumer; defect and deficiency (Consumer Protection Act, 2019, s.2) — https://www.indiacode.nic.in/ (search: Consumer Protection Act, 2019); [2] E-commerce grievance officer (E-Commerce Rules, 2020) — https://consumeraffairs.nic.in/ (Consumer Protection (E-Commerce) Rules, 2020); [3] National Consumer Helpline 1915 (free, before going to court) — https://consumerhelpline.gov.in/; [4] Online filing on e-Jagriti and fees — https://e-jagriti.gov.in/; [5] Which Consumer Commission and where (s.34, s.35 + 2021 Jurisdiction Rules) — https://pib.gov.in/PressReleasePage.aspx?PRID=1847881; [6] What the Commission can order (s.39) — https://www.indiacode.nic.in/ (search: Consumer Protection Act, 2019); [7] 2-year time limit for consumer complaints (s.69) — https://www.advocatekhoj.com/library/bareacts/consumerprotection2019/69.php

`routed_issue=consumer  model_issue=consumer  needs_lawyer=False  red_flags=[]  ready_to_draft=consumer_complaint  cards_given=10`

Guard flags: []

<details><summary>Raw model output</summary>

```json
{
 "language": "hinglish",
 "issue": "consumer",
 "case_file": {
  "summary": "Phone (Rs 18,999) bought online on 12 Oct 2026 developed screen green line within 2 days; return rejected as 'physical damage'; 3 customer-care complaints unanswered",
  "people": {
   "user": "buyer, Lucknow",
   "other_side": "online shopping app + seller (names not given)"
  },
  "place": "Lucknow, Uttar Pradesh",
  "amount_at_stake": "Rs 18,999 + compensation",
  "timeline": [
   {
    "date": "2026-10-12",
    "event": "Phone ordered online for Rs 18,999"
   },
   {
    "date": "~2 days after delivery",
    "event": "Green line appeared on screen"
   },
   {
    "date": "unknown",
    "event": "Return request rejected citing 'physical damage'"
   },
   {
    "date": "unknown",
    "event": "3 complaints to customer care, no reply"
   }
  ],
  "proof_have": [
   "order on the app (presumably)"
  ],
  "proof_missing": [
   "invoice",
   "payment proof",
   "photos/video of the green line",
   "screenshot of return rejection",
   "ticket numbers of the 3 complaints",
   "app and seller name",
   "delivery date"
  ],
  "deadlines": [
   "Consumer complaint within 2 years of the problem (~Oct 2028) [CPA-LIMIT]",
   "Grievance officer must acknowledge in 48 hours, resolve in 1 month [ECOM-GRIEV]"
  ],
  "what_user_wants": "full refund"
 },
 "reply": "Bhai, tension mat lo — ye clear consumer case lagta hai. 2 din me screen kharab hona product ka **defect** hai, aur bina sahi jaanch ke return reject karna **deficiency in service** ho sakta hai [CPA-DEF].\n\n**Abhi kya karo (free se shuru):**\n1. App ke Help/Legal page pe **Grievance Officer** ka contact dhoondo aur unko likhit complaint bhejo — unhe 48 ghante me acknowledge aur 1 mahine me solve karna hota hai [ECOM-GRIEV].\n2. Saath me **1915** pe call karo ya consumerhelpline.gov.in pe complaint daalo — free hai, docket number sambhal ke rakhna [CPA-NCH].\n3. Phir bhi na sune to **District Consumer Commission, Lucknow** me case — ghar baithe e-Jagriti pe, ₹5 lakh tak koi fee nahi [CPA-EFILE] [CPA-FORUM]. Lawyer zaroori nahi. Refund + pareshani ka compensation maang sakte ho [CPA-RELIEF].\n\n⏰ Deadline: problem se 2 saal ke andar [CPA-LIMIT] — time hai, par der mat karo.\n\n**Sambhal ke rakho:** invoice, payment proof, green line ka photo/video, reject message ka screenshot, teeno complaints ke ticket number.\n\nBatao: 1) app aur seller ka naam, 2) delivery kis din hui, 3) return kab reject hua? Phir main complaint draft kar deta hu.",
 "needs_lawyer": false,
 "lawyer_reason": "",
 "ready_to_draft": "consumer_complaint"
}
```
</details>

---
### 📝 Draft: consumer_complaint

```
BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION, LUCKNOW

Consumer Complaint No. ____ of 2026

IN THE MATTER OF:
[YOUR FULL NAME]
[YOUR FULL ADDRESS], Lucknow, Uttar Pradesh
Phone: [YOUR PHONE NUMBER]  Email: [YOUR EMAIL]
                                                                    ... Complainant
VERSUS

1. [NAME OF ONLINE SHOPPING PLATFORM], through its Grievance Officer
   [PLATFORM'S REGISTERED ADDRESS]
2. [NAME OF SELLER]
   [SELLER'S ADDRESS AS SHOWN ON INVOICE]
                                                                    ... Opposite Parties

COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019

1. PARTIES
The Complainant is a resident of Lucknow who bought a mobile phone for personal use. Opposite Party No. 1 runs the online shopping platform through which the phone was sold. Opposite Party No. 2 is the seller of the phone.

2. FACTS
2.1 On 12 October 2026 the Complainant ordered a mobile phone, [PHONE BRAND AND MODEL], for Rs 18,999 through the platform of Opposite Party No. 1, order ID [ORDER ID], paid by [PAYMENT MODE].
2.2 The phone was delivered on [DATE OF DELIVERY].
2.3 Within about two days of use, a green line appeared on the screen. The Complainant did not drop or damage the phone.
2.4 The Complainant raised a return request on [DATE OF RETURN REQUEST]. The request was rejected on [DATE OF REJECTION] on the ground of "physical damage", without any proper inspection report being shared.
2.5 The Complainant complained to customer care three times ([TICKET NUMBERS AND DATES]) but received no reply.

3. DEFECT AND DEFICIENCY IN SERVICE
A screen fault appearing within two days of normal use is a defect in the goods, and the refusal of the return without proper inspection, followed by no response to complaints, is a deficiency in service, within the meaning of Section 2 of the Consumer Protection Act, 2019.

4. JURISDICTION
The value of the goods paid as consideration is Rs 18,999, which is within the pecuniary jurisdiction of this District Commission. The Complainant resides in Lucknow, and this complaint is filed here under Section 34 of the Consumer Protection Act, 2019.

5. LIMITATION
The cause of action arose in October 2026. This complaint is filed within two years, as required by Section 69 of the Consumer Protection Act, 2019.

6. EARLIER ATTEMPTS TO RESOLVE
The Complainant contacted customer care three times as stated above, wrote to the Grievance Officer of Opposite Party No. 1 on [DATE OF GRIEVANCE OFFICER COMPLAINT], and registered a grievance with the National Consumer Helpline, docket number [NCH DOCKET NUMBER, IF ANY]. The matter remains unresolved.

7. RELIEFS PRAYED
Under Section 39 of the Consumer Protection Act, 2019, the Complainant prays that this Commission may direct the Opposite Parties, jointly and severally, to:
(a) refund Rs 18,999, the price of the phone;
(b) pay Rs [COMPENSATION AMOUNT] as compensation for mental agony and harassment;
(c) pay Rs [LITIGATION COST AMOUNT] as costs of this complaint;
(d) pass any other order this Commission considers fit.

LIST OF DOCUMENTS (ANNEXURES)
Annexure A: Order confirmation and invoice
Annexure B: Proof of payment
Annexure C: Photos/video showing the green line on the screen
Annexure D: Screenshot of the return rejection
Annexure E: Customer-care complaints and ticket numbers
Annexure F: Complaint to the Grievance Officer and NCH docket (if any)

VERIFICATION
I, [YOUR FULL NAME], the Complainant, verify that the contents of paragraphs 1 to 7 above are true and correct to my knowledge and belief, and nothing material has been concealed.

Place: Lucknow
Date: [DATE]
                                                                    [SIGNATURE]
                                                                    Complainant

Note: To be filed online at e-Jagriti (https://e-jagriti.gov.in) with a supporting affidavit.

```

**Blanks to fill:** [COMPENSATION AMOUNT], [DATE OF DELIVERY], [DATE OF GRIEVANCE OFFICER COMPLAINT], [DATE OF REJECTION], [DATE OF RETURN REQUEST], [DATE], [LITIGATION COST AMOUNT], [NAME OF ONLINE SHOPPING PLATFORM], [NAME OF SELLER], [NCH DOCKET NUMBER, IF ANY], [ORDER ID], [PAYMENT MODE], [PHONE BRAND AND MODEL], [PLATFORM'S REGISTERED ADDRESS], [SELLER'S ADDRESS AS SHOWN ON INVOICE], [SIGNATURE], [TICKET NUMBERS AND DATES], [YOUR EMAIL], [YOUR FULL ADDRESS], [YOUR FULL NAME], [YOUR PHONE NUMBER]

**Note to user:** Bhai, saare [BRACKET] bharo — naam, address, order ID, ticket number invoice se check karke. Compensation ka amount aap khud decide karo (reasonable rakho). Pehle Grievance Officer aur 1915 pe complaint kar lo, uska docket number isme daalo. Phir e-Jagriti pe account banake ye complaint, affidavit aur saare documents (invoice, photo, screenshots) PDF me upload karo. ₹5 lakh tak fee nahi lagti.

Guard flags: []

---
## Final case file
```json
{
  "summary": "Phone (Rs 18,999) bought online on 12 Oct 2026 developed screen green line within 2 days; return rejected as 'physical damage'; 3 customer-care complaints unanswered",
  "people": {
    "user": "buyer, Lucknow",
    "other_side": "online shopping app + seller (names not given)"
  },
  "place": "Lucknow, Uttar Pradesh",
  "amount_at_stake": "Rs 18,999 + compensation",
  "timeline": [
    {
      "date": "2026-10-12",
      "event": "Phone ordered online for Rs 18,999"
    },
    {
      "date": "~2 days after delivery",
      "event": "Green line appeared on screen"
    },
    {
      "date": "unknown",
      "event": "Return request rejected citing 'physical damage'"
    },
    {
      "date": "unknown",
      "event": "3 complaints to customer care, no reply"
    }
  ],
  "proof_have": [
    "order on the app (presumably)"
  ],
  "proof_missing": [
    "invoice",
    "payment proof",
    "photos/video of the green line",
    "screenshot of return rejection",
    "ticket numbers of the 3 complaints",
    "app and seller name",
    "delivery date"
  ],
  "deadlines": [
    "Consumer complaint within 2 years of the problem (~Oct 2028) [CPA-LIMIT]",
    "Grievance officer must acknowledge in 48 hours, resolve in 1 month [ECOM-GRIEV]"
  ],
  "what_user_wants": "full refund"
}
```
