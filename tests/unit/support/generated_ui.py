"""The generic pack's App component rendered for a spec."""

from pathlib import Path

from yaml_api_generator.generators.frontend.packs.loader import load_pack
from yaml_api_generator.generators.frontend.renderer import render_templates
from yaml_api_generator.parsers.ui_parser import build_generator_context
from yaml_api_generator.parsers.yaml_parser import load_and_generate_ir

APP = "src/__generated__/App.tsx"


def generator_context(spec: Path, ui: dict | None = None):
    ir = load_and_generate_ir(str(spec)).ir
    return build_generator_context(ir, ui or {}, load_pack("generic").manifest)


def rendered_app(context) -> str:
    return next(item.content for item in render_templates(load_pack("generic"), context) if item.path == APP)
