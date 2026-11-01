"""The login exposure HTTP suite, served on MongoDB by the dev server and every generated backend."""

from uuid import uuid4

import pytest

from tests.unit.support.live_apps import MONGO_SERVERS, mongo, serve, write_spec
from tests.unit.test_login_exposure_http import CASES, SPEC, case_id, expected_statuses, login_status

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("server", MONGO_SERVERS, ids=lambda server: server.name)
@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_login_route_follows_the_auth_flag(tmp_path, mongo_uri, server, case):
    version, (flags, served) = case
    spec = write_spec(tmp_path, SPEC.format(version=version, flags=flags), mongo(mongo_uri, f"login_{uuid4().hex}"))
    with serve(server, spec) as client:
        assert login_status(client) in expected_statuses(served)
