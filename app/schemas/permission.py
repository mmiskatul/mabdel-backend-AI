from pydantic import BaseModel, ConfigDict


class PermissionUpdate(BaseModel):
    microphone_enabled: bool | None = None
    notifications_enabled: bool | None = None
    contacts_enabled: bool | None = None


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    microphone_enabled: bool
    notifications_enabled: bool
    contacts_enabled: bool

