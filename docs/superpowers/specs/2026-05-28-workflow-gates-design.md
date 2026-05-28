# Thiết kế: AI Workflow Gates trong `shipwithai-starter`

**Ngày:** 2026-05-28
**Trạng thái:** Đã duyệt
**Tác giả:** Claude Code (phiên brainstorming)

---

## Tổng quan

Thêm phần "Quy trình phát triển" vào CLAUDE.md được tạo bởi `shipwithai-starter`, kèm theo cơ chế **phỏng vấn tăng dần** để plugin tự phát hiện khi có câu hỏi mới và chỉ hỏi bổ sung mà không chạy lại toàn bộ phỏng vấn.

**Vấn đề 1:** Plugin hiện tại tạo ra context dự án tốt nhưng không có hướng dẫn quy trình AI — Claude không biết nên theo quy trình nào khi làm task (cần lập kế hoạch trước không? TDD? review code?).

**Vấn đề 2:** Khi plugin cập nhật có tính năng mới (câu hỏi mới), các dự án hiện tại không có cơ chế nhận cập nhật mà không bị hỏi lại toàn bộ.

**Giải pháp:**
- Workflow gates: thêm 1 câu hỏi checkbox vào Phần 3, tạo section "Quy trình phát triển" trong CLAUDE.md
- Phiên bản schema: `starter-context.json` theo dõi version, `init --update` chỉ hỏi các trường còn thiếu, `review` phát hiện schema lỗi thời

**Giá trị cốt lõi:** Plugin cập nhật → `review` tự phát hiện → người dùng chạy `init --update` → chỉ trả lời câu hỏi mới → CLAUDE.md được cập nhật.

---

## Kiến trúc

### Các file thay đổi

```
plugins/starter/
├── skills/
│   ├── init/SKILL.md           ← +1 câu hỏi cuối Phần 3 + chế độ --update mới
│   ├── setup-memory/SKILL.md   ← +1 template section + logic tạo nội dung
│   └── review/SKILL.md         ← +1 kiểm tra phiên bản schema + 1 kiểm tra component + 1 quy tắc drift
```

Không có file mới. Không thay đổi mô hình tier.

### Luồng dữ liệu — init thông thường

```
init (phỏng vấn Phần 3)
  → người dùng chọn workflow gates
  → lưu vào: starter-context.json → conventions.workflow_gates[] + schema_version: "1.1"

setup-memory (tạo CLAUDE.md)
  → đọc conventions.workflow_gates[]
  → tạo section "Quy trình phát triển" với hướng dẫn tương ứng
```

### Luồng dữ liệu — khi plugin được cập nhật

```
Plugin cập nhật: schema_version tăng 1.0 → 1.1 (thêm workflow_gates)

review (dự án hiện tại)
  → đọc starter-context.json → schema_version: "1.0"
  → so sánh với schema plugin hiện tại: "1.1"
  → cảnh báo: "Plugin có câu hỏi mới (v1.1). Chạy /shipwithai-starter:init --update"

init --update (phỏng vấn tăng dần)
  → đọc starter-context.json
  → duyệt qua tất cả câu hỏi phỏng vấn
  → bỏ qua câu đã có câu trả lời
  → chỉ hỏi những trường null/vắng mặt: workflow_gates
  → cập nhật starter-context.json + schema_version
  → gọi setup-memory (chế độ merge)
```

### Thay đổi schema starter-context.json

Tăng version và thêm 1 trường:

```json
{
  "version": "1.1",
  "tier": "full",
  "stack": { "...": "không đổi" },
  "conventions": {
    "formatter": "prettier",
    "branch_strategy": "gitflow",
    "commit_format": "conventional",
    "coverage_target": "80%",
    "workflow_gates": ["plan-before-code", "tdd", "code-review"]
  }
}
```

Giá trị `workflow_gates`: `"plan-before-code"` | `"tdd"` | `"code-review"` | `"security-review"` | `"none"`

`"none"` là loại trừ lẫn nhau — nếu được chọn, ghi đè tất cả gates khác. Giao diện phỏng vấn đảm bảo: khi chọn "None", bỏ chọn các lựa chọn còn lại.

Tương thích ngược: `workflow_gates` vắng mặt → không tạo section, `review` cảnh báo schema lỗi thời.

---

## Phần 1: Thay đổi `init/SKILL.md`

### 1a — Câu hỏi mới trong Phần 3 (Quy ước)

**Vị trí:** Cuối Phần 3, sau câu hỏi về định dạng commit (tất cả tiers).

```
"Claude nên tuân theo những workflow gates nào khi làm task?"
(Chọn tất cả các mục phù hợp — chọn None sẽ bỏ chọn các mục khác)

→ [ ] Lập kế hoạch/thiết kế trước khi viết code
      Claude phải tạo kế hoạch hoặc tài liệu thiết kế trước khi viết code cho task > 30 phút
→ [ ] TDD — viết test trước
      Claude viết test thất bại trước khi triển khai
→ [ ] Review code
      Claude chạy code-reviewer agent sau mỗi thay đổi quan trọng
→ [ ] Review bảo mật cho các khu vực nhạy cảm
      Claude chạy security-reviewer trước khi commit vào các khu vực nhạy cảm
→ [ ] Không — để Claude tự quyết định
```

### 1b — Chế độ `--update` mới

Kích hoạt: `init --update` hoặc khi `review` gợi ý.

```
Bước 1: Đọc .claude/starter-context.json
        → Không tìm thấy: "Không có context. Chạy /shipwithai-starter:init để thiết lập đầy đủ."
        → Tìm thấy: tiếp tục

Bước 2: So sánh các trường hiện có với schema chuẩn (v1.1)
        → Tìm tất cả trường null hoặc vắng mặt

Bước 3: Với mỗi trường còn thiếu:
        → Hỏi câu hỏi tương ứng (cùng nội dung như phỏng vấn đầy đủ)
        → Bỏ qua tất cả trường đã có câu trả lời

Bước 4: Cập nhật starter-context.json
        → Merge câu trả lời mới vào
        → Đặt version thành "1.1"

Bước 5: Gọi setup-memory (chế độ merge)
        → Chỉ thêm/cập nhật các section có dữ liệu mới
        → Các section hiện có được giữ nguyên
```

Các trường schema theo version:
```
v1.0: stack, project, architecture, conventions (formatter/branch_strategy/commit_format/coverage_target), permissions, hooks_selected, mcp_selected, agents_selected, ssot
v1.1: + conventions.workflow_gates
```

**Chế độ độc lập** (`setup-memory` gọi trực tiếp, không có file context):
Hỏi câu hỏi workflow gates. Người dùng bỏ qua → không tạo section, không để placeholder.

---

## Phần 2: Thay đổi `setup-memory/SKILL.md`

### Template CLAUDE.md — section mới

Thêm sau section "Quy ước chính":

```markdown
## Quy trình phát triển

**Khi làm bất kỳ task nào, Claude phải tuân theo các gates sau:**

- [tạo dòng tương ứng với từng gate được chọn]
```

### Mapping gate → hướng dẫn

| Gate | Hướng dẫn |
|---|---|
| `plan-before-code` | **Lập kế hoạch trước:** Với task > 30 phút, tạo kế hoạch và được duyệt trước khi viết code. |
| `tdd` | **TDD:** Viết test thất bại trước. Không bao giờ viết code triển khai mà không có test tương ứng. |
| `code-review` | **Review code:** Chạy code-reviewer agent sau mỗi thay đổi quan trọng. Xử lý tất cả phát hiện mức CRITICAL và HIGH. |
| `security-review` (có sensitive_areas) | **Review bảo mật:** Trước khi commit vào `src/auth/, src/payments/` (từ `architecture.sensitive_areas`), chạy security-reviewer agent. |
| `security-review` (sensitive_areas rỗng) | **Review bảo mật:** Trước khi commit vào các khu vực nhạy cảm (auth, payments, migrations), chạy security-reviewer agent. |
| `none` / rỗng | *(bỏ qua toàn bộ section)* |

### Ví dụ kết quả (chọn plan-before-code + tdd + code-review)

```markdown
## Quy trình phát triển

**Khi làm bất kỳ task nào, Claude phải tuân theo các gates sau:**

- **Lập kế hoạch trước:** Với task > 30 phút, tạo kế hoạch và được duyệt trước khi viết code.
- **TDD:** Viết test thất bại trước. Không bao giờ viết code triển khai mà không có test tương ứng.
- **Review code:** Chạy code-reviewer agent sau mỗi thay đổi quan trọng. Xử lý tất cả phát hiện mức CRITICAL và HIGH.
```

### Hành vi merge

CLAUDE.md đã có section "Quy trình phát triển":
→ Hỏi Ghi đè / Giữ nguyên / Bỏ qua — nhất quán với hành vi các section khác.

---

## Phần 3: Thay đổi `review/SKILL.md`

### Bước 1 — Chấm điểm Components (thêm 2 dòng)

```
Phiên bản schema starter-context.json  → hiện tại (1.1) ✅ / lỗi thời ⚠️ / thiếu ❌
Section quy trình trong CLAUDE.md      → có ✅ / đã từ chối ✅ / thiếu ⚠️
```

### Logic kiểm tra phiên bản schema

```
Đọc .claude/starter-context.json:
  → không tìm thấy                → ❌ chưa khởi tạo
  → version == "1.1"              → ✅ cập nhật
  → version < "1.1" hoặc vắng mặt → ⚠️ lỗi thời (ghi rõ version hiện tại vs kỳ vọng)
```

### Kiểm tra section quy trình (phát hiện từ chối thông minh)

```
starter-context.json tồn tại:
  → workflow_gates vắng mặt             → ⚠️ schema lỗi thời — chạy init --update
  → workflow_gates == ["none"] hoặc []  → ✅ đã từ chối có chủ ý
  → workflow_gates có giá trị           → kiểm tra CLAUDE.md có section "Quy trình phát triển"
      có                                → ✅
      thiếu                             → ⚠️ context đã set nhưng CLAUDE.md chưa cập nhật

starter-context.json không tồn tại:
  → kiểm tra CLAUDE.md có section "## Quy trình phát triển" không
      có                                → ✅
      thiếu                             → ⚠️ không tìm thấy section quy trình
```

### Bước 2 — Phát hiện Drift (thêm 1 quy tắc)

```
workflow_gates  ←→  architecture.sensitive_areas
  sensitive_areas có trong starter-context.json
  VÀ "security-review" không có trong workflow_gates?
  → cảnh báo ⚠️ "Phát hiện khu vực nhạy cảm nhưng chưa cấu hình security-review gate"
```

### Bảng báo cáo sức khỏe (thêm 2 dòng)

```
| Phiên bản schema          | ⚠️ | v1.0 → v1.1 có sẵn (workflow_gates)              |
| Quy trình CLAUDE.md       | ⚠️ | Schema lỗi thời — chạy init --update             |
```

### Hành động gợi ý

Schema lỗi thời:
> "Plugin có câu hỏi mới (v1.1). Chạy `/shipwithai-starter:init --update` để trả lời các câu hỏi mới — các câu trả lời hiện có được giữ nguyên."

Section quy trình thiếu (schema cập nhật):
> "Section quy trình phát triển thiếu trong CLAUDE.md. Chạy `/shipwithai-starter:init --update` để thêm vào."

---

## Tier

Hướng dẫn quy trình phát triển thuộc **Tier 1 (Cơ bản)** — tất cả tiers đều nhận.

Phiên bản schema áp dụng cho toàn bộ plugin, không phụ thuộc tier.

---

## Hướng mở rộng trong tương lai

Mỗi lần plugin thêm tính năng mới:
1. Thêm câu hỏi vào phỏng vấn (`init/SKILL.md`)
2. Thêm trường vào schema `starter-context.json`
3. Tăng `schema_version`
4. `review` tự phát hiện các dự án hiện tại bị lỗi thời
5. `init --update` chỉ hỏi trường mới — không làm phiền người dùng với câu hỏi cũ

---

## Ngoài phạm vi

- Lệnh `add-workflow` riêng (thay thế bằng `init --update`)
- Skill `setup-workflow` riêng (quá phức tạp so với giá trị đạt được)
- Suy luận tự động từ team_size/stage (không đáng tin, thiếu minh bạch)
- Cơ chế bắt buộc ngoài hướng dẫn trong CLAUDE.md
