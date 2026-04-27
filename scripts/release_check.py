#!/usr/bin/env python3
"""Validate cross-ecosystem release metadata before publishing."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[a-zA-Z0-9.-]+)?$")
GO_MODULE = "github.com/shailvshah/firstcut/packages/go"


def fail(message: str) -> None:
    print(f"release-check: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_pyproject() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text())


def read_npm_package() -> dict[str, object]:
    return json.loads((ROOT / "packages" / "npm" / "package.json").read_text())


def validate_pyproject() -> str:
    data = read_pyproject()
    project = data.get("project")
    require(isinstance(project, dict), "pyproject.toml needs a [project] table")

    version = project.get("version")
    require(isinstance(version, str), "pyproject project.version must be a string")
    require(bool(SEMVER_RE.match(version)), f"invalid PyPI version: {version}")
    require(project.get("name") == "firstcut", "PyPI package name must be firstcut")
    require(project.get("readme") is not None, "PyPI readme metadata is missing")
    require(project.get("authors") is not None, "PyPI authors metadata is missing")
    require(project.get("urls") is not None, "PyPI project URLs are missing")
    require(
        project.get("scripts") is not None,
        "PyPI console script metadata is missing",
    )
    return version


def validate_npm_package() -> str:
    data = read_npm_package()
    version = data.get("version")
    require(isinstance(version, str), "npm package version must be a string")
    require(bool(SEMVER_RE.match(version)), f"invalid npm version: {version}")
    require(data.get("name") == "firstcut-cli", "npm package name must be firstcut-cli")
    require(data.get("bin") == {"firstcut": "./bin/firstcut.js"}, "npm bin is wrong")
    require("bin/firstcut.js" in data.get("files", []), "npm files must include bin")
    require(data.get("repository") is not None, "npm repository metadata is missing")
    return version


def validate_go_module() -> None:
    go_mod = (ROOT / "packages" / "go" / "go.mod").read_text().splitlines()
    require(go_mod, "packages/go/go.mod is empty")
    require(go_mod[0] == f"module {GO_MODULE}", "Go module path is not publishable")


def main() -> int:
    py_version = validate_pyproject()
    npm_version = validate_npm_package()
    validate_go_module()
    print(f"release-check: PyPI firstcut {py_version}")
    print(f"release-check: npm firstcut-cli {npm_version}")
    print(f"release-check: Go module {GO_MODULE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
