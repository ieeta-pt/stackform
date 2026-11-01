"""The DTO body suite, served on MongoDB by the dev server and every generated backend."""

import itertools
from uuid import uuid4

import pytest

from tests.unit.support.live_apps import MONGO_SERVERS, mongo
from tests.unit.test_dto_bodies_http import (  # noqa: F401
    MONGO_NAMED,
    VERSIONS,
    case_id,
    note,
    serving,
    test_create_body_must_satisfy_the_dto_and_the_entity,
    test_create_body_satisfying_both_is_stored,
    test_custom_operation_runs_with_a_body_the_dto_accepts,
    test_handler_and_custom_operation_reject_a_body_outside_the_dto,
    test_handler_receives_the_conformed_body,
    test_update_body_is_any_subset_both_accept,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", params=list(itertools.product(MONGO_SERVERS, VERSIONS)), ids=case_id)
def client(request, tmp_path_factory, mongo_uri):
    server, version = request.param
    name = case_id(request.param)
    datastore = mongo(mongo_uri, f"{name.replace('.', '')}_{uuid4().hex}")
    with serving(server, version, tmp_path_factory.mktemp(name), datastore, MONGO_NAMED) as client:
        yield client
