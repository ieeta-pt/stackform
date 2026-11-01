"""A soft-deleting, expiring notes API and the HTTP behaviour every backend serving it must show."""

import sqlite3
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial
from uuid import uuid4

import httpx
import psycopg
from pymongo import MongoClient

from tests.integration.support.network import wait_until

_SPEC = """
version: "{version}"
api:
  basePath: /api
  operations:
    auth: {{ register: true, login: true }}
{storage}
entities:
  user:
    type: auth
    auth: {{ identifier: email, via: password }}
    fields:
      id: {{ type: id }}
      email: {{ type: string, required: true, unique: true }}
  note:
    fields:
      id: {{ type: id }}
      title: {{ type: string, required: true }}
      createdAt: {{ type: datetime }}
  draft:
    fields:
      id: {{ type: id }}
      title: {{ type: string, required: true }}
      retiredAt: {{ type: datetime }}
repositories:
  users: {{ entity: user, softDelete: deletedAt }}
  searchable:
    abstract: true
    operations:
{inherited}
  removable:
    abstract: true
    softDelete: deletedAt
    ttl: {{ field: createdAt, seconds: 3600 }}
    operations:
{inherited}
  notes:
    entity: note
{lifecycle}
    operations:
{operations}
  drafts: {{ entity: draft, softDelete: retiredAt }}
services:
  users: {{ repository: users }}
  drafts: {{ repository: drafts }}
  notes: {{ repository: notes }}
  everything: {{ repository: notes, operation: everything }}
  current: {{ repository: notes, operation: current }}
  joined: {{ repository: notes, operation: joined }}
  revive: {{ repository: notes, operation: revive }}
  wipe: {{ repository: notes, operation: wipe }}
  sweep: {{ repository: notes, operation: sweep }}
{services}
controllers:
  users:
    base_path: /users
    routes:
      register: {{ service: users, method: POST, path: "/register", access: public }}
      delete: {{ service: users, method: DELETE, path: "/{{id}}", access: public }}
  mine:
    base_path: /mine
    routes:
      list: {{ service: notes, method: GET, path: "", access: "*" }}
  notes:
    base_path: /notes
    routes:
      create:  {{ service: notes, method: POST, path: "", access: public }}
      list:    {{ service: notes, method: GET, path: "", access: public }}
      get:     {{ service: notes, method: GET, path: "/{{id}}", access: public }}
      update:  {{ service: notes, method: PATCH, path: "/{{id}}", access: public }}
      replace: {{ service: notes, method: PUT, path: "/{{id}}", access: public }}
      delete:  {{ service: notes, method: DELETE, path: "/{{id}}", access: public }}
  drafts:
    base_path: /drafts
    routes:
      create: {{ service: drafts, method: POST, path: "", access: public }}
      update: {{ service: drafts, method: PATCH, path: "/{{id}}", access: public }}
      delete: {{ service: drafts, method: DELETE, path: "/{{id}}", access: public }}
  guarded:
    base_path: /guarded
    routes:
      delete: {{ service: notes, method: DELETE, path: "/{{id}}", access: "*" }}
  archive:
    base_path: /archive
    routes:
      everything: {{ service: everything, method: GET, path: "", access: public }}
  queries:
    base_path: /queries
    routes:
      current: {{ service: current, method: GET, path: "/current", access: public }}
      joined: {{ service: joined, method: GET, path: "/joined", access: public }}
      revive: {{ service: revive, method: POST, path: "/revive", access: public }}
  purge:
    base_path: /purge
    routes:
      wipe: {{ service: wipe, method: DELETE, path: "/one/{{title}}", access: public }}
      sweep: {{ service: sweep, method: DELETE, path: "/all/{{title}}", access: public }}
{controllers}
"""

VERSIONS = ("0.2", "0.3")
"""The grammar versions declaring repository softDelete and ttl."""

LIFECYCLES = {
    "declared": "    extends: searchable\n    softDelete: deletedAt\n    ttl: { field: createdAt, seconds: 3600 }",
    "inherited": "    extends: removable",
}
"""The notes repository declaring its soft deletion and expiry, or inheriting them from an abstract repository.

Either way the `current` operation is inherited from an abstract repository."""

sql_spec = partial(
    _SPEC.format,
    lifecycle=LIFECYCLES["declared"],
    storage='datastores:\n  store: { type: postgres, dsn: "${SQL_DSN}", default: true }',
    inherited='      current: { query: { sql: "SELECT title FROM notes" } }',
    operations=(
        '      everything: { includeDeleted: true, query: { sql: "SELECT * FROM notes" } }\n'
        "      joined:\n"
        "        query:\n"
        "          sql: >-\n"
        "            SELECT d.title FROM notes n JOIN drafts d ON n.title = 'kept'\n"
        "            UNION ALL SELECT title FROM drafts WHERE title = 'retired'\n"
        "      revive:\n"
        "        includeDeleted: true\n"
        "        query: { sql: \"UPDATE notes SET title = 'revived' WHERE title = 'removed'\" }\n"
        '      wipe: { query: { sql: "DELETE FROM notes WHERE title = :title", params: { title: $title } } }\n'
        "      sweep:\n"
        "        query:\n"
        '          sql: "DELETE FROM notes WHERE title IN (SELECT title FROM notes WHERE title = :title)"\n'
        "          params: { title: $title }"
    ),
    services="",
    controllers="",
)

mongo_spec = partial(
    _SPEC.format,
    lifecycle=LIFECYCLES["declared"],
    storage="mongo:\n  uri: ${MONGO_URI:-mongodb://localhost:27017}\n  database: ${MONGO_DB:-notes}",
    inherited="      current: { query: { command: find, filter: {} } }",
    operations=(
        "      everything: { includeDeleted: true, query: { command: find, filter: {} } }\n"
        "      joined:\n"
        "        query:\n"
        "          command: aggregate\n"
        "          pipeline:\n"
        "            - $match: { title: kept }\n"
        "            - $lookup: { from: drafts, pipeline: [{ $project: { _id: 0, title: 1 } }], as: drafts }\n"
        "            - $unionWith: { coll: drafts, pipeline: [{ $match: { title: retired } }] }\n"
        "            - $project: { _id: 0, title: 1, drafts: 1 }\n"
        "      revive:\n"
        "        includeDeleted: true\n"
        "        query: { command: updateMany, filter: { title: removed }, update: { $set: { title: revived } } }\n"
        "      batch:\n"
        "        query:\n"
        "          command: bulkWrite\n"
        "          requests: [{ updateMany: { filter: { title: removed }, update: { $set: { title: batched } } } }]\n"
        "      tally: { query: { command: estimatedDocumentCount } }\n"
        '      wipe: { query: { command: deleteOne, filter: { title: "$title" } } }\n'
        '      sweep: { query: { command: deleteMany, filter: { title: "$title" } } }'
    ),
    services=(
        "  batch: { repository: notes, operation: batch }\n"
        "  tally: { repository: notes, operation: tally }"
    ),
    controllers=(
        "  bulk:\n"
        "    base_path: /bulk\n"
        "    routes:\n"
        '      batch: { service: batch, method: POST, path: "/batch", access: public }\n'
        '      tally: { service: tally, method: GET, path: "/tally", access: public }'
    ),
)

EXPIRED = "2000-01-01T00:00"
"""A creation time long past, as a datetime-local input submits it."""

_STORED = {"kept": False, "removed": True, "guarded": False}


class NotesTable(ABC):
    """The stored notes, read past the API."""

    @abstractmethod
    def rows(self) -> dict[str, bool]:
        """The title of every stored note and whether it carries its removal timestamp."""


@dataclass(frozen=True)
class SqliteNotes(NotesTable):
    path: str

    def rows(self):
        with sqlite3.connect(self.path) as connection:
            return {title: removed is not None for title, removed in connection.execute('SELECT title, "deletedAt" FROM notes')}


@dataclass(frozen=True)
class PostgresNotes(NotesTable):
    dsn: str

    def rows(self):
        with psycopg.connect(self.dsn) as connection:
            return {title: removed is not None for title, removed in connection.execute('SELECT title, "deletedAt" FROM notes')}


@dataclass(frozen=True)
class MongoNotes(NotesTable):
    uri: str
    database: str

    def rows(self):
        with MongoClient(self.uri) as client:
            return {row["title"]: row.get("deletedAt") is not None for row in client[self.database]["notes"].find()}


def _create(client: httpx.Client, title: str, created_at: str) -> str:
    response = client.post("/api/notes", json={"title": title, "createdAt": created_at})
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _recently() -> str:
    return (datetime.now(UTC) - timedelta(minutes=1)).isoformat()


def exercise(client: httpx.Client, notes: NotesTable) -> None:
    """Removed and expired notes vanish from every CRUD operation, only a permitted delete removes a note,
    and no request body writes a removal timestamp, declared by the entity or not."""
    ids = {title: _create(client, title, _recently()) for title in ("kept", "removed", "guarded")}
    ids["expired"] = _create(client, "expired", EXPIRED)
    removed, expired, kept = ids["removed"], ids["expired"], ids["kept"]

    assert client.delete(f"/api/guarded/{ids['guarded']}").status_code == 401
    assert client.delete(f"/api/notes/{removed}").status_code == 200
    assert notes.rows().items() >= _STORED.items()

    hiding = (
        client.get, client.delete,
        partial(client.patch, json={"title": "back"}),
        partial(client.put, json={"title": "back"}),
    )
    assert all(request(f"/api/notes/{note}").status_code == 404 for request in hiding for note in (removed, expired))

    stamped = datetime.now(UTC).isoformat()
    writes = (
        partial(client.post, "/api/notes", json={"title": "sneaky", "deletedAt": stamped}),
        partial(client.patch, f"/api/notes/{kept}", json={"deletedAt": stamped}),
        partial(client.patch, f"/api/notes/{kept}", json={"deletedAt": None}),
        partial(client.patch, f"/api/notes/{removed}", json={"deletedAt": None}),
        partial(client.put, f"/api/notes/{kept}", json={"title": "kept", "deletedAt": stamped}),
    )
    assert all(400 <= write().status_code < 500 for write in writes)
    assert notes.rows().items() >= _STORED.items()

    draft = client.post("/api/drafts", json={"title": "draft"})
    assert draft.status_code == 200, draft.text
    retirements = (
        partial(client.post, "/api/drafts", json={"title": "sneaky", "retiredAt": stamped}),
        partial(client.patch, f"/api/drafts/{draft.json()['id']}", json={"retiredAt": stamped}),
    )
    assert [retire().status_code for retire in retirements] == [422, 422]
    assert sorted(note["title"] for note in client.get("/api/notes").json()) == ["guarded", "kept"]


def _titles(response: httpx.Response) -> list[str]:
    assert response.status_code == 200, response.text
    return sorted(row["title"] for row in response.json())


def exercise_identity(client: httpx.Client) -> None:
    """A removed user can neither sign in nor use a token issued before, and its email can be registered again."""
    account = {"email": "gone@example.com", "password": "correct-horse-battery-staple"}
    registered = client.post("/api/users/register", json=account)
    assert registered.status_code in (200, 201), registered.text
    login = client.post("/api/users/login", json=account)
    assert login.status_code == 200, login.text
    bearer = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/api/mine", headers=bearer).status_code == 200
    assert client.delete(f"/api/users/{registered.json()['id']}").status_code == 200
    assert client.post("/api/users/login", json=account).status_code == 401
    assert client.get("/api/mine", headers=bearer).status_code == 401
    assert client.post("/api/users/register", json=account).status_code in (200, 201)


def _joined_drafts(rows: list[dict]) -> list[dict]:
    """The drafts a joined query returned: as rows of its own, or nested under the note they joined."""
    return [draft for row in rows for draft in row.get("drafts", [row])]


def exercise_queries(client: httpx.Client, notes: NotesTable) -> None:
    """Declared operations keep to the lifecycle of every table they touch, and includeDeleted widens reads only:
    an inherited query hides removed notes, a join hides retired drafts, a write cannot reach a removed note,
    and a declared delete stamps the removal timestamp in place of erasing."""
    exercise(client, notes)
    exercise_identity(client)
    assert {"kept", "removed"} <= set(_titles(client.get("/api/archive")))
    assert _titles(client.get("/api/queries/current")) == ["guarded", "kept"]

    drafts = {title: client.post("/api/drafts", json={"title": title}).json()["id"] for title in ("live", "retired")}
    assert client.delete(f"/api/drafts/{drafts['retired']}").status_code == 200
    joined = client.get("/api/queries/joined")
    assert joined.status_code == 200, joined.text
    assert sorted(draft["title"] for draft in _joined_drafts(joined.json())) == ["draft", "live"]

    assert client.post("/api/queries/revive").status_code == 200
    assert notes.rows().items() >= _STORED.items()

    for title in ("wiped", "swept"):
        _create(client, title, _recently())
    assert client.delete("/api/purge/one/wiped").status_code == 200
    assert client.delete("/api/purge/all/swept").status_code == 200
    rows = notes.rows()
    assert rows["wiped"] and rows["swept"], rows


def exercise_bulk(client: httpx.Client, notes: NotesTable) -> None:
    """A bulk write cannot reach a removed note, and an estimated count counts only the notes in view."""
    exercise_queries(client, notes)
    assert client.post("/api/bulk/batch").status_code == 200
    assert notes.rows().items() >= _STORED.items()
    tally = client.get("/api/bulk/tally")
    assert tally.status_code == 200, tally.text
    assert tally.json() == len(client.get("/api/notes").json())


Scenario = Callable[[httpx.Client, NotesTable], None]


def verify(
    serve: Callable[[], AbstractContextManager[httpx.Client]], notes: NotesTable, scenario: Scenario = exercise_queries
) -> None:
    """Runs `scenario` on one server, then checks that the next one erases the expired note and nothing else."""
    with serve() as client:
        scenario(client, notes)
    survivors = {title: removed for title, removed in notes.rows().items() if title != "expired"}
    with serve():
        assert wait_until(lambda: notes.rows() == survivors, timeout=15), notes.rows()


PROVISIONED = "provisioned@example.com"


async def reprovision(
    create: Callable[[dict], Awaitable[dict]],
    delete: Callable[[str], Awaitable[object]],
    upsert: Callable[[str, dict], Awaitable[dict]],
) -> list[str]:
    """Provisions the email of a removed user, as a sign-in through a provider does, and returns the two ids."""
    removed = await create({"id": str(uuid4()), "email": PROVISIONED})
    await delete(removed["id"])
    return [removed["id"], (await upsert("email", {"id": str(uuid4()), "email": PROVISIONED}))["id"]]
