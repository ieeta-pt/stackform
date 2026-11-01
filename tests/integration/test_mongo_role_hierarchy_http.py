"""The entity-level role hierarchy suite, served on MongoDB by the dev server and every generated backend."""

import itertools
from uuid import uuid4

import pytest

from tests.unit.support.live_apps import MONGO_SERVERS, mongo, serve, write_spec
from tests.unit.test_role_hierarchy_http import *  # noqa: F403
from tests.unit.test_role_hierarchy_http import register_admin, versioned

pytestmark = pytest.mark.integration


@pytest.fixture(
    scope="module",
    params=list(itertools.product(MONGO_SERVERS, ("0.2", "0.3"))),
    ids=lambda param: f"{param[0].name}-{param[1]}",
)
def client(request, tmp_path_factory, mongo_uri):
    server, version = request.param
    directory = tmp_path_factory.mktemp(f"{server.name}-{version}")
    with serve(server, write_spec(directory, versioned(version), mongo(mongo_uri, f"{server.name}_{uuid4().hex}"))) as client:
        register_admin(client)
        yield client
