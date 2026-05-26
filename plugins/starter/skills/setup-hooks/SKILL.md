---
name: setup-hooks
description: >
  Configure .claude/settings.json hooks section for your stack: auto-format,
  auto-lint, and test-on-stop triggers. Called by cold-start-interview or
  standalone to configure the hooks pillar.
  Trigger phrases: "setup hooks", "configure auto-format", "add lint hook".
argument-hint: "[--formatter prettier|black|ruff|gofmt|rustfmt] [--test jest|pytest|make|cargo]"
---

# /setup-hooks

Configures `.claude/settings.json` → `hooks` section.

## Mode Detection

```
Read .claude/starter-context.json if it exists
  → Exists: use fields stack.detected_tools, hooks_selected — skip detect + confirm
  → Does not exist (standalone): detect tools → suggest from catalog → confirm
```

## Argument Handling

If flags are provided, skip auto-detection and only suggest hooks for the specified tools:

- `--formatter <name>`: only suggest hook for that formatter (e.g. `--formatter black`)
- `--test <name>`: only suggest hook for that test runner (e.g. `--test pytest`)

Flags can be combined: `/setup-hooks --formatter prettier --test jest`

## Tool Detection

Load `hooks-catalog.json`. For each entry, detect presence in order:

1. **files**: check whether any listed filename/glob exists in the project root
2. **packageJson**: read `package.json`, check key under `devDependencies` or `dependencies`
3. **binary**: run `which <binary>` — pass if exit code is 0

Only suggest a hook if the tool passes at least one of the three checks.

If no tools are detected: inform the user, suggest using flags to specify tools manually.

## Suggest & Confirm

Suggest hooks **one at a time**. Show a preview before confirming:

**PostToolUse hook:**
> "This hook will run `prettier --write $FILE` every time Claude uses the Edit tool
> on `.js|ts|jsx|tsx|css|md` files. Enable it?"

**Stop hook:**
> "This hook will run `npm test` every time Claude finishes a session. Enable it?"

If the user declines: record as skipped, continue to the next hook.

After all hooks are processed, show a summary:
> "Enabled: prettier-on-edit, eslint-fix-on-edit. Skipped: jest-on-stop."

## Output Format

If `.claude/settings.json` does not exist: create it with `{ "hooks": {} }`.

Merge into `.claude/settings.json` — do not overwrite the permissions section:

```json
{
  "permissions": { "...existing..." },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "case \"$CLAUDE_TOOL_INPUT_PATH\" in *.js|*.ts|*.jsx|*.tsx|*.css|*.md) npx prettier --write \"$CLAUDE_TOOL_INPUT_PATH\";; esac"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npm test"
          }
        ]
      }
    ]
  }
}
```

## Write Rules

- If `settings.json` does not exist: create it with `{ "hooks": {} }`
- Merge hooks into `settings.json` — do not overwrite the entire file
- Before writing: check `hook.id` against existing hooks — skip if the id already exists (prevent duplicates)
- Do not write a hook for a tool that was not detected (unless specified via flags)
- Confirm one hook at a time — do not batch-confirm all at once

## Post-Write

If `.claude/starter-context.json` exists:
→ Update the `hooks_selected` field with the list of `hook.id` values the user confirmed
