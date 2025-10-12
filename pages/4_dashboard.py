"""Dashboard de métricas de agentes IA."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from src.application.services.metrics_service import MetricsService

# Configuración de página
st.set_page_config(
    page_title="📊 Dashboard de Métricas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Dashboard de Métricas")
st.markdown("**Análisis de uso de agentes IA y sistema RAG**")
st.markdown("---")

# Inicializar servicio
metrics_service = MetricsService()

# Sidebar con filtros
with st.sidebar:
    st.header("⚙️ Configuración")
    
    days_filter = st.selectbox(
        "Período de análisis",
        options=[7, 14, 30, 60, 90],
        index=0,
        format_func=lambda x: f"Últimos {x} días"
    )
    
    st.divider()
    
    st.info("""
    **Métricas disponibles:**
    - Uso de agentes
    - Tokens consumidos
    - Costos estimados
    - Tiempos de respuesta
    - Uso de RAG y Bear API
    """)

# Obtener datos
summary = metrics_service.get_metrics_summary(days=days_filter)
daily_metrics = metrics_service.get_daily_metrics(days=days_filter)
top_agents = metrics_service.get_top_agents(days=days_filter)
recent_errors = metrics_service.get_recent_errors(limit=5)

# KPIs principales
st.header("📈 Resumen General")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total de Consultas",
        value=f"{summary['total_requests']:,}",
        delta=f"{summary['unique_sessions']} sesiones"
    )

with col2:
    st.metric(
        label="Tokens Consumidos",
        value=f"{summary['total_tokens']:,}",
        delta=f"${summary['total_cost_usd']:.4f} USD"
    )

with col3:
    st.metric(
        label="Tiempo Promedio",
        value=f"{summary['avg_response_time_seconds']:.2f}s",
        delta="Por respuesta"
    )

with col4:
    rag_pct = summary['rag_percentage']
    st.metric(
        label="Uso de RAG",
        value=f"{rag_pct:.1f}%",
        delta=f"{summary['rag_requests']} consultas"
    )

st.divider()

# Gráficos principales
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🤖 Uso por Agente")
    
    if summary['agent_usage']:
        agent_df = pd.DataFrame([
            {"Agente": k, "Consultas": v}
            for k, v in summary['agent_usage'].items()
        ])
        
        fig_agents = px.pie(
            agent_df,
            values="Consultas",
            names="Agente",
            title="Distribución de Consultas por Agente",
            hole=0.4
        )
        fig_agents.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_agents, use_container_width=True)
    else:
        st.info("No hay datos de uso de agentes en este período")

with col_right:
    st.subheader("🔧 Uso por Modelo")
    
    if summary['model_usage']:
        model_df = pd.DataFrame([
            {"Modelo": k, "Consultas": v}
            for k, v in summary['model_usage'].items()
        ])
        
        fig_models = px.bar(
            model_df,
            x="Modelo",
            y="Consultas",
            title="Consultas por Modelo de IA",
            color="Consultas",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_models, use_container_width=True)
    else:
        st.info("No hay datos de uso de modelos en este período")

st.divider()

# Gráfico de evolución temporal
st.subheader("📅 Evolución Temporal")

if daily_metrics:
    df_daily = pd.DataFrame(daily_metrics)
    
    # Crear gráfico con múltiples métricas
    fig_timeline = go.Figure()
    
    fig_timeline.add_trace(go.Scatter(
        x=df_daily['date'],
        y=df_daily['requests'],
        name='Consultas',
        mode='lines+markers',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig_timeline.add_trace(go.Scatter(
        x=df_daily['date'],
        y=df_daily['rag_requests'],
        name='Consultas RAG',
        mode='lines+markers',
        line=dict(color='#2ca02c', width=2)
    ))
    
    fig_timeline.add_trace(go.Scatter(
        x=df_daily['date'],
        y=df_daily['bear_requests'],
        name='Consultas Bear API',
        mode='lines+markers',
        line=dict(color='#ff7f0e', width=2)
    ))
    
    fig_timeline.update_layout(
        title="Evolución Diaria de Consultas",
        xaxis_title="Fecha",
        yaxis_title="Cantidad de Consultas",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("No hay datos históricos disponibles")

st.divider()

# Tabla de top agentes
col_table1, col_table2 = st.columns(2)

with col_table1:
    st.subheader("🏆 Top Agentes")
    
    if top_agents:
        top_df = pd.DataFrame(top_agents)
        top_df.columns = ["Agente", "Uso", "Tokens", "Tiempo Prom."]
        st.dataframe(
            top_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay datos de agentes")

with col_table2:
    st.subheader("⚠️ Errores Recientes")
    
    if recent_errors:
        errors_df = pd.DataFrame(recent_errors)
        errors_df = errors_df[['type', 'message', 'endpoint']]
        errors_df.columns = ["Tipo", "Mensaje", "Endpoint"]
        st.dataframe(
            errors_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No hay errores recientes")

st.divider()

# Métricas de costos
st.subheader("💰 Análisis de Costos")

col_cost1, col_cost2, col_cost3 = st.columns(3)

with col_cost1:
    st.metric(
        label="Costo Total",
        value=f"${summary['total_cost_usd']:.4f}",
        delta=f"{days_filter} días"
    )

with col_cost2:
    if summary['total_requests'] > 0:
        cost_per_request = summary['total_cost_usd'] / summary['total_requests']
        st.metric(
            label="Costo por Consulta",
            value=f"${cost_per_request:.6f}",
            delta="Promedio"
        )
    else:
        st.metric(label="Costo por Consulta", value="$0.00")

with col_cost3:
    if summary['total_requests'] > 0:
        tokens_per_request = summary['total_tokens'] / summary['total_requests']
        st.metric(
            label="Tokens por Consulta",
            value=f"{tokens_per_request:.0f}",
            delta="Promedio"
        )
    else:
        st.metric(label="Tokens por Consulta", value="0")

# Gráfico de costos diarios
if daily_metrics:
    st.subheader("💸 Evolución de Costos")
    
    df_costs = pd.DataFrame(daily_metrics)
    
    fig_costs = px.area(
        df_costs,
        x='date',
        y='cost',
        title="Costos Diarios (USD)",
        labels={'cost': 'Costo (USD)', 'date': 'Fecha'}
    )
    fig_costs.update_traces(fill='tozeroy', line_color='#d62728')
    
    st.plotly_chart(fig_costs, use_container_width=True)

st.divider()

# Features usage
st.subheader("🎯 Uso de Funcionalidades")

col_feat1, col_feat2 = st.columns(2)

with col_feat1:
    # RAG usage
    rag_data = pd.DataFrame({
        'Tipo': ['Con RAG', 'Sin RAG'],
        'Cantidad': [
            summary['rag_requests'],
            summary['total_requests'] - summary['rag_requests']
        ]
    })
    
    fig_rag = px.pie(
        rag_data,
        values='Cantidad',
        names='Tipo',
        title='Uso de RAG (Contexto de PDFs)',
        color_discrete_sequence=['#2ca02c', '#d3d3d3']
    )
    st.plotly_chart(fig_rag, use_container_width=True)

with col_feat2:
    # Bear API usage
    bear_data = pd.DataFrame({
        'Tipo': ['Con Bear API', 'Sin Bear API'],
        'Cantidad': [
            summary['bear_requests'],
            summary['total_requests'] - summary['bear_requests']
        ]
    })
    
    fig_bear = px.pie(
        bear_data,
        values='Cantidad',
        names='Tipo',
        title='Uso de Bear API (Búsquedas Python)',
        color_discrete_sequence=['#ff7f0e', '#d3d3d3']
    )
    st.plotly_chart(fig_bear, use_container_width=True)

st.divider()

# Footer con información
st.caption(f"""
📊 Dashboard actualizado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
📁 Base de datos: SQLite (metrics.db)  
🔄 Los datos se actualizan en tiempo real con cada consulta
""")
