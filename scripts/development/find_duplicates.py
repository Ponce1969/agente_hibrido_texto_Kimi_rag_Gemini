#!/usr/bin/env python3
"""
Script para encontrar archivos duplicados en el proyecto.

Detecta:
1. Archivos duplicados por contenido (mismo hash MD5)
2. Archivos con nombres similares
3. Archivos de código con contenido muy similar
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class DuplicateGroup:
    """Grupo de archivos duplicados."""
    hash: str
    size: int
    files: List[Path]
    
    @property
    def count(self) -> int:
        return len(self.files)
    
    @property
    def wasted_space(self) -> int:
        """Espacio desperdiciado (tamaño * (cantidad - 1))."""
        return self.size * (self.count - 1)


class DuplicateFinder:
    """Buscador de archivos duplicados."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.duplicates: List[DuplicateGroup] = []
        
        # Directorios a ignorar
        self.ignore_dirs = {
            '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
            'node_modules', '.git', '.venv', 'venv', 'env',
            'dist', 'build', '.egg-info', 'htmlcov',
            'data', 'uploads'  # Datos de usuario
        }
        
        # Extensiones a analizar
        self.code_extensions = {
            '.py', '.md', '.txt', '.yml', '.yaml', '.json',
            '.toml', '.ini', '.cfg', '.conf', '.sh'
        }
        
        # Archivos a ignorar por nombre
        self.ignore_files = {
            '.DS_Store', 'Thumbs.db', 'desktop.ini',
            '.gitkeep', '__init__.py'  # __init__.py vacíos son normales
        }
    
    def should_ignore(self, path: Path) -> bool:
        """Verifica si un archivo/directorio debe ignorarse."""
        # Ignorar directorios
        for parent in path.parents:
            if parent.name in self.ignore_dirs:
                return True
        
        # Ignorar archivos específicos
        if path.name in self.ignore_files:
            return True
        
        # Ignorar archivos muy pequeños (< 10 bytes)
        if path.is_file() and path.stat().st_size < 10:
            return True
        
        return False
    
    def calculate_hash(self, file_path: Path) -> str:
        """Calcula el hash MD5 de un archivo."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, PermissionError):
            return ""
    
    def find_duplicates_by_content(self) -> List[DuplicateGroup]:
        """Encuentra archivos duplicados por contenido (hash)."""
        print("🔍 Buscando archivos duplicados por contenido...\n")
        
        # Agrupar archivos por tamaño primero (optimización)
        files_by_size: Dict[int, List[Path]] = defaultdict(list)
        
        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file():
                continue
            
            if self.should_ignore(file_path):
                continue
            
            # Solo analizar archivos de código/config
            if file_path.suffix not in self.code_extensions:
                continue
            
            size = file_path.stat().st_size
            files_by_size[size].append(file_path)
        
        # Calcular hash solo para archivos del mismo tamaño
        files_by_hash: Dict[str, List[Path]] = defaultdict(list)
        
        for size, files in files_by_size.items():
            if len(files) < 2:
                continue  # No hay duplicados posibles
            
            for file_path in files:
                file_hash = self.calculate_hash(file_path)
                if file_hash:
                    files_by_hash[file_hash].append(file_path)
        
        # Crear grupos de duplicados
        duplicates = []
        for file_hash, files in files_by_hash.items():
            if len(files) > 1:
                duplicates.append(DuplicateGroup(
                    hash=file_hash,
                    size=files[0].stat().st_size,
                    files=sorted(files)
                ))
        
        return sorted(duplicates, key=lambda x: x.wasted_space, reverse=True)
    
    def find_similar_names(self) -> Dict[str, List[Path]]:
        """Encuentra archivos con nombres muy similares."""
        print("🔍 Buscando archivos con nombres similares...\n")
        
        files_by_name: Dict[str, List[Path]] = defaultdict(list)
        
        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file():
                continue
            
            if self.should_ignore(file_path):
                continue
            
            # Normalizar nombre (sin extensión, lowercase)
            name_normalized = file_path.stem.lower()
            files_by_name[name_normalized].append(file_path)
        
        # Filtrar solo los que tienen múltiples archivos
        similar = {
            name: files 
            for name, files in files_by_name.items() 
            if len(files) > 1
        }
        
        return similar
    
    def scan(self):
        """Escanea el proyecto buscando duplicados."""
        self.duplicates = self.find_duplicates_by_content()
        return self.duplicates
    
    def print_report(self):
        """Imprime el reporte de duplicados."""
        print("\n" + "="*80)
        print("📊 REPORTE DE ARCHIVOS DUPLICADOS")
        print("="*80 + "\n")
        
        if not self.duplicates:
            print("✅ ¡No se encontraron archivos duplicados!\n")
            return
        
        total_wasted = sum(d.wasted_space for d in self.duplicates)
        total_files = sum(d.count for d in self.duplicates)
        
        print(f"🔍 Grupos de duplicados encontrados: {len(self.duplicates)}")
        print(f"📁 Total de archivos duplicados: {total_files}")
        print(f"💾 Espacio desperdiciado: {self._format_size(total_wasted)}\n")
        
        print("="*80)
        print("GRUPOS DE DUPLICADOS (ordenados por espacio desperdiciado)")
        print("="*80 + "\n")
        
        for i, group in enumerate(self.duplicates, 1):
            print(f"Grupo {i}:")
            print(f"  Hash: {group.hash[:16]}...")
            print(f"  Tamaño: {self._format_size(group.size)}")
            print(f"  Archivos: {group.count}")
            print(f"  Espacio desperdiciado: {self._format_size(group.wasted_space)}")
            print(f"  Ubicaciones:")
            
            for file_path in group.files:
                rel_path = file_path.relative_to(self.project_root)
                print(f"    - {rel_path}")
            
            print()
        
        # Sugerencias
        print("="*80)
        print("💡 SUGERENCIAS")
        print("="*80 + "\n")
        
        print("Para cada grupo de duplicados:")
        print("1. Revisa cuál archivo es el correcto")
        print("2. Elimina los duplicados innecesarios")
        print("3. Si son necesarios, considera usar symlinks\n")
        
        print("Comandos para revisar:")
        for i, group in enumerate(self.duplicates[:5], 1):  # Solo primeros 5
            print(f"\n# Grupo {i}:")
            for file_path in group.files:
                rel_path = file_path.relative_to(self.project_root)
                print(f"cat {rel_path}")
                print(f"# rm {rel_path}  # Si decides eliminarlo")
        
        print("\n⚠️  IMPORTANTE: Revisa cada archivo antes de eliminarlo.")
        print("   Algunos duplicados pueden ser intencionales.\n")
    
    def print_similar_names_report(self):
        """Imprime reporte de nombres similares."""
        similar = self.find_similar_names()
        
        if not similar:
            return
        
        print("\n" + "="*80)
        print("📝 ARCHIVOS CON NOMBRES SIMILARES")
        print("="*80 + "\n")
        
        for name, files in sorted(similar.items()):
            if len(files) < 2:
                continue
            
            print(f"Nombre base: '{name}'")
            print(f"  Archivos encontrados: {len(files)}")
            for file_path in sorted(files):
                rel_path = file_path.relative_to(self.project_root)
                size = self._format_size(file_path.stat().st_size)
                print(f"    - {rel_path} ({size})")
            print()
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formatea el tamaño en bytes a formato legible."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


def main():
    """Función principal."""
    current_dir = Path(__file__).parent.parent
    
    print(f"📂 Analizando proyecto en: {current_dir}\n")
    
    finder = DuplicateFinder(str(current_dir))
    finder.scan()
    finder.print_report()
    finder.print_similar_names_report()
    
    return 0


if __name__ == "__main__":
    exit(main())
