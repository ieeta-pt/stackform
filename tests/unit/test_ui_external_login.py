"""The generated UI signs in through every external provider an identity binds, using the routes the backend serves for it."""

from pathlib import Path

import pytest

from tests.unit.support.generated_ui import generator_context, rendered_app
from tests.unit.support.live_apps import write_spec
from tests.unit.test_identity_http import _SPEC

SAML_SPEC = Path(__file__).parents[1] / "fixtures" / "valid" / "auth-saml.yaml"


@pytest.fixture(scope="module")
def app() -> str:
    return rendered_app(generator_context(SAML_SPEC))


def test_sign_in_page_lists_the_providers_of_the_identity(app):
    assert '<ExternalProviders identity="user" collection="users" />' in app
    assert "fetch(`${API_BASE_URL}/${collection}/auth/providers`)" in app


def test_provider_button_starts_the_provider_login(app):
    assert "window.location.href = `${API_BASE_URL}/${collection}/auth/${p.name}`;" in app


def test_callback_route_exchanges_the_login_code_for_a_session(app):
    assert '<Route path="/auth/callback" element={<AuthCallback onSession={signInExternally} />} />' in app
    assert "const code = new URLSearchParams(window.location.search).get('code');" in app
    assert "fetch(`${API_BASE_URL}/auth/exchange`, {" in app


def test_sign_out_ends_the_provider_session(app):
    assert "localStorage.setItem('sso', JSON.stringify({ identity, logoutPath: `${collection}/auth/${p.name}/logout` }));" in app
    assert "window.location.href = `${API_BASE_URL}/${logoutPath}`;" in app


def test_provider_session_signs_in_with_the_roles_the_exchange_reports(app):
    assert "callerOf(JSON.parse(localStorage.getItem('sso')!).identity, session)" in app


def test_password_identity_lists_no_providers(tmp_path):
    spec = write_spec(tmp_path, _SPEC.replace("login: false", "login: true"))
    assert "<ExternalProviders " not in rendered_app(generator_context(spec))
