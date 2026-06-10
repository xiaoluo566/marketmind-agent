# MarketMind Agent Constitution

## Core Principles

### I. Spec-First Development

Every Day33+ feature starts with a Spec Kit SDD pass before code changes. The
active requirement, API contract, state transition, acceptance criteria, and
rollback boundary must be captured or reviewed through Spec Kit artifacts before
implementation. Roadmap documents remain the project timeline, but executable
feature decisions should be reflected in `specs/` and linked back to
`doc/roadmap/day-xx.md` and the related supporting documents.

### II. Test-First Implementation

After the SDD pass, implementation follows TDD. Write or update the failing test
first, confirm the RED state, implement the smallest correct change, then keep
the test green during refactor. Backend changes require pytest coverage;
frontend changes require contract, lint, build, and browser-level verification
when user-visible behavior changes.

### III. Traceable Long-Task Workflow

The product is an engineering-grade e-commerce operations Agent, not a toy LLM
demo. Long-running task behavior must be observable through task status, event
timeline, Agent steps, logs, trace IDs, and recovery paths. Features that affect
task lifecycle must define state transitions and failure behavior before code is
merged.

### IV. Evidence-Grounded Reports

Reports, RAG retrieval, and Agent output must preserve evidence references. The
system must not promote model output that cannot be traced to review chunks,
crawler artifacts, Agent observations, or explicit fallback explanations. Any
LLM or embedding provider integration must keep fake providers for tests and
must not claim production metrics from mock data.

### V. Verification and Documentation Gates

No feature is complete until verification and documentation are both updated.
The required sequence is:

1. Spec Kit SDD.
2. `tdd-workflow` RED/GREEN implementation.
3. Code implementation.
4. `verification-loop` with tests, lint, build, compose config, and security
   checks appropriate to the change.
5. Roadmap, development log, interview dossier, and testing strategy backfill.

## Project Constraints

- Primary branch workflow: daily development happens on `dev`; `main` is kept
  for stable, reviewed milestones.
- Commit messages use Conventional Commit prefixes with Chinese descriptions.
- User-facing frontend copy is Chinese by default; technical IDs such as
  `task_id`, `trace_id`, status enum values, and API fields stay untranslated.
- Docker real build/up, provider calls, token cost, and recovery success rates
  must only be claimed after real verification.
- Secrets must stay in environment variables or local ignored files; generated
  agent folders are reviewed before commit.
- Existing Day1-Day32 roadmap and supporting documentation remain the historical
  source of project decisions.

## Development Workflow

For each Day33+ feature:

1. Review the current roadmap day and related supporting docs.
2. Use Spec Kit skills in this order when appropriate:
   - `$speckit-specify` for requirements and acceptance criteria.
   - `$speckit-plan` for implementation plan.
   - `$speckit-tasks` for actionable task breakdown.
   - `$speckit-analyze` or `$speckit-checklist` when contracts are complex.
3. Use `tdd-workflow` to write failing tests before implementation.
4. Implement with minimal, cohesive code changes.
5. Use `verification-loop` before commit.
6. Update `doc/roadmap/day-xx.md`,
   `doc/supporting/development-log.md`,
   `doc/supporting/interview-defense-dossier.md`, and
   `doc/supporting/testing-strategy.md`.

## Governance

This constitution governs Day33+ development. If a roadmap document conflicts
with this constitution, update the roadmap or write an explicit exception before
implementation. Changes to this constitution require a documentation update in
`doc/supporting/dev-workflow.md` and must be committed separately from unrelated
feature code.

**Version**: 1.0.0 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-06-10
