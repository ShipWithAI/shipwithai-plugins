---
name: setup-agents
description: >
  Configure .claude/agents/ with specialized sub-agents for your project.
  Called by cold-start-interview or standalone to configure the agents pillar.
  Trigger phrases: "setup agents", "configure agents", "add claude agents".
argument-hint: "[agent-name]"
---

# /setup-agents

Configures `.claude/agents/` với specialized agents cho project.

## Mode Detection

```
Đọc .claude/starter-context.json nếu tồn tại
  → Tồn tại: dùng fields agents_selected, project.type, project.team_size — skip suggest
  → Không tồn tại (standalone): load catalog → suggest theo project context → confirm
```

## Agent Suggestions

Load `agents-catalog.json`, suggest theo project context:

```
Tier 3 mặc định      → drift-monitor (luôn include)
Team > 3 người       → pr-review
Có background jobs   → worker-monitor
Có external APIs     → api-health-check
Có CI/CD             → deploy-sentinel
```

Với mỗi agent: show preview → confirm.

## Agent File Format

Theo convention của commercial-legal:

```markdown
---
name: [name]
description: >
  [Mô tả mục đích. Trigger phrases người dùng nói để invoke.
  Ví dụ: "check drift", "ssot health", "run drift monitor".]
model: sonnet
tools: ["Read", "Bash", "Glob", "Grep"]
---

# [Agent Name]

## Purpose

[Tại sao agent này tồn tại. Vấn đề nó giải quyết.]

## What it does

### Step 1 — [...]
### Step 2 — [...]

## What this agent does NOT do

- [Boundaries rõ ràng]
- Does not modify files directly
- Does not self-schedule
```

## Write Rules

- Write vào `.claude/agents/[name].md`
- `drift-monitor` luôn được include khi Tier 3
- Không overwrite agent đã có không hỏi
