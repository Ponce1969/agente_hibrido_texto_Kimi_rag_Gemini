#!/usr/bin/env python3
"""
Script de prueba directa para LLM Gateway sin backend completo.

Este script simula el comportamiento del LLM Gateway para probar
la conexión con los modelos locales y el RAG de manera directa.
"""
import hashlib
import sqlite3
import time
from datetime import UTC, datetime, timedelta

import requests


class SimpleLLMGateway:
    """Gateway simplificado para pruebas directas."""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url.rstrip('/')
        self.cache_db = "test_llm_gateway_cache.db"
        self._init_cache()

    def _init_cache(self):
        """Inicializa cache SQLite simple."""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE NOT NULL,
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    mode_used TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            conn.commit()

    def _get_query_hash(self, query: str, mode: str) -> str:
        """Genera hash único para query+mode."""
        content = f"{query.lower().strip()}:{mode}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_cached(self, query: str, mode: str) -> str | None:
        """Obtiene respuesta cacheada."""
        query_hash = self._get_query_hash(query, mode)

        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.execute("""
                SELECT answer FROM cached_responses
                WHERE query_hash = ? AND expires_at > datetime('now')
            """, (query_hash,))
            result = cursor.fetchone()

            if result:
                print(f"🎯 Cache HIT para: {query[:50]}...")
                return result[0]

            print(f"❌ Cache MISS para: {query[:50]}...")
            return None

    def save_to_cache(self, query: str, answer: str, mode: str, ttl_hours: int = 24):
        """Guarda respuesta en cache."""
        query_hash = self._get_query_hash(query, mode)
        expires_at = datetime.now(UTC).replace(microsecond=0) + timedelta(hours=ttl_hours)

        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cached_responses
                (query_hash, query, answer, mode_used, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query_hash, query, answer, mode, expires_at))
            conn.commit()
            print(f"💾 Guardado en cache: {query[:50]}...")

    def should_use_rag(self, query: str) -> bool:
        """Heurísticas simples para decidir RAG vs Kimi."""
        query_lower = query.lower()

        rag_keywords = [
            "qué es", "qué significa", "cómo funciona", "explicar",
            "definición", "principio", "concepto", "según el pdf",
            "según el libro", "documentación", "technical", "arquitectura",
            "ortogonalidad", "dry", "pragmático"
        ]

        kimi_keywords = [
            "hola", "buenos días", "cómo estás", "gracias",
            "tiempo", "clima", "noticias", "conversar"
        ]

        for keyword in rag_keywords:
            if keyword in query_lower:
                return True

        for keyword in kimi_keywords:
            if keyword in query_lower:
                return False

        return len(query) > 50

    def call_backend_rag(self, query: str) -> str:
        """Llama al backend con RAG (simulado)."""
        try:
            # Usar el endpoint normal del backend con modo RAG
            payload = {
                "session_id": 1,
                "message": query,
                "mode": "Arquitecto Python Senior",  # Modo que usa RAG
                "file_id": 1  # Archivo de libros técnicos
            }

            response = requests.post(
                f"{self.backend_url}/api/v1/chat",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get("reply", "Error: respuesta vacía")
            else:
                return f"Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error de conexión: {str(e)}"

    def call_backend_kimi(self, query: str) -> str:
        """Llama al backend con Kimi (simulado)."""
        try:
            # Usar el endpoint normal del backend con modo simple
            payload = {
                "session_id": 1,
                "message": query,
                "mode": "Ingeniero de Código",  # Modo simple
                "file_id": None  # Sin RAG
            }

            response = requests.post(
                f"{self.backend_url}/api/v1/chat",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get("reply", "Error: respuesta vacía")
            else:
                return f"Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error de conexión: {str(e)}"

    def ask(self, query: str, mode: str = "auto") -> dict:
        """Método principal del gateway."""
        print(f"\n🚀 LLM Gateway - Query: {query}")
        print(f"📍 Modo solicitado: {mode}")

        # 1. Verificar cache
        cached_answer = self.get_cached(query, mode)
        if cached_answer:
            return {
                "answer": cached_answer,
                "mode_used": mode,
                "cached": True,
                "timestamp": datetime.now(UTC).isoformat()
            }

        # 2. Decidir modo real
        if mode == "auto":
            real_mode = "rag" if self.should_use_rag(query) else "kimi"
        else:
            real_mode = mode

        print(f"🎯 Modo real usado: {real_mode}")

        # 3. Llamar al backend
        start_time = time.time()

        if real_mode == "rag":
            answer = self.call_backend_rag(query)
        else:
            answer = self.call_backend_kimi(query)

        response_time = time.time() - start_time

        # 4. Guardar en cache
        self.save_to_cache(query, answer, real_mode)

        print(f"⏰ Tiempo de respuesta: {response_time:.2f}s")

        return {
            "answer": answer,
            "mode_used": real_mode,
            "cached": False,
            "response_time": response_time,
            "timestamp": datetime.now(UTC).isoformat()
        }


def test_gateway():
    """Función de prueba del gateway."""
    gateway = SimpleLLMGateway()

    print("🎯 Pruebas del LLM Gateway Simplificado")
    print("=" * 50)

    # Test 1: Pregunta técnica (debería usar RAG)
    print("\n📚 Test 1: Pregunta técnica (RAG)")
    result1 = gateway.ask("¿Qué es la ortogonalidad según el PDF?", "rag")
    print(f"✅ Respuesta: {result1['answer'][:200]}...")
    print(f"🎯 Modo usado: {result1['mode_used']}")
    print(f"💾 Cache: {result1['cached']}")

    # Test 2: Pregunta conversacional (debería usar Kimi)
    print("\n💬 Test 2: Pregunta conversacional (Kimi)")
    result2 = gateway.ask("hola, cómo estás?", "kimi")
    print(f"✅ Respuesta: {result2['answer'][:200]}...")
    print(f"🎯 Modo usado: {result2['mode_used']}")
    print(f"💾 Cache: {result2['cached']}")

    # Test 3: Modo automático
    print("\n🤖 Test 3: Modo automático")
    result3 = gateway.ask("explicar el principio DRY", "auto")
    print(f"✅ Respuesta: {result3['answer'][:200]}...")
    print(f"🎯 Modo usado: {result3['mode_used']}")
    print(f"💾 Cache: {result3['cached']}")

    # Test 4: Cache HIT
    print("\n💾 Test 4: Prueba de cache (repetir pregunta)")
    result4 = gateway.ask("explicar el principio DRY", "auto")
    print(f"✅ Respuesta: {result4['answer'][:200]}...")
    print(f"🎯 Modo usado: {result4['mode_used']}")
    print(f"💾 Cache: {result4['cached']}")

    print("\n🎉 Pruebas completadas!")
    print("📊 Tiempos de respuesta:")
    print(f"   - Test 1: {result1.get('response_time', 0):.2f}s")
    print(f"   - Test 2: {result2.get('response_time', 0):.2f}s")
    print(f"   - Test 3: {result3.get('response_time', 0):.2f}s")
    print(f"   - Test 4: {result4.get('response_time', 0):.2f}s (cache)")


if __name__ == "__main__":
    test_gateway()
