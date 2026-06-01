# Project Facts

*Add decisions and facts that Claude should remember across sessions.*

## Key decisions
- Content-only workspace: no runtime, no build step, no package manager
- Plugin standard: ShipWithAI Claude Code plugin standard (SKILL.md + manifest.json + evals.json)
- SSOT rule: README.md and plugin docs must be updated after every plugin/skill change
- manifest.json must stay in sync with skills/ directory structure at all times
- assets/ directories contain templates used verbatim in user projects — changes have downstream impact

## Known constraints
- SKILL.md hard cap: 500 lines (ideal < 300)
- Skill descriptions: < 200 characters, must include trigger phrases
- Every skill needs evals/evals.json with 5+ test prompts
- Test every skill on 2+ real projects before shipping
- Never create or modify skills without an approved plan (PLAN.md first)

## Future work
- Telegram release notification via GitHub Actions when tag pushed to main (not yet implemented)
- CI/CD: auto-build .plugin file and validate plugin structure on PR (not yet implemented)
