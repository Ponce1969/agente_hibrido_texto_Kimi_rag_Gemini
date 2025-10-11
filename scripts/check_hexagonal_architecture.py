#!/usr/bin/env python3
"""
Script para verificar violaciones de la arquitectura hexagonal.

Verifica:
1. Dependencias entre capas (domain no debe importar adapters/infrastructure)
2. Puertos correctamente definidos
3. Archivos mal ubicados
4. Acoplamiento directo a frameworks
"""
import ast
import os
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum


class Layer(Enum):
    """Capas de la arquitectura hexagonal."""
    DOMAIN = "domain"
    APPLICATION = "application"
    ADAPTERS = "adapters"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class Violation:
    """Representa una violación de arquitectura."""
    severity: str  # "ERROR", "WARNING", "INFO"
    layer: str
    file: str
    line: int
    message: str
    rule: str


class HexagonalArchitectureChecker:
    """Verifica la arquitectura hexagonal del proyecto."""
    
    def __init__(self, src_path: str):
        self.src_path = Path(src_path)
        self.violations: List[Violation] = []
        
        # Reglas de dependencias permitidas
        self.allowed_dependencies = {
            Layer.DOMAIN: set(),  # Domain no debe importar nada de otras capas
            Layer.APPLICATION: {Layer.DOMAIN},  # Application puede importar Domain
            Layer.ADAPTERS: {Layer.DOMAIN, Layer.APPLICATION},  # Adapters puede importar Domain y Application
        }
        
        # Frameworks/librerías que NO deben estar en domain
        self.forbidden_in_domain = {
            'fastapi', 'sqlmodel', 'sqlalchemy', 'pydantic', 'streamlit',
            'httpx', 'requests', 'flask', 'django', 'psycopg2', 'pymongo'
        }
        
        # Frameworks permitidos solo en adapters
        self.adapter_only_frameworks = {
            'fastapi', 'streamlit', 'httpx', 'sqlmodel', 'sqlalchemy'
        }
    
    def check_all(self) -> List[Violation]:
        """Ejecuta todas las verificaciones."""
        print("🔍 Iniciando análisis de arquitectura hexagonal...\n")
        
        self.check_domain_purity()
        self.check_dependency_direction()
        self.check_ports_location()
        self.check_models_location()
        self.check_framework_leakage()
        
        return self.violations
    
    def check_domain_purity(self):
        """Verifica que domain no importe adapters o infrastructure."""
        print("📦 Verificando pureza del dominio...")
        domain_path = self.src_path / "domain"
        
        if not domain_path.exists():
            return
        
        for py_file in domain_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            imports = self._extract_imports(py_file)
            
            for imp in imports:
                # Verificar importaciones de adapters
                if "adapters" in imp or "infrastructure" in imp:
                    self.violations.append(Violation(
                        severity="ERROR",
                        layer="domain",
                        file=str(py_file.relative_to(self.src_path)),
                        line=imp.get('line', 0),
                        message=f"Domain importa desde adapters/infrastructure: {imp['module']}",
                        rule="DOMAIN_PURITY"
                    ))
                
                # Verificar frameworks prohibidos
                for framework in self.forbidden_in_domain:
                    if framework in imp['module']:
                        self.violations.append(Violation(
                            severity="ERROR",
                            layer="domain",
                            file=str(py_file.relative_to(self.src_path)),
                            line=imp.get('line', 0),
                            message=f"Domain usa framework externo: {framework}",
                            rule="NO_FRAMEWORK_IN_DOMAIN"
                        ))
    
    def check_dependency_direction(self):
        """Verifica que las dependencias fluyan hacia adentro."""
        print("➡️  Verificando dirección de dependencias...")
        
        for layer in [Layer.DOMAIN, Layer.APPLICATION, Layer.ADAPTERS]:
            layer_path = self.src_path / layer.value
            
            if not layer_path.exists():
                continue
            
            for py_file in layer_path.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                imports = self._extract_imports(py_file)
                
                for imp in imports:
                    # Verificar si importa de una capa no permitida
                    imported_layer = self._get_layer_from_import(imp['module'])
                    
                    if imported_layer and imported_layer not in self.allowed_dependencies.get(layer, set()):
                        # Application no debe importar Adapters
                        if layer == Layer.APPLICATION and imported_layer == Layer.ADAPTERS:
                            self.violations.append(Violation(
                                severity="ERROR",
                                layer=layer.value,
                                file=str(py_file.relative_to(self.src_path)),
                                line=imp.get('line', 0),
                                message=f"Application importa Adapters: {imp['module']}",
                                rule="DEPENDENCY_INVERSION"
                            ))
    
    def check_ports_location(self):
        """Verifica que los puertos estén en domain/ports."""
        print("🔌 Verificando ubicación de puertos...")
        
        # Buscar archivos que definan puertos fuera de domain/ports
        for py_file in self.src_path.rglob("*.py"):
            if "domain/ports" in str(py_file):
                continue
            
            if py_file.name == "__init__.py":
                continue
            
            content = py_file.read_text(encoding='utf-8')
            
            # Buscar definiciones de puertos (ABC con métodos abstractos)
            if "ABC" in content and "@abstractmethod" in content:
                # Verificar si está fuera de domain/ports
                if "domain" in str(py_file) and "ports" not in str(py_file):
                    self.violations.append(Violation(
                        severity="WARNING",
                        layer="domain",
                        file=str(py_file.relative_to(self.src_path)),
                        line=0,
                        message="Puerto (ABC) definido fuera de domain/ports",
                        rule="PORT_LOCATION"
                    ))
    
    def check_models_location(self):
        """Verifica que los modelos de dominio estén en domain/models."""
        print("📋 Verificando ubicación de modelos...")
        
        # Buscar dataclasses o modelos fuera de domain/models
        for py_file in self.src_path.rglob("*.py"):
            if "domain/models" in str(py_file) or "adapters/db" in str(py_file):
                continue
            
            if py_file.name == "__init__.py":
                continue
            
            content = py_file.read_text(encoding='utf-8')
            
            # Buscar dataclasses en lugares incorrectos
            if "@dataclass" in content and "domain" in str(py_file) and "models" not in str(py_file):
                self.violations.append(Violation(
                    severity="INFO",
                    layer="domain",
                    file=str(py_file.relative_to(self.src_path)),
                    line=0,
                    message="Modelo de dominio (dataclass) fuera de domain/models",
                    rule="MODEL_LOCATION"
                ))
    
    def check_framework_leakage(self):
        """Verifica que frameworks estén solo en adapters."""
        print("🚫 Verificando fuga de frameworks...")
        
        for layer in [Layer.DOMAIN, Layer.APPLICATION]:
            layer_path = self.src_path / layer.value
            
            if not layer_path.exists():
                continue
            
            for py_file in layer_path.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                imports = self._extract_imports(py_file)
                
                # Verificar imports de FastAPI
                for imp in imports:
                    if "fastapi" in imp['module'].lower():
                        self.violations.append(Violation(
                            severity="ERROR",
                            layer=layer.value,
                            file=str(py_file.relative_to(self.src_path)),
                            line=imp.get('line', 0),
                            message=f"Import de FastAPI en {layer.value}: {imp['module']}",
                            rule="FRAMEWORK_LEAKAGE"
                        ))
                    
                    # Verificar imports de SQLModel/SQLAlchemy en domain
                    if layer == Layer.DOMAIN:
                        if "sqlmodel" in imp['module'].lower() or "sqlalchemy" in imp['module'].lower():
                            self.violations.append(Violation(
                                severity="ERROR",
                                layer=layer.value,
                                file=str(py_file.relative_to(self.src_path)),
                                line=imp.get('line', 0),
                                message=f"Import de ORM en {layer.value}: {imp['module']}",
                                rule="FRAMEWORK_LEAKAGE"
                            ))
    
    def _extract_imports(self, file_path: Path) -> List[Dict]:
        """Extrae las importaciones de un archivo Python."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'module': alias.name,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append({
                            'module': node.module,
                            'line': node.lineno
                        })
            
            return imports
        except Exception as e:
            print(f"⚠️  Error al parsear {file_path}: {e}")
            return []
    
    def _get_layer_from_import(self, module: str) -> Layer | None:
        """Determina la capa de un módulo importado."""
        if "src.domain" in module:
            return Layer.DOMAIN
        elif "src.application" in module:
            return Layer.APPLICATION
        elif "src.adapters" in module or "src.infrastructure" in module:
            return Layer.ADAPTERS
        return None
    
    def print_report(self):
        """Imprime el reporte de violaciones."""
        print("\n" + "="*80)
        print("📊 REPORTE DE ARQUITECTURA HEXAGONAL")
        print("="*80 + "\n")
        
        if not self.violations:
            print("✅ ¡No se encontraron violaciones! La arquitectura está limpia.\n")
            return
        
        # Agrupar por severidad
        errors = [v for v in self.violations if v.severity == "ERROR"]
        warnings = [v for v in self.violations if v.severity == "WARNING"]
        infos = [v for v in self.violations if v.severity == "INFO"]
        
        print(f"❌ ERRORES: {len(errors)}")
        print(f"⚠️  ADVERTENCIAS: {len(warnings)}")
        print(f"ℹ️  INFORMACIÓN: {len(infos)}\n")
        
        # Imprimir errores
        if errors:
            print("="*80)
            print("❌ ERRORES CRÍTICOS")
            print("="*80)
            for v in errors:
                print(f"\n📁 {v.file}:{v.line}")
                print(f"   Capa: {v.layer}")
                print(f"   Regla: {v.rule}")
                print(f"   ❌ {v.message}")
        
        # Imprimir advertencias
        if warnings:
            print("\n" + "="*80)
            print("⚠️  ADVERTENCIAS")
            print("="*80)
            for v in warnings:
                print(f"\n📁 {v.file}:{v.line}")
                print(f"   Capa: {v.layer}")
                print(f"   Regla: {v.rule}")
                print(f"   ⚠️  {v.message}")
        
        # Imprimir información
        if infos:
            print("\n" + "="*80)
            print("ℹ️  INFORMACIÓN")
            print("="*80)
            for v in infos:
                print(f"\n📁 {v.file}:{v.line}")
                print(f"   Capa: {v.layer}")
                print(f"   Regla: {v.rule}")
                print(f"   ℹ️  {v.message}")
        
        print("\n" + "="*80)
        print(f"Total de violaciones: {len(self.violations)}")
        print("="*80 + "\n")
        
        # Recomendaciones
        if errors:
            print("💡 RECOMENDACIONES:")
            print("   - Los errores críticos deben corregirse para mantener la arquitectura limpia")
            print("   - Domain no debe depender de Adapters o Infrastructure")
            print("   - Application no debe depender de Adapters")
            print("   - Usa Ports (interfaces) para invertir dependencias\n")


def main():
    """Función principal."""
    # Detectar la ruta src
    current_dir = Path(__file__).parent.parent
    src_path = current_dir / "src"
    
    if not src_path.exists():
        print(f"❌ No se encontró la carpeta src en: {src_path}")
        return
    
    print(f"📂 Analizando proyecto en: {src_path}\n")
    
    checker = HexagonalArchitectureChecker(str(src_path))
    checker.check_all()
    checker.print_report()
    
    # Retornar código de salida
    errors = [v for v in checker.violations if v.severity == "ERROR"]
    return 1 if errors else 0


if __name__ == "__main__":
    exit(main())
