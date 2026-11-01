"""Semantic checks for payload declarations: top-level ``dto`` and service ``input``.

The schema types a payload field, so persistence attributes (``type: id``,
``unique``) never reach these checks:

- DTO_NOT_FOUND: a DTO or service input field, at any nesting depth, references a type that is
  neither a declared entity nor a declared DTO.
- FILE_FIELD_CONTEXT_INVALID: a DTO field is, or contains, a ``type: file`` node.
"""

from typing import Any

from yaml_api_generator.parsers.transformers.field_maps import field_maps, spec_fields
from yaml_api_generator.parsers.transformers.file_validation import file_context_errors
from yaml_api_generator.parsers.transformers.ref_validation import field_refs
from yaml_api_generator.parsers.yaml_parser import ConfigError

_PAYLOADS = {"dto": "DTO", "services": "Service input"}


def validate_spec_dtos(spec: dict[str, Any]) -> list[ConfigError]:
    known_refs = frozenset((spec.get("entities") or {}).keys() | (spec.get("dto") or {}).keys())
    return [
        *(
            error
            for path, field in spec_fields(spec, ("dto",))
            for error in file_context_errors(field, path, "DTOs")
        ),
        *(
            ConfigError(
                code="DTO_NOT_FOUND",
                message=f"{label} field references undeclared type '{target}'",
                path=path,
            )
            for section, label in _PAYLOADS.items()
            for base, fields in field_maps(spec, (section,))
            for path, target in field_refs(fields, base)
            if target not in known_refs
        ),
    ]
