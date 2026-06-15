# setup-skills Skill — Implementation Spec
> Version target: 2.2.0 (Skills Provisioning)
> Target plugin: `plugins/starter/`
> Status: Draft — pending approval
> Flagship installable skill: `git-workflow`

---

## 1. Scope & Positioning

`setup-skills` is a **pillar installer skill** that provisions reusable
project-level skills into the user's `.claude/skills/` directory. It is the
direct sibling of `setup-agents` — same install model, different artifact type.

**The asymmetry it closes:**

| Capability | Provisioned into project today? | Mechanism |
|------------|--------------------------------|-----------|
| Agents     | ✅ `.claude/agents/*.md`        | `setup-agents` + `agents-catalog.json` |
| Hooks      | ✅ `.claude/settings.json`      | `setup-hooks` + `hooks-catalog.json` |
| MCP        | ✅ `.mcp.json`                  | `setup-mcp` + `mcp-registry.json` |
| **Skills** | ❌ — none                       | **`setup-skills` + `skills-catalog.json`** (this spec) |

**Why a skill, not CLAUDE.md, not an agent:**
- **vs CLAUDE.md** — CLAUDE.md is always-loaded (token cost every turn). Detailed
  procedural git knowledge (message structure, branch naming, PR steps) is needed
  only when the user actually touches git. A skill is lazy-loaded on trigger →
  progressive disclosure. CLAUDE.md keeps the 2-line summary; the skill holds the HOW.
- **vs agent** — commit / branch / PR are actions the **main agent performs inline**
  during normal work, not delegated background tasks. Skills load into the main
  conversation; agents run in isolated sub-contexts. `pr-review` (an agent) already
  exists for the delegated case; `git-workflow` (a skill) is the inline case.

**The unique value (why it belongs in starter, not a generic git plugin):**
The installed skill is **generated to match the conventions the user chose at
`init`** (`conventions.commit_format`, `conventions.branch_strategy`). A teammate
who clones the repo gets a git skill that already encodes *this project's* rules —
even if they never installed `shipwithai-starter`. This is the same "commit these
files → team shares the harness" value prop as agents/hooks (`README.md:71`).

**Non-goals:**
- NOT a git tutorial. The skill encodes *this project's rules*, not how git works.
- NOT a runtime "do the commit for me" command. The skill is reference the main
  agent applies; it does not replace built-in commit behavior.
- NOT installing third-party skills from the network. Catalog is curated, shipped
  with the plugin.

---

## 2. Install Model — mirror `setup-agents`

`setup-skills` copies a **template** from the plugin into the project and injects
a small number of convention values. Reuse the exact orchestration shape of
`setup-agents/SKILL.md`:

```
Read .claude/starter-context.json if it exists
  → Exists: use fields skills_selected, conventions, project.* — skip suggest
  → Does not exist (standalone): load catalog → detect context → suggest → confirm
```

| `setup-agents` behavior | `setup-skills` equivalent |
|-------------------------|---------------------------|
| Mode detection from `starter-context.json` (`setup-agents/SKILL.md:16`) | identical, reads `skills_selected` |
| `suggestWhen` evaluation (`:29`) | identical |
| Preview → confirm before writing (`:40`) | identical |
| Check file exists → skip/overwrite, never silent (`:118`) | check skill **dir** exists |
| Post-write: update `skills_selected` in context (`:124`) | identical |

**Difference from agents:** agents are *synthesized from catalog metadata* (the
file is built field-by-field). Skills are larger and authored → use the
**template + inject** approach (like `assets/observe.py` copied verbatim by
`setup-observability/SKILL.md:42`), NOT field synthesis.

---

## 3. Install Target & Mechanism

### Write target
```
.claude/skills/<skill-id>/SKILL.md
```
One directory per installed skill. (Future: a skill may ship `references/` too —
out of scope for v2.2.0; `git-workflow` is single-file.)

### Template source (shipped with plugin, co-located with the skill)
```
plugins/starter/skills/setup-skills/templates/<skill-id>.SKILL.md.tmpl
```

### Injection
The template contains `{{TOKEN}}` placeholders. `setup-skills` reads
`conventions` from `starter-context.json` and substitutes. Unknown/absent
conventions fall back to a documented default (see §6).

| Token | Source field | Fallback |
|-------|--------------|----------|
| `{{COMMIT_BLOCK}}` | `conventions.commit_format` | `conventional` |
| `{{BRANCH_BLOCK}}` | `conventions.branch_strategy` | `trunk-based` |
| `{{PROJECT_NAME}}` | `project.name` | "this project" |
| `{{TEMPLATE_VERSION}}` | catalog entry `version` | n/a (always present) |

Standalone mode (no context file): ask the two convention questions inline
(same wording as `init` Part 3, `init/SKILL.md:163-164`) before injecting.

---

## 4. skills-catalog.json Schema

File: `plugins/starter/skills/setup-skills/skills-catalog.json`

```json
{
  "schema": "1.0",
  "catalog": [
    {
      "id": "git-workflow",
      "name": "git-workflow",
      "description": "Project git conventions — commit message format, branch naming, PR flow",
      "template": "templates/git-workflow.SKILL.md.tmpl",
      "version": "1.0.0",
      "injects": ["COMMIT_BLOCK", "BRANCH_BLOCK", "PROJECT_NAME"],
      "alwaysInclude": true,
      "suggestWhen": {
        "files": [".git/"],
        "context": []
      },
      "triggers": ["commit", "create branch", "open PR", "git workflow"]
    }
  ]
}
```

Field semantics match `agents-catalog.json` where shared (`alwaysInclude`,
`suggestWhen.files`, `suggestWhen.context`). New fields: `template`, `version`,
`injects`, `triggers`.

`git-workflow` is `alwaysInclude: true` — every project has git. `suggestWhen.files`
includes `.git/` as a belt-and-suspenders signal for standalone mode.

---

## 5. starter-context.json — schema bump to v1.3

Add a new field (sibling of `agents_selected`):

```json
"skills_selected": ["git-workflow"],
```

Schema version line in `init/SKILL.md:96-101` gains:
```
v1.3: + skills_selected
```

`init` Step 4.5 context template (`init/SKILL.md:259-311`) adds the field after
`agents_selected`. `init` Update Mode (`--update`) treats a missing
`skills_selected` as an unanswered field and offers to install.

---

## 6. git-workflow Template — full content

File: `plugins/starter/skills/setup-skills/templates/git-workflow.SKILL.md.tmpl`

Target: < 120 lines after injection. Project rules only — no git tutorial.

````markdown
---
name: git-workflow
description: >
  {{PROJECT_NAME}} git conventions — commit message format, branch naming,
  and PR flow. Apply when committing, branching, or opening a pull request.
  Trigger phrases: "commit", "create branch", "open PR", "git workflow".
template_version: {{TEMPLATE_VERSION}}
---

# Git Workflow — {{PROJECT_NAME}}

Project-specific git rules. Follow these for every commit, branch, and PR.
This is not a git tutorial — it encodes the conventions chosen for this repo.

## Commits

{{COMMIT_BLOCK}}

## Branches

{{BRANCH_BLOCK}}

## Pull Requests

- PR title = the commit subject (or the dominant change if multiple commits).
- Body: summarize *what changed and why*, derived from the commit history
  (`git log <base>..HEAD`).
- Include a short test plan / verification note.
- Keep PRs scoped to one logical change.

## Boundaries

- Do not force-push to shared branches ({{PROTECTED_BRANCHES}}).
- Do not amend or rebase commits that are already pushed to a shared branch.
- Do not commit secrets, build artifacts, or files matching `.gitignore`.
````

### COMMIT_BLOCK variants

**`conventional`** (default):
```markdown
Format: `type(scope): subject`
- Types: feat, fix, chore, docs, refactor, test, perf, ci
- Subject: imperative, ≤ 72 chars, no trailing period
- Body (optional): explain *why*, not *what*. Wrap at 72 columns.
- Breaking change: add `!` after type/scope, or a `BREAKING CHANGE:` footer.

Examples:
- `feat(auth): add refresh-token rotation`
- `fix(api): handle null cursor in pagination`
```

**`none`**:
```markdown
Format: plain imperative subject line.
- ≤ 72 chars, no trailing period, describe the change directly.
- Body (optional): explain *why*. Wrap at 72 columns.

Example: `Add refresh-token rotation to auth flow`
```

**`custom`**:
```markdown
This project uses a custom commit convention. Follow the format documented
in CLAUDE.md ("Commit format" line). If unclear, ask before committing.
```

### BRANCH_BLOCK variants

**`gitflow`**:
```markdown
- `feature/<short-slug>`  → merges into `develop`
- `release/<version>`     → merges into `main` and back into `develop`
- `hotfix/<short-slug>`   → branches from `main`, merges into `main` + `develop`
- Default working branch: `develop`. Never commit directly to `main`.
```
→ `{{PROTECTED_BRANCHES}}` = `main, develop`

**`trunk-based`** (default):
```markdown
- Short-lived branches off `main`: `<initials>/<short-slug>`.
- Merge back to `main` frequently (small PRs). Delete the branch after merge.
- Default working branch: `main`.
```
→ `{{PROTECTED_BRANCHES}}` = `main`

> `{{PROTECTED_BRANCHES}}` is derived from the branch strategy, not a separate token.

---

## 7. setup-skills SKILL.md — structure & budget

Target: **< 160 lines**. Orchestration only — variants live in templates, metadata
in the catalog.

```
1. Frontmatter (name, description, argument-hint "[skill-id]")        ~10
2. Mode detection (context vs standalone)                             ~12
3. Argument handling (/setup-skills git-workflow → skip suggest)      ~8
4. Context detection — load catalog, evaluate suggestWhen             ~20
5. Convention resolution — read conventions or ask (standalone)       ~18
6. Injection — load template, substitute tokens, pick variants        ~25
7. Write rules — mkdir, collision check, write SKILL.md               ~20
8. Post-write — update skills_selected, print trigger phrases         ~12
9. Failure Modes                                                       ~12
```

### Write rules (§7 of the skill)
- Create `.claude/skills/<id>/` if absent.
- **Collision:** if `.claude/skills/<id>/SKILL.md` exists → show diff intent,
  offer **Skip / Overwrite** (never silent replace). Mirrors `setup-agents:118`.
- Stamp `template_version` into the written frontmatter (enables staleness detection).
- After write: update `skills_selected` in `starter-context.json` if it exists.
- Print: "Installed `git-workflow`. It loads when you say: commit, create branch, open PR."

### Failure Modes
```
Don't install a git tutorial — the skill is project rules only
Don't overwrite an existing skill dir without asking
Don't inject conventions you didn't read or confirm — ask in standalone mode
Don't widen triggers to bare "git" — keep them scoped
Don't add the installed skill to the plugin's own manifest.json
```

---

## 8. init Integration

Add **Part 7.5: Project Skills** to the interview (`init/SKILL.md`, after Part 7
Agents, Tier 3+ — but git-workflow offered at **Tier 2+** since it is low-cost
and universal):

```
#### Part 7.5: Project Skills (Tier 2+)

Load ./setup-skills/skills-catalog.json → suggest installable skills.
git-workflow is alwaysInclude — offer it by default.
Show preview (with the resolved commit/branch variant) → confirm.
```

Step 4 preview table (`init/SKILL.md:236`) gains a row:
```
│ .claude/skills/git-workflow/SKILL.md │ CREATE   │ 2     │
```

Step 5 orchestration (`init/SKILL.md:325-331`) gains, under Tier 2:
```
/shipwithai-starter:setup-skills   (reads: skills_selected, conventions)
```

---

## 9. review & drift integration (staleness)

The install model forks the template into the project, so it can drift when the
plugin updates `template_version`. Add lightweight detection:

- **`review` Step 2b (static analysis):** for each dir in `.claude/skills/`, read
  `template_version` from frontmatter; compare against the catalog entry's
  `version`. If older → ⚠️ "git-workflow skill is v1.0.0; current template is v1.1.0.
  Re-run /shipwithai-starter:setup-skills to refresh."
- Health report table gains a `Project skills` row.
- `drift-monitor` agent: no change required (it reads CLAUDE.md, not skills).

---

## 10. Evals

File: `plugins/starter/skills/setup-skills/evals.json`

```json
{
  "evals": [
    {
      "prompt": "Set up project skills — context has commit_format conventional, branch_strategy gitflow",
      "expect": [
        "loads skills-catalog.json",
        "installs git-workflow to .claude/skills/git-workflow/SKILL.md",
        "COMMIT_BLOCK uses conventional (feat/fix/...) variant",
        "BRANCH_BLOCK uses gitflow (feature/release/hotfix) variant",
        "protected branches = main, develop",
        "updates skills_selected in starter-context.json"
      ]
    },
    {
      "prompt": "Set up project skills — context has commit_format none, branch_strategy trunk-based",
      "expect": [
        "COMMIT_BLOCK uses plain imperative variant (no type prefix)",
        "BRANCH_BLOCK uses trunk-based variant",
        "protected branches = main only"
      ]
    },
    {
      "prompt": "/setup-skills git-workflow — no starter-context.json present (standalone)",
      "expect": [
        "does not error on missing context",
        "asks commit format and branch strategy inline",
        "installs after confirmation",
        "does not invent conventions silently"
      ]
    },
    {
      "prompt": "Set up project skills — .claude/skills/git-workflow/SKILL.md already exists",
      "expect": [
        "detects existing skill dir",
        "offers Skip or Overwrite",
        "does not silently replace"
      ]
    },
    {
      "prompt": "Set up project skills — commit_format is custom",
      "expect": [
        "COMMIT_BLOCK uses custom variant pointing to CLAUDE.md",
        "does not fabricate a commit format"
      ]
    },
    {
      "prompt": "Set up project skills, then ask: what triggers the git skill?",
      "expect": [
        "reports trigger phrases: commit, create branch, open PR",
        "triggers are scoped, not bare 'git'",
        "explains skill is lazy-loaded, not always in context"
      ]
    }
  ]
}
```

---

## 11. manifest.json Entry

Add ONE entry — for the installer skill only. The installed `git-workflow` is a
template asset, NOT a plugin skill, so it does NOT appear in the manifest.

```json
{
  "skillId": "setup-skills",
  "name": "setup-skills",
  "description": "Install reusable project-level skills into .claude/skills/. Ships git-workflow (commit/branch/PR conventions matched to your init choices). Catalog-driven, extensible.",
  "creatorType": "community",
  "updatedAt": "2026-06-14T00:00:00Z",
  "enabled": true
}
```

Also add `"./skills/setup-skills"` to `plugin.json` `skills` array.

---

## 12. Files to Create / Update

### Create
| File | Notes |
|------|-------|
| `plugins/starter/skills/setup-skills/SKILL.md` | < 160 lines, orchestration |
| `plugins/starter/skills/setup-skills/skills-catalog.json` | §4 schema, git-workflow entry |
| `plugins/starter/skills/setup-skills/templates/git-workflow.SKILL.md.tmpl` | §6 template |
| `plugins/starter/skills/setup-skills/evals.json` | 6 prompts (§10) |

### Update
| File | Change |
|------|--------|
| `plugins/starter/.claude-plugin/plugin.json` | add `./skills/setup-skills` to skills array; bump version 2.2.0 |
| `plugins/starter/manifest.json` | add setup-skills entry (§11); bump lastUpdated |
| `plugins/starter/skills/init/SKILL.md` | Part 7.5; schema v1.3 (`skills_selected`); preview row; Step 5 orchestration |
| `plugins/starter/skills/review/SKILL.md` | Step 2b template_version staleness check; health row |
| `plugins/starter/CHANGELOG.md` | add [2.2.0] entry |
| `plugins/starter/README.md` | add setup-skills to skills table; note git-workflow install |
| `plugins/starter/CLAUDE.md` | note skills provisioning pillar |

---

## 13. Open Questions — Proposed Resolutions

| Question | Proposed resolution |
|----------|--------------------|
| New pillar or extend setup-agents? | **New skill `setup-skills`**, sibling of setup-agents. Not a new numbered pillar — it rounds out the existing "provision into project" capability. |
| Synthesize from catalog (like agents) or template? | **Template + inject.** Skills are larger and authored; field-synthesis fits agents, not skills. |
| Static template or convention-adaptive? | **Convention-adaptive.** This is the core value — the skill matches the project's chosen commit/branch conventions. |
| Tier placement? | **Tier 2 (Standard).** git-workflow is cheap and universal; gating it behind Tier 3 (agents) undersells it. |
| Catalog beyond git? | **git-workflow only for v2.2.0.** Catalog schema is extensible (testing-workflow, code-review skills as future entries) without a new installer. |
| Installed skill in manifest? | **No.** It is a template asset of starter, installed into the user's repo; only the `setup-skills` installer is a plugin skill. |
| Staleness after plugin updates? | **template_version frontmatter + review check.** Detect-and-notify, never auto-overwrite. |
| Collision with OMC/superpowers git skills? | **Detect dir + offer Skip/Overwrite; scoped triggers** to limit redundant loads. |

---

## 14. Version Note

This spec ships as **v2.2.0**. The previously drafted catalog-expansion + dashboard
plan (`docs/starter/v2.2.0-prompts.md`) was dropped; this skills-provisioning work
takes the v2.2.0 slot.
```
