"""An entity-level role hierarchy over real HTTP, in the dev server and the generated FastAPI app, for 0.2 and 0.3 specs."""

import itertools

import pytest

from tests.unit.support.live_apps import SERVERS, serve, write_spec

SPEC = """
version: "0.3"
api:
  basePath: /api
  operations:
    auth: { register: true }
{datastore}
entities:
  staff:
    type: auth
    auth: { identifier: email, via: password }
    roles: { values: [root, admin, moderator], default: admin, hierarchy: { admin: [moderator] } }
    fields:
      id: { type: id }
      email: { type: string, required: true, unique: true }
  note:
    fields:
      id: { type: id }
      title: { type: string }
repositories:
  staff: { entity: staff }
  notes: { entity: note }
services:
  staff: { repository: staff }
  notes: { repository: notes }
controllers:
  staff:
    service: staff
    base_path: /staff
    access: staff:root
    operations:
      register: { access: public }
  notes:
    service: notes
    base_path: /notes
    access: staff:moderator
    operations:
      delete: { access: staff:root }
"""

ADMIN = ("admin@x.io", "pw")


def versioned(version: str) -> str:
    return SPEC.replace('"0.3"', f'"{version}"', 1)


def register_admin(client) -> None:
    client.post("/api/staff/register", json={"email": ADMIN[0], "password": ADMIN[1]}).raise_for_status()


@pytest.fixture(
    scope="module",
    params=list(itertools.product(SERVERS, ("0.2", "0.3"))),
    ids=lambda param: f"{param[0].name}-{param[1]}",
)
def client(request, tmp_path_factory):
    server, version = request.param
    with serve(server, write_spec(tmp_path_factory.mktemp(f"{server.name}-{version}"), versioned(version))) as client:
        register_admin(client)
        yield client


def test_a_role_reaches_the_routes_of_the_roles_it_includes(client):
    created = client.post("/api/notes", json={"title": "t"}, auth=ADMIN)

    assert [created.status_code, client.get("/api/notes", auth=ADMIN).status_code] == [200, 200]


def test_a_role_does_not_reach_a_role_it_does_not_include(client):
    note = client.post("/api/notes", json={"title": "t"}, auth=ADMIN).json()

    assert client.delete(f"/api/notes/{note['id']}", auth=ADMIN).status_code == 403


def test_an_anonymous_caller_reaches_no_role_route(client):
    assert client.get("/api/notes").status_code == 401
