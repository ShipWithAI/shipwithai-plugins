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

## Eager fetching (`jpa-eager-fetch`)

**Failure mode:** `FetchType.EAGER` loads the association on *every* query, even when
the caller never touches it — wasted joins/queries, and a classic N+1 trigger. Remember
`@ManyToOne`/`@OneToOne` default to EAGER, so the cost is easy to ship by accident.

**Fix:** make associations `fetch = FetchType.LAZY` and pull them in only when needed
via a `JOIN FETCH` query or `@EntityGraph(attributePaths = …)`.

## Cascading & orphan removal (`jpa-cascade-all`)

**Failure mode:** `CascadeType.ALL` (and `orphanRemoval=true`) propagate *remove* as well
as persist. Deleting one entity can silently cascade through the object graph and wipe
rows you never meant to touch — especially across an association you don't fully own.

**Fix:** cascade explicitly and narrowly — e.g. `cascade = {PERSIST, MERGE}` — and only
inside an aggregate root that owns its children. Avoid `REMOVE`/`ALL` across entity
boundaries; delete related rows deliberately in the service layer instead.

## Id generation strategy (`jpa-id-generation`)

**Failure mode:** `GenerationType.IDENTITY` forces Hibernate to read the
database-generated key back for every inserted row, which disables JDBC batch inserts.
Bulk persists then run one INSERT per row instead of a batched statement — a real
throughput hit on large writes.

**Fix:** use `GenerationType.SEQUENCE` with a `@SequenceGenerator(allocationSize = 50)`
(pooled allocator) so ids are reserved in blocks and inserts can batch.

## Open Session In View (`jpa-osiv`)

**Failure mode:** `spring.jpa.open-in-view=true` (the Spring Boot default) holds the
persistence context open through view rendering. Lazy associations then load during
controller serialization, so N+1 queries hide outside the service layer where you can't
see or tune them. Detected in `application.properties`/`.yml`, not Java.

**Fix:** set `spring.jpa.open-in-view=false` and load the associations you need in the
service layer explicitly — `JOIN FETCH`, `@EntityGraph`, or a DTO projection.

## DTO projection (read paths) (`jpa-dto-projection`)

**Failure mode:** loading a full entity graph just to read a few fields over-fetches —
it selects every column, drags in lazy associations on access, and risks
`LazyInitializationException` outside the persistence context (see `jpa-eager-fetch` and
`nplus1-heuristic`). A projection fetches *exactly* the columns the read needs in one
query and never touches lazy state.

**Fix:** project straight into a read model:

- **Interface projection** — declare an interface of getters and return it from the repo.
  Spring Data builds the `select` from the getter names; least boilerplate for simple shapes.
- **Constructor expression** — `select new com.x.XDto(e.a, e.b) from X e` in `@Query`.
  Use when you need computed values, joins across entities, or a `record`/class target.

```java
interface AccountView {            // interface projection
    String getName();
    BigDecimal getBalance();
}

@Query("select new com.x.AccountDto(a.name, a.balance) from Account a where a.active = true")
List<AccountDto> findActive();     // constructor expression
```

These DTOs are also what you return at the API boundary — keep entities out of
controllers (`entity-in-controller`).
