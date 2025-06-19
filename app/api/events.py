import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)

from app.data.connection import Database
from app.data.db import get_db
from app.extractors.context_faq_extractor import (
    perform_context_faq_extraction_and_update,
    prepare_context_faq_data,
)
from app.extractors.targeted_faq_extractor import (
    perform_direct_faq_extraction_and_update,
    prepare_direct_faq_data,
)
from app.schemas.events import IngestResponse, UsageEvent
from app.utils.auth import verify_api_key

db_dep = Depends(get_db)

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    dependencies=[db_dep],
)


@router.post(
    "/ingest",
    summary="Ingest a usage event",
    description=(
        "Accepts a `UsageEvent` JSON body, auto-generates `event_id` and "
        "`timestamp` if omitted, then persists it into the MongoDB collection "
        "named by `event_type`. Collections are created on first insert. "
        "For 'faq' events, an answer extraction task is queued in the background, "
        "using either direct user message or context analysis."
    ),
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Confirmation with stored event identifiers",
    operation_id="ingestUsageEvent",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid payload or database insertion error",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or missing API Key",
        },
    },
    dependencies=[Depends(verify_api_key)],
)
async def ingest_event(
    event: UsageEvent,
    background_tasks: BackgroundTasks,
    db: Database = db_dep,
) -> IngestResponse:
    if not event.event_id:
        event.event_id = str(uuid.uuid4())
    if not event.timestamp:
        event.timestamp = datetime.now(UTC)

    coll = db.get_collection(event.event_type)
    doc = event.model_dump(mode="json", exclude_none=True)

    try:
        result = await coll.insert_one(doc)
        inserted_id_str = str(result.inserted_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to insert event: {exc}",
        ) from exc

    if event.event_type == "faq":
        direct_faq_data = prepare_direct_faq_data(event)

        if direct_faq_data:
            print(
                f"FAQ event {event.event_id}: Direct question found. Queuing direct extraction.",
            )
            background_tasks.add_task(
                perform_direct_faq_extraction_and_update,
                db,
                direct_faq_data,
            )
        else:
            context_faq_data = await prepare_context_faq_data(event)

            if context_faq_data:
                print(
                    f"FAQ event {event.event_id}: No direct question, but relevant message found in context. Queuing context extraction.",
                )
                background_tasks.add_task(
                    perform_context_faq_extraction_and_update,
                    db,
                    context_faq_data,
                )
            else:
                print(
                    f"FAQ event {event.event_id}: No direct question and no relevant message found in context. Skipping extraction.",
                )
    else:
        print(
            f"Event {event.event_id} (type: {event.event_type}): Not an FAQ event, skipping extraction logic.",
        )

    return IngestResponse(
        status="ok",
        event_type=event.event_type,
        event_id=event.event_id,
        inserted_id=inserted_id_str,
    )


@router.get(
    "/{event_type}/",
    summary="List usage events",
    description=(
        "Return events of type `event_type` with optional filtering "
        "by timestamp. Results are sorted newest first."
    ),
    response_model=list[UsageEvent],
    status_code=status.HTTP_200_OK,
    response_description="A page of matching usage events",
    operation_id="listUsageEvents",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "No such event_type collection exists",
        },
    },
)
async def list_events(
    event_type: str = Path(
        description="Name of the event_type / MongoDB collection",
    ),
    start_time: datetime | None = Query(  # noqa: B008
        None,
        description="Only events on or after this ISO timestamp",
    ),
    end_time: datetime | None = Query(  # noqa: B008
        None,
        description="Only events on or before this ISO timestamp",
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of events to skip (offset for pagination)",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=10000,
        description="Max number of events to return (capped at 10 000)",
    ),
    db: Database = db_dep,
) -> list[UsageEvent]:
    coll = db.get_collection(event_type)

    query: dict = {}
    if start_time or end_time:
        ts_filter: dict = {}
        if start_time:
            ts_filter["$gte"] = start_time
        if end_time:
            ts_filter["$lte"] = end_time
        query["timestamp"] = ts_filter

    if event_type not in await db.db.list_collection_names():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No events of type '{event_type}' found",
        )

    cursor = coll.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
    events = await cursor.to_list(length=limit)

    return events
