"""Every key location a spec schema declares is consumed, and every prop a pack component declares is read by
the UI.

A location is consumed when a valid spec among the examples and fixtures uses it and some change
of its value that the schema still accepts changes what the consumers receive: the IR the dev
server and every generated backend are built from, the UI generator context, or a rejection by a
check past the schema. A value the schema pins, such as a branch discriminator, admits no change
to observe; the schema reading it to pick the branch is its consumer.
"""

import re
from collections.abc import Iterator
from copy import deepcopy
from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path
from typing import Any

import pytest

from tests.unit.support.schema_locations import Node, declared
from yaml_api_generator.generators.frontend.packs.loader import load_pack
from yaml_api_generator.generators.frontend.renderer import CRUD_PAGES
from yaml_api_generator.parsers.template_loader import Manifest
from yaml_api_generator.parsers.ui_parser import build_generator_context
from yaml_api_generator.parsers.yaml_parser import (
    SPEC_SCHEMAS,
    ParseResult,
    generate_ir,
)

ROOT = Path(__file__).parents[2]
SCHEMA_FILES = (*SPEC_SCHEMAS.values(), "ui.schema.json")
DELETED = object()


def received(result: ParseResult) -> tuple[Any, ...]:
    """What the consumers receive from a spec: the IR, and for a UI block the generator context and the
    ``frontend`` target the command line reads."""
    if result.ui_block is None:
        return (result.ir,)
    frontend = result.ui_block["frontend"]
    return result.ir, frontend, build_generator_context(result.ir, result.ui_block, load_pack(frontend["pack"]).manifest)


def changed(config: Any, value_path: tuple, value: Any) -> Any:
    """A copy of ``config`` with ``value`` at ``value_path``, or without that key when ``value`` is ``DELETED``."""
    config = deepcopy(config)
    *parents, key = value_path
    container = config
    for step in parents:
        container = container[step]
    if value is DELETED:
        del container[key]
    else:
        container[key] = value
    return config


def variants(location: Node, value: Any) -> Iterator[Any]:
    """Changes of ``value`` worth trying: dropping it, another value its schema allows, or a nearby one."""
    yield DELETED
    yield from (other for node in location.applicable(value) for other in node.schema.get("enum", ()) if other != value)
    match value:
        case bool():
            yield not value
        case int() | float():
            yield value + 1
        case str():
            yield f"{value}x"
        case list():
            yield from (changed(value, (index,), DELETED) for index in range(len(value)))
        case dict():
            yield from (changed(value, (key,), DELETED) for key in value)


@dataclass(frozen=True)
class Spec:
    """An example or fixture spec, as loaded."""

    path: Path

    def __str__(self) -> str:
        return str(self.path.relative_to(ROOT))

    @cached_property
    def config(self) -> dict[str, Any]:
        return Manifest.discover(self.path).load()

    @cached_property
    def schema(self) -> Node:
        return Node(SPEC_SCHEMAS.get(str(self.config.get("version", "0.1")), SPEC_SCHEMAS["0.1"]))

    def outcome(self, config: dict[str, Any]) -> object:
        try:
            return received(generate_ir(deepcopy(config), self.path.parent))
        except Exception as exc:  # noqa: BLE001 - a consumer refusing the change still read the key
            return type(exc), str(exc)

    @cached_property
    def baseline(self) -> object:
        return self.outcome(self.config)

    def uses(self) -> Iterator[tuple[Node, tuple]]:
        return self.schema.uses(self.config)

    def consumes(self, location: Node, value_path: tuple) -> bool:
        value = self.config
        for step in value_path:
            value = value[step]
        accepted = [
            config
            for config in (changed(self.config, value_path, variant) for variant in variants(location, value))
            if self.schema.holds(config)
        ]
        return not accepted or any(self.outcome(config) != self.baseline for config in accepted)


@cache
def corpus() -> tuple[Spec, ...]:
    """Every example and fixture spec the parser accepts."""
    specs = (
        Spec(path)
        for pattern in ("examples/**/*.yaml", "tests/fixtures/**/*.yaml")
        for path in sorted(ROOT.glob(pattern))
        if "invalid" not in path.parts
    )
    return tuple(spec for spec in specs if spec.schema.holds(spec.config) and isinstance(spec.baseline, tuple))


@cache
def uses() -> dict[Node, list[tuple[Spec, tuple]]]:
    """Each location the corpus uses, with every spec and value path using it."""
    found: dict[Node, list[tuple[Spec, tuple]]] = {}
    for spec in corpus():
        for location, value_path in spec.uses():
            found.setdefault(location, []).append((spec, value_path))
    return found


LOCATIONS = sorted({location for file in SCHEMA_FILES for location in declared(file)}, key=str)


@pytest.mark.parametrize("location", LOCATIONS, ids=str)
def test_every_schema_location_has_a_consumer(location):
    found = uses().get(location)
    assert found, f"no example or fixture uses {location}"
    assert any(spec.consumes(location, value_path) for spec, value_path in found), (
        f"no change of {location} reaches a consumer in " + ", ".join(sorted({str(spec) for spec, _ in found}))
    )


GENERIC = load_pack("generic")
TEMPLATES = GENERIC.templates_dir
COMPONENTS = GENERIC.manifest.components

# Declared by the pack without a template: a view using one fails generation naming the missing template.
TEMPLATELESS = {"auth-centered", "auth-signup-role", "auth-error", "split-pane", "sidebar-layout"}

# Declared pack props no template reads, with what the page uses instead.
UNREAD_PROPS: dict[tuple[str, str], str] = {
    ("form-stacked", "mode"): "create or edit follows the route",
    ("form-sectioned", "mode"): "create or edit follows the route",
    ("form-preview", "mode"): "create or edit follows the route",
    ("form-inline-row", "record"): "the rows listed from the collection",
    ("auth-tabbed", "providers"): "nothing: the page calls no login operation and its provider buttons no provider",
    ("filter-builder", "rules"): "an empty rule set",
    ("filter-facets", "facets"): "no facet selected",
    ("filter-column", "column"): "no column filtered",
    ("filter-column", "values"): "no column filtered",
    ("bulk-floating", "selected"): "the rows the user selects",
    ("bulk-toolbar", "selected"): "the rows the user selects",
    ("bulk-toolbar", "total"): "the number of listed rows",
    ("bulk-edit-drawer", "selected"): "the rows the user selects",
    ("bulk-progress", "current"): "the progress of the running deletion",
    ("bulk-progress", "total"): "the number of listed rows",
    ("context-menu", "selected"): "the rows the user selects",
    ("settings-yaml", "spec"): "a placeholder spec and the generated summary",
    ("settings-roles", "roles"): "the roles of entities.<e>.roles",
    ("settings-danger", "actions"): "its fixed action list",
}


@cache
def _template_text(path: str) -> str:
    """A template's source with every template it includes or imports macros from."""
    source = (TEMPLATES / path).read_text()
    used = re.findall(r"{%\s*(?:include|from)\s+'([^']+)'", source)
    return "\n".join([source, *map(_template_text, used)])


def _reads(component: str, prop: str, kind: str | None) -> bool:
    """Whether the UI consumes `prop` of `component`: a function prop by its name, the collection through the
    renderer's entity, a crud slot through the renderer and any other prop through `props` in its template."""
    if component == "crud":
        defaults = {COMPONENTS[component]["props"][slot]["default"] for slot in CRUD_PAGES}
        return prop in CRUD_PAGES or any(_reads(slot, prop, kind) for slot in defaults if prop in COMPONENTS[slot].get("props", {}))
    text = _template_text(f"components/{component}.jinja")
    pattern = rf"\b{prop}\b" if kind == "function" else rf"props(\.{prop}\b|\.get\('{prop}'\))"
    return prop == "collection" or re.search(pattern, text) is not None


def _pack_props() -> Iterator[tuple[str, str, str | None]]:
    for component, component_spec in COMPONENTS.items():
        if component not in TEMPLATELESS:
            for prop, spec in (component_spec.get("props") or {}).items():
                yield component, prop, spec.get("type")


def test_every_rendered_pack_component_has_a_template():
    rendered = COMPONENTS.keys() - TEMPLATELESS - {"crud"}
    assert {name for name in rendered if not (TEMPLATES / "components" / f"{name}.jinja").is_file()} == set()


def test_every_pack_prop_is_read_by_the_ui():
    unread = {(component, prop) for component, prop, kind in _pack_props() if not _reads(component, prop, kind)}
    assert unread - UNREAD_PROPS.keys() == set()


@pytest.mark.parametrize("component", sorted(TEMPLATELESS))
def test_templateless_component_still_has_no_template(component):
    assert component in COMPONENTS and not (TEMPLATES / "components" / f"{component}.jinja").exists()


@pytest.mark.parametrize(("component", "prop"), sorted(UNREAD_PROPS))
def test_unread_prop_is_still_declared_and_unread(component, prop):
    assert not _reads(component, prop, COMPONENTS[component]["props"][prop].get("type"))
