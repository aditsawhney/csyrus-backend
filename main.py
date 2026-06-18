from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, requests, reviewer
from app.core.config import get_settings
from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.database.database import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_all is convenient for local development and for this
    # assessment's scope. A production deployment would manage schema
    # changes through Alembic migrations instead - see
    # ENGINEERING_DECISIONS.md.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Csyrus Workflow Approval Management System", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(requests.router)
app.include_router(reviewer.router)

_ERROR_STATUS_MAP = {
    NotFoundError: 404,
    ForbiddenError: 403,
    ConflictError: 409,
    UnauthorizedError: 401,
}


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    status_code = _ERROR_STATUS_MAP.get(type(exc), 400)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.get("/health")
def health_check():
    return {"status": "ok"}
