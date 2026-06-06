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
starter-context.json    → version current (1.1) ✅ / outdated ⚠️ / missing ❌
CLAUDE.md               → populated ✅ / has-placeholder ⚠️ / missing ❌
CLAUDE.md workflow      → present ✅ / opted-out ✅ / missing ⚠️
.claude/settings.json   → configured ✅ / exists-empty ⚠️ / missing ❌
settings.json hooks     → hooks configured ✅ / empty ⚠️ / missing ❌
.mcp.json               → servers configured ✅ / exists-empty ⚠️ / missing ❌
.claude/agents/         → agents present ✅ / missing ❌
docs/architecture.md    → exists ✅ / missing ❌
docs/adr/               → ADRs present ✅ / index-only ⚠️ / missing ❌
.claude/memory/         → MEMORY.md with content ✅ / exists-empty ⚠️ / missing ❌
.claude/hooks/observe.py  → present ✅ / missing (Tier 3 opt-in) ❌
.claude/logs/ in .gitignore → in gitignore ✅ / tracked by git ⚠️ / not applicable ✅
```

**Schema version check:**
```
Read .claude/starter-context.json:
  → not found                    → ❌ not initialized
  → version == "1.2"             → ✅ current
  → version == "1.1"             → ⚠️ outdated — run init --update (adds observability field)
  → version < "1.1" or absent    → ⚠️ outdated — run init --update
```

**Workflow section check (smart opt-out):**
```
starter-context.json exists:
  → workflow_gates absent                → ⚠️ schema outdated — run init --update
  → workflow_gates == ["none"] or []     → ✅ explicitly opted out
  → workflow_gates has values            → check CLAUDE.md has "Development workflow" section
      present                            → ✅
      missing                            → ⚠️ context set but CLAUDE.md not updated

starter-context.json not found:
  → check CLAUDE.md for "## Development workflow" section
      present                            → ✅
      missing                            → ⚠️ no workflow section found
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

workflow_gates  ←→  architecture.sensitive_areas
  sensitive_areas present in starter-context.json
  AND "security-review" not in workflow_gates?
  → flag ⚠️ "Sensitive areas detected but no security-review gate configured"
```

## Step 2b — Static Analysis

Run for ALL tiers. No runtime logs required.

### Hook binary check

For each hook command in `.claude/settings.json`:
- Extract effective binary: `npx <pkg>` → check `<pkg>`; `python3 <script>` → check `python3`; otherwise check first token
- Binary in `devDependencies` / `dependencies` (package.json) OR `which <binary>` returns a path → ✅
- Neither found → flag ⚠️ `Hook [hook-id] references [binary] but it's not installed`

### Hook pattern match check

For hook commands that filter by file extension (e.g. `case "$CLAUDE_TOOL_INPUT_PATH" in *.ts|*.tsx`):
- Extract file extensions from the command (patterns after `*.`)
- `find . -name "*.<ext>" -not -path "*/node_modules/*"` returns results → ✅
- No matching files in project → flag ⚠️ `Hook [hook-id] matches [pattern] but no matching files found`

### MCP usage vs codebase

Compare `.mcp.json` servers vs actual imports/usage in source files. Check both directions:

| MCP server | Detect usage by looking for |
|------------|----------------------------|
| github     | `@octokit/*`, `octokit` (JS imports), `gh` CLI calls |
| linear     | `@linear/sdk` import |
| slack      | `@slack/bolt`, `@slack/web-api` import |
| sentry     | `@sentry/*` import, `sentry-sdk` (Python) |
| postgres   | `pg`, `postgres` (JS), `psycopg2`, `sqlalchemy` (Python) |
| notion     | `@notionhq/client` import |
| jira       | `jira-client` (JS), `jira` (Python) |
| supabase   | `@supabase/supabase-js` import, `supabase` CLI calls |
| stripe     | `stripe` (JS/Python), `@stripe/*` imports |
| datadog    | `dd-trace`, `datadog-api-client`, `@datadog/*` imports |
| vercel     | `vercel` CLI calls, `@vercel/*` imports |
| cloudflare | `wrangler` CLI calls, `@cloudflare/*` imports |
| neon       | `@neondatabase/serverless` import |

**Configured but no usage found:**
→ flag ⚠️ `MCP [name] configured but no related usage found — consider removing`

**Usage found but no MCP configured:**
→ flag ⚠️ `Code imports [package] but no [service] MCP configured — consider adding`

## Step 3 — Health Report

```
## Harness Health — [project name]
Current tier: [Essential / Standard / Full]
Checked: YYYY-MM-DD

| Component            | Status | Issue                                      |
|----------------------|--------|--------------------------------------------|
| Schema version       | ⚠️     | v1.0 → v1.1 available (workflow_gates)     |
| CLAUDE.md            | ✅     | —                                          |
| CLAUDE.md workflow   | ⚠️     | Schema outdated — run init --update        |
| settings.json        | ✅     | —                                          |
| Hooks                | ⚠️     | prettier hook but prettier not in project  |
| .mcp.json            | ❌     | Redis used in code, no MCP server          |
| docs/architecture.md | ⚠️     | Not updated in 45 days                     |
| ADRs                 | ✅     | 3 ADRs present                             |
| .claude/memory/      | ❌     | Not set up (Tier 3 item)                   |
| Observability        | ❌     | observe.py not installed (Tier 3 opt-in)   |
| Hook binaries        | ⚠️     | jest-on-stop: jest not in devDeps or PATH  |
| Hook patterns        | ✅     | —                                          |
| MCP alignment        | ⚠️     | GitHub MCP configured, no octokit imports  |

Drift detected: [list of flagged items, or "None"]
Static analysis: [list of flagged items, or "None"]
```

## Step 4 — Suggest Actions

Prioritize by severity: ❌ first, then ⚠️. Suggest one action at a time:

> "Want to fix [highest priority issue] now?"

If user accepts: invoke the relevant skill directly:
- Schema outdated → `/shipwithai-starter:init --update` ("Plugin has new questions (v1.1). Run init --update to answer only new questions — existing answers are preserved.")
- Workflow missing (schema current) → `/shipwithai-starter:init --update`
- Hooks issue → `/shipwithai-starter:setup-hooks`
- MCP issue → `/shipwithai-starter:setup-mcp`
- Agents issue → `/shipwithai-starter:setup-agents`
- SSOT/docs issue → `/shipwithai-starter:update-ssot`
- Observability missing (Tier 3) → `/shipwithai-starter:setup-observability`
- Logs tracked by git → warn: run `git rm -r --cached .claude/logs/` and add to .gitignore

Tier upgrade path:
- Tier 1 → list Standard tier items not yet configured
- Tier 2 → list Full tier items not yet configured
- To upgrade: run `/shipwithai-starter:init`

If `.claude/logs/` exists and contains log files spanning ≥7 calendar days:
> For runtime-based suggestions (usage patterns, hook coverage): `/shipwithai-starter:optimize-harness`
