---
title: Grammar reference
description: Every key a v0.3 spec accepts, and the access and binding grammar inside them.
---

This page lists every key a v0.3 spec accepts, then the access and binding
forms used inside those keys. The JSON schema validates the keys and their
shape; the parsers and semantic validators enforce the grammar, declared names,
symbol scopes, and wiring rules described below. The live server and generated
FastAPI, Django REST Framework, and raw-ASGI backends implement the same
behavior.

## Spec keys

Every key a `version: "0.3"` spec accepts. `<name>` stands for a name you
choose. A key outside these tables, or a value of the wrong type, fails schema
validation with `SCHEMA_VALIDATION_ERROR`. Keys v0.3 shares with v0.2 behave as
the v0.2 reference describes.

### Version

| Key | Type | Reference |
| --- | --- | --- |
| `version` | `"0.3"` | [Spec version 0.3](spec-version.md) |

### API

| Key | Type | Reference |
| --- | --- | --- |
| `api` | object | [api](../v0.2/Reference/configuration/api.md) |
| `api.basePath` | string | [api](../v0.2/Reference/configuration/api.md) |
| `api.version` | string | [api](../v0.2/Reference/configuration/api.md) |
| `api.port` | integer, 1 to 65535 | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations` | object | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.defaults` | object | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.defaults.list` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.defaults.get` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.defaults.create` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.defaults.update` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.defaults.replace` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.defaults.delete` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.auth` | object | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.auth.register` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.operations.auth.login` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.cors` | object | [api](../v0.2/Reference/configuration/api.md) |
| `api.cors.origins` | list of strings | [api](../v0.2/Reference/configuration/api.md) |
| `api.cors.methods` | list of strings | [api](../v0.2/Reference/configuration/api.md) |
| `api.cors.headers` | list of strings | [api](../v0.2/Reference/configuration/api.md) |
| `api.cors.credentials` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.securityHeaders` | boolean | [api](../v0.2/Reference/configuration/api.md) |
| `api.files` | object | [File fields](file-fields.md#limits-and-precedence) |
| `api.files.maxSize` | integer or size string | [File fields](file-fields.md#limits-and-precedence) |
| `api.files.types` | list of MIME types | [File fields](file-fields.md#limits-and-precedence) |
| `api.files.maxFiles` | integer | [File fields](file-fields.md#limits-and-precedence) |

### Imports

| Key | Type | Reference |
| --- | --- | --- |
| `imports` | map | [Vendored imports](vendored-imports.md) |
| `imports.<name>.path` | string | [Vendored imports](vendored-imports.md) |
| `imports.<name>.package` | Python identifier | [Vendored imports](vendored-imports.md) |
| `imports.<name>.requires` | list of strings | [Vendored imports](vendored-imports.md#dependency-merging) |

### MongoDB

| Key | Type | Reference |
| --- | --- | --- |
| `mongo` | object | [mongo](../v0.2/Reference/configuration/mongo.md) |
| `mongo.uri` | string | [mongo](../v0.2/Reference/configuration/mongo.md) |
| `mongo.database` | string | [mongo](../v0.2/Reference/configuration/mongo.md) |

### Datastores

| Key | Type | Reference |
| --- | --- | --- |
| `datastores` | map | [datastores](../v0.2/Reference/configuration/datastores.md) |
| `datastores.<name>.type` | `mongodb` \| `mongo` \| `postgres` \| `postgresql` \| `filesystem` \| `s3` | [datastores](../v0.2/Reference/configuration/datastores.md), [File datastores](file-datastores.md) |
| `datastores.<name>.default` | boolean | [datastores](../v0.2/Reference/configuration/datastores.md) |
| `datastores.<name>.uri` | string | [datastores](../v0.2/Reference/configuration/datastores.md) |
| `datastores.<name>.database` | string | [datastores](../v0.2/Reference/configuration/datastores.md) |
| `datastores.<name>.dsn` | string | [datastores](../v0.2/Reference/configuration/datastores.md) |
| `datastores.<name>.path` | string | [File datastores](file-datastores.md#type-filesystem) |
| `datastores.<name>.bucket` | string | [File datastores](file-datastores.md#type-s3) |
| `datastores.<name>.endpoint` | string | [File datastores](file-datastores.md#type-s3) |
| `datastores.<name>.region` | string | [File datastores](file-datastores.md#type-s3) |
| `datastores.<name>.accessKey` | string | [File datastores](file-datastores.md#type-s3) |
| `datastores.<name>.secretKey` | string | [File datastores](file-datastores.md#type-s3) |
| `datastores.<name>.prefix` | string | [File datastores](file-datastores.md#type-s3) |
| `datastores.<name>.files` | object, file datastores only | [File fields](file-fields.md#limits-and-precedence) |
| `datastores.<name>.files.maxSize` | integer or size string | [File fields](file-fields.md#limits-and-precedence) |
| `datastores.<name>.files.types` | list of MIME types | [File fields](file-fields.md#limits-and-precedence) |

### Entities

| Key | Type | Reference |
| --- | --- | --- |
| `entities` | map | [entities](../v0.2/Reference/entities/overview.md) |
| `entities.<name>.type` | `base` \| `auth` | [entities](../v0.2/Reference/entities/overview.md) |
| `entities.<name>.extends` | string | [inheritance](../v0.2/Reference/entities/inheritance.md) |
| `entities.<name>.abstract` | boolean | [inheritance](../v0.2/Reference/entities/inheritance.md) |
| `entities.<name>.pk` | string | [primary keys](../v0.2/Reference/entities/primary-keys.md) |
| `entities.<name>.fields` | map of [fields](#field-keys) | [field types](../v0.2/Reference/entities/field-types.md) |
| `entities.<name>.auth` | object, `type: auth` only | [auth](../v0.2/Reference/auth/overview.md) |
| `entities.<name>.auth.identifier` | string | [auth](../v0.2/Reference/auth/overview.md) |
| `entities.<name>.auth.roles` | string | [auth](../v0.2/Reference/auth/overview.md) |
| `entities.<name>.auth.via` | string, list of strings, or list of objects | [login and SSO](../v0.2/Reference/auth/login-and-sso.md) |
| `entities.<name>.auth.via[].provider` | string | [login and SSO](../v0.2/Reference/auth/login-and-sso.md) |
| `entities.<name>.auth.via[].identifier` | string | [login and SSO](../v0.2/Reference/auth/login-and-sso.md) |
| `entities.<name>.auth.via[].claim_mapping` | map of strings | [claim mapping](../v0.2/Reference/auth/claim-mapping.md) |
| `entities.<name>.auth.via[].auto_provision` | boolean | [login and SSO](../v0.2/Reference/auth/login-and-sso.md) |
| `entities.<name>.auth.via[].relations` | map | [claim mapping](../v0.2/Reference/auth/claim-mapping.md) |
| `entities.<name>.auth.via[].relations.<name>.collection` | string | [claim mapping](../v0.2/Reference/auth/claim-mapping.md) |
| `entities.<name>.auth.via[].relations.<name>.match` | map of strings | [claim mapping](../v0.2/Reference/auth/claim-mapping.md) |
| `entities.<name>.roles` | object, `type: auth` only | [roles](../v0.2/Reference/roles/overview.md) |
| `entities.<name>.roles.values` | list of strings | [roles](../v0.2/Reference/roles/overview.md) |
| `entities.<name>.roles.default` | string | [roles](../v0.2/Reference/roles/overview.md) |
| `entities.<name>.roles.hierarchy` | map of role lists | [role hierarchy](../v0.2/Reference/roles/hierarchy.md) |

### Field keys

An entity field (`entities.<name>.fields.<name>`), a DTO field
(`dto.<name>.fields.<name>`), a service input field
(`services.<name>.input.<name>`) and a nested field (`items`, or
`properties.<name>`) each take `type` and the keys of that type. `items` takes
no `required`, `readonly` or `default`.

| Key | Accepted on | Type | Reference |
| --- | --- | --- | --- |
| `type` | every field | `string` \| `number` \| `boolean` \| `datetime` \| `enum` \| `array` \| `object` \| `ref` \| `id` \| `file` | [field types](../v0.2/Reference/entities/field-types.md), [File fields](file-fields.md) |
| `required` | every field except `items` | boolean | [field types](../v0.2/Reference/entities/field-types.md) |
| `readonly` | every field except `items` | boolean | [field types](../v0.2/Reference/entities/field-types.md) |
| `default` | every field except `items`, every type except `file` | a value of the field's type | [field types](../v0.2/Reference/entities/field-types.md) |
| `unique` | top-level entity fields, every type except `file` | boolean | [field types](../v0.2/Reference/entities/field-types.md) |
| `minLength` | `string` | integer | [field types](../v0.2/Reference/entities/field-types.md) |
| `maxLength` | `string` | integer | [field types](../v0.2/Reference/entities/field-types.md) |
| `format` | `string` | `email` \| `e164` \| `uri` \| `uuidv7` \| `uuidv4` | [field types](../v0.2/Reference/entities/field-types.md) |
| `format` | `id` | `uuidv7` \| `uuidv4` | [primary keys](../v0.2/Reference/entities/primary-keys.md) |
| `min` | `number` | number | [field types](../v0.2/Reference/entities/field-types.md) |
| `max` | `number` | number | [field types](../v0.2/Reference/entities/field-types.md) |
| `values` | `enum`, required | list of strings | [field types](../v0.2/Reference/entities/field-types.md) |
| `items` | `array`, required | nested field | [field types](../v0.2/Reference/entities/field-types.md) |
| `maxItems` | `array` of `file` items | integer | [File fields](file-fields.md#arrays-of-files) |
| `properties` | `object` | map of nested fields | [field types](../v0.2/Reference/entities/field-types.md) |
| `additionalProperties` | `object` | boolean | [field types](../v0.2/Reference/entities/field-types.md) |
| `ref` | `ref`, required | entity name | [field types](../v0.2/Reference/entities/field-types.md) |
| `maxSize` | `file` | integer or size string | [File fields](file-fields.md#options) |
| `types` | `file` | list of MIME types | [File fields](file-fields.md#options) |
| `disposition` | `file` | `attachment` \| `inline` | [File fields](file-fields.md#disposition) |

`type: id` is accepted on a top-level entity field only. A `file` field, or an
array of `file` items, is accepted on a top-level entity field only; see
[where file fields are allowed](file-fields.md#where-file-fields-are-allowed).

### Repositories

| Key | Type | Reference |
| --- | --- | --- |
| `repositories` | map | [repositories](../v0.2/Reference/repositories/overview.md) |
| `repositories.<name>.entity` | string | [repositories](../v0.2/Reference/repositories/overview.md) |
| `repositories.<name>.datastore` | string | [repositories](../v0.2/Reference/repositories/overview.md) |
| `repositories.<name>.files` | string | [File datastores](file-datastores.md#binding-a-repository) |
| `repositories.<name>.abstract` | boolean | [repositories](../v0.2/Reference/repositories/overview.md) |
| `repositories.<name>.extends` | string | [repositories](../v0.2/Reference/repositories/overview.md) |
| `repositories.<name>.crud` | list of `list` \| `get` \| `create` \| `update` \| `replace` \| `delete` | [composable CRUD](../v0.2/Reference/repositories/composable-crud.md) |
| `repositories.<name>.softDelete` | string | [lifecycle](../v0.2/Reference/repositories/lifecycle.md) |
| `repositories.<name>.ttl` | object | [lifecycle](../v0.2/Reference/repositories/lifecycle.md) |
| `repositories.<name>.ttl.field` | string | [lifecycle](../v0.2/Reference/repositories/lifecycle.md) |
| `repositories.<name>.ttl.seconds` | integer | [lifecycle](../v0.2/Reference/repositories/lifecycle.md) |
| `repositories.<name>.operations` | map | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.handler` | string | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.includeDeleted` | boolean, with `query` only | [lifecycle](../v0.2/Reference/repositories/lifecycle.md#includedeleted) |
| `repositories.<name>.operations.<name>.query` | object | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.command` | string | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.collection` | string | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.key` | string | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.sql` | string | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.params` | map | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.filter` | any | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.pipeline` | any | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.document` | any | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.documents` | any | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.update` | any | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.replacement` | any | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |
| `repositories.<name>.operations.<name>.query.requests` | any | [operations](../v0.2/Reference/repositories/operations.md#custom-operations) |

### Services

| Key | Type | Reference |
| --- | --- | --- |
| `services` | map | [services](../v0.2/Reference/services/overview.md) |
| `services.<name>.repository` | string | [services](../v0.2/Reference/services/overview.md) |
| `services.<name>.operation` | string | [services](../v0.2/Reference/services/overview.md) |
| `services.<name>.handler` | string | [Service `input:`](service-input.md) |
| `services.<name>.abstract` | boolean | [services](../v0.2/Reference/services/overview.md#inheritance-with-abstract-and-extends) |
| `services.<name>.extends` | string | [services](../v0.2/Reference/services/overview.md#inheritance-with-abstract-and-extends) |
| `services.<name>.operations` | map of booleans or objects | [services](../v0.2/Reference/services/overview.md#per-operation-overrides) |
| `services.<name>.operations.<name>.handler` | string | [services](../v0.2/Reference/services/overview.md#per-operation-overrides) |
| `services.<name>.input` | map of [fields](#field-keys) or type names, or list of DTO names | [Service `input:`](service-input.md) |
| `services.<name>.with` | map of `$` references or scalars | [Service `input:`](service-input.md#forwarding-values) |

### Controllers

`<access>` stands for `controllers.<name>`, `controllers.<name>.operations.<name>`
or `controllers.<name>.routes.<name>`, and `<pagination>` for
`controllers.<name>.operations.<name>` or `controllers.<name>.routes.<name>`.

| Key | Type | Reference |
| --- | --- | --- |
| `controllers` | map | [controllers](../v0.2/Reference/controllers/overview.md) |
| `controllers.<name>.service` | string | [controllers](../v0.2/Reference/controllers/overview.md) |
| `controllers.<name>.base_path` | string | [controllers](../v0.2/Reference/controllers/overview.md) |
| `controllers.<name>.operations` | map of booleans or objects | [operations](../v0.2/Reference/controllers/operations.md) |
| `controllers.<name>.operations.<name>.method` | `GET` \| `POST` \| `PUT` \| `PATCH` \| `DELETE` | [operations](../v0.2/Reference/controllers/operations.md) |
| `controllers.<name>.operations.<name>.path` | string | [operations](../v0.2/Reference/controllers/operations.md) |
| `controllers.<name>.routes` | map | [controllers](../v0.2/Reference/controllers/overview.md) |
| `controllers.<name>.routes.<name>.service` | string, without controller `service` only | [controllers](../v0.2/Reference/controllers/overview.md) |
| `controllers.<name>.routes.<name>.method` | `GET` \| `POST` \| `PUT` \| `PATCH` \| `DELETE`, without controller `service` only | [controllers](../v0.2/Reference/controllers/overview.md) |
| `controllers.<name>.routes.<name>.path` | string, without controller `service` only | [controllers](../v0.2/Reference/controllers/overview.md) |
| `<access>.access` | [access value](#access-values) | [Access values](#access-values) |
| `<access>.access[].given` | map of [bindings](#given-bindings) | [`given:` bindings](#given-bindings) |
| `<access>.access[].when` | string or list of strings | [When expressions](../v0.2/Reference/when-expressions/overview.md) |
| `<access>.access[].then` | `allow` \| `deny` | [Access-rule objects](#access-rule-objects) |
| `<access>.access[].reason` | string | [Explainable access denials](access-reason.md) |
| `<access>.access[].bind` | map of `$` references or scalars | [Access-rule `bind:`](controller-bind.md) |
| `<pagination>.pagination` | object, list routes only | [Pagination](pagination.md) |
| `<pagination>.pagination.strategy` | `offset` \| `keyset` | [Pagination](pagination.md#strategies) |
| `<pagination>.pagination.size` | object | [Pagination](pagination.md) |
| `<pagination>.pagination.size.default` | integer | [Pagination](pagination.md) |
| `<pagination>.pagination.size.max` | integer | [Pagination](pagination.md) |
| `<pagination>.pagination.count` | `none` \| `exact` | [Pagination](pagination.md#envelopes) |
| `<pagination>.pagination.onOverflow` | `clamp` \| `reject` | [Pagination](pagination.md) |
| `<pagination>.pagination.envelope` | boolean | [Pagination](pagination.md#envelopes) |
| `<pagination>.pagination.sort` | list of objects | [Pagination](pagination.md) |
| `<pagination>.pagination.sort[].field` | string | [Pagination](pagination.md) |
| `<pagination>.pagination.sort[].dir` | `asc` \| `desc` | [Pagination](pagination.md) |

### Providers

| Key | Type | Reference |
| --- | --- | --- |
| `providers` | map | [providers](../v0.2/Reference/providers/overview.md) |
| `providers.<name>.type` | `oidc` \| `saml` | [providers](../v0.2/Reference/providers/overview.md) |
| `providers.<name>.trust` | `app` \| `idp`, OIDC only | [Dual-trust token dispatch](trust-dispatch.md) |
| `providers.<name>.client_id` | string, OIDC only | [OIDC](../v0.2/Reference/providers/oidc.md) |
| `providers.<name>.discovery_url` | string, OIDC only | [OIDC](../v0.2/Reference/providers/oidc.md) |
| `providers.<name>.client_secret` | string, OIDC `trust: app` only | [OIDC](../v0.2/Reference/providers/oidc.md) |
| `providers.<name>.pkce` | boolean, OIDC `trust: app` only | [PKCE](pkce.md) |
| `providers.<name>.dpop` | boolean, OIDC `trust: app` only | [DPoP](dpop.md) |
| `providers.<name>.issuer` | string, OIDC `trust: idp` only | [IdP token verification](verify-idp.md) |
| `providers.<name>.audiences` | list of strings, OIDC `trust: idp` only | [IdP token verification](verify-idp.md) |
| `providers.<name>.idp_metadata_url` | string, SAML only | [SAML](../v0.2/Reference/providers/saml.md) |
| `providers.<name>.sp_entity_id` | string, SAML only | [SAML](../v0.2/Reference/providers/saml.md) |

### Session

| Key | Type | Reference |
| --- | --- | --- |
| `session` | object | [session](../v0.2/Reference/configuration/session.md) |
| `session.algorithm` | `HS256` \| `RS256` | [RS256 session tokens](rs256-signing.md) |
| `session.ttl` | integer | [session](../v0.2/Reference/configuration/session.md) |
| `session.refresh` | boolean | [Refresh-token rotation](refresh-tokens.md) |
| `session.delivery` | `token-url` \| `cookie` | [Cookie (BFF) session delivery](cookie-bff.md) |

### DTOs

| Key | Type | Reference |
| --- | --- | --- |
| `dto` | map | [DTOs](../v0.2/Reference/dto/overview.md) |
| `dto.<name>.fields` | map of [fields](#field-keys) | [DTOs](../v0.2/Reference/dto/overview.md) |

### Policies

| Key | Type | Reference |
| --- | --- | --- |
| `policies` | map | [policies](../v0.2/Reference/policies/overview.md) |
| `policies.<name>.given` | map of strings | [policies](../v0.2/Reference/policies/overview.md) |
| `policies.<name>.params` | list of strings | [policies](../v0.2/Reference/policies/overview.md) |
| `policies.<name>.when` | string or list of strings | [policies](../v0.2/Reference/policies/overview.md) |

### UI

| Key | Type | Reference |
| --- | --- | --- |
| `ui` | object | [UI](../v0.2/Reference/ui/overview.md) |
| `ui.frontend` | object | [frontend](../v0.2/Reference/ui/frontend.md) |
| `ui.frontend.pack` | string | [frontend](../v0.2/Reference/ui/frontend.md) |
| `ui.frontend.output` | string | [frontend](../v0.2/Reference/ui/frontend.md) |
| `ui.frontend.overwrite` | `never` \| `always` | [frontend](../v0.2/Reference/ui/frontend.md) |
| `ui.config` | map | [UI](../v0.2/Reference/ui/overview.md) |
| `ui.collections` | map | [collections](../v0.2/Reference/ui/collections.md) |
| `ui.collections.<name>.fields` | map | [collections](../v0.2/Reference/ui/collections.md) |
| `ui.collections.<name>.fields.<name>.from` | string | [collections](../v0.2/Reference/ui/collections.md) |
| `ui.collections.<name>.fields.<name>.format` | string | [collections](../v0.2/Reference/ui/collections.md) |
| `ui.components` | map | [components](../v0.2/Reference/ui/components.md) |
| `ui.components.<name>.props` | map | [components](../v0.2/Reference/ui/components.md) |
| `ui.components.<name>.props.<name>.required` | boolean | [components](../v0.2/Reference/ui/components.md) |
| `ui.components.<name>.render` | object | [components](../v0.2/Reference/ui/components.md) |
| `ui.components.<name>.render.component` | string | [components](../v0.2/Reference/ui/components.md) |
| `ui.components.<name>.render.props` | map | [components](../v0.2/Reference/ui/components.md) |
| `ui.views` | map | [views](../v0.2/Reference/ui/views.md) |
| `ui.views.<name>.path` | string | [views](../v0.2/Reference/ui/views.md) |
| `ui.views.<name>.component` | string | [views](../v0.2/Reference/ui/views.md) |
| `ui.views.<name>.props` | map | [views](../v0.2/Reference/ui/views.md) |

### Deploy

| Key | Type | Reference |
| --- | --- | --- |
| `deploy` | object | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.name` | string | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.port` | integer | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.runtime` | `docker` \| `systemd` | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services` | map | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.image` | string | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.build` | string or object | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.build.context` | string | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.build.dockerfile` | string | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.build.args` | map | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.ports` | list of integers or strings | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.environment` | map or list of strings | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.volumes` | list of strings | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.depends_on` | list of strings or map | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.depends_on.<name>.condition` | `service_started` \| `service_healthy` \| `service_completed_successfully` | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.services.<name>.command` | string or list of strings | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.include` | list of strings | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.mongo` | object | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.mongo.local` | boolean | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.docker` | object | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.docker.image` | string | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.systemd` | object | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.systemd.user` | string | [deploy](../v0.2/Reference/configuration/deploy.md) |
| `deploy.systemd.restart` | string | [deploy](../v0.2/Reference/configuration/deploy.md) |

## Access values

`access:` may be declared on a controller as the default for its routes or on an
individual route as a complete override.

```text
RoleRule ::= Entity ":" "*"
           | Entity ":" Role
           | Role
Access   ::= "public"
           | "*"
           | RoleRule
           | [ RoleRule | AccessRule, ... ]
```

| Value | Authentication and authorization |
| --- | --- |
| `public` | No principal is required. |
| `"*"` | Any authenticated principal. Quote it so YAML does not treat `*` as an alias. |
| `<entity>:*` | Any principal from the named `type: auth` entity. |
| `<entity>:<role>` | A principal from that auth entity holding the role. |
| `<role>` | The role on the only auth entity; rejected as ambiguous when multiple auth entities exist. |

A principal holds its own roles and every role they inherit through
`entities.<entity>.roles.hierarchy`, so with `editor: [viewer]` an editor passes
a `viewer` rule. A missing `access:` is
treated as public and emits the `PUBLIC_ROUTE` build warning. An explicit
`access: public` also emits a warning so accidental exposure is visible during
generation.

`authenticated` is not the any-authenticated spelling; use `"*"`.
Use `public` and `"*"` as complete access values, not as entries mixed into an
ordered rule list.

## Access-rule objects

An access list may contain rule objects:

```yaml
access:
  - given:
      principal: identity:user
      record: posts
    when: principal.sub equals record.ownerId
    then: allow
```

```text
AccessRule ::= {
  given?: GivenBindings,
  when?: WhenExpression | [WhenExpression, ...],
  then?: "allow" | "deny",
  reason?: String,
  bind?: SymbolBinding
}
```

At least one of `given`, `when`, or `then` is required, and any other key is
rejected with `SCHEMA_VALIDATION_ERROR`. `then` defaults to `allow`. Rules are
evaluated in order; the first matching rule decides the request. A matching deny
returns 403. When no rule matches, an anonymous caller gets 401 and a signed-in
one gets 403. A non-public route answers 401 to a request whose token or
password does not authenticate.

To require a role together with a condition, keep the role in an `enum` field
of the identity record named by `entities.<entity>.auth.roles` and test it in
`when:`, for example `principal.record.role in ['editor', 'admin']`.

`reason:` supplies the safe 403 detail; see
[Explainable access denials](access-reason.md). To fix the value of
a field a client must not choose, declare it `readonly: true` and supply it
through [`bind:`](#access-rule-bind).

### Row filtering on list routes

On a `list` route, a rule whose `when:` reads the bound collection becomes a row
filter: the datastore query returns only the rows the rule admits.

```yaml
operations:
  list:
    access:
      - admin
      - given:
          principal: identity:user
          document: sensitive_data
        when: principal.sub equals document.owner_id
```

An admin lists every row; any other signed-in user lists only their own.

### Document bindings on custom routes

On a route that runs a custom repository operation or a handler, a bare
document binding loads the record named by the last path parameter, within the
scope of the other path parameters that name fields of its collection. The rule
decides on that record before the operation runs; the operation's result is not
row-filtered. A route whose path has no parameter cannot bind its record and is
reported as `DOCUMENT_BINDING_INVALID`; bind a record by another parameter with
`<collection> by <param>`.

## `given:` bindings

`given:` maps author-chosen symbol names to sources. `principal`, `document`,
and `request` are conventions, not built-in variable names.
`public` and `authenticated` are not bindings: declare public access with
`access: public` and any-authenticated access with `access: "*"`.

```text
GivenBindings   ::= { Name: GivenBinding, ... }
GivenBinding    ::= IdentityBinding
                  | DocumentBinding
                  | RequestBinding
                  | WhereBinding
IdentityBinding ::= "identity:" Entity
DocumentBinding ::= Collection [ " by " PathParameter ]
RequestBinding  ::= "request" [ "." RequestPart ] [ ":" Type ]
RequestPart     ::= "body" | "path" | "query" | "header" | "cookie"
```

| Form | Example | Bound value |
| --- | --- | --- |
| `identity:<entity>` | `principal: identity:user` | Authenticated principal, including `sub`, roles, identity collection, and stored record. |
| `<collection>` | `record: posts` | The route record from that collection. |
| `<collection> by <param>` | `owner: users by ownerId` | A record loaded by the named route parameter instead of the operation token. |
| `request` | `req: request` | Whole request; body remains raw. |
| `request:<type>` | `req: request:CreatePost` | Whole request with its body validated against a primitive, entity, or DTO. |
| `request.<part>` | `query: request.query` | One raw request part. |
| `request.<part>:<type>` | `body: request.body:CreatePost` | A typed body, path, or query part. |
| `<collection> where ...` | `owner: users where email = $req.body.email` | One record selected by an equality predicate. |

A type suffix is valid only for the whole request (where it types the body) or
for `body`, `path`, and `query`. Headers and cookies are not typeable. A body
binding is rejected on `get`, `list`, and `delete` because those operations do
not carry a body. Authentication runs before the body is read, so an anonymous
caller gets 401 whatever the body holds.

Every root used by `when:` must be a key in that same rule's `given:` map. Route
slugs are not ambient inside `when:`. Refer to
[When expressions](../v0.2/Reference/when-expressions/overview.md) for operand,
literal, and operator syntax.

## Route slugs and symbol scopes

A route declares a slug with braces and references its value with a `$` sigil:

```yaml
path: /organizations/{orgId}/posts/{postId}
```

Here `{orgId}` and `{postId}` declare the roots; `$orgId` and `$postId` reference
them. A `$` reference uses this shape:

```text
SymbolPath ::= "$" Name ( "." Name )*
Name       ::= ( letter | "_" ) ( letter | digit | "_" )*
```

There is no ambient `$principal`, `$request`, or `$document`. The available
roots depend on the reference site:

| Reference site | Ambient roots | Explicitly bound roots | Not available |
| --- | --- | --- | --- |
| `when:` operand | None | Every key in that rule's `given:` | Route slugs not also bound in `given:` |
| `where` right-hand side | Route slugs | Identity and request keys in the same rule's `given:` | Document and `where` result keys |
| Access-rule `bind:` value | Route slugs | Identity and request keys in the same rule's `given:` | Document and `where` result keys |
| Service `with:` value | None | Fields declared by that service's `input:` | Route, principal, request, and document roots |
| Repository operation query | Slugs on each route reaching the operation | Keys produced by the service's `with:` | Principal and request roots |

Repository-query validation is per route. If two routes reach one operation,
each route must independently supply every symbol used by that query.
`UNDEFINED_SYMBOL` aborts a v0.3 build whenever a root is absent from its site.
See [Symbol resolution](symbol-resolution.md) for examples.

## `where` bindings

A `where` binding selects one record before its access rule is evaluated:

```yaml
given:
  principal: identity:user
  category: assetCategories where slug = $categorySlug and active = true
```

```text
WhereBinding ::= Collection "where" Conjunct ( "and" Conjunct )*
Conjunct     ::= Field "=" Rhs
Rhs          ::= SymbolPath | String | Number | Boolean
Boolean      ::= "true" | "false"
```

`Collection` and `Field` are plain identifiers. A field is top-level and must
exist on the collection entity; dotted fields are rejected. Strings may use
single or double quotes and backslash escapes. Numbers accept an optional sign,
integers, decimals (including `.5` and `3.`), and exponents such as `1e3` or
`2.5E-2`. Keywords are lowercase and case-sensitive.

| Token | Status |
| --- | --- |
| `=` | Active comparison operator |
| `and` | Active conjunction |
| `!=`, `<`, `<=`, `>`, `>=`, `in` | Reserved and rejected with `WHERE_OPERATOR_UNSUPPORTED` |

Each rule receives its own fetched bindings, so equal symbol names in different
rules do not collide. A predicate miss makes only that rule fail; it never
returns 404. Evaluation continues, and the final result is the normal 401 or
403 if no rule allows the request. This prevents the route from revealing whether the
selected record exists. See [The `where` binding form](given-where.md) for the
complete parser and runtime contract.

## Service `input:` and `with:`

A service declares the request values it consumes and maps them into its
repository operation or handler:

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
    with:
      lookup: $postId
      state: archived
```

```text
InputConfig   ::= { Name: FieldType | FieldConfig, ... }
                | [ DtoName, ... ]
SymbolBinding ::= { Name: BindingValue, ... }
BindingValue  ::= SymbolPath | String | Number | Boolean
```

Both forms must be non-empty. A list in `input:` names DTOs whose fields are
merged; it is not a list of input field names. Inline inputs support `string`,
`number`, `boolean`, `datetime`, `enum`, `array`, `object`, and `ref`, including
their normal constraints. Inputs are required unless `required: false`.

Body fields and path parameters populate the input contract, with path values
taking precedence. `with:` right-hand symbols may reference only fields declared
by that service's `input:`. Its keys become the names available to a repository
query or handler. A repository forwarding key that its operation does not use is
rejected rather than silently discarded. See
[Service `input:` and `with:` forwarding](service-input.md).

## Access-rule `bind:`

An allow rule may supply trusted service inputs after it matches:

```yaml
access:
  - given:
      principal: identity:user
    bind:
      actorId: $principal.sub
```

`bind:` uses `SymbolBinding`. Each key must be declared in the route service's
`input:`. Route slugs and bind keys together must cover every required input.
The matching rule's values override client body and path values before input
validation, so the client cannot spoof them. Bindings on non-matching, deny, or
later rules are not applied.

A route using `bind:` cannot contain any document binding, including a `where`
binding, because service inputs are finalized before the document-authorization
lifecycle. Its expressions may use only route slugs and identity/request keys
from the same rule. See [Access-rule `bind:`](controller-bind.md).

## Single-record route locators

For v0.3 `get`, `update`, `replace`, and `delete` routes, the final route token
selects the record by the collection id field. Earlier tokens constrain fields
of the same name:

```text
/organizations/{orgId}/posts/{postId}
  -> posts where orgId = $orgId and id = $postId
```

Each earlier token must name a collection field. The full predicate is applied
atomically to reads and writes. See
[Freely-named single-record tokens](free-slug-fetch.md).

## Runtime results

| Status | Condition |
| --- | --- |
| 401 | A non-public route has no valid principal. |
| 403 | A signed-in caller meets an explicit deny, no allowing rule, or a `where` lookup miss. |
| 404 | An authorized single-record operation's route locator matches no target. |
| 409 | A datastore unique constraint rejects a write. |
| 422 | Request/service input validation fails, including a client value for a `readonly` field. |

The first matching rule decides access. Document-dependent rules run after the
route record is fetched; `where` bindings are isolated per rule. A v0.3 deny
reason and unique-conflict detail follow the security rules in
[Explainable access denials](access-reason.md) and
[Unique violations and `409 Conflict`](conflict-status.md).

## File endpoints

Derived [file endpoints](file-endpoints.md) declare no access of their own.
Download endpoints evaluate the access of the controller's `get` route, and
replace and delete endpoints evaluate the access of its `update` route, with
the same principal, `given:` bindings, `when:` rules and record locator. File
fields hold upload metadata, so they cannot be compared in `when:` or `where`.

## Coded diagnostics

### Access and `when:`

| Code | Condition |
| --- | --- |
| `ACCESS_UNKNOWN_ENTITY` | An identity or scoped-role form names an undeclared auth entity. |
| `ACCESS_NO_AUTH_ENTITY` | A bare role is used without any auth entity. |
| `ACCESS_AMBIGUOUS_ROLE` | A bare role is used with multiple auth entities. |
| `ACCESS_RULE_INVALID` | An access list/rule has an invalid shape or unsafe combination. |
| `WHEN_EXPR_INVALID` | A `when:` expression is empty or has trailing tokens. |
| `WHEN_OPERAND_MISSING` | An operator has no following operand. |
| `WHEN_OPERAND_INVALID` | An operand is not a field reference or supported literal. |
| `WHEN_LIST_INVALID` | An `in`/`not in` list is malformed. |
| `UNDEFINED_SYMBOL` | A `$` or `when:` root is absent from its exact v0.3 scope. |

`PUBLIC_ROUTE` is a warning, not a fatal error.

### `given:` and request bindings

| Code | Condition |
| --- | --- |
| `DOCUMENT_BINDING_INVALID` | A document binding is not `<collection>` or `<collection> by <param>`, names an unknown collection, or binds the record of a route that has none. |
| `REQUEST_BINDING_INVALID` | A request binding has an unknown part or includes a leaf in `given:`. |
| `REQUEST_TYPE_NOT_FOUND` | A request type is empty or not a primitive, entity, or DTO. |
| `REQUEST_TYPE_ON_LEAF` | A type is attached to a non-typeable request part. |
| `REQUEST_PATH_PARAM_NOT_DECLARED` | A request path field is not declared by the route template. |
| `REQUEST_BODY_ON_BODILESS_OP` | A body binding is used on `get`, `list`, or `delete`. |

### `where` and route locators

| Code | Condition |
| --- | --- |
| `WHERE_BINDING_INVALID` | The binding has invalid grammar, tokens, or a dotted field. |
| `WHERE_OPERATOR_UNSUPPORTED` | A reserved comparison operator is used. |
| `WHERE_RHS_INVALID` | A right-hand side is not a symbol, string, number, or boolean. |
| `WHERE_FIELD_UNKNOWN` | A predicate field is absent from the collection entity. |
| `ROUTE_LOCATOR_FIELD_UNKNOWN` | A parent route token is absent from the target collection entity. |
| `FILE_FIELD_NOT_COMPARABLE` | A `when:` operand or `where` predicate references a [file field](file-fields.md). |

### Service inputs, forwarding, and rule binding

| Code | Condition |
| --- | --- |
| `SERVICE_INPUT_INVALID` | `input:` is not a non-empty field map or DTO list. |
| `SERVICE_INPUT_FIELD_INVALID` | An inline input field type or `required` flag is invalid. |
| `SERVICE_INPUT_DTO_NOT_FOUND` | An `input:` list names an unknown DTO. |
| `SERVICE_WITH_VALUE_INVALID` | A `with:`/`bind:` value is not a `$` reference or scalar. |
| `SERVICE_WITH_TARGET_UNKNOWN` | A forwarding key is unused by its repository query. |
| `BIND_TARGET_UNKNOWN` | A bind key is not declared by the route service's input. |
| `BIND_MISSING_REQUIRED_INPUT` | Bind keys and route slugs do not cover a required input. |
| `BIND_DOCUMENT_RULE_UNSUPPORTED` | A bind-producing route also contains a document rule. |

## Version boundary

`where`, service `input:`/`with:`, access-rule `bind:`, unified
`UNDEFINED_SYMBOL`, token-derived record locators, pagination and file
endpoints are v0.3 only. A v0.2 spec binds identities, documents and requests,
fetches single records by `{id}`, and reports `WHEN_UNBOUND_SYMBOL` for an
unbound `when:` operand.
