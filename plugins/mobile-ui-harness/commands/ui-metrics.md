---
description: Render the harness's self-improvement metrics from the ledger — iterations-to-pass, first-pass yield, and recurrence-after-deposit — to show whether the harness is actually compounding.
argument-hint: (none)
allowed-tools: Read, Bash
---

Show whether the harness is getting better over time. This is read-only analysis — the work is in the deterministic script; you just run it and interpret.

## 1. Compute

```bash
python3 harness/bin/metrics_ledger.py    # writes harness/ledger/metrics.md (gitignored)
```
`Read` `harness/ledger/metrics.md`.

## 2. Interpret the three numbers

- **Iterations-to-pass per screen (↓):** how many loop iterations a screen needed before it stopped surfacing findings. Falling over time means prevention (rails, gates, reused components) is catching things earlier. A screen that needs 4 every time is a candidate for a structural fix.
- **First-pass yield (↑):** share of screens that came in with zero Tier-1 structural blockers on the *first* render. Rising means the upstream rails (Konsist boundaries, tokens, designsystem reuse) are working — fewer broken-before-tasteless first drafts.
- **Recurrence after deposit (→ 0):** for each promoted category, how many findings appeared *after* it was deposited. **This is the key health signal.** Zero = the promotion stuck. Non-zero (flagged ⚠️) = the deposit isn't holding — the finding slipped past the gate you added, so harden it further down the ladder (rubric line → deterministic assertion → structural impossibility). Recurrence rising after a promotion is the cue to re-open it in `/ui-distill`.

## 3. Act on it

If any category is flagged ⚠️, that's the most valuable thing the metrics surfaced: re-run `/ui-distill` for it and push the deposit one rung deeper. Everything else is trend-watching — re-run after each batch of `/ui-iterate` work; the ledger is the durable history, this report is the current snapshot.

> These need data to be meaningful — they read what `/ui-iterate` (capture) and `/ui-distill` (deposit) write. On an empty ledger the report just says so.
