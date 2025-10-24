"""
Modelo de dominio para usuarios del sistema.

Define la entidad User con sus atributos y validaciones.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    Entidad de usuario para autenticación y autorización.
    
    Attributes:
        id: Identificador único del usuario
        email: Email único del usuario (usado para login)
        hashed_password: Contraseña hasheada con Argon2
        full_name: Nombre completo del usuario (opcional)
        is_active: Si el usuario está activo
        is_superuser: Si el usuario tiene privilegios de administrador
        created_at: Fecha de creación del usuario
        updated_at: Fecha de última actualización
    """
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Configuración del modelo."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False
            }
        }


class UserCreate(SQLModel):
    """Schema para crear un nuevo usuario."""
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)


class UserLogin(SQLModel):
    """Schema para login de usuario."""
    email: str = Field(max_length=255)
    password: str = Field(max_length=100)


class UserResponse(SQLModel):
    """Schema para respuestas de usuario (sin contraseña)."""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        """Configuración del schema."""
        from_attributes = True


class TokenResponse(SQLModel):
    """Schema para respuesta de autenticación."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
