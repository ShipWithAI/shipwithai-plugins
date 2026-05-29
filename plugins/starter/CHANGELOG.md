# Changelog

## [1.2.0] — 2026-05-29

### Added

- `new-project` skill — greenfield entry point: 3-phase interview (project goals →
  tech stack → architecture → conventions), scaffolds via official tools, then
  configures the Claude harness
- `init` now routes to `new-project` when no stack files are detected in directory
- `setup-memory` now writes a greenfield status marker and build order in CLAUDE.md
  when `project.stage` is `"greenfield"`

## [1.1.0] — 2026-05-28

### Added

- `init` skill schema v1.1: added `conventions.workflow_gates` field — multi-select
  workflow gates (plan-before-code, TDD, code-review, security-review)

## [1.0.0] — 2026-05-23

### Added

- `init` skill — main entry point, interview + orchestrator
- `setup-memory` skill — configures CLAUDE.md and .claude/memory/
- `setup-permissions` skill — configures .claude/settings.json allowedTools
- `setup-hooks` skill — configures .claude/settings.json hooks section
- `setup-mcp` skill — configures .mcp.json with MCP servers
- `setup-agents` skill — configures .claude/agents/
- `setup-ssot` skill — configures docs/architecture.md, ADRs, CODEMAPS
- `review` skill — harness health audit and drift detection
- `update-ssot` skill — syncs SSOT docs with codebase
- `add-mcp` command — quick MCP server addition
- `add-hook` command — quick hook addition
- `add-agent` command — quick agent creation
- `add-adr` command — quick ADR creation
- `drift-monitor` agent — weekly SSOT freshness check
- `references/settings-presets.json` — permission profiles for 7 stacks
- `references/hooks-catalog.json` — 10 hook templates
- `references/mcp-registry.json` — 8 MCP server entries
- `references/agents-catalog.json` — 5 common agent templates
- `references/adr-template.md` — ADR format
- `references/claude-md-template.md` — CLAUDE.md full template
