"""
Implementaciones de repositorio que usan SQLModel/SQLAlchemy para persistencia.

Estos adaptadores implementan las interfaces del domain layer usando
tecnología específica de persistencia.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import ChatSession as DBSession, ChatMessage as DBMessage
from ..db.models import FileUpload as DBFile, FileSection as DBFileSection
from ..config.settings import settings
from src.domain import (
    ChatSession,
    ChatMessage,
    FileDocument,
    FileSection,
    MessageRole
)
from src.domain.ports.repository_port import ChatRepositoryPort
from src.domain.ports.file_repository_port import FileRepositoryPort

# Aliases temporales para compatibilidad
ChatRepositoryInterface = ChatRepositoryPort
FileRepositoryInterface = FileRepositoryPort
AgentRepositoryInterface = Any  # TODO: Crear puerto si es necesario
AnalyticsRepositoryInterface = Any  # TODO: Crear puerto si es necesario


class SQLChatRepository(ChatRepositoryInterface):
    """Implementación de repositorio de chat usando SQLModel."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_session(self, session_id: int) -> Optional[ChatSession]:
        """Obtiene una sesión por ID."""
        result = await self.session.execute(
            select(DBSession).where(DBSession.id == session_id)
        )
        db_session = result.scalar_one_or_none()

        if not db_session:
            return None

        return self._db_to_domain_session(db_session)

    async def get_session_by_user(self, user_id: str, session_id: int) -> Optional[ChatSession]:
        """Obtiene una sesión específica de un usuario."""
        result = await self.session.execute(
            select(DBSession).where(
                and_(DBSession.user_id == user_id, DBSession.id == session_id)
            )
        )
        db_session = result.scalar_one_or_none()

        if not db_session:
            return None

        return self._db_to_domain_session(db_session)

    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[ChatSession]:
        """Obtiene todas las sesiones de un usuario."""
        query = select(DBSession).where(DBSession.user_id == user_id)
        if active_only:
            query = query.where(DBSession.is_active == True)

        query = query.order_by(desc(DBSession.updated_at))

        result = await self.session.execute(query)
        db_sessions = result.scalars().all()

        return [self._db_to_domain_session(db) for db in db_sessions]

    async def create_session(self, user_id: str, session_name: Optional[str] = None) -> ChatSession:
        """Crea una nueva sesión de chat."""
        db_session = DBSession(
            user_id=user_id,
            session_name=session_name or f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
        )

        self.session.add(db_session)
        await self.session.commit()
        await self.session.refresh(db_session)

        return self._db_to_domain_session(db_session)

    async def update_session(self, session: ChatSession) -> ChatSession:
        """Actualiza una sesión existente."""
        result = await self.session.execute(
            select(DBSession).where(DBSession.id == session.id)
        )
        db_session = result.scalar_one_or_none()

        if not db_session:
            raise ValueError(f"Sesión {session.id} no encontrada")

        # Actualizar campos
        db_session.session_name = session.session_name
        db_session.updated_at = datetime.now(UTC)
        db_session.is_active = session.is_active
        db_session.extra_data = str(session.metadata) if session.metadata else None

        await self.session.commit()
        await self.session.refresh(db_session)

        return self._db_to_domain_session(db_session)

    async def delete_session(self, session_id: int) -> bool:
        """Elimina una sesión y todos sus mensajes."""
        result = await self.session.execute(
            select(DBSession).where(DBSession.id == session_id)
        )
        db_session = result.scalar_one_or_none()

        if not db_session:
            return False

        await self.session.delete(db_session)
        await self.session.commit()
        return True

    async def save_message(self, message: ChatMessage) -> ChatMessage:
        """Guarda un mensaje en la sesión."""
        db_message = DBMessage(
            session_id=message.session_id,
            role=message.role.value,
            content=message.content,
            message_index=message.message_index,
            extra_data=str(message.metadata) if message.metadata else None,
            token_count=message.token_count
        )

        self.session.add(db_message)
        await self.session.commit()
        await self.session.refresh(db_message)

        # Actualizar el mensaje con el ID de la base de datos
        message.metadata['db_id'] = db_message.id
        return message

    async def get_session_messages(
        self,
        session_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ChatMessage]:
        """Obtiene los mensajes de una sesión."""
        query = select(DBMessage).where(DBMessage.session_id == session_id)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        query = query.order_by(DBMessage.message_index)

        result = await self.session.execute(query)
        db_messages = result.scalars().all()

        return [self._db_to_domain_message(db) for db in db_messages]

    async def get_message(self, message_id: int) -> Optional[ChatMessage]:
        """Obtiene un mensaje específico."""
        result = await self.session.execute(
            select(DBMessage).where(DBMessage.id == message_id)
        )
        db_message = result.scalar_one_or_none()

        if not db_message:
            return None

        return self._db_to_domain_message(db_message)

    async def delete_message(self, message_id: int) -> bool:
        """Elimina un mensaje."""
        result = await self.session.execute(
            select(DBMessage).where(DBMessage.id == message_id)
        )
        db_message = result.scalar_one_or_none()

        if not db_message:
            return False

        await self.session.delete(db_message)
        await self.session.commit()
        return True

    async def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Obtiene las sesiones más recientes."""
        result = await self.session.execute(
            select(DBSession)
            .order_by(desc(DBSession.updated_at))
            .limit(limit)
        )
        db_sessions = result.scalars().all()

        return [self._db_to_domain_session(db) for db in db_sessions]

    async def get_session_count(self, user_id: str) -> int:
        """Obtiene el número de sesiones de un usuario."""
        result = await self.session.execute(
            select(func.count(DBSession.id)).where(DBSession.user_id == user_id)
        )
        return result.scalar_one()

    def _db_to_domain_session(self, db_session: DBSession) -> ChatSession:
        """Convierte un modelo de DB a modelo de dominio."""
        return ChatSession(
            user_id=db_session.user_id,
            session_name=db_session.session_name,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            is_active=db_session.is_active,
            metadata=eval(db_session.extra_data) if db_session.extra_data else {}
        )

    def _db_to_domain_message(self, db_message: DBMessage) -> ChatMessage:
        """Convierte un modelo de DB a modelo de dominio."""
        return ChatMessage(
            session_id=db_message.session_id,
            role=MessageRole(db_message.role),
            content=db_message.content,
            timestamp=db_message.timestamp,
            message_index=db_message.message_index,
            metadata=eval(db_message.extra_data) if db_message.extra_data else {},
            token_count=db_message.token_count
        )


class SQLFileRepository(FileRepositoryInterface):
    """Implementación de repositorio de archivos usando SQLModel."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_file(self, file_id: int) -> Optional[FileDocument]:
        """Obtiene un archivo por ID."""
        result = await self.session.execute(
            select(DBFile).where(DBFile.id == file_id)
        )
        db_file = result.scalar_one_or_none()

        if not db_file:
            return None

        return self._db_to_domain_file(db_file)

    async def get_user_files(self, user_id: str) -> List[FileDocument]:
        """Obtiene todos los archivos de un usuario."""
        # TODO: Implementar relación user-files
        result = await self.session.execute(select(DBFile))
        db_files = result.scalars().all()

        return [self._db_to_domain_file(db) for db in db_files]

    async def create_file(
        self,
        filename_original: str,
        filename_saved: str,
        file_path: str,
        file_size: int,
        content_type: str
    ) -> FileDocument:
        """Crea un nuevo registro de archivo."""
        db_file = DBFile(
            uuid_str=str(uuid.uuid4()),
            filename_original=filename_original,
            filename_saved=filename_saved,
            path=file_path,
            size_bytes=file_size,
            total_pages=0,
            pages_processed=0,
            status="pending"
        )

        self.session.add(db_file)
        await self.session.commit()
        await self.session.refresh(db_file)

        return self._db_to_domain_file(db_file)

    async def update_file(self, file: FileDocument) -> FileDocument:
        """Actualiza un archivo existente."""
        result = await self.session.execute(
            select(DBFile).where(DBFile.id == file.id)
        )
        db_file = result.scalar_one_or_none()

        if not db_file:
            raise ValueError(f"Archivo {file.id} no encontrado")

        # Actualizar campos
        db_file.total_pages = file.total_pages
        db_file.pages_processed = file.pages_processed
        db_file.status = file.status
        db_file.error_message = file.error_message
        db_file.updated_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(db_file)

        return self._db_to_domain_file(db_file)

    async def delete_file(self, file_id: int) -> bool:
        """Elimina un archivo y sus secciones."""
        result = await self.session.execute(
            select(DBFile).where(DBFile.id == file_id)
        )
        db_file = result.scalar_one_or_none()

        if not db_file:
            return False

        await self.session.delete(db_file)
        await self.session.commit()
        return True

    async def save_section(self, section: FileSection) -> FileSection:
        """Guarda una sección de archivo."""
        db_section = DBFileSection(
            file_id=section.file_id,
            title=section.title,
            start_page=section.start_page,
            end_page=section.end_page,
            char_count=section.char_count
        )

        self.session.add(db_section)
        await self.session.commit()
        await self.session.refresh(db_section)

        # Actualizar la sección con el ID
        section.id = db_section.id
        return section

    async def get_file_sections(self, file_id: int) -> List[FileSection]:
        """Obtiene todas las secciones de un archivo."""
        result = await self.session.execute(
            select(DBFileSection).where(DBFileSection.file_id == file_id)
        )
        db_sections = result.scalars().all()

        return [self._db_to_domain_section(db) for db in db_sections]

    async def get_section(self, section_id: int) -> Optional[FileSection]:
        """Obtiene una sección específica."""
        result = await self.session.execute(
            select(DBFileSection).where(DBFileSection.id == section_id)
        )
        db_section = result.scalar_one_or_none()

        if not db_section:
            return None

        return self._db_to_domain_section(db_section)

    async def delete_section(self, section_id: int) -> bool:
        """Elimina una sección de archivo."""
        result = await self.session.execute(
            select(DBFileSection).where(DBFileSection.id == section_id)
        )
        db_section = result.scalar_one_or_none()

        if not db_section:
            return False

        await self.session.delete(db_section)
        await self.session.commit()
        return True

    async def get_sections_by_page_range(
        self,
        file_id: int,
        start_page: int,
        end_page: int
    ) -> List[FileSection]:
        """Obtiene secciones en un rango de páginas."""
        result = await self.session.execute(
            select(DBFileSection).where(
                and_(
                    DBFileSection.file_id == file_id,
                    DBFileSection.start_page >= start_page,
                    DBFileSection.end_page <= end_page
                )
            )
        )
        db_sections = result.scalars().all()

        return [self._db_to_domain_section(db) for db in db_sections]

    async def search_sections_by_content(
        self,
        file_id: int,
        query: str,
        limit: int = 10
    ) -> List[FileSection]:
        """Busca secciones que contengan texto específico."""
        # TODO: Implementar búsqueda full-text
        result = await self.session.execute(
            select(DBFileSection).where(DBFileSection.file_id == file_id).limit(limit)
        )
        db_sections = result.scalars().all()

        return [self._db_to_domain_section(db) for db in db_sections]

    async def get_files_by_status(self, status: str) -> List[FileDocument]:
        """Obtiene archivos por estado de procesamiento."""
        result = await self.session.execute(
            select(DBFile).where(DBFile.status == status)
        )
        db_files = result.scalars().all()

        return [self._db_to_domain_file(db) for db in db_files]

    async def get_processing_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de procesamiento de archivos."""
        result = await self.session.execute(
            select(
                DBFile.status,
                func.count(DBFile.id)
            ).group_by(DBFile.status)
        )
        stats = result.all()

        return {status: count for status, count in stats}

    def _db_to_domain_file(self, db_file: DBFile) -> FileDocument:
        """Convierte un modelo de DB a modelo de dominio."""
        return FileDocument(
            filename_original=db_file.filename_original,
            filename_saved=db_file.filename_saved,
            file_path=db_file.path,
            file_size=db_file.size_bytes,
            content_type="application/pdf",  # TODO: Detectar tipo real
            status=db_file.status,
            error_message=db_file.error_message,
            total_pages=db_file.total_pages,
            pages_processed=db_file.pages_processed
        )

    def _db_to_domain_section(self, db_section: DBFileSection) -> FileSection:
        """Convierte un modelo de DB a modelo de dominio."""
        return FileSection(
            file_id=db_section.file_id,
            title=db_section.title,
            start_page=db_section.start_page,
            end_page=db_section.end_page,
            char_count=db_section.char_count
        )


# Implementaciones básicas para las otras interfaces
class InMemoryAgentRepository(AgentRepositoryInterface):
    """Implementación en memoria para configuración de agentes."""

    def __init__(self) -> None:
        self._configs = {
            "Arquitecto Python Senior": {"system_prompt": "Eres un arquitecto..."},
            "Ingeniero de Código": {"system_prompt": "Eres un ingeniero..."},
            # ... otros agentes
        }

    async def get_agent_config(self, agent_mode: str) -> Dict[str, Any]:
        return self._configs.get(agent_mode, {})

    async def save_agent_config(self, agent_mode: str, config: Dict[str, Any]) -> Dict[str, Any]:
        self._configs[agent_mode] = config
        return config

    async def get_available_agents(self) -> List[str]:
        return list(self._configs.keys())

    async def get_agent_usage_stats(self) -> Dict[str, int]:
        return {agent: 0 for agent in self._configs.keys()}

    async def log_agent_interaction(
        self,
        agent_mode: str,
        session_id: int,
        token_count: int,
        response_time: float
    ) -> None:
        pass


class InMemoryAnalyticsRepository(AnalyticsRepositoryInterface):
    """Implementación en memoria para analíticas."""

    async def log_chat_interaction(
        self,
        session_id: int,
        message_count: int,
        agent_mode: str,
        has_file_context: bool,
        response_time: float,
        token_count: int
    ) -> None:
        pass

    async def get_daily_stats(self, date: datetime) -> Dict[str, Any]:
        return {"total_interactions": 0, "avg_response_time": 0}

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        return {"total_sessions": 0, "total_messages": 0}

    async def get_popular_agents(self, limit: int = 5) -> List[Dict[str, Any]]:
        return []

    async def get_file_processing_stats(self) -> Dict[str, Any]:
        return {"total_files": 0, "processed_files": 0}
