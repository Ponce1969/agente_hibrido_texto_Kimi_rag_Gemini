"""
Servicio de aplicación para gestión de archivos y PDFs.
Encapsula la lógica de negocio relacionada con archivos.
"""
import streamlit as st
from typing import List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.backend_client import BackendClient
from models.file_models import FileUploadInfo, FileProgress, FileSection, ProcessingPhase


class FileService:
    """Servicio para gestión de archivos y PDFs."""
    
    def __init__(self, backend_client: BackendClient):
        self.backend = backend_client
    
    def upload_pdf(self, uploaded_file, auto_index: bool = True) -> Tuple[bool, str, Optional[int]]:
        """
        Sube un archivo PDF.
        Returns: (success, message, file_id)
        """
        try:
            file_bytes = uploaded_file.read()
            result = self.backend.upload_pdf(
                file_name=uploaded_file.name,
                file_bytes=file_bytes,
                mime=uploaded_file.type or "application/pdf",
                auto_index=auto_index
            )
            file_id = result["file_id"]
            st.session_state.pdf_file_id = file_id
            return True, f"Subido. file_id={file_id}", file_id
        except Exception as e:
            return False, f"Error al subir PDF: {e}", None
    
    def get_file_progress(self, file_id: int) -> Optional[FileProgress]:
        """Obtiene el progreso de un archivo."""
        try:
            return self.backend.get_file_progress(file_id)
        except Exception:
            return None
    
    def is_file_ready_for_context(self, file_id: int) -> Tuple[bool, str]:
        """
        Verifica si un archivo está listo para usar como contexto.
        Returns: (is_ready, status_message)
        """
        try:
            progress = self.get_file_progress(file_id)
            if not progress:
                return False, "No se pudo verificar el estado del archivo"
            
            chunks = 0
            if progress.detail:
                chunks = int(progress.detail.get("chunks_indexed", 0))
            
            if progress.phase == ProcessingPhase.READY and chunks > 0:
                return True, f"Listo ({chunks} chunks indexados)"
            elif progress.phase == ProcessingPhase.PROCESSING_SECTIONS:
                return False, "Procesando secciones del PDF..."
            elif progress.phase == ProcessingPhase.INDEXING_EMBEDDINGS:
                return False, "Indexando embeddings..."
            elif chunks == 0:
                return False, "Sin embeddings indexados"
            else:
                return False, f"Estado: {progress.phase.value}"
        except Exception as e:
            return False, f"Error verificando estado: {e}"
    
    def trigger_indexing(self, file_id: int) -> Tuple[bool, str]:
        """
        Dispara la indexación de un archivo.
        Returns: (success, message)
        """
        try:
            self.backend.trigger_indexing(file_id)
            return True, "Indexación iniciada en segundo plano"
        except Exception as e:
            return False, f"Error iniciando indexación: {e}"
    
    def get_file_list(self, limit: int = 30) -> List[FileUploadInfo]:
        """Obtiene la lista de archivos."""
        return self.backend.list_files(limit=limit)
    
    def get_file_sections(self, file_id: int) -> List[FileSection]:
        """Obtiene las secciones de un archivo."""
        try:
            return self.backend.get_file_sections(file_id)
        except Exception:
            return []
    
    def setup_pdf_context(self, file_id: int) -> Tuple[bool, str]:
        """
        Configura un PDF para usar como contexto.
        Returns: (success, message)
        """
        try:
            # Verificar estado actual
            is_ready, status_msg = self.is_file_ready_for_context(file_id)
            
            if is_ready:
                st.session_state.pdf_file_id = file_id
                st.session_state._use_pdf_context = True
                return True, f"PDF configurado como contexto. {status_msg}"
            else:
                # Intentar disparar indexación si no está lista
                success, index_msg = self.trigger_indexing(file_id)
                if success:
                    st.session_state.pdf_file_id = file_id
                    st.session_state._use_pdf_context = True
                    return True, f"PDF configurado. {index_msg}. Estado: {status_msg}"
                else:
                    return False, f"No se pudo configurar el PDF: {index_msg}"
        except Exception as e:
            return False, f"Error configurando PDF: {e}"
    
    def delete_file(self, file_id: int) -> Tuple[bool, str]:
        """
        Elimina un archivo y todos sus datos asociados.
        
        Args:
            file_id: ID del archivo a eliminar
            
        Returns:
            (success, message)
        """
        try:
            success = self.backend.delete_file(file_id)
            if success:
                # Limpiar session state si era el archivo activo
                if st.session_state.get("pdf_file_id") == file_id:
                    st.session_state.pdf_file_id = None
                    st.session_state._use_pdf_context = False
                return True, f"Archivo {file_id} eliminado correctamente"
            else:
                return False, f"No se pudo eliminar el archivo {file_id}"
        except Exception as e:
            return False, f"Error eliminando archivo: {e}"
