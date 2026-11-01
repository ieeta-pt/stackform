"""The generated UI offers an operation to a signed-in caller exactly when the server serves it, on MongoDB, for every backend."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from tests.unit.support.live_apps import MONGO_SERVERS, mongo, serve, write_spec
from yaml_api_generator.cli.compiler import compile_project

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("node") is None, reason="node runs the generated data layer"),
]

UI = """
ui:
  frontend: { pack: generic, output: ./frontend, overwrite: always }
"""

HIERARCHY = """
version: "0.3"
api:
  basePath: /api
  operations:
    defaults: { list: true, get: true, create: true, update: true, replace: false, delete: true }
    auth: { register: true, login: true }
{datastore}
entities:
  member:
    type: auth
    auth: { identifier: handle, via: password, roles: role }
    roles: { values: [owner, editor, viewer], default: owner, hierarchy: { owner: [editor], editor: [viewer] } }
    fields:
      id: { type: id }
      handle: { type: string, required: true, unique: true }
      role: { type: enum, values: [owner, editor, viewer], default: owner }
  doc:
    fields:
      id: { type: id }
      title: { type: string, required: true }
repositories:
  members: { entity: member }
  docs: { entity: doc }
services:
  members: { repository: members }
  docs: { repository: docs }
controllers:
  members:
    service: members
    base_path: /members
    access: member:owner
    operations:
      register: { access: public }
      login: { access: public }
  docs:
    service: docs
    base_path: /docs
    access: member:viewer
    operations:
      update: { access: member:editor }
      delete: { access: member:owner }
""" + UI

COLLECTION_ROLES = """
version: "0.1"
api:
  basePath: /api
{datastore}
collections:
  users:
    type: auth
    auth: { identifier: email, via: password }
    roles: { values: [admin, user], default: user, hierarchy: { admin: [user] } }
    access:
      create: public
    fields:
      id: { type: id }
      email: { type: string, required: true, unique: true }
  posts:
    access:
      list: users:user
      create: users:user
      update: users:user
      delete: users:admin
    fields:
      id: { type: id }
      title: { type: string, required: true }
""" + UI

DRIVER = """
import { callOperation, readJson } from './records.ts';
import { allows, callerOf } from './access.ts';

const nativeFetch = globalThis.fetch;
globalThis.fetch = (path, init) => nativeFetch(process.env.ORIGIN + path, init);

const { identity, entity, record, creator, accounts, operations } = JSON.parse(process.env.PLAN);
const json = { 'Content-Type': 'application/json' };
const send = (target, operation, { body, ...request }) =>
  callOperation(target, operation, { headers: json, body: body && JSON.stringify(body), ...request });

const signIn = async (credentials) => {
  const session = await send(identity, 'login', { body: credentials }).then(readJson);
  return { caller: callerOf(identity, session), headers: { ...json, Authorization: `Bearer ${session.token}` } };
};

const author = await signIn(creator);
const report = {};
for (const [name, credentials] of Object.entries(accounts)) {
  const { caller, headers } = await signIn(credentials);
  report[name] = {};
  for (const [operation, body] of Object.entries(operations)) {
    const { id } = await send(entity, 'create', { headers: author.headers, body: record }).then(readJson);
    const served = await send(entity, operation, { id, headers, body });
    report[name][operation] = [allows(entity, operation, caller), served.ok];
  }
}
console.log(JSON.stringify(report));
"""


def _frontend(directory: Path, spec: str, mongo_uri: str) -> Path:
    """The generated data layer of `spec`, with the driver beside it."""
    directory.mkdir()
    output = directory / "ui"
    compile_project(yaml_file=write_spec(directory, spec, mongo(mongo_uri, "ui")), output_dir=output, target="fastapi")
    generated = output / "frontend/src/__generated__"
    (generated / "drive.mjs").write_text(DRIVER)
    return generated


def _drive(generated: Path, origin: str, plan: dict) -> dict:
    result = subprocess.run(
        ["node", "--experimental-strip-types", "--no-warnings", "drive.mjs"],
        cwd=generated,
        env={**os.environ, "ORIGIN": origin, "PLAN": json.dumps(plan)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture(scope="module", params=MONGO_SERVERS, ids=lambda server: server.name)
def server(request):
    return request.param


def _served(server, directory: Path, spec: str, mongo_uri: str):
    directory.mkdir()
    return serve(server, write_spec(directory, spec, mongo(mongo_uri, f"{server.name}_{uuid4().hex}")))


def test_role_hierarchy_gates_the_ui_as_the_server_does(server, tmp_path, mongo_uri):
    generated = _frontend(tmp_path / "frontend", HIERARCHY, mongo_uri)
    owner = {"handle": "olga", "password": "pw-owner"}
    accounts = {"owner": owner, "editor": {"handle": "ed", "password": "pw-editor"}, "viewer": {"handle": "vi", "password": "pw-viewer"}}

    with _served(server, tmp_path / "server", HIERARCHY, mongo_uri) as client:
        client.post("/api/members/register", json=owner).raise_for_status()
        for role in ("editor", "viewer"):
            client.post("/api/members", json={**accounts[role], "role": role}, auth=tuple(owner.values())).raise_for_status()
        report = _drive(
            generated,
            str(client.base_url).rstrip("/"),
            {
                "identity": "member",
                "entity": "doc",
                "record": {"title": "draft"},
                "creator": owner,
                "accounts": accounts,
                "operations": {"list": None, "update": {"title": "edited"}, "delete": None},
            },
        )

    assert report == {
        "owner": {"list": [True, True], "update": [True, True], "delete": [True, True]},
        "editor": {"list": [True, True], "update": [True, True], "delete": [False, False]},
        "viewer": {"list": [True, True], "update": [False, False], "delete": [False, False]},
    }


def test_collection_roles_held_by_the_session_gate_the_ui(server, tmp_path, mongo_uri):
    generated = _frontend(tmp_path / "frontend", COLLECTION_ROLES, mongo_uri)
    user = {"email": "user@x.io", "password": "pw"}

    with _served(server, tmp_path / "server", COLLECTION_ROLES, mongo_uri) as client:
        client.post("/api/users", json=user).raise_for_status()
        report = _drive(
            generated,
            str(client.base_url).rstrip("/"),
            {
                "identity": "users",
                "entity": "posts",
                "record": {"title": "first"},
                "creator": user,
                "accounts": {"user": user},
                "operations": {"list": None, "update": {"title": "edited"}, "delete": None},
            },
        )

    assert report == {"user": {"list": [True, True], "update": [True, True], "delete": [False, False]}}
