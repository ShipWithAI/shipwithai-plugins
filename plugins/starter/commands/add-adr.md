---
name: add-adr
description: >
  Create a new Architecture Decision Record in docs/adr/. Quick operation.
  Trigger phrases: "create ADR", "document decision", "record architecture choice",
  "add ADR", "document this decision".
argument-hint: "[title of the decision]"
---

# /add-adr

Tạo một ADR mới trong `docs/adr/`. Stateless.

## Steps

1. Check `docs/adr/` tồn tại không.
   - Không: "Thư mục docs/adr/ chưa có. Tạo structure không?"
     → Có: tạo `docs/adr/README.md` + ADR này.

2. Count existing ADRs → next number = ADR-[XXXX].

3. Hỏi nếu không có trong args:
   - Title của decision?
   - Context: tại sao cần quyết định này?
   - Options đã consider? (list từng option với pros/cons)
   - Decision: chọn gì và tại sao?
   - Consequences: trade-offs, risks, next steps?

4. Draft ADR từ `references/adr-template.md` → show preview → confirm.

5. Write `docs/adr/ADR-[XXXX]-[kebab-slug].md`.

6. Update ADR table trong `CLAUDE.md` nếu tồn tại:
   ```
   | ADR-[XXXX] | [title] | Accepted |
   ```
