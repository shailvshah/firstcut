# Contributing to firstcut

## Before writing any code

1. Check `docs/domain/glossary.md` — is the concept already named?
2. If not, add a glossary entry first
3. Read the relevant skill in `.claude/skills/`
4. Write the domain doc if adding a new concept
5. Write the failing test
6. Then implement

## Setup

```bash
git clone https://github.com/your-org/firstcut
cd firstcut
pip install uv pre-commit
uv sync --all-extras
pre-commit install --hook-type commit-msg
pre-commit install
```

## Running tests

```bash
uv run pytest -q
```

## Commit messages

Follow Conventional Commits:
- `feat: add rust stack support`
- `fix: default org name escaping`
- `docs: update glossary with Scaffold term`
- `refactor: extract write_ci into separate module`
- `test: add coverage for gitlab-ci generation`

## PR checklist

- [ ] Glossary updated (if new names introduced)
- [ ] Tests pass: `uv run pytest -q`
- [ ] Types pass: `uv run mypy scripts/ --strict`
- [ ] Lint passes: `uv run ruff check . && uv run black --check .`
- [ ] PR description explains **why**, not what
