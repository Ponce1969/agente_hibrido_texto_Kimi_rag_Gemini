"""
Implementación del puerto TokenServicePort usando JWT.

Adaptador que gestiona tokens de autenticación con JSON Web Tokens.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from src.domain.ports.auth_port import TokenServicePort


class JWTTokenService(TokenServicePort):
    """
    Implementación de TokenServicePort usando JWT (JSON Web Tokens).
    
    Utiliza el algoritmo HS256 para firmar tokens de forma segura.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expire_minutes: int = 60
    ) -> None:
        """
        Inicializa el servicio JWT.
        
        Args:
            secret_key: Clave secreta para firmar tokens
            algorithm: Algoritmo de firma (default: HS256)
            expire_minutes: Tiempo de expiración en minutos (default: 60)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Crea un token de acceso JWT.
        
        Args:
            user_id: ID único del usuario
            email: Email del usuario
            
        Returns:
            Token JWT firmado
        """
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict[str, str]]:
        """
        Verifica y decodifica un token JWT.
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Diccionario con user_id y email si es válido, None en caso contrario
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            
            if user_id is None or email is None:
                return None
            
            return {
                "user_id": user_id,
                "email": email
            }
        except JWTError:
            return None
