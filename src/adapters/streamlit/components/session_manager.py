"""
Componente para gestión de sesiones de chat.
Maneja la visualización y selección de sesiones.
"""
import streamlit as st
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chat_models import ChatSession
from services.session_service import SessionService


class SessionManager:
    """Componente para gestión de sesiones."""
    
    def __init__(self, session_service: SessionService):
        self.session_service = session_service
    
    def render_session_controls(self) -> None:
        """Renderiza los controles de sesión."""
        st.subheader("🔄 Gestión de Sesiones")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ Nueva Sesión", use_container_width=True):
                self.session_service.create_new_session()
                st.success("Nueva sesión creada")
                st.rerun()
        
        with col2:
            current_session = st.session_state.get("session_id", 0)
            st.info(f"Sesión actual: {current_session}")
    
    def render_session_list(self) -> None:
        """Renderiza la lista de sesiones anteriores."""
        st.header("📋 Sesiones anteriores")
        
        try:
            sessions = self.session_service.get_session_list()
            
            if sessions:
                # Filtrar sesiones inválidas (ID 0 son sesiones temporales/fallidas)
                valid_sessions = [s for s in sessions if s.id > 0]
                
                if not valid_sessions:
                    st.info("No hay sesiones guardadas disponibles.")
                    return
                
                # Usar enumerate para keys únicas
                for idx, session in enumerate(valid_sessions):
                    with st.expander(
                        f"Sesión {session.id} - {session.message_count} mensajes",
                        expanded=False
                    ):
                        st.write(f"**Creada:** {session.created_at}")
                        if session.session_name:
                            st.write(f"**Nombre:** {session.session_name}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button(
                                "🔄 Cargar sesión", 
                                key=f"load_session_{session.id}_{idx}",  # Key única con índice
                                use_container_width=True
                            ):
                                self.session_service.switch_to_session(session.id)
                        
                        with col2:
                            if st.button(
                                "🗑️ Eliminar", 
                                key=f"delete_session_{session.id}_{idx}",  # Key única con índice
                                use_container_width=True,
                                type="secondary"
                            ):
                                if self.session_service.delete_session(session.id):
                                    st.success(f"Sesión {session.id} eliminada")
                                    st.rerun()
                                else:
                                    st.error("Error al eliminar la sesión")
            else:
                st.info("No hay sesiones previas para este usuario.")
        
        except Exception as e:
            st.error(f"Error cargando sesiones: {e}")
    
    def render_session_section(self) -> None:
        """Renderiza la sección completa de gestión de sesiones."""
        self.render_session_controls()
        self.render_session_list()
