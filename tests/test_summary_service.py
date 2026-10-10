"""Tests del caso de uso con un repositorio en memoria."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.application.services.summary_service import SummaryService
from tests.conftest import FakeRepository


@pytest.fixture
def service(fake_repository) -> SummaryService:
    return SummaryService(fake_repository)


async def test_create_asigna_un_uuid_y_una_fecha_utc(service):
    summary = await service.create("doc.pdf", "Un resumen")

    assert isinstance(summary.id, UUID)
    assert isinstance(summary.created_at, datetime)
    assert summary.created_at.tzinfo == timezone.utc


async def test_create_conserva_el_nombre_y_el_texto(service):
    summary = await service.create("doc.pdf", "Un resumen")

    assert summary.original_filename == "doc.pdf"
    assert summary.summary_text == "Un resumen"


async def test_create_guarda_exactamente_el_resumen_que_devuelve(service, fake_repository):
    summary = await service.create("doc.pdf", "Un resumen")

    assert fake_repository.saved == [summary]


async def test_cada_resumen_recibe_un_id_distinto(service):
    first = await service.create("a.pdf", "uno")
    second = await service.create("b.pdf", "dos")

    assert first.id != second.id


async def test_get_devuelve_el_resumen_guardado(service):
    summary = await service.create("doc.pdf", "Un resumen")

    assert await service.get(summary.id) == summary


async def test_get_devuelve_none_si_no_existe(service):
    assert await service.get(uuid4()) is None


async def test_list_devuelve_del_mas_reciente_al_mas_antiguo(service):
    first = await service.create("a.pdf", "uno")
    second = await service.create("b.pdf", "dos")

    assert await service.list(limit=10) == [second, first]


async def test_list_respeta_el_limite(service):
    await service.create("a.pdf", "uno")
    await service.create("b.pdf", "dos")

    assert len(await service.list(limit=1)) == 1


async def test_delete_borra_y_devuelve_true(service):
    summary = await service.create("doc.pdf", "Un resumen")

    assert await service.delete(summary.id) is True
    assert await service.get(summary.id) is None


async def test_delete_de_un_id_inexistente_devuelve_false(service):
    assert await service.delete(uuid4()) is False


async def test_is_available_delega_en_el_repositorio():
    assert await SummaryService(FakeRepository(available=True)).is_available() is True
    assert await SummaryService(FakeRepository(available=False)).is_available() is False
