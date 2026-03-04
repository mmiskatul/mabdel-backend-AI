from dataclasses import dataclass
from datetime import datetime


@dataclass
class AccountEntity:
    full_name: str
    email: str
    phone: str
    password_hash: str
    is_active: bool = True
    id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    reset_code_hash: str | None = None
    reset_code_expires_at: datetime | None = None
    reset_code_channel: str | None = None
    reset_token_hash: str | None = None
    reset_token_expires_at: datetime | None = None

    def to_document(self) -> dict:
        return {
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "password_hash": self.password_hash,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "reset_code_hash": self.reset_code_hash,
            "reset_code_expires_at": self.reset_code_expires_at,
            "reset_code_channel": self.reset_code_channel,
            "reset_token_hash": self.reset_token_hash,
            "reset_token_expires_at": self.reset_token_expires_at,
        }

    @classmethod
    def from_document(cls, document: dict) -> "AccountEntity":
        return cls(
            id=str(document["_id"]),
            full_name=document["full_name"],
            email=document["email"],
            phone=document["phone"],
            password_hash=document["password_hash"],
            is_active=document.get("is_active", True),
            created_at=document.get("created_at"),
            updated_at=document.get("updated_at"),
            reset_code_hash=document.get("reset_code_hash"),
            reset_code_expires_at=document.get("reset_code_expires_at"),
            reset_code_channel=document.get("reset_code_channel"),
            reset_token_hash=document.get("reset_token_hash"),
            reset_token_expires_at=document.get("reset_token_expires_at"),
        )

