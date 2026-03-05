from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.schemas import ExecuteCommandBody, InterpretCommandBody
from app.api.service_factory import get_command_service
from app.application.services.command_service import CommandService

router = APIRouter(prefix="/commands", tags=["commands"])


@router.post("/interpret")
async def interpret(
    body: InterpretCommandBody,
    user_id: str = Depends(get_current_user_id),
    service: CommandService = Depends(get_command_service),
):
    return await service.interpret(user_id, body.text, body.context)


@router.post("/execute")
async def execute(
    body: ExecuteCommandBody,
    user_id: str = Depends(get_current_user_id),
    service: CommandService = Depends(get_command_service),
):
    return await service.execute(user_id, body.execute_token)


@router.get("/history")
async def history(
    category: str = "all",
    limit: int = 20,
    cursor: str | None = None,
    user_id: str = Depends(get_current_user_id),
    service: CommandService = Depends(get_command_service),
):
    _ = cursor
    return await service.history(user_id, category=category, limit=limit)


@router.post("/{command_run_id}/rerun")
async def rerun(
    command_run_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CommandService = Depends(get_command_service),
):
    return await service.rerun(user_id, command_run_id)

