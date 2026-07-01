---
name: security-filter-chain
description: >
  Scaffold a Spring Security 6 SecurityFilterChain @Bean baseline — deny-by-default
  authorizeHttpRequests, a BCryptPasswordEncoder, explicit CORS, and CSRF guidance
  (kept for cookie/session auth, disabled only for stateless token APIs). Lambda DSL,
  Jakarta, no deprecated .and() chaining.
  Trigger phrases: "set up spring security", "securityfilterchain", "lock down
  endpoints", "spring security config", "password encoder bean".
argument-hint: "[base-package]"
---

# Security Filter Chain — Scaffold

Generates a `SecurityConfig` whose authorization is **deny-by-default**, so a new
endpoint is locked until you explicitly open it — the opposite of the permit-all
defaults that trip `sec-missing-method-auth`. See `references/security.md` for the why.

## Step 1 — Detect conventions (do not assume)

Read before generating:
- **Existing security config:** search for a `@Bean SecurityFilterChain` or the legacy
  `WebSecurityConfigurerAdapter`. If one exists, EDIT it (show a diff) — two filter
  chains with overlapping matchers is non-deterministic. If it's the deprecated adapter,
  offer to migrate it to the component-based `SecurityFilterChain` bean.
- **Auth model — pick before generating:**
  - **Cookie/session** (server renders, browser holds a session cookie) → **KEEP CSRF**,
    allow the default `SessionCreationPolicy`.
  - **Stateless token** (JWT/opaque bearer, no cookie) → `SessionCreationPolicy.STATELESS`
    and CSRF disabled (no cookie to forge). Pair with the `jwt-auth` skill.
- **Origins:** find the SPA/mobile origins for CORS; never reflect `*` with credentials.
- **Base package:** mirror existing `config`/`security` packages.

## Step 2 — Render the template

From `assets/SecurityConfig.java.tmpl`, substitute `{{PACKAGE}}` and `{{ALLOWED_ORIGIN}}`
→ `<pkg>/config/SecurityConfig.java`. It provides three beans:
1. `SecurityFilterChain` — `authorizeHttpRequests` ending in `anyRequest().authenticated()`
   (deny-by-default); only health/auth endpoints are `permitAll()`.
2. `PasswordEncoder` → `BCryptPasswordEncoder` (adaptive; never MD5/SHA-1/plaintext —
   `sec-weak-hash`).
3. `CorsConfigurationSource` — explicit origins/methods/headers, `allowCredentials(true)`
   only with exact origins.

## Step 3 — Tune for the chosen auth model

- **Cookie/session:** delete the `.csrf(...).disable()` and `.sessionManagement(...)`
  lines. CSRF protection stays ON. Add a `formLogin`/`httpBasic` or your login flow.
- **Stateless token:** keep both lines; register the bearer filter from `jwt-auth`
  before `UsernamePasswordAuthenticationFilter`.
- Prefer `requestMatchers(HttpMethod.X, "...")` over broad patterns; keep the matcher
  list ordered most-specific first.

## Step 4 — Report

```
Created:
  src/main/java/.../config/SecurityConfig.java
    (deny-by-default authz ✓, BCrypt ✓, CORS ✓, CSRF: <kept|disabled> for <session|token>)
```
State which auth model was chosen and why CSRF is on/off.

## Failure modes — do NOT

- Do NOT leave a wildcard `anyRequest().permitAll()` — that defeats the whole config.
- Do NOT disable CSRF for cookie/session auth (CSRF is exactly that threat model).
- Do NOT set `allowedOrigins("*")` together with `allowCredentials(true)` (forbidden combo).
- Do NOT store passwords with MD5/SHA-1/SHA-256 or plaintext — use BCrypt/Argon2 (`sec-weak-hash`).
- Do NOT use the deprecated `WebSecurityConfigurerAdapter` / `.and()` chaining (Spring Security 6).
- Do NOT add a second SecurityFilterChain bean that overlaps an existing one.
