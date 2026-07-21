#!/usr/bin/env python3
"""jpa-guardrail.py — Spring Boot + JPA guardrail hook for shipwithai-java-backend-toolkit.

PostToolUse hook for Edit/Write on *.java files. Reads the just-written file,
runs the heuristic checks defined in rules/ruleset.json, and emits just-in-time
advisories back to Claude. Rules listed in guardrails-config.json `strictChecks`
(and marked strictEligible) BLOCK with exit 2; everything else advises (exit 0).

Silent-fails on any error — never breaks tool execution. Stdlib only.

Install target (in the user's project): .claude/hooks/jpa-guardrail.py
Reads ruleset.json + guardrails-config.json from the same hooks/ directory.

Escape hatch: `// jbt:ignore <rule-id>` suppresses one rule for a file;
`// jbt:ignore-all` skips the file entirely.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

_HOOK_FILE = pathlib.Path(__file__).resolve()
_CONFIG_PATH = _HOOK_FILE.parent / "guardrails-config.json"

# ruleset.json is the SSOT shared with the reviewer agent. In the plugin source it
# lives in ../rules/; when setup installs the hook it is copied flat into the same
# dir. Search both so the hook works in source and installed layouts.
_RULESET_CANDIDATES = (
    _HOOK_FILE.parent / "ruleset.json",
    _HOOK_FILE.parent.parent / "rules" / "ruleset.json",
)

_FLAG_MAP = {"m": re.MULTILINE, "s": re.DOTALL, "i": re.IGNORECASE, "x": re.VERBOSE}


def ruleset_path() -> pathlib.Path:
    """First existing ruleset.json candidate (installed-flat, then source layout)."""
    for path in _RULESET_CANDIDATES:
        if path.is_file():
            return path
    return _RULESET_CANDIDATES[0]


def parse_flags(flags: str) -> int:
    """Translate a flag string like 'mi' into a combined re flag int."""
    result = 0
    for ch in flags or "":
        result |= _FLAG_MAP.get(ch, 0)
    return result


def load_json(path: pathlib.Path) -> dict:
    """Load a JSON file, returning {} on any failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def collect_ignores(content: str) -> tuple[set[str], bool]:
    """Return (set of rule-ids to ignore, ignore_all flag) from inline markers."""
    if re.search(r"//\s*jbt:ignore-all\b", content):
        return set(), True
    ids = set(re.findall(r"//\s*jbt:ignore\s+([\w-]+)", content))
    return ids, False


def rule_matches(content: str, match: dict) -> bool:
    """Evaluate a single rule's match spec against file content."""
    strategy = match.get("strategy", "")

    if strategy == "file-has-without":
        has = match.get("has", [])
        without = match.get("without", [])
        if not all(re.search(p, content) for p in has):
            return False
        if any(re.search(p, content) for p in without):
            return False
        return True

    if strategy == "regex":
        pattern = match.get("pattern", "")
        if not pattern:
            return False
        return re.search(pattern, content, parse_flags(match.get("flags", ""))) is not None

    # 'reviewer-only' and unknown strategies are not evaluated by the hook.
    return False


def evaluate(content: str, ruleset: dict, config: dict) -> tuple[list[dict], list[dict]]:
    """Return (advisories, strict_hits) for the given file content.

    advisories: rules that matched and should be surfaced as reminders.
    strict_hits: subset that should block (in strictChecks and strictEligible).
    """
    ignored, ignore_all = collect_ignores(content)
    if ignore_all:
        return [], []

    disabled = set(config.get("disabledChecks", []))
    strict = set(config.get("strictChecks", []))

    advisories: list[dict] = []
    strict_hits: list[dict] = []

    for rule in ruleset.get("rules", []):
        rid = rule.get("id", "")
        if not rule.get("hookEnabled"):
            continue
        if rid in disabled or rid in ignored:
            continue
        if not rule_matches(content, rule.get("match", {})):
            continue

        if rid in strict and rule.get("strictEligible"):
            strict_hits.append(rule)
        else:
            advisories.append(rule)

    return advisories, strict_hits


def format_block(rules: list[dict], header: str) -> str:
    """Render matched rules into a readable advisory block."""
    lines = [header]
    for r in rules:
        lines.append(f"\n• [{r.get('id')}] {r.get('title')}")
        lines.append(f"  {r.get('advisory')}")
        if r.get("fixHint"):
            lines.append(f"  Fix: {r.get('fixHint')}")
    lines.append("\n(Suppress a check with `// jbt:ignore <rule-id>` if intentional.)")
    return "\n".join(lines)


def is_scannable(file_path: str) -> bool:
    """True for Java sources and Spring config files the rules apply to.

    Covers `*.java` plus Spring config whose basename starts with `application`
    and ends with `.properties`, `.yml`, or `.yaml` (e.g. `application-prod.properties`).
    """
    if file_path.endswith(".java"):
        return True
    name = pathlib.PurePath(file_path).name
    return name.startswith("application") and name.endswith(
        (".properties", ".yml", ".yaml")
    )


def read_target(payload: dict, max_bytes: int) -> str | None:
    """Resolve the edited file content, or None if it should be skipped."""
    tool = payload.get("tool_name", "")
    if tool not in ("Edit", "Write"):
        return None

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not is_scannable(file_path):
        return None

    path = pathlib.Path(file_path)
    try:
        if path.is_file():
            if path.stat().st_size > max_bytes:
                return None
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Fallback (e.g. file not yet on disk): use the write payload directly.
    content = tool_input.get("content")
    if isinstance(content, str) and len(content.encode("utf-8")) <= max_bytes:
        return content
    return None


def emit_advisory(text: str) -> None:
    """Surface non-blocking context back to Claude via PostToolUse JSON output."""
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": text,
        }
    }
    print(json.dumps(out))


def run(payload: dict) -> int:
    """Core logic. Returns the intended exit code."""
    config = load_json(_CONFIG_PATH)
    if not config.get("enabled", True):
        return 0

    ruleset = load_json(ruleset_path())
    if not ruleset.get("rules"):
        return 0

    content = read_target(payload, int(config.get("maxFileBytes", 200000)))
    if content is None:
        return 0

    advisories, strict_hits = evaluate(content, ruleset, config)

    if strict_hits:
        block = format_block(strict_hits, "🚫 Spring Boot guardrail (blocking):")
        if advisories:
            block += "\n\n" + format_block(advisories, "Additional advisories:")
        print(block, file=sys.stderr)
        return 2

    if advisories:
        emit_advisory(format_block(advisories, "⚠️ Spring Boot guardrail:"))
    return 0


def main(stdin_bytes: bytes | None = None) -> int:
    """Entry point. stdin_bytes is injectable for testing."""
    raw = stdin_bytes if stdin_bytes is not None else sys.stdin.buffer.read()
    try:
        payload = json.loads(raw) if raw and raw.strip() else {}
    except Exception:
        return 0
    try:
        return run(payload)
    except Exception:
        return 0  # Silent-fail — never block tool execution.


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
