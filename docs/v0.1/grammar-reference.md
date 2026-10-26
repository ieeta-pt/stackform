---
title: Grammar Reference
description: Every key a v0.1 spec accepts, with its type, in one tree.
---

This tree lists every key a v0.1 spec accepts. Every object is closed: a key
that does not appear here fails the build with `SCHEMA_VALIDATION_ERROR`
(`'<key>' was unexpected`). The [specification](./specification.md) describes
what each key does.

Notation:

- `!` = required
- `?` = optional
- `map<K,V>` = mapping from names to values
- `enum(...)` = one of the listed values
- `array<T>` = list of values
- `oneOf(...)` = one of the listed forms

```yaml
YAML-SPEC:
  version!: "0.1"

  api?:
    basePath?: string                         # default: /api
    version?: string
    pagination?:
      defaultPageSize?: integer >= 1          # default: the smaller of 20 and maxPageSize
      maxPageSize?: integer >= 1              # default: 100
    operations?:
      defaults?: OperationFlags

  mongo?:
    uri?: string                              # default: mongodb://localhost:27017
    database?: string                         # default: yaml_api

  security?:
    cors?:
      allowedOrigins?: array<string>          # no "*" when allowCredentials is true
      allowCredentials?: boolean              # default: false
      allowedMethods?: array<string>          # default: ["*"]
    headers?:
      enableStandard?: boolean                # default: true

  providers?: map<string, ProviderConfig>

  collections!: map<string, CollectionConfig>

  ui?: UiConfig                               # see the UI reference


OperationFlags:
  list?: boolean
  get?: boolean
  create?: boolean
  update?: boolean
  replace?: boolean
  delete?: boolean


ProviderConfig: oneOf(OIDCProvider, SAMLProvider)

OIDCProvider:
  type!: oidc
  client_id!: string
  client_secret!: string

SAMLProvider:
  type!: saml
  idp_metadata_url!: string
  sp_entity_id!: string


CollectionConfig:
  type?: enum(base, auth)                     # default: base
  fields!: map<string, FieldConfig>           # exactly one field of type id
  auth?: AuthConfig                           # required when type is auth
  roles?: RolesConfig                         # only when type is auth
  operations?: OperationFlags
  access?:
    list?: Access
    get?: Access
    create?: Access
    update?: Access
    replace?: Access                          # default: the update access
    delete?: Access
  softDelete?: boolean                        # default: false


AuthConfig:
  identifier!: string                         # a field of the collection
  via!: oneOf(string, array<string>)          # password, apiKey or a providers key


RolesConfig:
  values!: array<string>                      # at least one role
  default!: string                            # one of values
  hierarchy?: map<string, array<string>>      # role -> roles it includes


FieldConfig:                                  # a top-level collection field
  <the keys of its type, below>
  unique?: boolean

NestedFieldConfig:                            # an object property or array item
  <the keys of its type, below>

Keys of every type:
  type!: enum(string, number, boolean, datetime, enum, array, object, ref, id)
  required?: boolean
  default?: any                               # must satisfy the field's own keys

Keys added by type:
  string:
    minLength?: integer >= 0
    maxLength?: integer >= 0
    format?: enum(email, e164, uri, uuidv7, uuidv4)
  number:
    min?: number
    max?: number
  enum:
    values!: array<string>                    # at least one value
  array:
    items!: NestedFieldConfig
  object:
    properties?: map<string, NestedFieldConfig>
    additionalProperties?: boolean            # default: false with properties, true without
  ref:
    ref!: string                              # a declared collection
  id:
    format?: enum(uuidv7, uuidv4)             # default: uuidv7
  boolean, datetime: no further keys


Access: oneOf(Principal, array<AccessRule>)

Principal: oneOf(
  public,
  "*",
  <authCollection>:*,
  <authCollection>:<role>,
  <role>                                      # only with a single auth collection
)

AccessRule:
  principal!: Principal
  when?: string                               # when expression
  reason?: string                             # 403 detail when the rule refuses
```

The `ui` block has the same shape in every spec version; see the
[UI reference](../v0.2/Reference/ui/overview.md).
