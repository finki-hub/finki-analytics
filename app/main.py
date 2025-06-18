from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.events import router as events_router
from app.api.health import router as health_router
from app.data.connection import Database
from app.utils.settings import Settings

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    db = Database(dsn=settings.MONGO_URL)
    app.state.db = db
    db.init()
    yield
    db.disconnect()


def make_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.API_VERSION,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Events", "description": "Ingest usage events"},
            {"name": "Health", "description": "Health check & status"},
        ],
        host=settings.HOST,
        port=settings.PORT,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=settings.EXPOSE_HEADERS,
    )

    app.include_router(health_router)
    app.include_router(events_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        raw = exc.body
        if isinstance(raw, bytes | bytearray):
            try:
                body_str = raw.decode("utf-8")
            except Exception:
                body_str = repr(raw)
        else:
            body_str = raw

        content = {"detail": exc.errors(), "body": body_str}
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(content),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal server error occurred."},
        )

    return app


app = make_app(settings)
