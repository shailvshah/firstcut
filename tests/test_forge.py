"""Tests for scripts/forge.py — scaffolding logic, not the interactive wizard."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import forge  # noqa: E402


# ── ForgeConfig helpers ───────────────────────────────────────────────────────

def make_cfg(
    project_type: str = "backend",
    language: str = "python",
    framework: str = "fastapi",
    pkg_manager: str = "uv",
    ext: str = "py",
    tmp_path: Path | None = None,
) -> forge.ForgeConfig:
    cfg = forge.ForgeConfig(
        project_type=project_type,
        language=language,
        framework=framework,
        pkg_manager=pkg_manager,
        ext=ext,
        project_name="test-project",
        org="test-org",
        description="A test project",
        license="MIT",
        ci=["github-actions"],
        skills=[k for k, _ in forge.SKILLS],
        init_git=False,
        include_docs_submodule=True,
    )
    if tmp_path:
        cfg.output_dir = tmp_path
    return cfg


# ── PROJECT_TYPES / STACKS constants ─────────────────────────────────────────

def test_all_project_types_present() -> None:
    expected = {"backend", "frontend", "monorepo", "tooling", "infrastructure", "docs"}
    assert set(forge.PROJECT_TYPES.keys()) == expected


def test_stacks_cover_all_project_types() -> None:
    for pt in forge.PROJECT_TYPES:
        assert pt in forge.STACKS, f"STACKS missing key: {pt}"


def test_stacks_have_required_fields() -> None:
    for pt, langs in forge.STACKS.items():
        for lang, info in langs.items():
            for field in ("framework", "pkg", "ext"):
                assert field in info, f"STACKS[{pt}][{lang}] missing field '{field}'"


# ── SKILLS constant ───────────────────────────────────────────────────────────

def test_all_eight_skills_defined() -> None:
    skill_names = [k for k, _ in forge.SKILLS]
    expected = {
        "grill-me", "tdd", "domain-model", "ubiquitous-language",
        "qa", "request-refactor-plan", "interface-design", "implementation-simplicity",
    }
    assert set(skill_names) == expected


# ── ForgeConfig.slug ──────────────────────────────────────────────────────────

def test_slug_lowercases_and_hyphenates() -> None:
    cfg = make_cfg()
    cfg.project_name = "My Cool Project"
    assert cfg.slug == "my-cool-project"


def test_slug_already_lowercase() -> None:
    cfg = make_cfg()
    cfg.project_name = "simple"
    assert cfg.slug == "simple"


# ── command helpers ───────────────────────────────────────────────────────────

def test_install_cmd_python() -> None:
    cfg = make_cfg(pkg_manager="uv")
    assert forge._install_cmd(cfg) == "uv sync"


def test_install_cmd_typescript() -> None:
    cfg = make_cfg(pkg_manager="pnpm")
    assert forge._install_cmd(cfg) == "pnpm install"


def test_test_cmd_python_includes_coverage() -> None:
    cfg = make_cfg(pkg_manager="uv")
    cmd = forge._test_cmd(cfg)
    assert "--cov-fail-under=95" in cmd


def test_lint_cmd_python_includes_ruff_and_black() -> None:
    cfg = make_cfg(pkg_manager="uv")
    cmd = forge._lint_cmd(cfg)
    assert "ruff" in cmd
    assert "black" in cmd


# ── file writers (use tmp_path) ───────────────────────────────────────────────

def test_write_claude_md_creates_file(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_claude_md(cfg)
    out = cfg.dest / "CLAUDE.md"
    assert out.exists()
    content = out.read_text()
    assert "test-project" in content
    assert "skills/" in content
    assert ".claude/skills/" not in content


def test_write_agents_md_creates_file(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_agents_md(cfg)
    out = cfg.dest / "AGENTS.md"
    assert out.exists()
    assert "skills/" in out.read_text()


def test_write_cursorrules_creates_file(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_cursorrules(cfg)
    assert (cfg.dest / ".cursorrules").exists()


def test_write_windsurfrules_creates_file(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_windsurfrules(cfg)
    assert (cfg.dest / ".windsurfrules").exists()


def test_skills_written_to_skills_dir(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_skills(cfg)
    skills_dir = cfg.dest / "skills"
    assert skills_dir.is_dir()
    for skill_name in cfg.skills:
        skill_file = skills_dir / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Missing skill file: {skill_file}"


def test_skills_not_written_to_claude_dir(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_skills(cfg)
    assert not (cfg.dest / ".claude").exists()


def test_precommit_python_has_ruff_and_pytest(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_precommit(cfg)
    content = (cfg.dest / ".pre-commit-config.yaml").read_text()
    assert "ruff" in content
    assert "pytest" in content
    assert "mypy" in content


def test_github_ci_python_creates_workflow(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_github_ci(cfg)
    assert (cfg.dest / ".github" / "workflows" / "ci.yml").exists()
    assert (cfg.dest / ".github" / "workflows" / "release.yml").exists()


def test_gitlab_ci_python_creates_file(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_gitlab_ci(cfg)
    assert (cfg.dest / ".gitlab-ci" / "ci.yml").exists()


def test_docs_creates_glossary(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_docs(cfg)
    assert (cfg.dest / "docs" / "domain" / "glossary.md").exists()
    assert (cfg.dest / "docs" / "CONTRIBUTING.md").exists()
    assert (cfg.dest / "docs" / "ADR" / "0001-first-principles-sdlc.md").exists()


def test_lang_config_python_creates_pyproject(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_lang_config(cfg)
    pyproject = cfg.dest / "pyproject.toml"
    assert pyproject.exists()
    content = pyproject.read_text()
    assert "test-project" in content
    assert "pytest-cov" in content


def test_readme_contains_slug_and_install(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_readme(cfg)
    content = (cfg.dest / "README.md").read_text()
    assert "test-project" in content
    assert "uv sync" in content


def test_gitignore_python_excludes_venv(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    forge.write_gitignore(cfg)
    content = (cfg.dest / ".gitignore").read_text()
    assert ".venv/" in content
    assert "__pycache__/" in content


# ── skill content sanity ──────────────────────────────────────────────────────

def test_all_skills_have_frontmatter_and_hardstop(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    skills = forge._build_skills(cfg)
    for name, content in skills.items():
        assert content.startswith("---"), f"{name}: missing frontmatter"
        assert "Hard stop" in content, f"{name}: missing Hard stop section"


def test_tdd_skill_mentions_failing_test(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    skills = forge._build_skills(cfg)
    assert "failing test" in skills["tdd"].lower()


def test_qa_skill_mentions_95_coverage(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path=tmp_path)
    skills = forge._build_skills(cfg)
    assert "95" in skills["qa"]
