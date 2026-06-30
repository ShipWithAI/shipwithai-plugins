---
description: Iterate on a Compose screen until it passes the structural gate + visual evaluator — renders the stress matrix, grades it in a separate lane, logs findings to the ledger. Caps at 4 iterations then escalates.
argument-hint: <ScreenName> (e.g. SongsScreen)
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Task
---

Iterate on **$ARGUMENTS** until it passes, then stop. Hard cap: **4 iterations**, then escalate to the human.

**Two lanes, kept apart.** *You* are the executor: you edit the `@Composable` and run the gates. The **evaluator is a separate subagent in a fresh context** (step 4) — never grade your own edits, that's the self-review this loop exists to prevent.

## 0. Locate + resolve target

- `Glob` for the screen's inspection test: `**/*$ARGUMENTS*Inspection.kt` (convention: `<Screen>Inspection`). From its path derive three things: the **Gradle module** (e.g. `:feature:chord-smoother:impl`), the **test FQN** (e.g. `com.linh.pianoflow.feature.chordsmoother.impl.presentation.SongsScreenInspection`), and the **PNG dir** (`<module>/build/outputs/roborazzi/`).
- **No inspection test yet?** Create one first, following the stress-matrix pattern in `CLAUDE.md` ("Visual inspection…") and `SongsScreenInspection` — width {360,411} × fontScale {1.0,1.5,2.0} × {light,dark} × content {default,long,empty,error}, each capturing to `_inspect_*.png` then calling `Tier1Assertions.assertAll`.
- **Target:** if `harness/targets/$ARGUMENTS.png` exists → *Fidelity mode* (evaluator reports deltas vs target). Else → *absolute rubric* mode. (No targets exist today; absolute mode in practice.)

## 1. Implement / edit (executor lane)

Edit the `@Composable` for **$ARGUMENTS**. Rails:
- **Reuse** `core:designsystem` — check `docs/components/COMPONENTS.md` before building anything new.
- **Tokens, not literals:** `AppColors` / `Spacing` / `AppType` / `AppShapes` (and `MaterialTheme.*` only inside `core:designsystem`).
- **Insets:** top-level screens consume `WindowInsets` (status/nav bars, IME).
- **No raw Material 3 in feature code** — the Konsist gate (step 2) fails the build if you import `androidx.compose.material3.*`. Add/reuse a `core:designsystem` wrapper instead.

## 2. Cheap gate — boundaries (deterministic, no render)

```bash
./gradlew :androidApp:testDebugUnitTest --tests "com.linh.pianoflow.architecture.ArchitectureTest"
```
On failure: the message names the offending file/import. Fix it and repeat step 1. Clear this before rendering — it's fast and catches reuse/boundary mistakes a vision pass shouldn't waste effort on.

## 3. Render + Tier-1 (one Gradle task)

Record the matrix for the screen, e.g. for `SongsScreen`:
```bash
./gradlew :feature:chord-smoother:impl:testAndroidHostTest \
  --tests "com.linh.pianoflow.feature.chordsmoother.impl.presentation.SongsScreenInspection" \
  -Proborazzi.test.record=true
```
This writes `<module>/build/outputs/roborazzi/_inspect_*.png` **and** runs `Tier1Assertions` (capture happens *before* the assert, so PNGs land even when Tier-1 fails). A Tier-1 failure = a structural blocker (zero-size, touch-target, out-of-bounds, truncation); its message names the element and it drops a `_findings.jsonl` sidecar — leave the sidecar, step 5 collects it. Fix structural blockers (back to step 1) until Tier-1 is clean before spending a vision pass.

## 4. Evaluate (separate lane)

Dispatch the evaluator subagent — `Task` with `subagent_type: "mobile-design-evaluator"` — pointed at the PNG dir. It reads every PNG, grades against the `mobile-design` rubric (Tier-1 structural → Tier-2 taste, or fidelity-vs-target), writes `_verdict.md` + `_eval_findings.jsonl` beside the PNGs, and returns a `pass`/`fail` verdict with element-level fixes. Do **not** grade the screen yourself.

The evaluator keys each finding's `screen` on the PNG's **leading filename token** (`songs`/`field`/`picker`), matching the Tier-1 lane — so don't hand it a single screen name to stamp; a dir may mix components (e.g. `ChordPickerInspection` renders both `field` and `picker`).

## 5. Aggregate the ledger

Fold this iteration's Tier-1 + evaluator findings into the durable ledger:
```bash
python3 harness/bin/aggregate_ledger.py --iteration <N>
```
(`<N>` = current iteration number.) See `harness/ledger/README.md`.

## 6. Decide

- **`pass`** (Tier-1 clean **and** rubric pass / fidelity diff < tolerance): done. If the screen has a *committed regression golden* (e.g. `ChordPickerScreenshotTest`), re-record it to bless the intentional change (`-Proborazzi.test.record=true`); inspection-only screens have no golden to promote. **Stop.**
- **`fail` and iteration < 4:** apply the verdict's **Tier-1 fixes first**, then Tier-2; loop from step 1 with the iteration incremented.
- **iteration == 4 and still failing:** **stop and escalate** — report the outstanding findings and the `_verdict.md` path to the human. Do not loop further.

**Stop conditions:** Tier-1 clean AND (fidelity diff < tolerance OR rubric pass).

> Heavy work (Gradle render, evaluator dispatch) lives here, not in an edit hook — the gates are Gradle tests, far too slow to run per keystroke. Run `/ui-iterate $ARGUMENTS` after a batch of `@Composable` edits, not after each one.
