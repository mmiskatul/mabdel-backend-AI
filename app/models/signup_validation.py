from dataclasses import dataclass
from datetime import datetime


@dataclass
class SignupValidationEntity:
    email: str
    code_hash: str | None = None
    code_expires_at: datetime | None = None
    token_hash: str | None = None
    token_expires_at: datetime | None = None
    id: str | None = None

    def to_document(self) -> dict:
        return {
            "email": self.email,
            "code_hash": self.code_hash,
            "code_expires_at": self.code_expires_at,
            "token_hash": self.token_hash,
            "token_expires_at": self.token_expires_at,
        }

    @classmethod
    def from_document(cls, document: dict) -> "SignupValidationEntity":
        return cls(
            id=str(document["_id"]),
            email=document["email"],
            code_hash=document.get("code_hash"),
            code_expires_at=document.get("code_expires_at"),
            token_hash=document.get("token_hash"),
            token_expires_at=document.get("token_expires_at"),
        )
