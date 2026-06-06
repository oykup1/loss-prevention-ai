"""
eval.py
-------
QA evaluation for the retrieval layer.
Runs 10 test queries and verifies the top results meet expected criteria.


"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from search import search

# ── Eval criteria ──────────────────────────────────────────────────────────────
# Each test defines:
#   query       — the natural language question
#   index       — which index to search
#   k           — how many results to retrieve
#   pass_if     — a function that takes the top result and returns True/False
#   description — what this test is checking

EVAL_TESTS = [
    {
        "id":          "EVAL_01",
        "query":       "incidents where jewelry was taken out of case",
        "index":       "incidents",
        "k":           5,
        "description": "Top result should be in accessories or purses zone",
        "pass_if":     lambda r: r["metadata"].get("zone") in ("accessories", "purses"),
    },
    {
        "id":          "EVAL_02",
        "query":       "incidents of purse alarm going off",
        "index":       "incidents",
        "k":           5,
        "description": "Top result should be purses zone or alarm_activation type",
        "pass_if":     lambda r: (
            r["metadata"].get("zone") == "purses" or
            r["metadata"].get("incident_type") == "alarm_activation"
        ),
    },
    {
        "id":          "EVAL_03",
        "query":       "incidents of people walking out of the store with visible merchandise being stolen",
        "index":       "incidents",
        "k":           5,
        "description": "Top result description should mention exit or entrance",
        "pass_if":     lambda r: any(
            word in r["text"].lower()
            for word in ("exit", "entrance", "exited", "fled", "main entrance")
        ),
    },
    {
        "id":          "EVAL_04",
        "query":       "incidents where beauty items were seen to be concealed",
        "index":       "incidents",
        "k":           5,
        "description": "Top result should be in beauty zone",
        "pass_if":     lambda r: r["metadata"].get("zone") == "beauty",
    },
    {
        "id":          "EVAL_05",
        "query":       "incidents where customers seen with large bags filled",
        "index":       "incidents",
        "k":           5,
        "description": "Top result description should mention bag or tote",
        "pass_if":     lambda r: any(
            word in r["text"].lower()
            for word in ("bag", "tote", "shopping bag", "reusable", "personal bag")
        ),
    },
    {
        "id":          "EVAL_06",
        "query":       "incidents where customer seen removing security stickers",
        "index":       "incidents",
        "k":           5,
        "description": "Top result should mention security tag or wrap removal",
        "pass_if":     lambda r: any(
            word in r["text"].lower()
            for word in ("security", "tag", "wrap", "sticker", "removed")
        ),
    },
    {
        "id":          "EVAL_07",
        "query":       "incidents where customer seen removing clothing security tag",
        "index":       "incidents",
        "k":           5,
        "description": "Top result incident_type should be tag_removal or mention tag in text",
        "pass_if":     lambda r: (
            r["metadata"].get("incident_type") == "tag_removal" or
            "tag" in r["text"].lower()
        ),
    },
    {
        "id":          "EVAL_08",
        "query":       "incident where customer seen wearing and leaving with clothing",
        "index":       "incidents",
        "k":           5,
        "description": "Top result should mention wearing or layering clothing",
        "pass_if":     lambda r: any(
            word in r["text"].lower()
            for word in ("wearing", "layering", "dressed", "under own clothing")
        ),
    },
    {
        "id":          "EVAL_09",
        "query":       "incident where customer seen concealing childrens clothing in bag",
        "index":       "incidents",
        "k":           5,
        "description": "Top result should be in kids zone",
        "pass_if":     lambda r: r["metadata"].get("zone") == "kids",
    },
    {
        "id":          "EVAL_10",
        "query":       "incident where associate has been suspected of concealing items",
        "index":       "incidents",
        "k":           5,
        "description": "Top result should be backroom zone or mention associate",
        "pass_if":     lambda r: (
            r["metadata"].get("zone") == "backroom" or
            "associate" in r["text"].lower()
        ),
    },
]


# ── Runner ─────────────────────────────────────────────────────────────────────
def run_eval():
    print("\n" + "="*60)
    print("RETRIEVAL EVAL — Retail Loss Intelligence Platform")
    print("="*60)

    passed = 0
    failed = 0
    failures = []

    for test in EVAL_TESTS:
        results = search(test["query"], index_name=test["index"], k=test["k"])

        if not results:
            status  = "FAIL"
            reason  = "No results returned"
            failed += 1
            failures.append({**test, "reason": reason, "top_result": None})
        else:
            top = results[0]
            if test["pass_if"](top):
                status  = "PASS"
                passed += 1
            else:
                status  = "FAIL"
                reason  = f"Top result zone='{top['metadata'].get('zone')}' type='{top['metadata'].get('incident_type')}'"
                failed += 1
                failures.append({**test, "reason": reason, "top_result": top})

        # Print result
        top_result = results[0] if results else None
        score      = top_result["score"] if top_result else 0
        zone       = top_result["metadata"].get("zone", "unknown") if top_result else "n/a"

        print(f"\n[{status}] {test['id']} — score: {score}")
        print(f"  Query:    {test['query']}")
        print(f"  Expected: {test['description']}")
        print(f"  Got:      zone={zone}, type={top_result['metadata'].get('incident_type') if top_result else 'n/a'}")
        if status == "FAIL":
            print(f"  ✗ FAILED: {reason}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print(f"RESULTS: {passed}/10 passed")
    precision = passed / 10
    print(f"Retrieval precision: {precision:.0%}")

    if failures:
        print(f"\nFailed tests ({len(failures)}):")
        for f in failures:
            print(f"  {f['id']}: {f['query'][:50]}...")
            if f["top_result"]:
                print(f"    Top result text: {f['top_result']['text'][:80]}...")

    if precision == 1.0:
        print("\n✓ All tests passing. Retrieval layer is production ready.")
    elif precision >= 0.8:
        print("\n⚠ Most tests passing. Review failures before proceeding.")
    else:
        print("\n✗ Too many failures. Review chunking and embedding strategy.")

    print("="*60 + "\n")
    return passed, failed


if __name__ == "__main__":
    run_eval()