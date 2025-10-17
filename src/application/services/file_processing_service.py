"""
Servicio de aplicación para procesar y indexar archivos.
"""
from __future__ import annotations

import io
import logging
import os
from typing import TYPE_CHECKING, Optional
from uuid import uuid4
from pathvalidate import sanitize_filename

from pypdf import PdfReader

from src.domain.models.file_models import FileStatus, FileDocument
from src.adapters.config.settings import settings

if TYPE_CHECKING:
    from src.domain.ports.file_repository_port import FileRepositoryPort
    from src.application.services.embeddings_service import EmbeddingsServiceV2

logger = logging.getLogger(__name__)

class FileProcessingService:
    """Orquesta el procesamiento, extracción de texto e indexación de archivos."""

    def __init__(
        self, 
        file_repo: FileRepositoryPort, 
        embeddings_service: EmbeddingsServiceV2,
        max_pdf_size_mb: int = 50
    ):
        self.file_repo = file_repo
        self.embeddings_service = embeddings_service
        self.max_pdf_size_mb = max_pdf_size_mb

    async def upload_and_save_file(self, file: 'UploadFile') -> FileDocument:
        filename_original = sanitize_filename(file.filename or "uploaded.pdf")
        content = await file.read()
        size_bytes = len(content)

        max_bytes = self.max_pdf_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError(f"Archivo demasiado grande. Máximo {self.max_pdf_size_mb} MB")

        uid = str(uuid4())
        filename_saved = f"{uid}.pdf"
        save_path = os.path.join("data", "files", filename_saved)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(content)

        return self.file_repo.create_file_record(filename_original, save_path, size_bytes)

    def process_pdf_sections(self, file_id: int):
        logger.info(f"Iniciando procesamiento de secciones para file_id={file_id}")
        file_doc = self.file_repo.get_file(file_id)
        if not file_doc:
            logger.error(f"Intento de procesar archivo no existente: {file_id}")
            return

        try:
            self.file_repo.update_file_status(file_id, FileStatus.PROCESSING)
            with open(file_doc.file_path, "rb") as f:
                reader = PdfReader(io.BytesIO(f.read()))

            total_pages = len(reader.pages)
            self.file_repo.update_file_pages(file_id, total_pages=total_pages, pages_processed=0)

            window = max(1, settings.file_chapter_max_pages)
            sections_data = []
            for start in range(0, total_pages, window):
                end = min(total_pages - 1, start + window - 1)
                text_parts = [reader.pages[i].extract_text() or "" for i in range(start, end + 1)]
                char_count = len("\n".join(text_parts))
                sections_data.append({"start_page": start, "end_page": end, "char_count": char_count})
                self.file_repo.update_file_pages(file_id, total_pages, pages_processed=end + 1)

            self.file_repo.add_sections_to_file(file_id, sections_data)
            self.file_repo.update_file_status(file_id, FileStatus.READY)
            logger.info(f"Procesamiento de secciones completado para file_id={file_id}")

        except Exception as e:
            logger.error(f"Error procesando secciones para file_id={file_id}: {e}", exc_info=True)
            self.file_repo.update_file_status(file_id, FileStatus.ERROR, str(e))

    async def index_file(self, file_id: int) -> int:
        logger.info(f"Iniciando indexación para file_id={file_id}")
        file_doc = self.file_repo.get_file(file_id)
        if not file_doc or file_doc.status not in [FileStatus.READY, FileStatus.INDEXED]:
            raise ValueError(f"Archivo {file_id} no está listo para indexar (estado: {file_doc.status if file_doc else 'N/A'}).")

        try:
            with open(file_doc.file_path, "rb") as f:
                reader = PdfReader(io.BytesIO(f.read()))
        except Exception as e:
            raise IOError(f"No se pudo leer el archivo físico {file_doc.file_path}: {e}")

        sections = self.file_repo.get_file_sections(file_id)
        if not sections:
            raise ValueError(f"El archivo {file_id} no tiene secciones para procesar.")

        for section in sections:
            text_parts = [reader.pages[i].extract_text() or "" for i in range(section.page_number, section.page_number + 1)]
            section.text = "\n".join(text_parts).strip()
        
        valid_sections = [sec for sec in sections if sec.text]
        if not valid_sections:
            raise ValueError(f"No se pudo extraer texto de ninguna sección del archivo {file_id}")

        try:
            self.file_repo.update_file_status(file_id, FileStatus.INDEXING)
            indexed_count = await self.embeddings_service.index_document(file_doc, valid_sections)
            self.file_repo.update_file_status(file_id, FileStatus.INDEXED)
            logger.info(f"Se indexaron {indexed_count} chunks para el archivo {file_id}")
            return indexed_count
        except Exception as e:
            self.file_repo.update_file_status(file_id, FileStatus.ERROR, str(e))
            logger.error(f"Error al indexar el archivo {file_id}: {e}", exc_info=True)
            raise

    def get_file_status(self, file_id: int) -> Optional[FileDocument]:
        return self.file_repo.get_file(file_id)

    def list_files(self, limit: int) -> list[FileDocument]:
        return self.file_repo.list_files(limit)
