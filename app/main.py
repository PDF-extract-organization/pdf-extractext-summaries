from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.dependencies import get_repository
from app.presentation.routers import summaries


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_repository().ensure_indexes()
    yield


app = FastAPI(title="pdf-extractext-summaries", lifespan=lifespan)
app.include_router(summaries.router)
