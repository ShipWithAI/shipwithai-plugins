---
name: update-ssot
description: >
  Sync CLAUDE.md and architecture docs with the current state of the codebase.
  Use after significant changes: new dependencies, refactoring, architecture shifts.
  Trigger phrases: "update CLAUDE.md", "sync docs", "CLAUDE.md is outdated",
  "update architecture docs", "sync ssot".
argument-hint: "[--section stack|architecture|conventions|all]"
---

# /update-ssot

Sync SSOT docs với codebase thực tế. Section-by-section, confirm từng phần.

## Step 1 — Diff CLAUDE.md vs Codebase

```
Tech stack section vs package.json / pyproject.toml / go.mod:
  → New dependency chưa mention trong CLAUDE.md? → flag
  → Dependency đã remove nhưng vẫn còn trong CLAUDE.md? → flag

Key directories vs actual tree -L 3:
  → Directory mới tạo chưa document? → flag
  → Directory mention trong CLAUDE.md không còn tồn tại? → flag

Build tool vs Makefile / scripts / package.json scripts:
  → Changed? → flag

Test framework vs config files:
  → Changed? → flag

Hooks section vs .claude/settings.json hooks:
  → Mismatch? → flag

MCP section vs .mcp.json:
  → Mismatch? → flag
```

## Step 2 — Report Differences

```
Tôi thấy những khác biệt này:
- package.json có `@tanstack/react-query` nhưng CLAUDE.md chưa mention
- `src/workers/` mới tạo nhưng không có trong architecture section
- `.eslintrc.json` đã xóa nhưng CLAUDE.md vẫn mention ESLint
- `.mcp.json` có Sentry nhưng CLAUDE.md không list
```

## Step 3 — Update Section by Section

Với mỗi difference:

```
Section: Tech stack
Current:  "Framework: Next.js 14"
Proposed: "Framework: Next.js 15, @tanstack/react-query 5"

Update this section? [Yes / Skip / Edit manually]
```

Chờ confirm từng section. Không batch update tất cả.

## Step 4 — Update Timestamp

Sau khi update: set `**Last updated:** [DATE]` trong CLAUDE.md harness config section.

## Failure Modes

```
Don't update sections user chưa confirm
Don't remove information mà không hỏi (có thể intentional)
Don't guess meaning của changes — describe what you see
```
