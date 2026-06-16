---
name: springboot-conventions
description: >
  Fine-grained Spring Boot 3.x + JPA conventions and the rationale behind the
  toolkit's guardrail rules. Split by domain — load the reference for what you're
  touching. Use when working on persistence, controllers, transactions, or tests
  and you want the why, not just the what.
  Trigger phrases: "spring boot conventions", "jpa best practice", "why @Version",
  "transactional not working", "n+1 spring", "entity vs dto".
---

# Spring Boot Conventions

The rules enforced by the guardrail hook (`ruleset.json`) and the always-on summary
in CLAUDE.md are deliberately terse. This skill holds the **rationale and the fix
patterns**, split by domain so you only load what's relevant.

Load the reference for the layer you're in:

| You're working on… | Read | Covers rules |
|--------------------|------|--------------|
| Entities, repositories, queries | `references/persistence.md` | `jpa-optimistic-lock`, `jpa-entity-equals`, `nplus1-heuristic`, `jpql-injection` |
| Controllers, request/response | `references/web.md` | `entity-in-controller` |
| Service methods, `@Transactional` | `references/transactions.md` | `tx-proxy` |
| Tests | `references/testing.md` | (slice tests, Testcontainers) |

Each reference explains: the failure mode, why it bites, the correct pattern, and how
to suppress the guardrail (`// jbt:ignore <rule-id>`) when a deviation is intentional.

This is reference material, not a tutorial — it assumes you know Spring Boot and
focuses on the mistakes that are easy to miss.
