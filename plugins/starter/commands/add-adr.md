---
name: add-adr
description: >
  Create a new Architecture Decision Record in docs/adr/. Quick operation.
  Trigger phrases: "create ADR", "document decision", "record architecture choice",
  "add ADR", "document this decision".
argument-hint: "[title of the decision]"
---

# /add-adr

Create a new ADR in `docs/adr/`. Stateless.

## Steps

1. Check if `docs/adr/` exists.
   - Missing: "docs/adr/ does not exist yet. Create the ADR structure?"
     → Yes: create `docs/adr/README.md` then proceed with this ADR.
   - Exists but `docs/adr/README.md` missing: create `README.md` before writing the ADR.

2. Count existing ADR files → next number = ADR-[XXXX] (zero-padded, e.g. ADR-0004).

3. If title not provided as argument, ask:
   - Title of the decision?
   - Context: why does this decision need to be made?
   - Options considered? (list each option with pros and cons)
   - Decision: what was chosen and why?
   - Consequences: trade-offs, risks, next steps?

4. Draft ADR using the template from the plugin's `adr-template.md`
   (located at `skills/setup-ssot/adr-template.md` in the plugin directory)
   → show preview → confirm.

5. Write `docs/adr/ADR-[XXXX]-[kebab-slug].md`.

6. Update the ADR index table in `docs/adr/README.md`:
   ```
   | [ADR-XXXX](ADR-XXXX-title.md) | [title] | Accepted | YYYY-MM-DD |
   ```

7. Update `**Last updated:**` date in the Harness config section of `CLAUDE.md` if the file exists.
