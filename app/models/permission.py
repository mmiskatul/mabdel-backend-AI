from dataclasses import dataclass


@dataclass
class PermissionEntity:
    user_id: str
    microphone_enabled: bool = False
    notifications_enabled: bool = False
    contacts_enabled: bool = False
    id: str | None = None

    def accept_all(self) -> None:
        self.microphone_enabled = True
        self.notifications_enabled = True
        self.contacts_enabled = True

    def to_document(self) -> dict:
        return {
            "user_id": self.user_id,
            "microphone_enabled": self.microphone_enabled,
            "notifications_enabled": self.notifications_enabled,
            "contacts_enabled": self.contacts_enabled,
        }

    @classmethod
    def from_document(cls, document: dict) -> "PermissionEntity":
        return cls(
            id=str(document["_id"]),
            user_id=document["user_id"],
            microphone_enabled=document.get("microphone_enabled", False),
            notifications_enabled=document.get("notifications_enabled", False),
            contacts_enabled=document.get("contacts_enabled", False),
        )

