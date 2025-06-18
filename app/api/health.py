from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.data.connection import Database
from app.data.db import get_db
from app.schemas.health import DependencyStatus, HealthResponse, RootStatus

db_dep = Depends(get_db)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
    dependencies=[db_dep],
)


@router.get(
    "/",
    summary="API Status",
    response_model=RootStatus,
    status_code=status.HTTP_200_OK,
    operation_id="getApiStatus",
)
@router.head("/", include_in_schema=False)
async def root() -> RootStatus:
    return RootStatus(message="The API is up and running.")


@router.get(
    "/health",
    summary="Application Health Check",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    operation_id="getHealthStatus",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "Service unhealthy",
        },
    },
)
@router.head("/health", include_in_schema=False)
async def health_check(db: Database = db_dep) -> JSONResponse:
    db_status = "ok"
    healthy = True

    if not hasattr(db, "client") or db.client is None:
        db_status = "mongo_client_not_initialized"
        healthy = False
    else:
        try:
            ping = await db.client.admin.command("ping")
            if ping.get("ok") != 1:
                db_status = "mongo_ping_unexpected"
                healthy = False
        except Exception:
            db_status = "mongo_ping_error"
            healthy = False

    overall = "ok" if healthy else "unhealthy"
    code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    payload = HealthResponse(
        status=overall,
        timestamp=datetime.now(UTC),
        dependencies={"database": DependencyStatus(status=db_status, healthy=healthy)},
    )

    return JSONResponse(
        status_code=code,
        content=jsonable_encoder(payload.model_dump()),
    )
