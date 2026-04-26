# Domain glossary — firstcut

> Single source of truth for all names in this codebase.
> Every identifier in `scripts/forge.py` and any future module must appear here first.

---

## ForgeConfig
**Definition**: The complete, validated set of choices a user makes during the 4-step wizard — project type, stack, metadata, and selected skills.
**Used in**: forge (core)
**Synonyms to avoid**: Config, Settings, Options, Params

## ProjectType
**Definition**: One of six categories describing the primary purpose of a generated project: backend, frontend, monorepo, tooling, infrastructure, or docs.
**Used in**: forge (core)
**Synonyms to avoid**: Template, Kind, Category, Mode

## Skill
**Definition**: A self-contained SKILL.md file that instructs an AI coding assistant to follow a specific engineering discipline (e.g. TDD, DDD, interface-first).
**Used in**: forge (core), templates
**Synonyms to avoid**: Plugin, Extension, Module, Feature

## Scaffold
**Definition**: The act of generating a complete, opinionated project directory tree from a ForgeConfig, including CI, pre-commit hooks, domain docs, and AI skills.
**Used in**: forge (core)
**Synonyms to avoid**: Generate, Create, Bootstrap, Init (too generic)

## Stack
**Definition**: The combination of language, framework, and package manager chosen for a generated project.
**Used in**: forge (core)
**Synonyms to avoid**: Tech stack (redundant), Setup, Config

## DocsSubmodule
**Definition**: The `docs/` directory included in every generated project, containing the domain glossary, ADRs, and contributing guide — structured to be usable as a git submodule.
**Used in**: forge (core), all templates
**Synonyms to avoid**: Documentation, Docs folder

## PreCommitHook
**Definition**: A local git hook that enforces quality gates (ruff, black, mypy, coverage, secret scan, commit message format) before a commit is accepted.
**Used in**: forge (core), templates
**Synonyms to avoid**: Hook, Git hook, Linter

## CoverageGate
**Definition**: The 95% line coverage threshold that pre-commit hooks and CI must enforce. Failing below this threshold blocks a commit or merge.
**Used in**: forge (core), qa skill, tdd skill
**Synonyms to avoid**: Coverage threshold, Coverage requirement

## MandatoryWorkflow
**Definition**: The 5-phase SDLC sequence enforced by CLAUDE.md: domain doc → ubiquitous language → interface → failing test → simple implementation.
**Used in**: CLAUDE.md, all skills
**Synonyms to avoid**: Process, Workflow, SDLC steps
