"""
Servicio de gestión de contexto para RAG.

Responsabilidades:
1. Mapear "ID:5" → file_id real
2. Gestionar contexto conversacional ("este PDF")
3. Mantener estado por sesión
"""
import re
from typing import Any


class RagContextService:
    def __init__(self, file_repository: Any) -> None:
        self.file_repository = file_repository
        self.session_contexts: dict[str, dict[str, Any]] = {}
        # {session_id: {"current_file_id": 123, "current_file_name": "doc.pdf"}}

    def get_current_file_id(self, session_id: str) -> int | None:
        return self.session_contexts.get(session_id, {}).get("current_file_id")

    def set_current_file_id(self, session_id: str, file_id: int, file_name: str | None = None) -> None:
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {}
        self.session_contexts[session_id]["current_file_id"] = file_id
        if file_name:
            self.session_contexts[session_id]["current_file_name"] = file_name

    async def resolve_file_reference(self, session_id: str, query: str) -> int | None:
        """Resuelve referencias como 'ID:5' o 'este PDF' a file_id"""
        # 1. Buscar referencia explícita: "ID:5"
        id_match = re.search(r"ID:?\s*(\d+)", query, re.IGNORECASE)
        if id_match:
            display_id = id_match.group(1)
            return await self._get_file_id_by_display_id(display_id)

        # 2. Referencias contextuales: "este PDF", "ese documento"
        reference_keywords = ["este", "ese", "aquel", "el documento", "el pdf", "el libro"]
        if any(keyword in query.lower() for keyword in reference_keywords):
            return self.get_current_file_id(session_id)

        return None

    async def _get_file_id_by_display_id(self, display_id: str) -> int | None:
        """Convierte '5' (mostrado al usuario) a file_id real"""
        # Buscar en file_repository por metadata
        files = await self.file_repository.get_files_by_metadata(
            {"display_id": display_id}
        )
        if files:
            return int(files[0].id)

        # Si display_id es numérico, asumir que es el file_id
        try:
            return int(display_id)
        except ValueError:
            return None
