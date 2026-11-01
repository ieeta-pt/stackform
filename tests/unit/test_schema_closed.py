"""Every record a spec or UI schema describes is closed, so an unknown key is a schema error.

A record is an object schema that names its keys under ``properties``. It is closed when some
schema applying to the same instance, through ``$ref``, ``allOf``, ``anyOf``, ``oneOf``, ``then``,
``else`` or ``dependentSchemas``, sets ``additionalProperties`` or ``unevaluatedProperties`` to
``false``. A map, whose ``additionalProperties`` is a schema, is closed by that schema.
"""

from collections.abc import Iterable, Iterator
from typing import Any

import pytest

from tests.unit.support.schema_locations import Node
from yaml_api_generator.parsers.yaml_parser import SPEC_SCHEMAS

SCHEMA_FILES = (*SPEC_SCHEMAS.values(), "ui.schema.json")
APPLICATORS = ("allOf", "anyOf", "oneOf")
BRANCHES = ("then", "else")
VALUE_SCHEMAS = ("additionalProperties", "unevaluatedProperties", "items")


def _closes(schema: dict[str, Any]) -> bool:
    return schema.get("unevaluatedProperties") is False or schema.get("additionalProperties", True) not in (True, {})


def _refinements(node: Node) -> Iterator[Node]:
    """The subschemas that apply to the same instance as ``node``."""
    schema = node.schema
    if "$ref" in schema:
        yield node.referenced()
    for keyword in APPLICATORS:
        yield from (node.child(keyword, index) for index, _ in enumerate(schema.get(keyword, ())))
    yield from (node.child(branch) for branch in BRANCHES if branch in schema)
    yield from (node.child("dependentSchemas", key) for key in schema.get("dependentSchemas", {}))


def _instance_schemas(nodes: Iterable[Node]) -> frozenset[Node]:
    """``nodes`` and every subschema that applies to the same instance through them."""
    found, pending = set(), list(nodes)
    while pending:
        node = pending.pop()
        if isinstance(node.schema, dict) and node not in found:
            found.add(node)
            pending.extend(_refinements(node))
    return frozenset(found)


def _value_schemas(schemas: frozenset[Node]) -> Iterator[frozenset[Node]]:
    """The schemas of each value inside the instance ``schemas`` apply to, one set per value."""
    keys = {key for node in schemas for key in node.schema.get("properties", {})}
    for key in keys:
        yield _instance_schemas(node.child("properties", key) for node in schemas if key in node.schema.get("properties", {}))
    for node in schemas:
        yield from ({node.child("patternProperties", key)} for key in node.schema.get("patternProperties", {}))
        yield from ({node.child(keyword)} for keyword in VALUE_SCHEMAS if isinstance(node.schema.get(keyword), dict))
        yield from ({node.child("prefixItems", index)} for index, _ in enumerate(node.schema.get("prefixItems", ())))


def open_records(schemas: frozenset[Node], seen: set[frozenset[Node]]) -> Iterator[Node]:
    """The records among ``schemas`` and the schemas of the values inside, when nothing applying closes them."""
    if schemas in seen:
        return
    seen.add(schemas)
    if not any(_closes(node.schema) for node in schemas):
        yield from (node for node in schemas if "properties" in node.schema)
    for values in _value_schemas(schemas):
        yield from open_records(_instance_schemas(values), seen)


@pytest.mark.parametrize("file", SCHEMA_FILES)
def test_every_record_is_closed(file):
    assert sorted(map(str, set(open_records(_instance_schemas([Node(file)]), set())))) == []
