"""
Estilos CSS encapsulados para la UI de Streamlit.

Inyecta CSS con selectores específicos para evitar cascada global.
Todos los selectores usan clases específicas de Streamlit o data attributes
para minimizar colisiones con otros componentes.
"""

CHAT_STYLES = """
/* ===== LAYOUT FIJO: Chat messages scroll + Input fijo abajo ===== */

/* Contenedor principal del chat: ocupa todo el viewport disponible */
[data-testid="stMainBlockContainer"] {
    padding-bottom: 0 !important;
}

/* Hacer que el area de mensajes sea scrollable con altura fija
   El input queda fijado abajo del viewport gracias a st.chat_input */
.stChatFloatingInputContainer {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 999 !important;
    background: var(--streamlit-background-color, #ffffff) !important;
    border-top: 1px solid var(--streamlit-secondary-background-color, #f0f2f6) !important;
    padding: 0.75rem 1rem !important;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.08) !important;
}

/* Dar padding-bottom al contenedor de mensajes para que no quede
   oculto detras del input fijo */
.stChatMessageContainer {
    padding-bottom: 80px !important;
}

/* ===== SCROLLBAR MINIMALISTA ===== */
.stChatMessageContainer::-webkit-scrollbar {
    width: 6px;
}
.stChatMessageContainer::-webkit-scrollbar-track {
    background: transparent;
}
.stChatMessageContainer::-webkit-scrollbar-thumb {
    background: #c1c7cf;
    border-radius: 3px;
}
.stChatMessageContainer::-webkit-scrollbar-thumb:hover {
    background: #a0a6af;
}

/* ===== CHAT BUBBLES ===== */

/* Mensajes del asistente */
.stChatMessage[data-testid="assistantMessage"] {
    background: var(--streamlit-secondary-background-color, #f0f2f6) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    margin: 4px 0 !important;
    max-width: 85% !important;
    margin-left: 0 !important;
}

/* Mensajes del usuario */
.stChatMessage[data-testid="userMessage"] {
    background: #e8f0fe !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    margin: 4px 0 !important;
    max-width: 85% !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}

/* Avatar del asistente */
.stChatMessage[data-testid="assistantMessage"] .stChatMessageAvatar {
    font-size: 1.2rem !important;
}

/* ===== SIDEBAR COMPACTA ===== */
[data-testid="stSidebar"] {
    max-width: 280px !important;
    min-width: 240px !important;
}

/* Reducir padding en sidebar para maximizar espacio */
[data-testid="stSidebar"] .stSidebarContent {
    padding: 1rem 0.75rem !important;
}

/* ===== INDICADORES DE MODO ===== */

/* Success container (RAG activado) - mas compacto */
.stSuccess {
    padding: 0.5rem 1rem !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
}

/* Info container (Chat normal) - mas compacto */
.stInfo {
    padding: 0.5rem 1rem !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
}

/* ===== SEPARADORES MINIMALISTAS ===== */
hr {
    margin: 0.5rem 0 !important;
    border-color: #e0e0e0 !important;
}

/* ===== RESPONSIVE: Cuando la pantalla es estrecha ===== */
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        max-width: 100% !important;
        min-width: 100% !important;
    }

    .stChatMessage[data-testid="assistantMessage"],
    .stChatMessage[data-testid="userMessage"] {
        max-width: 95% !important;
    }
}
"""

DASHBOARD_STYLES = """
/* ===== DASHBOARD STYLES ===== */

/* Metric cards con borde sutil */
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
}

/* Plotly charts responsivos */
.js-plotly-plot {
    border-radius: 8px !important;
    overflow: hidden !important;
}
"""


def inject_chat_styles() -> None:
    """Inyecta los estilos CSS del chat en la pagina."""
    import streamlit as st

    st.markdown(f"<style>{CHAT_STYLES}</style>", unsafe_allow_html=True)


def inject_dashboard_styles() -> None:
    """Inyecta los estilos CSS del dashboard en la pagina."""
    import streamlit as st

    st.markdown(f"<style>{DASHBOARD_STYLES}</style>", unsafe_allow_html=True)
