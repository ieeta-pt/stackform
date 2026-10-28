"""`api.operations.auth.login` serves a password login route only when true, over real HTTP in the dev server and the generated FastAPI app."""

import itertools

import pytest

from tests.unit.support.live_apps import SERVERS, serve, write_spec

SPEC = """
version: "{version}"
api:
  basePath: /api
  operations:
    auth: {flags}
{{datastore}}
entities:
  user:
    type: auth
    auth: {{ identifier: email, via: password }}
    fields:
      id: {{ type: id }}
      email: {{ type: string, required: true, unique: true }}
repositories:
  users: {{ entity: user }}
services:
  users: {{ repository: users }}
controllers:
  users:
    service: users
    base_path: /users
    access: "*"
    operations:
      register: {{ access: public }}
"""

# auth flags -> whether login is served
FLAGS = {
    "{ register: true }": False,
    "{ register: true, login: false }": False,
    "{ register: true, login: true }": True,
}
VERSIONS = ("0.2", "0.3")
CASES = list(itertools.product(VERSIONS, FLAGS.items()))
USER = {"email": "login@x.io", "password": "pw"}


def case_id(case) -> str:
    version, (flags, _) = case
    return f"{version}-{flags}"


def login_status(client) -> int:
    assert client.post("/api/users/register", json=USER).status_code in (200, 201)
    return client.post("/api/users/login", json=USER).status_code


def expected_statuses(served: bool) -> set[int]:
    return {200} if served else {404, 405}


@pytest.mark.parametrize("server", SERVERS, ids=lambda server: server.name)
@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_login_route_follows_the_auth_flag(tmp_path, server, case):
    version, (flags, served) = case
    with serve(server, write_spec(tmp_path, SPEC.format(version=version, flags=flags))) as client:
        assert login_status(client) in expected_statuses(served)
