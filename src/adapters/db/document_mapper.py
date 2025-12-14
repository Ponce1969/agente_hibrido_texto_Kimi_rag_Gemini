from __future__ import annotations

import logging
import re

from src.domain.ports.file_repository_port import FileRepositoryPort

logger = logging.getLogger(__name__)

class DocumentMapper:
    """
    Mapea identificadores amigables (display_ids, nombres) a file_ids internos.
    Usa el repositorio de archivos para resolver referencias reales.
    """

    def __init__(self, file_repository: FileRepositoryPort):
        self.file_repository = file_repository
        # Caché opcional para rendimiento
        self._cache: dict[str, int] = {}

    def get_file_id(self, display_reference: str) -> int | None:
        """
        Obtiene el file_id interno basado en una referencia de visualización.

        Soporta:
        - "ID:5" -> 5
        - "5" -> 5 (si es numérico)
        - "nombre_archivo.pdf" -> Búsqueda por nombre (implementación futura/opcional)
        """
        if not display_reference:
            return None

        # 1. Intentar patrón "ID:X"
        match = re.search(r"ID:?\s*(\d+)", display_reference, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        # 2. Intentar numérico directo
        if str(display_reference).isdigit():
            return int(display_reference)

        # 3. Intentar búsqueda por nombre (si tuviéramos búsqueda por nombre en el repo)
        # Por ahora nos limitamos a IDs explícitos para mantenerlo simple y seguro

        return None

    def parse_document_reference_from_text(self, text: str) -> int | None:
        """
        Busca referencias a documentos dentro de un texto libre.
        Ej: "analiza el documento ID:5" -> 5
        """
        # Patrón estricto para evitar falsos positivos con números sueltos
        match = re.search(r"\bID:?\s*(\d+)\b", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
