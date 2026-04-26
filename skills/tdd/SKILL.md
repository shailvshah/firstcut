---
name: tdd
description: Red-green-refactor enforcer. Write a failing test first. Never write implementation without a red test. Triggers on any request to implement a feature, fix a bug, or add a method.
---

# TDD — red, green, refactor

## Non-negotiable sequence

1. Write ONE failing test (red) — run it — confirm it fails
2. Write MINIMAL code to pass — run it — confirm green
3. Refactor names and duplication — stay green throughout

Never write step 2 before step 1 is confirmed red.

## Test anatomy (Python)

```python
# Arrange
order = Order.empty()
item = Item.create("book", 9.99)

# Act
result = order.add_item(item)

# Assert
assert result.item_count == 1
```

- Blank line between each section — mandatory
- One concept per test
- One assertion per test (prefer)

## Naming

Plain English sentence describing the behaviour:

✓ `"returns error when cart is empty at checkout"`
✗ `"test1"`, `"checkoutTest"`, `"myTest"`

## Mock discipline

- Pure functions: real inputs/outputs — **no mocks**
- Mocks only at infrastructure boundaries: HTTP, DB, filesystem, clock, external APIs
- Prefer fakes (in-memory implementations of your interfaces) over mocks

## File location

Co-locate: `order.py` → `order_test.py` in the same directory.
Integration/e2e tests only → `tests/integration/` or `tests/e2e/`

## Coverage gate

`pytest` must report ≥ 95% line coverage. CI will fail below this threshold.

## Hard stop

If no failing test exists, refuse to write implementation. Ask the user to write the test first.
