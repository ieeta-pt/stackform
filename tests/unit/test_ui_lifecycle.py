"""The generated UI never shows a removed or expired record nor offers to write its removal timestamp,
on the dev server and on a generated FastAPI app."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.support.lifecycle import EXPIRED
from tests.unit.test_ui_records import DEV_SERVER, UVICORN, _serving
from yaml_api_generator.cli.compiler import compile_project
from yaml_api_generator.server.factory import RAW_ENV, SPEC_ENV

SPEC = """
version: "0.3"
api:
  basePath: /api
  operations:
    defaults: { list: true, get: true, create: true, update: true, replace: true, delete: true }
datastores:
  local: { type: postgres, dsn: "${SQL_DSN}", default: true }
entities:
  note:
    fields:
      id: { type: id }
      title: { type: string, required: true }
      createdAt: { type: datetime }
      deletedAt: { type: datetime }
repositories:
  notes:
    entity: note
    softDelete: deletedAt
    ttl: { field: createdAt, seconds: 3600 }
services:
  notes: { repository: notes }
controllers:
  notes: { service: notes, base_path: /notes, access: public }
ui:
  frontend: { pack: generic, output: ./frontend, overwrite: always }
"""

DRIVER = f"""
import {{ ENTITY_FIELDS }} from './fields.ts';
import {{ callOperation, listRecords, readJson }} from './records.ts';

const nativeFetch = globalThis.fetch;
globalThis.fetch = (path, init) => nativeFetch(process.env.ORIGIN + path, init);

const json = {{ 'Content-Type': 'application/json' }};
const send = (operation, {{ body, ...request }} = {{}}) =>
  callOperation('note', operation, {{ headers: json, body: body && JSON.stringify(body), ...request }}).then(readJson);
const recently = new Date(Date.now() - 60000).toISOString();

const notes = {{}};
for (const [title, createdAt] of [['kept', recently], ['removed', recently], ['expired', '{EXPIRED}']]) {{
  notes[title] = (await send('create', {{ body: {{ title, createdAt }} }})).id;
}}
await send('delete', {{ id: notes.removed }});
const opened = (id) => send('get', {{ id }}).then(() => 'shown', (error) => error.message);
console.log(JSON.stringify({{
  listed: (await listRecords('note')).map((note) => note.title),
  opened: [await opened(notes.kept), await opened(notes.removed), await opened(notes.expired)],
  offered: Object.keys(ENTITY_FIELDS.note),
  stamped: await send('update', {{ id: notes.kept, body: {{ deletedAt: recently }} }}).then(() => 'written', (error) => error.message),
  born: await send('create', {{ body: {{ title: 'born', deletedAt: recently }} }}).then(() => 'written', (error) => error.message),
}}));
"""


@pytest.fixture(scope="module")
def project(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("ui-lifecycle")
    (root / "spec.yaml").write_text(SPEC)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("SQL_DSN", "sqlite+aiosqlite:///unused.sqlite")
        compile_project(yaml_file=root / "spec.yaml", output_dir=root / "generated", target="fastapi")
    (root / "generated/frontend/src/__generated__/drive.mjs").write_text(DRIVER)
    return root


SERVERS = {
    "dev-fastapi": lambda project, env: _serving(
        DEV_SERVER, project, {**env, SPEC_ENV: str(project / "spec.yaml"), RAW_ENV: "0"}
    ),
    "generated-fastapi": lambda project, env: _serving((*UVICORN, "app:app"), project / "generated/backend", env),
}


@pytest.mark.skipif(shutil.which("node") is None, reason="node runs the generated data layer")
@pytest.mark.parametrize("server", SERVERS)
def test_removed_and_expired_notes_stay_hidden(project, tmp_path, server):
    env = {"SQL_DSN": f"sqlite+aiosqlite:///{tmp_path / 'notes.sqlite'}", "JWT_SECRET": "ui-lifecycle-signing-key"}
    with SERVERS[server](project, env) as origin:
        result = subprocess.run(
            ["node", "--experimental-strip-types", "--no-warnings", "drive.mjs"],
            cwd=project / "generated/frontend/src/__generated__",
            env={**os.environ, "ORIGIN": origin},
            capture_output=True,
            text=True,
        )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "listed": ["kept"],
        "opened": ["shown", "Error: 404", "Error: 404"],
        "offered": ["title", "createdAt"],
        "stamped": "Error: 422",
        "born": "Error: 422",
    }
