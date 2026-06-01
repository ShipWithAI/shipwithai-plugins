import datetime
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import observe


class TestBuildEvent(unittest.TestCase):

    def test_edit_tool_produces_relative_file_path(self):
        payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/project/src/auth.ts'}}
        with patch('os.getcwd', return_value='/project'):
            event = observe.build_event(payload)
        self.assertEqual(event['tool'], 'Edit')
        self.assertEqual(event['file'], 'src/auth.ts')

    def test_write_tool_produces_relative_file_path(self):
        payload = {'tool_name': 'Write', 'tool_input': {'file_path': '/project/out/result.json'}}
        with patch('os.getcwd', return_value='/project'):
            event = observe.build_event(payload)
        self.assertEqual(event['file'], 'out/result.json')

    def test_bash_tool_logs_argv0_only(self):
        payload = {'tool_name': 'Bash', 'tool_input': {'command': 'npm test --coverage --reporter=json'}}
        event = observe.build_event(payload)
        self.assertEqual(event['cmd'], 'npm')
        self.assertNotIn('test', str(event.get('cmd', '')))

    def test_bash_strips_args_containing_secrets(self):
        payload = {'tool_name': 'Bash', 'tool_input': {'command': 'aws s3 cp file.txt s3://bucket --aws-access-key-id=AKIA123SECRET'}}
        event = observe.build_event(payload)
        self.assertEqual(event['cmd'], 'aws')
        self.assertNotIn('AKIA', json.dumps(event))

    def test_edit_does_not_log_old_or_new_string(self):
        payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts', 'old_string': 'secret_old', 'new_string': 'secret_new'}}
        with patch('os.getcwd', return_value='/p'):
            event = observe.build_event(payload)
        self.assertNotIn('secret_old', json.dumps(event))
        self.assertNotIn('secret_new', json.dumps(event))

    def test_write_does_not_log_content(self):
        payload = {'tool_name': 'Write', 'tool_input': {'file_path': '/p/f.ts', 'content': 'supersecret content here'}}
        with patch('os.getcwd', return_value='/p'):
            event = observe.build_event(payload)
        self.assertNotIn('supersecret', json.dumps(event))

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

    def test_sid_empty_when_no_session_id_env(self):
        payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
        env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_SESSION_ID'}
        with patch('os.getcwd', return_value='/p'), patch.dict(os.environ, env, clear=True):
            event = observe.build_event(payload)
        self.assertEqual(event['sid'], '')

    def test_ts_is_utc_iso8601(self):
        payload = {'tool_name': 'Edit', 'tool_input': {'file_path': '/p/f.ts'}}
        with patch('os.getcwd', return_value='/p'):
            event = observe.build_event(payload)
        datetime.datetime.strptime(event['ts'], '%Y-%m-%dT%H:%M:%SZ')
        self.assertTrue(event['ts'].endswith('Z'))

    def test_tool_name_comes_from_stdin_payload(self):
        payload = {'tool_name': 'Bash', 'tool_input': {'command': 'make build'}}
        event = observe.build_event(payload)
        self.assertEqual(event['tool'], 'Bash')


class TestWriteLog(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)

    def _make_event(self, tool='Edit', file='src/x.ts'):
        return {'ts': '2026-06-01T10:00:00Z', 'sid': 'a1b2c3d4', 'event': 'tool', 'tool': tool, 'file': file}

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
            observe.main(b'{"tool_name":"Edit","tool_input":{"file_path":"/p/f.ts"}}')
        self.assertFalse(Path('.claude/logs').exists())

    def test_does_not_raise_on_write_error(self):
        with patch('observe.write_log', side_effect=PermissionError('no write')), \
             patch('os.getcwd', return_value='/p'):
            observe.main(b'{"tool_name":"Edit","tool_input":{"file_path":"/p/f.ts"}}')

    def test_skips_when_payload_has_no_tool_name(self):
        observe.main(b'{"tool_input":{}}')
        self.assertFalse(Path('.claude/logs').exists())


if __name__ == '__main__':
    unittest.main()
