#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del RAG.
Este script se puede eliminar en producción.
"""
import httpx
import json

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
FILE_ID = 1
SESSION_ID = 999  # Sesión de prueba

def test_chat_with_rag():
    """Prueba el endpoint de chat con RAG activado."""
    print("=" * 60)
    print("🧪 TEST: Chat con RAG (file_id=1)")
    print("=" * 60)
    
    # Payload para chat con RAG
    payload = {
        "session_id": SESSION_ID,
        "message": "¿Qué dice el PDF sobre funciones en Python?",
        "mode": "Arquitecto Python Senior",
        "file_id": FILE_ID  # ← Esto activa el RAG
    }
    
    print(f"\n📤 Enviando request:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = httpx.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"\n📥 Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Verificar si la respuesta contiene contexto del PDF
        reply = data.get("reply", "")
        if "contexto" in reply.lower() or "pdf" in reply.lower():
            print("\n✅ La respuesta menciona el PDF/contexto")
        else:
            print("\n⚠️ La respuesta NO menciona el PDF/contexto")
            
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"\n❌ Error HTTP {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_chat_without_rag():
    """Prueba el endpoint de chat SIN RAG."""
    print("\n" + "=" * 60)
    print("🧪 TEST: Chat sin RAG (file_id=None)")
    print("=" * 60)
    
    payload = {
        "session_id": SESSION_ID,
        "message": "¿Qué es Python?",
        "mode": "Arquitecto Python Senior"
        # Sin file_id = chat normal
    }
    
    print(f"\n📤 Enviando request:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = httpx.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"\n📥 Response (primeros 200 chars):")
        reply = data.get("reply", "")
        print(reply[:200] + "...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_files_endpoint():
    """Prueba el endpoint de archivos."""
    print("\n" + "=" * 60)
    print("🧪 TEST: Listar archivos")
    print("=" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/files", timeout=10)
        response.raise_for_status()
        
        files = response.json()
        print(f"\n✅ Archivos encontrados: {len(files)}")
        
        for file in files:
            print(f"\n📄 Archivo:")
            print(f"  - ID: {file.get('id')}")
            print(f"  - Nombre: {file.get('filename')}")
            print(f"  - Estado: {file.get('status')}")
            print(f"  - Páginas: {file.get('pages_processed')}/{file.get('total_pages')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_health():
    """Prueba el endpoint de health."""
    print("\n" + "=" * 60)
    print("🧪 TEST: Health check")
    print("=" * 60)
    
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"\n✅ Backend Status: {data.get('status')}")
        print(f"Service: {data.get('service')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Iniciando tests del sistema RAG\n")
    
    results = {
        "Health Check": test_health(),
        "Listar Archivos": test_files_endpoint(),
        "Chat sin RAG": test_chat_without_rag(),
        "Chat con RAG": test_chat_with_rag(),
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n🎯 Total: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n✅ ¡Todos los tests pasaron!")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisar logs arriba.")
