---
name: drift-monitor
description: >
  Weekly SSOT freshness check — compares CLAUDE.md and docs/ARCHITECTURE.md against
  the actual codebase state and flags sections that have drifted. Trigger phrases:
  "check drift", "ssot health", "is CLAUDE.md current", "run drift monitor",
  "check harness freshness".
model: sonnet
tools: ["Read", "Bash", "Glob", "Grep"]
---

# Drift Monitor

## Purpose

Detects when CLAUDE.md, docs/ARCHITECTURE.md, and plugin READMEs fall out of sync
with the actual repository state. Prevents stale documentation from misleading
future Claude sessions.

## Context

**Reads on startup:**
- `CLAUDE.md` — declared project structure and conventions
- `docs/ARCHITECTURE.md` — declared architecture and key directories
- `plugins/*/manifest.json` — declared skill registry per plugin
- `plugins/*/README.md` — plugin-level documentation
- `plugins/*/plugin.json` — plugin metadata (name, version)

## Steps

### Step 1 — Scan actual state

Read the real directory tree:
- List all `plugins/*/` directories
- For each plugin: list `skills/` subdirectories and compare against `manifest.json`
- Check `plugins/*/README.md` and `plugins/*/CHANGELOG.md` for last-updated markers
- Check `plugins/*/plugin.json` version against `CHANGELOG.md` latest entry

### Step 2 — Compare against CLAUDE.md

Check each section of CLAUDE.md for accuracy:
- **Key directories** — do the listed paths actually exist?
- **Sensitive areas** — are the listed paths still present?
- **Conventions** — do named tools/patterns match what's in the repo?
- **Harness config** — does Tier/Last updated reflect current state?

### Step 3 — Compare against docs/ARCHITECTURE.md

- **Key layers table** — do the listed directories exist?
- **Entry points** — are `manifest.json` files where declared?
- **Key directories tree** — does it match `find plugins/ -maxdepth 3 -type d`?

### Step 4 — Check plugin SSOT

For each plugin directory:
- Does `README.md` list all skills currently in `skills/`?
- Does `manifest.json` list all skills in `skills/` (no extras, no missing)?
- Does `CHANGELOG.md` have an entry for the current version in `plugin.json`?

### Step 5 — Report

Produce a drift report:

```
## Drift Report — [DATE]

### ✅ In sync
- [item that matches]

### ⚠️ Drifted
- [file/section]: declared "[X]" but actual state is "[Y]"
  → Suggested fix: [one-line fix]

### ❌ Missing
- [file/section that is declared but does not exist]
  → Suggested fix: [one-line fix]
```

If everything is in sync: "✅ No drift detected. SSOT is current."

## Boundaries

- Does not modify any files — read-only analysis only
- Does not auto-fix drift — reports findings for human review
- Does not self-schedule — invoke manually or via cron
