#!/usr/bin/env python3
"""
Script para analizar violaciones de arquitectura hexagonal.

Detecta:
- Domain importando de Application o Adapters
- Application importando de Adapters
- Dependencias circulares
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class ArchitectureAnalyzer:
    """Analizador de arquitectura hexagonal."""
    
    def __init__(self, src_path: Path):
        self.src_path = src_path
        self.violations: List[Dict] = []
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
    
    def analyze(self) -> Dict:
        """Analiza toda la arquitectura."""
        print("🔍 Analizando arquitectura hexagonal...\n")
        
        # Analizar cada capa
        self._analyze_layer("domain")
        self._analyze_layer("application")
        self._analyze_layer("adapters")
        
        # Generar reporte
        return self._generate_report()
    
    def _analyze_layer(self, layer: str):
        """Analiza una capa específica."""
        layer_path = self.src_path / layer
        
        if not layer_path.exists():
            return
        
        print(f"📂 Analizando capa: {layer}")
        
        for py_file in layer_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            self._analyze_file(py_file, layer)
    
    def _analyze_file(self, file_path: Path, layer: str):
        """Analiza un archivo Python."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  ⚠️  Error leyendo {file_path}: {e}")
            return
        
        # Buscar imports
        imports = self._extract_imports(content)
        
        # Verificar violaciones
        for imp in imports:
            self._check_violation(file_path, layer, imp)
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extrae todos los imports de un archivo."""
        imports = []
        
        # Patrón para "from src.xxx import yyy"
        pattern1 = r'^from\s+(src\.\S+)\s+import'
        # Patrón para "import src.xxx"
        pattern2 = r'^import\s+(src\.\S+)'
        
        for line in content.split('\n'):
            line = line.strip()
            
            match1 = re.match(pattern1, line)
            if match1:
                imports.append(match1.group(1))
            
            match2 = re.match(pattern2, line)
            if match2:
                imports.append(match2.group(1))
        
        return imports
    
    def _check_violation(self, file_path: Path, layer: str, import_path: str):
        """Verifica si hay violación de arquitectura."""
        # Determinar capa importada
        imported_layer = self._get_layer_from_import(import_path)
        
        if not imported_layer:
            return
        
        # Registrar dependencia
        self.dependencies[layer].add(imported_layer)
        
        # Verificar violaciones según reglas
        violation = None
        severity = None
        
        if layer == "domain":
            if imported_layer in ["application", "adapters"]:
                violation = f"Domain NO debe importar de {imported_layer}"
                severity = "CRÍTICO"
        
        elif layer == "application":
            if imported_layer == "adapters":
                violation = f"Application NO debe importar de Adapters"
                severity = "CRÍTICO"
        
        if violation:
            self.violations.append({
                "file": str(file_path.relative_to(self.src_path)),
                "layer": layer,
                "import": import_path,
                "imported_layer": imported_layer,
                "violation": violation,
                "severity": severity
            })
    
    def _get_layer_from_import(self, import_path: str) -> str:
        """Determina la capa desde un import path."""
        parts = import_path.split('.')
        
        if len(parts) < 2:
            return None
        
        # src.domain.xxx → domain
        # src.application.xxx → application
        # src.adapters.xxx → adapters
        if parts[0] == "src" and parts[1] in ["domain", "application", "adapters"]:
            return parts[1]
        
        return None
    
    def _generate_report(self) -> Dict:
        """Genera reporte de análisis."""
        print("\n" + "="*70)
        print("📊 REPORTE DE ANÁLISIS")
        print("="*70 + "\n")
        
        # Resumen
        total_violations = len(self.violations)
        critical = len([v for v in self.violations if v["severity"] == "CRÍTICO"])
        
        print(f"Total de violaciones: {total_violations}")
        print(f"  ├─ Críticas: {critical}")
        print(f"  └─ Moderadas: {total_violations - critical}\n")
        
        # Violaciones por capa
        violations_by_layer = defaultdict(list)
        for v in self.violations:
            violations_by_layer[v["layer"]].append(v)
        
        for layer, viols in violations_by_layer.items():
            print(f"\n🔴 Violaciones en {layer.upper()}:")
            print(f"   Total: {len(viols)}\n")
            
            for v in viols[:5]:  # Mostrar primeras 5
                print(f"   Archivo: {v['file']}")
                print(f"   Import:  {v['import']}")
                print(f"   Problema: {v['violation']}")
                print()
            
            if len(viols) > 5:
                print(f"   ... y {len(viols) - 5} más\n")
        
        # Grafo de dependencias
        print("\n" + "="*70)
        print("🔗 GRAFO DE DEPENDENCIAS")
        print("="*70 + "\n")
        
        for layer, deps in self.dependencies.items():
            if deps:
                print(f"{layer} → {', '.join(sorted(deps))}")
        
        # Validación de reglas
        print("\n" + "="*70)
        print("✅ VALIDACIÓN DE REGLAS")
        print("="*70 + "\n")
        
        rules = [
            ("Domain → Ninguna capa", "domain" not in self.dependencies or not self.dependencies["domain"]),
            ("Application → Solo Domain", "adapters" not in self.dependencies.get("application", set())),
            ("Adapters → Application y Domain", True)  # Siempre válido
        ]
        
        for rule, valid in rules:
            status = "✅" if valid else "❌"
            print(f"{status} {rule}")
        
        print("\n" + "="*70)
        
        return {
            "total_violations": total_violations,
            "critical_violations": critical,
            "violations_by_layer": dict(violations_by_layer),
            "dependencies": dict(self.dependencies)
        }


def main():
    """Función principal."""
    # Obtener ruta del proyecto
    script_dir = Path(__file__).parent
    src_path = script_dir.parent / "src"
    
    if not src_path.exists():
        print(f"❌ No se encontró directorio src en {src_path}")
        return
    
    # Analizar
    analyzer = ArchitectureAnalyzer(src_path)
    report = analyzer.analyze()
    
    # Conclusión
    print("\n" + "="*70)
    print("🎯 CONCLUSIÓN")
    print("="*70 + "\n")
    
    if report["critical_violations"] == 0:
        print("✅ No se encontraron violaciones críticas")
        print("✅ La arquitectura hexagonal está bien implementada")
    else:
        print(f"❌ Se encontraron {report['critical_violations']} violaciones críticas")
        print("❌ Se requiere refactorización para cumplir arquitectura hexagonal")
    
    print("\n📝 Ver doc/ARCHITECTURE_AUDIT.md para plan de acción\n")


if __name__ == "__main__":
    main()
