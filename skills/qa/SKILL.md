---
name: qa
description: QA review skill. Use before any PR is created, before merging, or when the user asks for a quality review. Checks coverage, types, edge cases, and domain correctness.
---

# QA review

## QA checklist (run in order)

### 1. Coverage gate
```bash
pytest --cov=src --cov-fail-under=95 --cov-report=term-missing
```
Must be ≥ 95%. List any uncovered lines and ask the user to add tests before proceeding.

### 2. Type safety
```bash
mypy src/ --strict
```
Zero type errors. No `Any` escapes.

### 3. Lint + format
```bash
ruff check . && black --check .
```
Zero warnings.

### 4. Domain correctness review

For each changed file, check:
- [ ] Class/function name is in `docs/domain/glossary.md`
- [ ] Aggregate root is the only mutation entry point
- [ ] Domain events are past-tense and emitted (not called externally)
- [ ] No infrastructure types in domain interfaces

### 5. Test quality review

For each test file, check:
- [ ] Test name is a plain-English sentence
- [ ] Arrange–Act–Assert with blank lines between
- [ ] No mocks on pure functions
- [ ] Each test has one concept and one assertion

### 6. Complexity check

For each function:
- [ ] Cyclomatic complexity ≤ 3
- [ ] ≤ 20 lines
- [ ] ≤ 3 parameters (or options object)
- [ ] No mixed I/O and computation

## Output format

```
## QA Report — <date>

### Coverage: <X>% [PASS/FAIL]
### Type errors: <n> [PASS/FAIL]
### Lint warnings: <n> [PASS/FAIL]

### Issues found
- <file>:<line> — <description>

### Verdict: PASS / NEEDS WORK
```

## Hard stop

Do not approve a PR that fails any gate. List what must be fixed.
