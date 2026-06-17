# Security conventions

Rules: `sec-weak-hash`, `sec-mass-assignment`, `sec-hardcoded-secret`,
`sec-missing-method-auth` (plus `entity-in-controller` from web.md). The line-level hook
catches `sec-weak-hash` and `sec-hardcoded-secret`; the cross-file ones are
reviewer-enforced by `springboot-reviewer`.

## Password hashing (`sec-weak-hash`)

**Failure mode:** hashing passwords with MD5 or SHA-1. Both are fast and collision-prone,
so an attacker who grabs the table brute-forces them at billions/sec. A plain
`MessageDigest` has no salt and no work factor.

**Fix:** use an adaptive password encoder with a tunable cost — `BCryptPasswordEncoder`,
`Argon2PasswordEncoder`, or PBKDF2 from Spring Security:

```java
PasswordEncoder encoder = new BCryptPasswordEncoder();
String hash = encoder.encode(rawPassword);
boolean ok = encoder.matches(rawPassword, hash);
```

MD5/SHA-1 are fine for *non-security* checksums (cache keys, ETags). If that's the case,
suppress with `// jbt:ignore sec-weak-hash` — don't reach for them on a credential path.

## Mass assignment — DTO at the boundary (`sec-mass-assignment`)

**Failure mode:** binding a request body straight onto a JPA `@Entity`
(`create(@RequestBody Account account)`). The client controls the whole object graph and
can set fields you never meant to expose — `id`, `role`, `balance`, audit columns.

**Fix:** bind to a request DTO that contains only client-writable fields, then map it onto
the entity in the service. This is the same boundary discipline as `entity-in-controller`
(see web.md) — the persistence model never touches the wire, in either direction.

## Secret management (`sec-hardcoded-secret`)

**Failure mode:** a key/password/token written as a string literal in source. Once
committed it lives in VCS history forever, even after you "delete" it.

**Fix:** inject secrets from the environment or a secret manager; keep source clean.

```java
@Value("${app.api-key}")          // resolved from env / config server / vault
private String apiKey;
// or: System.getenv("API_KEY")
```

Empty defaults (`""`) and `${...}` placeholders are intentionally NOT flagged — those
already defer to external configuration. If a secret was ever committed, rotate it.

## Authorization — method and URL (`sec-missing-method-auth`)

**Failure mode:** a mutating endpoint (`@PostMapping`/`@PutMapping`/`@DeleteMapping`/
`@PatchMapping`) with no authorization the reviewer can see — neither a method annotation
nor a matching `SecurityFilterChain` rule. Easy to ship an unprotected write.

**Fix — defense in depth, pick at least one and be explicit:**

```java
// Method-level (needs @EnableMethodSecurity)
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/accounts/{id}")
void delete(@PathVariable UUID id) { ... }
```

```java
// URL-level, in the SecurityFilterChain
http.authorizeHttpRequests(reg -> reg
    .requestMatchers(HttpMethod.DELETE, "/accounts/**").hasRole("ADMIN")
    .anyRequest().authenticated());
```

If the endpoint is genuinely public, say so explicitly with `permitAll()` rather than
leaving it implicit. The `security-filter-chain` scaffold generates a baseline chain;
`jwt-auth` adds stateless token auth.

## CORS

Don't `*`-allow everything. List the exact origins, methods, and headers your frontend
needs, and only set `allowCredentials(true)` with explicit origins (never with `*` — the
browser rejects that combination anyway). Configure it once in the `SecurityFilterChain`,
not ad hoc per controller.

## CSRF

CSRF protection defends *cookie/session* auth, where the browser attaches credentials
automatically.

- **Cookie/session-based UI** → keep CSRF enabled (Spring's default), use the
  `CookieCsrfTokenRepository` for SPAs.
- **Stateless token API** (Authorization: Bearer …, no session cookie) → CSRF doesn't
  apply; disable it (`http.csrf(csrf -> csrf.disable())`) so it doesn't block your
  non-browser clients. Disable it *because* you're stateless, not to silence an error.

## HTTPS

Terminate TLS at the edge and never accept credentials over plaintext. Behind a proxy,
trust forwarded headers (`server.forward-headers-strategy=framework`) so redirects and
`secure` cookies are correct; consider HSTS and redirecting HTTP→HTTPS.

## OAuth2 / token auth

For delegated auth or first-party tokens, prefer a standard over hand-rolled login: Spring
Security OAuth2 Resource Server (validate JWTs / opaque tokens) and, if you issue your own
tokens, the Spring Authorization Server. The `jwt-auth` scaffold wires up the resource-server
side (JWT decoding + authority mapping) on top of the `security-filter-chain` baseline.
