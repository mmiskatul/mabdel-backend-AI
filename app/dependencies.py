from fastapi import Depends

from app.core.database import MongoClientManager
from app.repositories.base import IUserRepository
from app.repositories.user_repository import MongoUserRepository
from app.services.user_service import UserService


def get_user_repository() -> IUserRepository:
    db = MongoClientManager.get_database()
    return MongoUserRepository(db)


def get_user_service(
    repository: IUserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)

