from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.schemas import UploadRecordingBody
from app.api.service_factory import get_calls_service
from app.application.services.calls_service import CallsService

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("")
async def list_calls(
    filter: str = "all",
    user_id: str = Depends(get_current_user_id),
    service: CallsService = Depends(get_calls_service),
):
    return await service.list_calls(user_id, filter)


@router.get("/stats/monthly")
async def monthly_stats(
    user_id: str = Depends(get_current_user_id),
    service: CallsService = Depends(get_calls_service),
):
    return await service.monthly_stats(user_id)


@router.get("/{call_id}")
async def get_call(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallsService = Depends(get_calls_service),
):
    return await service.get_call(user_id, call_id)


@router.post("/{call_id}/mark_callback")
async def mark_callback(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallsService = Depends(get_calls_service),
):
    return await service.mark_callback(user_id, call_id)


@router.post("/{call_id}/upload_recording")
async def upload_recording(
    call_id: str,
    body: UploadRecordingBody,
    user_id: str = Depends(get_current_user_id),
    service: CallsService = Depends(get_calls_service),
):
    return await service.upload_recording(user_id, call_id, body.recording_url)


@router.post("/{call_id}/transcribe")
async def transcribe(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallsService = Depends(get_calls_service),
):
    return await service.transcribe(user_id, call_id)


@router.post("/{call_id}/summarize")
async def summarize(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallsService = Depends(get_calls_service),
):
    return await service.summarize(user_id, call_id)

