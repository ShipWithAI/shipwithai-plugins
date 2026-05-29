# Design Spec: `new-project` Skill

**Date:** 2026-05-29
**Status:** Approved
**Plugin:** shipwithai-starter
**Skill:** `new-project`

---

## Overview

A new skill for greenfield project setup. Runs on an empty directory, guides the user through architecture decisions via a 3-phase interview, scaffolds the project using official tools, then configures the Claude harness.

**Trigger:** `/shipwithai-starter:new-project`
**Trigger phrases:** "start a new project", "create project from scratch", "greenfield setup", "I have an empty directory"

---

## Position in Plugin

```
init          → existing project (detect stack → configure harness)
new-project   → greenfield (consult → scaffold → configure harness)
review        → audit + upgrade
```

`init` and `new-project` are separate entry points. Users on an empty directory use `new-project`. Users with existing code use `init`.

`init` routes to `new-project` automatically when no stack files are detected:

```
If no package.json / pom.xml / go.mod / pyproject.toml / Cargo.toml / Gemfile →
  "This looks like an empty project. Handing you off to new-project for a better experience."
  → invoke /shipwithai-starter:new-project
```

**Prerequisite check on skill start:**

```
If directory already has stack files →
  "This directory already has a project. Use /shipwithai-starter:init instead."
  → stop
```

---

## Interview Design: 3-Phase Progressive Reveal

Each phase ends with a visible artifact the user confirms before moving on. User can redirect early without wasting the full interview.

### Phase 1 — Project Goals (3-4 questions)

**Goal:** Understand enough to recommend a tech stack.

```
Q1: What are you building?
    → Web app / REST API / Mobile backend / CLI tool / Library

Q2: Who will use it?
    → Just me (personal/internal)
    → Small team or customers (<1k users)
    → Product with real growth targets

Q3: Any hard constraints?
    → Must use a specific language or framework?
    → Existing database or infra to integrate with?
    → Specific hosting? (Vercel, AWS, self-hosted)
    → (free text, or "none")

Q4: One-line description of what the project does.
    → Free text — used to enrich the recommendation
```

**Output — Tech Stack Recommendation:**

```
Based on your answers, I recommend:

  Language:    TypeScript
  Framework:   Next.js 14 (App Router)
  Database:    PostgreSQL
  Hosting:     Vercel

  Why: [reasoning based on answers]

Use this stack? (yes / swap one thing / different direction)
```

- `yes` → Phase 2 starts with confirmed stack as input
- `swap one thing` → ask what to swap, regenerate recommendation
- `different direction` → return to Q1

---

### Phase 2 — Technical Decisions (4-5 questions)

**Goal:** Deep technical choices based on confirmed stack. Questions are generated dynamically by LLM — only relevant questions for the confirmed stack are asked.

**Example questions for Next.js + PostgreSQL:**

```
Q1: ORM / database access?
    → Drizzle / Prisma / Raw SQL / Let me decide

Q2: Authentication?
    → Better Auth / Clerk / NextAuth / Custom / None yet

Q3: API style?
    → Server Actions / REST API routes / tRPC / Let me decide

Q4: Email?
    → Resend / SendGrid / None yet

Q5: Payments?
    → Stripe / Lemon Squeezy / None yet
```

**Example questions for Spring Boot + PostgreSQL:**

```
Q1: ORM?    → JPA/Hibernate / jOOQ / JDBC
Q2: Auth?   → Spring Security + JWT / OAuth2 / Keycloak
Q3: API?    → REST / GraphQL / gRPC
Q4: Async?  → Kafka / RabbitMQ / None
```

**"Let me decide" option:** Skill picks an opinionated default and notes it in CLAUDE.md as a decision to revisit.

**Output — Architecture Pattern + Folder Structure:**

```
Here's your architecture:

  Pattern: Feature-based Modular Monolith

  src/
  ├── app/                  ← Next.js App Router
  ├── features/             ← business domains
  │   └── <feature>/
  │       ├── components/
  │       ├── actions/      ← Server Actions
  │       └── types.ts
  ├── db/
  │   ├── schema.ts         ← Drizzle schema
  │   └── index.ts
  ├── lib/                  ← shared utilities
  └── components/           ← shared UI

  Key decisions:
  - [reasoning per choice]

Does this architecture look right?
(yes / adjust folders / different pattern)
```

- `yes` → Phase 3
- `adjust folders` → free text, regenerate folder structure only
- `different pattern` → show 2 alternatives with tradeoffs

---

### Phase 3 — Conventions (2-3 questions)

**Goal:** Capture how the dev wants to work.

```
Q1: Workflow gates — what should Claude follow? (multi-select)
    → [ ] Plan before coding
          Claude creates a design doc before coding any task > 30 min
    → [ ] TDD — write tests first
    → [ ] Code review after every significant change
    → [ ] Security review for auth/payments areas
    → [ ] None — let Claude decide

Q2: Commit format?
    → Conventional commits (feat/fix/chore)
    → Custom
    → None

Q3: Test coverage target?
    → 80% (recommended)
    → 60%
    → No target
```

**Output — Final Preview:**

```
Here's everything I'll set up:

  ┌─────────────────────────────────────┬────────────────────────────┐
  │ Action                              │ Details                    │
  ├─────────────────────────────────────┼────────────────────────────┤
  │ Run scaffold command                │ npx create-next-app@latest │
  │ CLAUDE.md                           │ CREATE — full architecture │
  │ docs/architecture.md                │ CREATE                     │
  │ .claude/settings.json               │ CREATE — Node.js preset    │
  │ .claude/starter-context.json        │ CREATE — committed to git  │
  └─────────────────────────────────────┴────────────────────────────┘

  Stack:        Next.js 14, PostgreSQL, Drizzle, Better Auth
  Architecture: Feature-based Modular Monolith
  Gates:        Plan before code, Code review
  Commits:      Conventional

Ready to execute? (yes / go back to change something)
```

- `yes` → Execute phase
- `go back` → ask which phase to return to (1 / 2 / 3)

---

## Execute Phase

**Order matters — do not reorder:**

```
Step 1: Write .claude/starter-context.json
        → Persist all interview answers before doing anything else
        → Enables resume if skill crashes mid-execution

Step 2: Run scaffold command
        → Derived from confirmed stack:
            Next.js       → npx create-next-app@latest
            Spring Boot   → spring init (with selected deps)
            Django        → django-admin startproject
            Go            → go mod init <name>
            Rust          → cargo new <name>
            Node.js API   → npm init + express/fastify/hono install
        → Show command to user before running — no silent execution
        → If scaffold fails → stop, report error, do not continue

Step 3: Invoke pillar skills (read from starter-context.json)
        → /setup-memory      → CLAUDE.md pre-filled with full architecture
        → /setup-permissions → .claude/settings.json with stack preset
        → /setup-ssot        → docs/architecture.md
```

---

## CLAUDE.md for Greenfield vs Existing Projects

`init` on existing project → CLAUDE.md describes **what exists**.
`new-project` → CLAUDE.md describes **intent** — architecture not yet built but Claude will build toward it.

```markdown
## Architecture overview

**Pattern:** Feature-based Modular Monolith
**Status:** Greenfield — build toward this structure

**Target structure:**
src/features/<domain>/components/  ← UI per domain
src/features/<domain>/actions/     ← Server Actions
src/db/schema.ts                   ← Drizzle schema (create this first)

**Build order:**
1. db/schema.ts → run Drizzle migrate
2. features/auth/ → authentication first
3. features/<core-domain>/

**Sensitive areas:** src/db/, src/features/auth/
```

---

## After-Write Summary

```
Done! Here's what was created:

  ✓ my-app/          scaffolded via create-next-app
  ✓ CLAUDE.md        architecture + conventions
  ✓ docs/architecture.md
  ✓ .claude/settings.json
  ✓ .claude/starter-context.json

Next steps:
  1. git add .claude/ CLAUDE.md docs/ && git commit -m "chore: add Claude harness"
  2. Open Claude Code → harness is ready
  3. Run /shipwithai-starter:review anytime to audit harness health
```

---

## Failure Modes

```
Don't run scaffold without showing the command first
Don't continue if scaffold command fails
Don't write harness files before starter-context.json is written
Don't ask about team size — not relevant to harness config
Don't hardcode architecture recommendations — use LLM to generate based on stack + project type
Don't skip the "Let me decide" option — some users aren't ready to commit
```

---

## Out of Scope

- Maintaining scaffold templates (delegated to official tools)
- CI/CD setup (Phase 2)
- MCP and agents setup (user can upgrade via `/review` after project starts)
- Team size as an interview signal
