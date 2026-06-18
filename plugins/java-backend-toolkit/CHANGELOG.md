# Changelog

All notable changes to `shipwithai-java-backend-toolkit` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

## [0.5.0] — 2026-06-18

Testing milestone.

### Added
- **Rule** `test-thread-sleep` — flags `Thread.sleep` in `@Test` files (needs both `@Test` and
  `Thread.sleep(`); advises Awaitility.
- **Scaffold skills** `integration-test` (Testcontainers `@SpringBootTest` base with
  `@ServiceConnection` Postgres + Awaitility) and `test-slice` (`@DataJpaTest` / `@WebMvcTest`).
- **Reference** `references/testing.md` — slices vs full context, Testcontainers, Awaitility.

## [0.4.0] — 2026-06-18

Security pack.

### Added
- **Rules** `sec-weak-hash` (MD5/SHA-1), `sec-hardcoded-secret` (literal secrets) — hook;
  `sec-mass-assignment`, `sec-missing-method-auth` — reviewer-only.
- **Scaffold skills** `security-filter-chain` (Spring Security 6 deny-by-default baseline, BCrypt,
  CORS) and `jwt-auth` (resource server, or a custom filter that verifies signature + `exp` and
  rejects `alg=none`).
- **Reference** `references/security.md` — hashing, secrets, authz, CORS/CSRF, OAuth2.

## [0.3.0] — 2026-06-18

Web hardening.

### Added
- **Rules** `web-missing-valid` (`@RequestBody` without `@Valid`) — hook; `web-slow-in-controller`
  — reviewer-only.
- **Scaffold skills** `rest-error-handler` (`@RestControllerAdvice` → RFC 7807 `ProblemDetail`),
  `idempotent-endpoint` (Idempotency-Key replay for unsafe POST); cursor-pagination variant for
  `spring-rest-endpoint`.
- **Reference** `references/web.md` — versioning, error contract, validation, rate limiting.

## [0.2.0] — 2026-06-17

Persistence depth.

### Added
- **Rules** `jpa-eager-fetch`, `jpa-cascade-all`, `jpa-id-generation`, `jpa-osiv` (config-file
  aware) — hook; `jpa-dto-projection` — reviewer-only.
- **Scaffold** `@EntityGraph` repository variant for `jpa-entity`.
- **Reference** DTO-projection section in `references/persistence.md`.

### Changed
- Guardrail hook now also scans `application.properties` / `.yml` (for `jpa-osiv`).

## [0.1.0] — 2026-06-16

Initial release. Guardrail-first Spring Boot + JPA toolkit.

### Added
- **Guardrail hook** (`hooks/jpa-guardrail.py`) — PostToolUse on `Write`/`Edit` of `*.java`.
  Heuristic checks from `rules/ruleset.json`; advisories via `additionalContext`, blocking
  (exit 2) for `strictChecks`. Stdlib-only, silent-fails. Honors `// jbt:ignore <rule-id>`.
- **Ruleset SSOT** (`rules/ruleset.json`) — 6 v1 rules shared by the hook and the reviewer:
  `jpa-optimistic-lock`, `jpa-entity-equals`, `tx-proxy`, `entity-in-controller` (reviewer-only),
  `nplus1-heuristic`, `jpql-injection` (strict-eligible).
- **Config** (`hooks/guardrails-config.json`) — `disabledChecks`, `strictChecks`, `maxFileBytes`.
- **setup skill** — installs the enforcement layer into the project's `.claude/` (hook, ruleset,
  config, reviewer agent, CLAUDE.md rule block); merges settings.json without clobbering existing hooks.
- **Scaffold skills** — `jpa-entity`, `spring-rest-endpoint`, `db-migration` (generate-correct-by-default).
- **Knowledge skill** — `springboot-conventions` with references split by domain.
- **Reviewer agent** — `springboot-reviewer`, checklist driven by `ruleset.json`.

### Scope
- v1 paved road: Spring Boot 3.x + Spring Data JPA only. Kotlin, reactive, non-Spring,
  raw-JDBC, and Android/KMP are intentionally out of scope.
