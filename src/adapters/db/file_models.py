from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class FileStatus(str):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class FileUpload(SQLModel, table=True):
    __tablename__ = "file_uploads"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    uuid_str: str = Field(index=True, description="UUID4 como nombre lógico del archivo en disco")
    filename_original: str
    filename_saved: str
    path: str
    size_bytes: int
    total_pages: int = 0
    pages_processed: int = 0
    status: str = Field(default=FileStatus.PENDING, index=True)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relación inversa no tipada para evitar problemas con SQLAlchemy 2.0.
    # Consultas se realizan por file_id en FileSection.


class FileSection(SQLModel, table=True):
    __tablename__ = "file_sections"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    file_id: int = Field(foreign_key="file_uploads.id", index=True)
    title: str | None = None
    start_page: int
    end_page: int
    char_count: int = 0

    # Relación ORM omitida; se accede vía consultas por file_id.
