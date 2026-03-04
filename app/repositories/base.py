from abc import ABC, abstractmethod

from app.models.user import UserEntity


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: str) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[UserEntity]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity:
        raise NotImplementedError

