"""
Adaptador de repositorio de archivos para SQL (SQLite).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlmodel import Session as SQLSession
from sqlmodel import select

from src.adapters.db.database import engine as sqlite_engine
from src.adapters.db.file_models import FileSection, FileUpload
from src.domain.models.file_models import FileDocument, FileStatus
from src.domain.models.file_models import FileSection as DomainSection
from src.domain.ports.file_repository_port import FileRepositoryPort


class SQLFileRepository(FileRepositoryPort):
    """Implementación de FileRepositoryPort para una base de datos SQL."""

    def _to_domain(self, db_file: FileUpload) -> FileDocument:
        return FileDocument(
            id=str(db_file.id),
            filename=db_file.filename_original,
            file_path=db_file.path,
            status=FileStatus(db_file.status),
            created_at=db_file.created_at,
            total_pages=db_file.total_pages,
            pages_processed=db_file.pages_processed,
            error_message=db_file.error_message,
        )

    def create_file_record(self, filename: str, file_path: str, size_bytes: int) -> FileDocument:
        with SQLSession(sqlite_engine) as session:
            db_file = FileUpload(
                uuid_str=str(uuid.uuid4()),
                filename_original=filename,
                filename_saved=file_path.split('/')[-1],
                path=file_path,
                size_bytes=size_bytes,
                status=FileStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            session.add(db_file)
            session.commit()
            session.refresh(db_file)
            return self._to_domain(db_file)

    def add_sections_to_file(self, file_id: int, sections: list[dict]) -> None:
        with SQLSession(sqlite_engine) as session:
            for sec_data in sections:
                db_section = FileSection(file_id=file_id, **sec_data)
                session.add(db_section)
            session.commit()

    def get_file(self, file_id: int) -> FileDocument | None:
        with SQLSession(sqlite_engine) as session:
            db_file = session.get(FileUpload, file_id)
            return self._to_domain(db_file) if db_file else None

    def list_files(self, limit: int = 20) -> list[FileDocument]:
        with SQLSession(sqlite_engine) as session:
            db_files = session.exec(
                select(FileUpload).order_by(FileUpload.created_at.desc()).limit(limit)
            ).all()
            return [self._to_domain(f) for f in db_files]

    def get_file_sections(self, file_id: int) -> list[DomainSection]:
        with SQLSession(sqlite_engine) as session:
            db_sections = session.exec(
                select(FileSection).where(FileSection.file_id == file_id).order_by(FileSection.start_page)
            ).all()
            return [
                DomainSection(
                    id=sec.id, file_id=str(sec.file_id), text="",
                    page_number=sec.start_page, chunk_index=0
                )
                for sec in db_sections
            ]

    def update_file_status(self, file_id: int, status: FileStatus, error_message: str | None = None) -> None:
        with SQLSession(sqlite_engine) as session:
            db_file = session.get(FileUpload, file_id)
            if db_file:
                db_file.status = status.value
                db_file.error_message = error_message
                db_file.updated_at = datetime.now(UTC)
                session.add(db_file)
                session.commit()

    def update_file_pages(self, file_id: int, total_pages: int, pages_processed: int) -> None:
        with SQLSession(sqlite_engine) as session:
            db_file = session.get(FileUpload, file_id)
            if db_file:
                db_file.total_pages = total_pages
                db_file.pages_processed = pages_processed
                db_file.updated_at = datetime.now(UTC)
                session.add(db_file)
                session.commit()

    def delete_file(self, file_id: int) -> bool:
        """
        Elimina un archivo y sus secciones asociadas.

        Args:
            file_id: ID del archivo a eliminar

        Returns:
            True si se eliminó correctamente, False si no existía
        """
        with SQLSession(sqlite_engine) as session:
            # Eliminar secciones primero (FK constraint)
            sections = session.exec(
                select(FileSection).where(FileSection.file_id == file_id)
            ).all()
            for section in sections:
                session.delete(section)

            # Eliminar archivo
            db_file = session.get(FileUpload, file_id)
            if db_file:
                session.delete(db_file)
                session.commit()
                return True
            return False
