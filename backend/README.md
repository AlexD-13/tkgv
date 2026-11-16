# Backend — GestionPlatos API

FastAPI service backing the Thanksgiving dinner dish management platform. Handles dishes, quotas, registrations, guest proposals, and admin panel operations.

## Stack

- Python 3.13
- FastAPI + Uvicorn
- python-decouple (config)
- (planned) SQLAlchemy + SQLite

## Project layout (current + planned)

```
backend/
├── main.py                 app entry point, CORS, static serving
├── config/
│   └── logging_config.py   logging setup
├── routers/                API routers (planned: dishes, registrations, proposals, admin)
├── services/               business logic (planned)
├── database/               models & session (planned)
├── public/                 built frontend assets (served by FastAPI)
├── .env                    environment variables
└── pyproject.toml
```

## Environment variables

See `.env`. Key ones:

- `DATABASE_URL` — SQLite connection string (e.g. `sqlite:///./database.db`)
- `SECRET_KEY` — app secret
- `CORS_ORIGINS` — comma-separated allowed origins
- `ACCESS_TOKEN_EXPIRE_DAYS`, `AUTH_COOKIE_*` — session cookie settings (if admin auth is enabled)

## Run

```bash
cd backend
uv sync
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: `http://localhost:8000/docs`

## Concurrency note

Quota decrement on sign-up must be atomic to prevent two guests taking the last seat (RNF-01). SQLite serializes writes per DB file; use a single write transaction (`BEGIN IMMEDIATE`) and verify
`(SELECT COUNT(*) FROM registrations WHERE dish_id = ?) < max_quota` before inserting. Set a `busy_timeout` on the connection to handle lock contention.
