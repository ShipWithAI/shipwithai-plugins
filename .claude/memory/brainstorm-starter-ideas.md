# Brainstorm: shipwithai-starter next features (2026-05-29)

**Key constraint:** Plugin phải serve cả greenfield (project trống) lẫn existing projects. MCP auto-discovery và CI/CD gate không fit greenfield vì không có gì để scan.

## Top candidates

**1. Stack-specific deep presets**
Pre-filled bundles per stack (Next.js 14, Spring Boot, Django REST). User chọn stack → CLAUDE.md, hooks, MCP, agents pre-configured. Đặc biệt quan trọng cho greenfield — user đang *chọn* stack, chưa có gì.

**2. Progressive disclosure interview**
Interview adapt theo context: solo dev → bỏ team questions, greenfield → bỏ legacy gotchas, hỏi nhiều hơn về định hướng thay vì gotchas.

**3. Team sync (`harness.lock`)**
`init --export` → `harness.lock`. Teammate mới chạy `init --import` → identical setup.

**4. Architecture advisor mode (greenfield-specific)**
Detect `stage: greenfield` + project trống → chuyển từ interview sang consultation: hỏi goals/scale → recommend stack + architecture → gen harness.

**5. CI/CD harness health gate**
GitHub Actions chạy `review --ci` trên mỗi PR. Chỉ relevant sau khi project đã có CI.

## Open question chưa resolve

**Scope của plugin:** Có nên scaffold initial project structure (folders, config files) cho greenfield không, hay giữ scope thuần "configure Claude harness"? Quyết định này ảnh hưởng lớn đến direction của architecture advisor mode.
