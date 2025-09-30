"""
Aplicación Streamlit refactorizada con arquitectura hexagonal.
Orquesta los componentes y servicios siguiendo principios SOLID.
"""
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="🤖 Asistente IA con RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports de la arquitectura hexagonal
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.backend_client import BackendClient
from services.session_service import SessionService
from services.file_service import FileService
from components.chat_interface import ChatInterface
from components.session_manager import SessionManager
from components.pdf_context import PDFContextManager


def initialize_services() -> tuple[BackendClient, SessionService, FileService]:
    """Inicializa los servicios de la aplicación."""
    backend_client = BackendClient()
    session_service = SessionService(backend_client)
    file_service = FileService(backend_client)
    
    return backend_client, session_service, file_service


def initialize_components(
    backend_client: BackendClient, 
    session_service: SessionService, 
    file_service: FileService
) -> tuple[ChatInterface, SessionManager, PDFContextManager]:
    """Inicializa los componentes UI."""
    chat_interface = ChatInterface(backend_client, session_service)
    session_manager = SessionManager(session_service)
    pdf_manager = PDFContextManager(file_service)
    
    return chat_interface, session_manager, pdf_manager


def main():
    """Función principal de la aplicación."""
    st.title("🤖 Asistente IA con RAG")
    st.markdown("*Arquitectura hexagonal • Python 3.12+ • PostgreSQL + pgvector*")
    
    # Inicializar servicios
    backend_client, session_service, file_service = initialize_services()
    
    # Inicializar componentes
    chat_interface, session_manager, pdf_manager = initialize_components(
        backend_client, session_service, file_service
    )
    
    # Asegurar sesión activa
    session_service.get_or_create_current_session()
    
    # Layout principal
    with st.sidebar:
        # Selector de agente
        agent_mode = chat_interface.render_agent_selector()
        
        st.divider()
        
        # Gestión de PDFs
        file_id, use_context = pdf_manager.render_pdf_section()
        
        st.divider()
        
        # Botones de descarga (siempre visibles)
        st.subheader("📥 Descargar Chat")
        chat_interface.render_download_buttons()
        
        st.divider()
        
        # Diagnóstico de conexión
        st.subheader("🔧 Diagnóstico")
        if st.button("🔍 Probar conexión Backend", use_container_width=True):
            success, message = backend_client.test_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
        
        st.divider()
        
        # Gestión de sesiones
        session_manager.render_session_section()
    
    # Área principal de chat
    # LÓGICA HÍBRIDA: Solo enviar file_id si el usuario activó el toggle
    # - use_context = False: Chat normal con Kimi-K2 (file_id=None)
    # - use_context = True: RAG con Gemini (file_id=X)
    final_file_id = file_id if (use_context and file_id) else None
    chat_interface.render_chat_section(agent_mode, final_file_id)
    
    # Footer
    st.divider()
    st.caption("🏗️ Arquitectura hexagonal • 🔍 RAG con embeddings • ⚡ Optimizado para bajos recursos")


if __name__ == "__main__":
    main()
