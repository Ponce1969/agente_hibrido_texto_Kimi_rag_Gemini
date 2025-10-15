"""
Servicio de aplicación para autenticación.

Orquesta los puertos de seguridad siguiendo arquitectura hexagonal.
"""
from typing import Optional

from src.domain.ports.auth_port import (
    PasswordHasherPort,
    TokenServicePort,
    UserRepositoryPort,
)


class AuthService:
    """
    Servicio de aplicación para gestionar autenticación.
    
    Coordina los puertos de hashing, tokens y repositorio de usuarios
    para implementar los casos de uso de registro y login.
    """
    
    def __init__(
        self,
        password_hasher: PasswordHasherPort,
        token_service: TokenServicePort,
        user_repository: UserRepositoryPort,
    ) -> None:
        """
        Inicializa el servicio con sus dependencias.
        
        Args:
            password_hasher: Puerto para hashing de contraseñas
            token_service: Puerto para gestión de tokens
            user_repository: Puerto para persistencia de usuarios
        """
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.user_repository = user_repository
    
    def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> dict[str, any]:
        """
        Registra un nuevo usuario en el sistema.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            full_name: Nombre completo (opcional)
            
        Returns:
            Diccionario con usuario creado y token de acceso
            
        Raises:
            ValueError: Si el email ya existe o la contraseña es débil
        """
        # Validar que el email no exista
        if self.user_repository.exists_by_email(email):
            raise ValueError("El email ya está registrado")
        
        # Validar contraseña (mínimo 8 caracteres)
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        
        # Hashear contraseña
        hashed_password = self.password_hasher.hash_password(password)
        
        # Crear usuario
        user = self.user_repository.create(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        
        # Generar token
        token = self.token_service.create_access_token(
            user_id=str(user["id"]),
            email=user["email"]
        )
        
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "is_active": user["is_active"],
                "created_at": user["created_at"].isoformat() if user.get("created_at") else None
            },
            "access_token": token,
            "token_type": "bearer"
        }
    
    def login_user(self, email: str, password: str) -> dict[str, any]:
        """
        Autentica un usuario y genera un token de acceso.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Diccionario con usuario y token de acceso
            
        Raises:
            ValueError: Si las credenciales son inválidas
        """
        # Buscar usuario
        user = self.user_repository.get_by_email(email)
        if not user:
            raise ValueError("Credenciales inválidas")
        
        # Verificar contraseña
        if not self.password_hasher.verify_password(password, user["hashed_password"]):
            raise ValueError("Credenciales inválidas")
        
        # Verificar que el usuario esté activo
        if not user.get("is_active", True):
            raise ValueError("Usuario inactivo")
        
        # Verificar si necesita rehash (actualización de seguridad)
        if self.password_hasher.needs_rehash(user["hashed_password"]):
            new_hash = self.password_hasher.hash_password(password)
            user["hashed_password"] = new_hash
            self.user_repository.update(user)
        
        # Generar token
        token = self.token_service.create_access_token(
            user_id=str(user["id"]),
            email=user["email"]
        )
        
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "is_active": user["is_active"],
                "is_superuser": user.get("is_superuser", False)
            },
            "access_token": token,
            "token_type": "bearer"
        }
    
    def verify_token(self, token: str) -> Optional[dict[str, str]]:
        """
        Verifica un token de acceso.
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Datos del usuario si el token es válido, None en caso contrario
        """
        return self.token_service.verify_token(token)
    
    def get_user_by_id(self, user_id: int) -> Optional[dict[str, any]]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        user = self.user_repository.get_by_id(user_id)
        if user:
            # No devolver el hash de contraseña
            user.pop("hashed_password", None)
        return user
