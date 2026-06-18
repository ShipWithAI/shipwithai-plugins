---
name: test-slice
description: >
  Scaffold focused Spring slice tests — @DataJpaTest for the persistence layer (rolls
  back per test) and @WebMvcTest for the web layer (MockMvc + mocked services). Pick the
  narrowest slice that proves the behavior; reach for full @SpringBootTest only for
  cross-layer flows.
  Trigger phrases: "datajpatest", "webmvctest", "slice test", "test my repository",
  "test my controller", "mockmvc test", "unit test the web layer".
argument-hint: "[EntityName]"
---

# Test Slice — Scaffold

A slice test loads only the beans for one layer, so it's fast and its failure points
straight at that layer. Use the narrowest slice that still proves the behavior; only
escalate to `@SpringBootTest` when the test genuinely spans layers (then see the
`integration-test` skill for the Testcontainers full-stack case).

## Step 1 — Pick the slice

- **`@DataJpaTest`** — repositories, entity mappings, custom queries. Loads JPA only,
  each test runs in a transaction rolled back at the end. Embedded DB by default; point
  it at real Postgres with `@AutoConfigureTestDatabase(replace = NONE)` + Testcontainers.
- **`@WebMvcTest(XController.class)`** — controller routing, JSON, validation, status
  codes, error mapping. Loads the MVC layer only; the service is a mock.
- **Full `@SpringBootTest`** — only when the behavior crosses controller → service →
  repository in one flow. Heavier; don't default to it.

## Step 2 — Detect conventions

- Test framework: JUnit 5 + AssertJ assumed; match Mockito/Hamcrest if the project differs.
- **Mock annotation by version:** `@MockitoBean` (Spring Boot 3.4+) vs `@MockBean`
  (≤ 3.3, deprecated in 3.4). Check the Boot version and use the right one.
- Mirror the existing `src/test/java` package layout and naming (`*Test` under Surefire).

## Step 3 — Render templates

From `assets/`, substitute `{{PACKAGE}}`, `{{ENTITY}}`, `{{ENTITY_LOWER}}`:
- `DataJpaTest.java.tmpl` → `<pkg>/{{ENTITY}}RepositoryTest.java` — autowires the
  repository + `TestEntityManager`, asserts with AssertJ.
- `WebMvcTest.java.tmpl` → `<pkg>/{{ENTITY}}ControllerTest.java` — `MockMvc` drives the
  controller, `@MockitoBean {{ENTITY}}Service` stubs the dependency, `jsonPath` checks the body.

## Step 4 — Report

```
Created:
  src/test/java/.../<Entity>RepositoryTest.java   (@DataJpaTest, rolls back per test)
  src/test/java/.../<Entity>ControllerTest.java    (@WebMvcTest, MockMvc + mocked service)
```
State which slice(s) you generated and which mock annotation matches the Boot version.

## Failure modes — do NOT

- Do NOT reach for `@SpringBootTest` when a slice proves the behavior — it's slower and broader.
- Do NOT load the database in a `@WebMvcTest` — mock the service; the web slice has no repo.
- Do NOT mix `@MockBean` and `@MockitoBean` arbitrarily — pick the one for your Boot version.
- Do NOT assume `@DataJpaTest`'s embedded DB matches production SQL — use Testcontainers
  when dialect fidelity matters (see `integration-test`).
- Do NOT forget the controller class argument: `@WebMvcTest({{ENTITY}}Controller.class)`
  keeps the slice narrow; a bare `@WebMvcTest` loads every controller.
