# Design Spec: `shipwithai-starter` Plugin

**Date:** 2026-05-23
**Status:** Draft — awaiting user approval
**Author:** Claude Code (brainstorming session)

---

## Overview

`shipwithai-starter` là Claude Code plugin giúp team chuẩn hóa engineering harness cho mọi project dùng Claude Code. Một lần chạy `cold-start-interview` → mọi thành viên có cùng context, permissions, hooks, MCP, agents, và SSOT docs.

**Problem:** Mỗi dev setup Claude Code khác nhau → inconsistent behavior. CLAUDE.md viết vội, thiếu architecture context. Hooks, permissions, MCP config thủ công → lãng phí, dễ sai.

**Value prop:** *"Một cold-start interview → harness hoàn chỉnh cho cả team."*

---

## Section 1: Architecture

### Plugin Identity

- **Name:** `shipwithai-starter`
- **Namespace:** `/shipwithai-starter:<skill>`
- **Location:** `plugins/starter/` trong shipwithai-plugins repo

### 7 Pillars

| # | Pillar | Files configured |
|---|---|---|
| 1 | Memory | `CLAUDE.md`, `.claude/memory/` |
| 2 | Permissions | `.claude/settings.json` → allowedTools/disallowedTools |
| 3 | Hooks | `.claude/settings.json` → hooks section |
| 4 | MCP | `.mcp.json` |
| 5 | Agents | `.claude/agents/*.md` |
| 6 | SSOT | `docs/architecture.md`, `docs/adr/`, `docs/CODEMAPS/` |
| 7 | Observability | *(Phase 2 — deferred)* |

### Tier Model

```
Tier 1 — Essential (5 min)
  Pillars: Memory + Permissions
  → Minimum viable: Claude hiểu project, biết được làm gì

Tier 2 — Standard (15 min)
  Pillars: + Hooks + MCP
  → Automation + external connectivity

Tier 3 — Full (30 min)
  Pillars: + Agents + SSOT
  → Advanced: team-wide, self-documenting
```

### Component Map

```
Skills (complex, stateful):
  cold-start-interview   ← MANDATORY FIRST. Interview + orchestrator.
  setup-memory           ← Pillar skill: CLAUDE.md + memory
  setup-permissions      ← Pillar skill: settings.json allowedTools
  setup-hooks            ← Pillar skill: settings.json hooks
  setup-mcp              ← Pillar skill: .mcp.json
  setup-agents           ← Pillar skill: .claude/agents/
  setup-ssot             ← Pillar skill: docs/architecture, ADRs, CODEMAPS
  review                 ← Audit harness health + drift detection
  update-ssot            ← Sync SSOT docs với codebase

Commands (quick, stateless):
  add-mcp                ← Thêm 1 MCP server
  add-hook               ← Thêm 1 hook
  add-agent              ← Tạo 1 agent
  add-adr                ← Tạo 1 ADR

Agents (background):
  drift-monitor          ← Weekly SSOT freshness check

References (lazy-loaded):
  settings-presets.json
  hooks-catalog.json
  mcp-registry.json
  agents-catalog.json
  claude-md-template.md
  adr-template.md
```

---

## Section 2: `cold-start-interview`

Entry point bắt buộc. Không chạy skill nào khác trước cold-start.

### State Detection

Chạy trước khi hỏi bất cứ điều gì:

```
Đọc project state:
  CLAUDE.md              → populated / has [PLACEHOLDER] / missing
  .claude/settings.json  → exists / missing
  .mcp.json              → exists / missing
  .claude/agents/        → exists / missing
  docs/architecture.md   → exists / missing

Auto-detect stack:
  package.json           → Node/TypeScript
  pyproject.toml         → Python
  go.mod                 → Go
  Cargo.toml             → Rust
  pom.xml                → Java

Report: "Tôi thấy [summary]. Confirm stack và chọn tier?"
```

### Fork-First Preamble

Hiện trước khi hỏi bất cứ điều gì:

```
> shipwithai-starter thiết lập Claude Code harness cho project của bạn.
>
> Tier 1 — Essential (5 min): CLAUDE.md + permissions.
>   Claude hiểu project, biết được làm gì.
>
> Tier 2 — Standard (15 min): + hooks + MCP.
>   Auto-format, lint, kết nối external services.
>
> Tier 3 — Full (30 min): + agents + SSOT docs.
>   Architecture docs, ADRs, CODEMAPS, drift monitoring.
>
> Chọn tier? (Upgrade bất cứ lúc nào với /shipwithai-starter:review)
```

→ Wait for tier selection trước khi hỏi gì khác.

### Interview Flow

**Part 0 — Stack confirmation** *(auto-detected, chỉ confirm)*
- Confirm detected stack. Nếu không detect → hỏi: language, framework, build tool, test framework.

**Part 1 — Project identity** *(Tier 1+)*
- Project name + type (web app / API / CLI / lib / monorepo)
- Team size
- Stage (greenfield / active / maintenance)

**Part 2 — Architecture** *(Tier 1+)*
- Architecture style (monolith / microservices / modular monolith)
- Key layers + thư mục tương ứng
- Entry points
- External dependencies (DB, queue, cache)
- "Paste `tree -L 3` hoặc tôi tự scan" → extract key dirs
- Gotchas: generated dirs, build order, test isolation, sensitive areas

**Part 3 — Conventions** *(Tier 1+)*
- Detect eslint/prettier/black/gofmt → confirm, không hỏi lại
- Nếu không detect → hỏi: code style, branch strategy, commit format, test coverage target

**Part 4 — Permissions** *(Tier 1+)*
- Load preset từ `settings-presets.json` theo detected stack
- Show preset + giải thích → confirm hoặc customize
- Hỏi: tools nào KHÔNG được dùng, paths nào chỉ đọc

**Part 5 — Hooks** *(Tier 2+)*
- Detect tools → suggest từ `hooks-catalog.json`
- Từng hook một. Show preview trước khi confirm.

**Part 6 — MCP** *(Tier 2+)*
- "Project interact với services nào?"
- Show list từ `mcp-registry.json`
- Verify connection thực sự (không trust `.mcp.json` declarations)

**Part 7 — Agents** *(Tier 3+)*
- Suggest từ `agents-catalog.json` theo project type/team size
- Show preview từng agent → confirm

**Part 8 — SSOT** *(Tier 3+)*
- Tạo `docs/architecture.md`? → Draft từ Part 2 answers
- Setup ADR structure? → `docs/adr/` + ADR-0001-init
- Tạo CODEMAPS? → `docs/CODEMAPS/` structure guide

### Orchestration Phase

Sau khi interview xong:

```
1. Generate preview toàn bộ files sẽ write:
   ┌──────────────────────────────────────┬──────────┬───────┐
   │ File                                 │ Action   │ Tier  │
   ├──────────────────────────────────────┼──────────┼───────┤
   │ CLAUDE.md                            │ CREATE   │ 1     │
   │ .claude/settings.json (permissions)  │ CREATE   │ 1     │
   │ .claude/settings.json (hooks)        │ UPDATE   │ 2     │
   │ .mcp.json                            │ CREATE   │ 2     │
   │ .claude/agents/drift-monitor.md      │ CREATE   │ 3     │
   │ docs/architecture.md                 │ CREATE   │ 3     │
   └──────────────────────────────────────┴──────────┴───────┘
   Confirm không?

2. User approve → invoke pillar skills theo tier:
   setup-memory       (pass context từ interview)
   setup-permissions  (pass context)
   setup-hooks        (Tier 2+ only)
   setup-mcp          (Tier 2+ only)
   setup-agents       (Tier 3+ only)
   setup-ssot         (Tier 3+ only)

3. After-write:
   - Summary table: files created/updated/skipped
   - "Commit .claude/ và CLAUDE.md để team share harness"
   - Suggest test: "Muốn simulate một task nhỏ?"
   - Upgrade note: "Đang Tier [N]. Upgrade với /shipwithai-starter:review"
```

### Failure Modes

```
Don't guess stack nếu ambiguous → hỏi
Don't write hooks cho tool không detect được
Don't add MCP nếu chưa verify connection
Don't overwrite existing file không hỏi
Don't skip gotchas section
Don't proceed nếu user chưa confirm preview
```

---

## Section 3: Pillar Skills

Mỗi pillar skill có 2 modes:
- **Called from cold-start:** Nhận context → skip questions → generate → write
- **Standalone:** Đọc existing config → hỏi missing → generate → write

Pattern chung:
```
1. Check mode (có context không?)
2. Generate file content
3. Check file exists → Overwrite / Merge / Skip?
4. Confirm → write
```

### `setup-memory`

**Writes:** `CLAUDE.md`, `.claude/memory/` (Tier 3+)

CLAUDE.md sections:
- Project identity (name, type, stage, team size)
- Tech stack (language, framework, build tool, test, package manager)
- Architecture overview (style, layers, entry points, key dirs)
- Key conventions (code style, branch strategy, commit format)
- Gotchas (generated dirs, build order, test isolation, sensitive areas)
- Harness config (tier, installed MCP, active hooks)

`.claude/memory/` (Tier 3 only): `MEMORY.md` (index), `project.md`, `team.md`

### `setup-permissions`

**Writes:** `.claude/settings.json` → allowedTools, disallowedTools

Load preset từ `settings-presets.json` theo stack → apply user overrides.

Presets:
- `nodejs`: Read/Write/Edit/Grep/Glob + Bash(npm,npx,node,git)
- `python`: Read/Write/Edit/Grep/Glob + Bash(python,pip,pytest,git)
- `golang`: Read/Write/Edit/Grep/Glob + Bash(go,git)
- `java`: Read/Write/Edit/Grep/Glob + Bash(mvn,gradle,java,git)
- `rust`: Read/Write/Edit/Grep/Glob + Bash(cargo,git)
- `general`: Read only, require-confirm(Write,Bash)

### `setup-hooks`

**Writes:** `.claude/settings.json` → hooks section

Map detected tools → `hooks-catalog.json` entries. Merge vào settings.json (không overwrite permissions section).

### `setup-mcp`

**Writes:** `.mcp.json`

Lookup trong `mcp-registry.json` → show preview → test connection (✓/⚪/✗) → confirm → write. Không báo ✓ nếu chưa test thực sự.

### `setup-agents`

**Writes:** `.claude/agents/*.md`

Suggest từ `agents-catalog.json` theo project type. Luôn include `drift-monitor` khi Tier 3.

Agent file format:
```markdown
---
name: [name]
description: >
  [trigger phrases, purpose]
model: sonnet
tools: ["Read", "Bash", "Glob", "Grep"]
---
# [Name]
## Purpose
## What it does
## What it does NOT do
```

### `setup-ssot`

**Writes:** `docs/architecture.md`, `docs/adr/`, `docs/CODEMAPS/`

Draft `docs/architecture.md` từ Part 2 answers — dùng actual paths từ codebase scan, không generic.

ADR structure: `docs/adr/README.md` + `docs/adr/ADR-0001-initial-architecture.md`

---

## Section 4: Skills hỗ trợ, Commands & Agents

### Skill: `review`

```
Step 1: Read all configured files → score each component
Step 2: Detect drift (CLAUDE.md vs codebase, hooks vs tools, MCP vs services)
Step 3: Health report table (✅/⚠️/❌ per component)
Step 4: Suggest highest priority fix, one at a time
         + Upgrade path nếu có tier cao hơn
```

### Skill: `update-ssot`

```
Step 1: Diff CLAUDE.md sections vs codebase thực tế
Step 2: Report differences cụ thể
Step 3: Update từng section: show current → show proposed → confirm → write
Step 4: Update timestamp trong CLAUDE.md
```

### Commands

**`add-mcp`:** Lookup registry → preview → test connection → append `.mcp.json` → update CLAUDE.md

**`add-hook`:** Hỏi trigger/tool/pattern/command → preview → merge `settings.json`

**`add-agent`:** Suggest catalog → draft `.md` → confirm → write `.claude/agents/`

**`add-adr`:** Count existing → hỏi title/context/options/decision → draft → write `docs/adr/ADR-[XXXX]-[slug].md` → update CLAUDE.md table

### Agent: `drift-monitor`

```yaml
model: sonnet
tools: ["Read", "Bash", "Glob", "Grep"]
schedule: weekly (Monday morning — user sets up crontab manually)
```

Steps:
1. Read CLAUDE.md → extract stack, dirs, tools, MCP, hooks
2. Scan codebase: package.json, tree, .mcp.json, settings.json, git log
3. Diff và flag: missing paths, undocumented deps, stale hooks, unused MCP
4. Report drift table → suggest `update-ssot`

**Does NOT:** Modify files, self-schedule, report code quality.

---

## Section 5: File Structure & References

### Plugin File Structure

```
plugins/starter/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── skills/
│   ├── cold-start-interview/SKILL.md
│   ├── setup-memory/SKILL.md
│   ├── setup-permissions/SKILL.md
│   ├── setup-hooks/SKILL.md
│   ├── setup-mcp/SKILL.md
│   ├── setup-agents/SKILL.md
│   ├── setup-ssot/SKILL.md
│   ├── review/SKILL.md
│   └── update-ssot/SKILL.md
├── commands/
│   ├── add-mcp.md
│   ├── add-hook.md
│   ├── add-agent.md
│   └── add-adr.md
├── agents/
│   └── drift-monitor.md
├── references/
│   ├── settings-presets.json
│   ├── hooks-catalog.json
│   ├── mcp-registry.json
│   ├── agents-catalog.json
│   ├── claude-md-template.md
│   └── adr-template.md
├── evals/
│   └── evals.json
├── CLAUDE.md
├── CHANGELOG.md
└── README.md
```

### Size Estimates

| File | Est. Lines | Note |
|---|---|---|
| cold-start-interview/SKILL.md | ~250 | Interview flow + orchestration |
| setup-memory/SKILL.md | ~120 | CLAUDE.md template + memory |
| setup-permissions/SKILL.md | ~80 | Preset lookup + override |
| setup-hooks/SKILL.md | ~80 | Catalog lookup + merge |
| setup-mcp/SKILL.md | ~80 | Registry lookup + verify |
| setup-agents/SKILL.md | ~80 | Catalog + template |
| setup-ssot/SKILL.md | ~100 | 3 output types |
| review/SKILL.md | ~120 | Audit + drift + suggest |
| update-ssot/SKILL.md | ~80 | Diff + section-by-section |

Tất cả dưới 300 lines — đúng convention (hard cap 500).

### Evals

5 test prompts minimum:
1. "Set up Claude Code harness for this project" → cold-start-interview
2. "Configure claude for my team" → cold-start-interview
3. "Check my harness setup" → review
4. "My CLAUDE.md is outdated" → update-ssot
5. "Onboard this project to Claude Code" → cold-start-interview
6. "Add GitHub MCP" → add-mcp command
7. "Add prettier hook" → add-hook command

---

## Decisions Log

| Decision | Choice | Rationale |
|---|---|---|
| harness-optimizer | Deferred Phase 2 | Cần observability data; skip until Phase 2 |
| Config location | Project-level only | Mỗi project khác nhau; no user-level state |
| cold-start write strategy | Preview + confirm (Option C) | Safety: touch sensitive files; builds trust |
| cold-start architecture | Monolithic interview + pillar sub-skills | Interview continuity + pillar reusability |
| Tier model | 3 tiers by dependency | Essential→Standard→Full maps to real dependencies |
| Observability | Phase 2 | Scope management |

---

## Out of Scope (Phase 1)

- Observability (logging hooks, `.claude/logs/`, session tracking)
- `harness-optimizer` agent (learning loop)
- User-level profile (cross-project preferences)
- Dashboard/reporting UI
