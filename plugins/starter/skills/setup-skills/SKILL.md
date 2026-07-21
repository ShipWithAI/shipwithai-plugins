---
name: setup-skills
description: >
  Install reusable project skills into .claude/skills/. Ships git-workflow
  (commit/branch/PR conventions from your init choices).
  Triggers: "setup skills", "install project skills", "add git skill".
argument-hint: "[skill-id]"
---

# /setup-skills

Provisions reusable skills into `.claude/skills/<id>/SKILL.md` for the project.
Sibling of `setup-agents` — same install model, different artifact type.

## Mode Detection

```
Read .claude/starter-context.json if it exists
  → Exists: use skills_selected + conventions + project.name — skip suggestion step
  → Does not exist (standalone): load catalog → detect context → suggest → confirm
```

## Argument Handling

If a skill id is passed directly (e.g. `/setup-skills git-workflow`): skip the
suggestion step and go straight to that catalog entry.

## Step 1 — Context Detection

**Context mode** (`starter-context.json` present): install exactly the ids listed
in `skills_selected` — skip the suggestion logic below. If `skills_selected` is
absent or empty, the user declined skills at init; do not re-suggest. The
`suggestWhen` / `alwaysInclude` evaluation applies to **standalone mode only**.

Load `skills-catalog.json`. For each entry, evaluate `suggestWhen`:

1. **files**: check whether any listed glob exists in the project root
2. **context**: if `starter-context.json` exists, evaluate conditions against its fields
3. **alwaysInclude**: if `true`, suggest unconditionally — present first

`git-workflow` is `alwaysInclude: true` — every project has git.

For each suggested skill: show preview (with resolved variants from Step 2) →
confirm before writing.

## Step 2 — Resolve Conventions

The template adapts to the conventions chosen at init. Resolve these values:

| Token | Source | Fallback |
|-------|--------|----------|
| `COMMIT_BLOCK` | `conventions.commit_format` (`conventional`/`none`/`custom`) | `conventional` |
| `BRANCH_BLOCK` | `conventions.branch_strategy` (`gitflow`/`trunk-based`) | `trunk-based` |
| `PROTECTED_BRANCHES` | derived from `branch_strategy` | from `trunk-based` |
| `PROJECT_NAME` | `project.name` | "this project" |
| `TEMPLATE_VERSION` | catalog entry `version` | (always present) |

**Standalone mode** (no `starter-context.json`): ask only the two convention
questions before injecting — same wording as init Part 3:
- "Branch strategy (trunk-based / gitflow)?"
- "Commit format (conventional / custom / none)?"

Never invent a convention silently — if unknown, ask or use the documented fallback.

## Step 3 — Inject

For each skill to install:

```
1. Read template:  <template> from catalog entry (e.g. templates/git-workflow.SKILL.md.tmpl)
2. Read variants:  <variants> from catalog entry (e.g. templates/git-workflow.variants.json)
3. Pick blocks:
     COMMIT_BLOCK       = variants.commit[commit_format]   (fallback: commit.conventional)
     BRANCH_BLOCK       = variants.branch[branch_strategy]  (fallback: branch.trunk-based)
     PROTECTED_BRANCHES = variants.protected_branches[branch_strategy] (fallback: trunk-based)
4. Substitute every {{TOKEN}} in the template. PROJECT_NAME and TEMPLATE_VERSION
   come from Step 2, not the variants file. Treat PROJECT_NAME as a literal
   single-line string: strip newlines and any YAML control characters
   (`:`, leading `-`, `#`) that could break frontmatter; if it is empty or
   unsafe, fall back to "this project".
5. Validate: no {{...}} tokens remain AND the frontmatter still parses as valid YAML.
```

## Step 4 — Write Rules

- Create `.claude/skills/<id>/` if it does not exist.
- **Collision:** if `.claude/skills/<id>/SKILL.md` already exists → do NOT replace
  silently. Show that it exists and offer **Skip** or **Overwrite**.
- Write the injected content to `.claude/skills/<id>/SKILL.md`.
- The written frontmatter carries `template_version` — this enables `review` to
  detect staleness when the plugin template is later updated.

## Step 5 — Post-Write

1. If `starter-context.json` exists → update `skills_selected` with installed ids.
2. Print: "Installed `<id>`. It loads when you say: [triggers from catalog]."
3. Remind: "Commit `.claude/skills/` so teammates get this skill without the plugin."

## Failure Modes

```
Don't install a git tutorial — git-workflow is project rules only
Don't overwrite an existing skill dir without asking (Skip / Overwrite)
Don't inject conventions you didn't read or confirm — ask in standalone mode
Don't leave any {{TOKEN}} unsubstituted in the written file
Don't widen triggers to bare "git" — keep the catalog's scoped triggers
Don't add the installed skill to the plugin's own manifest.json — it is a project asset
```
