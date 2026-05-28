# Design Spec: AI Workflow Gates in `shipwithai-starter`

**Date:** 2026-05-28
**Status:** Approved
**Author:** Claude Code (brainstorming session)

---

## Overview

Thêm "Development Workflow" instructions vào CLAUDE.md được gen bởi `shipwithai-starter`, cùng với cơ chế **incremental interview** để plugin tự detect khi có câu hỏi mới và hỏi bổ sung mà không re-run toàn bộ interview.

**Problem 1:** Plugin hiện tại gen ra project context tốt nhưng không có AI workflow instructions — Claude không biết nên follow process gì khi làm task.

**Problem 2:** Khi plugin update có feature mới (câu hỏi mới), existing projects không có cơ chế để nhận update mà không bị hỏi lại toàn bộ.

**Solution:**
- Workflow gates: thêm 1 checkbox question vào Part 3, gen "Development Workflow" section trong CLAUDE.md
- Schema versioning: `starter-context.json` track version, `init --update` chỉ hỏi missing fields, `review` detect outdated schema

**Core value prop:** Plugin updates → `review` tự phát hiện → user chạy `init --update` → chỉ trả lời câu hỏi mới → CLAUDE.md được cập nhật.

---

## Architecture

### Files thay đổi

```
plugins/starter/
├── skills/
│   ├── init/SKILL.md           ← +1 câu hỏi cuối Part 3 + --update mode mới
│   ├── setup-memory/SKILL.md   ← +1 section template + gen logic
│   └── review/SKILL.md         ← +1 schema version check + 1 component check + 1 drift rule
```

Không có file mới. Không thay đổi tier model.

### Data flow — normal init

```
init (Part 3 interview)
  → user selects workflow gates
  → lưu: starter-context.json → conventions.workflow_gates[] + schema_version: "1.1"

setup-memory (gen CLAUDE.md)
  → đọc conventions.workflow_gates[]
  → gen "Development Workflow" section với instructions tương ứng
```

### Data flow — plugin update scenario

```
Plugin update: schema_version bump 1.0 → 1.1 (thêm workflow_gates)

review (existing project)
  → đọc starter-context.json → schema_version: "1.0"
  → so sánh với current plugin schema: "1.1"
  → flag: "Plugin has new questions (v1.1). Run /shipwithai-starter:init --update"

init --update (incremental interview)
  → đọc starter-context.json
  → loop qua tất cả interview questions
  → skip câu đã có answer trong context
  → hỏi CHỈ câu null/absent: workflow_gates
  → update starter-context.json + schema_version
  → invoke setup-memory (merge mode)
```

### starter-context.json schema change

Bump version và thêm 1 field:

```json
{
  "version": "1.1",
  "tier": "full",
  "stack": { "...": "unchanged" },
  "conventions": {
    "formatter": "prettier",
    "branch_strategy": "gitflow",
    "commit_format": "conventional",
    "coverage_target": "80%",
    "workflow_gates": ["plan-before-code", "tdd", "code-review"]
  }
}
```

`workflow_gates` values: `"plan-before-code"` | `"tdd"` | `"code-review"` | `"security-review"` | `"none"`

`"none"` là mutually exclusive — nếu được chọn, override tất cả gates khác. Interview UI enforce: khi chọn "None", deselect các option còn lại.

Backward compatible: `workflow_gates` absent → section không gen, `review` flag schema outdated.

---

## Section 1: `init/SKILL.md` changes

### 1a — Câu hỏi mới trong Part 3 (Conventions)

**Vị trí:** Cuối Part 3, sau commit format question (all tiers).

```
"Which workflow gates should Claude follow when working on tasks?"
(Select all that apply)

→ [ ] Plan/design before coding
      Claude must create a plan or design doc before writing code for any task > 30 min
→ [ ] TDD — write tests first
      Claude writes failing tests before implementation
→ [ ] Code review gate
      Claude runs code-reviewer agent after every significant change
→ [ ] Security review for sensitive areas
      Claude runs security-reviewer before committing to sensitive areas
→ [ ] None — let Claude decide
```

### 1b — `--update` mode mới

Trigger: `init --update` hoặc khi `review` suggest.

```
Step 1: Đọc starter-context.json
        → Không tồn tại: "No context found. Run /shipwithai-starter:init for full setup."
        → Tồn tại: tiếp tục

Step 2: So sánh existing answers với canonical question list
        → Tìm tất cả fields null hoặc absent

Step 3: Với mỗi missing field:
        → Hỏi câu hỏi tương ứng (same wording as full interview)
        → Lưu answer vào context

Step 4: Update starter-context.json:
        → Merge answers mới vào
        → Bump schema_version lên current

Step 5: Invoke setup-memory (merge mode)
        → Chỉ add/update sections có data mới
        → Existing sections giữ nguyên
```

**Standalone mode** (`setup-memory` gọi độc lập, không có context file):
Hỏi workflow gates question. User skip → không gen section, không để placeholder.

---

## Section 2: `setup-memory/SKILL.md` changes

### CLAUDE.md template — section mới

Thêm sau "Key conventions" section:

```markdown
## Development workflow

**When working on any task, Claude must follow these gates:**

- [generated lines per gate selected]
```

### Gate → instruction mapping

| Gate | Instruction |
|---|---|
| `plan-before-code` | **Plan first:** For any task > 30 min, create a plan and get approval before writing code. |
| `tdd` | **TDD:** Write failing tests first. Never write implementation without a corresponding test. |
| `code-review` | **Code review:** Run the code-reviewer agent after every significant change. Address all CRITICAL and HIGH findings. |
| `security-review` (có sensitive_areas) | **Security review:** Before committing to `src/auth/, src/payments/` (từ `architecture.sensitive_areas`), run security-reviewer agent. |
| `security-review` (sensitive_areas empty) | **Security review:** Before committing to sensitive areas (auth, payments, migrations), run security-reviewer agent. |
| `none` / empty | *(section omitted entirely)* |

### Example output (plan-before-code + tdd + code-review)

```markdown
## Development workflow

**When working on any task, Claude must follow these gates:**

- **Plan first:** For any task > 30 min, create a plan and get approval before writing code.
- **TDD:** Write failing tests first. Never write implementation without a corresponding test.
- **Code review:** Run the code-reviewer agent after every significant change. Address all CRITICAL and HIGH findings.
```

### Merge behavior

CLAUDE.md đã có "Development workflow" section:
→ Offer Overwrite / Keep existing / Skip — consistent với behavior các section khác.

---

## Section 3: `review/SKILL.md` changes

### Step 1 — Score Components (thêm 1 dòng)

```
starter-context.json schema  → current ✅ / outdated ⚠️ / missing ❌
CLAUDE.md workflow section   → present ✅ / missing ⚠️
```

### Schema version check logic

```
starter-context.json tồn tại:
  → đọc version field
  → version == current plugin schema ("1.1")  → ✅
  → version < current ("1.0")                 → ⚠️ "Schema outdated (v1.0 → v1.1)"
  → version field absent                      → ⚠️ "Schema version unknown"

starter-context.json không tồn tại:
  → ❌ "Not initialized — run /shipwithai-starter:init"
```

### Workflow section check (smart opt-out)

```
starter-context.json tồn tại:
  → workflow_gates absent        → ⚠️ "Schema outdated — run init --update"
  → workflow_gates = ["none"]    → ✅ "Explicitly opted out"
  → workflow_gates = [...]       → check CLAUDE.md section exists → ✅/⚠️

starter-context.json không tồn tại:
  → check CLAUDE.md có workflow section không
  → present                      → ✅
  → missing                      → ⚠️ "No workflow section found"
```

### Step 2 — Drift Detection (thêm 1 rule)

```
workflow_gates  ←→  architecture.sensitive_areas
  sensitive_areas present NHƯNG "security-review" không có trong workflow_gates?
  → flag ⚠️ "Sensitive areas detected but no security-review gate configured"
```

### Health report table (thêm 2 rows)

```
| starter-context.json schema | ⚠️ | Schema outdated (v1.0 → v1.1)           |
| CLAUDE.md workflow          | ⚠️ | No development workflow gates configured |
```

### Suggest action

Schema outdated:
> "Plugin has new questions (v1.1). Run `/shipwithai-starter:init --update` to answer only new questions — existing answers are preserved."

Workflow missing nhưng schema current:
> "Workflow section missing from CLAUDE.md. Run `/shipwithai-starter:init --update` to add it."

---

## Tier

Workflow instructions thuộc **Tier 1 (Essential)** — tất cả tiers đều nhận.

Schema versioning áp dụng toàn bộ plugin, không phụ thuộc tier.

---

## Future-proofing

Mỗi lần plugin thêm feature mới:
1. Thêm câu hỏi vào interview (init/SKILL.md)
2. Thêm field vào starter-context.json schema
3. Bump `schema_version`
4. `review` tự phát hiện existing projects bị outdated
5. `init --update` chỉ hỏi field mới — không làm phiền user với câu hỏi cũ

---

## Out of Scope

- `add-workflow` command riêng (superseded by `init --update`)
- Skill `setup-workflow` riêng (overkill)
- Autonomous inference từ team_size/stage (không reliable)
- Enforcement mechanisms ngoài CLAUDE.md instructions
