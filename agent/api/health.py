from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from agent import __version__

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["jarvis-agent"]
    version: str


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service="jarvis-agent", version=__version__)
