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
