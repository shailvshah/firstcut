from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from firstcut._core import (
    ForgeConfig,
    PromptCancelledError,
    _dev_cmd,
    _install_cmd,
    _lint_cmd,
    _test_cmd,
    _typecheck_cmd,
    confirm,
    dim,
    h,
    info,
    init_git,
    ok,
    print_summary,
    prompt,
    prompt_multi,
    step1_project_type,
    step2_stack,
    step3_metadata,
    step4_skills,
    warn,
    write,
    write_agents_md,
    write_claude_md,
    write_cursorrules,
    write_docs,
    write_github_ci,
    write_gitignore,
    write_gitlab_ci,
    write_lang_config,
    write_makefile,
    write_precommit,
    write_project_structure,
    write_readme,
    write_skills,
    write_windsurfrules,
)

# ── Formatting Helpers ────────────────────────────────────────────────────────


def test_color_formatters() -> None:
    """Test ANSI color formatting helpers."""
    assert "\033[1m" in h("text")
    assert "\033[2m" in dim("text")
    assert "\033[32m" in ok("text")
    assert "\033[34m" in info("text")
    assert "\033[33m" in warn("text")


# ── Prompt Helpers ────────────────────────────────────────────────────────────


@patch("builtins.input", side_effect=["", "custom"])
def test_prompt(mock_input: MagicMock) -> None:
    """Test standard input prompting."""
    assert prompt("Q", "def") == "def"
    assert prompt("Q", "def") == "custom"


@patch("builtins.input", side_effect=["invalid", "backend"])
def test_prompt_choices(mock_input: MagicMock) -> None:
    """Test prompting with restricted choices."""
    # It should reject "invalid" and accept "backend" on the second loop
    assert prompt("Q", "def", choices=["backend", "frontend"]) == "backend"


@patch("builtins.input", return_value="exit")
def test_prompt_can_cancel(mock_input: MagicMock) -> None:
    with pytest.raises(PromptCancelledError):
        prompt("Q", "def", choices=["backend", "frontend"])


@patch("builtins.input", side_effect=["", "1, 3, a", ""])
def test_prompt_multi(mock_input: MagicMock) -> None:
    """Test multi-select prompting logic."""
    opts = [("a", "A"), ("b", "B"), ("c", "C")]
    # Empty input, default_all=True
    assert prompt_multi("Q", opts, True) == ["a", "b", "c"]
    # Selection logic: indices 1 and 3 are 'a' and 'c'
    assert prompt_multi("Q", opts, True) == ["b"]
    # Empty input, default_all=False
    assert prompt_multi("Q", opts, False) == []


@patch("builtins.input", return_value="q")
def test_prompt_multi_can_cancel(mock_input: MagicMock) -> None:
    opts = [("a", "A"), ("b", "B")]

    with pytest.raises(PromptCancelledError):
        prompt_multi("Q", opts)


@patch("builtins.input", side_effect=["", "y", "n"])
def test_confirm(mock_input: MagicMock) -> None:
    """Test confirmation dialogs."""
    assert confirm("Q", default=True) is True
    assert confirm("Q", default=False) is True  # Based on snippet logic
    assert confirm("Q") is False


@patch("builtins.input", return_value="cancel")
def test_confirm_can_cancel(mock_input: MagicMock) -> None:
    with pytest.raises(PromptCancelledError):
        confirm("Q")


# ── Config ────────────────────────────────────────────────────────────────────


def test_forge_config() -> None:
    """Test configuration slug generation and pathing."""
    cfg = ForgeConfig(project_name="My Cool App", output_dir=Path("/tmp"))
    assert cfg.slug == "my-cool-app"
    assert cfg.dest == Path("/tmp/my-cool-app")


@patch("firstcut._core.prompt", return_value="frontend")
def test_step1_project_type(mock_prompt: MagicMock) -> None:
    """Test project type selection step."""
    cfg = ForgeConfig()
    step1_project_type(cfg)
    assert cfg.project_type == "frontend"


@patch(
    "firstcut._core.prompt", side_effect=["python", "fastapi", "uv", "github-actions"]
)
def test_step2_stack(mock_prompt: MagicMock) -> None:
    """Test technology stack selection step."""
    cfg = ForgeConfig(project_type="backend")
    step2_stack(cfg)
    assert cfg.language == "python"
    assert cfg.framework == "fastapi"
    assert cfg.pkg_manager == "uv"
    assert cfg.ci == ["github-actions"]


@patch("firstcut._core.prompt", side_effect=["typescript", "nextjs", "pnpm", "both"])
def test_step2_stack_both_ci(mock_prompt: MagicMock) -> None:
    """Test selection of both CI options."""
    cfg = ForgeConfig(project_type="frontend")
    step2_stack(cfg)
    assert cfg.ci == ["github-actions", "gitlab-ci"]


@patch("firstcut._core.prompt", side_effect=["go", "gin", "go mod", "none"])
def test_step2_stack_none_ci(mock_prompt: MagicMock) -> None:
    """Test selection of no CI options."""
    cfg = ForgeConfig(project_type="backend")
    step2_stack(cfg)
    assert cfg.ci == []


@patch(
    "firstcut._core.prompt",
    side_effect=["test-proj", "my-org", "A desc", "MIT", "/out"],
)
def test_step3_metadata(mock_prompt: MagicMock) -> None:
    """Test project metadata collection."""
    cfg = ForgeConfig()
    step3_metadata(cfg)
    assert cfg.project_name == "test-proj"
    assert cfg.org == "my-org"
    assert cfg.license == "MIT"


@patch("firstcut._core.prompt_multi", return_value=["tdd"])
@patch("firstcut._core.confirm", side_effect=[True, True])  # Changed False to True
def test_step4_skills(mock_confirm: MagicMock, mock_multi: MagicMock) -> None:
    """Test AI skill selection and submodule configuration."""
    cfg = ForgeConfig()
    step4_skills(cfg)
    assert cfg.skills == ["tdd"]
    assert cfg.include_docs_submodule is True


# ── File Writers ──────────────────────────────────────────────────────────────


def test_write(tmp_path: Path) -> None:
    """Test atomic file write helper."""
    f = tmp_path / "subdir" / "test.txt"
    write(f, "content")
    assert f.read_text() == "content"


def test_command_helpers() -> None:
    cfg = ForgeConfig(pkg_manager="poetry", framework="fastapi", language="python")
    assert "poetry install" in _install_cmd(cfg)

    assert _dev_cmd(cfg) == "poetry run uvicorn src.main:app --reload"
    cfg.framework = "mkdocs"
    assert _dev_cmd(cfg) == "poetry run mkdocs serve"
    cfg.framework = "unknown"
    assert _dev_cmd(cfg) == "poetry run python -m src.main"
    cfg.pkg_manager = "unknown"
    assert _install_cmd(cfg) == "install deps"
    assert _test_cmd(cfg) == "run tests"
    assert _lint_cmd(cfg) == "run lint"
    assert _typecheck_cmd(cfg) == "run typecheck"

    # Fully transition the config state
    cfg.language = "rust"
    cfg.pkg_manager = "cargo"
    cfg.framework = ""
    cfg.ext = "rs"  # Good practice to keep the state consistent

    assert "cargo clippy" in _lint_cmd(cfg)
    assert _typecheck_cmd(ForgeConfig(pkg_manager="go mod")) == "go vet ./..."


def test_write_skills(tmp_path: Path) -> None:
    """Test generation of skill documentation."""
    cfg = ForgeConfig(
        output_dir=tmp_path,
        project_name="test",
        language="python",
        ext="py",
        skills=["tdd", "qa"],
    )
    write_skills(cfg)
    assert (cfg.dest / "skills" / "tdd" / "SKILL.md").exists()
    assert (cfg.dest / "skills" / "qa" / "SKILL.md").exists()


def test_write_precommit(tmp_path: Path) -> None:
    """Test pre-commit configuration generation across languages."""
    langs = ["python", "typescript", "go", "rust", "hcl", "other"]
    for lang in langs:
        cfg = ForgeConfig(
            output_dir=tmp_path, language=lang, project_name=f"test_{lang}"
        )
        write_precommit(cfg)
        content = (cfg.dest / ".pre-commit-config.yaml").read_text()
        if lang == "go":
            assert "gofmt" in content


def test_write_makefile(tmp_path: Path) -> None:
    """Test Makefile generation logic."""
    langs = ["python", "typescript", "go", "rust", "hcl", "other"]
    for lang in langs:
        cfg = ForgeConfig(
            output_dir=tmp_path, language=lang, project_name=f"test_{lang}"
        )
        if lang == "typescript":
            cfg.project_type = "monorepo"
        write_makefile(cfg)
        assert (cfg.dest / "Makefile").exists()

    cfg_fe = ForgeConfig(
        output_dir=tmp_path,
        language="typescript",
        project_type="frontend",
        project_name="ts_fe",
    )
    write_makefile(cfg_fe)
    assert "pnpm dev" in (cfg_fe.dest / "Makefile").read_text()


def test_write_github_ci(tmp_path: Path) -> None:
    """Test GitHub Actions workflow generation."""
    for lang in ["python", "typescript", "go"]:
        cfg = ForgeConfig(
            output_dir=tmp_path, language=lang, project_name=f"test_{lang}"
        )
        if lang == "python":
            cfg.pkg_manager = "poetry"
        write_github_ci(cfg)
        assert (cfg.dest / ".github" / "workflows" / "release.yml").exists()


def test_write_gitlab_ci(tmp_path: Path) -> None:
    """Test GitLab CI configuration generation."""
    scenarios = [
        ("python", "uv"),
        ("python", "poetry"),
        ("typescript", "pnpm"),
        ("go", "go mod"),
    ]
    for lang, pkg in scenarios:
        cfg = ForgeConfig(
            output_dir=tmp_path,
            language=lang,
            pkg_manager=pkg,
            project_name=f"test_{lang}_{pkg}",
        )
        write_gitlab_ci(cfg)
        assert (cfg.dest / ".gitlab-ci" / "ci.yml").exists()


def test_write_lang_config(tmp_path: Path) -> None:
    """Test language-specific configuration files (e.g., go.mod, pyproject.toml)."""
    scenarios = [
        ("python", "poetry", "backend", "fastapi"),
        ("typescript", "pnpm", "frontend", "nextjs"),
        ("typescript", "pnpm", "monorepo", "turborepo"),
        ("go", "go mod", "tooling", ""),
    ]
    for lang, pkg, ptype, fw in scenarios:
        cfg = ForgeConfig(
            output_dir=tmp_path,
            language=lang,
            pkg_manager=pkg,
            project_type=ptype,
            framework=fw,
            project_name=f"test_{lang}_{pkg}",
        )
        write_lang_config(cfg)
        if lang == "go":
            assert (cfg.dest / "go.mod").exists()
        if ptype == "monorepo":
            assert (cfg.dest / "pnpm-workspace.yaml").exists()
        if lang == "typescript" and ptype != "monorepo":
            assert (cfg.dest / "vitest.config.ts").exists()


def test_write_project_structure(tmp_path: Path) -> None:
    """Test full project scaffold structure generation."""
    combos = [
        ("backend", "python", "fastapi"),
        ("backend", "typescript", "hono"),
        ("backend", "go", "gin"),
        ("backend", "rust", "axum"),
        ("frontend", "typescript", "nextjs"),
        ("frontend", "typescript", "vite"),
        ("frontend", "javascript", "vite"),
        ("monorepo", "typescript", "turborepo"),
        ("tooling", "python", "typer"),
        ("tooling", "typescript", "commander"),
        ("tooling", "go", "cobra"),
        ("infrastructure", "python", "pulumi"),
        ("infrastructure", "hcl", "terraform"),
        ("docs", "python", "mkdocs"),
        ("docs", "typescript", "docusaurus"),
    ]
    for ptype, lang, fw in combos:
        cfg = ForgeConfig(
            output_dir=tmp_path,
            project_type=ptype,
            language=lang,
            framework=fw,
            project_name=f"proj_{ptype}_{lang}_{fw}",
        )
        write_project_structure(cfg)
        assert cfg.dest.exists()


def test_write_project_structure_ignores_unknown_stack(tmp_path: Path) -> None:
    cfg = ForgeConfig(
        output_dir=tmp_path,
        project_type="unknown",
        language="unknown",
        project_name="unknown",
    )

    write_project_structure(cfg)

    assert not cfg.dest.exists()


@patch("firstcut._core.subprocess.run")
def test_init_git(mock_run: MagicMock, tmp_path: Path) -> None:
    """Test git initialization commands."""
    cfg = ForgeConfig(output_dir=tmp_path, project_name="git_test")
    cfg.dest.mkdir(parents=True, exist_ok=True)
    init_git(cfg)
    assert mock_run.call_count == 3


def test_miscellaneous_writers(tmp_path: Path) -> None:
    """Test supplementary file writers like README and AI rules."""
    cfg = ForgeConfig(output_dir=tmp_path, project_name="misc")
    write_claude_md(cfg)
    write_docs(cfg)
    write_agents_md(cfg)
    write_cursorrules(cfg)
    write_windsurfrules(cfg)
    write_gitignore(cfg)
    write_readme(cfg)

    assert (cfg.dest / "CLAUDE.md").exists()
    assert (cfg.dest / "docs" / "domain" / "glossary.md").exists()
    assert (cfg.dest / "AGENTS.md").exists()


@patch("builtins.print")
def test_print_summary(mock_print: MagicMock) -> None:
    """Test the summary output display."""
    cfg = ForgeConfig()
    print_summary(cfg)
    assert mock_print.called
