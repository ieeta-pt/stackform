---
title: "Repositories Overview"
description: Repositories bind an entity to a collection or table in a datastore, select which CRUD operations are available, and declare custom query and handler operations.
---

Repositories bind an entity to a collection (MongoDB) or table (relational datastores), select which CRUD operations are available, and declare custom operations.

The repository name is the collection or table name. It is free-form (no pluralization is applied) and is what services reference. A repository whose `entity` is `myEntity` and whose key is `myCollection` stores documents in a collection named `myCollection`.

## Structure

```yaml
repositories:
  myCollection:
    entity: myEntity
    datastore: main                              # optional, see datastores
    crud: [list, get, create, update, delete]    # subset; omit for all six
    softDelete: removedAt                        # optional, see lifecycle
    ttl: { field: lastSeenAt, seconds: 86400 }   # optional, see lifecycle
    operations:                                  # custom ops (optional)
      publishedByOwner:
        query:
          command: find
          filter: { ownerId: $ownerId, status: published }
```

## Fields

### `entity`

Type: string (entity name). Required unless the repository only declares custom `operations`.

The entity this repository stores. Must match a concrete (non-abstract) key in `entities:`. Pointing a repository at an abstract entity is rejected at build time with `DESUGAR_ABSTRACT_REFERENCED`.

### `crud`

Type: list of operation names. Optional.

Selects which built-in CRUD operations this repository exposes. When omitted, all six are enabled. Listing a subset opts the rest out end-to-end: an omitted operation produces no repository method, no service, no HTTP route, no OpenAPI entry, and no UI action.

Valid operation names are `list`, `get`, `create`, `update`, `replace`, `delete`; any other value fails schema validation. Specifying `crud` without an `entity` is rejected with `CRUD_WITHOUT_ENTITY`.

For the full enablement model and resolution precedence, see [composable-crud](composable-crud.md).

### `datastore`

Type: string (datastore name). Optional.

The datastore this repository is stored in, referencing a key in [`datastores:`](../configuration/datastores.md). Omit it to use the default datastore. This is how a single spec keeps different repositories in different databases.

### `softDelete` and `ttl`

Optional. `softDelete: <field>` makes DELETE stamp a timestamp instead of erasing the row; `ttl: { field, seconds }` expires rows a fixed time after a timestamp. Both require `entity`. See [Record lifecycle](lifecycle.md).

### `abstract` and `extends`

Type: boolean / string (repository name). Optional.

An `abstract: true` repository is a template: it stores nothing and no service may reference it. A repository with `extends: <name>` inherits every key of that abstract repository except `abstract` and `extends`; its own keys win and `operations` merge per operation, so it can add or redefine single operations. Chains of abstract repositories are allowed.

```yaml
repositories:
  published:
    abstract: true
    operations:
      recent:
        query:
          command: find
          filter: { status: published }
  articles:
    entity: article
    extends: published
  pages:
    entity: page
    extends: published
    crud: [list, get]
```

When the abstract repository declares `operations`, the generated backend emits it as a base class that every extending repository subclasses. An abstract repository without operations only contributes configuration.

An abstract repository may declare any repository key, including `crud`, `softDelete`, `ttl` and operations whose queries use `$params` symbols or name fields of the stored entity. Those keys are checked where they take effect: on every extending repository, whose merged entry must be a valid repository for its own entity.

```yaml
repositories:
  auditable:
    abstract: true
    crud: [list, get, create]
    softDelete: deletedAt
    ttl: { field: createdAt, seconds: 86400 }
    operations:
      bySlug:
        query:
          command: findOne
          filter: { slug: $params.slug }
  articles:
    entity: article
    extends: auditable
```

### `operations`

Type: map. Optional.

Declares custom operations beyond the six built-in CRUD verbs. This block is exclusively for custom operations; it does NOT toggle CRUD on or off (use `crud:` for that). Operation names start with a letter and contain only letters, digits and underscores (`publishedByOwner`, `count_all`). Each entry defines exactly one of `query` or `handler`; an entry with neither or both fails schema validation.

On a MongoDB datastore a `query` runs a MongoDB command against the repository's collection:

```yaml
repositories:
  myCollection:
    entity: myEntity
    operations:
      recent:
        query:
          command: find
          filter: { status: published }
          collection: myArchiveCollection   # optional: another repository to query
```

On a relational datastore a `query` is a parameterized `sql` statement:

```yaml
repositories:
  events:
    entity: event
    operations:
      mine:
        query:
          sql: "SELECT * FROM events WHERE owner = :owner"
          params: { owner: "$principal.sub" }
```

Query values that start with `$` are resolved per request; see [operations](operations.md#request-values). The `command` must be one of: `find`, `findOne`, `aggregate`, `countDocuments`, `estimatedDocumentCount`, `distinct`, `insertOne`, `insertMany`, `updateOne`, `updateMany`, `replaceOne`, `deleteOne`, `deleteMany`, `findOneAndUpdate`, `findOneAndReplace`, `findOneAndDelete`, `bulkWrite`. An unknown command is rejected with `QUERY_COMMAND_UNKNOWN`, and a command missing its required field (see [operations](operations.md#query-backed-operations)) with `QUERY_MISSING_FIELD`.

By default a query targets the repository's own collection. `collection:` must name another concrete repository, otherwise the build fails with `QUERY_COLLECTION_NOT_FOUND`. If the repository declares no `entity`, the query must set `collection:`, otherwise the build fails with `QUERY_MISSING_COLLECTION`.

A `handler` names a dotted import path to your own function instead of a query:

```yaml
repositories:
  myCollection:
    entity: myEntity
    operations:
      rebuildSlugs:
        handler: my_app.maintenance.rebuild_slugs
```

To expose a custom operation over HTTP, reference it from a service and add a controller operation with `method` and `path`. See [services/custom-operations](../services/custom-operations.md).

A repository must carry at least an `entity` or one custom operation; an empty repository is rejected with `REPOSITORY_EMPTY`.

## Default operations

When `crud` is omitted, all six operations are enabled (subject to `api.operations.defaults` and per-service overrides):

| Operation | HTTP method | Description |
|-----------|-------------|-------------|
| `list` | GET | Return all documents |
| `get` | GET | Return one document by ID |
| `create` | POST | Insert a new document |
| `update` | PATCH | Partial update of a document |
| `replace` | PUT | Full replacement of a document |
| `delete` | DELETE | Remove a document by ID |

`replace` (PUT) is enabled by default like the other five; it is not a repository-level opt-in.

## Selecting a subset

To expose only a subset, list it in `crud`. The example below makes `myOtherCollection` read-and-write but never editable (no `update`), so the generated app emits no PATCH route and no Edit action for it:

```yaml
repositories:
  myOtherCollection:
    entity: myOtherEntity
    crud: [create, list, get, delete]
```

## Resolution precedence

The final per-operation decision is resolved in this order, most specific first:

1. A service-level override (`services.<name>.operations.<op>: true | false | {handler}`).
2. The repository `crud` list.
3. `api.operations.defaults` (an OperationFlags object used to disable an op globally, e.g. `{ replace: false }`).
4. All six enabled.

See [operations](operations.md) for service-level overrides and [composable-crud](composable-crud.md) for the full model.

## Example

```yaml
api:
  basePath: /api
  version: v1

repositories:
  users:
    entity: user

  myCollection:
    entity: myEntity
    crud: [list, get, create, update, delete]

  myOtherCollection:
    entity: myOtherEntity
    crud: [create, list, get, delete]
```

Each repository name is independent of the entity name. `users` binds to entity `user`, `myCollection` to `myEntity`, etc. With the `api:` block above, the generated routes live under `/api/v1` (for example `GET /api/v1/myCollection`, `POST /api/v1/myOtherCollection`). The repository name is both the collection name and what controllers and services reference.

## Errors

| Code | Cause |
|------|-------|
| `CRUD_WITHOUT_ENTITY` | `crud` specified on a concrete repository that has no `entity`. |
| `QUERY_COMMAND_UNKNOWN` | `query.command` is not a recognized MongoDB command. |
| `QUERY_MISSING_FIELD` | The command requires a field (e.g. `filter`, `pipeline`) that is absent. |
| `QUERY_MISSING_COLLECTION` | A query on an entity-less repository omits `collection`. |
| `QUERY_COLLECTION_NOT_FOUND` | `query.collection` does not name a concrete repository. |
| `QUERY_FORM_MISMATCH` | A `sql` query on a MongoDB datastore, or a `command` query on a PostgreSQL datastore. |
| `QUERY_SQL_INVALID` | `query.sql` is empty. |
| `REPOSITORY_EMPTY` | A repository declares neither `entity` nor any custom operation. |
| `REPOSITORY_EXTENDS_NOT_FOUND` | `extends` names a repository that does not exist. |
| `REPOSITORY_EXTENDS_NOT_ABSTRACT` | `extends` names a repository without `abstract: true`. |
| `REPOSITORY_CIRCULAR_EXTENDS` | An `extends` chain loops back on itself. |
| `DESUGAR_ABSTRACT_REPOSITORY_BOUND` | A service references an abstract repository. |
| `DESUGAR_ABSTRACT_REFERENCED` | The `entity` names an abstract entity. |
| `LIFECYCLE_FIELD_NOT_FOUND`, `LIFECYCLE_FIELD_NOT_DATETIME` | See [Record lifecycle](lifecycle.md#errors). |
