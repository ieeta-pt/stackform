"""The purges that erase each collection's expired rows, discarding the files those rows held."""

from collections.abc import Awaitable, Callable, Mapping
from functools import partial
from types import MappingProxyType

from yaml_api_generator.ir import IRDocument
from yaml_api_generator.runtime.files import RecordFiles
from yaml_api_generator.runtime.lifecycle import releasing

from .repositories import RepositoryRegistry


def expiring_purges(
    ir: IRDocument,
    registry: RepositoryRegistry,
    record_files: Mapping[str, RecordFiles] = MappingProxyType({}),
) -> list[Callable[[], Awaitable[object]]]:
    def purge(name: str) -> Callable[[], Awaitable[object]]:
        erase = partial(registry.for_collection(name).purge_expired, name)
        files = record_files.get(name)
        return erase if files is None else releasing(erase, files.release)

    return [purge(name) for name, collection in ir.collections.items() if collection.lifecycle.expiry]
