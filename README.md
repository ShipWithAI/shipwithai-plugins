# shipwithai-plugins

**Open-source Claude Code plugins.** Build a real project harness — not another pasted CLAUDE.md.

Install this first: **shipwithai-starter** — CLAUDE.md, permissions, hooks (and more) via a ~5-minute interview.

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/claude%20code-plugin-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![GitHub stars](https://img.shields.io/github/stars/ShipWithAI/shipwithai-plugins?style=social)](https://github.com/ShipWithAI/shipwithai-plugins)

[Website](https://shipwithai.io) · [Issues](https://github.com/ShipWithAI/shipwithai-plugins/issues) · [Claude Code Mastery (free course)](https://github.com/ShipWithAI/claude-code-mastery)

---

## Prerequisites

1. [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and working
2. A project directory you can write to (or an empty folder for greenfield)
3. ~5 minutes for Essential tier (`/shipwithai-starter:init`)

## Install shipwithai-starter (≈5 minutes)

```text
# 1) Register this marketplace once
/plugin marketplace add ShipWithAI/shipwithai-plugins

# 2) Install the hero plugin
/plugin install shipwithai-starter@shipwithai

# 3) Run setup in your project
/shipwithai-starter:init
```

Marketplace name: **`shipwithai`** (see [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)).

### Done when

- [ ] `shipwithai-starter` appears in your Claude Code plugin list / skills
- [ ] After `init`: project has `CLAUDE.md` and/or `.claude/settings.json` (Essential+)
- [ ] You can re-run `/shipwithai-starter:review` to audit the harness

### What you get

- Guided harness setup — tiers: **Essential (~5 min)** / **Standard (~15 min)** / **Full (~30 min)**
- **13 skills** (plugin v2.4.0): `init`, `new-project`, `review`, `update-ssot`, `optimize-harness`, and setup pillars (memory, permissions, hooks, MCP, agents, SSOT, observability, skills)
- MIT, no build step, no runtime dependency — Markdown + JSON skills Claude Code loads directly

---

## Plugins on this branch (`main`)

Truth source: `plugins/*` tree + [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) on **default branch**.

| Plugin | In tree | Marketplace (`@shipwithai`) | Role | Skills | Install target |
|--------|:-------:|:---------------------------:|------|-------:|----------------|
| **[`shipwithai-starter`](plugins/starter/)** (v2.4.0) | ✅ | ✅ listed | **Start here** — harness for any project | 13 | `shipwithai-starter@shipwithai` |
| [`shipwithai-auth`](plugins/auth/) (v1.7.1) | ✅ | ✅ listed | Next.js auth (Better Auth / Firebase) | 2 | `shipwithai-auth@shipwithai` |
| [`shipwithai-harness`](plugins/harness/) (v2.0.0) | ✅ | ✅ listed | Auto-detect stack → harness generator | 2 | `shipwithai-harness@shipwithai` |
| [`shipwithai-java-backend-toolkit`](plugins/java-backend-toolkit/) (v0.5.0) | ✅ | ❌ **not listed** | Spring Boot + JPA guardrails + reviewer | 11 + agent | local `--plugin-dir` only (below) |
| `shipwithai-design-toolkit` (v0.7.3) | ❌ external | ✅ listed | Design system governance | — | `shipwithai-design-toolkit@shipwithai` (external: `MangalaHQ/shipwithai-design-toolkit`) |

**Not on `main`:** `mobile-ui-harness` and other WIP plugins may exist on other branches; they are not installable from this default-branch marketplace until merged here.

> Note: marketplace metadata currently lists `shipwithai-starter` as `1.0.0` while `plugins/starter` is **2.4.0**. Install still pulls the monorepo source path `./plugins/starter`. Syncing the marketplace version field is a separate packaging task.

### Secondary plugins (after starter)

| Plugin | One-liner | Slash commands |
|--------|-----------|----------------|
| **auth** | Production auth for Next.js — Better Auth or Firebase, OAuth, UI, schema. | `/shipwithai-auth:setup` · `/shipwithai-auth:doctor` |
| **harness** | Scan project → CLAUDE.md, settings, safety hooks (Next.js / Laravel / Spring Boot and more). | `/shipwithai-harness:setup` · `/shipwithai-harness:doctor` |
| **java-backend-toolkit** | Hooks catch broken `@Transactional` proxies, missing `@Version`, N+1, query injection as you type. | via local plugin load (not in marketplace yet) |
| **design-toolkit** | Spec-first design governance (external repo wired in marketplace). | after marketplace install |

---

## Dogfood

We dogfood these plugins on real ShipWithAI / Mangala work. Source is readable Markdown and JSON before you run anything.

---

## Links

- Site: [shipwithai.io](https://shipwithai.io)
- Free course: [Claude Code Mastery](https://github.com/ShipWithAI/claude-code-mastery) (~86★) — learn the workflow, then install plugins here
- Bugs / features: [GitHub Issues](https://github.com/ShipWithAI/shipwithai-plugins/issues)
- Authoring conventions: [`CLAUDE.md`](CLAUDE.md) · architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Install other plugins (after starter)

After the marketplace is registered (step 1 above):

```text
/plugin install shipwithai-auth@shipwithai
/plugin install shipwithai-harness@shipwithai
/plugin install shipwithai-design-toolkit@shipwithai
```

### Java backend toolkit (local only on `main`)

Present under [`plugins/java-backend-toolkit/`](plugins/java-backend-toolkit/) but **not** in `marketplace.json`. Use a local path:

```bash
git clone https://github.com/ShipWithAI/shipwithai-plugins.git
claude --plugin-dir ./shipwithai-plugins/plugins/java-backend-toolkit
```

### Local / development install (any in-tree plugin)

```bash
git clone https://github.com/ShipWithAI/shipwithai-plugins.git
claude --plugin-dir ./shipwithai-plugins/plugins/starter
# or: plugins/auth | plugins/harness | plugins/java-backend-toolkit
```

---

## Repository structure (`main`)

```
shipwithai-plugins/
├── plugins/
│   ├── starter/                 # shipwithai-starter v2.4.0 (marketplace)
│   ├── auth/                    # shipwithai-auth v1.7.1 (marketplace)
│   ├── harness/                 # shipwithai-harness v2.0.0 (marketplace)
│   └── java-backend-toolkit/    # v0.5.0 (in tree, not marketplace)
├── .claude-plugin/
│   └── marketplace.json         # name: shipwithai — starter, auth, design-toolkit, harness
├── docs/
├── scripts/publish-plugin.sh
└── CLAUDE.md
```

No compiled code. Plugin content is Markdown (`SKILL.md`, references) and JSON (manifest, evals, settings).

---

## Troubleshooting

- **Marketplace add fails** — update Claude Code; check network / git access to GitHub
- **Skill not found** — use the full slash with plugin prefix: `/shipwithai-starter:init` (not `/starter:init`)
- **Permission denied writing `.claude/`** — run init inside a project directory you can write to
- **Java plugin not found via marketplace** — expected on `main`; use `--plugin-dir` until it is listed in `marketplace.json`

---

## Contributing

Open issues for bugs and feature requests. For new skills or providers, check [open issues](https://github.com/ShipWithAI/shipwithai-plugins/issues) first.

1. Read [`CLAUDE.md`](CLAUDE.md) before authoring plugins.
2. Add a directory under `plugins/` with `plugin.json` / `manifest.json`, skills (`SKILL.md` + evals).
3. If the plugin should be marketplace-installable, add it to [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) and keep versions honest.
4. Test on two real projects before opening a PR.

```bash
./scripts/publish-plugin.sh starter --dry-run
```

## License

MIT — see [LICENSE](LICENSE).
