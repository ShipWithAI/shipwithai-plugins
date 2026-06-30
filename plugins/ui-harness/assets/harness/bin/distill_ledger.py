#!/usr/bin/env python3
"""Distill the feedback ledger into promotion candidates — the ratchet's act-half.

Reads `harness/ledger/findings.jsonl`, clusters UNRESOLVED findings by category, and flags
every category at/over the promotion threshold (default: seen >= 3 times) as a *pattern* worth
hardening rather than a one-off. For each, it picks the most permanent substrate the finding can
reach on the **durability ladder** (spec §7) and writes a proposal to `harness/ledger/promotions.md`
for human approval.

It deliberately does NOT implement promotions — that's judgment + code, owned by the `/ui-distill`
command and you. Two modes:

    analyze (default):   python3 harness/bin/distill_ledger.py
    mark deposited:      python3 harness/bin/distill_ledger.py --deposit touch-target \
                             --label "Tier1Assertions min-size check (#123)"

Marking sets `resolved=true` + `deposit=<label>` on a category's open findings (rewriting the
ledger in place) so they stop surfacing as candidates and feed `/ui-metrics`' "recurrence after
deposit" signal — if a deposited category keeps recurring, the promotion didn't stick.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_LEDGER = "harness/ledger/findings.jsonl"
DEFAULT_PROMOTIONS = "harness/ledger/promotions.md"
DEFAULT_THRESHOLD = 3

# Durability ladder (spec §7): for each finding category, the most permanent substrate it can
# reach and the concrete deposit in THIS repo. (rung, concrete deposit).
LADDER = {
    # Mechanically checkable structural blockers -> a deterministic Tier-1 assertion.
    "touch-target":  ("T2 gate", "Add/extend a Tier-1 assertion in Tier1Assertions.kt (min tap-size check)."),
    "zero-size":     ("T2 gate", "Extend the zero-size Tier-1 assertion in Tier1Assertions.kt."),
    "out-of-bounds": ("T2 gate", "Extend the out-of-bounds Tier-1 assertion in Tier1Assertions.kt."),
    "overflow":      ("T2 gate", "Tag critical Text with Modifier.testTag(\"noTruncate\"); Tier-1 then fails on overflow."),
    "truncation":    ("T2 gate", "Tag the offending Text with Modifier.testTag(\"noTruncate\") so Tier-1 catches it."),
    "insets":        ("T2 gate", "Implement the stubbed insets Tier-1 assertion in Tier1Assertions.kt (inject non-zero WindowInsets)."),
    "contrast":      ("T2 gate", "Add a contrast Tier-1 assertion (sample fg/bg, assert >= WCAG AA) — it's measurable."),
    # Reuse / off-theme -> structural boundary (Konsist) or a promoted component.
    "reuse":         ("T3 structural", "Promote the reinvented component into core:designsystem (+ catalog + golden), or tighten a Konsist rule in ArchitectureTest.kt."),
    # Measurable layout -> gate the measurable part; the rest stays taste.
    "spacing":       ("T2 gate / T1 soft", "If one off-grid value recurs, assert it; otherwise a minimal rubric line."),
    # Pure taste -> a minimal rubric line (kept short; delete once anything upstream enforces it).
    "hierarchy":     ("T1 soft", "Concise rubric line in mobile-design SKILL.md."),
    "color":         ("T1 soft", "Rubric line (M3 roles, real dark mode) in mobile-design SKILL.md."),
    "typography":    ("T1 soft", "Rubric line in mobile-design SKILL.md."),
    "affordance":    ("T1 soft", "Rubric line in mobile-design SKILL.md."),
    "state":         ("T1 soft", "Rubric line (empty/error/loading states) in mobile-design SKILL.md."),
    # Target-matching -> tighten the frozen target or the impl.
    "fidelity":      ("target", "Reconcile against harness/targets/<screen>.png — adjust the impl or re-freeze the target."),
}
UNKNOWN_LADDER = ("T1 soft", "No ladder mapping — review manually; add a rubric line if mechanizable.")


def ladder_for(category: str):
    return LADDER.get(category, UNKNOWN_LADDER)


def load_findings(ledger_path) -> list:
    p = Path(ledger_path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            out.append(json.loads(s))
        except json.JSONDecodeError:
            print(f"warning: skipping malformed ledger line: {s[:80]}", file=sys.stderr)
    return out


def is_open(f: dict) -> bool:
    """Unresolved and not yet promoted — the only findings distill considers."""
    return not f.get("resolved", False) and f.get("deposit") in (None, "")


def cluster(findings: list) -> dict:
    """Group OPEN findings by category. Returns category -> aggregate stats + samples."""
    clusters = {}
    for f in findings:
        if not is_open(f):
            continue
        cat = f.get("category", "unknown")
        c = clusters.setdefault(cat, {
            "count": 0, "screens": set(), "configs": set(),
            "roles": set(), "tiers": set(), "fixes": set(), "samples": [],
        })
        c["count"] += 1
        c["screens"].add(f.get("screen", "unknown"))
        c["configs"].add(f.get("config", ""))
        c["roles"].add(f.get("role", "unknown"))
        c["tiers"].add(f.get("tier"))
        if f.get("fix"):
            c["fixes"].add(f["fix"])
        c["samples"].append(f)
    return clusters


def rank(clusters: dict, threshold: int):
    """Split into (over, under) threshold, each sorted by breadth (distinct screens) then count."""
    items = list(clusters.items())
    items.sort(key=lambda kv: (len(kv[1]["screens"]), kv[1]["count"]), reverse=True)
    over = [(c, s) for c, s in items if s["count"] >= threshold]
    under = [(c, s) for c, s in items if s["count"] < threshold]
    return over, under


def _sample_line(f: dict) -> str:
    screen = f.get("screen", "?")
    config = f.get("config", "?")
    element = f.get("element", "?")
    finding = (f.get("finding") or "").strip()
    return f"  - `{screen}` / `{config}` · **{element}** — {finding}"


def render_promotions(over, under, threshold: int) -> str:
    lines = []
    lines.append("# Promotion proposals")
    lines.append("")
    lines.append("> Generated by `harness/bin/distill_ledger.py` — do not hand-edit; re-run to refresh.")
    lines.append(f"> Promotion threshold: a category seen **≥ {threshold}** times across the ledger.")
    lines.append("> Approve in `/ui-distill`; on approval, implement the deposit, then mark it with the")
    lines.append("> `--deposit` command shown per candidate. **Promote-and-delete:** once a finding is")
    lines.append("> enforced upstream, delete its now-redundant rubric/CLAUDE.md line.")
    lines.append("")

    if not over:
        lines.append("## No candidates over threshold")
        lines.append("")
        lines.append(f"Nothing has recurred ≥ {threshold} times yet. Watchlist below.")
        lines.append("")
    else:
        lines.append(f"## Candidates ({len(over)})")
        lines.append("")
        for cat, s in over:
            rung, deposit = ladder_for(cat)
            tiers = ",".join(str(t) for t in sorted(x for x in s["tiers"] if x is not None))
            lines.append(f"### `{cat}` — {s['count']} findings · {len(s['screens'])} screen(s) · {len(s['configs'])} config(s)  [tier {tiers or '?'}]")
            lines.append("")
            lines.append(f"- **Ladder:** {rung} — {deposit}")
            lines.append(f"- **Seen on:** {', '.join(sorted(s['screens']))}  ·  **roles:** {', '.join(sorted(s['roles']))}")
            if s["fixes"]:
                lines.append(f"- **Distinct fixes proposed:** {len(s['fixes'])}")
            lines.append("- **Sample findings:**")
            for f in s["samples"][:3]:
                lines.append(_sample_line(f))
            lines.append("")
            lines.append("  After implementing, record the deposit:")
            lines.append("")
            lines.append(f"  ```bash")
            lines.append(f"  python3 harness/bin/distill_ledger.py --deposit {cat} --label \"<what you added>\"")
            lines.append(f"  ```")
            lines.append("")
            lines.append("  - [ ] approved &nbsp;&nbsp; - [ ] implemented &nbsp;&nbsp; - [ ] soft guidance deleted")
            lines.append("")

    lines.append(f"## Watchlist (below threshold of {threshold})")
    lines.append("")
    if under:
        for cat, s in under:
            lines.append(f"- `{cat}` — {s['count']} ({', '.join(sorted(s['screens']))})")
    else:
        lines.append("- _(empty)_")
    lines.append("")
    return "\n".join(lines)


def mark_deposit(ledger_path, category: str, label: str) -> int:
    """Set resolved=true + deposit=label on a category's OPEN findings. Rewrites the ledger
    in place (the one sanctioned in-place mutation — capture appends, distill closes out).
    Returns the number of findings marked. Idempotent: a second run marks 0."""
    p = Path(ledger_path)
    findings = load_findings(p)
    marked = 0
    for f in findings:
        if f.get("category") == category and is_open(f):
            f["resolved"] = True
            f["deposit"] = label
            marked += 1
    if marked:
        with p.open("w", encoding="utf-8") as fh:
            for f in findings:
                fh.write(json.dumps(f, ensure_ascii=False, separators=(",", ":")) + "\n")
    return marked


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"ledger path (default: {DEFAULT_LEDGER})")
    ap.add_argument("--out", default=DEFAULT_PROMOTIONS, help=f"promotions file to write (default: {DEFAULT_PROMOTIONS})")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD, help=f"promotion threshold (default: {DEFAULT_THRESHOLD})")
    ap.add_argument("--deposit", metavar="CATEGORY", help="mark a category's open findings as deposited (close them out)")
    ap.add_argument("--label", help="deposit label (required with --deposit) — what was added/enforced")
    args = ap.parse_args(argv)

    if args.deposit:
        if not args.label:
            ap.error("--deposit requires --label")
        n = mark_deposit(args.ledger, args.deposit, args.label)
        print(f"marked {n} '{args.deposit}' finding(s) as deposited: {args.label}")
        return 0

    findings = load_findings(args.ledger)
    clusters = cluster(findings)
    over, under = rank(clusters, args.threshold)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(render_promotions(over, under, args.threshold), encoding="utf-8")

    open_n = sum(1 for f in findings if is_open(f))
    print(f"{open_n} open finding(s) in {len(clusters)} categor(ies); "
          f"{len(over)} over threshold ({args.threshold}) -> {args.out}")
    for cat, s in over:
        rung, _ = ladder_for(cat)
        print(f"  [{rung:16}] {cat:14} x{s['count']} across {len(s['screens'])} screen(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
