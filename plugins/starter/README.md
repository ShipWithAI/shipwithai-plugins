# shipwithai-starter

> Sets up a standardized Claude Code harness for your project. One init interview → consistent setup across every team member.

## What it does

Configures 7 pillars of your Claude Code environment:

| Pillar | Files | Tier |
|--------|-------|------|
| Memory | `CLAUDE.md`, `.claude/memory/` | Essential |
| Permissions | `.claude/settings.json` | Essential |
| Hooks | `.claude/settings.json` hooks | Standard |
| MCP | `.mcp.json` | Standard |
| Agents | `.claude/agents/` | Full |
| SSOT | `docs/architecture.md`, `docs/adr/` | Full |
| Observability | `.claude/hooks/observe.py`, `.claude/logs/` | Full |

## Quick Start

```
/shipwithai-starter:init
```

Runs a guided interview (5–30 min depending on tier), then configures everything for you.

## Skills

| Skill | Description |
|-------|-------------|
| `/shipwithai-starter:init` | **Start here.** Setup interview + full harness configuration |
| `/shipwithai-starter:new-project` | **Greenfield.** 3-phase interview from empty directory → scaffold + harness |
| `/shipwithai-starter:review` | Audit harness health, detect drift, suggest upgrades |
| `/shipwithai-starter:update-ssot` | Sync CLAUDE.md and architecture docs with codebase |
| `/shipwithai-starter:setup-memory` | Configure CLAUDE.md + .claude/memory/ |
| `/shipwithai-starter:setup-permissions` | Configure .claude/settings.json permissions |
| `/shipwithai-starter:setup-hooks` | Configure .claude/settings.json hooks |
| `/shipwithai-starter:setup-mcp` | Configure .mcp.json MCP servers |
| `/shipwithai-starter:setup-agents` | Configure .claude/agents/ |
| `/shipwithai-starter:setup-ssot` | Configure architecture docs, ADRs, CODEMAPS |
| `/shipwithai-starter:setup-observability` | Enable tool call logging for harness optimization (Tier 3 opt-in) |
| `/shipwithai-starter:optimize-harness` | Analyze tool call logs and suggest hooks/gates based on actual usage patterns |

## Commands

| Command | Description |
|---------|-------------|
| `/shipwithai-starter:add-mcp` | Add a single MCP server |
| `/shipwithai-starter:add-hook` | Add a single hook |
| `/shipwithai-starter:add-agent` | Create a new agent |
| `/shipwithai-starter:add-adr` | Create an Architecture Decision Record |

## Agents

| Agent | Description |
|-------|-------------|
| `drift-monitor` | Weekly: checks if CLAUDE.md matches codebase reality |

## Tier Model

```
Tier 1 — Essential (5 min)   → Memory + Permissions
Tier 2 — Standard (15 min)   → + Hooks + MCP
Tier 3 — Full (30 min)       → + Agents + SSOT + Observability
```

Upgrade anytime: `/shipwithai-starter:review`

## Team Sharing

After setup, commit these files so teammates get the same harness automatically:

```bash
git add CLAUDE.md .claude/ .mcp.json docs/adr/ docs/CODEMAPS/
git commit -m "chore: add Claude Code harness"
```

Teammates clone → open Claude Code → harness is ready. No manual setup.
