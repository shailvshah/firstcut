# firstcut

> The scaffolder that scaffolds scaffolders.
> This repo generates first-principles projects. It eats its own cooking.

## Mandatory engineering workflow

Follow these phases **in order** for every contribution. Skipping a phase is not permitted.

1. **Domain first** — produce `docs/domain/<concept>.md` before any code (read `skills/domain-model/SKILL.md`)
2. **Name from glossary** — every identifier must be in `docs/domain/glossary.md` (read `skills/ubiquitous-language/SKILL.md`)
3. **Interface before class** — design the contract first (read `skills/interface-design/SKILL.md`)
4. **Failing test first** — red → green → refactor (read `skills/tdd/SKILL.md`)
5. **Implement simply** — complexity ≤ 3, pure functions (read `skills/implementation-simplicity/SKILL.md`)
6. **QA review** — before any PR (read `skills/qa/SKILL.md`)

## Hard stops

- Do not write a class or function before a domain doc exists
- Do not write implementation before a **failing** test exists
- Do not name anything that is not in `docs/domain/glossary.md`
- Do not use functions with cyclomatic complexity > 3
- Do not merge code with < 95% test coverage

---

## AI skill manifest

- grill-me → `skills/grill-me/SKILL.md`
- tdd → `skills/tdd/SKILL.md`
- domain-model → `skills/domain-model/SKILL.md`
- ubiquitous-language → `skills/ubiquitous-language/SKILL.md`
- qa → `skills/qa/SKILL.md`
- request-refactor-plan → `skills/request-refactor-plan/SKILL.md`
- interface-design → `skills/interface-design/SKILL.md`
- implementation-simplicity → `skills/implementation-simplicity/SKILL.md`

---

## Key files

| File | Purpose |
|------|---------|
| `src/firstcut/cli.py` | The main CLI — 4-step interactive scaffolder |
| `skills/` | All 8 AI skills — provider-agnostic markdown |
| `docs/domain/` | Domain model for this repo |

## Useful commands

```bash
uv run firstcut init             # run the scaffolder
uv run pytest -q                 # run tests
uv run ruff check . && uv run black --check .   # lint
uv run mypy src/ tests/          # type check
```
