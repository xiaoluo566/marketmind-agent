# MarketMind Agent Frontend

Next.js control console for MarketMind Agent.

## Responsibilities

- Submit research tasks to the FastAPI backend
- Display task status, events, and Agent steps
- Browse reports and evidence references
- Keep frontend logic separate from crawler, model, RAG, and database responsibilities

## Current status

Day 1 frontend baseline:

- Next.js 16 App Router
- TypeScript
- Tailwind CSS
- lucide-react icons
- Mock data layer ready to be replaced by FastAPI calls
- Dashboard, New Research, Tasks, Task Detail, Reports, Report Detail, Evidence, and Settings routes

## Development

```bash
npm run dev
```

Open `http://localhost:3000`.

## API integration

API calls are centralized in `src/lib/api.ts`. Mock mode is enabled by default.

Set this later when the FastAPI backend task endpoints are available:

```bash
NEXT_PUBLIC_USE_MOCKS=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

