# 🚀 Comandos Git para el Proyecto

## 📋 **Comandos Básicos**

### **Estado y Información**
```bash
git status                    # Ver estado de archivos
git log --oneline            # Ver historial de commits
git log --oneline -10        # Ver últimos 10 commits
git diff                     # Ver cambios no guardados
```

### **Guardar Cambios**
```bash
git add .                    # Agregar todos los archivos
git add src/                 # Agregar solo la carpeta src
git add doc/                 # Agregar solo documentación
git commit -m "mensaje"      # Guardar con mensaje descriptivo
```

### **Ramas (Branches)**
```bash
git branch                   # Ver ramas actuales
git checkout -b nueva-rama   # Crear y cambiar a nueva rama
git checkout main            # Cambiar a rama principal
git merge feature-branch     # Fusionar rama feature
```

## 🎯 **Estrategia de Commits Recomendada**

### **Commits por Tipo de Cambio**
```bash
# Para nuevas funcionalidades
git commit -m "✨ feat: implementar nueva funcionalidad"

# Para correcciones de bugs
git commit -m "🐛 fix: corregir error en validación"

# Para mejoras de código
git commit -m "🔧 refactor: mejorar arquitectura domain"

# Para documentación
git commit -m "📚 docs: actualizar documentación"

# Para configuración
git commit -m "⚙️ chore: actualizar configuración Docker"
```

### **Commits por Componente**
```bash
# Para cambios en API
git commit -m "🔌 api: agregar endpoint de descarga"

# Para cambios en UI
git commit -m "🎨 ui: mejorar interfaz de chat"

# Para cambios en base de datos
git commit -m "🗄️ db: optimizar consultas"

# Para cambios en agentes IA
git commit -m "🤖 agents: mejorar prompts del sistema"
```

## 📊 **Ver Historial por Componente**

```bash
# Ver commits relacionados con la API
git log --oneline --grep="api"

# Ver commits de documentación
git log --oneline --grep="docs"

# Ver commits de la última semana
git log --oneline --since="1 week ago"
```

## 🔍 **Buscar en el Historial**

```bash
# Buscar commits que mencionen "domain"
git log --oneline --grep="domain"

# Buscar commits que modifiquen archivos específicos
git log --oneline -- src/domain/

# Ver qué cambió en un commit específico
git show COMMIT_HASH
```

## 🚨 **Si algo sale mal**

```bash
# Ver qué cambios tienes sin guardar
git status

# Deshacer cambios en un archivo
git checkout -- archivo.py

# Ver diferencias con el último commit
git diff HEAD

# Crear commit de emergencia
git add . && git commit -m "🚨 TEMP: commit de emergencia"
```

## 📈 **Mejores Prácticas**

1. **Commits pequeños y frecuentes** - Mejor que commits grandes
2. **Mensajes descriptivos** - Explicar qué y por qué
3. **Una tarea por commit** - No mezclar diferentes cambios
4. **Probar antes de commitear** - Asegurarse de que funciona
5. **Pull antes de push** - Sincronizar con repositorio remoto

## 🎉 **Comandos para Mostrar Progreso**

```bash
# Ver commits del día
git log --oneline --since="today"

# Estadísticas del repositorio
git log --oneline --all | wc -l  # Número total de commits

# Ver archivos más modificados
git log --name-only --pretty=format: | sort | uniq -c | sort -nr | head -10
```

---
**💡 Tip**: Usa `git commit -m "📝 docs: actualizar progreso"` para documentar avances importantes del proyecto.
