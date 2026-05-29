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

Ask 5 questions, one per message. Do not bundle questions.

**Q0:** What's the project name? *(used for scaffold command and CLAUDE.md)*
> "What should we call this project? (e.g. my-app, acme-api)"

**Q1:** What are you building?
> "What type of project is this?"
- Web app
- REST API
- Mobile backend
- CLI tool
- Library

**Q2:** Who will use it?
> "Who's the primary audience for this project?"
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

  Project:     [name]
  Type:        [web app / REST API / mobile backend / CLI / library]
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

When "Let me decide" is chosen: pick an opinionated default and record it in
`starter-context.json` under the relevant field. In CLAUDE.md, add a comment
inline next to the value: `# default — revisit before production`.

**Required question categories (adapt wording to stack):**
1. Database access / ORM
2. Authentication approach
3. API style
4. Email service (if web app or API with users)
5. Payments (if growth-stage product)
6. Base package (if Java or Kotlin stack only)
   > "What's your base package? (e.g. com.example, io.acme.myapp)"
   → Used to generate exact package paths in folder tree: `src/main/java/com/example/myapp/`

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
| Email? | Spring Mail + SendGrid / Resend / None yet |
| Payments? | Stripe Java SDK / None yet |

---

After the last technical question, generate and show an architecture recommendation:

```
Here's your architecture:

  Pattern: [pattern name]

  [project-name]/
  ├── src/
  │   ├── features/          ← business domains (auth, billing, dashboard)
  │   │   └── <feature>/
  │   │       ├── components/
  │   │       ├── actions/   ← Server Actions or route handlers
  │   │       └── types.ts
  │   ├── components/        ← shared UI components
  │   ├── db/
  │   │   ├── schema.ts      ← Drizzle schema definitions
  │   │   └── index.ts       ← database client
  │   └── lib/               ← shared utilities and configs
  └── [framework-specific root files]

  Key decisions:
  - [decision 1 + one-line rationale]
  - [decision 2 + one-line rationale]
  - [decision 3 + one-line rationale]

Does this architecture look right?
(yes / adjust folders / different pattern)
```

Generate the actual folder tree based on the confirmed stack and technical decisions — the example above is for Next.js + Drizzle. Adapt structure for other stacks (e.g. Spring Boot → `src/main/java/.../controller|service|repository`, Go → flat package layout).

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

### Step 1 — Run scaffold command

Run scaffold FIRST while the directory is still empty — writing files before scaffold can cause tools to refuse or warn about non-empty directories.

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

### Step 2 — Write context file

After scaffold succeeds, write `.claude/starter-context.json`.
Use the v1.1 schema (same as `init`). Always set:
- `project.stage` → `"greenfield"`
- `project.team_size` → `1`
- `architecture.gotchas` → include `"Project is greenfield — structure does not exist yet, build toward it"`
- `tier` → `"essential"` (default for new-project; user can upgrade via `/shipwithai-starter:review`)

### Step 3 — Invoke pillar skills

Each pillar skill auto-reads `.claude/starter-context.json` — do not pass parameters manually.

```
/shipwithai-starter:setup-memory        → writes CLAUDE.md + .claude/memory/ structure
/shipwithai-starter:setup-permissions   → writes .claude/settings.json
/shipwithai-starter:setup-ssot --architecture-only  → writes docs/architecture.md
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
