---
name: init
description: >
  Set up the Claude Code harness for this project. Configures CLAUDE.md, permissions,
  hooks, MCP servers, agents, and SSOT docs based on your stack and chosen tier.
  Run on first setup or when CLAUDE.md is missing or has [PLACEHOLDER] markers.
  Trigger phrases: "set up harness", "configure claude", "onboard project",
  "bootstrap claude", "let's get started", "setup claude code".
argument-hint: "[--redo] [--tier essential|standard|full]"
---

# /init

Mandatory entry point for the plugin. Do not run any other skill before init completes.

## Instructions

### Step 1 — State Detection

Before asking anything, read the project state:

```
CLAUDE.md              → populated / has [PLACEHOLDER] / missing
.claude/settings.json  → exists / missing
.mcp.json              → exists / missing
.claude/agents/        → exists / missing
docs/architecture.md   → exists / missing
```

Auto-detect tech stack:
```
package.json           → Node/TypeScript
pyproject.toml         → Python
go.mod                 → Go
Cargo.toml             → Rust
pom.xml / build.gradle → Java
Gemfile                → Ruby
```

Detect existing tools:
```
.eslintrc* / eslint.config.*   → ESLint
prettier.config* / .prettierrc → Prettier
jest.config*                   → Jest
pytest.ini / conftest.py       → pytest
Makefile                       → make
docker-compose.yml             → Docker Compose
```

If CLAUDE.md is already populated and `--redo` is not set: "Harness is already set up. Want to redo? (use --redo)"

If `--tier` argument is provided, skip the tier selection prompt in Step 2 and use the given value directly.

### Step 2 — Fork-First Preamble

Show immediately after state detection, before asking anything:

> **shipwithai-starter** sets up a standard Claude Code harness for your project.
>
> **Tier 1 — Essential (5 min):** CLAUDE.md with tech stack + conventions + architecture,
> `docs/architecture.md`, `.claude/settings.json` with stack-appropriate permissions. Ready to use immediately.
>
> **Tier 2 — Standard (15 min):** Adds auto-format/lint hooks,
> `.mcp.json` for external services.
>
> **Tier 3 — Full (30 min):** Adds specialized agents, ADR structure,
> CODEMAPS for codebase navigation.
>
> Which tier? (Upgrade any time with `/shipwithai-starter:review`)

→ Wait for tier selection before asking anything else.

### Step 3 — Interview Flow

#### Part 0: Stack Confirmation *(all tiers)*

"I detected: [list detected stack + tools]. Anything wrong?"

If nothing detected → ask:
- Primary language?
- Primary framework?
- Build tool?
- Test framework?
- Package manager?

#### Part 1: Project Identity *(all tiers)*

Ask once, grouped:
- Project name + type (web app / API / CLI / lib / monorepo)?
- Team size?
- Stage (greenfield / active / maintenance / legacy)?

#### Part 2: Architecture *(all tiers)*

- Architecture style (monolith / microservices / modular monolith / event-driven)?
- Key layers and their corresponding directories?
- Entry points?
- External dependencies (DB, queue, cache, external APIs)?

"Paste `tree -L 3` or I'll scan the codebase myself."
→ Read output, extract key directories automatically.

Gotchas (highest value — do not skip):
- Which directories/files must NOT be edited manually? (generated code)
- Build order dependencies? (codegen → compile)
- What does test isolation require? (Docker? env vars? seeds?)
- Which areas of code need extra care? (auth, payments, migrations)

#### Part 3: Conventions *(all tiers)*

If eslint/prettier/black/gofmt detected → confirm, do not re-ask.
If not detected → ask:
- Code style tool?
- Branch strategy (trunk-based / gitflow)?
- Commit format (conventional / custom / none)?
- Test coverage target?

#### Part 4: Permissions *(all tiers)*

Load preset from `./setup-permissions/settings-presets.json` by detected stack.

"Based on your stack, I suggest this permission profile:
[show preset with explanation per rule]
Want to customize?"

Also ask:
- Which tools should Claude NOT use? → disallowedTools
- Which paths are read-only? → read-only paths

#### Part 5: Hooks *(Tier 2+)*

Detect available tools → suggest from `./setup-hooks/hooks-catalog.json`:

```
ESLint detected   → "Enable eslint --fix hook after Claude edits .ts/.js?"
Prettier detected → "Enable prettier --write hook after Edit tool?"
pytest detected   → "Enable pytest hook after Claude edits *_test.py?"
Jest detected     → "Enable jest hook after Claude edits *.test.*?"
gofmt detected    → "Enable gofmt -w hook after Edit tool on .go files?"
```

One hook at a time. Show preview before confirming.

#### Part 6: MCP Servers *(Tier 2+)*

"Which external services does this project interact with?"
→ Show list from `./setup-mcp/mcp-registry.json`.

For each selected service:
- Show config preview.
- Attempt test connection → report ✓ tested / ⚪ configured-not-verified / ✗ not-found.
- Never report ✓ without actually testing.
- Confirm before adding.

#### Part 7: Agents *(Tier 3+)*

Load `./setup-agents/agents-catalog.json` → suggest agents by project type/team size.

Always include `drift-monitor` for Tier 3.
Show preview per agent → confirm.

#### Part 8: SSOT *(Tier 3+)*

- "Set up ADR structure?" → Yes: create `docs/adr/` + `ADR-0001-initial-architecture.md`.
- "Create CODEMAPS?" → Yes: create `docs/CODEMAPS/` structure guide.

### Step 4 — Preview & Confirm

After the interview, generate a preview of all files to be written:

```
Here is what I will create/update:
┌──────────────────────────────────────┬──────────┬───────┐
│ File                                 │ Action   │ Tier  │
├──────────────────────────────────────┼──────────┼───────┤
│ CLAUDE.md                            │ CREATE   │ 1     │
│ docs/architecture.md                 │ CREATE   │ 1     │
│ .claude/settings.json (permissions)  │ CREATE   │ 1     │
│ .claude/settings.json (hooks)        │ UPDATE   │ 2     │
│ .mcp.json                            │ CREATE   │ 2     │
│ .claude/agents/drift-monitor.md      │ CREATE   │ 3     │
└──────────────────────────────────────┴──────────┴───────┘
Confirm?
```

For existing files: "File [X] already exists. Overwrite / Merge / Skip?"

### Step 4.5 — Write Context File

Immediately after the user confirms the preview, before invoking any pillar skill,
write `.claude/starter-context.json` with all interview answers:

```json
{
  "version": "1.0",
  "tier": "essential|standard|full",
  "stack": {
    "language": "...",
    "framework": "...",
    "build_tool": "...",
    "test_framework": "...",
    "package_manager": "...",
    "detected_tools": ["eslint", "prettier", "..."]
  },
  "project": {
    "name": "...",
    "type": "web-app|api|cli|lib|monorepo",
    "team_size": 3,
    "stage": "greenfield|active|maintenance|legacy"
  },
  "architecture": {
    "style": "monolith|microservices|modular-monolith|event-driven",
    "key_layers": [{ "name": "API", "dir": "src/routes/", "responsibility": "..." }],
    "entry_points": ["src/index.ts"],
    "external_deps": [{ "service": "PostgreSQL", "purpose": "...", "env_var": "DATABASE_URL" }],
    "gotchas": ["src/generated/ — do not edit manually"],
    "build_order": ["codegen before tsc"],
    "test_isolation": ["requires Docker Compose"],
    "sensitive_areas": ["auth/", "payments/"]
  },
  "conventions": {
    "formatter": "prettier",
    "branch_strategy": "trunk-based",
    "commit_format": "conventional",
    "coverage_target": "80%"
  },
  "permissions": {
    "preset": "nodejs",
    "disallowed_tools": [],
    "readonly_paths": []
  },
  "hooks_selected": ["prettier", "eslint"],
  "mcp_selected": ["github", "linear"],
  "agents_selected": ["drift-monitor"],
  "ssot": {
    "adr": true,
    "codemaps": false
  },
  "collected_at": "ISO8601 timestamp"
}
```

This file is the source of truth for all pillar skills — both when called from init and standalone.
Commit this file alongside `.claude/` so the team shares context.

### Step 5 — Orchestrate Pillar Skills

User approves → invoke each pillar skill by tier, reading context from `.claude/starter-context.json`:

```
Tier 1: /shipwithai-starter:setup-memory       (reads: project, stack, architecture, conventions)
         /shipwithai-starter:setup-permissions  (reads: stack, permissions)
         /shipwithai-starter:setup-ssot --architecture-only  (reads: architecture)

Tier 2: /shipwithai-starter:setup-hooks        (reads: stack.detected_tools, hooks_selected)
         /shipwithai-starter:setup-mcp          (reads: mcp_selected)

Tier 3: /shipwithai-starter:setup-agents       (reads: agents_selected, project)
         /shipwithai-starter:setup-ssot --adr --codemaps  (reads: ssot)
```

### Step 6 — After-Write

1. Summary table: files created / updated / skipped.
2. "Commit `.claude/` and `CLAUDE.md` to the repo so the team shares the harness."
3. Upgrade note: "Currently at Tier [N]. Upgrade with `/shipwithai-starter:review`."

## Failure Modes

```
Don't guess stack if ambiguous → ask
Don't write hooks for tools not detected in the project
Don't add MCP server without actually verifying the connection
Don't overwrite existing files without asking
Don't skip the gotchas section — it's the highest-value part
Don't proceed if the user has not confirmed the preview
```
