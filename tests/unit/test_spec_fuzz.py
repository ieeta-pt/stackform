"""Random valid specs compile to FastAPI backends whose every declared route answers without a server error.

Set ``STACKFORM_FUZZ_EXAMPLES`` to run more examples than the quick default.
"""

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from tests.unit.support.generated_apps import run_generated, write_spec
from yaml_api_generator.constants import CRUD_OPERATIONS
from yaml_api_generator.parsers.yaml_parser import ConfigErrors, load_and_generate_ir

# Field type -> (definition, a value it accepts)
_SCALARS = {
    "string": ({"type": "string", "minLength": 1}, "text"),
    "number": ({"type": "number", "min": 0}, 1),
    "boolean": ({"type": "boolean"}, True),
    "datetime": ({"type": "datetime"}, "2026-01-01T00:00:00Z"),
    "enum": ({"type": "enum", "values": ["a", "b"]}, "a"),
}

_ROUTES = {
    "list": ("GET", ""),
    "get": ("GET", "/{id}"),
    "create": ("POST", ""),
    "update": ("PATCH", "/{id}"),
    "replace": ("PUT", "/{id}"),
    "delete": ("DELETE", "/{id}"),
}

_RECORD_OPERATIONS = frozenset(operation for operation, (_, path) in _ROUTES.items() if path)

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@dataclass(frozen=True)
class Collection:
    name: str
    plural: str
    fields: dict[str, tuple[str, bool]]
    files: tuple[str, ...]
    crud: tuple[str, ...]
    offered: tuple[str, ...]

    @property
    def entity(self) -> dict:
        scalars = {field: {**_SCALARS[kind][0], "required": required} for field, (kind, required) in self.fields.items()}
        uploads = {field: {"type": "file", "types": ["image/png"]} for field in self.files}
        return {"fields": {"id": {"type": "id"}, "ownerId": {"type": "string", "readonly": True}, **scalars, **uploads}}

    @property
    def repository(self) -> dict:
        return {"entity": self.name, "crud": list(self.crud)}

    @property
    def service(self) -> dict:
        return {"repository": self.plural, "operations": {operation: operation in self.offered for operation in self.crud}}

    @property
    def payload(self) -> dict:
        return {field: _SCALARS[kind][1] for field, (kind, _) in self.fields.items()}

    def owner_only(self) -> list[dict]:
        return [{
            "given": {"principal": "identity:member", self.name: self.plural},
            "when": f"principal.sub equals {self.name}.ownerId",
        }]


def _access(collection: Collection, operation: str):
    rules = [st.just("public"), st.just("*"), st.just([{"given": {"principal": "identity:member"}}])]
    owner_only = [st.just(collection.owner_only())] if operation in _RECORD_OPERATIONS else []
    return st.one_of(*rules, *owner_only)


def _subset(operations: tuple[str, ...]):
    return st.lists(st.booleans(), min_size=len(operations), max_size=len(operations)).map(
        lambda kept: tuple(operation for operation, keep in zip(operations, kept) if keep)
    )


@st.composite
def _collection(draw, name: str, plural: str) -> Collection:
    kinds = st.tuples(st.sampled_from(sorted(_SCALARS)), st.booleans())
    fields = draw(st.dictionaries(st.sampled_from(["title", "size", "flag", "due", "level"]), kinds, max_size=3))
    files = draw(st.sampled_from([(), ("cover",)]))
    crud = tuple(operation for operation in CRUD_OPERATIONS if operation in {"create", *draw(_subset(CRUD_OPERATIONS))})
    return Collection(name, plural, fields, files, crud, draw(_subset(crud)))


@st.composite
def _controller(draw, collection: Collection) -> dict:
    operations = draw(_subset(collection.offered))
    access = {operation: draw(_access(collection, operation)) for operation in operations}
    if draw(st.booleans()):
        return {
            "service": collection.plural,
            "base_path": f"/{collection.plural}",
            "operations": {
                operation: (operation in operations) and {"access": access[operation]}
                for operation in collection.offered
            },
        }
    return {
        "base_path": f"/{collection.plural}",
        "routes": {
            operation: {
                "service": collection.plural,
                "method": _ROUTES[operation][0],
                "path": _ROUTES[operation][1],
                "access": access[operation],
            }
            for operation in operations
        },
    }


def _seeding(collection: Collection) -> dict:
    return {
        "base_path": f"/seed/{collection.plural}",
        "routes": {
            "create": {
                "service": f"{collection.name}Seeding",
                "method": "POST",
                "path": "",
                "access": [{"given": {"principal": "identity:member"}, "bind": {"ownerId": "$principal.sub"}}],
            }
        },
    }


@st.composite
def specs(draw, directory: Path) -> tuple[dict, list[Collection]]:
    names = draw(st.lists(st.sampled_from([("book", "books"), ("loan", "loans"), ("shelf", "shelves")]), min_size=1, max_size=2, unique=True))
    collections = [draw(_collection(name, plural)) for name, plural in names]
    spec = {
        "version": "0.3",
        "api": {"basePath": "/api", "operations": {"auth": {"register": True, "login": True}}},
        "datastores": {
            "main": {"type": "postgres", "dsn": f"sqlite+aiosqlite:///{directory}/app.sqlite", "default": True},
            "disk": {"type": "filesystem", "path": str(directory / "uploads"), "default": True},
        },
        "entities": {
            "member": {
                "type": "auth",
                "auth": {"identifier": "email", "via": "password"},
                "fields": {"id": {"type": "id"}, "email": {"type": "string", "required": True, "unique": True, "format": "email"}},
            },
            **{collection.name: collection.entity for collection in collections},
        },
        "repositories": {
            "members": {"entity": "member"},
            **{collection.plural: collection.repository for collection in collections},
        },
        "services": {
            "members": {"repository": "members"},
            **{collection.plural: collection.service for collection in collections},
            **{
                f"{collection.name}Seeding": {"repository": collection.plural, "operation": "create", "input": {"ownerId": "string"}}
                for collection in collections
            },
        },
        "controllers": {
            "members": {"service": "members", "base_path": "/members", "access": "public", "operations": {"create": False}},
            **{f"{collection.name}Seeding": _seeding(collection) for collection in collections},
            **{collection.plural: draw(_controller(collection)) for collection in collections},
        },
    }
    return spec, collections


_PROBE = """
PLAN = json.loads({plan!r})
PNG = {png!r}

def credentials(email):
    client.post("/api/members/register", json={{"email": email, "password": "pw123456"}})
    login = client.post("/api/members/login", json={{"email": email, "password": "pw123456"}})
    return {{"Authorization": "Bearer " + login.json()["token"]}}

def body(collection, method):
    data = collection["payload"]
    if collection["files"] and method in ("POST", "PATCH"):
        uploads = [(field, (field + ".png", PNG, "image/png")) for field in collection["files"]]
        return {{"files": [("_data", (None, json.dumps(data), "application/json")), *uploads]}}
    return {{"json": data}} if method in ("POST", "PATCH", "PUT") else {{}}

def seed(collection, owner):
    created = client.post(f"/api/seed/{{collection['plural']}}", headers=owner, **body(collection, "POST"))
    assert created.status_code == 200, created.text
    return created.json()["id"]

with client:
    callers = {{"anonymous": {{}}, "owner": credentials("owner@example.com"), "stranger": credentials("stranger@example.com")}}
    failures = []
    for route in PLAN:
        collection = route["collection"]
        for caller, headers in callers.items():
            path = route["path"].replace("{{id}}", seed(collection, callers["owner"]))
            response = client.request(route["method"], path, headers=headers, **body(collection, route["method"]))
            if response.status_code >= 500:
                failures.append([route["method"], route["path"], caller, response.status_code, response.text[:200]])
    print(json.dumps(failures))
"""


def _plan(ir, collections: list[Collection]) -> str:
    by_plural = {collection.plural: collection for collection in collections}
    return json.dumps([
        {
            "method": route.method,
            "path": re.sub(r"\{\w+\}", "{id}", route.path),
            "collection": {"plural": route.collection, "payload": by_plural[route.collection].payload, "files": by_plural[route.collection].files},
        }
        for route in ir.routes
        if route.collection in by_plural and not route.path.startswith("/api/seed/")
    ])


@settings(
    max_examples=int(os.environ.get("STACKFORM_FUZZ_EXAMPLES", "8")),
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
@given(data=st.data())
def test_every_declared_route_answers_without_server_error(data):
    with tempfile.TemporaryDirectory() as scratch:
        directory = Path(scratch)
        spec, collections = data.draw(specs(directory))
        path = write_spec(directory, yaml.safe_dump(spec, sort_keys=False))
        try:
            ir = load_and_generate_ir(str(path)).ir
        except ConfigErrors:
            assume(False)
        failures = run_generated(path, "fastapi", _PROBE.format(plan=_plan(ir, collections), png=_PNG))
        assert failures == [], yaml.safe_dump(spec, sort_keys=False)
