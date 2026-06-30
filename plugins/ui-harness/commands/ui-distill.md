---
description: Distill the feedback ledger into promotion proposals and — on human approval — harden recurring findings into permanent gates, then delete the now-redundant soft guidance. The self-improvement ratchet's act-half.
argument-hint: (none) | --threshold N
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Task
---

Turn recurring ledger findings into permanent gates. The **deterministic** part (cluster → threshold → map to the durability ladder) is the script; the **judgment** part (approve → implement → delete soft guidance) is you + the human. Never auto-implement a promotion — approval gates everything.

## 1. Analyze (deterministic)

```bash
python3 harness/bin/distill_ledger.py $ARGUMENTS    # writes harness/ledger/promotions.md
```
`Read` `harness/ledger/promotions.md`. Each candidate is a category seen ≥ threshold (default 3) times, with its **durability-ladder** rung + concrete deposit, breadth (screens/configs), and sample findings.

If there are **no candidates over threshold**, report the watchlist and stop — nothing has recurred enough to harden yet.

## 2. Propose to the human (approval required)

Present each candidate: category, count/breadth, the recommended deposit, and 2–3 sample findings. **Human approval is required for every Tier-2/3 deposit** (a new assertion, a Konsist rule, a component, an API change). Surface them; do not implement anything yet. Let the human pick which to promote (and they may downgrade a rung — e.g. "keep it a rubric line for now").

## 3. Implement the approved deposit — push it as far down the ladder as it goes

Per the candidate's rung:

- **T2 gate** (`touch-target`, `zero-size`, `out-of-bounds`, `insets`, `overflow`, `truncation`, `contrast`): add/extend the deterministic assertion in `Tier1Assertions.kt` (or tag critical `Text` with `Modifier.testTag("noTruncate")`). **Verify it bites:** run an inspection test that exhibits the finding and confirm Tier-1 now fails on it, then fix so it passes.
- **T3 structural** (`reuse`, raw-material3, hardcoded values): either promote the reinvented component into `core:designsystem` (+ catalog entry per `docs/components/`, + golden), or tighten a Konsist rule in `ArchitectureTest.kt`. **Verify** the gate fails on a planted violation (the negative-test discipline from the Konsist work).
- **T1 soft** (`color`, `typography`, `hierarchy`, `affordance`, `state`, non-mechanizable `spacing`): add ONE concise line to `.claude/skills/mobile-design/SKILL.md`. Keep it minimal — soft guidance is a staging area, not storage.

A deposit isn't done until you've **seen it catch the finding** (gate runs red on the bad case, green after the fix). Don't mark deposited on faith.

## 4. Close out the ledger

```bash
python3 harness/bin/distill_ledger.py --deposit <category> --label "<what you added, incl. file/commit>"
```
This sets `resolved=true` + `deposit=<label>` on that category's open findings (in place), so they stop surfacing as candidates and feed `/ui-metrics`' recurrence-after-deposit signal.

## 5. Promote-and-delete (the ratchet's point)

Once a finding is enforced upstream, **delete the now-redundant soft guidance** — the matching rubric line in `mobile-design/SKILL.md` or rail in `CLAUDE.md`. A healthy harness's soft guidance *shrinks* as gates accrete; if you only ever add, you've built a second pile of advice, not a ratchet. Note what you deleted in the promotion record.

## 6. Confirm

Re-run step 1 and confirm the promoted category dropped out of candidates (it will, once `--deposit` closed it out). The durable record is the ledger `deposit` label — point it at the file/commit you added — plus the committed gate itself; `promotions.md` is a regenerated worksheet, not the record.

> The threshold is a default, not a law. A single `blocker` that will obviously recur is worth promoting at count 1; pass `--threshold 1` or just use judgment. Conversely, three taste nits that aren't mechanizable may never deserve more than a rubric line.
