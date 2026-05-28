# ADR-0001: Initial Architecture — Content-Only Plugin Monorepo

**Date:** 2026-05-28
**Status:** Accepted
**Deciders:** Leonard Trinh

---

## Context

shipwithai-plugins needs a structure to house multiple Claude Code plugins (auth, starter, etc.)
that are authored and published independently but maintained in a single repository.
Each plugin is a collection of SKILL.md files, JSON manifests, and reference assets —
there is no compiled code, no runtime, and no package manager.

---

## Options Considered

### Option A: Monorepo — one directory per plugin (chosen)

Each plugin lives under `plugins/<plugin-name>/` with its own `manifest.json`,
`plugin.json`, `skills/`, `CHANGELOG.md`, and `README.md`.

**Pros:**
- Single repo to clone, review, and maintain
- Shared `.claude/` harness (settings, hooks, agents) across all plugins
- Easy to cross-reference skills and spot conventions drift
- One CI/CD pipeline for all plugins

**Cons:**
- Releasing one plugin requires tagging in a shared repo
- Contributors touching one plugin see unrelated changes in history

### Option B: One repo per plugin

Each plugin has its own GitHub repository.

**Pros:**
- Independent release cycles and issue trackers
- Clean git history per plugin

**Cons:**
- Duplicated harness config (settings, hooks, CLAUDE.md) across repos
- Harder to enforce consistent conventions
- More overhead for a solo maintainer

---

## Decision

We chose Option A (monorepo) because the project is solo-maintained and the benefits of
shared harness config, unified conventions enforcement, and simpler tooling outweigh the
downsides of a shared release history.

---

## Consequences

**Positive:**
- Single CLAUDE.md and `.claude/settings.json` govern all plugins
- drift-monitor agent checks all plugins in one pass
- One `scripts/publish-plugin.sh` handles all releases

**Negative / Risks:**
- As the plugin count grows, release tagging strategy will need formalization
- Contributors must understand that `plugins/auth/` and `plugins/starter/` are independent products sharing one repo

**Follow-up actions:**
- [ ] Define release tagging convention (e.g. `starter-v1.0.0`, `auth-v1.0.0`)
- [ ] Add GitHub Actions workflow to validate plugin structure on PR
- [ ] Add Telegram notification on release tag push to main
