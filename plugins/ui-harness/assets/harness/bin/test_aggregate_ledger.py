#!/usr/bin/env python3
"""Self-test for aggregate_ledger.py. Run: python3 harness/bin/test_aggregate_ledger.py

No deps; uses tempdirs + plain asserts. Exits non-zero on first failure.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aggregate_ledger as agg  # noqa: E402


def _tier1_line(screen, config, element, finding, dup=False):
    obj = {
        "ts": "2026-06-22T10:00:00Z", "screen": screen, "config": config,
        "loop": "impl", "role": "tier1", "tier": 1, "category": "touch-target",
        "severity": "blocker", "element": element, "finding": finding,
        "fix": None, "iteration": 1, "resolved": False, "deposit": None,
    }
    return json.dumps(obj)


def _eval_line(screen, config, element, finding):
    obj = {
        "ts": "2026-06-22T10:05:00Z", "screen": screen, "config": config,
        "loop": "impl", "role": "evaluator", "tier": 2, "category": "spacing",
        "severity": "warn", "element": element, "finding": finding,
        "fix": "use Spacing.md", "iteration": None, "resolved": False, "deposit": None,
    }
    return json.dumps(obj)


def _read_ledger(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def test_basic_append_and_dedup():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        roborazzi = d / "feature" / "x" / "build" / "outputs" / "roborazzi"
        roborazzi.mkdir(parents=True)
        # Tier-1 sidecar with a duplicate line (re-run-without-clean simulation).
        (roborazzi / "_findings.jsonl").write_text(
            "\n".join([
                _tier1_line("Songs", "360_font2_0", "Play", "tap area 32x32"),
                "",  # blank line ignored
                "# comment ignored",
                _tier1_line("Songs", "360_font2_0", "Play", "tap area 32x32"),  # dup
                "{ not json",  # malformed
            ]) + "\n"
        )
        # Evaluator sidecar in the same dir, different filename.
        (roborazzi / "_eval_findings.jsonl").write_text(
            _eval_line("Songs", "360_font2_0_dark", "Title", "cramped") + "\n"
        )
        ledger = d / "harness" / "ledger" / "findings.jsonl"

        sidecars = agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger)
        assert len(sidecars) == 2, f"expected 2 sidecars, got {len(sidecars)}"

        summary = agg.aggregate(ledger, sidecars)
        assert summary["appended"] == 2, summary
        assert summary["duplicates_collapsed"] == 1, summary
        assert summary["malformed_lines"] == 1, summary

        rows = _read_ledger(ledger)
        assert len(rows) == 2, rows
        roles = sorted(r["role"] for r in rows)
        assert roles == ["evaluator", "tier1"], roles
        # Evaluator's null iteration defaults to 1.
        ev = next(r for r in rows if r["role"] == "evaluator")
        assert ev["iteration"] == 1, ev
        # All canonical fields present.
        for r in rows:
            assert set(r.keys()) == set(agg.FIELDS), r.keys()

        # Sidecars truncated (consumed exactly once).
        assert (roborazzi / "_findings.jsonl").read_text() == ""
        assert (roborazzi / "_eval_findings.jsonl").read_text() == ""


def test_recurrence_across_runs_is_kept():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        roborazzi = d / "m" / "build" / "outputs" / "roborazzi"
        roborazzi.mkdir(parents=True)
        ledger = d / "harness" / "ledger" / "findings.jsonl"
        line = _tier1_line("Songs", "411", "Btn", "tiny")

        # Run 1
        (roborazzi / "_findings.jsonl").write_text(line + "\n")
        agg.aggregate(ledger, agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger))
        # Run 2: same finding recurs in a fresh run.
        (roborazzi / "_findings.jsonl").write_text(line + "\n")
        agg.aggregate(ledger, agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger))

        rows = _read_ledger(ledger)
        assert len(rows) == 2, f"recurrence across runs must be preserved, got {rows}"


def test_iteration_override():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        roborazzi = d / "m" / "build" / "outputs" / "roborazzi"
        roborazzi.mkdir(parents=True)
        ledger = d / "harness" / "ledger" / "findings.jsonl"
        (roborazzi / "_findings.jsonl").write_text(_tier1_line("Songs", "411", "B", "x") + "\n")
        agg.aggregate(ledger, agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger), iteration=3)
        rows = _read_ledger(ledger)
        assert rows[0]["iteration"] == 3, rows


def test_dry_run_writes_nothing():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        roborazzi = d / "m" / "build" / "outputs" / "roborazzi"
        roborazzi.mkdir(parents=True)
        ledger = d / "harness" / "ledger" / "findings.jsonl"
        sc = roborazzi / "_findings.jsonl"
        sc.write_text(_tier1_line("Songs", "411", "B", "x") + "\n")
        summary = agg.aggregate(ledger, agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger), dry_run=True)
        assert summary["appended"] == 1, summary
        assert not ledger.exists(), "dry-run must not create the ledger"
        assert sc.read_text() != "", "dry-run must not truncate sidecars"


def test_ledger_not_globbed_as_sidecar():
    # A ledger literally named findings.jsonl must never be consumed as a sidecar.
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "harness" / "ledger" / "findings.jsonl"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(_tier1_line("Old", "411", "B", "x") + "\n")
        sidecars = agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger)
        assert sidecars == [], sidecars


def test_screen_canonicalization_reconciles_lanes():
    # The two lanes name the same screen differently — Tier-1 emits the filename slug
    # ("songs"), the evaluator the composable name ("SongsScreen"). The alias file must
    # collapse both to one canonical id so /ui-distill clusters per screen.
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "harness" / "ledger" / "findings.jsonl"
        ledger.parent.mkdir(parents=True)
        (ledger.parent / "screen-aliases.json").write_text(
            json.dumps({"SongsScreen": "songs", "ChordProgressionField": "field"})
        )
        rob = d / "m" / "build" / "outputs" / "roborazzi"
        rob.mkdir(parents=True)
        (rob / "_findings.jsonl").write_text(_tier1_line("songs", "411", "Btn", "tiny") + "\n")
        (rob / "_eval_findings.jsonl").write_text(_eval_line("SongsScreen", "411", "Title", "cramped") + "\n")

        agg.aggregate(ledger, agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger))
        rows = _read_ledger(ledger)
        assert sorted({r["screen"] for r in rows}) == ["songs"], [r["screen"] for r in rows]


def test_unmapped_screen_falls_back_to_normalized():
    # No alias file: a screen still gets lowercased/alnum-stripped so casing can't split it.
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ledger = d / "harness" / "ledger" / "findings.jsonl"
        ledger.parent.mkdir(parents=True)
        rob = d / "m" / "build" / "outputs" / "roborazzi"
        rob.mkdir(parents=True)
        (rob / "_findings.jsonl").write_text(_tier1_line("New Screen", "411", "B", "x") + "\n")
        agg.aggregate(ledger, agg.find_sidecars(d, [agg.DEFAULT_GLOB], ledger))
        assert _read_ledger(ledger)[0]["screen"] == "newscreen"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
