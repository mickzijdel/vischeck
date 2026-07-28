"""Tests for bin/screenshot argument validation.

Imported as a module via SourceFileLoader so main() can be driven with a patched
argv without the `uv run --script` shebang installing Playwright. The validation
under test (--selector vs --full-page) runs before any server probe or Playwright
import, so these tests need neither a browser nor a dev server.

Run with: uv run --with pytest pytest tests/
"""

import importlib.machinery
import importlib.util
import re
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


# --- Argument validation that must fail before a browser is launched ---


def test_scroll_and_full_page_are_mutually_exclusive(mod, monkeypatch, capsys):
    """--full-page stitches the whole document, so it cannot show a fixed bar at
    a scroll position — accepting both would silently discard the --scroll."""
    monkeypatch.setattr(
        "sys.argv", ["screenshot", "/x", "--scroll", "bottom", "--full-page"]
    )
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 1
    assert "mutually exclusive" in capsys.readouterr().err


def test_zero_dpr_is_rejected(mod, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["screenshot", "/x", "--dpr", "0"])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 1
    assert "--dpr" in capsys.readouterr().err


def test_malformed_sweep_pair_fails_before_the_server_probe(mod, monkeypatch, capsys):
    """A bad selector pair is caught up front, not after a browser launch."""
    probed = _capture_probe(mod, monkeypatch)
    monkeypatch.setattr("sys.argv", ["screenshot", "/x", "--sweep-pair", ".only-one"])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 1
    assert "--sweep-pair" in capsys.readouterr().err
    assert probed == {}, "argument validation must run before the server probe"


# --- parse_scroll ---


def test_parse_scroll_none_when_unset(mod):
    assert mod.parse_scroll(None) is None


def test_parse_scroll_top_and_bottom(mod):
    assert mod.parse_scroll("top") == "0"
    # Larger than any real document; the browser clamps it to the true maximum.
    assert float(mod.parse_scroll("bottom")) > 1e6


def test_parse_scroll_pixel_offset(mod):
    assert mod.parse_scroll("600") == "600"


def test_parse_scroll_rejects_garbage(mod, capsys):
    with pytest.raises(SystemExit) as exc:
        mod.parse_scroll("halfway")
    assert exc.value.code == 1
    assert "--scroll" in capsys.readouterr().err


# --- parse_pairs ---


def test_parse_pairs_splits_two_selectors(mod):
    assert mod.parse_pairs([".breadcrumb, .artwork"]) == [[".breadcrumb", ".artwork"]]


def test_parse_pairs_empty_without_input(mod):
    assert mod.parse_pairs(None) == []


def test_parse_pairs_rejects_three_selectors(mod):
    with pytest.raises(SystemExit):
        mod.parse_pairs([".a,.b,.c"])


# --- format_sweep: the report an agent actually reads ---


def test_format_sweep_says_clean_when_empty(mod):
    assert "clean" in mod.format_sweep([], 390, 844)


def test_format_sweep_counts_defects_and_leads_separately(mod):
    findings = [
        {"check": "horizontal-overflow", "severity": "defect", "byPx": 34},
        {"check": "small-tap-target", "severity": "lead", "count": 3},
    ]
    report = mod.format_sweep(findings, 390, 844)
    assert "1 defect(s), 1 lead(s)" in report


def test_format_sweep_ranks_defects_above_leads(mod):
    findings = [
        {"check": "small-tap-target", "severity": "lead"},
        {"check": "horizontal-overflow", "severity": "defect"},
    ]
    report = mod.format_sweep(findings, 390, 844)
    assert report.index("horizontal-overflow") < report.index("small-tap-target")


def test_format_sweep_explains_every_check_it_can_emit(mod):
    """Each check name carries a plain-English hint, so a report never lands as a
    bare key the reader has to decode."""
    emitted = set(re.findall(r"check: '([a-z-]+)'", mod.SWEEP_JS))
    assert emitted, "sweep JS should push named checks"
    assert emitted <= set(mod.SWEEP_HINTS), (
        f"checks with no hint: {sorted(emitted - set(mod.SWEEP_HINTS))}"
    )


def test_no_unused_sweep_hints(mod):
    """The reverse guard: a hint left behind after a check is renamed is dead."""
    emitted = set(re.findall(r"check: '([a-z-]+)'", mod.SWEEP_JS))
    assert set(mod.SWEEP_HINTS) <= emitted, (
        f"hints for checks that no longer exist: {sorted(set(mod.SWEEP_HINTS) - emitted)}"
    )
