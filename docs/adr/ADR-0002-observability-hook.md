# ADR-0002: Observability Hook for Session Replay and Drift Detection

**Date:** 2026-06-01
**Status:** Accepted
**Deciders:** Leonard Trinh

---

## Context

As the shipwithai-starter harness grows, there is no way to audit what Claude Code
actually did during a session — which files were edited, which commands were run, and
in what order. This makes debugging broken sessions, detecting configuration drift, and
understanding harness usage patterns difficult.

A lightweight observability layer is needed that:
- Does not block or slow down tool execution
- Does not log sensitive content (file contents, command output)
- Works without external dependencies (stdlib only)
- Can be disabled per-project or per-session

---

## Options Considered

### Option A: PostToolUse hook writing JSONL logs locally

A Python script installed at `.claude/hooks/observe.py` intercepts PostToolUse events
for Edit, Write, and Bash. Logs one structured line per call to
`.claude/logs/YYYY-MM-DD.jsonl`. Silent-fails so it never blocks execution.

**Pros:**
- Zero external dependencies (Python stdlib only)
- Silent failure — never interrupts work
- JSONL is easy to parse for replay and analysis
- Logs stay local, never leave the machine
- 50 MB cap prevents runaway disk usage
- Disable via `DISABLE_OBSERVE` env var

**Cons:**
- Logs accumulate on disk (mitigated by size cap + .gitignore)
- Only captures tool name + file/command, not outcome or duration

### Option B: External telemetry (PostHog, Mixpanel, etc.)

Send events to a hosted analytics service.

**Pros:**
- Centralized across all user projects
- Dashboards out of the box

**Cons:**
- External dependency and network call per tool use
- Privacy concern — tool calls may reveal sensitive filenames
- Requires API key management
- Adds latency to every tool call

### Option C: No observability

Keep the harness stateless; rely on git log for audit trail.

**Pros:**
- No additional complexity
- Git already captures file change history

**Cons:**
- No visibility into tool call sequence within a session
- No way to detect which hooks fire or how often
- Cannot replay sessions for debugging

---

## Decision

We chose **Option A** (local JSONL hook). It provides session-level observability with
no external dependencies, no content leakage, and zero impact on tool execution. The
50 MB cap and `.gitignore` entry keep disk usage and repo cleanliness under control.
Option B was rejected on privacy and dependency grounds. Option C leaves too large a
debugging blind spot as the harness grows.

The schema was bumped to v1.2 to track `observability.enabled` per project, so the
`/review` skill can detect whether the hook is installed and report drift.

---

## Consequences

**Positive:**
- Sessions are now replayable via `.claude/logs/YYYY-MM-DD.jsonl`
- `/review` skill can detect if observe.py is installed or missing
- Future drift-monitor can correlate tool call patterns with config changes

**Negative / Risks:**
- Logs are local only — no cross-project aggregation without additional tooling
- Hook must be re-installed per project (shipped as an asset, not auto-applied)

**Follow-up actions:**
- [ ] Add log parsing utility to shipwithai-starter for session replay (Phase 3)
- [ ] Consider adding duration/outcome fields to the JSONL schema in a future version
