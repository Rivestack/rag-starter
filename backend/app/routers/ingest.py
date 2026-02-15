from fastapi import APIRouter, BackgroundTasks

from app.schemas import IngestResponse
from app.services.ingest import ingest_initial, ingest_daily

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/initial", response_model=IngestResponse)
async def trigger_initial_ingest():
    """Trigger initial 30-day HN data fetch. This may take several minutes."""
    result = await ingest_initial()
    return IngestResponse(**result)


@router.post("/daily", response_model=IngestResponse)
async def trigger_daily_ingest():
    """Trigger daily update: fetch last 24h, clean up old stories."""
    result = await ingest_daily()
    return IngestResponse(**result)
