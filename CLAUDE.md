# shipwithai-plugins

> Repository for developing and maintaining Claude Code plugins for the ShipWithAI ecosystem. Stack: none (plugin authoring workspace). Last updated: 2026-05-19.

## Commands

No build/test commands — this is a content-only workspace. Plugin files are SKILL.md, manifest.json, and reference assets consumed by Claude Code.

## Architecture

The repository is the canonical source for ShipWithAI Claude Code plugins. Each plugin lives in its own directory under the root and follows the structure defined in the plugin blueprint standard. Plugin directories contain `skills/`, `assets/`, `references/`, `evals/`, `manifest.json`, and `plugin.json`.

## Workflow

- **New plugin/skill:** Read `plugin-blueprint-standard.md` and `plugin-blueprint-advanced.md` from the blueprint path before any work. Create `PLAN.md` and wait for approval before writing files.
- **Updating existing plugin:** Read `UPDATE-WORKFLOW.md` from the blueprint path. Audit all SKILL.md files and manifest before proposing changes.
- **Never** create or modify skills without an approved plan.

## Conventions

- Skill directories: lowercase with dashes (e.g. `auth-setup`)
- SKILL.md: always uppercase filename
- Reference files: lowercase with dashes
- Every skill needs `evals/evals.json` with 5+ test prompts
- SKILL.md hard cap: 500 lines (ideal < 300)
- Skill descriptions: < 200 characters, include trigger phrases
- Test every skill on 2+ real projects before shipping