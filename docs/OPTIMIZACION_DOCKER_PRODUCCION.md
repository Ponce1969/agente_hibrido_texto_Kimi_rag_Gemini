# 🚀 Plan de Optimización Docker para Producción

**Fecha**: 14 de Diciembre, 2025  
**Objetivo**: Reducir tamaño de imágenes de ~4.2GB a ~1.5GB y consumo de RAM de ilimitado a ~2.3GB máximo

---

## 📊 Estado Actual (Baseline)

### Tamaño de Imágenes
- **Backend**: 4.22GB (11.9GB en disco)
- **Frontend**: 4.22GB (11.9GB en disco)
- **PostgreSQL**: 185MB (723MB en disco)
- **Total**: ~8.6GB

### Consumo de RAM Actual
- **Backend**: ~342MB (sin límite)
- **Frontend**: ~50MB (sin límite)
- **PostgreSQL**: ~66MB (sin límite)
- **Total**: ~458MB actual, pero puede crecer sin control

---

## 🎯 Objetivos de Optimización

### Tamaño de Imágenes (Meta)
- **Backend**: ~1.5GB (-64% reducción)
- **Frontend**: ~1.5GB (-64% reducción)
- **PostgreSQL**: 185MB (sin cambios)
- **Total**: ~3.2GB (-63% reducción)

### Límites de RAM (Meta)
- **Backend**: Máx 1GB, Min 512MB
- **Frontend**: Máx 768MB, Min 256MB
- **PostgreSQL**: Máx 512MB, Min 128MB
- **Total**: ~2.3GB máximo garantizado

---

## 📋 Plan de Trabajo para Mañana

### Fase 1: Optimización de Imágenes Docker (2-3 horas)

#### ✅ Archivos ya creados:
- `Dockerfile.prod` - Dockerfile optimizado
- `docker-compose.prod.yml` - Compose con límites de recursos

#### 🔧 Tareas pendientes:

1. **Separar imágenes Backend y Frontend** (30 min)
   - Crear `Dockerfile.backend`
   - Crear `Dockerfile.frontend`
   - Cada uno con solo las dependencias necesarias

2. **Optimizar dependencias Python** (1 hora)
   - Revisar `pyproject.toml` y eliminar dependencias no usadas
   - Identificar paquetes pesados:
     - `sentence-transformers` (~1.5GB con modelos)
     - `torch` (si no se usa directamente)
     - `transformers` (si no se usa directamente)
   - Considerar usar embeddings API en lugar de local

3. **Implementar .dockerignore** (15 min)
   - Excluir archivos innecesarios del contexto de build
   - Reducir tiempo de build y tamaño de contexto

4. **Optimizar capas Docker** (30 min)
   - Combinar comandos RUN para reducir capas
   - Usar multi-stage builds eficientemente
   - Limpiar caches en cada capa

5. **Probar y medir resultados** (30 min)
   ```bash
   docker compose -f docker-compose.prod.yml build --no-cache
   docker images
   docker stats --no-stream
   ```

---

### Fase 2: Configuración de Límites de Recursos (1 hora)

#### 🔧 Tareas:

1. **Ajustar límites de memoria** (20 min)
   - Probar con límites conservadores
   - Monitorear comportamiento bajo carga
   - Ajustar según necesidad real

2. **Configurar swap y OOM killer** (20 min)
   - Configurar comportamiento ante falta de memoria
   - Prevenir que un contenedor mate a otros

3. **Optimizar PostgreSQL** (20 min)
   - Ajustar `shared_buffers`, `work_mem`, `max_connections`
   - Configurar para el hardware disponible del servidor

---

### Fase 3: Optimizaciones Adicionales (1-2 horas)

#### 🔧 Tareas opcionales:

1. **Implementar caché de dependencias** (30 min)
   - Usar BuildKit cache mounts
   - Acelerar rebuilds futuros

2. **Comprimir imágenes** (30 min)
   - Usar `docker-slim` o `dive` para analizar
   - Eliminar archivos innecesarios

3. **Configurar logging eficiente** (20 min)
   - Limitar tamaño de logs
   - Rotar logs automáticamente

4. **Implementar health checks optimizados** (20 min)
   - Reducir frecuencia si es necesario
   - Optimizar comandos de health check

---

## 🛠️ Comandos Útiles para Mañana

### Construcción y Pruebas
```bash
# Construir imágenes optimizadas
docker compose -f docker-compose.prod.yml build --no-cache

# Ver tamaño de imágenes
docker images | grep agente_hibrido

# Iniciar con límites de recursos
docker compose -f docker-compose.prod.yml up -d

# Monitorear recursos en tiempo real
docker stats

# Ver logs de un contenedor
docker compose -f docker-compose.prod.yml logs -f backend
```

### Análisis y Debug
```bash
# Analizar capas de una imagen
docker history agente_hibrido_texto_kimi_rag_gemini-backend:latest

# Inspeccionar uso de recursos
docker inspect agente_hibrido_texto_kimi_rag_gemini-backend-1 | grep -A 20 Resources

# Verificar health checks
docker inspect --format='{{json .State.Health}}' agente_hibrido_texto_kimi_rag_gemini-backend-1
```

### Limpieza
```bash
# Limpiar imágenes antiguas
docker image prune -a

# Limpiar todo (cuidado!)
docker system prune -a --volumes
```

---

## 📝 Checklist de Validación

Antes de desplegar en producción, verificar:

- [ ] Imágenes construidas correctamente
- [ ] Tamaño de imágenes reducido significativamente
- [ ] Contenedores inician correctamente
- [ ] Health checks pasan (verde)
- [ ] Aplicación funciona correctamente
- [ ] Límites de RAM respetados
- [ ] No hay OOM kills bajo carga normal
- [ ] Logs funcionan correctamente
- [ ] Backups de base de datos funcionan
- [ ] Tiempo de inicio aceptable (<2 min)

---

## 🎓 Recursos y Referencias

### Herramientas Útiles
- **dive**: Analizar capas de imágenes Docker
- **docker-slim**: Reducir tamaño de imágenes automáticamente
- **ctop**: Monitoreo de contenedores en tiempo real
- **lazydocker**: TUI para gestionar Docker

### Documentación
- [Docker Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Compose resource limits](https://docs.docker.com/compose/compose-file/deploy/)
- [Python Docker best practices](https://pythonspeed.com/docker/)

---

## 💡 Notas Importantes

### Dependencias Pesadas Identificadas
1. **sentence-transformers** (~1.5GB)
   - Incluye modelos de ML pre-entrenados
   - Considerar usar API de embeddings en su lugar
   - O descargar modelos bajo demanda

2. **torch/transformers** (~800MB)
   - Solo necesario si se usan modelos locales
   - Evaluar si realmente se necesita

3. **Streamlit** (~200MB)
   - Solo necesario en frontend
   - Separar imagen backend/frontend

### Estrategias de Optimización
1. **Separación de concerns**: Backend y Frontend en imágenes distintas
2. **Lazy loading**: Cargar modelos solo cuando se necesitan
3. **API externa**: Usar APIs de embeddings en lugar de modelos locales
4. **Cache inteligente**: Cachear dependencias entre builds

---

## 🚦 Criterios de Éxito

### Mínimo Viable
- ✅ Reducción de 50% en tamaño de imágenes
- ✅ Límites de RAM configurados y respetados
- ✅ Aplicación funcional en producción

### Objetivo Ideal
- 🎯 Reducción de 60-70% en tamaño de imágenes
- 🎯 Consumo de RAM <2GB bajo carga normal
- 🎯 Tiempo de inicio <90 segundos
- 🎯 Costo de servidor reducido en 40-50%

---

## 📅 Timeline Estimado

| Fase | Tiempo | Prioridad |
|------|--------|-----------|
| Separar imágenes Backend/Frontend | 30 min | Alta |
| Optimizar dependencias | 1 hora | Alta |
| Implementar .dockerignore | 15 min | Media |
| Optimizar capas Docker | 30 min | Media |
| Configurar límites de recursos | 1 hora | Alta |
| Pruebas y validación | 1 hora | Alta |
| Optimizaciones adicionales | 1-2 horas | Baja |

**Total estimado**: 4-6 horas

---

## ✅ Estado Actual del Proyecto

### Completado Hoy (14 Dic)
- ✅ Health checks de Docker funcionando (curl instalado)
- ✅ Respuestas RAG optimizadas (max_tokens: 4096)
- ✅ Contexto RAG optimizado (límite 6000 tokens)
- ✅ Prompts mejorados con estructura y referencias
- ✅ Archivos base creados: `Dockerfile.prod`, `docker-compose.prod.yml`

### Pendiente para Mañana
- ⏳ Implementar optimizaciones de Docker
- ⏳ Probar en entorno de producción
- ⏳ Documentar proceso de deployment
- ⏳ Configurar monitoreo de recursos

---

**Preparado por**: Cascade AI  
**Última actualización**: 14 de Diciembre, 2025 - 01:17 AM
