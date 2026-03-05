from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service
from app.schemas.auth import (
    ForgotPasswordOptionsRequest,
    ForgotPasswordOptionsResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ResetPasswordRequest,
    SendVerificationCodeRequest,
    SendVerificationCodeResponse,
    SignUpRequest,
    ValidateEmailRequest,
    ValidateEmailResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/validate-email", response_model=ValidateEmailResponse)
async def validate_signup_email(
    payload: ValidateEmailRequest,
    service: AuthService = Depends(get_auth_service),
) -> ValidateEmailResponse:
    return await service.validate_signup_email(str(payload.email))


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    payload: SignUpRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        return await service.sign_up(payload)
    except ValueError as exc:
        detail = str(exc)
        error_status = (
            status.HTTP_409_CONFLICT
            if "already registered" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=error_status, detail=detail) from exc


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        return await service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/forgot-password/options", response_model=ForgotPasswordOptionsResponse)
async def forgot_password_options(
    payload: ForgotPasswordOptionsRequest,
    service: AuthService = Depends(get_auth_service),
) -> ForgotPasswordOptionsResponse:
    try:
        return await service.forgot_password_options(payload.identifier)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/forgot-password/send-code", response_model=SendVerificationCodeResponse)
async def send_forgot_password_code(
    payload: SendVerificationCodeRequest,
    service: AuthService = Depends(get_auth_service),
) -> SendVerificationCodeResponse:
    try:
        return await service.send_verification_code(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/forgot-password/verify-otp", response_model=VerifyOtpResponse)
async def verify_forgot_password_otp(
    payload: VerifyOtpRequest,
    service: AuthService = Depends(get_auth_service),
) -> VerifyOtpResponse:
    try:
        return await service.verify_otp(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/forgot-password/reset-password", response_model=MessageResponse)
async def reset_forgot_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await service.reset_password(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message="Password updated successfully.")
