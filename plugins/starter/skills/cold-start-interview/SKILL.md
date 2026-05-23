---
name: cold-start-interview
description: >
  Set up the Claude Code harness for this project. Configures CLAUDE.md, permissions,
  hooks, MCP servers, agents, and SSOT docs based on your stack and chosen tier.
  Run on first setup or when CLAUDE.md is missing or has [PLACEHOLDER] markers.
  Trigger phrases: "set up harness", "configure claude", "onboard project",
  "bootstrap claude", "let's get started", "setup claude code".
argument-hint: "[--redo] [--tier essential|standard|full]"
---

# /cold-start-interview

Entry point bắt buộc của plugin. Không chạy skill nào khác trước khi cold-start hoàn thành.

## Instructions

### Step 1 — State Detection

Trước khi hỏi bất cứ điều gì, đọc project state:

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
.eslintrc* / eslint.config.*  → ESLint
prettier.config* / .prettierrc → Prettier
jest.config*                  → Jest
pytest.ini / conftest.py      → pytest
Makefile                      → make
docker-compose.yml            → Docker Compose
```

Nếu CLAUDE.md đã populated và không có `--redo`: "Harness đã được setup. Muốn redo không? (dùng --redo)"

### Step 2 — Fork-First Preamble

Hiện ngay sau state detection, trước khi hỏi bất cứ điều gì:

> **shipwithai-starter** thiết lập Claude Code harness chuẩn cho project của bạn.
>
> **Tier 1 — Essential (5 min):** CLAUDE.md với tech stack + conventions + architecture,
> `.claude/settings.json` với permissions phù hợp stack. Đủ dùng ngay.
>
> **Tier 2 — Standard (15 min):** Thêm hooks tự động cho formatter/linter,
> `.mcp.json` cho external services.
>
> **Tier 3 — Full (30 min):** Thêm agents chuyên biệt, architecture docs,
> ADR structure, CODEMAPS cho codebase navigation.
>
> Chọn tier? (Upgrade bất cứ lúc nào với `/shipwithai-starter:review`)

→ Wait for tier selection trước khi hỏi gì khác.

### Step 3 — Interview Flow

#### Part 0: Stack Confirmation *(tất cả tiers)*

"Tôi detect được: [list detected stack + tools]. Có gì sai không?"

Nếu không detect được → hỏi:
- Language chính?
- Framework chính?
- Build tool?
- Test framework?
- Package manager?

#### Part 1: Project Identity *(tất cả tiers)*

Hỏi một lần, group lại:
- Project name + type (web app / API / CLI / lib / monorepo)?
- Team size?
- Stage (greenfield / active / maintenance / legacy)?

#### Part 2: Architecture *(tất cả tiers)*

- Architecture style (monolith / microservices / modular monolith / event-driven)?
- Key layers và thư mục tương ứng?
- Entry points?
- External dependencies (DB, queue, cache, external APIs)?

"Paste `tree -L 3` hoặc tôi tự scan codebase."
→ Đọc output, extract key directories tự động.

Gotchas (high-value nhất — không bỏ qua):
- Thư mục/file nào KHÔNG được edit thủ công? (generated code)
- Build order dependencies? (codegen → compile)
- Test isolation cần gì? (Docker? env vars? seeds?)
- Vùng code nào cần extra care? (auth, payments, migrations)

#### Part 3: Conventions *(tất cả tiers)*

Nếu detect được eslint/prettier/black/gofmt → confirm, không hỏi lại.
Nếu không detect → hỏi:
- Code style tool?
- Branch strategy (trunk-based / gitflow)?
- Commit format (conventional / custom / none)?
- Test coverage target?

#### Part 4: Permissions *(tất cả tiers)*

Load preset từ `references/settings-presets.json` theo detected stack.

"Dựa trên stack của bạn, tôi suggest permission profile này:
[show preset với giải thích từng rule]
Muốn customize không?"

Hỏi thêm:
- Tool nào Claude KHÔNG được dùng? → disallowedTools
- Path nào chỉ đọc không được sửa? → read-only paths

#### Part 5: Hooks *(Tier 2+)*

Detect tools có sẵn → suggest từ `references/hooks-catalog.json`:

```
ESLint detect   → "Bật hook eslint --fix sau khi Claude edit .ts/.js?"
Prettier detect → "Bật hook prettier --write sau Edit tool?"
pytest detect   → "Bật hook pytest sau khi Claude edit *_test.py?"
Jest detect     → "Bật hook jest sau khi Claude edit *.test.*?"
gofmt detect    → "Bật hook gofmt -w sau Edit tool trên .go files?"
```

Từng hook một. Show preview trước khi confirm.

#### Part 6: MCP Servers *(Tier 2+)*

"Project này interact với services nào từ external?"
→ Show danh sách từ `references/mcp-registry.json`.

Với mỗi service chọn:
- Show config preview.
- Attempt test connection → report ✓ tested / ⚪ configured-not-verified / ✗ not-found.
- Không báo ✓ nếu chưa test thực sự.
- Confirm trước khi add.

#### Part 7: Agents *(Tier 3+)*

Load `references/agents-catalog.json` → suggest agents theo project type/team size.

Luôn include `drift-monitor` khi Tier 3.
Show preview từng agent → confirm.

#### Part 8: SSOT *(Tier 3+)*

- "Tạo `docs/architecture.md`?" → Có: draft từ Part 2 answers.
- "Setup ADR structure?" → Có: tạo `docs/adr/` + `ADR-0001-initial-architecture.md`.
- "Tạo CODEMAPS?" → Có: tạo `docs/CODEMAPS/` structure guide.

### Step 4 — Preview & Confirm

Sau khi interview xong, generate preview toàn bộ files sẽ write:

```
Đây là những gì tôi sẽ tạo/update:
┌──────────────────────────────────────┬──────────┬───────┐
│ File                                 │ Action   │ Tier  │
├──────────────────────────────────────┼──────────┼───────┤
│ CLAUDE.md                            │ CREATE   │ 1     │
│ .claude/settings.json (permissions)  │ CREATE   │ 1     │
│ .claude/settings.json (hooks)        │ UPDATE   │ 2     │
│ .mcp.json                            │ CREATE   │ 2     │
│ .claude/agents/drift-monitor.md      │ CREATE   │ 3     │
│ docs/architecture.md                 │ CREATE   │ 3     │
└──────────────────────────────────────┴──────────┴───────┘
Confirm không?
```

Với file đã tồn tại: "File [X] đã có. Overwrite / Merge / Skip?"

### Step 5 — Orchestrate Pillar Skills

User approve → invoke từng pillar skill theo tier với context từ interview:

```
Tier 1: /shipwithai-starter:setup-memory       (pass: project identity, stack, architecture, conventions)
         /shipwithai-starter:setup-permissions  (pass: stack, user overrides)

Tier 2: /shipwithai-starter:setup-hooks        (pass: detected tools, hook selections)
         /shipwithai-starter:setup-mcp          (pass: service selections)

Tier 3: /shipwithai-starter:setup-agents       (pass: agent selections)
         /shipwithai-starter:setup-ssot         (pass: architecture answers, SSOT selections)
```

### Step 6 — After-Write

1. Summary table: files created / updated / skipped.
2. "Commit `.claude/` và `CLAUDE.md` vào repo để team share harness."
3. "Muốn test harness? Tôi simulate một task nhỏ với config mới."
4. Upgrade note: "Đang ở Tier [N]. Upgrade với `/shipwithai-starter:review`."

## Failure Modes

```
Don't guess stack nếu ambiguous → hỏi
Don't write hooks cho tool không detect được trong project
Don't add MCP server nếu chưa verify connection thực sự
Don't overwrite existing file không hỏi
Don't skip gotchas section — đây là high-value nhất
Don't proceed nếu user chưa confirm preview
```
