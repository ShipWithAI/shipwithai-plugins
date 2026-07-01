---
name: optimize-harness
description: >
  Analyze Claude Code tool call logs and suggest harness improvements based on
  actual usage patterns. Requires observability enabled + 7 days of data.
  Trigger phrases: "optimize harness", "harness suggestions", "improve my setup",
  "analyze tool usage", "what hooks should I add".
argument-hint: "[--verbose] [--window N] [--json] [--force]"
---

# /optimize-harness

Reads `.claude/logs/*.jsonl` (written by `observe.py`) and surfaces actionable
suggestions: hooks to add, workflow gates to enable — based on what you actually do.

> **Does NOT repeat static analysis from `/review`.**
> Hook binaries, MCP alignment, schema drift → run `/shipwithai-starter:review`.
> Runtime usage patterns (frequency, directories, commands) → run this skill.

## Flag Handling

- `--verbose` — include LOW confidence suggestions (hidden by default)
- `--window N` — analysis window in days, minimum 7 (default: 30)
- `--json` — output as JSON instead of markdown report
- `--force` — bypass the 7-day cooldown advisory without prompting

## Step 1 — Guard Clauses

Evaluate in order. Stop on first failure and output the message below.

**Guard 1 — Observability not enabled:**
```
Check: .claude/logs/ exists AND .claude/hooks/observe.py exists
Fail output:
  Observability not enabled. Run /shipwithai-starter:setup-observability
  first. optimize-harness requires at least 7 days of log data.
```

**Guard 2 — Not enough data:**
```
Check: ≥7 distinct YYYY-MM-DD log filenames within window
       AND ≥50 total parsed events
Fail output:
  Not enough data yet.
  Current: [N] days of logs, [T] tool calls
  Required: 7 days AND 50 tool calls
  Come back after [earliest_date + 7 days].
```
N = count of YYYY-MM-DD filenames within window. T = successfully parsed events.

**Guard 3 — Cooldown (advisory only, not a hard block):**
```
Check: starter-context.json → optimizer.last_run exists
       AND today - last_run < 7 days
Warn:  Last optimization was [N] days ago (last run: [date]).
       Results may not reflect new patterns. Run anyway? [y/N]
```
Proceed if user says yes, passes `--force`, or `optimizer.last_run` is absent.

## Step 2 — Parse & Aggregate

**Parse:**
1. List `.claude/logs/*.jsonl` sorted by filename date; filter to window
2. Read line by line — skip malformed lines silently (no error output)
3. Discard: `tool` absent or not in `{Edit, Write, Bash}`
4. Discard: `ts` absent or unparseable

**Log format** (observe.py — no exit codes, no ms duration):
```
Edit/Write: {"ts":"2026-06-01T10:00:00Z","sid":"a3f2c8b1","event":"tool","tool":"Edit","file":"src/auth.ts"}
Bash:       {"ts":"2026-06-01T10:00:05Z","sid":"a3f2c8b1","event":"tool","tool":"Bash","cmd":"npm"}
```

**Aggregate** (pure computation — no further file I/O):

| Metric | Definition |
|--------|-----------|
| `bash_cmd_frequency` | `Map<cmd, count>` — Bash events only, key on `cmd` |
| `file_edit_frequency` | `Map<file_path, count>` — Edit+Write, skip empty `file` |
| `file_edit_by_dir` | `Map<first_path_component, count>` — from Edit+Write `file` field |
| `ts_extension_edits` | `Map<lowercase_ext_with_dot, count>` — from Edit+Write `file` field |
| `session_count` | `len(set(e.sid for e in events))` |
| `session_duration_minutes` | Per sid ≥2 events: `(last_ts - first_ts).total_seconds() / 60` |
| `daily_tool_calls` | `Map<YYYY-MM-DD, count>` from `ts` field |
| `days_with_data` | `len(daily_tool_calls)` |

## Step 3 — Correlate & Evaluate Rules

**Read `.claude/starter-context.json`:**
- `hooks_selected` — list of active hook IDs (default: `[]`)
- `workflow_gates` — list of active gate IDs (default: `[]`)
- `architecture.sensitive_areas` — list of path patterns (default: `[]`)

**Compute `sensitive_area_edits`:** for each pattern, count Edit+Write events
where `file` starts with the pattern (strip leading `./` from file paths).

**Load `optimize-rules.json`** (same directory as this file) to get rule definitions.

**Evaluate all 8 rules:**

| Rule | Condition | Confidence |
|------|-----------|------------|
| R1 | `bash_cmd_frequency["npm"] ≥ 5` AND `jest-on-stop` not in hooks_selected | HIGH ≥20 / MEDIUM ≥5 |
| R2 | `bash_cmd_frequency["pytest"] ≥ 5` AND `pytest-on-stop` not in hooks_selected | HIGH ≥20 / MEDIUM ≥5 |
| R3 | `sum(.ts+.tsx+.js+.jsx edits) ≥ 20` AND `prettier-on-edit` not in hooks_selected | HIGH ≥50 / MEDIUM ≥20 |
| R4 | `.py edits ≥ 20` AND neither `black-on-edit` nor `ruff-on-edit` in hooks_selected | HIGH ≥50 / MEDIUM ≥20 |
| R5 | `any sensitive_area_edits[P] ≥ 10` AND `security-review` not in workflow_gates | HIGH |
| R6 | `make ≥ 5` AND `make-test-on-stop` absent; OR `cargo ≥ 5` AND `cargo-test-on-stop` absent | HIGH ≥20 / MEDIUM ≥5 |
| R7 | top `file_edit_frequency` entry ≥ 30 AND no test file found | LOW |
| R8 | ≥3 timed sessions AND `median(session_duration_minutes) > 60` | LOW |

**R5:** Use the pattern with the highest `sensitive_area_edits` count for the evidence line.

**R6:** If both `make` and `cargo` trigger, emit one suggestion per tool (two results).

**R7 — test file detection:**
```
base = filename without extension (e.g. "auth" from "src/auth.ts")
find . -not -path "*/node_modules/*" -not -path "*/.git/*" \
  \( -name "*${base}.test*" -o -name "*${base}.spec*" \
     -o -name "test_${base}*" -o -name "${base}_test*" \) 2>/dev/null
```
Non-empty output → test file exists → R7 does NOT trigger.

**Filter & rank:**
1. Keep triggered rules only
2. Drop LOW confidence if `--verbose` not set
3. Sort: HIGH first, then MEDIUM, then LOW
4. Deduplicate by rule ID (keep first)
5. Truncate to top 5

## Step 4 — Output

**Normal report:**
```
## Harness Optimization Report — [project name from CLAUDE.md]
Period: YYYY-MM-DD → YYYY-MM-DD ([N] days, [M] sessions, [T] tool calls)

### Usage Summary
Most edited files:  [file1] ([N]), [file2] ([N]), [file3] ([N])
Most used commands: [cmd1] ([N]), [cmd2] ([N]), [cmd3] ([N])
Active directories: [dir1] ([N] edits), [dir2] ([N] edits), [dir3] ([N] edits)
Tool distribution:  Edit [X]% / Write [Y]% / Bash [Z]%

### Suggestions

[HIGH] [title]
Evidence: [evidence string]
Action: [action label from rule definition]

[MEDIUM] ...

---
Data window: [N] days | Next optimization: [today + 7 days]
```

**No suggestions — replace Suggestions section with:**
```
### No issues detected
Your harness matches your usage patterns. Keep it up!
```

**`--json` output schema:**
```json
{
  "project": "string", "generated_at": "YYYY-MM-DD",
  "period": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "days": 30, "sessions": 12, "total_events": 347},
  "summary": {
    "top_files": [{"file": "src/auth.ts", "count": 42}],
    "top_commands": [{"cmd": "npm", "count": 67}],
    "top_dirs": [{"dir": "src", "count": 93}],
    "tool_distribution": {"Edit": 54, "Write": 12, "Bash": 34}
  },
  "suggestions": [{"id": "R1", "confidence": "HIGH", "title": "...", "evidence": "...", "action": "..."}]
}
```

## Step 5 — Update Cooldown

Read `.claude/starter-context.json`, merge `optimizer.last_run = today_iso_date`,
write back. Preserve all other fields.

## Failure Modes

- Don't suggest hooks for tools not detected in logs
- Don't auto-apply any changes — every suggestion includes an action command, user runs manually
- Don't run analysis with <7 days data or <50 events — guard clause handles this
- Don't duplicate static analysis from `/review` (hook binaries, MCP alignment, schema drift)
- Don't crash on malformed log lines — skip silently
- Don't show LOW confidence suggestions unless `--verbose` is set
- Don't write cooldown timestamp if analysis was blocked by a guard clause
