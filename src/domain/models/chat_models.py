"""
Modelos de dominio puros para el asistente de aprendizaje de Python.

Estos modelos representan entidades de negocio independientes de cualquier
tecnología de persistencia o presentación.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """Roles posibles para los mensajes en el dominio."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Representa un mensaje en una conversación."""
    session_id: int
    role: MessageRole
    content: str
    timestamp: datetime
    message_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: Optional[int] = None

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.content.strip():
            raise ValueError("El contenido del mensaje no puede estar vacío")

        if len(self.content) > 100000:  # Límite razonable
            raise ValueError("El contenido del mensaje es demasiado largo")

        if self.message_index < 0:
            raise ValueError("El índice del mensaje debe ser no negativo")

    def is_from_user(self) -> bool:
        """Verifica si el mensaje es del usuario."""
        return self.role == MessageRole.USER

    def is_from_assistant(self) -> bool:
        """Verifica si el mensaje es del asistente."""
        return self.role == MessageRole.ASSISTANT

    def is_system_message(self) -> bool:
        """Verifica si el mensaje es del sistema."""
        return self.role == MessageRole.SYSTEM

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el mensaje a diccionario."""
        return {
            "session_id": self.session_id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_index": self.message_index,
            "metadata": self.metadata,
            "token_count": self.token_count,
        }


@dataclass
class ChatSession:
    """Representa una sesión de conversación."""
    user_id: str
    session_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Relación con mensajes (no se incluye en __init__)
    messages: List[ChatMessage] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.user_id.strip():
            raise ValueError("El ID de usuario no puede estar vacío")

        if self.session_name and len(self.session_name) > 200:
            raise ValueError("El nombre de la sesión es demasiado largo")

    def add_message(self, message: ChatMessage) -> None:
        """Agrega un mensaje a la sesión."""
        if message.session_id != self.id:
            raise ValueError("El mensaje no pertenece a esta sesión")

        # Actualizar timestamp
        self.updated_at = datetime.utcnow()

        # Agregar mensaje
        self.messages.append(message)

        # Actualizar índice del mensaje
        message.message_index = len(self.messages) - 1

    def get_message_count(self) -> int:
        """Retorna el número de mensajes en la sesión."""
        return len(self.messages)

    def get_user_messages(self) -> List[ChatMessage]:
        """Retorna solo los mensajes del usuario."""
        return [msg for msg in self.messages if msg.is_from_user()]

    def get_assistant_messages(self) -> List[ChatMessage]:
        """Retorna solo los mensajes del asistente."""
        return [msg for msg in self.messages if msg.is_from_assistant()]

    def get_last_message(self) -> Optional[ChatMessage]:
        """Retorna el último mensaje de la sesión."""
        return self.messages[-1] if self.messages else None

    def is_empty(self) -> bool:
        """Verifica si la sesión está vacía."""
        return len(self.messages) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la sesión a diccionario."""
        return {
            "user_id": self.user_id,
            "session_name": self.session_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "metadata": self.metadata,
            "message_count": len(self.messages),
        }

    @property
    def id(self) -> int:
        """ID de la sesión (se asignará externamente)."""
        return getattr(self, '_id', 0)

    @id.setter
    def id(self, value: int) -> None:
        """Establece el ID de la sesión."""
        self._id = value


@dataclass
class FileDocument:
    """Representa un documento subido al sistema."""
    filename_original: str
    filename_saved: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_at: datetime = field(default_factory=datetime.utcnow)

    # Estado del procesamiento
    status: str = "pending"  # pending, processing, ready, error
    error_message: Optional[str] = None

    # Información del contenido
    total_pages: int = 0
    pages_processed: int = 0
    sections: List[FileSection] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.filename_original.strip():
            raise ValueError("El nombre de archivo original no puede estar vacío")

        if self.file_size <= 0:
            raise ValueError("El tamaño del archivo debe ser positivo")

        if self.file_size > 100 * 1024 * 1024:  # 100MB límite
            raise ValueError("El archivo es demasiado grande")

    def add_section(self, section: FileSection) -> None:
        """Agrega una sección al documento."""
        if section.file_id != self.id:
            raise ValueError("La sección no pertenece a este documento")

        self.sections.append(section)
        self.pages_processed += (section.end_page - section.start_page + 1)

    def get_section(self, section_id: int) -> Optional[FileSection]:
        """Obtiene una sección por ID."""
        return next((s for s in self.sections if s.id == section_id), None)

    def is_processing_complete(self) -> bool:
        """Verifica si el procesamiento del documento está completo."""
        return self.pages_processed >= self.total_pages and self.status == "ready"

    def has_error(self) -> bool:
        """Verifica si hay un error en el procesamiento."""
        return self.status == "error"

    def mark_as_ready(self) -> None:
        """Marca el documento como listo."""
        self.status = "ready"

    def mark_as_error(self, error_message: str) -> None:
        """Marca el documento con error."""
        self.status = "error"
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el documento a diccionario."""
        return {
            "filename_original": self.filename_original,
            "filename_saved": self.filename_saved,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "uploaded_at": self.uploaded_at.isoformat(),
            "status": self.status,
            "error_message": self.error_message,
            "total_pages": self.total_pages,
            "pages_processed": self.pages_processed,
            "section_count": len(self.sections),
        }

    @property
    def id(self) -> int:
        """ID del documento (se asignará externamente)."""
        return getattr(self, '_id', 0)

    @id.setter
    def id(self, value: int) -> None:
        """Establece el ID del documento."""
        self._id = value


@dataclass
class FileSection:
    """Representa una sección de un documento."""
    file_id: int
    title: Optional[str]
    start_page: int
    end_page: int
    char_count: int
    text_content: str = ""

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if self.start_page < 0:
            raise ValueError("La página inicial debe ser no negativa")

        if self.end_page < self.start_page:
            raise ValueError("La página final debe ser mayor o igual a la inicial")

        if self.char_count < 0:
            raise ValueError("El conteo de caracteres debe ser no negativo")

    def get_page_count(self) -> int:
        """Retorna el número de páginas en la sección."""
        return self.end_page - self.start_page + 1

    def is_empty(self) -> bool:
        """Verifica si la sección está vacía."""
        return self.char_count == 0

    def has_content(self) -> bool:
        """Verifica si la sección tiene contenido de texto."""
        return bool(self.text_content.strip())

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la sección a diccionario."""
        return {
            "file_id": self.file_id,
            "title": self.title,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "char_count": self.char_count,
            "has_content": self.has_content(),
            "page_count": self.get_page_count(),
        }

    @property
    def id(self) -> int:
        """ID de la sección (se asignará externamente)."""
        return getattr(self, '_id', 0)

    @id.setter
    def id(self, value: int) -> None:
        """Establece el ID de la sección."""
        self._id = value
