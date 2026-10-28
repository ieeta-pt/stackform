"""Provider parsing: every `providers.<name>` entry becomes the IR provider of its `type`."""

from collections.abc import Callable
from typing import Any

from yaml_api_generator.ir.api import IROIDCProvider, IRProvider, IRSAMLProvider

_PROVIDER_TYPES: dict[str, Callable[..., IRProvider]] = {"oidc": IROIDCProvider, "saml": IRSAMLProvider}


def parse_providers(providers_data: dict[str, Any]) -> dict[str, IRProvider]:
    """Build each provider from its keys, which the schema limits to the fields of its IR type."""
    return {
        name: _PROVIDER_TYPES[config["type"]](
            name=name, **{key: tuple(value) if isinstance(value, list) else value for key, value in config.items()}
        )
        for name, config in providers_data.items()
    }
