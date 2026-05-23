---
name: setup-mcp
description: >
  Configure .mcp.json with MCP servers for external services your project uses.
  Called by cold-start-interview or standalone to configure the MCP pillar.
  Trigger phrases: "setup mcp", "configure mcp servers", "connect to [service]".
argument-hint: "[service-name]"
---

# /setup-mcp

Configures `.mcp.json` với MCP servers cho external services.

## Mode Detection

```
Có context từ cold-start-interview?
  → Có: dùng service selections đã có
  → Không (standalone): hỏi "Project interact với services nào?"
```

## Service Lookup

Load `references/mcp-registry.json` → show danh sách phổ biến:

```
GitHub     → code search, PR management, issues
Linear     → issue tracking, sprint planning
Slack      → notifications, search messages
Sentry     → error tracking, performance data
PostgreSQL → direct DB queries, schema inspection
Redis      → cache inspection
Google Drive → search and read documents
```

Với mỗi service chọn:
1. Lookup config trong registry.
2. Show config preview:
   ```json
   {
     "mcpServers": {
       "github": {
         "url": "https://api.githubcopilot.com/mcp/",
         "description": "Search code, manage PRs and issues"
       }
     }
   }
   ```
3. Attempt test connection:
   - ✓ tested — MCP tool call thực sự succeeded
   - ⚪ configured, not verified — không test được từ đây
   - ✗ not found — hướng dẫn cách connect
4. Confirm trước khi add.

**Không bao giờ báo ✓ nếu chỉ dựa trên .mcp.json declarations.**

## Write Rules

- Check `.mcp.json` exists → append / overwrite / skip?
- Sau khi write: update "Installed MCP servers" table trong `CLAUDE.md`
- Nếu service không có trong registry: "Paste MCP URL nếu bạn có, hoặc skip — add sau với `/shipwithai-starter:add-mcp`"
