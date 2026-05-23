---
name: add-agent
description: >
  Create a new agent in .claude/agents/. Quick operation, no full interview needed.
  Trigger phrases: "add agent", "create agent", "add [name] agent".
argument-hint: "[agent-name] [--model haiku|sonnet|opus]"
---

# /add-agent

Tạo một agent mới trong `.claude/agents/`. Stateless.

## Steps

1. Check `references/agents-catalog.json` nếu có match với intent.
   - Match: show preset, confirm hoặc customize.
   - No match: hỏi:
     - Agent name + purpose?
     - Model: haiku (fast/cheap) / sonnet (balanced) / opus (complex reasoning)?
     - Tools needed: Read, Write, Bash, Glob, Grep, mcp__*?
     - Trigger phrases người dùng nói để invoke agent?
     - Schedule nếu là background agent?

2. Draft agent file theo format chuẩn:
   ```markdown
   ---
   name: [name]
   description: >
     [purpose + trigger phrases]
   model: [haiku|sonnet|opus]
   tools: ["Read", "Bash", "Glob", "Grep"]
   ---
   # [Agent Name]
   ## Purpose
   ## What it does
   ## What this agent does NOT do
   ```

3. Show preview → confirm → write `.claude/agents/[name].md`.

4. Note: "Claude Code agents không self-schedule. Set up crontab thủ công nếu cần."
