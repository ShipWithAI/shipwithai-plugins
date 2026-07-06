# shipwithai-mobile-ui-harness — Claude context

A self-improving Compose Multiplatform UI harness. **Architecture seam** to keep in mind when
editing: the **brain** (the loop, the JSONL ledger, aggregate/distill/metrics, the evaluator, the
rubric) is substrate-agnostic; the **substrate** (`Tier1Assertions`, the Roborazzi convention
plugin, the inspection-test matrix, Konsist rails) is Compose/Kotlin-specific. Anything that only
knows the finding schema stays in the brain.

## Map

- `skills/setup/` — scaffolds the per-repo half (`assets/`) into a project; package-parameterized.
- `skills/mobile-design/` — the evaluator rubric (Tier-1 structural → Tier-2 taste).
- `skills/konsist-architecture-tests/` — generate a Konsist module-boundary test.
- `commands/ui-{iterate,distill,metrics}.md` — the loop drivers (heavy Gradle/agent work; run
  after a batch of edits, not per keystroke).
- `agents/mobile-design-evaluator.md` — the vision lane; never edits source, only writes a verdict.
- `assets/` — templates the `setup` skill installs: `harness/bin/*.py` (self-tested ledger tools),
  `harness/ledger/`, `substrate/*.kt.tmpl`, `INTEGRATION.md`.

## Conventions

- `manifest.json` lists every skill — keep it in sync with `skills/` (never add a skill without
  updating the manifest).
- The `mobile-design` and `konsist-architecture-tests` skill bodies are vendored from the upstream
  `compose-ui-harness`; keep them byte-aligned to ease re-syncing.
- The Python ledger tools are self-tested: `python3 assets/harness/bin/test_*.py` must stay green.
- `assets/` are template files consumed verbatim downstream — edits change what `setup` generates
  in user projects.
