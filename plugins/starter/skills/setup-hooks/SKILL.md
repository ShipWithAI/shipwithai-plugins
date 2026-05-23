---
name: setup-hooks
description: >
  Configure .claude/settings.json hooks section for your stack: auto-format,
  auto-lint, and test-on-stop triggers. Called by cold-start-interview or
  standalone to configure the hooks pillar.
  Trigger phrases: "setup hooks", "configure auto-format", "add lint hook".
argument-hint: "[--formatter prettier|black|gofmt] [--test jest|pytest|make]"
---

# /setup-hooks

Configures `.claude/settings.json` → `hooks` section.

## Mode Detection

```
Có context từ cold-start-interview?
  → Có: dùng detected tools + hook selections đã có
  → Không (standalone): detect tools → suggest từ catalog → confirm
```

## Hook Suggestions

Load `references/hooks-catalog.json`, match theo detected tools:

```
Prettier detect  → PostToolUse Edit (*.js|ts|jsx|tsx|css|md) → prettier --write $FILE
ESLint detect    → PostToolUse Edit (*.js|ts|jsx|tsx)        → eslint --fix $FILE
Black detect     → PostToolUse Edit (*.py)                   → black $FILE
gofmt detect     → PostToolUse Edit (*.go)                   → gofmt -w $FILE
Jest detect      → Stop                                      → npm test
pytest detect    → Stop                                      → pytest
make test detect → Stop                                      → make test
```

Từng hook một. Show preview trước khi confirm:

> "Hook này sẽ chạy `prettier --write $FILE` mỗi khi Claude dùng Edit tool
> trên files `.js|ts|jsx|tsx`. Bật không?"

## Output Format

Merge vào `.claude/settings.json` — không overwrite permissions section:

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
            "command": "npx prettier --write $CLAUDE_TOOL_INPUT_PATH"
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

- Merge hooks vào settings.json, không overwrite toàn bộ file
- Không write hook cho tool không detect được trong project
- Từng hook một — không batch confirm tất cả cùng lúc
