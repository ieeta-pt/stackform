"""Routes that read a record before writing it work whichever CRUD operations the service exposes."""

from pathlib import Path

import pytest
import yaml

from tests.unit.support.generated_apps import run_generated, write_spec
from yaml_api_generator.parsers.yaml_parser import ConfigErrors, load_and_generate_ir

def _owner_only(name: str, plural: str) -> list[dict]:
    return [{"given": {"principal": "identity:member", name: plural}, "when": f"principal.sub equals {name}.ownerId"}]


def _creation(name: str, plural: str) -> dict:
    return {
        "base_path": f"/{plural}",
        "routes": {
            "create": {
                "service": f"{name}Creation",
                "method": "POST",
                "path": "",
                "access": [{"given": {"principal": "identity:member"}, "bind": {"ownerId": "$principal.sub"}}],
            }
        },
    }


def _explicit(operation: str, method: str):
    def controller(name: str, plural: str) -> dict:
        route = {"service": plural, "method": method, "path": "/{id}", "access": _owner_only(name, plural)}
        return {"base_path": f"/{plural}", "routes": {operation: route}}
    return controller


def _shorthand(name: str, plural: str) -> dict:
    guarded = {"access": _owner_only(name, plural)}
    return {
        "service": plural,
        "base_path": f"/{plural}",
        "operations": {"create": False, "update": guarded, "delete": guarded},
    }


# name -> (plural, service CRUD switches, controller)
_RESOURCES = {
    "note": ("notes", {}, _explicit("delete", "DELETE")),
    "draft": ("drafts", {}, _explicit("update", "PATCH")),
    "clip": ("clips", {"get": False, "list": False}, _shorthand),
}


def _spec(directory: Path) -> dict:
    owned = {"fields": {
        "id": {"type": "id"},
        "ownerId": {"type": "string", "readonly": True},
        "title": {"type": "string", "required": True},
        "cover": {"type": "file", "types": ["image/png"]},
    }}
    return {
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
            **{name: owned for name in _RESOURCES},
        },
        "repositories": {"members": {"entity": "member"}, **{plural: {"entity": name} for name, (plural, *_) in _RESOURCES.items()}},
        "services": {
            "members": {"repository": "members"},
            **{plural: {"repository": plural, "operations": switches} for plural, switches, _ in _RESOURCES.values()},
            **{f"{name}Creation": {"repository": plural, "operation": "create", "input": {"ownerId": "string"}} for name, (plural, *_) in _RESOURCES.items()},
        },
        "controllers": {
            "members": {"service": "members", "base_path": "/members", "access": "public", "operations": {"create": False}},
            **{f"{name}Creation": _creation(name, plural) for name, (plural, *_) in _RESOURCES.items()},
            **{plural: controller(name, plural) for name, (plural, _, controller) in _RESOURCES.items()},
        },
    }


_PROBE = """
PNG = b"\\x89PNG\\r\\n\\x1a\\n" + b"\\x00" * 64

def headers(email):
    client.post("/api/members/register", json={"email": email, "password": "pw123456"})
    login = client.post("/api/members/login", json={"email": email, "password": "pw123456"})
    return {"Authorization": "Bearer " + login.json()["token"]}

def create(plural, owner):
    parts = [("_data", (None, json.dumps({"title": "t"}), "application/json")), ("cover", ("c.png", PNG, "image/png"))]
    return client.post(f"/api/{plural}", files=parts, headers=owner).json()["id"]

def patch(plural, record, who):
    return client.patch(f"/api/{plural}/{record}", files=[("_data", (None, json.dumps({"title": "u"}), "application/json"))], headers=who)

with client:
    owner, stranger = headers("owner@example.com"), headers("stranger@example.com")
    note, draft, clip = create("notes", owner), create("drafts", owner), create("clips", owner)
    attempts = {
        "delete note": [client.delete(f"/api/notes/{note}", headers=who) for who in (stranger, owner, owner)],
        "update draft": [patch("drafts", draft, who) for who in (stranger, owner)] + [patch("drafts", "missing", owner)],
        "update clip": [patch("clips", clip, who) for who in (stranger, owner)],
        "delete clip": [client.delete(f"/api/clips/{clip}", headers=who) for who in (stranger, owner, owner)],
    }
    print(json.dumps({name: [response.status_code for response in responses] for name, responses in attempts.items()}))
"""


@pytest.fixture(scope="module")
def statuses(tmp_path_factory) -> dict[str, list[int]]:
    directory = tmp_path_factory.mktemp("record-lookup")
    return run_generated(write_spec(directory, yaml.safe_dump(_spec(directory))), "fastapi", _PROBE)


@pytest.mark.parametrize(
    ("attempt", "expected"),
    [
        ("delete note", [403, 200, 404]),
        ("update draft", [403, 200, 404]),
        ("update clip", [403, 200]),
        ("delete clip", [403, 200, 404]),
    ],
)
def test_record_is_read_before_it_is_written(statuses, attempt, expected):
    assert statuses[attempt] == expected


def test_route_running_an_operation_its_service_disables_is_rejected(tmp_path):
    spec = write_spec(tmp_path, """
        version: "0.3"
        datastores:
          main: { type: postgres, dsn: "sqlite+aiosqlite:///app.sqlite", default: true }
        entities:
          note:
            fields:
              id: { type: id }
              title: { type: string }
        repositories:
          notes: { entity: note }
        services:
          notes:
            repository: notes
            operations: { delete: false }
        controllers:
          notes:
            base_path: /notes
            routes:
              delete: { service: notes, method: DELETE, path: "/{id}", access: public }
    """)
    with pytest.raises(ConfigErrors) as raised:
        load_and_generate_ir(str(spec))
    assert [error.code for error in raised.value.errors] == ["SERVICE_OPERATION_DISABLED"]
