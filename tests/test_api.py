"""Tests de los endpoints HTTP con un repositorio en memoria. Sin base de datos."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.summary_service import SummaryService
from app.dependencies import get_summary_service
from app.main import app
from tests.conftest import FakeRepository


def client_con(repository: FakeRepository) -> TestClient:
    app.dependency_overrides[get_summary_service] = lambda: SummaryService(repository)
    return TestClient(app)


@pytest.fixture
def client(fake_repository):
    yield client_con(fake_repository)
    app.dependency_overrides.clear()


def crear(client, filename="doc.pdf", text="Un resumen"):
    return client.post("/", json={"original_filename": filename, "summary_text": text})


# --- POST / ---


def test_crear_devuelve_201_con_id_y_fecha(client):
    response = crear(client)

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "doc.pdf"
    assert body["summary_text"] == "Un resumen"
    assert body["id"]
    assert body["created_at"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"original_filename": "doc.pdf"},
        {"summary_text": "Un resumen"},
        {"original_filename": "  ", "summary_text": "Un resumen"},
        {"original_filename": "doc.pdf", "summary_text": ""},
    ],
)
def test_crear_con_datos_incompletos_devuelve_422(client, body):
    assert client.post("/", json=body).status_code == 422


# --- GET / ---


def test_listar_devuelve_los_resumenes_y_el_total(client):
    crear(client, "a.pdf")
    crear(client, "b.pdf")

    body = client.get("/").json()

    assert body["total"] == 2
    assert [s["original_filename"] for s in body["summaries"]] == ["b.pdf", "a.pdf"]


def test_listar_respeta_el_limite(client):
    crear(client, "a.pdf")
    crear(client, "b.pdf")

    assert len(client.get("/?limit=1").json()["summaries"]) == 1


@pytest.mark.parametrize("limit", [0, -1, 1001])
def test_listar_con_un_limite_fuera_de_rango_devuelve_422(client, limit):
    assert client.get(f"/?limit={limit}").status_code == 422


def test_listar_sin_resumenes_devuelve_lista_vacia(client):
    assert client.get("/").json() == {"summaries": [], "total": 0}


# --- GET /{id} ---


def test_obtener_devuelve_el_resumen(client):
    created = crear(client).json()

    response = client.get(f"/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_obtener_un_id_inexistente_devuelve_404(client):
    assert client.get(f"/{uuid4()}").status_code == 404


def test_obtener_un_id_que_no_es_uuid_devuelve_422(client):
    assert client.get("/no-es-un-uuid").status_code == 422


# --- DELETE /{id} ---


def test_borrar_devuelve_204_y_el_resumen_desaparece(client):
    created = crear(client).json()

    response = client.delete(f"/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/{created['id']}").status_code == 404


def test_borrar_un_id_inexistente_devuelve_404(client):
    assert client.delete(f"/{uuid4()}").status_code == 404


# --- GET /health ---


def test_health_responde_200_si_la_base_de_datos_responde(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "summaries"}


def test_health_responde_503_si_la_base_de_datos_no_responde():
    response = client_con(FakeRepository(available=False)).get("/health")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "service": "summaries"}
