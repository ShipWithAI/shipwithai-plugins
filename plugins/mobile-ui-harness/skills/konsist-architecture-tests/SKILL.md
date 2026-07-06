---
name: konsist-architecture-tests
description: Use when adding or extending automated module-boundary / architecture enforcement in a Kotlin or Kotlin Multiplatform Gradle project — rules like "core must not depend on feature", "api must not leak impl", layer/package dependency directions that should fail the build the moment a bad import is written. Covers tool choice (Konsist vs ArchUnit/Detekt), the scan-from-disk scaffold, and verifying a rule actually bites.
---

# Konsist architecture tests

## Overview

Enforce module-boundary invariants as **plain JVM unit tests** with [Konsist](https://docs.konsist.lemonappdev.com), which parses Kotlin source straight from disk. Each violation turns the suite red the moment a forbidding `import` is written — before review, before the dependency graph is even wired. The check is on **imports** (source-level), the right altitude: a stray `dependencies {}` edge can sit unnoticed, but the first illegal `import` that relies on it fails.

## Why Konsist — not ArchUnit or Detekt

This is the non-obvious decision; get it right first.

- **ArchUnit** reads compiled **bytecode** off a classpath. A pure `commonMain` / `iosMain` KMP module never hands a JVM test task its bytecode, so ArchUnit can't see that code at all. Konsist reads **source**, so it sees every source set.
- **Detekt** wants a Gradle plugin per module; on `com.android.kotlin.multiplatform.library` (AGP 9) plugin-compat lags and KMP source-set wiring is awkward.
- **Konsist** needs no plugin and no classpath: `Konsist.scopeFromProject()` walks the whole repo from a single host test — the same "rule as a host test" shape as other structural checks. One prevention mechanism, not two.

## Where it lives + wiring

Put it in one JVM `test` source set that runs `testDebugUnitTest` — conventionally the **app module** (it already depends on everything, but Konsist scans the whole project from disk regardless of which module hosts the test):

```
app/src/test/kotlin/<base.package>/architecture/ArchitectureTest.kt
```

Add the dependency to that module: `testImplementation(libs.konsist)` (catalog: `konsist = { module = "com.lemonappdev:konsist", version.ref = "konsist" }`). Run just these rules:

```bash
./gradlew :app:testDebugUnitTest --tests "<base.package>.architecture.ArchitectureTest"
```

## Survey the graph, then write one rule per edge

Read `settings.gradle(.kts)` and the module folders. For each *intended* dependency direction (`core ← feature`, `api` is a seam over `impl`, `domain ↛ data`, …), write one `@Test`. Don't invent rules the project doesn't hold.

## The canonical scaffold

Rules key on the **on-disk Gradle module path** (`core/audio`, `feature/foo/api`) derived from each file's `projectPath`, over **production source only** — never on bytecode, and never only on package names. Three helpers carry that; copy them verbatim:

```kotlin
package com.example.app.architecture

import com.lemonappdev.konsist.api.Konsist
import com.lemonappdev.konsist.api.declaration.KoFileDeclaration
import com.lemonappdev.konsist.api.verify.assertFalse
import org.junit.Test

class ArchitectureTest {

    private val files: List<KoFileDeclaration> = Konsist.scopeFromProject().files

    /** Core modules are foundational — they must never depend on a feature. */
    @Test
    fun `core does not depend on feature`() {
        files
            .filter { it.isProductionSource() && it.modulePath().startsWith("core/") }
            .assertFalse { file ->
                file.hasImport { it.name.startsWith("com.example.app.feature.") }
            }
    }

    /** A feature's public `api` contract must not leak its own `impl` internals. */
    @Test
    fun `feature api does not depend on feature impl`() {
        files
            .filter {
                it.isProductionSource() &&
                    it.modulePath().startsWith("feature/") &&
                    it.modulePath().endsWith("/api")
            }
            .assertFalse { file ->
                file.hasImport {
                    it.name.startsWith("com.example.app.feature.") && it.name.contains(".impl.")
                }
            }
    }
}

/** Source-set folder (the path segment after `src/`); null for build/generated or non-source files. */
private fun KoFileDeclaration.sourceSet(): String? {
    val segs = projectPath.trimStart('/').split('/')
    if ("build" in segs) return null
    val i = segs.indexOf("src")
    return if (i >= 0) segs.getOrNull(i + 1) else null
}

/** True for main/production source sets; excludes test, commonTest, androidHostTest, etc. */
private fun KoFileDeclaration.isProductionSource(): Boolean {
    val ss = sourceSet() ?: return false
    return ss != "test" && !ss.endsWith("Test")
}

/** Gradle module path = everything before /src/, e.g. feature/chord-smoother/impl. */
private fun KoFileDeclaration.modulePath(): String =
    projectPath.trimStart('/').substringBefore("/src/")
```

## Adding a rule (the recipe)

1. `filter` to `isProductionSource()` **and** the modules the rule governs, by `modulePath()`.
2. `assertFalse { file.hasImport { it.name.startsWith("<forbidden import prefix>") } }`.
3. Name the `@Test` after the invariant, in backticks.

The `.impl.` import-substring check is enough **when packages encode the module** (the common case: `feature/foo/impl` → `…feature.foo.impl.*`). Only if packages don't encode the module — or you must forbid importing *another* feature's impl — pair `api`↔`impl` by module-path feature name. Don't reach for that extra machinery by default; it's complexity the simple check doesn't need.

## Verify the rule BITES — required

A green suite proves nothing until you have watched it go red. After adding a rule, **plant a violation**: add the forbidden `import` in a governed production file, run the test, and confirm it FAILS *naming that file*. Then revert and confirm green. Skip this and a misfiltered rule (wrong `modulePath` prefix, scanning test source, a typo'd package prefix) silently filters to **zero files** and passes forever — enforcing nothing while looking enforced.

**Back the one-time check with a permanent guard.** The planted-violation test is manual and runs once; add a rule that *stays* in the suite and fails the day a selector silently matches zero files:

```kotlin
@Test
fun `boundary selectors match real files (guard against vacuous pass)`() {
    val core = files.filter { it.isProductionSource() && it.modulePath().startsWith("core/") }
    val featureApi = files.filter {
        it.isProductionSource() && it.modulePath().startsWith("feature/") && it.modulePath().endsWith("/api")
    }
    assert(core.isNotEmpty()) { "core/ selector matched 0 files — prefix or source-set filter is wrong" }
    assert(featureApi.isNotEmpty()) { "feature/**/api selector matched 0 files — selector is wrong" }
}
```

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Scanning all files | test-only imports trip the rule | filter `isProductionSource()` |
| Keying on package names only | misses kebab-case modules, wrong pairing | derive `modulePath()` from `projectPath` |
| Never planting a violation | rule filters to 0 files, passes forever | the BITES step above |
| ArchUnit on a KMP module | `commonMain`/`iosMain` code invisible | Konsist (reads source, not bytecode) |
| Reinventing api↔impl pairing | fragile extra helpers | the `.impl.` substring check suffices when packages encode the module |
