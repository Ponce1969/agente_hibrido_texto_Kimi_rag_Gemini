"""
Puertos (interfaces) para el sistema de autenticación.

Define las interfaces que deben implementar los adaptadores de seguridad,
siguiendo los principios de arquitectura hexagonal.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models.user import User


class PasswordHasherPort(ABC):
    """
    Puerto para el servicio de hashing de contraseñas.

    Define la interfaz que debe implementar cualquier adaptador
    de hashing de contraseñas (Argon2, Bcrypt, etc.).
    """

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Genera un hash seguro de la contraseña."""
        pass

    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica si una contraseña coincide con su hash."""
        pass

    @abstractmethod
    def needs_rehash(self, hashed: str) -> bool:
        """Verifica si un hash necesita ser regenerado."""
        pass


class TokenServicePort(ABC):
    """
    Puerto para el servicio de gestión de tokens.

    Define la interfaz para crear y validar tokens de autenticación
    (JWT, OAuth, etc.).
    """

    @abstractmethod
    def create_access_token(self, user_id: str, email: str) -> str:
        """Crea un token de acceso para el usuario."""
        pass

    @abstractmethod
    def verify_token(self, token: str) -> dict[str, str] | None:
        """Verifica y decodifica un token."""
        pass


class UserRepositoryPort(ABC):
    """
    Puerto para el repositorio de usuarios.

    Define las operaciones de persistencia para usuarios.
    """

    @abstractmethod
    def create(
        self, email: str, hashed_password: str, full_name: str | None = None
    ) -> User:
        """Crea un nuevo usuario."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Obtiene un usuario por email."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None:
        """Obtiene un usuario por ID."""
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Verifica si existe un usuario con el email dado."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un usuario."""
        pass
