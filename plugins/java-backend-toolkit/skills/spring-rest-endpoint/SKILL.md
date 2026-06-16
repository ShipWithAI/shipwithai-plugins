---
name: spring-rest-endpoint
description: >
  Scaffold a Spring Web REST endpoint correct-by-default — controller + request/
  response DTOs + service method + mapper. Never exposes a JPA entity (satisfies the
  entity-in-controller guardrail). Request bodies are @Valid DTOs.
  Trigger phrases: "add endpoint", "scaffold rest controller", "new REST endpoint",
  "create controller".
argument-hint: "[ResourceName]"
---

# Spring REST Endpoint — Scaffold

Generates a controller that returns **DTOs only**, so the `entity-in-controller`
guardrail never fires. Output: controller, response DTO, request DTO, a service
method, and an entity→DTO mapper.

## Step 1 — Detect conventions

- Base package: infer from `src/main/java/.../` (the deepest package holding existing
  `*Controller.java`, else the application's root package).
- Existing patterns: if the project already has a `mapper`/`dto` package or MapStruct
  on the classpath, match it; otherwise generate a plain hand-written mapper.

## Step 2 — Gather the resource

Ask (or take from argument): resource name (e.g. `Order`), and which operations
(`GET /{id}`, `GET` list, `POST`, `PUT`, `DELETE`). Default to read + create if unspecified.

## Step 3 — Render templates

From `assets/`, substitute `{{PACKAGE}}`, `{{RESOURCE}}`, `{{RESOURCE_LOWER}}`:

- `Controller.java.tmpl`  → `<pkg>/web/{{RESOURCE}}Controller.java`
- `ResponseDto.java.tmpl` → `<pkg>/web/dto/{{RESOURCE}}Response.java`
- `RequestDto.java.tmpl`  → `<pkg>/web/dto/{{RESOURCE}}Request.java`

Rules baked into the templates:
- Controller methods return `{{RESOURCE}}Response` / `List<{{RESOURCE}}Response>` /
  `ResponseEntity<{{RESOURCE}}Response>` — **never the entity**.
- `@PostMapping`/`@PutMapping` take `@Valid @RequestBody {{RESOURCE}}Request`.
- A `{{RESOURCE}}Mapper` (or inline mapping in the service) converts entity → response.

## Step 4 — Wire the service

If a `{{RESOURCE}}Service` exists, add the method; otherwise generate a minimal
service that depends on the repository and returns the mapped DTO. Keep the
`@Transactional` boundary on the **public** service method (not the controller).

## Step 5 — Report

List created files and remind: the controller never returns the entity; map in the
service/mapper. If the resource has no entity yet, suggest `/jpa-entity` first.

## Failure modes — do NOT

- Do NOT return, accept, or expose a JPA `@Entity` in any controller signature.
- Do NOT put `@Transactional` on the controller.
- Do NOT skip `@Valid` on request bodies.
- Do NOT overwrite an existing controller without showing a diff and confirming.
