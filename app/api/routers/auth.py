from fastapi import APIRouter, Depends

from app.api.schemas import (
    LoginRequestSchema,
    RefreshRequestSchema,
    SignupRequestSchema,
    SignupSendCodeRequest,
    SignupVerifyCodeRequest,
)
from app.api.service_factory import get_auth_service
from app.application.services.auth_service import AuthService
from app.domain.models import LoginRequest, SignupRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup/send-code")
async def signup_send_code(payload: SignupSendCodeRequest, service: AuthService = Depends(get_auth_service)):
    return await service.send_signup_code(str(payload.email))


@router.post("/signup/verify-code")
async def signup_verify_code(payload: SignupVerifyCodeRequest, service: AuthService = Depends(get_auth_service)):
    return await service.verify_signup_code(str(payload.email), payload.code)


@router.post("/signup")
async def signup(payload: SignupRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.signup(
        SignupRequest(
            email=payload.email,
            name=payload.name,
            password=payload.password,
            language=payload.language,
            timezone=payload.timezone,
        ),
        signup_validation_token=payload.signup_validation_token,
    )


@router.post("/login")
async def login(payload: LoginRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.login(LoginRequest(email=payload.email, password=payload.password))


@router.post("/refresh")
async def refresh(payload: RefreshRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.refresh(payload.refresh_token)

