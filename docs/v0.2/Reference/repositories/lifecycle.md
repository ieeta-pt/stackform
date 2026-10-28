---
title: "Record Lifecycle"
description: "softDelete keeps deleted rows as tombstones, ttl expires rows a fixed time after a timestamp, and includeDeleted lets a custom query read both."
---

A repository can control how long its rows stay visible:

- `softDelete` turns DELETE into a tombstone: the row is kept and stamped, not erased.
- `ttl` expires a row a fixed number of seconds after a timestamp it holds.

Both need an `entity`. They work wherever the repository's datastore is served:

| Datastore | Backends |
|-----------|----------|
| MongoDB | dev server, FastAPI, raw ASGI, DRF |
| Relational | dev server, FastAPI |

```yaml
repositories:
  sessions:
    entity: session
    softDelete: removedAt
    ttl: { field: lastSeenAt, seconds: 86400 }
```

## `softDelete`

Type: string (field name). Optional.

DELETE sets this field to the current time instead of removing the row, and answers `200` with the stamped record. From then on the row is hidden from `list`, `get`, `update`, `replace`, `delete` and from custom operations, so a second DELETE answers `404`. A removed row cannot be restored.

The field must be a `datetime`. When the entity does not declare it, it is added as a readonly `datetime`; either way a request body that writes it is rejected with `422`.

Custom operations that delete stamp the field as well:

- MongoDB: `deleteOne`, `deleteMany` and `findOneAndDelete`, also inside `bulkWrite`.
- Relational: a `DELETE` statement on the table, including one that selects its rows through a subquery or `USING`.

A unique value of a removed row is free again: a new row may take it. Unique indexes cover only rows that are not removed.

On an identity collection, a removed user can no longer sign in, and a token issued to it before the removal is refused with `401`. Its email can be registered again. A sign-in through an external provider never revives a removed user; it provisions a new one.

A record's files stay in storage when the record is soft-deleted, since the record is kept. See [file endpoints](../../../v0.3/file-endpoints.md#lifecycle).

## `ttl`

Type: object with `field` (a `datetime` field of the entity) and `seconds` (integer, at least 1). Optional.

A row expires `seconds` after the instant stored in `field`. Expired rows are excluded from every query at once; a row whose `field` is null never expires. The server erases expired rows at startup and every 60 seconds, deleting the files they hold. On MongoDB, a TTL index named `lifecycle_expiry` on `field` also erases them, 120 seconds after the purge would.

The generated UI lists and opens only the rows the API serves, so it never shows a removed or expired row.

## Custom operations

Custom operations keep to the lifecycle of every collection or table they touch, not only their own:

- MongoDB: reads and writes match visible rows only, and aggregation pipelines see visible rows of the collections they join through `$lookup`, `$unionWith`, `$graphLookup` and `$facet`. `bulkWrite` applies the same rule to each of its requests, and `estimatedDocumentCount` answers the exact count of visible rows.
- Relational: every table a `sql` statement names, in joins, subqueries and `UNION`s alike, stands for its visible rows; `UPDATE` and `DELETE` reach visible rows only.

Operations inherited from an abstract repository follow the lifecycle of the repository that inherits them.

## `includeDeleted`

Type: `true`. Allowed only on a custom `query` operation of a repository with `softDelete` or `ttl`.

The operation's reads also see soft-deleted and expired rows. Its writes stay confined to visible rows: `includeDeleted` cannot update, delete or restore a removed or expired row. Generated `list`, `get`, `update`, `replace` and `delete` operations always hide them.

```yaml
repositories:
  sessions:
    entity: session
    softDelete: removedAt
    operations:
      history:
        query:
          sql: "SELECT * FROM sessions WHERE owner = :owner"
          params: { owner: "$principal.sub" }
        includeDeleted: true
```

## Errors

| Code | Cause |
|------|-------|
| `LIFECYCLE_FIELD_NOT_FOUND` | `ttl.field` is not a field of the entity. |
| `LIFECYCLE_FIELD_NOT_DATETIME` | The `softDelete` or `ttl.field` field is not a `datetime`. |
| `SCHEMA_VALIDATION_ERROR` | `softDelete` or `ttl` without `entity`, or `includeDeleted` on a repository without a lifecycle. |
