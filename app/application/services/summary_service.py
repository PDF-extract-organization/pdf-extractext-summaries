"""Caso de uso: el historial de resúmenes."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.entities import Summary
from app.application.interfaces.summary_repository import SummaryRepository


class SummaryService:
    def __init__(self, repository: SummaryRepository):
        self._repository = repository

    async def create(self, original_filename: str, summary_text: str) -> Summary:
        # Único sitio donde se generan el id y la fecha
        summary = Summary(
            id=uuid4(),
            original_filename=original_filename,
            summary_text=summary_text,
            created_at=datetime.now(timezone.utc),
        )
        await self._repository.save(summary)
        return summary

    async def get(self, summary_id: UUID) -> Summary | None:
        return await self._repository.get_by_id(summary_id)

    async def list(self, limit: int) -> list[Summary]:
        return await self._repository.get_all(limit)

    async def delete(self, summary_id: UUID) -> bool:
        return await self._repository.delete(summary_id)

    async def is_available(self) -> bool:
        return await self._repository.is_available()
