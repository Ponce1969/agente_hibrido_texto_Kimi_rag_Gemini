## 📊 Dashboard de Métricas

Sistema completo de análisis y visualización de métricas de uso de agentes IA.

---

## 🎯 Objetivo

Proporcionar visibilidad completa sobre:
- **Uso de agentes**: Qué agentes se usan más
- **Consumo de tokens**: Cuántos tokens se consumen
- **Costos**: Cuánto cuesta el uso de las APIs
- **Rendimiento**: Tiempos de respuesta
- **Features**: Uso de RAG y Bear API
- **Errores**: Problemas del sistema

---

## 📁 Arquitectura

### **Base de Datos: SQLite**

Archivo: `data/metrics.db`

**Tablas:**

1. **`agent_metrics`** - Métricas por consulta
   - session_id, agent_mode, model_name
   - prompt_tokens, completion_tokens, total_tokens
   - estimated_cost, response_time
   - has_rag_context, rag_chunks_used
   - used_bear_search, bear_sources_count
   - created_at

2. **`daily_metrics_summary`** - Resumen diario agregado
   - date, total_requests, total_sessions
   - total_tokens, total_cost
   - avg_response_time
   - rag_requests, bear_requests
   - agent_usage (JSON)

3. **`error_logs`** - Log de errores
   - error_type, error_message, stack_trace
   - session_id, endpoint
   - created_at

---

## 🚀 Uso

### **Acceder al Dashboard**

```bash
# Iniciar la aplicación
docker compose up -d

# Acceder al dashboard
http://localhost:8501/📊_dashboard
```

### **API de Métricas**

```bash
# Resumen general
curl http://localhost:8000/metrics/summary?days=7

# Métricas diarias
curl http://localhost:8000/metrics/daily?days=30

# Top agentes
curl http://localhost:8000/metrics/top-agents?days=7&limit=5

# Errores recientes
curl http://localhost:8000/metrics/errors?limit=10
```

---

## 📊 Visualizaciones Disponibles

### **1. KPIs Principales**
- Total de consultas
- Tokens consumidos
- Tiempo promedio de respuesta
- Porcentaje de uso de RAG

### **2. Gráficos de Distribución**
- **Pie Chart**: Uso por agente
- **Bar Chart**: Uso por modelo (Kimi vs Gemini)

### **3. Evolución Temporal**
- **Line Chart**: Consultas diarias
- **Area Chart**: Costos diarios
- Comparación RAG vs Bear API

### **4. Tablas de Análisis**
- Top agentes más usados
- Errores recientes
- Métricas de rendimiento

### **5. Análisis de Costos**
- Costo total del período
- Costo promedio por consulta
- Tokens promedio por consulta
- Proyección de costos

### **6. Uso de Features**
- Porcentaje de consultas con RAG
- Porcentaje de consultas con Bear API
- Distribución de uso

---

## 🔧 Integración con Chat Service

Para registrar métricas automáticamente, el `ChatService` debe llamar a `MetricsService`:

```python
from src.application.services.metrics_service import MetricsService

class ChatServiceV2:
    def __init__(self, ...):
        self.metrics_service = MetricsService()
    
    async def send_message(self, ...):
        start_time = time.time()
        
        # ... procesamiento del mensaje ...
        
        # Registrar métricas
        response_time = time.time() - start_time
        
        self.metrics_service.record_agent_usage(
            session_id=session_id,
            agent_mode=mode,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            response_time=response_time,
            model_name=model_name,
            has_rag_context=bool(file_id),
            rag_chunks_used=len(rag_context) if rag_context else 0,
            file_id=file_id,
            used_bear_search=used_bear,
            bear_sources_count=len(bear_sources) if bear_sources else 0
        )
```

---

## 💰 Cálculo de Costos

### **Precios por Modelo (aproximados)**

| Modelo | Input (por 1K tokens) | Output (por 1K tokens) |
|--------|----------------------|------------------------|
| **Kimi-K2** | $0.0003 | $0.0003 |
| **Gemini 2.5 Flash** | $0.00015 | $0.0006 |
| **Bear API** | Gratis (con límites) | - |

### **Fórmula de Costo**

```python
# Kimi
cost = (total_tokens / 1000) * 0.0003

# Gemini
cost = (prompt_tokens / 1000) * 0.00015 + (completion_tokens / 1000) * 0.0006
```

---

## 📈 Casos de Uso

### **1. Monitoreo de Costos**
- Ver cuánto se gasta diariamente
- Identificar picos de uso
- Proyectar costos futuros

### **2. Optimización de Uso**
- Identificar agentes más costosos
- Ver si RAG reduce tokens
- Comparar eficiencia de modelos

### **3. Análisis de Rendimiento**
- Tiempos de respuesta por agente
- Impacto de RAG en latencia
- Cuellos de botella

### **4. Debugging**
- Ver errores recientes
- Identificar patrones de fallo
- Correlacionar errores con uso

### **5. Reportes para Stakeholders**
- Métricas de adopción
- ROI del sistema
- Justificación de costos

---

## 🔄 Mantenimiento

### **Limpiar Datos Antiguos**

```python
# Script para limpiar métricas de más de 90 días
from datetime import datetime, timedelta, UTC
from sqlmodel import Session, select
from src.adapters.db.metrics_models import AgentMetrics
from src.adapters.db.database import engine

cutoff_date = datetime.now(UTC) - timedelta(days=90)

with Session(engine) as session:
    old_metrics = session.exec(
        select(AgentMetrics).where(AgentMetrics.created_at < cutoff_date)
    ).all()
    
    for metric in old_metrics:
        session.delete(metric)
    
    session.commit()
    print(f"Eliminadas {len(old_metrics)} métricas antiguas")
```

### **Backup de Métricas**

```bash
# Backup de la base de datos
cp data/metrics.db data/metrics_backup_$(date +%Y%m%d).db

# Comprimir
gzip data/metrics_backup_*.db
```

---

## 🎨 Personalización

### **Agregar Nuevas Métricas**

1. **Modificar modelo**:
```python
# En src/adapters/db/metrics_models.py
class AgentMetrics(SQLModel, table=True):
    # ... campos existentes ...
    custom_metric: Optional[float] = Field(default=None)
```

2. **Actualizar servicio**:
```python
# En src/application/services/metrics_service.py
def record_agent_usage(self, ..., custom_metric: Optional[float] = None):
    metric = AgentMetrics(
        # ... campos existentes ...
        custom_metric=custom_metric
    )
```

3. **Agregar visualización**:
```python
# En pages/4_📊_dashboard.py
st.metric("Custom Metric", value=custom_value)
```

### **Agregar Nuevos Gráficos**

```python
# Ejemplo: Gráfico de dispersión tokens vs tiempo
fig_scatter = px.scatter(
    df_metrics,
    x='total_tokens',
    y='response_time',
    color='agent_mode',
    title='Tokens vs Tiempo de Respuesta',
    labels={'total_tokens': 'Tokens', 'response_time': 'Tiempo (s)'}
)
st.plotly_chart(fig_scatter, use_container_width=True)
```

---

## 🔒 Seguridad y Privacidad

### **Datos Sensibles**

- ❌ NO se almacenan mensajes de usuarios
- ❌ NO se almacenan respuestas completas
- ✅ Solo se almacenan metadatos y métricas
- ✅ Session IDs son anónimos

### **Acceso al Dashboard**

Para producción, considera agregar autenticación:

```python
# En pages/4_📊_dashboard.py
import streamlit_authenticator as stauth

# Configurar autenticación
authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Mostrar dashboard
    ...
else:
    st.error("Acceso denegado")
```

---

## 📊 Ejemplo de Salida

### **Resumen General (7 días)**

```json
{
  "period_days": 7,
  "total_requests": 245,
  "unique_sessions": 18,
  "total_tokens": 125430,
  "total_cost_usd": 0.0523,
  "avg_response_time_seconds": 2.34,
  "agent_usage": {
    "Arquitecto Python Senior": 98,
    "Ingeniero de Código": 67,
    "Auditor de Seguridad": 45,
    "Optimizador de Rendimiento": 23,
    "Documentador Técnico": 12
  },
  "model_usage": {
    "kimi-k2": 145,
    "gemini-2.5-flash": 100
  },
  "rag_requests": 87,
  "rag_percentage": 35.5,
  "bear_requests": 23,
  "bear_percentage": 9.4
}
```

---

## 🚀 Próximas Mejoras

### **Fase 1: Básico** ✅
- [x] Registro de métricas
- [x] Dashboard con gráficos
- [x] API de consulta
- [x] Cálculo de costos

### **Fase 2: Avanzado** (Futuro)
- [ ] Alertas por umbral de costos
- [ ] Exportar reportes PDF
- [ ] Comparación entre períodos
- [ ] Predicción de costos con ML
- [ ] Integración con Grafana
- [ ] Webhooks para notificaciones

---

## 📝 Notas

- La base de datos SQLite es suficiente para hasta 100K registros
- Para mayor escala, considerar PostgreSQL
- Los costos son estimados, verificar con facturas reales
- El dashboard se actualiza en tiempo real

---

**Última actualización:** Octubre 2025  
**Mantenedor:** Equipo de desarrollo
