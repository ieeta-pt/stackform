"""session.ttl sets the login token lifetime over HTTP on MongoDB in the dev server and every generated backend."""

from uuid import uuid4

import pytest

from tests.unit.support.http_probes import token_lifetime
from tests.unit.support.live_apps import MONGO_SERVERS, serve
from tests.unit.support.session_spec import LASTING, mongo, session_spec

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("server", MONGO_SERVERS, ids=lambda server: server.name)
@pytest.mark.parametrize("version", ["0.2", "0.3"])
@pytest.mark.parametrize(("session", "lifetime"), LASTING.items(), ids=lambda value: str(value) or "none")
def test_login_token_lifetime(tmp_path, mongo_uri, server, version, session, lifetime):
    spec = session_spec(tmp_path, session, version, mongo(mongo_uri, f"ttl_{uuid4().hex}"))
    with serve(server, spec) as client:
        assert token_lifetime(client) == lifetime
