import asyncio
import logging

from fastapi import APIRouter

from app.schemas import IngestResponse, PruneResponse
from app.services.ingest import ingest_initial, ingest_daily, prune_old_stories

router = APIRouter(prefix="/api/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)

_ingest_running = False


@router.post("/initial")
async def trigger_initial_ingest():
    """Trigger initial 30-day HN data fetch. Runs in background."""
    global _ingest_running
    if _ingest_running:
        return {"status": "already_running"}
    _ingest_running = True

    async def _run():
        global _ingest_running
        try:
            result = await ingest_initial()
            logger.info(f"Initial ingest completed: {result}")
        except Exception as e:
            logger.error(f"Initial ingest failed: {e}")
        finally:
            _ingest_running = False

    asyncio.create_task(_run())
    return {"status": "started"}


@router.post("/daily", response_model=IngestResponse)
async def trigger_daily_ingest():
    """Trigger daily update: fetch last 24h of stories."""
    result = await ingest_daily()
    return IngestResponse(**result)


@router.post("/prune", response_model=PruneResponse)
async def trigger_prune():
    """Drop stories outside the retention window to keep the database bounded."""
    result = await prune_old_stories()
    return PruneResponse(**result)
