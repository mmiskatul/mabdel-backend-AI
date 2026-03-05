import pytest

from app.application.services.auth_service import AuthService
from app.domain.models import LoginRequest, SignupRequest


@pytest.mark.asyncio
async def test_auth_signup_login_flow(fake_repo, fake_sessions, fake_email):
    service = AuthService(fake_repo, fake_sessions, fake_email)

    send_code = await service.send_signup_code("user@example.com")
    assert send_code["is_available"] is True
    code = send_code["dev_verification_code"]

    verify = await service.verify_signup_code("user@example.com", code)
    assert "signup_validation_token" in verify

    token_pair = await service.signup(
        SignupRequest(
            email="user@example.com",
            name="Test User",
            password="StrongPass123!",
            language="en",
            timezone="UTC",
        ),
        signup_validation_token=verify["signup_validation_token"],
    )
    assert token_pair.access_token
    assert token_pair.refresh_token

    login = await service.login(LoginRequest(email="user@example.com", password="StrongPass123!"))
    assert login.access_token

