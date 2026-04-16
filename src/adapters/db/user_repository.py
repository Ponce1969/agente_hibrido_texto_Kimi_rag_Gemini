"""
Repositorio para gestionar usuarios en la base de datos.

Implementa el puerto UserRepositoryPort usando SQLModel.
"""

from datetime import UTC, datetime

from sqlmodel import Session, select

from src.domain.models.user import User
from src.domain.ports.auth_port import UserRepositoryPort


class SQLModelUserRepository(UserRepositoryPort):
    """Repositorio para operaciones de base de datos con usuarios."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self, email: str, hashed_password: str, full_name: str | None = None
    ) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def update(self, user: User) -> User:
        user.updated_at = datetime.now(UTC)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def exists_by_email(self, email: str) -> bool:
        return self.get_by_email(email) is not None
