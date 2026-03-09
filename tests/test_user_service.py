import pytest

from app.application.services.auth_service import AuthService
from app.domain.models import SignupRequest
from app.shared.errors import AppError
from app.users.service import UserService


@pytest.mark.asyncio
async def test_user_service_lists_registered_month_and_status(fake_repo, fake_sessions, fake_email):
    auth = AuthService(fake_repo, fake_sessions, fake_email)
    users = UserService(fake_repo)

    await auth.start_registration(
        SignupRequest(
            email="user1@example.com",
            name="User One",
            password="StrongPass123!",
            language="en",
            timezone="UTC",
        ),
        role="customer",
    )
    code = fake_email.sent[-1][1]
    created = await auth.complete_registration("user1@example.com", code)

    await auth.start_registration(
        SignupRequest(
            email="admin1@example.com",
            name="Admin One",
            password="StrongPass123!",
            language="en",
            timezone="UTC",
        ),
        role="admin",
    )
    admin_code = fake_email.sent[-1][1]
    await auth.complete_registration("admin1@example.com", admin_code)

    records = await users.list_users()

    assert len(records) == 1
    assert records[0].id == created["user_id"]
    assert records[0].status == "unblocked"
    assert records[0].registered_month


@pytest.mark.asyncio
async def test_user_service_can_block_and_unblock_user(fake_repo, fake_sessions, fake_email):
    auth = AuthService(fake_repo, fake_sessions, fake_email)
    users = UserService(fake_repo)

    await auth.start_registration(
        SignupRequest(
            email="user2@example.com",
            name="User Two",
            password="StrongPass123!",
            language="en",
            timezone="UTC",
        ),
        role="customer",
    )
    code = fake_email.sent[-1][1]
    created = await auth.complete_registration("user2@example.com", code)

    blocked = await users.update_status(created["user_id"], "blocked")
    unblocked = await users.update_status(created["user_id"], "unblocked")

    assert blocked.status == "blocked"
    assert unblocked.status == "unblocked"


@pytest.mark.asyncio
async def test_user_service_cannot_block_admin(fake_repo, fake_sessions, fake_email):
    auth = AuthService(fake_repo, fake_sessions, fake_email)
    users = UserService(fake_repo)

    await auth.start_registration(
        SignupRequest(
            email="admin2@example.com",
            name="Admin Two",
            password="StrongPass123!",
            language="en",
            timezone="UTC",
        ),
        role="admin",
    )
    code = fake_email.sent[-1][1]
    created = await auth.complete_registration("admin2@example.com", code)

    with pytest.raises(AppError):
        await users.update_status(created["user_id"], "blocked")
