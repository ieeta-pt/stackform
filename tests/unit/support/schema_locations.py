"""Where spec keys sit in the schemas: the key locations a schema declares and the ones a spec uses.

A location is one ``properties`` entry of a schema, named by its file and JSON pointer, so the
same key name declared under two objects is two locations.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache, cached_property
from typing import Any

from jsonschema import Draft202012Validator

from yaml_api_generator.parsers.yaml_parser import SCHEMA_DIR, SCHEMA_REGISTRY

CONDITIONS = frozenset({"if", "not", "contains", "propertyNames"})
"""Keywords whose subschemas test an instance rather than declare its keys."""

VALUES = frozenset({"const", "enum", "default", "examples"})
"""Keywords holding instance values, never subschemas."""

Path = tuple[str | int, ...]


def _escape(token: str | int) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


@dataclass(frozen=True)
class Node:
    """A subschema, by its schema file and JSON pointer."""

    file: str
    pointer: str = ""

    def __str__(self) -> str:
        return f"{self.file.removesuffix('.schema.json')}#{self.pointer}"

    def child(self, *tokens: str | int) -> Node:
        return Node(self.file, self.pointer + "".join(f"/{_escape(token)}" for token in tokens))

    @cached_property
    def schema(self) -> Any:
        return SCHEMA_REGISTRY.resolver(base_uri=self.file).lookup(f"{self.file}#{self.pointer}").contents

    def holds(self, instance: Any) -> bool:
        return _validator(self).is_valid(instance)

    def referenced(self) -> Node:
        target, _, pointer = self.schema["$ref"].partition("#")
        return Node(target or self.file, pointer)

    def applicable(self, instance: Any) -> Iterator[Node]:
        """This subschema and every subschema it applies to ``instance``."""
        if not isinstance(self.schema, dict):
            return
        yield self
        if "$ref" in self.schema:
            yield from self.referenced().applicable(instance)
        for index, _ in enumerate(self.schema.get("allOf", ())):
            yield from self.child("allOf", index).applicable(instance)
        for keyword in ("anyOf", "oneOf"):
            for index, _ in enumerate(self.schema.get(keyword, ())):
                branch = self.child(keyword, index)
                if branch.holds(instance):
                    yield from branch.applicable(instance)
        if "if" in self.schema:
            branch = "then" if self.child("if").holds(instance) else "else"
            if branch in self.schema:
                yield from self.child(branch).applicable(instance)
        if isinstance(instance, dict):
            for key in self.schema.get("dependentSchemas", {}).keys() & instance.keys():
                yield from self.child("dependentSchemas", key).applicable(instance)

    def uses(self, instance: Any, path: Path = ()) -> Iterator[tuple[Node, Path]]:
        """Every location ``instance`` uses under this subschema, with the instance path of its value."""
        nodes = list(self.applicable(instance))
        if isinstance(instance, dict):
            for key, value in instance.items():
                yield from _key_uses(nodes, key, value, (*path, key))
        elif isinstance(instance, list):
            for index, item in enumerate(instance):
                for node in nodes:
                    if index < len(node.schema.get("prefixItems", ())):
                        yield from node.child("prefixItems", index).uses(item, (*path, index))
                    elif isinstance(node.schema.get("items"), dict):
                        yield from node.child("items").uses(item, (*path, index))


def _key_uses(nodes: list[Node], key: str, value: Any, path: Path) -> Iterator[tuple[Node, Path]]:
    declaring = [node.child("properties", key) for node in nodes if key in node.schema.get("properties", {})]
    for location in declaring:
        yield location, path
        yield from location.uses(value, path)
    if declaring:
        return
    for node in nodes:
        for pattern in node.schema.get("patternProperties", {}):
            if re.search(pattern, key):
                yield from node.child("patternProperties", pattern).uses(value, path)
        if isinstance(node.schema.get("additionalProperties"), dict):
            yield from node.child("additionalProperties").uses(value, path)


@cache
def _validator(node: Node) -> Draft202012Validator:
    return Draft202012Validator({"$ref": f"{node.file}#{node.pointer}"}, registry=SCHEMA_REGISTRY)


def _forbids(schema: Any) -> bool:
    """Whether ``schema`` accepts no value, the way a schema forbids a key."""
    return schema is False or (isinstance(schema, dict) and schema.get("not") == {})


def declared(file: str) -> Iterator[Node]:
    """Every location ``file`` declares outside a condition, leaving out the keys it forbids."""
    def walk(schema: Any, node: Node) -> Iterator[Node]:
        if isinstance(schema, list):
            for index, item in enumerate(schema):
                yield from walk(item, node.child(index))
        elif isinstance(schema, dict):
            for keyword, value in schema.items():
                if keyword == "properties":
                    for key, sub in value.items():
                        if not _forbids(sub):
                            yield node.child(keyword, key)
                            yield from walk(sub, node.child(keyword, key))
                elif keyword not in CONDITIONS | VALUES:
                    yield from walk(value, node.child(keyword))

    yield from walk(json.loads((SCHEMA_DIR / file).read_text()), Node(file))
