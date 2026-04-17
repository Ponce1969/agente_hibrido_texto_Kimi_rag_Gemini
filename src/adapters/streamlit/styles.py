"""
Estilos CSS encapsulados para la UI de Streamlit.

Principios:
- NO tocar position/float/z-index de elementos que Streamlit ya posiciona
- NO forzar anchos en sidebar (rompe el drawer en movil)
- Solo estilizar lo que Streamlit no controla: colores, padding fino, bordes
- Multiplataforma: PC y celular deben verse bien
"""

CHAT_STYLES = """
/* ===== CHAT: mensajes compactos y legibles ===== */

/* Mensajes mas compactos: menos espacio vertical entre ellos */
.stChatMessage {
    padding: 0.25rem 0.5rem !important;
}

/* Scrollbar fino para el historial de chat */
.element-container:has(.stChatMessage) {
    scrollbar-width: thin;
    scrollbar-color: #c1c7cf transparent;
}

/* ===== SIDEBAR: solo padding sutil, SIN tocar width ===== */
[data-testid="stSidebar"] .stSidebarContent {
    padding: 0.75rem !important;
}

/* ===== INDICADORES DE MODO: mas compactos ===== */
.stSuccess {
    padding: 0.4rem 0.75rem !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

.stInfo {
    padding: 0.4rem 0.75rem !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

/* ===== SEPARADORES ===== */
hr {
    margin: 0.4rem 0 !important;
}

/* ===== MOVIL: ajustes solo para pantallas chicas ===== */
@media (max-width: 768px) {
    /* Sidebar: dejar que Streamlit haga el drawer nativo */
    /* NO forzar width ni max-width - Streamlit maneja el drawer */

    /* Mensajes mas compactos en movil */
    .stChatMessage {
        padding: 0.15rem 0.25rem !important;
    }

    /* Indicadores de modo aun mas compactos */
    .stSuccess, .stInfo {
        padding: 0.3rem 0.5rem !important;
        font-size: 0.8rem !important;
    }

    /* Botones full width en movil */
    .stButton button {
        width: 100% !important;
    }
}
"""

DASHBOARD_STYLES = """
/* ===== DASHBOARD ===== */
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 600 !important;
}

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
