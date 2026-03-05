from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.schemas import InterpretCommandBody
from app.api.service_factory import get_command_service
from app.application.services.command_service import CommandService

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/interpret")
async def voice_interpret(
    body: InterpretCommandBody,
    user_id: str = Depends(get_current_user_id),
    command_service: CommandService = Depends(get_command_service),
):
    return await command_service.interpret(user_id, body.text, body.context)

