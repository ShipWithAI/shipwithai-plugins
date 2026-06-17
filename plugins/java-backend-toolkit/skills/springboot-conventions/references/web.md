# Web layer conventions

Rule: `entity-in-controller` (reviewer-enforced — cross-file, so the line hook
defers to `springboot-reviewer`).

## Don't return JPA entities from controllers

**Failure mode (two of them):**
1. **Model leakage** — the API contract becomes your database schema. Add a column,
   you change the API; rename a field, you break clients.
2. **`LazyInitializationException`** — serializing an entity outside the persistence
   context triggers lazy associations after the session closed → 500 at render time.
   (Or worse: `EAGER` everything to "fix" it, and now every read over-fetches.)

**Fix:** map to a DTO at the boundary.

```java
public record AccountResponse(UUID id, String name, BigDecimal balance) {}

@GetMapping("/{id}")
AccountResponse get(@PathVariable UUID id) {
    return accountService.findById(id); // service returns the DTO
}
```

- Response DTOs: prefer `record`s — immutable, concise.
- Request DTOs: validated (`@Valid` + Jakarta Validation annotations), never the entity.
- Map in the service or a dedicated mapper (manual or MapStruct). Keep mapping out of
  the controller.

Use the `spring-rest-endpoint` skill to scaffold this correctly in one step.

**When to suppress:** almost never for public APIs. An internal admin endpoint
returning a projection DTO is fine; a raw `@Entity` return is the thing to avoid.

## API versioning

Version from day one — clients outlive any single contract. Pick **one** strategy and
apply it consistently across every endpoint:

- **URI versioning** (`/api/v1/accounts`) — explicit, cache-friendly, trivial to route
  and document. The pragmatic default for most services.
- **Header versioning** (`Accept: application/vnd.acme.v1+json`) — keeps URLs stable and
  models versions as content negotiation, at the cost of discoverability and tooling.

Don't mix the two. Bump the major version only for breaking changes; add fields
backward-compatibly within a version. Never reuse or silently repurpose an existing field.

## Error contract — RFC 7807 `ProblemDetail`

Standardize every error response on **RFC 7807** via Spring 6's `ProblemDetail`
(`application/problem+json`). One shape for all failures means clients parse errors once.

```java
@ExceptionHandler(AccountNotFoundException.class)
ProblemDetail handle(AccountNotFoundException ex) {
    ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    pd.setType(URI.create("https://api.acme.com/errors/account-not-found"));
    return pd;
}
```

Centralize handlers in a `@RestControllerAdvice` so the format and status mapping live in
one place. The `rest-error-handler` scaffold generates this advice plus the
`ProblemDetail` plumbing in one step. Returning a `ProblemDetail` (a DTO) rather than an
exception's raw stack or a leaked entity also keeps you on the right side of
`entity-in-controller` — never serialize the persistence model, not even on the error path.

## Validation at the boundary (`web-missing-valid`)

Validate request payloads **at the edge** so invalid input never reaches the service
layer. Annotate the body parameter with `@Valid` (or `@Validated` for validation groups)
and put Jakarta Validation constraints on the DTO:

```java
@PostMapping("/accounts")
AccountResponse create(@Valid @RequestBody CreateAccountRequest request) { ... }
```

The `web-missing-valid` guardrail flags a `@RequestBody`/`@ModelAttribute` parameter with
no `@Valid`. Pair it with a global handler that turns `MethodArgumentNotValidException`
into a `ProblemDetail` (status 400, field errors under a `errors`/`invalid-params`
extension) so validation failures share the same RFC 7807 contract as every other error.

## Rate limiting

Protect endpoints with a rate limiter and make the limit **observable** to clients:

- Reject over-limit requests with **HTTP 429 Too Many Requests**.
- Include a **`Retry-After`** header (seconds, or an HTTP-date) telling the client when to
  retry.
- Expose budget with **`X-RateLimit-Limit`**, **`X-RateLimit-Remaining`**, and
  **`X-RateLimit-Reset`** so well-behaved clients can self-throttle before hitting 429.

Apply limits per principal (API key / user / IP) rather than globally, and surface the 429
body as a `ProblemDetail` for contract consistency.
