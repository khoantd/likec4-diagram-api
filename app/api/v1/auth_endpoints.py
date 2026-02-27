from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import Token, create_access_token
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Issue a short-lived JWT access token using simple username/password credentials.

    This endpoint is enabled only when LIKEC4_API_AUTH_ENABLED=true. The credentials
    are configured via LIKEC4_API_AUTH_USERNAME / LIKEC4_API_AUTH_PASSWORD.
    """
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled",
        )

    if not settings.auth_username or not settings.auth_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication credentials are not configured",
        )

    if form_data.username != settings.auth_username or form_data.password != settings.auth_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(subject=form_data.username, expires_delta=access_token_expires)
    return Token(access_token=access_token)

