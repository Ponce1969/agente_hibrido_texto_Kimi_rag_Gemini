# 🔒 Deshabilitar Swagger UI en Producción

## ✅ Cambios Implementados

Se agregó detección automática de entorno para deshabilitar Swagger UI en producción por seguridad.

### Archivos Modificados:
- `src/adapters/config/settings.py` - Nueva variable `ENVIRONMENT`
- `src/main.py` - Deshabilitar `/docs`, `/redoc` y `/openapi.json` en producción
- `.env.example` - Documentación de la nueva variable

---

## 🚀 Instrucciones de Deploy en OrangePi 5

### 1. Conectar al servidor por SSH
```bash
ssh usuario@orangepi5
```

### 2. Ir al directorio del proyecto
```bash
cd /ruta/al/proyecto/agente_hibrido_texto_Kimi_rag_Gemini
```

### 3. Hacer pull de los cambios
```bash
git pull origin main
```

### 4. Agregar variable de entorno al .env
```bash
nano .env
```

Agregar al inicio del archivo:
```bash
# Entorno (production deshabilita Swagger)
ENVIRONMENT=production
```

Guardar con `Ctrl+O`, `Enter`, `Ctrl+X`

### 5. Reiniciar el servicio
```bash
# Si usas systemd
sudo systemctl restart tu-servicio-api

# O si usas docker
docker-compose restart backend

# O si usas uvicorn directamente
pkill -f uvicorn
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## ✅ Verificación

### Swagger UI debe estar deshabilitado:
```bash
curl https://swagger-rag.loquinto.com/docs
# Debe devolver: {"detail":"Not Found"}
```

### El CLI debe seguir funcionando:
```bash
# En tu máquina local
python cli.py "test de conexión"
# Debe funcionar normalmente
```

### El endpoint /health debe funcionar:
```bash
curl https://swagger-rag.loquinto.com/api/v1/health
# Debe devolver: {"api":"ok","timestamp":"..."}
```

---

## 🔧 Desarrollo Local

Si quieres habilitar Swagger en tu máquina local para desarrollo:

```bash
# En tu .env local
ENVIRONMENT=development
```

Luego Swagger estará disponible en:
- http://localhost:8000/docs
- http://localhost:8000/redoc

---

## 🔐 Seguridad

**Antes (vulnerable):**
- ❌ Cualquiera podía ver `/docs` y probar endpoints
- ❌ Swagger UI expuesto públicamente

**Después (seguro):**
- ✅ Swagger UI deshabilitado en producción
- ✅ CLI sigue funcionando normalmente (usa `/api/internal/llm-gateway`)
- ✅ Solo endpoints de API disponibles, sin documentación pública

---

## 📝 Notas Importantes

1. **El CLI NO se ve afectado** - No usa `/docs`, usa los endpoints directamente
2. **Los endpoints siguen funcionando** - Solo se deshabilita la UI de documentación
3. **Puedes revertir** - Cambia `ENVIRONMENT=development` si necesitas ver Swagger temporalmente
4. **Seguridad adicional** - Considera agregar Cloudflare Access si necesitas acceso ocasional a `/docs`
