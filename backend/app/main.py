from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import]
from app.core.config import settings
from app.api.v1.router import router
from app.services.notification_scheduler import send_daily_reminders

_scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Send daily reminders every day at 09:00 local server time
    _scheduler.add_job(
        send_daily_reminders,
        trigger="cron",
        hour=9,
        minute=0,
        id="daily_reminders",
        replace_existing=True,
    )
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)


app = FastAPI(title="HomeTask API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
