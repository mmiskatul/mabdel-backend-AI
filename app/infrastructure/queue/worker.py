from arq.connections import RedisSettings

from app.application.services.agent_service import AgentService
from app.application.services.inbox_service import InboxService
from app.application.services.webhook_service import WebhookService
from app.infrastructure.adapters.factory import AdapterFactory
from app.infrastructure.db.repositories import MongoRepository
from app.shared.config import get_settings


async def process_inbound(ctx, payload: dict) -> None:
    repo = MongoRepository()
    adapters = AdapterFactory()
    inbox_service = InboxService(repo, adapters)
    webhook_service = WebhookService(repo, inbox_service, ctx["queue"], ctx["ws"])
    await webhook_service.process_inbound(payload["raw_event_id"])


async def send_message(ctx, payload: dict) -> None:
    repo = MongoRepository()
    adapters = AdapterFactory()
    inbox_service = InboxService(repo, adapters)
    await inbox_service.process_outbound_message(payload["message_id"], ctx["ws"])


async def agent_decide(ctx, payload: dict) -> None:
    repo = MongoRepository()
    agent_service = AgentService(repo)
    await agent_service.decide_inbound(payload["message_id"])


class WorkerSettings:
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [process_inbound, send_message, agent_decide]

    @staticmethod
    async def startup(ctx):
        from app.infrastructure.queue.arq_queue import ArqJobQueue
        from app.api.websocket.manager import ws_manager

        ctx["queue"] = ArqJobQueue()
        ctx["ws"] = ws_manager

