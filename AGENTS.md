# AGENTS.md

Steering for AI agents working in this repo.

## Repo conventions

- Each command group lives in its own `src/circle_so/commands/*.py` module with a `register(group)` function that does `group.add_command(...)` for each `@click.command()`-decorated function. Register new groups in `cli.py`: define the `@main.group()` stub, import `register_x`, call `register_x(x)`.
- `pass_config = click.make_pass_decorator(Config)` at the top of every command module; commands take `config` as their first arg and call `config.get_client()` (Admin API) or authenticate headless per-command (see `chat.py`'s `_get_headless` helper) for user-scoped operations.
- Always `client.close()` at the end of a command that opens one.
- This CLI is built on [circle-so-python-sdk](https://github.com/boiyelove/circle-so-python-sdk) -- read that repo's `AGENTS.md` and `docs/limitations.md` before writing anything that touches posts, comments, mentions, or polls. Most surprises here are documented platform limitations, not bugs to work around cleverly.
- `docs/ROADMAP.md` has a **Non-Goals** section -- check it before adding a new command group. If what you're building conflicts with a stated non-goal, that's a signal to check with the user before proceeding, not to silently override the doc. If you do proceed with explicit sign-off, update the doc in the same commit so it stays truthful (this is exactly what happened when `posts` was added despite "Content creation ... workflows" being a listed non-goal -- the doc was narrowed to "full content-authoring workflows," not deleted).

## Testing

- Unit tests (`tests/*.py`) use `CliRunner` from `click.testing` and, for commands that hit the API, a monkeypatched `Config.get_client` returning a small fake object (see `tests/test_posts_cli.py`'s `FakeClient`/`FakePostsClient` for the pattern) -- no real network calls. Run: `pytest tests/ -v --ignore=tests/integration`.
- Integration tests (`tests/integration/*.py`) hit the real Circle API via the actual CLI (`CliRunner().invoke(main, [...])`), gated by `requires_circle` (skips if `CIRCLE_API_TOKEN` isn't set), matching the SDK's pattern. Run: `pytest tests/integration/ -m integration`.
- **CKAD 030 (space_id `1761803`) is the designated safe space for write-path integration tests** against the live Andela Learning Community. Never write-test against any other space. Always clean up what you create.
- CI runs `pytest tests/ -v --ignore=tests/integration` -- integration tests never run in CI (no `CIRCLE_API_TOKEN` secret configured there by design). Don't remove the `--ignore` flag without setting that up deliberately.

## Local dev against an unreleased SDK version

If you're testing CLI changes that depend on an SDK fix not yet published to PyPI, editable-install both from sibling checkouts:

```bash
pip install -e ../circle-so-python-sdk -e .
```

`pyproject.toml`'s `circle-so-python-sdk>=X.Y.Z` floor should match the minimum SDK version your change actually needs -- bump it in the same commit, and note in your summary to the user that CI/PyPI installs will fail until that SDK version is actually released (cutting a GitHub Release on the SDK repo triggers its PyPI publish).

## Release process

- Bump `version` in `pyproject.toml`.
- No separate `CHANGELOG.md` -- `docs/ROADMAP.md` is the closest thing; check off completed items there in the same commit.
- Conventional commit format (`feat(scope): ...`, `fix(scope): ...`).
