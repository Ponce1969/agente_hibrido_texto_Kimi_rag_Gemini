# 🛠️ Scripts de Utilidad

Scripts auxiliares para desarrollo, testing y deployment del proyecto.

---

## 📋 Scripts Disponibles

### 🧹 Producción

#### `cleanup_for_production.sh`
Limpia el proyecto antes de deployment a producción.

**Uso:**
```bash
bash scripts/cleanup_for_production.sh
```

**Acciones:**
- Elimina cachés de Python (`__pycache__`, `.pytest_cache`, `.mypy_cache`)
- Organiza archivos de desarrollo
- Verifica configuración de seguridad (`.env` no en Git)
- Muestra resumen de limpieza

---

#### `clear_error_message.py`
Limpia mensajes de error en archivos indexados con status "ready".

**Uso:**
```bash
# Dentro del contenedor Docker
docker exec agentes_front_bac-backend-1 python -c "
from sqlmodel import Session, select
from src.adapters.db.database import engine
from src.adapters.db.file_models import FileUpload
from datetime import datetime, UTC

with Session(engine) as session:
    statement = select(FileUpload).where(
        FileUpload.status.in_(['ready', 'indexed']),
        FileUpload.error_message.isnot(None)
    )
    files = session.exec(statement).all()
    
    for file in files:
        file.error_message = None
        file.updated_at = datetime.now(UTC)
        session.add(file)
    
    session.commit()
    print(f'✅ Limpiados {len(files)} archivo(s)')
"
```

---

### 🏗️ Desarrollo

#### `check_hexagonal_architecture.py`
Verifica que el proyecto respete los principios de arquitectura hexagonal.

**Uso:**
```bash
uv run python scripts/check_hexagonal_architecture.py
```

**Verifica:**
- ✅ Pureza del dominio (no importa adapters/infrastructure)
- ✅ Dirección de dependencias (Application no importa Adapters)
- ✅ Ubicación de puertos (deben estar en `domain/ports/`)
- ✅ Ubicación de modelos (deben estar en `domain/models/`)
- ✅ Fuga de frameworks (FastAPI, SQLModel solo en adapters)

**Salida:**
- ❌ Errores críticos (deben corregirse)
- ⚠️ Advertencias (mejoras recomendadas)
- ℹ️ Información (sugerencias menores)

---

#### `cleanup_project.py`
Analiza el proyecto buscando archivos a limpiar.

**Uso:**
```bash
uv run python scripts/cleanup_project.py
```

**Identifica:**
- Archivos de caché
- Archivos de desarrollo mal ubicados
- Backups obsoletos
- Carpetas vacías
- Archivos temporales

---

## 📊 Integración con CI/CD

### GitHub Actions

Puedes integrar estos scripts en tu pipeline de CI/CD:

```yaml
# .github/workflows/architecture-check.yml
name: Architecture Check

on: [push, pull_request]

jobs:
  check-architecture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Check Architecture
        run: uv run python scripts/check_hexagonal_architecture.py
```

---

## 🔒 Seguridad

**IMPORTANTE:** Estos scripts NO contienen credenciales ni información sensible.

- ✅ Seguros para subir a GitHub
- ✅ No acceden a `.env`
- ✅ Solo leen código fuente y estructura

---

## 📝 Contribuir

Si creas un nuevo script:

1. Agrégalo a este README
2. Documenta su propósito y uso
3. Incluye ejemplos de ejecución
4. Indica si requiere permisos especiales

---

## 🆘 Soporte

Si tienes problemas con algún script:

1. Verifica que estás en el directorio raíz del proyecto
2. Asegúrate de tener las dependencias instaladas (`uv sync`)
3. Revisa la documentación en `doc/`
4. Consulta los logs de error

---

**Última actualización:** 2025-10-10  
**Mantenedor:** Equipo de desarrollo
