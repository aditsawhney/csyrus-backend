class AppError(Exception):
    """Base class for domain-level errors that get translated into HTTP responses.

    Keeping these framework-agnostic means the service layer never has to
    import FastAPI - the translation to HTTP status codes happens once,
    in main.py.
    """


class NotFoundError(AppError):
    pass


class ForbiddenError(AppError):
    pass


class ConflictError(AppError):
    pass


class UnauthorizedError(AppError):
    pass
