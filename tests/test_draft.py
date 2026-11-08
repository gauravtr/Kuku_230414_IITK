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


def test_found_in_third_live_review():
    proved = GOOD.replace("the conduct in paras 2.1-2.2, if established, would amount to putting\nme in fear",
                          "these ingredients are satisfied by paras 2.1-2.2, which put\nme in fear")
    assert any("treats the allegation as proved" in p for p in lint_draft(proved, "legal_notice", "self", kb))
    bare = GOOD.replace("Section 308(3) of the Bharatiya", "Section 308 of the Bharatiya")
    assert any("exact sub-section of Section 308" in p for p in lint_draft(bare, "legal_notice", "self", kb))
    case = GOOD.replace("4. LEGAL POSITION\n", "4. LEGAL POSITION\nIn M/s Balaji Traders v. State of U.P. (2025) the Court held so.\n")
    assert any("2025 INSC 806" in p for p in lint_draft(case, "legal_notice", "self", kb))
    assert lint_draft(case.replace("(2025) the", "(2025), 2025 INSC 806, the"), "legal_notice", "self", kb) == []
    from nyay.engine import NyaySaathi as _N  # the Ref. No. rewrite keeps the colon
    llm = TwoStepLLM()
    llm.chat = lambda system, messages, **k: json.dumps({"document": GOOD.replace("Ref. No.: NIL", "Ref. No.: LN/2026/07")})
    res = _N(llm=llm, kb=kb).draft(dict(new_state(), issue="threats"), "legal_notice", {"sender": "self"})
    assert "Ref. No.: [YOUR REFERENCE NUMBER, OR NIL]" in res["document"]


def test_judgments_only_when_they_fit_the_facts():
    """A Supreme Court ruling is suggested only when its fact pattern appears in what the client said."""
    from nyay.engine import pick_judgments
    ids = lambda j: {c["id"] for g in ("for", "against") for c in (j or {}).get(g, [])}   # noqa: E731
    same = lambda x: x   # noqa: E731
    # an ordinary deposit case: forfeiture rulings fit; 'stayed on after tenancy' and 'lock-in clause' rulings do not
    w = "My landlord kept my whole deposit of Rs 40,000 saying painting is needed. I vacated on 1 Oct after giving notice."
    j = pick_judgments(kb, "deposit", "tenant", {}, same, w)
    assert {"JUD-MAULA", "JUD-KAILASH"} <= ids(j) and not {"JUD-ATMARAM", "JUD-SBATRA"} & ids(j)
    assert any("whole deposit" in c["quote"] for c in j["for"])          # the client's own words are the reason shown
    # ...until the client says they stayed on: then the ruling against them is shown, never hidden
    j = pick_judgments(kb, "deposit", "tenant", {}, same, w + " I stayed 2 extra months after the agreement ended.")
    assert "JUD-ATMARAM" in {c["id"] for c in j["against"]}
    # private-company salary: the State-corporation and 'not a workman' rulings stay out
    j = pick_judgments(kb, "salary", "employee", {}, same, "My private IT company (ABC Corporation) hasn't paid salary for 3 months.")
    assert "JUD-BIHAR26" in ids(j) and not {"JUD-HINGORANI", "JUD-ADYANTHAYA", "JUD-KELAWALA"} & ids(j)
    # a plain cheque bounce: no loan-capacity or advance-cheque rulings
    j = pick_judgments(kb, "cheque", "payee", {}, same, "The cheque he gave me for the goods bounced, insufficient funds.")
    assert ids(j) == {"JUD-RANGAPPA"}
    # nothing fits: nothing is shown; if the client asked for case law, say honestly that none fits
    assert pick_judgments(kb, "domestic", "woman", {}, same, "I want a divorce.") is None
    j = pick_judgments(kb, "domestic", "woman", {}, same, "I want a divorce. Any Supreme Court judgment?", asked=True)
    assert j["none_fit"] and not j["for"] and not j["against"]
    # once the model has weighed the facts, a favourable ruling it left out is dropped; a fitting adverse one is kept
    w = "He threatens on WhatsApp to leak my photos unless I pay Rs 50,000. I have screenshots."
    j = pick_judgments(kb, "threats", "victim", {"JUD-BALAJI": "fits"}, same, w)
    assert {c["id"] for c in j["for"]} == {"JUD-BALAJI"} and "JUD-MUSUMBA" in {c["id"] for c in j["against"]}


class CaptureLLM:
    name = "fake"

    def __init__(self, reply):
        self.reply, self.system = reply, ""

    def chat(self, system, messages, json_mode=False, **k):
        self.system = system
        return json.dumps(self.reply)


def test_model_sees_only_fitting_rulings_and_answer_is_structured():
    llm = CaptureLLM({"issue": "deposit", "headline": "You have a strong claim to the full deposit [TEN-WEAR].",
                      "reply": "Painting is normal wear and tear.", "assessment": {"strength": "strong", "why": "x"},
                      "case_file": {"summary": "deposit", "deadlines": ["Consumer complaint within 2 years [CPA-LIMIT]",
                                    "File under Section 999 of the Indian Penal Code by Friday"],
                                    "proof_have": ["rent agreement"], "proof_missing": ["move-out photos"]},
                      "next_steps": [{"step": "Send a legal notice", "by_when": "this week"}], "open_questions": []})
    bot = NyaySaathi(llm=llm, kb=kb)
    r = bot.turn(new_state(), "Landlord kept my whole security deposit of Rs 40,000 for painting after I vacated the flat.")
    assert "Maula Bux" in llm.system and "Atma Ram" not in llm.system and "Satish Batra" not in llm.system
    assert r["headline"] and "[" not in r["headline"]                  # card markers removed from the headline
    assert r["deadlines"] == ["Consumer complaint within 2 years"]     # the unverified-law deadline is dropped
    assert r["proof_have"] == ["rent agreement"] and r["proof_missing"] == ["move-out photos"]


def test_extortion_message_routes_to_threats_not_salary():
    """Found while previewing: 'pay 50,000 or I post your private photos' tied with salary on the word 'pay'."""
    assert next(iter(kb.classify("My ex sent a WhatsApp: pay 50,000 or I post your private photos. I haven't paid."))) == "threats"
    assert next(iter(kb.classify("My company did not pay my salary for 2 months"))) == "salary"
    assert next(iter(kb.classify("Landlord not returning deposit, says I must pay for painting"))) == "deposit"


def test_found_in_live_test_runs():
    """Found running the long test cases on the live app (8 Nov 2026)."""
    from nyay.engine import parse_json, reply_from_broken_json
    # Gemini dropped a quote on a key: one slip must not show the client raw JSON
    bad = '{\n  "people": {\n    "user": "Employee",\n    other_side": "Technova"\n  },\n  "reply": "ठीक है",\n}'
    assert parse_json(bad)["people"]["other_side"] == "Technova"
    assert reply_from_broken_json('{"reply": "Line one\\nline two", "case_file": {oops') == "Line one\nline two"
    # 'no managerial role' denies the fact pattern of the sales/managerial ruling; 'not paid for 3 months' doesn't
    fit = lambda t: [j["id"] for j, _ in kb.judgments_fitting("salary", t)]   # noqa: E731
    assert fit("software tester, no managerial role, PF unpaid") == []
    assert fit("I was not a manager or supervisor") == []
    assert "JUD-ADYANTHAYA" in fit("I was a sales manager")
    assert fit("salary not paid for 3 months") == ["JUD-BIHAR26"]


class BrokenThenFixedLLM:
    name = "fake"

    def __init__(self):
        self.n = 0

    def chat(self, system, messages, json_mode=False, **k):
        self.n += 1
        return "{not json at all" if self.n == 1 else json.dumps({"issue": "deposit", "reply": "Fixed reply.", "case_file": {}})


def test_unreadable_reply_is_asked_again_once():
    llm = BrokenThenFixedLLM()
    r = NyaySaathi(llm=llm, kb=kb).turn(new_state(), "Landlord kept my deposit")
    assert llm.n == 2 and r["reply_body"] == "Fixed reply." and not r["parse_error"]


def test_empty_gemini_reply_is_retried_then_falls_back(monkeypatch):
    """Found in the live test runs: Gemini 2.5 sometimes answers 200 OK with no text."""
    import os
    from nyay import llm as L
    monkeypatch.setitem(os.environ, "GEMINI_API_KEY", "x")

    class R:
        def __init__(self, d):
            self.d, self.status_code, self.ok = d, 200, True

        def json(self):
            return self.d

        def raise_for_status(self):
            pass
    empty, good = {"candidates": [{"content": {}, "finishReason": "STOP"}]}, {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    seq = [R(empty), R(empty), R(good)]
    monkeypatch.setattr(L.requests, "post", lambda *a, **k: seq.pop(0))
    assert L.LLM("gemini", "gemini-2.5-flash")._gemini_post({"contents": []}) == "ok"      # asked again
    seq[:] = [R(empty)] * 3 + [R(good)]
    m = L.LLM("gemini", "gemini-2.5-flash")
    assert m._gemini_post({"contents": []}) == "ok" and m.model != "gemini-2.5-flash"      # next model answered


def test_found_in_live_test_runs_2():
    """Case 06: the model correctly refused a made-up case; the guard must not count the refusal as a citation.
    Also: 'I vacated ... after the lease ended' is not 'stayed on after the lease ended'."""
    from nyay.guard import check
    ok = check("I cannot confirm 'Sharma v. Kapoor (2019)' because it is not in my verified database.", kb)
    assert ok.clean and "⚠️" not in ok.text and ok.flags[0]["severity"] == "note"
    bad = check("As held in Sharma v. Kapoor (2019), you get 18% interest.", kb)
    assert not bad.clean and "⚠️[unverified]" in bad.text
    fit = lambda t: [j["id"] for j, _ in kb.judgments_fitting("deposit", t)]   # noqa: E731
    assert "JUD-ATMARAM" not in fit("I vacated on 30 June 2026 after the lease ended.")
    assert "JUD-ATMARAM" in fit("I stayed 2 extra months after the agreement ended.")


def test_found_in_live_test_runs_3():
    """Case 13: a draft named the BNS in its legal-position section and later wrote 'Section 308(4)' in the
    authorities paragraph, 400+ characters away. A section of an act named elsewhere in the text is verified;
    a section that exists in no named act is still blocked."""
    from nyay.guard import check
    far = "Section 308(3) of the Bharatiya Nyaya Sanhita, 2023 applies. " + "x " * 400 + "That case concerned Section 308(4)."
    assert check(far, kb).clean
    assert [f["mention"] for f in check(far.replace("Section 308(4)", "Section 999"), kb).flags] == ["Section 999"]
    assert not check("That case concerned Section 308(4).", kb).clean


def test_found_in_live_test_runs_4():
    """Case 13 again: the model wrote '2005 INSC 806' for Balaji Traders (2025 INSC 806), and a BNS section came
    right after an IT Act paragraph."""
    from nyay.guard import check
    g = check("The Supreme Court in M/s Balaji Traders v. State of U.P. (2025), 2005 INSC 806 held so.", kb)
    assert "2025 INSC 806" in g.text and "2005 INSC" not in g.text
    t = ("4.2 Section 351(2) of the Bharatiya Nyaya Sanhita, 2023 applies.\n4.3 Section 66E of the Information Technology Act, "
         "2000 penalises publishing images.\n4.4 The same reasoning supports Section 308(3).")
    assert check(t, kb).clean
    assert not check(t.replace("Section 308(3)", "Section 999"), kb).clean


class AccusedLLM:
    name = "fake"

    def chat(self, system, messages, json_mode=False, **k):
        return json.dumps({"issue": "domestic", "reply": "Get a lawyer today; carry your documents.", "case_file": {},
                           "judgments": {"client_side": "respondent", "notes": {}}})


def test_accused_husband_gets_no_victim_safety_block():
    """Case 08: a husband named in a dowry FIR was shown 'If she is in danger right now: call 112, 181'."""
    r = NyaySaathi(llm=AccusedLLM(), kb=kb).turn(new_state(), "My wife's family filed a dowry FIR against me and my parents.")
    assert "If she is in danger" not in r["reply_body"] and "violence" not in r["escalation"]["safety"]


def test_model_side_labels_are_normalized():
    """Case 08: in later turns the model said client_side 'husband'; it defaulted to 'woman' and flipped the rulings."""
    from nyay.engine import normalize_side
    assert normalize_side(kb, "domestic", "Husband") == "respondent"
    assert normalize_side(kb, "domestic", "the wife") == "woman"
    assert normalize_side(kb, "domestic", "", "respondent") == "respondent"
    assert normalize_side(kb, "deposit", "Tenant") == "tenant" and normalize_side(kb, "cheque", "borrower") == "drawer"
    assert normalize_side(kb, "domestic", "xyz") is None


def test_withholding_without_any_damage_claim_fits_the_forfeiture_rulings():
    """Found in the live run of case 06: 'sitting on my deposit ... doesn't have money right now' matched no ruling."""
    from nyay.engine import pick_judgments
    w = ("My landlord has been sitting on my Rs 1,00,000 security deposit for 4 months. He keeps saying 'next week'. "
         "He hasn't claimed any damage, he just says he doesn't have money right now.")
    j = pick_judgments(kb, "deposit", "tenant", {}, lambda x: x, w)
    assert {"JUD-MAULA", "JUD-KAILASH"} <= {c["id"] for c in j["for"]}
    assert not {"JUD-ATMARAM", "JUD-SBATRA"} & {c["id"] for g in ("for", "against") for c in j[g]}
