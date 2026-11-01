"""An operation naming a collection of another MongoDB datastore reads that datastore under `stackform run`."""

import pytest

from tests.integration.support.spec_apps import DEV, serve

pytestmark = pytest.mark.integration

SPEC = """
version: "0.3"
api: { basePath: /api }
datastores:
  main: { type: mongodb, uri: "${MONGO_URI}", database: "${MONGO_DB}", default: true }
  archive: { type: mongodb, uri: "${MONGO_URI}", database: "${MONGO_ARCHIVE_DB}" }
entities:
  task: { fields: { id: { type: id }, title: { type: string, required: true } } }
  note: { fields: { id: { type: id }, body: { type: string, required: true } } }
repositories:
  tasks:
    entity: task
    crud: [list]
    operations:
      notesByBody: { query: { command: find, collection: notes, filter: { body: $text } } }
  notes: { entity: note, datastore: archive, crud: [create] }
services:
  tasks: { repository: tasks, operations: { notesByBody: true } }
  notes: { repository: notes }
controllers:
  tasks:
    service: tasks
    base_path: /tasks
    access: public
    operations:
      notesByBody: { method: GET, path: "/notes/{text}" }
  notes: { service: notes, base_path: /notes, access: public }
"""


def test_operation_reads_the_named_collection_from_its_datastore(tmp_path, mongo_uri, mongo_database):
    spec = tmp_path / "spec.yaml"
    spec.write_text(SPEC)
    env = {"MONGO_URI": mongo_uri, "MONGO_DB": mongo_database, "MONGO_ARCHIVE_DB": f"{mongo_database}_archive"}
    with serve(DEV, spec, env) as api:
        assert api.post("/api/notes", json={"body": "kept"}).status_code == 200
        response = api.get("/api/tasks/notes/kept")
    assert response.status_code == 200, response.text
    assert [note["body"] for note in response.json()] == ["kept"]
