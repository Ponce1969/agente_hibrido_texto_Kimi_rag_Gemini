# 🔄 Plan de Refactorización: Sistema de Prompts Optimizado

**Fecha de Planificación:** 29 de Septiembre 2025  
**Fecha de Implementación:** 30 de Septiembre 2025  
**Estado:** 📋 **PLANIFICADO - LISTO PARA IMPLEMENTAR**

---

## 🎯 Objetivo Principal

**Reducir el consumo de tokens en un 58%** (de 4200 a 1750 tokens por request) sin perder la calidad de respuestas de Kimi-K2, manteniendo su excelencia en código Python.

---

## 📊 Diagnóstico del Problema Actual

### **Estado Actual**
```
❌ PROBLEMA: 3000-4000 tokens fijos por llamada
├── System Prompt: 2500 tokens (muy largo, repetitivo)
├── Few-shot examples: 500 tokens (siempre incluidos)
├── Contexto histórico: 1000 tokens (toda la conversación)
└── User input: 200 tokens

TOTAL: ~4200 tokens por request
```

### **Impacto**
- 💰 **Costo elevado** - Más tokens = más dinero
- ⏱️ **Latencia alta** - Más tokens = más tiempo de respuesta
- 🔄 **Mantenimiento difícil** - Cambiar estilo = editar 5 prompts
- 📈 **No escalable** - Agregar rol = copiar/pegar 100 líneas

---

## ✅ Solución Propuesta

### **Nueva Arquitectura**
```
✅ SOLUCIÓN: 1750 tokens por request (58% reducción)
├── System Prompt minimalista: 400 tokens
├── Docs externos (cacheados): 800 tokens
├── Few-shot condicional: 150 tokens
├── Contexto mínimo: 200 tokens
└── User input: 200 tokens

TOTAL: ~1750 tokens por request
AHORRO: 2450 tokens (58%)
```

---

## 🏗️ Arquitectura del Sistema

### **Estructura de Archivos**
```
src/adapters/agents/
├── prompts/                    # 🆕 Prompts minimalistas
│   ├── architect.txt           # 20 líneas (~400 tokens)
│   ├── dba.txt                 # 15 líneas (~300 tokens)
│   ├── tester.txt              # 18 líneas (~350 tokens)
│   ├── refactor.txt            # 16 líneas (~320 tokens)
│   └── devops.txt              # 20 líneas (~400 tokens)
│
├── docs/                       # 🆕 Documentación externa
│   ├── STYLEGUIDE.md           # Convenciones de código
│   ├── HEXA.md                 # Reglas arquitectura hexagonal
│   ├── TESTGUIDE.md            # Guías de testing
│   └── DBGUIDE.md              # Reglas de base de datos
│
├── snippets/                   # 🆕 Few-shot examples
│   ├── architect.json          # Ejemplos de código
│   ├── dba.json                # Ejemplos de SQL
│   ├── tester.json             # Ejemplos de tests
│   ├── refactor.json           # Ejemplos de refactoring
│   └── devops.json             # Ejemplos de DevOps
│
├── prompt_builder.py           # 🆕 Constructor de prompts
├── prompt_config.py            # 🆕 Configuraciones
└── prompts.py                  # ⚠️ LEGACY (mantener por ahora)
```

---

## 📝 Contenido de Archivos

### **1. Prompts Minimalistas**

#### **`prompts/architect.txt`**
```
You are SoftwareArchitect-15y.
Goal: produce maintainable Python 3.12 code following hexagonal architecture.
Tools: FastAPI, SQLModel, Pydantic v2, UV, Docker, pytest.
Output: unified diff (-U3) ready to apply with git apply.
Follow: STYLEGUIDE.md, HEXA.md.
Max lines: 80.
```

#### **`prompts/dba.txt`**
```
You are DBA-Agent.
Goal: optimize PostgreSQL/SQLite schemas and queries.
Tools: pgvector, Alembic, EXPLAIN ANALYZE, indexes, partial indexes.
Output: SQL + short rationale (< 60 words).
Follow: DBGUIDE.md.
Max lines: 60.
```

#### **`prompts/tester.txt`**
```
You are Tester-Agent.
Goal: write pytest tests achieving >= 95% branch coverage.
Tools: pytest, factory-boy, faker, pytest-cov, hypothesis.
Output: whole test file, no prose.
Follow: TESTGUIDE.md.
Max lines: 100.
```

#### **`prompts/refactor.txt`**
```
You are Refactor-Agent.
Goal: reduce complexity without behavior change.
Metrics: mccabe <= 10, cognitive <= 15, mypy strict pass.
Output: git diff (-U3) + one-line reason.
Follow: STYLEGUIDE.md, HEXA.md.
Max lines: 80.
```

#### **`prompts/devops.txt`**
```
You are DevOps-Agent.
Goal: keep Dockerfile, CI, UV, docker-compose.yml optimal.
Constraints: image < 150 MB, layer cache friendly, non-root user.
Output: changed files inline (```dockerfile ...).
Max lines: 60.
```

---

### **2. Documentos de Guías**

#### **`docs/STYLEGUIDE.md`**
```markdown
# Python Style Guide

## Naming Conventions
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

## Type Hints
- Always use type hints
- Use `from __future__ import annotations`
- Prefer `list[str]` over `List[str]` (Python 3.12+)

## Docstrings
- Use Google style
- Include Args, Returns, Raises

## Code Quality
- Max line length: 120
- Max function length: 50 lines
- Max complexity: McCabe <= 10

## Imports
- Standard library first
- Third-party second
- Local imports last
- Alphabetical order within groups
```

#### **`docs/HEXA.md`**
```markdown
# Hexagonal Architecture Rules

## Layer Dependencies
```
domain/          # No dependencies
  ↑
application/     # Depends on domain
  ↑
adapters/        # Depends on application + domain
```

## Domain Layer
- Pure business logic
- No external dependencies
- Only Python standard library
- Entities and value objects

## Application Layer
- Use cases and services
- Orchestrates domain logic
- Defines repository interfaces

## Adapters Layer
- API endpoints (FastAPI)
- Database implementations (SQLModel)
- External services (Groq, Gemini)
- UI (Streamlit)

## Rules
1. Domain never imports from application or adapters
2. Use dependency injection
3. Interfaces in domain, implementations in adapters
```

#### **`docs/TESTGUIDE.md`**
```markdown
# Testing Guide

## Coverage Requirements
- Minimum: 95% branch coverage
- Critical paths: 100% coverage

## Test Structure
```python
def test_feature_scenario():
    # Arrange
    setup_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected
```

## Tools
- pytest for test runner
- factory-boy for test data
- faker for random data
- hypothesis for property testing
- pytest-cov for coverage

## Best Practices
- One assertion per test (when possible)
- Use factories, not fixtures
- Test behavior, not implementation
- Mock external dependencies only
```

#### **`docs/DBGUIDE.md`**
```markdown
# Database Guide

## PostgreSQL Best Practices
- Use indexes on foreign keys
- Use partial indexes when appropriate
- EXPLAIN ANALYZE before optimizing
- Avoid N+1 queries

## SQLite Best Practices
- Use WAL mode for concurrency
- Create indexes on frequently queried columns
- Use transactions for bulk operations

## Migrations (Alembic)
- One migration per feature
- Always test rollback
- Include data migrations when needed

## pgvector
- Use cosine distance for embeddings
- Create IVFFlat index for > 1000 vectors
- Normalize embeddings before storage
```

---

### **3. Few-Shot Examples**

#### **`snippets/architect.json`**
```json
{
  "example": "User: Add user authentication endpoint\n\nAssistant:\n```diff\n--- a/src/adapters/api/auth.py\n+++ b/src/adapters/api/auth.py\n@@ -10,6 +10,15 @@\n from src.domain.services.auth_service import AuthService\n \n+@router.post(\"/login\")\n+async def login(\n+    credentials: LoginRequest,\n+    auth_service: AuthService = Depends(get_auth_service)\n+) -> TokenResponse:\n+    token = await auth_service.authenticate(credentials)\n+    return TokenResponse(access_token=token)\n+\n```"
}
```

#### **`snippets/tester.json`**
```json
{
  "example": "User: Add test for user soft-delete\n\nAssistant:\n```python\ndef test_user_soft_delete(session: Session):\n    # Arrange\n    user = UserFactory()\n    session.add(user)\n    session.commit()\n    \n    # Act\n    SoftDeleteUser(session).execute(user.id)\n    \n    # Assert\n    session.refresh(user)\n    assert user.deleted_at is not None\n    assert user.is_active is False\n```"
}
```

---

### **4. PromptBuilder (Código)**

#### **`prompt_builder.py`**
```python
"""
Constructor de prompts optimizado para reducir tokens.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json


@dataclass
class PromptConfig:
    """Configuración de un prompt de rol."""
    role: str
    goal: str
    tools: list[str]
    output_format: str
    max_lines: int
    docs: list[str]  # ["STYLEGUIDE", "HEXA", "TESTGUIDE", "DBGUIDE"]


class PromptBuilder:
    """
    Constructor de prompts que combina:
    - Prompt minimalista del rol
    - Documentos externos (cacheados)
    - Few-shot examples (condicionales)
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.docs_cache: dict[str, str] = {}
        self.snippets_cache: dict[str, dict] = {}
        
    def load_doc(self, doc_name: str, max_chars: int = 1000) -> str:
        """
        Carga y cachea un documento externo.
        
        Args:
            doc_name: Nombre del documento (sin extensión)
            max_chars: Máximo de caracteres a incluir
            
        Returns:
            Contenido del documento (truncado si es necesario)
        """
        if doc_name not in self.docs_cache:
            path = self.base_path / "docs" / f"{doc_name}.md"
            if not path.exists():
                return f"[{doc_name} not found]"
            
            content = path.read_text(encoding="utf-8")
            # Truncar si es muy largo
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... (truncated)"
            
            self.docs_cache[doc_name] = content
            
        return self.docs_cache[doc_name]
    
    def load_snippet(self, role: str) -> Optional[str]:
        """
        Carga un ejemplo few-shot para el rol.
        
        Args:
            role: Nombre del rol (architect, dba, etc.)
            
        Returns:
            Ejemplo formateado o None si no existe
        """
        if role not in self.snippets_cache:
            path = self.base_path / "snippets" / f"{role}.json"
            if not path.exists():
                return None
            
            data = json.loads(path.read_text(encoding="utf-8"))
            self.snippets_cache[role] = data
        
        return self.snippets_cache[role].get("example")
    
    def build(
        self,
        config: PromptConfig,
        include_few_shot: bool = False,
        include_docs: bool = True
    ) -> str:
        """
        Construye el prompt completo.
        
        Args:
            config: Configuración del rol
            include_few_shot: Si incluir ejemplo few-shot
            include_docs: Si incluir documentos externos
            
        Returns:
            Prompt completo listo para enviar a Kimi
        """
        # 1. Prompt base del rol
        role_file = self.base_path / "prompts" / f"{config.role.lower()}.txt"
        if role_file.exists():
            prompt = role_file.read_text(encoding="utf-8").strip()
        else:
            # Fallback: construir prompt básico
            prompt = f"""You are {config.role}.
Goal: {config.goal}.
Tools: {', '.join(config.tools)}.
Output: {config.output_format}.
Max lines: {config.max_lines}."""
        
        # 2. Agregar documentos externos (si se solicita)
        if include_docs and config.docs:
            prompt += "\n\nGuidelines:\n"
            for doc in config.docs:
                content = self.load_doc(doc, max_chars=800)
                prompt += f"\n{doc}:\n{content}\n"
        
        # 3. Agregar few-shot example (si se solicita)
        if include_few_shot:
            snippet = self.load_snippet(config.role.lower())
            if snippet:
                prompt += f"\n\nExample:\n{snippet}\n"
        
        return prompt
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima tokens usando aproximación simple.
        Regla: ~4 caracteres = 1 token
        
        Args:
            text: Texto a estimar
            
        Returns:
            Número estimado de tokens
        """
        return len(text) // 4


# Configuraciones predefinidas de roles
ROLE_CONFIGS = {
    "architect": PromptConfig(
        role="SoftwareArchitect-15y",
        goal="produce maintainable Python 3.12 code following hexagonal architecture",
        tools=["FastAPI", "SQLModel", "Pydantic v2", "UV", "Docker", "pytest"],
        output_format="unified diff (-U3) ready to apply with git apply",
        max_lines=80,
        docs=["STYLEGUIDE", "HEXA"]
    ),
    "dba": PromptConfig(
        role="DBA-Agent",
        goal="optimize PostgreSQL/SQLite schemas and queries",
        tools=["pgvector", "Alembic", "EXPLAIN ANALYZE", "indexes"],
        output_format="SQL + short rationale (< 60 words)",
        max_lines=60,
        docs=["DBGUIDE"]
    ),
    "tester": PromptConfig(
        role="Tester-Agent",
        goal="write pytest tests achieving >= 95% branch coverage",
        tools=["pytest", "factory-boy", "faker", "pytest-cov", "hypothesis"],
        output_format="whole test file, no prose",
        max_lines=100,
        docs=["TESTGUIDE"]
    ),
    "refactor": PromptConfig(
        role="Refactor-Agent",
        goal="reduce complexity without behavior change",
        tools=["ruff", "mypy", "radon"],
        output_format="git diff (-U3) + one-line reason",
        max_lines=80,
        docs=["STYLEGUIDE", "HEXA"]
    ),
    "devops": PromptConfig(
        role="DevOps-Agent",
        goal="keep Dockerfile, CI, UV, docker-compose.yml optimal",
        tools=["Docker", "docker-compose", "UV", "GitHub Actions"],
        output_format="changed files inline",
        max_lines=60,
        docs=[]
    )
}


# Ejemplo de uso
if __name__ == "__main__":
    from pathlib import Path
    
    builder = PromptBuilder(Path("src/adapters/agents"))
    
    # Construir prompt para arquitecto
    config = ROLE_CONFIGS["architect"]
    prompt = builder.build(config, include_few_shot=True)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {builder.estimate_tokens(prompt)}")
    print("\n" + "="*60)
    print(prompt)
```

---

## 📋 Plan de Implementación

### **Fase 1: Preparación (30 minutos)**

#### **Paso 1.1: Crear estructura de directorios**
```bash
cd src/adapters/agents
mkdir -p prompts docs snippets
```

#### **Paso 1.2: Crear archivos de prompts**
```bash
# Crear cada archivo .txt con el contenido minimalista
touch prompts/architect.txt
touch prompts/dba.txt
touch prompts/tester.txt
touch prompts/refactor.txt
touch prompts/devops.txt
```

#### **Paso 1.3: Crear documentos de guías**
```bash
touch docs/STYLEGUIDE.md
touch docs/HEXA.md
touch docs/TESTGUIDE.md
touch docs/DBGUIDE.md
```

#### **Paso 1.4: Crear snippets**
```bash
touch snippets/architect.json
touch snippets/dba.json
touch snippets/tester.json
touch snippets/refactor.json
touch snippets/devops.json
```

---

### **Fase 2: Implementación (2 horas)**

#### **Paso 2.1: Copiar contenido de archivos**
- Copiar los prompts minimalistas a cada `.txt`
- Copiar las guías a cada `.md`
- Copiar los ejemplos a cada `.json`

#### **Paso 2.2: Crear `prompt_builder.py`**
- Copiar el código completo del PromptBuilder
- Agregar imports necesarios
- Verificar que compile sin errores

#### **Paso 2.3: Crear `prompt_config.py`**
```python
"""Configuraciones de roles para el sistema de prompts."""
from prompt_builder import PromptConfig

# Exportar configuraciones
__all__ = ["ROLE_CONFIGS"]

ROLE_CONFIGS = {
    # ... (copiar del código arriba)
}
```

---

### **Fase 3: Integración (1 hora)**

#### **Paso 3.1: Modificar `groq_client.py`**
```python
# Agregar al inicio
from .prompt_builder import PromptBuilder, ROLE_CONFIGS
from pathlib import Path

class GroqClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        # Inicializar builder
        self.prompt_builder = PromptBuilder(
            Path(__file__).parent
        )
    
    async def get_chat_completion(
        self,
        system_prompt: str,  # Ahora puede ser nombre de rol
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        role: str | None = None  # 🆕 NUEVO parámetro
    ) -> str:
        # Si se proporciona rol, construir prompt optimizado
        if role and role in ROLE_CONFIGS:
            config = ROLE_CONFIGS[role]
            # Incluir few-shot solo en primeros mensajes
            include_few_shot = len(messages) < 3
            system_prompt = self.prompt_builder.build(
                config,
                include_few_shot=include_few_shot
            )
        
        # Resto del código igual...
```

#### **Paso 3.2: Modificar `chat_service.py`**
```python
# En handle_chat_message, pasar el rol
ai_response_content = await self.client.get_chat_completion(
    system_prompt=system_prompt,
    messages=history,
    max_tokens=max_tokens,
    temperature=temperature,
    role=agent_mode.value.lower()  # 🆕 Pasar rol
)
```

---

### **Fase 4: Testing (1 hora)**

#### **Paso 4.1: Crear script de prueba**
```python
# scripts/test_prompts.py
"""Test del nuevo sistema de prompts."""
from pathlib import Path
from src.adapters.agents.prompt_builder import PromptBuilder, ROLE_CONFIGS

def test_all_roles():
    builder = PromptBuilder(Path("src/adapters/agents"))
    
    for role_name, config in ROLE_CONFIGS.items():
        print(f"\n{'='*60}")
        print(f"Testing role: {role_name}")
        print(f"{'='*60}")
        
        # Sin few-shot
        prompt = builder.build(config, include_few_shot=False)
        tokens = builder.estimate_tokens(prompt)
        print(f"Without few-shot: {tokens} tokens")
        
        # Con few-shot
        prompt_with_fs = builder.build(config, include_few_shot=True)
        tokens_with_fs = builder.estimate_tokens(prompt_with_fs)
        print(f"With few-shot: {tokens_with_fs} tokens")
        
        # Verificar que no exceda límite
        assert tokens < 1500, f"Prompt too long for {role_name}"
        
        print(f"✅ {role_name} OK")

if __name__ == "__main__":
    test_all_roles()
    print("\n🎉 All tests passed!")
```

#### **Paso 4.2: Ejecutar tests**
```bash
python3 scripts/test_prompts.py
```

#### **Paso 4.3: Comparar respuestas**
```bash
# Hacer una pregunta con sistema viejo
# Hacer la misma pregunta con sistema nuevo
# Comparar calidad de respuestas
```

---

### **Fase 5: Optimización (30 minutos)**

#### **Paso 5.1: Medir tokens reales**
```python
# Usar tiktoken para medición precisa
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
tokens = len(encoding.encode(prompt))
```

#### **Paso 5.2: Ajustar según métricas**
- Si un rol excede 1500 tokens, reducir docs
- Si respuestas son pobres, agregar más contexto
- Balancear tokens vs calidad

---

## 📊 Métricas Esperadas

### **Antes vs Después**

| Componente | Antes | Después | Ahorro |
|------------|-------|---------|--------|
| System Prompt | 2500 | 400 | -84% |
| Docs (cacheados) | 0 | 800 | +800 |
| Few-shot | 500 | 150 | -70% |
| Contexto | 1000 | 200 | -80% |
| User Input | 200 | 200 | 0% |
| **TOTAL** | **4200** | **1750** | **-58%** |

### **Beneficios**

| Aspecto | Mejora |
|---------|--------|
| **Costo por request** | -58% |
| **Latencia** | -30% (menos tokens = más rápido) |
| **Mantenibilidad** | +300% (cambios centralizados) |
| **Escalabilidad** | +500% (agregar rol = 1 archivo) |

---

## ⚠️ Consideraciones Importantes

### **1. Calidad de Respuestas**
- ✅ **Monitorear** las primeras 50 respuestas
- ✅ **Comparar** con sistema anterior
- ✅ **Ajustar** si hay degradación

### **2. Caché de Documentos**
- ✅ Los docs se cargan **una vez** por sesión
- ✅ Reutilizados en todas las llamadas
- ✅ Ahorro adicional después del primer request

### **3. Few-Shot Condicional**
- ✅ Solo incluir en primeros 3 mensajes
- ✅ Después, Kimi ya "aprendió" el formato
- ✅ Ahorro de 150 tokens por request

### **4. Contexto Histórico**
- ✅ Solo último mensaje del usuario
- ✅ Resumen del último asistente
- ✅ Lista de archivos afectados
- ✅ Tarea actual (1 línea)

---

## 🎯 Checklist de Implementación

### **Preparación**
- [ ] Crear estructura de directorios
- [ ] Crear archivos `.txt` de prompts
- [ ] Crear archivos `.md` de docs
- [ ] Crear archivos `.json` de snippets

### **Implementación**
- [ ] Copiar contenido a todos los archivos
- [ ] Implementar `prompt_builder.py`
- [ ] Implementar `prompt_config.py`
- [ ] Modificar `groq_client.py`
- [ ] Modificar `chat_service.py`

### **Testing**
- [ ] Crear `scripts/test_prompts.py`
- [ ] Ejecutar tests de tokens
- [ ] Comparar respuestas (viejo vs nuevo)
- [ ] Ajustar según resultados

### **Optimización**
- [ ] Medir tokens con tiktoken
- [ ] Ajustar max_lines si es necesario
- [ ] Optimizar docs si exceden límite
- [ ] Documentar métricas finales

### **Documentación**
- [ ] Actualizar README con nuevo sistema
- [ ] Documentar cómo agregar nuevos roles
- [ ] Crear guía de troubleshooting
- [ ] Actualizar CHANGELOG

---

## 🚀 Próximos Pasos (Post-Implementación)

### **Corto Plazo (1 semana)**
1. Monitorear métricas de tokens
2. Recopilar feedback de calidad
3. Ajustar prompts según necesidad

### **Mediano Plazo (1 mes)**
1. Implementar A/B testing
2. Agregar métricas automáticas
3. Optimizar caché de documentos

### **Largo Plazo (3 meses)**
1. RAG sobre documentos (búsqueda dinámica)
2. Auto-tuning de prompts
3. Sistema de fallback a modelos locales

---

## 📞 Soporte y Troubleshooting

### **Si los prompts son muy largos**
```python
# Reducir max_chars en load_doc()
content = self.load_doc(doc, max_chars=500)  # Reducir de 800 a 500
```

### **Si las respuestas pierden calidad**
```python
# Incluir few-shot en más mensajes
include_few_shot = len(messages) < 5  # Aumentar de 3 a 5
```

### **Si necesitas agregar un nuevo rol**
```python
# 1. Crear prompts/nuevo_rol.txt
# 2. Agregar a ROLE_CONFIGS
# 3. Crear snippets/nuevo_rol.json (opcional)
# 4. ¡Listo!
```

---

## 🎉 Conclusión

Este plan de refactorización está diseñado para:

✅ **Reducir costos** en un 58%  
✅ **Mantener calidad** de respuestas  
✅ **Mejorar mantenibilidad** significativamente  
✅ **Facilitar escalabilidad** del sistema  

**Tiempo estimado total: 5 horas**

**¡Mañana estarás listo para implementar!** 🚀

---

*Documento creado: 29 de Septiembre 2025*  
*Para implementación: 30 de Septiembre 2025*  
*Versión: 1.0.0*
