---
title: "Custom Service Operations"
description: Custom operations attach your own Python handler functions to a service and expose them as HTTP routes, alongside the generated CRUD operations.
---

Custom operations attach your own Python handler functions to a service and expose them as HTTP routes, alongside the generated CRUD operations. Use them when a route needs behavior that the built-in CRUD operations do not provide (for example, "publish a record" or "archive a record").

## Declaration

A custom operation is a named entry under a service's `operations:` whose value carries a `handler:`:

```yaml
imports:
  ops: myapp.handlers.ops

services:
  myCollection:
    repository: myCollection
    operations:
      publish: { handler: ops.publish_record }
      archive: { handler: ops.archive_record }
```

`handler:` is `<importAlias>.<functionName>`. The alias is resolved against the
`imports:` map by splitting on the first dot only: `ops` maps to
`myapp.handlers.ops`, so `ops.publish_record` resolves to the dotted path
`myapp.handlers.ops.publish_record`. If the alias before the first dot is not
present in `imports:`, the handler string is used verbatim as a fully qualified
dotted path, so you can also write `handler: myapp.handlers.ops.publish_record`
directly.

## Exposing via a controller

A custom operation has no naming convention, so the controller operation that
exposes it MUST set both `method:` and `path:`. Omitting either is a generate-time
error (`DESUGAR_CUSTOM_OP_MISSING_ROUTE`). There is no method/path inference for
custom operations (only the built-in CRUD and auth operations have conventional
routes).

```yaml
api:
  basePath: /api
  version: v1

controllers:
  myCollection:
    service: myCollection
    base_path: /my-collection
    operations:
      publish:
        method: POST
        path: "/{id}/publish"
        access: "*"
      archive:
        method: POST
        path: "/{id}/archive"
        access: moderator
```

The full route path is `basePath` + version segment + `base_path` + the
operation `path:`. With the `api:` block above, `publish` is served at
`POST /api/v1/my-collection/{id}/publish`.

A custom controller operation only produces a route when the referenced service
defines a matching custom operation; the controller operation name must match the
service operation name.

## Handler signature

Every backend, and `stackform run`, calls the handler with one request object and
sends its return value as the JSON response body. The handler may be a plain or an
`async` function.

```python
# myapp/handlers/ops.py
from datetime import datetime, timezone


async def publish_record(request):
    if request.body.get("draft"):
        raise ValueError("Cannot publish a draft")
    return {
        "id": request.params["id"],
        "published": True,
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    }
```

- Read path parameters from `request.params`, query parameters from
  `request.query`, the JSON body from `request.body` and the caller from
  `request.principal`; see [Handler context](./handler-context.md) for every
  attribute.
- The handler owns its data access: import the client or service it needs.
- Raising `ValueError` answers 422 with its message as `detail`; any other
  exception answers 500.

## Access control

Custom operations participate in the same access control as built-in operations.
Set `access:` on the controller operation exactly as you would for `create`,
`update`, etc. The example above gates `publish` with `"*"` (any authenticated
principal) and `archive` with the `moderator` role.

> **Enforcement**
>
> Roles, role hierarchies, `<entity>:*` scoping, and ownership/ABAC `when` rules
> are enforced by the generated FastAPI backend, the generated DRF backend, and the
> `stackform run` dev server alike. A request that no rule admits gets 401 when it
> carries no valid credentials and 403 otherwise; a missing record answers 404
> before ownership is checked.

## Repository-level operations (declarative alternative)

If you only need a database query and not arbitrary Python, declare the operation
on the repository instead of writing a handler. A repository operation is either a
`query:` (a named MongoDB command) or a `handler:` called with the request object:

```yaml
repositories:
  myCollection:
    entity: myEntity
    operations:
      recent:
        query:
          command: find
          filter: { published: true }
      featured:
        handler: ops.featured_records
```

`query.command` must be one of the allowed MongoDB commands (for example `find`,
`findOne`, `aggregate`, `countDocuments`, `distinct`, `updateMany`,
`deleteMany`). Some commands require a field (`find`/`findOne` require `filter`).
A repository without an `entity:` must set `query.collection`
(`QUERY_MISSING_COLLECTION`). An operation declares exactly one of `query:` or
`handler:`; neither or both is a `SCHEMA_VALIDATION_ERROR`. An unknown command is
`QUERY_COMMAND_UNKNOWN`.

A repository `operations.<op>.handler` receives the same request object as a
service handler. See [Repository operations](../repositories/operations.md) for the
full repository operation model.
