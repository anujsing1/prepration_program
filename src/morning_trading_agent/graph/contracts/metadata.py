"""Workflow run metadata."""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowRunMetadata(BaseModel):
    """Metadata attached to workflow results."""

    run_id: str = ""
    workflow: str = ""
    duration_ms: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    session_mode: str = ""
    strategy: str = ""
    node_count: int = 0
    errors: list[str] = Field(default_factory=list)
