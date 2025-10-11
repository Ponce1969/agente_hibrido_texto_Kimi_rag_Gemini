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
        ("sentence-transformers", "sentence_transformers"),
        ("psycopg2", "psycopg2"),
        ("pgvector", "pgvector"),
        ("pypdf", "pypdf"),
        ("torch", "torch"),
        ("numpy", "numpy"),
        ("sqlalchemy", "sqlalchemy"),
        ("fastapi", "fastapi"),
        ("streamlit", "streamlit"),
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
    
    # Verificar modelo de embeddings
    print("\n🤖 MODELO DE EMBEDDINGS:")
    print("-" * 30)
    try:
        from sentence_transformers import SentenceTransformer
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"Modelo objetivo: {model_name}")
        
        # Intentar cargar el modelo (esto puede tomar tiempo la primera vez)
        print("Verificando disponibilidad del modelo...")
        model = SentenceTransformer(model_name)
        print(f"✅ Modelo cargado correctamente")
        print(f"   Dimensiones: {model.get_sentence_embedding_dimension()}")
        print(f"   Dispositivo: {model.device}")
        
        # Liberar memoria
        del model
        
    except Exception as e:
        print(f"❌ Error con modelo de embeddings: {e}")
        missing_deps.append("sentence-transformers")
    
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
        print("pip install sentence-transformers psycopg2-binary pgvector pypdf torch")
        print("# O usando uv:")
        print("uv add sentence-transformers psycopg2-binary pgvector pypdf torch")
    else:
        print("✅ Todas las dependencias críticas están instaladas")
    
    print("\n💡 RECOMENDACIONES PARA PC DE BAJOS RECURSOS:")
    print("- Usar EMBEDDING_BATCH_SIZE=2 en .env")
    print("- Usar EMBEDDING_CHUNK_SIZE=600 en .env")
    print("- Cerrar otras aplicaciones durante la indexación")
    print("- Procesar PDFs de máximo 25MB")

if __name__ == "__main__":
    main()
