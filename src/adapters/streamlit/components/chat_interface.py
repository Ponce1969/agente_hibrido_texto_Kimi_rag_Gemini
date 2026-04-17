"""
Componente de interfaz de chat.
Maneja la visualizacion y entrada de mensajes de chat.
Layout: mensajes con scroll + input fijo abajo.
"""

import io
import os
import sys
from datetime import datetime

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chat_models import AgentMode, ChatRequest
from services.backend_client import BackendClient
from services.session_service import SessionService


class ChatInterface:
    """Componente para la interfaz de chat con input fijo abajo."""

    def __init__(self, backend_client: BackendClient, session_service: SessionService):
        self.backend = backend_client
        self.session_service = session_service

    def render_agent_selector(self) -> AgentMode:
        """Renderiza el selector de agente."""
        st.subheader("🤖 Selector de Agente")

        agent_options = {
            "🏗️ Arquitecto Python Senior": AgentMode.PYTHON_ARCHITECT,
            "⚙️ Ingeniero de Código": AgentMode.CODE_GENERATOR,
            "🔒 Auditor de Seguridad": AgentMode.SECURITY_ANALYST,
            "🗄️ Especialista en BD": AgentMode.DATABASE_SPECIALIST,
            "🔄 Ingeniero de Refactoring": AgentMode.REFACTOR_ENGINEER,
        }

        selected = st.selectbox(
            "Elige el rol del agente:",
            options=list(agent_options.keys()),
            index=0,
            key="agent_mode_selector",
        )

        return agent_options[selected]

    def render_chat_history(self) -> None:
        """Renderiza el historial de chat dentro de un contenedor con scroll.

        Usa st.container(height=...) para crear un area de mensajes con scroll
        propio. El chat input queda fuera de este contenedor, siempre abajo.
        """
        if "messages" not in st.session_state:
            st.session_state.messages = []

        msg_count = len(st.session_state.messages)

        if msg_count == 0:
            chat_height = 180
        elif msg_count <= 3:
            chat_height = 300
        elif msg_count <= 8:
            chat_height = 450
        else:
            chat_height = 550

        with st.container(height=chat_height, border=False):
            if msg_count == 0:
                st.markdown(
                    '<div style="text-align: center; padding: 2rem 1rem; color: #888; '
                    'font-size: 0.95rem;">'
                    "Escribi tu consulta abajo para empezar"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

    def handle_user_input(
        self, agent_mode: AgentMode, file_id: int | None = None
    ) -> None:
        """Maneja la entrada del usuario y genera respuesta."""
        if prompt := st.chat_input("Escribe tu consulta aqui..."):
            with st.chat_message("user"):
                st.markdown(prompt)

            st.session_state.messages.append({"role": "user", "content": prompt})

            session_id = self.session_service.get_or_create_current_session()
            request = ChatRequest(
                session_id=session_id,
                message=prompt,
                mode=agent_mode,
                file_id=file_id,
            )

            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    response = self.backend.send_chat_message(request)

                if response.success:
                    st.markdown(response.content)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response.content,
                        }
                    )

                    try:
                        self.session_service.load_session_messages(session_id)
                    except Exception:
                        pass
                else:
                    st.error(f"Error: {response.error}")

    def _generate_markdown_content(self) -> str:
        """Genera contenido Markdown del chat."""
        if "messages" not in st.session_state or not st.session_state.messages:
            return "# Chat vacio\n\nNo hay mensajes para exportar."

        md_content = (
            f"# Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        for msg in st.session_state.messages:
            role = "🧑‍💻 Usuario" if msg["role"] == "user" else "🤖 Asistente"
            md_content += f"## {role}\n\n{msg['content']}\n\n---\n\n"

        return md_content

    def _generate_pdf_content(self) -> bytes | None:
        """Genera contenido PDF del chat usando reportlab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=30,
            )

            user_style = ParagraphStyle(
                "UserStyle",
                parent=styles["Normal"],
                fontSize=12,
                leftIndent=20,
                spaceAfter=10,
            )

            assistant_style = ParagraphStyle(
                "AssistantStyle",
                parent=styles["Normal"],
                fontSize=12,
                leftIndent=40,
                spaceAfter=10,
            )

            story = []
            title = f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 20))

            if "messages" in st.session_state and st.session_state.messages:
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        story.append(Paragraph("<b>🧑‍💻 Usuario:</b>", user_style))
                        story.append(Paragraph(msg["content"], user_style))
                    else:
                        story.append(Paragraph("<b>🤖 Asistente:</b>", assistant_style))
                        story.append(Paragraph(msg["content"], assistant_style))

                    story.append(Spacer(1, 10))
            else:
                story.append(
                    Paragraph("No hay mensajes para exportar.", styles["Normal"])
                )

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        except ImportError:
            st.warning("📄 Para generar PDFs, instala: pip install reportlab")
            return None
        except Exception as e:
            st.error(f"Error generando PDF: {e}")
            return None

    def render_download_buttons(self) -> None:
        """Renderiza los botones de descarga."""
        if "messages" not in st.session_state or not st.session_state.messages:
            st.info("💬 Inicia una conversacion para descargar")
            return

        md_content = self._generate_markdown_content()
        md_bytes = md_content.encode("utf-8")
        pdf_bytes = self._generate_pdf_content()

        st.download_button(
            label="📄 Markdown",
            data=md_bytes,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        if pdf_bytes is not None:
            st.download_button(
                label="📑 PDF",
                data=pdf_bytes,
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button(
                "📑 PDF (no disponible)",
                disabled=True,
                use_container_width=True,
                help="Instala reportlab para generar PDFs",
            )

    def render_chat_section(
        self, agent_mode: AgentMode, file_id: int | None = None
    ) -> None:
        """Renderiza la seccion completa de chat.

        Layout: header -> messages container (scroll) -> chat input (bottom).
        st.chat_input siempre queda al final y Streamlit lo fija abajo.
        """
        st.header("💬 Chat")

        if file_id:
            st.success(
                f"🔍 **RAG Activado** - Gemini 2.5 Flash consultara el PDF (ID: {file_id})",
                icon="✅",
            )
        else:
            st.info(
                "💬 **Chat Normal** - Conversacion general con Kimi-K2",
                icon="💭",
            )

        self.render_chat_history()
        self.handle_user_input(agent_mode, file_id)
