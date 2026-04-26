"""Canonical CLI for firstcut."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from ._core import PromptCancelledError, confirm, prompt, prompt_multi
from .config import CI_OPTIONS, LICENSES, PROJECT_TYPES, SKILLS, STACKS, ForgeConfig
from .generate import generate_project, print_banner

EXIT_OK = 0
EXIT_USAGE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="firstcut")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser("init", help="Scaffold a new project")
    init.add_argument("--defaults", action="store_true", help="Use current defaults")
    init.add_argument("--config", type=Path, help="Load config from JSON or TOML")
    init.add_argument("--project-type", choices=sorted(PROJECT_TYPES))
    init.add_argument("--language")
    init.add_argument("--framework")
    init.add_argument("--pkg-manager")
    init.add_argument("--ext")
    init.add_argument("--project-name")
    init.add_argument("--org")
    init.add_argument("--description")
    init.add_argument("--license", dest="license_name", choices=sorted(LICENSES))
    init.add_argument("--output-dir", type=Path)
    init.add_argument(
        "--ci",
        help="Comma-separated CI targets: github-actions, gitlab-ci, both, none",
    )
    init.add_argument(
        "--skills", help="Comma-separated skill names; use 'all' to keep defaults"
    )
    init.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the destination if it exists",
    )
    init.add_argument("--init-git", dest="init_git", action="store_true", default=None)
    init.add_argument("--no-init-git", dest="init_git", action="store_false")
    init.add_argument(
        "--include-docs-submodule",
        dest="include_docs_submodule",
        action="store_true",
        default=None,
    )
    init.add_argument(
        "--no-include-docs-submodule",
        dest="include_docs_submodule",
        action="store_false",
    )

    return parser


def _load_config_file(path: Path) -> dict[str, Any]:
    raw = path.read_text()
    if path.suffix == ".json":
        data = json.loads(raw)
    else:
        data = tomllib.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("config file must contain a top-level object")
    return data


def _parse_csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or []


def _build_cfg(args: argparse.Namespace) -> ForgeConfig:
    cfg = ForgeConfig()
    if args.config:
        payload = _load_config_file(args.config)
        _apply_mapping(cfg, payload)
    _apply_mapping(
        cfg,
        {
            "project_type": args.project_type,
            "language": args.language,
            "framework": args.framework,
            "pkg_manager": args.pkg_manager,
            "ext": args.ext,
            "project_name": args.project_name,
            "org": args.org,
            "description": args.description,
            "license": args.license_name,
            "output_dir": args.output_dir,
            "ci": _normalize_ci(_parse_csv(args.ci)),
            "skills": _normalize_skills(_parse_csv(args.skills)),
            "init_git": args.init_git,
            "include_docs_submodule": args.include_docs_submodule,
        },
    )
    return cfg


def _apply_mapping(cfg: ForgeConfig, payload: dict[str, Any]) -> None:
    key_map = {
        "project_type": "project_type",
        "language": "language",
        "framework": "framework",
        "pkg_manager": "pkg_manager",
        "ext": "ext",
        "project_name": "project_name",
        "org": "org",
        "description": "description",
        "license": "license",
        "output_dir": "output_dir",
        "ci": "ci",
        "skills": "skills",
        "init_git": "init_git",
        "include_docs_submodule": "include_docs_submodule",
    }
    for raw_key, target in key_map.items():
        if raw_key not in payload:
            continue
        value = payload[raw_key]
        if value is None:
            continue
        if target == "output_dir":
            setattr(cfg, target, Path(value).expanduser().resolve())
            continue
        setattr(cfg, target, value)


def _normalize_ci(items: list[str] | None) -> list[str] | None:
    if items is None:
        return None
    if items == ["all"] or items == ["both"]:
        return ["github-actions", "gitlab-ci"]
    if items == ["none"]:
        return []
    return items


def _normalize_skills(items: list[str] | None) -> list[str] | None:
    if items is None:
        return None
    if items == ["all"]:
        return [name for name, _ in SKILLS]
    return items


def _validate_cfg(cfg: ForgeConfig) -> None:
    if cfg.project_type not in PROJECT_TYPES:
        raise ValueError(f"unknown project type: {cfg.project_type}")
    available = STACKS.get(cfg.project_type)
    if not available:
        raise ValueError(f"no stacks defined for project type: {cfg.project_type}")
    if cfg.language not in available:
        raise ValueError(
            f"language {cfg.language!r} is not supported for {cfg.project_type}"
        )
    stack = available[cfg.language]
    if cfg.framework != stack["framework"]:
        raise ValueError(
            "framework "
            f"{cfg.framework!r} is not supported for "
            f"{cfg.project_type}/{cfg.language}"
        )
    unknown_ci = [
        item for item in cfg.ci if item not in {"github-actions", "gitlab-ci"}
    ]
    if unknown_ci:
        raise ValueError(f"unknown CI target(s): {', '.join(unknown_ci)}")
    valid_skills = {name for name, _ in SKILLS}
    unknown_skills = [item for item in cfg.skills if item not in valid_skills]
    if unknown_skills:
        raise ValueError(f"unknown skill(s): {', '.join(unknown_skills)}")


def _run_interactive(cfg: ForgeConfig) -> ForgeConfig:
    print_banner()

    # Keep the original prompt order, but seed each step from the current config.
    _interactive_step1(cfg)
    _interactive_step2(cfg)
    _interactive_step3(cfg)
    _interactive_step4(cfg)
    return cfg


def _interactive_step1(cfg: ForgeConfig) -> None:
    from ._core import h

    print(f"\n{h('─── Step 1 of 4 — Project type ───────────────────────────────')}")
    for key, desc in PROJECT_TYPES.items():
        print(f"  {h(key):<18} {desc}")
    cfg.project_type = prompt("Project type", cfg.project_type, list(PROJECT_TYPES))


def _interactive_step2(cfg: ForgeConfig) -> None:
    from ._core import h

    print(f"\n{h('─── Step 2 of 4 — Stack ──────────────────────────────────────')}")
    available = STACKS.get(cfg.project_type, STACKS["backend"])
    langs = list(available.keys())
    default_lang = cfg.language if cfg.language in langs else langs[0]

    print(f"  Available languages: {', '.join(langs)}")
    cfg.language = prompt("Language", default_lang, langs)

    stack = available[cfg.language]
    cfg.framework = prompt("Framework", cfg.framework or stack["framework"])
    cfg.pkg_manager = prompt("Package manager", cfg.pkg_manager or stack["pkg"])
    cfg.ext = cfg.ext or stack["ext"]

    ci_default = (
        "both"
        if cfg.ci == ["github-actions", "gitlab-ci"]
        else ("none" if not cfg.ci else cfg.ci[0])
    )
    ci_raw = prompt("CI target", ci_default, CI_OPTIONS)
    cfg.ci = (
        ["github-actions", "gitlab-ci"]
        if ci_raw == "both"
        else ([] if ci_raw == "none" else [ci_raw])
    )


def _interactive_step3(cfg: ForgeConfig) -> None:
    from ._core import h

    print(f"\n{h('─── Step 3 of 4 — Project metadata ───────────────────────────')}")
    cfg.project_name = prompt("Project name", cfg.project_name)
    cfg.org = prompt("Organisation / owner", cfg.org)
    cfg.description = prompt("One-line description", cfg.description)
    cfg.license = prompt("License", cfg.license, list(LICENSES))
    out_raw = prompt("Output directory", str(cfg.output_dir))
    cfg.output_dir = Path(out_raw).expanduser().resolve()


def _interactive_step4(cfg: ForgeConfig) -> None:
    from ._core import dim, h

    print(f"\n{h('─── Step 4 of 4 — AI skills ──────────────────────────────────')}")
    print(dim("  All skills are enabled by default (recommended for beginners)."))
    current_default_all = set(cfg.skills) == {name for name, _ in SKILLS}
    skills = prompt_multi(
        "Select skills to include:",
        SKILLS,
        default_all=current_default_all,
    )
    cfg.skills = skills
    cfg.init_git = confirm("Initialise a git repo?", default=cfg.init_git)
    cfg.include_docs_submodule = confirm(
        "Include docs/ as a submodule scaffold?",
        default=cfg.include_docs_submodule,
    )


def run_init(args: argparse.Namespace) -> int:
    try:
        cfg = _build_cfg(args)
        if not args.defaults:
            cfg = _run_interactive(cfg)
        _validate_cfg(cfg)
        overwrite = args.overwrite
        if cfg.dest.exists() and not overwrite and not args.defaults:
            if not confirm(f"Overwrite existing directory {cfg.dest}?", default=False):
                print("Aborted.")
                return EXIT_OK
            overwrite = True
        generate_project(cfg, overwrite=overwrite)
        return EXIT_OK
    except FileExistsError as exc:
        print(
            (
                f"Destination already exists: {exc}. "
                "Re-run with --overwrite to replace it."
            ),
            file=sys.stderr,
        )
        return EXIT_USAGE
    except (KeyboardInterrupt, PromptCancelledError):
        print("Aborted.")
        return EXIT_OK
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["init"]
    elif argv[0] not in {"init", "-h", "--help"}:
        argv = ["init", *argv]

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return run_init(args)

    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
