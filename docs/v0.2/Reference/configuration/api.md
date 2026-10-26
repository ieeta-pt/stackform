---
title: "`api:`"
description: The `api:` section sets URL prefixes (basePath/version), the default port, CORS, security headers, and which CRUD and auth operations are generated.
---

The `api:` section controls global API settings: the URL prefix (`basePath` + `version`), the default port, CORS, standard security headers, and which CRUD and auth operations the generator produces.

## Schema

```yaml
api:
  basePath: /api          # optional, default: /api
  version: v1             # optional, default: none (no version segment)
  port: 8000              # optional, default: 8000
  cors:                   # optional; omit to disable CORS entirely
    origins: ["*"]
    methods: ["*"]
    headers: ["*"]
    credentials: false
  securityHeaders: true   # optional, default: true
  operations:
    defaults:             # optional; use this to DISABLE ops (all six are on by default)
      replace: false
    auth:                 # optional; register/login are NOT generated unless listed here
      register: true
      login: true
```

## Fields

### `basePath`

Type: string. Default: `/api`.

Prepended to every route path. With `basePath: /api` and a controller whose `base_path` is `/my-collection`, routes are served under `/api/my-collection`. Omitting `basePath` still yields the `/api` prefix; set it to `""` to serve routes at the root.

### `version`

Type: string. Default: none.

Optional version segment inserted after `basePath`. When omitted, no version segment is added. With `basePath: /api` and `version: v1`, routes are served under `/api/v1/...`:

```yaml
api:
  basePath: /api
  version: v1
```

```
GET  /api/v1/my-collection
POST /api/v1/my-collection
```

The same prefix is used to derive the frontend's API base URL (`basePath` plus the optional `/version`), so the generated React app calls the backend at the matching path.

### `port`

Type: integer (1-65535). Default: `8000`.

The port the API listens on. `stackform run` binds to it unless `-p`/`--port` is given; every generated backend (FastAPI, Django REST Framework, raw ASGI) uses it as its `PORT` setting, which the `PORT` environment variable overrides at runtime; and `deploy.port` defaults to it.

### `cors`

Type: object. Optional.

Configures Cross-Origin Resource Sharing (CORS). When the `cors:` block is omitted, no CORS middleware is added, so cross-origin browser requests are blocked. Add the block (even empty) to enable it with permissive defaults.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `origins` | list of strings | `["*"]` | Allowed origins. |
| `methods` | list of strings | `["*"]` | Allowed HTTP methods. |
| `headers` | list of strings | `["*"]` | Allowed HTTP headers. |
| `credentials` | boolean | `false` | Allow credentials (cookies, authorization headers). |

### `securityHeaders`

Type: boolean. Default: `true`.

Adds standard security headers to every response of the dev server and of every generated backend:

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `no-referrer` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Cross-Origin-Opener-Policy` | `same-origin` |

A header the response already carries is left as it is. Set `securityHeaders: false` when a reverse proxy in front of the API sets these headers.

### `operations.defaults`

Type: object (operation flags). Optional.

All six CRUD operations -- `list`, `get`, `create`, `update`, `replace`, `delete` -- are **enabled by default**. This block exists to DISABLE operations globally; set any flag to `false` to turn that operation off across every repository.

| Field | Type | Default |
|-------|------|---------|
| `list` | boolean | `true` |
| `get` | boolean | `true` |
| `create` | boolean | `true` |
| `update` | boolean | `true` |
| `replace` | boolean | `true` |
| `delete` | boolean | `true` |

Example -- turn off full-document replace (PUT) everywhere:

```yaml
api:
  operations:
    defaults:
      replace: false
```

A repository can further narrow its own operations with its `crud:` list, and a service can override individual operations. See `operation resolution` below.

### `operations.auth`

Type: object (operation flags). Optional.

Controls the `register` and `login` endpoints for `type: auth` entities. These are **not generated unless you list them here.** Omitting `operations.auth` produces an auth entity with no register or login route.

| Field | Type | Default |
|-------|------|---------|
| `register` | boolean | not generated unless set to `true` |
| `login` | boolean | not generated unless set to `true` |

```yaml
api:
  operations:
    auth:
      register: true
      login: true
```

## Operation resolution

For each CRUD operation, the effective on/off decision is resolved in this order (later wins):

1. all six enabled (the baseline)
2. `api.operations.defaults` (global disables)
3. the repository's `crud:` list (`repositories.<name>.crud`)
4. the service's per-operation override (`services.<name>.operations.<op>`)

A disabled operation is removed end to end: no repository method, no service, no HTTP route, no OpenAPI entry, and no UI action.

## Environment-variable interpolation

Any string value in the spec, including those under `api:`, may reference an environment variable with `${VAR}` or `${VAR:-default}`. Interpolation runs after the YAML is loaded and before schema validation, so the substituted value must still satisfy the schema. The result is always a string, so interpolate only string-typed keys: `port: ${PORT}` fails with `SCHEMA_VALIDATION_ERROR`; set the runtime port through the `PORT` environment variable of the generated app instead. A missing variable with no default aborts generation with `Environment variable 'VAR' is required`.

```yaml
api:
  basePath: ${API_BASE_PATH:-/api}
  version: ${API_VERSION:-v1}
```

## Example

A reproducible block that serves routes under `/api/v1`, enables full CRUD plus replace, and turns on register/login:

```yaml
api:
  basePath: /api
  version: v1
  port: 8080
  cors:
    origins: ["http://localhost:3000"]
  operations:
    auth:
      register: true
      login: true
```

With this configuration, the `myCollection` resource is served at `/api/v1/my-collection` (including `PUT /api/v1/my-collection/{id}` for replace), and the auth entity exposes `POST /api/v1/my-collection/register` and `POST /api/v1/my-collection/login`.
