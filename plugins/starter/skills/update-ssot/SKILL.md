---
name: update-ssot
description: >
  Sync CLAUDE.md and architecture docs with the current state of the codebase.
  Use after significant changes: new dependencies, refactoring, architecture shifts.
  Trigger phrases: "update CLAUDE.md", "sync docs", "CLAUDE.md is outdated",
  "update architecture docs", "sync ssot".
argument-hint: "[--section stack|architecture|conventions|hooks|mcp|all]"
---

# /update-ssot

Sync SSOT docs with the actual codebase. Section by section, confirm each change.

## Flag Handling

- `--section stack` — diff and update tech stack section only
- `--section architecture` — diff and update architecture/directories sections only
- `--section conventions` — diff and update coding conventions section only
- `--section hooks` — diff `.claude/settings.json` hooks vs CLAUDE.md only
- `--section mcp` — diff `.mcp.json` vs CLAUDE.md only
- `--section all` — default: diff everything
- Flags can be combined: `--section stack --section mcp`

## Pre-flight Check

Before diffing, check which SSOT files exist:

- `CLAUDE.md` not found → inform user, suggest running `/shipwithai-starter:setup-ssot` first, offer to continue anyway
- `docs/architecture.md` found → include in diff scope
- `docs/CODEMAPS/overview.md` found → include directories in diff scope

## Step 1 — Diff SSOT vs Codebase

Run only the sections relevant to the `--section` flag (or all if `--section all`):

```
CLAUDE.md tech stack        ←→  package.json / pyproject.toml / go.mod / Cargo.toml
CLAUDE.md key directories   ←→  actual directory tree (depth 3)
CLAUDE.md build/test tools  ←→  Makefile / scripts section of package.json / config files
CLAUDE.md hooks section     ←→  .claude/settings.json hooks
CLAUDE.md MCP section       ←→  .mcp.json mcpServers

docs/architecture.md layers ←→  actual src/ structure       (if file exists)
docs/CODEMAPS/overview.md   ←→  actual key directories      (if file exists)
```

## Step 2 — Report Differences

Use consistent tags. Report all differences before asking to update anything:

```
Found N differences:

[STACK]    package.json has @tanstack/react-query 5 — not mentioned in CLAUDE.md
[DIR]      src/workers/ exists — not documented in architecture section
[REMOVED]  .eslintrc.json deleted — still mentioned in CLAUDE.md
[MCP]      .mcp.json has Sentry server — not listed in CLAUDE.md
[ARCH]     docs/architecture.md lists src/legacy/ — directory no longer exists
```

If no differences found: report "SSOT is up to date — no changes needed" and stop.

## Step 3 — Update Section by Section

For each difference, show current vs proposed and ask to confirm:

```
Section: Tech stack
Current:  "Framework: Next.js 14"
Proposed: "Framework: Next.js 15, @tanstack/react-query 5"

Update? [Yes / Skip / Suggest edit]
```

- **Yes**: apply the proposed change
- **Skip**: leave untouched, move to next difference
- **Suggest edit**: user provides the exact text to write instead

Wait for a response before moving to the next difference. Do not batch-update.

## Step 4 — Update Timestamp

After at least one section is updated: set `**Last updated:** YYYY-MM-DD` in the
CLAUDE.md harness config section using today's date in ISO 8601 format.

Do not update the timestamp if the user skipped all changes.

## Failure Modes

- Do not update sections the user has not confirmed
- Do not remove information without asking — it may be intentional
- Do not interpret what a change *means* — describe what you observe
  (e.g. "dependency added" not "team switched to React Query for data fetching")
- Do not update `docs/architecture.md` or `docs/CODEMAPS/` without surfacing the
  diff to the user first, same as CLAUDE.md sections
