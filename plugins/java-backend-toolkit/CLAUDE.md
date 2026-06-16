# shipwithai-java-backend-toolkit — Plugin Development Context

> Plugin development workspace. Stack: Markdown + JSON + Python 3 (stdlib) hook.
> Last updated: 2026-06-16.

## Plugin Identity

- **Name:** `shipwithai-java-backend-toolkit`
- **Namespace:** `/shipwithai-java-backend-toolkit:<skill>`
- **Purpose:** Guardrail-first Spring Boot + JPA toolkit — just-in-time hook + scaffold
  skills + knowledge + reviewer agent, all driven by one ruleset.

## Design stance (settled 2026-06-16)

- **Guardrail-first.** The hook (activation) is the differentiator, not the knowledge.
  Generic springboot skills fail because they are passive; do not regress toward that.
- **Single source of truth.** `rules/ruleset.json` is read by BOTH the hook and the
  reviewer agent. Add/change a rule there — never duplicate rule logic in the agent prompt.
- **Generalizable only.** This plugin ships rules true for *all* Spring Boot projects.
  Project-specific conventions (BaseEntity name, soft-delete column) belong in the user's
  `.claude/`, filled by the `setup` interview — never hardcoded here.
- **Scope discipline.** v1 = Spring Boot 3.x + JPA only. Each release adds at most one
  paved road. The broad name must not justify shallow multi-framework coverage.

## File Conventions

- Skill directories: lowercase with dashes (`jpa-entity`)
- SKILL.md: always uppercase filename, < 500 lines (ideal < 300), code snippets < 20 lines
- Full templates live in `assets/` / skill `assets/`, not inline in SKILL.md
- Reference files: lowercase with dashes, < 300 lines, lazy-loaded
- Every skill: a corresponding `evals.json` with 5+ prompts
- The hook is Python 3 **stdlib only**, type-annotated (PEP 8), and must silent-fail

## Ruleset invariant

When you add a rule to `rules/ruleset.json`:
1. Set `hookEnabled` (line-level heuristic feasible?) and `reviewerEnabled` (cross-file?).
2. Add a hook test fixture and verify advisory vs block behavior.
3. The `springboot-conventions` references should explain its *why* and cite its `id`.
4. The `springboot-reviewer` agent reads the ruleset at runtime — no prompt edit needed.

## Hook mechanics

- Resolves `ruleset.json` from `./ruleset.json` (installed flat) or `../rules/ruleset.json` (source).
- Advisory → JSON `hookSpecificOutput.additionalContext`, exit 0.
- Strict (`strictChecks` ∩ `strictEligible`) → stderr, exit 2 (blocks).
- Match strategies: `file-has-without`, `regex`, `reviewer-only`.

## Integration

`shipwithai-starter` detects Spring Boot and routes here (launcher model). The toolkit's
`setup` skill is the entry point; it installs the enforcement layer into the project's
`.claude/` so it is committed and team-shared.
