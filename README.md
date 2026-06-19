# Csyrus Workflow Approval Management System - Backend

A FastAPI backend for a lightweight internal approvals tool. Requesters submit
approval requests to a specific reviewer; reviewers approve or reject with
comments. Authentication is Google OAuth 2.0 only - there is no
email/password login path.

## Stack

Python 3.11+, FastAPI, SQLAlchemy ORM, PostgreSQL, JWT sessions issued after
a Google OAuth handshake.

## Project layout

```
backend/
├── app/
│   ├── api/            # FastAPI routers (HTTP boundary only)
│   ├── core/           # config, JWT, exceptions, auth dependencies
│   ├── database/       # engine/session setup, custom UUID column type
│   ├── models/          # SQLAlchemy ORM models
│   ├── repositories/    # raw DB access, no business rules
│   ├── schemas/          # Pydantic request/response models
│   └── services/         # business logic, sits between API and repositories
├── tests/                # pytest suite
└── main.py
```

See `ENGINEERING_DECISIONS.md` for why the code is split this way.

## Setup

Requires Python 3.11+ and a running PostgreSQL instance (skip Postgres
entirely if you only want to run the test suite - tests use an in-memory
SQLite database).

Using `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Using plain `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy the environment template and fill in real values:

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string, e.g. `postgresql+psycopg2://user:pass@localhost:5432/csyrus` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | From a Google Cloud OAuth 2.0 Client ID (Web application type) |
| `GOOGLE_REDIRECT_URI` | Must exactly match an authorized redirect URI in the Google Cloud console, e.g. `http://localhost:8000/auth/google/callback` |
| `JWT_SECRET_KEY` | Long random string used to sign session JWTs |
| `JWT_ALGORITHM` | Defaults to `HS256` |
| `JWT_EXPIRE_MINUTES` | Session lifetime in minutes |
| `FRONTEND_URL` | Used for CORS and for the post-login redirect target |
| `SESSION_COOKIE_NAME` | Name of the httponly cookie carrying the session JWT |

## Running the app

```bash
uvicorn main:app --reload
```

The API comes up on `http://localhost:8000`. Interactive docs (Swagger UI)
are available at `http://localhost:8000/docs`, and the raw OpenAPI schema at
`/openapi.json`. Tables are created automatically on startup via
`Base.metadata.create_all` - see `ENGINEERING_DECISIONS.md` for why this
isn't Alembic yet.

## Running tests

```bash
pytest -v
```

The suite spins up a fresh in-memory SQLite database per test (see
`tests/conftest.py`), so it never touches the real Postgres database or
your real Google OAuth credentials. The Google token exchange is mocked at
the network boundary in `tests/test_auth.py`.

## API reference

### Auth

| Method | Path | Description |
|---|---|---|
| GET | `/auth/google/login` | Redirects to the Google consent screen |
| GET | `/auth/google/callback?code=...` | Exchanges the code, upserts the user, sets the session cookie, redirects to the frontend |
| GET | `/auth/me` | Returns the authenticated user's profile |

### Requests (Requester role)

| Method | Path | Description |
|---|---|---|
| POST | `/requests` | Create a request (`title`, `description`, `priority`, `reviewer_id`) |
| GET | `/requests` | List the current user's own requests |
| GET | `/requests/{id}` | Fetch one of the current user's own requests |
| PUT | `/requests/{id}` | Edit a request - only while it's still `PENDING` |
| DELETE | `/requests/{id}` | Delete a request - only while it's still `PENDING` |
| GET | `/requests/reviewers` | List users with the Reviewer role, for populating the assignment dropdown (not in the original spec - see `COLLABORATION.md`) |

### Reviewer (Reviewer role)

| Method | Path | Description |
|---|---|---|
| GET | `/reviewer/requests` | List requests assigned to the current reviewer |
| POST | `/reviewer/requests/{id}/approve` | Approve a pending request, with optional `comments` |
| POST | `/reviewer/requests/{id}/reject` | Reject a pending request, with optional `comments` |

All authenticated endpoints accept the session either as an
`Authorization: Bearer <token>` header or as the httponly session cookie set
during the OAuth callback. Role mismatches return `403`, missing/invalid
sessions return `401`, and attempts to act on someone else's request or a
request that's no longer pending return `403`/`409` respectively.

## Authentication flow

```
Login with Google → Google Consent Screen → Successful Auth →
JWT Session Created → Protected App Access
```

New Google accounts are provisioned as `REQUESTER` by default. Promoting an
account to `REVIEWER` is treated as an administrative action outside the
OAuth flow - see `ENGINEERING_DECISIONS.md` and `COLLABORATION.md`.
