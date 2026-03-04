from abc import ABC, abstractmethod

from app.models.permission import PermissionEntity
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


class IPermissionRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> PermissionEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, permission: PermissionEntity) -> PermissionEntity:
        raise NotImplementedError

    @abstractmethod
    async def accept_all(self, user_id: str) -> PermissionEntity:
        raise NotImplementedError
