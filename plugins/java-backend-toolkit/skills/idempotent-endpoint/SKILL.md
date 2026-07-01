---
name: idempotent-endpoint
description: >
  Scaffold idempotency-key handling for unsafe POSTs — read an Idempotency-Key header,
  replay the stored response on a retry instead of re-processing, otherwise process
  once and store the response keyed by (key, request fingerprint). Ships a servlet
  filter plus a storage SPI the project implements with Redis or a DB.
  Trigger phrases: "idempotency key", "idempotent endpoint", "make POST idempotent",
  "safe retries", "exactly-once POST", "dedupe requests".
argument-hint: "[base-package]"
---

# Idempotent Endpoint — Scaffold

Unsafe POSTs get retried — by clients, proxies, and message queues. Without
idempotency a retry charges the card twice or creates two orders. This scaffolds a
filter that makes a retry carrying the same `Idempotency-Key` **replay** the original
response, so the side effect happens exactly once.

## Step 1 — Detect conventions (do not assume)

Read before generating:
- **Existing filter chain:** look for `OncePerRequestFilter` / `FilterRegistrationBean`
  config and a `…​.web` / `…​.config` package; place the filter there and register it
  the same way the project registers other filters.
- **Storage available:** check for Redis (`spring-data-redis`) or a relational DB. The
  filter depends only on the `IdempotencyStore` SPI — pick the backing store that
  already exists; do not add a new datastore.
- **Existing idempotency:** if the project already keys retries somewhere, extend that
  instead of adding a parallel mechanism.

## Step 2 — Render templates

From `assets/`, substitute `{{PACKAGE}}`:

- `IdempotencyStore.java.tmpl` → `<pkg>/web/idempotency/IdempotencyStore.java` (the SPI)
- `IdempotencyKeyFilter.java.tmpl` → `<pkg>/web/idempotency/IdempotencyKeyFilter.java`

The filter logic:
1. Only guards `POST` requests that carry an `Idempotency-Key` header; everything else
   passes straight through.
2. Computes a **fingerprint** = hash of method + URI + body.
3. `store.find(key)`:
   - **hit, same fingerprint** → replay the stored status/body, skip the handler.
   - **hit, different fingerprint** → `422` (the key was reused for a different request).
   - **miss** → run the handler, then `store.save(key, response)`.

## Step 3 — Implement the store

Generate (or point the user to write) one `IdempotencyStore` implementation:
```java
@Component
class RedisIdempotencyStore implements IdempotencyStore {
    // SET key <json> NX EX <ttl>; GET key. Use a short TTL (minutes–hours), not forever.
    // A DB variant: unique column on key + an inserted-at for expiry.
}
```
Register the filter (e.g. a `FilterRegistrationBean<IdempotencyKeyFilter>`) scoped to
the POST routes that need it — not every endpoint.

## Step 4 — Report

```
Created:
  src/main/java/.../web/idempotency/IdempotencyStore.java        (SPI)
  src/main/java/.../web/idempotency/IdempotencyKeyFilter.java    (filter)
  + a store implementation (Redis/DB) — implement before shipping
```

## Failure modes — do NOT

- Do NOT store responses forever — set a TTL; an unbounded store is a memory/disk leak.
- Do NOT replay on a different request body under the same key — return 422 instead.
- Do NOT apply idempotency to safe methods (GET/HEAD) — they are already idempotent.
- Do NOT key only on the header — include a request fingerprint so a reused key can't
  replay an unrelated response.
- Do NOT store the key without scoping it to the caller/tenant if keys aren't globally
  unique in your system.
