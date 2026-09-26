import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import sys
import threading

from fastapi import FastAPI
import uvicorn

from agent import __version__
from agent.api.health import router as health_router
from agent.core.config import settings
from agent.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    logger.info("agent service starting")
    yield
    logger.info("agent service stopping")


app = FastAPI(
    title="JARVIS Agent",
    description="Local-only service for JARVIS Desktop AI",
    version=__version__,
    lifespan=lifespan,
)
app.include_router(health_router)


async def serve_until_parent_closes() -> None:
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=settings.agent_host,
            port=settings.agent_port,
            log_level=settings.log_level.lower(),
        )
    )
    event_loop = asyncio.get_running_loop()

    def watch_parent_pipe() -> None:
        try:
            sys.stdin.buffer.read()
        except OSError:
            return
        event_loop.call_soon_threadsafe(setattr, server, "should_exit", True)

    threading.Thread(target=watch_parent_pipe, name="parent-pipe", daemon=True).start()
    await server.serve()


def run() -> None:
    configure_logging(settings.log_level)
    asyncio.run(
        serve_until_parent_closes()
    )


if __name__ == "__main__":
    run()
