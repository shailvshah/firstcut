"""Project generation orchestration."""

from __future__ import annotations

import shutil
from pathlib import Path

from ._core import h, info, ok, print_summary, warn
from .config import ForgeConfig
from .scaffolds import init_git, write_project_structure
from .writers import (
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
    write_readme,
    write_skills,
    write_windsurfrules,
)


def print_banner() -> None:
    """Render the interactive welcome banner."""
    from ._core import CYAN, RESET, dim

    print(f"""
{h("╔══════════════════════════════════════════════════════╗")}
{h("║")}  {CYAN}firstcut{RESET} — first-principles project scaffolder       {h("║")}
{h("║")}  {dim("4 steps. Opinionated defaults. AI skills embedded.")}  {h("║")}
{h("╚══════════════════════════════════════════════════════╝")}

{dim("Press Enter to accept defaults (shown in parentheses).")}
""")


def generate_project(cfg: ForgeConfig, overwrite: bool = False) -> Path:
    """Generate a project from the fully resolved config."""
    print(f"\n{info('Scaffolding project...')}")

    if cfg.dest.exists():
        if not overwrite:
            raise FileExistsError(cfg.dest)
        shutil.rmtree(cfg.dest)

    write_claude_md(cfg)
    write_agents_md(cfg)
    write_cursorrules(cfg)
    write_windsurfrules(cfg)
    write_skills(cfg)
    write_precommit(cfg)

    if "github-actions" in cfg.ci:
        write_github_ci(cfg)
    if "gitlab-ci" in cfg.ci:
        write_gitlab_ci(cfg)

    if cfg.include_docs_submodule:
        write_docs(cfg)

    write_gitignore(cfg)
    write_readme(cfg)
    write_lang_config(cfg)
    write_project_structure(cfg)
    write_makefile(cfg)

    if cfg.init_git:
        try:
            init_git(cfg)
            print(ok("Git repository initialised with initial commit"))
        except Exception as exc:
            print(warn(f"Git init skipped: {exc}"))

    print_summary(cfg)
    return cfg.dest
