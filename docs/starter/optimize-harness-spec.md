# optimize-harness Skill — Implementation Spec
> Version: 2.1.0
> Target plugin: `plugins/starter/`
> Status: Ready for implementation

---

## 1. Scope & Positioning

`optimize-harness` is a **standalone skill** that analyzes runtime tool call logs
and suggests harness improvements. It is the runtime complement to `review`.

**Division of responsibility:**
- `review` → static analysis (hook binaries, MCP alignment, schema drift)
- `optimize-harness` → runtime analysis (usage patterns from `.claude/logs/`)

The two skills do NOT overlap. `optimize-harness` never re-runs static checks.

**`review` integration (one line only):**
In `review` Step 4, append after all action suggestions — only when
`.claude/logs/` exists AND contains files spanning ≥7 calendar days:
```
For runtime-based suggestions: /shipwithai-starter:optimize-harness
```

---

## 2. Prerequisites & Guard Clauses

Evaluate in order — stop and output the relevant message on first failure:

### Guard 1: Observability not enabled
```
Condition:  .claude/logs/ does not exist OR .claude/hooks/observe.py not found
Output:     "Observability not enabled. Run /shipwithai-starter:setup-observability
             first. optimize-harness requires at least 7 days of log data."
```

### Guard 2: Not enough data
```
Condition:  Fewer than 7 distinct calendar days with log files,
            OR total parsed events < 50
Output:     "Not enough data yet.
             Current: [N] days of logs, [T] tool calls
             Required: 7 days AND 50 tool calls
             Come back after [earliest_date + 7 days]."
```
`N` = count of distinct YYYY-MM-DD filenames within the analysis window.
`T` = total successfully parsed events.

### Guard 3: Cooldown (advisory, not hard block)
```
Condition:  starter-context.json has optimizer.last_run AND
            today - last_run < 7 days
Output:     "Last optimization was [N] days ago (last run: [date]).
             Results may not reflect new patterns. Run anyway? [y/N]"
```
If user says yes (or passes `--force`): proceed. If no: stop.

---

## 3. Input Files

| File | Required | Purpose |
|------|----------|---------|
| `.claude/logs/*.jsonl` | yes | Tool call events from observe.py |
| `.claude/starter-context.json` | yes | hooks_selected, workflow_gates, sensitive_areas, optimizer state |
| `.claude/settings.json` | yes | Active hook commands (for binary extraction) |

### Log format (exact — from observe.py)

Each line is a compact JSON object. Fields present depend on `tool`:

```jsonl
{"ts":"2026-06-01T10:30:00Z","sid":"a3f2c8b1","event":"tool","tool":"Edit","file":"src/auth.ts"}
{"ts":"2026-06-01T10:30:05Z","sid":"a3f2c8b1","event":"tool","tool":"Write","file":"src/config.ts"}
{"ts":"2026-06-01T10:30:10Z","sid":"a3f2c8b1","event":"tool","tool":"Bash","cmd":"npm"}
```

**All events:** `ts` (ISO8601 UTC), `sid` (8-char), `event` ("tool"), `tool`
**Edit/Write only:** `file` (relative path)
**Bash only:** `cmd` (argv[0] only — no arguments, no exit code, no duration)

> **Implementation note:** `exit` codes and `ms` duration are NOT logged.
> observe.py only logs `cmd` = argv[0]. Rules that would require exit codes
> (PRD R6 draft) are replaced by R6 below (make/cargo hook coverage).

---

## 4. Analysis Pipeline

### Phase 1: Parse

```
1. List .claude/logs/*.jsonl — sort by filename (YYYY-MM-DD.jsonl = chronological)
2. Filter to files within window: filename date >= (today - window_days)
   Default window_days = 30; overridden by --window flag
3. For each file, read line by line:
   a. json.parse(line) — if parse fails: skip silently (no error)
   b. Discard if: tool absent or not in {"Edit", "Write", "Bash"}
   c. Discard if: ts absent or unparseable
4. Result: events: List[Event]
```

### Phase 2: Aggregate

Compute all metrics from the parsed event list. All are pure computations
(no further file I/O).

**`total_events`** = `len(events)`

**`date_range`** = `{start: min(ts), end: max(ts)}` — parsed from ts field

**`session_count`** = `len(set(e.sid for e in events))`

**`bash_cmd_frequency`**: `Map<cmd: str, count: int>`
- Include only Bash events; key on `cmd` field

**`file_edit_frequency`**: `Map<file_path: str, count: int>`
- Include Edit + Write events; key on `file` field
- Skip events where `file` is empty string

**`file_edit_by_dir`**: `Map<dir: str, count: int>`
- For each Edit/Write event with non-empty `file`, take the first path component
  (i.e. `src/auth/user.ts` → `src`; `auth.ts` → `.` for root files)

**`ts_extension_edits`**: `Map<ext: str, count: int>`
- For each Edit/Write event, extract lowercase file extension including dot
  (e.g. `src/auth.ts` → `.ts`; `README.md` → `.md`)
- Skip files with no extension

**`ts_by_session`**: `Map<sid: str, sorted_ts_list: List[str]>`
- Group events by `sid`, collect all `ts` values per session, sort ascending

**`session_duration_minutes`**: `Map<sid: str, minutes: float>`
- For each sid with ≥2 events: parse first and last ts, compute delta in minutes
- Sessions with only 1 event: exclude from duration estimates
- Implementation: `(datetime.fromisoformat(last_ts) - datetime.fromisoformat(first_ts)).total_seconds() / 60`

**`daily_tool_calls`**: `Map<date: str, count: int>`
- Group by date extracted from ts field (first 10 chars: `YYYY-MM-DD`)

**`days_with_data`** = `len(daily_tool_calls.keys())`

### Phase 3: Correlate with starter-context.json

Read `.claude/starter-context.json`. Extract:
- `hooks_selected`: list of hook IDs (e.g. `["prettier-on-edit", "jest-on-stop"]`)
  — if absent, treat as empty list
- `workflow_gates`: list of gate IDs (e.g. `["plan-before-code", "security-review"]`)
  — if absent, treat as empty list
- `architecture.sensitive_areas`: list of path patterns (e.g. `["src/auth/", "src/payments/"]`)
  — if absent, treat as empty list
- `optimizer.last_run`: ISO date string — used for cooldown check in Guard 3

Correlate:
- `sensitive_area_edits`: for each pattern in `sensitive_areas`, count total
  Edit/Write events where `file` starts with the pattern (strip leading `./`)
- `uncovered_commands`: bash commands with frequency ≥ 5 that have no
  corresponding test-on-stop hook (see rule definitions below)

### Phase 4: Evaluate Rules

Read `optimize-rules.json` to get rule definitions. Evaluate each rule.
Each rule returns one of:
- `{triggered: false}`
- `{triggered: true, id, confidence, title, evidence, action}`

Rules are documented in Section 6 and externalized to `optimize-rules.json`.

### Phase 5: Filter & Rank

```
1. Keep only triggered rules
2. If --verbose NOT set: drop LOW confidence results
3. Sort: HIGH first, then MEDIUM, then LOW
4. Deduplicate by rule id (keep first occurrence)
5. Truncate to top 5 results
```

### Phase 6: Write Cooldown & Report

1. Read `starter-context.json`, merge `optimizer.last_run = today_iso`, write back
2. Generate output from template (Section 5)

---

## 5. Rules

All rules are evaluated against the aggregated metrics. Load definitions from
`optimize-rules.json` — the skill reads that file and applies each rule.

### R1 — npm without jest hook
```
Condition:  bash_cmd_frequency["npm"] >= 5
            AND "jest-on-stop" NOT in hooks_selected
Confidence: HIGH if >= 20, MEDIUM if >= 5
Title:      "Add jest-on-stop hook to auto-run tests"
Evidence:   "npm called [N] times — no test-on-stop hook configured"
Action:     "Run /shipwithai-starter:setup-hooks to add jest-on-stop"
```

### R2 — pytest without pytest hook
```
Condition:  bash_cmd_frequency["pytest"] >= 5
            AND "pytest-on-stop" NOT in hooks_selected
Confidence: HIGH if >= 20, MEDIUM if >= 5
Title:      "Add pytest-on-stop hook to auto-run tests"
Evidence:   "pytest called [N] times — no test-on-stop hook configured"
Action:     "Run /shipwithai-starter:setup-hooks to add pytest-on-stop"
```

### R3 — TypeScript/JavaScript edits without prettier
```
Condition:  sum(ts_extension_edits[e] for e in [".ts",".tsx",".js",".jsx"]) >= 20
            AND "prettier-on-edit" NOT in hooks_selected
Confidence: HIGH if >= 50, MEDIUM if >= 20
Title:      "Add prettier-on-edit hook to auto-format JS/TS files"
Evidence:   "[N] edits on .ts/.tsx/.js/.jsx files — no formatter hook configured"
Action:     "Run /shipwithai-starter:setup-hooks to add prettier-on-edit"
```

### R4 — Python edits without formatter
```
Condition:  ts_extension_edits[".py"] >= 20
            AND "black-on-edit" NOT in hooks_selected
            AND "ruff-on-edit" NOT in hooks_selected
Confidence: HIGH if >= 50, MEDIUM if >= 20
Title:      "Add a Python formatter hook (black-on-edit or ruff-on-edit)"
Evidence:   "[N] edits on .py files — no Python formatter hook configured"
Action:     "Run /shipwithai-starter:setup-hooks to add black-on-edit or ruff-on-edit"
```

### R5 — Sensitive area edits without security gate
```
Condition:  any pattern P in sensitive_areas where sensitive_area_edits[P] >= 10
            AND "security-review" NOT in workflow_gates
Confidence: HIGH
Title:      "Enable security-review gate — sensitive areas are actively edited"
Evidence:   "[N] edits in [matching_pattern] — no security-review gate configured"
Action:     "Run /shipwithai-starter:init --update to update workflow gates"
```
Use the pattern with the highest edit count for the evidence line.

### R6 — make/cargo without test hook
```
Condition:  (bash_cmd_frequency["make"] >= 5 AND "make-test-on-stop" NOT in hooks_selected)
            OR (bash_cmd_frequency["cargo"] >= 5 AND "cargo-test-on-stop" NOT in hooks_selected)
Confidence: HIGH if >= 20, MEDIUM if >= 5
Title:      "Add [make-test-on-stop / cargo-test-on-stop] hook to auto-run tests"
Evidence:   "[make/cargo] called [N] times — no test-on-stop hook configured"
Action:     "Run /shipwithai-starter:setup-hooks to add [hook-id]"
```
If both make and cargo trigger: emit one suggestion per tool (two results, both count toward top-5).

### R7 — Heavily edited file with no test counterpart (LOW)
```
Condition:  Top file in file_edit_frequency has count >= 30
            AND no test file found for that file (see detection below)
Confidence: LOW (only shown with --verbose)
Title:      "[file] is heavily edited but has no test file"
Evidence:   "[file] edited [N] times — no test/spec file found"
Action:     "Consider adding tests. See /shipwithai-starter:setup-hooks for test runner setup."
```

**Test file detection algorithm:**
Take base filename without extension (e.g. `auth` from `src/auth.ts`).
Run: `find . -not -path "*/node_modules/*" -not -path "*/.git/*" \
  \( -name "*${base}.test*" -o -name "*${base}.spec*" \
     -o -name "test_${base}*" -o -name "${base}_test*" \) 2>/dev/null`
If output is non-empty → test file exists → rule does NOT trigger.

### R8 — Long average session duration (LOW)
```
Condition:  len(session_duration_minutes) >= 3 (at least 3 timed sessions)
            AND median(session_duration_minutes.values()) > 60
Confidence: LOW (only shown with --verbose)
Title:      "Sessions average [X] min — consider breaking work into smaller tasks"
Evidence:   "[N] sessions measured; median [X] min, longest [Y] min"
Action:     "Informational — no specific skill action"
```
Median of values in `session_duration_minutes` (exclude single-event sessions).

---

## 6. optimize-rules.json Schema

Externalize rule metadata for easy extension without editing SKILL.md.
File location: `plugins/starter/skills/optimize-harness/optimize-rules.json`

```json
{
  "schema": "1.0",
  "rules": [
    {
      "id": "R1",
      "name": "npm without jest hook",
      "bash_cmd": "npm",
      "hook_missing": "jest-on-stop",
      "threshold_high": 20,
      "threshold_medium": 5,
      "suggestion": "Add jest-on-stop hook to auto-run tests",
      "action_skill": "setup-hooks",
      "action_label": "Run /shipwithai-starter:setup-hooks to add jest-on-stop"
    },
    {
      "id": "R2",
      "name": "pytest without pytest hook",
      "bash_cmd": "pytest",
      "hook_missing": "pytest-on-stop",
      "threshold_high": 20,
      "threshold_medium": 5,
      "suggestion": "Add pytest-on-stop hook to auto-run tests",
      "action_skill": "setup-hooks",
      "action_label": "Run /shipwithai-starter:setup-hooks to add pytest-on-stop"
    },
    {
      "id": "R3",
      "name": "js/ts edits without prettier",
      "extensions": [".ts", ".tsx", ".js", ".jsx"],
      "hook_missing": "prettier-on-edit",
      "threshold_high": 50,
      "threshold_medium": 20,
      "suggestion": "Add prettier-on-edit hook to auto-format JS/TS files",
      "action_skill": "setup-hooks",
      "action_label": "Run /shipwithai-starter:setup-hooks to add prettier-on-edit"
    },
    {
      "id": "R4",
      "name": "python edits without formatter",
      "extensions": [".py"],
      "hooks_missing_any": ["black-on-edit", "ruff-on-edit"],
      "threshold_high": 50,
      "threshold_medium": 20,
      "suggestion": "Add black-on-edit or ruff-on-edit hook",
      "action_skill": "setup-hooks",
      "action_label": "Run /shipwithai-starter:setup-hooks to add black-on-edit or ruff-on-edit"
    },
    {
      "id": "R5",
      "name": "sensitive area edits without security gate",
      "sensitive_area_min_edits": 10,
      "gate_missing": "security-review",
      "confidence": "HIGH",
      "suggestion": "Enable security-review gate",
      "action_skill": "init",
      "action_label": "Run /shipwithai-starter:init --update to update workflow gates"
    },
    {
      "id": "R6",
      "name": "make/cargo without test hook",
      "bash_cmds": [
        {"cmd": "make", "hook_missing": "make-test-on-stop"},
        {"cmd": "cargo", "hook_missing": "cargo-test-on-stop"}
      ],
      "threshold_high": 20,
      "threshold_medium": 5,
      "suggestion": "Add {hook} hook to auto-run tests",
      "action_skill": "setup-hooks",
      "action_label": "Run /shipwithai-starter:setup-hooks to add {hook}"
    },
    {
      "id": "R7",
      "name": "heavily edited file without tests",
      "min_edits": 30,
      "confidence": "LOW",
      "suggestion": "{file} is heavily edited but has no test file",
      "action_label": "Consider adding tests"
    },
    {
      "id": "R8",
      "name": "long session duration",
      "min_sessions": 3,
      "median_minutes_threshold": 60,
      "confidence": "LOW",
      "suggestion": "Sessions average {median} min — consider breaking work into smaller tasks",
      "action_label": "Informational"
    }
  ]
}
```

---

## 7. Output Format

### Normal report
```
## Harness Optimization Report — [project name]
Period: YYYY-MM-DD → YYYY-MM-DD ([N] days, [M] sessions, [T] tool calls)

### Usage Summary
Most edited files:  src/auth.ts (42), src/api/routes.ts (31), src/db/schema.ts (18)
Most used commands: npm (67), git (34), python3 (8)
Active directories: src (93 edits), tests (21 edits), scripts (7 edits)
Tool distribution:  Edit 54% / Write 12% / Bash 34%

### Suggestions

[HIGH] Add jest-on-stop hook to auto-run tests
Evidence: npm called 67 times — no test-on-stop hook configured
Action: Run /shipwithai-starter:setup-hooks to add jest-on-stop

[MEDIUM] Add prettier-on-edit hook to auto-format JS/TS files
Evidence: 41 edits on .ts/.tsx files — no formatter hook configured
Action: Run /shipwithai-starter:setup-hooks to add prettier-on-edit

---
Data window: 30 days | Next optimization: 2026-07-06
```

### No suggestions
```
## Harness Optimization Report — [project name]
Period: YYYY-MM-DD → YYYY-MM-DD ([N] days, [M] sessions, [T] tool calls)

### Usage Summary
[same block as above]

### No issues detected
Your harness matches your usage patterns. Keep it up!

---
Data window: [N] days | Next optimization: [date + 7 days]
```

### Not enough data
```
## Not enough data yet
Current: [N] days of logs, [T] tool calls
Required: 7 days AND 50 tool calls
Come back after [earliest_file_date + 7 days].
```

### Observability not enabled
```
## Observability not enabled
Run /shipwithai-starter:setup-observability to start logging tool usage.
optimize-harness requires at least 7 days of log data.
```

### `--json` output schema
```json
{
  "project": "string",
  "period": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "days": 30, "sessions": 12, "total_events": 347},
  "summary": {
    "top_files": [{"file": "src/auth.ts", "count": 42}],
    "top_commands": [{"cmd": "npm", "count": 67}],
    "top_dirs": [{"dir": "src", "count": 93}],
    "tool_distribution": {"Edit": 54, "Write": 12, "Bash": 34}
  },
  "suggestions": [
    {"id": "R1", "confidence": "HIGH", "title": "...", "evidence": "...", "action": "..."}
  ],
  "generated_at": "YYYY-MM-DD"
}
```

---

## 8. Flags

| Flag | Default | Behavior |
|------|---------|---------|
| `--verbose` | off | Include LOW confidence suggestions |
| `--window N` | 30 | Analysis window in days (minimum 7) |
| `--json` | off | Output as JSON instead of markdown |
| `--force` | off | Bypass cooldown warning without prompt |

---

## 9. SKILL.md Budget & Structure

Target: **< 250 lines**

Recommended SKILL.md structure:
1. Frontmatter (name, description, argument-hint) — ~10 lines
2. Overview & prerequisites — ~15 lines
3. Flag handling — ~8 lines
4. Step 1: Check prerequisites (guards 1-3) — ~20 lines
5. Step 2: Parse & aggregate (reference log format, key metrics) — ~30 lines
6. Step 3: Evaluate rules (reference optimize-rules.json, define pipeline) — ~40 lines
7. Step 4: Output (reference format templates) — ~25 lines
8. Step 5: Update cooldown — ~5 lines

Rule definitions go in `optimize-rules.json`. Log format example data goes in comments
within the skill, not a separate reference file (too small to justify lazy-loading).

---

## 10. harness-optimizer.md Agent Spec

File: `plugins/starter/agents/harness-optimizer.md`

```markdown
---
name: harness-optimizer
description: >
  Analyze harness usage patterns and suggest improvements. Reads tool call logs
  and surfaces actionable hook/gate suggestions.
  Trigger phrases: "optimize harness", "harness suggestions",
  "improve my setup", "what should I change in my harness", "analyze tool usage".
---

Invoke /shipwithai-starter:optimize-harness and present the output.

If the skill reports "not enough data", explain that the user needs to enable
observability (/shipwithai-starter:setup-observability) and use Claude Code
for at least 7 days before patterns can be analyzed.
```

---

## 11. manifest.json Entry

Add to `plugins/starter/manifest.json` skills array:

```json
{
  "skillId": "optimize-harness",
  "name": "optimize-harness",
  "description": "Analyze Claude Code tool call logs and suggest harness improvements: hooks to add, workflow gates to enable, based on actual usage patterns. Requires 7 days of observability data.",
  "creatorType": "community",
  "updatedAt": "2026-06-06T00:00:00Z",
  "enabled": true
}
```

---

## 12. Evals

File: `plugins/starter/skills/optimize-harness/evals.json`

```json
{
  "evals": [
    {
      "prompt": "Optimize my harness — I have 30 days of logs and npm appears 45 times but I have no jest hook",
      "expect": [
        "runs Phase 1-4 pipeline",
        "triggers R1 with HIGH confidence",
        "evidence mentions npm count",
        "action points to setup-hooks",
        "outputs Usage Summary section"
      ]
    },
    {
      "prompt": "Optimize my harness — I only have 4 days of logs",
      "expect": [
        "detects fewer than 7 days",
        "outputs not-enough-data message",
        "shows current N days and required 7",
        "does NOT run analysis pipeline",
        "does NOT suggest any rules"
      ]
    },
    {
      "prompt": "Optimize my harness — .claude/logs/ does not exist",
      "expect": [
        "detects observability not enabled",
        "outputs observability-not-enabled message",
        "suggests setup-observability",
        "does NOT attempt to read logs"
      ]
    },
    {
      "prompt": "Optimize my harness — 30 days of logs, all relevant hooks already configured (prettier-on-edit, jest-on-stop, security-review gate active)",
      "expect": [
        "runs full pipeline",
        "no rules trigger",
        "outputs no-issues-detected message",
        "still shows Usage Summary",
        "shows next optimization date"
      ]
    },
    {
      "prompt": "Optimize my harness — 20 days of logs, 15 edits in src/auth/ directory, no security-review gate",
      "expect": [
        "triggers R5",
        "evidence mentions auth/ edit count",
        "confidence is HIGH",
        "action points to init --update",
        "does not trigger rules where condition not met"
      ]
    },
    {
      "prompt": "Optimize my harness --verbose",
      "expect": [
        "includes LOW confidence suggestions in output",
        "R7 and R8 appear if conditions met",
        "confidence label shows [LOW] prefix",
        "HIGH and MEDIUM suggestions still ranked first"
      ]
    },
    {
      "prompt": "Optimize my harness --json",
      "expect": [
        "outputs valid JSON",
        "JSON has period, summary, suggestions keys",
        "suggestions array has id, confidence, title, evidence, action per item",
        "no markdown formatting in output"
      ]
    }
  ]
}
```

---

## 13. Files to Create / Update

### Create
| File | Notes |
|------|-------|
| `plugins/starter/skills/optimize-harness/SKILL.md` | < 250 lines, orchestration only |
| `plugins/starter/skills/optimize-harness/evals.json` | 7 prompts defined above |
| `plugins/starter/skills/optimize-harness/optimize-rules.json` | Rule definitions from Section 6 |
| `plugins/starter/agents/harness-optimizer.md` | Agent spec from Section 10 |

### Update
| File | Change |
|------|--------|
| `plugins/starter/manifest.json` | Add optimize-harness entry (Section 11) |
| `plugins/starter/skills/review/SKILL.md` | Append to Step 4: "For runtime-based suggestions..." (only when logs ≥7 days) |
| `plugins/starter/CHANGELOG.md` | Add v2.1.0 entry |
| `plugins/starter/README.md` | Add optimize-harness to skill list |

---

## 14. Open Questions — Resolved

| Question (from PRD) | Resolution |
|--------------------|------------|
| Standalone skill or integrated into review? | **Standalone.** review mentions it with one line only when data is available. |
| Confidence threshold? | **MEDIUM+** shown by default, LOW shown with --verbose only. |
| Auto-apply suggestions? | **No.** All suggestions are advisory. Each includes the action command; user runs manually. |
| Scheduled weekly? | **No** — deferred. Agent (harness-optimizer.md) can be invoked manually. |
| exit code in logs? | **Not available.** observe.py does not log exit codes. R6 covers make/cargo hook gaps instead. |
| `ms` duration in logs? | **Not available.** Session duration estimated from first/last ts per sid. |

---

## 15. Example Log Data for Testing Rules

### R1 trigger (npm × 25, no jest-on-stop)
```jsonl
{"ts":"2026-05-01T09:00:00Z","sid":"aabb1122","event":"tool","tool":"Bash","cmd":"npm"}
{"ts":"2026-05-01T09:05:00Z","sid":"aabb1122","event":"tool","tool":"Edit","file":"src/index.ts"}
```
Repeat the Bash/npm line 25 times across 8+ days in starter-context with no jest-on-stop.

### R3 trigger (48 TypeScript edits, no prettier-on-edit)
```jsonl
{"ts":"2026-05-01T10:00:00Z","sid":"ccdd3344","event":"tool","tool":"Edit","file":"src/auth.ts"}
{"ts":"2026-05-01T10:01:00Z","sid":"ccdd3344","event":"tool","tool":"Edit","file":"src/api/routes.tsx"}
```
Repeat with .ts/.tsx files totaling ≥ 50 events for HIGH confidence.

### R5 trigger (12 edits in auth/, no security-review gate)
starter-context.json: `"sensitive_areas": ["src/auth/"]`, `"workflow_gates": ["plan-before-code"]`
```jsonl
{"ts":"2026-05-05T14:00:00Z","sid":"eeff5566","event":"tool","tool":"Edit","file":"src/auth/session.ts"}
```
Repeat 12 times. Expect: R5 HIGH, mentions "12 edits in src/auth/".

### Guard 2 (not enough data)
Only 3 .jsonl files in .claude/logs/, total 30 events across those 3 days.
Expect: "Not enough data yet. Current: 3 days, 30 tool calls."
