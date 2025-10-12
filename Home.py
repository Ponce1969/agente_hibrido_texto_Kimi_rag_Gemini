"""
Página principal del Asistente IA con RAG.
Sistema híbrido con Kimi-K2 y Gemini 2.5 Flash.
"""
import streamlit as st
import requests
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="🤖 Asistente IA con RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🤖 Asistente IA con RAG")
st.markdown("**Sistema híbrido con Kimi-K2 y Gemini 2.5 Flash**")
st.markdown("*Arquitectura hexagonal • Python 3.12+ • PostgreSQL + pgvector*")
st.markdown("---")

# Información del sistema
col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    ### 💬 Chat Normal
    - Modelo: **Kimi-K2**
    - Velocidad: Rápida
    - Uso: Consultas generales
    """)

with col2:
    st.success("""
    ### 📄 Chat con RAG
    - Modelo: **Gemini 2.5 Flash**
    - Contexto: PDFs indexados
    - Uso: Análisis de documentos
    """)

with col3:
    st.warning("""
    ### 🔍 Búsqueda Python
    - API: **Bear Search**
    - Fuentes: GitHub, docs, PEPs
    - Uso: Errores y APIs
    """)

st.markdown("---")

# Características principales
st.header("✨ Características")

col_feat1, col_feat2 = st.columns(2)

with col_feat1:
    st.markdown("""
    ### 🎯 Funcionalidades
    - ✅ **5 Agentes Especializados**
      - Arquitecto Python Senior
      - Ingeniero de Código
      - Auditor de Seguridad
      - Especialista en Bases de Datos
      - Ingeniero de Refactoring
    
    - ✅ **Sistema RAG Completo**
      - Indexación de PDFs
      - Búsqueda semántica
      - Contexto automático
    
    - ✅ **Búsqueda Inteligente**
      - Detección automática de errores
      - Fuentes Python confiables
      - Integración transparente
    """)

with col_feat2:
    st.markdown("""
    ### 🏗️ Arquitectura
    - ✅ **Hexagonal (Ports & Adapters)**
      - Dominio puro
      - Puertos bien definidos
      - Adaptadores intercambiables
    
    - ✅ **Stack Tecnológico**
      - FastAPI + SQLModel
      - PostgreSQL + pgvector
      - Streamlit + Plotly
    
    - ✅ **Calidad de Código**
      - Type hints completos
      - Tests automatizados
      - Documentación exhaustiva
    """)

st.markdown("---")

# Estado del sistema
st.header("📊 Estado del Sistema")

try:
    # Verificar backend
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        st.success("✅ **Backend:** Operativo")
    else:
        st.error("❌ **Backend:** Error")
except:
    st.error("❌ **Backend:** No disponible")

try:
    # Obtener métricas rápidas
    response = requests.get("http://localhost:8000/metrics/summary?days=1", timeout=2)
    if response.status_code == 200:
        data = response.json()
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.metric("Consultas Hoy", data.get('total_requests', 0))
        
        with col_m2:
            st.metric("Tokens Usados", f"{data.get('total_tokens', 0):,}")
        
        with col_m3:
            st.metric("Costo", f"${data.get('total_cost_usd', 0):.4f}")
        
        with col_m4:
            st.metric("Tiempo Prom.", f"{data.get('avg_response_time_seconds', 0):.1f}s")
except:
    st.info("ℹ️ Métricas no disponibles")

st.markdown("---")

# Navegación
st.header("🧭 Navegación")

st.markdown("""
### Páginas Disponibles:

1. **📊 Dashboard** - Análisis completo de métricas y uso
2. **🔍 Superagent** - Chat con búsqueda Python avanzada

Usa la barra lateral para navegar entre páginas.
""")

st.markdown("---")

# Footer
st.caption(f"""
🤖 Asistente IA con RAG v0.1.0  
📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
🏗️ Arquitectura Hexagonal • Python 3.12+
""")
