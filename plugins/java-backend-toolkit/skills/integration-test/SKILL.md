---
name: integration-test
description: >
  Scaffold a Spring Boot integration test against REAL infrastructure via Testcontainers
  — a throwaway Postgres (Kafka optional), wired with Spring Boot 3.1+ @ServiceConnection
  so there's no manual datasource config. Async assertions use Awaitility, never
  Thread.sleep.
  Trigger phrases: "integration test", "testcontainers", "test against real postgres",
  "spring boot test with a database", "end-to-end repository test".
argument-hint: "[EntityName]"
---

# Integration Test — Scaffold (Testcontainers)

Generates an integration test that boots the real Spring context against a real
database in a container — so it catches dialect, constraint, and migration bugs that
H2 or mocks silently hide.

## Step 1 — Detect conventions (do not assume)

Read before generating:
- **Existing test setup:** look for a base test class, an `@AutoConfigureTestDatabase`,
  or existing `@Testcontainers` usage; extend the existing base instead of adding a rival.
- **Dependencies:** confirm `org.springframework.boot:spring-boot-testcontainers`,
  `org.testcontainers:junit-jupiter`, and `org.testcontainers:postgresql` are present;
  if not, list them for the user's `pom.xml`/`build.gradle`.
- **Spring Boot version:** `@ServiceConnection` needs 3.1+. On older versions fall back
  to `@DynamicPropertySource` (and say so).
- **Test naming/runner:** `*IT` runs under Failsafe / a Gradle `integrationTest` task;
  `*Test` runs under Surefire. Match the project's split.

## Step 2 — Render templates

From `assets/`, substitute `{{PACKAGE}}` and `{{ENTITY}}`:
- `AbstractIntegrationTest.java.tmpl` → `<pkg>/AbstractIntegrationTest.java` — the base:
  `@SpringBootTest` + `@Testcontainers`, a `static @Container @ServiceConnection`
  `PostgreSQLContainer<>("postgres:16")` (started once, shared by subclasses).
- `ExampleIT.java.tmpl` → `<pkg>/{{ENTITY}}IT.java` — extends the base, autowires the
  real repository, and shows an Awaitility-polled async assertion.

## Step 3 — Why these choices

- **Real Postgres over H2/mocks:** integration tests should fail when the *real* database
  would fail. H2 accepts SQL Postgres rejects (and vice versa); mocks prove nothing about
  persistence.
- **`@ServiceConnection` over `@DynamicPropertySource`:** the container's URL/credentials
  flow into the context automatically — less boilerplate, fewer wiring mistakes.
- **Awaitility over `Thread.sleep`:** poll until the condition holds (or times out)
  instead of sleeping a fixed guess. `Thread.sleep` in tests is flaky and slow — it trips
  the `test-thread-sleep` guardrail.

## Step 4 — Report

```
Created:
  src/test/java/.../AbstractIntegrationTest.java   (@SpringBootTest + Testcontainers Postgres)
  src/test/java/.../<Entity>IT.java                (real repository + Awaitility async assert)
```
Note any missing Testcontainers dependencies the user must add.

## Failure modes — do NOT

- Do NOT swap in H2 or `@DataJpaTest` embedded DB for a test meant to exercise real infra.
- Do NOT use `Thread.sleep` for async waits — use Awaitility (`test-thread-sleep`).
- Do NOT create a non-static container per test method (slow; loses the shared-startup win).
- Do NOT hand-wire the datasource when `@ServiceConnection` is available.
- Do NOT name a Testcontainers boot test `*Test` if the project runs only `*IT` under Failsafe.
