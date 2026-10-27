---
title: "Services Overview"
description: Services are the business-logic layer. Controllers reference services; services reference repositories. Controllers never reference repositories directly.
---

Services are the business-logic layer. Controllers reference services; services reference repositories. Controllers never reference repositories directly.

Each service entry resolves to a set of per-operation units (one per CRUD operation, plus `register`/`login` for auth entities). The generator wires those units into repository methods and HTTP routes. A service you do not declare for a given operation produces no method and no route.

## Forms

```yaml
services:
  # Minified: bind a service group to a repository (the common form)
  myCollection:
    repository: myCollection

  # Empty map: same as above when the service key matches a repository key
  myOtherCollection: {}

  # Per-operation overrides on a repository-backed service
  myCollection:
    repository: myCollection
    operations:
      delete: false                      # disable an operation
      publish: { handler: handlers.publish }  # add a custom operation

  # Explicit single operation (a named delegate)
  list-my-collection: { repository: myCollection, operation: list }
```

## Minified `serviceName: { repository: repoName }`

The primary form binds a service to a repository. The generator expands it into one service unit per resolved CRUD operation, named `<operation>-<serviceName>` internally (for example `list-myCollection`, `create-myCollection`). A controller that references the service group `myCollection` picks those up automatically.

```yaml
services:
  myCollection:
    repository: myCollection
```

## Shorthand `{}`

An empty map is the same as `{ repository: <serviceName> }`: it binds the service to the repository of the same name and enables all resolved CRUD operations.

```yaml
services:
  myCollection: {}
```

The service key must match a repository key of the same name for this shorthand to work. Which operations end up enabled depends on the resolution order below, not on a fixed list:

- Default is all six CRUD operations enabled: `list`, `get`, `create`, `update`, `replace`, `delete`.
- `api.operations.defaults` can disable operations globally (for example `replace: false`).
- `repositories.<name>.crud: [...]` selects the subset that repository exposes.
- `services.<name>.operations.<op>` is the final override (a boolean, or a `{ handler }` map).

A boolean switch names a CRUD operation (or, on an auth entity, an auth operation) or a custom operation the repository declares; any other name, such as a misspelled `lsit: false`, fails with `DESUGAR_SERVICE_OPERATION_UNKNOWN`. To add a new operation, give it a `{ handler }` map instead.

Resolution precedence, highest first: service `operations` > repository `crud` > `api.operations.defaults` > all enabled. See [Composable per-operation CRUD](../repositories/composable-crud.md) and [Repository operations](../repositories/operations.md).

## Per-operation overrides

Use `operations:` to disable an operation or attach a custom handler on a repository-backed service:

```yaml
services:
  myCollection:
    repository: myCollection
    operations:
      replace: false                      # disable the PUT operation
      publish: { handler: handlers.publish }
```

Each value is either a boolean (enable/disable) or a `{ handler: <importKey.functionName> }` map for a custom operation. A custom operation declared here is exposed only when the controller also declares its route (see below).

## Custom operations

A custom operation needs two things:

1. A handler on the service: `services.<name>.operations.<op>: { handler: ... }`.
2. A route on the controller: `controllers.<name>.operations.<op>: { method, path }`.

The controller route is required for custom (non-CRUD) operations; without `method` and `path` the build fails with `DESUGAR_CUSTOM_OP_MISSING_ROUTE`.

```yaml
imports:
  handlers: my_app.handlers

services:
  myCollection:
    repository: myCollection
    operations:
      publish: { handler: handlers.publish }

controllers:
  myCollection:
    service: myCollection
    base_path: /my-collection
    operations:
      publish: { method: POST, path: "/{id}/publish" }
```

With `api: { basePath: /api, version: v1 }` this exposes `POST /api/v1/my-collection/{id}/publish`.

### Handler contract

The handler is a Python function referenced by `importKey.functionName`. Every
backend and `stackform run` call it with the same request object and send its
return value as the response body:

```python
async def publish(request):
    return {"id": request.params["id"], "published": True, "note": request.body.get("note")}
```

The handler does its own data access. Raising `ValueError` answers 422; any other exception answers 500. Every request attribute is listed in [Handler context](handler-context.md).

## Top-level `handler` vs per-operation `handler`

- A top-level `handler` on a service replaces the whole service group with one custom function (no CRUD units are generated for it). It cannot be combined with `operation`.
- `operations.<op>.handler` adds a single custom operation alongside the repository-backed CRUD operations.

```yaml
services:
  search: { handler: handlers.search }    # whole-service custom handler

  myCollection:
    repository: myCollection
    operations:
      publish: { handler: handlers.publish }  # one extra operation
```

## Inheritance with `abstract` and `extends`

An `abstract: true` service is a template: no controller may reference it. A service with `extends: <name>` inherits every key of that abstract service except `abstract` and `extends`; its own keys win and `operations` merge per operation. An abstract service may itself extend another abstract service: a service inherits from every level of the chain, and the nearest declaration of an operation wins, so an extending service replaces an inherited handler by declaring the operation again.

```yaml
services:
  publishable:
    abstract: true
    operations:
      publish: { handler: handlers.publish }
  articles:
    repository: articles
    extends: publishable
  pages:
    repository: pages
    extends: publishable
    operations:
      delete: false
```

When the abstract service declares `operations`, the generated backend emits it as a base class that every extending service subclasses.

| Code | Cause |
|------|-------|
| `SERVICE_EXTENDS_NOT_FOUND` | `extends` names a service that does not exist. |
| `SERVICE_EXTENDS_NOT_ABSTRACT` | `extends` names a service without `abstract: true`. |
| `SERVICE_CIRCULAR_EXTENDS` | An `extends` chain loops back on itself. |
| `DESUGAR_ABSTRACT_SERVICE_BOUND` | A controller references an abstract service. |

## Imports

`handler:` values are dotted references of the form `importKey.functionName`. The leading key is looked up in the top-level `imports:` map and the rest is appended; if the key is not declared, the value is treated as a verbatim dotted module path.

```yaml
imports:
  handlers: my_app.handlers            # handlers.publish -> my_app.handlers.publish
```

Declaring the alias in `imports:` keeps handler references short and is recommended, but is not strictly required.

## Repository-level operations as an alternative

Declarative custom reads/writes can also live on the repository instead of the service, via `repositories.<name>.operations.<op>` with a `query: { command, ... }` or a `handler:`. Use the service-level form when the operation is a thin custom HTTP endpoint; use the repository-level form for reusable data operations. See [Repository operations](../repositories/operations.md).

## Auth service operations

Auth entities (`type: auth`) gain `register` and `login` service operations, but only when you enable them under `api.operations.auth`; they are OFF by default.

```yaml
api:
  basePath: /api
  version: v1
  operations:
    auth:
      register: true
      login: true

controllers:
  users:
    service: users
    base_path: /users
    operations:
      register: { access: public }
      login: { access: public }
```

With this `api:` block the endpoints are `POST /api/v1/users/register` and `POST /api/v1/users/login`. Marking them `public` matters because, once any `type: auth` entity exists, non-public routes require a valid principal. See [Authentication required by default](../auth/auth-required-by-default.md).

## Example

```yaml
api:
  basePath: /api
  version: v1
  operations:
    auth:
      register: true
      login: true

imports:
  handlers: my_app.handlers

services:
  users: {}                              # all CRUD + register/login (auth entity)

  myCollection:
    repository: myCollection
    operations:
      replace: false                     # no PUT
      publish: { handler: handlers.publish }

  # Named single-operation delegate
  list-my-collection: { repository: myCollection, operation: list }
```
