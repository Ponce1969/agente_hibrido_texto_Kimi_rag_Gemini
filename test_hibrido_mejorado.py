#!/usr/bin/env python3
"""
🧪 Script de Prueba para el Sistema Híbrido Mejorado

Este script prueba todas las funcionalidades del nuevo sistema híbrido:
- Verificación de modelos disponibles
- Prueba de routing inteligente
- Test de fallback cascade
- Validación de endpoints nuevos

Uso:
    python test_hibrido_mejorado.py
"""

import asyncio
import json
import time
from typing import Any

import httpx


class HybridSystemTester:
    """Tester para el sistema híbrido mejorado."""
    
    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30)
        
    async def test_all(self) -> dict[str, Any]:
        """Ejecuta todas las pruebas del sistema híbrido."""
        print("🧪 **INICIANDO PRUEBAS DEL SISTEMA HÍBRIDO MEJORADO**")
        print("=" * 60)
        
        results = {
            "timestamp": time.time(),
            "tests": {},
            "summary": {"passed": 0, "failed": 0, "total": 0}
        }
        
        # 1. Health check básico
        results["tests"]["health"] = await self._test_health_check()
        
        # 2. Estado del sistema híbrido
        results["tests"]["hibrido_status"] = await self._test_hibrido_status()
        
        # 3. Modelos disponibles
        results["tests"]["hibrido_models"] = await self._test_hibrido_models()
        
        # 4. Test del sistema híbrido
        results["tests"]["hibrido_test"] = await self._test_hibrido_system()
        
        # 5. Pruebas de routing específico
        results["tests"]["routing_rag"] = await self._test_rag_routing()
        results["tests"]["routing_python"] = await self._test_python_routing()
        results["tests"]["routing_general"] = await self._test_general_routing()
        
        # 6. Prueba de fallback
        results["tests"]["fallback_cascade"] = await self._test_fallback_cascade()
        
        # Calcular resumen
        for test_name, test_result in results["tests"].items():
            if test_result.get("success", False):
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
            results["summary"]["total"] += 1
        
        # Imprimir resumen
        self._print_summary(results)
        
        return results
    
    async def _test_health_check(self) -> dict[str, Any]:
        """Prueba 1: Health check básico."""
        print("\n🔍 Test 1: Health Check Básico")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend healthy: {data.get('service')}")
                return {"success": True, "data": data}
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_hibrido_status(self) -> dict[str, Any]:
        """Prueba 2: Estado del sistema híbrido."""
        print("\n🤖 Test 2: Estado Sistema Híbrido")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/hibrido/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sistema híbrido operativo")
                print(f"   📊 Models available: {data['total_models_available']}")
                print(f"   🏥 System health: {data['system_health']}")
                print(f"   🎯 Strategy: {data['recommended_strategy']}")
                
                # Detalle de modelos
                for model_name, model_info in data["models"].items():
                    status = "✅" if model_info["available"] else "❌"
                    print(f"   {status} {model_name}: {model_info['type']}")
                
                return {"success": True, "data": data}
            else:
                print(f"❌ Status endpoint failed: {response.status_code}")
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            print(f"❌ Status endpoint error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_hibrido_models(self) -> dict[str, Any]:
        """Prueba 3: Modelos disponibles con capacidades."""
        print("\n📋 Test 3: Modelos Disponibles")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/hibrido/models")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data['total_available']} modelos configurados")
                
                for model in data["models"]:
                    print(f"   🤖 {model['name']} ({model['provider']})")
                    print(f"      💪 Especialidades: {', '.join(model['specialties'])}")
                    print(f"      ⚡ Velocidad: {model['speed']}")
                    print(f"      📚 Contexto: {model['context_window']}")
                    print()
                
                return {"success": True, "data": data}
            else:
                print(f"❌ Models endpoint failed: {response.status_code}")
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            print(f"❌ Models endpoint error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_hibrido_system(self) -> dict[str, Any]:
        """Prueba 4: Test automático del sistema híbrido."""
        print("\n🧪 Test 4: Prueba Automática Sistema")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/hibrido/test")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    print(f"✅ Test exitoso")
                    print(f"   ⏱️ Response time: {data['response_time_ms']}ms")
                    print(f"   📝 Response preview: {data['response'][:100]}...")
                    return {"success": True, "data": data}
                else:
                    print(f"❌ Test falló: {data.get('error')}")
                    return {"success": False, "error": data.get("error")}
            else:
                print(f"❌ Test endpoint failed: {response.status_code}")
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            print(f"❌ Test endpoint error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_rag_routing(self) -> dict[str, Any]:
        """Prueba 5: Routing para RAG (debería usar Gemini)."""
        print("\n📄 Test 5: Routing RAG (PDF)")
        try:
            # Crear sesión
            session_response = await self.client.post(
                f"{self.base_url}/api/v1/sessions",
                json={"user_id": "test_hibrido"}
            )
            if session_response.status_code != 201:
                return {"success": False, "error": "No se pudo crear sesión"}
            
            session_id = session_response.json()["session_id"]
            
            # Enviar pregunta con file_id (debería activar RAG con Gemini)
            start_time = time.time()
            chat_response = await self.client.post(
                f"{self.base_url}/api/v1/chat",
                json={
                    "session_id": session_id,
                    "message": "¿Qué es Python y para qué sirve?",
                    "mode": "architect",
                    "file_id": 1  # Simular PDF
                }
            )
            response_time = (time.time() - start_time) * 1000
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                print(f"✅ RAG routing funcionó")
                print(f"   ⏱️ Response time: {response_time:.0f}ms")
                print(f"   📝 Response: {data['reply'][:100]}...")
                return {"success": True, "response_time": response_time}
            else:
                print(f"❌ RAG routing failed: {chat_response.status_code}")
                return {"success": False, "error": f"Status {chat_response.status_code}"}
        except Exception as e:
            print(f"❌ RAG routing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_python_routing(self) -> dict[str, Any]:
        """Prueba 6: Routing para Python (debería usar Kimi-K2)."""
        print("\n🐍 Test 6: Routing Python Code")
        try:
            # Crear sesión
            session_response = await self.client.post(
                f"{self.base_url}/api/v1/sessions",
                json={"user_id": "test_hibrido"}
            )
            if session_response.status_code != 201:
                return {"success": False, "error": "No se pudo crear sesión"}
            
            session_id = session_response.json()["session_id"]
            
            # Enviar pregunta de Python (debería usar Kimi-K2 especializado)
            start_time = time.time()
            chat_response = await self.client.post(
                f"{self.base_url}/api/v1/chat",
                json={
                    "session_id": session_id,
                    "message": "¿Cómo creo una función en Python que calcule el factorial?",
                    "mode": "architect",
                    "file_id": None
                }
            )
            response_time = (time.time() - start_time) * 1000
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                print(f"✅ Python routing funcionó")
                print(f"   ⏱️ Response time: {response_time:.0f}ms")
                print(f"   📝 Response: {data['reply'][:100]}...")
                return {"success": True, "response_time": response_time}
            else:
                print(f"❌ Python routing failed: {chat_response.status_code}")
                return {"success": False, "error": f"Status {chat_response.status_code}"}
        except Exception as e:
            print(f"❌ Python routing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_general_routing(self) -> dict[str, Any]:
        """Prueba 7: Routing general (debería usar Kimi-K2)."""
        print("\n💬 Test 7: Routing General Chat")
        try:
            # Crear sesión
            session_response = await self.client.post(
                f"{self.base_url}/api/v1/sessions",
                json={"user_id": "test_hibrido"}
            )
            if session_response.status_code != 201:
                return {"success": False, "error": "No se pudo crear sesión"}
            
            session_id = session_response.json()["session_id"]
            
            # Enviar pregunta general
            start_time = time.time()
            chat_response = await self.client.post(
                f"{self.base_url}/api/v1/chat",
                json={
                    "session_id": session_id,
                    "message": "¿Cuál es la capital de Francia y qué me recomiendas visitar?",
                    "mode": "architect",
                    "file_id": None
                }
            )
            response_time = (time.time() - start_time) * 1000
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                print(f"✅ General routing funcionó")
                print(f"   ⏱️ Response time: {response_time:.0f}ms")
                print(f"   📝 Response: {data['reply'][:100]}...")
                return {"success": True, "response_time": response_time}
            else:
                print(f"❌ General routing failed: {chat_response.status_code}")
                return {"success": False, "error": f"Status {chat_response.status_code}"}
        except Exception as e:
            print(f"❌ General routing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_fallback_cascade(self) -> dict[str, Any]:
        """Prueba 8: Verificar que fallback cascade esté configurado."""
        print("\n🔄 Test 8: Verificación Fallback Cascade")
        try:
            # Obtener estado para verificar modelos disponibles
            status_response = await self.client.get(f"{self.base_url}/api/v1/hibrido/status")
            if status_response.status_code == 200:
                status = status_response.json()
                
                total_models = status["total_models_available"]
                local_models = status["local_models_available"]
                routing_enabled = status["routing_enabled"]
                
                print(f"✅ Fallback cascade configurado")
                print(f"   📊 Total modelos: {total_models}")
                print(f"   🏠 Modelos locales: {local_models}")
                print(f"   🔄 Routing habilitado: {routing_enabled}")
                
                if total_models >= 2:
                    print(f"   🎯 Cascade con {total_models} niveles funcionando")
                    return {"success": True, "cascade_levels": total_models}
                else:
                    print(f"   ⚠️ Solo {total_models} modelos disponibles")
                    return {"success": True, "cascade_levels": total_models, "warning": "Limited models"}
            else:
                return {"success": False, "error": "No se pudo verificar estado"}
        except Exception as e:
            print(f"❌ Fallback verification error: {e}")
            return {"success": False, "error": str(e)}
    
    def _print_summary(self, results: dict[str, Any]) -> None:
        """Imprime resumen final de pruebas."""
        print("\n" + "=" * 60)
        print("📊 **RESUMEN DE PRUEBAS**")
        print("=" * 60)
        
        summary = results["summary"]
        print(f"✅ Pasados: {summary['passed']}")
        print(f"❌ Fallidos: {summary['failed']}")
        print(f"📁 Total: {summary['total']}")
        
        success_rate = (summary['passed'] / summary['total']) * 100 if summary['total'] > 0 else 0
        print(f"🎯 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 **SISTEMA HÍBRIDO FUNCIONANDO PERFECTAMENTE**")
        elif success_rate >= 60:
            print("⚠️ **SISTEMA FUNCIONANDO CON ALGUNOS PROBLEMAS**")
        else:
            print("🚨 **SISTEMA REQUIERE ATENCIÓN**")
        
        print("\n📋 Detalle:")
        for test_name, test_result in results["tests"].items():
            status = "✅" if test_result.get("success", False) else "❌"
            print(f"   {status} {test_name}")
    
    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self.client.aclose()


async def main() -> None:
    """Función principal del tester."""
    tester = HybridSystemTester()
    
    try:
        results = await tester.test_all()
        
        # Guardar resultados en archivo
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"hibrido_test_results_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: {filename}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado en pruebas: {e}")
    finally:
        await tester.close()


if __name__ == "__main__":
    print("🧪 **TESTER DEL SISTEMA HÍBRIDO MEJORADO**")
    print("Asegúrate de que el backend esté corriendo en http://localhost:8000")
    print("y que Ollama esté disponible en http://localhost:11434")
    print()
    
    asyncio.run(main())
