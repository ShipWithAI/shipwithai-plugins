# Phase 2 — Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Pillar 7 (Observability) to shipwithai-starter — a PostToolUse hook that logs tool call metadata to `.claude/logs/YYYY-MM-DD.jsonl` so harness-optimizer (v2.1.0) can analyze usage patterns.

**Architecture:** `observe.py` (stdlib-only Python) is installed as a PostToolUse hook for Edit/Write/Bash tools. It writes one JSONL line per tool call to per-date log files. `setup-observability` skill handles installation, `.gitignore`, and idempotency. `init` and `review` are updated to integrate the new pillar.

**Tech Stack:** Python 3 stdlib only (no external deps), Markdown (SKILL.md authoring), JSON (manifest, evals, hooks-catalog)

**Scope:** Component 1 only (v2.0.0). Component 2 (harness-optimizer) is a separate plan.

---

## File Map

**CREATE:**
- `plugins/starter/assets/observe.py` — hook script copied into user projects
- `plugins/starter/assets/tests/test_observe.py` — unit tests for observe.py
- `plugins/starter/skills/setup-observability/SKILL.md` — pillar skill
- `plugins/starter/skills/setup-observability/evals.json` — 6 eval prompts

**MODIFY:**
- `plugins/starter/skills/setup-hooks/hooks-catalog.json` — add observability entry
- `plugins/starter/skills/init/SKILL.md` — Step 4 table, Step 5 Tier 3, schema v1.2
- `plugins/starter/skills/review/SKILL.md` — add observability health checks
- `plugins/starter/manifest.json` — add setup-observability skill
- `plugins/starter/CHANGELOG.md` — v2.0.0 entry
- `plugins/starter/README.md` — add setup-observability to skill list

---

## Task 1: Verify Claude Code Hook Data Mechanism

Before writing observe.py, confirm what data Claude Code actually provides to a PostToolUse hook (env vars vs stdin, exact var names).

**Files:**
- Create: `/tmp/debug_hook.py` (temp only — not committed)
- Create: `/tmp/test-hook-project/` (temp test project)

- [ ] **Step 1: Create a debug hook script**

```bash
cat > /tmp/debug_hook.py << 'HOOKEOF'
import sys, os, json

env_dump = {k: v for k, v in os.environ.items() if any(x in k for x in ['CLAUDE', 'TOOL', 'SESSION'])}
stdin_raw = sys.stdin.buffer.read()

try:
    stdin_parsed = json.loads(stdin_raw) if stdin_raw.strip() else None
except Exception:
    stdin_parsed = None

output = {
    'env_vars': env_dump,
    'stdin_raw_bytes': len(stdin_raw),
    'stdin_parsed': stdin_parsed,
}

with open('/tmp/hook_debug_output.json', 'w') as f:
    json.dump(output, f, indent=2)
HOOKEOF
echo "debug hook written"
```

- [ ] **Step 2: Create minimal test project with debug hook configured**

```bash
mkdir -p /tmp/test-hook-project/.claude
cat > /tmp/test-hook-project/.claude/settings.json << 'EOF'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "python3 /tmp/debug_hook.py"}]
      }
    ]
  }
}
EOF
cat > /tmp/test-hook-project/hello.txt << 'EOF'
hello
EOF
echo "test project created"
```

- [ ] **Step 3: Run claude in test project to trigger the hook**

```bash
cd /tmp/test-hook-project
claude --print "Replace the word 'hello' in hello.txt with 'world'" 2>&1
```

- [ ] **Step 4: Inspect debug output**

```bash
cat /tmp/hook_debug_output.json
```

Expected: JSON with `env_vars` and `stdin_parsed`. Look for:
- `CLAUDE_TOOL_NAME` or similar → tool name
- `CLAUDE_TOOL_INPUT_PATH` → file path for Edit
- `CLAUDE_SESSION_ID` → session identifier
- `stdin_parsed` → non-null means Claude Code sends JSON via stdin

- [ ] **Step 5: Record findings and update observe.py design if needed**

Document the exact env var names found. If stdin has JSON: `observe.py` reads stdin. If only env vars: `observe.py` reads env vars. Update Task 2 accordingly before proceeding.

- [ ] **Step 6: Cleanup temp files**

```bash
rm -rf /tmp/test-hook-project /tmp/debug_hook.py /tmp/hook_debug_output.json
```

---

## Task 2: Implement observe.py (TDD)

**Files:**
- Create: `plugins/starter/assets/observe.py`
- Create: `plugins/starter/assets/tests/test_observe.py`

- [ ] **Step 1: Create assets/ directory and write the test file first**

```bash
mkdir -p plugins/starter/assets/tests
```

```python
# plugins/starter/assets/tests/test_observe.py
import datetime
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
import observe


class TestBuildEvent(unittest.TestCase):

    def test_edit_tool_produces_relative_file_path(self):
        payload = {
            'tool_name': 'Edit',
            'tool_input': {'file_path': '/project/src/auth.ts'},
        }
        with patch('os.getcwd', return_value='/project'):
            event = observe.build_event(payload)
        self.assertEqual(event['tool'], 'Edit')
        self.assertEqual(event['file'], 'src/auth.ts')

    def test_write_tool_produces_relative_file_path(self):
        payload = {
            'tool_name': 'Write',
            'tool_input': {'file_path': '/project/out/result.json'},
        }
        with patch('os.getcwd', return_value='/project'):
            event = observe.build_event(payload)
        self.assertEqual(event['file'], 'out/result.json')

    def test_bash_tool_logs_argv0_only(self):
        payload = {
            'tool_name': 'Bash',
            'tool_input': {'command': 'npm test --coverage --reporter=json'},
        }
        event = observe.build_event(payload)
        self.assertEqual(event['cmd'], 'npm')

    def test_bash_strips_args_containing_secrets(self):
        payload = {
            'tool_name': 'Bash',
            'tool_input': {'command': 'aws s3 cp file.txt s3://bucket --aws-access-key-id=AKIA123SECRET'},
        }
        event = observe.build_event(payload)
        self.assertEqual(event['cmd'], 'aws')
        self.assertNotIn('AKIA', json.dumps(event))

    def test_event_always_has_required_fields(self):
        payload = {'tool_name': 'Write', 'tool_input': {'file_path': '/p/f.ts'}}
        with patch('os.getcwd', return_value='/p'):
            event = observe.build_event(payload)
        for field in ('ts', 'sid', 'event', 'tool'):
            self.assertIn(field, event)
        self.assertEqual(event['event'], 'tool')

    def test_sid_truncated_to_8_chars(self):
        payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
        with patch('os.getcwd', return_value='/p'), \
             patch.dict(os.environ, {'CLAUDE_SESSION_ID': 'abc123def456xyz'}):
            event = observe.build_event(payload)
        self.assertEqual(len(event['sid']), 8)

    def test_sid_empty_when_no_session_id(self):
        payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
        env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_SESSION_ID'}
        with patch('os.getcwd', return_value='/p'), patch.dict(os.environ, env, clear=True):
            event = observe.build_event(payload)
        self.assertEqual(event['sid'], '')

    def test_ts_is_utc_iso8601(self):
        payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
        with patch('os.getcwd', return_value='/p'):
            event = observe.build_event(payload)
        # Should parse without error and end with Z
        datetime.datetime.strptime(event['ts'], '%Y-%m-%dT%H:%M:%SZ')
        self.assertTrue(event['ts'].endswith('Z'))

    def test_falls_back_to_env_var_for_tool_name(self):
        payload = {}  # No tool_name in payload
        with patch.dict(os.environ, {'CLAUDE_TOOL_NAME': 'Edit', 'CLAUDE_TOOL_INPUT_PATH': '/p/f.ts'}), \
             patch('os.getcwd', return_value='/p'):
            event = observe.build_event(payload)
        self.assertEqual(event['tool'], 'Edit')


class TestWriteLog(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)

    def _make_event(self, tool='Edit', file='src/x.ts'):
        return {'ts': '2026-06-01T10:00:00Z', 'sid': 'a1b2c3d4',
                'event': 'tool', 'tool': tool, 'file': file}

    def test_creates_log_directory_if_missing(self):
        observe.write_log(self._make_event())
        self.assertTrue(Path('.claude/logs').is_dir())

    def test_writes_valid_jsonl_line(self):
        observe.write_log(self._make_event())
        today = datetime.date.today().isoformat()
        content = Path(f'.claude/logs/{today}.jsonl').read_text().strip()
        parsed = json.loads(content)
        self.assertEqual(parsed['tool'], 'Edit')

    def test_appends_multiple_events(self):
        observe.write_log(self._make_event(file='a.ts'))
        observe.write_log(self._make_event(file='b.ts'))
        today = datetime.date.today().isoformat()
        lines = Path(f'.claude/logs/{today}.jsonl').read_text().strip().split('\n')
        self.assertEqual(len(lines), 2)

    def test_skips_write_when_over_50mb(self):
        log_dir = Path('.claude/logs')
        log_dir.mkdir(parents=True)
        (log_dir / 'old.jsonl').write_bytes(b'x' * (51 * 1024 * 1024))
        observe.write_log(self._make_event())
        today = datetime.date.today().isoformat()
        self.assertFalse(Path(f'.claude/logs/{today}.jsonl').exists())

    def test_log_filename_is_todays_date(self):
        observe.write_log(self._make_event())
        today = datetime.date.today().isoformat()
        self.assertTrue(Path(f'.claude/logs/{today}.jsonl').exists())


class TestMain(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)

    def test_exits_silently_when_disable_observe_set(self):
        with patch.dict(os.environ, {'DISABLE_OBSERVE': '1'}):
            observe.main()  # Must not raise or write anything
        self.assertFalse(Path('.claude/logs').exists())

    def test_exits_silently_when_no_payload_and_no_env(self):
        with patch('observe.read_payload', return_value={}), \
             patch.dict(os.environ, {k: v for k, v in os.environ.items()
                        if k not in ('CLAUDE_TOOL_NAME', 'CLAUDE_SESSION_ID')}, clear=True):
            observe.main()
        self.assertFalse(Path('.claude/logs').exists())

    def test_does_not_raise_on_unexpected_error(self):
        with patch('observe.write_log', side_effect=PermissionError('no write')), \
             patch('observe.read_payload', return_value={'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}), \
             patch('os.getcwd', return_value='/p'):
            observe.main()  # Must swallow the error silently


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run tests — confirm all FAIL (RED)**

```bash
cd plugins/starter/assets
python3 -m pytest tests/test_observe.py -v 2>&1 | head -40
```

Expected: `ModuleNotFoundError: No module named 'observe'` — observe.py doesn't exist yet.

- [ ] **Step 3: Write observe.py**

```python
# plugins/starter/assets/observe.py
"""
observe.py — Claude Code tool call logger for shipwithai-starter.
Copy to .claude/hooks/observe.py in the user's project.

PostToolUse hook for Edit, Write, Bash.
Writes one JSONL line per call to .claude/logs/YYYY-MM-DD.jsonl.
Silent-fails — never blocks tool execution.
"""
import datetime
import json
import os
import pathlib
import sys

MAX_LOG_BYTES = 50 * 1024 * 1024  # 50 MB


def read_payload():
    """Read tool call data from stdin (Claude Code sends JSON if available)."""
    try:
        raw = sys.stdin.buffer.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def build_event(payload):
    """Build a log event dict from the hook payload."""
    tool = payload.get('tool_name') or os.environ.get('CLAUDE_TOOL_NAME', '')
    tool_input = payload.get('tool_input', {})
    session_id = os.environ.get('CLAUDE_SESSION_ID', '')

    event = {
        'ts': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'sid': session_id[:8],
        'event': 'tool',
        'tool': tool,
    }

    if tool in ('Edit', 'Write'):
        raw_path = tool_input.get('file_path') or os.environ.get('CLAUDE_TOOL_INPUT_PATH', '')
        try:
            event['file'] = os.path.relpath(raw_path, os.getcwd()) if raw_path else ''
        except ValueError:
            event['file'] = raw_path

    elif tool == 'Bash':
        cmd = tool_input.get('command') or os.environ.get('CLAUDE_TOOL_INPUT_COMMAND', '')
        parts = cmd.split()
        event['cmd'] = parts[0] if parts else ''

    return event


def write_log(event):
    """Append event to today's JSONL log file."""
    log_dir = pathlib.Path('.claude/logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    total = sum(f.stat().st_size for f in log_dir.glob('*.jsonl') if f.exists())
    if total > MAX_LOG_BYTES:
        return

    today = datetime.date.today().isoformat()
    with open(log_dir / f'{today}.jsonl', 'a') as f:
        f.write(json.dumps(event, separators=(',', ':')) + '\n')


def main():
    if os.environ.get('DISABLE_OBSERVE'):
        return

    payload = read_payload()
    if not payload and not os.environ.get('CLAUDE_TOOL_NAME'):
        return

    event = build_event(payload)
    if not event.get('tool'):
        return

    write_log(event)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pass  # Silent fail — never block tool execution
```

- [ ] **Step 4: Run tests — confirm all PASS (GREEN)**

```bash
cd plugins/starter/assets
python3 -m pytest tests/test_observe.py -v
```

Expected output:
```
PASSED tests/test_observe.py::TestBuildEvent::test_edit_tool_produces_relative_file_path
PASSED tests/test_observe.py::TestBuildEvent::test_write_tool_produces_relative_file_path
PASSED tests/test_observe.py::TestBuildEvent::test_bash_tool_logs_argv0_only
PASSED tests/test_observe.py::TestBuildEvent::test_bash_strips_args_containing_secrets
PASSED tests/test_observe.py::TestBuildEvent::test_event_always_has_required_fields
PASSED tests/test_observe.py::TestBuildEvent::test_sid_truncated_to_8_chars
PASSED tests/test_observe.py::TestBuildEvent::test_sid_empty_when_no_session_id
PASSED tests/test_observe.py::TestBuildEvent::test_ts_is_utc_iso8601
PASSED tests/test_observe.py::TestBuildEvent::test_falls_back_to_env_var_for_tool_name
PASSED tests/test_observe.py::TestWriteLog::test_creates_log_directory_if_missing
PASSED tests/test_observe.py::TestWriteLog::test_writes_valid_jsonl_line
PASSED tests/test_observe.py::TestWriteLog::test_appends_multiple_events
PASSED tests/test_observe.py::TestWriteLog::test_skips_write_when_over_50mb
PASSED tests/test_observe.py::TestWriteLog::test_log_filename_is_todays_date
PASSED tests/test_observe.py::TestMain::test_exits_silently_when_disable_observe_set
PASSED tests/test_observe.py::TestMain::test_exits_silently_when_no_payload_and_no_env
PASSED tests/test_observe.py::TestMain::test_does_not_raise_on_unexpected_error
17 passed
```

- [ ] **Step 5: Commit**

```bash
git add plugins/starter/assets/observe.py plugins/starter/assets/tests/test_observe.py
git commit -m "feat(starter): add observe.py hook script with unit tests"
```

---

## Task 3: Write setup-observability/SKILL.md

**Files:**
- Create: `plugins/starter/skills/setup-observability/SKILL.md`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p plugins/starter/skills/setup-observability
```

- [ ] **Step 2: Write SKILL.md**

```markdown
---
name: setup-observability
description: >
  Enable tool call logging: installs observe.py hook that writes tool usage
  metadata to .claude/logs/. Opt-in Tier 3 feature for harness optimization.
  Trigger phrases: "setup observability", "enable tool logging", "track tool usage",
  "add observability hook", "observe tool calls".
argument-hint: "[--disable]"
---

# /setup-observability

Installs a lightweight logging hook that records tool call metadata.
Used by `harness-optimizer` to detect patterns and suggest improvements.

## What gets logged

Only metadata — never content:

| Tool  | Logged                        | NOT logged                        |
|-------|-------------------------------|-----------------------------------|
| Edit  | Relative file path            | File content, old/new string      |
| Write | Relative file path            | File content                      |
| Bash  | Command name (argv[0] only)   | Arguments, output, exit code      |

One line per call: `.claude/logs/YYYY-MM-DD.jsonl`

Opt-out anytime: `export DISABLE_OBSERVE=1` in terminal or shell profile.

## Mode Detection

```
--disable flag    → reverse setup (see --disable Flow below)
No args           → run setup flow
```

## Setup Steps

1. Copy `observe.py` to `.claude/hooks/observe.py`
2. Merge PostToolUse hook into `.claude/settings.json` — matcher `Edit|Write|Bash`
3. Merge Stop hook (log rotation) into `.claude/settings.json`
4. Add `.claude/logs/` to `.gitignore` (skip if already present)
5. Check `git ls-files .claude/logs` — warn user if currently tracked
6. Update `starter-context.json` → `observability.enabled: true`

## Output Format

Preview before writing:

```
Observability setup:
  .claude/hooks/observe.py         CREATE
  .claude/settings.json (hook)     UPDATE — add PostToolUse + Stop entries
  .gitignore                       UPDATE — add .claude/logs/

Logs will be written to: .claude/logs/YYYY-MM-DD.jsonl
Opt-out: export DISABLE_OBSERVE=1

Proceed?
```

After writing:
```
✅ Observability enabled.
Logs: .claude/logs/ (excluded from git)
Disable anytime: export DISABLE_OBSERVE=1
Run /shipwithai-starter:optimize-harness after 7+ days to see suggestions.
```

## Write Rules

- Read `settings.json` before writing — merge into existing structure, never overwrite
- Check `hooks.PostToolUse` for matcher `Edit|Write|Bash` — skip if already present (idempotent)
- Check `hooks.Stop` for rotation command — skip if already present (idempotent)
- Check `.gitignore` for `.claude/logs/` — skip line if already present
- Never proceed without user confirmation of the preview

## --disable Flow

1. Remove PostToolUse hook entry with matcher `Edit|Write|Bash` from `settings.json`
2. Remove Stop hook rotation entry from `settings.json`
3. Update `starter-context.json` → `observability.enabled: false`
4. Report: "Observability disabled. Existing logs at `.claude/logs/` preserved — delete manually if not needed."
```

- [ ] **Step 3: Verify line count is under 500**

```bash
wc -l plugins/starter/skills/setup-observability/SKILL.md
```

Expected: under 100 lines. Under 300 is ideal.

- [ ] **Step 4: Commit**

```bash
git add plugins/starter/skills/setup-observability/SKILL.md
git commit -m "feat(starter): add setup-observability skill"
```

---

## Task 4: Write setup-observability/evals.json

**Files:**
- Create: `plugins/starter/skills/setup-observability/evals.json`

- [ ] **Step 1: Write evals.json**

```json
[
  {
    "prompt": "set up observability for my project",
    "expected": "Copies observe.py to .claude/hooks/, adds PostToolUse hook for Edit|Write|Bash, adds Stop rotation hook, adds .claude/logs/ to .gitignore, updates starter-context.json observability.enabled to true"
  },
  {
    "prompt": "I want to track which tools Claude uses most in my project",
    "expected": "Triggers setup-observability, explains log format (YYYY-MM-DD.jsonl), explains what is logged (file path, cmd argv[0] only), explains DISABLE_OBSERVE=1 opt-out"
  },
  {
    "prompt": "enable tool call logging so harness-optimizer has data",
    "expected": "Runs setup flow, shows preview table of files to create/update, asks for confirmation before writing"
  },
  {
    "prompt": "/shipwithai-starter:setup-observability --disable",
    "expected": "Removes PostToolUse hook entry, removes Stop rotation hook, sets starter-context.json observability.enabled to false, reports that existing logs are preserved"
  },
  {
    "prompt": "I already ran setup-observability, run it again",
    "expected": "Detects existing hook entry, skips without duplicating (idempotent), reports already configured"
  },
  {
    "prompt": "setup observability — but what exactly gets logged? I'm worried about privacy",
    "expected": "Shows the table: Edit/Write log relative file path only, Bash logs argv[0] only (no arguments), no content/output/prompt ever logged, explains DISABLE_OBSERVE=1 per-session opt-out"
  }
]
```

- [ ] **Step 2: Commit**

```bash
git add plugins/starter/skills/setup-observability/evals.json
git commit -m "feat(starter): add setup-observability evals"
```

---

## Task 5: Update hooks-catalog.json

Add an observability entry so `setup-hooks` (and advanced users) can see the hook template.

**Files:**
- Modify: `plugins/starter/skills/setup-hooks/hooks-catalog.json`

- [ ] **Step 1: Read current file to find insertion point**

```bash
tail -10 plugins/starter/skills/setup-hooks/hooks-catalog.json
```

The catalog ends with `]` closing the array. Add the new entry before the closing `]`.

- [ ] **Step 2: Add observability entry before the closing `]`**

The entry to add (as the last element in the `"catalog"` array, after `cargo-test-on-stop`):

```json
    {
      "id": "observability",
      "description": "Log tool call metadata (relative file path, command name) to .claude/logs/ for harness optimization",
      "requires": "python3",
      "detectBy": {
        "files": [],
        "packageJson": [],
        "binary": "python3"
      },
      "hook": {
        "PostToolUse": [{
          "matcher": "Edit|Write|Bash",
          "hooks": [{"type": "command", "command": "python3 .claude/hooks/observe.py"}]
        }],
        "Stop": [{
          "hooks": [{"type": "command", "command": "find .claude/logs -name '*.jsonl' -mtime +30 -delete 2>/dev/null || true"}]
        }]
      }
    }
```

- [ ] **Step 3: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('plugins/starter/skills/setup-hooks/hooks-catalog.json')); print('valid')"
```

Expected: `valid`

- [ ] **Step 4: Commit**

```bash
git add plugins/starter/skills/setup-hooks/hooks-catalog.json
git commit -m "feat(starter): add observability hook template to hooks-catalog"
```

---

## Task 6: Update init/SKILL.md

Three targeted changes: preview table, Step 5 Tier 3 invocation, starter-context.json schema.

**Files:**
- Modify: `plugins/starter/skills/init/SKILL.md`

- [ ] **Step 1: Add two rows to the Step 4 preview table**

Find the table in Step 4 (the `┌──` table). After the row for `.claude/agents/drift-monitor.md`, add:

```
│ .claude/hooks/observe.py             │ CREATE   │ 3     │
│ .claude/logs/ (.gitignore entry)     │ UPDATE   │ 3     │
```

- [ ] **Step 2: Add setup-observability to Step 5 Tier 3 invocation**

Find the Step 5 Tier 3 block:
```
Tier 3: /shipwithai-starter:setup-agents       (reads: agents_selected, project)
         /shipwithai-starter:setup-ssot --adr --codemaps  (reads: ssot)
```

Change to:
```
Tier 3: /shipwithai-starter:setup-agents       (reads: agents_selected, project)
         /shipwithai-starter:setup-ssot --adr --codemaps  (reads: ssot)
         /shipwithai-starter:setup-observability  (reads: observability)
```

- [ ] **Step 3: Add observability field and bump schema version in Step 4.5**

In the starter-context.json example block, change `"version": "1.1"` to `"version": "1.2"` and add after the `"ssot"` block:

```json
  "observability": {
    "enabled": false
  },
```

Also update the schema version reference in the Update Mode section:

Find:
```
Step 4: Update starter-context.json
        → Merge new answers in
        → Set version to "1.1"
```

Change to:
```
Step 4: Update starter-context.json
        → Merge new answers in
        → Set version to "1.2"
```

And update the schema version list:
```
v1.0: stack, project, architecture, conventions (...), permissions, hooks_selected, mcp_selected, agents_selected, ssot
v1.1: + conventions.workflow_gates
v1.2: + observability.enabled
```

- [ ] **Step 4: Update schema version check in Update Mode**

Find:
```
v1.1: + conventions.workflow_gates
```

Add after it:
```
v1.2: + observability.enabled
```

- [ ] **Step 5: Verify line count is under 500**

```bash
wc -l plugins/starter/skills/init/SKILL.md
```

- [ ] **Step 6: Commit**

```bash
git add plugins/starter/skills/init/SKILL.md
git commit -m "feat(starter): integrate setup-observability into init Tier 3 flow (schema v1.2)"
```

---

## Task 7: Update review/SKILL.md

Add observability health checks to Step 1 (scoring) and Step 3 (report table) and Step 4 (actions).

**Files:**
- Modify: `plugins/starter/skills/review/SKILL.md`

- [ ] **Step 1: Add observability to Step 1 — Score Components**

Find the scoring block (the ``` block listing components). After the `.claude/memory/` line, add:

```
.claude/hooks/observe.py  → present ✅ / missing (Tier 3 item) ❌
.claude/logs/ in .gitignore → in gitignore ✅ / tracked by git ⚠️ / not applicable ✅
```

- [ ] **Step 2: Update schema version check in Step 1**

Find:
```
→ version == "1.1"             → ✅ current
→ version < "1.1" or absent    → ⚠️ outdated (flag with current vs expected)
```

Change to:
```
→ version == "1.2"             → ✅ current
→ version == "1.1"             → ⚠️ outdated — run init --update (adds observability field)
→ version < "1.1" or absent    → ⚠️ outdated — run init --update
```

- [ ] **Step 3: Add observability row to Step 3 — Health Report table**

Find the sample table. After the `.claude/memory/` row, add:

```
| Observability        | ❌     | observe.py not installed (Tier 3 opt-in)   |
```

- [ ] **Step 4: Add observability action to Step 4 — Suggest Actions**

Find the action list in Step 4. After `- SSOT/docs issue → /shipwithai-starter:update-ssot`, add:

```
- Observability missing (Tier 3) → `/shipwithai-starter:setup-observability`
- Logs tracked by git → warn: run `git rm -r --cached .claude/logs/` and add to .gitignore
```

- [ ] **Step 5: Commit**

```bash
git add plugins/starter/skills/review/SKILL.md
git commit -m "feat(starter): add observability health checks to review skill"
```

---

## Task 8: Update manifest.json

**Files:**
- Modify: `plugins/starter/manifest.json`

- [ ] **Step 1: Add setup-observability entry to the skills array**

Add after the `update-ssot` entry:

```json
    {
      "skillId": "setup-observability",
      "name": "setup-observability",
      "description": "Enable tool call logging: installs observe.py hook that writes tool usage metadata to .claude/logs/ for harness optimization. Tier 3 opt-in.",
      "creatorType": "community",
      "updatedAt": "2026-06-01T00:00:00Z",
      "enabled": true
    }
```

- [ ] **Step 2: Update lastUpdated timestamp**

Change `"lastUpdated"` to `1779840000000` (2026-06-01 in epoch ms).

- [ ] **Step 3: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('plugins/starter/manifest.json')); print('valid')"
```

Expected: `valid`

- [ ] **Step 4: Commit**

```bash
git add plugins/starter/manifest.json
git commit -m "feat(starter): register setup-observability in manifest"
```

---

## Task 9: Update CHANGELOG.md and README.md

**Files:**
- Modify: `plugins/starter/CHANGELOG.md`
- Modify: `plugins/starter/README.md`

- [ ] **Step 1: Prepend v2.0.0 entry to CHANGELOG.md**

Add at the top (before the `## [1.2.0]` entry):

```markdown
## [2.0.0] — 2026-06-01

### Added

- `setup-observability` skill — Pillar 7: installs `observe.py` PostToolUse hook that
  logs tool call metadata (tool name, relative file path, command argv[0]) to
  `.claude/logs/YYYY-MM-DD.jsonl`
- `assets/observe.py` — stdlib-only Python hook script; silent-fails to never block
  tool execution; respects `DISABLE_OBSERVE=1` env var for per-session opt-out
- Log rotation via Stop hook: `find .claude/logs -name '*.jsonl' -mtime +30 -delete`
- `init` updated: schema v1.2 adds `observability.enabled` field; Tier 3 flow now
  invokes `setup-observability`; preview table includes observe.py and .gitignore entry
- `review` updated: checks observe.py presence, .claude/logs/ gitignore status,
  schema v1.2 currency; suggests setup-observability for Tier 3 projects
- `hooks-catalog.json` updated: adds observability hook template entry
```

- [ ] **Step 2: Update README.md skill list**

Find the skills table or list in README.md. Add `setup-observability` alongside the other Tier 3 skills with description: "Enable tool call logging for harness optimization (Tier 3 opt-in)".

- [ ] **Step 3: Commit**

```bash
git add plugins/starter/CHANGELOG.md plugins/starter/README.md
git commit -m "docs(starter): update CHANGELOG and README for v2.0.0 observability"
```

---

## Task 10: End-to-End Test on Real Project

Verify the full skill works on an actual project before declaring done.

**Files:** None — test only

- [ ] **Step 1: Install the plugin in a test project**

Use an existing project that has Claude Code set up (e.g., any project on your machine with a `package.json` or `pom.xml`).

- [ ] **Step 2: Run setup-observability**

```
/shipwithai-starter:setup-observability
```

Verify:
- `observe.py` copied to `.claude/hooks/`
- `settings.json` has PostToolUse + Stop hook entries
- `.gitignore` has `.claude/logs/`
- `starter-context.json` has `"observability": {"enabled": true}`

- [ ] **Step 3: Trigger a Claude session with tool use**

Run a simple Claude task that uses Edit or Bash (e.g., "add a comment to README.md").

- [ ] **Step 4: Verify log was written**

```bash
today=$(date +%Y-%m-%d)
cat .claude/logs/${today}.jsonl
```

Expected: one or more JSONL lines with `tool`, `file`/`cmd`, `ts`, `sid` fields.

- [ ] **Step 5: Test DISABLE_OBSERVE opt-out**

```bash
DISABLE_OBSERVE=1 claude --print "add a comment to README.md"
# Verify no new lines were added to today's log
wc -l .claude/logs/${today}.jsonl  # count should not increase
```

- [ ] **Step 6: Test --disable flag**

```
/shipwithai-starter:setup-observability --disable
```

Verify: PostToolUse hook entry removed from `settings.json`, `observability.enabled` set to false, logs preserved.

- [ ] **Step 7: Final commit if any fixes were needed**

```bash
git add -p  # stage only relevant fixes
git commit -m "fix(starter): observability e2e fixes from real project test"
```

---

## Self-Review

**Spec coverage check:**

| PRD requirement | Task covering it |
|---|---|
| `assets/observe.py` hook script | Task 2 |
| `skills/setup-observability/SKILL.md` | Task 3 |
| `skills/setup-observability/evals.json` (5+ prompts) | Task 4 — 6 prompts |
| Add entry to `hooks-catalog.json` | Task 5 |
| `init` Step 4 preview table update | Task 6 Step 1 |
| `init` Step 5 Tier 3 add setup-observability | Task 6 Step 2 |
| `starter-context.json` schema v1.2 | Task 6 Steps 3–4 |
| `review` observability health checks | Task 7 |
| `manifest.json` register new skill | Task 8 |
| CHANGELOG v2.0.0 | Task 9 |
| Per-date log files | observe.py (Task 2) |
| Stop hook rotation | hooks-catalog + setup-observability SKILL.md |
| Privacy: relative paths, argv[0] only | observe.py + tests |
| DISABLE_OBSERVE=1 opt-out | observe.py + SKILL.md |
| Git tracking warning | setup-observability SKILL.md Step 5 + review Task 7 Step 1 |
| 50MB cap | observe.py write_log + test |
| Idempotent skill | setup-observability SKILL.md Write Rules |
| E2E validation | Task 10 |

**Placeholder scan:** No TBDs, TODOs, or "similar to Task N" patterns found.

**Type consistency:** `observe.py` function names (`read_payload`, `build_event`, `write_log`, `main`) used consistently across implementation and tests.
