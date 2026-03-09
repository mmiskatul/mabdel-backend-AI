from fastapi import Depends

from app.api.deps import get_repo, get_session_repo
from app.application.services.agent_service import AgentService
from app.application.services.auth_service import AuthService
from app.application.services.email_service import EmailService
from app.persistence.repositories import MongoRepository, MongoSessionRepository
from app.users.service import UserService


def get_auth_service(
    repo: MongoRepository = Depends(get_repo),
    sessions: MongoSessionRepository = Depends(get_session_repo),
) -> AuthService:
    return AuthService(repo, sessions, EmailService())


def get_agent_service(
    repo: MongoRepository = Depends(get_repo),
) -> AgentService:
    return AgentService(repo)


def get_user_service(
    repo: MongoRepository = Depends(get_repo),
) -> UserService:
    return UserService(repo)
