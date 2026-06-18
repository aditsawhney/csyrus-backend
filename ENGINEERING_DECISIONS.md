# Engineering Decisions

## Architecture

The backend follows a layered structure: API routers → services →
repositories → models. Each layer has one job.

- **API routers** parse the request, enforce role-based access through a
  dependency, call a service, and return the result. They contain no
  business rules.
- **Services** hold the actual rules — who can create a request, when a
  request can be edited, whether a reviewer is allowed to act on a given
  request. Services raise framework-agnostic exceptions
  (`NotFoundError`, `ForbiddenError`, `ConflictError`, `UnauthorizedError`)
  defined in `app/core/exceptions.py` rather than importing FastAPI's
  `HTTPException` directly.
- **Repositories** are the only layer that talks to SQLAlchemy. They expose
  intention-revealing methods (`list_for_reviewer`, `get_owned_request`)
  instead of leaking ORM query objects upward.

The payoff of this split shows up in `main.py`: a single
`@app.exception_handler(AppError)` maps every domain exception to the right
HTTP status code, so no router or service has to remember which status code
means what. It also means the service layer is unit-testable without
spinning up FastAPI at all, although in practice the test suite exercises
everything through the HTTP layer because that's a more honest test of the
whole stack including request validation.

## Auth design

The brief requires Google OAuth only, no password login, with this exact
sequence: `Login with Google → Consent Screen → Successful Auth → JWT
Session Created → Protected App Access`.

A few decisions inside that flow:

- **Authorization code flow, not implicit.** The frontend never sees a
  Google token. It redirects the browser to `/auth/google/login`, which
  redirects to Google; Google redirects back to `/auth/google/callback`
  with a code; the backend exchanges that code server-side for the user's
  profile. This keeps the Google client secret on the server only.
- **The session token is our own JWT, not Google's token.** Once the
  backend has the Google profile, it issues a short-lived, self-signed JWT
  (`app/core/security.py`) carrying the user id and role. This decouples
  the app's session lifetime from Google's token lifetime, and means
  protected routes only need to verify our own signature, not call out to
  Google on every request.
- **Session delivery is an httponly cookie**, set during the OAuth
  callback redirect. `get_current_user` (`app/core/dependencies.py`) also
  accepts a `Bearer` header, since that's the simpler shape for the pytest
  suite and for any future non-browser client, but the browser flow itself
  relies on the cookie so the JWT is never exposed to frontend JavaScript.
- **Role assignment on first login.** The spec defines two roles but
  doesn't define how an account becomes a Reviewer. Provisioning every new
  Google sign-in as a Requester is the safe default — promoting someone to
  Reviewer is an administrative action, not something a user should be
  able to grant themselves by checking a box during signup. See
  `COLLABORATION.md` for what an admin-facing promotion flow would look
  like in a real deployment.

## Database design

Three tables, matching the brief: `users`, `approval_requests`,
`review_actions`. A `ReviewAction` row is created on every approve/reject,
even though `ApprovalRequest.status` already tracks the current state —
this keeps a permanent audit trail (who decided what, and when) separate
from the request's current state, which a single mutable status column on
its own wouldn't give you for free.

Primary keys are UUIDs rather than auto-incrementing integers, since they
don't leak the count of requests in the system and they're safe to generate
client-side later if needed. The one wrinkle: SQLAlchemy's UUID handling
differs between Postgres and SQLite. Rather than write separate models for
local dev versus tests, `app/database/types.py` defines a single `GUID`
type decorator that uses Postgres's native UUID type in production and
falls back to a `CHAR(36)` string under SQLite — so the test suite runs
against the exact same model definitions that hit Postgres in production.

## Testing strategy

Tests run through FastAPI's `TestClient` against the real routers, with
only two things swapped out: the database (in-memory SQLite via dependency
override) and the Google network call (mocked in `test_auth.py`). This was
a deliberate choice over mocking the service layer — hitting the actual
HTTP layer also exercises Pydantic validation, the role-based dependencies,
and the exception-to-status-code mapping, which is most of what could
actually break.

Coverage focuses on the things that are easy to get subtly wrong: a
requester can't read or edit someone else's request, a reviewer can't act
on a request that isn't theirs, a request can't be edited or reviewed twice
once it's left the `PENDING` state, and a repeat Google login reuses the
existing account instead of creating a duplicate.

## Trade-offs accepted

- **`Base.metadata.create_all` instead of Alembic.** Fine for an assessment
  with one schema version and no migration history to manage; the first
  thing I'd add for a real deployment is Alembic, specifically so schema
  changes are reviewable and reversible instead of being whatever
  `create_all` happens to produce.
- **Synchronous SQLAlchemy instead of async.** FastAPI's async story pairs
  well with `asyncpg`, but the sync ORM is more mature, has simpler test
  fixtures, and this app's request volume doesn't come close to needing
  async DB I/O. The OAuth network calls, which are the actual I/O-bound
  part, are async via `httpx.AsyncClient`.
- **No reviewer-listing endpoint in the original spec.** The frontend needs
  some way to populate the "assign a reviewer" dropdown, and the spec
  doesn't define one. Added `GET /requests/reviewers`, scoped to the
  Requester role. Documented as an assumption in `COLLABORATION.md` rather
  than silently added.

## What I'd improve with more time

Alembic migrations, rate limiting on the OAuth callback, structured logging
with request IDs, an admin endpoint (or at least a documented manual
process) for promoting a user to Reviewer, and pagination on the request
list endpoints once the data volume justifies it.
