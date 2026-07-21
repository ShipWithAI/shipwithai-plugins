# Transaction conventions

Rule: `tx-proxy`.

## `@Transactional` only works on public methods called from another bean

**Failure mode:** Spring implements `@Transactional` with a proxy that wraps the
bean. The proxy can only intercept calls that go *through* it. So:
- `@Transactional` on a `private`/`protected`/package-private/`static` method →
  silently ignored. No transaction starts. No warning at runtime.
- A `public` `@Transactional` method called from **another method in the same class**
  (self-invocation) → also bypasses the proxy. Same silent no-op.

The hook catches the non-public case (line-level). Self-invocation needs review.

**Fix:**

```java
@Service
public class TransferService {
    @Transactional                       // public, called from outside the bean
    public void transfer(Long from, Long to, BigDecimal amount) { ... }
}
```

- Put the transactional boundary on a **public service method**.
- Call it from a *different* bean (controller → service), not from a sibling method.
- If you need an inner transactional step, extract it into its own bean.

## Where the boundary belongs

- Service layer, not controllers (controllers shouldn't own transactions) and not
  repositories (too granular — one transaction per repo call defeats atomicity).
- Keep transactions short; don't do remote calls / slow IO inside them.

**When to suppress** (`// jbt:ignore tx-proxy`): the annotation is on a non-public
method intentionally because a framework/library re-proxies it — rare; document it.
