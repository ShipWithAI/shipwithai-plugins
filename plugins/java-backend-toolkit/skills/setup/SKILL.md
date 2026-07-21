---
name: setup
description: >
  Wire the Spring Boot guardrails into this project — install the jpa-guardrail
  PostToolUse hook + ruleset, register it in settings.json, copy the
  springboot-reviewer agent, and inject the Spring Boot rule block into CLAUDE.md.
  Short interview fills project slots (base entity, migration tool, strict mode).
  Trigger phrases: "set up spring boot guardrails", "install java backend toolkit",
  "wire jpa guardrails", "setup springboot toolkit".
argument-hint: "[--strict] [--no-agent]"
---

# Spring Boot Toolkit — Setup

Installs the **enforcement layer** into the project's `.claude/` so it is committed
and shared with the whole team — a teammate who clones the repo gets the guardrails
even without installing this plugin. The **authoring skills** (`jpa-entity`,
`spring-rest-endpoint`, `db-migration`) stay plugin-provided and are not copied.

Plugin source root (where templates live): the directory containing this skill's
parent, i.e. `plugins/java-backend-toolkit/`. Resolve files relative to it.

## Step 1 — Verify this is a Spring Boot + JPA project

Confirm at least one of:
- `pom.xml` containing `spring-boot-starter`, or
- `build.gradle` / `build.gradle.kts` containing `spring-boot`.

And JPA in use: `spring-boot-starter-data-jpa` (or `jakarta.persistence` / `javax.persistence` imports).

If not a Spring Boot + JPA project → **stop** and say so. This toolkit's v1 paved
road is Spring Boot 3.x + Spring Data JPA only (no Kotlin, reactive, or non-Spring).

## Step 2 — Detect project slots (smart defaults, confirm — do not interrogate)

Scan, propose, ask only to confirm:

| Slot | Detect from | Default if absent |
|------|-------------|-------------------|
| `MIGRATION_TOOL` | `flyway-core` dep or `src/main/resources/db/migration/` → Flyway; `liquibase-core` → Liquibase | `Flyway` |
| `BASE_ENTITY` | a `@MappedSuperclass` class and/or `AuditingEntityListener` usage | `a @MappedSuperclass BaseEntity with Spring Data JPA auditing` |
| `PROJECT_NAME` | CLAUDE.md identity / repo dir name | repo directory name |
| strict mode | `--strict` arg | `jpql-injection` blocks (already the default in `guardrails-config.json`) |

Show the resolved slot values in one block and get a single confirmation.

## Step 3 — Install the guardrail hook (copy flat into `.claude/hooks/`)

Copy these three files from the plugin's `hooks/` and `rules/` into the project's
`.claude/hooks/` (flat — the hook finds its ruleset beside itself):

- `hooks/jpa-guardrail.py`        → `.claude/hooks/jpa-guardrail.py`
- `rules/ruleset.json`            → `.claude/hooks/ruleset.json`
- `hooks/guardrails-config.json`  → `.claude/hooks/guardrails-config.json`

If `--strict` was NOT passed and the user wanted advisory-only for injection too,
edit the copied `guardrails-config.json` to set `"strictChecks": []`. Otherwise leave
the default (`["jpql-injection"]`).

Do not modify the plugin's source files — only the copies in the project.

## Step 4 — Register the hook in `.claude/settings.json` (merge, never clobber)

Read `.claude/settings.json` (create `{}` if absent). Under `hooks.PostToolUse`,
add this entry **only if an equivalent is not already present**:

```json
{ "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "python3 .claude/hooks/jpa-guardrail.py" }] }
```

Preserve every existing hook (e.g. `protect-files.py`, `observe.py`). Append; do not
replace the array. If a `jpa-guardrail.py` entry already exists, skip (idempotent).

## Step 5 — Inject the Spring Boot rule block into CLAUDE.md

Load `assets/rules/springboot-rules.md.tmpl`, substitute `{{PROJECT_NAME}}`,
`{{BASE_ENTITY}}`, `{{MIGRATION_TOOL}}`, `{{TEMPLATE_VERSION}}` (= toolkit version).

- If the project keeps rules in `.claude/rules/`, write `.claude/rules/springboot.md`.
- Otherwise append a `## Spring Boot conventions` section to `CLAUDE.md` (do not duplicate
  if a prior install already added it — replace that section instead).

## Step 6 — Install the reviewer agent (unless `--no-agent`)

Copy `agents/springboot-reviewer.md` → `.claude/agents/springboot-reviewer.md`.
This makes the reviewer available to teammates and keeps its checklist (the same
`ruleset.json`) in the repo.

## Step 7 — Report

Print a summary:
```
Installed Spring Boot guardrails:
  .claude/hooks/jpa-guardrail.py        (PostToolUse: Write|Edit on *.java)
  .claude/hooks/ruleset.json            (6 rules — 5 hook-enforced, 1 reviewer-only)
  .claude/hooks/guardrails-config.json  (strict: <strictChecks>)
  .claude/agents/springboot-reviewer.md
  CLAUDE.md                             (Spring Boot conventions block)

Try it: create an @Entity without @Version → the hook reminds you at write time.
Authoring helpers (from the plugin): jpa-entity, spring-rest-endpoint, db-migration.
Tune checks in guardrails-config.json (disabledChecks / strictChecks); suppress per-file
with `// jbt:ignore <rule-id>`.
```

## Failure modes — do NOT

- Do NOT clobber existing hooks in settings.json — merge only.
- Do NOT copy the scaffold skills into the project — they are plugin-provided.
- Do NOT edit the plugin's source `ruleset.json`/`guardrails-config.json`; only project copies.
- Do NOT install on a non-Spring-Boot or Kotlin/reactive project — stop with a clear message.
- Do NOT invent slot values you did not detect or confirm.
- Do NOT register the hook twice — check for an existing entry first.
