# firstcut

`firstcut` is a first-principles project scaffolder for teams that want more than a folder template.

Run one command, answer four prompts, and get a project with:

- layered architecture for backend, frontend, monorepo, tooling, infrastructure, or docs projects
- AI context files for Claude Code, Codex, Cursor, and Windsurf
- embedded AI skills for domain modeling, TDD, interface design, implementation simplicity, and QA
- pre-commit hooks, CI templates, domain docs, and a 95% coverage culture baked in

## Install

```bash
uv tool install firstcut
# or
pipx install firstcut
```

## Use

```bash
firstcut init
firstcut init --defaults
firstcut init --defaults --project-name billing-api --output-dir ./scratch
firstcut init --defaults --config ./firstcut.toml
```

Interactive prompts can be cancelled with `cancel`, `exit`, `quit`, or `q`.

## Example config

```toml
project_type = "backend"
language = "python"
framework = "fastapi"
pkg_manager = "uv"
project_name = "billing-api"
ci = ["github-actions"]
skills = ["tdd", "qa", "implementation-simplicity"]
```

## Project status

firstcut is alpha software. The Python CLI is the canonical runtime; npm and Go launcher wrappers live in the source repository for cross-ecosystem distribution.

See the full README and source at: https://github.com/shailvshah/firstcut
