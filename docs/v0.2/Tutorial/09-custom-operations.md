---
title: "Tutorial 09: Custom Operations"
description: Custom operations with handler functions (e.g. publishing a note), wiring imports, and the handler contract.
---

**Concept introduced:** Custom operations backed by handler functions (for example, publishing a note) that do not map to plain create/update/delete.

## When you need a custom operation

Standard CRUD (`list`, `get`, `create`, `update`, `replace`, `delete`) covers most cases. A custom operation handles a domain action that is not a plain write, such as `POST /notes/{id}/publish`. You attach a handler in three places:

- `imports:` maps a short alias to a Python module path.
- `services.<name>.operations.<op>: { handler: <alias>.<function> }` binds the handler to the service.
- `controllers.<name>.operations.<op>: { method, path }` exposes it as a route. Custom operations have no default verb or path, so both `method` and `path` are required (omitting them fails generation with `DESUGAR_CUSTOM_OP_MISSING_ROUTE`).

## The imports block

`imports:` maps aliases to dotted Python module paths. It lives at the top level of the spec:

```yaml
imports:
  notes: myapp.handlers.notes
```

Resolution splits a handler reference on the first dot: `notes.publish` becomes the alias `notes` plus the rest, `publish`. The alias is looked up in `imports`, so `notes.publish` resolves to `myapp.handlers.notes.publish`. If the first segment is not a declared alias, the whole reference is used verbatim as a dotted path. The module must be importable on `PYTHONPATH` when the app runs; place your package next to the generated backend or install it.

## Full spec

This spec sets `api: { basePath: /api, version: v1 }`, so every route below is prefixed with `/api/v1` (for example `POST /api/v1/notes/{id}/publish`).

```yaml
version: "0.2"

imports:
  notes: myapp.handlers.notes

api:
  basePath: /api
  version: v1
  operations:
    auth:
      register: true
      login: true

mongo:
  uri: mongodb://localhost:27017
  database: myapp

entities:
  base:
    abstract: true
    fields:
      id: { type: id }
      createdAt: { type: datetime }

  user:
    extends: base
    type: auth
    auth:
      identifier: email
      via: password
      roles: role
    fields:
      email: { type: string, required: true, unique: true }
      displayName: { type: string, required: true }
      role:
        type: enum
        values: [admin, moderator, user]
        default: user

  note:
    extends: base
    fields:
      title: { type: string, required: true }
      body: { type: string }
      authorId: { type: ref, ref: user }
      published: { type: boolean, default: false }
      publishedAt: { type: datetime }

repositories:
  users:
    entity: user
  notes:
    entity: note

services:
  users:
    repository: users
  notes:
    repository: notes
    operations:
      publish: { handler: notes.publish }

controllers:
  users:
    service: users
    base_path: /users
    operations:
      register: { access: public }
      login: { access: public }

  notes:
    service: notes
    base_path: /notes
    access: public
    operations:
      create: { access: "*" }
      update:
        access:
          - moderator
          - given:
              principal: identity:user
              document: notes
            when: principal.sub equals document.authorId
      delete:
        access:
          - moderator
          - given:
              principal: identity:user
              document: notes
            when: principal.sub equals document.authorId
      publish:
        method: POST
        path: "/{id}/publish"
        access:
          - moderator
          - given:
              principal: identity:user
              document: notes
            when: principal.sub equals document.authorId
```

Notes on this spec:

- Roles come from an enum field plus `auth.roles: role`. The standalone entity-level `roles: { values, default, hierarchy }` block is parsed but not wired in v0.2, so do not rely on it. A new user's role is set only by the enum field's `default:`; clients cannot set `role`/`roles` on write (those keys are stripped).
- `register`/`login` routes are not generated unless you enable them with `api.operations.auth`, as shown above.
- `access: "*"` means any logged-in user; `public` means no auth; `moderator` is an exact role match; the `given`/`when` rule is an ownership check.

## Handler contract

`stackform run` and every generated backend (FastAPI, DRF, raw ASGI) call the
handler the same way: with one request object, sending its return value as the
JSON response body.

```python
# myapp/handlers/notes.py
from datetime import datetime, timezone


async def publish(request):
    if request.body.get("draft"):
        raise ValueError("Cannot publish a draft")
    return {
        "id": request.params["id"],
        "published": True,
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "by": request.principal["sub"],
    }
```

The request carries `params` (path parameters), `query`, `headers`, `cookies`,
`body` (the JSON body, or `{}`), `principal` (a plain dict, or `None` on public
routes) and `inputs` (the service's `with:` values). The handler owns its data
access. Raise `ValueError` for a 422; any other exception answers 500. The route's
access rules run before the handler.

> **Enforcement**
>
> Roles, role hierarchies, `<entity>:*` scoping, and ownership/ABAC `when` rules
> are enforced by the generated FastAPI backend, the generated DRF backend, and the
> `stackform run` dev server alike. A request that no rule admits gets 401 when it
> carries no valid credentials and 403 otherwise; a missing record answers 404
> before ownership is checked.

## Declarative alternative: repository query operations

If your custom action is just a parameterized read, you can avoid a handler entirely with a repository-level query operation. These run against MongoDB without custom Python:

```yaml
repositories:
  notes:
    entity: note
    operations:
      published:
        query:
          command: find
          filter: { published: true }
```

Supported `query.command` values are `find`, `findOne`, `aggregate`, `countDocuments`, and `estimatedDocumentCount`. `find`/`findOne`/`countDocuments` require a `filter`; `aggregate` requires a `pipeline`. A repository with no `entity` may set `query.collection` to target a collection explicitly (otherwise `QUERY_MISSING_COLLECTION`). A repository-level operation declares exactly one of `query` or `handler`; neither or both fails schema validation (`SCHEMA_VALIDATION_ERROR`).

A repository `operations.<op>.handler` receives the same request object as a service handler.

## What the custom operation generates

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/notes/{id}/publish | Custom publish handler |

The full path is `basePath + version + controller base_path + operation path`. With the `api:` block above, `/{id}/publish` under `base_path: /notes` becomes `/api/v1/notes/{id}/publish`.

Custom-operation routes are emitted by the FastAPI, DRF, and raw-ASGI targets.

## Key points

- `handler:` on a service operation points to `<alias>.<function>`, resolved through `imports:`.
- Custom operations require `method` and `path` on the controller operation; there is no inference.
- Every target and `stackform run` pass the handler the same request object.
- For a plain parameterized read, prefer a repository `query` operation over a handler.
- Custom operations use the same access vocabulary as CRUD, and every target (`run`, FastAPI, raw ASGI and DRF) enforces the rules before your handler runs. A bare `document:` binding loads the record named by the route's `{id}` parameter.

## See Also

- [Handler Context Reference](../Reference/services/handler-context.md) -- every attribute of the handler's request object.
- [Custom operations reference](../Reference/services/custom-operations.md) -- custom operation routes and import resolution.
