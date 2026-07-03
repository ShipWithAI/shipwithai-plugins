---
description: Iterate on a Compose screen until it passes the structural gate + visual evaluator — renders the stress matrix, grades it in a separate lane, logs findings to the ledger. Caps at 4 iterations then escalates.
argument-hint: <ScreenName> (e.g. SongsScreen)
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Task
---

Iterate on **$ARGUMENTS** until it passes, then stop. Hard cap: **4 iterations**, then escalate to the human.

**Two lanes, kept apart.** *You* are the executor: you edit the `@Composable` and run the gates. The **evaluator is a separate subagent in a fresh context** (step 4) — never grade your own edits, that's the self-review this loop exists to prevent.

> Commands below use placeholders (`<app-module>`, `<module>`, `<your.pkg>`) and `e.g.` examples. Derive the real values from *this* project in step 0 — never run the example coordinates verbatim.

## 0. Locate + resolve target

- `Glob` for the screen's inspection test: `**/*$ARGUMENTS*Inspection.kt` (convention: `<Screen>Inspection`, seeded by the `setup` skill). From its path derive three things: the **Gradle module** (e.g. `:feature:foo:impl`), the **test FQN** (e.g. `com.acme.feature.foo.impl.presentation.<Screen>Inspection`), and the **PNG dir** (`<module>/build/outputs/roborazzi/`).
- **No inspection test yet?** Create one from the template the `setup` skill installs (`assets/substrate/ScreenInspection.kt.tmpl`; see INTEGRATION.md) — width {360,411} × fontScale {1.0,1.5,2.0} × {light,dark} × content {default,long,empty,error}, each capturing to `_inspect_*.png` then calling `Tier1Assertions.assertAll`.
- **Target:** if `harness/targets/$ARGUMENTS.png` exists → *Fidelity mode* (evaluator reports deltas vs target). Else → *absolute rubric* mode.

## 1. Implement / edit (executor lane)

Edit the `@Composable` for **$ARGUMENTS**. Rails (apply whichever your project has):
- **Reuse your design system** — check your component catalog before building anything new.
- **Tokens, not literals** — use your theme's color/spacing/type/shape tokens (keep raw `MaterialTheme.*` inside the design-system module).
- **Insets:** top-level screens consume `WindowInsets` (status/nav bars, IME).
- **Boundary gate:** if your project enforces a design-system / Material-3 boundary (e.g. via the `konsist-architecture-tests` skill or a Konsist rule), satisfy it — add or reuse a wrapper rather than importing the gated API directly.

## 2. Cheap gate — boundaries (deterministic, no render)

If your project has an architecture/boundary test (e.g. installed via the `konsist-architecture-tests` skill), run it first — it's fast and catches reuse/boundary mistakes a vision pass shouldn't waste effort on. Substitute your own app module + architecture-test FQN:

```bash
# e.g. — replace <app-module> and <your.pkg> with this project's values
./gradlew :<app-module>:testDebugUnitTest --tests "<your.pkg>.architecture.ArchitectureTest"
```

On failure: the message names the offending file/import. Fix it and repeat step 1. (No such gate in this project? Skip to step 3.)

## 3. Render + Tier-1 (one Gradle task)

Record the matrix for the screen — substitute the module + FQN from step 0:
```bash
./gradlew :<module>:testAndroidHostTest \
  --tests "<your.pkg>.<Screen>Inspection" \
  -Proborazzi.test.record=true
```
This writes `<module>/build/outputs/roborazzi/_inspect_*.png` **and** runs `Tier1Assertions` (capture happens *before* the assert, so PNGs land even when Tier-1 fails). A Tier-1 failure = a structural blocker (zero-size, touch-target, out-of-bounds, truncation); its message names the element and it drops a `_findings.jsonl` sidecar — leave the sidecar, step 5 collects it. Fix structural blockers (back to step 1) until Tier-1 is clean before spending a vision pass.

## 4. Evaluate (separate lane)

Dispatch the evaluator subagent — `Task` with `subagent_type: "mobile-design-evaluator"` — pointed at the PNG dir. It reads every PNG, grades against the `mobile-design` rubric (Tier-1 structural → Tier-2 taste, or fidelity-vs-target), writes `_verdict.md` + `_eval_findings.jsonl` beside the PNGs, and returns a `pass`/`fail` verdict with element-level fixes. Do **not** grade the screen yourself.

The evaluator keys each finding's `screen` on the PNG's **leading filename token** — matching the Tier-1 lane — so don't hand it a single screen name to stamp; one inspection dir may mix components.

## 5. Aggregate the ledger

Fold this iteration's Tier-1 + evaluator findings into the durable ledger:
```bash
python3 harness/bin/aggregate_ledger.py --iteration <N>
```
(`<N>` = current iteration number.) See `harness/ledger/README.md`.

## 6. Decide

- **`pass`** (Tier-1 clean **and** rubric pass / fidelity diff < tolerance): done. If the screen has a *committed regression golden*, re-record it to bless the intentional change (`-Proborazzi.test.record=true`); inspection-only screens have no golden to promote. **Stop.**
- **`fail` and iteration < 4:** apply the verdict's **Tier-1 fixes first**, then Tier-2; loop from step 1 with the iteration incremented.
- **iteration == 4 and still failing:** **stop and escalate** — report the outstanding findings and the `_verdict.md` path to the human. Do not loop further.

**Stop conditions:** Tier-1 clean AND (fidelity diff < tolerance OR rubric pass).

> Heavy work (Gradle render, evaluator dispatch) lives here, not in an edit hook — the gates are Gradle tests, far too slow to run per keystroke. Run `/ui-iterate $ARGUMENTS` after a batch of `@Composable` edits, not after each one.
