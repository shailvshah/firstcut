#!/usr/bin/env python3
"""Bump firstcut release versions across package manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[a-zA-Z0-9.-]+)?$")


def fail(message: str) -> None:
    print(f"release-bump: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_version(version: str, name: str) -> None:
    if not SEMVER_RE.match(version):
        fail(f"invalid {name} version: {version}")


def bump_pyproject(version: str) -> None:
    path = ROOT / "pyproject.toml"
    text = path.read_text()
    updated, count = re.subn(
        r'(?m)^(version = ")[^"]+(")$',
        rf"\g<1>{version}\2",
        text,
        count=1,
    )
    if count != 1:
        fail("could not update pyproject.toml project.version")
    path.write_text(updated)


def bump_npm(version: str) -> None:
    path = ROOT / "packages" / "npm" / "package.json"
    data = json.loads(path.read_text())
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="PyPI/GitHub/Go version, e.g. 0.1.1")
    parser.add_argument(
        "--npm-version",
        help="npm wrapper version; defaults to VERSION",
    )
    args = parser.parse_args()

    npm_version = args.npm_version or args.version
    validate_version(args.version, "release")
    validate_version(npm_version, "npm")

    bump_pyproject(args.version)
    bump_npm(npm_version)

    print(f"release-bump: PyPI/GitHub/Go version -> {args.version}")
    print(f"release-bump: npm version -> {npm_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
