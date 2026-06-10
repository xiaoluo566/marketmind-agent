<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan.
<!-- SPECKIT END -->

# MarketMind Agent Project Instructions

This repository uses GitHub Spec Kit for Day33+ spec-driven development.

## Required Daily Workflow

For new feature work after Day32, follow this order:

1. Spec Kit SDD
   - Review or create the feature specification with `$speckit-specify`.
   - Create the implementation plan with `$speckit-plan`.
   - Generate or review actionable tasks with `$speckit-tasks`.
   - Use `$speckit-analyze`, `$speckit-checklist`, or `$speckit-clarify` when the
     contract is ambiguous or cross-module.
2. `tdd-workflow`
   - Write or update failing tests first.
   - Confirm the RED state before implementation.
3. Code implementation
   - Keep changes scoped to the active roadmap day or feature spec.
   - Preserve existing Day1-Day32 docs and contracts.
4. `verification-loop`
   - Run tests, lint, build, compose config, and security checks appropriate to
     the change.
5. Documentation backfill
   - Update `doc/roadmap/day-xx.md`.
   - Update `doc/supporting/development-log.md`.
   - Update `doc/supporting/interview-defense-dossier.md`.
   - Update `doc/supporting/testing-strategy.md`.
   - Update any affected supporting contract document, such as
     `api-contract.md`, `data-model.md`, `frontend-localization-contract.md`,
     `phase-2-practicality-plan.md`, or `deployment.md`.

## Project Boundaries

- Develop on `dev`; keep `main` for stable milestones.
- Use Chinese Conventional Commit descriptions.
- Keep user-facing frontend copy in Chinese.
- Keep technical IDs, API fields, status enum values, trace IDs, and provider
  names untranslated.
- Do not claim real Docker, provider, token-cost, or recovery metrics unless
  they were actually verified.
- Treat `.specify/memory/constitution.md` and
  `doc/supporting/dev-workflow.md` as the source of the Day33+ development
  workflow.
