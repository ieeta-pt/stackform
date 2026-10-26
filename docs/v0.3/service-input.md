---
title: Service `input:` and `with:` forwarding
description: Declare the request values a service requires and map them to its repository operation or custom handler.
---

# Service `input:` and `with:` forwarding

In v0.3, a service declares the request values it requires with `input:` and
maps those validated values to its repository operation or custom handler with
`with:`. Both the in-process server and generated FastAPI, DRF, and raw-ASGI
backends enforce the same contract. Both keys are v0.3 only; a v0.2 spec using
either is rejected with `SCHEMA_VALIDATION_ERROR`.

## Declaring inputs

`input:` is an inline field map or a non-empty list of DTO names. DTO fields are
merged into one input contract.

```yaml
services:
  archivePost:
    repository: posts
    operation: archive
    input:
      postId: string
      reason:
        type: string
        required: false
  publishPost:
    handler: app.handlers.publish
    input: [PublishRequest]
```

An input field is `string`, `number`, `boolean`, `datetime`, `enum`, `array`,
`object` or `ref`, and takes the keys an entity field of that type takes (see
[Field types](../v0.2/Reference/entities/field-types.md)). An `object` input
with `properties` checks every nested key and rejects keys it does not declare
unless `additionalProperties: true`. A `file` input is rejected with
`FILE_FIELD_CONTEXT_INVALID`; files travel through
[file endpoints](file-endpoints.md). Fields are required unless their
configuration sets `required: false`.

Values come from JSON body fields and route path parameters. A path parameter
wins when the body contains the same name, so a body cannot spoof a route
identity, and a matching [access-rule `bind:`](controller-bind.md) wins over
both. A path segment is read as text; a `number` or `boolean` input reads the
number or `true`/`false` its segment spells, so `GET /sized/3` gives a
`size: number` input the value `3`. Missing or invalid inputs return 422 before
the repository operation or handler runs. An optional input may be absent or
`null`.

A service runs either a repository `operation` or a `handler`, never both; a
service declaring both is rejected with `SCHEMA_VALIDATION_ERROR`.

## Forwarding values

`with:` maps a downstream name to a declared `$input` or to a YAML scalar
literal. Strings are ordinary YAML strings; no nested quoting is required.

```yaml
services:
  archivePost:
    repository: posts
    operation: archive
    input:
      postId: string
    with:
      lookup: $postId
      state: archived
      audit: true
      retries: 3
```

Dotted references such as `$payload.owner.id` traverse object inputs. A symbol
may reference only a field declared by the same service's `input:`. An unbound
name aborts the build with `UNDEFINED_SYMBOL`.

For a repository-backed service, each `with:` key is a root symbol available to
the operation query. Every query symbol must be supplied on every route that
reaches the operation, either by a route slug or by `with:`.

```yaml
repositories:
  posts:
    operations:
      archive:
        query:
          command: findOne
          filter:
            id: $lookup
            state: $state
```

A forwarding key that the repository query does not reference is rejected with
`SERVICE_WITH_TARGET_UNKNOWN`. This catches misspelled targets rather than
silently discarding a value.

A custom handler receives one request object, the same under `stackform run`
and every generated backend, and returns the JSON response body:

```python
def publish(request):
    return {"id": request.inputs["postId"], "by": request.principal["sub"]}
```

| Attribute | Value |
| --- | --- |
| `inputs` | The `with:` values, keyed by their `with:` names |
| `params` | Route path parameters |
| `query` | Query parameters; a repeated key keeps its last value |
| `headers`, `cookies` | Request headers and cookies |
| `body` | The JSON body, or `{}` when the body is empty or not JSON |
| `principal` | The signed-in principal, or `None`; its `record` leaves out the stored id and password |

A handler may be a plain or an `async` function. Raising `ValueError` answers
422.

## Error codes

| Code | Raised when |
| --- | --- |
| `SERVICE_INPUT_INVALID` | `input:` is neither a non-empty field map nor a non-empty DTO list |
| `SERVICE_INPUT_FIELD_INVALID` | an input field type or `required` flag is invalid |
| `SERVICE_INPUT_DTO_NOT_FOUND` | an input lists a DTO that does not exist |
| `SERVICE_WITH_VALUE_INVALID` | a forwarded value is not a `$symbol` or scalar literal |
| `SERVICE_WITH_TARGET_UNKNOWN` | a repository forwarding key is unused by its operation query |
| `UNDEFINED_SYMBOL` | a `with:` symbol is not declared by the service input |
