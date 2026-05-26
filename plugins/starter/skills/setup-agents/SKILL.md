---
name: setup-agents
description: >
  Configure .claude/agents/ with specialized sub-agents for your project.
  Called by init or standalone to configure the agents pillar.
  Trigger phrases: "setup agents", "configure agents", "add claude agents".
argument-hint: "[agent-name]"
---

# /setup-agents

Configures `.claude/agents/` with specialized sub-agents for the project.

## Mode Detection

```
Read .claude/starter-context.json if it exists
  → Exists: use fields agents_selected, project.type, project.team_size, project.tier — skip suggest
  → Does not exist (standalone): load catalog → detect context → suggest → confirm
```

## Argument Handling

If an agent name is passed directly (e.g. `/setup-agents pr-review`): skip the suggestion
step and go straight to that agent's entry in the catalog.

## Context Detection

Load `agents-catalog.json`. For each entry, evaluate `suggestWhen`:

1. **files**: check whether any listed glob exists in the project root
2. **context**: if `.claude/starter-context.json` exists, evaluate conditions against its fields
   - `teamSize > N` → read `project.team_size`
   - `tier == N` → read `project.tier`
3. **always**: if `alwaysInclude` is `true`, suggest unconditionally — present first

In standalone mode without `starter-context.json`: ask the user for context that cannot
be inferred from files (e.g. "How many people work on this project?").

For each suggested agent: show preview → confirm before writing.

## How Sub-Agent Context Works

Sub-agents receive **only two inputs** when invoked:
1. Their agent file content (system prompt)
2. The prompt string passed by the main agent at invocation time

They do **not** inherit the main agent's conversation history or open files.

Two patterns handle this:

**Autonomous agents** — self-orient by reading project files on startup.
No runtime input needed beyond a trigger phrase.
Examples: drift-monitor, dependency-scanner, test-coverage.

**Task-specific agents** — require runtime context passed in the invocation prompt.
The caller must include specific parameters (e.g. PR number, branch name).
Examples: pr-review.

Use `contextType` in the catalog to identify which pattern each agent follows.

## Agent File Format

Write to `.claude/agents/[id].md` using this structure:

```markdown
---
name: [id]
description: >
  [One sentence: what this agent does and when to invoke it.
  Include trigger phrases, e.g. "check drift", "run health check".]
model: [sonnet|haiku]
tools: ["Read", "Bash", "Glob", "Grep"]
---

# [Agent Name]

## Purpose

[Why this agent exists. What problem it solves.]

## Context

**Reads on startup:**
- `CLAUDE.md` — project conventions and standards
- `[other files this agent always reads to orient itself]`

**Expects in prompt:** *(omit this block for autonomous agents)*
- `[PARAM_NAME]`: [what it is and how to pass it]

## Steps

### Step 1 — [Action]
[Description]

### Step 2 — [Action]
[Description]

## Boundaries

- Does not modify files directly
- Does not self-schedule
- [Other explicit limits for this agent]
```

**Model selection:**
- `haiku`: read-only checks, simple scans, lightweight file inspection
- `sonnet`: analysis requiring judgment, code review, multi-step reasoning

**Tools selection:** include only what the agent needs.
- Read/Glob/Grep — file inspection
- Bash — running commands or scripts

## Write Rules

- Create `.claude/agents/` directory if it does not exist
- Write one file per agent: `.claude/agents/[id].md`
- Before writing: check if the file already exists — offer skip or overwrite, do not silently replace
- For autonomous agents: populate `Reads on startup` from `selfDiscovers` in the catalog
- For task-specific agents: populate `Expects in prompt` from `expects` in the catalog

## Post-Write

If `.claude/starter-context.json` exists:
→ Update the `agents_selected` field with the list of agent `id` values that were written
