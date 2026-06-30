# shipwithai-ui-harness

A self-improving UI harness for **Compose Multiplatform** projects, packaged as a ShipWithAI
Claude Code plugin. It turns "did that `@Composable` edit actually render correctly?" into a
deterministic loop — and, the point, it **compounds**: recurring findings ratchet into permanent
gates so the soft guidance shrinks over time.

## The three layers

```
PREVENT (rails) ─────► GATE + GRADE (loop) ─────► RATCHET (compounding learnings)
Konsist boundary tests   /ui-iterate drives:        findings.jsonl (committed ledger)
design tokens            1. cheap gate (no render)     ▲          │
                         2. render matrix + Tier-1     │ deposit   ▼
                         3. evaluator (fresh lane)   aggregate → distill → metrics
                         4. aggregate ledger
        ▲                                                 │
        └────── promote a recurring finding, then delete its soft guidance ◄──┘
```

Two finding producers emit the **same JSONL schema**: a deterministic `Tier1Assertions` (walks the
Compose semantics tree) and the `mobile-design-evaluator` agent (vision, run in a separate context
so it never grades its own edits). Everything downstream of that schema — the ledger,
aggregate/distill/metrics, the ratchet — is substrate-agnostic.

## Install

```bash
/plugin marketplace add ShipWithAI/shipwithai-plugins
/plugin install shipwithai-ui-harness@shipwithai
```

## Quickstart

```bash
/shipwithai-ui-harness:setup com.acme.app --module feature/foo/impl   # scaffold the harness into a Compose/KMP repo
/ui-iterate FooScreen                           # render → grade → log, capped at 4 iterations
/ui-distill                                     # promote recurring findings into permanent gates
/ui-metrics                                     # is it compounding?
```

## What's inside

| Kind | Name | Role |
|---|---|---|
| skill | `setup` | scaffold the harness (ledger + Python tools + Kotlin substrate) into a project |
| skill | `mobile-design` | evaluator rubric: Tier-1 structural → Tier-2 taste |
| skill | `konsist-architecture-tests` | generate a Konsist module-boundary test |
| agent | `mobile-design-evaluator` | the vision grading lane (writes verdict + ledger findings) |
| command | `/ui-iterate` | the executor-evaluator loop driver (cap 4, then escalate) |
| command | `/ui-distill` | cluster recurring findings → promote to gates, delete redundant guidance |
| command | `/ui-metrics` | trend iterations-to-pass, first-pass yield, recurrence-after-deposit |

## Requirements

Compose Multiplatform + Roborazzi + Robolectric on an `androidHostTest` source set. The `setup`
skill and `assets/INTEGRATION.md` cover the build wiring (version-catalog aliases, the convention
plugin, the six coupling points). Kotlin-specific — not for web or native-iOS UIs.

## Layout

```
plugins/ui-harness/
├── skills/{setup,mobile-design,konsist-architecture-tests}/  SKILL.md + evals.json
├── commands/ui-{iterate,distill,metrics}.md
├── agents/mobile-design-evaluator.md
└── assets/
    ├── harness/bin/*.py            # aggregate / distill / metrics (+ self-tests)
    ├── harness/ledger/             # schema (README.md) + screen-aliases.json
    ├── substrate/*.kt.tmpl         # Tier1Assertions, convention plugin, inspection test
    └── INTEGRATION.md              # Roborazzi/Robolectric build wiring + the 6 coupling points
```
