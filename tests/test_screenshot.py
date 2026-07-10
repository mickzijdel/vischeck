"""Tests for bin/screenshot argument validation.

Imported as a module via SourceFileLoader so main() can be driven with a patched
argv without the `uv run --script` shebang installing Playwright. The validation
under test (--selector vs --full-page) runs before any server probe or Playwright
import, so these tests need neither a browser nor a dev server.

Run with: uv run --with pytest pytest tests/
"""

import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "screenshot"


def load_screenshot_module():
    loader = importlib.machinery.SourceFileLoader("screenshot", str(SCRIPT))
    spec = importlib.util.spec_from_loader("screenshot", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return load_screenshot_module()


def test_selector_and_full_page_are_mutually_exclusive(mod, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv", ["screenshot", "/x", "--selector", ".card", "--full-page"]
    )
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 1
    assert "mutually exclusive" in capsys.readouterr().err


def _capture_probe(mod, monkeypatch):
    """Stub the server preflight so main() exits before Playwright, recording host/port."""
    captured = {}

    def fake_check(host, port):
        captured["host"], captured["port"] = host, port
        return False  # a "down" server aborts with exit 1, before any browser work

    monkeypatch.setattr(mod, "check_server", fake_check)
    return captured


def test_port_defaults_to_env_PORT(mod, monkeypatch):
    """With no --port, the dev-server port comes from $PORT (set per-worktree via mise)."""
    captured = _capture_probe(mod, monkeypatch)
    monkeypatch.setenv("PORT", "4321")
    monkeypatch.setattr("sys.argv", ["screenshot", "/x"])
    with pytest.raises(SystemExit):
        mod.main()
    assert captured["port"] == 4321


def test_explicit_port_overrides_env_PORT(mod, monkeypatch):
    captured = _capture_probe(mod, monkeypatch)
    monkeypatch.setenv("PORT", "4321")
    monkeypatch.setattr("sys.argv", ["screenshot", "/x", "--port", "5000"])
    with pytest.raises(SystemExit):
        mod.main()
    assert captured["port"] == 5000


def test_port_falls_back_to_3000_without_env(mod, monkeypatch):
    captured = _capture_probe(mod, monkeypatch)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setattr("sys.argv", ["screenshot", "/x"])
    with pytest.raises(SystemExit):
        mod.main()
    assert captured["port"] == 3000
