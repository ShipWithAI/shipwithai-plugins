# shipwithai-java-backend-toolkit — Implementation Spec

> Status: Draft — pending approval
> Target location: `plugins/java-backend-toolkit/` (module in this monorepo, NOT a separate repo)
> Design stance: **guardrail-first** (activation over knowledge)
> v1 paved road: **Spring Boot 3.x + Spring Data JPA** only

---

## 0. Decision Record (settled in discussion 2026-06-16)

| Decision | Resolution |
|----------|-----------|
| starter identity | **(a) ShipWithAI launcher** — wire own plugins deeply, suggest external lightly, never install OMC/superpowers |
| Where this lives | **Module in monorepo** `plugins/java-backend-toolkit/` — shares marketplace.json + publish-plugin.sh; enables atomic starter↔toolkit changes |
| Primary mechanism | **Guardrail-first** — action-triggered hooks, not passive knowledge skills (the gap that makes ECC useless) |
| Content boundary | Generalizable Spring Boot best-practice → this plugin. Project-specific convention (BaseEntity, soft-delete column) → project `.claude/` via starter init, NOT published |

---

## 1. Positioning & Why It Exists

### The painpoint
`everything-claude-code`'s `springboot-patterns` / `jpa-patterns` skills are **exhaustive + passive**: one large reference doc that fires only when a broad keyword happens to match. When a dev scaffolds an `@Entity`, there is **no guarantee** the "add `@Version` for optimistic locking" rule loads. The knowledge exists but is **not activated at the moment of the mistake** → the dev feels it "does nothing".

Many Spring Boot correctness rules are exactly the kind a dev forgets or lacks experience to notice:
- Missing `@Version` (no optimistic locking → lost updates)
- `@Transactional` on a non-public / self-invoked method (silently not proxied)
- Returning a JPA entity straight from a `@RestController` (lazy-init serialization failure / over-exposure)
- N+1 query from a loop over a lazy association
- String-concatenated JPQL/native query (injection)

### The differentiator vs ECC
| | ECC springboot skills | This toolkit |
|---|---|---|
| Activation | Passive (keyword hope) | **Deterministic hooks on action** + scaffold-correct-by-default |
| Coverage | Exhaustive, generic | **Opinionated, sharp, few rules done right** |
| Output shape | Read-a-doc | Just-in-time advisory + correct generated code |

The toolkit does NOT try to out-document ECC. It wins on **when the rule fires**, not how much it knows.

---

## 2. Scope Discipline (critical — the name is broad on purpose, v1 is narrow)

The published name is `shipwithai-java-backend-toolkit` — the *destination*. **v1 ships exactly one paved road:**

**IN (v1):** Spring Boot 3.x, Spring Data JPA, Spring Web (MVC), Flyway/Liquibase migrations, JUnit 5 + Spring Boot Test.

**OUT (explicitly deferred, documented as non-goals):**
- Kotlin (different idioms — would dilute into ECC-style breadth)
- Non-Spring JVM (Quarkus, Micronaut)
- Reactive stack (WebFlux / R2DBC)
- Raw-JDBC-only projects
- Android / KMP

> Rule: the name may be broad, but **every release adds at most one paved road**. Never let "toolkit" justify shipping shallow coverage of five frameworks. One excellent Spring Boot road > a mediocre "java toolkit".

---

## 3. The Four Mechanisms (in priority order)

### Mechanism 1 — Guardrail hooks (PRIMARY, the moat)

Deterministic `PostToolUse` hooks (Python 3 stdlib only — matches existing `.claude/hooks/observe.py`, `protect-files.py`) installed into the **project's** `.claude/settings.json`. They fire after `Edit`/`Write` on `*.java`, read the just-written content, run **cheap heuristic checks** (regex/structural — NOT a full parser), and emit an **advisory** back as additional context (exactly the `<system-reminder>` injection pattern this repo already uses).

v1 guardrail checks (`hooks/guardrails-config.json` toggles each):

| id | Trigger (file content) | Advisory emitted |
|----|------------------------|------------------|
| `jpa-optimistic-lock` | `@Entity` present, no `@Version` | "Entity `X` has no `@Version` — add optimistic locking unless intentionally omitted." |
| `jpa-entity-equals` | `@Entity` + custom `equals`/`hashCode` on `@Id` | "equals/hashCode on a generated `@Id` is unsafe pre-persist — use a business key or stable UUID." |
| `tx-proxy` | `@Transactional` on non-`public` or self-invoked method | "`@Transactional` here won't be proxied (Spring AOP) — make it public + call from another bean." |
| `entity-in-controller` | `@RestController` method returns a `@Entity` type | "Returning an entity from a controller leaks the model + risks lazy-init errors — return a DTO." |
| `nplus1-heuristic` | loop body calls a `*Repository.findBy*` | "Possible N+1 — consider a fetch join / `@EntityGraph` / batch fetch." |
| `jpql-injection` | `@Query` value built by string concat, or native query w/ `+` | "Build queries with bind parameters (`:name`), never string concatenation." **(strict-eligible)** |

**Advisory vs blocking:** default = **advisory** (never block an edit — blocking is what makes harnesses hated). `guardrails-config.json` exposes `strictChecks: ["jpql-injection"]` so genuinely dangerous patterns *can* block via non-zero exit, opt-in only.

**Accepted limitation (documented, not hidden):** heuristics are regex-level → false positives possible. Mitigation: advisory tone ("Possible…"), each check independently toggleable, and `// jbt:ignore <id>` inline escape hatch the hook honors. A false positive that's easy to silence beats a missed bug.

### Mechanism 2 — Scaffold skills (generate-correct-by-default)

If code is born correct, the guardrail never fires. Model-invoked skills triggered by "create entity", "add endpoint":

- `jpa-entity` — scaffolds `@Entity` with `@Version`, safe equals/hashCode (business key), audit fields (`@CreatedDate`/`@LastModifiedDate`), optional soft-delete; **slots** for project-specific `BaseEntity` / column names (filled from project context, see §5).
- `spring-rest-endpoint` — controller + request/response **DTO** + service + mapper; never exposes the entity.
- `db-migration` — emits a Flyway/Liquibase migration alongside any entity change (so schema + entity stay in lockstep).

### Mechanism 3 — Knowledge skills + rule pack (supporting, fine-grained)

NOT one mega-skill. Split by domain so triggers are scoped:
- `springboot-conventions` skill with lazy `references/` split: `persistence.md`, `web.md`, `transactions.md`, `testing.md`.
- An **always-on rule block** (cheap) injected into the project's `CLAUDE.md` (or `.claude/rules/`) by `setup` — the 2-line summary layer (e.g. "Persistence: Spring Data JPA, no raw JDBC unless justified; entities always carry `@Version`"). Mirrors the CLAUDE.md-summary / skill-detail split from `setup-skills-spec.md` §1.

### Mechanism 4 — Reviewer agent

`springboot-reviewer` agent (Read/Grep/Glob/Bash) tuned to **exactly the §3.1 rule set** — sharper than ECC's generic `java-reviewer`. Invoked for diff/PR review. Reuses the same rule definitions the hooks use (single source of truth — see §6), so hook advisories and review findings never disagree.

---

## 4. Content Boundary — generalizable vs project-specific

| Content | Generalizable? | Home |
|---------|---------------|------|
| `@Version` rule, N+1, tx-proxy, DTO-not-entity | ✅ true for all Spring Boot | **This plugin** (hooks + rules) |
| `BaseEntity` name, soft-delete column, package layout, team naming | ❌ project-only | **Project `.claude/`**, filled by starter `init` reading the codebase — NOT published |

Scaffold templates ship with **slots** (`{{BASE_ENTITY}}`, `{{AUDIT_STRATEGY}}`); the plugin provides the correct *shape*, the project provides the *specifics*. Never publish a project's private convention as a plugin default.

---

## 5. Integration with starter (the launcher wiring)

starter stays the orchestrator; the toolkit owns the Java knowledge. The seam:

1. **Detect** — starter gains a `stack-recipes.json` (extends the `suggestWhen` pattern of `setup-skills/skills-catalog.json`). Recipe `spring-boot`: `detect = { files: [pom.xml, build.gradle], content: [spring-boot-starter] }`.
2. **Recommend (Tier-1 WIRE)** — on detect, starter `init` proposes installing `shipwithai-java-backend-toolkit` and, on confirm, **delegates** to the toolkit's own entry skill.
3. **Delegate** — the toolkit ships `java-backend-toolkit:setup` (mirrors starter's pillar installers): writes the guardrail hooks into project `.claude/settings.json`, installs scaffold skills into `.claude/skills/`, injects the rule block into `CLAUDE.md`, installs `springboot-reviewer` into `.claude/agents/`. It runs a **short** interview to fill the §4 project slots (smart defaults from codebase scan; confirm, don't interrogate).

> Separation of concerns: **starter knows _when_** (stack detected), **toolkit knows _what_** (Spring Boot specifics). starter never embeds Java knowledge; toolkit never duplicates harness-setup mechanics — it reuses starter-context.json conventions where present.

This realizes the **3-tier recommend model**: toolkit = Tier 1 (WIRE + verify); a suggested `postgres` MCP = Tier 2 (suggest + command); OMC/superpowers = Tier 3 (detect & adapt only).

---

## 6. Single Source of Truth for rules

Hooks (Mechanism 1) and the reviewer agent (Mechanism 4) must never disagree. Define rules once:

```
plugins/java-backend-toolkit/rules/ruleset.json
  [{ id, title, severity, detect (heuristic spec), advisory, fixHint, strictEligible }]
```
- `hooks/jpa-guardrail.py` reads `ruleset.json` → runs heuristics.
- `agents/springboot-reviewer.md` references the same `ruleset.json` as its checklist.
- `springboot-conventions` references explain the *why* behind each `id`.

One rule added = hook + reviewer + doc all updated from one place.

---

## 7. Plugin Structure

```
plugins/java-backend-toolkit/
├── .claude-plugin/plugin.json        # name, version, skills[], agents
├── manifest.json                     # skill registry (in sync with skills/)
├── CHANGELOG.md
├── README.md                         # live SSOT
├── CLAUDE.md                         # plugin-dev context
├── rules/
│   └── ruleset.json                  # §6 single source of truth
├── hooks/
│   ├── jpa-guardrail.py              # PostToolUse, stdlib only
│   └── guardrails-config.json        # per-check toggle, strictChecks[]
├── agents/
│   └── springboot-reviewer.md
├── skills/
│   ├── setup/                        # entry: wire into project (§5.3)
│   ├── jpa-entity/                   # scaffold skill
│   ├── spring-rest-endpoint/         # scaffold skill
│   ├── db-migration/                 # scaffold skill
│   └── springboot-conventions/       # knowledge (split references/)
└── assets/
    └── rules/springboot-rules.md.tmpl  # rule block injected into project CLAUDE.md
```

Every `skills/*/` carries `SKILL.md` (< 500 lines) + `evals.json` (5+ prompts) per repo standard.

---

## 8. Evals (per artifact)

Guardrail hook (the novel part) needs behavioral evals, not just prompt evals:

| Scenario | Expect |
|----------|--------|
| Write `@Entity` with no `@Version` | hook emits `jpa-optimistic-lock` advisory |
| Write `@Entity` **with** `@Version` | hook silent (no false positive) |
| Write `@Entity` with `// jbt:ignore jpa-optimistic-lock` | hook silent (escape hatch honored) |
| Write `@Transactional private void` | hook emits `tx-proxy` advisory |
| `@RestController` returns DTO | hook silent |
| `@Query("... " + var)` with `strictChecks=[jpql-injection]` | non-zero exit (blocks) |
| `jpa-entity` scaffold | output contains `@Version`, safe equals/hashCode, audit fields |
| `springboot-reviewer` on a diff with N+1 | flags it, cites the `ruleset.json` id |

Each scaffold skill: 5+ prompt evals per repo standard.

---

## 9. Files to Create

| File | Notes |
|------|-------|
| `plugins/java-backend-toolkit/.claude-plugin/plugin.json` | name, version 0.1.0, skills[], agents |
| `plugins/java-backend-toolkit/manifest.json` | skill registry |
| `plugins/java-backend-toolkit/{README,CHANGELOG,CLAUDE}.md` | docs |
| `plugins/java-backend-toolkit/rules/ruleset.json` | §6 SSOT, 6 v1 rules |
| `plugins/java-backend-toolkit/hooks/jpa-guardrail.py` | PostToolUse, reads ruleset.json |
| `plugins/java-backend-toolkit/hooks/guardrails-config.json` | toggles + strictChecks |
| `plugins/java-backend-toolkit/agents/springboot-reviewer.md` | tuned reviewer |
| `plugins/java-backend-toolkit/skills/setup/**` | entry installer |
| `plugins/java-backend-toolkit/skills/{jpa-entity,spring-rest-endpoint,db-migration}/**` | scaffolds |
| `plugins/java-backend-toolkit/skills/springboot-conventions/**` | knowledge + references/ |
| `plugins/java-backend-toolkit/assets/rules/springboot-rules.md.tmpl` | project rule block |

### Update (starter side, same PR — atomic)
| File | Change |
|------|--------|
| `plugins/starter/skills/.../stack-recipes.json` (new) | `spring-boot` recipe → points to toolkit |
| `plugins/starter/skills/init/SKILL.md` | detect Spring Boot → offer toolkit (Tier 1) |
| `.claude-plugin/marketplace.json` | register `shipwithai-java-backend-toolkit` |

---

## 10. Open Questions — Proposed Resolutions

| Question | Proposed resolution |
|----------|--------------------|
| Name/namespace verbosity (`/shipwithai-java-backend-toolkit:jpa-entity`) | Keep published name; consider dir slug `java-backend` + short alias. **Confirm with user.** |
| Hooks advisory or blocking? | **Advisory by default**, `strictChecks[]` opt-in for injection-class only. |
| Own reviewer agent vs reuse ECC `java-reviewer`? | **Own**, but thin — its checklist *is* `ruleset.json`. Sharper + SSOT-aligned. |
| Heuristic false positives | Accept; mitigate with advisory tone + per-check toggle + `// jbt:ignore` escape hatch. |
| Kotlin? | **Deferred.** v1 = Spring Boot + JPA only (§2). |
| Who fills project-specific slots? | toolkit `setup` interview, seeded by codebase scan + starter-context.json. |
| Guardrail on Write only, or Edit too? | **Both** (`Edit` + `Write` on `*.java`); re-check on every modification. |
| v1 focus confirmed guardrail-first? | **Yes** per §0 — knowledge layer is supporting, not lead. |

---

## 11. Version

Ships as `shipwithai-java-backend-toolkit` **v0.1.0** (new plugin). starter changes (stack-recipe + detection) ship as a starter **minor bump**, same PR.
