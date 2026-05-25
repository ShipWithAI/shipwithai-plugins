---
name: setup-permissions
description: >
  Configure .claude/settings.json with appropriate tool permissions for your stack.
  Called by cold-start-interview or standalone to configure the permissions pillar.
  Trigger phrases: "setup permissions", "configure allowed tools", "set claude permissions".
argument-hint: "[--stack nodejs|python|golang|java|rust|general] [--preset-only]"
---

# /setup-permissions

Configures `.claude/settings.json` → `allowedTools` và `disallowedTools`.

## Mode Detection

```
Đọc .claude/starter-context.json nếu tồn tại
  → Tồn tại: dùng fields stack, permissions.preset, permissions.disallowed_tools, permissions.readonly_paths
  → Không tồn tại (standalone): detect stack → show preset → confirm
```

## Load Preset

Đọc `settings-presets.json`, match theo detected stack:

```
nodejs  → Read/Write/Edit/Grep/Glob + Bash(npm:*,npx:*,node:*,git:*)
python  → Read/Write/Edit/Grep/Glob + Bash(python:*,pip:*,pytest:*,git:*)
golang  → Read/Write/Edit/Grep/Glob + Bash(go:*,git:*)
java    → Read/Write/Edit/Grep/Glob + Bash(mvn:*,gradle:*,java:*,git:*)
rust    → Read/Write/Edit/Grep/Glob + Bash(cargo:*,git:*)
general → Read only + require-confirm(Write,Edit,Bash)
```

Show preset với giải thích từng rule. Confirm hoặc customize.

Hỏi thêm:
- "Tool nào Claude KHÔNG được dùng?" → thêm vào `disallowedTools`
- "Path nào chỉ đọc không được sửa?" → thêm read-only path rules

## Output Format

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Write",
      "Edit",
      "Grep",
      "Glob",
      "Bash(npm:*)",
      "Bash(npx:*)",
      "Bash(node:*)",
      "Bash(git:*)"
    ],
    "deny": []
  }
}
```

## Write Rules

- Check `.claude/settings.json` exists → Overwrite / Merge (keep existing sections) / Skip?
- Merge: chỉ update permissions section, không touch hooks section nếu đã có
- Không set permissions quá restrictive → team không làm được gì
