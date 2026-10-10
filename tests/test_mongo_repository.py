"""Tests de integración del repositorio de MongoDB.

Necesitan un MongoDB en marcha en MONGODB_URL (por defecto mongodb://localhost:27017),
por ejemplo `docker run -d -p 27017:27017 mongo:7`. Se saltan solos si no hay conexión.
Ejecutar con `uv run pytest -m integration`.

Usan una base de datos aparte que se borra al terminar, para no tocar datos reales.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.application.entities import Summary
from app.core import Settings
from app.infrastructure.mongo_repository import MongoSummaryRepository

pytestmark = pytest.mark.integration

TEST_DB = "pdf_extractext_summaries_test"


@pytest.fixture
async def client():
    client = AsyncMongoClient(Settings().mongodb_url, serverSelectionTimeoutMS=1500)
    try:
        await client.admin.command("ping")
    except PyMongoError:
        await client.close()
        pytest.skip("no hay un MongoDB accesible")

    await client.drop_database(TEST_DB)
    yield client
    await client.drop_database(TEST_DB)
    await client.close()


@pytest.fixture
async def repo(client) -> MongoSummaryRepository:
    repo = MongoSummaryRepository(client, TEST_DB)
    await repo.ensure_indexes()
    return repo


def make_summary(filename="doc.pdf", created_at=None) -> Summary:
    return Summary(
        id=uuid4(),
        original_filename=filename,
        summary_text="Un resumen",
        created_at=created_at or datetime.now(timezone.utc).replace(microsecond=0),
    )


async def test_guarda_y_recupera_un_resumen(repo):
    summary = make_summary()

    await repo.save(summary)

    assert await repo.get_by_id(summary.id) == summary


async def test_get_by_id_devuelve_none_si_no_existe(repo):
    assert await repo.get_by_id(uuid4()) is None


async def test_get_all_ordena_del_mas_reciente_al_mas_antiguo(repo):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    old = make_summary("viejo.pdf", now - timedelta(days=1))
    new = make_summary("nuevo.pdf", now)
    await repo.save(old)
    await repo.save(new)

    assert await repo.get_all(limit=10) == [new, old]


async def test_get_all_respeta_el_limite(repo):
    await repo.save(make_summary("a.pdf"))
    await repo.save(make_summary("b.pdf"))

    assert len(await repo.get_all(limit=1)) == 1


async def test_delete_borra_y_devuelve_true(repo):
    summary = make_summary()
    await repo.save(summary)

    assert await repo.delete(summary.id) is True
    assert await repo.get_by_id(summary.id) is None


async def test_delete_de_un_id_inexistente_devuelve_false(repo):
    assert await repo.delete(uuid4()) is False


async def test_created_at_se_guarda_como_fecha_nativa(repo, client):
    summary = make_summary()
    await repo.save(summary)

    doc = await client[TEST_DB].summaries.find_one({"_id": str(summary.id)})

    assert isinstance(doc["created_at"], datetime)


async def test_existe_el_indice_descendente_por_created_at(repo, client):
    indexes = await client[TEST_DB].summaries.index_information()

    assert any(info["key"] == [("created_at", -1)] for info in indexes.values())


async def test_lee_documentos_antiguos_del_monolito(repo, client):
    """El monolito guardaba created_at como texto ISO y un extracted_text que ya no se usa."""
    legacy_id = uuid4()
    await client[TEST_DB].summaries.insert_one(
        {
            "_id": str(legacy_id),
            "original_filename": "antiguo.pdf",
            "summary_text": "Resumen antiguo",
            "extracted_text": "texto que ya no se guarda",
            "created_at": "2026-04-20T10:00:00+00:00",
        }
    )

    summary = await repo.get_by_id(legacy_id)

    assert summary.original_filename == "antiguo.pdf"
    assert summary.created_at == datetime(2026, 4, 20, 10, 0, tzinfo=timezone.utc)


async def test_is_available_es_true_con_mongo_en_marcha(repo):
    assert await repo.is_available() is True


async def test_is_available_es_false_si_mongo_no_responde():
    unreachable = AsyncMongoClient(
        "mongodb://localhost:1", serverSelectionTimeoutMS=300
    )
    repo = MongoSummaryRepository(unreachable, TEST_DB)

    assert await repo.is_available() is False
    await unreachable.close()
