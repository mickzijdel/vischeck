Make sure to check all of the following and make sure they are up-to-date after making changes;
1. tool-specific documentation for tools you edited
2. skills for tools you edited
3. plugin.json
4. README.md
5. CLAUDE.md
6. tests/ — keep the pytest suite green and add coverage for behaviour you change

Bump the plugin version on every commit. Patch version for small fixes, minor version for more substantial changes (new skill or tool).

# Development

Tooling is managed by **mise** + **hk** (dev-hooks:dev-env-setup standard v9). Tools are
spec'd `"latest"` in `mise.toml` and pinned in the committed `mise.lock`.

- `mise install` — provision the toolchain (hk, gitleaks, shellcheck, shfmt, uv, ruff, node).
- `hk install` — install the git pre-commit hook (runs the linters + gitleaks + large-file check,
  plus the dead-code `vulture` and duplication `jscpd` audits — both fast enough for every commit;
  `jscpd` tracks latest on a 4-day cooldown floored at v5, and degrades gracefully when the npm
  registry is unreachable so offline commits aren't blocked).
- `hk run check` — full check (same set as pre-commit under one name); this is what CI runs.
- `uv run pytest` — run the test suite in `tests/` (each bundled script is exercised as a subprocess).

**Linting covers the extensionless `bin/` scripts** via shebang detection: `bin/vischeck-hook`
(bash) → `shellcheck`/`shfmt`; `bin/screenshot`, `bin/screenshots` (PEP 723 Python) → `ruff`.
No glob tweaks needed when adding a new `bin/` script.

**Key packages / versions:** the `bin/` Python scripts are PEP 723 (`requires-python >= 3.11`),
deps unpinned (latest via `uv`): `bin/screenshot` → Playwright, `bin/screenshots` → PyYAML.
Dev toolchain versions are pinned in `mise.lock`. Keep this list and README's "Built with" in
sync with `mise.lock` / the scripts' PEP 723 blocks when they change.