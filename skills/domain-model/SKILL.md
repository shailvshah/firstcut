---
name: domain-model
description: DDD domain modeling. Use at the start of every new feature before any code is written. Produces domain glossary entry, aggregate definition, event catalog, and context map before any .py file is created.
---

# Domain model — domain first, always

## Mandatory first output

Before writing any code, produce `docs/domain/<entity-name>.md` with this exact structure:

```markdown
# <EntityName>

## Plain-language definition
One sentence that a non-technical domain expert would agree with.

## Invariants
- What must always be true (enforced by the aggregate root)
- What can never be true

## Commands (inputs)
- <commandName>(<params>) → <result>

## Domain events (outputs, past tense)
- <EntityName><Verb>  e.g. OrderPlaced, PaymentFailed

## Bounded context
- Owner: <context-name>
- Adjacent contexts: <list, how they communicate>

## Glossary entry
Term: <EntityName>
Synonyms to avoid: <list of forbidden synonyms>
Domain expert quote: "<quote that captures the concept>"
```

## Aggregate rules

- Aggregate root is the only mutation entry point
- External code calls methods on the root; never mutates child entities directly
- Root emits domain events; never calls external services directly
- Aggregate enforces all invariants before emitting events

## Bounded context rules

- One model per context — no shared god objects
- Cross-context: events over the wire, or anti-corruption layer
- Each context lives in its own module: `src/<context>/`

## Hard stop

No `.py` file may be created until `docs/domain/<entity>.md` exists and has been reviewed.
