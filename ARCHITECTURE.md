# Architecture

Built with Mermaid (one of the assessment's accepted diagramming tools).
GitHub renders Mermaid code blocks natively, so this file displays as a
diagram directly in the repo — no separate image export needed.

## System components

```mermaid
flowchart LR
    subgraph Client
        FE["React + Vite frontend<br/>(React Router, Axios)"]
    end

    subgraph Server
        API["FastAPI backend"]
        DB[("PostgreSQL")]
    end

    subgraph External
        Google["Google OAuth 2.0"]
    end

    FE -- "Axios calls (withCredentials)" --> API
    API -- "SQLAlchemy ORM" --> DB
    API -- "Authorization code exchange<br/>+ profile fetch" --> Google
    Google -- "redirect with auth code" --> API
    API -- "Set-Cookie: session JWT,<br/>redirect to frontend" --> FE
```

## Authentication sequence

```mermaid
sequenceDiagram
    participant U as User (browser)
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant G as Google OAuth

    U->>FE: Click "Sign in with Google"
    FE->>API: GET /auth/google/login
    API->>U: 302 redirect to Google consent screen
    U->>G: Approve access
    G->>API: 302 redirect to /auth/google/callback?code=...
    API->>G: POST /token (exchange code)
    G->>API: access_token
    API->>G: GET /userinfo
    G->>API: profile (sub, email, name)
    API->>API: find-or-create User, issue JWT
    API->>U: Set-Cookie (httponly session JWT), redirect to frontend
    U->>FE: GET / (cookie sent automatically)
    FE->>API: GET /auth/me (withCredentials)
    API->>FE: current user profile
    FE->>U: Render dashboard for that role
```

## Request lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Requester creates request
    PENDING --> APPROVED: Reviewer approves
    PENDING --> REJECTED: Reviewer rejects
    PENDING --> PENDING: Requester edits (title/description/priority/reviewer)
    APPROVED --> [*]
    REJECTED --> [*]
```

Once a request leaves `PENDING`, it's immutable: no further edits, deletes,
or review actions are accepted on it (enforced in `RequestService` and
`ReviewerService`, see `ENGINEERING_DECISIONS.md`).
