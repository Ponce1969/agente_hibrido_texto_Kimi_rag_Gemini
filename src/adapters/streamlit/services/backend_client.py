"""
Cliente HTTP para comunicación con el backend.
Adaptador que encapsula todas las llamadas HTTP.
"""
import os
import sys
from typing import Any

import httpx
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chat_models import ChatMessage, ChatRequest, ChatResponse, ChatSession
from models.file_models import (
    EmbeddingSearchResult,
    FileProgress,
    FileSection,
    FileUploadInfo,
)


class BackendClient:
    """Cliente para comunicación con el backend API."""

    def __init__(self, base_url: str = None):
        # Detectar si estamos en Docker o desarrollo local
        import os
        if base_url is None:
            # En Docker, usar el nombre del servicio
            if os.environ.get("DOCKER_ENV") == "true" or os.path.exists("/.dockerenv"):
                base_url = "http://backend:8000/api/v1"
            else:
                base_url = "http://localhost:8000/api/v1"

        self.base_url = base_url
        self.user_id = "streamlit_user"

    def test_connection(self) -> tuple[bool, str]:
        """Prueba la conexión con el backend."""
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return True, f"✅ Conectado a {self.base_url}"
            else:
                return False, f"❌ Error {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"❌ Error de conexión: {e}"

    # === Sesiones de Chat ===

    def create_session(self) -> int:
        """Crea una nueva sesión de chat."""
        try:
            response = httpx.post(
                f"{self.base_url}/sessions",
                json={"user_id": self.user_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            # Backend retorna {"session_id": X}, no {"id": X}
            session_id = data.get("session_id", 0)
            return session_id if session_id else 0
        except Exception as e:
            print(f"Error creando sesión: {e}")
            return 0

    def get_session_messages(self, session_id: int) -> list[ChatMessage]:
        """Obtiene los mensajes de una sesión."""
        try:
            response = httpx.get(
                f"{self.base_url}/sessions/{session_id}/messages",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            messages = [
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    message_index=msg.get("message_index", msg.get("index", 0)),  # Soporte para ambos campos
                    created_at=msg.get("created_at")
                )
                for msg in data
            ]
            return messages
        except Exception as e:
            st.error(f"Error cargando mensajes de sesión {session_id}: {e}")
            return []

    @st.cache_data(show_spinner=False, ttl=10)
    def list_sessions(_self, limit: int = 30) -> list[ChatSession]:
        """Lista las sesiones del usuario."""
        try:
            response = httpx.get(
                f"{_self.base_url}/sessions",
                params={"user_id": _self.user_id, "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return [
                ChatSession(
                    id=session["id"],
                    user_id=session["user_id"],
                    session_name=session.get("session_name"),
                    created_at=session["created_at"],
                    message_count=session.get("message_count", 0)
                )
                for session in data
            ]
        except Exception:
            return []

    def delete_session(self, session_id: int) -> bool:
        """Elimina una sesión."""
        try:
            response = httpx.delete(f"{self.base_url}/sessions/{session_id}", timeout=10)
            # Backend puede retornar 200 o 204 (No Content) al eliminar
            return response.status_code in [200, 204]
        except Exception as e:
            st.error(f"Error eliminando sesión {session_id}: {e}")
            return False

    def send_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Envía un mensaje de chat al backend."""
        try:
            payload = {
                "session_id": request.session_id,
                "message": request.message,
                "mode": request.mode.value
            }
            if request.file_id is not None:
                payload["file_id"] = request.file_id
            if request.selected_section_ids:
                payload["selected_section_ids"] = request.selected_section_ids

            response = httpx.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()

            return ChatResponse(
                content=data.get("reply", ""),  # El backend devuelve "reply", no "response"
                success=True
            )
        except httpx.TimeoutException:
            return ChatResponse(
                content="",
                success=False,
                error="Timeout: El agente tardó demasiado en responder"
            )
        except httpx.HTTPStatusError as e:
            # Intentar extraer mensaje user-friendly del JSON de error
            error_msg = f"Error del servidor: {e.response.status_code}"
            try:
                error_data = e.response.json()
                # Si el Guardian bloqueó el mensaje (403)
                if e.response.status_code == 403 and error_data.get("error") == "message_blocked":
                    user_message = error_data.get("message", "Tu mensaje ha sido bloqueado por razones de seguridad.")
                    reason = error_data.get("reason", "")
                    error_msg = f"🛡️ {user_message}\n\n💡 **Motivo:** {reason}"
                else:
                    # Otros errores del servidor
                    error_msg = error_data.get("detail", error_msg)
            except Exception:
                # Si no se puede parsear el JSON, usar mensaje genérico
                pass

            return ChatResponse(
                content="",
                success=False,
                error=error_msg
            )
        except Exception:
            return ChatResponse(
                content="",
                success=False,
            )

    # === Gestión de Archivos ===

    def list_files(self, limit: int = 30) -> list[FileUploadInfo]:
        """Lista los archivos subidos."""
        try:
            response = httpx.get(f"{self.base_url}/files", params={"limit": limit}, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [FileUploadInfo(**item) for item in data]
        except httpx.ConnectError:
            import streamlit as st
            st.error("🔌 Error de conexión con el backend. Verifica que esté funcionando.")
            return []
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Error obteniendo archivos: {e}")
            return []

    def upload_pdf(self, file_name: str, file_bytes: bytes, mime: str, auto_index: bool = False) -> dict[str, Any]:
        """Sube un archivo PDF."""
        files = {
            "file": (file_name, file_bytes, mime or "application/pdf"),
        }
        params = {"auto_index": "true" if auto_index else "false"}
        response = httpx.post(f"{self.base_url}/files/upload", files=files, params=params, timeout=60)
        response.raise_for_status()
        return response.json()

    def get_file_progress(self, file_id: int) -> FileProgress:
        """Obtiene el progreso de procesamiento de un archivo."""
        response = httpx.get(f"{self.base_url}/files/progress/{file_id}", timeout=10)
        response.raise_for_status()
        data = response.json()

        return FileProgress(
            phase=data["phase"],
            status=data["status"],
            pages_processed=data["pages_processed"],
            total_pages=data["total_pages"],
            detail=data.get("detail")
        )

    def start_file_processing(self, file_id: int) -> dict[str, Any]:
        """Inicia el procesamiento de un archivo."""
        response = httpx.post(f"{self.base_url}/files/process/{file_id}", timeout=10)
        response.raise_for_status()
        return response.json()

    def delete_file(self, file_id: int) -> bool:
        """
        Elimina un archivo y todos sus datos asociados.

        Args:
            file_id: ID del archivo a eliminar

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            response = httpx.delete(f"{self.base_url}/files/{file_id}", timeout=10)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                import streamlit as st
                st.warning(f"⚠️ Archivo {file_id} no encontrado")
                return False
            raise
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Error eliminando archivo: {e}")
            return False

    def get_file_sections(self, file_id: int) -> list[FileSection]:
        """Obtiene las secciones de un archivo."""
        response = httpx.get(f"{self.base_url}/files/{file_id}/sections", timeout=30)
        response.raise_for_status()
        data = response.json()

        return [
            FileSection(
                id=section["id"],
                file_id=section["file_id"],
                title=section["title"],
                start_page=section["start_page"],
                end_page=section["end_page"],
                content_preview=section.get("content_preview")
            )
            for section in data
        ]

    # === Embeddings ===

    def trigger_indexing(self, file_id: int) -> dict[str, Any]:
        """Dispara la indexación de embeddings."""
        response = httpx.post(f"{self.base_url}/embeddings/index/{file_id}", timeout=10)
        response.raise_for_status()
        return response.json()

    def search_embeddings(self, query: str, file_id: int | None, top_k: int = 5) -> list[EmbeddingSearchResult]:
        """Busca en los embeddings."""
        params = {"q": query, "top_k": top_k}
        if file_id is not None:
            params["file_id"] = file_id

        response = httpx.get(f"{self.base_url}/embeddings/search", params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        return [
            EmbeddingSearchResult(
                id=result["id"],
                file_id=result["file_id"],
                section_id=result["section_id"],
                chunk_index=result["chunk_index"],
                distance=result["distance"],
                content=result["content"]
            )
            for result in data.get("results", [])
        ]
