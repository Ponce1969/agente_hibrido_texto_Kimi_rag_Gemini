"""
Puertos (interfaces) para el sistema de autenticación.

Define las interfaces que deben implementar los adaptadores de seguridad,
siguiendo los principios de arquitectura hexagonal.
"""
from abc import ABC, abstractmethod
from typing import Optional


class PasswordHasherPort(ABC):
    """
    Puerto para el servicio de hashing de contraseñas.
    
    Define la interfaz que debe implementar cualquier adaptador
    de hashing de contraseñas (Argon2, Bcrypt, etc.).
    """
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        Genera un hash seguro de la contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifica si una contraseña coincide con su hash.
        
        Args:
            password: Contraseña en texto plano
            hashed: Hash almacenado
            
        Returns:
            True si coincide, False en caso contrario
        """
        pass
    
    @abstractmethod
    def needs_rehash(self, hashed: str) -> bool:
        """
        Verifica si un hash necesita ser regenerado.
        
        Args:
            hashed: Hash a verificar
            
        Returns:
            True si necesita rehash, False en caso contrario
        """
        pass


class TokenServicePort(ABC):
    """
    Puerto para el servicio de gestión de tokens.
    
    Define la interfaz para crear y validar tokens de autenticación
    (JWT, OAuth, etc.).
    """
    
    @abstractmethod
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Crea un token de acceso para el usuario.
        
        Args:
            user_id: ID del usuario
            email: Email del usuario
            
        Returns:
            Token de acceso
        """
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[dict[str, str]]:
        """
        Verifica y decodifica un token.
        
        Args:
            token: Token a verificar
            
        Returns:
            Datos del token si es válido, None en caso contrario
        """
        pass


class UserRepositoryPort(ABC):
    """
    Puerto para el repositorio de usuarios.
    
    Define las operaciones de persistencia para usuarios.
    """
    
    @abstractmethod
    def create(self, email: str, hashed_password: str, full_name: Optional[str] = None) -> dict[str, any]:
        """
        Crea un nuevo usuario.
        
        Args:
            email: Email del usuario
            hashed_password: Contraseña hasheada
            full_name: Nombre completo (opcional)
            
        Returns:
            Usuario creado
        """
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[dict[str, any]]:
        """
        Obtiene un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[dict[str, any]]:
        """
        Obtiene un usuario por ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe, False en caso contrario
        """
        pass
    
    @abstractmethod
    def update(self, user: dict[str, any]) -> dict[str, any]:
        """
        Actualiza un usuario.
        
        Args:
            user: Usuario con datos actualizados
            
        Returns:
            Usuario actualizado
        """
        pass
