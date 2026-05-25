---
name: setup-permissions
description: >
  Configure .claude/settings.json with appropriate tool permissions for your stack.
  Called by cold-start-interview or standalone to configure the permissions pillar.
  Trigger phrases: "setup permissions", "configure allowed tools", "set claude permissions".
argument-hint: "[--stack nodejs|python|golang|java|rust|general] [--preset-only]"
---

# /setup-permissions

Configures `.claude/settings.json` → `permissions.allow` and `permissions.deny`.

## Flags

Check flags first — they override Mode Detection behavior:

- `--stack <name>` — skip auto-detection, use the provided stack preset directly
- `--preset-only` — apply the matched preset without asking customization questions

## Mode Detection

```
If --stack flag is provided → skip detection, use that stack value directly

Otherwise:
  Read .claude/starter-context.json if it exists
    → Exists:
        - Use fields: stack, permissions.preset, permissions.disallowed_tools, permissions.readonly_paths
        - For each field that is null or missing → ask for that field only
    → Not found (standalone):
        - Auto-detect stack from project files
        - If detection fails → default to "general" preset, inform user:
          "Could not detect stack — using the general (read-only) preset. Pass --stack to override."
        - Show preset → confirm or customize (unless --preset-only is set)
```

## Load Preset

Read `settings-presets.json`, match by stack:

```
nodejs  → allow: Read, Write, Edit, Grep, Glob, Bash(npm:*), Bash(npx:*), Bash(node:*), Bash(git:*)
python  → allow: Read, Write, Edit, Grep, Glob, Bash(python:*), Bash(pip:*), Bash(pytest:*), Bash(git:*)
golang  → allow: Read, Write, Edit, Grep, Glob, Bash(go:*), Bash(git:*)
java    → allow: Read, Write, Edit, Grep, Glob, Bash(mvn:*), Bash(gradle:*), Bash(java:*), Bash(git:*)
rust    → allow: Read, Write, Edit, Grep, Glob, Bash(cargo:*), Bash(git:*)
general → allow: Read, Grep, Glob  (Write/Edit/Bash not allowed until user explicitly adds them)
```

Show the preset with a one-line explanation per rule. Then ask:
- "Any tools Claude should NOT use?" → add to `deny`
- "Any paths that should be read-only?" → add path-scoped deny rules (see Output Format)

Skip both questions if `--preset-only` is set.

**Multi-stack projects** (e.g., Node frontend + Python backend): apply the union of both presets.
Ask: "I detected both Node and Python — should I allow tools for both stacks?"

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
    "deny": [
      "Write(src/generated/*)",
      "Edit(src/generated/*)"
    ]
  }
}
```

**Readonly paths** map to `deny` rules scoped to that path:
- `src/generated/` read-only → `deny: ["Write(src/generated/*)", "Edit(src/generated/*)"]`
- `migrations/` read-only → `deny: ["Write(migrations/*)", "Edit(migrations/*)"]`

## Write Rules

- Check `.claude/settings.json` exists before writing → Overwrite / Merge / Skip?
- Merge: update `permissions` section only, never touch `hooks` section if already present
- Do not set permissions so restrictive that the team cannot do normal work
