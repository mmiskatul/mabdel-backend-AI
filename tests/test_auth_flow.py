import pytest

from app.application.services.auth_service import AuthService, ensure_seed_admin
from app.domain.models import LoginRequest, SignupRequest
from app.shared.config import get_settings
from app.shared.errors import UnauthorizedError
from app.shared.security import hash_password


@pytest.mark.asyncio
async def test_customer_register_verify_login_flow(fake_repo, fake_sessions, fake_email):
    service = AuthService(fake_repo, fake_sessions, fake_email)

    send_code = await service.start_registration(
        SignupRequest(
            email="user@example.com",
            name="Test User",
            password="StrongPass123!",
            language="en",
            timezone="UTC",
        ),
        role="customer",
    )
    assert send_code["is_available"] is True
    code = send_code["dev_verification_code"]

    verify = await service.complete_registration("user@example.com", code)
    assert verify["message"] == "Registration successful."
    saved_user = await fake_repo.find_one("users", {"email": "user@example.com"})
    assert saved_user["status"] == "unblocked"
    assert saved_user["registered_month"]

    login = await service.customer_login(LoginRequest(email="user@example.com", password="StrongPass123!"))
    assert login.access_token


@pytest.mark.asyncio
async def test_admin_forgot_password_verify_and_reset(fake_repo, fake_sessions, fake_email):
    service = AuthService(fake_repo, fake_sessions, fake_email)
    await fake_repo.insert_one(
        "users",
        {
            "email": "admin@example.com",
            "name": "Admin User",
            "password_hash": hash_password("StrongPass123!"),
            "role": "admin",
            "status": "unblocked",
            "registered_month": "2026-03",
        },
    )

    forgot = await service.start_password_reset("admin@example.com")
    assert forgot["message"] == "Verification code sent."
    reset_code = forgot["dev_verification_code"]

    verified = await service.verify_password_reset_code("admin@example.com", reset_code)
    assert verified["message"] == "Verification successful."
    assert verified["reset_token"]

    reset = await service.reset_password(
        email="admin@example.com",
        reset_token=verified["reset_token"],
        new_password="NewStrongPass123!",
        confirm_password="NewStrongPass123!",
    )
    assert reset["message"] == "Password reset successful."

    login = await service.admin_login(LoginRequest(email="admin@example.com", password="NewStrongPass123!"))
    assert login.access_token


@pytest.mark.asyncio
async def test_blocked_flag_does_not_stop_admin_login(fake_repo, fake_sessions, fake_email):
    service = AuthService(fake_repo, fake_sessions, fake_email)

    created_id = await fake_repo.insert_one(
        "users",
        {
            "email": "admin-block@example.com",
            "name": "Admin Block",
            "password_hash": hash_password("StrongPass123!"),
            "role": "admin",
            "status": "unblocked",
            "registered_month": "2026-03",
        },
    )

    await fake_repo.update_one(
        "users",
        {"_id": fake_repo.object_id(created_id)},
        {"$set": {"status": "blocked"}},
    )

    login = await service.admin_login(LoginRequest(email="admin-block@example.com", password="StrongPass123!"))
    assert login.access_token


@pytest.mark.asyncio
async def test_blocked_customer_cannot_login(fake_repo, fake_sessions, fake_email):
    service = AuthService(fake_repo, fake_sessions, fake_email)

    await service.start_registration(
        SignupRequest(
            email="blocked@example.com",
            name="Blocked User",
            password="StrongPass123!",
            language="en",
            timezone="UTC",
        ),
        role="customer",
    )
    code = fake_email.sent[-1][1]
    verify = await service.complete_registration("blocked@example.com", code)

    await fake_repo.update_one(
        "users",
        {"_id": fake_repo.object_id(verify["user_id"])},
        {"$set": {"status": "blocked"}},
    )

    with pytest.raises(UnauthorizedError):
        await service.customer_login(LoginRequest(email="blocked@example.com", password="StrongPass123!"))


@pytest.mark.asyncio
async def test_seed_admin_from_env(fake_repo, monkeypatch):
    monkeypatch.setenv("ADMIN_NAME", "Env Admin")
    monkeypatch.setenv("ADMIN_EMAIL", "env-admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "EnvAdmin123!")
    get_settings.cache_clear()

    await ensure_seed_admin(fake_repo)

    admin = await fake_repo.find_one("users", {"email": "env-admin@example.com"})
    assert admin is not None
    assert admin["name"] == "Env Admin"
    assert admin["role"] == "admin"
    assert admin["status"] == "unblocked"
    assert admin["registered_month"]

    get_settings.cache_clear()
