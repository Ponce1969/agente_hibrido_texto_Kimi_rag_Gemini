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
- [ ] Instalar SlowAPI
- [ ] Configurar limitador en `main.py`
- [ ] Decorar `/chat` (10/min)
- [ ] Decorar `/embeddings/index` (5/min)
- [ ] Eximir `/health`, `/docs`
- [ ] Tests de 429
- [ ] Documentar en README

### Fase 2: Argon2 🔐
- [ ] Instalar argon2-cffi
- [ ] Crear `PasswordService`
- [ ] Crear modelo `User`
- [ ] Endpoint `/register`
- [ ] Endpoint `/login`
- [ ] Tests de hashing
- [ ] Migración desde Bcrypt (si aplica)

### Fase 3: JWT (Futuro) 🎫
- [ ] Instalar python-jose
- [ ] Crear `JWTService`
- [ ] Generación de tokens
- [ ] Validación de tokens
- [ ] Middleware de auth

### Fase 4: Headers (Futuro) 🛡️
- [ ] Configurar CORS
- [ ] Security headers
- [ ] HTTPS redirect
- [ ] Trusted hosts

---

## 📊 Prioridades

1. **Crítico (Implementar Ya):**
   - ✅ Rate limiting en `/chat`
   - ✅ Argon2 para contraseñas

2. **Alto (Próxima Sprint):**
   - JWT authentication
   - Security headers

3. **Medio (Backlog):**
   - Audit logging
   - Input sanitization

---

## 🔗 Referencias

- [SlowAPI Docs](https://slowapi.readthedocs.io/)
- [Argon2 RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Documento creado:** 2025-10-12  
**Próxima revisión:** Al implementar Fase 1
