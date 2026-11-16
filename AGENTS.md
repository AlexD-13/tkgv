# AGENTS.md — GestionPlatos

Instructions for AI agents working on this repository.

## Project

Lightweight web platform (no registration/login) to organize food contributions for a Thanksgiving dinner. Guests browse dishes, sign up for one with free seats, or propose a new dish. Organizers (Alexis and Mariló) get a private panel to manage quotas, approve suggestions, and control attendance.

## Stack

- Backend: Python 3.13, FastAPI, Uvicorn, python-decouple.
- Database: SQLite (file: `backend/database.db`), accessed with **SQLAlchemy Core only** (no ORM) + `aiosqlite` async driver.
- Frontend: Nuxt 4, Vue 3, Nuxt UI, Tailwind CSS 4, TypeScript.
- Migrations: Alembic (raw SQL migrations preferred).

## Critical rule: raw SQL only

- **Do NOT define SQLAlchemy ORM models** (`Base`, `mapped_column`, `relationship`, declarative classes, etc.). The "magic" of ORM models is explicitly out of scope.
- SQLAlchemy is used **only** for connection management and its infrastructure advantages: `create_async_engine`, `AsyncSession`, connection pooling, transaction control, `text()` execution, and `event.listen` for PRAGMAs.
- All queries must be **raw SQL** written with `sqlalchemy.text(...)`. Map result rows to Pydantic schemas or plain dicts manually.
- Schema changes are expressed as raw SQL (see `docs/schema.sql` and Alembic migrations), never via `Base.metadata.create_all` or ORM.

## Database conventions (SQLite)

- Enable per-connection PRAGMAs: `PRAGMA foreign_keys = ON;` and `PRAGMA busy_timeout = ...;`.
- Writes that touch quotas must run in a single transaction using `BEGIN IMMEDIATE` semantics (via SQLAlchemy `begin()` with isolation) and verify the quota before insert.
- Concurrency: SQLite serializes writes per file. Handle `SQLITE_BUSY` with a busy_timeout and return a friendly 409 on conflict.
- `updated_at` is maintained by a DB trigger (see `docs/schema.sql`); do not rely on ORM hooks.

## Backend structure

```
backend/
├── main.py
├── core/          # config (decouple), security (admin token)
├── database/      # engine, session factory, PRAGMA listeners
├── schemas/       # Pydantic request/response models
├── services/      # business logic + raw SQL queries
├── routers/       # FastAPI routers (thin; delegate to services)
└── alembic/       # migrations (raw SQL)
```

- Routers stay thin: parse/validate input, call a service, return a schema.
- Services own SQL and business rules (quota checks, proposal approval flow).
- No ORM models anywhere in the tree.

## Frontend

- Mobile-first (primary entry is WhatsApp links).
- Public view: welcome + dish list with live occupancy + sign-up/propose.
- Admin view under a protected route (`/admin`) with token.
- Internal fields (`min_quota`, `tested`) must never be exposed in public endpoints/UI.
- Nuxtjs. only nuxtUI. 

## Coding standards

- Python: type hints everywhere, async endpoints, Pydantic v2 schemas.
- SQL: parameterized queries only (`:param` bind params) — never string interpolation.
- Conventional commits; no AI attribution.
- Artifacts (code, comments, identifiers, UI copy) in English.

## Do / Don't

- Do: use `text("SELECT ... WHERE id = :id")` with bound params.
- Do: map `result.mappings()` rows to schemas manually.
- Don't: import `declarative_base`, `mapped_column`, or define ORM classes.
- Don't: use `Base.metadata.create_all` for schema creation.
- Don't: expose admin-only fields in public responses.
