# ADR 0001 — Mandatory 5-phase SDLC

**Status**: Accepted
**Date**: 2025-01-01

## Context

We want both beginners and experts using AI coding assistants to follow the same engineering discipline automatically. The AI should enforce the process, not just suggest it.

## Decision

Adopt a 5-phase mandatory workflow enforced by `CLAUDE.md` and `.claude/skills/`:

1. Domain doc first (DDD)
2. Ubiquitous language for all names
3. Interface before class (ISP)
4. Failing test before implementation (TDD)
5. Simplicity gate (complexity ≤ 3, pure functions)

The AI will refuse (with explanation) to skip any phase.

## Consequences

- Beginners get guardrails without needing to know the theory
- Experts can override by editing CLAUDE.md
- Pre-commit + CI enforce the same gates locally and on every PR
- The domain glossary becomes the living contract between product and engineering
