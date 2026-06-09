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
