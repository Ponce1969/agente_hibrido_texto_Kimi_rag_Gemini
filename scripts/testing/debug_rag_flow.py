#!/usr/bin/env python3
"""
Script de debugging para RAG - Muestra exactamente qué recibe el LLM

Ejecutar desde Docker:
docker compose exec backend python scripts/debug_rag_flow.py
"""

import asyncio
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, '/app')

async def debug_rag_flow():
    """Prueba completa del flujo RAG y muestra todos los detalles."""
    
    print("=" * 80)
    print("🔍 DEBUG RAG FLOW - Diagnóstico Completo")
    print("=" * 80)
    print()
    
    # 1. Verificar chunks en PostgreSQL
    print("📊 PASO 1: Verificar chunks indexados")
    print("-" * 80)
    
    from src.adapters.db.embeddings_repository import EmbeddingsRepository
    
    repo = EmbeddingsRepository()
    total_chunks = repo.count_chunks(None)
    file1_chunks = repo.count_chunks(1)
    file2_chunks = repo.count_chunks(2)
    
    print(f"Total chunks: {total_chunks}")
    print(f"file_id=1: {file1_chunks} chunks")
    print(f"file_id=2: {file2_chunks} chunks")
    print()
    
    if file2_chunks == 0:
        print("❌ ERROR: file_id=2 no tiene chunks indexados")
        print("   Indexar con: curl -X POST http://localhost:8000/api/v1/embeddings/index/2")
        return
    
    # 2. Buscar chunks relevantes
    print("🔎 PASO 2: Buscar chunks relevantes")
    print("-" * 80)
    
    from src.adapters.dependencies import get_embeddings_service
    
    svc = get_embeddings_service()
    query = "¿De qué trata este documento?"
    
    print(f"Query: '{query}'")
    print(f"file_id: 2")
    print(f"top_k: 5")
    print()
    
    results = await svc.search_similar(
        query=query,
        file_id="2",
        top_k=5
    )
    
    print(f"✅ Encontrados: {len(results)} chunks")
    print()
    
    if not results:
        print("❌ ERROR: No se encontraron chunks")
        return
    
    # 3. Mostrar preview de chunks
    print("📄 PASO 3: Preview de chunks encontrados")
    print("-" * 80)
    
    for i, r in enumerate(results, 1):
        text = r.get('text', '')
        similarity = r.get('similarity', 0.0)
        chunk_idx = r.get('chunk_index', 0)
        
        print(f"\nChunk {i}:")
        print(f"  Similarity: {similarity:.4f}")
        print(f"  Chunk index: {chunk_idx}")
        print(f"  Text length: {len(text)} caracteres")
        print(f"  Preview: {text[:200]}...")
    print()
    
    # 4. Construir contexto RAG
    print("🛠️ PASO 4: Construir contexto RAG")
    print("-" * 80)
    
    limit = 8000
    acc = 0
    parts = []
    
    for r in results:
        remaining = limit - acc
        if remaining <= 100:
            break
        
        content = r.get('text', '')
        chunk_idx = r.get('chunk_index', 0)
        similarity = r.get('similarity', 0.0)
        
        if not content:
            print(f"⚠️ Chunk {chunk_idx} sin contenido")
            continue
        
        snippet = content[:remaining]
        parts.append(f"[chunk {chunk_idx}, score={similarity:.3f}]\n{snippet}")
        acc += len(snippet)
    
    rag_context = "\n\n".join(parts)
    
    print(f"✅ Contexto construido:")
    print(f"   Total caracteres: {len(rag_context)}")
    print(f"   Total chunks usados: {len(parts)}")
    print(f"\n   Preview del contexto:")
    print(f"   {rag_context[:400]}...")
    print()
    
    # 5. Construir system prompt
    print("📝 PASO 5: Construir system prompt")
    print("-" * 80)
    
    system_prompt = (
        "Eres un asistente experto. El usuario te ha proporcionado un documento PDF y te hará preguntas sobre él.\n\n"
        "**IMPORTANTE:** Debes responder EXCLUSIVAMENTE basándote en la información del documento que se proporciona a continuación.\n"
        "Si la información no está en el documento, indica claramente que no se encuentra en el texto proporcionado.\n\n"
        "--- EXTRACTO DEL DOCUMENTO PDF ---\n\n"
        f"{rag_context}\n\n"
        "--- FIN DEL EXTRACTO ---\n\n"
        "Responde la pregunta del usuario usando SOLO la información del extracto anterior."
    )
    
    print(f"✅ System prompt creado:")
    print(f"   Longitud total: {len(system_prompt)} caracteres")
    print(f"\n   Contenido completo:")
    print("   " + "=" * 76)
    print(f"   {system_prompt[:1000]}...")
    print("   " + "=" * 76)
    print()
    
    # 6. Crear mensaje del usuario
    print("💬 PASO 6: Crear mensaje del usuario")
    print("-" * 80)
    
    from src.domain.models import ChatMessageCreate, MessageRole
    
    user_message = ChatMessageCreate(
        session_id="debug",
        role=MessageRole.USER,
        content=query
    )
    
    print(f"User message: '{user_message.content}'")
    print()
    
    # 7. Llamar al LLM (SIN caché)
    print("🤖 PASO 7: Llamar al LLM")
    print("-" * 80)
    
    from src.adapters.dependencies import get_groq_adapter
    
    llm = get_groq_adapter()
    
    print("Configuración:")
    print(f"  use_cache: False (para RAG)")
    print(f"  max_tokens: 2048")
    print(f"  temperature: 0.3")
    print()
    
    print("Llamando a Kimi-K2 (Groq)...")
    print()
    
    try:
        # Crear lista de mensajes vacía (solo el user message actual)
        from src.domain.models import ChatMessage
        
        # Convertir ChatMessageCreate a ChatMessage
        class MockMessage:
            def __init__(self, role, content):
                self.role = role
                self.content = content
        
        messages = [MockMessage(MessageRole.USER, query)]
        
        response, tokens = await llm.get_chat_completion(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=2048,
            temperature=0.3,
            use_cache=False,  # ✅ IMPORTANTE: Sin caché para RAG
        )
        
        print("✅ RESPUESTA DEL LLM:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        print()
        
        if tokens:
            print(f"Tokens consumidos: {tokens}")
        
        # 8. Verificar si la respuesta usa el contexto
        print()
        print("🔍 PASO 8: Verificar si usa el contexto")
        print("-" * 80)
        
        # Buscar frases que indiquen que NO vio el documento
        no_access_phrases = [
            "no tengo acceso",
            "no puedo ver",
            "no tengo visibilidad",
            "el entorno no me ha proporcionado",
            "no me ha entregado",
        ]
        
        response_lower = response.lower()
        found_no_access = any(phrase in response_lower for phrase in no_access_phrases)
        
        if found_no_access:
            print("❌ ERROR: El LLM dice que NO ve el documento")
            print("   Frases detectadas:")
            for phrase in no_access_phrases:
                if phrase in response_lower:
                    print(f"   - '{phrase}'")
            print()
            print("   POSIBLES CAUSAS:")
            print("   1. El system_prompt no llega al LLM")
            print("   2. El sistema de caché está sobrescribiendo el prompt")
            print("   3. El LLM ignora el system_prompt")
        else:
            print("✅ ÉXITO: El LLM parece usar el contexto del documento")
        
    except Exception as e:
        print(f"❌ ERROR al llamar al LLM: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("🏁 FIN DEL DIAGNÓSTICO")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(debug_rag_flow())
