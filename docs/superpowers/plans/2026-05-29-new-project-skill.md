# new-project Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `new-project` skill to shipwithai-starter that guides a user from an empty directory through a 3-phase interview (goals → architecture → conventions), scaffolds the project via official tools, and configures the Claude harness.

**Architecture:** New skill `new-project` is a standalone entry point parallel to `init`. `init` gains a greenfield routing step. `setup-memory` gains a greenfield marker. All other pillar skills are reused as-is via orchestration.

**Tech Stack:** Markdown + JSON (content-only plugin — no code to compile or test)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `plugins/starter/skills/new-project/SKILL.md` | CREATE | Full 3-phase interview + execute orchestration |
| `plugins/starter/skills/new-project/evals.json` | CREATE | 6+ test prompts defining expected behavior |
| `plugins/starter/skills/init/SKILL.md` | MODIFY | Add greenfield routing at top of Step 1 |
| `plugins/starter/skills/setup-memory/SKILL.md` | MODIFY | Add greenfield status marker in CLAUDE.md output |
| `plugins/starter/manifest.json` | MODIFY | Register new-project skill |
| `plugins/starter/README.md` | MODIFY | Add new-project to skills table |
| `plugins/starter/CHANGELOG.md` | MODIFY | Document v1.2.0 |

---

## Task 1: Create evals.json (TDD — define expected behavior first)

**Files:**
- Create: `plugins/starter/skills/new-project/evals.json`

- [ ] **Step 1: Create directory**

```bash
mkdir -p plugins/starter/skills/new-project
```

Expected: directory exists, no error.

- [ ] **Step 2: Write evals.json**

Write `plugins/starter/skills/new-project/evals.json`:

```json
{
  "evals": [
    {
      "prompt": "I want to start a new Next.js project from scratch",
      "expect": [
        "asks Q1 (what are you building) first",
        "asks Q2 (who will use it)",
        "asks Q3 (constraints)",
        "asks Q4 (one-line description)",
        "generates tech stack recommendation with reasoning",
        "waits for user confirmation before Phase 2"
      ]
    },
    {
      "prompt": "Empty directory — user runs new-project but package.json already exists",
      "expect": [
        "detects package.json",
        "stops immediately",
        "suggests /shipwithai-starter:init instead",
        "does not ask any interview questions"
      ]
    },
    {
      "prompt": "User reaches Phase 2 with Next.js + PostgreSQL stack confirmed",
      "expect": [
        "asks about ORM",
        "asks about authentication",
        "asks about API style",
        "includes 'Let me decide' option for each technical question",
        "generates folder structure after last technical question",
        "waits for architecture confirmation before Phase 3"
      ]
    },
    {
      "prompt": "User selects 'Let me decide' for ORM in Phase 2",
      "expect": [
        "picks an opinionated default",
        "notes the default choice in CLAUDE.md output as chosen-by-default",
        "continues interview without blocking"
      ]
    },
    {
      "prompt": "User reaches Phase 3 and confirms all conventions",
      "expect": [
        "shows final preview table with exact scaffold command",
        "shows stack summary",
        "shows architecture pattern",
        "shows selected workflow gates",
        "waits for final yes/go-back before executing"
      ]
    },
    {
      "prompt": "User confirms execute — verify execution order",
      "expect": [
        "writes .claude/starter-context.json before scaffold command",
        "shows scaffold command to user before running it",
        "invokes setup-memory after scaffold",
        "invokes setup-permissions after scaffold",
        "invokes setup-ssot --architecture-only after scaffold",
        "shows after-write summary with next steps"
      ]
    },
    {
      "prompt": "User says 'go back to phase 2' at final preview",
      "expect": [
        "returns to Phase 2 first question",
        "does not execute anything",
        "does not write any files"
      ]
    }
  ]
}
```

- [ ] **Step 3: Verify evals cover all spec scenarios**

Check each eval maps to a section in `docs/superpowers/specs/2026-05-29-new-project-skill-design.md`:
- Prerequisite check ✓ (eval 2)
- Phase 1 full flow ✓ (eval 1)
- Phase 2 dynamic questions + Let me decide ✓ (evals 3, 4)
- Phase 3 + final preview ✓ (eval 5)
- Execute order ✓ (eval 6)
- Go-back routing ✓ (eval 7)

- [ ] **Step 4: Commit**

```bash
git add plugins/starter/skills/new-project/evals.json
git commit -m "test(starter): add new-project skill evals"
```

---

## Task 2: Write new-project/SKILL.md

**Files:**
- Create: `plugins/starter/skills/new-project/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

Write `plugins/starter/skills/new-project/SKILL.md` with the following content exactly:

```markdown
---
name: new-project
description: >
  Start a new project from scratch. 3-phase interview: project goals → tech stack →
  architecture → conventions. Scaffolds using official tools then configures the
  Claude Code harness. Run on an empty directory.
  Trigger phrases: "start a new project", "create project from scratch",
  "greenfield setup", "I have an empty directory", "new project from scratch".
argument-hint: ""
---

# /new-project

Greenfield entry point. Guides from an empty directory to a scaffolded project with a configured Claude harness.

## Prerequisite Check

Scan for stack indicator files before anything else:

```
package.json  pom.xml  build.gradle  go.mod  Cargo.toml
pyproject.toml  Gemfile  composer.json  mix.exs
```

If any found:
> "This directory already has a project. Use `/shipwithai-starter:init` instead."
> → stop

## Overview

3 phases, each ending with a confirmed artifact. User can redirect at any checkpoint.

```
Phase 1 → confirm tech stack
Phase 2 → confirm architecture + folder structure
Phase 3 → confirm conventions → final preview → execute
```

---

## Phase 1 — Project Goals

Ask 4 questions, one per message. Do not bundle questions.

**Q1:** What are you building?
- Web app
- REST API
- Mobile backend
- CLI tool
- Library

**Q2:** Who will use it?
- Just me (personal / internal tool)
- Small team or customers (< 1k users)
- Product with real growth targets

**Q3:** Any hard constraints? *(free text, or "none")*
> "Any constraints I should know? e.g. must use a specific language, existing database to integrate with, specific hosting (Vercel, AWS, self-hosted)."

**Q4:** One-line description of what the project does. *(free text)*

---

After Q4, generate and show a tech stack recommendation:

```
Based on your answers, I recommend:

  Language:    [language]
  Framework:   [framework + version]
  Database:    [database]
  Hosting:     [hosting]

  Why: [2-3 sentence reasoning grounded in their specific answers]

Use this stack? (yes / swap one thing / different direction)
```

| Response | Action |
|---|---|
| `yes` | Proceed to Phase 2 with confirmed stack |
| `swap one thing` | "What would you like to swap?" → regenerate recommendation |
| `different direction` | Return to Q1 |

---

## Phase 2 — Technical Decisions

Generate 4-5 questions dynamically based on confirmed stack. Ask only questions relevant to the stack. One per message. Always include "Let me decide" for decisions that have a sensible default.

When "Let me decide" is chosen: pick an opinionated default, plan to note it in CLAUDE.md as:
`# Chosen by default — revisit before going to production`

**Required question categories (adapt wording to stack):**
1. Database access / ORM
2. Authentication approach
3. API style
4. Email service (if web app or API with users)
5. Payments (if growth-stage product)

**Example — Next.js + PostgreSQL:**

| Question | Options |
|---|---|
| ORM / database access? | Drizzle / Prisma / Raw SQL (postgres.js) / Let me decide |
| Authentication? | Better Auth / Clerk / NextAuth.js / None yet / Let me decide |
| API style? | Server Actions / REST API routes / tRPC / Let me decide |
| Email? | Resend / SendGrid / None yet |
| Payments? | Stripe / Lemon Squeezy / None yet |

**Example — Spring Boot + PostgreSQL:**

| Question | Options |
|---|---|
| ORM? | JPA/Hibernate / jOOQ / JDBC Template / Let me decide |
| Auth? | Spring Security + JWT / OAuth2 Resource Server / Keycloak / Let me decide |
| API? | REST / GraphQL / gRPC / Let me decide |
| Async messaging? | Kafka / RabbitMQ / None yet |

---

After the last technical question, generate and show an architecture recommendation:

```
Here's your architecture:

  Pattern: [pattern name]

  [folder tree — 2 levels deep, with inline comment per directory]

  Key decisions:
  - [decision 1 + one-line rationale]
  - [decision 2 + one-line rationale]
  - [decision 3 + one-line rationale]

Does this architecture look right?
(yes / adjust folders / different pattern)
```

| Response | Action |
|---|---|
| `yes` | Phase 3 |
| `adjust folders` | "What would you change?" → regenerate folder tree only → re-confirm |
| `different pattern` | Show 2 alternative patterns with tradeoffs → user picks → confirm |

---

## Phase 3 — Conventions

Ask 3 questions, one per message:

**Q1:** Workflow gates — what should Claude follow? *(multi-select)*
```
→ [ ] Plan before coding
      Claude creates a plan before writing code for any task > 30 min
→ [ ] TDD — write tests first
      Claude writes failing tests before implementation
→ [ ] Code review after every significant change
      Claude runs code-reviewer agent after each change
→ [ ] Security review for sensitive areas
      Claude runs security-reviewer before committing to auth/payments areas
→ [ ] None — let Claude decide
```

**Q2:** Commit format?
- Conventional commits (feat/fix/chore/docs)
- Custom (ask for format)
- None

**Q3:** Test coverage target?
- 80% (recommended)
- 60%
- No target

---

After Q3, show the final preview before executing:

```
Here's everything I'll set up:

  ┌──────────────────────────────────────┬──────────────────────────────┐
  │ Action                               │ Details                      │
  ├──────────────────────────────────────┼──────────────────────────────┤
  │ Run scaffold                         │ [exact command]              │
  │ CLAUDE.md                            │ CREATE — full architecture   │
  │ docs/architecture.md                 │ CREATE                       │
  │ .claude/settings.json                │ CREATE — [stack] preset      │
  │ .claude/starter-context.json         │ CREATE — committed to git    │
  └──────────────────────────────────────┴──────────────────────────────┘

  Stack:        [confirmed stack summary]
  Architecture: [pattern name]
  Gates:        [selected gates, or "None"]
  Commits:      [format]

Ready to execute? (yes / go back to phase 1 / 2 / 3)
```

| Response | Action |
|---|---|
| `yes` | Execute |
| `go back to phase N` | Return to that phase, re-run from its first question |

---

## Execute

Run in this exact order — do not reorder steps:

### Step 1 — Write context file

Write `.claude/starter-context.json` before scaffold and before any pillar skill.
Use the v1.1 schema (same as `init`). Always set:
- `project.stage` → `"greenfield"`
- `project.team_size` → `1`
- `architecture.gotchas` → include `"Project is greenfield — structure does not exist yet, build toward it"`

### Step 2 — Run scaffold command

Show the exact command to the user before running it:
> "I'll run: `[command]`. This will scaffold the project in the current directory."

Scaffold commands by stack:
```
Next.js       → npx create-next-app@latest .
Spring Boot   → spring init --dependencies=[selected deps] --build=gradle .
Django        → django-admin startproject [name] .
Go            → go mod init [module-name]
Rust          → cargo init .
Node.js API   → npm init -y then install chosen framework
Other stack   → ask user for the scaffold command
```

If scaffold fails:
> "Scaffold failed: [error]. Please fix the issue above, then run `/new-project` again."
> → stop, do not proceed to pillar skills

### Step 3 — Invoke pillar skills

```
/shipwithai-starter:setup-memory        reads: project, stack, architecture, conventions
/shipwithai-starter:setup-permissions   reads: stack, permissions
/shipwithai-starter:setup-ssot --architecture-only  reads: architecture
```

### Step 4 — After-write summary

```
Done! Here's what was set up:

  ✓ Project scaffolded via [tool]
  ✓ CLAUDE.md         architecture + conventions (greenfield intent)
  ✓ docs/architecture.md
  ✓ .claude/settings.json
  ✓ .claude/starter-context.json

Next steps:
  1. git init && git add .claude/ CLAUDE.md docs/ && git commit -m "chore: add Claude harness"
  2. Open Claude Code → harness is ready
  3. Run /shipwithai-starter:review anytime to check harness health
```

---

## Failure Modes

```
Don't run scaffold without showing the command first
Don't continue past a checkpoint without user confirmation
Don't write harness files before starter-context.json is written
Don't continue if scaffold command fails
Don't ask about team size — irrelevant to harness config
Don't hardcode architecture patterns — generate with LLM based on stack + type + answers
Don't skip "Let me decide" option in Phase 2 questions
```
```

- [ ] **Step 2: Verify line count is under 500**

```bash
wc -l plugins/starter/skills/new-project/SKILL.md
```

Expected: output shows a number under 500.

- [ ] **Step 3: Spot-check against evals**

For each eval in evals.json, mentally trace through SKILL.md and confirm the expected behavior is covered:
- Eval 2 (existing project) → Prerequisite Check section ✓
- Eval 1 (Phase 1 flow) → Phase 1 section ✓
- Eval 3, 4 (Phase 2 + Let me decide) → Phase 2 section ✓
- Eval 5 (Phase 3 + preview) → Phase 3 section ✓
- Eval 6 (execute order) → Execute section ✓
- Eval 7 (go back) → Phase 3 response table ✓

- [ ] **Step 4: Commit**

```bash
git add plugins/starter/skills/new-project/SKILL.md
git commit -m "feat(starter): add new-project skill — greenfield 3-phase interview"
```

---

## Task 3: Update init/SKILL.md — add greenfield routing

**Files:**
- Modify: `plugins/starter/skills/init/SKILL.md:18-30` (top of Step 1)

- [ ] **Step 1: Add greenfield routing block at the top of Step 1**

In `plugins/starter/skills/init/SKILL.md`, find the beginning of `### Step 1 — State Detection`. The current first line after the heading is:

```
Before asking anything, read the project state:
```

Replace that opening with:

```markdown
### Step 1 — State Detection

Before any other detection, check for an empty directory:

```
Scan for: package.json, pom.xml, build.gradle, go.mod, Cargo.toml,
          pyproject.toml, Gemfile, composer.json, mix.exs

If NONE of these files are found and no source files exist:
  "This looks like an empty project. Handing you off to
   /shipwithai-starter:new-project for a better setup experience."
  → invoke /shipwithai-starter:new-project
  → stop
```

If stack files are found, continue with normal state detection:
```

Then the existing lines follow unchanged.

- [ ] **Step 2: Verify init SKILL.md still reads correctly**

Read `plugins/starter/skills/init/SKILL.md` lines 18–45 and confirm:
- Greenfield routing block appears first in Step 1
- Original detection logic (CLAUDE.md, settings.json, .mcp.json scan) still follows intact
- No lines were accidentally deleted

- [ ] **Step 3: Commit**

```bash
git add plugins/starter/skills/init/SKILL.md
git commit -m "feat(starter): route greenfield directories from init to new-project"
```

---

## Task 4: Update setup-memory/SKILL.md — greenfield marker

**Files:**
- Modify: `plugins/starter/skills/setup-memory/SKILL.md:75-95` (Architecture overview section)

- [ ] **Step 1: Add greenfield status block in CLAUDE.md structure**

In `plugins/starter/skills/setup-memory/SKILL.md`, find the `## Architecture overview` section of the CLAUDE.md template (around line 75). It currently reads:

```markdown
## Architecture overview

**Style:** [monolith / microservices / modular monolith]
```

Add a conditional greenfield block immediately after `**Style:**`:

```markdown
## Architecture overview

**Style:** [monolith / microservices / modular monolith]

[Only include the following block when project.stage === "greenfield":]
**Status:** Greenfield — build toward this structure

**Build order:**
[Derive from architecture.build_order if present, otherwise generate a sensible
 3-step build order based on the stack and architecture decisions:]
- Step 1: [e.g., db/schema.ts → run initial migration]
- Step 2: [e.g., features/auth/ — authentication before any other domain]
- Step 3: [e.g., features/<core-domain>/ — first business domain]
[End greenfield block]
```

- [ ] **Step 2: Verify the modification is coherent**

Read `plugins/starter/skills/setup-memory/SKILL.md` and confirm:
- Greenfield block is conditional (`when project.stage === "greenfield"`)
- Non-greenfield projects are unaffected (block is skipped)
- No existing sections were accidentally removed

- [ ] **Step 3: Commit**

```bash
git add plugins/starter/skills/setup-memory/SKILL.md
git commit -m "feat(starter): add greenfield status marker in CLAUDE.md output"
```

---

## Task 5: Update manifest.json

**Files:**
- Modify: `plugins/starter/manifest.json`

- [ ] **Step 1: Add new-project entry after the init entry**

In `plugins/starter/manifest.json`, after the closing `}` of the `init` skill entry and before the `setup-memory` entry, insert:

```json
    {
      "skillId": "new-project",
      "name": "new-project",
      "description": "Start a new project from scratch. 3-phase interview: project goals → tech stack → architecture → conventions. Scaffolds with official tools and configures the Claude harness. Run on an empty directory.",
      "creatorType": "community",
      "updatedAt": "2026-05-29T00:00:00Z",
      "enabled": true
    },
```

- [ ] **Step 2: Validate JSON**

```bash
python3 -c "import json; json.load(open('plugins/starter/manifest.json')); print('valid')"
```

Expected: `valid`

- [ ] **Step 3: Verify skill count**

```bash
python3 -c "import json; d=json.load(open('plugins/starter/manifest.json')); print(len(d['skills']), 'skills')"
```

Expected: `10 skills` (was 9, now 10 with new-project added)

- [ ] **Step 4: Commit**

```bash
git add plugins/starter/manifest.json
git commit -m "chore(starter): register new-project skill in manifest"
```

---

## Task 6: Update README.md and CHANGELOG.md

**Files:**
- Modify: `plugins/starter/README.md`
- Modify: `plugins/starter/CHANGELOG.md`

- [ ] **Step 1: Add new-project to the skills table in README.md**

In `plugins/starter/README.md`, find the Skills table. It currently starts with:

```markdown
| `/shipwithai-starter:init` | **Start here.** Setup interview + full harness configuration |
```

Add a new row immediately after it:

```markdown
| `/shipwithai-starter:new-project` | **Greenfield.** 3-phase interview from empty directory → scaffold + harness |
```

- [ ] **Step 2: Add v1.2.0 entry to CHANGELOG.md**

In `plugins/starter/CHANGELOG.md`, add the following block at the top, before the existing `## [1.0.0]` entry:

```markdown
## [1.2.0] — 2026-05-29

### Added

- `new-project` skill — greenfield entry point: 3-phase interview (project goals →
  tech stack → architecture → conventions), scaffolds via official tools, then
  configures the Claude harness
- `init` now routes to `new-project` when no stack files are detected in directory
- `setup-memory` now writes a greenfield status marker and build order in CLAUDE.md
  when `project.stage` is `"greenfield"`

```

- [ ] **Step 3: Commit**

```bash
git add plugins/starter/README.md plugins/starter/CHANGELOG.md
git commit -m "docs(starter): update README and CHANGELOG for new-project skill v1.2.0"
```

---

## Self-Review Checklist

Before calling this plan complete, verify:

- [ ] All 7 files in the File Map are accounted for across the 6 tasks
- [ ] evals.json has 7 prompts covering all major flows
- [ ] SKILL.md has no TBD / TODO / placeholder text
- [ ] init routing only triggers when NO stack files found (not partial projects)
- [ ] setup-memory greenfield block is conditional — non-greenfield projects unaffected
- [ ] manifest.json has exactly 10 skills after Task 5
- [ ] Execute order in SKILL.md: context file → scaffold → pillar skills (not reordered)
