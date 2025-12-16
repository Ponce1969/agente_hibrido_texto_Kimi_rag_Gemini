#!/usr/bin/env python3
"""
Script de verificación de dependencias para el sistema de indexación de PDFs.
Especialmente útil para PCs de bajos recursos como AMD APU A10.
"""

import sys
import subprocess
from typing import Dict, List, Tuple

def check_python_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Verifica si un paquete de Python está instalado."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, "✅ Instalado"
    except ImportError as e:
        return False, f"❌ No instalado: {e}"

def check_system_resources() -> Dict[str, str]:
    """Verifica recursos del sistema."""
    import psutil
    import platform
    
    return {
        "CPU": f"{psutil.cpu_count()} cores - {platform.processor()}",
        "RAM Total": f"{psutil.virtual_memory().total // (1024**3)} GB",
        "RAM Disponible": f"{psutil.virtual_memory().available // (1024**3)} GB",
        "Python": f"{sys.version.split()[0]}",
        "Plataforma": platform.platform()
    }

def main():
    print("🔍 VERIFICACIÓN DE DEPENDENCIAS PARA INDEXACIÓN DE PDFs")
    print("=" * 60)
    
    # Dependencias críticas
    critical_deps = [
        ("psycopg2", "psycopg2"),
        ("pgvector", "pgvector"),
        ("pypdf", "pypdf"),
        ("numpy", "numpy"),
        ("sqlalchemy", "sqlalchemy"),
        ("fastapi", "fastapi"),
        ("streamlit", "streamlit"),
        ("httpx", "httpx"),
    ]
    
    print("\n📦 DEPENDENCIAS CRÍTICAS:")
    print("-" * 30)
    
    missing_deps = []
    for pkg_name, import_name in critical_deps:
        installed, status = check_python_package(pkg_name, import_name)
        print(f"{pkg_name:20} {status}")
        if not installed:
            missing_deps.append(pkg_name)
    
    # Verificar recursos del sistema
    print("\n💻 RECURSOS DEL SISTEMA:")
    print("-" * 30)
    try:
        resources = check_system_resources()
        for key, value in resources.items():
            print(f"{key:15} {value}")
    except Exception as e:
        print(f"❌ Error verificando recursos: {e}")
    
    # Verificar Gemini API
    print("\n🤖 GEMINI API (EMBEDDINGS):")
    print("-" * 30)
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            print(f"✅ GEMINI_API_KEY configurada")
            print(f"   Modelo: text-embedding-004")
            print(f"   Dimensiones: 768")
            print(f"   Tipo: Cloud API (sin carga local)")
        else:
            print(f"❌ GEMINI_API_KEY no configurada en .env")
            missing_deps.append("GEMINI_API_KEY")
        
    except Exception as e:
        print(f"❌ Error verificando Gemini API: {e}")
        missing_deps.append("GEMINI_API_KEY")
    
    # Verificar PostgreSQL
    print("\n🐘 POSTGRESQL:")
    print("-" * 30)
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/pg/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API accesible")
            print(f"   Configurado: {data.get('configured', False)}")
            print(f"   Conectado: {data.get('connected', False)}")
            print(f"   pgvector: {data.get('pgvector_installed', False)}")
        else:
            print(f"⚠️  API responde pero con error: {response.status_code}")
    except Exception as e:
        print(f"❌ No se puede verificar PostgreSQL: {e}")
        print("   Asegúrate de que el backend esté ejecutándose")
    
    # Resumen
    print("\n📋 RESUMEN:")
    print("-" * 30)
    if missing_deps:
        print(f"❌ Dependencias faltantes: {', '.join(missing_deps)}")
        print("\n🔧 COMANDOS DE INSTALACIÓN:")
        print("pip install psycopg2-binary pgvector pypdf httpx")
        print("# O usando uv:")
        print("uv sync")
    else:
        print("✅ Todas las dependencias críticas están instaladas")
    
    print("\n💡 RECOMENDACIONES:")
    print("- Configurar GEMINI_API_KEY en .env")
    print("- Embeddings se procesan en cloud (sin carga local)")
    print("- Límites de RAM configurados en docker-compose.yml")
    print("- Backend: 1GB max, Frontend: 768MB max, Postgres: 512MB max")

if __name__ == "__main__":
    main()
