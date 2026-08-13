#!/usr/bin/env python3
"""Self-test for distill_ledger.py. Run: python3 harness/bin/test_distill_ledger.py

No deps; tempdirs + plain asserts. Exits non-zero on first failure.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import distill_ledger as dl  # noqa: E402


def _f(category, screen, config="411", element="el", finding="x", fix=None,
       resolved=False, deposit=None, role="tier1", tier=1):
    return {
        "ts": "2026-06-24T10:00:00Z", "screen": screen, "config": config, "loop": "impl",
        "role": role, "tier": tier, "category": category, "severity": "blocker",
        "element": element, "finding": finding, "fix": fix, "iteration": 1,
        "resolved": resolved, "deposit": deposit,
    }


def _write(ledger, findings):
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("\n".join(json.dumps(f) for f in findings) + "\n")


def test_threshold_promotes_at_three():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "findings.jsonl"
        out = d / "promotions.md"
        _write(ledger, [
            _f("insets", "songs", config="411"),
            _f("insets", "field", config="360"),
            _f("insets", "picker", config="411_dark"),
            _f("color", "songs"),   # only 1 -> watchlist
        ])
        dl.main(["--ledger", str(ledger), "--out", str(out)])
        md = out.read_text()
        # insets is over threshold and maps to a Tier-1 assertion deposit.
        assert "`insets`" in md and "Tier1Assertions.kt" in md, md
        assert "## Candidates (1)" in md, md
        # color is below threshold -> watchlist, not a candidate.
        assert "`color` — 1" in md, md


def test_below_threshold_not_promoted():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "findings.jsonl"
        out = d / "promotions.md"
        _write(ledger, [_f("touch-target", "songs"), _f("touch-target", "songs")])
        dl.main(["--ledger", str(ledger), "--out", str(out)])
        md = out.read_text()
        assert "No candidates over threshold" in md, md
        assert "`touch-target` — 2" in md, md  # on the watchlist


def test_ladder_mapping():
    assert dl.ladder_for("touch-target")[0] == "T2 gate"
    assert "Tier1Assertions" in dl.ladder_for("insets")[1]
    assert dl.ladder_for("reuse")[0] == "T3 structural"
    assert dl.ladder_for("color")[0] == "T1 soft"
    assert dl.ladder_for("totally-unknown") == dl.UNKNOWN_LADDER


def test_resolved_and_deposited_are_excluded():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "findings.jsonl"
        out = d / "promotions.md"
        _write(ledger, [
            _f("insets", "songs", resolved=True),                 # closed
            _f("insets", "field", deposit="already promoted"),    # deposited
            _f("insets", "picker"),                               # only 1 open
        ])
        dl.main(["--ledger", str(ledger), "--out", str(out)])
        assert "No candidates over threshold" in out.read_text()


def test_mark_deposit_closes_and_is_idempotent():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "findings.jsonl"
        _write(ledger, [_f("insets", "songs"), _f("insets", "field"), _f("color", "songs")])

        n = dl.mark_deposit(ledger, "insets", "Tier1Assertions inset check")
        assert n == 2, n
        rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
        insets = [r for r in rows if r["category"] == "insets"]
        assert all(r["resolved"] and r["deposit"] == "Tier1Assertions inset check" for r in insets)
        # untouched category stays open
        assert not any(r["resolved"] for r in rows if r["category"] == "color")
        # idempotent: nothing left open to mark
        assert dl.mark_deposit(ledger, "insets", "x") == 0


def test_cross_screen_ranks_above_single_screen():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "findings.jsonl"
        out = d / "promotions.md"
        _write(ledger, [
            # spacing: 3 findings but all one screen
            _f("spacing", "songs"), _f("spacing", "songs"), _f("spacing", "songs"),
            # insets: 3 findings across 3 screens -> broader, should rank first
            _f("insets", "songs"), _f("insets", "field"), _f("insets", "picker"),
        ])
        dl.main(["--ledger", str(ledger), "--out", str(out)])
        md = out.read_text()
        assert md.index("`insets`") < md.index("`spacing`"), "cross-screen cluster must rank first"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
