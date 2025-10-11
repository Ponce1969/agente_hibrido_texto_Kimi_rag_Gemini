#!/usr/bin/env python3
"""
Script de verificación post-despliegue para el sistema optimizado.
Verifica que todos los servicios estén funcionando correctamente.
"""

import requests
import time
import json
from typing import Dict, Any

def check_service(url: str, service_name: str, timeout: int = 10) -> Dict[str, Any]:
    """Verifica que un servicio esté respondiendo."""
    try:
        response = requests.get(url, timeout=timeout)
        return {
            "service": service_name,
            "status": "✅ OK" if response.status_code == 200 else f"⚠️ HTTP {response.status_code}",
            "response_time": f"{response.elapsed.total_seconds():.2f}s",
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }
    except requests.exceptions.ConnectionError:
        return {
            "service": service_name,
            "status": "❌ No conecta",
            "error": "Servicio no disponible"
        }
    except requests.exceptions.Timeout:
        return {
            "service": service_name,
            "status": "⏱️ Timeout",
            "error": f"No responde en {timeout}s"
        }
    except Exception as e:
        return {
            "service": service_name,
            "status": "❌ Error",
            "error": str(e)
        }

def wait_for_services(max_wait: int = 120):
    """Espera a que los servicios estén listos."""
    print(f"🕐 Esperando a que los servicios estén listos (máximo {max_wait}s)...")
    
    services = [
        ("http://localhost:8000/health", "Backend API"),
        ("http://localhost:8501", "Frontend Streamlit"),
        ("http://localhost:8000/api/v1/pg/health", "PostgreSQL Health")
    ]
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        all_ready = True
        for url, name in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code != 200:
                    all_ready = False
                    break
            except:
                all_ready = False
                break
        
        if all_ready:
            print("✅ Todos los servicios están listos!")
            return True
        
        print("⏳ Servicios iniciando...", end="\r")
        time.sleep(5)
    
    print(f"⚠️ Algunos servicios no están listos después de {max_wait}s")
    return False

def main():
    print("🚀 VERIFICACIÓN POST-DESPLIEGUE")
    print("=" * 50)
    
    # Esperar a que los servicios estén listos
    wait_for_services()
    
    # Verificar servicios principales
    services_to_check = [
        ("http://localhost:8000/health", "Backend API Health"),
        ("http://localhost:8000/docs", "API Documentation"),
        ("http://localhost:8501", "Streamlit Frontend"),
        ("http://localhost:8000/api/v1/pg/health", "PostgreSQL Connection"),
    ]
    
    print("\n🔍 VERIFICANDO SERVICIOS:")
    print("-" * 30)
    
    results = []
    for url, name in services_to_check:
        result = check_service(url, name)
        results.append(result)
        
        status = result["status"]
        response_time = result.get("response_time", "N/A")
        print(f"{name:25} {status:15} {response_time}")
        
        # Mostrar información adicional para PostgreSQL
        if "PostgreSQL" in name and result.get("data"):
            data = result["data"]
            print(f"  └─ Configurado: {data.get('configured', 'N/A')}")
            print(f"  └─ Conectado: {data.get('connected', 'N/A')}")
            print(f"  └─ pgvector: {data.get('pgvector_installed', 'N/A')}")
            print(f"  └─ Dimensiones: {data.get('embedding_dim', 'N/A')}")
    
    # Verificar endpoints específicos de archivos
    print("\n📄 VERIFICANDO ENDPOINTS DE ARCHIVOS:")
    print("-" * 30)
    
    file_endpoints = [
        ("http://localhost:8000/api/v1/files", "Lista de archivos"),
        ("http://localhost:8000/api/v1/embeddings/health", "Embeddings health"),
    ]
    
    for url, name in file_endpoints:
        result = check_service(url, name)
        status = result["status"]
        response_time = result.get("response_time", "N/A")
        print(f"{name:25} {status:15} {response_time}")
    
    # Resumen
    print("\n📊 RESUMEN:")
    print("-" * 30)
    
    ok_count = sum(1 for r in results if "✅" in r["status"])
    total_count = len(results)
    
    if ok_count == total_count:
        print("🎉 ¡Todos los servicios están funcionando correctamente!")
        print("\n🔗 ENLACES ÚTILES:")
        print("- Frontend: http://localhost:8501")
        print("- API Docs: http://localhost:8000/docs")
        print("- PostgreSQL Health: http://localhost:8000/api/v1/pg/health")
        
        print("\n✨ PRÓXIMOS PASOS:")
        print("1. Subir un PDF pequeño (< 25MB) para probar")
        print("2. Verificar que se indexe correctamente")
        print("3. Probar el chat con contexto del PDF")
        
    else:
        print(f"⚠️ {ok_count}/{total_count} servicios funcionando correctamente")
        print("Revisa los logs con: docker-compose logs")

if __name__ == "__main__":
    main()
