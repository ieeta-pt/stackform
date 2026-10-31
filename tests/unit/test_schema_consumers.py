"""Every key a spec schema accepts is read by some consumer: parser, generator or UI pack, and every prop a
pack component declares is read by the UI.

A key counts as consumed when it occurs as an identifier or a string literal in the
package's Python code, or anywhere in its Jinja templates. Docstrings and dict
display keys do not count: the latter write a key, as schema builders do, rather
than read one.
"""

import ast
import json
import re
from collections.abc import Iterator
from functools import cache
from pathlib import Path

import pytest

from yaml_api_generator.generators.frontend.packs.loader import load_pack
from yaml_api_generator.generators.frontend.renderer import CRUD_PAGES

PACKAGE = Path(__file__).parents[2] / "src" / "yaml_api_generator"
SCHEMAS = PACKAGE / "parsers" / "schemas"

# Accepted by the schema but read by no consumer yet.
UNENFORCED: dict[str, str] = {}

# Read by an external tool from a block the generator copies verbatim.
VERBATIM = {
    "dockerfile": "deploy.services.<name>.build, rendered into docker-compose",
}


def _schema_keys(node, location: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "properties" and isinstance(value, dict):
                for name, sub in value.items():
                    yield name, f"{location}.{name}"
                    yield from _schema_keys(sub, f"{location}.{name}")
            else:
                yield from _schema_keys(value, location)
    elif isinstance(node, list):
        for item in node:
            yield from _schema_keys(item, location)


def _docstring_ids(tree: ast.Module) -> set[int]:
    scopes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    return {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, scopes)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }


def _written_key_ids(tree: ast.Module) -> set[int]:
    return {id(key) for node in ast.walk(tree) if isinstance(node, ast.Dict) for key in node.keys if key is not None}


def _python_words(source: str) -> Iterator[str]:
    tree = ast.parse(source)
    unread = _docstring_ids(tree) | _written_key_ids(tree)
    for node in ast.walk(tree):
        match node:
            case ast.Constant(value=str(text)) if id(node) not in unread:
                yield text
            case ast.Name(id=word) | ast.Attribute(attr=word) | ast.arg(arg=word) | ast.alias(name=word):
                yield word
            case ast.keyword(arg=str(word)) | ast.FunctionDef(name=word) | ast.ClassDef(name=word):
                yield word


@cache
def _corpus() -> str:
    return "\n".join(
        [
            *(word for path in PACKAGE.rglob("*.py") for word in _python_words(path.read_text())),
            *(path.read_text() for path in PACKAGE.rglob("*.jinja")),
        ]
    )


@cache
def _locations() -> dict[str, tuple[str, ...]]:
    found: dict[str, list[str]] = {}
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        for key, location in _schema_keys(json.loads(path.read_text())):
            found.setdefault(key, []).append(f"{path.name}{location}")
    return {key: tuple(locations) for key, locations in found.items()}


def _consumed(key: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(key)}(?![\w-])", _corpus()) is not None


EXEMPT = UNENFORCED | VERBATIM


def test_every_schema_key_has_a_consumer():
    orphans = {
        key: locations[:3]
        for key, locations in _locations().items()
        if key not in EXEMPT and not _consumed(key)
    }
    assert orphans == {}


@pytest.mark.parametrize("key", sorted(EXEMPT))
def test_exempt_key_is_still_an_unconsumed_schema_key(key):
    assert key in _locations()
    assert key in VERBATIM or not _consumed(key)


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
    for component, declared in COMPONENTS.items():
        if component not in TEMPLATELESS:
            for prop, spec in (declared.get("props") or {}).items():
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
