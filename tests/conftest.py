from __future__ import annotations

import copy
from collections import defaultdict
from datetime import UTC, datetime

import pytest


class FakeRepo:
    def __init__(self):
        self.data: dict[str, list[dict]] = defaultdict(list)
        self._counter = 0

    def object_id(self, value: str):
        return value

    async def insert_one(self, collection: str, document: dict):
        self._counter += 1
        doc = copy.deepcopy(document)
        doc["_id"] = str(self._counter)
        self.data[collection].append(doc)
        return str(self._counter)

    async def find_one(self, collection: str, query: dict):
        for doc in self.data[collection]:
            if self._matches(doc, query):
                return self._clean(doc)
        return None

    async def find_many(self, collection: str, query: dict, limit: int = 50, sort=None):
        matched = [self._clean(d) for d in self.data[collection] if self._matches(d, query)]
        if sort:
            key, order = sort[0]
            matched.sort(key=lambda x: x.get(key), reverse=order < 0)
        return matched[:limit]

    async def update_one(self, collection: str, query: dict, update: dict, upsert: bool = False):
        for i, doc in enumerate(self.data[collection]):
            if self._matches(doc, query):
                if "$set" in update:
                    for key, value in update["$set"].items():
                        self._set_path(doc, key, value)
                if "$inc" in update:
                    for key, value in update["$inc"].items():
                        doc[key] = int(doc.get(key, 0)) + int(value)
                self.data[collection][i] = doc
                return
        if upsert:
            payload = {}
            if "$set" in update:
                payload.update(update["$set"])
            await self.insert_one(collection, payload)

    async def count(self, collection: str, query: dict):
        return len([d for d in self.data[collection] if self._matches(d, query)])

    async def aggregate(self, collection: str, pipeline: list[dict]):
        docs = [self._clean(d) for d in self.data[collection]]
        if len(pipeline) >= 2 and "$group" in pipeline[1]:
            group_field = pipeline[1]["$group"]["_id"].lstrip("$")
            counts = defaultdict(int)
            for doc in docs:
                counts[doc.get(group_field)] += 1
            return [{"_id": k, "count": v} for k, v in counts.items()]
        return docs

    def _matches(self, doc: dict, query: dict):
        for key, value in query.items():
            if key == "$or":
                if not any(self._matches(doc, q) for q in value):
                    return False
                continue
            if isinstance(value, dict) and "$gt" in value:
                lhs = doc.get(key)
                rhs = value["$gt"]
                if lhs is None:
                    return False
                if isinstance(lhs, datetime) and lhs.tzinfo is None:
                    lhs = lhs.replace(tzinfo=UTC)
                if isinstance(rhs, datetime) and rhs.tzinfo is None:
                    rhs = rhs.replace(tzinfo=UTC)
                if not (lhs > rhs):
                    return False
                continue
            if key == "_id":
                if doc.get("_id") != str(value):
                    return False
            elif doc.get(key) != value:
                return False
        return True

    @staticmethod
    def _set_path(doc: dict, dotted_key: str, value):
        parts = dotted_key.split(".")
        node = doc
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    @staticmethod
    def _clean(doc: dict):
        d = copy.deepcopy(doc)
        d["id"] = d.pop("_id")
        return d


class FakeSessions:
    def __init__(self):
        self.tokens: dict[str, dict] = {}

    async def store_refresh_token(self, user_id: str, token_hash: str, expires_at):
        self.tokens[token_hash] = {"user_id": user_id, "expires_at": expires_at, "revoked": False}

    async def revoke_refresh_token(self, token_hash: str):
        if token_hash in self.tokens:
            self.tokens[token_hash]["revoked"] = True

    async def is_refresh_token_active(self, token_hash: str):
        token = self.tokens.get(token_hash)
        if not token:
            return False
        return not token["revoked"]


class FakeEmailService:
    def __init__(self):
        self.sent = []

    async def send_otp(self, to_email: str, code: str, expiry_minutes: int):
        self.sent.append((to_email, code, expiry_minutes))


class FakeWs:
    def __init__(self):
        self.events = []

    async def emit(self, user_id: str, event: str, payload: dict):
        self.events.append((user_id, event, payload))


class FakeQueue:
    def __init__(self):
        self.jobs = []

    async def enqueue(self, name: str, payload: dict):
        self.jobs.append((name, payload))
        return f"job_{len(self.jobs)}"


@pytest.fixture
def fake_repo():
    return FakeRepo()


@pytest.fixture
def fake_sessions():
    return FakeSessions()


@pytest.fixture
def fake_email():
    return FakeEmailService()


@pytest.fixture
def fake_ws():
    return FakeWs()


@pytest.fixture
def fake_queue():
    return FakeQueue()

