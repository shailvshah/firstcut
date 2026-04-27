#!/usr/bin/env python3
"""Commit and tag a verified firstcut release."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[a-zA-Z0-9.-]+)?$")


def run(args: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )
    return result.stdout.strip() if capture else ""


def fail(message: str) -> None:
    print(f"release-tag: {message}", file=sys.stderr)
    raise SystemExit(1)


def is_secrets_timestamp_only_change() -> bool:
    diff = run(["git", "diff", "--", ".secrets.baseline"], capture=True)
    if not diff:
        return False
    changed = [
        line
        for line in diff.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    return bool(changed) and all('"generated_at":' in line for line in changed)


def read_versions() -> tuple[str, str]:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    npm_package = json.loads((ROOT / "packages" / "npm" / "package.json").read_text())
    py_version = pyproject["project"]["version"]
    npm_version = npm_package["version"]
    if not isinstance(py_version, str) or not isinstance(npm_version, str):
        fail("release versions must be strings")
    return py_version, npm_version


def ensure_clean_allowed_changes(allow_dirty: bool) -> None:
    status = run(["git", "status", "--porcelain"], capture=True).splitlines()
    if not status:
        return
    if status == [" M .secrets.baseline"] and is_secrets_timestamp_only_change():
        return
    if allow_dirty:
        return
    fail(
        "working tree has uncommitted changes. Commit them first, or rerun with "
        "--allow-dirty to commit release files."
    )


def ensure_tag_missing(tag: str) -> None:
    existing = run(["git", "tag", "--list", tag], capture=True)
    if existing:
        fail(f"tag already exists: {tag}")


def commit_allowed_release_files(version: str) -> None:
    paths = [
        "PYPI.md",
        "Makefile",
        "README.md",
        "pyproject.toml",
        "uv.lock",
        "packages/npm/package.json",
        "packages/go/go.mod",
        "src/firstcut/_core.py",
        "scripts/release_check.py",
        "scripts/release_tag.py",
    ]
    run(["git", "add", *paths])
    staged = run(["git", "diff", "--cached", "--name-only"], capture=True)
    if staged:
        run(["git", "commit", "-m", f"chore: prepare {version} release"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="PyPI/GitHub release version, e.g. 0.1.1")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="commit known release files before tagging",
    )
    args = parser.parse_args()

    if not SEMVER_RE.match(args.version):
        fail(f"invalid version: {args.version}")

    py_version, npm_version = read_versions()
    if py_version != args.version:
        fail(f"pyproject version is {py_version}, expected {args.version}")
    if not SEMVER_RE.match(npm_version):
        fail(f"invalid npm version: {npm_version}")

    ensure_clean_allowed_changes(args.allow_dirty)
    if args.allow_dirty:
        commit_allowed_release_files(args.version)
        ensure_clean_allowed_changes(False)

    py_tag = f"v{args.version}"
    go_tag = f"packages/go/v{args.version}"
    ensure_tag_missing(py_tag)
    ensure_tag_missing(go_tag)

    run(["git", "tag", "-a", py_tag, "-m", f"firstcut v{args.version}"])
    run(["git", "tag", "-a", go_tag, "-m", f"firstcut Go launcher v{args.version}"])

    print(f"release-tag: created {py_tag}")
    print(f"release-tag: created {go_tag}")
    print("release-tag: push with:")
    print("  git push origin main")
    print(f"  git push origin {py_tag} {go_tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
