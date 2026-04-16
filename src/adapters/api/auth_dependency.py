"""
Dependencia de autenticación JWT para proteger endpoints.

Proporciona `get_current_user` y `get_current_user_optional` como
dependencias de FastAPI para verificar tokens JWT en el header Authorization.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.adapters.config.settings import settings
from src.adapters.security.jwt_token_service import JWTTokenService

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=True)
bearer_scheme_optional = HTTPBearer(auto_error=False)


def _get_token_service() -> JWTTokenService:
    return JWTTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm="HS256",
        expire_minutes=settings.jwt_expire_minutes,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict[str, str]:
    """
    Dependencia que requiere un JWT válido.

    Uso en endpoints:
        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}

    Retorna dict con user_id y email si el token es válido.
    Lanza 401 si el token es inválido o falta.
    """
    token_service = _get_token_service()
    payload = token_service.verify_token(credentials.credentials)

    if payload is None:
        logger.warning("Token JWT inválido o expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme_optional)
    ],
) -> dict[str, str] | None:
    """
    Dependencia que acepta un JWT opcional.

    Si el token está presente y es válido, retorna el payload.
    Si no hay token, retorna None (no lanza error).

    Uso en endpoints que funcionan con o sin auth:
        @router.get("/public-optional")
        async def endpoint(user: dict | None = Depends(get_current_user_optional)):
            ...
    """
    if credentials is None:
        return None

    token_service = _get_token_service()
    return token_service.verify_token(credentials.credentials)
