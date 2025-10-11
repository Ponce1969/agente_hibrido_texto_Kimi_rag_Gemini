# 🧪 Suite de Tests

Esta carpeta contiene todos los tests del proyecto, organizados por tipo y propósito.

---

## 📂 Estructura

```
tests/
├── conftest.py                 # Fixtures compartidos
├── test_rag_system.py         # Tests del sistema RAG
├── test_chat_service.py       # Tests del servicio de chat
├── test_prompt_baseline.py   # Tests de baseline (IMPORTANTE)
└── README.md                  # Este archivo
```

---

## 🚀 Cómo Ejecutar los Tests

### **Todos los tests**
```bash
pytest
```

### **Solo tests unitarios (rápidos)**
```bash
pytest -m unit
```

### **Solo tests de RAG**
```bash
pytest -m rag
```

### **Solo tests de baseline**
```bash
pytest -m baseline
```

### **Excluir tests lentos**
```bash
pytest -m "not slow"
```

### **Con cobertura**
```bash
pytest --cov=src --cov-report=html
```

---

## 📊 Tests de Baseline (CRÍTICO)

Los tests en `test_prompt_baseline.py` son **CRÍTICOS** porque:

1. **Capturan el estado actual** de los prompts ANTES del refactor
2. **Generan archivos JSON** con métricas actuales:
   - `baseline_prompts.json` - Estructura de prompts
   - `baseline_tokens.json` - Uso de tokens
   - `baseline_responses.json` - Calidad de respuestas
   - `baseline_performance.json` - Tiempos de respuesta

3. **Sirven para comparar** después del refactor:
   ```bash
   # ANTES del refactor
   pytest -m baseline
   
   # Guardar archivos baseline_*.json
   
   # DESPUÉS del refactor
   pytest -m baseline
   
   # Comparar archivos para ver mejoras/degradaciones
   ```

---

## 🎯 Workflow Recomendado

### **Antes de Refactorizar**
```bash
# 1. Ejecutar todos los tests
pytest

# 2. Ejecutar tests de baseline
pytest -m baseline

# 3. Guardar archivos baseline_*.json
cp tests/baseline_*.json tests/baseline_before_refactor/

# 4. Verificar que todo pasa
pytest -v
```

### **Después de Refactorizar**
```bash
# 1. Ejecutar tests de baseline
pytest -m baseline

# 2. Comparar con baseline anterior
diff tests/baseline_before_refactor/baseline_tokens.json tests/baseline_tokens.json

# 3. Verificar mejoras
# - Tokens: Debe reducirse ~58%
# - Performance: Debe mantenerse o mejorar
# - Calidad: Debe mantenerse

# 4. Ejecutar todos los tests
pytest

# 5. Si todo pasa, el refactor es exitoso ✅
```

---

## 📈 Métricas Esperadas Después del Refactor

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Tokens por prompt** | ~2500 | ~400 | -84% |
| **Tokens totales** | ~4200 | ~1750 | -58% |
| **Tiempo de respuesta** | Similar | Similar | 0% |
| **Calidad** | Baseline | Igual o mejor | ≥0% |

---

## 🐛 Troubleshooting

### **Error: "No module named 'src'"**
```bash
# Asegúrate de estar en el directorio raíz
cd /home/gonzapython/Documentos/vscode_codigo/agentes_Front_Bac/agentes_Front_Bac

# Y que el venv esté activado
source .venv/bin/activate
```

### **Error: "fixture not found"**
```bash
# Verifica que conftest.py existe
ls tests/conftest.py

# Ejecuta desde la raíz del proyecto
pytest tests/
```

### **Tests muy lentos**
```bash
# Excluye tests lentos
pytest -m "not slow"

# O ejecuta solo unitarios
pytest -m unit
```

### **Quiero ver más detalles**
```bash
# Modo verbose
pytest -vv

# Con output de prints
pytest -s

# Con traceback completo
pytest --tb=long
```

---

## 📝 Agregar Nuevos Tests

### **Test Unitario**
```python
import pytest

@pytest.mark.unit
def test_my_function():
    result = my_function()
    assert result == expected
```

### **Test de Integración**
```python
import pytest

@pytest.mark.integration
@pytest.mark.slow
def test_full_flow():
    # Test que requiere servicios externos
    pass
```

### **Test con Fixture**
```python
def test_with_fixture(db_session, sample_chunks):
    # Usa fixtures de conftest.py
    assert len(sample_chunks) > 0
```

---

## 🎯 Objetivos de Cobertura

- **Mínimo**: 80% de cobertura
- **Objetivo**: 90% de cobertura
- **Crítico**: 100% en servicios core (chat, RAG)

```bash
# Ver cobertura actual
pytest --cov=src --cov-report=term-missing
```

---

## 🚀 CI/CD

Estos tests se ejecutarán automáticamente en CI cuando esté configurado:

```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: |
    pytest -m "not slow"
    pytest -m baseline
```

---

## 📞 Ayuda

Si tienes problemas con los tests:

1. Verifica que todas las dependencias estén instaladas
2. Asegúrate de estar en el venv correcto
3. Ejecuta `pytest --collect-only` para ver qué tests se detectan
4. Revisa los logs con `pytest -vv -s`

---

*Última actualización: 1 de Octubre 2025*
