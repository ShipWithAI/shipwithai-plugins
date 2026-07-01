---
name: db-migration
description: >
  Generate a Flyway or Liquibase migration in lockstep with an entity change.
  Detects which migration tool the project uses and the next version number.
  Invoked by jpa-entity after a schema change, or directly.
  Trigger phrases: "create migration", "add db migration", "new flyway migration",
  "add liquibase changeset".
argument-hint: "[description]"
---

# DB Migration — Scaffold

Keeps schema and entities in lockstep: every entity/schema change ships with a
migration. Never rely on `ddl-auto: update` in shared environments.

## Step 1 — Detect the migration tool

| Tool | Signal |
|------|--------|
| **Flyway** | `flyway-core` dependency, or a `src/main/resources/db/migration/` directory |
| **Liquibase** | `liquibase-core` dependency, or a `src/main/resources/db/changelog/` directory |

If neither is present, ask which to set up (default **Flyway** — simplest for v1),
and note the dependency the project must add.

## Step 2 — Determine the next version

- **Flyway:** scan `db/migration/` for `V<n>__*.sql`, take `max(n) + 1`. Filenames:
  `V<n>__<snake_case_description>.sql`.
- **Liquibase:** find the changelog (`db.changelog-master.*`), add a new changeset
  with a unique incrementing `id` and the project's author convention.

## Step 3 — Render the migration

From `assets/`, substitute `{{VERSION}}`, `{{DESCRIPTION}}`, `{{TABLE_NAME}}`,
`{{AUTHOR}}`:

- Flyway:    `flyway_migration.sql.tmpl`     → `db/migration/V{{VERSION}}__{{DESCRIPTION}}.sql`
- Liquibase: `liquibase_changeset.xml.tmpl`  → appended/included into the master changelog

The DDL must include the columns the guardrails imply for entities: a `version`
column (optimistic lock) and audit columns (`created_at`, `updated_at`) when the
entity extends the audited base.

## Step 4 — Report

Show the migration path + the SQL/changeset. If invoked standalone, remind the user
to keep the entity and migration in the same commit.

## Failure modes — do NOT

- Do NOT reuse an existing version number (Flyway will refuse; checksums break).
- Do NOT mix Flyway and Liquibase in one project.
- Do NOT edit an already-applied migration — add a new one (immutable history).
- Do NOT forget the `version` / audit columns when the entity uses them.
