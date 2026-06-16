# Changelog

All notable changes to `shipwithai-java-backend-toolkit` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

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
