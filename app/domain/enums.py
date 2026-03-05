from enum import Enum


class Platform(str, Enum):
    email_gmail = "email_gmail"
    email_outlook = "email_outlook"
    whatsapp = "whatsapp"
    meta_messenger = "meta_messenger"
    instagram = "instagram"
    telegram = "telegram"
    sms = "sms"
    linkedin = "linkedin"
    x = "x"
    tiktok = "tiktok"
    google_business = "google_business"


class ConversationStatus(str, Enum):
    open = "open"
    closed = "closed"


class AutomationMode(str, Enum):
    manual = "manual"
    suggest = "suggest"
    auto = "auto"


class MessageDirection(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageStatus(str, Enum):
    received = "received"
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class DocumentType(str, Enum):
    invoice = "invoice"
    contract = "contract"
    lease = "lease"
    other = "other"


class DocumentStatus(str, Enum):
    draft = "draft"
    final = "final"
    sent = "sent"
    signed = "signed"
    cancelled = "cancelled"


class CallStatus(str, Enum):
    missed = "missed"
    completed = "completed"
    scheduled = "scheduled"
    callback_needed = "callback_needed"


class CommandStatus(str, Enum):
    completed = "completed"
    archived = "archived"
    exported = "exported"
    delivered = "delivered"
    failed = "failed"

