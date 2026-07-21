#!/usr/bin/env bash
# Stop hook — nudge Claude to distill memory before the session ends.
# Fires AT MOST ONCE per session, and only when there is real uncommitted
# work outside the memory dir. Guarded against the Stop-hook loop.
#
# Installed by shipwithai-starter /setup-memory (Tier 3). Disable by removing
# this hook's entry from .claude/settings.json (the SessionStart load hook can
# stay — only this save-nudge is opinionated).
set -euo pipefail

input="$(cat)"

# Avoid infinite loop: if this Stop was already triggered by us, allow it.
active="$(printf '%s' "$input" | python3 -c "import sys,json;print(json.load(sys.stdin).get('stop_hook_active',False))" 2>/dev/null || echo False)"
[ "$active" = "True" ] && exit 0

sid="$(printf '%s' "$input" | python3 -c "import sys,json;print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null || echo unknown)"
flag="${TMPDIR:-/tmp}/claude-save-reminded-${sid}"

# Already reminded this session — don't nag again.
[ -f "$flag" ] && exit 0

# Any uncommitted change outside .claude/memory/ ? (real work worth saving)
changes="$(git status --porcelain 2>/dev/null | grep -v '\.claude/memory/' | head -1 || true)"
[ -z "$changes" ] && exit 0

touch "$flag"

cat <<'EOF'
{"decision":"block","reason":"This session made changes. Before ending, run the /save-memory skill to distill decisions, conventions, HANDOFF (WIP) and a session summary into .claude/memory/ so the next session can catch up. If nothing is worth saving, say so briefly and stop."}
EOF
