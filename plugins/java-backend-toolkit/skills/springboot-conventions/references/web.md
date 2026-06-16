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
