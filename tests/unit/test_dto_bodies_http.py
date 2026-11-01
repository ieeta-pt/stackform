"""Bodies typed by a DTO binding over real HTTP, in the dev server and the generated FastAPI app, on every route kind."""

import itertools
from contextlib import contextmanager

import pytest

from tests.unit.support.live_apps import SERVERS, serve, write_spec

_SPEC = """
version: "{version}"
api:
  basePath: /api
{datastore}
dto:
  noteInput:
    fields:
      title: { type: string, required: true, maxLength: 5 }
      extra: { type: string }
  lookup:
    fields:
      title: { type: string, required: true, maxLength: 5 }
      tag: { type: string, default: plain }
entities:
  note:
    fields:
      id: { type: id }
      title: { type: string, required: true }
repositories:
  notes:
    entity: note
    operations:
      named:
        query: {named}
services:
  notes: { repository: notes }
  echo: { handler: handlers.echo }
  named: { repository: notes, operation: named }
controllers:
  notes:
    base_path: /notes
    routes:
      create:
        service: notes
        method: POST
        path: ""
        access:
          - given: { req: "request:noteInput" }
            then: allow
      update:
        service: notes
        method: PATCH
        path: /{id}
        access:
          - given: { req: "request:noteInput" }
            then: allow
  echo:
    base_path: /echo
    routes:
      run:
        service: echo
        method: POST
        path: ""
        access:
          - given: { req: "request:lookup" }
            then: allow
  lookup:
    base_path: /lookup
    routes:
      run:
        service: named
        method: POST
        path: /{name}
        access:
          - given: { req: "request:lookup" }
            then: allow
"""

# The dev server hands a handler its request context; a generated backend hands it the request
_HANDLERS = '''
async def echo(target):
    if hasattr(target, "response"):
        target.response = target.body
        return target
    return target.body
'''

# The ``named`` repository operation, the notes titled by the ``name`` path parameter, in each datastore's query language
SQL_NAMED = '{ sql: "SELECT * FROM notes WHERE title = :name", params: { name: $name } }'
MONGO_NAMED = "{ command: find, filter: { title: $name } }"

VERSIONS = ("0.2", "0.3")


def case_id(case):
    server, version = case
    return f"{server.name}-{version}"


@contextmanager
def serving(server, version, directory, datastore=None, named=SQL_NAMED):
    """``server`` serving the spec at ``version`` with the ``named`` query, its handlers module beside it."""
    (directory / "handlers.py").write_text(_HANDLERS)
    spec = write_spec(directory, _SPEC.replace("{version}", version).replace("{named}", named), datastore)
    with serve(server, spec, env={"PYTHONPATH": str(directory)}) as client:
        yield client


@pytest.fixture(scope="module", params=list(itertools.product(SERVERS, VERSIONS)), ids=case_id)
def client(request, tmp_path_factory):
    server, version = request.param
    with serving(server, version, tmp_path_factory.mktemp(case_id(request.param))) as client:
        yield client


@pytest.fixture(scope="module")
def note(client):
    created = client.post("/api/notes", json={"title": "note"})
    assert created.status_code == 200, created.text
    return created.json()


@pytest.mark.parametrize("body", [
    {"extra": "x"},
    {"title": "note", "extra": "x"},
    {"title": "too long"},
    {"title": "note", "other": 1},
])
def test_create_body_must_satisfy_the_dto_and_the_entity(client, body):
    assert client.post("/api/notes", json=body).status_code == 422


def test_create_body_satisfying_both_is_stored(note):
    assert note["title"] == "note"


@pytest.mark.parametrize("body,status", [
    ({}, 200),
    ({"title": "edit"}, 200),
    ({"title": "too long"}, 422),
    ({"extra": "x"}, 422),
])
def test_update_body_is_any_subset_both_accept(client, note, body, status):
    assert client.patch(f"/api/notes/{note['id']}", json=body).status_code == status


def test_handler_receives_the_conformed_body(client):
    echoed = client.post("/api/echo", json={"title": "hi"})
    assert echoed.status_code == 200, echoed.text
    assert echoed.json() == {"title": "hi", "tag": "plain"}


@pytest.mark.parametrize("path", ["/api/echo", "/api/lookup/note"])
@pytest.mark.parametrize("body", [{}, {"title": "too long"}, {"title": "hi", "other": 1}])
def test_handler_and_custom_operation_reject_a_body_outside_the_dto(client, path, body):
    assert client.post(path, json=body).status_code == 422


def test_custom_operation_runs_with_a_body_the_dto_accepts(client):
    sought = client.post("/api/notes", json={"title": "find"}).json()
    found = client.post("/api/lookup/find", json={"title": "hi"})
    assert found.status_code == 200, found.text
    assert [row["id"] for row in found.json()] == [sought["id"]]


def test_openapi_documents_the_update_body_as_partial(client):
    document = client.get("/openapi.json").json()
    body = document["paths"]["/api/notes/{id}"]["patch"]["requestBody"]["content"]["application/json"]["schema"]
    schema = document["components"]["schemas"][body["$ref"].rsplit("/", 1)[-1]] if "$ref" in body else body
    assert set(schema["properties"]) == {"title", "extra"}
    assert not schema.get("required")
