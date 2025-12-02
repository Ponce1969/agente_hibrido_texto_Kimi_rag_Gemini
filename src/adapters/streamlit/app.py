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

# CSS para fijar el chat_input abajo (estilo ChatGPT)
st.markdown("""
<style>
    /* Fijar el input del chat en la parte inferior */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem 2rem;
        background: #F5F7FA;
        border-top: 2px solid #FF4B4B;
        z-index: 999;
    }
    
    /* Estilizar el input de texto en rojo */
    .stChatInput textarea {
        background: #FFFFFF !important;
        border: 2px solid #FF4B4B !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        box-shadow: 0 2px 8px rgba(255, 75, 75, 0.15) !important;
    }
    
    /* Eliminar TODOS los efectos de focus que agrandan el input */
    .stChatInput *:focus,
    .stChatInput *:focus-visible,
    .stChatInput *:focus-within {
        outline: none !important;
        outline-width: 0 !important;
        box-shadow: 0 2px 8px rgba(255, 75, 75, 0.15) !important;
    }
    
    /* Eliminar el borde extra del contenedor de Streamlit */
    .stChatInput > div,
    .stChatInput > div > div,
    .stChatInput [data-baseweb="base-input"],
    .stChatInput [data-baseweb="textarea"] {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #666 !important;
        font-style: italic;
    }
    
    /* Botón de enviar en rojo */
    .stChatInput button {
        background: #FF4B4B !important;
        border-radius: 10px !important;
    }
    
    .stChatInput button:hover {
        background: #E03E3E !important;
    }
    
    /* Ajustar para el sidebar cuando está abierto */
    [data-testid="stSidebar"][aria-expanded="true"] ~ div .stChatInput {
        left: 21rem;
    }
    
    /* Dar espacio al contenido para que no quede tapado por el input fijo */
    .main .block-container {
        padding-bottom: 100px;
    }
</style>
""", unsafe_allow_html=True)

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


def render_dashboard():
    """Renderiza el dashboard de métricas."""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime
    from src.application.services.metrics_service import MetricsService
    
    st.title("📊 Dashboard de Métricas")
    st.markdown("**Análisis de uso de agentes IA y sistema RAG**")
    st.markdown("---")
    
    # Inicializar servicio
    from src.adapters.repositories.metrics_repository import SQLModelMetricsRepository
    from src.application.services.metrics_service import MetricsService
    metrics_repository = SQLModelMetricsRepository()
    metrics_service = MetricsService(repository=metrics_repository)
    
    # Filtro de días
    col_filter1, col_filter2 = st.columns([3, 1])
    with col_filter1:
        days_filter = st.selectbox(
            "Período de análisis",
            options=[1, 7, 14, 30],
            index=1,
            format_func=lambda x: f"Últimos {x} días"
        )
    with col_filter2:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    # Obtener datos
    summary = metrics_service.get_metrics_summary(days=days_filter)
    
    # KPIs principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Consultas", f"{summary['total_requests']:,}")
    with col2:
        st.metric("Tokens", f"{summary['total_tokens']:,}")
    with col3:
        st.metric("Costo", f"${summary['total_cost_usd']:.4f}")
    with col4:
        st.metric("Tiempo Prom.", f"{summary['avg_response_time_seconds']:.1f}s")
    
    st.markdown("---")
    
    # Gráficos
    if summary['total_requests'] > 0:
        col_left, col_right = st.columns(2)
        
        with col_left:
            if summary['agent_usage']:
                agent_df = pd.DataFrame([
                    {"Agente": k, "Consultas": v}
                    for k, v in summary['agent_usage'].items()
                ])
                fig_agents = px.pie(
                    agent_df,
                    values="Consultas",
                    names="Agente",
                    title="Uso por Agente",
                    hole=0.4
                )
                st.plotly_chart(fig_agents, use_container_width=True)
        
        with col_right:
            if summary['model_usage']:
                model_df = pd.DataFrame([
                    {"Modelo": k, "Consultas": v}
                    for k, v in summary['model_usage'].items()
                ])
                fig_models = px.bar(
                    model_df,
                    x="Modelo",
                    y="Consultas",
                    title="Uso por Modelo",
                    color="Consultas"
                )
                st.plotly_chart(fig_models, use_container_width=True)
        
        # Features
        st.markdown("---")
        col_feat1, col_feat2 = st.columns(2)
        
        with col_feat1:
            st.metric("Consultas con RAG", summary['rag_requests'], 
                     delta=f"{summary['rag_percentage']:.1f}%")
        
        with col_feat2:
            st.metric("Consultas con Bear API", summary['bear_requests'],
                     delta=f"{summary['bear_percentage']:.1f}%")
    else:
        st.info("📊 No hay métricas disponibles. Haz algunas consultas primero.")


def main():
    """Función principal de la aplicación."""
    # Inicializar servicios primero (necesarios para detectar modo)
    backend_client, session_service, file_service = initialize_services()
    
    # Inicializar componentes
    chat_interface, session_manager, pdf_manager = initialize_components(
        backend_client, session_service, file_service
    )
    
    # Inicializar session_id si no existe
    if "session_id" not in st.session_state:
        st.session_state.session_id = 0
    
    # Detectar modo RAG antes de renderizar título
    # (necesitamos saber si hay PDF seleccionado)
    temp_file_id = st.session_state.get("selected_file_id", None)
    temp_use_context = st.session_state.get("usar_pdf_contexto", False)
    is_rag_mode = temp_use_context and temp_file_id
    
    # TÍTULO DINÁMICO según modo
    if is_rag_mode:
        st.title("🔍 RAG Activado - Gemini 2.5 Flash")
        st.markdown("*Búsqueda inteligente en PDF • Embeddings 768 dims • PostgreSQL + pgvector*")
    else:
        st.title("💬 Chat Normal - Kimi-K2")
        st.markdown("*Conversación general • Arquitectura hexagonal • Python 3.12+*")
    
    # Tabs principales
    tab1, tab2 = st.tabs(["💬 Chat", "📊 Dashboard"])
    
    with tab1:
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
        
        # Debug: mostrar valores actuales
        st.sidebar.caption(f"🔍 Debug: use_context={use_context}, file_id={file_id}, final_file_id={final_file_id}")
        
        chat_interface.render_chat_section(agent_mode, final_file_id)
        
        # Footer
        st.divider()
        st.caption("🏗️ Arquitectura hexagonal • 🔍 RAG con embeddings • ⚡ Optimizado para bajos recursos")
    
    with tab2:
        render_dashboard()


if __name__ == "__main__":
    main()
