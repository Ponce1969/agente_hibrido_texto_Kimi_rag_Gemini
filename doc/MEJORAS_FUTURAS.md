# 🚀 Mejoras Futuras del Proyecto

Este documento contiene mejoras planificadas que se implementarán en el futuro para mejorar la calidad, mantenibilidad y profesionalismo del proyecto.

---

## 📋 Índice

1. [Protección de Arquitectura Hexagonal con import-linter](#1-protección-de-arquitectura-hexagonal-con-import-linter)

---

## 1. Protección de Arquitectura Hexagonal con import-linter

### 🎯 **Objetivo**

Reemplazar el script Python custom de validación de arquitectura por **import-linter**, una herramienta estándar de la industria que garantiza que la arquitectura hexagonal no sea violada.

### 📊 **Beneficios**

| Aspecto | Script Actual | import-linter |
|---------|---------------|---------------|
| **Mantenimiento** | Manual (nosotros) | Comunidad |
| **Cobertura** | Básica | Completa |
| **CI/CD** | Manual | Automático |
| **Configuración** | Código Python | TOML declarativo |
| **Reportes** | Básicos | Detallados |
| **Estándar** | Custom | Industria |

### 🔧 **Implementación**

#### **Paso 1: Instalación**

```bash
# Agregar a requirements.txt o pyproject.toml
pip install import-linter

# O con uv
uv add --dev import-linter
```

#### **Paso 2: Crear Configuración**

Crear archivo `.importlinter` en la raíz del proyecto:

```toml
[importlinter]
root_package = src

# ============================================
# Contrato 1: Capas de Arquitectura Hexagonal
# ============================================
[[importlinter.contracts]]
name = "Arquitectura Hexagonal - Capas"
type = layers
layers =
    src.domain
    src.application
    src.adapters

# ============================================
# Contrato 2: Domain es completamente independiente
# ============================================
[[importlinter.contracts]]
name = "Domain no depende de nada"
type = forbidden
source_modules =
    src.domain
forbidden_modules =
    src.adapters
    src.application

# ============================================
# Contrato 3: Application solo usa Domain (puertos)
# ============================================
[[importlinter.contracts]]
name = "Application usa solo puertos del Domain"
type = forbidden
source_modules =
    src.application
forbidden_modules =
    src.adapters.db
    src.adapters.api
    src.adapters.tools
    src.adapters.agents
    src.adapters.streamlit

# ============================================
# Contrato 4: Adapters pueden usar Domain y Application
# ============================================
# (Esto está permitido por defecto en layers)

# ============================================
# Contrato 5: Sin dependencias circulares
# ============================================
[[importlinter.contracts]]
name = "Sin dependencias circulares"
type = independence
modules =
    src.domain
    src.application
    src.adapters.db
    src.adapters.api
    src.adapters.agents
    src.adapters.tools

# ============================================
# Contrato 6: Streamlit no debe importar FastAPI
# ============================================
[[importlinter.contracts]]
name = "Streamlit independiente de FastAPI"
type = forbidden
source_modules =
    src.adapters.streamlit
forbidden_modules =
    src.adapters.api.endpoints
```

#### **Paso 3: Ejecutar Validación**

```bash
# Validar arquitectura
lint-imports

# Output esperado si todo está bien:
# ============
# Import Linter
# ============
# 
# All contracts kept!
```

#### **Paso 4: Integrar con CI/CD (GitHub Actions)**

Crear archivo `.github/workflows/architecture-check.yml`:

```yaml
name: Architecture Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint-architecture:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install import-linter
      
      - name: Check architecture
        run: lint-imports
      
      - name: Comment on PR (if failed)
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '⚠️ **Violación de Arquitectura Hexagonal detectada!**\n\nPor favor, revisa los logs del CI para ver qué imports violan la arquitectura.'
            })
```

#### **Paso 5: Pre-commit Hook (Opcional)**

Crear archivo `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: import-linter
        name: Check Architecture (import-linter)
        entry: lint-imports
        language: system
        pass_filenames: false
        always_run: true
```

Instalar pre-commit:

```bash
pip install pre-commit
pre-commit install
```

#### **Paso 6: Eliminar Script Custom**

Una vez que import-linter esté funcionando, eliminar el script Python custom de validación de arquitectura.

### 📚 **Recursos**

- **Documentación oficial:** https://import-linter.readthedocs.io/
- **GitHub:** https://github.com/seddonym/import-linter
- **Tutorial:** https://import-linter.readthedocs.io/en/stable/usage.html

### 🎯 **Resultado Esperado**

Después de implementar import-linter:

1. ✅ **Arquitectura protegida automáticamente**
   - Cualquier violación será detectada inmediatamente
   
2. ✅ **CI/CD automático**
   - Los PRs no se pueden mergear si violan la arquitectura
   
3. ✅ **Documentación viva**
   - El archivo `.importlinter` documenta las reglas de arquitectura
   
4. ✅ **Menos mantenimiento**
   - No hay que mantener código custom
   
5. ✅ **Estándar de la industria**
   - Herramienta reconocida y profesional

### ⏱️ **Tiempo Estimado de Implementación**

- **Configuración inicial:** 30-45 minutos
- **Testing y ajustes:** 15-30 minutos
- **Integración CI/CD:** 15 minutos
- **Total:** ~1-1.5 horas

### 🚦 **Estado**

- **Estado actual:** 📋 Planificado
- **Prioridad:** 🟡 Media (mejora de calidad, no urgente)
- **Complejidad:** 🟢 Baja
- **Impacto:** 🟢 Alto (mejora significativa en mantenibilidad)

---

## 📝 **Notas Adicionales**

- Este documento se actualizará con nuevas mejoras planificadas
- Cada mejora debe tener una justificación clara de por qué es útil
- Solo se agregan mejoras que aporten valor real al proyecto
- Principio YAGNI: "You Aren't Gonna Need It" - no agregar por agregar

---

**Última actualización:** 2025-10-21
