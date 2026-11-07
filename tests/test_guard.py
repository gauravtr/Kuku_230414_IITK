"""Offline tests for the citation guard (no model needed): python -m pytest -q  or  python tests/test_guard.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from nyay.kb import KB
from nyay.guard import check

kb = KB()
def blocked(text):
    return [f["mention"] for f in check(text, kb).flags if f["severity"] == "block"]

CASES = [
    # (text, should_be_flagged)
    ("File within 2 years under Section 69 of the Consumer Protection Act [CPA-LIMIT].", False),
    ("Wages must be paid by the 7th under Section 17 of the Code on Wages [COW-17].", False),
    ("वेतन संहिता की धारा 45 के तहत दावा करें [COW-45]", False),
    ("Normal wear and tear is excluded (s.108(m), Transfer of Property Act) [TEN-WEAR].", False),
    ("Under NI Act 138 the drawer gets 15 days [NI-138].", False),
    ("The Code on Wages replaced the Payment of Wages Act, 1936 [COW-INFORCE].", False),
    ("Section 72 of the Consumer Protection Act lets you claim 18% interest.", True),     # real section, not on a card
    ("You can also file a case under Section 420 IPC for cheating.", True),             # repealed code
    ("Under BNS 318 this is cheating.", True),                                          # not on a card
    ("In Sharma v. Gupta (2019) 4 SCC 112 the Supreme Court held deposits carry interest.", True),
    ("Article 21 protects your right to shelter.", True),
    ("Under the Tenant Protection Act, 2015 you get double the deposit.", True),        # invented act
    ("See [XYZ-99] for details.", True),                                                # invented card id
    ("Pay before the 7th [COW-17] and see [FAKE-1].", True),                           # short invented id (bug found in smoke test)
    ("Section 45 lets you claim.", True),                                               # no act, no card cited
    ("Section 45 lets you claim [COW-45].", False),                                     # act inferred from cited card
    ("You paid Rs. 18,999 for the phone.", False),                                      # 'Rs.' must not look like 's.'
]

def run():
    bad = 0
    for text, expect in CASES:
        got = bool(blocked(text))
        status = "ok " if got == expect else "FAIL"
        bad += got != expect
        print(f"{status} flagged={got!s:5} expected={expect!s:5} | {text[:70]}  {blocked(text)}")
    print(f"\n{len(CASES)-bad}/{len(CASES)} guard tests pass")
    return bad

def test_guard():
    assert run() == 0

if __name__ == "__main__":
    sys.exit(run())
