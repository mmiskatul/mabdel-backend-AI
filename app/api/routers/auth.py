from fastapi import APIRouter, Depends

from app.api.schemas import (
    ForgotPasswordRequestSchema,
    ForgotPasswordVerifyRequestSchema,
    RegisterRequestSchema,
    RegisterVerifyRequestSchema,
    LoginRequestSchema,
    RefreshRequestSchema,
    ResetPasswordRequestSchema,
)
from app.api.service_factory import get_auth_service
from app.application.services.auth_service import AuthService
from app.domain.models import LoginRequest, SignupRequest

customer_router = APIRouter(prefix="/auth/customer", tags=["customer auth"])
admin_router = APIRouter(prefix="/auth/admin", tags=["admin auth"])


@customer_router.post("/register")
async def customer_register(payload: RegisterRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.start_registration(
        SignupRequest(
            email=payload.email,
            name=payload.name,
            password=payload.password,
            language=payload.language,
            timezone=payload.timezone,
        ),
        role="customer",
    )


@customer_router.post("/register/verify")
async def customer_register_verify(
    payload: RegisterVerifyRequestSchema,
    service: AuthService = Depends(get_auth_service),
):
    return await service.complete_registration(str(payload.email), payload.code)


@customer_router.post("/login")
async def customer_login(payload: LoginRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.customer_login(LoginRequest(email=payload.email, password=payload.password))


@customer_router.post("/refresh")
async def customer_refresh(payload: RefreshRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.refresh(payload.refresh_token)


@admin_router.post("/login")
async def admin_login(payload: LoginRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.admin_login(LoginRequest(email=payload.email, password=payload.password))


@admin_router.post("/refresh")
async def admin_refresh(payload: RefreshRequestSchema, service: AuthService = Depends(get_auth_service)):
    return await service.refresh(payload.refresh_token)


@admin_router.post("/forgot-password")
async def admin_forgot_password(
    payload: ForgotPasswordRequestSchema,
    service: AuthService = Depends(get_auth_service),
):
    return await service.start_password_reset(str(payload.email))


@admin_router.post("/forgot-password/verify")
async def admin_forgot_password_verify(
    payload: ForgotPasswordVerifyRequestSchema,
    service: AuthService = Depends(get_auth_service),
):
    return await service.verify_password_reset_code(str(payload.email), payload.code)


@admin_router.post("/reset-password")
async def admin_reset_password(
    payload: ResetPasswordRequestSchema,
    service: AuthService = Depends(get_auth_service),
):
    return await service.reset_password(
        email=str(payload.email),
        reset_token=payload.reset_token,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
        current_password=payload.current_password,
    )
