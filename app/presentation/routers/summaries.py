from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from app.application.services.summary_service import SummaryService
from app.dependencies import get_summary_service
from app.presentation.schemas import (
    CreateSummaryRequest,
    HealthResponse,
    SummaryListResponse,
    SummaryResponse,
)

NOT_FOUND_DETAIL = "No existe un resumen con ese id."

router = APIRouter()


# Declarada antes que /{summary_id} para que "health" no se tome por un id
@router.get("/health", response_model=HealthResponse)
async def health(service: SummaryService = Depends(get_summary_service)):
    if await service.is_available():
        return HealthResponse(status="healthy", service="summaries")
    return JSONResponse(
        status_code=503, content={"status": "unhealthy", "service": "summaries"}
    )


@router.post("/", response_model=SummaryResponse, status_code=201)
async def create_summary(
    request: CreateSummaryRequest,
    service: SummaryService = Depends(get_summary_service),
):
    return await service.create(request.original_filename, request.summary_text)


@router.get("/", response_model=SummaryListResponse)
async def list_summaries(
    limit: int = Query(100, ge=1, le=1000),
    service: SummaryService = Depends(get_summary_service),
):
    summaries = await service.list(limit)
    return SummaryListResponse(summaries=summaries, total=len(summaries))


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: UUID, service: SummaryService = Depends(get_summary_service)
):
    summary = await service.get(summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return summary


@router.delete("/{summary_id}", status_code=204)
async def delete_summary(
    summary_id: UUID, service: SummaryService = Depends(get_summary_service)
):
    if not await service.delete(summary_id):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return Response(status_code=204)
