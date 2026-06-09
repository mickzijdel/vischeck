# Tests to add for `bin/screenshots`

`tests/test_screenshots.py` now covers the selector overrides and a few resolve/parse
cases. This file lists the **remaining** tests that should be written for the batch tool
— especially the **reusable groups** feature — so the pure parsing/resolution logic is
covered without needing a live dev server.

## Harness

`bin/screenshots` has no `.py` extension, so import it as a module via
`importlib.util` + `SourceFileLoader`:

```python
import importlib.util
from pathlib import Path

def load_screenshots_module():
    path = Path(__file__).resolve().parent.parent / "bin" / "screenshots"
    spec = importlib.util.spec_from_loader("screenshots", importlib.machinery.SourceFileLoader("screenshots", str(path)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
```

The `if __name__ == "__main__"` guard means importing it does **not** run `main()`.
Functions that call `sys.exit(1)` on bad input should be asserted with
`pytest.raises(SystemExit)`. Write config files into `tmp_path` and `chdir` there
(or pass an explicit path to `load_config`).

Run with: `uv run --with pytest,pyyaml pytest tests/`

## Cases

### `parse_entries(raw_list, config_path, source_desc)`
- String entry `"/foo"` → `{"path": "/foo"}`.
- Mapping entry with overrides → `{"path", ...only ENTRY_KEYS that were present}`;
  keys outside `ENTRY_KEYS` are dropped.
- Mapping without a `path:` key → `SystemExit` (exit 1).
- Non-string / non-mapping entry (e.g. `42`) → `SystemExit`.

### `load_config(config_path)` → `(globals_dict, default_entries, groups)`
- Top-level `pages:` only → `default_entries` populated, `groups == {}`.
- `groups:` only (no `pages:`) → `default_entries is None`, groups populated, **no error**
  (regression guard: the pre-groups version errored when `pages:` was absent).
- Both `pages:` and `groups:` present → both populated.
- Neither `pages:` nor `groups:` (e.g. only globals) → `SystemExit`.
- Empty / non-mapping YAML (e.g. a bare list or empty file) → `SystemExit`.
- Top-level globals (`port` + `ENTRY_KEYS`) collected into `globals_dict`.
- Group **list form** → `{"defaults": {}, "entries": [...]}`.
- Group **mapping form** with group-level keys → `defaults` holds those `ENTRY_KEYS`,
  `entries` parsed from its `pages:`.
- Group mapping form **without `pages:`** → `SystemExit`.
- Group value that is neither list nor mapping (e.g. a string) → `SystemExit`.
- `groups:` that is not a mapping (e.g. a list) → `SystemExit`.

### `resolve(entry, key, group_defaults, cli_value, global_value, default)`
Precedence, most specific first — assert each layer wins over the ones below it:
1. per-entry `entry[key]`
2. `group_defaults[key]`
3. `cli_value` (when not None)
4. `global_value` (when not None)
5. `default`
Specifically: a per-entry value beats a group default; a group default beats a CLI
value; a CLI value beats a top-level global; the built-in default is the fallback.

### Filename + dedup
- `path_to_filename("/", dark=False) == "home.png"`; `"/a/b"` → `"a__b.png"`;
  `dark=True` appends `_dark`.
- Selection dedup: two selected groups sharing a path that resolves to the same
  filename produce **one** job (first occurrence wins). A same-path light vs dark
  pair (`shows.png` vs `shows_dark.png`) is **not** deduped (distinct filenames).

### CLI selection (integration-ish, no server needed if it exits before preflight)
- `--list` on a config with groups → prints group names + counts, exit 0.
- `--group <unknown>` → error naming available groups, exit 1.
- `--group` / `--all` on a config with **no** `groups:` → exit 1.
- No paths, no `--group`, groups-only config → lists groups, exit 1 (never guesses).
- `--group a,b` and `--group a --group b` both flatten to the same name list.

> Note: cases that reach the server preflight (`socket.create_connection`) need a
> listener or should be asserted only up to the point of selection. Prefer testing
> the pure helpers directly over driving `main()` end-to-end.
