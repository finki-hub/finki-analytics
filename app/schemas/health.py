from datetime import datetime

from pydantic import BaseModel, Field


class RootStatus(BaseModel):
    message: str = Field(
        examples=["My Chat API is running"],
        description="A one-line liveness check message",
    )


class DependencyStatus(BaseModel):
    status: str = Field(
        examples=["ok"],
        description="Low-level status string for this dependency",
    )
    healthy: bool = Field(
        examples=[True],
        description="True if the dependency is healthy, False if not",
    )


class HealthResponse(BaseModel):
    status: str = Field(
        examples=["ok"],
        description="Overall health status of the application",
    )
    timestamp: datetime = Field(
        examples=["2025-06-05T12:34:56Z"],
        description="UTC ISO-8601 timestamp of the check",
    )
    dependencies: dict[str, DependencyStatus] = Field(
        description="Status of each dependency",
        examples=[
            {
                "database": DependencyStatus(
                    status="ok",
                    healthy=True,
                ),
                "cache": DependencyStatus(
                    status="ok",
                    healthy=True,
                ),
            },
        ],
    )
