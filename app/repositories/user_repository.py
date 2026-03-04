from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserEntity
from app.repositories.base import IUserRepository


class MongoUserRepository(IUserRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def create(self, user: UserEntity) -> UserEntity:
        result = await self.collection.insert_one(user.to_document())
        created = await self.collection.find_one({"_id": result.inserted_id})
        return UserEntity.from_document(created)

    async def get_by_id(self, user_id: str) -> UserEntity | None:
        if not ObjectId.is_valid(user_id):
            return None
        document = await self.collection.find_one({"_id": ObjectId(user_id)})
        return UserEntity.from_document(document) if document else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        document = await self.collection.find_one({"email": email})
        return UserEntity.from_document(document) if document else None

    async def list_all(self) -> list[UserEntity]:
        users: list[UserEntity] = []
        async for document in self.collection.find():
            users.append(UserEntity.from_document(document))
        return users

    async def update(self, user: UserEntity) -> UserEntity:
        if user.id is None or not ObjectId.is_valid(user.id):
            raise ValueError("User ID is invalid.")

        await self.collection.update_one(
            {"_id": ObjectId(user.id)},
            {
                "$set": {
                    "name": user.name,
                    "email": user.email,
                    "is_active": user.is_active,
                }
            },
        )
        updated = await self.collection.find_one({"_id": ObjectId(user.id)})
        return UserEntity.from_document(updated)

