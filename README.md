# GestionPlatos

Lightweight web platform (no registration, no login) to organize food contributions for a group Thanksgiving dinner. Guests browse dishes in real time, sign up for one with free seats, or propose a new dish. Organizers (Alexis and Mariló) get a private panel to manage min/max quotas, approve suggestions, and control attendance.

## Status

Scaffold stage: the frontend is still the Nuxt UI dashboard template and the backend is an empty FastAPI skeleton. Feature implementation is pending. See the requirements summary below.

## Repository layout

```
GestionPlatos/
├── backend/          FastAPI service (Python 3.13)
├── frontend/         Nuxt 4 + Nuxt UI web app (Vue 3)
├── docs/             SQL schema and design notes
├── .gitignore
└── README.md
```

## Stack (planned)

- Frontend: Nuxt 4, Vue 3, Nuxt UI, Tailwind CSS, TypeScript
- Backend: FastAPI, Python 3.13, Uvicorn
- Persistence: relational database (MySQL in production, SQLite for local dev)
- Concurrency: atomic quota decrement (row-level locking / conditional update)

## Functional requirements (summary)

Public module (guests, no auth):

- RF-01 frictionless access via link, no account/email
- RF-02 welcome screen + live occupancy (e.g. 3/5, 4/5 — 1 left, 0/5 available)
- RF-03 show sign-up option or "already registered on this device" (allow registering a companion)
- RF-04 sign up to an existing dish with free seats (Name, Last name); auto-decrement seat; block at max
- RF-05 propose a new dish (Name, Last name, dish name/description); sent to review tray + notification

Admin module (Alexis and Mariló, private link/credential):

- RF-06 restricted access
- RF-07 create/edit/deactivate dishes; set min (desired threshold) and max (hard limit) quotas; internal "tested/validated" flag
- RF-08 review guest proposals; approve (assign quotas + tested flag → publish) or discard
- RF-09 attendance list grouped by dish; delete/reassign registrations, freeing seats

Non-functional: atomic quota decrement under concurrency (RNF-01); fast mobile load from WhatsApp links (RNF-02); persistent storage across the event cycle (RNF-03, Tue review → Wed launch → Mon close).

Business rules: a dish at max quota stops accepting sign-ups automatically; guest proposals are never auto-published; min quota and tested flag are internal control indicators.

## Getting started

### Backend

```bash
cd backend
uv sync            # or: pip install -e .
# adjust DATABASE_URL, SECRET_KEY, CORS_ORIGINS in .env
uvicorn main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/status`

### Frontend

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:3000
```

Point the frontend API base at the backend (see `frontend/.env.example`).

## Development notes

- Frontend is currently the Nuxt UI dashboard template; pages/components will be replaced with the dish-management UI.
- Backend exposes CORS for `http://localhost:5173` and `http://localhost:3000` by default.
- Database schema draft: `docs/schema.sql`.

## License

TBD.
