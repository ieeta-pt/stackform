"""0.1 providers reach the IR, the dev server's sign-in routes and the UI's login choices."""

from pathlib import Path

from yaml_api_generator.generators.frontend.packs.loader import load_pack
from yaml_api_generator.ir.api import IRSAMLProvider
from yaml_api_generator.parsers.ui_parser import build_generator_context
from yaml_api_generator.parsers.yaml_parser import load_and_generate_ir
from yaml_api_generator.server import build_app

SPEC = str(Path(__file__).parents[1] / "fixtures" / "valid" / "v01-auth-saml.yaml")


def test_saml_provider_is_built_from_its_keys():
    assert load_and_generate_ir(SPEC).ir.providers == {
        "corporate": IRSAMLProvider(
            name="corporate",
            idp_metadata_url="http://idp.example.com/metadata",
            sp_entity_id="https://sp.example.com/metadata",
        )
    }


def test_dev_server_serves_the_provider_sign_in_routes():
    paths = {route.path for route in build_app(SPEC).routes}

    assert {"/api/v1/users/auth/corporate", "/api/v1/users/auth/corporate/callback"} <= paths


def test_ui_offers_the_provider_sign_in():
    context = build_generator_context(load_and_generate_ir(SPEC).ir, {}, load_pack("generic").manifest)

    assert [(provider.name, provider.type) for provider in context.entities["users"].auth_providers] == [
        ("corporate", "saml")
    ]
