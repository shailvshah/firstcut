---
name: interface-design
description: Interface-before-class enforcer. Use at the start of any new module, service, or component. The interface/protocol must be written and tested before the concrete implementation exists. Triggers on any request to create a new service, repository, gateway, or component.
---

# Interface-first design

## Mandatory sequence

1. Write the interface / protocol
2. Write tests against the interface using a fake implementation
3. Write the concrete implementation
4. Wire the concrete implementation via dependency injection

Never write step 3 before step 2 is green.

## Interface rules

- One responsibility per interface (Interface Segregation Principle)
- Max 3–5 methods per interface — if more, split
- No infrastructure types in domain interfaces:
  - ✗ HTTP `Request`/`Response`
  - ✗ ORM model objects
  - ✗ Framework-specific types
- Parameters: accept the widest satisfying type
- Return types: the narrowest precise type — never `Any` or untyped
- Errors as `Result[T, E]` — not raised exceptions (for expected failures)

## Python pattern

```python
from typing import Protocol

class OrderRepository(Protocol):
    def find_by_id(self, id: OrderId) -> Order | None: ...
    def save(self, order: Order) -> None: ...


# Fake for testing
class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def find_by_id(self, id: OrderId) -> Order | None:
        return self._store.get(str(id))

    def save(self, order: Order) -> None:
        self._store[str(order.id)] = order
```

## Dependency injection

```python
# Wire at application boundary only
def create_order_service(repo: OrderRepository) -> OrderService:
    return OrderService(repo)
```

## Hard stop

Do not write a concrete class until the interface is defined and tested with a fake.
