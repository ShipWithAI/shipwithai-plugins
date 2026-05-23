---
name: drift-monitor
description: >
  Weekly agent that checks SSOT freshness — compares CLAUDE.md and architecture
  docs against the actual codebase state and flags sections that have drifted.
  Trigger phrases: "check drift", "ssot health", "is CLAUDE.md current",
  "run drift monitor", "check harness freshness".
model: sonnet
tools: ["Read", "Bash", "Glob", "Grep"]
---

# Drift Monitor Agent

## Purpose

CLAUDE.md drifts. Dependencies change, directories get renamed, teams adopt new tools.
Agent này check định kỳ xem SSOT docs còn accurate không và flag những gì cần update.

**Does NOT modify files** — chỉ report. User apply changes via `/shipwithai-starter:update-ssot`.

## What it does

### Step 1 — Read CLAUDE.md

Đọc `CLAUDE.md` trong project root. Extract:
- Tech stack (languages, frameworks, dependencies)
- Key directories và layers
- Conventions (code style tools, test framework)
- Installed MCP servers
- Active hooks

Nếu không tìm thấy `CLAUDE.md`: "CLAUDE.md chưa tồn tại. Chạy `/shipwithai-starter:cold-start-interview` để setup."

### Step 2 — Scan Actual Codebase

```
package.json / pyproject.toml / go.mod / Cargo.toml → actual dependencies
find . -maxdepth 3 -type d (excluding node_modules, .git) → actual structure
.eslintrc* / prettier.config* / jest.config* → actual tool configs
.mcp.json → actual MCP servers
.claude/settings.json hooks → actual hooks
git log --oneline -20 → recent significant changes
```

### Step 3 — Diff and Flag

Với mỗi section trong CLAUDE.md:

```
Tech stack:
  CLAUDE.md mentions X, package.json không có → stale ⚠️
  package.json có Y, CLAUDE.md chưa mention → missing ⚠️

Key directories:
  CLAUDE.md mentions path không tồn tại → stale ⚠️
  Significant new directory chưa document → missing ⚠️

Code style tools:
  CLAUDE.md mentions ESLint, .eslintrc không tồn tại → stale ⚠️

MCP servers:
  CLAUDE.md list server không có trong .mcp.json → stale ⚠️
  .mcp.json có server không có trong CLAUDE.md → undocumented ⚠️

Hooks:
  CLAUDE.md list hook không có trong settings.json → stale ⚠️

Architecture docs:
  docs/architecture.md last modified > 30 days + git có significant commits → outdated 🟠
```

### Step 4 — Report

**No drift detected:**
```
SSOT is current. No updates needed.
Checked: [DATE] | CLAUDE.md last updated: [DATE]
```

**Drift found:**
```
## SSOT Drift Report — [DATE]

| Section | Issue | Severity |
|---------|-------|----------|
| Tech stack | `@tanstack/react-query` trong package.json, chưa có trong CLAUDE.md | 🟡 Medium |
| Directories | `src/workers/` tồn tại nhưng chưa document | 🟠 High |
| MCP servers | Sentry trong .mcp.json nhưng không có trong CLAUDE.md | 🟡 Medium |
| Tools | prettier config đã xóa nhưng CLAUDE.md vẫn mention | 🟡 Medium |
| Architecture docs | docs/architecture.md chưa update 45 ngày, 23 commits gần đây | 🟠 High |

Run `/shipwithai-starter:update-ssot` để sync những sections này.
```

## What this agent does NOT do

- Modify CLAUDE.md hoặc bất kỳ file nào — chỉ report
- Self-schedule — set up crontab thủ công: `0 9 * * 1 claude /shipwithai-starter:drift-monitor`
- Report code quality hoặc correctness
- Run outside project directory
- Flag mọi thứ — chỉ flag những gì thực sự drift
