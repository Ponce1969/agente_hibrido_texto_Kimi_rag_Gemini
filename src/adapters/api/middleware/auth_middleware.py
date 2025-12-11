"""
Middleware de autenticación para proteger endpoints.

Verifica que las requests tengan un token JWT válido en el header Authorization.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.adapters.dependencies import get_auth_service
from src.application.services.auth_service import AuthService

# Esquema de seguridad HTTP Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Dependency para obtener el usuario actual desde el token JWT.

    Args:
        credentials: Credenciales del header Authorization
        auth_service: Servicio de autenticación

    Returns:
        Diccionario con datos del usuario

    Raises:
        HTTPException: Si el token es inválido o expiró
    """
    token = credentials.credentials

    # Verificar token
    token_data = auth_service.verify_token(token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener usuario de la base de datos
    user = auth_service.get_user_by_id(int(token_data["user_id"]))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency para obtener el usuario actual activo.

    Alias de get_current_user para mayor claridad.
    """
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict | None:
    """
    Dependency para obtener el usuario actual de forma opcional.

    Si no hay token, devuelve None en lugar de lanzar error.
    Útil para endpoints que funcionan con o sin autenticación.
    """
    if not credentials:
        return None

    token = credentials.credentials
    token_data = auth_service.verify_token(token)

    if not token_data:
        return None

    user = auth_service.get_user_by_id(int(token_data["user_id"]))
    return user if user and user.get("is_active", True) else None
