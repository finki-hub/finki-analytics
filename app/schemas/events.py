from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class UsageEvent(BaseModel):
    event_type: str = Field(description="Used as the Mongo collection name")
    event_id: str | None = Field(
        None,
        description="Unique event identifier (auto-generated if missing)",
    )
    timestamp: datetime | None = Field(
        None,
        description="ISO timestamp (auto-set if missing)",
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description="Optional free-form metadata",
    )
    payload: dict[str, Any] = Field(description="Event-specific data object")


class IngestResponse(BaseModel):
    status: Literal["ok"] = Field("ok", description="Always 'ok' if ingest succeeded")
    event_type: str = Field(description="The event_type under which this was stored")
    event_id: str = Field(description="The UUID of the stored event")
    inserted_id: str = Field(description="The MongoDB `_id` of the created document")
