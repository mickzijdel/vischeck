"""Tests for bin/vischeck-hook (the PostToolUse view-detection hook).

The hook reads a PostToolUse JSON payload on stdin and, when the edited file
looks like a view/template, prints a JSON reminder to invoke vischeck:verify.
These tests drive it as a black box via subprocess, asserting on stdout.

Requires `jq` on PATH (the hook uses it to parse its input).

Run with: uv run --with pytest pytest tests/
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "bin" / "vischeck-hook"

pytestmark = pytest.mark.skipif(
    shutil.which("jq") is None, reason="vischeck-hook requires jq on PATH"
)


def run_hook(file_path, new_string="x"):
    """Run the hook with a synthetic PostToolUse payload; return stdout."""
    payload = json.dumps({"tool_input": {"file_path": file_path, "new_string": new_string}})
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def fires(file_path, new_string="x"):
    return "vischeck:verify" in run_hook(file_path, new_string)


# --- Regression guards: data/config files in a templates/ dir must NOT fire ---


def test_yml_in_templates_dir_is_silent():
    # Helm/CI/Ansible YAML lives in templates/ — must not misfire.
    assert run_hook("config/templates/deploy.yml") == ""


def test_pkl_in_templates_dir_is_silent():
    # Pkl is a config-templating language; templates/*.pkl must not misfire.
    assert run_hook("infra/templates/config.pkl") == ""


# --- Real templates still fire via the extension allowlist ---


def test_html_erb_in_templates_dir_fires():
    # Recognized view extensions win even inside a templates/ dir.
    assert fires("app/templates/home.html.erb")


# --- Other view directories and extensions are unaffected ---


def test_erb_in_views_dir_fires():
    assert fires("app/views/home/index.html.erb")


def test_component_tsx_fires():
    assert fires("app/components/widget.tsx")


# --- Non-view files outside any view dir stay silent ---


def test_plain_yml_is_silent():
    assert run_hook("config/deploy.yml") == ""
