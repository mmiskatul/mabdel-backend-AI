from dataclasses import dataclass


@dataclass
class UserEntity:
    name: str
    email: str
    is_active: bool = True
    id: str | None = None

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def to_document(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active,
        }

    @classmethod
    def from_document(cls, document: dict) -> "UserEntity":
        return cls(
            id=str(document["_id"]),
            name=document["name"],
            email=document["email"],
            is_active=document.get("is_active", True),
        )

