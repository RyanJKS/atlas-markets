# Contributing

Follow the setup steps in [README.md](README.md), including `pre-commit install`.

1. Create a branch from `main` with a descriptive name.
2. Keep changes focused and add tests for new behavior when applicable.
3. Run `uv run pre-commit run --all-files`, `uv run ruff check .`,
   `uv run ruff format --check .`, `uv run pytest`, and
   `python -m compileall -q services packages`.
4. Update documentation and the changelog when behavior or setup changes.
5. Open a pull request describing the problem, changes, and validation.

Use clear commit messages. Never commit secrets, local environment files, or infrastructure state. Document new configuration with safe example values.

Keep service business logic local. Add shared infrastructure code under `packages/`
only when multiple services need it. Document interfaces under `contracts/`. Commit
`uv.lock` whenever manifests change. See [development](docs/development.md) for service
creation and TechDocs checks.

To update hook versions, run `uv run pre-commit autoupdate`, align the Ruff dependency
in `pyproject.toml`, run all checks, and review the resulting changes before committing.
