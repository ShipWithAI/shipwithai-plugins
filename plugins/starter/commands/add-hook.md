---
name: add-hook
description: >
  Add a new hook to .claude/settings.json. Quick operation, no full interview needed.
  Trigger phrases: "add hook", "auto-format on save", "run tests after edit",
  "lint on write", "run [command] after [tool]".
argument-hint: "[hook type: PreToolUse|PostToolUse|Stop] [tool: Edit|Write|Bash|*]"
---

# /add-hook

Thêm một hook vào `.claude/settings.json` hooks section. Stateless.

## Steps

1. Check `references/hooks-catalog.json` cho common patterns.
   Nếu match → show preset, confirm.
   Nếu không match → hỏi:

   - Hook type: PreToolUse / PostToolUse / Stop?
   - Trigger on which tool: Edit / Write / Bash / * (all)?
   - File pattern (optional): `*.ts`, `*.py`, `*.go`?
   - Command to run?

2. Show preview:
   ```
   Hook này sẽ chạy `[command]` mỗi khi Claude dùng [tool]
   [trên files matching [pattern]].

   Preview:
   {
     "PostToolUse": [{
       "matcher": "Edit",
       "hooks": [{"type": "command", "command": "[command]"}]
     }]
   }
   ```

3. Confirm → merge vào `.claude/settings.json` hooks section.
   Không overwrite permissions section.

4. Update "Active hooks" table trong `CLAUDE.md` nếu file tồn tại.
