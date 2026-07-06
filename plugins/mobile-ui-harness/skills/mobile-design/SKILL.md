---
name: mobile-design
description: >-
  Evaluation criteria for grading rendered mobile UI screens. Use when reviewing,
  critiquing, or self-checking a mobile UI screenshot — especially after any UI
  edit in an agentic loop — to decide pass/fail and produce concrete fixes.
  Targets Compose Multiplatform (Android + iOS), Material 3. The mobile counterpart
  to frontend-design: structural integrity first ("is it broken?"), visual taste second.
---

# Mobile UI design evaluation

This skill is a rubric for an **evaluator**, not a generator. Given a rendered screen
(a screenshot, ideally one per device config), grade it against the criteria below and
return a verdict plus specific, element-level fixes.

The ordering is deliberate and matches how mobile agent output actually fails: most
defects are **structural** (clipped, overlapping, off-grid) before they are **tasteless**.
Catch broken layouts first — they are hard fails — then judge polish.

## How to use this skill

- **When**: reviewing a mobile UI screenshot, or after the implementer edits any
  `@Composable` and re-renders. Pair it with the screenshot harness (Roborazzi / emulator
  capture). Anything a deterministic layout assertion already caught does not need
  re-judging here; this skill covers what assertions can't see plus all of taste.
- **Two passes**: Tier 1 (structural integrity) → any violation is a blocker. Tier 2
  (visual quality) → weighted issues, reported but not auto-failing unless they pile up.
- **Output**: a verdict (`pass` / `fail`), violations grouped by tier, each naming the
  **element**, the **config it appears in**, and a **concrete fix**. Never return "looks
  off" — always say what and where.

## Evaluation protocol — render the matrix

Most "broken" only shows under stress. Evaluate each screen across this matrix and grade
the worst case, not the happy path:

- **Default** — reference device (e.g. Pixel-class, ~411dp wide).
- **Compact width** — ~360dp or narrower (small phones, split screen).
- **Large font scale** — `fontScale` 1.5 and 2.0 (accessibility text size). This is where
  overflow and truncation surface.
- **Dark mode** — both light and dark.
- **Long content** — longest realistic strings, large numbers, missing images.
- **RTL** — only if the app localizes to RTL.

A defect in any config is a defect.

---

## Tier 1 — Structural integrity (blockers)

Each item is a **hard fail**. Fix before evaluating taste. These are the "is it broken?"
checks, severity-ranked.

1. **Overflow & clipping** — content cut off at a screen or container edge; rows wider than
   the viewport; text or controls pushed off-screen. Check first at `fontScale` 1.5+.
2. **Unintended truncation** — labels, buttons, prices, or numbers showing `…` or cut
   digits where the full value must be visible. Prefer wrap or resize over ellipsis for
   critical text.
3. **Overlap / z-fighting** — composables drawn on top of one another; text over text; FAB
   or bottom bar covering actionable content; shadows bleeding into neighbors.
4. **Zero-size / collapsed elements** — a node that measured to 0 width or height (missing
   size, a `weight` with no space, an empty image slot). Invisible content and untappable
   targets.
5. **Inset / safe-area violations** — content under the status bar, notch/cutout, or home
   indicator; not consuming `WindowInsets` (status bars, navigation bars, IME). Header text
   under the clock; the last list item hidden behind the nav bar.
6. **Touch target size** — interactive elements smaller than **48×48 dp** (Android) /
   **44×44 pt** (iOS). Icon buttons and chips are the usual offenders.
7. **Keyboard (IME) handling** — focused field obscured by the keyboard; form not scrollable
   while the IME is open; submit button trapped behind the keyboard.
8. **Misalignment** — elements off the spacing grid; ragged left/right edges where items
   should share a margin; inconsistent margins on the same screen.
9. **Readability-breaking contrast** — text or essential icons below WCAG AA
   (4.5:1 body text, 3:1 large text and UI components). Light-gray-on-white, low-contrast
   placeholder mistaken for a value.
10. **Scroll / viewport failures** — content taller than the screen with no scroll; bottom
    actions clipped; nested scroll conflicts; sticky elements that cover content.
11. **Missing core states** — list with no empty state; screen with no loading and no error
    state; a permanent skeleton or spinner.

If any Tier-1 item is present → **VERDICT: fail**. Stop and return fixes.

---

## Tier 2 — Visual quality (weighted polish)

The "is it tasteless?" axis. Report every issue; fail only if several stack up on one screen.

### Hierarchy & focus
- Exactly **one** clear primary action per screen. Not three filled buttons competing.
- A single focal point; the eye knows where to land first.
- Type scale carries hierarchy (display / headline / title / body / label) — not
  medium-weight-everything.
- Visual weight (size, color, position) matches importance.

### Spacing & rhythm
- Spacing comes from a scale (**4 / 8 dp grid**). No stray 13 dp, 17 dp, 23 dp values.
- Intentional whitespace: not cramped edge-to-edge, not adrift in a void.
- Padding is consistent within a component and between sibling components.
- Related items grouped (proximity); unrelated items separated.

### Color & theming
- Colors come from the **Material 3 theme color roles** (`primary`, `secondary`,
  `surface`, `onSurface`, `surfaceVariant`, …), not hardcoded hex.
- Restrained palette; color signals meaning (state, action), it doesn't decorate.
- Real tonal/elevation hierarchy between surfaces. Dark mode is purpose-built, not a
  broken inversion (no pure-black-on-pure-white, no glowing shadows).
- The default seed-purple theme is **not** left untouched.

### Typography
- One type family; a limited, deliberate ramp.
- Body text ≥ 14–16 sp; no walls of dense small text.
- Line height and letter spacing follow M3; lines not jammed together.
- Start-aligned by default; centering used sparingly and on purpose (never center every
  block of text).

### Components & platform idiom
- Correct M3 components and variants (`Button` vs `OutlinedButton` vs `TextButton`,
  `Card`, `TopAppBar`, `NavigationBar`, `ListItem`) instead of hand-rolled lookalikes.
- Elevation used meaningfully — not heavy shadows on every card.
- States are designed: pressed, disabled, focused, selected, error.
- Iconography consistent in style, weight, and size; aligned to text baselines.
- Platform conventions respected where they matter (back navigation, system bars,
  edge gestures, native pickers/sheets).

### Content & resilience
- Realistic content, not placeholder/lorem leaking into the render.
- Graceful with edge content: very long names, empty strings, 0 and 7-digit numbers,
  missing avatars/thumbnails.
- Images keep aspect ratio (no stretch/squish), cropped and rounded per theme.

### Affordance & feedback (inferred from a still)
- Tappable things look tappable; disabled things look disabled.
- Skeleton/placeholder over a blank screen during load.

---

## Anti-patterns — the "mobile AI-slop" tells

Fast signals that an agent generated the screen without looking at it. Flag any present:

- Everything center-aligned.
- One uniform medium font weight; no hierarchy.
- Untouched default purple Material theme.
- Identical heavy elevation on every card.
- 16-dp-on-everything cramming, or huge arbitrary gaps with no rhythm.
- Stacks of full-width filled buttons with no grouping or primary/secondary distinction.
- Content under the status bar or nav bar (insets ignored).
- No empty, loading, or error state.
- Emoji used as UI icons.
- Critical text truncated with `…` instead of wrapped or resized.
- Pure `#000` / `#FFF` backgrounds and shadows that glow in dark mode.

---

## Verdict format

Return exactly this shape:

```
VERDICT: fail            # fail if any Tier-1 violation, else pass

Tier-1 violations (blockers):
- [overflow] "Continue" button row clipped at right edge @ fontScale 1.5 (LoginScreen).
  Fix: let the label wrap, or make the row horizontally scrollable, or shorten the label.
- [insets] App bar title overlaps the status bar (HomeScreen, default).
  Fix: apply Modifier.windowInsetsPadding(WindowInsets.statusBars) or use a Scaffold TopAppBar.

Tier-2 issues (polish):
- [hierarchy] Three filled buttons compete; no clear primary (SettingsScreen).
  Fix: one filled primary, others OutlinedButton/TextButton.
- [spacing] Mixed 12/16/20 dp gaps in the list (FeedScreen).
  Fix: snap to the 8 dp scale (8/16/24).

Score: 2 blockers → re-render after fixes. Taste re-check deferred until Tier-1 clears.
```

When `pass`, still list Tier-2 issues as suggestions, but mark the screen shippable.

---

## Quick checklist (fast pass)

Structural (any ✗ = fail): edges not clipped · no truncated critical text · nothing
overlapping · no 0-size nodes · insets respected · targets ≥ 48 dp · keyboard doesn't
cover the field · aligned to grid · text contrast ≥ AA · scrolls when it must · empty/
loading/error states exist.

Taste (weighted): one clear primary · hierarchy via type scale · 8 dp spacing · theme
colors not hex · dark mode real · M3 components used right · realistic + edge content ·
not center-everything · not default-purple.
