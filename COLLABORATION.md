# Collaboration Notes

## Assumptions made

- **New Google sign-ins default to the Requester role.** The spec defines
  two roles but not how a user becomes a Reviewer. Defaulting to Requester
  and treating Reviewer status as something granted out-of-band (admin
  action, or a one-off DB update in this assessment) seemed safer than
  letting users self-select a role with more authority on signup.
- **A `GET /requests/reviewers` endpoint exists even though it isn't in the
  spec.** The Request Management page needs a way to populate the
  "reviewer assignment" field, and nothing in the brief defines how the
  frontend would know which users are reviewers. Scoped to the Requester
  role and kept intentionally minimal (id + name + email, no extra
  metadata).
- **One reviewer per request, fixed at creation.** The data model has a
  single `reviewer_id` foreign key rather than a list, matching the brief's
  schema exactly. Reassigning a reviewer is allowed through `PUT
  /requests/{id}` but only while the request is still `PENDING`.
- **Editing or deleting a request is blocked once it leaves `PENDING`.**
  The brief doesn't say this explicitly, but allowing edits after a
  decision has been made would let a requester silently change what a
  reviewer already approved or rejected, which defeats the point of having
  an audit trail.

## Known limitations

- No way to revoke a JWT session before it expires (no server-side
  session store, no token blocklist) - a stolen token is valid for the
  full `JWT_EXPIRE_MINUTES` window.
- No pagination, filtering, or sorting on `GET /requests` or `GET
  /reviewer/requests`. Fine at assessment scale, not fine once a reviewer
  has hundreds of requests.
- No way to promote a user to Reviewer through the API or UI - it has to
  be done directly in the database. Documented rather than silently
  worked around.
- No rate limiting on the OAuth callback or any other endpoint.
- Email notifications (e.g. "your request was reviewed") aren't
  implemented; the brief doesn't ask for them, but a real version of this
  tool would need them.

## What would change in production

- Alembic migrations instead of `create_all`, so schema changes ship with
  a reviewable, reversible history.
- A real secrets manager for `JWT_SECRET_KEY` and the Google client
  secret instead of a `.env` file.
- Structured logging with a request id threaded through each request, so
  an approval decision can be traced end to end in logs.
- An admin surface (even a simple one) for managing reviewer assignments,
  instead of direct database edits.
- HTTPS-only cookies enforced unconditionally (currently gated on
  `ENVIRONMENT != "development"` so local development over HTTP still
  works).

## Scalability considerations

The current design comfortably handles the access patterns a single
organization's internal approvals tool would generate - read-heavy,
low write volume, no need for real-time updates. If this grew into
something heavier, the first changes would be: pagination on the list
endpoints, an index-backed search instead of full-table scans as the
`approval_requests` table grows, and moving the OAuth token exchange call
behind a timeout-and-retry wrapper since it's the one external dependency
in the otherwise self-contained request lifecycle. None of that is needed
at this scope, which is why it isn't built - premature infrastructure for
a tool with a handful of users would be its own kind of bad engineering
judgment.
