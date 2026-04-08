from fastapi import APIRouter
from app.api.v1.endpoints import auth, tasks, events, rooms, members, analytics, advice

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router, tags=["auth"])
router.include_router(tasks.router, tags=["tasks"])
router.include_router(events.router, tags=["events"])
router.include_router(rooms.router, tags=["rooms"])
router.include_router(members.router, tags=["members"])
router.include_router(analytics.router, tags=["analytics"])
router.include_router(advice.router, tags=["advice"])
