# Persistence conventions

Rules: `jpa-optimistic-lock`, `jpa-entity-equals`, `nplus1-heuristic`, `jpql-injection`.

## Optimistic locking — `@Version` (`jpa-optimistic-lock`)

**Failure mode:** two transactions read the same row, both write — the second
silently overwrites the first (lost update). No error, just wrong data.

**Fix:** add a `@Version` field. JPA then checks the version on UPDATE and throws
`OptimisticLockException` on conflict, so the caller can retry.

```java
@Version
private Long version;
```

**When to suppress** (`// jbt:ignore jpa-optimistic-lock`): append-only tables,
read-only projections, or rows never updated concurrently. Document why.

## Entity equality — business key, not `@Id` (`jpa-entity-equals`)

**Failure mode:** `equals`/`hashCode` based on a `GenerationType.IDENTITY` id are
broken before persist (id is `null`), and an entity's hash changes once it's saved —
so it gets lost in a `HashSet`/`HashMap` populated before flush.

**Fix:** use a stable business/natural key, or a UUID assigned at construction:

```java
@Column(nullable = false, unique = true, updatable = false)
private UUID businessKey = UUID.randomUUID();
// equals/hashCode use businessKey only
```

Avoid Lombok `@Data`/`@EqualsAndHashCode` on entities — they default to all fields.

## N+1 queries (`nplus1-heuristic`)

**Failure mode:** iterating a collection and calling a repository (or touching a
lazy association) per element → one query becomes N+1.

**Fix options:**
- `JOIN FETCH` in the query, or `@EntityGraph(attributePaths = …)` on the repo method.
- Batch: `findAllById(ids)` instead of `findById` in a loop.
- `@BatchSize(size = n)` on the association for windowed fetching.

The hook only *suspects* N+1 (a repository call near a loop). Confirm by reading the
method; suppress with `// jbt:ignore nplus1-heuristic` if it's a bounded, non-DB loop.

## Query injection (`jpql-injection`, strict/blocking)

**Failure mode:** building JPQL or native SQL by string concatenation — injection,
and it defeats prepared-statement plan caching.

**Fix:** always bind parameters.

```java
@Query("select u from User u where u.email = :email")
Optional<User> findByEmail(@Param("email") String email);
```

This rule blocks by default (`strictChecks`). If you have a vetted dynamic-query
builder (Criteria API / QueryDSL), use it rather than string concat — don't just
suppress.
