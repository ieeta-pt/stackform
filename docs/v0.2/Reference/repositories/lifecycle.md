---
title: "Record Lifecycle"
description: "softDelete keeps deleted rows as tombstones, ttl expires rows a fixed time after a timestamp, and includeDeleted lets a custom operation see both."
---

A repository can control how long its rows stay visible:

- `softDelete` turns DELETE into a tombstone: the row is kept and stamped, not erased.
- `ttl` expires a row a fixed number of seconds after a timestamp it holds.

Both need an `entity` and work on every datastore and every backend.

```yaml
repositories:
  sessions:
    entity: session
    softDelete: removedAt
    ttl: { field: lastSeenAt, seconds: 86400 }
```

## `softDelete`

Type: string (field name). Optional.

DELETE sets this field to the current time instead of removing the row, and answers `200` with the stamped record. From then on the row is hidden from `list`, `get`, `update`, `replace`, `delete` and from custom operations, so a second DELETE answers `404`.

The field must be a `datetime`. When the entity does not declare it, it is added as a readonly `datetime`; either way a request body that writes it is rejected with `422`.

On MongoDB, custom `deleteOne`, `deleteMany` and `findOneAndDelete` operations soft-delete as well.

## `ttl`

Type: object with `field` (a `datetime` field of the entity) and `seconds` (integer, at least 1). Optional.

A row expires `seconds` after the instant stored in `field`. Expired rows are excluded from every query at once; a row whose `field` is null never expires. Expired rows are also erased in the background:

- MongoDB: a TTL index named `lifecycle_expiry` on `field`.
- Relational datastores: a purge at startup and every 60 seconds.

## `includeDeleted`

Type: `true`. Allowed only on a custom `query` operation of a repository with `softDelete` or `ttl`.

The operation also sees soft-deleted and expired rows. It changes reads only; writes still follow the lifecycle.

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

A query the lifecycle filter cannot rewrite must set `includeDeleted: true`: any `sql` query, and the `bulkWrite` and `estimatedDocumentCount` commands. Without it the spec fails schema validation.

## Errors

| Code | Cause |
|------|-------|
| `LIFECYCLE_FIELD_NOT_FOUND` | `ttl.field` is not a field of the entity. |
| `LIFECYCLE_FIELD_NOT_DATETIME` | The `softDelete` or `ttl.field` field is not a `datetime`. |
| `SCHEMA_VALIDATION_ERROR` | `softDelete` or `ttl` without `entity`, `includeDeleted` on a repository without a lifecycle, or a `sql`, `bulkWrite` or `estimatedDocumentCount` operation on a lifecycle repository without `includeDeleted: true`. |
