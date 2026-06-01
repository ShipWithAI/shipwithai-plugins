---
name: setup-observability
description: >
  Enable tool call logging for harness optimization. Installs observe.py hook
  writing tool metadata to .claude/logs/. Tier 3 opt-in.
  Trigger phrases: "setup observability", "enable tool logging", "track tool usage",
  "observe tool calls".
argument-hint: "[--disable]"
---

# /setup-observability

Installs a lightweight logging hook that records tool call metadata.
Logs feed future harness analysis tooling (coming in a later phase).

## What gets logged

Only metadata — never content:

| Tool  | Logged                        | NOT logged                        |
|-------|-------------------------------|-----------------------------------|
| Edit  | Relative file path            | File content, old/new string      |
| Write | Relative file path            | File content                      |
| Bash  | Command name (argv[0] only)   | Arguments, output, exit code      |

One line per call: `.claude/logs/YYYY-MM-DD.jsonl`

Opt-out anytime: `export DISABLE_OBSERVE=1` in terminal or shell profile.

## Mode Detection

```
--disable flag    → reverse setup (see --disable Flow below)
No args           → run setup flow
```

## Setup Steps

1. Copy `observe.py` from plugin assets to `.claude/hooks/observe.py`
2. Merge PostToolUse hook into `.claude/settings.json` — matcher `Edit|Write|Bash`
3. Merge Stop hook (log rotation) into `.claude/settings.json`
4. Add `.claude/logs/` to `.gitignore` (skip if already present)
5. Check `git ls-files .claude/logs` — warn user if currently tracked
6. Update `starter-context.json` → `observability.enabled: true`

## Output Format

Preview before writing:

```
Observability setup:
  .claude/hooks/observe.py         CREATE
  .claude/settings.json (hook)     UPDATE — add PostToolUse + Stop entries
  .gitignore                       UPDATE — add .claude/logs/

Logs will be written to: .claude/logs/YYYY-MM-DD.jsonl
Opt-out: export DISABLE_OBSERVE=1

Proceed?
```

After writing:
```
✅ Observability enabled.
Logs: .claude/logs/ (excluded from git)
Disable anytime: export DISABLE_OBSERVE=1
After 7+ days of logging, use `/shipwithai-starter:drift-monitor` to review harness health.
Harness pattern analysis (optimize-harness) is coming in a future phase.
```

## settings.json Hook Entries

PostToolUse entry to add:
```json
{
  "matcher": "Edit|Write|Bash",
  "hooks": [{"type": "command", "command": "python3 .claude/hooks/observe.py"}]
}
```

Stop entry to add:
```json
{
  "hooks": [{"type": "command", "command": "find .claude/logs -name '*.jsonl' -mtime +30 -delete 2>/dev/null || true"}]
}
```

## Write Rules

- Read `settings.json` before writing — merge into existing structure, never overwrite
- Check `hooks.PostToolUse` for matcher `Edit|Write|Bash` — skip if already present (idempotent)
- Check `hooks.Stop` for rotation command — skip if already present (idempotent)
- Check `.gitignore` for `.claude/logs/` — skip line if already present
- Never proceed without user confirmation of the preview

## --disable Flow

1. Remove PostToolUse hook entry with matcher `Edit|Write|Bash` from `settings.json`
2. Remove Stop hook rotation entry from `settings.json`
3. Update `starter-context.json` → `observability.enabled: false`
4. Report: "Observability disabled. Existing logs at `.claude/logs/` preserved — delete manually if not needed."
