"""
Excepciones de dominio para el asistente de aprendizaje de Python.

Estas excepciones representan errores de negocio y deben ser independientes
de la infraestructura (base de datos, APIs externas, etc.).
"""
from __future__ import annotations


class DomainException(Exception):
    """Excepción base para errores de dominio."""
    pass


class ChatSessionNotFoundError(DomainException):
    """Se lanza cuando no se encuentra una sesión de chat."""
    def __init__(self, session_id: int | str) -> None:
        self.session_id = session_id
        super().__init__(f"Sesión de chat {session_id} no encontrada")


class ChatSessionAlreadyExistsError(DomainException):
    """Se lanza cuando se intenta crear una sesión que ya existe."""
    def __init__(self, session_id: int | str) -> None:
        self.session_id = session_id
        super().__init__(f"Sesión de chat {session_id} ya existe")


class InvalidMessageError(DomainException):
    """Se lanza cuando un mensaje es inválido."""
    def __init__(self, message: str, reason: str = "") -> None:
        self.message = message
        self.reason = reason
        reason_text = f": {reason}" if reason else ""
        super().__init__(f"Mensaje inválido '{message}'{reason_text}")


class MessageNotFoundError(DomainException):
    """Se lanza cuando no se encuentra un mensaje."""
    def __init__(self, message_id: int | str) -> None:
        self.message_id = message_id
        super().__init__(f"Mensaje {message_id} no encontrado")


class FileNotFoundError(DomainException):
    """Se lanza cuando no se encuentra un archivo."""
    def __init__(self, file_id: int | str) -> None:
        self.file_id = file_id
        super().__init__(f"Archivo {file_id} no encontrado")


class FileProcessingError(DomainException):
    """Se lanza cuando hay un error procesando un archivo."""
    def __init__(self, file_id: int | str, reason: str = "") -> None:
        self.file_id = file_id
        self.reason = reason
        reason_text = f": {reason}" if reason else ""
        super().__init__(f"Error procesando archivo {file_id}{reason_text}")


class FileSectionNotFoundError(DomainException):
    """Se lanza cuando no se encuentra una sección de archivo."""
    def __init__(self, file_id: int | str, section_id: int | str) -> None:
        self.file_id = file_id
        self.section_id = section_id
        super().__init__(f"Sección {section_id} del archivo {file_id} no encontrada")


class AgentModeNotSupportedError(DomainException):
    """Se lanza cuando se solicita un modo de agente no soportado."""
    def __init__(self, mode: str) -> None:
        self.mode = mode
        super().__init__(f"Modo de agente '{mode}' no soportado")


class AIProviderError(DomainException):
    """Se lanza cuando hay un error con el proveedor de IA."""
    def __init__(self, provider: str, reason: str = "") -> None:
        self.provider = provider
        self.reason = reason
        reason_text = f": {reason}" if reason else ""
        super().__init__(f"Error con proveedor de IA '{provider}'{reason_text}")


class InsufficientContextError(DomainException):
    """Se lanza cuando no hay suficiente contexto para responder."""
    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        reason_text = f": {reason}" if reason else ""
        super().__init__(f"Contexto insuficiente para generar respuesta{reason_text}")


class RateLimitExceededError(DomainException):
    """Se lanza cuando se excede el límite de uso."""
    def __init__(self, limit_type: str = "") -> None:
        self.limit_type = limit_type
        limit_text = f" ({limit_type})" if limit_type else ""
        super().__init__(f"Límite de uso excedido{limit_text}")


class ValidationError(DomainException):
    """Se lanza cuando hay un error de validación."""
    def __init__(self, field: str, value: str, reason: str = "") -> None:
        self.field = field
        self.value = value
        self.reason = reason
        reason_text = f": {reason}" if reason else ""
        super().__init__(f"Validación fallida para '{field}' con valor '{value}'{reason_text}")
