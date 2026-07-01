---
name: jwt-auth
description: >
  Scaffold JWT bearer authentication for a stateless JSON API. Recommends Spring
  Security's resource server (framework verifies signature + exp); also ships a custom
  OncePerRequestFilter using jjwt for teams that need it — it verifies the signature,
  rejects alg=none, checks exp/nbf, and returns 401 JSON on failure. Secret from env.
  Trigger phrases: "jwt auth", "bearer token", "validate jwt", "secure my api with
  tokens", "jwt filter", "resource server".
argument-hint: "[base-package]"
---

# JWT Auth — Scaffold

Bearer-token auth for a stateless API. The cardinal rule: **never read claims from a
token you have not verified.** Prefer the framework path; the custom filter is a
fallback, not the default.

## Step 1 — Detect conventions

- Confirm a `SecurityFilterChain` exists (use the `security-filter-chain` skill first);
  JWT auth plugs into it with `SessionCreationPolicy.STATELESS` and CSRF disabled.
- Check for an issuer/JWKS endpoint (Auth0/Keycloak/Cognito) → strongly favors Option 1.
- Confirm the signing secret/JWKS URI is in config/env, never in source.

## Step 2 — Option 1 (RECOMMENDED): Spring Security resource server

Let Spring validate the token — signature, `exp`, `nbf`, issuer — no hand-rolled crypto:

```java
// build.gradle: implementation 'org.springframework.boot:spring-boot-starter-oauth2-resource-server'
http.oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()));

@Bean // JWKS (asymmetric) — the usual case with an external IdP:
JwtDecoder jwtDecoder(@Value("${security.jwt.jwks-uri}") String jwksUri) {
    return NimbusJwtDecoder.withJwkSetUri(jwksUri).build();
}
// HMAC (shared secret) variant:
//   NimbusJwtDecoder.withSecretKey(new SecretKeySpec(secret.getBytes(UTF_8), "HmacSHA256"))
//       .macAlgorithm(MacAlgorithm.HS256).build();
```

Map scopes/roles with a `JwtAuthenticationConverter` if needed. Choose this whenever an
IdP issues the tokens — you maintain zero verification code.

## Step 3 — Option 2 (only if you must): custom filter

For teams that issue their own tokens and can't add the resource server. Render from
`assets/`, substitute `{{PACKAGE}}`:
- `JwtService.java.tmpl` → `<pkg>/security/JwtService.java` (issue + **verify** via jjwt)
- `JwtAuthenticationFilter.java.tmpl` → `<pkg>/security/JwtAuthenticationFilter.java`
- `JwtAuthenticationEntryPoint.java.tmpl` → `<pkg>/security/JwtAuthenticationEntryPoint.java`

Requires jjwt: `io.jsonwebtoken:jjwt-api` + runtime `jjwt-impl`, `jjwt-jackson`.

What the templates guarantee:
- `Jwts.parser().verifyWith(key).build().parseSignedClaims(token)` — verifies the
  signature, **rejects `alg=none`** and algorithm-confusion, and enforces `exp`/`nbf`.
- The filter only trusts a token after `verify` returns; on any `JwtException` it clears
  the context and returns **401 JSON** via the entry point — never partially authenticated.
- The secret is injected from `${security.jwt.secret}` (env), HS256 key >= 256 bits.
- Authorities are mapped from a `roles` claim (fallback `ROLE_USER`) in the filter's
  `authorities(...)` helper — adjust the claim name/prefix to match your issuer so
  `hasRole(...)` / `@PreAuthorize` reflect real token roles.

Wire the filter in `SecurityConfig`:
```java
http.exceptionHandling(e -> e.authenticationEntryPoint(jwtAuthenticationEntryPoint))
    .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
```

## Step 4 — Report

List created files and state which option was used. For Option 2, confirm: signature
verified, `alg=none` rejected, `exp` checked, secret from env, 401 JSON on failure.

## Failure modes — do NOT

- Do NOT read claims from an unverified token, and do NOT call a "parse without verify" API.
- Do NOT accept `alg=none` or let the token's header pick the algorithm (algorithm confusion).
- Do NOT hardcode the signing secret — inject from env/config (`sec-hardcoded-secret`).
- Do NOT skip the `exp` check or set tokens that never expire.
- Do NOT hand-roll Base64 + HMAC parsing — use the resource server or a vetted library (jjwt).
- Do NOT return 200/HTML on auth failure — return 401 JSON for an API.
