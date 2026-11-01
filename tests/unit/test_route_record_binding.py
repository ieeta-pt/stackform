"""A bare document binding on a route that runs no CRUD operation needs a record parameter in the route path."""

import pytest

from yaml_api_generator.parsers.yaml_parser import ConfigErrors, load_and_generate_ir

SPEC = """
version: "{version}"
api:
  basePath: /api
mongo: {{ uri: "mongodb://localhost", database: blog }}
entities:
  user:
    type: auth
    auth: {{ identifier: email, via: password }}
    fields:
      id: {{ type: id }}
      email: {{ type: string, required: true, unique: true }}
  post:
    fields:
      id: {{ type: id }}
      ownerId: {{ type: string }}
repositories:
  users: {{ entity: user }}
  posts:
    entity: post
    operations:
      recent:
        query: {{ command: find, filter: {{}} }}
services:
  users: {{ repository: users }}
  recent: {{ repository: posts, operation: recent }}
controllers:
  users: {{ service: users, base_path: /users, access: public }}
  feeds:
    base_path: /feeds
    routes:
      recent:
        service: recent
        method: GET
        path: /recent
        access:
          - given: {{ principal: "identity:user", document: posts }}
            when: document.ownerId equals principal.sub
"""

@pytest.mark.parametrize("version", ["0.2", "0.3"])
def test_route_without_a_record_parameter_is_refused(tmp_path, version):
    spec = tmp_path / "spec.yaml"
    spec.write_text(SPEC.format(version=version))

    with pytest.raises(ConfigErrors) as raised:
        load_and_generate_ir(spec)

    assert [(error.code, error.message) for error in raised.value.errors] == [(
        "DOCUMENT_BINDING_INVALID",
        "'posts' binds the route's record, but the route path has no record parameter",
    )]
