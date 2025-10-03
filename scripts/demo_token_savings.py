#!/usr/bin/env python3
"""
Script de demostración del sistema de caché de prompts.

Muestra el ahorro de tokens en una conversación simulada.
"""

from pathlib import Path
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters.agents.prompt_manager import PromptManager
from src.adapters.agents.prompts import AgentMode
from src.adapters.db.message import ChatMessage, MessageRole


def simulate_conversation(session_id: str, num_messages: int = 5):
    """
    Simula una conversación y muestra métricas de tokens.
    
    Args:
        session_id: ID de la sesión
        num_messages: Número de mensajes a simular
    """
    manager = PromptManager()
    agent_mode = AgentMode.PYTHON_ARCHITECT
    
    print(f"\n{'='*70}")
    print(f"🎯 Simulación de conversación - Sesión: {session_id}")
    print(f"🤖 Agente: {agent_mode.value}")
    print(f"💬 Mensajes: {num_messages}")
    print(f"{'='*70}\n")
    
    # Simular conversación
    for i in range(num_messages):
        # Obtener prompt (completo o referencia)
        prompt, is_cached = manager.get_prompt(session_id, agent_mode)
        
        # Simular historial creciente
        history = [
            ChatMessage(
                id=j,
                session_id=session_id,
                role=MessageRole.USER if j % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {j}: This is a test message with some content.",
                message_index=j
            )
            for j in range(i)
        ]
        
        # Limitar historial
        limited_history = manager.limit_history(history)
        
        # Registrar métricas
        user_message = f"User message {i}: Please help me with Python code."
        metrics = manager.record_metrics(
            session_id=session_id,
            system_prompt=prompt,
            history=limited_history,
            user_message=user_message,
            is_cached=is_cached
        )
        
        # Mostrar métricas
        status = "🔴 FULL" if not is_cached else "🟢 CACHED"
        print(f"Llamada #{i+1} {status}")
        print(f"  ├─ System tokens:  {metrics.system_tokens:>5}")
        print(f"  ├─ History tokens: {metrics.history_tokens:>5}")
        print(f"  ├─ User tokens:    {metrics.user_tokens:>5}")
        print(f"  └─ TOTAL:          {metrics.total_tokens:>5} tokens")
        print()
    
    # Mostrar estadísticas finales
    print(f"\n{'='*70}")
    print("📊 ESTADÍSTICAS DE LA SESIÓN")
    print(f"{'='*70}")
    
    stats = manager.get_session_stats(session_id)
    
    print(f"\n📈 Resumen:")
    print(f"  ├─ Total de llamadas:     {stats['total_calls']}")
    print(f"  ├─ Tokens totales usados: {stats['total_tokens']:,}")
    print(f"  ├─ Promedio por llamada:  {stats['avg_tokens_per_call']:,}")
    print(f"  └─ Tokens ahorrados:      {stats['tokens_saved']:,} ({stats['savings_percentage']}%)")
    
    print(f"\n💰 Desglose:")
    print(f"  ├─ Primera llamada:       {stats['first_call_tokens']:,} tokens")
    print(f"  └─ Promedio con caché:    {stats['avg_cached_tokens']:,} tokens")
    
    # Calcular ahorro proyectado
    if stats['total_calls'] > 1:
        without_cache = stats['first_call_tokens'] * stats['total_calls']
        with_cache = stats['total_tokens']
        total_saved = without_cache - with_cache
        pct_saved = (total_saved / without_cache) * 100
        
        print(f"\n🎯 Proyección sin caché:")
        print(f"  ├─ Tokens sin caché:      {without_cache:,}")
        print(f"  ├─ Tokens con caché:      {with_cache:,}")
        print(f"  ├─ Ahorro total:          {total_saved:,} tokens")
        print(f"  └─ Porcentaje ahorrado:   {pct_saved:.1f}%")


def compare_all_agents():
    """Compara el ahorro de tokens entre todos los agentes."""
    manager = PromptManager()
    
    print(f"\n{'='*70}")
    print("🔍 COMPARACIÓN DE AHORRO POR AGENTE")
    print(f"{'='*70}\n")
    
    results = []
    
    for agent_mode in AgentMode:
        session_id = f"compare_{agent_mode.value}"
        
        # Primera llamada (completo)
        prompt1, _ = manager.get_prompt(session_id, agent_mode)
        tokens1 = manager.estimate_tokens(prompt1)
        
        # Segunda llamada (referencia)
        prompt2, _ = manager.get_prompt(session_id, agent_mode)
        tokens2 = manager.estimate_tokens(prompt2)
        
        savings = tokens1 - tokens2
        savings_pct = (savings / tokens1) * 100
        
        results.append({
            'agent': agent_mode.value,
            'full': tokens1,
            'cached': tokens2,
            'saved': savings,
            'pct': savings_pct
        })
    
    # Mostrar tabla
    print(f"{'Agente':<30} {'Full':<10} {'Cached':<10} {'Ahorro':<10} {'%':<8}")
    print(f"{'-'*70}")
    
    for r in results:
        print(f"{r['agent']:<30} {r['full']:<10} {r['cached']:<10} {r['saved']:<10} {r['pct']:.1f}%")
    
    # Promedio
    avg_full = sum(r['full'] for r in results) / len(results)
    avg_cached = sum(r['cached'] for r in results) / len(results)
    avg_saved = sum(r['saved'] for r in results) / len(results)
    avg_pct = sum(r['pct'] for r in results) / len(results)
    
    print(f"{'-'*70}")
    print(f"{'PROMEDIO':<30} {avg_full:<10.0f} {avg_cached:<10.0f} {avg_saved:<10.0f} {avg_pct:.1f}%")


def main():
    """Función principal."""
    print("\n" + "="*70)
    print("🚀 DEMOSTRACIÓN DEL SISTEMA DE CACHÉ DE PROMPTS")
    print("="*70)
    
    # Simulación 1: Conversación corta
    simulate_conversation("demo_short", num_messages=3)
    
    # Simulación 2: Conversación larga
    simulate_conversation("demo_long", num_messages=10)
    
    # Comparación entre agentes
    compare_all_agents()
    
    # Estadísticas globales
    manager = PromptManager()
    global_stats = manager.get_global_stats()
    
    print(f"\n{'='*70}")
    print("🌍 ESTADÍSTICAS GLOBALES")
    print(f"{'='*70}")
    print(f"\n  ├─ Total de sesiones:     {global_stats['total_sessions']}")
    print(f"  ├─ Total de llamadas:     {global_stats['total_calls']}")
    print(f"  ├─ Tokens totales:        {global_stats['total_tokens']:,}")
    print(f"  ├─ Tokens ahorrados:      {global_stats['total_saved']:,}")
    print(f"  └─ Ahorro global:         {global_stats['savings_percentage']}%")
    
    print(f"\n{'='*70}")
    print("✅ Demostración completada")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
