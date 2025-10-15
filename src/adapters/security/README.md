# 🔒 Adaptadores de Seguridad

Esta carpeta contiene las implementaciones concretas de los puertos de seguridad definidos en `src/domain/ports/auth_port.py`.

## 📁 Contenido

### `argon2_hasher.py`
**Implementa**: `PasswordHasherPort`

Hasher de contraseñas usando Argon2id, el algoritmo ganador del Password Hashing Competition y recomendado por OWASP.

**Características**:
- Memory-hard (dificulta ataques GPU/ASIC)
- Salt único por contraseña
- Parámetros configurables
- Rehashing automático

**Uso**:
```python
from src.adapters.security.argon2_hasher import Argon2PasswordHasher

hasher = Argon2PasswordHasher()
hashed = hasher.hash_password("mi_contraseña")
is_valid = hasher.verify_password("mi_contraseña", hashed)
```

### `jwt_token_service.py`
**Implementa**: `TokenServicePort`

Servicio de gestión de tokens JWT para autenticación stateless.

**Características**:
- Firmado con HS256
- Expiración configurable
- Claims estándar (sub, email, exp, iat)
- Validación robusta

**Uso**:
```python
from src.adapters.security.jwt_token_service import JWTTokenService

service = JWTTokenService(secret_key="tu_clave_secreta")
token = service.create_access_token(user_id="123", email="user@example.com")
decoded = service.verify_token(token)
```

## 🏗️ Arquitectura Hexagonal

Estos adaptadores implementan las interfaces definidas en el dominio, permitiendo:

1. **Independencia del dominio**: La lógica de negocio no conoce detalles de implementación
2. **Testabilidad**: Fácil crear mocks para testing
3. **Intercambiabilidad**: Cambiar de Argon2 a Bcrypt sin tocar el dominio
4. **Mantenibilidad**: Cada adaptador tiene una responsabilidad clara

## 🔄 Flujo de Dependencias

```
Domain (Puertos)
    ↑
    │ implementa
    │
Adapters (Implementaciones)
    ↑
    │ usa
    │
Application (Servicios)
    ↑
    │ expone
    │
API (Endpoints)
```

## 🧪 Testing

Los tests se encuentran en `tests/test_security.py`:

```bash
uv run pytest tests/test_security.py -v
```

## 📚 Referencias

- [Argon2 RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
