# shipwithai-starter — Plugin Development Context

> Plugin development workspace. Stack: none (content-only plugin).
> Last updated: 2026-06-06.

## Plugin Identity

- **Name:** `shipwithai-starter`
- **Namespace:** `/shipwithai-starter:<skill>`
- **Purpose:** Sets up Claude Code harness for any project — CLAUDE.md, permissions, hooks, MCP, agents, SSOT docs.

## File Conventions

- Skill directories: lowercase with dashes (`init`)
- SKILL.md: always uppercase filename
- Reference files: lowercase with dashes (`settings-presets.json`)
- Command files: lowercase with dashes (`add-mcp.md`)
- Agent files: lowercase with dashes (`drift-monitor.md`)

## Quality Standards

- SKILL.md hard cap: 500 lines (ideal < 300)
- Skill descriptions: < 200 characters, include trigger phrases
- Every skill: must have corresponding entry in `evals/evals.json`
- References: lazy-loaded only when skill needs them

## Design Decisions

See `docs/superpowers/specs/2026-05-23-shipwithai-starter-design.md` for full design spec.

Key decisions:
- 7 pillars: Memory, Permissions, Hooks, MCP, Agents, SSOT, Observability
- 3 tiers: Essential → Standard → Full
- init is mandatory first — orchestrates pillar skills
- Pillar skills work both called-from-init AND standalone
- All config written to project-level (no user-level profile)
- Observability shipped in Phase 2 (setup-observability skill, observe.py hook, ADR-0002)
- harness-optimizer shipped in v2.1.0 (optimize-harness skill, optimize-rules.json, harness-optimizer agent)
- MCP registry expanded to 14 servers in v2.2.0; custom MCP entry support added (flow in setup-mcp + add-mcp fallback)
- dashboard command added in v2.2.0 (read-only aggregate health across all harness-configured projects)
