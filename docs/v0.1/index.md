---
title: v0.1 Documentation
description: Stackform v0.1 specification reference.
---

A v0.1 spec declares MongoDB collections and gets a CRUD API for each of them,
with authentication, roles and access rules. `stackform run` serves it with the
development server, and `stackform build` generates a FastAPI, Django REST
Framework or raw-ASGI backend with the same behaviour.

- [Specification](./specification.md): what each key does, the requests it
  serves and the errors it reports
- [Grammar reference](./grammar-reference.md): every key a v0.1 spec accepts
