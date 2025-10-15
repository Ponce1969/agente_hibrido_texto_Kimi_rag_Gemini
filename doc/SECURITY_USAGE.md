# 🔒 Guía de Uso de Seguridad

## ✅ Seguridad Implementada

### **1. Rate Limiting (ACTIVO)**
Protege contra abuso y DDoS limitando requests por IP.

**Endpoints protegidos:**
- `/api/v1/chat` - 10 requests/minuto
- `/api/v1/embeddings/index` - 5 requests/minuto
- `/api/v1/auth/register` - 5 registros/hora
- `/api/v1/auth/login` - 10 intentos/minuto

### **2. Autenticación JWT (DISPONIBLE)**
Sistema de registro/login con tokens JWT.

**Endpoints disponibles:**
- `POST /api/v1/auth/register` - Registrar usuario
- `POST /api/v1/auth/login` - Iniciar sesión

### **3. Hashing Argon2 (ACTIVO)**
Contraseñas encriptadas con Argon2id (estándar OWASP).

---

## 🚀 Cómo Usar la Autenticación

### **Paso 1: Registrar un Usuario**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "MiPassword123",
    "full_name": "Juan Pérez"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ1c3VhcmlvQGV4YW1wbGUuY29tIiwiZXhwIjoxNzI5MDAwMDAwLCJpYXQiOjE3Mjg5OTY0MDB9.abc123...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "usuario@example.com",
    "full_name": "Juan Pérez",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-10-14T21:00:00"
  }
}
```

**Guarda el `access_token`** - lo necesitarás para hacer requests autenticadas.

---

### **Paso 2: Hacer Login**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "MiPassword123"
  }'
```

**Respuesta:** Igual que el registro, devuelve un nuevo token.

---

### **Paso 3: Usar el Token en Requests**

**Ejemplo SIN autenticación (funciona actualmente):**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "message": "Hola",
    "mode": "arquitecto"
  }'
```

**Ejemplo CON autenticación (cuando se proteja el endpoint):**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "session_id": 1,
    "message": "Hola",
    "mode": "arquitecto"
  }'
```

---

## 🔧 Cómo Proteger un Endpoint

### **Opción 1: Autenticación Requerida**

```python
from fastapi import APIRouter, Depends
from src.adapters.api.middleware import get_current_user

router = APIRouter()

@router.post("/chat")
async def handle_chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)  # ← Requiere autenticación
):
    """Este endpoint REQUIERE token JWT válido."""
    user_id = current_user["id"]
    user_email = current_user["email"]
    
    # Tu lógica aquí
    return {"message": f"Hola {user_email}"}
```

**Resultado:**
- ✅ Con token válido: Funciona
- ❌ Sin token: Error 401 Unauthorized
- ❌ Token inválido: Error 401 Unauthorized
- ❌ Usuario inactivo: Error 403 Forbidden

---

### **Opción 2: Autenticación Opcional**

```python
from src.adapters.api.middleware import get_current_user_optional

@router.post("/chat")
async def handle_chat(
    request: ChatRequest,
    current_user: dict | None = Depends(get_current_user_optional)  # ← Opcional
):
    """Este endpoint funciona con o sin autenticación."""
    if current_user:
        # Usuario autenticado - funcionalidades premium
        user_id = current_user["id"]
        return {"message": f"Bienvenido {current_user['email']}"}
    else:
        # Usuario anónimo - funcionalidades limitadas
        return {"message": "Bienvenido invitado (funcionalidad limitada)"}
```

---

## 📋 Estado Actual de los Endpoints

| Endpoint | Rate Limit | Autenticación | Estado |
|----------|------------|---------------|--------|
| `POST /api/v1/auth/register` | 5/hora | No requerida | ✅ Activo |
| `POST /api/v1/auth/login` | 10/min | No requerida | ✅ Activo |
| `POST /api/v1/chat` | 10/min | **No protegido** | ⚠️ Público |
| `POST /api/v1/embeddings/index` | 5/min | **No protegido** | ⚠️ Público |
| `GET /health` | Sin límite | No requerida | ✅ Público |
| `GET /docs` | Sin límite | No requerida | ✅ Público |

---

## 🛡️ Cómo Proteger Todos los Endpoints

### **Paso 1: Editar `chat.py`**

```python
# src/adapters/api/endpoints/chat.py
from src.adapters.api.middleware import get_current_user

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def handle_chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),  # ← AGREGAR ESTO
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Maneja un mensaje de chat (REQUIERE AUTENTICACIÓN)."""
    # Ahora tienes acceso a current_user["id"], current_user["email"], etc.
    ...
```

### **Paso 2: Editar `embeddings.py`**

```python
# src/adapters/api/endpoints/embeddings.py
from src.adapters.api.middleware import get_current_user

@router.post("/embeddings/index/{file_id}")
@limiter.limit("5/minute")
async def embeddings_index(
    request: Request,
    file_id: int,
    current_user: dict = Depends(get_current_user),  # ← AGREGAR ESTO
    service: FileProcessingService = Depends(get_file_processing_service_dependency),
):
    """Indexa un archivo (REQUIERE AUTENTICACIÓN)."""
    ...
```

---

## 🧪 Cómo Probar la Seguridad

### **Test 1: Rate Limiting**

```bash
# Hacer 12 requests rápidos (límite es 10/min)
for i in {1..12}; do 
  echo "Request $i:"
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/v1/chat \
    -H "Content-Type: application/json" \
    -d '{"session_id":1,"message":"test","mode":"arquitecto"}'
done
```

**Esperado:** Primeros 10 devuelven `200`, siguientes devuelven `429`.

---

### **Test 2: Autenticación**

```bash
# 1. Registrar usuario
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Usar token en request protegida (cuando se implemente)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id":1,"message":"test","mode":"arquitecto"}'
```

---

### **Test 3: Hashing de Contraseñas**

```bash
# Ver base de datos
sqlite3 data/chat_history.db "SELECT id, email, hashed_password FROM users;"
```

**Esperado:** Verás algo como:
```
1|test@test.com|$argon2id$v=19$m=65536,t=3,p=4$randomsalt$randomhash
```

La contraseña está hasheada, **NO** en texto plano.

---

## 📊 Resumen

### **✅ Lo que FUNCIONA ahora:**
1. Rate limiting en endpoints críticos
2. Sistema de registro/login con JWT
3. Contraseñas hasheadas con Argon2
4. Tokens JWT firmados y verificables

### **⚠️ Lo que FALTA (opcional):**
1. Proteger endpoints con autenticación (agregar `Depends(get_current_user)`)
2. Implementar roles y permisos (admin, user, etc.)
3. Audit logging de eventos de seguridad
4. 2FA (autenticación de dos factores)

### **🎯 Recomendación:**
Si tu aplicación es de **uso personal/interno**, el rate limiting actual es suficiente.

Si quieres **restringir acceso por usuario**, agrega `Depends(get_current_user)` a los endpoints que quieras proteger.

---

**Fecha:** 2025-10-14  
**Versión:** 1.0.0  
**Estado:** Sistema de autenticación disponible, protección de endpoints opcional
