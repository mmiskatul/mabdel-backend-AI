from datetime import UTC, datetime
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id, get_repo
from app.infrastructure.db.repositories import MongoRepository

router = APIRouter(prefix="/automations", tags=["automations"])


@router.get("/rules")
async def list_rules(
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
):
    return await repo.find_many("automation_rules", {"user_id": user_id}, limit=100, sort=[("created_at", -1)])


@router.post("/rules")
async def upsert_rule(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
):
    rule_id = body.get("id")
    if rule_id:
        await repo.update_one(
            "automation_rules",
            {"_id": repo.object_id(rule_id), "user_id": user_id},
            {"$set": {**body, "updated_at": datetime.now(UTC)}},
        )
        return {"id": rule_id, "updated": True}
    new_id = await repo.insert_one(
        "automation_rules",
        {
            "user_id": user_id,
            "enabled": body.get("enabled", True),
            "triggers": body.get("triggers", ["busy_mode_on"]),
            "conditions": body.get("conditions", {"cooldown_minutes": 5}),
            "actions": body.get("actions", ["notify_only"]),
            "reply_template": body.get("reply_template"),
            "schedule_delay_minutes": body.get("schedule_delay_minutes"),
            "add_tags": body.get("add_tags", []),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        },
    )
    return {"id": new_id, "created": True}


@router.get("/jobs")
async def list_jobs(
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
):
    return await repo.find_many("scheduled_jobs", {"user_id": user_id}, limit=100, sort=[("created_at", -1)])

