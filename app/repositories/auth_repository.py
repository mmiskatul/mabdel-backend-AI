from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.auth import AccountEntity
from app.repositories.base import IAuthRepository


class MongoAuthRepository(IAuthRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["accounts"]

    async def create(self, account: AccountEntity) -> AccountEntity:
        result = await self.collection.insert_one(account.to_document())
        created = await self.collection.find_one({"_id": result.inserted_id})
        return AccountEntity.from_document(created)

    async def get_by_email(self, email: str) -> AccountEntity | None:
        document = await self.collection.find_one({"email": email})
        return AccountEntity.from_document(document) if document else None

    async def get_by_phone(self, phone: str) -> AccountEntity | None:
        document = await self.collection.find_one({"phone": phone})
        return AccountEntity.from_document(document) if document else None

    async def get_by_identifier(self, identifier: str) -> AccountEntity | None:
        document = await self.collection.find_one({"$or": [{"email": identifier}, {"phone": identifier}]})
        return AccountEntity.from_document(document) if document else None

    async def get_by_reset_token_hash(self, token_hash: str) -> AccountEntity | None:
        document = await self.collection.find_one({"reset_token_hash": token_hash})
        return AccountEntity.from_document(document) if document else None

    async def update(self, account: AccountEntity) -> AccountEntity:
        if account.id is None or not ObjectId.is_valid(account.id):
            raise ValueError("Account ID is invalid.")

        await self.collection.update_one({"_id": ObjectId(account.id)}, {"$set": account.to_document()})
        updated = await self.collection.find_one({"_id": ObjectId(account.id)})
        return AccountEntity.from_document(updated)

