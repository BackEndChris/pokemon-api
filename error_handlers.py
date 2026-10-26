import logging

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def install_error_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # Default validation errors echo input, including passwords. Omit it.
        details = [{"loc": item["loc"], "msg": item["msg"], "type": item["type"]} for item in error.errors()]
        return JSONResponse(status_code=422, content={"detail": details})

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, error):
        # SQLAlchemy exception text may contain SQL parameters or credentials.
        logger.error("Database operation failed (%s)", type(error).__name__)
        return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"}, headers={"Retry-After": "5"})

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        logger.error("Unexpected server failure (%s)", type(error).__name__)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
