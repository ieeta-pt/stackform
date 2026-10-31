from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, TemplateNotFound

from yaml_api_generator.ir.ui import ComponentNode, GeneratorContext, PropValue, UIView
from .output import OutputFile
from yaml_api_generator.ir.pack_manifest import Pack

SHARED_TEMPLATES = Path(__file__).parent / "shared" / "templates"
"""Templates every pack may list in its scaffold, such as the `records.ts` data layer."""


def render_templates(pack: Pack, context: GeneratorContext) -> list[OutputFile]:
    env = _create_jinja_env(pack.templates_dir)
    files: list[OutputFile] = []

    files.extend(_render_scaffold(env, pack, context))
    files.extend(_render_data_layer(env, pack, context))
    files.extend(_render_views(env, pack, context))

    return files


def _render_scaffold(
    env: Environment, pack: Pack, context: GeneratorContext
) -> list[OutputFile]:
    files: list[OutputFile] = []
    output = pack.manifest.output
    ext = output.extension

    _ROOT_ITEMS = {
        "package.json",
        "index.html",
        "vite.config.ts",
        ".env.example",
        "tsconfig.json",
        "tsconfig.node.json",
        "tailwind.config.js",
        "postcss.config.js",
    }

    roots = {name: _root_node(view, context) for name, view in context.views.items()}
    crud_views = {name for name, root in roots.items() if root.component == "crud"}
    view_entities = {
        name: _resolve_entity(_given(root, context), context, root.component) for name, root in roots.items()
    }

    for item in context.pack_scaffold:
        template_path = f"scaffold/{item}.jinja"
        content = _render(
            env,
            template_path,
            {
                "context": context,
                "views": context.views,
                "entities": context.entities,
                "collections": context.collections,
                "pack_config": context.pack_config,
                "crud_views": crud_views,
                "view_entities": view_entities,
            },
        )
        if content is not None:
            if item in _ROOT_ITEMS:
                out_path = item
            elif "." in item:
                out_path = f"{output.generated_dir}/{item}"
            else:
                out_path = f"{output.generated_dir}/{item}.{ext}"
            files.append(
                OutputFile(
                    path=out_path,
                    content=content,
                    zone="generated",
                )
            )

    return files


def _render_data_layer(
    env: Environment, pack: Pack, context: GeneratorContext
) -> list[OutputFile]:
    files: list[OutputFile] = []
    output = pack.manifest.output
    ext = output.extension

    content = _try_render(
        env,
        "types/index.jinja",
        {
            "context": context,
            "entities": context.entities,
            "collections": context.collections,
            "pack_config": context.pack_config,
        },
    )
    if content is not None:
        files.append(
            OutputFile(
                path=f"{output.generated_dir}/types/index.{ext}",
                content=content,
                zone="generated",
            )
        )

    content = _try_render(
        env,
        "lib/api.jinja",
        {
            "context": context,
            "entities": context.entities,
            "pack_config": context.pack_config,
        },
    )
    if content is not None:
        files.append(
            OutputFile(
                path=f"{output.generated_dir}/lib/api.{ext}",
                content=content,
                zone="generated",
            )
        )

    for col_name, collection in context.collections.items():
        content = _try_render(
            env,
            "hooks/useCollection.jinja",
            {
                "collection": collection,
                "entity": context.entities[collection.entity],
                "context": context,
                "pack_config": context.pack_config,
            },
        )
        if content is not None:
            files.append(
                OutputFile(
                    path=f"{output.hooks_dir}/use{_pascal(col_name)}.{ext}",
                    content=content,
                    zone="generated",
                )
            )

    for entity_name, entity in context.entities.items():
        if not entity.repository_name:
            continue
        content = _try_render(
            env,
            "hooks/useMutation.jinja",
            {
                "entity": entity,
                "context": context,
                "pack_config": context.pack_config,
            },
        )
        if content is not None:
            files.append(
                OutputFile(
                    path=f"{output.hooks_dir}/use{_pascal(entity_name)}Mutation.{ext}",
                    content=content,
                    zone="generated",
                )
            )

    for entity_name in context.identity_entities:
        entity = context.entities.get(entity_name)
        if not entity:
            continue
        content = _try_render(
            env,
            "hooks/useAuth.jinja",
            {
                "entity": entity,
                "context": context,
                "pack_config": context.pack_config,
            },
        )
        if content is not None:
            files.append(
                OutputFile(
                    path=f"{output.hooks_dir}/use{_pascal(entity_name)}Auth.{ext}",
                    content=content,
                    zone="generated",
                )
            )

    return files


CRUD_PAGES = {"list": "", "form": "Form", "detail": "Detail", "delete": "Delete"}
"""The page each `crud` slot renders, named by the suffix it adds to the view's page name."""


def _render_views(
    env: Environment, pack: Pack, context: GeneratorContext
) -> list[OutputFile]:
    output = pack.manifest.output
    return [
        OutputFile(path=f"{output.pages_dir}/{name}.{output.extension}", content=content, zone="editable")
        for view_name, view in context.views.items()
        for name, page, pages in _view_pages(view, context)
        if (content := _render(env, f"components/{page.component}.jinja", _page_variables(view, page, pages, context)))
        is not None
    ]


def _view_pages(
    view: UIView, context: GeneratorContext
) -> list[tuple[str, ComponentNode, dict[str, str] | None]]:
    """Each page file a view renders, with its component and, for a `crud` view, every page of that view."""
    root = _root_node(view, context)
    name = _pascal(view.name)
    if root.component != "crud":
        return [(name, root, None)]
    props = _given(root, context)
    pages = {slot: name + suffix for slot, suffix in CRUD_PAGES.items()}
    return [
        (pages[slot], ComponentNode(slot_node.component, {**props, **slot_node.props}), pages)
        for slot in CRUD_PAGES
        for slot_node in [_slot_node(props[slot])]
    ]


def _page_variables(
    view: UIView, page: ComponentNode, pages: dict[str, str] | None, context: GeneratorContext
) -> dict[str, Any]:
    props = _given(page, context)
    return {
        "view": view,
        "collection": _resolve_collection(props, context),
        "entity": _resolve_entity(props, context, page.component),
        "context": context,
        "pack_config": context.pack_config,
        "component_tree": _build_component_tree(view, context),
        "props": props,
        "pages": pages,
    }


def _root_node(view: UIView, context: GeneratorContext) -> ComponentNode:
    """The pack component a view renders."""
    return _rendered(ComponentNode(view.component, view.props), context)


def _rendered(node: ComponentNode, context: GeneratorContext) -> ComponentNode:
    """`node` itself, or the render root of the declared component it names, `$prop`s bound to `node`'s props."""
    declared = context.components.get(node.component)
    if declared is None:
        return node
    bound = {
        name: node.props.get(value.value) if value.kind == "ref" else value
        for name, value in declared.render.props.items()
    }
    return _rendered(
        ComponentNode(declared.render.component, {name: value for name, value in bound.items() if value}), context
    )


def _slot_node(value: PropValue) -> ComponentNode:
    """The component a `component` prop names, bare or with props of its own."""
    return value.value if value.kind == "component" else ComponentNode(str(value.value), {})


def _given(node: ComponentNode, context: GeneratorContext) -> dict[str, PropValue]:
    """The props `node` passes, over the defaults its pack component declares."""
    declared = context.pack_components[node.component].props.values()
    defaults = {
        prop.name: PropValue("component_ref" if prop.type == "component" else "literal", prop.default)
        for prop in declared
        if prop.default is not None
    }
    return {**defaults, **node.props}


def _resolve_collection(props: dict[str, PropValue], context: GeneratorContext) -> Any:
    for prop_val in props.values():
        if prop_val.kind == "literal" and isinstance(prop_val.value, str):
            col_ref = _parse_collection_ref(prop_val.value)
            if col_ref and col_ref in context.collections:
                return context.collections[col_ref]
    return None


def _resolve_entity(props: dict[str, PropValue], context: GeneratorContext, pack_component: str) -> Any:
    for prop_val in props.values():
        if prop_val.kind == "literal" and isinstance(prop_val.value, str):
            if prop_val.value in context.entities:
                return context.entities[prop_val.value]
    if pack_component.startswith("auth"):
        return next((entity for entity in context.entities.values() if entity.serves_login), None)
    return None


def _build_component_tree(view: UIView, context: GeneratorContext) -> dict[str, Any]:
    """Build a serializable component tree for the template."""
    tree: dict[str, Any] = {"component": view.component, "props": {}}

    yaml_comp = context.components.get(view.component)
    if yaml_comp:
        tree["render"] = _component_node_to_dict(yaml_comp.render)
        tree["declared_props"] = yaml_comp.props

    for prop_name, prop_val in view.props.items():
        tree["props"][prop_name] = _prop_value_to_dict(prop_val)

    return tree


def _component_node_to_dict(node: Any) -> dict[str, Any]:
    from yaml_api_generator.ir.ui import ComponentNode

    if not isinstance(node, ComponentNode):
        return {}
    result: dict[str, Any] = {"component": node.component, "props": {}}
    for prop_name, prop_val in node.props.items():
        result["props"][prop_name] = _prop_value_to_dict(prop_val)
    return result


def _prop_value_to_dict(prop_val: Any) -> dict[str, Any]:
    from yaml_api_generator.ir.ui import PropValue, ComponentNode

    if not isinstance(prop_val, PropValue):
        return {"kind": "literal", "value": prop_val}
    if prop_val.kind == "component" and isinstance(prop_val.value, ComponentNode):
        return {
            "kind": "component",
            "value": _component_node_to_dict(prop_val.value),
        }
    return {"kind": prop_val.kind, "value": prop_val.value}


def _parse_collection_ref(value: str) -> str | None:
    """Extract collection name from reference like 'post-feed' or 'post-feed[id]'."""
    match = re.match(r"^([a-zA-Z0-9_-]+)(?:\[[a-zA-Z0-9_]+\])?$", value)
    if match:
        return match.group(1)
    return None


def _create_jinja_env(templates_dir: Path) -> Environment:
    env = Environment(
        loader=ChoiceLoader([FileSystemLoader(templates_dir), FileSystemLoader(SHARED_TEMPLATES)]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["pascal_case"] = _pascal
    env.filters["camel_case"] = _camel
    env.filters["snake_case"] = _snake
    env.filters["kebab_case"] = _kebab
    return env


def _render(env: Environment, template_path: str, variables: dict[str, Any]) -> str | None:
    """A template the pack declares; blank output means the spec needs no such file."""
    try:
        template = env.get_template(template_path)
    except TemplateNotFound as missing:
        raise ValueError(f"Pack has no template '{missing.name}'") from missing
    content = template.render(**variables)
    return content if content.strip() else None


def _try_render(env: Environment, template_path: str, variables: dict[str, Any]) -> str | None:
    """A data-layer template the pack may omit."""
    if template_path not in env.list_templates():
        return None
    return _render(env, template_path, variables)


def _pascal(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name)
    parts = [
        sub
        for word in parts
        for sub in re.sub(r"([a-z])([A-Z])", r"\1_\2", word).split("_")
    ]
    return "".join(word.capitalize() for word in parts if word)


def _camel(name: str) -> str:
    p = _pascal(name)
    return p[0].lower() + p[1:] if p else ""


def _snake(name: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"[_\-\s]+", "_", s)
    return s.lower()


def _kebab(name: str) -> str:
    return _snake(name).replace("_", "-")
