"""A frontend rendering every component of the generic pack type-checks as the project it is generated into."""

import shutil
import subprocess

import pytest
import yaml

from tests.unit.support.live_apps import STACKFORM
from yaml_api_generator.generators.frontend.packs.loader import load_pack

NPM = shutil.which("npm")

SPEC = """
version: "0.3"

api:
  basePath: /api
  version: v1
  operations:
    defaults: { list: true, get: true, create: true, update: true, replace: false, delete: true }
    auth: { register: true, login: true }

datastores:
  local: { type: postgres, dsn: "sqlite+aiosqlite:///compile.sqlite", default: true }

entities:
  member:
    type: auth
    auth: { identifier: handle, via: password }
    roles:
      values: [admin, viewer]
      default: viewer
      hierarchy: { admin: [viewer] }
    fields:
      id: { type: id }
      handle: { type: string, required: true, unique: true }
      age: { type: number }
      active: { type: boolean, default: true }
  item:
    fields:
      id: { type: id }
      code: { type: string, required: true, unique: true }
      rank: { type: number, required: true }
      flag: { type: boolean, default: false }
      status: { type: enum, values: [draft, live], default: draft }
      stamp: { type: string, readonly: true }
      owner: { type: ref, ref: member }
      removedAt: { type: datetime }

repositories:
  members: { entity: member }
  items: { entity: item, softDelete: removedAt }

services:
  members: { repository: members }
  items: { repository: items }

controllers:
  members:
    service: members
    base_path: /members
    access: admin
    operations:
      register: { access: public }
      login: { access: public }
  items:
    service: items
    base_path: /items
    access: viewer
"""

REQUIRED_VALUES = {"collection": "item", "component": "list-table", "string": "Title", "array": []}

NAMED_SAMPLES = {
    "array": {
        "columns": ["code", "rank"],
        "fields": ["status", "code"],
        "sections": [{"title": "Main", "fields": ["code", "rank"]}],
        "relations": ["owner"],
        "filters": ["status"],
    },
    "object": {"field_roles": {"title": "code", "status": "status", "date": "stamp"}, "active_filters": {"status": "live"}},
    "string": {"groupBy": "status"},
}


def _sample(name: str, spec: dict):
    """A value of the prop declared by `spec` other than its default, so its branch is rendered too."""
    items = spec.get("items", {})
    if "enum" in items:
        return items["enum"][-1:]
    by_type = {
        "boolean": lambda: not spec.get("default", False),
        "number": lambda: spec.get("default", 1) + 1,
        "string": lambda: "Sample",
        "collection": lambda: "member",
        "component": lambda: "list-card-grid",
        "object": dict,
        "array": lambda: ["member"] if items.get("type") == "collection" else [],
    }
    return NAMED_SAMPLES.get(spec["type"], {}).get(name, by_type[spec["type"]]())


def _props(component: dict, given) -> dict:
    return {
        prop: REQUIRED_VALUES[spec["type"]] if spec.get("required") else given(prop, spec)
        for prop, spec in (component.get("props") or {}).items()
        if spec.get("required") or (given and spec["type"] != "function")
    }


def _views() -> dict:
    """Per component the pack renders, a view given only the props it requires and one given a sample of every
    prop, plus a crud view per delete and detail variant, over a collection with and one without soft delete."""
    pack = load_pack("generic")
    components = pack.manifest.components
    templates = {"crud"} | {template.stem for template in (pack.templates_dir / "components").glob("*.jinja")}
    rendered = sorted(components.keys() & templates)
    slots = [(slot, name) for slot in ("delete", "detail") for name in rendered if name.startswith(f"{slot}-")]
    views = {
        f"{name}{suffix}": {"path": f"/{name}{suffix}", "component": name, "props": _props(components[name], given)}
        for name in rendered
        for suffix, given in (("", None), ("-sampled", _sample))
    }
    crud = {
        f"crud-{collection}-{variant}": {
            "path": f"/crud-{collection}-{variant}",
            "component": "crud",
            "props": {"collection": collection, slot: variant},
        }
        for collection in ("item", "member")
        for slot, variant in slots
    }
    return views | crud


@pytest.fixture(scope="module")
def frontend(tmp_path_factory):
    root = tmp_path_factory.mktemp("compile")
    spec = root / "spec.yaml"
    ui = {"ui": {"frontend": {"pack": "generic"}, "views": _views()}}
    spec.write_text(SPEC + yaml.safe_dump(ui, sort_keys=False))
    built = subprocess.run([STACKFORM, "build", str(spec), "frontend", "-o", str(root / "app")], capture_output=True, text=True)
    assert built.returncode == 0, built.stdout + built.stderr
    installed = subprocess.run(
        [NPM, "install", "--no-audit", "--no-fund", "--loglevel=error"], cwd=root / "app", capture_output=True, text=True
    )
    assert installed.returncode == 0, installed.stderr
    return root / "app"


@pytest.mark.skipif(NPM is None, reason="npm installs the generated project's compiler and types")
def test_every_pack_component_type_checks(frontend):
    compiled = subprocess.run(["npx", "--no-install", "tsc", "-b"], cwd=frontend, capture_output=True, text=True)

    assert compiled.returncode == 0, compiled.stdout
