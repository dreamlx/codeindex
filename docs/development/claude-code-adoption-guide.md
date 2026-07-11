# Adopting Claude Code on an Existing Project

> This guide is for programmers who already have a running project and want to upgrade
> their Claude Code workflow. It is language-agnostic and migration-focused.
>
> Read `team-workflow-guide.md` after this — that document describes what the *destination*
> looks like. This document tells you how to get there from where you are now.
>
> **中文版本**: [claude-code-adoption-guide.zh.md](claude-code-adoption-guide.zh.md)

---

## The Core Insight: Claude Code is Only as Good as the Context You Give It

Most teams use Claude Code like a smarter autocomplete: they paste code, ask a question,
get an answer. That works, but it leaves 80% of the value on the table.

The difference between a useful Claude Code session and a frustrating one is almost always
**whether Claude understands your project before you ask the first question**.

Claude Code has access to your files and terminal — but it doesn't automatically know:
- What this project does
- What conventions you follow
- What tools are installed
- What files NOT to touch
- What "done" means here

Without that context, Claude Code defaults to generic patterns that conflict with your
codebase. With it, Claude Code behaves like a senior engineer who already knows the repo.

**How you provide that context: `CLAUDE.md`**

---

## Part 1: CLAUDE.md — The Foundation

### What it is

`CLAUDE.md` is a plain markdown file that Claude Code reads at the start of every session.
It is your project's standing instructions to the AI. Think of it as the README that
Claude Code — not humans — reads first.

There are two levels:
- `~/.claude/CLAUDE.md` — global rules across all your projects (installed once)
- `<project-root>/CLAUDE.md` — project-specific rules (committed to the repo)

Project-level `CLAUDE.md` overrides global when they conflict.

### Creating it

```bash
# Fastest way: let Claude Code generate a first draft
# Run this inside your project directory in Claude Code:
/init
```

The `/init` slash command reads your project structure and generates a starter `CLAUDE.md`.
You then edit it to add what it missed.

### What belongs in CLAUDE.md

A good `CLAUDE.md` answers these questions for Claude Code:

**1. How to navigate the codebase**
```markdown
## Code Navigation
- Entry point: `src/app.ts` / `cmd/server/main.go` / `manage.py`
- Core modules: `src/services/` (business logic), `src/api/` (HTTP layer)
- Tests: `tests/unit/`, `tests/integration/`
- Do NOT modify: `src/generated/` (auto-generated from protobuf)
```

**2. How to run things**
```markdown
## Commands
- Install: `npm ci` / `pip install -e ".[dev]"` / `./gradlew build`
- Test: `npm test` / `pytest -v` / `./gradlew test`
- Lint: `npm run lint` / `ruff check src/` / `./gradlew ktlintCheck`
- Dev server: `npm run dev` / `uvicorn app:main --reload`
```

**3. Conventions that aren't obvious from the code**
```markdown
## Conventions
- Branch naming: `feature/ticket-NNN-short-description`
- Commit format: `feat(auth): add JWT refresh token support`
- API errors always return `{ error: { code, message } }`, never bare strings
- Database migrations live in `db/migrations/`, never edit them after merge
```

**4. What NOT to do**
```markdown
## Do Not
- Do not run `git push --force` on master
- Do not modify `package-lock.json` manually
- Do not add `console.log` to production code — use the logger in `src/utils/logger.ts`
- Tests must not hit real network or database — use fixtures in `tests/fixtures/`
```

**5. Architecture decisions that would surprise a newcomer**
```markdown
## Architecture Notes
- We use CQRS: reads go through `QueryBus`, writes through `CommandBus`
- Auth middleware runs before route handlers — do not add auth checks inside handlers
- All external API calls go through `src/gateways/` — never call fetch/axios directly from services
```

### What does NOT belong in CLAUDE.md

- Obvious things (`npm install` installs dependencies)
- Information already in README.md that Claude can read
- Step-by-step tutorials — Claude Code reads instructions, not tutorials
- More than ~200 lines — long CLAUDE.md files get ignored in practice

### Good vs bad CLAUDE.md entries

| Bad (too vague) | Good (specific and actionable) |
|-----------------|-------------------------------|
| "Follow best practices" | "Errors: throw `AppError` from `src/errors.ts`, never native `Error`" |
| "Write tests" | "Tests: `jest`, coverage threshold 75%, run with `npm test`" |
| "Use the logger" | "Logging: `import logger from '@/utils/logger'`, never `console.*`" |
| "Be careful with the database" | "DB: never write raw SQL — use the repository pattern in `src/repositories/`" |

---

## Part 2: Give Claude Code a Map of Your Codebase

CLAUDE.md tells Claude Code the rules. But for large codebases, it also needs a **map** —
a way to understand what's where without reading every file.

### The README_AI.md pattern

The codeindex tool generates `README_AI.md` files — one per directory — that describe
what that directory contains, its key exports, and how it relates to other modules.
These files live next to the code and Claude Code reads them before diving into source files.

```bash
# Install codeindex
pip install ai-codeindex

# Generate indexes for your project (works with Python, JS/TS, Java, PHP, Swift)
codeindex init          # creates .codeindex.yaml + adds README_AI.md to .gitignore
codeindex scan-all      # generates README_AI.md in each directory

# After code changes, rescan
codeindex scan ./src/changed-module
```

The result: Claude Code can answer "where is X implemented?" correctly on the first try,
without grepping the entire codebase.

### Manual alternative (if you don't use codeindex)

Write a single `PROJECT_MAP.md` at the root with a module-by-module description.
Less precise than per-directory files, but much better than nothing:

```markdown
# Project Map

## src/auth/
JWT authentication. Key exports: `AuthMiddleware`, `JwtService`, `TokenBlacklist`.
Entry: `auth.module.ts`. Does NOT handle permissions — see `src/rbac/`.

## src/payments/
Stripe integration. `PaymentService.charge()` is the main entry point.
Never instantiate directly — use `PaymentsModule` DI.
All webhook handling lives in `src/payments/webhooks/`.
```

Reference this file in `CLAUDE.md`:
```markdown
## Code Navigation
Read `PROJECT_MAP.md` first before searching for any module.
```

---

## Part 3: Migration Path — Where to Start

Don't try to adopt everything at once. Here's the priority order based on impact vs effort.

### Phase 0 — Context setup (Day 1, 2 hours)
*Unlocks everything else. Do this before writing a single line of code with Claude Code.*

1. Run `/init` in Claude Code to generate starter `CLAUDE.md`
2. Edit `CLAUDE.md`: add commands, conventions, do-not list
3. Run `codeindex scan-all` to generate directory maps (or write `PROJECT_MAP.md` manually)
4. Test: ask Claude Code "where is the user authentication implemented?" and see if the answer is correct

**Success signal**: Claude Code navigates to the right file without guessing.

### Phase 1 — Git discipline (Week 1)
*Makes Claude Code's commits safe and traceable.*

1. Adopt branch naming convention (`feature/`, `fix/`)
2. Adopt conventional commit format — add it to `CLAUDE.md`
3. Add pre-commit hook for lint (see tool table below for your language)

The pre-commit hook is a one-time install that enforces quality automatically.
Claude Code respects hooks — it won't tell you to bypass them.

**Language-agnostic hook setup:**

```bash
# Python
pip install pre-commit
# create .pre-commit-config.yaml (see template below)
pre-commit install

# JavaScript/TypeScript
npm install --save-dev husky lint-staged
npx husky init

# Any language (raw git hook)
cat > .git/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
set -e
# Insert your lint command here
npm run lint    # or: ruff check src/  or: ./gradlew ktlintCheck
EOF
chmod +x .git/hooks/pre-commit
```

**Success signal**: `git commit` runs your linter automatically. Bad code cannot be committed.

### Phase 2 — GitHub Issues as work units (Week 2)
*Gives Claude Code a precise target for each session.*

Instead of: *"Add user profile editing"*

Write an issue with a checklist:
```markdown
## Goal
Users can update their display name and avatar from the profile settings page.

## Checklist
- [ ] `PATCH /api/users/:id` accepts `{ displayName?, avatarUrl? }`
- [ ] Validates displayName length (3–50 chars)
- [ ] Stores in `users` table, updates `updated_at`
- [ ] Returns updated user object
- [ ] Frontend form reflects saved values without page reload
- [ ] Error displayed if validation fails
```

Then tell Claude Code: *"Implement issue #47. Follow TDD — write the failing tests first."*

The checklist items map directly to test cases. Claude Code works through them one by one.

**Success signal**: The Issue checklist and the test file tell the same story.

### Phase 3 — TDD (Week 3–4, gradual)
*The biggest culture change. Don't force it on the whole codebase at once.*

Start with the **next new feature only**. Don't retrofit TDD onto existing code yet.

The rule: for any new function or API endpoint, write a test that calls it before the function exists.

```
# Session with Claude Code:
"I need to implement the password reset flow (issue #52).
Before writing any implementation, write the failing tests first.
Use our test setup in tests/helpers/auth.ts."
```

Build the habit on new code for 2–3 weeks. Then, when you touch old code to fix a bug,
add a regression test as part of the fix. Gradually the coverage rises.

**Never set an aspirational coverage target.** Measure current coverage, set the floor at
`current - 2%`, enforce it in CI. Raise it 5% every quarter.

**Success signal**: You feel uncomfortable writing code without a test first.

### Phase 4 — CI gates (Month 2)
*Automates what the hooks enforce locally, so it covers all contributors.*

Add a CI workflow (GitHub Actions, GitLab CI, etc.) with at minimum:
- Lint job
- Test job with coverage floor (`--coverage-threshold` or equivalent)

See `team-workflow-guide.md §6` for the exact CI structure used in this project.
Translate the steps to your language using the tool table below.

---

## Part 4: Language/Framework Tool Table

The workflow is the same regardless of language. The tools differ.

| What | Python | JavaScript/TypeScript | Java/Kotlin | PHP | Go |
|------|--------|----------------------|-------------|-----|-----|
| **Test runner** | `pytest` | `jest` / `vitest` | JUnit 5 | PHPUnit | `go test` |
| **Coverage** | `pytest-cov` | `jest --coverage` | JaCoCo | `phpunit --coverage` | `go test -cover` |
| **Linter** | `ruff` | `eslint` | ktlint / Checkstyle | PHP-CS-Fixer | `golangci-lint` |
| **Type check** | `mypy` | `tsc --noEmit` | built-in | `phpstan` | built-in |
| **Formatter** | `ruff format` | `prettier` | ktlint | PHP-CS-Fixer | `gofmt` |
| **Pre-commit** | `pre-commit` | `husky` + `lint-staged` | pre-commit / Maven | pre-commit | pre-commit |
| **Build** | `python -m build` | `npm run build` | `./gradlew build` | `composer install` | `go build` |
| **Package manager** | `pip` / `poetry` | `npm` / `pnpm` | Maven / Gradle | Composer | Go modules |

Add your language's commands to `CLAUDE.md` under `## Commands`. Claude Code uses whatever
you specify — it does not assume tools.

---

## Part 5: Effective Claude Code Conversation Patterns

### Start every session with context

Don't just ask a question. Orient Claude Code first:

```
# Bad — Claude Code starts from scratch every session
"How do I add rate limiting?"

# Good — Claude Code knows where it is
"We're working on the API gateway (src/gateway/). I need to add per-user rate limiting
to all authenticated routes. Rate limit config is in src/config/limits.ts.
We use Redis for shared state (see src/cache/redis.ts).
Start by reading the relevant files, then write failing tests."
```

### Reference Issues and files explicitly

```
"Implement issue #31. The affected service is src/notifications/email.service.ts.
Tests go in tests/unit/notifications/. Use the existing email mock in tests/mocks/email.ts."
```

### Delegate complete tasks, not steps

```
# Bad — you become the loop controller
"Write the test."
[Claude writes test]
"Now run it."
[Claude runs test]
"Now implement."

# Good — Claude Code handles the loop
"Implement the checkout discount validation (issue #44) using TDD.
Write tests, run them (should fail), implement until green, then commit."
```

### Ask for a plan on complex changes

```
"Before writing any code: what files will you need to change to add multi-tenancy
to the auth system? List them and explain why each one needs to change."
```

This surfaces unexpected dependencies before you're 200 lines deep.

### Checkpoint on long tasks

For tasks that span multiple modules, ask for an intermediate status:

```
"Stop and tell me: what have you changed so far, what's still left,
and are there any decisions you need me to make before continuing?"
```

---

## Part 6: What Claude Code Does and Doesn't Replace

### It accelerates

- Writing boilerplate (CRUD endpoints, test stubs, migration files)
- Navigating unfamiliar parts of the codebase
- Translating an Issue checklist into test cases
- Running the QA checklist before a PR
- Explaining what a piece of code does

### It does not replace

| Responsibility | Stays with you |
|---------------|----------------|
| Architecture decisions | Claude Code can suggest options, you decide |
| "Is this the right feature?" | Product judgment is yours |
| PR approval | A human reviews before merge |
| Incident response | Claude Code can help investigate, not own |
| Security review | Claude Code assists, you verify |

### Anti-patterns that waste time

| What you do | What happens | Better alternative |
|-------------|-------------|-------------------|
| Give a vague request | Claude Code invents requirements | Write an Issue checklist first |
| Ask it to "just fix CI" without context | It guesses at root cause | Paste the exact CI error log |
| Accept the first solution without reading it | Subtle bugs merge | Read every diff before accepting |
| Use it to generate documentation | Docs drift from code | Generate docs from code (docstrings, JSDoc) |
| Skip CLAUDE.md setup | Generic patterns that conflict with your codebase | Phase 0 takes 2 hours, saves days |

---

## Quick Assessment: Is Your Project Claude Code Ready?

Run through this checklist. Each "No" is a gap in Phase 0–2.

**Context**
- [ ] `CLAUDE.md` exists with commands, conventions, do-not list
- [ ] Claude Code can answer "where is [core feature] implemented?" correctly

**Git discipline**
- [ ] All work is on feature branches (not direct commits to main)
- [ ] Commit messages follow a consistent format
- [ ] Pre-commit hook runs lint

**Testing**
- [ ] You know your current coverage percentage
- [ ] CI fails if tests fail
- [ ] New code is accompanied by tests

**Traceability**
- [ ] Every PR links to a GitHub Issue
- [ ] Issue has a checklist of acceptance criteria

If you have all of these, Claude Code will behave like a well-onboarded engineer on your team.
If you're missing several, start at Phase 0 and work forward — don't skip steps.
