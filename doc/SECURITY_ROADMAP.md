# 🔒 Roadmap de Seguridad para FastAPI

Guía completa para implementar seguridad profesional en el sistema de agentes IA.

---

## 📋 Índice

1. [Rate Limiting con SlowAPI](#1-rate-limiting-con-slowapi)
2. [Hashing de Contraseñas con Argon2](#2-hashing-de-contraseñas-con-argon2)
3. [Checklist de Implementación](#checklist-de-implementación)

---

## 1. Rate Limiting con SlowAPI

### 🎯 Objetivo
Proteger los endpoints que consumen tokens de LLMs contra abuso y ataques DDoS.

### 📦 Instalación

```bash
# Agregar a pyproject.toml
uv add slowapi
```

### 🔧 Implementación

#### **Paso 1: Configurar en main.py**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

#### **Paso 2: Decorar Endpoints**

```python
@router.post("/chat")
@limiter.limit("10/minute")  # 10 requests por minuto
async def chat_endpoint(request: Request, ...):
    pass
```

#### **Paso 3: Configuración por Tipo**

| Endpoint | Límite | Razón |
|----------|--------|-------|
| `/chat` | 10/min | Consume tokens LLM |
| `/embeddings/index` | 5/min | Muy costoso |
| `/metrics` | 100/min | Barato |
| `/health` | Sin límite | Monitoreo |

#### **Paso 4: Tests**

```python
def test_rate_limit():
    for i in range(11):
        response = client.post("/api/v1/chat", json={...})
        if i < 10:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
```

---

## 2. Hashing de Contraseñas con Argon2

### 🎯 Objetivo
Usar el algoritmo más seguro y moderno para proteger contraseñas.

### 🏆 ¿Por Qué Argon2?

| Característica | Bcrypt | **Argon2id** |
|----------------|--------|--------------|
| Resistencia GPU | ⚠️ Media | ✅ Alta |
| Memory-hard | ⚠️ Parcial | ✅ Sí |
| Estándar oficial | ✅ Bueno | ✅ **Mejor** |
| Recomendado 2025 | ⚠️ Aceptable | ✅ **Sí** |

**Ventajas:**
- ✅ Ganador Password Hashing Competition
- ✅ Estándar IETF RFC 9106
- ✅ Memory-hard (dificulta GPU/ASIC)
- ✅ Configurable (tiempo, memoria, paralelismo)

### 📦 Instalación

```bash
uv add argon2-cffi
```

### 🔧 Implementación

#### **Paso 1: Servicio de Hashing**

```python
# src/application/services/password_service.py
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

class PasswordService:
    def __init__(self):
        self.ph = PasswordHasher(
            time_cost=3,        # Iteraciones
            memory_cost=65536,  # 64 MB
            parallelism=4,      # Threads
            hash_len=32,
            salt_len=16
        )
    
    def hash_password(self, password: str) -> str:
        return self.ph.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            self.ph.verify(hashed, password)
            return True
        except VerifyMismatchError:
            return False
```

#### **Paso 2: Endpoint de Registro**

```python
@router.post("/register")
async def register(
    email: EmailStr,
    password: str,
    password_service: PasswordService = Depends()
):
    hashed = password_service.hash_password(password)
    user = await create_user(email, hashed)
    return user
```

#### **Paso 3: Endpoint de Login**

```python
@router.post("/login")
async def login(
    email: EmailStr,
    password: str,
    password_service: PasswordService = Depends()
):
    user = await get_user_by_email(email)
    if not password_service.verify_password(password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_jwt(user)}
```

#### **Paso 4: Tests**

```python
def test_hash_password():
    service = PasswordService()
    hashed = service.hash_password("test123")
    assert hashed.startswith("$argon2id$")
    assert service.verify_password("test123", hashed)
    assert not service.verify_password("wrong", hashed)
```

---

## 📋 Checklist de Implementación

### Fase 1: Rate Limiting ⏱️
- [x] Instalar SlowAPI
- [x] Configurar limitador en `main.py`
- [x] Decorar `/chat` (10/min)
- [x] Decorar `/embeddings/index` (5/min)
- [x] Eximir `/health`, `/docs`
- [x] Tests de 429
- [x] Documentar en README

### Fase 2: Argon2 🔐
- [x] Instalar argon2-cffi
- [x] Crear `PasswordService` (con arquitectura hexagonal)
- [x] Crear modelo `User`
- [x] Endpoint `/register`
- [x] Endpoint `/login`
- [x] Tests de hashing
- [x] Arquitectura hexagonal implementada

### Fase 3: JWT 🎫
- [x] Instalar python-jose
- [x] Crear `JWTService` (JWTTokenService con arquitectura hexagonal)
- [x] Generación de tokens
- [x] Validación de tokens
- [ ] Middleware de auth (próximo paso recomendado)

### Fase 4: Headers 🛡️
- [x] Configurar CORS (mejorado con dominios específicos)
- [ ] Security headers adicionales (CSP, X-Frame-Options)
- [ ] HTTPS redirect (Cloudflare Tunnel ya maneja esto)
- [ ] Trusted hosts

---

## 📊 Prioridades

1. **✅ Crítico (COMPLETADO):**
   - ✅ Rate limiting en `/chat` y `/embeddings/index`
   - ✅ Argon2 para contraseñas
   - ✅ JWT authentication
   - ✅ CORS mejorado
   - ✅ Endpoints de registro/login
   - ✅ Tests de seguridad

2. **Alto (Próxima Sprint):**
   - [ ] Middleware de autenticación para proteger endpoints
   - [ ] Security headers adicionales (CSP, X-Frame-Options)
   - [ ] Implementar roles y permisos (RBAC)

3. **Medio (Backlog):**
   - [ ] Audit logging de eventos de seguridad
   - [ ] Input sanitization avanzado
   - [ ] 2FA (autenticación de dos factores)
   - [ ] Rate limiting por usuario autenticado

---

## 🔗 Referencias

- [SlowAPI Docs](https://slowapi.readthedocs.io/)
- [Argon2 RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

## ✅ Estado de Implementación

**Fases 1-3: COMPLETADAS** (2025-10-13)

Todas las funcionalidades críticas de seguridad han sido implementadas siguiendo **arquitectura hexagonal**:

- ✅ Rate Limiting con SlowAPI
- ✅ Hashing Argon2 con puertos e implementaciones
- ✅ JWT con arquitectura desacoplada
- ✅ Endpoints de autenticación funcionales
- ✅ Tests automatizados
- ✅ Documentación completa

**Documentos relacionados:**
- `SECURITY_IMPLEMENTATION.md` - Guía detallada de implementación
- `SECURITY_SUMMARY.md` - Resumen ejecutivo
- `tests/test_security.py` - Suite de tests

---

**Documento creado:** 2025-10-12  
**Última actualización:** 2025-10-13  
**Estado:** ✅ Fases críticas completadas
