---
name: setup-mcp
description: >
  Configure .mcp.json with MCP servers for external services your project uses.
  Called by init or standalone to configure the MCP pillar.
  Trigger phrases: "setup mcp", "configure mcp servers", "connect to [service]".
argument-hint: "[service-name]"
---

# /setup-mcp

Configures `.mcp.json` with MCP servers for external services.

## Mode Detection

```
Read .claude/starter-context.json if it exists
  → Exists: use field mcp_selected — skip asking, go straight to lookup + write
  → Does not exist (standalone): ask "Which external services does your project use?"
```

## Argument Handling

If a service name is passed directly (e.g. `/setup-mcp github`): skip the service selection
prompt and go straight to lookup for that service.

## Service Lookup

Load `mcp-registry.json` and show the available services:

```
GitHub       → code search, PR management, issues
Linear       → issue tracking, sprint planning
Slack        → search messages, read channels
Sentry       → error tracking, performance data
PostgreSQL   → direct DB queries, schema inspection
Google Drive → search and read documents
Notion       → read and search pages and databases
Jira         → issue tracking, sprint management
```

For each selected service:

1. Look up config in the registry.
2. If `authRequired` is true: show auth requirement before writing:
   > "This server requires [authNote]. Do you have credentials ready?"
   If no: offer to skip and add later.
3. If service type is `stdio`: ask for required runtime values (e.g. connection string)
   before writing — never write placeholder values literally.
4. Show config preview (see Output Format below).
5. Attempt test connection after writing (see Verification below).
6. Confirm before writing.

After listing registry options, always show:
```
[N+1] Custom — add your own MCP server
```

If user selects Custom, run the Custom Server Flow below instead.

If the requested service is not in the registry: offer the Custom Server Flow.

## Custom Server Flow

Ask in order:

1. **Name** — display name (e.g. "My Internal API")
2. **Type** — `http` (remote URL) or `stdio` (local command)
3. If `http`: **URL endpoint** (e.g. `https://api.example.com/mcp`)
4. If `stdio`: **Command** (e.g. `npx`) + **Args** as a JSON array (e.g. `["my-mcp-server"]`)
5. **Auth required?** (yes/no) — if yes, ask for a one-line auth note
6. **Description** — one line describing what this server does

Generate `id` as a slug: lowercase, spaces → hyphens, strip special chars (e.g. "My API" → `my-api`).

Write to `.mcp.json` using the same format as registry servers:
```json
"my-api": {
  "url": "https://api.example.com/mcp",
  "type": "http",
  "description": "User-provided description"
}
```
Update `starter-context.json` → append `"custom-<id>"` to `mcp_selected`.

## Output Format

If `.mcp.json` does not exist: create it with `{ "mcpServers": {} }`.

**HTTP server:**
```json
{
  "mcpServers": {
    "github": {
      "url": "https://api.githubcopilot.com/mcp/",
      "type": "http",
      "description": "Search code, manage PRs and issues"
    }
  }
}
```

**stdio server (e.g. PostgreSQL — ask user for connection string first):**
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres", "postgresql://user:pass@host/db"],
      "description": "Direct database queries and schema inspection"
    }
  }
}
```

## Write Rules

- If `.mcp.json` does not exist: create it with `{ "mcpServers": {} }`
- If `.mcp.json` exists: read it, check if server `id` already in `mcpServers` — skip if duplicate
- Never overwrite an existing server entry without asking the user first
- Never write placeholder values (e.g. `<connection-string>`) — always resolve real values first

## Verification

MCP servers load at Claude Code startup. Writing `.mcp.json` takes effect in the next session.

After writing, report status:
- **✓ tested** — a tool call to this MCP server actually succeeded in the current session
- **⚪ configured, not verified** — config written but connection not testable until next session
- **✗ not found** — server unreachable; show auth/setup guidance

**Never report ✓ based on `.mcp.json` declarations alone.**

## Post-Write

If `.claude/starter-context.json` exists:
→ Update the `mcp_selected` field with the list of server `id` values that were written
