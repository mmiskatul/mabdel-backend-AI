from datetime import UTC, datetime

from app.domain.enums import Platform
from app.infrastructure.db.repositories import MongoRepository
from app.infrastructure.security.token_store import encrypt_oauth_tokens


class IntegrationService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    async def catalog(self, user_id: str) -> list[dict]:
        connected = await self.repo.find_many("integration_accounts", {"user_id": user_id}, limit=200)
        connected_map = {item["platform"]: item for item in connected}
        catalog = []
        for platform in Platform:
            current = connected_map.get(platform.value)
            catalog.append(
                {
                    "platform": platform.value,
                    "description": f"Connect {platform.value} to Unified Inbox",
                    "connected": current is not None and current.get("status") == "connected",
                }
            )
        return catalog

    async def connect(self, user_id: str, platform: Platform) -> dict:
        external_account_id = f"{platform.value}_{user_id}"
        existing = await self.repo.find_one(
            "integration_accounts",
            {"user_id": user_id, "platform": platform.value, "external_account_id": external_account_id},
        )
        if existing:
            return {"status": "connected", "oauth_url": f"https://oauth.example/{platform.value}"}
        integration_id = await self.repo.insert_one(
            "integration_accounts",
            {
                "user_id": user_id,
                "platform": platform.value,
                "external_account_id": external_account_id,
                "display_name": platform.value,
                "status": "connected",
                "scopes": ["messages.read", "messages.write"],
                "connected_at": datetime.now(UTC),
                "disconnected_at": None,
            },
        )
        tokens = encrypt_oauth_tokens(f"mock_access_{integration_id}", f"mock_refresh_{integration_id}")
        await self.repo.insert_one(
            "oauth_tokens",
            {
                "integration_account_id": integration_id,
                "user_id": user_id,
                "access_token_enc": tokens["access_token_enc"],
                "refresh_token_enc": tokens["refresh_token_enc"],
                "expires_at": datetime.now(UTC),
            },
        )
        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": user_id,
                "event_type": "integration_connected",
                "ref": {"type": "integration_account", "id": integration_id},
                "title": "Integration connected",
                "subtitle": platform.value,
                "created_at": datetime.now(UTC),
            },
        )
        return {"status": "connected", "oauth_url": f"https://oauth.example/{platform.value}"}

    async def disconnect(self, user_id: str, platform: Platform) -> dict:
        await self.repo.update_one(
            "integration_accounts",
            {"user_id": user_id, "platform": platform.value, "status": "connected"},
            {"$set": {"status": "disconnected", "disconnected_at": datetime.now(UTC)}},
        )
        return {"status": "disconnected", "platform": platform.value}

