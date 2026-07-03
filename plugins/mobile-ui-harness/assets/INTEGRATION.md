# Substrate integration (Compose Multiplatform + Roborazzi)

The plugin's commands/skill/agent are stack-agnostic. The **substrate** — the part that
actually renders a screen and deterministically asserts its structure — assumes a Kotlin
Multiplatform module that targets Android via `com.android.kotlin.multiplatform.library`,
with Roborazzi + Robolectric on the `androidHostTest` source set. This is the wiring.

> Convention-id prefix: pick your own (this doc uses `acme.*`; the source project used
> `pianoflow.*`). Keep it consistent across `build-logic` and the modules that apply it.

## Version-catalog aliases (`gradle/libs.versions.toml`)

The convention plugin (`ComposeScreenshotTestingConventionPlugin`) resolves these aliases by
name — add any you don't already have:

```toml
[versions]
junit = "4.13.2"
roborazzi = "1.43.1"
robolectric = "4.15.1"            # pinned: supports up to SDK 35 (see caveat below)
# composeMultiplatform / composeUiTestJunit4 — reuse your existing Compose versions

[libraries]
junit                          = { module = "junit:junit", version.ref = "junit" }
kotlin-testJunit               = { module = "org.jetbrains.kotlin:kotlin-test-junit", version.ref = "kotlin" }
robolectric                    = { module = "org.robolectric:robolectric", version.ref = "robolectric" }
roborazzi                      = { module = "io.github.takahirom.roborazzi:roborazzi", version.ref = "roborazzi" }
roborazzi-compose              = { module = "io.github.takahirom.roborazzi:roborazzi-compose", version.ref = "roborazzi" }
roborazzi-junit-rule           = { module = "io.github.takahirom.roborazzi:roborazzi-junit-rule", version.ref = "roborazzi" }
roborazzi-gradlePlugin         = { module = "io.github.takahirom.roborazzi:roborazzi-gradle-plugin", version.ref = "roborazzi" }
androidx-compose-ui-testJunit4 = { module = "androidx.compose.ui:ui-test-junit4", version.ref = "composeUiTestJunit4" }
androidx-compose-ui-testManifest = { module = "androidx.compose.ui:ui-test-manifest", version.ref = "composeUiTestJunit4" }
compose-uiTooling              = { module = "org.jetbrains.compose.ui:ui-tooling", version.ref = "composeMultiplatform" }

[plugins]
roborazzi = { id = "io.github.takahirom.roborazzi", version.ref = "roborazzi" }
```

## Build wiring

**1. `build-logic/convention/build.gradle.kts`** — give the convention plugin the Roborazzi
plugin on its compile classpath, and register it:

```kotlin
dependencies {
    compileOnly(libs.roborazzi.gradlePlugin)
    // ...your other convention deps
}

gradlePlugin {
    plugins {
        register("composeScreenshotTesting") {
            id = "acme.compose-screenshot-testing"
            implementationClass = "com.acme.buildlogic.ComposeScreenshotTestingConventionPlugin"
        }
    }
}
```

**2. Each module that renders screens** — apply the convention plugin *last*, after the KMP +
Android library plugins it builds on:

```kotlin
plugins {
    // ...kmp.library / compose plugins
    id("acme.compose-screenshot-testing")
}
```

## Robolectric / SDK caveat

Robolectric 4.15.1 supports up to **SDK 35**. If your `compileSdk` is 36+, every inspection
test must declare `@Config(sdk = [35])` (the template already does) or it dies in
`DefaultSdkPicker`. The KMP test variant is `testAndroidHostTest` (not `testDebugUnitTest`);
the source set is `androidHostTest`.

## How a render run works

```bash
./gradlew :<module>:testAndroidHostTest \
  --tests "<pkg>.<Screen>Inspection" \
  -Proborazzi.test.record=true
```

`-Proborazzi.test.{record,verify,compare}` are project properties the convention plugin
translates into the system properties Roborazzi reads (and registers as task inputs, so
switching modes invalidates the cache — no `--rerun-tasks`). `captureRoboImage(filePath=...)`
resolves relative to the **module dir**, so inspection PNGs land in
`<module>/build/outputs/roborazzi/`.

## gitignore

```gitignore
# regenerated worksheets (durable record is findings.jsonl + the committed gates)
harness/ledger/promotions.md
harness/ledger/metrics.md
# build-local sidecars + inspection captures (hermetic, wiped on clean)
**/build/outputs/roborazzi/_inspect_*.png
**/build/outputs/roborazzi/*_findings.jsonl
```

Keep **`harness/ledger/findings.jsonl` committed** — it's the durable, append-only ledger the
ratchet reads. Committed regression goldens (if you add any) live in
`<module>/src/androidHostTest/screenshots/`.

## The six coupling points

Everything project-specific is one of these — all handled by the `setup` skill:

| # | Point | Where |
|---|---|---|
| 1 | Base package | `Tier1Assertions` (`__TESTING_PACKAGE__`), inspection tests (`__PACKAGE__`) |
| 2 | Module coordinates | the `:module:path` you apply the convention plugin to; `/ui-iterate` discovers it |
| 3 | Ledger root | `harness/ledger/` (path convention; change via the tools' `--ledger`/`--root`) |
| 4 | Sidecar glob | `**/build/outputs/roborazzi/*findings.jsonl` (Roborazzi). Change via `aggregate_ledger.py --sidecar-glob` |
| 5 | Catalog aliases | the `[libraries]`/`[plugins]` names above |
| 6 | Screen-alias map | `harness/ledger/screen-aliases.json` — `{ "MyScreen": "myscreen" }` |

## screen-aliases workflow

Both lanes must agree on a screen's id. The deterministic Tier-1 sidecar emits the inspection
PNG's leading filename slug (`myscreen`); the LLM evaluator tends to emit the composable name
(`MyScreen`). `aggregate_ledger.py` canonicalizes every `screen` through
`screen-aliases.json` (keys matched case/punctuation-insensitively). **Add a row whenever a
new screen or a new evaluator phrasing appears**; unmapped names fall back to a lowercased,
alnum-stripped form.
