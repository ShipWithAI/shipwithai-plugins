# shipwithai-java-backend-toolkit — Roadmap

> Status: Draft backlog — pending prioritization
> Companion to [`spec.md`](./spec.md). Same design stance: **guardrail-first**, **one ruleset SSOT**, **scope discipline** (≤ 1 new paved road per release).
> Source basis: web research on Spring Boot / JPA best practices & production anti-patterns (2025–2026), mapped against shipped v0.1.0.

---

## How to read this

Every candidate is classified by the plugin's four artifact types, so it slots into the existing architecture without inventing new mechanics:

| Type | Mechanism | Where it lives |
|------|-----------|----------------|
| **rule+hook** | Line-level heuristic, fires on `Write`/`Edit` of `*.java` | `rules/ruleset.json` + `hooks/jpa-guardrail.py` |
| **rule (reviewer-only)** | Cross-file / semantic judgement | `rules/ruleset.json` (`reviewerEnabled`), read by `springboot-reviewer` |
| **scaffold skill** | Correct-by-default code generation | `skills/<name>/` + `assets/*.tmpl` |
| **reference** | Lazy-loaded "why" doc | `skills/springboot-conventions/references/` |

**Ruleset invariant still holds:** every new rule is defined once in `ruleset.json` (sets `hookEnabled` / `reviewerEnabled` / `strictEligible`), gets a hook fixture, and the reference explains its *why* citing the rule `id`. No prompt edits to the reviewer agent.

---

## Shipped — v0.1.0 (baseline)

The paved road today: **6 JPA-correctness rules + 3 scaffolds + 1 knowledge skill + reviewer.**

| Rule id | Type | Severity |
|---------|------|----------|
| `jpa-optimistic-lock` | rule+hook | warning |
| `jpa-entity-equals` | reviewer-only | info |
| `tx-proxy` | rule+hook | warning |
| `entity-in-controller` | reviewer-only | warning |
| `nplus1-heuristic` | rule+hook | info |
| `jpql-injection` | rule+hook | critical (strict-eligible) |

Scaffolds: `jpa-entity`, `spring-rest-endpoint`, `db-migration`. Knowledge: `springboot-conventions`.

---

## Release themes

Each milestone is **one paved road** (per scope rule). Ordered by impact × fit with current strengths.

### v0.2.0 — Persistence depth *(lowest risk: extends the existing strength)*

Natural extension of the JPA road already shipped. High guardrail value, low scope risk.

| id | Title | Type | Severity |
|----|-------|------|----------|
| `jpa-eager-fetch` | `FetchType.EAGER` on association (fetches too much, re-introduces N+1) | rule+hook | warning |
| `jpa-cascade-all` | `CascadeType.ALL` / `orphanRemoval` outside an aggregate boundary | rule+hook | warning |
| `jpa-id-generation` | `GenerationType.IDENTITY` disables JDBC batch inserts → prefer `SEQUENCE`/pooled | rule+hook | info |
| `jpa-osiv` | `spring.jpa.open-in-view=true` (hides lazy-loading cost into the view layer) | rule+hook (props file) | warning |
| `jpa-dto-projection` | Prefer DTO projection over loading full entity graphs for read paths | reference | — |

- **New reference:** expand `references/persistence.md` with EAGER vs LAZY, cascade boundaries, ID strategy throughput.
- **Scaffold touch-up:** `jpa-entity` already correct-by-default; add an optional `@EntityGraph` repository snippet variant.

### v0.3.0 — Web hardening

Closes the request/response boundary gaps. Pairs with the existing `entity-in-controller` rule.

| id | Title | Type |
|----|-------|------|
| `web-missing-valid` | Request body / params without `@Valid` Bean Validation | rule+hook |
| `web-slow-in-controller` | Blocking/slow op directly in a controller method | reviewer-only |
| — | Global `@RestControllerAdvice` + RFC 7807 `ProblemDetail` error contract | **scaffold skill** `rest-error-handler` |
| — | Cursor-based pagination endpoint (offset is the anti-pattern) | scaffold (extend `spring-rest-endpoint`) |
| — | Idempotency-key handling for unsafe POST | **scaffold skill** `idempotent-endpoint` |
| — | API versioning + error-contract conventions | reference `references/web.md` (extend) |

### v0.4.0 — Security pack *(highest production risk closed; biggest current gap)*

The largest blank area in v0.1.0. Each item is generalizable across all Spring Boot apps.

| id | Title | Type |
|----|-------|------|
| `sec-weak-hash` | MD5 / SHA-1 used for passwords (require BCrypt / Argon2 / PBKDF2) | rule+hook |
| `sec-mass-assignment` | Request payload bound straight onto a `@Entity` (object-binding leak) | reviewer-only |
| `sec-hardcoded-secret` | Hardcoded key / password / token literal | rule+hook (extends existing scan) |
| `sec-missing-method-auth` | Mutating endpoint with no `@PreAuthorize` / method security | reviewer-only |
| — | `SecurityFilterChain` (Spring Security 6) baseline scaffold | **scaffold skill** `security-filter-chain` |
| — | JWT auth filter + validation scaffold | **scaffold skill** `jwt-auth` |
| — | CORS / CSRF / HTTPS / OAuth2 (Spring Authorization Server) | reference `references/security.md` (new) |

> Note: also run the `security-reviewer` agent against `assets/` here per project policy before shipping any auth template.

### v0.5.0 — Testing

Plugin ships evals but no test scaffold today. Make correct-by-default tests as easy as correct-by-default entities.

| id | Title | Type |
|----|-------|------|
| `test-thread-sleep` | `Thread.sleep` in a test (flaky async) → require Awaitility | rule+hook |
| — | Testcontainers integration-test scaffold (Postgres/Kafka, real infra) | **scaffold skill** `integration-test` |
| — | Test-slice scaffolds (`@DataJpaTest`, `@WebMvcTest`) | scaffold (extend) |
| — | Why slices vs full-context, Awaitility over sleep | reference `references/testing.md` (extend) |

### Backlog — beyond the v1 paved road *(requires an explicit scope decision)*

These touch frameworks/stacks intentionally **OUT** of v1. Listed so they are not lost; each needs a deliberate "widen the road" call before work starts.

- **Resilience4j** — circuit breaker / retry+backoff / bulkhead / rate-limiter / time-limiter scaffolds; fallback-method rule; liveness-vs-external probe rule.
- **Async / messaging** — Transactional Outbox scaffold, idempotent Kafka consumer, `@Async` default-pool rule, `@TransactionalEventListener`.
- **Config / production-readiness** — HikariCP pool-sizing rule, config-externalization (no hardcoded endpoint/cred) rule, Actuator health/probes scaffold, structured logging + correlation-id, graceful shutdown.
- **Architecture** — layer-skipping rule (controller→repository directly), field-injection (`@Autowired` field) rule, single-impl-interface advisory.
- **Build / supply-chain** — OWASP dependency-check hook, Maven/Gradle convention reference. (Note: `java-build-resolver` already exists in `everything-claude-code` — reference, don't duplicate.)

---

## Prioritization rationale

1. **v0.2.0 Persistence** first — lowest scope risk, compounds the area already proven.
2. **v0.4.0 Security** is the highest-value gap (production risk), but sequenced after web hardening so error-contract + DTO discipline land before auth templates.
3. **v0.3.0 Web** bridges the two and reuses `entity-in-controller`.
4. **v0.5.0 Testing** makes the rules above verifiable on real projects.
5. **Backlog** stays parked until a paved-road-widening decision — never let "toolkit" justify shallow breadth.

## Cross-cutting checklist (every milestone)

- [ ] New rules defined once in `ruleset.json`; hook fixtures added; advisory vs block verified.
- [ ] `references/*` explain the *why* and cite the rule `id`.
- [ ] Each new skill has `evals.json` with 5+ prompts; tested on 2+ real Spring Boot projects.
- [ ] `manifest.json` + `plugin.json` skills array kept in sync.
- [ ] `CHANGELOG.md` + `README.md` updated; version bumped (minor per feature road).
- [ ] `security-reviewer` run before committing any auth/`assets/` template.

---

## Sources

Best-practice basis (2025–2026):

- [Spring Boot Anti-Patterns That Cause Production Outages — System Weakness](https://systemweakness.com/spring-boot-anti-patterns-that-cause-production-outages-f6d084c3b698)
- [The Toxic Side of Spring Boot: 10 Anti-Patterns — Medium](https://medium.com/@sunil17bbmp/the-toxic-side-of-spring-boot-10-anti-patterns-that-ruin-your-application-architecture-591e282706cd)
- [Spring Boot Security Best Practices: A Developer's Complete Guide — Medium](https://medium.com/@shahharsh172/spring-boot-security-best-practices-a-developers-complete-guide-e91c49dfd5d3)
- [How to Secure Your Spring Boot Application with JWT — Medium](https://medium.com/@ayoubtaouam/how-to-secure-your-spring-boot-application-with-jwt-authentication-06c99893eda7)
- [Mastering JPA Performance: N+1 & Cartesian Explosions — Medium](https://medium.com/@markus.jessenitschnig/mastering-jpa-performance-real-world-strategies-to-eliminate-n-1-queries-and-cartesian-explosions-94ddd9c59b90)
- [Hibernate Performance Best Practices (2025) — Javarevisited](https://medium.com/javarevisited/hibernate-performance-best-practices-2025-9-expert-tips-you-wont-find-in-generic-blogs-87b4a02013e0)
- [Production-Ready Spring Boot: A Complete 2025 Checklist — Medium](https://medium.com/@khawaraleem/production-ready-spring-boot-a-complete-2025-checklist-for-real-world-microservices-0618738cde01)
- [Resilience4j: Designing Fault-Resilient Java Microservices — Paradigma](https://en.paradigmadigital.com/dev/resilience4j-designing-fault-resilient-java-microservices/)
- [API Design Patterns: REST, Pagination, Versioning & Error Handling — Zuplo](https://zuplo.com/learning-center/api-design-patterns)
- [Event-Driven Spring Boot: The 2025 Blueprint (Kafka, Outbox, Idempotency) — Medium](https://medium.com/@lakshitagangola123/event-driven-spring-boot-the-2025-blueprint-kafka-outbox-idempotency-fdc629bb5525)
- [Spring Boot Testcontainers Integration Testing: A Complete Guide — Katyella](https://katyella.com/blog/spring-boot-testcontainers-integration-testing/)
