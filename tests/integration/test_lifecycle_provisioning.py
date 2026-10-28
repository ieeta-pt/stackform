"""Provisioning an identity, as a provider sign-in does, never revives a removed one: it adds a user beside it."""

import asyncio
import json
import os
import subprocess
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from pymongo import MongoClient

from tests.integration.support.postgres import fresh_database
from tests.support.lifecycle import PROVISIONED, VERSIONS, mongo_spec, reprovision, sql_spec
from yaml_api_generator.cli.compiler import compile_project
from yaml_api_generator.server.common.loader import create_repositories, initialize_indexes

pytestmark = pytest.mark.integration

ROOT = Path(__file__).parents[2]

_GENERATED = """
import asyncio, json
from app import app, lifespan
from dependencies.repositories import repository
from tests.support.lifecycle import reprovision

async def main():
    async with lifespan(app):
        users = repository("users")
        print(json.dumps(await reprovision(users.create, users.delete, users.upsert_by)))

asyncio.run(main())
"""


async def _dev(spec: Path) -> list[str]:
    ir, registry = create_repositories(str(spec))
    await initialize_indexes(ir, registry)
    users = registry.for_collection("users")
    try:
        return await reprovision(partial(users.create, "users"), partial(users.delete, "users"), partial(users.upsert_by, "users"))
    finally:
        await users.close()


def _generated(spec: Path) -> list[str]:
    compile_project(yaml_file=str(spec), output_dir=str(spec.parent), target="fastapi")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, (str(ROOT), os.environ.get("PYTHONPATH"))))}
    result = subprocess.run(
        [sys.executable, "-c", _GENERATED], cwd=spec.parent / "backend", env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.splitlines()[-1])


def _provision(server: str, spec: Path) -> list[str]:
    return asyncio.run(_dev(spec)) if server == "dev" else _generated(spec)


def _check(ids: list[str], removals: Callable[[], list[bool]]) -> None:
    assert len(set(ids)) == 2, ids
    assert sorted(removals()) == [False, True]


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("server", ["dev", "fastapi"])
def test_mongo(tmp_path, monkeypatch, mongo_uri, server, version):
    database = f"provisioning_{uuid4().hex[:12]}"
    for name, value in {"MONGO_URI": mongo_uri, "MONGO_DB": database, "JWT_SECRET": "provisioning-secret"}.items():
        monkeypatch.setenv(name, value)
    spec = tmp_path / "notes.yaml"
    spec.write_text(mongo_spec(version=version))

    def removals() -> list[bool]:
        with MongoClient(mongo_uri) as client:
            return [row.get("deletedAt") is not None for row in client[database]["users"].find({"email": PROVISIONED})]

    _check(_provision(server, spec), removals)


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("server", ["dev", "fastapi"])
def test_postgres(tmp_path, monkeypatch, postgres_uri, server, version):
    spec = tmp_path / "notes.yaml"
    spec.write_text(sql_spec(version=version))
    with fresh_database(postgres_uri) as dsn:
        monkeypatch.setenv("SQL_DSN", dsn)
        monkeypatch.setenv("JWT_SECRET", "provisioning-secret")

        def removals() -> list[bool]:
            with psycopg.connect(dsn.replace("postgresql+asyncpg", "postgresql", 1)) as connection:
                rows = connection.execute('SELECT "deletedAt" FROM users WHERE email = %s', (PROVISIONED,))
                return [removed is not None for (removed,) in rows]

        _check(_provision(server, spec), removals)
