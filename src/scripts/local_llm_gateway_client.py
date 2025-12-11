#!/usr/bin/env python3
"""
Cliente de ejemplo para que modelos locales (LLaMA, Gemma) usen el LLM Gateway.

Este script muestra cómo los modelos locales pueden consultar al backend
a través del endpoint interno /api/internal/llm-gateway.

Uso:
    python local_llm_gateway_client.py "¿Qué es la ortogonalidad?"
    python local_llm_gateway_client.py "hola" --mode kimi
    python local_llm_gateway_client.py "explicar Python" --mode rag
"""
import argparse
import json
import sys
import time
from typing import Any

import requests


class LLMGatewayClient:
    """Cliente para comunicarse con el LLM Gateway interno."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.gateway_url = f"{self.base_url}/api/internal/llm-gateway"
        self.status_url = f"{self.base_url}/api/internal/llm-gateway/status"

    def ask(self, query: str, mode: str = "auto", session_id: int = 1) -> dict[str, Any]:
        """
        Envía una pregunta al LLM Gateway.

        Args:
            query: La pregunta a realizar
            mode: "auto" | "kimi" | "rag"
            session_id: ID de sesión para persistencia

        Returns:
            Diccionario con la respuesta y metadatos
        """
        payload = {
            "query": query,
            "mode": mode,
            "session_id": session_id
        }

        try:
            print(f"🤖 Enviando query al gateway: {query[:50]}...")
            print(f"📍 Modo: {mode} | Session: {session_id}")

            start_time = time.time()
            response = requests.post(self.gateway_url, json=payload, timeout=30)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta recibida en {response_time:.2f}s")
                print(f"🎯 Modo usado: {data['mode_used']}")
                print(f"💾 Cache: {'HIT' if data['cached'] else 'MISS'}")
                return data
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

        except requests.exceptions.Timeout:
            print("⏰ Timeout: El gateway tardó demasiado en responder")
            return {"error": "timeout"}
        except requests.exceptions.ConnectionError:
            print("🔌 Error de conexión: ¿Está corriendo el backend?")
            return {"error": "connection_error"}
        except Exception as e:
            print(f"💥 Error inesperado: {e}")
            return {"error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """Obtiene el estado del gateway y estadísticas de cache."""
        try:
            response = requests.get(self.status_url)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def interactive_mode(self):
        """Modo interactivo para pruebas manuales."""
        print("🚀 Modo interactivo del LLM Gateway Client")
        print("Comandos especiales:")
        print("  /status - Ver estado del gateway")
        print("  /mode auto|kimi|rag - Cambiar modo")
        print("  /quit - Salir")
        print("-" * 50)

        current_mode = "auto"
        session_id = 1

        while True:
            try:
                query = input(f"\n[{current_mode}] Query> ").strip()

                if query.lower() == "/quit":
                    print("👋 ¡Hasta luego!")
                    break

                if query.lower() == "/status":
                    status = self.get_status()
                    print(f"📊 Estado: {json.dumps(status, indent=2)}")
                    continue

                if query.lower().startswith("/mode "):
                    new_mode = query.lower().split(" ", 1)[1]
                    if new_mode in ["auto", "kimi", "rag"]:
                        current_mode = new_mode
                        print(f"✅ Modo cambiado a: {current_mode}")
                    else:
                        print("❌ Modo inválido. Use: auto, kimi, o rag")
                    continue

                if not query:
                    continue

                # Enviar query al gateway
                result = self.ask(query, current_mode, session_id)

                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"\n🎯 Respuesta ({result['mode_used']}):")
                    print("-" * 40)
                    print(result['answer'])
                    print("-" * 40)

                    # Incrementar session_id para simular conversación
                    session_id += 1

            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except EOFError:
                print("\n👋 ¡Hasta luego!")
                break


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Cliente para LLM Gateway")
    parser.add_argument("query", nargs="?", help="Query a enviar al gateway")
    parser.add_argument("--mode", choices=["auto", "kimi", "rag"], default="auto",
                       help="Modo de procesamiento (default: auto)")
    parser.add_argument("--session", type=int, default=1,
                       help="ID de sesión (default: 1)")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Modo interactivo")
    parser.add_argument("--status", action="store_true",
                       help="Mostrar estado del gateway")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="URL del backend (default: http://localhost:8000)")

    args = parser.parse_args()

    client = LLMGatewayClient(args.url)

    if args.status:
        print("📊 Estado del LLM Gateway:")
        status = client.get_status()
        print(json.dumps(status, indent=2))
        return

    if args.interactive or not args.query:
        client.interactive_mode()
        return

    # Modo single query
    result = client.ask(args.query, args.mode, args.session)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"\n🎯 Respuesta ({result['mode_used']}):")
        print("-" * 40)
        print(result['answer'])
        print("-" * 40)
        print(f"💾 Cache: {'HIT' if result['cached'] else 'MISS'}")
        print(f"⏰ Timestamp: {result['timestamp']}")


if __name__ == "__main__":
    main()
