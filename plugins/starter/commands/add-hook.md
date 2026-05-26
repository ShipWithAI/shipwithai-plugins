---
name: add-hook
description: >
  Add a new hook to .claude/settings.json. Quick operation, no full interview needed.
  Trigger phrases: "add hook", "auto-format on save", "run tests after edit",
  "lint on write", "run [command] after [tool]".
argument-hint: "[hook type: PreToolUse|PostToolUse|Stop] [tool: Edit|Write|Bash|*]"
---

# /add-hook

Add a single hook to the `.claude/settings.json` hooks section. Stateless.

## Steps

1. Check `skills/setup-hooks/hooks-catalog.json` for a matching common pattern.
   - Match found: show preset, confirm or customize.
   - No match: ask:
     - Hook type: PreToolUse / PostToolUse / Stop?
     - Trigger on which tool: Edit / Write / Bash / * (all)?
     - File pattern (optional): `*.ts`, `*.py`, `*.go`?
     - Command to run?

2. Show preview before confirming:
   ```
   This hook will run `[command]` every time Claude uses the [tool] tool
   [on files matching [pattern]].

   Preview:
   {
     "PostToolUse": [{
       "matcher": "Edit",
       "hooks": [{"type": "command", "command": "[command]"}]
     }]
   }
   ```

3. Check for duplicate: if an identical hook already exists in `settings.json`, skip.

4. Confirm → merge into `.claude/settings.json` hooks section.
   Do not overwrite the permissions section.

5. Update the "Active hooks" section in `CLAUDE.md` if the file exists.
