from datetime import UTC, datetime
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id, get_repo
from app.infrastructure.db.repositories import MongoRepository

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/internal")
async def internal_messages(
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
):
    return await repo.find_many("internal_messages", {"user_id": user_id}, limit=100, sort=[("created_at", -1)])


@router.post("/internal")
async def send_internal_message(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
):
    message_id = await repo.insert_one(
        "internal_messages",
        {
            "user_id": user_id,
            "text": body.get("text", ""),
            "created_at": datetime.now(UTC),
        },
    )
    return {"id": message_id}

