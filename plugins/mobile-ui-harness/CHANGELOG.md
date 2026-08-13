# Changelog

All notable changes to `shipwithai-mobile-ui-harness` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

## [0.1.0] — 2026-06-30

Initial release — the self-improving Compose Multiplatform UI harness.

### Added
- **Skill** `setup` — scaffolds the harness into a project: `harness/` ledger + Python tools
  (aggregate/distill/metrics), `Tier1Assertions`, the Roborazzi screenshot-testing convention
  plugin, and an inspection-test template (all package-parameterized).
- **Skill** `mobile-design` — evaluator rubric (Tier-1 structural blockers → Tier-2 taste) for
  grading rendered Compose Material 3 screens.
- **Skill** `konsist-architecture-tests` — generate a Konsist module-boundary test for a
  Kotlin/KMP project, including the verify-it-bites discipline and a permanent vacuous-pass guard.
- **Agent** `mobile-design-evaluator` — the vision-grading lane; reads rendered PNGs and writes a
  pass/fail verdict + ledger findings, never edits source.
- **Commands** `/ui-iterate`, `/ui-distill`, `/ui-metrics` — drive the render→grade loop, promote
  recurring findings into permanent gates, and trend whether the harness is compounding.
- **Assets** — `harness/bin/*.py` (self-tested ledger tools), the ledger schema + screen-alias
  map, Kotlin substrate templates, and `INTEGRATION.md` (Roborazzi/Robolectric build wiring).
