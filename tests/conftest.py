"""Dobles de prueba compartidos por la suite."""

from uuid import UUID

import pytest

from app.application.entities import Summary
from app.application.interfaces.summary_repository import SummaryRepository


class FakeRepository(SummaryRepository):
    """Repositorio en memoria con el mismo contrato que el real."""

    def __init__(self, available: bool = True):
        self.saved: list[Summary] = []
        self._available = available

    async def save(self, summary: Summary) -> None:
        self.saved.append(summary)

    async def get_by_id(self, summary_id: UUID) -> Summary | None:
        return next((s for s in self.saved if s.id == summary_id), None)

    async def get_all(self, limit: int) -> list[Summary]:
        # El último guardado primero. No ordena por created_at para no depender de
        # la resolución del reloj; el orden por fecha real lo cubre el test de Mongo.
        return list(reversed(self.saved))[:limit]

    async def delete(self, summary_id: UUID) -> bool:
        before = len(self.saved)
        self.saved = [s for s in self.saved if s.id != summary_id]
        return len(self.saved) < before

    async def is_available(self) -> bool:
        return self._available


@pytest.fixture
def fake_repository() -> FakeRepository:
    return FakeRepository()
