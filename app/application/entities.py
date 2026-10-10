"""Entidades del dominio. Viven aparte de los puertos que las usan."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Summary:
    id: UUID
    original_filename: str
    summary_text: str
    created_at: datetime
