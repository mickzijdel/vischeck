"""Tests for the pure parsing/resolution logic of bin/screenshots.

bin/screenshots has no .py extension, so it is imported as a module via
SourceFileLoader. The `if __name__ == "__main__"` guard means importing it does
not run main(), so these tests never touch a browser or a dev server.

Run with: uv run --with pytest,pyyaml pytest tests/
"""

import importlib.machinery
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "screenshots"


def load_screenshots_module():
    loader = importlib.machinery.SourceFileLoader("screenshots", str(SCRIPT))
    spec = importlib.util.spec_from_loader("screenshots", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return load_screenshots_module()


def make_args(mod, **overrides):
    """A minimal args namespace with the attributes build_command reads."""
    defaults = dict(
        dark=False,
        full_page=False,
        no_auth=False,
        width=None,
        height=None,
        port=None,
        auth_url=None,
        host=mod.DEFAULT_HOST,
        wait=mod.DEFAULT_WAIT_MS,
        selector=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# --- selector survives entry parsing (it's in ENTRY_KEYS) ---


def test_selector_in_entry_keys(mod):
    assert "selector" in mod.ENTRY_KEYS


def test_parse_entries_keeps_selector(mod):
    entries = mod.parse_entries(
        [{"path": "/signup", "selector": ".signup-form"}], SCRIPT, "test"
    )
    assert entries == [{"path": "/signup", "selector": ".signup-form"}]


# --- resolve() precedence for the selector key ---


def test_selector_per_entry_beats_cli(mod):
    val = mod.resolve({"selector": ".per-entry"}, "selector", {}, ".cli", None, None)
    assert val == ".per-entry"


def test_selector_cli_used_when_entry_absent(mod):
    val = mod.resolve({}, "selector", {}, ".cli", None, None)
    assert val == ".cli"


def test_selector_default_none(mod):
    assert mod.resolve({}, "selector", {}, None, None, None) is None


# --- build_command emits --selector only when one is resolved ---


def test_build_command_appends_selector_from_entry(mod):
    cmd, _ = build(mod, entry={"path": "/", "selector": ".card"})
    assert "--selector" in cmd
    assert cmd[cmd.index("--selector") + 1] == ".card"


def test_build_command_appends_selector_from_cli(mod):
    cmd, _ = build(mod, entry={"path": "/"}, args_overrides={"selector": ".cli-card"})
    assert cmd[cmd.index("--selector") + 1] == ".cli-card"


def test_build_command_omits_selector_when_none(mod):
    cmd, _ = build(mod, entry={"path": "/"})
    assert "--selector" not in cmd


def test_selector_suppresses_full_page(mod):
    # A global full_page default + a selector must NOT emit both flags (the child
    # rejects them as mutually exclusive). Selector wins.
    cmd, _ = build(
        mod,
        entry={"path": "/"},
        args_overrides={"selector": ".card"},
        globals_dict={"full_page": True},
    )
    assert "--full-page" not in cmd
    assert cmd[cmd.index("--selector") + 1] == ".card"


def build(mod, entry, group_defaults=None, args_overrides=None, globals_dict=None):
    return mod.build_command(
        "screenshot",
        entry,
        group_defaults or {},
        Path("/tmp/out.png"),
        make_args(mod, **(args_overrides or {})),
        globals_dict or {},
    )


# --- parse_entries(raw_list, config_path, source_desc) ---


def test_parse_entries_string_entry(mod):
    assert mod.parse_entries(["/foo"], SCRIPT, "test") == [{"path": "/foo"}]


def test_parse_entries_mapping_keeps_only_entry_keys(mod):
    # `dark` is an ENTRY_KEY and is kept; `bogus` is outside ENTRY_KEYS and dropped.
    entries = mod.parse_entries(
        [{"path": "/foo", "dark": True, "bogus": "x"}], SCRIPT, "test"
    )
    assert entries == [{"path": "/foo", "dark": True}]


def test_parse_entries_mapping_without_path_exits(mod):
    with pytest.raises(SystemExit) as exc:
        mod.parse_entries([{"dark": True}], SCRIPT, "test")
    assert exc.value.code == 1


def test_parse_entries_non_string_non_mapping_exits(mod):
    with pytest.raises(SystemExit) as exc:
        mod.parse_entries([42], SCRIPT, "test")
    assert exc.value.code == 1


# --- load_config(config_path) -> (globals_dict, default_entries, groups) ---


def write_config(tmp_path, text):
    path = tmp_path / "screenshots.yml"
    path.write_text(text)
    return path


def test_load_config_pages_only(mod, tmp_path):
    path = write_config(tmp_path, "pages:\n  - /\n  - /news\n")
    globals_dict, default_entries, groups = mod.load_config(path)
    assert default_entries == [{"path": "/"}, {"path": "/news"}]
    assert groups == {}


def test_load_config_groups_only_no_error(mod, tmp_path):
    # Regression guard: the pre-groups version errored when `pages:` was absent.
    path = write_config(tmp_path, "groups:\n  smoke:\n    - /\n    - /shows\n")
    globals_dict, default_entries, groups = mod.load_config(path)
    assert default_entries is None
    assert "smoke" in groups
    assert groups["smoke"]["entries"] == [{"path": "/"}, {"path": "/shows"}]


def test_load_config_both_pages_and_groups(mod, tmp_path):
    path = write_config(tmp_path, "pages:\n  - /\ngroups:\n  smoke:\n    - /shows\n")
    globals_dict, default_entries, groups = mod.load_config(path)
    assert default_entries == [{"path": "/"}]
    assert "smoke" in groups


def test_load_config_neither_pages_nor_groups_exits(mod, tmp_path):
    path = write_config(tmp_path, "port: 3000\ndark: true\n")
    with pytest.raises(SystemExit) as exc:
        mod.load_config(path)
    assert exc.value.code == 1


def test_load_config_empty_file_exits(mod, tmp_path):
    path = write_config(tmp_path, "")
    with pytest.raises(SystemExit) as exc:
        mod.load_config(path)
    assert exc.value.code == 1


def test_load_config_bare_list_exits(mod, tmp_path):
    path = write_config(tmp_path, "- /\n- /news\n")
    with pytest.raises(SystemExit) as exc:
        mod.load_config(path)
    assert exc.value.code == 1


def test_load_config_collects_globals(mod, tmp_path):
    path = write_config(tmp_path, "port: 4000\ndark: true\nwidth: 800\npages:\n  - /\n")
    globals_dict, _, _ = mod.load_config(path)
    assert globals_dict == {"port": 4000, "dark": True, "width": 800}


def test_load_config_group_list_form(mod, tmp_path):
    path = write_config(tmp_path, "groups:\n  smoke:\n    - /\n    - /shows\n")
    _, _, groups = mod.load_config(path)
    assert groups["smoke"] == {
        "defaults": {},
        "entries": [{"path": "/"}, {"path": "/shows"}],
    }


def test_load_config_group_mapping_form(mod, tmp_path):
    path = write_config(
        tmp_path,
        "groups:\n"
        "  admin:\n"
        "    dark: true\n"
        "    auth_url: /x\n"
        "    pages:\n"
        "      - /admin\n"
        "      - /admin/users\n",
    )
    _, _, groups = mod.load_config(path)
    assert groups["admin"]["defaults"] == {"dark": True, "auth_url": "/x"}
    assert groups["admin"]["entries"] == [{"path": "/admin"}, {"path": "/admin/users"}]


def test_load_config_group_mapping_without_pages_exits(mod, tmp_path):
    path = write_config(tmp_path, "groups:\n  admin:\n    dark: true\n")
    with pytest.raises(SystemExit) as exc:
        mod.load_config(path)
    assert exc.value.code == 1


def test_load_config_group_scalar_value_exits(mod, tmp_path):
    path = write_config(tmp_path, "groups:\n  admin: just-a-string\n")
    with pytest.raises(SystemExit) as exc:
        mod.load_config(path)
    assert exc.value.code == 1


def test_load_config_groups_not_a_mapping_exits(mod, tmp_path):
    path = write_config(tmp_path, "groups:\n  - /\n  - /shows\n")
    with pytest.raises(SystemExit) as exc:
        mod.load_config(path)
    assert exc.value.code == 1


# --- resolve() precedence, most specific first ---


def test_resolve_per_entry_beats_group_default(mod):
    assert (
        mod.resolve({"k": "entry"}, "k", {"k": "group"}, "cli", "glob", "def")
        == "entry"
    )


def test_resolve_group_default_beats_cli(mod):
    assert mod.resolve({}, "k", {"k": "group"}, "cli", "glob", "def") == "group"


def test_resolve_cli_beats_global(mod):
    assert mod.resolve({}, "k", {}, "cli", "glob", "def") == "cli"


def test_resolve_global_beats_default(mod):
    assert mod.resolve({}, "k", {}, None, "glob", "def") == "glob"


def test_resolve_falls_back_to_default(mod):
    assert mod.resolve({}, "k", {}, None, None, "def") == "def"


# --- path_to_filename(path, dark) ---


def test_path_to_filename_home(mod):
    assert mod.path_to_filename("/", dark=False) == "home.png"


def test_path_to_filename_nested(mod):
    assert mod.path_to_filename("/a/b", dark=False) == "a__b.png"


def test_path_to_filename_dark_suffix(mod):
    assert mod.path_to_filename("/shows", dark=True) == "shows_dark.png"


# --- Driving main() for dedup + CLI selection (no live server needed) ---


def run_main(mod, monkeypatch, tmp_path, config_text, argv, server_up=True):
    """Run main() in tmp_path against a written config, mocking the server probe
    and the per-page subprocess so nothing touches a browser or a real server."""
    import socket
    import subprocess
    import sys

    write_config(tmp_path, config_text)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["screenshots", *argv])

    if server_up:

        class _Sock:
            def close(self):
                pass

        monkeypatch.setattr(socket, "create_connection", lambda *_a, **_k: _Sock())
    else:

        def _refuse(*_a, **_k):
            raise ConnectionRefusedError

        monkeypatch.setattr(socket, "create_connection", _refuse)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    with pytest.raises(SystemExit) as exc:
        mod.main()
    return exc.value.code


# --- Selection dedup ---


def test_dedup_same_path_across_groups_one_job(mod, monkeypatch, tmp_path, capsys):
    config = "groups:\n  a:\n    - /shows\n  b:\n    - /shows\n"
    run_main(mod, monkeypatch, tmp_path, config, ["--all"])
    out = capsys.readouterr().out
    assert "Capturing 1 page(s) with" in out


def test_light_vs_dark_same_path_not_deduped(mod, monkeypatch, tmp_path, capsys):
    config = "groups:\n  a:\n    - /shows\n  b:\n    - path: /shows\n      dark: true\n"
    run_main(mod, monkeypatch, tmp_path, config, ["--all"])
    out = capsys.readouterr().out
    assert "Capturing 2 page(s) with" in out


# --- CLI selection (exits before preflight, so no server needed) ---


def test_list_prints_group_names_and_counts(mod, monkeypatch, tmp_path, capsys):
    config = "groups:\n  smoke:\n    - /\n    - /shows\n  admin:\n    - /admin\n"
    code = run_main(mod, monkeypatch, tmp_path, config, ["--list"], server_up=False)
    out = capsys.readouterr().out
    assert code == 0
    assert "smoke  (2 page(s))" in out
    assert "admin  (1 page(s))" in out


def test_unknown_group_errors_and_lists_available(mod, monkeypatch, tmp_path, capsys):
    config = "groups:\n  smoke:\n    - /\n"
    code = run_main(
        mod, monkeypatch, tmp_path, config, ["--group", "nope"], server_up=False
    )
    err = capsys.readouterr().err
    assert code == 1
    assert "not found" in err
    assert "smoke" in err


def test_group_flag_with_no_groups_config_exits(mod, monkeypatch, tmp_path, capsys):
    config = "pages:\n  - /\n"
    code = run_main(
        mod, monkeypatch, tmp_path, config, ["--group", "x"], server_up=False
    )
    assert code == 1
    assert "no 'groups:'" in capsys.readouterr().err


def test_all_flag_with_no_groups_config_exits(mod, monkeypatch, tmp_path, capsys):
    config = "pages:\n  - /\n"
    code = run_main(mod, monkeypatch, tmp_path, config, ["--all"], server_up=False)
    assert code == 1
    assert "no 'groups:'" in capsys.readouterr().err


def test_groups_only_config_no_selection_lists_and_exits(
    mod, monkeypatch, tmp_path, capsys
):
    config = "groups:\n  smoke:\n    - /\n"
    code = run_main(mod, monkeypatch, tmp_path, config, [], server_up=False)
    err = capsys.readouterr().err
    assert code == 1
    assert "Available groups" in err
    assert "smoke" in err


def test_group_comma_and_repeat_flatten_identically(mod, monkeypatch, tmp_path, capsys):
    config = "groups:\n  a:\n    - /a\n  b:\n    - /b\n"
    run_main(mod, monkeypatch, tmp_path, config, ["--group", "a,b"])
    comma = capsys.readouterr().out
    run_main(mod, monkeypatch, tmp_path, config, ["--group", "a", "--group", "b"])
    repeat = capsys.readouterr().out
    assert "Capturing a, b (2 page(s) before dedup)" in comma
    assert "Capturing a, b (2 page(s) before dedup)" in repeat
