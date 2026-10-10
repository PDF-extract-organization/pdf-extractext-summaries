from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CreateSummaryRequest(BaseModel):
    original_filename: NonBlankText
    summary_text: NonBlankText


class SummaryResponse(BaseModel):
    # Se construye directamente desde la entidad Summary (un dataclass)
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    summary_text: str
    created_at: datetime


class SummaryListResponse(BaseModel):
    summaries: list[SummaryResponse]
    total: int


class HealthResponse(BaseModel):
    status: str
    service: str
