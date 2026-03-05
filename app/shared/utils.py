from datetime import UTC, datetime
from bson import ObjectId


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_object_id(value: str) -> ObjectId:
    return ObjectId(value)


def to_string_id(document: dict) -> dict:
    if "_id" in document:
        document["id"] = str(document["_id"])
    return document

