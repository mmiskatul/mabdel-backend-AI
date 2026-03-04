from app.models.user import UserEntity
from app.repositories.base import IUserRepository
from app.schemas.user import UserCreate


class UserService:
    """Application business logic for users."""

    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def create_user(self, payload: UserCreate) -> UserEntity:
        existing = await self.repository.get_by_email(payload.email)
        if existing:
            raise ValueError("User with this email already exists.")

        user = UserEntity(name=payload.name, email=payload.email)
        return await self.repository.create(user)

    async def get_user(self, user_id: str) -> UserEntity | None:
        return await self.repository.get_by_id(user_id)

    async def list_users(self) -> list[UserEntity]:
        return await self.repository.list_all()

    async def deactivate_user(self, user_id: str) -> UserEntity | None:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return None
        user.deactivate()
        return await self.repository.update(user)

