from fastapi import Depends

from app.core.database import MongoClientManager
from app.repositories.base import IPermissionRepository, IUserRepository
from app.repositories.permission_repository import MongoPermissionRepository
from app.repositories.user_repository import MongoUserRepository
from app.services.permission_service import PermissionService
from app.services.user_service import UserService


def get_user_repository() -> IUserRepository:
    db = MongoClientManager.get_database()
    return MongoUserRepository(db)


def get_user_service(
    repository: IUserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)


def get_permission_repository() -> IPermissionRepository:
    db = MongoClientManager.get_database()
    return MongoPermissionRepository(db)


def get_permission_service(
    repository: IPermissionRepository = Depends(get_permission_repository),
) -> PermissionService:
    return PermissionService(repository)
