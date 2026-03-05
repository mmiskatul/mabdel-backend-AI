from datetime import UTC, datetime
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id, get_repo
from app.infrastructure.db.repositories import MongoRepository

router = APIRouter(prefix="/group", tags=["group"])


@router.get("/conversations")
async def list_groups(
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
):
    return await repo.find_many("group_conversations", {"user_id": user_id}, limit=50, sort=[("created_at", -1)])


@router.post("/conversations")
async def create_group(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
):
    group_id = await repo.insert_one(
        "group_conversations",
        {
            "user_id": user_id,
            "name": body.get("name", "New Group"),
            "members": body.get("members", []),
            "created_at": datetime.now(UTC),
        },
    )
    return {"id": group_id}

