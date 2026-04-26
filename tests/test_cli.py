"""Tests for the packaged firstcut CLI and generator entrypoints."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from firstcut import cli
from firstcut.config import PROJECT_TYPES, SKILLS, STACKS, ForgeConfig
from firstcut.generate import generate_project


def test_cli_defaults_generates_project(tmp_path: Path) -> None:
    exit_code = cli.main(["init", "--defaults", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "my-project" / "README.md").exists()


def test_cli_private_normalizers() -> None:
    assert cli._parse_csv(None) is None
    assert cli._parse_csv("github-actions, gitlab-ci,, ") == [
        "github-actions",
        "gitlab-ci",
    ]
    assert cli._parse_csv(" , ") == []

    assert cli._normalize_ci(None) is None
    assert cli._normalize_ci(["all"]) == ["github-actions", "gitlab-ci"]
    assert cli._normalize_ci(["both"]) == ["github-actions", "gitlab-ci"]
    assert cli._normalize_ci(["none"]) == []
    assert cli._normalize_ci(["github-actions"]) == ["github-actions"]

    assert cli._normalize_skills(None) is None
    assert cli._normalize_skills(["all"]) == [name for name, _ in SKILLS]
    assert cli._normalize_skills(["tdd"]) == ["tdd"]


def test_cli_apply_mapping_skips_unknown_and_none(tmp_path: Path) -> None:
    cfg = ForgeConfig(project_name="kept")

    cli._apply_mapping(
        cfg,
        {
            "project_name": None,
            "output_dir": tmp_path,
            "ignored": "value",
        },
    )

    assert cfg.project_name == "kept"
    assert cfg.output_dir == tmp_path.resolve()


def test_cli_config_file_and_flag_override(tmp_path: Path) -> None:
    config_path = tmp_path / "firstcut.json"
    config_path.write_text(
        json.dumps(
            {
                "project_type": "docs",
                "language": "python",
                "framework": "mkdocs",
                "project_name": "from-config",
            }
        )
    )

    exit_code = cli.main(
        [
            "init",
            "--defaults",
            "--config",
            str(config_path),
            "--project-name",
            "from-flag",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "from-flag" / "mkdocs.yml").exists()


def test_cli_build_cfg_normalizes_flags(tmp_path: Path) -> None:
    parser = cli._build_parser()
    args = parser.parse_args(
        [
            "init",
            "--defaults",
            "--project-type",
            "frontend",
            "--language",
            "typescript",
            "--framework",
            "nextjs",
            "--pkg-manager",
            "pnpm",
            "--ext",
            "ts",
            "--project-name",
            "flaggy",
            "--org",
            "acme",
            "--description",
            "From flags",
            "--license",
            "Apache-2.0",
            "--output-dir",
            str(tmp_path),
            "--ci",
            "both",
            "--skills",
            "all",
            "--no-init-git",
            "--no-include-docs-submodule",
        ]
    )

    cfg = cli._build_cfg(args)

    assert cfg.project_type == "frontend"
    assert cfg.ci == ["github-actions", "gitlab-ci"]
    assert cfg.skills == [name for name, _ in SKILLS]
    assert cfg.init_git is False
    assert cfg.include_docs_submodule is False
    assert cfg.output_dir == tmp_path.resolve()


@patch("builtins.input")
def test_cli_interactive_generation(mock_input: MagicMock, tmp_path: Path) -> None:
    mock_input.side_effect = [
        "tooling",
        "python",
        "typer",
        "uv",
        "none",
        "interactive-app",
        "my-org",
        "Interactive description",
        "MIT",
        str(tmp_path),
        "",
        "n",
        "n",
    ]

    exit_code = cli.main(["init"])

    assert exit_code == 0
    dest = tmp_path / "interactive-app"
    assert (dest / "src" / "cli.py").exists()
    assert not (dest / "docs").exists()


def test_cli_existing_destination_requires_overwrite(tmp_path: Path) -> None:
    dest = tmp_path / "my-project"
    dest.mkdir()

    exit_code = cli.main(["init", "--defaults", "--output-dir", str(tmp_path)])

    assert exit_code == cli.EXIT_USAGE


@patch("firstcut.cli.confirm", return_value=False)
def test_cli_interactive_existing_destination_can_abort(
    mock_confirm: MagicMock, tmp_path: Path
) -> None:
    cfg = ForgeConfig(output_dir=tmp_path)
    cfg.dest.mkdir(parents=True)

    with (
        patch("firstcut.cli._build_cfg", return_value=cfg),
        patch("firstcut.cli._run_interactive", return_value=cfg),
    ):
        args = cli._build_parser().parse_args(["init"])
        exit_code = cli.run_init(args)

    assert exit_code == cli.EXIT_OK
    assert mock_confirm.called


@patch("firstcut.cli.confirm", return_value=True)
@patch("firstcut.cli.generate_project")
def test_cli_interactive_existing_destination_can_overwrite(
    mock_generate_project: MagicMock, mock_confirm: MagicMock, tmp_path: Path
) -> None:
    cfg = ForgeConfig(output_dir=tmp_path)
    cfg.dest.mkdir(parents=True)

    with (
        patch("firstcut.cli._build_cfg", return_value=cfg),
        patch("firstcut.cli._run_interactive", return_value=cfg),
    ):
        args = cli._build_parser().parse_args(["init"])
        exit_code = cli.run_init(args)

    assert exit_code == cli.EXIT_OK
    mock_generate_project.assert_called_once_with(cfg, overwrite=True)
    assert mock_confirm.called


def test_cli_accepts_toml_config(tmp_path: Path) -> None:
    config_path = tmp_path / "firstcut.toml"
    config_path.write_text("""
project_type = "docs"
language = "python"
framework = "mkdocs"
project_name = "toml-docs"
""")

    exit_code = cli.main(
        [
            "init",
            "--defaults",
            "--config",
            str(config_path),
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "toml-docs" / "mkdocs.yml").exists()


def test_cli_rejects_non_object_config(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.json"
    config_path.write_text('["not", "an", "object"]')

    exit_code = cli.main(["init", "--defaults", "--config", str(config_path)])

    assert exit_code == cli.EXIT_USAGE


def test_cli_rejects_invalid_configs(capsys: pytest.CaptureFixture[str]) -> None:
    scenarios = [
        ["init", "--defaults", "--project-type", "backend", "--language", "ruby"],
        [
            "init",
            "--defaults",
            "--project-type",
            "backend",
            "--language",
            "python",
            "--framework",
            "django",
        ],
        ["init", "--defaults", "--ci", "circle"],
        ["init", "--defaults", "--skills", "unknown"],
    ]

    for argv in scenarios:
        assert cli.main(argv) == cli.EXIT_USAGE

    captured = capsys.readouterr()
    assert "unknown" in captured.err or "not supported" in captured.err


def test_cli_validate_rejects_stack_without_options() -> None:
    cfg = ForgeConfig(project_type="empty")

    with (
        patch.dict(PROJECT_TYPES, {"empty": "No stacks"}),
        patch.dict(STACKS, {"empty": {}}),
    ):
        try:
            cli._validate_cfg(cfg)
        except ValueError as exc:
            assert "no stacks defined" in str(exc)
        else:
            raise AssertionError("expected ValueError")


def test_cli_defaults_to_init_when_no_args(tmp_path: Path) -> None:
    exit_code = cli.main(["--defaults", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "my-project").exists()


def test_cli_uses_sys_argv_when_argv_is_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["firstcut", "--defaults", "--output-dir", str(tmp_path)],
    )

    exit_code = cli.main()

    assert exit_code == cli.EXIT_OK
    assert (tmp_path / "my-project").exists()


def test_generate_project_overwrite_gitlab_and_init_git_failure(tmp_path: Path) -> None:
    cfg = ForgeConfig(
        project_type="backend",
        language="python",
        framework="fastapi",
        pkg_manager="uv",
        ext="py",
        project_name="gitlab-project",
        org="test-org",
        description="A test project",
        license="MIT",
        ci=["gitlab-ci"],
        skills=[name for name, _ in SKILLS],
        init_git=True,
        include_docs_submodule=False,
        output_dir=tmp_path,
    )
    cfg.dest.mkdir(parents=True)

    with patch("firstcut.generate.init_git", side_effect=RuntimeError("boom")):
        dest = generate_project(cfg, overwrite=True)

    assert dest == cfg.dest
    assert (cfg.dest / ".gitlab-ci" / "ci.yml").exists()
