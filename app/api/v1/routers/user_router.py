from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_user_service
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return UserRead.model_validate(user.__dict__)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserRead.model_validate(user.__dict__)


@router.get("/", response_model=list[UserRead])
async def list_users(service: UserService = Depends(get_user_service)) -> list[UserRead]:
    users = await service.list_users()
    return [UserRead.model_validate(user.__dict__) for user in users]


@router.patch("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.deactivate_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserRead.model_validate(user.__dict__)

