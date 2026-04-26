---
name: implementation-simplicity
description: Simplicity enforcer. Use during all implementation work. Rejects complexity before it enters the codebase. Cyclomatic complexity ≤ 3, pure functions, dependency injection, rule of three for abstraction.
---

# Implementation — simple by default

## Function rules (all mandatory)

| Rule | Limit |
|------|-------|
| Lines per function | ≤ 20 |
| Cyclomatic complexity | ≤ 3 |
| Parameters | ≤ 3 (use options object beyond 3) |
| Nesting depth | ≤ 2 |

Count complexity: each `if/elif/else/for/while/except/and/or` adds 1.

## Purity

Separate computation from I/O — always:

```python
# Pure — always testable, no mocks needed
def calculate_total(items: list[Item]) -> Money:
    return sum(item.price for item in items)

# Side effect — explicit, named with verb
async def save_order(order: Order, repo: OrderRepository) -> None:
    await repo.save(order)
```

## Error handling

Explicit, typed, never silent:

```python
from result import Result, Ok, Err

def parse_date(s: str) -> Result[date, ParseError]:
    try:
        return Ok(date.fromisoformat(s))
    except ValueError as e:
        return Err(ParseError(str(e)))
```

## Dependency injection

```python
# Never: new inside a function
# Always: injected at construction
def create_order_service(
    repo: OrderRepository,
    events: EventBus,
) -> OrderService:
    return OrderService(repo, events)
```

## Abstraction discipline (rule of three)

- Copy once: leave the duplication
- Copy twice: still leave it
- Copy three times: now extract

Premature abstraction costs more than duplication.

## Complexity red flags — stop and refactor

- Nested `if` beyond 2 levels → extract a guard clause
- Function longer than 20 lines → split at the natural seam
- More than 3 parameters → use a config/options dataclass
- A comment explaining **what** the code does → rename instead
- `Any` type anywhere → type it properly
- Logic and I/O in the same function → split them

## Hard stop

Refuse to merge any function with complexity > 3. Ask the user to split it first.
