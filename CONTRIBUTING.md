# Contributing to Stackform

Thank you for your interest in Stackform. Bug reports, documentation fixes and code changes are all
welcome. This guide explains how to get in touch, how to set up a development environment, and what
a pull request needs before it can be merged.

For what Stackform does and how to use it, read the [README](README.md) and the
[manual](https://sebastiaoteixeira.github.io/yaml-framework-docs/).

## Questions, bugs and ideas

All conversation happens in [GitHub issues](https://github.com/ieeta-pt/stackform/issues). Search
the open and closed issues first; your question or bug may already have an answer.

- **Questions.** Open an issue and describe what you are trying to do.
- **Bug reports.** Include:
  - the Stackform commit or version and your Python version;
  - the smallest YAML spec that reproduces the problem, including its `version:` line;
  - the exact command you ran (for example `stackform build spec.yaml --target drf`);
  - what you expected and what happened, with the full error output.
- **Feature proposals.** Describe the problem first, then the change you suggest. For a change to
  the specification language, show the YAML a user would write.

## Before you write code

Small fixes such as typos, broken links or an obvious one-line bug can go straight to a pull
request. For anything larger, open an issue first and wait for a maintainer to agree on the
approach. This applies in particular to new spec keys or changes to existing ones, which every
backend target has to support. Issues labelled
[`good first issue`](https://github.com/ieeta-pt/stackform/labels/good%20first%20issue) or
[`help wanted`](https://github.com/ieeta-pt/stackform/labels/help%20wanted) are open for anyone to
take; leave a comment saying you are working on one.

## Development setup

You need:

- Python 3.11 or newer (CI tests 3.11 and 3.13);
- [uv](https://docs.astral.sh/uv/), which installs the locked dependencies;
- Docker, for the integration tests;
- Node.js 18 or newer, only for frontend generation and the tests that run generated frontend code.

Fork the repository, then clone your fork and install the project with its development
dependencies:

```bash
git clone https://github.com/<your-username>/stackform.git
cd stackform
uv sync --all-extras
```

The `stackform` command is now available through `uv run`:

```bash
uv run stackform --help
```

## Running the tests

The suite has two parts. Tests marked `integration` start real services; everything else runs
without them.

Run the unit suite, as CI does:

```bash
uv run pytest -m "not integration"
```

Run the integration suite:

```bash
uv run pytest -m integration
```

Each integration test starts a throwaway Docker container for the service it needs (`mongo:7`,
`postgres:16` or `minio/minio`). To use a service you already run, set its environment variable
instead:

| Service    | Variable                     |
| ---------- | ---------------------------- |
| MongoDB    | `YAML_API_TEST_MONGO_URI`    |
| PostgreSQL | `YAML_API_TEST_POSTGRES_URI` |
| S3 (MinIO) | `YAML_API_TEST_S3_ENDPOINT`  |

Some tests are skipped instead of failing when a tool is missing:

- without Docker and without the variable above, the tests that need that service;
- without `node` or `npm` on the `PATH`, the tests that run generated frontend code;
- without `YAML_API_TEST_DRF_PYTHON`, the tests that serve a generated Django REST Framework
  backend. Set it to a Python interpreter that has the generated DRF project's requirements
  installed.

CI runs only the unit suite. If your change touches generated backends, datastores or
authentication, run the integration suite locally as well.

To run one file or one test, pass it to pytest as usual:

```bash
uv run pytest tests/unit/test_parser.py -k <name>
```

## Where things live

| Path                                     | Contents                                                   |
| ---------------------------------------- | ---------------------------------------------------------- |
| `src/yaml_api_generator/cli/`            | The `stackform` command                                    |
| `src/yaml_api_generator/parsers/`        | Spec loading and validation; JSON Schemas in `schemas/`    |
| `src/yaml_api_generator/ir/`             | The intermediate representation the generators consume     |
| `src/yaml_api_generator/generators/`     | `backend/` (`fastapi`, `drf`, `raw`), `frontend/`, `deploy/` |
| `src/yaml_api_generator/server/`         | The development server behind `stackform run`              |
| `src/yaml_api_generator/runtime/`        | Modules shared by the development server and generated applications |
| `tests/unit/`, `tests/integration/`      | The two test suites                                        |
| `tests/fixtures/valid/`, `tests/fixtures/invalid/` | Specs that must load and specs that must be rejected |
| `examples/`                              | Example specs, grouped by spec version                     |
| `docs/`                                  | The manual, one directory per spec version                 |

The Python package keeps the name `yaml_api_generator`; the distribution and the command are
named `stackform`.

## Changing the specification language

A spec file selects its grammar with its `version:` key. Each version has a JSON Schema in
`src/yaml_api_generator/parsers/schemas/` (for example `yaml-spec-v0.3.schema.json`). A pull
request that adds or changes a spec key carries:

- the schema change and the parser change for the affected version;
- a spec in `tests/fixtures/valid/` that uses the key, and specs in `tests/fixtures/invalid/` for
  each way it can be misused, with unit tests that load them;
- the generator change for every backend target that supports the feature;
- the manual page for the key in `docs/<version>/`, and an entry in that version's
  `grammar-reference.md`.

## Documentation

The manual is written in Markdown under `docs/`, with one directory per spec version. Each page
starts with front matter that sets `title` and `description`, and each directory's `meta.json`
sets the page order. When you add a page, add it to `meta.json`.

The site is built with Fumadocs from the separate
[yaml-framework-docs](https://github.com/sebastiaoteixeira/yaml-framework-docs) repository. A push
to `main` that changes `docs/` triggers a rebuild. To preview your changes locally, clone that
repository next to this one and link the content in:

```bash
git clone https://github.com/sebastiaoteixeira/yaml-framework-docs.git
cd yaml-framework-docs
mkdir -p content
ln -s "$(pwd)/../stackform/docs" content/docs
npm install
npm run dev
```

The site is then served at <http://localhost:3000/yaml-framework-docs/docs>.

## Pull requests

1. Create a branch named `<type>/<short-description>`, where the type is `feat`, `fix`, `docs`,
   `refactor`, `ci` or `chore`. If the branch implements an issue, put its number after the type,
   for example `feat/83-pagination`.
2. Keep each pull request to one change. Unrelated fixes go in separate pull requests.
3. Add or update tests for the behaviour you change, and update the manual if users will notice
   the change.
4. Run the unit suite, and the integration suite where it applies.
5. Open the pull request against `main`. In the description, say what changes and how you tested
   it, and link the issue it resolves (for example `Closes #83`).

Pull requests are squash-merged, so the pull request title becomes the commit message on `main`.
Write the title as a single sentence in the imperative mood that states the change, without a type
prefix or a trailing period. For example:

- `Reject deploy build contexts that enclose the spec or output directory`
- `Await pymongo async aggregate and list_indexes cursors`
- `Add file datastores and file field type`

No formatter or linter is enforced; follow the style of the code around your change.

CI runs the unit suite on Python 3.11 and 3.13 for every pull request. A maintainer reviews the pull
request once CI passes and may ask for changes before merging.

## Licence

Stackform is released under the [MIT License](LICENSE.txt). By submitting a contribution, you agree
that it is licensed under the same terms.
