---
title: "Operation and Role Gating"
description: The generated React app shows an action or route only when the server would serve that operation to the signed-in caller.
---

The generated React app never offers an action the server would refuse. Every
button (New, View, Edit, Delete) and every client-side route (`/new`, `/:id`,
`/:id/edit`) passes two gates:

1. **Operation gate**, at build time: the operation exists, because the backing
   repository's `crud` set exposes it. An absent operation emits no button and
   no route.
2. **Access gate**, at run time: the signed-in caller holds a role the
   operation's access rules admit, with the role hierarchy applied. A refused
   operation hides its button, and its route renders a "no access" page (or the
   login page for an anonymous caller).

## Example

```yaml
version: "0.2"

api:
  basePath: /api

entities:
  member:
    type: auth
    auth: { identifier: handle, via: password }
    roles:
      values: [owner, editor, viewer]
      default: viewer
      hierarchy:
        owner: [editor]
        editor: [viewer]
    fields:
      id: { type: id }
      handle: { type: string, required: true, unique: true }
  doc:
    fields:
      id: { type: id }
      title: { type: string, required: true }
  note:
    fields:
      id: { type: id }
      body: { type: string, required: true }

repositories:
  members: { entity: member }
  docs:
    entity: doc
    crud: [list, get, create, update, delete]
  notes:
    entity: note
    crud: [create, list, get, delete]   # no update -> no Edit anywhere

services:
  docs: { repository: docs }
  notes: { repository: notes }

controllers:
  docs:
    service: docs
    base_path: /docs
    access: member:viewer
    operations:
      create: { access: member:editor }
      update: { access: member:editor }
      delete: { access: member:owner }
  notes:
    service: notes
    base_path: /notes
    access: member:viewer

ui:
  frontend: { pack: generic, output: ./frontend }
  config: { app_name: Docs }
  views:
    docs:
      path: /docs
      component: crud
      props: { collection: doc }
    notes:
      path: /notes
      component: crud
      props: { collection: note }
```

With this spec:

| Caller | Docs | Notes |
|--------|------|-------|
| viewer | list, View | list, View, New, Delete |
| editor | list, View, New, Edit | list, View, New, Delete |
| owner  | list, View, New, Edit, Delete | list, View, New, Delete |

Notes never show Edit, because `update` is not in its repository's `crud` list.
An editor sees what a viewer sees because `editor` includes `viewer`; an owner
sees everything because `owner` includes `editor`.

## Operation gate

Each entity rendered in the UI carries the CRUD operations its repository
exposes, taken from the repository's `crud` list (default: all six of `list`,
`get`, `create`, `update`, `replace`, `delete`). An operation absent from `crud`
is absent from the repository, the service, the HTTP route and the UI.

| Operation | Surface | Affordance |
|-----------|---------|------------|
| `create`  | List page | "New" button (and the empty-state create button) |
| `get`     | List page | "View" link on each row |
| `update`  | Detail page | "Edit" button |
| `delete`  | Detail page | "Delete" button, from the view's `delete` component |

A `crud` view registers up to four routes, each only when its operation exists:

| Route | Renders | Needs |
|-------|---------|-------|
| `/docs`          | List page   | `list` |
| `/docs/new`      | Form (create) | `create` |
| `/docs/:id`      | Detail page | `get` |
| `/docs/:id/edit` | Form (edit) | `update` |

## Access gate

The app generates `src/__generated__/access.ts`, the same decision the server
makes, as data:

- `ACCESS[entity][operation][column]` is the verdict for each column of callers:
  `anonymous`, and one column per identity role (`member.owner`,
  `member.editor`, `member.viewer`), or one per identity entity without roles.
  A verdict is `allow`, `deny`, or `conditional` when the admitting rule has a
  `when` condition the server checks against the record.
- `ROLES[identity].includes` lists, per role, every role it includes, flattened
  from `entities.<e>.roles.hierarchy` (`owner: [editor, viewer]` above).
- `allows(entity, operation, caller)` is true when some column the caller
  occupies has a verdict other than `deny`. A caller occupies a role column when
  it holds that role or a role that includes it. A `conditional` verdict shows
  the action and leaves the record check to the server.
- `grants(caller, role)` is true for the roles the caller holds, directly or by
  inclusion. A role select disables every other option, since the server drops a
  role the caller cannot grant.

The caller comes from the session: password login and the code exchange that ends
an OIDC or SAML sign-in both answer the signed-in record and the roles it holds,
whether they are managed roles or a role field.

## Login gate

When the spec declares a `type: auth` entity, the app has a login page. With
`ui.config.require_auth: true`, every route shows the login page until a session
exists; it defaults to `false`, leaving pages open and gated by the access gate
alone:

```yaml
ui:
  config:
    require_auth: true
```

The generated app exposes a `useAuth()` hook (`token`, `user`, `caller`, `login`,
`logout`). External identity providers bound to the auth entity appear as sign-in
buttons on the login page, read from
`GET {basePath}[/{version}]/{collection}/auth/providers`. See
[Login, SSO, and the token flow](../auth/login-and-sso) for the backend side.

## See also

- [Composable per-operation CRUD](../repositories/composable-crud) - the
  repository `crud` list the operation gate mirrors.
- [Roles](../roles/overview) and [role hierarchy](../roles/hierarchy) - the
  rules the access gate mirrors.
- [UI Views](views) - how a `crud` view expands into pages and routes.
