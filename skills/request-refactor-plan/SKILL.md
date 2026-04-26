---
name: request-refactor-plan
description: Refactor-before-implement planner. Use when the user wants to change existing code. Forces a written refactor plan before any code changes. Triggers on requests to change, update, improve, or modify existing code.
---

# Request refactor plan — plan before you touch

## When invoked

The user wants to change existing code. Before writing a single line, produce a refactor plan.

## Mandatory plan structure

```markdown
## Refactor plan — <feature or fix name>

### Current state
- What the code does today
- Why it exists this way (if known)
- What tests cover it currently

### Trigger
- What changed to make this refactor necessary?

### Target state
- What the code should do after
- Which interfaces change (and which stay stable)
- Which domain glossary entries change

### Risk assessment
- What breaks if this goes wrong?
- Which callers are affected?
- Is this reversible?

### Steps (ordered, each independently testable)
1. <step> — tests remain green
2. <step> — tests remain green
3. ...

### Definition of done
- [ ] All existing tests pass
- [ ] New behaviour covered by new tests
- [ ] Coverage ≥ 95%
- [ ] Domain glossary updated if names changed
- [ ] No increase in cyclomatic complexity
```

## Rules

- Each step must leave the test suite green
- Never delete a test to make refactoring easier
- If a name changes, update the glossary first
- If an interface changes, update all callers in the same PR

## Hard stop

Do not write any code until the plan is written and the user has confirmed it.
