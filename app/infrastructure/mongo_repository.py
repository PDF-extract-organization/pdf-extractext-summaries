"""Adaptador del puerto SummaryRepository para MongoDB."""

from datetime import datetime, timezone
from uuid import UUID

from pymongo import DESCENDING, AsyncMongoClient
from pymongo.errors import PyMongoError

from app.application.entities import Summary
from app.application.interfaces.summary_repository import SummaryRepository


class MongoSummaryRepository(SummaryRepository):
    def __init__(self, client: AsyncMongoClient, db_name: str):
        self._client = client
        self._collection = client[db_name].summaries

    async def ensure_indexes(self) -> None:
        """Idempotente: se puede llamar en cada arranque."""
        await self._collection.create_index([("created_at", DESCENDING)])

    async def save(self, summary: Summary) -> None:
        await self._collection.insert_one(
            {
                "_id": str(summary.id),
                "original_filename": summary.original_filename,
                "summary_text": summary.summary_text,
                "created_at": summary.created_at,
            }
        )

    async def get_by_id(self, summary_id: UUID) -> Summary | None:
        doc = await self._collection.find_one({"_id": str(summary_id)})
        return self._to_summary(doc) if doc else None

    async def get_all(self, limit: int) -> list[Summary]:
        cursor = self._collection.find().sort("created_at", DESCENDING).limit(limit)
        return [self._to_summary(doc) async for doc in cursor]

    async def delete(self, summary_id: UUID) -> bool:
        result = await self._collection.delete_one({"_id": str(summary_id)})
        return result.deleted_count == 1

    async def is_available(self) -> bool:
        try:
            await self._client.admin.command("ping")
        except PyMongoError:
            return False
        return True

    @staticmethod
    def _to_summary(doc: dict) -> Summary:
        return Summary(
            id=UUID(doc["_id"]),
            original_filename=doc["original_filename"],
            summary_text=doc["summary_text"],
            created_at=_as_utc_datetime(doc["created_at"]),
        )


def _as_utc_datetime(value: datetime | str) -> datetime:
    """Mongo devuelve fechas sin zona; el monolito guardaba texto ISO."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
