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

Audit full harness health. Detect drift. Suggest next actions.

## Flag Handling

- `--drift-only` — skip component scoring (Step 1), run drift detection only (Step 2)
- `--tier-check` — skip drift detection (Step 2), show current tier and what is missing for the next tier upgrade

## Step 1 — Score Components

Read and score each component:

```
CLAUDE.md               → populated ✅ / has-placeholder ⚠️ / missing ❌
.claude/settings.json   → configured ✅ / exists-empty ⚠️ / missing ❌
settings.json hooks     → hooks configured ✅ / empty ⚠️ / missing ❌
.mcp.json               → servers configured ✅ / exists-empty ⚠️ / missing ❌
.claude/agents/         → agents present ✅ / missing ❌
docs/architecture.md    → exists ✅ / missing ❌
docs/adr/               → ADRs present ✅ / index-only ⚠️ / missing ❌
.claude/memory/         → MEMORY.md with content ✅ / exists-empty ⚠️ / missing ❌
```

Detect current tier from the `Harness config` section of `CLAUDE.md`.
If CLAUDE.md is missing: treat as Tier 0 (not configured).
If CLAUDE.md exists but tier is not specified: infer from what is present.

## Step 2 — Detect Drift

```
CLAUDE.md tech stack  ←→  package.json / pyproject.toml / go.mod
  New dependency not mentioned in CLAUDE.md?         → flag ⚠️ undocumented
  Dependency removed but still listed in CLAUDE.md?  → flag ⚠️ stale

Hooks in settings.json  ←→  tools present in project
  Hook references a tool no longer in devDependencies or PATH?  → flag ⚠️ stale

.mcp.json servers  ←→  services referenced in codebase (imports, env vars)
  Service used in code but no MCP server configured?  → flag ⚠️ missing

docs/architecture.md last modified  ←→  git log
  File not updated in 30+ days AND new directories added since?  → flag ⚠️ outdated

docs/adr/  ←→  git log
  Commits in past 30 days added/removed directories, changed framework,
  or modified core config (package.json, pyproject.toml)?
  AND no new ADR written?  → flag ⚠️ decision not recorded
```

## Step 3 — Health Report

```
## Harness Health — [project name]
Current tier: [Essential / Standard / Full]
Checked: YYYY-MM-DD

| Component            | Status | Issue                                      |
|----------------------|--------|--------------------------------------------|
| CLAUDE.md            | ✅     | —                                          |
| settings.json        | ✅     | —                                          |
| Hooks                | ⚠️     | prettier hook but prettier not in project  |
| .mcp.json            | ❌     | Redis used in code, no MCP server          |
| docs/architecture.md | ⚠️     | Not updated in 45 days                     |
| ADRs                 | ✅     | 3 ADRs present                             |
| .claude/memory/      | ❌     | Not set up (Tier 3 item)                   |

Drift detected: [list of flagged items, or "None"]
```

## Step 4 — Suggest Actions

Prioritize by severity: ❌ first, then ⚠️. Suggest one action at a time:

> "Want to fix [highest priority issue] now?"

If user accepts: invoke the relevant skill directly:
- Hooks issue → `/shipwithai-starter:setup-hooks`
- MCP issue → `/shipwithai-starter:setup-mcp`
- Agents issue → `/shipwithai-starter:setup-agents`
- SSOT/docs issue → `/shipwithai-starter:update-ssot`

Tier upgrade path:
- Tier 1 → list Standard tier items not yet configured
- Tier 2 → list Full tier items not yet configured
- To upgrade: run `/shipwithai-starter:cold-start-interview`
