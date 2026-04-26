#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const PACKAGE_SPEC = process.env.FIRSTCUT_PYPI_SPEC || "firstcut";
const ARGS = process.argv.slice(2);
const ERROR_MESSAGE =
  "Unable to launch firstcut. Install uv or pipx, or ensure python3 can create a venv for firstcut.";

function run(command, args) {
  return spawnSync(command, args, { stdio: "inherit" });
}

function tryCommand(command, args) {
  const result = run(command, args);
  if (result.error) {
    return false;
  }
  process.exit(result.status === null ? 1 : result.status);
}

function findPython() {
  for (const candidate of ["python3", "python"]) {
    const result = spawnSync(candidate, ["--version"], { stdio: "ignore" });
    if (!result.error && result.status === 0) {
      return candidate;
    }
  }
  return null;
}

function ensureVenv(python, venvDir) {
  const exeDir = process.platform === "win32" ? "Scripts" : "bin";
  const pipName = process.platform === "win32" ? "pip.exe" : "pip";
  const firstcutName = process.platform === "win32" ? "firstcut.exe" : "firstcut";
  const pipPath = path.join(venvDir, exeDir, pipName);
  const cliPath = path.join(venvDir, exeDir, firstcutName);

  if (!fs.existsSync(cliPath)) {
    fs.mkdirSync(venvDir, { recursive: true });
    let result = run(python, ["-m", "venv", venvDir]);
    if (result.error || result.status !== 0) {
      return null;
    }
    result = run(pipPath, ["install", PACKAGE_SPEC]);
    if (result.error || result.status !== 0) {
      return null;
    }
  }

  return cliPath;
}

if (tryCommand("uvx", [PACKAGE_SPEC, ...ARGS])) {
  process.exit(0);
}

if (tryCommand("pipx", ["run", PACKAGE_SPEC, ...ARGS])) {
  process.exit(0);
}

const python = findPython();
if (!python) {
  console.error(ERROR_MESSAGE);
  process.exit(1);
}

const venvDir = path.join(os.homedir(), ".cache", "firstcut-wrapper", "venv");
const cliPath = ensureVenv(python, venvDir);
if (!cliPath) {
  console.error(ERROR_MESSAGE);
  process.exit(1);
}

const result = run(cliPath, ARGS);
if (result.error) {
  console.error(ERROR_MESSAGE);
  process.exit(1);
}
process.exit(result.status === null ? 1 : result.status);
