# Implementation Plan: 真实应用闭环

## Technical Context

- Backend: FastAPI, SQLAlchemy, Pydantic.
- Storage: existing `tasks`, `products`, `reviews`, `review_chunks`.
- Frontend: Next.js App Router.
- RAG: existing review chunk store and deterministic embedding test provider.
- Report: existing evidence-bound report prompt and evidence chain API.

## Implementation Steps

1. Write RED tests for CSV/JSON import, JSON-LD adapter and frontend import page.
2. Implement `app.imports` parsing and persistence service.
3. Add `POST /api/imports/reviews`.
4. Add JSON-LD Product.review extraction to crawler extractor.
5. Add `importReviews()` frontend client, `/imports` page and `ReviewImportForm`.
6. Update supporting docs.
7. Run verification loop.

## Risk Controls

- Keep `author` as hash in persisted review row.
- Do not treat JSON-LD adapter as anti-bot bypass.
- Keep invalid JSON as whole-payload 400, but row-level content errors as partial import errors.
- Do not modify report generation to accept evidence ids outside provided evidence refs.

