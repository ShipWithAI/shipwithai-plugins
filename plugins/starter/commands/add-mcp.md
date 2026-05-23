---
name: add-mcp
description: >
  Add a new MCP server to .mcp.json. Quick operation, no full interview needed.
  Trigger phrases: "add MCP", "connect to [service]", "configure [service] MCP".
argument-hint: "[service-name or MCP URL]"
---

# /add-mcp

Thêm một MCP server vào `.mcp.json`. Stateless, không cần context từ cold-start.

## Steps

1. Nếu user cung cấp service name → lookup trong `references/mcp-registry.json`.
   - Tìm thấy: show preset config, confirm.
   - Không tìm thấy: "Paste MCP URL và description."

2. Show config preview trước khi write:
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

3. Attempt test connection → report ✓ / ⚪ / ✗.
   Không báo ✓ nếu chưa test thực sự.

4. Confirm → append vào `.mcp.json`.

5. Update "Installed MCP servers" table trong `CLAUDE.md` nếu file tồn tại.

6. "Test connection bằng cách invoke một tool từ server này."
