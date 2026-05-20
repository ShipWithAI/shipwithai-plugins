# Architecture — shipwithai-plugins

## Overview

Content-only plugin authoring workspace. No compiled code, no runtime, no package manager.
All artifacts are Markdown (SKILL.md, references), JSON (manifest, evals, settings), and Python hooks.

## Stack

- Plugin format: ShipWithAI Claude Code plugin standard
- Authoring language: Markdown + JSON
- Safety hooks: Python 3 (stdlib only)
- Version control: Git

## Directory Map

```
shipwithai-plugins/
├── <plugin-name>/          # One directory per plugin
│   ├── skills/             # One subdirectory per skill (SKILL.md + assets)
│   │   └── <skill-name>/
│   │       ├── SKILL.md
│   │       ├── assets/     # Templates, code snippets, static files
│   │       ├── references/ # Lazy-loaded reference docs (< 300 lines each)
│   │       └── evals/      # evals.json with 5+ test prompts
│   ├── manifest.json       # Skill registry for this plugin
│   └── plugin.json         # Plugin metadata (name, version, description)
├── .claude/
│   ├── settings.json       # Permission rules + safety hooks
│   └── hooks/              # validate-command.py, protect-files.py
├── docs/
│   └── ARCHITECTURE.md     # This file
└── CLAUDE.md               # Harness instructions for Claude Code
```

## Entry Points

No runtime entry point. Claude Code loads plugins via the manifest.json registry.

## Data Layer

None. All data is static files read by Claude Code at session start or on-demand via skills.