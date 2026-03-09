async def ensure_indexes(db) -> None:
    await db["users"].create_index("email", unique=True)
    await db["signup_validations"].create_index("email", unique=True)
    await db["refresh_tokens"].create_index("token_hash", unique=True)
    await db["password_reset_requests"].create_index("email", unique=True)
    await db["agent_sessions"].create_index([("user_id", 1), ("last_active_at", -1)])
    await db["agent_messages"].create_index([("session_id", 1), ("created_at", 1)])
