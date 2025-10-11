#!/usr/bin/env python3
"""
Script para limpiar el proyecto antes de producción.

Identifica:
1. Archivos obsoletos o duplicados
2. Archivos de desarrollo que no deben ir a producción
3. Carpetas vacías
4. Archivos temporales
5. Configuraciones de desarrollo
"""
import os
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class CleanupItem:
    """Item a limpiar."""
    path: str
    type: str  # "file", "directory", "pattern"
    reason: str
    action: str  # "delete", "review", "move"
    priority: str  # "high", "medium", "low"


class ProjectCleaner:
    """Limpieza del proyecto."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.items_to_clean: List[CleanupItem] = []
        
        # Patrones de archivos a eliminar
        self.delete_patterns = {
            '*.pyc', '*.pyo', '*.pyd', '__pycache__',
            '.pytest_cache', '.mypy_cache', '.ruff_cache',
            '*.log', '*.tmp', '*.bak', '*.swp', '*.swo',
            '.DS_Store', 'Thumbs.db', 'desktop.ini',
            '*.egg-info', 'dist/', 'build/',
        }
        
        # Archivos de desarrollo que no van a producción
        self.dev_files = {
            'check_dependencies.py',
            'verify_deployment.py',
            'activate.sh',
            'TESTING_SUMMARY.md',
            'IMPLEMENTATION_PLAN.md',
            'REFACTORING_COMPLETE.md',
        }
        
        # Carpetas que pueden estar vacías
        self.check_empty_dirs = {
            'uploads', 'data', 'backup_obsoletos_20251006_224158'
        }
    
    def scan_project(self):
        """Escanea el proyecto buscando items a limpiar."""
        print("🔍 Escaneando proyecto...\n")
        
        self.check_cache_files()
        self.check_dev_files()
        self.check_empty_directories()
        self.check_duplicate_docs()
        self.check_obsolete_backups()
        self.check_test_files()
        
        return self.items_to_clean
    
    def check_cache_files(self):
        """Busca archivos de caché."""
        print("📦 Verificando archivos de caché...")
        
        for pattern in ['__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache']:
            for path in self.project_root.rglob(pattern):
                if path.exists():
                    self.items_to_clean.append(CleanupItem(
                        path=str(path.relative_to(self.project_root)),
                        type="directory",
                        reason=f"Caché de Python ({pattern})",
                        action="delete",
                        priority="high"
                    ))
        
        # Archivos .pyc
        for pyc in self.project_root.rglob("*.pyc"):
            self.items_to_clean.append(CleanupItem(
                path=str(pyc.relative_to(self.project_root)),
                type="file",
                reason="Archivo compilado de Python",
                action="delete",
                priority="high"
            ))
    
    def check_dev_files(self):
        """Verifica archivos de desarrollo."""
        print("🛠️  Verificando archivos de desarrollo...")
        
        for dev_file in self.dev_files:
            file_path = self.project_root / dev_file
            if file_path.exists():
                self.items_to_clean.append(CleanupItem(
                    path=dev_file,
                    type="file",
                    reason="Archivo de desarrollo/testing",
                    action="review",
                    priority="medium"
                ))
    
    def check_empty_directories(self):
        """Busca directorios vacíos."""
        print("📁 Verificando directorios vacíos...")
        
        for dir_name in self.check_empty_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # Verificar si está vacío (ignorando .gitkeep)
                contents = list(dir_path.iterdir())
                if not contents or (len(contents) == 1 and contents[0].name == '.gitkeep'):
                    self.items_to_clean.append(CleanupItem(
                        path=dir_name,
                        type="directory",
                        reason="Directorio vacío o solo con .gitkeep",
                        action="review",
                        priority="low"
                    ))
    
    def check_duplicate_docs(self):
        """Busca documentación duplicada."""
        print("📄 Verificando documentación duplicada...")
        
        # Verificar si existe docs/ (debería estar solo doc/)
        docs_path = self.project_root / "docs"
        if docs_path.exists():
            self.items_to_clean.append(CleanupItem(
                path="docs/",
                type="directory",
                reason="Carpeta duplicada (existe doc/)",
                action="delete",
                priority="high"
            ))
        
        # Buscar archivos .md duplicados en raíz
        root_md_files = list(self.project_root.glob("*.md"))
        if len(root_md_files) > 2:  # README.md es normal
            for md_file in root_md_files:
                if md_file.name not in ['README.md']:
                    self.items_to_clean.append(CleanupItem(
                        path=md_file.name,
                        type="file",
                        reason="Archivo .md en raíz (debería estar en doc/)",
                        action="review",
                        priority="medium"
                    ))
    
    def check_obsolete_backups(self):
        """Busca backups obsoletos."""
        print("🗄️  Verificando backups obsoletos...")
        
        for backup_dir in self.project_root.glob("backup_*"):
            if backup_dir.is_dir():
                self.items_to_clean.append(CleanupItem(
                    path=str(backup_dir.relative_to(self.project_root)),
                    type="directory",
                    reason="Backup obsoleto",
                    action="review",
                    priority="medium"
                ))
    
    def check_test_files(self):
        """Verifica archivos de test en lugares incorrectos."""
        print("🧪 Verificando archivos de test...")
        
        # Buscar archivos test_*.py fuera de tests/
        for test_file in self.project_root.rglob("test_*.py"):
            if "tests/" not in str(test_file):
                self.items_to_clean.append(CleanupItem(
                    path=str(test_file.relative_to(self.project_root)),
                    type="file",
                    reason="Archivo de test fuera de tests/",
                    action="move",
                    priority="medium"
                ))
    
    def print_report(self):
        """Imprime el reporte de limpieza."""
        print("\n" + "="*80)
        print("🧹 REPORTE DE LIMPIEZA DEL PROYECTO")
        print("="*80 + "\n")
        
        if not self.items_to_clean:
            print("✅ ¡Proyecto limpio! No se encontraron items para limpiar.\n")
            return
        
        # Agrupar por acción
        to_delete = [i for i in self.items_to_clean if i.action == "delete"]
        to_review = [i for i in self.items_to_clean if i.action == "review"]
        to_move = [i for i in self.items_to_clean if i.action == "move"]
        
        print(f"🗑️  ELIMINAR: {len(to_delete)}")
        print(f"👀 REVISAR: {len(to_review)}")
        print(f"📦 MOVER: {len(to_move)}\n")
        
        # Imprimir items a eliminar
        if to_delete:
            print("="*80)
            print("🗑️  ITEMS A ELIMINAR (Prioridad Alta)")
            print("="*80)
            for item in to_delete:
                print(f"\n📁 {item.path}")
                print(f"   Tipo: {item.type}")
                print(f"   Razón: {item.reason}")
                print(f"   Prioridad: {item.priority}")
        
        # Imprimir items a revisar
        if to_review:
            print("\n" + "="*80)
            print("👀 ITEMS A REVISAR")
            print("="*80)
            for item in to_review:
                print(f"\n📁 {item.path}")
                print(f"   Tipo: {item.type}")
                print(f"   Razón: {item.reason}")
                print(f"   Prioridad: {item.priority}")
        
        # Imprimir items a mover
        if to_move:
            print("\n" + "="*80)
            print("📦 ITEMS A MOVER")
            print("="*80)
            for item in to_move:
                print(f"\n📁 {item.path}")
                print(f"   Tipo: {item.type}")
                print(f"   Razón: {item.reason}")
                print(f"   Prioridad: {item.priority}")
        
        print("\n" + "="*80)
        print(f"Total de items: {len(self.items_to_clean)}")
        print("="*80 + "\n")
        
        # Comandos sugeridos
        print("💡 COMANDOS SUGERIDOS PARA LIMPIEZA:\n")
        
        if to_delete:
            print("# Eliminar cachés y archivos compilados:")
            print("find . -type d -name '__pycache__' -exec rm -rf {} +")
            print("find . -type d -name '.pytest_cache' -exec rm -rf {} +")
            print("find . -type d -name '.mypy_cache' -exec rm -rf {} +")
            print("find . -type f -name '*.pyc' -delete\n")
        
        if any(i.path == "docs/" for i in to_delete):
            print("# Eliminar carpeta docs/ duplicada:")
            print("rm -rf docs/\n")
        
        print("# Revisar y decidir manualmente:")
        for item in to_review:
            if item.type == "directory":
                print(f"# Revisar: {item.path}")
                print(f"ls -la {item.path}/")
            else:
                print(f"# Revisar: {item.path}")
                print(f"cat {item.path}")
        
        print("\n⚠️  IMPORTANTE: Revisa cada item antes de eliminarlo definitivamente.")
        print("   Haz un backup si no estás seguro.\n")


def main():
    """Función principal."""
    current_dir = Path(__file__).parent.parent
    
    print(f"📂 Analizando proyecto en: {current_dir}\n")
    
    cleaner = ProjectCleaner(str(current_dir))
    cleaner.scan_project()
    cleaner.print_report()
    
    return 0


if __name__ == "__main__":
    exit(main())
