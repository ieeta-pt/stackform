---
title: "`deploy:`"
description: The `deploy:` section makes `stackform build` emit Docker Compose or systemd deployment artifacts, with the app's datastores and any extra services.
---

The `deploy:` section makes `stackform build` (with `all` or `deploy`) write deployment artifacts next to the backend: an Ansible inventory and playbook plus either a Docker Compose stack or a systemd unit. Without it, no deploy artifacts are produced.

## Schema

```yaml
deploy:
  runtime: docker          # required: docker | systemd
  name: my-app             # optional, default: app
  port: 8000               # optional, default: api.port
  mongo:
    local: true            # optional, default: derived from each MongoDB URI
  docker:
    image: ghcr.io/me/my-app:1.0   # optional; default: build ./backend
  systemd:
    user: ubuntu           # optional, default: ubuntu
    restart: on-failure    # optional, default: on-failure
  include:                 # optional, docker only: Compose files to include
    - monitoring.compose.yml
  services:                # optional, docker only: extra Compose services
    worker:
      build: ./worker
      environment: { QUEUE: jobs }
      depends_on: [app]
```

## Fields

### `runtime`

Type: `docker` or `systemd`. Required.

- `docker`: a `docker-compose.yml` with the `app` service, one service per local datastore, a `frontend` service when the spec has a `ui:` block, and the extra `services`; plus `backend/Dockerfile`, `.env.example` and Ansible roles that install Docker and start the stack.
- `systemd`: an `app.service` unit that runs the backend with uvicorn from `/opt/<name>`, plus Ansible roles that install Python and, for a local MongoDB datastore, MongoDB.

### `name`

Type: string. Default: `app`.

Names the deployment: the systemd unit description and its install directory `/opt/<name>`, and the Ansible play.

### `port`

Type: integer, 1 to 65535. Default: [`api.port`](./api.md#port).

The port the deployed app listens on. Docker publishes it as `${APP_PORT:-<port>}` and passes it to the app as `PORT`.

### `mongo.local`

Type: boolean. Optional.

Whether the MongoDB datastores run on the deploy host. `true` adds a MongoDB container (Docker) or installs MongoDB (systemd); `false` points the app at the URI from the spec. When unset, a MongoDB datastore is local exactly when its URI names `localhost` or `127.0.0.1`. A PostgreSQL datastore is local by the same rule applied to its DSN.

### `docker.image`

Type: string. Optional.

A prebuilt image for the `app` service. When set, the stack pulls it; otherwise it builds `backend/Dockerfile`.

### `systemd.user` and `systemd.restart`

Type: string. Defaults: `ubuntu` and `on-failure`.

The `User=` and `Restart=` values of the generated unit.

### `include`

Type: list of strings. Optional; used by `runtime: docker`.

Paths copied into the top-level `include:` of the generated `docker-compose.yml`.

### `services`

Type: map of service name to service. Optional; used by `runtime: docker`.

Extra Compose services added to the stack. Each needs `image` or `build`:

| Key | Type | Description |
|-----|------|-------------|
| `image` | string | Image to run. |
| `build` | string or `{ context, dockerfile, args }` | Build context relative to the spec. It must be a subdirectory of the spec's directory; it is copied into the output so the bundle is self-contained. |
| `ports` | list of integers or strings | Published ports. |
| `environment` | map of strings, or list of `KEY=value` strings | Environment variables. |
| `volumes` | list of strings | Volume mounts. |
| `depends_on` | list of service names, or map of name to `{ condition }` | Start order; `condition` is `service_started`, `service_healthy` or `service_completed_successfully`. |
| `command` | string or list of strings | Command override. |

## Errors

| Code / message | Cause |
|----------------|-------|
| `SCHEMA_VALIDATION_ERROR` | `runtime` missing or unknown, an unknown key, a service with neither `image` nor `build`, or a value of the wrong type. |
| `deploy service '<name>' build context not found` | A `build` context directory does not exist. |
| `deploy service '<name>' build context must be a subdirectory of the spec that excludes the output` | A `build` context contains the spec or the output directory. |
| `No 'deploy' block found in the YAML spec.` | `stackform build <spec> deploy` on a spec without `deploy:`. |
