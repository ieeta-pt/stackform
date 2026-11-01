---
title: "Handler Context"
description: Every custom handler receives one request object, the same under stackform run and every generated backend, and returns the JSON response body.
---

A custom handler is a plain or `async` Python function that receives one request
object and returns the JSON response body. The contract is the same under
`stackform run` and every generated backend (FastAPI, DRF, raw ASGI), and for every
place a handler is declared:

- a service custom operation, `services.<name>.operations.<op>.handler`
- a service handler, `services.<name>.handler` (see [Service `input:`](../../../v0.3/service-input.md))
- a repository operation, `repositories.<name>.operations.<op>.handler`

```python
async def publish(request):
    if "reason" not in request.body:
        raise ValueError("A reason is required")
    return {"id": request.params["id"], "by": request.principal["sub"], "reason": request.body["reason"]}
```

## Request attributes

| Attribute | Value |
|-----------|-------|
| `request.params` | Route path parameters, e.g. `request.params["id"]` for `/{id}` |
| `request.query` | Query parameters; a repeated key keeps its last value |
| `request.headers`, `request.cookies` | Request headers and cookies |
| `request.body` | The JSON body, or `{}` when the body is empty or not JSON |
| `request.principal` | The signed-in principal, or `None` on a public route |
| `request.inputs` | The service's `with:` values, keyed by their `with:` names |

`request.principal` is a plain dict:

| Key | Value |
|-----|-------|
| `sub` | The caller's primary-key value |
| `identity_collection` | The auth entity the caller belongs to |
| `roles` | The caller's roles, as a list |
| `record` | The caller's stored record, without the stored id and password |

## Access and data

A handler route runs the controller operation's `access:` rules before the handler,
exactly like a built-in operation: a request no rule admits gets 401 without valid
credentials and 403 otherwise. The handler owns its data access: import the client
or service it needs.

## Response and errors

The return value is sent as the JSON body with status 200. Raising `ValueError`
answers 422 with the exception message as `detail`. Any other exception answers 500.

## See Also

- [Custom operations](./custom-operations.md)
- [Services overview](./overview.md)
- [Repository operations](../repositories/operations.md)
- [Tutorial 09: Custom Operations](../../Tutorial/09-custom-operations.md)
