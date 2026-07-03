#!/usr/bin/env python3
"""Self-test for metrics_ledger.py. Run: python3 harness/bin/test_metrics_ledger.py

No deps; tempdirs + plain asserts. Exits non-zero on first failure.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics_ledger as m  # noqa: E402


def _f(screen, category="touch-target", tier=1, iteration=1, resolved=False, deposit=None):
    return {
        "ts": "2026-06-24T10:00:00Z", "screen": screen, "config": "411", "loop": "impl",
        "role": "tier1", "tier": tier, "category": category, "severity": "blocker",
        "element": "el", "finding": "x", "fix": None, "iteration": iteration,
        "resolved": resolved, "deposit": deposit,
    }


def test_iterations_to_pass():
    its = m.iterations_to_pass([
        _f("songs", iteration=1), _f("songs", iteration=2), _f("songs", iteration=3),
        _f("field", iteration=1, resolved=True, deposit="closed"),
    ])
    assert its["songs"]["iters"] == 3, its
    assert its["songs"]["open"] == 3, its
    assert its["field"]["iters"] == 1, its
    assert its["field"]["open"] == 0, its  # resolved+deposited -> not open


def test_first_pass_yield():
    clean, dirty, screens = m.first_pass_yield([
        _f("songs", tier=1, iteration=1),                 # dirty: tier1 at iter1
        _f("field", tier=2, iteration=1),                 # clean: only tier2 at iter1
        _f("picker", tier=1, iteration=2),                # clean: tier1 but at iter2, not iter1
    ])
    assert dirty == {"songs"}, dirty
    assert clean == {"field", "picker"}, clean
    assert len(screens) == 3


def test_recurrence_after_deposit():
    rec = m.recurrence_after_deposit([
        # touch-target: deposited, no open after -> stuck
        _f("songs", category="touch-target", resolved=True, deposit="Tier1 min-size"),
        _f("field", category="touch-target", resolved=True, deposit="Tier1 min-size"),
        # insets: deposited once, then recurred (an open one appeared after)
        _f("songs", category="insets", resolved=True, deposit="Tier1 inset check"),
        _f("picker", category="insets"),  # open -> recurrence
        # color: never deposited -> not in the report
        _f("songs", category="color", tier=2),
    ])
    assert "color" not in rec, rec
    assert rec["touch-target"]["recurred"] == 0, rec
    assert rec["touch-target"]["closed"] == 2, rec
    assert rec["insets"]["recurred"] == 1, rec


def test_render_flags_recurrence_and_renders_three_sections():
    md = m.render([
        _f("songs", category="insets", resolved=True, deposit="Tier1 inset check"),
        _f("picker", category="insets"),  # recurrence
        _f("field", tier=2, iteration=1),
    ])
    assert "## 1. Iterations-to-pass" in md
    assert "## 2. First-pass yield" in md
    assert "## 3. Recurrence after deposit" in md
    assert "⚠️" in md and "`insets`" in md, "must flag the recurring deposited category"


def test_empty_ledger_renders_gracefully():
    md = m.render([])
    assert "No findings yet" in md, md


def test_end_to_end_writes_file():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "findings.jsonl"
        out = d / "metrics.md"
        ledger.write_text("\n".join(json.dumps(x) for x in [
            _f("songs", category="insets", resolved=True, deposit="dep"),
            _f("picker", category="insets"),
        ]) + "\n")
        m.main(["--ledger", str(ledger), "--out", str(out)])
        assert out.exists() and "Recurrence after deposit" in out.read_text()


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
