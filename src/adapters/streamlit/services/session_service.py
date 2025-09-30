"""
Servicio de aplicación para gestión de sesiones de chat.
Encapsula la lógica de negocio relacionada con sesiones.
"""
import streamlit as st
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.backend_client import BackendClient
from models.chat_models import ChatSession, ChatMessage


class SessionService:
    """Servicio para gestión de sesiones de chat."""
    
    def __init__(self, backend_client: BackendClient):
        self.backend = backend_client
    
    def get_or_create_current_session(self) -> int:
        """Obtiene la sesión actual o crea una nueva."""
        if "session_id" not in st.session_state or st.session_state.session_id == 0:
            session_id = self.backend.create_session()
            st.session_state.session_id = session_id
            st.session_state.messages = []
        return st.session_state.session_id
    
    def load_session_messages(self, session_id: int) -> List[ChatMessage]:
        """Carga los mensajes de una sesión."""
        messages = self.backend.get_session_messages(session_id)
        st.session_state.messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        return messages
    
    def switch_to_session(self, session_id: int) -> None:
        """Cambia a una sesión específica."""
        st.session_state.session_id = session_id
        self.load_session_messages(session_id)
        st.rerun()
    
    def create_new_session(self) -> int:
        """Crea una nueva sesión y cambia a ella."""
        session_id = self.backend.create_session()
        st.session_state.session_id = session_id
        st.session_state.messages = []
        return session_id
    
    def delete_session(self, session_id: int) -> bool:
        """Elimina una sesión."""
        success = self.backend.delete_session(session_id)
        if success and st.session_state.get("session_id") == session_id:
            # Si eliminamos la sesión actual, crear una nueva
            self.create_new_session()
        return success
    
    def get_session_list(self, limit: int = 30) -> List[ChatSession]:
        """Obtiene la lista de sesiones del usuario."""
        return self.backend.list_sessions(limit=limit)
