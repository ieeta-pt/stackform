"""The generated UI signs in with a password only through an identity that serves a login route, and registers through one that serves register."""

import re

import pytest

from tests.unit.support.generated_ui import generator_context, rendered_app
from tests.unit.support.live_apps import write_spec
from tests.unit.test_identity_http import _SPEC

PASSWORD_FORM = re.compile(r"<Auth\b")
SIGN_IN_CALL = re.compile(r"callOperation\('\w+', '(login|register)'")
LOGIN_VIEW = {"views": {"signIn": {"path": "/login", "component": "auth-tabbed"}}}


def _context(tmp_path, login, ui=None):
    spec = _SPEC.replace("login: false", f"login: {str(login).lower()}")
    return generator_context(write_spec(tmp_path, spec), ui)


def test_disabled_login_renders_registration_only(tmp_path):
    app = rendered_app(_context(tmp_path, login=False))

    assert {match.group(1) for match in SIGN_IN_CALL.finditer(app)} == {"register"}
    assert PASSWORD_FORM.search(app)


def test_enabled_login_signs_in_through_the_identity_login_route(tmp_path):
    app = rendered_app(_context(tmp_path, login=True))

    assert {match.group(1) for match in SIGN_IN_CALL.finditer(app)} == {"login", "register"}
    assert PASSWORD_FORM.search(app)


def test_a_login_view_without_a_login_route_aborts_generation(tmp_path):
    with pytest.raises(ValueError, match="no identity serves a login route"):
        _context(tmp_path, login=False, ui=LOGIN_VIEW)
