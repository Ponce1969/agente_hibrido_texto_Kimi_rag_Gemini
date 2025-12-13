# 🎓 Aprendizaje de Git y Docker: Lecciones del Proyecto RAG

## 📋 Índice

1. [El Problema que Tuvimos](#el-problema-que-tuvimos)
2. [Por Qué Pasó](#por-qué-pasó)
3. [Cómo Detectarlo](#cómo-detectarlo)
4. [Cómo Prevenirlo](#cómo-prevenirlo)
5. [Workflow Recomendado](#workflow-recomendado)
6. [Comandos Esenciales](#comandos-esenciales)
7. [Troubleshooting](#troubleshooting)

---

## 🚨 El Problema que Tuvimos

### **Síntoma**
- ✅ **Local:** El código funcionaba perfectamente
- ❌ **Servidor:** El mismo código fallaba con errores

### **Causa Raíz**
El código en **local** y **GitHub** estaban **desincronizados**:

```
Local (funciona)     →  NO SE SUBIÓ  →  GitHub (código viejo)
                                              ↓
                                         Servidor (clonó código viejo)
```

### **Ejemplo Concreto**

**Local tenía:**
```python
response = httpx.post(f"{self.base_url}/embeddings/index/{file_id}", timeout=10)  # ✅ Correcto
```

**GitHub tenía:**
```python
response = httpx.post(f"{self.base_url}/files/index/{file_id}", timeout=10)  # ❌ Incorrecto
```

**Servidor clonó de GitHub** → Obtuvo código incorrecto → Falló

---

## 🔍 Por Qué Pasó

### **1. Cambios No Commiteados**
Hiciste cambios en local que funcionaban, pero:
- ❌ No los agregaste con `git add`
- ❌ No los commiteaste con `git commit`
- ❌ No los subiste con `git push`

### **2. Commits Selectivos**
Subiste algunos archivos pero no todos:
```bash
git add archivo1.py archivo2.py  # ← Olvidaste backend_client.py
git commit -m "fix"
git push
```

### **3. Merge Conflicts Mal Resueltos**
Durante un merge, elegiste la versión incorrecta del archivo.

### **4. Caché de Docker**
Incluso después de actualizar el código, Docker usaba capas cacheadas:
```bash
docker compose build  # ← Usó caché, NO copió código nuevo
```

---

## 🔍 Cómo Detectarlo

### **Antes de Hacer Push**

#### **1. Verificar Estado**
```bash
git status
```

**Salida esperada:**
```
En la rama main
Tu rama está actualizada con 'origin/main'.

nada para hacer commit, el árbol de trabajo está limpio  ✅
```

**Salida problemática:**
```
Cambios no rastreados para el commit:
  modificado:     src/adapters/streamlit/services/backend_client.py  ❌
```

#### **2. Ver Qué Cambió**
```bash
git diff
```

Esto muestra **línea por línea** qué cambió. Revisa que sean los cambios que quieres subir.

#### **3. Verificar Commits Pendientes**
```bash
git log origin/main..HEAD
```

**Si sale algo:** Tienes commits en local que NO están en GitHub ❌  
**Si sale vacío:** Todo está sincronizado ✅

### **Después de Hacer Push**

#### **4. Verificar en GitHub**
Ve al navegador y revisa que el archivo en GitHub tenga el código correcto:
```
https://github.com/TU_USUARIO/TU_REPO/blob/main/ruta/al/archivo.py
```

#### **5. Comparar Local vs GitHub**
```bash
# Clonar en carpeta temporal
cd /tmp
git clone https://github.com/TU_USUARIO/TU_REPO.git test_clone
cd test_clone

# Comparar archivo crítico
diff /tmp/test_clone/src/archivo.py ~/proyecto/src/archivo.py

# Si NO sale nada = Son idénticos ✅
# Si sale algo = Hay diferencias ❌

# Limpiar
rm -rf /tmp/test_clone
```

---

## 🛡️ Cómo Prevenirlo

### **Regla de Oro: Siempre Verificar Antes de Push**

```bash
# 1. Ver qué archivos cambiaron
git status

# 2. Ver QUÉ cambió en cada archivo
git diff

# 3. Agregar TODOS los cambios
git add -A

# 4. Commit con mensaje descriptivo
git commit -m "fix: Descripción clara del cambio"

# 5. Subir a GitHub
git push origin main

# 6. Verificar que se subió
git log origin/main..HEAD  # Debe estar vacío
```

### **Checklist Pre-Push**

- [ ] `git status` → No debe mostrar archivos modificados sin agregar
- [ ] `git diff` → Revisar que los cambios sean correctos
- [ ] `git log origin/main..HEAD` → Debe estar vacío después del push
- [ ] Verificar en GitHub que el archivo se actualizó

---

## 🔄 Workflow Recomendado

### **Desarrollo Local**

```bash
# 1. Asegurarte de estar en la rama correcta
git branch  # Debe mostrar: * main

# 2. Hacer cambios en el código
# ... editas archivos ...

# 3. Probar que funciona en local
docker compose down
docker compose up -d
# ... pruebas ...

# 4. Ver qué cambió
git status
git diff

# 5. Agregar cambios
git add -A  # O especificar archivos: git add src/archivo.py

# 6. Commit
git commit -m "fix: Descripción del cambio"

# 7. Push
git push origin main

# 8. Verificar
git log origin/main..HEAD  # Debe estar vacío
```

### **Actualizar Servidor**

```bash
# 1. SSH al servidor
ssh usuario@servidor

# 2. Ir al proyecto
cd ~/ruta/al/proyecto

# 3. Ver estado actual
git log --oneline -1

# 4. Actualizar código
git pull origin main

# 5. Verificar que se actualizó
git log --oneline -1  # Debe mostrar el último commit

# 6. Rebuild SIN CACHÉ
docker compose down
docker compose build --no-cache
docker compose up -d

# 7. Verificar logs
docker compose logs -f backend
```

---

## 📚 Comandos Esenciales

### **Git - Verificación**

```bash
# Ver estado de archivos
git status

# Ver cambios línea por línea
git diff

# Ver cambios de un archivo específico
git diff src/archivo.py

# Ver historial de commits
git log --oneline -10

# Ver commits no subidos
git log origin/main..HEAD

# Ver diferencia entre local y remoto
git diff origin/main
```

### **Git - Sincronización**

```bash
# Agregar todos los cambios
git add -A

# Agregar archivo específico
git add src/archivo.py

# Commit
git commit -m "mensaje descriptivo"

# Push
git push origin main

# Pull (actualizar desde GitHub)
git pull origin main

# Ver ramas
git branch

# Ver remotes
git remote -v
```

### **Docker - Rebuild**

```bash
# Rebuild SIN caché (fuerza copiar código nuevo)
docker compose build --no-cache

# Rebuild solo un servicio
docker compose build --no-cache backend

# Detener y eliminar contenedores
docker compose down

# Levantar
docker compose up -d

# Ver logs
docker compose logs -f backend

# Ver qué código tiene el contenedor
docker exec NOMBRE_CONTENEDOR cat /app/src/archivo.py

# Comparar código contenedor vs local
docker exec NOMBRE_CONTENEDOR cat /app/src/archivo.py > /tmp/contenedor.py
diff /tmp/contenedor.py src/archivo.py
```

---

## 🔧 Troubleshooting

### **Problema: Local Funciona, Servidor No**

#### **Diagnóstico**

```bash
# 1. Verificar que local y GitHub están sincronizados
git log origin/main..HEAD  # Debe estar vacío

# 2. Verificar código en servidor
ssh usuario@servidor
cd ~/proyecto
git log --oneline -1  # Comparar con local

# 3. Verificar código en contenedor
docker exec CONTENEDOR cat /app/src/archivo.py | grep "línea_crítica"
```

#### **Solución**

```bash
# Si local y GitHub NO están sincronizados:
git add -A
git commit -m "fix: Sincronizar cambios"
git push origin main

# Si servidor tiene código viejo:
ssh usuario@servidor
cd ~/proyecto
git pull origin main
docker compose down
docker compose build --no-cache
docker compose up -d

# Si contenedor tiene código viejo (caché):
docker compose down
docker compose build --no-cache
docker compose up -d
```

### **Problema: Merge Conflicts**

```bash
# Ver archivos en conflicto
git status

# Editar archivos manualmente y resolver conflictos
# Buscar marcadores: <<<<<<< HEAD, =======, >>>>>>>

# Después de resolver:
git add archivo_resuelto.py
git commit -m "fix: Resolver conflictos de merge"
git push origin main
```

### **Problema: Código Corrupto en GitHub**

#### **Verificación**

```bash
# Clonar en carpeta temporal
cd /tmp
git clone https://github.com/USUARIO/REPO.git test
cd test

# Comparar con local
diff -r /tmp/test/src ~/proyecto/src

# Si hay diferencias, GitHub tiene código diferente
```

#### **Solución (Último Recurso)**

```bash
# SOLO si estás 100% seguro que local está correcto:

# 1. Hacer backup
cp -r ~/proyecto ~/proyecto_backup

# 2. Forzar push (PELIGROSO)
git push --force origin main

# O mejor: Crear commit que sobrescriba
git add -A
git commit -m "fix: Sincronizar con local correcto"
git push origin main
```

---

## 🎯 Mejores Prácticas

### **1. Commits Pequeños y Frecuentes**
```bash
# ❌ Mal: 1 commit gigante con 50 archivos
git add -A
git commit -m "fix"

# ✅ Bien: Commits pequeños y descriptivos
git add src/adapters/agents/gemini_adapter.py
git commit -m "fix: Corregir timeout en Gemini adapter"

git add src/adapters/streamlit/services/backend_client.py
git commit -m "fix: Cambiar ruta de indexación a /embeddings/index"
```

### **2. Mensajes de Commit Descriptivos**
```bash
# ❌ Mal
git commit -m "fix"
git commit -m "cambios"
git commit -m "update"

# ✅ Bien
git commit -m "fix: Corregir ruta de indexación de /files/index a /embeddings/index"
git commit -m "feat: Agregar soporte para búsqueda semántica con pgvector"
git commit -m "refactor: Extraer lógica de embeddings a servicio separado"
```

### **3. Probar Antes de Push**
```bash
# 1. Hacer cambios
# 2. Probar en local
docker compose down
docker compose up -d
# ... pruebas ...

# 3. Si funciona, commit y push
git add -A
git commit -m "fix: ..."
git push origin main

# 4. Probar en servidor
ssh usuario@servidor
cd ~/proyecto
git pull origin main
docker compose down
docker compose build --no-cache
docker compose up -d
```

### **4. Usar .gitignore**
```bash
# Evitar subir archivos innecesarios
cat .gitignore

# Ejemplos:
__pycache__/
*.pyc
.env
.venv/
*.log
.DS_Store
```

### **5. Branches para Features Grandes**
```bash
# Crear rama para feature
git checkout -b feature/nueva-funcionalidad

# Hacer cambios y commits
git add -A
git commit -m "feat: Agregar nueva funcionalidad"

# Cuando esté lista, merge a main
git checkout main
git merge feature/nueva-funcionalidad
git push origin main

# Eliminar rama
git branch -d feature/nueva-funcionalidad
```

---

## 📖 Recursos Adicionales

### **Documentación Oficial**
- [Git Documentation](https://git-scm.com/doc)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Guides](https://guides.github.com/)

### **Tutoriales Recomendados**
- [Learn Git Branching (Interactivo)](https://learngitbranching.js.org/)
- [Oh Shit, Git!?!](https://ohshitgit.com/) - Soluciones a problemas comunes
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

### **Comandos de Emergencia**

```bash
# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer cambios en archivo (PELIGROSO)
git checkout -- archivo.py

# Ver qué cambió en un commit específico
git show COMMIT_HASH

# Volver a un commit anterior (PELIGROSO)
git reset --hard COMMIT_HASH

# Crear backup antes de operaciones peligrosas
cp -r ~/proyecto ~/proyecto_backup_$(date +%Y%m%d_%H%M%S)
```

---

## ✅ Checklist Final

Antes de cada push, verifica:

- [ ] `git status` → Árbol de trabajo limpio
- [ ] `git diff` → Cambios revisados
- [ ] Código probado en local
- [ ] Commit con mensaje descriptivo
- [ ] `git push origin main` ejecutado
- [ ] `git log origin/main..HEAD` → Vacío
- [ ] Verificado en GitHub (navegador)
- [ ] Servidor actualizado con `git pull`
- [ ] Docker rebuild con `--no-cache`
- [ ] Probado en servidor

---

## 🎓 Lección Aprendida

> **"El código que funciona en local pero no en servidor, casi siempre es un problema de sincronización Git o caché de Docker, no un bug del código."**

**Siempre verifica:**
1. ✅ Git: Local y GitHub sincronizados
2. ✅ Docker: Rebuild sin caché
3. ✅ Código: Comparar local vs contenedor

---

**Fecha de creación:** 18 de Octubre, 2025  
**Proyecto:** Sistema RAG con Gemini 2.5 + PostgreSQL + pgvector  
**Autor:** Aprendizaje colaborativo con Cascade AI
