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
    static PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16");
    // @DynamicPropertySource wires the JDBC url
}
```

## Assert the invariants

- Optimistic locking: a test that two concurrent updates raise `OptimisticLockException`.
- Migrations: a test that the schema migrates cleanly from empty (catches drift between
  entity and migration).
