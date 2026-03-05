from dataclasses import dataclass
from datetime import datetime


@dataclass
class SignupValidationEntity:
    email: str
    token_hash: str
    expires_at: datetime
    id: str | None = None

    def to_document(self) -> dict:
        return {
            "email": self.email,
            "token_hash": self.token_hash,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_document(cls, document: dict) -> "SignupValidationEntity":
        return cls(
            id=str(document["_id"]),
            email=document["email"],
            token_hash=document["token_hash"],
            expires_at=document["expires_at"],
        )

