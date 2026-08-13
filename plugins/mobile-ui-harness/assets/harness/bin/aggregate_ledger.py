#!/usr/bin/env python3
"""Aggregate per-run UI-finding sidecars into the durable harness ledger.

The mobile-UI harness has two finding producers:

  * Tier-1 deterministic assertions (`Tier1Assertions.kt`) — write structural
    blockers to `<module>/build/outputs/roborazzi/_findings.jsonl`.
  * The `mobile-design-evaluator` agent — writes taste/fidelity findings to
    `_eval_findings.jsonl` in the directory of PNGs it grades.

Both sidecars live under `build/` (gitignored, wiped on `clean`) so test runs and
agent passes stay hermetic. This script is the "close the loop" step: it collects
those ephemeral sidecars and appends them — deduplicated within the batch — to the
committed, append-only ledger at `harness/ledger/findings.jsonl`, then truncates
each consumed sidecar so a single run is recorded exactly once.

Dedup is intentionally *within a batch only*: an identical finding surfacing in a
later run is a fresh row, because cross-run recurrence is the signal the ratchet
(`/ui-distill`) and `/ui-metrics` are built to read. Those steps consume the ledger
this script maintains; they are deliberately NOT part of aggregation.

Usage:
    python3 harness/bin/aggregate_ledger.py            # collect from repo, fold into ledger
    python3 harness/bin/aggregate_ledger.py --dry-run  # show what would be appended
    python3 harness/bin/aggregate_ledger.py --iteration 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Canonical field order for ledger rows (spec §7). Insertion order is preserved
# by json.dumps on py3.7+, so rows read consistently.
FIELDS = [
    "ts", "screen", "config", "loop", "role", "tier", "category",
    "severity", "element", "finding", "fix", "iteration", "resolved", "deposit",
]

DEFAULT_LEDGER = "harness/ledger/findings.jsonl"
# Matches both `_findings.jsonl` (Tier-1) and `_eval_findings.jsonl` (evaluator)
# under any module's Roborazzi output dir. Does not match the canonical ledger,
# which lives outside build/outputs/roborazzi/.
DEFAULT_GLOB = "**/build/outputs/roborazzi/*findings.jsonl"

# Stable identity of a finding, ignoring run-specific fields (ts, iteration). Two
# findings sharing this key within one batch are the same observation.
DEDUP_KEY = ("screen", "config", "role", "category", "element", "finding")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


SCREEN_ALIAS_FILE = "screen-aliases.json"


def _norm_screen_key(s) -> str:
    """Lowercase, strip non-alphanumerics — absorbs casing/spacing variance."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def load_screen_aliases(ledger_path) -> dict:
    """Load {alias -> canonical} from `screen-aliases.json` beside the ledger (keys normalized).

    Reconciles the two lanes' screen names: the deterministic Tier-1 sidecar emits the PNG-filename
    slug (`songs`), while the LLM evaluator tends to emit the composable name (`SongsScreen`).
    Canonicalizing here — not in the evaluator — keeps screen identity deterministic regardless of
    what the LLM writes. Missing/invalid file → no aliases (screens are merely lowercased)."""
    p = Path(ledger_path).parent / SCREEN_ALIAS_FILE
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"warning: {p} is not valid JSON; ignoring screen aliases", file=sys.stderr)
        return {}
    return {_norm_screen_key(k): v for k, v in raw.items()}


def canonical_screen(s, aliases) -> str:
    """Map a raw screen name to its canonical slug via the alias table; fall back to a normalized
    (lowercased, alnum-only) key so casing/spacing alone can never split one screen into two."""
    key = _norm_screen_key(s)
    return aliases.get(key, key or "unknown")


def normalize(obj: dict, default_iteration=None, aliases=None) -> dict:
    """Coerce a raw finding into the canonical schema with sane defaults."""
    out = {
        "ts": obj.get("ts") or _now_iso(),
        "screen": canonical_screen(obj.get("screen", "unknown"), aliases or {}),
        "config": obj.get("config", ""),
        "loop": obj.get("loop", "impl"),
        "role": obj.get("role", "unknown"),
        "tier": obj.get("tier"),
        "category": obj.get("category", "unknown"),
        "severity": obj.get("severity", ""),
        "element": obj.get("element", ""),
        "finding": obj.get("finding", ""),
        "fix": obj.get("fix"),
        "iteration": obj.get("iteration"),
        "resolved": bool(obj.get("resolved", False)),
        "deposit": obj.get("deposit"),
    }
    if default_iteration is not None:
        out["iteration"] = default_iteration
    elif out["iteration"] is None:
        out["iteration"] = 1
    return out


def dedup(findings):
    """Collapse findings sharing DEDUP_KEY; keep the first. Returns (kept, n_dropped)."""
    seen = set()
    kept = []
    dropped = 0
    for f in findings:
        key = tuple(f.get(k) for k in DEDUP_KEY)
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(f)
    return kept, dropped


def read_sidecar(path: Path):
    """Parse one JSONL sidecar. Returns (findings, n_malformed). Blank/`#` lines skipped."""
    findings = []
    malformed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            findings.append(json.loads(s))
        except json.JSONDecodeError:
            malformed += 1
    return findings, malformed


def find_sidecars(root: Path, patterns, ledger_path: Path):
    """Glob sidecar files under root, excluding the canonical ledger itself."""
    ledger_abs = ledger_path.resolve()
    found = []
    for pat in patterns:
        for p in sorted(root.glob(pat)):
            if p.is_file() and p.resolve() != ledger_abs:
                found.append(p)
    return found


def aggregate(ledger_path, sidecar_paths, iteration=None, dry_run=False, keep_sidecars=False):
    """Fold sidecars into the ledger. Returns a summary dict."""
    ledger_path = Path(ledger_path)
    aliases = load_screen_aliases(ledger_path)
    raw = []
    consumed = []
    malformed_total = 0
    for path in sidecar_paths:
        path = Path(path)
        findings, malformed = read_sidecar(path)
        malformed_total += malformed
        if findings:
            raw.extend(normalize(f, default_iteration=iteration, aliases=aliases) for f in findings)
        # A sidecar is consumed even if empty/all-malformed, so stale files clear.
        consumed.append(path)

    deduped, dropped = dedup(raw)

    if not dry_run:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with ledger_path.open("a", encoding="utf-8") as fh:
            for f in deduped:
                fh.write(json.dumps(f, ensure_ascii=False, separators=(",", ":")) + "\n")
        if not keep_sidecars:
            for path in consumed:
                # Truncate rather than delete: the path may be recreated by the
                # next run, and an empty file globs to zero findings (harmless).
                path.write_text("", encoding="utf-8")

    return {
        "sidecars": len(consumed),
        "appended": len(deduped),
        "duplicates_collapsed": dropped,
        "malformed_lines": malformed_total,
        "ledger": str(ledger_path),
        "dry_run": dry_run,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"canonical ledger path (default: {DEFAULT_LEDGER})")
    ap.add_argument("--root", default=".", help="directory to search for sidecars (default: .)")
    ap.add_argument("--sidecar-glob", action="append", default=None,
                    help=f"glob for sidecars, repeatable (default: {DEFAULT_GLOB})")
    ap.add_argument("--iteration", type=int, default=None,
                    help="stamp this iteration number on every finding (default: keep producer's, else 1)")
    ap.add_argument("--keep-sidecars", action="store_true", help="do not truncate sidecars after consuming")
    ap.add_argument("--dry-run", action="store_true", help="report what would be appended; write nothing")
    args = ap.parse_args(argv)

    patterns = args.sidecar_glob or [DEFAULT_GLOB]
    root = Path(args.root)
    ledger_path = Path(args.ledger)

    sidecars = find_sidecars(root, patterns, ledger_path)
    if not sidecars:
        print(f"No finding sidecars under {root} matching {patterns}. Ledger unchanged.")
        return 0

    summary = aggregate(ledger_path, sidecars, iteration=args.iteration,
                        dry_run=args.dry_run, keep_sidecars=args.keep_sidecars)

    verb = "would append" if args.dry_run else "appended"
    print(
        f"{summary['sidecars']} sidecar(s) -> {verb} {summary['appended']} finding(s) "
        f"to {summary['ledger']} "
        f"(collapsed {summary['duplicates_collapsed']} dup(s), {summary['malformed_lines']} malformed line(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
