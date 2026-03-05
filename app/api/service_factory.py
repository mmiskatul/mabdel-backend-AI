from fastapi import Depends

from app.api.deps import get_queue, get_repo, get_session_repo
from app.api.websocket.manager import ws_manager
from app.application.services.agent_service import AgentService
from app.application.services.auth_service import AuthService
from app.application.services.calendar_service import CalendarService
from app.application.services.calls_service import CallsService
from app.application.services.command_service import CommandService
from app.application.services.dashboard_service import DashboardService
from app.application.services.documents_service import DocumentsService
from app.application.services.email_service import EmailService
from app.application.services.inbox_service import InboxService
from app.application.services.integration_service import IntegrationService
from app.application.services.settings_service import SettingsService
from app.application.services.webhook_service import WebhookService
from app.infrastructure.adapters.factory import AdapterFactory
from app.infrastructure.calendar.stub import CalendarStub
from app.infrastructure.db.repositories import MongoRepository, MongoSessionRepository
from app.infrastructure.storage.file_storage import LocalObjectStorage


def get_auth_service(
    repo: MongoRepository = Depends(get_repo),
    sessions: MongoSessionRepository = Depends(get_session_repo),
) -> AuthService:
    return AuthService(repo, sessions, EmailService())


def get_inbox_service(repo: MongoRepository = Depends(get_repo)) -> InboxService:
    return InboxService(repo, AdapterFactory())


def get_webhook_service(
    repo: MongoRepository = Depends(get_repo),
    queue=Depends(get_queue),
) -> WebhookService:
    return WebhookService(repo, InboxService(repo, AdapterFactory()), queue, ws_manager)


def get_integration_service(repo: MongoRepository = Depends(get_repo)) -> IntegrationService:
    return IntegrationService(repo)


def get_dashboard_service(repo: MongoRepository = Depends(get_repo)) -> DashboardService:
    return DashboardService(repo)


def get_calendar_service() -> CalendarService:
    return CalendarService(CalendarStub())


def get_documents_service(repo: MongoRepository = Depends(get_repo)) -> DocumentsService:
    return DocumentsService(repo, LocalObjectStorage())


def get_calls_service(repo: MongoRepository = Depends(get_repo)) -> CallsService:
    return CallsService(repo)


def get_agent_service(repo: MongoRepository = Depends(get_repo)) -> AgentService:
    return AgentService(repo)


def get_settings_service(repo: MongoRepository = Depends(get_repo)) -> SettingsService:
    return SettingsService(repo)


def get_command_service(
    repo: MongoRepository = Depends(get_repo),
    queue=Depends(get_queue),
    inbox: InboxService = Depends(get_inbox_service),
    documents: DocumentsService = Depends(get_documents_service),
    agent: AgentService = Depends(get_agent_service),
) -> CommandService:
    return CommandService(
        repo,
        services={
            "queue": queue,
            "inbox": inbox,
            "documents": documents,
            "agent": agent,
        },
    )

