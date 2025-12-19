# lexicon

This repository provides a **FastAPI backend** (HTTP API) over the existing formal-languages code in `src/`,
plus a **React frontend** (Vite) in `frontend/`.

## Local development (no Docker)

### Backend
```bash
# From repo root
python -m venv .venv
source .venv/bin/activate
pip install -e .  # or: pip install fastapi uvicorn[standard] pydantic-settings

# Run API on http://localhost:8000
uvicorn backend.app.main:app --reload --port 8000
```

Docs:
- OpenAPI UI: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Local development (Docker Compose)

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Web: `http://localhost:5173`

## API overview

- `POST /api/v1/regex/normalize`
- `POST /api/v1/regex/syntax-tree`
- `POST /api/v1/regex/to-dfa`
