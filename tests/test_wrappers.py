"""Smoke tests for launcher wrappers."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_npm_wrapper_uses_consistent_bootstrap_order() -> None:
    content = (ROOT / "packages" / "npm" / "bin" / "firstcut.js").read_text()

    assert 'tryCommand("uvx"' in content
    assert 'tryCommand("pipx"' in content
    assert 'python3", "python"' in content


def test_go_wrapper_uses_consistent_bootstrap_order() -> None:
    content = (ROOT / "packages" / "go" / "cmd" / "firstcut" / "main.go").read_text()

    assert 'tryExec("uvx"' in content
    assert 'tryExec("pipx"' in content
    assert '[]string{"python3", "python"}' in content
