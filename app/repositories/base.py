from abc import ABC, abstractmethod

from app.models.auth import AccountEntity
from app.models.permission import PermissionEntity
from app.models.signup_validation import SignupValidationEntity
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


class IAuthRepository(ABC):
    @abstractmethod
    async def create(self, account: AccountEntity) -> AccountEntity:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> AccountEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_phone(self, phone: str) -> AccountEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_identifier(self, identifier: str) -> AccountEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_reset_token_hash(self, token_hash: str) -> AccountEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, account: AccountEntity) -> AccountEntity:
        raise NotImplementedError

    @abstractmethod
    async def upsert_signup_validation(self, validation: SignupValidationEntity) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_signup_validation(
        self,
        email: str,
        token_hash: str,
    ) -> SignupValidationEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_signup_validations(self, email: str) -> None:
        raise NotImplementedError
