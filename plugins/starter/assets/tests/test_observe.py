from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import observe


# ── build_event ──────────────────────────────────────────────────────────────

def test_edit_tool_produces_relative_file_path(tmp_path):
    src = tmp_path / 'src'
    src.mkdir()
    auth = src / 'auth.ts'
    auth.touch()
    payload = {'tool_name': 'Edit', 'tool_input': {'file_path': str(auth)}}
    event = observe.build_event(payload, _project_root=tmp_path.resolve())
    assert event['tool'] == 'Edit'
    assert event['file'] == 'src/auth.ts'


def test_write_tool_produces_relative_file_path(tmp_path):
    out = tmp_path / 'out'
    out.mkdir()
    result = out / 'result.json'
    result.touch()
    payload = {'tool_name': 'Write', 'tool_input': {'file_path': str(result)}}
    event = observe.build_event(payload, _project_root=tmp_path.resolve())
    assert event['file'] == 'out/result.json'


def test_bash_tool_logs_argv0_only():
    payload = {'tool_name': 'Bash', 'tool_input': {'command': 'npm test --coverage --reporter=json'}}
    event = observe.build_event(payload)
    assert event['cmd'] == 'npm'
    assert 'test' not in str(event.get('cmd', ''))


def test_bash_strips_args_containing_secrets():
    payload = {'tool_name': 'Bash', 'tool_input': {'command': 'aws s3 cp file.txt s3://bucket --aws-access-key-id=AKIA123SECRET'}}
    event = observe.build_event(payload)
    assert event['cmd'] == 'aws'
    assert 'AKIA' not in json.dumps(event)


def test_edit_does_not_log_old_or_new_string():
    payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts', 'old_string': 'secret_old', 'new_string': 'secret_new'}}
    event = observe.build_event(payload)
    assert 'secret_old' not in json.dumps(event)
    assert 'secret_new' not in json.dumps(event)


def test_write_does_not_log_content():
    payload = {'tool_name': 'Write', 'tool_input': {'file_path': '/p/f.ts', 'content': 'supersecret content here'}}
    event = observe.build_event(payload)
    assert 'supersecret' not in json.dumps(event)


def test_event_always_has_required_fields():
    payload = {'tool_name': 'Write', 'tool_input': {'file_path': '/p/f.ts'}}
    event = observe.build_event(payload)
    for field in ('ts', 'sid', 'event', 'tool'):
        assert field in event
    assert event['event'] == 'tool'


def test_sid_truncated_to_8_chars():
    payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
    with patch.dict(os.environ, {'CLAUDE_SESSION_ID': 'abc123def456xyz'}):
        event = observe.build_event(payload)
    assert len(event['sid']) == 8


def test_sid_empty_when_no_session_id_env():
    payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_SESSION_ID'}
    with patch.dict(os.environ, env, clear=True):
        event = observe.build_event(payload)
    assert event['sid'] == ''


def test_ts_is_utc_iso8601():
    payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
    event = observe.build_event(payload)
    datetime.datetime.strptime(event['ts'], '%Y-%m-%dT%H:%M:%SZ')
    assert event['ts'].endswith('Z')


def test_tool_name_comes_from_stdin_payload():
    payload = {'tool_name': 'Bash', 'tool_input': {'command': 'make build'}}
    event = observe.build_event(payload)
    assert event['tool'] == 'Bash'


# ── write_log ────────────────────────────────────────────────────────────────

@pytest.fixture
def log_dir(tmp_path):
    ld = tmp_path / 'logs'
    with patch.object(observe, '_LOG_DIR', ld):
        yield ld


def _make_event(tool: str = 'Edit', file: str = 'src/x.ts') -> dict:
    return {'ts': '2026-06-01T10:00:00Z', 'sid': 'a1b2c3d4', 'event': 'tool', 'tool': tool, 'file': file}


def test_creates_log_directory_if_missing(log_dir):
    observe.write_log(_make_event())
    assert log_dir.is_dir()


def test_writes_valid_jsonl_line(log_dir):
    observe.write_log(_make_event())
    today = datetime.date.today().isoformat()
    parsed = json.loads((log_dir / f'{today}.jsonl').read_text(encoding='utf-8').strip())
    assert parsed['tool'] == 'Edit'


def test_appends_multiple_events(log_dir):
    observe.write_log(_make_event(file='a.ts'))
    observe.write_log(_make_event(file='b.ts'))
    today = datetime.date.today().isoformat()
    lines = (log_dir / f'{today}.jsonl').read_text(encoding='utf-8').strip().split('\n')
    assert len(lines) == 2


def test_skips_write_when_over_50mb(log_dir):
    log_dir.mkdir(parents=True)
    (log_dir / 'old.jsonl').write_bytes(b'x' * (51 * 1024 * 1024))
    observe.write_log(_make_event())
    today = datetime.date.today().isoformat()
    assert not (log_dir / f'{today}.jsonl').exists()


def test_log_filename_is_todays_date(log_dir):
    observe.write_log(_make_event())
    today = datetime.date.today().isoformat()
    assert (log_dir / f'{today}.jsonl').exists()


# ── main ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_cwd(tmp_path):
    orig = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(orig)


def test_exits_silently_when_disable_observe_set(log_dir):
    with patch.dict(os.environ, {'DISABLE_OBSERVE': '1'}):
        observe.main(b'{"tool_name":"Edit","tool_input":{"file_path":"/p/f.ts"}}')
    assert not log_dir.exists()


def test_does_not_raise_on_write_error():
    with patch('observe.write_log', side_effect=PermissionError('no write')):
        observe.main(b'{"tool_name":"Edit","tool_input":{"file_path":"/p/f.ts"}}')


def test_skips_when_payload_has_no_tool_name(log_dir):
    observe.main(b'{"tool_input":{}}')
    assert not log_dir.exists()


def test_passthrough_writes_raw_to_stdout():
    import io
    raw = b'{"tool_name":"Edit","tool_input":{"file_path":"/p/f.ts"}}'
    buf = io.BytesIO()
    with patch('sys.stdout') as mock_stdout:
        mock_stdout.buffer = buf
        observe.main(raw)
    buf.seek(0)
    assert buf.read() == raw


def test_passthrough_runs_even_when_disable_observe_set():
    import io
    raw = b'{"tool_name":"Edit","tool_input":{"file_path":"/p/f.ts"}}'
    buf = io.BytesIO()
    with patch.dict(os.environ, {'DISABLE_OBSERVE': '1'}), \
         patch('sys.stdout') as mock_stdout:
        mock_stdout.buffer = buf
        observe.main(raw)
    buf.seek(0)
    assert buf.read() == raw
