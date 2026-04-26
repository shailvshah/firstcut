#!/usr/bin/env python3
"""
firstcut — first-principles project scaffolder
Run:  python -m firstcut.cli init
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── colour helpers ────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
BLUE = "\033[34m"
GREEN = "\033[32m"
AMBER = "\033[33m"
CYAN = "\033[36m"


def h(text: str) -> str:
    return f"{BOLD}{text}{RESET}"


def dim(text: str) -> str:
    return f"{DIM}{text}{RESET}"


def ok(text: str) -> str:
    return f"{GREEN}✓{RESET} {text}"


def info(text: str) -> str:
    return f"{BLUE}→{RESET} {text}"


def warn(text: str) -> str:
    return f"{AMBER}!{RESET} {text}"


# ── constants ─────────────────────────────────────────────────────────────────
FIRSTCUT_ROOT = Path(__file__).parent.parent.resolve()
FORGE_ROOT = FIRSTCUT_ROOT

PROJECT_TYPES = {
    "backend": "REST/GraphQL API, microservice, worker, data pipeline",
    "frontend": "SPA, SSG, component library, design system",
    "monorepo": "Full-stack with shared types (API + UI + packages)",
    "tooling": "CLI tool, SDK, developer library, scripts",
    "infrastructure": "IaC, platform engineering, Kubernetes, Pulumi/Terraform",
    "docs": "Documentation site (MkDocs / MDX / Docusaurus)",
}

STACKS: dict[str, dict[str, dict[str, str]]] = {
    "backend": {
        "python": {"framework": "fastapi", "pkg": "uv", "ext": "py"},
        "typescript": {"framework": "hono", "pkg": "pnpm", "ext": "ts"},
        "go": {"framework": "gin", "pkg": "go mod", "ext": "go"},
        "rust": {"framework": "axum", "pkg": "cargo", "ext": "rs"},
    },
    "frontend": {
        "typescript": {"framework": "nextjs", "pkg": "pnpm", "ext": "ts"},
        "javascript": {"framework": "vite", "pkg": "pnpm", "ext": "js"},
    },
    "monorepo": {
        "typescript": {"framework": "turborepo", "pkg": "pnpm", "ext": "ts"},
    },
    "tooling": {
        "python": {"framework": "typer", "pkg": "uv", "ext": "py"},
        "typescript": {"framework": "commander", "pkg": "pnpm", "ext": "ts"},
        "go": {"framework": "cobra", "pkg": "go mod", "ext": "go"},
    },
    "infrastructure": {
        "python": {"framework": "pulumi", "pkg": "uv", "ext": "py"},
        "hcl": {"framework": "terraform", "pkg": "none", "ext": "tf"},
    },
    "docs": {
        "python": {"framework": "mkdocs", "pkg": "uv", "ext": "md"},
        "typescript": {"framework": "docusaurus", "pkg": "pnpm", "ext": "md"},
    },
}

SKILLS = [
    ("grill-me", "Socratic challenge — asks hard questions about your design"),
    ("tdd", "Red-green-refactor enforcer — failing test before implementation"),
    ("domain-model", "DDD aggregate + event modeling — domain doc before code"),
    ("ubiquitous-language", "Glossary-first naming — names come from domain experts"),
    ("qa", "QA review + 95% coverage gate"),
    (
        "request-refactor-plan",
        "Refactor-before-implement — plan before changing existing code",
    ),
    ("interface-design", "Interface-before-class enforcer"),
    (
        "implementation-simplicity",
        "Complexity ≤ 3, pure functions, no premature abstraction",
    ),
]

CI_OPTIONS = ["github-actions", "gitlab-ci", "both", "none"]
CANCEL_WORDS = {"cancel", "exit", "quit", "q"}

LICENSES = {
    "MIT": "MIT License",
    "Apache-2.0": "Apache License 2.0",
    "ISC": "ISC License",
    "UNLICENSED": "Private / unlicensed",
}

# ── prompt helpers ────────────────────────────────────────────────────────────


class PromptCancelledError(Exception):
    """Raised when a user cancels an interactive prompt."""


def _raise_if_cancelled(raw: str) -> None:
    if raw.strip().lower() in CANCEL_WORDS:
        raise PromptCancelledError("Aborted.")


def prompt(question: str, default: str, choices: list[str] | None = None) -> str:
    choices_display = [*choices, "cancel"] if choices else ["cancel"]
    choices_str = f" [{'/'.join(choices_display)}]"
    default_str = f" {dim(f'(default: {default})')}"
    while True:
        raw = input(f"\n{question}{choices_str}{default_str}: ").strip()
        _raise_if_cancelled(raw)
        val = raw or default
        if choices and val not in choices:
            print(warn(f"Please choose one of: {', '.join(choices)}"))
            continue
        return val


def prompt_multi(
    question: str, options: list[tuple[str, str]], default_all: bool = True
) -> list[str]:
    print(f"\n{question}")
    for i, (key, desc) in enumerate(options, 1):
        print(f"  {dim(str(i) + '.')} {h(key)} — {desc}")
    default_label = "all" if default_all else "none"
    raw = input(
        "\n  Enter numbers to toggle off (comma-separated), "
        f"press Enter to keep {default_label}, or type cancel: "
    ).strip()
    _raise_if_cancelled(raw)
    if not raw:
        return [k for k, _ in options] if default_all else []
    excluded = {int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()}
    return [k for i, (k, _) in enumerate(options) if i not in excluded]


def confirm(question: str, default: bool = True) -> bool:
    suffix = dim("(Y/n)") if default else dim("(y/N)")
    raw = input(f"\n{question} {suffix}, or cancel: ").strip().lower()
    _raise_if_cancelled(raw)
    if not raw:
        return default
    return raw.startswith("y")


# ── config dataclass ──────────────────────────────────────────────────────────


@dataclass
class ForgeConfig:
    project_type: str = "backend"
    language: str = "python"
    framework: str = "fastapi"
    pkg_manager: str = "uv"
    ext: str = "py"
    project_name: str = "my-project"
    org: str = "my-org"
    description: str = "A well-crafted project"
    license: str = "MIT"
    ci: list[str] = field(default_factory=lambda: ["github-actions"])
    skills: list[str] = field(default_factory=lambda: [k for k, _ in SKILLS])
    init_git: bool = True
    include_docs_submodule: bool = True
    output_dir: Path = field(default_factory=lambda: Path.cwd().parent)

    @property
    def slug(self) -> str:
        return self.project_name.lower().replace(" ", "-")

    @property
    def dest(self) -> Path:
        return self.output_dir / self.slug


# ── step implementations ──────────────────────────────────────────────────────


def step1_project_type(cfg: ForgeConfig) -> None:
    print(f"\n{h('─── Step 1 of 4 — Project type ───────────────────────────────')}")
    for key, desc in PROJECT_TYPES.items():
        print(f"  {h(key):<18} {desc}")
    cfg.project_type = prompt("Project type", "backend", list(PROJECT_TYPES))


def step2_stack(cfg: ForgeConfig) -> None:
    print(f"\n{h('─── Step 2 of 4 — Stack ──────────────────────────────────────')}")
    available = STACKS.get(cfg.project_type, STACKS["backend"])
    langs = list(available.keys())
    default_lang = langs[0]

    print(f"  Available languages: {', '.join(langs)}")
    cfg.language = prompt("Language", default_lang, langs)

    stack = available[cfg.language]
    cfg.framework = prompt("Framework", stack["framework"])
    cfg.pkg_manager = prompt("Package manager", stack["pkg"])
    cfg.ext = stack["ext"]

    ci_raw = prompt("CI target", "github-actions", CI_OPTIONS)
    cfg.ci = (
        ["github-actions", "gitlab-ci"]
        if ci_raw == "both"
        else ([] if ci_raw == "none" else [ci_raw])
    )


def step3_metadata(cfg: ForgeConfig) -> None:
    print(f"\n{h('─── Step 3 of 4 — Project metadata ───────────────────────────')}")
    cfg.project_name = prompt("Project name", "my-project")
    cfg.org = prompt("Organisation / owner", "my-org")
    cfg.description = prompt("One-line description", "A well-crafted project")
    cfg.license = prompt("License", "MIT", list(LICENSES))
    out_raw = prompt("Output directory", str(Path.cwd().parent))
    cfg.output_dir = Path(out_raw).expanduser().resolve()


def step4_skills(cfg: ForgeConfig) -> None:
    print(f"\n{h('─── Step 4 of 4 — AI skills ──────────────────────────────────')}")
    print(dim("  All skills are enabled by default (recommended for beginners)."))
    cfg.skills = prompt_multi("Select skills to include:", SKILLS, default_all=True)
    cfg.init_git = confirm("Initialise a git repo?", default=True)
    cfg.include_docs_submodule = confirm(
        "Include docs/ as a submodule scaffold?", default=True
    )


# ── file writers ──────────────────────────────────────────────────────────────


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write_claude_md(cfg: ForgeConfig) -> None:
    skills_list = "\n".join(f"- **{s}** → `skills/{s}/SKILL.md`" for s in cfg.skills)
    write(
        cfg.dest / "CLAUDE.md",
        f"""# {cfg.slug}

> {cfg.description}

## Project context

| Field | Value |
|-------|-------|
| Type | {cfg.project_type} |
| Language | {cfg.language} |
| Framework | {cfg.framework} |
| Package manager | {cfg.pkg_manager} |
| Owner | {cfg.org} |
| License | {cfg.license} |

---

## Mandatory engineering workflow

Claude must follow these phases **in order** for every new feature.
Skipping a phase is not permitted.

```
1. Domain first      →  read skills/domain-model/SKILL.md
                         produce docs/domain/<entity>.md before any code
2. Name from glossary→  read skills/ubiquitous-language/SKILL.md
3. Interface first   →  read skills/interface-design/SKILL.md
4. Failing test first→  read skills/tdd/SKILL.md
5. Implement simply  →  read skills/implementation-simplicity/SKILL.md
6. QA review         →  read skills/qa/SKILL.md
```

## Hard stops — Claude must refuse and explain

- Writing a class or function before a domain doc exists
- Writing implementation before a **failing** test exists
- Naming anything that is not in `docs/domain/glossary.md`
- Functions with cyclomatic complexity > 3
- Any untyped return (`any`, `object`, untyped)
- Mixing I/O and computation in one function
- Mocking pure functions in tests
- Merging code with < 95% test coverage

---

## AI skill manifest

{skills_list}

---

## Useful commands

```bash
# Install dependencies
{_install_cmd(cfg)}

# Dev server / run
{_dev_cmd(cfg)}

# Test
{_test_cmd(cfg)}

# Lint + format
{_lint_cmd(cfg)}

# Type check
{_typecheck_cmd(cfg)}
```

---

## Coding conventions

- All new features start with a failing test (TDD)
- Domain glossary is updated before naming anything
- Every PR links to an issue
- Never push directly to `main`
- Commit messages follow Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`
""",
    )


def _install_cmd(cfg: ForgeConfig) -> str:
    return {
        "uv": "uv sync",
        "poetry": "poetry install",
        "pnpm": "pnpm install",
        "npm": "npm install",
        "cargo": "cargo build",
        "go mod": "go mod download",
    }.get(cfg.pkg_manager, "install deps")


def _dev_cmd(cfg: ForgeConfig) -> str:
    if cfg.pkg_manager == "poetry":
        fw_map = {
            "fastapi": "poetry run uvicorn src.main:app --reload",
            "mkdocs": "poetry run mkdocs serve",
        }
        return fw_map.get(cfg.framework, "poetry run python -m src.main")
    m = {
        "fastapi": "uvicorn src.main:app --reload",
        "nextjs": "pnpm dev",
        "hono": "pnpm dev",
        "gin": "go run ./cmd/server",
        "mkdocs": "mkdocs serve",
    }
    return m.get(cfg.framework, f"{cfg.pkg_manager} run dev")


def _test_cmd(cfg: ForgeConfig) -> str:
    return {
        "uv": "uv run pytest --cov=src --cov-fail-under=95",
        "poetry": "poetry run pytest --cov=src --cov-fail-under=95",
        "pnpm": "pnpm test",
        "go mod": "go test ./... -cover",
        "cargo": "cargo test",
    }.get(cfg.pkg_manager, "run tests")


def _lint_cmd(cfg: ForgeConfig) -> str:
    return {
        "uv": "uv run ruff check . && uv run black .",
        "poetry": "poetry run ruff check . && poetry run black .",
        "pnpm": "pnpm lint",
        "go mod": "golangci-lint run",
        "cargo": "cargo clippy",
    }.get(cfg.pkg_manager, "run lint")


def _typecheck_cmd(cfg: ForgeConfig) -> str:
    return {
        "uv": "uv run mypy src/",
        "poetry": "poetry run mypy src/",
        "pnpm": "pnpm typecheck",
        "go mod": "go vet ./...",
    }.get(cfg.pkg_manager, "run typecheck")


def write_skills(cfg: ForgeConfig) -> None:
    skills_content = _build_skills(cfg)
    for skill_name, content in skills_content.items():
        if skill_name in cfg.skills:
            write(cfg.dest / "skills" / skill_name / "SKILL.md", content)


def _build_skills(cfg: ForgeConfig) -> dict[str, str]:
    lang = cfg.language
    ext = cfg.ext
    test_ext = {
        "py": "_test.py",
        "ts": ".test.ts",
        "go": "_test.go",
        "rs": "_test.rs",
    }.get(ext, f".test.{ext}")
    runner = {"py": "pytest", "ts": "vitest", "go": "go test", "rs": "cargo test"}.get(
        ext, "test runner"
    )

    return {
        "grill-me": """---
name: grill-me
description: Socratic design challenge. Use when the user asks you to review, challenge, or stress-test a design, architecture decision, or implementation plan. Ask hard questions before validating anything.
---

# Grill me

When invoked, you are a skeptical senior engineer. Your job is to find every weak assumption before a line of code is written.

## Process

1. Read the design or plan the user presents
2. Identify the 3-5 hardest questions — the ones the user probably hasn't thought about
3. Ask them one at a time, waiting for answers before moving on
4. Only when you're satisfied with the answers, summarise what you've validated and what remains a risk

## Question categories to cover

- **Invariants**: What can never be true? What must always be true?
- **Failure modes**: What happens when this fails? How does the caller know?
- **Boundaries**: Where does this module's responsibility end?
- **Scaling**: What breaks first under load?
- **Reversibility**: Can this decision be undone cheaply?
- **Naming**: Does this name mean the same thing to a domain expert?

## Tone

Direct and Socratic. Not hostile. The goal is to make the design stronger, not to win an argument.

## Hard stop

Do not validate a design until you've asked at least 3 hard questions and received answers.
""",
        "tdd": f"""---
name: tdd
description: Red-green-refactor enforcer. Use for every new function, method, or behaviour. Always write a failing test first. Never write implementation without a red test. Triggers on any request to implement a feature, fix a bug, or add a method.
---

# TDD — red, green, refactor

## Non-negotiable sequence

1. Write ONE failing test (red) — run it — confirm it fails
2. Write MINIMAL code to pass — run it — confirm green
3. Refactor names and duplication — stay green throughout

Never write step 2 before step 1 is confirmed red.

## Test anatomy ({lang})

```{ext}
# Arrange
{"order = Order.empty()" if lang == "python" else "const order = Order.empty()"}
{'item = Item.create("book", 9.99)' if lang == "python" else "const item = Item.create('book', 9.99)"}

# Act
{"result = order.add_item(item)" if lang == "python" else "const result = order.addItem(item)"}

# Assert
{"assert result.item_count == 1" if lang == "python" else "expect(result.itemCount).toBe(1)"}
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

Co-locate: `order.{ext}` → `order{test_ext}` in the same directory.
Integration/e2e tests only → `tests/integration/` or `tests/e2e/`

## Coverage gate

`{runner}` must report ≥ 95% line coverage. CI will fail below this threshold.

## Hard stop

If no failing test exists, refuse to write implementation. Ask the user to write the test first.
""",
        "domain-model": f"""---
name: domain-model
description: DDD domain modeling. Use at the start of every new feature before any code is written. Produces domain glossary entry, aggregate definition, event catalog, and context map before any .{ext} file is created.
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

No `.{ext}` file may be created until `docs/domain/<entity>.md` exists and has been reviewed.
""",
        "ubiquitous-language": """---
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
| Placing an order | `placeOrder()` | createOrder, submitOrder, postOrder |
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
""",
        "qa": f"""---
name: qa
description: QA review skill. Use before any PR is created, before merging, or when the user asks for a quality review. Checks coverage, types, edge cases, and domain correctness.
---

# QA review

## QA checklist (run in order)

### 1. Coverage gate
```bash
{runner} {"--cov=src --cov-fail-under=95 --cov-report=term-missing" if lang == "python" else "--coverage"}
```
Must be ≥ 95%. List any uncovered lines and ask the user to add tests before proceeding.

### 2. Type safety
```bash
{"uv run mypy src/ --strict" if lang == "python" else "pnpm typecheck" if lang == "typescript" else "go vet ./..."}
```
Zero type errors. No `{"Any" if lang == "python" else "any"}` escapes.

### 3. Lint + format
```bash
{"uv run ruff check . && uv run black --check ." if lang == "python" else "pnpm lint"}
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

Produce a QA report:

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
""",
        "request-refactor-plan": """---
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
""",
        "interface-design": f"""---
name: interface-design
description: Interface-before-class enforcer. Use at the start of any new module, service, or component. The interface/protocol/trait must be written and tested before the concrete implementation exists. Triggers on any request to create a new service, repository, gateway, or component.
---

# Interface-first design

## Mandatory sequence

1. Write the interface / protocol / trait
2. Write tests against the interface using a fake implementation
3. Write the concrete implementation
4. Wire the concrete implementation via dependency injection

Never write step 3 before step 2 is green.

## Interface rules

- One responsibility per interface (Interface Segregation Principle)
- Max 3–5 methods per interface — if more, split
- No infrastructure types in domain interfaces:
  - ✗ HTTP `Request`/`Response`
  - ✗ ORM model objects (`Document`, `Row`)
  - ✗ Framework-specific types
- Parameters: accept the widest satisfying type
- Return types: the narrowest precise type — never `{"Any" if lang == "python" else "any"}` or untyped
- Errors as `Result[T, E]` — not raised exceptions (for expected failures)

## {lang.title()} pattern

```{ext}
{"# Interface" if lang == "python" else "// Interface"}
{"from typing import Protocol" if lang == "python" else ""}

{"class OrderRepository(Protocol):" if lang == "python" else "interface OrderRepository {"}
{"    def find_by_id(self, id: OrderId) -> Order | None: ..." if lang == "python" else "  findById(id: OrderId): Promise<Order | null>"}
{"    def save(self, order: Order) -> None: ..." if lang == "python" else "  save(order: Order): Promise<void>"}
{"}" if lang == "typescript" else ""}

{"# Fake for testing" if lang == "python" else "// Fake for testing"}
{"class InMemoryOrderRepository:" if lang == "python" else "class InMemoryOrderRepository implements OrderRepository {"}
{"    def __init__(self) -> None:" if lang == "python" else "  private store = new Map<string, Order>()"}
{"        self._store: dict[str, Order] = {}" if lang == "python" else ""}
{"    def find_by_id(self, id: OrderId) -> Order | None:" if lang == "python" else "  async findById(id: OrderId) {"}
{"        return self._store.get(str(id))" if lang == "python" else "    return this.store.get(id.value) ?? null"}
{"}" if lang == "typescript" else ""}
```

## Dependency injection

```{ext}
{"# Wire at application boundary only" if lang == "python" else "// Wire at application boundary only"}
{"def create_order_service(repo: OrderRepository) -> OrderService:" if lang == "python" else "function createOrderService(repo: OrderRepository): OrderService {"}
{"    return OrderService(repo)" if lang == "python" else "  return new OrderService(repo)"}
{"}" if lang == "typescript" else ""}
```

## Hard stop

Do not write a concrete class until the interface is defined and tested with a fake.
""",
        "implementation-simplicity": f"""---
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

Count complexity: each `{"if/elif/else/for/while/except/and/or" if lang == "python" else "if/else/for/while/catch/&&/||"}` adds 1.

## Purity

Separate computation from I/O — always:

```{ext}
{"# Pure — always testable, no mocks needed" if lang == "python" else "// Pure — always testable, no mocks needed"}
{"def calculate_total(items: list[Item]) -> Money:" if lang == "python" else "function calculateTotal(items: Item[]): Money {"}
{"    return sum(item.price for item in items)" if lang == "python" else "  return items.reduce((sum, i) => sum + i.price, 0 as Money)"}
{"}" if lang == "typescript" else ""}

{"# Side effect — explicit, named with verb" if lang == "python" else "// Side effect — explicit, named with verb"}
{"async def save_order(order: Order, repo: OrderRepository) -> None:" if lang == "python" else "async function saveOrder(order: Order, repo: OrderRepository): Promise<void> {"}
{"    await repo.save(order)" if lang == "python" else "  await repo.save(order)"}
{"}" if lang == "typescript" else ""}
```

## Error handling

Explicit, typed, never silent:

```{ext}
{"from result import Result, Ok, Err" if lang == "python" else "import { Result } from 'neverthrow'"}

{"def parse_date(s: str) -> Result[date, ParseError]:" if lang == "python" else "function parseDate(s: string): Result<Date, ParseError> {"}
{"    try:" if lang == "python" else ""}
{"        return Ok(date.fromisoformat(s))" if lang == "python" else "  const d = new Date(s); return isNaN(d.getTime()) ? err(new ParseError(s)) : ok(d)"}
{"    except ValueError as e:" if lang == "python" else ""}
{"        return Err(ParseError(str(e)))" if lang == "python" else ""}
```

## Dependency injection

```{ext}
{"# Never: new inside a function" if lang == "python" else "// Never: new inside a function"}
{"# Always: injected at construction" if lang == "python" else "// Always: injected at construction"}
{"def create_order_service(" if lang == "python" else "function createOrderService("}
{"    repo: OrderRepository," if lang == "python" else "  repo: OrderRepository,"}
{"    events: EventBus," if lang == "python" else "  events: EventBus,"}
{") -> OrderService:" if lang == "python" else "): OrderService {"}
{"    return OrderService(repo, events)" if lang == "python" else "  return new OrderService(repo, events)"}
{"}" if lang == "typescript" else ""}
```

## Abstraction discipline (rule of three)

- Copy once: leave the duplication
- Copy twice: still leave it
- Copy three times: now extract

Premature abstraction costs more than duplication.

## Complexity red flags — stop and refactor

- Nested `if` beyond 2 levels → extract a guard clause
- Function longer than 20 lines → split at the natural seam
- More than 3 parameters → use an options/config object
- A comment explaining **what** the code does → rename instead
- `{"Any" if lang == "python" else "any"}` type anywhere → type it properly
- Logic and I/O in the same function → split them

## Hard stop

Refuse to merge any function with complexity > 3. Ask the user to split it first.
""",
    }


def write_precommit(cfg: ForgeConfig) -> None:
    if cfg.language == "python":
        runner = "poetry run" if cfg.pkg_manager == "poetry" else "uv run"
        content = f"""repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        args: [--strict]
        additional_dependencies:
          - types-all

  - repo: local
    hooks:
      - id: pytest-coverage
        name: pytest coverage gate (95%)
        entry: {runner} pytest --cov=src --cov-fail-under=95 -q
        language: system
        pass_filenames: false
        always_run: true

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.24.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
"""
    elif cfg.language == "typescript":
        content = """repos:
  - repo: local
    hooks:
      - id: prettier
        name: Prettier format check
        entry: pnpm prettier --check .
        language: system
        pass_filenames: false

      - id: eslint
        name: ESLint
        entry: pnpm lint
        language: system
        pass_filenames: false

      - id: tsc
        name: TypeScript type check
        entry: pnpm typecheck
        language: system
        pass_filenames: false

      - id: vitest-coverage
        name: Vitest coverage gate (95%)
        entry: pnpm coverage
        language: system
        pass_filenames: false
        always_run: true

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.24.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
"""
    elif cfg.language == "go":
        content = """repos:
  - repo: local
    hooks:
      - id: gofmt
        name: gofmt
        entry: gofmt -l -w .
        language: system
        pass_filenames: false

      - id: golangci-lint
        name: golangci-lint
        entry: golangci-lint run
        language: system
        pass_filenames: false

      - id: go-test-coverage
        name: Go test coverage gate (80%)
        entry: bash -c 'go test ./... -coverprofile=coverage.out && go tool cover -func=coverage.out | awk '"'"'END{if ($3+0 < 80) {print "Coverage "$3" < 80%"; exit 1}}'"'"
        language: system
        pass_filenames: false
        always_run: true

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.24.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
"""
    elif cfg.language == "rust":
        content = """repos:
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt --all -- --check
        language: system
        pass_filenames: false

      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy --all-targets --all-features -- -D warnings
        language: system
        pass_filenames: false

      - id: cargo-test
        name: cargo test
        entry: cargo test
        language: system
        pass_filenames: false
        always_run: true

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.24.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
"""
    elif cfg.language == "hcl":
        content = """repos:
  - repo: local
    hooks:
      - id: terraform-fmt
        name: terraform fmt
        entry: terraform fmt -recursive -check
        language: system
        pass_filenames: false

      - id: terraform-validate
        name: terraform validate
        entry: bash -c 'for d in stacks/*/; do terraform -chdir="$d" init -backend=false -input=false && terraform -chdir="$d" validate; done'
        language: system
        pass_filenames: false

      - id: tflint
        name: tflint
        entry: tflint --recursive
        language: system
        pass_filenames: false

      - id: checkov
        name: checkov security scan
        entry: checkov -d . --quiet
        language: system
        pass_filenames: false

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.24.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
"""
    else:
        content = """repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.24.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
"""
    write(cfg.dest / ".pre-commit-config.yaml", content)


_HELP_AWK = (
    r"""@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ """
    r"""{ printf "  \033[36m%-18s\033[0m %s\n", $1, $2 }' $(MAKEFILE_LIST)"""
)

# detect-secrets targets shared by every stack
_SECRETS_TARGETS = """\
secrets-init: ## Create .secrets.baseline (run once after cloning)
\tdetect-secrets scan > .secrets.baseline

secrets: ## Scan for new secrets against baseline
\tdetect-secrets scan --baseline .secrets.baseline
"""


def write_makefile(cfg: ForgeConfig) -> None:
    """Generate a stack-aware Makefile whose quality target mirrors pre-commit."""

    if cfg.language == "python":
        runner = "poetry run" if cfg.pkg_manager == "poetry" else "uv run"
        install = (
            "poetry install" if cfg.pkg_manager == "poetry" else "uv sync --all-extras"
        )
        content = f""".DEFAULT_GOAL := help
.PHONY: help install lint format format-check typecheck test secrets-init secrets quality dev

RUNNER = {runner}

help: ## Show available targets
\t{_HELP_AWK}

install: ## Install dependencies
\t{install}

lint: ## ruff check (zero warnings)
\t$(RUNNER) ruff check .

format: ## Auto-format with ruff + black
\t$(RUNNER) ruff format .
\t$(RUNNER) black .

format-check: ## Check formatting without writing
\t$(RUNNER) ruff format --check .
\t$(RUNNER) black --check .

typecheck: ## mypy --strict
\t$(RUNNER) mypy src/ --strict

test: ## pytest — 95% coverage gate (threshold in pyproject.toml)
\t$(RUNNER) pytest

{_SECRETS_TARGETS}
quality: lint format-check typecheck test secrets ## All gates: matches pre-commit hooks

dev: ## Start development server
\t$(RUNNER) uvicorn src.main:app --reload
"""

    elif cfg.language == "typescript" and cfg.project_type == "monorepo":
        content = f""".DEFAULT_GOAL := help
.PHONY: help install lint format format-check typecheck test secrets-init secrets quality dev build

help: ## Show available targets
\t{_HELP_AWK}

install: ## Install all workspace dependencies
\tpnpm install

lint: ## ESLint across all packages
\tpnpm turbo lint

format: ## Prettier auto-fix
\tpnpm prettier --write "**/*.{{ts,tsx,md}}"

format-check: ## Check formatting without writing
\tpnpm prettier --check "**/*.{{ts,tsx,md}}"

typecheck: ## TypeScript check across all packages
\tpnpm turbo typecheck

test: ## Tests across all packages — 95% coverage threshold in vitest.config.ts
\tpnpm turbo test

build: ## Build all packages
\tpnpm turbo build

{_SECRETS_TARGETS}
quality: lint format-check typecheck test secrets ## All gates: matches pre-commit hooks

dev: ## Start all dev servers
\tpnpm turbo dev
"""

    elif cfg.language == "typescript":
        dev_cmd = "pnpm dev"
        content = f""".DEFAULT_GOAL := help
.PHONY: help install lint format format-check typecheck test secrets-init secrets quality dev build

help: ## Show available targets
\t{_HELP_AWK}

install: ## Install dependencies
\tpnpm install

lint: ## ESLint (zero warnings)
\tpnpm lint

format: ## Prettier auto-fix
\tpnpm format

format-check: ## Check formatting without writing
\tpnpm prettier --check .

typecheck: ## TypeScript type check
\tpnpm typecheck

test: ## Vitest — 95% coverage threshold enforced via vitest.config.ts
\tpnpm coverage

build: ## Production build
\tpnpm build

{_SECRETS_TARGETS}
quality: lint format-check typecheck test secrets ## All gates: matches pre-commit hooks

dev: ## Start dev server
\t{dev_cmd}
"""

    elif cfg.language == "go":
        content = f""".DEFAULT_GOAL := help
.PHONY: help deps lint format test coverage secrets-init secrets quality run

COVERAGE_THRESHOLD = 80

help: ## Show available targets
\t{_HELP_AWK}

deps: ## Download and tidy dependencies
\tgo mod download
\tgo mod tidy

lint: ## golangci-lint (zero warnings)
\tgolangci-lint run

format: ## gofmt auto-fix
\tgofmt -l -w .

test: ## go test with race detector and 80% coverage gate
\tgo test ./... -race -coverprofile=coverage.out
\t@go tool cover -func=coverage.out | \
\t  awk 'END{{if ($$3+0 < $(COVERAGE_THRESHOLD)) {{print "Coverage " $$3 " < $(COVERAGE_THRESHOLD)%"; exit 1}}}}'

coverage: test ## Open HTML coverage report
\tgo tool cover -html=coverage.out -o coverage.html
\topen coverage.html

{_SECRETS_TARGETS}
quality: format lint test secrets ## All gates: matches pre-commit hooks

run: ## Run the server
\tgo run ./cmd/server/...
"""

    elif cfg.language == "rust":
        content = f""".DEFAULT_GOAL := help
.PHONY: help build lint format format-check test secrets-init secrets quality run

help: ## Show available targets
\t{_HELP_AWK}

build: ## cargo build
\tcargo build

lint: ## cargo clippy — zero warnings
\tcargo clippy --all-targets --all-features -- -D warnings

format: ## cargo fmt auto-fix
\tcargo fmt

format-check: ## Check formatting without writing
\tcargo fmt --check

test: ## cargo test
\tcargo test

{_SECRETS_TARGETS}
quality: format-check lint test secrets ## All gates: matches pre-commit hooks

run: ## cargo run
\tcargo run
"""

    elif cfg.language == "hcl":
        content = f""".DEFAULT_GOAL := help
.PHONY: help fmt fmt-check validate lint scan secrets-init secrets plan apply quality

ENV ?= dev

help: ## Show available targets
\t{_HELP_AWK}

fmt: ## terraform fmt -recursive (auto-fix)
\tterraform fmt -recursive

fmt-check: ## Check formatting without writing
\tterraform fmt -recursive -check

validate: ## terraform validate for each stack
\t@for d in stacks/*/; do \
\t\techo "Validating $$d ..."; \
\t\tterraform -chdir="$$d" init -backend=false -input=false -reconfigure && \
\t\tterraform -chdir="$$d" validate; \
\tdone

lint: ## tflint recursive
\ttflint --recursive

scan: ## checkov security scan
\tcheckov -d . --quiet

{_SECRETS_TARGETS}
quality: fmt-check validate lint scan secrets ## All gates: matches pre-commit hooks

plan: ## terraform plan (ENV=dev|staging|prod)
\tcd stacks/$(ENV) && terraform init && terraform plan

apply: ## terraform apply (ENV=dev|staging|prod)
\tcd stacks/$(ENV) && terraform init && terraform apply
"""

    else:
        content = f""".DEFAULT_GOAL := help
.PHONY: help secrets-init secrets quality

help: ## Show available targets
\t{_HELP_AWK}

{_SECRETS_TARGETS}
quality: secrets ## Run all quality gates
"""

    write(cfg.dest / "Makefile", content)


def write_github_ci(cfg: ForgeConfig) -> None:
    if cfg.language == "python":
        if cfg.pkg_manager == "poetry":
            setup = """      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest
          virtualenvs-in-project: true
      - name: Install dependencies
        run: poetry install --no-interaction"""
            runner = "poetry run"
        else:
            setup = """      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync --all-extras"""
            runner = "uv run"
        lint = f"{runner} ruff check . && {runner} black --check ."
        types = f"{runner} mypy src/ --strict"
        test = f"{runner} pytest --cov=src --cov-fail-under=95 --cov-report=xml -q"
        cov_upload = """      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml"""
    elif cfg.language == "typescript":
        setup = """      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - name: Install pnpm
        run: npm i -g pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile"""
        lint = "pnpm lint"
        types = "pnpm typecheck"
        test = "pnpm test --coverage"
        cov_upload = ""
    else:
        setup = """      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Download modules
        run: go mod download"""
        lint = "golangci-lint run"
        types = "go vet ./..."
        test = "go test ./... -coverprofile=coverage.out && go tool cover -func=coverage.out"
        cov_upload = ""

    write(
        cfg.dest / ".github" / "workflows" / "ci.yml",
        f"""name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

concurrency:
  group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  quality:
    name: Quality gates
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

{setup}

      - name: Lint & format
        run: {lint}

      - name: Type check
        run: {types}

      - name: Test + coverage (≥ 95%)
        run: {test}
{cov_upload}

      - name: Check commit messages
        uses: wagoid/commitlint-github-action@v6
""",
    )

    write(
        cfg.dest / ".github" / "workflows" / "release.yml",
        """name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    name: Release
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        uses: orhun/git-cliff-action@v3
        with:
          config: cliff.toml

      - name: Create GitHub release
        uses: softprops/action-gh-release@v2
        with:
          body_path: CHANGELOG.md
          generate_release_notes: true
""",
    )


def write_gitlab_ci(cfg: ForgeConfig) -> None:
    if cfg.language == "python":
        image = "python:3.12-slim"
        if cfg.pkg_manager == "poetry":
            install = "pip install poetry && poetry install --no-interaction"
            runner = "poetry run"
        else:
            install = "pip install uv && uv sync --all-extras"
            runner = "uv run"
        lint = f"{runner} ruff check . && {runner} black --check ."
        types = f"{runner} mypy src/ --strict"
        test = f"{runner} pytest --cov=src --cov-fail-under=95 -q"
    elif cfg.language == "typescript":
        image = "node:22-alpine"
        install = "npm i -g pnpm && pnpm install --frozen-lockfile"
        lint = "pnpm lint"
        types = "pnpm typecheck"
        test = "pnpm test --coverage"
    else:
        image = "golang:1.22"
        install = "go mod download"
        lint = "golangci-lint run"
        types = "go vet ./..."
        test = "go test ./... -cover"

    write(
        cfg.dest / ".gitlab-ci" / "ci.yml",
        f"""image: {image}

stages:
  - quality
  - test
  - release

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/

lint:
  stage: quality
  script:
    - {install}
    - {lint}
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

typecheck:
  stage: quality
  script:
    - {install}
    - {types}
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

test:
  stage: test
  script:
    - {install}
    - {test}
  coverage: '/TOTAL.*\\s+(\\d+%)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
""",
    )


def write_docs(cfg: ForgeConfig) -> None:
    docs = cfg.dest / "docs"
    write(
        docs / "domain" / "glossary.md",
        f"""# Domain glossary — {cfg.slug}

> This file is the single source of truth for all names in the codebase.
> Every class, function, variable, and event name must appear here before it is used.
> Updated by the `ubiquitous-language` skill.

---

## How to add an entry

```markdown
## <Term>
**Definition**: One sentence, agreed with domain experts.
**Used in**: <list of bounded contexts>
**Synonyms to avoid**: <list — never use these>
```

---

<!-- Add domain terms below this line -->
""",
    )

    write(
        docs / "CONTRIBUTING.md",
        f"""# Contributing to {cfg.slug}

## Before you write any code

1. Check `docs/domain/glossary.md` — is the concept already named?
2. If not, add a glossary entry first
3. Write the domain doc: `docs/domain/<entity>.md`
4. Write the interface
5. Write the failing test
6. Then implement

## Pre-commit hooks

Install hooks after cloning:

```bash
pip install pre-commit
pre-commit install --hook-type commit-msg
pre-commit install
```

All hooks must pass before a commit is accepted.

## PR checklist

- [ ] Domain glossary updated (if new names introduced)
- [ ] Tests pass locally
- [ ] Coverage ≥ 95%
- [ ] No type errors
- [ ] Commit messages follow Conventional Commits
- [ ] PR description links to an issue
""",
    )

    write(
        docs / "ADR" / "0001-first-principles-sdlc.md",
        """# ADR 0001 — First-principles SDLC

**Status**: Accepted  
**Date**: 2025-01-01

## Context

We want every contributor — beginner or expert — to follow the same engineering discipline without needing to memorise it. AI assistants (Claude Code, Codex, etc.) should enforce the process automatically.

## Decision

We adopt a mandatory 5-phase workflow enforced by `.claude/skills/` and `CLAUDE.md`:

1. Domain doc first (DDD)
2. Ubiquitous language for all names
3. Interface before class
4. Failing test before implementation (TDD)
5. Simplicity gate (cyclomatic complexity ≤ 3)

## Consequences

- AI assistants will refuse to generate code that skips a phase
- Pre-commit hooks enforce coverage (95%), types, and lint locally
- CI enforces the same gates on every PR
- Beginners get guardrails; experts can always override manually
""",
    )


def write_agents_md(cfg: ForgeConfig) -> None:
    skills_list = "\n".join(f"- {s} → `skills/{s}/SKILL.md`" for s in cfg.skills)
    write(
        cfg.dest / "AGENTS.md",
        f"""# {cfg.slug}

> {cfg.description}

## Project context

| Field | Value |
|-------|-------|
| Type | {cfg.project_type} |
| Language | {cfg.language} |
| Framework | {cfg.framework} |
| Owner | {cfg.org} |

---

## Mandatory engineering workflow

Follow these phases **in order** for every new feature. Skipping a phase is not permitted.

1. **Domain first** — produce `docs/domain/<entity>.md` before any code (read `skills/domain-model/SKILL.md`)
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

{skills_list}

---

## Useful commands

```bash
{_install_cmd(cfg)}
{_test_cmd(cfg)}
{_lint_cmd(cfg)}
{_typecheck_cmd(cfg)}
```
""",
    )


def _ai_rules_body(cfg: ForgeConfig) -> str:
    skills_str = "\n".join(f"- {s}: skills/{s}/SKILL.md" for s in cfg.skills)
    return f"""You are working on a {cfg.project_type} project: {cfg.slug}
Language: {cfg.language} / {cfg.framework}

## Mandatory workflow (every new feature, in order)

1. Write domain doc → docs/domain/<entity>.md  (skills/domain-model/SKILL.md)
2. Add names to glossary → docs/domain/glossary.md  (skills/ubiquitous-language/SKILL.md)
3. Design interface before class  (skills/interface-design/SKILL.md)
4. Write failing test first  (skills/tdd/SKILL.md)
5. Implement minimally  (skills/implementation-simplicity/SKILL.md)
6. QA review before PR  (skills/qa/SKILL.md)

## Hard stops — refuse and explain if

- A class/function is requested before a domain doc exists
- Implementation is requested before a failing test exists
- A name is used that is not in docs/domain/glossary.md
- A function has cyclomatic complexity > 3
- Code coverage is below 95%

## Skills

{skills_str}

## Commands

install:    {_install_cmd(cfg)}
test:       {_test_cmd(cfg)}
lint:       {_lint_cmd(cfg)}
typecheck:  {_typecheck_cmd(cfg)}
"""


def write_cursorrules(cfg: ForgeConfig) -> None:
    write(cfg.dest / ".cursorrules", _ai_rules_body(cfg))


def write_windsurfrules(cfg: ForgeConfig) -> None:
    write(cfg.dest / ".windsurfrules", _ai_rules_body(cfg))


def write_gitignore(cfg: ForgeConfig) -> None:
    ignores = {
        "python": """__pycache__/
*.py[cod]
*.egg-info/
.venv/
.uv/
dist/
build/
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/
coverage.xml
.coverage
.secrets.baseline
# poetry
.poetry/
""",
        "typescript": """node_modules/
dist/
.next/
.turbo/
coverage/
*.tsbuildinfo
.env.local
""",
        "go": """/bin/
*.exe
*.test
coverage.out
""",
    }
    common = """.DS_Store
.env
.env.*
!.env.example
*.log
.idea/
.vscode/
"""
    write(cfg.dest / ".gitignore", ignores.get(cfg.language, "") + common)


def write_readme(cfg: ForgeConfig) -> None:
    write(
        cfg.dest / "README.md",
        f"""# {cfg.slug}

> {cfg.description}

## Overview

| | |
|-|-|
| Type | {cfg.project_type} |
| Language | {cfg.language} / {cfg.framework} |
| License | {cfg.license} |
| Owner | {cfg.org} |

## Getting started

```bash
# 1. Install dependencies
{_install_cmd(cfg)}

# 2. Install pre-commit hooks (first time only)
pip install pre-commit
pre-commit install --hook-type commit-msg
pre-commit install

# 3. Run tests
{_test_cmd(cfg)}

# 4. Start dev server
{_dev_cmd(cfg)}
```

## Project structure

See `CLAUDE.md` for the full project map and AI skill manifest.

## Contributing

See `docs/CONTRIBUTING.md`.

## Engineering workflow

This project enforces a mandatory 5-phase SDLC via AI skills:

1. **Domain doc first** — every feature starts with `docs/domain/<entity>.md`
2. **Name from glossary** — every identifier comes from `docs/domain/glossary.md`
3. **Interface before class** — design the contract before implementing it
4. **Failing test first** — red → green → refactor, always
5. **Simplicity gate** — complexity ≤ 3, pure functions, dependency injection

## License

{cfg.license}
""",
    )


def write_lang_config(cfg: ForgeConfig) -> None:
    if cfg.language == "python":
        if cfg.pkg_manager == "poetry":
            write(
                cfg.dest / "pyproject.toml",
                f"""[tool.poetry]
name = "{cfg.slug}"
version = "0.1.0"
description = "{cfg.description}"
license = "{cfg.license}"

[tool.poetry.dependencies]
python = "^3.11"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-cov = "^5.0"
pytest-asyncio = "^0.23"
mypy = "^1.10"
ruff = "^0.4"
black = "^24.4"
pre-commit = "^3.7"
result = "^0.17"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
testpaths = ["tests", "src"]
addopts = "--cov=src --cov-fail-under=95 --cov-report=term-missing"

[tool.mypy]
strict = true
python_version = "3.11"

[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "F", "I", "N", "UP", "ANN", "S", "B", "C90"]
ignore = ["ANN101"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.coverage.report]
fail_under = 95
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]
""",
            )
        else:
            write(
                cfg.dest / "pyproject.toml",
                f"""[project]
name = "{cfg.slug}"
version = "0.1.0"
description = "{cfg.description}"
license = "{{text = '{cfg.license}'}}"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "mypy>=1.10",
    "ruff>=0.4",
    "black>=24.4",
    "pre-commit>=3.7",
    "result>=0.17",
]

[tool.pytest.ini_options]
testpaths = ["tests", "src"]
addopts = "--cov=src --cov-fail-under=95 --cov-report=term-missing"

[tool.mypy]
strict = true
python_version = "3.11"

[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "F", "I", "N", "UP", "ANN", "S", "B", "C90"]
ignore = ["ANN101"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.coverage.report]
fail_under = 95
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]
""",
            )
    elif cfg.language == "typescript" and cfg.project_type != "monorepo":
        write(
            cfg.dest / "package.json",
            json.dumps(
                {
                    "name": cfg.slug,
                    "version": "0.1.0",
                    "description": cfg.description,
                    "license": cfg.license,
                    "scripts": {
                        "dev": (
                            "next dev"
                            if cfg.framework == "nextjs"
                            else "tsx src/index.ts"
                        ),
                        "build": "next build" if cfg.framework == "nextjs" else "tsc",
                        "test": "vitest run",
                        "test:watch": "vitest",
                        "coverage": "vitest run --coverage",
                        "lint": "eslint src --ext .ts,.tsx",
                        "typecheck": "tsc --noEmit",
                        "format": "prettier --write .",
                    },
                    "devDependencies": {
                        "typescript": "^5.4",
                        "vitest": "^1.6",
                        "@vitest/coverage-v8": "^1.6",
                        "eslint": "^8",
                        "@typescript-eslint/eslint-plugin": "^7",
                        "prettier": "^3",
                    },
                },
                indent=2,
            ),
        )
        write(
            cfg.dest / "tsconfig.json",
            json.dumps(
                {
                    "compilerOptions": {
                        "target": "ES2022",
                        "module": "NodeNext",
                        "moduleResolution": "NodeNext",
                        "strict": True,
                        "noUncheckedIndexedAccess": True,
                        "exactOptionalPropertyTypes": True,
                        "outDir": "dist",
                        "rootDir": "src",
                    },
                    "include": ["src/**/*"],
                    "exclude": ["node_modules", "dist"],
                },
                indent=2,
            ),
        )
        write(
            cfg.dest / "vitest.config.ts",
            "import { defineConfig } from 'vitest/config'\n\n"
            "export default defineConfig({\n"
            "  test: {\n"
            "    coverage: {\n"
            "      provider: 'v8',\n"
            "      include: ['src/**'],\n"
            "      exclude: ['src/**/*.test.ts', 'src/**/*.spec.ts'],\n"
            "      thresholds: {\n"
            "        lines: 95,\n"
            "        functions: 95,\n"
            "        branches: 80,\n"
            "        statements: 95,\n"
            "      },\n"
            "    },\n"
            "  },\n"
            "})\n",
        )

    elif cfg.project_type == "monorepo":
        write(
            cfg.dest / "package.json",
            json.dumps(
                {
                    "name": cfg.slug,
                    "private": True,
                    "scripts": {
                        "build": "turbo build",
                        "dev": "turbo dev",
                        "test": "turbo test",
                        "lint": "turbo lint",
                        "typecheck": "turbo typecheck",
                        "format": 'prettier --write "**/*.{ts,tsx,md}"',
                    },
                    "devDependencies": {
                        "turbo": "^2.0",
                        "typescript": "^5.4",
                        "prettier": "^3",
                    },
                },
                indent=2,
            ),
        )
        write(
            cfg.dest / "pnpm-workspace.yaml",
            "packages:\n  - 'apps/*'\n  - 'packages/*'\n",
        )
        write(
            cfg.dest / "turbo.json",
            json.dumps(
                {
                    "$schema": "https://turbo.build/schema.json",
                    "tasks": {
                        "build": {"dependsOn": ["^build"], "outputs": ["dist/**"]},
                        "dev": {"cache": False, "persistent": True},
                        "test": {"dependsOn": ["build"]},
                        "lint": {},
                        "typecheck": {},
                    },
                },
                indent=2,
            ),
        )
        base_tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "NodeNext",
                "moduleResolution": "NodeNext",
                "strict": True,
                "noUncheckedIndexedAccess": True,
                "exactOptionalPropertyTypes": True,
            }
        }
        write(
            cfg.dest / "packages" / "config" / "tsconfig" / "base.json",
            json.dumps(base_tsconfig, indent=2),
        )

    elif cfg.language == "go":
        write(
            cfg.dest / "go.mod",
            f"""module github.com/{cfg.org}/{cfg.slug}

go 1.22
""",
        )


# ── project structure scaffold ────────────────────────────────────────────────


def write_project_structure(cfg: ForgeConfig) -> None:
    """Create opinionated source layout aligned with the active skills."""
    dispatch = {
        ("backend", "python"): _scaffold_python_backend,
        ("backend", "typescript"): _scaffold_ts_backend,
        ("backend", "go"): _scaffold_go_backend,
        ("backend", "rust"): _scaffold_rust_backend,
        ("frontend", "typescript"): (
            _scaffold_nextjs if cfg.framework == "nextjs" else _scaffold_ts_frontend
        ),
        ("frontend", "javascript"): _scaffold_ts_frontend,
        ("monorepo", "typescript"): _scaffold_monorepo,
        ("tooling", "python"): _scaffold_python_tooling,
        ("tooling", "typescript"): _scaffold_ts_tooling,
        ("tooling", "go"): _scaffold_go_tooling,
        ("infrastructure", "python"): _scaffold_pulumi,
        ("infrastructure", "hcl"): _scaffold_terraform,
        ("docs", "python"): _scaffold_mkdocs,
        ("docs", "typescript"): _scaffold_docusaurus,
    }
    fn = dispatch.get((cfg.project_type, cfg.language))
    if fn:
        fn(cfg)


def _py_init(note: str) -> str:
    return f'"""{note}"""\n'


def _scaffold_python_backend(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(d / "src" / "__init__.py", "")
    write(
        d / "src" / "main.py",
        f'"""FastAPI application factory — wires DI and mounts routers."""\n'
        "from __future__ import annotations\n"
        "from fastapi import FastAPI\n"
        f"from src.api.routes import router\n\n"
        f"def create_app() -> FastAPI:\n"
        f'    app = FastAPI(title="{s}")\n'
        f"    app.include_router(router)\n"
        f"    return app\n\n"
        f"app = create_app()\n",
    )

    write(
        d / "src" / "domain" / "__init__.py",
        _py_init(
            "Pure business logic. Zero infrastructure imports allowed here.\n"
            "Governed by: skills/domain-model/SKILL.md"
        ),
    )
    write(
        d / "src" / "domain" / "models.py",
        '"""Entities, value objects, aggregates.\n'
        "Names must appear in docs/domain/glossary.md before use.\n"
        '"""\n'
        "from __future__ import annotations\n"
        "from dataclasses import dataclass, field\n"
        "from uuid import UUID, uuid4\n\n\n"
        "# Add domain models below — see skills/domain-model/SKILL.md\n",
    )
    write(
        d / "src" / "domain" / "events.py",
        '"""Domain events — past-tense facts emitted from aggregates.\n'
        "Rule: event names are past-tense (OrderPlaced, not PlaceOrder).\n"
        '"""\n'
        "from __future__ import annotations\n"
        "from dataclasses import dataclass\n"
        "from datetime import datetime, UTC\n\n\n"
        "# Add domain events below\n",
    )
    write(
        d / "src" / "domain" / "repositories.py",
        '"""Repository protocols — pure interfaces, zero DB imports.\n'
        "Governed by: skills/interface-design/SKILL.md\n"
        '"""\n'
        "from __future__ import annotations\n"
        "from typing import Protocol\n\n\n"
        "# Example:\n"
        "# class ExampleRepository(Protocol):\n"
        "#     def find_by_id(self, id: UUID) -> Example | None: ...\n"
        "#     def save(self, entity: Example) -> None: ...\n",
    )

    write(
        d / "src" / "application" / "__init__.py",
        _py_init("Use cases — orchestrate domain. No HTTP, no SQL imports."),
    )
    write(
        d / "src" / "application" / "commands.py",
        '"""Command handlers — write-side use cases (create, update, delete)."""\n'
        "from __future__ import annotations\n\n\n"
        "# Each handler: receives a command dataclass, calls domain, saves via repository\n",
    )
    write(
        d / "src" / "application" / "queries.py",
        '"""Query handlers — read-side use cases (fetch, list, search).\n'
        "Keep queries thin: no business logic, just data retrieval.\n"
        '"""\n'
        "from __future__ import annotations\n\n\n"
        "# Each handler: receives a query dataclass, returns a read model\n",
    )

    write(
        d / "src" / "infrastructure" / "__init__.py",
        _py_init("Adapters — concrete implementations of domain interfaces."),
    )
    write(
        d / "src" / "infrastructure" / "config.py",
        '"""Application configuration — loads from environment variables."""\n'
        "from __future__ import annotations\n"
        "from pydantic_settings import BaseSettings\n\n\n"
        "class Settings(BaseSettings):\n"
        f'    app_name: str = "{s}"\n'
        "    debug: bool = False\n"
        '    database_url: str = "sqlite:///./dev.db"\n\n'
        '    model_config = {"env_file": ".env"}\n\n\n'
        "settings = Settings()\n",
    )
    write(
        d / "src" / "infrastructure" / "db.py",
        '"""Concrete repository implementations — DB adapters.\n'
        "Implements Protocols from domain/repositories.py — never expose ORM types to domain.\n"
        '"""\n'
        "from __future__ import annotations\n\n\n"
        "# Add concrete repository classes here\n",
    )

    write(
        d / "src" / "api" / "__init__.py",
        _py_init("HTTP delivery — routes and schemas. No business logic."),
    )
    write(
        d / "src" / "api" / "routes.py",
        '"""FastAPI routers — thin HTTP adapter.\n'
        "Rule: routes call application handlers, never domain objects directly.\n"
        '"""\n'
        "from __future__ import annotations\n"
        "from fastapi import APIRouter\n\n"
        "router = APIRouter()\n\n\n"
        '@router.get("/health")\n'
        f"async def health() -> dict[str, str]:\n"
        f'    return {{"status": "ok", "service": "{s}"}}\n',
    )
    write(
        d / "src" / "api" / "schemas.py",
        '"""Pydantic request/response schemas — HTTP boundary types only.\n'
        "Rule: schemas live here, never in domain/.\n"
        '"""\n'
        "from __future__ import annotations\n"
        "from pydantic import BaseModel\n\n\n"
        "# Add request/response models here\n",
    )

    write(d / "tests" / "__init__.py", "")
    write(d / "tests" / "unit" / "__init__.py", "")
    write(d / "tests" / "unit" / "domain" / "__init__.py", "")
    write(
        d / "tests" / "unit" / "domain" / "test_models.py",
        '"""Unit tests for domain models — pure functions, no mocks.\n'
        "Governed by: skills/tdd/SKILL.md\n"
        '"""\n'
        "from __future__ import annotations\n\n\n"
        "def test_placeholder() -> None:\n"
        '    """Replace with a real domain test — skills/tdd/SKILL.md."""\n'
        "    assert True\n",
    )
    write(d / "tests" / "integration" / "__init__.py", "")
    write(
        d / "tests" / "integration" / "test_api.py",
        '"""Integration tests — real routes, in-memory repository fakes."""\n'
        "from __future__ import annotations\n\n\n"
        "def test_health() -> None:\n"
        '    """Health endpoint returns 200."""\n'
        "    assert True  # replace with TestClient call once app is wired\n",
    )


def _scaffold_python_tooling(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(d / "src" / "__init__.py", "")
    write(
        d / "src" / "cli.py",
        '"""Typer CLI entry point — thin command definitions, no business logic."""\n'
        "from __future__ import annotations\n"
        "import typer\n"
        "from src.core import logic\n\n"
        "app = typer.Typer()\n\n\n"
        "@app.command()\n"
        "def main() -> None:\n"
        '    """Entry point — replace with real commands."""\n'
        '    typer.echo("Hello from {s}")\n'.replace("{s}", s),
    )
    write(
        d / "src" / "core" / "__init__.py",
        _py_init("Pure business logic — no IO, no CLI framework imports."),
    )
    write(
        d / "src" / "core" / "logic.py",
        '"""Core logic — pure functions only.\n'
        "Rule: no side effects, no IO. Governed by: skills/implementation-simplicity/SKILL.md\n"
        '"""\n'
        "from __future__ import annotations\n\n\n"
        "# Add pure functions here\n",
    )
    write(
        d / "src" / "models" / "__init__.py",
        _py_init("Data models — Pydantic config, typed inputs/outputs."),
    )
    write(
        d / "src" / "models" / "config.py",
        '"""Configuration models — loaded from env or config file."""\n'
        "from __future__ import annotations\n"
        "from pydantic import BaseModel\n\n\n"
        "class Config(BaseModel):\n"
        "    verbose: bool = False\n",
    )
    write(
        d / "src" / "adapters" / "__init__.py",
        _py_init(
            "Infrastructure adapters — filesystem, network, subprocess. Isolated here."
        ),
    )
    write(
        d / "src" / "adapters" / "filesystem.py",
        '"""Filesystem adapter — all Path operations live here."""\n'
        "from __future__ import annotations\n"
        "from pathlib import Path\n\n\n"
        "# Add filesystem operations here, never in core/\n",
    )

    write(d / "tests" / "__init__.py", "")
    write(d / "tests" / "unit" / "__init__.py", "")
    write(
        d / "tests" / "unit" / "test_core.py",
        '"""Unit tests for core logic — pure functions, no mocks.\n'
        "Governed by: skills/tdd/SKILL.md\n"
        '"""\n'
        "from __future__ import annotations\n\n\n"
        "def test_placeholder() -> None:\n"
        '    """Replace with real tests — skills/tdd/SKILL.md."""\n'
        "    assert True\n",
    )
    write(d / "tests" / "integration" / "__init__.py", "")
    write(
        d / "tests" / "integration" / "test_cli.py",
        '"""Integration tests for CLI commands."""\n'
        "from __future__ import annotations\n"
        "from typer.testing import CliRunner\n"
        "from src.cli import app\n\n"
        "runner = CliRunner()\n\n\n"
        "def test_main_command_runs() -> None:\n"
        '    """CLI main command exits 0."""\n'
        "    result = runner.invoke(app)\n"
        "    assert result.exit_code == 0\n",
    )


def _scaffold_ts_backend(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(
        d / "src" / "index.ts",
        f"// {s} — application factory, wires DI and starts the server\n"
        "import { Hono } from 'hono'\n"
        "import { router } from './api/routes.js'\n\n"
        "const app = new Hono()\n"
        "app.route('/', router)\n\n"
        "export default app\n",
    )
    write(
        d / "src" / "domain" / "models.ts",
        "// Domain entities and value objects — pure types, no framework imports.\n"
        "// Names must appear in docs/domain/glossary.md before use.\n"
        "// Governed by: skills/domain-model/SKILL.md\n\n"
        "// Add domain types below\n",
    )
    write(
        d / "src" / "domain" / "events.ts",
        "// Domain events — past-tense facts (OrderPlaced, UserRegistered).\n\n"
        "// Add event types below\n",
    )
    write(
        d / "src" / "domain" / "repositories.ts",
        "// Repository interfaces — zero DB imports.\n"
        "// Governed by: skills/interface-design/SKILL.md\n\n"
        "// Example:\n"
        "// export interface ExampleRepository {\n"
        "//   findById(id: string): Promise<Example | null>\n"
        "//   save(entity: Example): Promise<void>\n"
        "// }\n",
    )
    write(
        d / "src" / "application" / "commands.ts",
        "// Command handlers — write-side use cases.\n"
        "// No HTTP, no SQL — only domain types and repository interfaces.\n\n"
        "// Add command handlers below\n",
    )
    write(
        d / "src" / "application" / "queries.ts",
        "// Query handlers — read-side use cases.\n\n// Add query handlers below\n",
    )
    write(
        d / "src" / "infrastructure" / "config.ts",
        "// Application config loaded from environment variables.\n\n"
        "export const config = {\n"
        f"  appName: process.env.APP_NAME ?? '{s}',\n"
        "  databaseUrl: process.env.DATABASE_URL ?? 'sqlite://dev.db',\n"
        "  port: Number(process.env.PORT ?? 3000),\n"
        "} as const\n",
    )
    write(
        d / "src" / "infrastructure" / "db.ts",
        "// Concrete repository implementations — DB adapters.\n"
        "// Implements interfaces from domain/repositories.ts.\n\n"
        "// Add concrete classes here\n",
    )
    write(
        d / "src" / "api" / "routes.ts",
        "// HTTP routes — thin adapter, calls application handlers only.\n"
        "import { Hono } from 'hono'\n\n"
        "export const router = new Hono()\n\n"
        f"router.get('/health', (c) => c.json({{ status: 'ok', service: '{s}' }}))\n",
    )
    write(
        d / "src" / "api" / "schemas.ts",
        "// Zod schemas for request/response validation.\n"
        "// Rule: schemas live here, never in domain/.\n"
        "import { z } from 'zod'\n\n"
        "// Add schemas below\n",
    )
    write(
        d / "src" / "index.test.ts",
        "import { describe, it, expect } from 'vitest'\n"
        "import app from './index.js'\n\n"
        "describe('health', () => {\n"
        "  it('returns 200 ok', async () => {\n"
        "    const res = await app.request('/health')\n"
        "    expect(res.status).toBe(200)\n"
        "  })\n"
        "})\n",
    )


def _scaffold_nextjs(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(
        d / "src" / "app" / "layout.tsx",
        "import type { Metadata } from 'next'\n\n"
        f"export const metadata: Metadata = {{ title: '{s}' }}\n\n"
        "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
        "  return (\n"
        '    <html lang="en">\n'
        "      <body>{children}</body>\n"
        "    </html>\n"
        "  )\n"
        "}\n",
    )
    write(
        d / "src" / "app" / "page.tsx",
        f"export default function Home() {{\n  return <main><h1>{s}</h1></main>\n}}\n",
    )
    write(
        d / "src" / "components" / "ui" / "button.tsx",
        "// Design system primitive — controlled, accessible, no business logic.\n"
        "interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {\n"
        "  variant?: 'primary' | 'secondary'\n"
        "}\n\n"
        "export function Button({ variant = 'primary', children, ...props }: ButtonProps) {\n"
        "  return <button data-variant={variant} {...props}>{children}</button>\n"
        "}\n",
    )
    write(
        d / "src" / "lib" / "utils.ts",
        "// Pure utility functions — no side effects, no React imports.\n\n"
        "export function cn(...classes: (string | undefined | false | null)[]): string {\n"
        "  return classes.filter(Boolean).join(' ')\n"
        "}\n",
    )
    write(
        d / "src" / "lib" / "api.ts",
        "// API client — all fetch calls live here, never in components.\n\n"
        "export async function apiFetch<T>(path: string): Promise<T> {\n"
        "  const res = await fetch(path)\n"
        "  if (!res.ok) throw new Error(`API error ${res.status}`)\n"
        "  return res.json() as Promise<T>\n"
        "}\n",
    )
    write(
        d / "src" / "types" / "index.ts",
        "// Shared TypeScript types — domain terms, not HTTP shapes.\n"
        "// Names must appear in docs/domain/glossary.md.\n\n"
        "// Add shared types below\n",
    )
    write(
        d / "src" / "hooks" / "index.ts",
        "// Custom React hooks — stateful, no business logic.\n\n// Add hooks below\n",
    )
    write(
        d / "src" / "services" / "index.ts",
        "// Service layer — wraps API client with typed domain calls.\n\n"
        "// Add service functions below\n",
    )
    write(
        d / "tests" / "unit" / "lib.test.ts",
        "import { describe, it, expect } from 'vitest'\n"
        "import { cn } from '../src/lib/utils.js'\n\n"
        "describe('cn', () => {\n"
        "  it('joins class names', () => {\n"
        "    expect(cn('a', 'b')).toBe('a b')\n"
        "  })\n"
        "  it('filters falsy values', () => {\n"
        "    expect(cn('a', false, null, 'b')).toBe('a b')\n"
        "  })\n"
        "})\n",
    )


def _scaffold_ts_frontend(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(d / "src" / "index.ts", f"// {s} — entry point\n")
    write(
        d / "src" / "components" / "index.ts",
        "// Component exports — re-export from sub-modules.\n",
    )
    write(
        d / "src" / "lib" / "utils.ts", "// Pure utility functions — no side effects.\n"
    )
    write(
        d / "src" / "types" / "index.ts",
        "// Shared TypeScript types — names from docs/domain/glossary.md.\n",
    )
    write(
        d / "src" / "index.test.ts",
        "import { describe, it, expect } from 'vitest'\n\n"
        "describe('placeholder', () => {\n"
        "  it('is true', () => { expect(true).toBe(true) })\n"
        "})\n",
    )


def _scaffold_ts_tooling(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(d / "src" / "index.ts", f"// {s} — CLI entry point\n")
    write(
        d / "src" / "cli" / "index.ts",
        "// Command definitions — thin wrappers over core logic.\n",
    )
    write(
        d / "src" / "core" / "index.ts",
        "// Pure business logic — no IO, no CLI framework imports.\n",
    )
    write(
        d / "src" / "adapters" / "filesystem.ts",
        "// Filesystem adapter — all fs operations live here.\n",
    )
    write(
        d / "src" / "index.test.ts",
        "import { describe, it, expect } from 'vitest'\n\n"
        "describe('cli', () => {\n"
        "  it('exports a command', () => { expect(true).toBe(true) })\n"
        "})\n",
    )


def _scaffold_monorepo(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    # apps/api
    write(d / "apps" / "api" / "src" / "index.ts", "// API application entry point\n")
    write(
        d / "apps" / "api" / "src" / "index.test.ts",
        "import { describe, it, expect } from 'vitest'\n"
        "describe('api', () => { it('starts', () => expect(true).toBe(true)) })\n",
    )
    write(
        d / "apps" / "api" / "package.json",
        json.dumps(
            {
                "name": f"@{s}/api",
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "tsx src/index.ts",
                    "build": "tsc",
                    "test": "vitest run",
                },
                "devDependencies": {
                    "typescript": "^5.4",
                    "vitest": "^1.6",
                    "tsx": "^4",
                },
            },
            indent=2,
        ),
    )
    write(
        d / "apps" / "api" / "tsconfig.json",
        json.dumps(
            {
                "extends": "../../packages/config/tsconfig/base.json",
                "compilerOptions": {"outDir": "dist", "rootDir": "src"},
                "include": ["src/**/*"],
            },
            indent=2,
        ),
    )

    # apps/web
    write(
        d / "apps" / "web" / "src" / "app" / "page.tsx",
        f"export default function Home() {{ return <main><h1>{s}</h1></main> }}\n",
    )
    write(
        d / "apps" / "web" / "package.json",
        json.dumps(
            {
                "name": f"@{s}/web",
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "test": "vitest run",
                },
                "devDependencies": {
                    "next": "^14",
                    "typescript": "^5.4",
                    "vitest": "^1.6",
                },
            },
            indent=2,
        ),
    )
    write(
        d / "apps" / "web" / "tsconfig.json",
        json.dumps(
            {
                "extends": "../../packages/config/tsconfig/base.json",
                "compilerOptions": {"jsx": "preserve"},
                "include": ["src/**/*"],
            },
            indent=2,
        ),
    )

    # packages/ui
    write(
        d / "packages" / "ui" / "src" / "index.ts",
        "// Shared UI component library — design system primitives.\n",
    )
    write(
        d / "packages" / "ui" / "package.json",
        json.dumps(
            {
                "name": f"@{s}/ui",
                "version": "0.1.0",
                "main": "./dist/index.js",
                "types": "./dist/index.d.ts",
                "scripts": {"build": "tsc", "test": "vitest run"},
            },
            indent=2,
        ),
    )

    # packages/shared
    write(
        d / "packages" / "shared" / "src" / "index.ts",
        "// Shared types and utilities — names from docs/domain/glossary.md.\n",
    )
    write(
        d / "packages" / "shared" / "package.json",
        json.dumps(
            {
                "name": f"@{s}/shared",
                "version": "0.1.0",
                "main": "./dist/index.js",
                "types": "./dist/index.d.ts",
                "scripts": {"build": "tsc", "test": "vitest run"},
            },
            indent=2,
        ),
    )


def _scaffold_go_backend(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug
    org = cfg.org

    write(
        d / "cmd" / "server" / "main.go",
        f"package main\n\n"
        f"// Entry point — wires dependency injection and starts the HTTP server.\n"
        f"import (\n"
        f'\t"github.com/{org}/{s}/internal/api"\n'
        f'\t"github.com/{org}/{s}/internal/infrastructure/config"\n'
        f")\n\n"
        f"func main() {{\n"
        f"\tcfg := config.Load()\n"
        f"\tr := api.NewRouter(cfg)\n"
        f"\t_ = r\n"
        f"}}\n",
    )

    write(
        d / "internal" / "domain" / "model.go",
        "// Package domain — pure business logic.\n"
        "// Zero imports from infrastructure, api, or framework packages.\n"
        "// Names must appear in docs/domain/glossary.md.\n"
        "package domain\n\n"
        "// Add domain entities and value objects below\n",
    )
    write(
        d / "internal" / "domain" / "events.go",
        "// Domain events — past-tense facts emitted from aggregates.\n"
        "package domain\n\n"
        "// Add event types below\n",
    )
    write(
        d / "internal" / "domain" / "repository.go",
        "// Repository interfaces — no database types, no SQL.\n"
        "// Governed by: skills/interface-design/SKILL.md\n"
        "package domain\n\n"
        "// Example:\n"
        "// type ExampleRepository interface {\n"
        "//     FindByID(id string) (*Example, error)\n"
        "//     Save(e *Example) error\n"
        "// }\n",
    )

    write(
        d / "internal" / "application" / "service.go",
        "// Application services — use-case orchestration.\n"
        "// No HTTP, no SQL — only domain types and repository interfaces.\n"
        "package application\n\n"
        "// Add use-case service types below\n",
    )

    write(
        d / "internal" / "infrastructure" / "db" / "postgres.go",
        "// Concrete repository implementations.\n"
        "// Implements domain repository interfaces.\n"
        "package db\n\n"
        "// Add concrete repository structs below\n",
    )
    write(
        d / "internal" / "infrastructure" / "config" / "config.go",
        f'package config\n\nimport "os"\n\n'
        f"type Config struct {{\n"
        f"\tDatabaseURL string\n"
        f"\tPort        string\n"
        f"}}\n\n"
        f"func Load() Config {{\n"
        f"\treturn Config{{\n"
        f'\t\tDatabaseURL: getEnv("DATABASE_URL", "postgres://localhost:5432/{s}"),\n'
        f'\t\tPort:        getEnv("PORT", "8080"),\n'
        f"\t}}\n"
        f"}}\n\n"
        f"func getEnv(key, fallback string) string {{\n"
        f"\tif v, ok := os.LookupEnv(key); ok {{\n"
        f"\t\treturn v\n"
        f"\t}}\n"
        f"\treturn fallback\n"
        f"}}\n",
    )

    write(
        d / "internal" / "api" / "handler.go",
        "// HTTP handlers — thin adapter, calls application services only.\n"
        "// No business logic here.\n"
        "package api\n\n"
        "// Add handler functions below\n",
    )
    write(
        d / "internal" / "api" / "routes.go",
        f'package api\n\nimport (\n\t"net/http"\n\t"github.com/gin-gonic/gin"\n\t"github.com/{org}/{s}/internal/infrastructure/config"\n)\n\n'
        f"func NewRouter(cfg config.Config) *gin.Engine {{\n"
        f"\tr := gin.Default()\n"
        f'\tr.GET("/health", func(c *gin.Context) {{\n'
        f'\t\tc.JSON(http.StatusOK, gin.H{{"status": "ok"}})\n'
        f"\t}})\n"
        f"\treturn r\n"
        f"}}\n",
    )
    write(
        d / "internal" / "api" / "middleware.go",
        "// Middleware — logging, auth, recovery.\npackage api\n",
    )

    write(
        d / "pkg" / "errors" / "errors.go",
        "// Shared error types used across layers.\n"
        "package errors\n\n"
        'import "fmt"\n\n'
        "type NotFoundError struct{ ID string }\n"
        'func (e NotFoundError) Error() string { return fmt.Sprintf("not found: %s", e.ID) }\n',
    )

    write(
        d / "tests" / "integration" / "api_test.go",
        f'package integration_test\n\nimport "testing"\n\n'
        f"func TestHealthEndpoint(t *testing.T) {{\n"
        f'\tt.Skip("Implement with httptest — skills/tdd/SKILL.md")\n'
        f"}}\n",
    )


def _scaffold_go_tooling(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug
    org = cfg.org

    write(
        d / "cmd" / s / "main.go",
        f"package main\n\n"
        f'import "github.com/{org}/{s}/internal/cli"\n\n'
        f"func main() {{\n"
        f"\tcli.Execute()\n"
        f"}}\n",
    )
    write(
        d / "internal" / "cli" / "root.go",
        f'package cli\n\nimport "github.com/spf13/cobra"\n\n'
        f"var rootCmd = &cobra.Command{{\n"
        f'\tUse:   "{s}",\n'
        f'\tShort: "{s} — add a description",\n'
        f"}}\n\n"
        f"func Execute() {{\n"
        f"\t_ = rootCmd.Execute()\n"
        f"}}\n",
    )
    write(
        d / "internal" / "core" / "logic.go",
        "// Pure business logic — no IO, no CLI framework imports.\n"
        "package core\n\n"
        "// Add pure functions here\n",
    )
    write(
        d / "internal" / "adapters" / "filesystem.go",
        "// Filesystem adapter — all fs operations isolated here.\n"
        "package adapters\n\n"
        "// Add filesystem helpers here\n",
    )
    write(
        d / "pkg" / "types" / "types.go",
        "// Shared types exported as part of the public API.\npackage types\n",
    )


def _scaffold_rust_backend(cfg: ForgeConfig) -> None:
    d = cfg.dest

    write(
        d / "src" / "main.rs",
        "// Entry point — wires Axum router and starts the server.\n"
        "mod api;\n"
        "mod domain;\n"
        "mod application;\n"
        "mod infrastructure;\n\n"
        "#[tokio::main]\n"
        "async fn main() {\n"
        "    let app = api::create_router();\n"
        '    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();\n'
        "    axum::serve(listener, app).await.unwrap();\n"
        "}\n",
    )
    write(
        d / "src" / "domain" / "mod.rs",
        "// Pure business logic — zero infrastructure imports.\n"
        "pub mod models;\n"
        "pub mod events;\n"
        "pub mod repositories;\n",
    )
    write(d / "src" / "domain" / "models.rs", "// Domain entities and value objects.\n")
    write(
        d / "src" / "domain" / "events.rs",
        "// Domain events — past-tense (OrderPlaced, UserRegistered).\n",
    )
    write(
        d / "src" / "domain" / "repositories.rs",
        "// Repository traits — no DB types.\n",
    )
    write(
        d / "src" / "application" / "mod.rs",
        "// Use cases — orchestrate domain. No HTTP, no SQL.\n"
        "pub mod commands;\n"
        "pub mod queries;\n",
    )
    write(d / "src" / "application" / "commands.rs", "// Command handlers.\n")
    write(d / "src" / "application" / "queries.rs", "// Query handlers.\n")
    write(
        d / "src" / "infrastructure" / "mod.rs",
        "// Adapters — concrete implementations.\npub mod config;\npub mod db;\n",
    )
    write(
        d / "src" / "infrastructure" / "config.rs",
        "// Config from environment variables.\n"
        "use std::env;\n\n"
        "pub struct Config {\n"
        "    pub database_url: String,\n"
        "    pub port: u16,\n"
        "}\n\n"
        "impl Config {\n"
        "    pub fn from_env() -> Self {\n"
        "        Self {\n"
        '            database_url: env::var("DATABASE_URL").unwrap_or_default(),\n'
        '            port: env::var("PORT").unwrap_or("3000".into()).parse().unwrap_or(3000),\n'
        "        }\n"
        "    }\n"
        "}\n",
    )
    write(
        d / "src" / "infrastructure" / "db.rs",
        "// Concrete repository implementations.\n",
    )
    write(
        d / "src" / "api" / "mod.rs",
        "// HTTP delivery — Axum router. No business logic.\n"
        "use axum::{Router, routing::get};\n\n"
        "pub fn create_router() -> Router {\n"
        '    Router::new().route("/health", get(health))\n'
        "}\n\n"
        'async fn health() -> &\'static str { "ok" }\n',
    )


def _scaffold_pulumi(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(
        d / "Pulumi.yaml",
        f"name: {s}\nruntime: python\ndescription: {cfg.description}\n",
    )
    write(d / "Pulumi.dev.yaml", f"config:\n  {s}:environment: dev\n")
    write(d / "Pulumi.staging.yaml", f"config:\n  {s}:environment: staging\n")
    write(d / "Pulumi.prod.yaml", f"config:\n  {s}:environment: prod\n")

    write(d / "stacks" / "__init__.py", "")
    write(
        d / "stacks" / "dev.py",
        '"""Dev stack — single-region, minimal resources."""\n'
        "from __future__ import annotations\n"
        "import pulumi\n"
        "from modules import network, compute, storage\n\n"
        "# Wire dev resources here\n",
    )
    write(
        d / "stacks" / "staging.py",
        '"""Staging stack — mirrors prod, smaller scale."""\n'
        "from __future__ import annotations\n\n"
        "# Wire staging resources here\n",
    )
    write(
        d / "stacks" / "prod.py",
        '"""Production stack."""\n'
        "from __future__ import annotations\n\n"
        "# Wire prod resources here\n",
    )
    write(
        d / "__main__.py",
        '"""Pulumi entry point — selects the active stack."""\n'
        "from __future__ import annotations\n"
        "import pulumi\n\n"
        "stack = pulumi.get_stack()\n\n"
        'if stack == "prod":\n'
        "    from stacks.prod import *  # noqa: F401,F403\n"
        'elif stack == "staging":\n'
        "    from stacks.staging import *  # noqa: F401,F403\n"
        "else:\n"
        "    from stacks.dev import *  # noqa: F401,F403\n",
    )

    write(d / "modules" / "__init__.py", "")
    write(
        d / "modules" / "network.py",
        '"""Reusable network module — VPCs, subnets, security groups."""\n'
        "from __future__ import annotations\n\n"
        "# Add network resources here\n",
    )
    write(
        d / "modules" / "compute.py",
        '"""Reusable compute module — VMs, containers, serverless."""\n'
        "from __future__ import annotations\n\n"
        "# Add compute resources here\n",
    )
    write(
        d / "modules" / "storage.py",
        '"""Reusable storage module — buckets, databases, queues."""\n'
        "from __future__ import annotations\n\n"
        "# Add storage resources here\n",
    )

    write(d / "tests" / "__init__.py", "")
    write(
        d / "tests" / "test_stacks.py",
        '"""Pulumi stack tests — validate resource configs without deploying."""\n'
        "from __future__ import annotations\n\n\n"
        "def test_placeholder() -> None:\n"
        '    """Replace with real Pulumi mock tests."""\n'
        "    assert True\n",
    )


def _scaffold_terraform(cfg: ForgeConfig) -> None:
    d = cfg.dest

    for env in ("dev", "staging", "prod"):
        write(
            d / "stacks" / env / "main.tf",
            f"# {env.capitalize()} stack\n\n"
            f'module "network" {{\n'
            f'  source = "../../modules/network"\n'
            f"}}\n\n"
            f'module "compute" {{\n'
            f'  source = "../../modules/compute"\n'
            f"}}\n",
        )
        write(
            d / "stacks" / env / "variables.tf",
            f'variable "environment" {{\n  default = "{env}"\n}}\n',
        )
        write(d / "stacks" / env / "outputs.tf", f"# {env} outputs\n")

    for mod in ("network", "compute", "storage"):
        write(d / "modules" / mod / "main.tf", f"# {mod.capitalize()} module\n")
        write(
            d / "modules" / mod / "variables.tf",
            f"# {mod.capitalize()} module inputs\n",
        )
        write(
            d / "modules" / mod / "outputs.tf", f"# {mod.capitalize()} module outputs\n"
        )

    write(
        d / "scripts" / "deploy.sh",
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        "ENV=${1:-dev}\n"
        'cd "stacks/$ENV"\n'
        "terraform init\n"
        "terraform plan -out=plan.tfplan\n"
        "terraform apply plan.tfplan\n",
    )


def _scaffold_mkdocs(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(
        d / "mkdocs.yml",
        f"site_name: {s}\n"
        f"site_description: {cfg.description}\n"
        "theme:\n  name: material\n"
        "nav:\n"
        "  - Home: index.md\n"
        "  - Getting Started: getting-started.md\n"
        "  - Domain Glossary: domain/glossary.md\n"
        "  - API Reference: api/reference.md\n",
    )
    write(d / "docs" / "index.md", f"# {s}\n\n{cfg.description}\n")
    write(
        d / "docs" / "getting-started.md",
        f"# Getting started\n\n## Installation\n\n```bash\n# Add install steps here\n```\n",
    )
    write(
        d / "docs" / "api" / "reference.md",
        "# API Reference\n\n<!-- Generated from source — add mkdocstrings here -->\n",
    )


def _scaffold_docusaurus(cfg: ForgeConfig) -> None:
    d = cfg.dest
    s = cfg.slug

    write(
        d / "docusaurus.config.ts",
        f"import type {{Config}} from '@docusaurus/types'\n\n"
        f"const config: Config = {{\n"
        f"  title: '{s}',\n"
        f"  url: 'https://your-site.com',\n"
        f"  baseUrl: '/',\n"
        f"  themeConfig: {{}},\n"
        f"}}\n\nexport default config\n",
    )
    write(d / "docs" / "intro.md", f"# {s}\n\n{cfg.description}\n")
    write(
        d / "docs" / "getting-started.md",
        "# Getting started\n\n## Install\n\n```bash\n# Add steps here\n```\n",
    )
    write(
        d / "src" / "pages" / "index.tsx",
        f"export default function Home() {{\n  return <main><h1>{s}</h1></main>\n}}\n",
    )


# ── git init ──────────────────────────────────────────────────────────────────


def init_git(cfg: ForgeConfig) -> None:
    dest = cfg.dest
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=dest, check=True, capture_output=True
    )
    subprocess.run(["git", "add", "."], cwd=dest, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"chore: initial scaffold via firstcut\n\nType: {cfg.project_type}\nStack: {cfg.language}/{cfg.framework}",
        ],
        cwd=dest,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": cfg.org,
            "GIT_AUTHOR_EMAIL": f"firstcut@{cfg.org}.com",
            "GIT_COMMITTER_NAME": cfg.org,
            "GIT_COMMITTER_EMAIL": f"firstcut@{cfg.org}.com",
        },
    )


# ── summary ───────────────────────────────────────────────────────────────────


def print_summary(cfg: ForgeConfig) -> None:
    print(f"\n{h('━' * 60)}")
    print(f"{GREEN}  Project scaffolded successfully!{RESET}")
    print(f"{h('━' * 60)}\n")
    print(f"  {dim('Location')}   {cfg.dest}")
    print(
        f"  {dim('Type')}       {cfg.project_type} · {cfg.language} / {cfg.framework}"
    )
    print(f"  {dim('Skills')}     {len(cfg.skills)} AI skills embedded")
    print(f"  {dim('CI')}         {', '.join(cfg.ci) or 'none'}")
    print()
    print(f"  {h('Next steps:')}")
    print(f"  1. cd {cfg.dest}")
    print(f"  2. {_install_cmd(cfg)}")
    print(
        f"  3. pip install pre-commit && pre-commit install --hook-type commit-msg && pre-commit install"
    )
    print(f"  4. Open in Claude Code, Codex, or your AI terminal")
    print(
        f'  5. Tell your AI tool: "Read CLAUDE.md or AGENTS.md and start a new feature"'
    )
    print()
    print(f"  {dim('Your AI tool will follow the 6-phase workflow automatically.')}")
    print(f"{h('━' * 60)}\n")


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:  # pragma: no cover - legacy entrypoint kept for compatibility
    print(f"""
{h("╔══════════════════════════════════════════════════════╗")}
{h("║")}  {CYAN}firstcut{RESET} — first-principles project scaffolder       {h("║")}
{h("║")}  {dim("4 steps. Opinionated defaults. AI skills embedded.")}  {h("║")}
{h("╚══════════════════════════════════════════════════════╝")}

{dim("Press Enter to accept defaults (shown in parentheses).")}
""")

    cfg = ForgeConfig()

    step1_project_type(cfg)
    step2_stack(cfg)
    step3_metadata(cfg)
    step4_skills(cfg)

    print(f"\n{info('Scaffolding project...')}")

    if cfg.dest.exists():
        if not confirm(
            f"\n{warn(f'{cfg.dest} already exists. Overwrite?')}", default=False
        ):
            print("Aborted.")
            sys.exit(0)
        shutil.rmtree(cfg.dest)

    write_claude_md(cfg)
    write_agents_md(cfg)
    write_cursorrules(cfg)
    write_windsurfrules(cfg)
    write_skills(cfg)
    write_precommit(cfg)

    if "github-actions" in cfg.ci:
        write_github_ci(cfg)
    if "gitlab-ci" in cfg.ci:
        write_gitlab_ci(cfg)

    if cfg.include_docs_submodule:
        write_docs(cfg)

    write_gitignore(cfg)
    write_readme(cfg)
    write_lang_config(cfg)
    write_project_structure(cfg)
    write_makefile(cfg)

    if cfg.init_git:
        try:
            init_git(cfg)
            print(ok("Git repository initialised with initial commit"))
        except Exception as e:
            print(warn(f"Git init skipped: {e}"))

    print_summary(cfg)


if __name__ == "__main__":  # pragma: no cover - direct script execution shim
    main()
