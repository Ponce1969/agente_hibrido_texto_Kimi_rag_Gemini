"""
Servicio de gestión de tokens JWT para autenticación.

Proporciona funcionalidades para crear y validar tokens de acceso seguros.
"""
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    """Datos contenidos en el token JWT."""
    user_id: str
    email: str
    exp: datetime


class JWTService:
    """
    Servicio para crear y validar tokens JWT.

    Utiliza el algoritmo HS256 para firmar tokens de forma segura.
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256", expire_minutes: int = 60) -> None:
        """
        Inicializa el servicio JWT.

        Args:
            secret_key: Clave secreta para firmar tokens (debe ser segura y única)
            algorithm: Algoritmo de firma (default: HS256)
            expire_minutes: Tiempo de expiración del token en minutos (default: 60)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def create_access_token(self, user_id: str, email: str, expires_delta: timedelta | None = None) -> str:
        """
        Crea un token de acceso JWT.

        Args:
            user_id: ID único del usuario
            email: Email del usuario
            expires_delta: Tiempo de expiración personalizado (opcional)

        Returns:
            Token JWT firmado como string

        Example:
            >>> service = JWTService(secret_key="mi_clave_secreta")
            >>> token = service.create_access_token(user_id="123", email="user@example.com")
        """
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.expire_minutes)

        to_encode: dict[str, Any] = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(UTC)
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenData | None:
        """
        Verifica y decodifica un token JWT.

        Args:
            token: Token JWT a verificar

        Returns:
            TokenData si el token es válido, None si es inválido o expirado

        Example:
            >>> service = JWTService(secret_key="mi_clave_secreta")
            >>> token = service.create_access_token("123", "user@example.com")
            >>> data = service.verify_token(token)
            >>> print(data.user_id)
            123
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            exp: float = payload.get("exp")

            if user_id is None or email is None or exp is None:
                return None

            return TokenData(
                user_id=user_id,
                email=email,
                exp=datetime.fromtimestamp(exp, tz=UTC)
            )
        except JWTError:
            return None

    def decode_token_unsafe(self, token: str) -> dict[str, Any] | None:
        """
        Decodifica un token sin verificar su firma (solo para debugging).

        ⚠️ ADVERTENCIA: No usar en producción para validación.

        Args:
            token: Token JWT a decodificar

        Returns:
            Payload del token o None si hay error
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except JWTError:
            return None
