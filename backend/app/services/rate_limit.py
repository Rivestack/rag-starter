"""Per-IP daily cap on searches.

Each search costs one embedding call, so on a public demo this is the spend cap.
"""

import logging

from fastapi import Request
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.database import async_session
from app.models import SearchQuota

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Return the caller's IP address.

    The ingress runs with `use-forwarded-headers` and `compute-full-forwarded-for`,
    so nginx does NOT replace X-Forwarded-For — it appends the PROXY-protocol peer
    address to whatever the client sent:

        X-Forwarded-For: <anything the client made up>, <real address>

    Only the last entry is written by nginx, so it is the only one that cannot be
    forged. Reading the conventional leftmost entry here would let any caller
    reset their quota just by sending the header, which defeats the cap entirely.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        candidate = forwarded.split(",")[-1].strip()
        if candidate:
            return candidate[:45]
    if request.client and request.client.host:
        return request.client.host[:45]
    # No usable address: bucket these together rather than granting free rein.
    return "unknown"


async def consume_search(client_ip: str) -> tuple[bool, int, int]:
    """Count one search against today's allowance for this IP.

    Increments and reads in a single statement so concurrent requests cannot both
    observe the same pre-increment value and slip past the cap.

    Returns (allowed, used, limit).
    """
    limit = settings.search_rate_limit_per_day

    stmt = (
        insert(SearchQuota)
        .values(client_ip=client_ip, day=func.current_date(), count=1)
        .on_conflict_do_update(
            index_elements=["client_ip", "day"],
            set_={"count": SearchQuota.count + 1},
        )
        .returning(SearchQuota.count)
    )

    try:
        async with async_session() as session:
            used = await session.scalar(stmt)
            await session.commit()
    except Exception:
        # Never let a counter problem take search down; log loudly and allow.
        logger.exception("search quota check failed for %s; allowing request", client_ip)
        return True, 0, limit

    return used <= limit, used, limit


async def refund_search(client_ip: str) -> None:
    """Give back a search that was counted but never actually performed.

    Consumption happens before the embedding call so that concurrent requests
    cannot overshoot the cap. When that call then fails, the caller spent nothing
    and should not lose their allowance — during the embedding outage that would
    have silently burned every visitor's five searches on failures.
    """
    try:
        async with async_session() as session:
            row = await session.scalar(
                select(SearchQuota).where(
                    SearchQuota.client_ip == client_ip,
                    SearchQuota.day == func.current_date(),
                )
            )
            if row and row.count > 0:
                row.count -= 1
                await session.commit()
    except Exception:
        logger.exception("failed to refund search quota for %s", client_ip)


async def prune_quota(keep_days: int = 7) -> int:
    """Drop counters older than the window so visitor IPs are not kept around."""
    async with async_session() as session:
        result = await session.execute(
            delete(SearchQuota).where(
                SearchQuota.day < func.current_date() - keep_days
            )
        )
        await session.commit()
    return result.rowcount or 0
