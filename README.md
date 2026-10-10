# pdf-extractext-summaries

Microservicio dueño del historial de resúmenes. Forma parte de
[pdf-extractext](https://github.com/PDF-extract-organization/pdf-extractext), dividido
en microservicios (épica: pdf-extractext#64).

Es el **único** servicio que habla con MongoDB: guarda, lista, consulta y borra
resúmenes. No genera resúmenes ni conoce PDFs.

## Contrato HTTP

Escucha en el puerto `8000`. En el stack completo, Traefik le quita el prefijo
`/summaries`, así que desde fuera `GET /` se ve como `http://pdf.localhost/summaries/`
y `GET /{id}` como `http://pdf.localhost/summaries/{id}`.

| Método y ruta | Entrada | Respuesta |
|---|---|---|
| `POST /` | JSON `{"original_filename", "summary_text"}` | `201` `{"id", "original_filename", "summary_text", "created_at"}` |
| `GET /?limit=100` | `limit` entre 1 y 1000 | `200` `{"summaries": [...], "total": n}`, del más reciente al más antiguo |
| `GET /{id}` | — | `200` el resumen |
| `DELETE /{id}` | — | `204` |
| `GET /health` | — | `200` si Mongo responde a un `ping`; `503` si no |

`id` es un UUID y `created_at` una fecha ISO 8601 en UTC. Los dos los asigna el
servicio al crear el resumen.

### Errores

Todos devuelven `{"detail": "..."}` en español.

| Código | Cuándo |
|---|---|
| `404` | No existe un resumen con ese id (al obtener o borrar) |
| `422` | Faltan campos, están vacíos, el id no es un UUID o `limit` está fuera de rango |

## Almacenamiento

Colección `summaries` en la base de datos `MONGODB_DB_NAME`:

| Campo | Tipo |
|---|---|
| `_id` | UUID como texto |
| `original_filename` | texto |
| `summary_text` | texto |
| `created_at` | fecha nativa (BSON Date) |

- Índice descendente sobre `created_at`, para el listado. Se crea al arrancar; es
  idempotente.
- Los documentos del monolito (con `created_at` como texto ISO y un campo
  `extracted_text`) se siguen leyendo: la fecha se convierte y el campo sobrante se
  ignora. Para ordenar bien junto a los nuevos conviene migrarlos a fecha nativa (#2).

## Configuración

| Variable | Por defecto | Uso |
|---|---|---|
| `MONGODB_URL` | `mongodb://localhost:27017` | Conexión. En el stack completo lleva usuario y contraseña |
| `MONGODB_DB_NAME` | `pdf_extractext` | Base de datos |

Ver `.env.example`. Si Mongo no responde, `/health` devuelve `503` en unos 3 segundos.

## Desarrollo

```bash
uv sync --group dev
uv run pytest                   # unitarios: sin base de datos

docker run -d -p 27017:27017 mongo:7
uv run pytest -m integration    # contra Mongo real; se saltan si no hay Mongo

uv run uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t pdf-extractext-summaries .
docker run -p 8000:8000 -e MONGODB_URL=mongodb://host.docker.internal:27017 pdf-extractext-summaries

curl -H "Content-Type: application/json" \
  -d '{"original_filename": "doc.pdf", "summary_text": "Un resumen"}' http://localhost:8000/
curl http://localhost:8000/
```

La imagen corre con un usuario sin privilegios y declara un `HEALTHCHECK`. La CI
ejecuta los tests unitarios y los de integración (con un Mongo como servicio) en cada
pull request, y al integrar en `main` publica la imagen en
`ghcr.io/pdf-extract-organization/pdf-extractext-summaries`.

## Arquitectura

| Capa | Contiene |
|---|---|
| `app/application/entities.py` | La entidad `Summary`, inmutable |
| `app/application/interfaces` | Puerto `SummaryRepository` |
| `app/application/services` | `SummaryService`: asigna id y fecha, delega en el repositorio |
| `app/infrastructure` | `MongoSummaryRepository`: el único sitio que importa `pymongo` |
| `app/presentation` | Router y schemas de FastAPI |
| `app/dependencies.py` | Cableado desde `Settings`; lo importan el router y `main` |

## Flujo de trabajo

`main` y `develop` son las ramas principales. Los cambios entran por pull request a
`develop`, con los tests en verde en la CI. Los commits citan el issue (`#1`).
