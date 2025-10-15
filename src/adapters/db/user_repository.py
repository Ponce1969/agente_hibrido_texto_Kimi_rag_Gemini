"""
Repositorio para gestionar usuarios en la base de datos.

Implementa el puerto UserRepositoryPort usando SQLModel.
"""
from typing import Optional, Any

from sqlmodel import Session, select

from src.domain.models.user import User
from src.domain.ports.auth_port import UserRepositoryPort


class SQLModelUserRepository(UserRepositoryPort):
    """
    Repositorio para operaciones de base de datos con usuarios.
    
    Proporciona métodos para crear, leer, actualizar y eliminar usuarios.
    """
    
    def __init__(self, session: Session) -> None:
        """
        Inicializa el repositorio con una sesión de base de datos.
        
        Args:
            session: Sesión de SQLModel para operaciones de BD
        """
        self.session = session
    
    def create(self, email: str, hashed_password: str, full_name: Optional[str] = None) -> dict[str, Any]:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            email: Email único del usuario
            hashed_password: Contraseña ya hasheada
            full_name: Nombre completo (opcional)
            
        Returns:
            Usuario creado con ID asignado
            
        Raises:
            IntegrityError: Si el email ya existe
        """
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user.model_dump()
    
    def get_by_id(self, user_id: int) -> Optional[dict[str, Any]]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        user = self.session.get(User, user_id)
        return user.model_dump() if user else None
    
    def get_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        statement = select(User).where(User.email == email)
        user = self.session.exec(statement).first()
        return user.model_dump() if user else None
    
    def update(self, user: dict[str, Any]) -> dict[str, Any]:
        """
        Actualiza un usuario existente.
        
        Args:
            user: Usuario con datos actualizados
            
        Returns:
            Usuario actualizado
        """
        from datetime import datetime
        user_obj = self.session.get(User, user["id"])
        if not user_obj:
            raise ValueError(f"User with id {user['id']} not found")
        
        for key, value in user.items():
            if hasattr(user_obj, key) and key != "id":
                setattr(user_obj, key, value)
        
        user_obj.updated_at = datetime.utcnow()
        self.session.add(user_obj)
        self.session.commit()
        self.session.refresh(user_obj)
        return user_obj.model_dump()
    
    def delete(self, user_id: int) -> bool:
        """
        Elimina un usuario por su ID.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        user = self.get_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
    
    def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Lista todos los usuarios con paginación.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a devolver
            
        Returns:
            Lista de usuarios
        """
        statement = select(User).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
    
    def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe, False en caso contrario
        """
        return self.get_by_email(email) is not None
