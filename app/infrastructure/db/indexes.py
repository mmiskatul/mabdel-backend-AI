async def ensure_indexes(db) -> None:
    await db["users"].create_index("email", unique=True)
    await db["conversations"].create_index([("user_id", 1), ("last_message_at", -1)])
    await db["messages"].create_index([("conversation_id", 1), ("timestamp", -1)])
    await db["messages"].create_index([("user_id", 1), ("platform_message_id", 1)])
    await db["command_runs"].create_index([("user_id", 1), ("created_at", -1)])

