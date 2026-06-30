---
name: setup
description: >
  Wire the self-improving UI harness into this Compose Multiplatform project — scaffold the
  harness/ ledger + Python tools, install Tier1Assertions + the Roborazzi screenshot-testing
  convention plugin + an inspection-test template (package-parameterized), and print the build
  wiring. Short interview fills project slots (base package, target module).
  Trigger phrases: "set up the ui harness", "install ui-harness", "wire the compose ui harness",
  "scaffold the screenshot harness".
argument-hint: "[<base.package>] [--module path/to/feature/impl]"
---

# UI Harness — Setup

Installs the **per-repo half** of the harness so it is committed and shared with the team: the
ledger, the Python tools beside it, and the Kotlin substrate. The agentic half (the `mobile-design`
skill, the `mobile-design-evaluator` agent, and `/ui-iterate` · `/ui-distill` · `/ui-metrics`)
ships with the plugin and is already available.

Bundled sources live under `${CLAUDE_PLUGIN_ROOT}/assets/`.

## 0. Prerequisite probe + interview

- Confirm this is **Compose Multiplatform + Roborazzi + Robolectric** (the substrate's
  assumptions). If not, stop and point at `${CLAUDE_PLUGIN_ROOT}/assets/INTEGRATION.md`.
- **Base package** = `$1`, else infer it from an existing `package` declaration and confirm.
- **Target module** = the `--module` value, else `Glob` for a feature `impl` module and ask which
  one. Derive its `androidHostTest` source root.

## 1. Lay down the ledger + tools (verbatim)

```bash
mkdir -p harness/bin harness/ledger
cp "${CLAUDE_PLUGIN_ROOT}/assets/harness/bin/"*.py             harness/bin/
cp "${CLAUDE_PLUGIN_ROOT}/assets/harness/ledger/README.md"    harness/ledger/README.md
cp "${CLAUDE_PLUGIN_ROOT}/assets/harness/ledger/screen-aliases.json" harness/ledger/screen-aliases.json
: > harness/ledger/findings.jsonl    # committed, append-only; starts empty
```

Confirm the tools run here: `python3 harness/bin/test_aggregate_ledger.py` (and the two sibling
`test_*.py`) should all pass.

## 2. Install the deterministic asserter

Copy `Tier1Assertions.kt.tmpl` into the target module's `androidHostTest` `testing` package,
replacing the token with the real package:

```bash
TESTING_PKG="<base.package>.<module-suffix>.testing"   # e.g. com.acme.feature.foo.impl.testing
DEST="<module>/src/androidHostTest/kotlin/$(echo "$TESTING_PKG" | tr . /)"
mkdir -p "$DEST"
sed "s/__TESTING_PACKAGE__.*/$TESTING_PKG/" \
  "${CLAUDE_PLUGIN_ROOT}/assets/substrate/Tier1Assertions.kt.tmpl" > "$DEST/Tier1Assertions.kt"
```

## 3. Install the convention plugin

Copy `ComposeScreenshotTestingConventionPlugin.kt.tmpl` into `build-logic` (replacing
`__BUILDLOGIC_PACKAGE__`), then register it and apply `id("<prefix>.compose-screenshot-testing")`
in each module that renders screens. See `${CLAUDE_PLUGIN_ROOT}/assets/INTEGRATION.md` for the exact
`build-logic` registration block and the version-catalog aliases it expects.

## 4. Seed one inspection test

Copy `${CLAUDE_PLUGIN_ROOT}/assets/substrate/ScreenInspection.kt.tmpl` next to `Tier1Assertions`,
replace `__PACKAGE__` / `__TESTING_PACKAGE__` / `__SCREEN__` / `__screen__` (the lowercase
single-token screen id), and wire the `TODO`s to render your stateless screen content. Add a
`"<ComposableName>": "<screen-id>"` row to `harness/ledger/screen-aliases.json`.

## 5. Wire the build + gitignore

Follow `${CLAUDE_PLUGIN_ROOT}/assets/INTEGRATION.md` §"Build wiring" and §"gitignore": add the
Roborazzi plugin + version-catalog aliases, register the convention plugin, and gitignore
`harness/ledger/promotions.md`, `harness/ledger/metrics.md`, and the
`build/outputs/roborazzi/_inspect_*.png` / `*_findings.jsonl` sidecars (keep
`harness/ledger/findings.jsonl` **committed**).

## 6. Smoke-test the loop

Run `/ui-iterate <YourScreen>` once. It should render the matrix, run Tier-1, dispatch the
evaluator in a fresh lane, and fold findings into `harness/ledger/findings.jsonl`. If it produces a
`_verdict.md`, the harness is live.

> The six coupling points (package, module coords, ledger root, sidecar glob, catalog aliases,
> screen-alias map) are all touched above. Everything else is project-agnostic.
