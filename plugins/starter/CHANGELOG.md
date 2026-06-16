# Changelog

## [2.3.0] — 2026-06-16

### Added

- **Stack-plugin routing** — `init` now recommends a dedicated ShipWithAI plugin
  based on the detected stack (launcher model). New `init/stack-recipes.json` maps
  a stack to a `recommendPlugin` + `setupCommand`; first recipe ships `spring-boot`
  → `shipwithai-java-backend-toolkit`.
- `init` Part 6.6 (Tier 2+): surfaces the matched stack plugin and, on confirm,
  records it in `stack_plugins_selected` and invokes its setup in Step 5. Recommend-
  only — never force-installs a plugin the user has not enabled.
- `init` schema v1.4: adds `stack_plugins_selected` field; Update Mode offers the
  recommendation when the field is missing.
- `review` schema-version check updated: v1.4 is now current; v1.3/v1.2 report as
  outdated (→ `init --update`) so existing harnesses are prompted to pick up the
  stack-plugin field.
- `review` stack-plugin coverage check: on a project whose stack matches a recipe,
  flags the recommended plugin as ⚠️ when its `verifyArtifact` is absent (drift-style —
  distinguishes "selected but not installed" from "available but not set up"). New
  `verifyArtifact` field in `stack-recipes.json`.

### Fixed

- `new-project` wrote a stale **v1.1** `starter-context.json` (missing `workflow_gates`,
  `observability.enabled`, `skills_selected`, `stack_plugins_selected`) — it would have
  been flagged outdated by `review` the moment it was created. Now emits the current
  **v1.4** schema with essential-tier defaults.

## [2.2.0] — 2026-06-15

### Added

- `setup-skills` skill — provisions reusable project-level skills into
  `.claude/skills/`, the sibling of `setup-agents` for the skills artifact type.
  Catalog-driven (`skills-catalog.json`), extensible.
- `git-workflow` installable skill (flagship) — commit message format, branch
  naming, and PR flow, **generated to match the conventions chosen at init**
  (`commit_format`, `branch_strategy`). Template + inject via
  `templates/git-workflow.SKILL.md.tmpl` and `git-workflow.variants.json`
  (3 commit variants × 2 branch variants). Committed into the user's repo so
  teammates get it without installing the plugin.
- `init` schema v1.3: adds `skills_selected` field; Part 6.5 (Tier 2+) offers
  git-workflow; preview table and Step 5 orchestration updated.
- `review` Step 2b: project-skill staleness check — compares installed
  `template_version` against the catalog and flags skills behind the current
  template. Health report gains a `Project skills` row.

### Fixed

- `plugin.json` skills array: added the missing `optimize-harness` entry
  (was present in `manifest.json` and on disk but absent from `plugin.json`).

## [2.1.0] — 2026-06-06

### Added

- `optimize-harness` skill — runtime harness optimization from observability logs
  - 3-phase guard: checks observability enabled, ≥7 days data, 7-day cooldown advisory
  - 6-phase analysis pipeline: parse → aggregate → correlate → score rules → filter/rank → report
  - 8 rules (R1-R8): jest/pytest/make/cargo test hooks, JS/TS/Python formatters, security gate,
    heavily-edited-without-tests, long session duration
  - Supports `--verbose` (show LOW confidence), `--window N` (custom days), `--json`, `--force`
  - Writes `optimizer.last_run` to `starter-context.json` after each run
- `optimize-rules.json` — externalized rule definitions (R1-R8), extend without editing SKILL.md
- `agents/harness-optimizer.md` — lightweight agent (Haiku) that invokes optimize-harness
- `review` skill — Step 2b: Static Analysis, runs for all tiers (no runtime logs required)
  - **Hook binary check**: for each hook in `settings.json`, verifies the effective binary
    (`npx <pkg>` → checks `<pkg>`; otherwise first token) exists in `devDependencies` or PATH
  - **Hook pattern match check**: for hooks that filter by file extension, verifies matching
    files exist in the project (skips `node_modules`)
  - **MCP usage vs codebase (bidirectional)**: compares `.mcp.json` servers against actual
    imports/CLI usage in source files; flags MCP configured but unused AND imports present
    but no MCP configured; covers GitHub, Linear, Slack, Sentry, PostgreSQL, Notion, Jira
  - Health report table extended with `Hook binaries`, `Hook patterns`, `MCP alignment` rows
    and a `Static analysis:` summary line
- `evals.json` — 2 new eval prompts covering hook binary missing and MCP bidirectional mismatch

## [2.0.0] — 2026-06-01

### Added

- `setup-observability` skill — Pillar 7: installs `observe.py` PostToolUse hook that
  logs tool call metadata (tool name, relative file path, command argv[0]) to
  `.claude/logs/YYYY-MM-DD.jsonl`
- `assets/observe.py` — stdlib-only Python hook script; silent-fails to never block
  tool execution; respects `DISABLE_OBSERVE=1` env var for per-session opt-out;
  passthrough stdout for hook chaining
- Log rotation via Stop hook: `find .claude/logs -name '*.jsonl' -mtime +30 -delete`
- `init` updated: schema v1.2 adds `observability.enabled` field; Tier 3 flow now
  invokes `setup-observability`; preview table includes observe.py and .gitignore entry
- `review` updated: checks observe.py presence, .claude/logs/ gitignore status,
  schema v1.2 currency; suggests setup-observability for Tier 3 projects
- `hooks-catalog.json` updated: adds observability hook template entry

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
