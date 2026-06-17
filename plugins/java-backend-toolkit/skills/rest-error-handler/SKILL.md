---
name: rest-error-handler
description: >
  Scaffold a global REST error contract — a @RestControllerAdvice that maps every
  exception to an RFC 7807 ProblemDetail (Spring 6): validation errors → 400 with
  field details, a domain NotFoundException → 404, and a fallback 500 that never
  leaks stack traces. This is the fix the entity-in-controller / error-contract
  guidance points at.
  Trigger phrases: "add global error handler", "problemdetail", "rest exception
  handler", "@RestControllerAdvice", "map exceptions to RFC 7807".
argument-hint: "[base-package]"
---

# REST Error Handler — Scaffold

One advice class so every endpoint shares one error shape. Clients always get an
RFC 7807 `ProblemDetail` (`application/problem+json`), and the server never leaks a
stack trace or internal message on an unexpected failure.

## Step 1 — Detect conventions (do not assume)

Read before generating:
- **Existing advice:** search for `@RestControllerAdvice` / `@ControllerAdvice` or a
  class extending `ResponseEntityExceptionHandler`. If one exists, ADD the missing
  handlers to it (show a diff) rather than creating a competing advice — two global
  advices fighting over the same exception is non-deterministic.
- **Base package:** mirror where existing `*Controller.java` live; place the advice in
  the `…​.web` package alongside them.
- **Existing not-found exception:** if the project already has a `NotFoundException` /
  `ResourceNotFoundException`, reuse it; don't generate a duplicate.
- **Error type base URI:** pick a stable base for the `type` field (e.g.
  `https://<app>/problems`); fill `{{PROBLEM_BASE}}`.

## Step 2 — Render templates

From `assets/`, substitute `{{PACKAGE}}` and `{{PROBLEM_BASE}}`:

- `GlobalExceptionHandler.java.tmpl` → `<pkg>/web/GlobalExceptionHandler.java`
- `NotFoundException.java.tmpl` → `<pkg>/NotFoundException.java` (skip if one exists)

The advice maps three cases:
1. `MethodArgumentNotValidException` → **400**, body carries an `errors` map of
   `field → message` built from `getBindingResult().getFieldErrors()`.
2. `NotFoundException` → **404** with the domain message.
3. `Exception` (fallback) → **500**, logged server-side, body is an opaque
   `"Unexpected error"` — no `ex.getMessage()`, no stack trace.

## Step 3 — Wire it up

- Throw `NotFoundException` from services (e.g. on `findById(...).orElseThrow(...)`),
  never return `null` to the controller.
- Spring 6 serializes `ProblemDetail` as `application/problem+json` automatically; no
  extra config needed. Confirm the app is Spring Boot 3.x (Spring 6) — `ProblemDetail`
  does not exist in Spring 5 / Boot 2.x.

## Step 4 — Report

List created files and confirm the contract:
```
Created:
  src/main/java/.../web/GlobalExceptionHandler.java   (400 validation, 404, 500 fallback)
  src/main/java/.../NotFoundException.java             (if absent)
```

## Failure modes — do NOT

- Do NOT return `ex.getMessage()` or a stack trace in the fallback 500 (information leak).
- Do NOT create a second global advice if one already exists — extend it.
- Do NOT use `javax.*` or Spring 5 `@ExceptionHandler` returning a hand-rolled body;
  use Spring 6 `ProblemDetail` (`jakarta.*` imports).
- Do NOT catch and swallow — every handled exception still produces a response.
- Do NOT map a generic `Exception` to anything other than 500.
