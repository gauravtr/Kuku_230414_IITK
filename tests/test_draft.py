"""The draft checker must catch the weaknesses a senior advocate would mark on a legal notice."""
import json

from nyay.engine import NyaySaathi, draft_checks, lint_draft, new_state
from nyay.kb import KB

kb = KB()

WEAK = """LEGAL NOTICE
Date: [DATE OF NOTICE]
To: [OTHER SIDE'S ADDRESS]
Under instructions from our client, Ms Riya, we state that our client was in an entirely consensual relationship with you.
You have committed extortion and criminal intimidation. The incontrovertible digital evidence (WhatsApp chats and audio
recordings) conclusively proves this. Our client has suffered mental agony.
Legal basis: your acts amount to extortion and criminal intimidation under the law.
Demand: cease harassment and monetary demands within 15 days.
Consequence: failing which our client will initiate proceedings at your sole cost, risk and consequences.
[YOUR FULL NAME / COUNSEL FOR THE CLIENT]
Enclosures: WhatsApp chats, audio recordings"""

GOOD = """Ref. No.: NIL                                        Date: 8 November 2026
BY SPEED POST / REGISTERED POST WITH ACKNOWLEDGEMENT DUE (RPAD)

To,
Rahul Verma, 12 MG Road, Pune 411001

Subject: Legal notice - to stop threats to publish private images and to withdraw the demand for Rs 50,000

Sir,
I, Riya Sharma, resident of 4 Park Street, Pune, address you as follows:

1. PARTIES AND BACKGROUND
1.1 We met at work in March 2025 and were in a relationship until August 2026.

2. FACTS IN ORDER OF DATE
2.1 On 2 October 2026, from WhatsApp number +91 98xxxxxx10, you wrote that you would send my private photographs to my
family unless I paid Rs 50,000 by 10 October 2026 (Annexure A-1).
2.2 On 12 October 2026 you repeated the demand in a call, which I recorded (Annexure A-2).

3. EVIDENCE IN MY POSSESSION
Annexure A-1 | WhatsApp messages | 2 October 2026 | +91 98xxxxxx10 | para 2.1 | original on my phone, preserved
Annexure A-2 | Call recording | 12 October 2026 | phone call | para 2.2 | original on my phone, preserved
The originals are preserved unaltered; a certificate under Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 will be
furnished when they are produced before any court. You are called upon to preserve all related messages and devices.

4. LEGAL POSITION
Section 308(3) of the Bharatiya Nyaya Sanhita, 2023: the conduct in paras 2.1-2.2, if established, would amount to putting
me in fear of injury to my reputation in order to commit extortion.

5. DEMANDS
(i) Stop all contact with me and my family immediately.
(ii) Within 7 days, deliver a signed written undertaking that you will not publish or share any image of me.
(iii) Within 7 days, withdraw in writing the demand for Rs 50,000.

6. TIME FOR COMPLIANCE AND MANNER OF REPLY
7 days is a reasonable period for a considered written reply. Reply in writing to 4 Park Street, Pune and riya@example.com.

7. CONSEQUENCES OF NON-COMPLIANCE
I may file a police complaint and a civil suit for an injunction and damages, and will seek costs as the court may allow.

8. RESERVATION OF RIGHTS
This notice is without prejudice to all my other rights and remedies, civil and criminal.

Riya Sharma, 4 Park Street, Pune, 8 November 2026

ENCLOSURES
Annexure A-1: WhatsApp messages, 2 October 2026
Annexure A-2: Call recording, 12 October 2026

SERVICE RECORD - office copy only
Speed Post article no. ______ booked on ______"""


def test_weak_notice_is_caught():
    probs = " | ".join(lint_draft(WEAK, "legal_notice", "self", kb))
    for must in ("incontrovertible", "conclusively prove", "sole cost", "states guilt", "FACTS",
                 "LEGAL POSITION", "DEMANDS", "without prejudice", "Annexure", "never 'my client'/'our client'"):
        assert must in probs, must


def test_good_notice_passes():
    assert lint_draft(GOOD, "legal_notice", "self", kb) == []
    assert all(ok for _, ok in draft_checks(GOOD, "legal_notice", "self"))


def test_unverified_section_flagged():
    probs = lint_draft(GOOD.replace("Section 308(3)", "Section 384 of the Indian Penal Code and Section 308(3)"),
                       "legal_notice", "self", kb)
    assert any("not on the law or judgment cards" in p for p in probs)


class TwoStepLLM:
    """First draft is weak; the repair pass returns the good one."""
    name = "fake"

    def __init__(self):
        self.calls = []

    def chat(self, system, messages, json_mode=False, **k):
        self.calls.append(system)
        doc = WEAK if len(self.calls) == 1 else GOOD
        return json.dumps({"document": doc, "blanks": [], "user_note": "Check and send."})


def test_draft_repairs_once_and_keeps_better_version():
    llm = TwoStepLLM()
    bot = NyaySaathi(llm=llm, kb=kb)
    st = new_state()
    st["issue"], st["case"] = "threats", {"summary": "ex-partner threatening to leak photos unless paid Rs 50,000"}
    res = bot.draft(st, "legal_notice", {"sender": "self", "sender_name": "Riya Sharma"})
    assert len(llm.calls) == 2 and res["repaired"] and res["problems"] == []
    assert "Section 308(3)" in res["document"] and "⚠️" not in res["document"]
    sys = llm.calls[0]
    assert "Balaji Traders" in sys and "Musumba" in sys          # judgments for and against are both given
    assert "BNS-EXTORT" in sys and "BSA-EVID" in sys and "Riya Sharma" in sys


def test_found_in_live_review():
    """Defects found by reviewing a live draft (8 Nov 2026)."""
    from nyay.guard import check
    # an act named in the heading covers sections on the next lines; an act in the NEXT sentence does not
    t = ("4.3. Information Technology Act, 2000 - Section 66E and Section 67:\n"
         "  (a) Ingredients: private images (Section 66E); obscene material (Section 67).\n"
         "FIR under Section 173 of the Bharatiya Nagarik Suraksha Sanhita, 2024. Section 999 of the Information Technology Act, 2000.")
    g = check(t, kb)
    assert [f["mention"] for f in g.flags if f["severity"] == "block"] == ["Section 999"]
    assert "Suraksha Sanhita, 2023" in g.text and "2024" not in g.text          # wrong year corrected in code
    assert "Consumer Protection Act, 1986" in check("the Consumer Protection Act, 1986 (old law)", kb).text
    # '7 (seven) days ... considered reply' is a stated period with its basis
    ok = GOOD.replace("7 days is a reasonable period for a considered written reply",
                      "You are given 7 (seven) days to send a considered written reply")
    assert lint_draft(ok, "legal_notice", "self", kb) == []
    bad = GOOD.replace("I, Riya Sharma, resident of", "Under instructions from myself, Riya Sharma, resident of")
    assert any("under instructions" in p for p in lint_draft(bad, "legal_notice", "self", kb))


def test_found_in_second_live_review():
    from nyay.guard import check
    hist = "decided under Section 387 IPC (now BNS Section 308(4)); and Section 384 of the IPC applies here."
    flagged = [f["mention"] for f in check(hist, kb).flags if f["severity"] == "block"]
    assert flagged == ["Section 384"]                        # history allowed, old law as the law to apply is not
    ok = GOOD.replace("7 days is a reasonable period for a considered written reply",
                      "A period of seven (7) days is granted for your considered written reply")
    assert lint_draft(ok, "legal_notice", "self", kb) == []
    llm = TwoStepLLM()
    llm.chat = lambda system, messages, **k: json.dumps({"document": GOOD.replace("Ref. No.: NIL", "Ref. No.: LN/2026/07")})
    res = NyaySaathi(llm=llm, kb=kb).draft(dict(new_state(), issue="threats"), "legal_notice", {"sender": "self"})
    assert "LN/2026/07" not in res["document"] and "[YOUR REFERENCE NUMBER, OR NIL]" in res["document"]
