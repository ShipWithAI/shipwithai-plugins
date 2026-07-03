# Feedback ledger

`findings.jsonl` is the **durable, append-only record** of every UI finding the harness
produces. It is the substrate the self-improvement ratchet reads: `/ui-distill` clusters
recurring findings into permanent gates/components, and `/ui-metrics` trends iterations-to-pass,
first-pass yield, and per-category recurrence. (Those two steps are not built yet — this file
and its aggregator are the *capture* half of the loop.)

## Who writes it

Two producers emit findings to **build-local sidecars** (gitignored, hermetic), which the
aggregator folds into this committed ledger:

| Producer | Sidecar | Catches |
|---|---|---|
| `Tier1Assertions.kt` (deterministic) | `<module>/build/outputs/roborazzi/_findings.jsonl` | structural blockers a machine can prove: zero-size, touch-target, out-of-bounds, text-overflow |
| `mobile-design-evaluator` agent (vision) | `_eval_findings.jsonl` beside the verdict it grades | everything assertions can't see: taste, hierarchy, spacing, fidelity vs. target |

## Closing the loop

After a render + evaluate pass, fold the sidecars into the ledger:

```bash
python3 harness/bin/aggregate_ledger.py            # collect from the repo
python3 harness/bin/aggregate_ledger.py --dry-run  # preview, write nothing
python3 harness/bin/aggregate_ledger.py --iteration 2   # stamp the loop iteration
```

The aggregator dedups identical findings **within a single batch** (so a test re-run without
`clean` doesn't double-count), then truncates each consumed sidecar so a run is recorded exactly
once. Dedup is intentionally *not* applied across runs — a finding that recurs in a later run is a
fresh row, because cross-run recurrence is the promotion signal the ratchet looks for.

Self-test for the aggregator: `python3 harness/bin/test_aggregate_ledger.py`.

## Row schema (one JSON object per line)

**Screen id (canonical).** Findings cluster per screen, so both lanes must agree on the name. The
deterministic Tier-1 sidecar emits the inspection PNG's leading filename slug (`songs`, `field`,
`picker`); the LLM evaluator tends to emit the composable name (`SongsScreen`). Rather than trust the
LLM, `aggregate_ledger.py` canonicalizes every `screen` through **`screen-aliases.json`** (beside
this file) — a `{ "SongsScreen": "songs", … }` map, keys matched case/punctuation-insensitively.
**Add an entry whenever a new screen or a new evaluator phrasing appears**; unmapped names fall back
to a lowercased, alnum-stripped form. `category` names the **defect** (e.g. `touch-target`), never
the fix (`reuse`) — that one is evaluator guidance the aggregator can't enforce.

```json
{
  "ts": "2026-06-22T10:00:00Z",
  "screen": "songs",
  "config": "long_compact_font1_5_dark",
  "loop": "impl",
  "role": "tier1 | evaluator",
  "tier": 1,
  "category": "insets | overflow | truncation | overlap | zero-size | touch-target | out-of-bounds | spacing | hierarchy | color | typography | reuse | fidelity | ...",
  "severity": "blocker | warn | nit",
  "element": "TopAppBar title",
  "finding": "App bar overlaps status bar",
  "fix": "apply Modifier.windowInsetsPadding(WindowInsets.statusBars)",
  "iteration": 1,
  "resolved": false,
  "deposit": null
}
```

`deposit` is set by the distill step when a finding is promoted to a permanent gate, lint rule,
component, or token — marking it as having ratcheted down the durability ladder.

## Distilling (promote recurring findings)

`distill_ledger.py` is the ratchet's act-half. It clusters **open** findings (not `resolved`, no
`deposit`) by `category`, flags every category at/over the threshold (default 3) as a pattern, maps
it to the most permanent substrate on the durability ladder (spec §7), and writes proposals to
`promotions.md` (regenerated each run → gitignored; the durable record is the `deposit` label below
plus the committed gate). Run it via the `/ui-distill` command, which adds the human-approval and
implement-then-delete-soft-guidance steps.

```bash
python3 harness/bin/distill_ledger.py                 # analyze -> promotions.md
python3 harness/bin/distill_ledger.py --threshold 1   # promote even one-off blockers
python3 harness/bin/distill_ledger.py --deposit touch-target --label "Tier1Assertions min-size (#123)"
```

The `--deposit` mode is the **one sanctioned in-place mutation** of the ledger (capture appends;
distill closes out): it stamps `resolved=true` + `deposit=<label>` on a category's open findings, so
they stop surfacing as candidates and feed `/ui-metrics`' recurrence-after-deposit signal — if a
deposited category keeps recurring, the promotion didn't stick. Self-test: `python3 harness/bin/test_distill_ledger.py`.

## Metrics (is it compounding?)

`metrics_ledger.py` (via `/ui-metrics`) renders three numbers to `metrics.md` (regenerated →
gitignored): **iterations-to-pass** per screen (↓), **first-pass yield** (↑ — screens with zero
Tier-1 findings at iteration 1), and **recurrence after deposit** (→ 0 — open findings in a
already-promoted category; non-zero means the promotion didn't stick and should ratchet down a
tier). Read-only. Self-test: `python3 harness/bin/test_metrics_ledger.py`.
