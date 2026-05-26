---
name: add-mcp
description: >
  Add a new MCP server to .mcp.json. Quick operation, no full interview needed.
  Trigger phrases: "add MCP", "connect to [service]", "configure [service] MCP".
argument-hint: "[service-name or MCP URL]"
---

# /add-mcp

Add a single MCP server to `.mcp.json`. Stateless — no cold-start context required.

## Steps

1. If user provides a service name → look up in `skills/setup-mcp/mcp-registry.json`.
   - Found: show preset config, confirm.
   - Not found: "Paste the MCP URL and a short description."

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

6. Update the "MCP servers" section in `CLAUDE.md` if the file exists.
