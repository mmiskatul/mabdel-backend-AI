from app.models.permission import PermissionEntity
from app.repositories.base import IPermissionRepository
from app.schemas.permission import PermissionUpdate


class PermissionService:
    def __init__(self, repository: IPermissionRepository):
        self.repository = repository

    async def get_permissions(self, user_id: str) -> PermissionEntity:
        permission = await self.repository.get_by_user_id(user_id)
        if permission is None:
            permission = PermissionEntity(user_id=user_id)
            return await self.repository.save(permission)
        return permission

    async def update_permissions(
        self,
        user_id: str,
        payload: PermissionUpdate,
    ) -> PermissionEntity:
        permission = await self.get_permissions(user_id)

        if payload.microphone_enabled is not None:
            permission.microphone_enabled = payload.microphone_enabled
        if payload.notifications_enabled is not None:
            permission.notifications_enabled = payload.notifications_enabled
        if payload.contacts_enabled is not None:
            permission.contacts_enabled = payload.contacts_enabled

        return await self.repository.save(permission)

    async def accept_all(self, user_id: str) -> PermissionEntity:
        return await self.repository.accept_all(user_id)

