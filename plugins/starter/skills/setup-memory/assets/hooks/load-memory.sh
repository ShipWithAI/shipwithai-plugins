#!/usr/bin/env bash
# SessionStart hook — inject project memory so Claude can catch up.
# Tiered load: always inject the index + current handoff (cheap),
# then instruct Claude to read only the files listed in the handoff.
#
# Installed by shipwithai-starter /setup-memory (Tier 3). Paths are resolved
# from the project root via $CLAUDE_PROJECT_DIR so the hook works even when the
# session cwd is a subdirectory.
set -euo pipefail

MEM_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/memory"

# Nothing to load yet — stay silent.
[ -d "$MEM_DIR" ] || exit 0

echo "<project-memory>"
echo "Source of truth for project progress (lives in .claude/memory/, version-controlled)."

if [ -f "$MEM_DIR/MEMORY.md" ]; then
  echo
  echo "## Memory Index"
  cat "$MEM_DIR/MEMORY.md"
fi

if [ -f "$MEM_DIR/HANDOFF.md" ]; then
  echo
  echo "## Current Handoff (WIP — latest state)"
  cat "$MEM_DIR/HANDOFF.md"
  echo
  echo "ACTION: Before responding, Read the files listed under \"Context to Load\" in the handoff."
  echo "Only read specific decisions/conventions when the index shows they are relevant — do not load everything."
fi

echo "</project-memory>"
