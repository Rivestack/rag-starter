import ssl as ssl_module
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings


def _build_async_url(raw_url: str) -> tuple[str, dict]:
    """Convert a standard PostgreSQL URL to an asyncpg-compatible one.

    Handles two things:
    1. Swaps the scheme to postgresql+asyncpg://
    2. Strips `sslmode` from the query string (asyncpg uses a connect_args `ssl` param instead)
    """
    parsed = urlparse(raw_url)

    # Fix scheme
    scheme = "postgresql+asyncpg"

    # Extract and remove sslmode from query params
    params = parse_qs(parsed.query)
    sslmode = params.pop("sslmode", [None])[0]

    new_query = urlencode(params, doseq=True)
    new_url = urlunparse((scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    connect_args: dict = {}
    if sslmode and sslmode != "disable":
        # asyncpg expects an ssl.SSLContext instead of sslmode query param
        ctx = ssl_module.create_default_context()
        connect_args["ssl"] = ctx

    return new_url, connect_args


db_url, connect_args = _build_async_url(settings.database_url)

engine = create_async_engine(db_url, echo=False, pool_size=5, max_overflow=10, connect_args=connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
