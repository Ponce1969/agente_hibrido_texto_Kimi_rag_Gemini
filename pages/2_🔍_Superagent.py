"""Página de SuperAgent con búsqueda Python especializada."""
import asyncio
import streamlit as st
from src.adapters.dependencies import get_chat_service
from src.domain.models import ChatSessionCreate

# Configuración de página
st.set_page_config(
    page_title="🦸‍♂️ SuperAgent Kimi-k2",
    page_icon="🦸‍♂️",
    layout="wide"
)

# Título principal
st.title("🦸‍♂️ SuperAgent Kimi-k2")
st.markdown("**Habilitá búsqueda en fuentes Python confiables cuando Kimi lo necesite.**")

# Sidebar con información
with st.sidebar:
    st.header("ℹ️ Información")
    st.info(
        "Este agente solo busca en Internet cuando:\n"
        "• No puede resolver con su conocimiento local\n"
        "• Es una consulta específica de Python\n"
        "• Hay tracebacks o errores de código\n"
        "• Preguntas sobre APIs específicas"
    )
    
    st.header("🔍 Fuentes permitidas")
    st.markdown(
        "✅ **GitHub**\n"
        "✅ **docs.python.org**\n"
        "✅ **PEPs**\n"
        "✅ **Real Python**\n"
        "✅ **Stack Overflow**\n"
        "✅ **PyPI**\n"
        "✅ **UV (Astral)**\n"
        "❌ **Clima, noticias, temas generales**"
    )

# Estado de sesión
if "session_id" not in st.session_state:
    st.session_state.session_id = "0"
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = "architect"

# Selector de agente
agent_modes = {
    "architect": "🏗️ Arquitecto Python",
    "code_generator": "👨‍💻 Ingeniero de Código", 
    "security_analyst": "🔒 Auditor de Seguridad",
    "database_specialist": "🗄️ Especialista DB",
    "refactor_engineer": "🔄 Ingeniero de Refactoring"
}

st.session_state.agent_mode = st.selectbox(
    "🎯 **Seleccionar agente especializado:**",
    options=list(agent_modes.keys()),
    format_func=lambda x: agent_modes[x],
    key="agent_selector"
)

# Toggle de superpoderes
use_internet = st.checkbox(
    "🔍 **Permitir búsqueda en Internet (solo fuentes Python)**",
    value=True,
    help="Kimi consultará GitHub, docs.python.org, PEPs, etc. solo cuando no tenga la respuesta local."
)

# Selector de profundidad
search_depth = st.radio(
    "📊 **Profundidad de búsqueda**",
    ["Rápido (3 fuentes)", "Normal (5 fuentes)", "Profundo (8 fuentes)"],
    horizontal=True,
    index=1  # Normal por defecto
)

depth_map = {"Rápido (3 fuentes)": 3, "Normal (5 fuentes)": 5, "Profundo (8 fuentes)": 8}

# Separador
st.markdown("---")

# Área de chat
chat_container = st.container()

# Inicializar servicio de chat
@st.cache_resource
def get_cached_service():
    return get_chat_service()

service = get_cached_service()

# Función asíncrona para manejar mensajes
async def handle_chat_message(user_input: str) -> str:
    """Maneja el mensaje del usuario con opción de búsqueda."""
    try:
        response = await service.handle_message(
            session_id=st.session_state.session_id,
            user_message=user_input,
            agent_mode=st.session_state.agent_mode,
            use_internet=use_internet
        )
        return response
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Mostrar fuentes si se usó búsqueda
            if message["role"] == "assistant" and hasattr(service, 'last_search_sources'):
                sources = service.last_search_sources
                if sources:
                    st.info(f"🔍 Kimi consultó {len(sources)} fuentes de Internet")
                    with st.expander("Ver fuentes"):
                        for source in sources:
                            st.markdown(
                                f"- **[{source.title}]({source.url})**"
                                f" ({source.source_type}, confiabilidad: {source.reliability}/10)"
                            )

# Input de chat
user_input = st.chat_input("💬 Escribí tu consulta sobre Python...")

if user_input:
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Procesar respuesta
    with st.chat_message("assistant"):
        with st.spinner(
            "Pensando..." if not use_internet 
            else "Pensando... (o buscando si es necesario)"
        ):
            response = asyncio.run(handle_chat_message(user_input))
            st.markdown(response)
            
            # Mostrar si se usó búsqueda
            if hasattr(service, 'last_search_sources'):
                sources = service.last_search_sources
                if sources:
                    st.info(f"🔍 Kimi consultó {len(sources)} fuentes de Internet")
                    with st.expander("Ver fuentes"):
                        for source in sources:
                            st.markdown(
                                f"- **[{source.title}]({source.url})**"
                                f" ({source.source_type}, confiabilidad: {source.reliability}/10)"
                            )
    
    # Agregar respuesta al historial
    st.session_state.messages.append({"role": "assistant", "content": response})

# Botones de control
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

with col2:
    if st.button("🔄 Nueva sesión", use_container_width=True):
        st.session_state.session_id = "0"
        st.session_state.messages = []
        st.rerun()

with col3:
    if st.button("📋 Ejemplos de uso", use_container_width=True):
        st.info(
            "**Prueba estas consultas:**\n\n"
            "• `ImportError: cannot import name 'BaseSettings' from 'pydantic'`\n"
            "• `¿Cómo uso asyncio.create_task()?`\n"
            "• `AttributeError: 'NoneType' object has no attribute 'split'`\n"
            "• `¿Qué es un decorator en Python?`\n\n"
            "**Y estas NO deberían buscar en Internet:**\n\n"
            "• `¿Qué temperatura hay en Montevideo?`\n"
            "• `Hora actual en Uruguay`\n"
            "• `Precio del dólar hoy`"
        )

# Footer
st.markdown("---")
st.caption("💡 **Tip:** El agente solo busca en Internet cuando realmente necesita información actualizada sobre Python.")
