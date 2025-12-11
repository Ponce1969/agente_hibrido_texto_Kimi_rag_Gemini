"""
Endpoints de autenticación (registro y login).

Implementa los endpoints para gestionar usuarios siguiendo arquitectura hexagonal.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.adapters.dependencies import get_auth_service
from src.application.services.auth_service import AuthService
from src.domain.models.user import TokenResponse, UserCreate, UserLogin, UserResponse

logger = logging.getLogger(__name__)

# Configurar limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # Límite: 5 registros por hora por IP
async def register(
    request: Request,
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Registra un nuevo usuario en el sistema.

    - **email**: Email único del usuario
    - **password**: Contraseña (mínimo 8 caracteres)
    - **full_name**: Nombre completo (opcional)

    Returns:
        Token de acceso y datos del usuario creado
    """
    try:
        result = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )

        return TokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user=UserResponse(**result["user"])
        )
    except ValueError as e:
        logger.warning(f"Error de validación en registro: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error al registrar usuario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar usuario"
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # Límite: 10 intentos de login por minuto
async def login(
    request: Request,
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Autentica un usuario y genera un token de acceso.

    - **email**: Email del usuario
    - **password**: Contraseña

    Returns:
        Token de acceso y datos del usuario
    """
    try:
        result = auth_service.login_user(
            email=credentials.email,
            password=credentials.password
        )

        return TokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user=UserResponse(**result["user"])
        )
    except ValueError as e:
        logger.warning(f"Intento de login fallido para {credentials.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error al autenticar usuario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al autenticar"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    auth_service: AuthService = Depends(get_auth_service),
    # TODO: Agregar dependency para extraer token del header Authorization
):
    """
    Obtiene los datos del usuario autenticado actual.

    Requiere token de autenticación en el header Authorization.
    """
    # TODO: Implementar extracción y validación del token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint en desarrollo"
    )
