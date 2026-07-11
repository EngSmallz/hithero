from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Stable application error that can be mapped at the HTTP boundary."""

    status_code = 500
    default_detail = "Internal Server Error"

    def __init__(self, detail=None):
        super().__init__(detail or self.default_detail)
        self.detail = detail or self.default_detail


class BadRequestError(DomainError):
    status_code = 400


class ForbiddenError(DomainError):
    status_code = 403


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


async def domain_error_handler(_request, exc: DomainError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
