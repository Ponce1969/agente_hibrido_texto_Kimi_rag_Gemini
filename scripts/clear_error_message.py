#!/usr/bin/env python3
"""
Script para limpiar el error_message de archivos indexados correctamente.
"""
from sqlmodel import Session, select
from src.adapters.db.database import engine
from src.adapters.db.file_models import FileUpload
from datetime import datetime, UTC


def clear_error_messages():
    """Limpia error_message de archivos con status 'ready' o 'indexed'."""
    with Session(engine) as session:
        # Buscar archivos con status ready/indexed que tengan error_message
        statement = select(FileUpload).where(
            FileUpload.status.in_(["ready", "indexed"]),
            FileUpload.error_message.isnot(None)
        )
        files = session.exec(statement).all()
        
        if not files:
            print("✅ No hay archivos con error_message para limpiar.")
            return
        
        print(f"📁 Encontrados {len(files)} archivo(s) con error_message:")
        for file in files:
            print(f"  - ID: {file.id}, Filename: {file.filename_original}")
            print(f"    Status: {file.status}, Error: {file.error_message[:50]}...")
            
            # Limpiar el error_message
            file.error_message = None
            file.updated_at = datetime.now(UTC)
            session.add(file)
        
        session.commit()
        print(f"\n✅ Se limpiaron {len(files)} archivo(s) exitosamente.")


if __name__ == "__main__":
    clear_error_messages()
