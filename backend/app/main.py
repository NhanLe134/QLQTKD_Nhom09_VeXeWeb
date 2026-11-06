import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, bookings, me, refunds, trips, webhooks
from app.api.validation_errors import handle_validation_error
from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.services.login_rate_limiter import LoginRateLimiter
from app.services.release_job import run_release_job


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if not settings.release_job_enabled:
            yield
            return
        stop_event = asyncio.Event()
        job = asyncio.create_task(
            run_release_job(
                get_session_factory(),
                settings.release_job_interval_seconds,
                stop_event,
            )
        )
        try:
            yield
        finally:
            stop_event.set()
            await job

    app = FastAPI(title="VeXe Backend", lifespan=lifespan)
    # Mỗi app một bộ đếm riêng (test tạo app mới thì bộ đếm mới)
    app.state.login_rate_limiter = LoginRateLimiter(
        settings.login_max_failed_attempts,
        timedelta(minutes=settings.login_lockout_minutes),
    )
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(trips.router, prefix="/api/v1")
    app.include_router(bookings.router, prefix="/api/v1")
    app.include_router(me.router, prefix="/api/v1")
    app.include_router(webhooks.router, prefix="/api/v1")
    app.include_router(refunds.router, prefix="/api/v1")

    return app


app = create_app()
