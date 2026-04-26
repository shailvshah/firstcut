# firstcut

> The scaffolder that scaffolds scaffolders.
> This repo generates first-principles projects. It eats its own cooking.

## This repo's own engineering workflow

When contributing to firstcut itself, follow the same 5-phase SDLC it enforces on generated projects.

```
1. Domain doc first      → docs/domain/<concept>.md
2. Name from glossary    → docs/domain/glossary.md
3. Interface before class→ skills/interface-design/SKILL.md
4. Failing test first    → skills/tdd/SKILL.md
5. Implement simply      → skills/implementation-simplicity/SKILL.md
```

## Skill manifest (for this repo)

- **tdd** → `skills/tdd/SKILL.md`
- **domain-model** → `skills/domain-model/SKILL.md`
- **ubiquitous-language** → `skills/ubiquitous-language/SKILL.md`
- **interface-design** → `skills/interface-design/SKILL.md`
- **implementation-simplicity** → `skills/implementation-simplicity/SKILL.md`
- **grill-me** → `skills/grill-me/SKILL.md`
- **qa** → `skills/qa/SKILL.md`
- **request-refactor-plan** → `skills/request-refactor-plan/SKILL.md`

## Hard stops

- No implementation before a failing test
- No name outside `docs/domain/glossary.md`
- No function with cyclomatic complexity > 3
- No merging below 95% coverage

## Key files

| File | Purpose |
|------|---------|
| `src/firstcut/cli.py` | The main CLI — 4-step interactive scaffolder |
| `skills/` | All 8 AI skills — provider-agnostic markdown |
| `docs/domain/` | Domain model for this repo |

## Useful commands

```bash
uv run firstcut init             # run the scaffolder
python -m pytest tests/ -q       # test the packaged CLI and core
```
