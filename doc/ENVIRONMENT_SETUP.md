# 🔧 Configuración del Entorno de Desarrollo

## 🎯 Entorno Virtual con uv

Este proyecto utiliza **uv** como gestor de dependencias y entornos virtuales. uv es una herramienta moderna, rápida y compatible con pip.

### **Activación del Entorno Virtual**

#### **Método Rápido (Recomendado)**
```bash
# Usar el script de activación automática
source activate.sh
```

#### **Método Manual**
```bash
# Activar el entorno virtual
source .venv/bin/activate

# Verificar que está activado
which python  # Debe mostrar: /ruta/al/proyecto/.venv/bin/python
python --version  # Debe mostrar la versión de Python del proyecto
```

### **Recreación del Entorno Virtual**

Si el entorno virtual se pierde o tiene problemas:

```bash
# Recrear el entorno virtual e instalar dependencias
uv sync

# Activar el nuevo entorno
source .venv/bin/activate
```

### **Comandos Útiles de uv**

```bash
# Instalar nuevas dependencias
uv add nombre_del_paquete

# Actualizar dependencias
uv sync --upgrade

# Ver packages instalados
uv pip list

# Exportar requirements.txt (si es necesario)
uv export --format requirements-txt > requirements.txt
```

### **Verificación del Entorno**

Una vez activado, verifica que todo funciona:

```bash
# Verificar Python
python --version

# Verificar que las dependencias están instaladas
python -c "import fastapi, streamlit, groq; print('✅ Todas las dependencias instaladas')"

# Verificar que el proyecto funciona
python -m pytest --version  # Para testing
```

### **Desactivación**

```bash
# Desactivar el entorno virtual
deactivate
```

### **Solución de Problemas**

#### **Problema: "No existe el archivo o directorio .venv/bin/activate"**
**Solución:**
```bash
# Recrear el entorno virtual
uv sync

# Luego activar
source .venv/bin/activate
```

#### **Problema: "uv command not found"**
**Solución:** Instalar uv
```bash
# En Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# En Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Luego reiniciar la terminal
```

#### **Problema: Permisos en Linux/macOS**
**Solución:**
```bash
# Hacer el script ejecutable
chmod +x activate.sh

# O activar directamente
source .venv/bin/activate
```

---

## 🐳 Docker (Alternativa)

Si prefieres usar Docker sin entorno virtual:

```bash
# Lanzar todo con Docker
docker-compose up --build

# Acceso:
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000
# - Documentación: http://localhost:8000/docs
```

---

## 📝 Notas Importantes

1. **El directorio `.venv` está en `.gitignore`** - No se sube a Git
2. **Usa siempre el entorno virtual** - Evita conflictos de dependencias
3. **El script `activate.sh` es automático** - Detecta y recrea el entorno si es necesario
4. **uv es compatible con pip** - Puedes usar comandos pip dentro del entorno uv

---

**💡 Consejo:** Usa `source activate.sh` para la activación más fácil y confiable.
