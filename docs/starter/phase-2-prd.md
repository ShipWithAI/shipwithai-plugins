# PRD: shipwithai-starter — Phase 2

> Date: 2026-05-29
> Last updated: 2026-06-01
> Status: Draft — in discussion
> Depends on: Phase 1 complete (v1.2.0)

---

## Overview

Phase 1 thiết lập harness tĩnh: interview → write files → done.
Phase 2 biến harness thành hệ thống **sống** — học từ usage thực tế và tự tối ưu theo thời gian.

**Theme:** *From static setup → living harness*

> **Component 1 (User-level Profile) — Dropped.**
> Chỉ cover 4 stack-agnostic fields (tier, commit format, gates, coverage).
> Value thấp so với effort: những fields này đã có auto-detect + catalog suggest,
> user chỉ cần confirm. Sẽ revisit nếu có user feedback thực tế.

---

## Research findings (2026-06-01)

### Claude Code OpenTelemetry — Không khả dụng cho local logging

Claude Code có OTEL support nhưng **không thể dùng làm local data source**:

- `OTEL_EXPORTER_OTLP_ENDPOINT=file:///...` — không tạo file (file protocol không được support)
- HTTP receiver trên port 4318 và 14318 — không nhận data nào dù đã set `OTEL_TRACES_EXPORTER=otlp`
- `--print` mode suppress toàn bộ OTEL export

Kết luận: Claude Code's OTEL gửi về Anthropic internal collector, không phải user-configurable endpoint.
**PostToolUse hook là cách duy nhất thực tế để capture tool call data locally.**

### Claude Code hook environment variables (confirmed)

Hooks nhận data qua env vars, không phải stdin:
- `$CLAUDE_TOOL_INPUT_PATH` — file path cho Edit/Write hooks
- `$CLAUDE_TOOL_INPUT_COMMAND` — command string cho Bash hooks (cần verify exact name)
- `$CLAUDE_SESSION_ID` — session identifier (cần verify availability)

---

## Component 1: Observability (Pillar 7)

### Problem

Hiện tại không có visibility vào cách harness được dùng thực tế:
- Claude dùng tool nào nhiều nhất?
- Hook có fire không?
- Workflow pattern như thế nào?

Không có data → không thể optimize. `harness-optimizer` (Component 2) phụ thuộc hoàn toàn vào component này.

### What it does

Thêm `observe.py` làm PostToolUse hook, ghi tool call metadata ra `.claude/logs/YYYY-MM-DD.jsonl`.
Không log prompt, response, hay nội dung file — chỉ log metadata.

### Files created

| File | Location | Purpose |
|------|----------|---------|
| `skills/setup-observability/SKILL.md` | plugin | Pillar skill — enable/disable logging |
| `assets/observe.py` | plugin | Hook script copied vào user project |
| Entry in `skills/setup-hooks/hooks-catalog.json` | plugin | "observability" hook template |

### Log format (decided)

**Per-date files** — không phải single `session.jsonl`:

```
.claude/logs/
  2026-05-29.jsonl
  2026-05-30.jsonl
  2026-06-01.jsonl
```

Mỗi line là một JSON object:

```jsonl
{"ts":"2026-06-01T10:30:00Z","sid":"a3f2","event":"tool","tool":"Edit","file":"src/auth.ts","ms":45}
{"ts":"2026-06-01T10:30:05Z","sid":"a3f2","event":"tool","tool":"Bash","cmd":"npm","exit":0,"ms":3420}
{"ts":"2026-06-01T10:30:10Z","sid":"a3f2","event":"tool","tool":"Write","file":"src/config.ts","ms":12}
```

**Fields:**

| Field | Type | Notes |
|-------|------|-------|
| `ts` | ISO8601 | Timestamp |
| `sid` | string | Short session ID — group events by session |
| `event` | string | Luôn là `"tool"` (xem Dropped below) |
| `tool` | string | Edit / Write / Bash |
| `file` | string | Relative path (Edit/Write only) — dùng `os.path.relpath(path, cwd)` |
| `cmd` | string | `argv[0]` only, không log arguments (Bash only) |
| `exit` | int | Process exit code (Bash only) |
| `ms` | int | Duration milliseconds |

**Dropped: `event:"hook"` type**

Không thể implement: `observe.py` là PostToolUse hook entry độc lập — nó không có visibility vào hook commands khác (prettier, eslint...) đã chạy hay chưa, exit code là bao nhiêu. Để track hook health, Component 2 dùng static analysis thay vì runtime data (xem Component 2).

### Hook scope (decided)

Chỉ hook **Edit, Write, Bash** — không phải all tools.

Read, Glob, Grep fire rất thường xuyên, low signal, tạo noise. Mutations và executions mới có giá trị cho optimizer.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Bash",
        "hooks": [{"type": "command", "command": "python3 .claude/hooks/observe.py"}]
      }
    ],
    "Stop": [
      {
        "hooks": [{"type": "command", "command": "find .claude/logs -name '*.jsonl' -mtime +30 -delete 2>/dev/null || true"}]
      }
    ]
  }
}
```

### Privacy model (decided)

| Data | Decision | Lý do |
|------|----------|-------|
| File path | Relative path only | Absolute path expose username (`/Users/john.doe/...`) |
| Bash command | `argv[0]` only, no args | Args có thể chứa credentials, tokens, secrets |
| File content | Không log | Tool input content không bao giờ được log |
| Prompt/response | Không log | Out of scope |

**Git tracking check**: `setup-observability` skill phải chạy `git ls-files .claude/logs` và warn nếu đang tracked trước khi enable.

### Opt-out (decided)

```bash
DISABLE_OBSERVE=1  # Per-session, set in terminal hoặc shell profile
```

`observe.py` check env var này đầu tiên, `sys.exit(0)` ngay nếu set.

### Rotation (decided)

**Per-date files + Stop hook:**
- Mỗi ngày một file (`YYYY-MM-DD.jsonl`) → không cần file locking, không có write contention
- Stop hook chạy `find .claude/logs -name "*.jsonl" -mtime +30 -delete` mỗi session end
- Max 50MB total — `observe.py` check total size và skip logging nếu vượt ngưỡng

### Tier placement (decided)

Tier 3 (Full) — opt-in. Không bật mặc định vì có disk footprint.
Tier 2 users có thể enable manually qua `/shipwithai-starter:setup-observability`.

### Integration với `init` skill (required — not yet done)

Khi Phase 2 ship, `init` SKILL.md cần update:

1. **Step 4 preview table** — thêm row cho `observe.py` và `.claude/logs/`
2. **Step 5 orchestration** — thêm Tier 3: `/shipwithai-starter:setup-observability`
3. **`starter-context.json` schema v1.2** — thêm field:
   ```json
   "observability": {"enabled": false}
   ```
4. **`review` skill** — thêm check: observe.py có tồn tại không? `.claude/logs/` có trong .gitignore không?

### `setup-observability` skill spec

Skill cần thực hiện:

1. Copy `observe.py` vào `.claude/hooks/observe.py`
2. Merge PostToolUse hook entry vào `.claude/settings.json` (merge, không overwrite)
3. Merge Stop hook rotation entry vào `.claude/settings.json`
4. Add `.claude/logs/` vào `.gitignore` (check duplicate trước)
5. Check `git ls-files .claude/logs` — warn nếu đang tracked
6. Explain privacy model: file path (relative), cmd (argv[0] only), không log content
7. Update `starter-context.json` → set `observability.enabled: true`

Support `--disable` flag: reverse tất cả các bước trên.

Idempotent: chạy lại không tạo duplicate entries.

---

## Component 2: harness-optimizer

### Problem

Harness setup một lần → không tự cải thiện.
Hooks có thể stale, MCP servers không dùng vẫn load, workflow gates không phù hợp với thực tế.

### What it does

Agent đọc observability logs (Component 1) + static analysis của codebase → phân tích patterns → suggest cải tiến cụ thể.

### Files created

| File | Location | Purpose |
|------|----------|---------|
| `agents/harness-optimizer.md` | plugin | Agent definition |
| `skills/optimize-harness/SKILL.md` | plugin | User-invoked optimization run |

### Analysis rules (decided)

**Runtime analysis** — từ `.claude/logs/*.jsonl`:

```
Tool usage patterns (30 days):
  Bash cmd="npm" > 5 lần, không có jest-on-stop hook  → suggest add jest-on-stop hook
  Edit trên *.ts > 20 lần/ngày, không có prettier hook → suggest add prettier-on-edit hook

Workflow patterns:
  Edit trên auth/ > 10 lần, không có security-review gate → suggest enable security-review gate
  Minimum data window: 7 ngày log trước khi suggest bất kỳ điều gì
```

**Static analysis** — từ codebase + `starter-context.json` (không cần runtime data):

```
Hook health:
  Hook command references binary X  → check X trong devDependencies / which X
  (Hook fire rate không track được từ logs — dùng static check thay thế)

MCP usage:
  ⚠️ Không thể track runtime MCP calls (OTEL không khả dụng locally)
  Thay thế: compare mcp_selected trong starter-context.json vs package.json imports
    → GitHub MCP configured nhưng không có gh/octokit imports → flag for review
    → package.json có @linear/sdk nhưng không có Linear MCP → suggest add

Codebase drift:
  sensitive_areas trong starter-context.json vs thư mục thực tế còn tồn tại không?
  Detected stack thay đổi so với stack.language trong starter-context.json?
```

### Trigger modes

- **Manual:** `/shipwithai-starter:optimize-harness` — user-invoked
- **Via review:** `review` gọi optimizer như optional Step cuối nếu log data ≥ 7 ngày
- ~~Scheduled weekly cron~~ — defer, quá phức tạp cho Phase 2

### Open questions (còn lại)

1. **Standalone skill hay tích hợp vào `review`?**
   Current leaning: standalone skill, `review` chỉ mention "run optimize-harness for deeper suggestions"
2. **Confidence threshold:** Suggest khi pattern xuất hiện ≥ 5 lần (runtime) hoặc static check pass
3. **Auto-apply:** Chỉ suggest, không auto-apply — user confirm trước khi thay đổi config

---

## Component 3: Dashboard / Reporting

### Problem

`review` check một project tại một thời điểm.
User có nhiều projects không có visibility tổng thể.

### What it does

Scan `~/` tìm projects có `.claude/starter-context.json` → aggregate health report.

### Output format (draft)

```
## harness health — all projects
Scanned: 2026-06-01 | 4 projects found

| Project          | Tier     | Schema | Drift | Last check |
|------------------|----------|--------|-------|------------|
| acme-api         | Standard | ✅ v1.1 | ⚠️ 2  | 3 days ago |
| personal-finance | Essential| ✅ v1.1 | ✅ 0  | today      |
| old-side-project | Essential| ⚠️ v1.0 | ❌ 5  | 45 days ago|
| monorepo-core    | Full     | ✅ v1.1 | ✅ 0  | today      |

→ "old-side-project" needs attention. Run /shipwithai-starter:review there?
```

### Priority note

**Lowest priority — likely defer sang Phase 3.**
`review` đã cover single-project health tốt. Dashboard chỉ có giá trị khi user có ≥ 3 active projects.
Có thể implement như một simple bash script thay vì full skill.

### Open questions

1. **Scope:** Full skill hay `find ~ -name starter-context.json | xargs ...` bash script?
2. **Search paths:** Scan `~/` hay user configure `search_paths`?
3. **In scope Phase 2?** Current leaning: defer sang Phase 3.

---

## Dependencies & Build Order

```
Component 1 (Observability)  → Standalone. Build first.
     ↓
Component 2 (Optimizer)      → Requires Component 1 logs (runtime rules).
                               Static analysis rules work without logs.

Component 3 (Dashboard)      → Independent. Lowest value. Defer.
```

## Tier mapping

```
Tier 1 (Essential): no change
Tier 2 (Standard):  no change
Tier 3 (Full):      + Observability (new) + harness-optimizer (new)
```

## Version targets

| Version | Scope |
|---------|-------|
| v2.0.0 | Component 1: Observability |
| v2.1.0 | Component 2: harness-optimizer |
| v2.2.0 | Component 3: Dashboard (or defer to Phase 3) |
