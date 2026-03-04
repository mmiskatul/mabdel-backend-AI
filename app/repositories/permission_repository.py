from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.permission import PermissionEntity
from app.repositories.base import IPermissionRepository


class MongoPermissionRepository(IPermissionRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["permissions"]

    async def get_by_user_id(self, user_id: str) -> PermissionEntity | None:
        document = await self.collection.find_one({"user_id": user_id})
        return PermissionEntity.from_document(document) if document else None

    async def save(self, permission: PermissionEntity) -> PermissionEntity:
        await self.collection.update_one(
            {"user_id": permission.user_id},
            {"$set": permission.to_document()},
            upsert=True,
        )
        updated = await self.collection.find_one({"user_id": permission.user_id})
        return PermissionEntity.from_document(updated)

    async def accept_all(self, user_id: str) -> PermissionEntity:
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "microphone_enabled": True,
                    "notifications_enabled": True,
                    "contacts_enabled": True,
                }
            },
            upsert=True,
        )
        updated = await self.collection.find_one({"user_id": user_id})
        return PermissionEntity.from_document(updated)

