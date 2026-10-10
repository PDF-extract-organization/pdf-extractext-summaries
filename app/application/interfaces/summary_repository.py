"""Puerto de persistencia: solo guarda y lee. La identidad la asigna el servicio."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.application.entities import Summary


class SummaryRepository(ABC):
    @abstractmethod
    async def save(self, summary: Summary) -> None:
        """Guarda el resumen tal cual, sin modificarlo."""

    @abstractmethod
    async def get_by_id(self, summary_id: UUID) -> Summary | None: ...

    @abstractmethod
    async def get_all(self, limit: int) -> list[Summary]:
        """Del más reciente al más antiguo."""

    @abstractmethod
    async def delete(self, summary_id: UUID) -> bool:
        """True si existía y se borró."""

    @abstractmethod
    async def is_available(self) -> bool:
        """True si el almacenamiento responde."""
