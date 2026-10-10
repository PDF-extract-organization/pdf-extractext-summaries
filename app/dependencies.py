"""Cableado de dependencias. Router y main lo importan; él no importa a ninguno."""

from functools import lru_cache

from pymongo import AsyncMongoClient

from app.application.services.summary_service import SummaryService
from app.core import Settings
from app.infrastructure.mongo_repository import MongoSummaryRepository

# Que /health responda rápido si Mongo no está, en vez de esperar 30 s
SERVER_SELECTION_TIMEOUT_MS = 3000


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_repository() -> MongoSummaryRepository:
    settings = get_settings()
    client = AsyncMongoClient(
        settings.mongodb_url, serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS
    )
    return MongoSummaryRepository(client, settings.mongodb_db_name)


@lru_cache
def get_summary_service() -> SummaryService:
    return SummaryService(get_repository())
