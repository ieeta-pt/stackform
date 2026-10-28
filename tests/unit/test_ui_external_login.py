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
    assert '<ExternalProviders collection="users" />' in app
    assert "fetch(`${API_BASE_URL}/${collection}/auth/providers`)" in app


def test_provider_button_starts_the_provider_login(app):
    assert "window.location.href = `${API_BASE_URL}/${collection}/auth/${p.name}`;" in app


def test_callback_route_exchanges_the_login_code_for_a_session(app):
    assert '<Route path="/auth/callback" element={<AuthCallback onToken={handleExternalToken} />} />' in app
    assert "const code = new URLSearchParams(window.location.search).get('code');" in app
    assert "fetch(`${API_BASE_URL}/auth/exchange`, {" in app


def test_sign_out_ends_the_provider_session(app):
    assert "localStorage.setItem('sso_logout_path', `${collection}/auth/${p.name}/logout`);" in app
    assert "window.location.href = `${API_BASE_URL}/${ssoLogoutPath}`;" in app


def test_password_identity_lists_no_providers(tmp_path):
    spec = write_spec(tmp_path, _SPEC.replace("login: false", "login: true"))
    assert "<ExternalProviders collection=" not in rendered_app(generator_context(spec))
