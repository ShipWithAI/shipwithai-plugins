---
name: add-mcp
description: >
  Add a new MCP server to .mcp.json. Quick operation, no full interview needed.
  Trigger phrases: "add MCP", "connect to [service]", "configure [service] MCP".
argument-hint: "[service-name or MCP URL]"
---

# /add-mcp

Add a single MCP server to `.mcp.json`. Stateless — no init context required.

## Steps

1. If user provides a service name → look up in the plugin's `mcp-registry.json`
   (located at `skills/setup-mcp/mcp-registry.json` in the plugin directory).
   - Found: show preset config, confirm.
   - Not found in registry: respond with:
     > "Server [name] not found in registry. Want to add it as a custom server?"
     If yes: ask for type (`http`/`stdio`), URL or command+args, auth note, description.
     Generate id as slug (lowercase, spaces→hyphens). Write to `.mcp.json` as a custom entry.

2. Show config preview before writing:
   ```json
   {
     "mcpServers": {
       "[name]": {
         "url": "...",
         "description": "..."
       }
     }
   }
   ```

3. If `authRequired` is true in the registry entry: surface auth requirement before writing.
   Ask: "This server requires [authNote]. Do you have credentials ready?"

4. Attempt test connection → report ✓ tested / ⚪ configured-not-verified / ✗ not-found.
   Never report ✓ without actually testing. MCP servers load at next Claude Code startup.

5. Confirm → append to `.mcp.json`.
   Check for duplicate `id` before writing — skip if already present.

6. Update `**Last updated:**` date in the Harness config section of `CLAUDE.md` if the file exists.
