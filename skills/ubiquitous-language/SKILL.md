---
name: ubiquitous-language
description: Glossary-first naming enforcer. Use whenever naming anything — class, function, variable, event, file, endpoint, column. Names must come from the domain glossary. Triggers on any naming decision or code generation request.
---

# Ubiquitous language — names from the domain

## Core rule

Every identifier in the codebase must appear verbatim in `docs/domain/glossary.md`.
If a name is not in the glossary, add it to the glossary first, then use it.

## Before naming anything, ask

1. What does a domain expert call this concept?
2. Is there an existing glossary entry? If yes, use it exactly.
3. If no entry exists, draft one and add it before writing code.

## Forbidden naming patterns

| Pattern | Example | Why |
|---------|---------|-----|
| Tech leaking into domain | `PostOrderController` | HTTP verb in domain name |
| Framework in name | `OrderDjangoSerializer` | Framework coupling |
| Abbreviations | `ord_mgr`, `usr_svc` | Ambiguous, not in glossary |
| Generic words | `Manager`, `Handler`, `Processor`, `Util` | Meaningless in domain |
| Synonyms | Using `Client` and `Customer` interchangeably | Must pick one |

## Correct patterns

| Concept | Domain name | Forbidden synonyms |
|---------|-------------|-------------------|
| The person buying | `Customer` | Client, User, Buyer, Person |
| Placing an order | `place_order()` | create_order, submit_order, post_order |
| Order confirmed | `OrderConfirmed` (event) | OrderCreated, OrderSuccess |

## Glossary format (`docs/domain/glossary.md`)

```markdown
## <Term>
**Definition**: One sentence, agreed with domain experts.
**Used in**: <list of contexts>
**Synonyms to avoid**: <list>
```

## Hard stop

If you're about to name something and it's not in the glossary, stop. Add the glossary entry first.
