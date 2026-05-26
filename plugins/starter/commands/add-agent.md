---
name: add-agent
description: >
  Create a new agent in .claude/agents/. Quick operation, no full interview needed.
  Trigger phrases: "add agent", "create agent", "add [name] agent".
argument-hint: "[agent-name] [--model haiku|sonnet|opus]"
---

# /add-agent

Create a new agent in `.claude/agents/`. Stateless.

## Steps

1. Check `skills/setup-agents/agents-catalog.json` for a match with the user's intent.
   - Match: show preset, confirm or customize.
   - No match: ask:
     - Agent name and purpose?
     - Context type: autonomous (self-orients by reading files) or task-specific (needs input from caller)?
     - Model: haiku (fast, read-only tasks) / sonnet (analysis, code review) / opus (complex reasoning)?
     - Tools needed: Read, Bash, Glob, Grep, WebFetch?
     - For autonomous: which files does it read on startup?
     - For task-specific: what parameters must the caller pass in the prompt?
     - Trigger phrases to invoke this agent?

2. Draft agent file using the standard format:
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

   [Why this agent exists. What problem it solves.]

   ## Context

   **Reads on startup:**
   - [files this agent reads to orient itself]

   **Expects in prompt:** *(task-specific agents only)*
   - [PARAM_NAME]: [description and how to pass it]

   ## Steps

   ### Step 1 — [Action]
   [Description]

   ## Boundaries

   - Does not modify files directly
   - Does not self-schedule
   ```

3. Show preview → confirm → write `.claude/agents/[name].md`.
   If file already exists: offer skip or overwrite, do not silently replace.

4. Note: "Claude Code agents do not self-schedule. Set up a crontab manually if needed."
