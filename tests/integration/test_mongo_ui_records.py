"""The generated UI reaches every server on MongoDB, the generated raw and DRF backends among them, through
the routes, pagination, roles, access and projections the spec declares."""

import shutil
from uuid import uuid4

import pytest

from tests.unit.support.live_apps import MONGO_SERVERS, mongo, serve, write_spec
from tests.unit.test_ui_records import DRIVER, SPEC, drive, driven
from yaml_api_generator.cli.compiler import compile_project

pytestmark = pytest.mark.integration

SQLITE = '''datastores:
  local: { type: postgres, dsn: "sqlite+aiosqlite:///records.sqlite", default: true }'''

INVALID = {
    "dev": "Missing required fields: code",
    "fastapi": "code: Field required",
    "raw": "Missing required fields: code",
    "drf": "Missing required fields: code",
}


@pytest.mark.skipif(shutil.which("node") is None, reason="node runs the generated data layer")
@pytest.mark.parametrize("server", MONGO_SERVERS, ids=lambda server: server.name)
def test_generated_data_layer_drives_every_server_on_mongo(tmp_path, mongo_uri, server):
    spec = write_spec(tmp_path, SPEC.replace(SQLITE, "{datastore}"), mongo(mongo_uri, f"ui_{server.name}_{uuid4().hex}"))
    compile_project(yaml_file=spec, output_dir=tmp_path / "generated", target="fastapi")
    with serve(server, spec) as client:
        (tmp_path / "generated/frontend/src/__generated__/drive.mjs").write_text(DRIVER)
        report = drive(tmp_path, str(client.base_url).rstrip("/"))

    assert report == driven(INVALID[server.name])
