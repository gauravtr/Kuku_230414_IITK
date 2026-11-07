"""Dev tool for the `manual` provider: store a response for a pending prompt key.
Used when no API is reachable (e.g. an offline sandbox): a person or another model
answers the exact prompt in outputs/cache/_pending/<key>.prompt.md, and this writes it
to the cache so run_tests.py replays it through the same guard + scoring code.
    python tools/answer_pending.py <responses.json> [--model NAME]
responses.json = {"<key>": "<raw model output string>", ...}
"""
import json, pathlib, sys
cache = pathlib.Path(__file__).resolve().parent.parent / "outputs" / "cache"
src = json.loads(pathlib.Path(sys.argv[1]).read_text())
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "manual"
for key, resp in src.items():
    p = cache / "_pending" / f"{key}.prompt.md"
    if not p.exists():
        print("no pending prompt for", key); continue
    last_user = p.read_text().rsplit("# USER\n", 1)[-1][:300]
    (cache / f"{key}.json").write_text(json.dumps({"model": model, "response": resp, "last_user": last_user}, ensure_ascii=False, indent=1))
    p.rename(p.with_suffix(".answered.md"))
    print("stored", key)
