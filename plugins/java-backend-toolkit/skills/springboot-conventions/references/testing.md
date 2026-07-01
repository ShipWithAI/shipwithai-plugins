# Testing conventions

No guardrail rule enforces these (testing style is hard to lint reliably), but the
reviewer and scaffolds follow them.

## Prefer slice tests over full context

`@SpringBootTest` boots the whole application context — slow, and it tests too much
at once. Use the narrowest slice:

| Testing… | Use |
|----------|-----|
| Repositories / JPA mappings | `@DataJpaTest` |
| Controllers / serialization | `@WebMvcTest` (mock the service) |
| A single bean's logic | plain JUnit + Mockito, no Spring context |
| Full wiring / smoke | `@SpringBootTest` — sparingly |

Pick the narrowest slice that actually proves the behavior: a slice loads only the beans
for that layer, so it starts fast and fails for the right reason. The `test-slice`
scaffold generates a ready-to-fill `@DataJpaTest`/`@WebMvcTest` (with `MockMvc`) class.

## Test persistence against a real engine

H2 behaves differently from Postgres/MySQL (types, sequences, locking, native SQL).
A test that passes on H2 can fail in prod. Use **Testcontainers** so `@DataJpaTest`
runs against the real database image, and run your Flyway/Liquibase migrations in the
test so the schema under test matches production.

```java
@DataJpaTest
@Testcontainers
class AccountRepositoryTest {
    @Container
    @ServiceConnection                       // Spring Boot 3.1+: wires the JDBC url for you
    static final PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16");
}
```

On Spring Boot 3.1+, `@ServiceConnection` replaces the hand-written
`@DynamicPropertySource` plumbing — it auto-configures the datasource (and works the same
way for Kafka, Redis, etc.) from the container. Use a real Postgres/Kafka image over H2 or
mocks for anything touching SQL, sequences, or broker semantics. The `integration-test`
scaffold generates a `@SpringBootTest` + Testcontainers `@ServiceConnection` harness.

## Assert the invariants

- Optimistic locking: a test that two concurrent updates raise `OptimisticLockException`.
- Migrations: a test that the schema migrates cleanly from empty (catches drift between
  entity and migration).

## Async assertions — Awaitility, not `Thread.sleep` (`test-thread-sleep`)

**Failure mode:** waiting on async work with `Thread.sleep(...)`. A fixed delay is both
slow (it always waits the full time) and flaky (too short under load → spurious failure;
padded longer → every run drags). It also doesn't express *what* you're waiting for.

**Fix:** poll for the expected state with Awaitility — it returns the instant the
condition holds and fails fast with a clear timeout:

```java
await().atMost(Duration.ofSeconds(5))
        .untilAsserted(() -> assertThat(jobRunner.isDone()).isTrue());
```

The `test-thread-sleep` guardrail flags any file that has both a JUnit `@Test` and a
`Thread.sleep(...)`. Add `org.awaitility:awaitility` in test scope.
