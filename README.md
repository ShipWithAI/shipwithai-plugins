# shipwithai-plugins

**Production-ready Claude Code plugins for ShipWithAI projects.**

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Plugin Format](https://img.shields.io/badge/claude%20code-plugin-blueviolet)](https://shipwithai.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/ShipWithAI/shipwithai-plugins/issues)

[Website](https://shipwithai.io) · [Report Bug](https://github.com/ShipWithAI/shipwithai-plugins/issues) · [Request Feature](https://github.com/ShipWithAI/shipwithai-plugins/issues)

---

Each plugin in this repo ships as a Claude Code skill set — install once, use via slash command or natural language. No build step, no runtime dependencies.

## Plugins

| Plugin | Skills | What it does |
|--------|--------|-------------|
| [`shipwithai-auth`](plugins/auth/) | `/auth:setup` · `/auth:doctor` | Full auth stack for Next.js: Better Auth or Firebase, Google OAuth, UI pages, middleware, DB schema. Doctor scans 22 checks and reports health. |

## Install

### Via Marketplace (recommended)

Register the ShipWithAI marketplace once, then install any plugin by name:

```bash
# Register the ShipWithAI marketplace (one-time setup)
/plugin marketplace add ShipWithAI/shipwithai-plugins

# Install any plugin by name
/plugin install shipwithai-auth@shipwithai
```

### Via Plugin Directory (local / development)

Clone this repo and point Claude Code at the plugin directory:

```bash
git clone https://github.com/ShipWithAI/shipwithai-plugins.git
claude --plugin-dir ./shipwithai-plugins/plugins/auth
```

### Usage

Once installed, trigger a skill by slash command or describe what you need in chat:

```bash
/shipwithai-auth:setup
# or
> Set up Firebase Auth with Google login for my Next.js app
```

See each plugin's `README.md` for full usage, supported stack, and what gets generated.

## Repository Structure

```
shipwithai-plugins/
├── plugins/
│   └── auth/                   # shipwithai-auth plugin
│       ├── skills/
│       │   ├── auth-setup/     # Setup wizard (SKILL.md + assets + references)
│       │   └── auth-doctor/    # Health scanner (SKILL.md)
│       ├── commands/           # Slash command definitions
│       ├── manifest.json       # Skill registry
│       └── README.md
├── scripts/
│   └── publish-plugin.sh       # Validate and package a plugin for release
├── docs/
│   └── ARCHITECTURE.md
└── CLAUDE.md                   # Authoring conventions for Claude Code
```

No compiled code. All plugin content is Markdown (SKILL.md, references) and JSON (manifest, evals, settings).

## Adding a Plugin

1. Read [`CLAUDE.md`](CLAUDE.md) — authoring conventions and blueprint references are required reading before any work.
2. Create a directory under `plugins/` following the structure above.
3. Add `manifest.json` (skill registry) and `plugin.json` (metadata).
4. Each skill needs a `SKILL.md` (< 500 lines) and `evals/evals.json` (5+ test prompts).
5. Test on two real projects before opening a PR.

## Contributing

Open issues for bugs and feature requests. For new skills or providers, check [open issues](https://github.com/ShipWithAI/shipwithai-plugins/issues) first to avoid duplicate work.

```bash
# Validate and dry-run a plugin before publishing
./scripts/publish-plugin.sh auth --dry-run
```

## License

MIT — see [LICENSE](LICENSE).