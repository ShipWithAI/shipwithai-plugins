# shipwithai-java-backend-toolkit

> Guardrail-first Spring Boot + JPA toolkit for Claude Code.
> Catches the subtle mistakes **at the moment you write them** — not in a doc you hope the model reads.

## Why this exists

Generic Spring Boot skill packs are **exhaustive and passive**: one big reference doc
that loads only when a keyword happens to match. When you scaffold an `@Entity`, nothing
guarantees the "add `@Version`" rule fires. The knowledge exists but isn't *activated at
the moment of the mistake*.

This toolkit inverts that. Its core is a **deterministic hook** that fires on every Java
edit and surfaces a just-in-time advisory the instant a known anti-pattern appears.
Knowledge is the supporting layer, not the lead.

| | Generic springboot skills | This toolkit |
|---|---|---|
| Activation | Passive (keyword hope) | **Hook on action** + scaffold-correct-by-default |
| Coverage | Exhaustive, generic | **Opinionated, few rules done right** |
| Output | Read-a-doc | Just-in-time advisory + correct generated code |

## The four mechanisms

1. **Guardrail hook** (`hooks/jpa-guardrail.py`) — PostToolUse on `Write`/`Edit` of `*.java`.
   Reads the just-written file, runs the heuristics in `rules/ruleset.json`, emits an
   advisory (or **blocks** for injection-class issues). Stdlib-only, silent-fails, never breaks a tool.
2. **Scaffold skills** — generate correct-by-default code so the guardrail never needs to fire:
   `jpa-entity`, `spring-rest-endpoint`, `db-migration`.
3. **Knowledge skill** — `springboot-conventions`, fine-grained references split by domain
   (persistence / web / transactions / testing) explaining the *why* behind each rule.
4. **Reviewer agent** — `springboot-reviewer`, whose checklist **is** `ruleset.json`, so the
   runtime hook and the PR review never disagree.

## The ruleset (v1)

`rules/ruleset.json` is the single source of truth shared by the hook and the reviewer:

| id | What it catches | Hook | Severity |
|----|-----------------|------|----------|
| `jpa-optimistic-lock` | `@Entity` without `@Version` (lost updates) | ✅ | warning |
| `jpa-entity-equals` | equals/hashCode on the generated `@Id` instead of a business key | reviewer-only¹ | info |
| `tx-proxy` | `@Transactional` on a non-public method (silently not proxied) | ✅ | warning |
| `entity-in-controller` | controller returns a JPA entity instead of a DTO | reviewer-only¹ | warning |
| `nplus1-heuristic` | repository call inside a loop (likely N+1) | ✅ | info |
| `jpql-injection` | query built by string concatenation | ✅ **blocks**² | critical |

¹ Needs reading code with judgment (which field `equals` uses, cross-file return types) — handled by the reviewer agent, not the line-level hook, so correct-by-default code isn't falsely flagged.
² Blocks by default (`strictChecks`); switch to advisory in `guardrails-config.json`.

## Install

From a Spring Boot + JPA project, run the setup skill:

```
/shipwithai-java-backend-toolkit:setup
```

It installs the **enforcement layer into the project's `.claude/`** (committed, shared
with the whole team — teammates get the guardrails even without the plugin):

- `.claude/hooks/jpa-guardrail.py` + `ruleset.json` + `guardrails-config.json`
- a `PostToolUse` `Write|Edit` entry merged into `.claude/settings.json`
- `.claude/agents/springboot-reviewer.md`
- a Spring Boot conventions block in `CLAUDE.md`

The authoring skills (`jpa-entity`, etc.) stay plugin-provided.

## Configure

`guardrails-config.json`:
- `disabledChecks` — rule ids to skip (e.g. `["nplus1-heuristic"]` if too noisy)
- `strictChecks` — rule ids that block instead of advise (only `strictEligible` ids honored)
- `maxFileBytes` — skip files larger than this

Per-file escape hatch: `// jbt:ignore <rule-id>` (or `// jbt:ignore-all`).

## Scope

**v1 paved road: Spring Boot 3.x + Spring Data JPA only.** Deliberately excluded for now:
Kotlin, reactive (WebFlux/R2DBC), non-Spring JVM (Quarkus/Micronaut), raw-JDBC-only,
Android/KMP. The name is the destination; each release adds **at most one** paved road —
one excellent road beats five shallow ones.

## Layout

```
java-backend-toolkit/
├── rules/ruleset.json              # SSOT: hook + reviewer read this
├── hooks/jpa-guardrail.py          # PostToolUse guardrail (stdlib only)
├── hooks/guardrails-config.json    # toggles, strictChecks
├── agents/springboot-reviewer.md   # checklist = ruleset.json
├── skills/
│   ├── setup/                      # wires the enforcement layer into a project
│   ├── jpa-entity/                 # scaffold @Entity correct-by-default
│   ├── spring-rest-endpoint/       # scaffold controller + DTO + service + mapper
│   ├── db-migration/               # Flyway/Liquibase migration
│   └── springboot-conventions/     # knowledge: the why, split by domain
└── assets/rules/springboot-rules.md.tmpl  # rule block injected into CLAUDE.md
```

Part of the **ShipWithAI** SDLC toolkit. `shipwithai-starter` detects a Spring Boot
project and routes here (launcher model).
