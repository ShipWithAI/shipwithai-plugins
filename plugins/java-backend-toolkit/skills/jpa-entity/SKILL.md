---
name: jpa-entity
description: >
  Scaffold a Spring Data JPA @Entity correct-by-default so the guardrails never
  fire: @Version optimistic locking, business-key equals/hashCode (never the
  generated @Id), JPA auditing fields, optional soft-delete, plus a matching
  repository — all matching this project's conventions.
  Trigger phrases: "create entity", "scaffold jpa entity", "add a jpa entity",
  "new @Entity", "generate entity".
argument-hint: "<EntityName> [field:type ...]"
---

# JPA Entity — Scaffold

Generate an entity that is born compliant with `ruleset.json`. The point: if the
code is correct from the start, `jpa-optimistic-lock`, `jpa-entity-equals`, and
friends never need to fire.

## Step 1 — Detect project conventions (do not assume)

Read before generating:
- **Base class / auditing:** look for a `@MappedSuperclass` (e.g. `BaseEntity`,
  `AuditableEntity`) and `AuditingEntityListener` / `@EnableJpaAuditing`. If present,
  extend it instead of re-declaring id/audit fields.
- **Id strategy:** match the codebase — `GenerationType.IDENTITY` (Postgres/MySQL
  serial) vs assigned UUID. Default `IDENTITY` for numeric, or UUID if entities use it.
- **Package + path:** mirror an existing entity's package (e.g. `…​.domain` /
  `…​.model` / `…​.entity`). Write to the matching `src/main/java/...` path.
- **Lombok:** if the project uses Lombok, use `@Getter/@Setter`; otherwise write explicit accessors.
- **Soft-delete:** if other entities use a `deleted`/`deletedAt` column or `@SQLDelete`,
  offer the same; otherwise skip.

## Step 2 — Generate (the non-negotiable invariants)

Every generated entity MUST have:
1. **`@Version`** field for optimistic locking.
2. **`equals`/`hashCode` based on a stable business key or an assigned UUID** — never
   the generated `@Id` (null pre-persist, breaks Set/Map membership).
3. **Audit fields** via the project's base class, or `@CreatedDate`/`@LastModifiedDate`
   if auditing is enabled and there's no base class.
4. Jakarta imports (`jakarta.persistence.*`), Spring Boot 3.x.

Use `assets/jpa-entity.java.tmpl` as the shape; fill `{{PACKAGE}}`, `{{ENTITY}}`,
`{{TABLE}}`, `{{FIELDS}}`, `{{ID_STRATEGY}}`. The template carries a `uid` UUID
business key (used by equals/hashCode) and `@CreatedDate`/`@LastModifiedDate` audit
fields. If extending a base class, drop the id/version/audit fields it already
provides (but ensure @Version exists somewhere in the hierarchy — if the base lacks
it, keep it on the entity).

## Step 3 — Repository + migration

- Generate a `Repository extends JpaRepository<Entity, IdType>` next to it.
- **If the entity has associations** (`@ManyToOne`/`@OneToMany`/`@OneToOne`), keep them
  LAZY and add a fetch-aware finder using `assets/repository-entitygraph.java.tmpl` — an
  `@EntityGraph(attributePaths = {"…"})` override or a `join fetch` `@Query`. Reads then
  load the graph explicitly, so `jpa-eager-fetch` / `nplus1-heuristic` never fire.
- If the project uses Flyway/Liquibase, invoke the `db-migration` skill to emit the
  matching `CREATE TABLE` migration in the same change — entity and schema stay in lockstep.
  Do NOT rely on `ddl-auto: update`.

## Step 4 — Report

List created files and confirm the invariants:
```
Created:
  src/main/java/.../<Entity>.java        (@Version ✓, business-key equals/hashCode ✓, audit ✓)
  src/main/java/.../<Entity>Repository.java
  src/main/resources/db/migration/V<n>__create_<table>.sql   (if Flyway)
```

## Failure modes — do NOT

- Do NOT emit an entity without `@Version` (the whole reason this skill exists).
- Do NOT base equals/hashCode on the generated `@Id`.
- Do NOT duplicate id/audit fields already provided by a detected base class.
- Do NOT invent a package — mirror an existing entity, or ask if none exists.
- Do NOT use `javax.persistence` (that's Spring Boot 2.x); use `jakarta.persistence`.
- Do NOT skip the migration when the project clearly uses Flyway/Liquibase.
