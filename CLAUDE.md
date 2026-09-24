Make sure to check all of the following and make sure they are up-to-date after making changes;
1. tool-specific documentation for tools you edited
2. skills for tools you edited
3. plugin.json
4. README.md
5. CLAUDE.md
6. tests/ — keep the pytest suite green and add coverage for behaviour you change

Bump the plugin version on every commit. Patch version for small fixes, minor version for more substantial changes (new skill or tool).

# Development

Tooling is managed by **mise** + **hk** (dev-hooks:dev-env-setup standard v26). Tools are
spec'd `"latest"` in `mise.toml` and pinned in the committed `mise.lock`.

- `mise install` — provision the toolchain (hk, gitleaks, shellcheck, shfmt, python, uv, ruff, node). `uv run` uses mise's Python (the `UV_PYTHON_*` settings in `mise.toml` [env]), and CI installs the same locked release via mise-action.
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

## The measurement sweep

`bin/screenshot --sweep` injects `SWEEP_JS` into the page and reports numeric layout
violations. Two invariants to preserve when touching it:

1. **Every check emitted by `SWEEP_JS` needs an entry in `SWEEP_HINTS`,** and vice versa.
   `tests/test_screenshot.py` greps the JS for `check: '...'` and asserts the two sets match
   exactly, so a renamed check fails the suite rather than printing a bare key.
2. **Severity is not cosmetic.** A check driven by a caller-supplied selector emits
   `severity: 'defect'` (the intended layout was declared, so the number is a verdict);
   an auto-detected or inherently ambiguous one emits `'lead'` (confirm by eye first).
   New checks must pick one deliberately — grading everything `defect` is what turns a
   useful report into noise that gets ignored.

The sweep is verified against the fixtures in
[HartreeWorks/skill--visual-review](https://github.com/HartreeWorks/skill--visual-review)
(`test-fixtures/`, with a ground-truth `GRADING-KEY.md` of ten planted defects). Serve that
directory over HTTP and sweep it after changing `SWEEP_JS`:

```bash
cd <fixtures>; python3 -m http.server 8899 &
screenshot /podcasts.html --port 8899 --no-auth --width 390 --height 640 --scroll bottom \
  --sweep --sweep-rows ".list" --sweep-full-width ".progwrap" --sweep-pair ".section-head,.row"
screenshot /settings.html --port 8899 --no-auth --width 390 --height 844 \
  --sweep --sweep-rows ".card" --sweep-align ".label"
```

All ten defects (P1–P6, S1–S4) must still be reported. Two of them only appear at a **short**
viewport scrolled to the bottom — a regression there is invisible at the default size.