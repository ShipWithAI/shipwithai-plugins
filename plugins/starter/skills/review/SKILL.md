---
name: review
description: >
  Audit the current Claude Code harness health: check configured components,
  detect drift from the codebase, and suggest fixes or tier upgrades.
  Trigger phrases: "review harness", "check setup", "harness health",
  "what's missing", "upgrade tier", "audit claude config".
argument-hint: "[--drift-only] [--tier-check]"
---

# /review

Audit toàn bộ harness health. Detect drift. Suggest next actions.

## Step 1 — Read Current State

Đọc và score từng component:

```
CLAUDE.md              → populated ✅ / has-placeholder ⚠️ / missing ❌
.claude/settings.json  → configured ✅ / exists-empty ⚠️ / missing ❌
settings.json hooks    → hooks configured ✅ / empty ⚠️ / missing ❌
.mcp.json              → servers configured ✅ / exists-empty ⚠️ / missing ❌
.claude/agents/        → agents present ✅ / missing ❌
docs/architecture.md   → exists ✅ / missing ❌
docs/adr/              → ADRs present ✅ / missing ❌
.claude/memory/        → setup ✅ / missing ❌
```

Detect current tier từ `CLAUDE.md` "Harness config" section.

## Step 2 — Detect Drift

```
CLAUDE.md stack vs package.json thực tế
  → New deps chưa document? → flag ⚠️

Hooks configured vs tools present in project
  → Hook cho tool đã uninstall? → flag ⚠️ stale

.mcp.json servers vs services mentioned in codebase
  → Service trong code nhưng chưa có MCP? → flag ⚠️ missing
  → MCP server không có tool call nào gần đây? → flag ⚠️ unused

docs/architecture.md last modified vs git log
  → Chưa update > 30 ngày + có significant commits? → flag ⚠️ outdated

ADR count vs major git commits
  → Significant architectural changes không có ADR? → flag ⚠️
```

## Step 3 — Health Report

```
## Harness Health — [project name]
Current tier: [Essential / Standard / Full]
Checked: [DATE]

| Component           | Status | Issue                                  |
|---------------------|--------|----------------------------------------|
| CLAUDE.md           | ✅     | —                                      |
| settings.json       | ✅     | —                                      |
| Hooks               | ⚠️     | prettier hook nhưng không có devDep    |
| .mcp.json           | ❌     | Redis detect trong code, chưa có MCP   |
| docs/architecture.md| ⚠️     | Chưa update 45 ngày                    |
| ADRs                | ✅     | 3 ADRs                                 |
| .claude/memory/     | ❌     | Chưa setup (Tier 3)                    |

Drift detected: [list hoặc "None"]
```

## Step 4 — Suggest Actions (one at a time)

Prioritize theo severity: ❌ trước, rồi ⚠️.

"Muốn fix [highest priority issue] ngay không?"

Upgrade path:
- Tier 1 → suggest Tier 2 items nếu chưa có
- Tier 2 → suggest Tier 3 items nếu chưa có
- "Upgrade với `/shipwithai-starter:cold-start-interview --redo --tier standard`"
