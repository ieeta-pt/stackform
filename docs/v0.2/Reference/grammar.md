---
title: "Grammar Reference"
description: Every key a version 0.2 spec accepts, with its type and the page that documents it.
---

Every key a `version: "0.2"` spec accepts. `<name>` stands for a name you choose. A key outside this list fails schema validation with `SCHEMA_VALIDATION_ERROR`.


## Version

| Key | Type | Reference |
|-----|------|-----------|
| `version` | `"0.2"` | [concepts](../concepts.md) |

## API

| Key | Type | Reference |
|-----|------|-----------|
| `api` | object | [configuration/api](configuration/api.md) |
| `api.basePath` | string | [configuration/api](configuration/api.md) |
| `api.version` | string | [configuration/api](configuration/api.md) |
| `api.port` | integer | [configuration/api](configuration/api.md) |
| `api.operations` | object | [configuration/api](configuration/api.md) |
| `api.operations.defaults` | object | [configuration/api](configuration/api.md) |
| `api.operations.defaults.list` | boolean | [configuration/api](configuration/api.md) |
| `api.operations.defaults.get` | boolean | [configuration/api](configuration/api.md) |
| `api.operations.defaults.create` | boolean | [configuration/api](configuration/api.md) |
| `api.operations.defaults.update` | boolean | [configuration/api](configuration/api.md) |
| `api.operations.defaults.replace` | boolean | [configuration/api](configuration/api.md) |
| `api.operations.defaults.delete` | boolean | [configuration/api](configuration/api.md) |
| `api.operations.auth` | object | [configuration/api](configuration/api.md) |
| `api.operations.auth.register` | boolean | [configuration/api](configuration/api.md) |
| `api.operations.auth.login` | boolean | [configuration/api](configuration/api.md) |
| `api.cors` | object | [configuration/api](configuration/api.md) |
| `api.cors.origins` | list of strings | [configuration/api](configuration/api.md) |
| `api.cors.methods` | list of strings | [configuration/api](configuration/api.md) |
| `api.cors.headers` | list of strings | [configuration/api](configuration/api.md) |
| `api.cors.credentials` | boolean | [configuration/api](configuration/api.md) |
| `api.securityHeaders` | boolean | [configuration/api](configuration/api.md) |

## Imports

| Key | Type | Reference |
|-----|------|-----------|
| `imports` | map | [services/overview](services/overview.md#imports) |

## MongoDB

| Key | Type | Reference |
|-----|------|-----------|
| `mongo` | object | [configuration/mongo](configuration/mongo.md) |
| `mongo.uri` | string | [configuration/mongo](configuration/mongo.md) |
| `mongo.database` | string | [configuration/mongo](configuration/mongo.md) |

## Datastores

| Key | Type | Reference |
|-----|------|-----------|
| `datastores` | map | [configuration/datastores](configuration/datastores.md) |
| `datastores.<name>.type` | `mongodb` \| `mongo` \| `postgres` \| `postgresql` | [configuration/datastores](configuration/datastores.md) |
| `datastores.<name>.uri` | string | [configuration/datastores](configuration/datastores.md) |
| `datastores.<name>.database` | string | [configuration/datastores](configuration/datastores.md) |
| `datastores.<name>.dsn` | string | [configuration/datastores](configuration/datastores.md) |
| `datastores.<name>.default` | boolean | [configuration/datastores](configuration/datastores.md) |

## Entities

| Key | Type | Reference |
|-----|------|-----------|
| `entities` | map | [entities/overview](entities/overview.md) |
| `entities.<name>.type` | `base` \| `auth` | [entities/overview](entities/overview.md) |
| `entities.<name>.extends` | string | [entities/inheritance](entities/inheritance.md) |
| `entities.<name>.abstract` | boolean | [entities/inheritance](entities/inheritance.md) |
| `entities.<name>.pk` | string | [entities/primary-keys](entities/primary-keys.md) |
| `entities.<name>.fields` | map | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.type` | `string` \| `number` \| `boolean` \| `datetime` \| `enum` \| `array` \| `object` \| `ref` \| `id` | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.required` | boolean | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.readonly` | boolean | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.default` | any | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.minLength` | integer | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.maxLength` | integer | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.format` | `email` \| `e164` \| `uri` \| `uuidv7` \| `uuidv4` | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.min` | number | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.max` | number | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.values` | list of strings | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.items` | object | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.items.*` | a nested field, with the keys of `fields.<name>` | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.properties` | map | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.properties.<name>.*` | a nested field, with the keys of `fields.<name>` | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.additionalProperties` | boolean | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.ref` | string | [entities/field-types](entities/field-types.md) |
| `entities.<name>.fields.<name>.unique` | boolean | [entities/field-types](entities/field-types.md) |
| `entities.<name>.auth` | object | [auth/overview](auth/overview.md) |
| `entities.<name>.auth.identifier` | string | [auth/overview](auth/overview.md) |
| `entities.<name>.auth.via` | string or list of strings or list of objects | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.via.provider` | string | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.via.identifier` | string | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.via.claim_mapping` | map | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.via.auto_provision` | boolean | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.via.relations` | map | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.via.relations.<name>.collection` | string | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.via.relations.<name>.match` | map | [auth/login-and-sso](auth/login-and-sso.md) |
| `entities.<name>.auth.roles` | string | [auth/overview](auth/overview.md) |
| `entities.<name>.roles` | object | [roles/overview](roles/overview.md) |
| `entities.<name>.roles.values` | list of strings | [roles/overview](roles/overview.md) |
| `entities.<name>.roles.default` | string | [roles/overview](roles/overview.md) |
| `entities.<name>.roles.hierarchy` | map | [roles/overview](roles/overview.md) |

## Repositories

| Key | Type | Reference |
|-----|------|-----------|
| `repositories` | map | [repositories/overview](repositories/overview.md) |
| `repositories.<name>.softDelete` | string | [repositories/lifecycle](repositories/lifecycle.md) |
| `repositories.<name>.ttl` | object | [repositories/lifecycle](repositories/lifecycle.md) |
| `repositories.<name>.ttl.field` | string | [repositories/lifecycle](repositories/lifecycle.md) |
| `repositories.<name>.ttl.seconds` | integer | [repositories/lifecycle](repositories/lifecycle.md) |
| `repositories.<name>.abstract` | boolean | [repositories/overview](repositories/overview.md) |
| `repositories.<name>.extends` | string | [repositories/overview](repositories/overview.md) |
| `repositories.<name>.entity` | string | [repositories/overview](repositories/overview.md) |
| `repositories.<name>.datastore` | string | [repositories/overview](repositories/overview.md) |
| `repositories.<name>.crud` | list of `list` \| `get` \| `create` \| `update` \| `replace` \| `delete` | [repositories/composable-crud](repositories/composable-crud.md) |
| `repositories.<name>.operations` | map | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query` | object | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.command` | string | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.collection` | string | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.key` | string | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.sql` | string | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.filter` | any | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.pipeline` | any | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.document` | any | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.documents` | any | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.update` | any | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.replacement` | any | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.requests` | any | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.params` | map | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.handler` | string | [repositories/operations](repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.includeDeleted` | boolean | [repositories/lifecycle](repositories/lifecycle.md#includedeleted) |

## Services

| Key | Type | Reference |
|-----|------|-----------|
| `services` | map | [services/overview](services/overview.md) |
| `services.<name>.abstract` | boolean | [services/overview](services/overview.md#inheritance-with-abstract-and-extends) |
| `services.<name>.extends` | string | [services/overview](services/overview.md#inheritance-with-abstract-and-extends) |
| `services.<name>.repository` | string | [services/overview](services/overview.md) |
| `services.<name>.operation` | string | [services/overview](services/overview.md) |
| `services.<name>.handler` | string | [services/overview](services/overview.md) |
| `services.<name>.operations` | map | [services/overview](services/overview.md#per-operation-overrides) |
| `services.<name>.operations.<name>.handler` | string | [services/overview](services/overview.md#per-operation-overrides) |

## Controllers

| Key | Type | Reference |
|-----|------|-----------|
| `controllers` | map | [controllers/overview](controllers/overview.md) |
| `controllers.<name>.service` | string | [controllers/overview](controllers/overview.md) |
| `controllers.<name>.base_path` | string | [controllers/overview](controllers/overview.md) |
| `controllers.<name>.access` | string or list of strings or objects | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.access.given` | map | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.access.when` | string or list of strings | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.access.then` | `allow` \| `deny` | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.access.reason` | string | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.operations` | map | [controllers/operations](controllers/operations.md) |
| `controllers.<name>.operations.<name>.method` | `GET` \| `POST` \| `PUT` \| `PATCH` \| `DELETE` | [controllers/operations](controllers/operations.md) |
| `controllers.<name>.operations.<name>.path` | string | [controllers/operations](controllers/operations.md) |
| `controllers.<name>.operations.<name>.access` | string or list of strings or objects | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.operations.<name>.access.given` | map | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.operations.<name>.access.when` | string or list of strings | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.operations.<name>.access.then` | `allow` \| `deny` | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.operations.<name>.access.reason` | string | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.routes` | map | [controllers/overview](controllers/overview.md) |
| `controllers.<name>.routes.<name>.access` | string or list of strings or objects | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.routes.<name>.access.given` | map | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.routes.<name>.access.when` | string or list of strings | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.routes.<name>.access.then` | `allow` \| `deny` | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.routes.<name>.access.reason` | string | [controllers/access-control](controllers/access-control.md) |
| `controllers.<name>.routes.<name>.service` | string | [controllers/overview](controllers/overview.md) |
| `controllers.<name>.routes.<name>.method` | `GET` \| `POST` \| `PUT` \| `PATCH` \| `DELETE` | [controllers/overview](controllers/overview.md) |
| `controllers.<name>.routes.<name>.path` | string | [controllers/overview](controllers/overview.md) |

## Providers

| Key | Type | Reference |
|-----|------|-----------|
| `providers` | map | [providers/overview](providers/overview.md) |
| `providers.<name>.type` | `oidc` \| `saml` | [providers/overview](providers/overview.md) |
| `providers.<name>.trust` | `app` \| `idp` | [providers/overview](providers/overview.md) |
| `providers.<name>.client_id` | string | [providers/overview](providers/overview.md) |
| `providers.<name>.client_secret` | string | [providers/overview](providers/overview.md) |
| `providers.<name>.discovery_url` | string | [providers/overview](providers/overview.md) |
| `providers.<name>.issuer` | string | [providers/overview](providers/overview.md) |
| `providers.<name>.audiences` | list of strings | [providers/overview](providers/overview.md) |
| `providers.<name>.idp_metadata_url` | string | [providers/saml](providers/saml.md) |
| `providers.<name>.sp_entity_id` | string | [providers/saml](providers/saml.md) |

## DTOs

| Key | Type | Reference |
|-----|------|-----------|
| `dto` | map | [dto/overview](dto/overview.md) |
| `dto.<name>.fields` | map | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.type` | `string` \| `number` \| `boolean` \| `datetime` \| `enum` \| `array` \| `object` \| `ref` \| `id` | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.required` | boolean | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.readonly` | boolean | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.default` | any | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.minLength` | integer | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.maxLength` | integer | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.format` | `email` \| `e164` \| `uri` \| `uuidv7` \| `uuidv4` | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.min` | number | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.max` | number | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.values` | list of strings | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.items` | object | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.items.*` | a nested field, with the keys of `fields.<name>` | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.properties` | map | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.properties.<name>.*` | a nested field, with the keys of `fields.<name>` | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.additionalProperties` | boolean | [dto/overview](dto/overview.md) |
| `dto.<name>.fields.<name>.ref` | string | [dto/overview](dto/overview.md) |

## Policies

| Key | Type | Reference |
|-----|------|-----------|
| `policies` | map | [policies/overview](policies/overview.md) |
| `policies.<name>.given` | map | [policies/overview](policies/overview.md) |
| `policies.<name>.params` | list of strings | [policies/overview](policies/overview.md) |
| `policies.<name>.when` | string or list of strings | [policies/overview](policies/overview.md) |

## UI

| Key | Type | Reference |
|-----|------|-----------|
| `ui` | object | [ui/overview](ui/overview.md) |
| `ui.frontend` | object | [ui/frontend](ui/frontend.md) |
| `ui.frontend.pack` | string | [ui/frontend](ui/frontend.md) |
| `ui.frontend.output` | string | [ui/frontend](ui/frontend.md) |
| `ui.frontend.overwrite` | `never` \| `always` | [ui/frontend](ui/frontend.md) |
| `ui.config` | map | [ui/overview](ui/overview.md) |
| `ui.collections` | map | [ui/collections](ui/collections.md) |
| `ui.collections.<name>.fields` | map | [ui/collections](ui/collections.md) |
| `ui.collections.<name>.fields.<name>.from` | string | [ui/collections](ui/collections.md) |
| `ui.collections.<name>.fields.<name>.format` | string | [ui/collections](ui/collections.md) |
| `ui.components` | map | [ui/components](ui/components.md) |
| `ui.components.<name>.props` | map | [ui/components](ui/components.md) |
| `ui.components.<name>.props.<name>.required` | boolean | [ui/components](ui/components.md) |
| `ui.components.<name>.render` | object | [ui/components](ui/components.md) |
| `ui.components.<name>.render.component` | string | [ui/components](ui/components.md) |
| `ui.components.<name>.render.props` | map | [ui/components](ui/components.md) |
| `ui.views` | map | [ui/views](ui/views.md) |
| `ui.views.<name>.path` | string | [ui/views](ui/views.md) |
| `ui.views.<name>.component` | string | [ui/views](ui/views.md) |
| `ui.views.<name>.props` | map | [ui/views](ui/views.md) |

## Deploy

| Key | Type | Reference |
|-----|------|-----------|
| `deploy` | object | [configuration/deploy](configuration/deploy.md) |
| `deploy.name` | string | [configuration/deploy](configuration/deploy.md) |
| `deploy.port` | integer | [configuration/deploy](configuration/deploy.md) |
| `deploy.runtime` | `docker` \| `systemd` | [configuration/deploy](configuration/deploy.md) |
| `deploy.services` | map | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.image` | string | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.build` | string or object | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.build.context` | string | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.build.dockerfile` | string | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.build.args` | map | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.ports` | list of integers or strings | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.environment` | map or list of strings | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.volumes` | list of strings | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.depends_on` | list of strings or map | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.depends_on.<name>.condition` | `service_started` \| `service_healthy` \| `service_completed_successfully` | [configuration/deploy](configuration/deploy.md) |
| `deploy.services.<name>.command` | string or list of strings | [configuration/deploy](configuration/deploy.md) |
| `deploy.include` | list of strings | [configuration/deploy](configuration/deploy.md) |
| `deploy.mongo` | object | [configuration/deploy](configuration/deploy.md) |
| `deploy.mongo.local` | boolean | [configuration/deploy](configuration/deploy.md) |
| `deploy.docker` | object | [configuration/deploy](configuration/deploy.md) |
| `deploy.docker.image` | string | [configuration/deploy](configuration/deploy.md) |
| `deploy.systemd` | object | [configuration/deploy](configuration/deploy.md) |
| `deploy.systemd.user` | string | [configuration/deploy](configuration/deploy.md) |
| `deploy.systemd.restart` | string | [configuration/deploy](configuration/deploy.md) |

## Session

| Key | Type | Reference |
|-----|------|-----------|
| `session` | object | [configuration/session](configuration/session.md) |
| `session.algorithm` | `HS256` \| `RS256` | [configuration/session](configuration/session.md) |
| `session.ttl` | integer | [configuration/session](configuration/session.md) |
| `session.refresh` | boolean | [configuration/session](configuration/session.md) |
| `session.delivery` | `token-url` \| `cookie` | [configuration/session](configuration/session.md) |
