---
title: "`session:`"
description: The `session:` section sets how the app signs the tokens it mints at login, how long they live, whether they rotate through refresh tokens, and whether they travel in a cookie.
---

The `session:` section configures the session tokens the app mints when an identity logs in (password login, and OIDC or SAML login with `trust: app`). Every key is optional; omitting the section keeps HS256 bearer tokens that live 24 hours.

## Schema

```yaml
session:
  algorithm: HS256     # HS256 (default) | RS256
  ttl: 900             # access-token lifetime in seconds
  refresh: true        # default: false
  delivery: token-url  # token-url (default) | cookie
```

## Fields

### `algorithm`

Type: `HS256` or `RS256`. Default: `HS256`.

- `HS256` signs with the shared secret `JWT_SECRET`.
- `RS256` signs with the RSA private key in `JWT_PRIVATE_KEY` (PEM) and serves the public key set at `GET /.well-known/jwks.json`, outside `basePath`. Each token carries a `kid` matching its key. To rotate keys without ending live sessions, put the old public key in `JWT_RETIRED_PUBLIC_KEY` while tokens signed by it are still valid; the JWKS then publishes both keys.

`stackform build` rejects `RS256` on a spec that never mints a session token (no password identity and no `trust: app` OIDC or SAML login) with `SESSION_ALGORITHM_UNUSED`.

### `ttl`

Type: integer, at least 1. Optional.

Access-token lifetime in seconds, read from the `JWT_ACCESS_TTL_SECONDS` setting it seeds. Without `ttl`, tokens live `JWT_EXPIRATION_HOURS` hours (default 24), or 900 seconds when `refresh` is on.

### `refresh`

Type: boolean. Default: `false`.

Login also returns a `refresh_token`, and every password identity gets `POST /{identity}/refresh`, which takes `{ "refresh_token": "..." }` and returns a new `{ "token", "refresh_token" }` pair. Each refresh token is single-use: presenting one that was already used revokes its whole session family and answers `401 Invalid refresh token`. Refresh tokens live `JWT_REFRESH_TTL_SECONDS` seconds (default 2592000, 30 days).

### `delivery`

Type: `token-url` or `cookie`. Default: `token-url`.

- `token-url`: login returns the token in the response body; clients send it as `Authorization: Bearer <token>`.
- `cookie`: login sets an `HttpOnly; SameSite=Lax` cookie named `session` (`Secure` over HTTPS) and a readable `csrf_token` cookie, and the login body carries the user record and `csrf_token` instead of the token. Unsafe requests (`POST`, `PUT`, `PATCH`, `DELETE`) that carry a session cookie must send the `csrf_token` value in the `x-csrf-token` header, otherwise they are rejected with `403 CSRF token missing or invalid`. With `refresh` on, the refresh token travels in an `HttpOnly` `refresh_token` cookie. `POST /auth/logout`, below `basePath`, expires the cookies. Cookie delivery assumes the UI and the API share an origin.

## Backend support

| Feature | `stackform run` | FastAPI | DRF | raw ASGI |
|---------|-----------------|---------|-----|----------|
| `algorithm` | yes | yes | yes | yes |
| `ttl` | yes | yes | yes | yes |
| `refresh` | yes | yes | no | no |
| `delivery: cookie` | yes | yes | no | no |

Building a DRF or raw backend from a spec that sets `refresh: true` or `delivery: cookie` fails with `BACKEND_FEATURE_UNSUPPORTED`.

## Errors

| Code | Cause |
|------|-------|
| `SCHEMA_VALIDATION_ERROR` | An unknown key, an `algorithm` or `delivery` outside the listed values, or a `ttl` below 1. |
| `SESSION_ALGORITHM_UNUSED` | `algorithm: RS256` on a spec that never mints a session token (`stackform build`). |
| `BACKEND_FEATURE_UNSUPPORTED` | `refresh` or `delivery: cookie` on the DRF or raw backend. |
