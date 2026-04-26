# firstcut

> Clone this repo, answer 4 questions, get a production-ready project scaffold — layered architecture, CI, pre-commit hooks, domain docs, and AI skills pre-wired for any AI coding tool.

---

## Inspiration

**firstcut** stands on the shoulders of two ideas:

- **[Cookiecutter](https://cookiecutter.readthedocs.io)** — the canonical project templating tool. Cookiecutter taught the world that answering a few questions should be enough to bootstrap a well-structured project. firstcut takes that spirit but drops template repos entirely: it's a packaged, dependency-free Python generator that carries all its opinions internally.

- **[Matt Pocock's skills](https://github.com/mattpocock/skills/tree/main)** — a system for encoding expert engineering knowledge as plain markdown files that AI assistants read as context. Matt's insight: instead of telling an AI what to do every time, embed your team's process in the repo itself. firstcut adapts this idea into a cross-language, project-creation-time system — your skills ship with every project from day one.

The combination: **structured templates** (Cookiecutter) + **AI skill files** (Pocock) + **opinionated layered architecture** = firstcut.

The supported CLI is `firstcut init`.

---

## What it does

`firstcut` is a one-command scaffolder. You run `firstcut init`, answer 4 questions (all have sensible defaults — just press Enter), and it writes a fully configured project to a new directory.

That project arrives with:

- **Layered source structure** — clean architecture layers (domain / application / infrastructure / API) with placeholder files that say what belongs where and which skill governs each layer
- **AI context files** for Claude Code, Codex, Cursor, and Windsurf — all pointing to the same `skills/` directory
- **8 AI skills** embedded at the project root — plain markdown, readable by any AI tool
- **Pre-commit hooks** — ruff, black, mypy, 95% coverage gate, secret scan, conventional commits
- **CI/CD** — GitHub Actions and/or GitLab CI, preconfigured for your stack
- **Domain docs** — a `glossary.md` template and ADR starter, so every name has a definition before a line of code is written

---

## Install and run

| Channel | Install | Resulting command | Example |
|------|------|------|------|
| Python | `uv tool install firstcut` or `pipx install firstcut` | `firstcut` | `firstcut init --defaults` |
| npm | `npm install -g firstcut-cli` | `firstcut` | `firstcut init --config ./firstcut.toml` |
| pnpm | `pnpm add -g firstcut-cli` | `firstcut` | `firstcut init` |
| Go | `go install github.com/your-org/firstcut-go/cmd/firstcut@latest` | `firstcut` | `firstcut init --defaults` |

The Python package is the canonical runtime. The npm and Go packages in `packages/` are launcher wrappers that try `uvx firstcut`, then `pipx run firstcut`, then a cached Python virtual environment. Every channel lands on the same CLI:

```bash
firstcut init
firstcut init --defaults
firstcut init --config ./firstcut.toml
firstcut init --defaults --project-name api --output-dir ./scratch
```

From this checkout, use:

```bash
uv sync --all-extras
uv run firstcut init

# Optional wrapper smoke paths before publishing
npm install -g ./packages/npm
cd packages/go && go install ./cmd/firstcut
```

## Quickstart

**Step 1 — clone firstcut**

```bash
git clone https://github.com/your-org/firstcut.git
cd firstcut
```

**Step 2 — install local dev dependencies**

```bash
uv sync --all-extras
```

**Step 3 — run the scaffolder**

```bash
uv run firstcut init
```

You'll see 4 prompts. Press Enter to accept every default:

```
─── Step 1 of 4 — Project type ───────────────────────────────
  backend       REST/GraphQL API, microservice, worker, data pipeline
  frontend      SPA, SSG, component library, design system
  monorepo      Full-stack with shared types (API + UI + packages)
  tooling       CLI tool, SDK, developer library, scripts
  infrastructure  IaC, platform engineering, Kubernetes, Pulumi/Terraform
  docs          Documentation site

Project type (default: backend):

─── Step 2 of 4 — Stack ──────────────────────────────────────
Language (default: python):
Framework (default: fastapi):
Package manager (default: uv):
CI target (default: github-actions):

─── Step 3 of 4 — Project metadata ───────────────────────────
Project name (default: my-project):
Organisation / owner (default: my-org):

─── Step 4 of 4 — AI skills ──────────────────────────────────
  All 8 skills enabled by default. Press Enter to keep all.
```

**Step 4 — install dependencies and hooks**

```bash
cd ../my-project

# Python (uv)
uv sync --all-extras
pip install pre-commit && pre-commit install --hook-type commit-msg && pre-commit install

# Python (poetry)
poetry install
pip install pre-commit && pre-commit install --hook-type commit-msg && pre-commit install

# TypeScript
pnpm install
```

**Step 5 — open in your AI tool**

```
Read CLAUDE.md and start a new feature.
```

The AI reads your context files and follows the 6-phase workflow automatically: domain model, glossary naming, interface design, failing test, simple implementation, and QA.

## Non-interactive usage

Use `--defaults` for the default backend scaffold, combine it with flags for automation, or load JSON/TOML config:

```bash
firstcut init --defaults --project-name billing-api --output-dir ./scratch
firstcut init --defaults --config ./firstcut.toml --overwrite
firstcut init --defaults \
  --project-type frontend \
  --language typescript \
  --framework nextjs \
  --pkg-manager pnpm \
  --ci both \
  --skills all
```

Config files use the same field names as the CLI flags:

```toml
project_type = "docs"
language = "python"
framework = "mkdocs"
pkg_manager = "uv"
project_name = "handbook"
ci = ["github-actions"]
skills = ["tdd", "qa", "implementation-simplicity"]
init_git = true
include_docs_submodule = true
```

---

## What you actually get

### Python backend (FastAPI + clean architecture)

```
my-project/
│
├── src/
│   ├── domain/
│   │   ├── models.py          ← entities, value objects, aggregates
│   │   ├── events.py          ← domain events (past-tense facts)
│   │   └── repositories.py    ← repository protocols (interfaces only — no DB)
│   │
│   ├── application/
│   │   ├── commands.py        ← write-side use cases (create, update, delete)
│   │   └── queries.py         ← read-side use cases (fetch, list, search)
│   │
│   ├── infrastructure/
│   │   ├── config.py          ← pydantic-settings, loaded from env
│   │   └── db.py              ← concrete repository implementations
│   │
│   ├── api/
│   │   ├── routes.py          ← FastAPI routers, thin HTTP adapter
│   │   └── schemas.py         ← Pydantic request/response models
│   │
│   └── main.py                ← app factory, wires DI
│
├── tests/
│   ├── unit/domain/           ← pure domain tests, real inputs, zero mocks
│   └── integration/           ← HTTP tests via TestClient
│
├── pyproject.toml             ← uv or poetry, mypy strict, ruff, 95% coverage gate
├── .pre-commit-config.yaml
└── .github/workflows/ci.yml
```

### Go backend (Gin + idiomatic Go layout)

```
my-project/
│
├── cmd/server/main.go         ← entry point, wires DI
│
├── internal/
│   ├── domain/
│   │   ├── model.go           ← entities — zero framework imports
│   │   ├── events.go          ← domain events
│   │   └── repository.go      ← repository interfaces (no SQL types)
│   │
│   ├── application/
│   │   └── service.go         ← use-case orchestration
│   │
│   ├── infrastructure/
│   │   ├── config/config.go   ← config from env
│   │   └── db/postgres.go     ← concrete repository implementations
│   │
│   └── api/
│       ├── routes.go          ← Gin router, /health endpoint wired
│       ├── handler.go         ← HTTP handlers
│       └── middleware.go      ← logging, auth, recovery
│
├── pkg/errors/errors.go       ← shared error types
└── tests/integration/
```

### TypeScript backend (Hono)

```
src/
  domain/         models.ts · events.ts · repositories.ts (interfaces)
  application/    commands.ts · queries.ts
  infrastructure/ config.ts · db.ts
  api/            routes.ts (Hono router) · schemas.ts (Zod)
  index.ts        app factory
  index.test.ts   /health integration test
```

### Next.js frontend (App Router)

```
src/
  app/            layout.tsx · page.tsx (App Router)
  components/ui/  button.tsx — design system primitives
  lib/            utils.ts (pure) · api.ts (typed fetch wrapper)
  types/          index.ts — shared TS types from domain glossary
  hooks/          custom React hooks
  services/       typed API call wrappers
tests/unit/       vitest — pure lib tests included
```

### Monorepo (Turborepo + pnpm)

```
apps/
  api/    src/index.ts · package.json · tsconfig.json
  web/    src/app/page.tsx · package.json · tsconfig.json
packages/
  ui/     shared component library
  shared/ shared types and utilities
  config/ tsconfig/base.json · eslint config
turbo.json · pnpm-workspace.yaml · root package.json
```

### Infrastructure (Pulumi / Terraform)

```
# Pulumi
stacks/dev.py · stacks/staging.py · stacks/prod.py
modules/network.py · modules/compute.py · modules/storage.py
__main__.py  (stack selector)
Pulumi.dev.yaml · Pulumi.staging.yaml · Pulumi.prod.yaml

# Terraform
stacks/dev/ · stacks/staging/ · stacks/prod/   (main.tf, variables.tf, outputs.tf)
modules/network/ · modules/compute/ · modules/storage/
scripts/deploy.sh
```

### Every project also gets

```
CLAUDE.md          ← Claude Code: mandatory workflow + skill manifest
AGENTS.md          ← Codex / OpenAI agents: same workflow
.cursorrules       ← Cursor: same workflow
.windsurfrules     ← Windsurf: same workflow

skills/
  grill-me/        SKILL.md — Socratic design challenge
  tdd/             SKILL.md — red-green-refactor enforcer
  domain-model/    SKILL.md — DDD aggregate + event modeling
  ubiquitous-language/  SKILL.md — glossary-first naming
  qa/              SKILL.md — QA review + 95% coverage gate
  interface-design/     SKILL.md — interface before class
  request-refactor-plan/ SKILL.md — plan before changing existing code
  implementation-simplicity/ SKILL.md — complexity ≤ 3, pure functions

docs/
  domain/glossary.md   ← single source of truth for all names in the codebase
  ADR/0001-...md       ← first-principles SDLC decision record
  CONTRIBUTING.md
```

---

## The 4 steps and their defaults

| Step | What you choose | Default |
|------|----------------|---------|
| **1. Project type** | backend / frontend / monorepo / tooling / infrastructure / docs | `backend` |
| **2. Stack** | language, framework, package manager, CI target | Python / FastAPI / uv / GitHub Actions |
| **3. Metadata** | project name, org, description, license, output directory | `my-project` / MIT / parent directory |
| **4. Skills** | which of the 8 AI skills to include | all 8 enabled |

---

## Project types and supported stacks

| Type | What it's for | Default stack | Also supports |
|------|--------------|---------------|---------------|
| `backend` | REST/GraphQL API, microservice, worker, pipeline | Python / FastAPI / uv | TypeScript / Hono, Go / Gin, Rust / Axum |
| `frontend` | SPA, SSG, component library | TypeScript / Next.js / pnpm | TypeScript / Vite |
| `monorepo` | Full-stack — API + UI + shared packages | TypeScript / Turborepo / pnpm | — |
| `tooling` | CLI tool, SDK, dev library | Python / Typer / uv | TypeScript / Commander, Go / Cobra |
| `infrastructure` | IaC, platform, Kubernetes | Python / Pulumi / uv | HCL / Terraform |
| `docs` | Documentation site | Python / MkDocs / uv | TypeScript / Docusaurus |

Python projects support both **uv** and **poetry** as the package manager.

---

## AI skills — what they enforce

Skills live in `skills/`. Each is a plain markdown file (`SKILL.md`) with a frontmatter header (`name`, `description`) and a **Hard stop** section that tells the AI when to refuse to proceed.

Inspired by [Matt Pocock's skills system](https://github.com/mattpocock/skills/tree/main) — the idea that an AI assistant's behaviour should be encoded in the repo, not re-explained in every prompt.

| Skill | Triggers on | Hard stop |
|-------|-------------|-----------|
| `grill-me` | Any design or architecture review | Won't validate until 3 hard questions are answered |
| `tdd` | Any new function, method, or behaviour | Refuses to write implementation before a failing test exists |
| `domain-model` | Starting a new feature | Requires domain doc before any code |
| `ubiquitous-language` | Naming anything | Requires the name to be in `glossary.md` first |
| `interface-design` | Creating any new module, service, or component | Won't write a concrete class before an interface is defined and tested |
| `implementation-simplicity` | Writing any implementation | Refuses functions with cyclomatic complexity > 3 |
| `request-refactor-plan` | Changing existing code | Requires a written plan before any modification |
| `qa` | Before any PR or merge | Won't approve if coverage < 95%, type errors exist, or lint fails |

---

## How a feature session looks in practice

```
You:   "Add a user registration feature"

AI:    "Before writing code, I need a domain doc.
        Let me add 'User' to docs/domain/glossary.md
        and create docs/domain/user.md."

       [creates glossary entry + domain doc]

       "Now I'll design the interface:"

       [writes UserRepository Protocol + InMemoryUserRepository fake]

       "Now the failing test:"

       [writes test_register_user.py — runs it — confirms red]

       "Now the minimal implementation:"

       [writes just enough to make it green]

       "QA: coverage 97%, zero type errors, zero lint warnings. PR-ready."
```

---

## Pre-commit hooks

Installed once with `pre-commit install`. Same gates run in CI on every push. Hooks are stack-specific — firstcut writes the right config for your language.

**Python** (all Python project types)

| Check | Tool | Gate |
|-------|------|------|
| Lint | `ruff` | zero warnings, auto-fix |
| Format | `ruff-format` + `black` | auto-fix |
| Type check | `mypy --strict` | zero errors |
| Test coverage | `pytest-cov` | ≥ 95% |
| Secret scan | `detect-secrets` | zero secrets |
| Commit message | `commitizen` | conventional commits |

**TypeScript / JavaScript**

| Check | Tool | Gate |
|-------|------|------|
| Format | `prettier --check` | zero diff |
| Lint | `eslint` | zero warnings |
| Type check | `tsc --noEmit` | zero errors |
| Test coverage | `vitest --coverage` | ≥ 95% |
| Secret scan | `detect-secrets` | zero secrets |
| Commit message | `commitizen` | conventional commits |

**Go**

| Check | Tool | Gate |
|-------|------|------|
| Format | `gofmt -l -w` | auto-fix |
| Lint | `golangci-lint run` | zero warnings |
| Test coverage | `go test ./... -coverprofile` | ≥ 80% |
| Secret scan | `detect-secrets` | zero secrets |
| Commit message | `commitizen` | conventional commits |

> Go's coverage threshold is 80% rather than 95%. Go's table-driven test idiom and interface-heavy patterns make 95% impractical without test helpers that add noise; 80% with `golangci-lint` catching dead/unreachable code is the accepted industry standard.

**Rust**

| Check | Tool | Gate |
|-------|------|------|
| Format | `cargo fmt --check` | zero diff |
| Lint | `cargo clippy -D warnings` | zero warnings |
| Test | `cargo test` | all pass |
| Secret scan | `detect-secrets` | zero secrets |
| Commit message | `commitizen` | conventional commits |

**HCL / Terraform**

| Check | Tool | Gate |
|-------|------|------|
| Format | `terraform fmt -check` | zero diff |
| Validate | `terraform validate` | zero errors per stack |
| Lint | `tflint --recursive` | zero warnings |
| Security scan | `checkov` | zero HIGH findings |
| Secret scan | `detect-secrets` | zero secrets |
| Commit message | `commitizen` | conventional commits |

---

## Supported AI tools

| Tool | File it reads | How |
|------|--------------|-----|
| Claude Code | `CLAUDE.md` | Built-in project context |
| OpenAI Codex CLI | `AGENTS.md` | AGENTS.md spec |
| Cursor | `.cursorrules` | Native rules file |
| Windsurf | `.windsurfrules` | Native rules file |
| Any other tool | `skills/*.md` directly | Plain markdown |

All four files point to the same `skills/` directory. Every developer gets consistent enforcement regardless of which AI tool they use.

---

## Requirements

- Python 3.11+ (to develop or publish the canonical package)
- git

The generated project's requirements depend on the stack you choose (uv, poetry, pnpm, go, cargo).

---

## Relationship to Cookiecutter

[Cookiecutter](https://cookiecutter.readthedocs.io) popularised the idea that project setup should be a short question-and-answer session. firstcut takes the same starting point but makes different tradeoffs:

| | Cookiecutter | firstcut |
|---|---|---|
| Template format | Jinja2 template repos (one repo per template) | Packaged Python generator — no external templates |
| Extensibility | Add a new template repo | Edit `src/firstcut/_core.py` and ship the Python package/wrappers |
| AI skills | Not included | 8 skills embedded at project creation |
| Architecture opinions | Depends on the template | Opinionated layers baked in (domain / application / infrastructure / api) |
| Dependencies to run | `pip install cookiecutter` | `firstcut init` via Python, npm, pnpm, or Go launcher |

Use Cookiecutter when you want a large ecosystem of community templates. Use firstcut when you want a single, self-contained generator package that embeds your team's engineering process.

---

## Contributing to firstcut itself

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). This repo eats its own cooking — it enforces the same workflow on itself that it generates for others.

Useful local checks:

```bash
make test      # pytest with the 95% coverage gate
make quality   # lint, format-check, typecheck, and secret scan
```

---

## License

MIT
